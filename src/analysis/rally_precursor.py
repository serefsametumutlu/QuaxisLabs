"""Buyuk Yukselis Onculu (Rally Precursor) Analizi -- "hangi teknik kosullar
BUYUK bir yukselisin BASLANGICINDA ortak olarak bulunuyor" sorusunun
VERIYE-DAYALI (bottom-up) cevabi. SAF MATEMATIK, I/O YOK (`abcd_pattern.py`
ile AYNI katman ilkesi).

## Motivasyon (2026-08-20, kullanici istegi)

Onceki yaklasim (Wavelet Trend Rider + ablasyon) DISARIDAN gelen bir
stratejiyi (AxiQuant script'i) alip KOTU sinyalleri FILTRELEMEYE calisti --
sonuc: cok az sinyal (TUPRS'de 5 yilda 1-2 tane), COK BUYUK yukselislerin
COGU KACIRILDI. Kullanici bunun YERINE TERSTEN gitmek istedi: "hisselerin
GERCEK buyuk yukselislerini BUL, o yukselislerin BASLADIGI anda hangi
teknik kosullar/degerler ORTAK, altin oran ne -- BUNLARI istatistiksel
olarak KESFEDELIM, sonra o kesfedilen kosullardan YENI bir strateji
kuralim." Bu modul TAM OLARAK BUNU yapar.

## Yontem -- iki asamali, nedensellik-yasakli (bkz. abcd_factor_analysis.py)

1. **Aday toplama** (`find_rally_candidates`): her PIVOT DIP (fiyatin
   yerel en dusuk noktasi, `abcd_pattern.pivot_low` ile ONAYLI) bir "aday"
   dir. O dipten SONRAKI `max_lookahead_bars` bar icinde ulasilan EN
   YUKSEK fiyattan hesaplanan `rally_pct` -- bu adayin "buyuk bir
   yukselisin baslangici mi" sorusunun ETIKETIDIR (LABEL, gelecek verisi
   -- bu SADECE etiket icin kullanilir, ozellik CIKARIMI icin DEGIL,
   bkz. asagidaki nokta 2 ve `abcd_factor_analysis.py`nin AYNI ilkesi).

2. **Ozellik cikarimi + istatistik** (`extract_features` + `run_factor_
   analysis` REUSE): her adayin dip barindaki (VE ONCESINDEKI, causal)
   RSI/MACD/ADX/Bollinger/hacim/trend-konumu/Fibonacci-geri-cekilme/
   mevcut-dedektor-ortusumu olculur. `abcd_factor_analysis.run_factor_
   analysis` DOGRUDAN REUSE edilir (kronolojik %70/%30 split, FDR-duzeltmeli
   coklu-test, holdout dogrulama, VIF-budanmis lojistik regresyon -- HESAPLAMA
   MANTIGI IKI YERDE YASAMASIN ilkesi, `label_fn`/`extract_features_fn`
   parametreleriyle BU modulun kendi soru/ozellik kumesine BAGLANIR).

## Fibonacci/"altin oran" ozelligi -- nasil hesaplanir

Her dip icin, ONDAN ONCEKI en yakin pivot TEPE (`prior_high`) ve ONDAN
ONCEKI pivot DIP (`prior_low`, `prior_high`i olusturan yukselis bacaginin
baslangici) bulunur. Bu dip, o ONCEKI yukselis bacaginin (prior_low->
prior_high) NE KADARINI geri cekmis: `fib_retracement = (prior_high -
low) / (prior_high - prior_low)`. 0.618'e (altin oran) ne kadar yakin
oldugu (`fib_dist_from_618`) AYRI bir surekli ozellik olarak da test edilir
-- "altin oran BIST'te GERCEKTEN onemli mi" sorusuna ISTATISTIKSEL cevap
(varsayim DEGIL, olcum).

## Nedensellik yasagi (abcd_factor_analysis.py ile AYNI disiplin)

Bu modulun ciktisi ASLA "X kosulu yukselis GARANTI EDER/SEBEP OLUR" dilinde
RAPORLANMAZ -- SADECE "buyuk yukselisle baslayan dipler ile BASLAMAYANLAR
arasinda X ozelliginde ISTATISTIKSEL FARK var (n=.., p=.., FDR q=..,
holdout: dogrulandi/dogrulanmadi)" dilinde. Nihai "strateji" (bu bulgulardan
kurulacak YENI bir detektor) AYRI bir script'te, bu bulgulara DAYANARAK
insa edilir -- bu modulun KENDISI bir strateji DEGIL, bir KESIF aracidir.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.analysis.abcd_factor_analysis import _adx_wilder, _bollinger_percent_b, _macd_hist, _rsi_wilder
from src.analysis.abcd_pattern import atr_wilder, pivot_high, pivot_low

OHLC_COLUMNS = ("time", "open", "high", "low", "close", "volume")

_GOLDEN_RATIO = 0.618


@dataclass(frozen=True)
class RallyCandidate:
    """Bir pivot-dip "aday"i -- `abcd_factor_analysis.run_factor_analysis`in
    `trades_df` seklindeki bir satirina karsilik gelir (symbol/tf/currency/
    entry_time ZORUNLU alanlar, geri kalani bu modulun KENDI ozel semasi)."""

    symbol: str
    tf: str
    currency: str
    signal_bar: int  # pivot dip barinin ONAY bari (bkz. pivot_low docstring'i -- p+L)
    signal_time: pd.Timestamp
    low_bar: int  # pivot dip barinin KENDISI (onaydan L bar ONCE)
    low_price: float
    rally_pct: float  # ETIKET kaynagi -- ileri-bakisli, SADECE etiket icin
    prior_high_bar: int | None
    prior_high_price: float | None
    prior_low_bar: int | None
    prior_low_price: float | None
    prev_pivot_low_price: float | None  # higher-low/lower-low karsilastirmasi icin


def find_rally_candidates(
    df: pd.DataFrame,
    symbol: str,
    tf: str,
    currency: str = "TRY",
    pivot_lookback: int = 10,
    max_lookahead_bars: int = 120,
) -> list[RallyCandidate]:
    """Her onayli pivot-dip icin bir `RallyCandidate` uretir. `p + max_
    lookahead_bars >= n` olan (yeterli ILERI veri OLMAYAN, adil etiketlenemez)
    dipler DISLANIR -- serinin SON `max_lookahead_bars` bari hic aday
    URETMEZ (bilincli, `abcd_backtest`in benzer "yeterli veri yok" disiplini)."""
    n = len(df)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    time_col = df["time"]

    ph = pivot_high(high, pivot_lookback)
    pl = pivot_low(low, pivot_lookback)

    # Tum onayli pivotlari (tip+bar+fiyat) zaman sirasina gore birlestir --
    # `vcp_breakout._pivot_points`/merge deseniyle AYNI (bkz. o modul).
    highs = [(i - pivot_lookback, float(ph[i])) for i in range(n) if not np.isnan(ph[i])]
    lows = [(i - pivot_lookback, float(pl[i])) for i in range(n) if not np.isnan(pl[i])]
    merged = sorted([(b, p, "H") for b, p in highs] + [(b, p, "L") for b, p in lows], key=lambda t: t[0])

    candidates: list[RallyCandidate] = []
    for idx, (low_bar, low_price, kind) in enumerate(merged):
        if kind != "L":
            continue
        signal_bar = low_bar + pivot_lookback
        if signal_bar >= n or low_bar + 1 + max_lookahead_bars > n:
            continue  # yeterli ileri veri yok -- adil etiketlenemez, DISLA

        # ONCEKI pivot TEPE (Fibonacci geri-cekilme icin) + ONDAN ONCEKI pivot DIP.
        prior_high_bar = prior_high_price = None
        prior_low_bar = prior_low_price = None
        prev_pivot_low_price = None
        for j in range(idx - 1, -1, -1):
            b, p, k = merged[j]
            if k == "H" and prior_high_bar is None:
                prior_high_bar, prior_high_price = b, p
            elif k == "L" and prior_high_bar is not None and prior_low_bar is None:
                prior_low_bar, prior_low_price = b, p
            elif k == "L" and prior_high_bar is None and prev_pivot_low_price is None:
                prev_pivot_low_price = p  # ONCEKI tepe yok ama ONCEKI bir dip VAR (higher-low kiyasi icin yeter)
            if prior_low_bar is not None:
                break

        future_high = float(np.max(high[low_bar + 1 : low_bar + 1 + max_lookahead_bars]))
        rally_pct = (future_high - low_price) / low_price * 100.0 if low_price > 0 else float("nan")

        candidates.append(
            RallyCandidate(
                symbol=symbol, tf=tf, currency=currency,
                signal_bar=signal_bar, signal_time=time_col.iloc[signal_bar],
                low_bar=low_bar, low_price=low_price, rally_pct=rally_pct,
                prior_high_bar=prior_high_bar, prior_high_price=prior_high_price,
                prior_low_bar=prior_low_bar, prior_low_price=prior_low_price,
                prev_pivot_low_price=prev_pivot_low_price if prior_low_price is None else prior_low_price,
            )
        )

    return candidates


ALL_FEATURES: list[str] = [
    "rsi14", "rsi_min_10", "macd_hist_sign", "macd_hist_rising",
    "adx14", "adx_rising", "bb_percent_b", "bb_width_pctrank",
    "vol_ratio_recent", "dist_from_sma200_pct", "atr_pct_of_price",
    "fib_retracement", "fib_dist_from_618", "higher_low",
    "bars_since_prior_high", "momentum_signal_nearby", "harmonic_signal_nearby",
    # --- 2026-08-20 genisletme (kullanici istegi: "en basitten en karisiga
    #     tum kosullari cikaralim") -- bkz. modul ust notu "Genisletilmis
    #     ozellik kutuphanesi" bolumu. ---
    "stoch_k", "williams_r", "cci20",
    "pct_from_52w_low", "vol_climax_ratio", "vol_dryup_min_ratio",
    "gap_into_low_pct", "candle_pattern_at_low", "rsi_bullish_divergence",
    "atr_pctrank", "ma_ribbon_score", "dist_from_ema20_pct", "month_of_year",
    "demand_zone_proximity_atr", "in_demand_zone", "wavelet_momentum_nearby",
    "vcp_pattern_nearby", "vol_breakout_nearby",
]
CATEGORICAL_FEATURES: list[str] = [
    "macd_hist_sign", "macd_hist_rising", "adx_rising", "higher_low",
    "momentum_signal_nearby", "harmonic_signal_nearby",
    "candle_pattern_at_low", "rsi_bullish_divergence", "month_of_year",
    "wavelet_momentum_nearby", "vcp_pattern_nearby", "vol_breakout_nearby",
    "in_demand_zone",
]


def _stoch_k(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14, smooth: int = 3) -> np.ndarray:
    """Stokastik %K (yumusatilmis) -- standart `100*(close-LL)/(HH-LL)`,
    sonra `smooth` bar SMA. Pine-parity ZORUNLU DEGIL (bu, cekirdek tespit
    motoru degil, KESIF/istatistik ozelligi -- `abcd_factor_analysis.
    _adx_wilder` docstring'indeki AYNI gerekce)."""
    n = len(close)
    ll = pd.Series(low).rolling(period).min().to_numpy()
    hh = pd.Series(high).rolling(period).max().to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        raw_k = np.where(hh > ll, 100.0 * (close - ll) / (hh - ll), np.nan)
    return pd.Series(raw_k).rolling(smooth).mean().to_numpy()


def _williams_r(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    hh = pd.Series(high).rolling(period).max().to_numpy()
    ll = pd.Series(low).rolling(period).min().to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(hh > ll, -100.0 * (hh - close) / (hh - ll), np.nan)


def _cci(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 20) -> np.ndarray:
    tp = (high + low + close) / 3.0
    tp_s = pd.Series(tp)
    sma_tp = tp_s.rolling(period).mean()
    mean_dev = tp_s.rolling(period).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        return ((tp_s - sma_tp) / (0.015 * mean_dev)).to_numpy()


def _is_bullish_pin_bar(o: float, h: float, l: float, c: float) -> bool:
    """`harmonic_confirmation._is_bullish_pin_bar`den KOPYALANDI (bkz.
    modul ust notu -- katman/kapsulleme ilkesi, `momentum_confluence_
    variants.py` ile AYNI gerekce)."""
    rng = h - l
    if rng <= 0:
        return False
    body = abs(c - o)
    lower_wick = min(o, c) - l
    upper_wick = h - max(o, c)
    return lower_wick >= 2.0 * body and upper_wick <= body and c >= (l + 0.5 * rng)


def _is_bullish_engulfing(prev_o: float, prev_c: float, o: float, c: float) -> bool:
    return c > o and prev_c < prev_o and c >= prev_o and o <= prev_c


def _candle_pattern_at(df: pd.DataFrame, bar: int) -> str | None:
    if bar < 0 or bar >= len(df):
        return None
    o, h, l, c = (float(df["open"].iloc[bar]), float(df["high"].iloc[bar]), float(df["low"].iloc[bar]), float(df["close"].iloc[bar]))
    if _is_bullish_pin_bar(o, h, l, c):
        return "PIN_BAR"
    if bar >= 1:
        prev_o, prev_c = float(df["open"].iloc[bar - 1]), float(df["close"].iloc[bar - 1])
        if _is_bullish_engulfing(prev_o, prev_c, o, c):
            return "ENGULFING"
    return None


# `extract_features` sembol basina ONLARCA kez (her aday icin bir kez)
# cagrilir, ama Order Block taramasi `df`nin (o dip'e kadar KESILMIS
# hali DEGIL, tam ohlcv_df) FONKSIYONU -- ayni sembol icin TEKRAR TEKRAR
# TARAMAK yerine `id(ohlcv_df)`e gore ONBELLEKLENIR (performans -- bkz.
# `harmonic_confirmation.IndicatorSeries`nin "TEK SEFER hesapla" ilkesiyle
# AYNI ruh). Onbellek `ohlcv_df` NESNESININ omru boyunca gecerlidir --
# script'ler sembol basina TEK bir df nesnesi kullandigi surece GUVENLIDIR.
_order_block_cache: dict[int, list] = {}


def _cached_order_blocks(ohlcv_df: pd.DataFrame) -> list:
    from src.analysis.order_block_zones import _find_bullish_order_blocks

    key = id(ohlcv_df)
    if key not in _order_block_cache:
        try:
            _order_block_cache[key] = _find_bullish_order_blocks(ohlcv_df)
        except Exception:
            _order_block_cache[key] = []
    return _order_block_cache[key]


def _demand_zone_proximity_atr(df: pd.DataFrame, full_ohlcv_df: pd.DataFrame, low_bar: int, atr_val: float | None) -> float | None:
    """`order_block_zones.py`nin TAM 3-asamali Order Block/Talep Bolgesi
    tespitini kullanir (kaynak: `ABCD formasyonu/01_OrderBlock_Zone_
    Architecture_V3.2.md`, bkz. o modulun ust notu) -- bu dip barinin
    fiyati, `low_bar`e kadar (causal, `nearest_unmitigated_zone`in kendi
    `as_of_bar` kesmesiyle) HALA UNMITIGATED VE kalite>=50 olan EN YAKIN
    boga Order Block'a ATR cinsinden ne kadar uzakta (0 = TAM bolge
    icinde/uzerinde). `full_ohlcv_df` -- onbellekleme icin TAM (kesilmemis)
    seri, bkz. `_cached_order_blocks`."""
    from src.analysis.order_block_zones import nearest_unmitigated_zone

    if atr_val is None or not np.isfinite(atr_val) or atr_val <= 0:
        return None
    zones = _cached_order_blocks(full_ohlcv_df)
    if not zones:
        return None
    close = df["close"].to_numpy(dtype=float)
    low_price = float(df["low"].iloc[low_bar])
    result = nearest_unmitigated_zone(zones, close, as_of_bar=low_bar, price=low_price, atr_val=atr_val)
    return result[1] if result is not None else None


def extract_features(candidate_row: pd.Series | dict, ohlcv_df: pd.DataFrame) -> dict[str, float | int | None]:
    """`candidate_row` (bkz. `RallyCandidate`, DataFrame satirina cevrilmis)
    ve TAM fiyat serisi icin ozellikleri hesaplar. LOOK-AHEAD YOK:
    `ohlcv_df.iloc[:signal_bar+1]`e kesilir (bkz. `abcd_factor_analysis.
    extract_features` ile AYNI ilke -- `rally_pct`/etiket BURADA hic
    KULLANILMAZ, sadece `find_rally_candidates`de, cagiranin `label_fn`inde)."""
    row = candidate_row if isinstance(candidate_row, dict) else candidate_row.to_dict()
    signal_bar = int(row["signal_bar"])
    low_bar = int(row["low_bar"])
    low_price = float(row["low_price"])

    df = ohlcv_df.iloc[: signal_bar + 1].reset_index(drop=True)
    n = len(df)
    if n <= signal_bar:
        raise ValueError(f"ohlcv_df, signal_bar={signal_bar} icin yetersiz (n={n}).")

    close = df["close"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    volume = df["volume"].to_numpy(dtype=float)

    features: dict[str, float | int | None] = {}

    rsi = _rsi_wilder(close, 14)
    features["rsi14"] = float(rsi[low_bar]) if not np.isnan(rsi[low_bar]) else None
    rsi_window = rsi[max(0, low_bar - 9) : low_bar + 1]
    valid_rsi = rsi_window[~np.isnan(rsi_window)]
    features["rsi_min_10"] = float(valid_rsi.min()) if len(valid_rsi) > 0 else None

    hist = _macd_hist(close)
    h_now = hist[low_bar]
    if low_bar >= 3 and not np.isnan(h_now) and not np.isnan(hist[low_bar - 3]):
        features["macd_hist_sign"] = int(np.sign(h_now))
        features["macd_hist_rising"] = int(h_now > hist[low_bar - 3])
    else:
        features["macd_hist_sign"] = None
        features["macd_hist_rising"] = None

    adx = _adx_wilder(df, 14)
    features["adx14"] = float(adx[low_bar]) if not np.isnan(adx[low_bar]) else None
    if low_bar >= 5 and not np.isnan(adx[low_bar]) and not np.isnan(adx[low_bar - 5]):
        features["adx_rising"] = int(adx[low_bar] > adx[low_bar - 5])
    else:
        features["adx_rising"] = None

    bb = _bollinger_percent_b(close, 20, 2.0)
    features["bb_percent_b"] = float(bb[low_bar]) if not np.isnan(bb[low_bar]) else None

    mid = pd.Series(close).rolling(20).mean()
    std = pd.Series(close).rolling(20).std(ddof=0)
    bb_width = ((4.0 * std) / mid).to_numpy()
    width_rank = pd.Series(bb_width).rolling(120, min_periods=60).rank(pct=True).to_numpy()
    features["bb_width_pctrank"] = float(width_rank[low_bar]) if low_bar < len(width_rank) and not np.isnan(width_rank[low_bar]) else None

    vol_recent = volume[max(0, low_bar - 4) : low_bar + 1].mean() if low_bar >= 0 else np.nan
    vol_base_start = max(0, low_bar - 49)
    vol_base = volume[vol_base_start:low_bar].mean() if low_bar > vol_base_start else np.nan
    features["vol_ratio_recent"] = float(vol_recent / vol_base) if vol_base and vol_base > 0 and not np.isnan(vol_recent) else None

    sma200 = pd.Series(close).rolling(200).mean().to_numpy()
    s200 = sma200[low_bar]
    features["dist_from_sma200_pct"] = float((low_price - s200) / s200 * 100.0) if not np.isnan(s200) and s200 != 0 else None

    atr14 = atr_wilder(df, 14)
    features["atr_pct_of_price"] = float(atr14[low_bar] / low_price * 100.0) if not np.isnan(atr14[low_bar]) and low_price > 0 else None

    # NOT: `row` bir pandas Series'ten `.to_dict()` ile geldiyse eksik
    # degerler Python `None` DEGIL, `float('nan')` olur -- `x is not None`
    # bu durumda YANLISLIKLA True doner (nan, None DEGILDIR ama BURADA
    # "eksik" anlamina gelir). TUM opsiyonel alanlar bu yuzden `pd.isna()`
    # ile kontrol edilir (2026-08-20 duzeltmesi -- bkz. `scripts/rally_
    # precursor_arastirma.py`nin AYNI hatayi `_zone_for_row`de duzelttigi
    # commit).
    prior_high_price = row.get("prior_high_price")
    prior_low_price = row.get("prior_low_price")
    if not pd.isna(prior_high_price) and not pd.isna(prior_low_price):
        leg = float(prior_high_price) - float(prior_low_price)
        if leg > 0:
            retr = (float(prior_high_price) - low_price) / leg
            features["fib_retracement"] = float(retr)
            features["fib_dist_from_618"] = float(abs(retr - _GOLDEN_RATIO))
        else:
            features["fib_retracement"] = None
            features["fib_dist_from_618"] = None
    else:
        features["fib_retracement"] = None
        features["fib_dist_from_618"] = None

    prev_low = row.get("prev_pivot_low_price")
    features["higher_low"] = int(low_price > float(prev_low)) if not pd.isna(prev_low) else None

    prior_high_bar = row.get("prior_high_bar")
    features["bars_since_prior_high"] = int(low_bar - int(prior_high_bar)) if not pd.isna(prior_high_bar) else None

    features["momentum_signal_nearby"] = _momentum_signal_nearby(df, low_bar)
    features["harmonic_signal_nearby"] = _harmonic_signal_nearby(df, low_bar)
    features["wavelet_momentum_nearby"] = _wavelet_momentum_nearby(close, low_bar)
    features["vcp_pattern_nearby"] = _vcp_pattern_nearby(df, low_bar)
    features["vol_breakout_nearby"] = _vol_breakout_nearby(df, low_bar)

    stoch_k = _stoch_k(high, low, close)
    features["stoch_k"] = float(stoch_k[low_bar]) if low_bar < len(stoch_k) and not np.isnan(stoch_k[low_bar]) else None

    wr = _williams_r(high, low, close)
    features["williams_r"] = float(wr[low_bar]) if low_bar < len(wr) and not np.isnan(wr[low_bar]) else None

    cci = _cci(high, low, close)
    features["cci20"] = float(cci[low_bar]) if low_bar < len(cci) and not np.isnan(cci[low_bar]) else None

    win_52w = low[max(0, low_bar - 251) : low_bar + 1]
    low_52w = float(win_52w.min()) if len(win_52w) > 0 else np.nan
    features["pct_from_52w_low"] = float((low_price - low_52w) / low_52w * 100.0) if not np.isnan(low_52w) and low_52w > 0 else None

    vol_sma20 = pd.Series(volume).rolling(20).mean().to_numpy()
    v_sma_at = vol_sma20[low_bar] if low_bar < len(vol_sma20) else np.nan
    features["vol_climax_ratio"] = float(volume[low_bar] / v_sma_at) if not np.isnan(v_sma_at) and v_sma_at > 0 else None

    dryup_start = max(0, low_bar - 9)
    dryup_window_vol = volume[dryup_start : low_bar + 1]
    dryup_window_sma = vol_sma20[dryup_start : low_bar + 1]
    with np.errstate(divide="ignore", invalid="ignore"):
        dryup_ratios = dryup_window_vol / dryup_window_sma
    valid_dryup = dryup_ratios[np.isfinite(dryup_ratios)]
    features["vol_dryup_min_ratio"] = float(valid_dryup.min()) if len(valid_dryup) > 0 else None

    open_ = df["open"].to_numpy(dtype=float) if "open" in df.columns else np.full(n, np.nan)
    if low_bar >= 1 and not np.isnan(open_[low_bar]) and close[low_bar - 1] != 0:
        features["gap_into_low_pct"] = float((open_[low_bar] - close[low_bar - 1]) / close[low_bar - 1] * 100.0)
    else:
        features["gap_into_low_pct"] = None

    features["candle_pattern_at_low"] = _candle_pattern_at(df, low_bar) or "NONE"

    features["rsi_bullish_divergence"] = _rsi_bullish_divergence(rsi, low_bar, low_price, prior_low_price, row.get("prior_low_bar"))

    atr14_full = atr_wilder(df, 14)
    with np.errstate(divide="ignore", invalid="ignore"):
        atr_ratio_series = atr14_full / close
    atr_rank = pd.Series(atr_ratio_series).rolling(120, min_periods=60).rank(pct=True).to_numpy()
    features["atr_pctrank"] = float(atr_rank[low_bar]) if low_bar < len(atr_rank) and not np.isnan(atr_rank[low_bar]) else None

    ema20 = pd.Series(close).ewm(span=20, adjust=False).mean().to_numpy()
    ema50 = pd.Series(close).ewm(span=50, adjust=False).mean().to_numpy()
    ema100 = pd.Series(close).ewm(span=100, adjust=False).mean().to_numpy()
    ema200 = pd.Series(close).ewm(span=200, adjust=False).mean().to_numpy()
    if low_bar < len(ema200):
        e20, e50, e100, e200 = ema20[low_bar], ema50[low_bar], ema100[low_bar], ema200[low_bar]
        score = int(low_price > e20) + int(e20 > e50) + int(e50 > e100) + int(e100 > e200)
        features["ma_ribbon_score"] = score
        features["dist_from_ema20_pct"] = float((low_price - e20) / e20 * 100.0) if e20 > 0 else None
    else:
        features["ma_ribbon_score"] = None
        features["dist_from_ema20_pct"] = None

    signal_time = row.get("signal_time")
    if signal_time is None or pd.isna(signal_time):
        signal_time = row.get("entry_time")
    features["month_of_year"] = int(pd.Timestamp(signal_time).month) if signal_time is not None and not pd.isna(signal_time) else None

    atr_at_low = atr14_full[low_bar] if low_bar < len(atr14_full) else np.nan
    dz_dist = _demand_zone_proximity_atr(df, ohlcv_df, low_bar, float(atr_at_low) if not np.isnan(atr_at_low) else None)
    features["demand_zone_proximity_atr"] = dz_dist
    features["in_demand_zone"] = int(dz_dist is not None and dz_dist <= 0.1) if dz_dist is not None else None

    return features


def _wavelet_momentum_nearby(close: np.ndarray, low_bar: int, window: int = 3) -> int | None:
    """`wavelet_trend_rider._causal_wavelet_denoise`nin HAM momentum kosulu
    (velocity>0 VE acceleration>0, MTF/EMA/ADX/RSI FILTRESIZ) BU dip
    barinin +-`window` civarinda saglaniyor mu -- bkz. modul ust notu."""
    from src.analysis.wavelet_trend_rider import _causal_wavelet_denoise

    try:
        denoised = _causal_wavelet_denoise(close)
    except Exception:
        return None
    velocity = np.diff(denoised, prepend=np.nan)
    acceleration = np.diff(velocity, prepend=np.nan)
    lo = max(0, low_bar - window)
    hi = min(len(close), low_bar + window + 1)
    seg_v, seg_a = velocity[lo:hi], acceleration[lo:hi]
    valid = ~np.isnan(seg_v) & ~np.isnan(seg_a)
    if not valid.any():
        return None
    return int(bool(np.any((seg_v[valid] > 0) & (seg_a[valid] > 0))))


def _vcp_pattern_nearby(df: pd.DataFrame, low_bar: int, window: int = 5) -> int | None:
    """`vcp_breakout.detect()` BU dip barinin +-`window` civarinda bir
    kirilim uretti mi (3 sikisan pullback + hacimli kirilim, bkz. o
    modulun ust notu)."""
    from src.analysis import vcp_breakout as vcp

    try:
        signals = vcp.detect(df)
    except Exception:
        return None
    return int(any(abs(s.signal_bar - low_bar) <= window for s in signals))


def _vol_breakout_nearby(df: pd.DataFrame, low_bar: int, window: int = 3) -> int | None:
    """`vol_breakout_kestner.detect()` (Referans+kxATR oynaklik kirilimi)
    BU dip barinin +-`window` civarinda bir LONG tetigi uretti mi."""
    from src.analysis import vol_breakout_kestner as vbk

    try:
        signals = vbk.detect(df, vbk.Params(enable_short=False))
    except Exception:
        return None
    return int(any(abs(s.signal_bar - low_bar) <= window for s in signals))


def _rsi_bullish_divergence(
    rsi: np.ndarray, low_bar: int, low_price: float, prior_low_price: float | None, prior_low_bar: float | None,
) -> int | None:
    """Fiyat bu dipte ONCEKI dipten (prior_low) DAHA DUSUK/ESIT ama RSI
    DAHA YUKSEK ise (klasik boga uyumsuzlugu) 1, degilse 0 -- ONCEKI dip
    YOKSA (seri basi) None. `harmonic_confirmation.py`nin B->D RSI
    uyumsuzluk ilkesiyle AYNI mantik, farkli veri kaynagi (pivot dip
    zinciri)."""
    if prior_low_price is None or pd.isna(prior_low_price) or prior_low_bar is None or pd.isna(prior_low_bar):
        return None
    prior_low_bar_int = int(prior_low_bar)
    if prior_low_bar_int < 0 or prior_low_bar_int >= len(rsi) or low_bar >= len(rsi):
        return None
    rsi_now, rsi_prior = rsi[low_bar], rsi[prior_low_bar_int]
    if np.isnan(rsi_now) or np.isnan(rsi_prior):
        return None
    return int(low_price <= float(prior_low_price) and rsi_now > rsi_prior)


def _momentum_signal_nearby(df: pd.DataFrame, low_bar: int, window: int = 3) -> int | None:
    """`momentum_confluence.detect()` (V1) BU dip barinin +-`window` bar
    civarinda bir LONG sinyali urettiyse 1, uretmediyse 0 -- mevcut
    dedektorlerimizden HERHANGI biri bu diple ORTUSUYOR MU sorusu."""
    from src.analysis import momentum_confluence as mc

    try:
        signals = mc.detect(df, mc.Params(), variant="v1")
    except Exception:
        return None
    return int(any(abs(s.signal_bar - low_bar) <= window for s in signals))


def _harmonic_signal_nearby(df: pd.DataFrame, low_bar: int, window: int = 3) -> int | None:
    """Herhangi bir harmonik formasyonun (ABCD/Gartley/Bat/Butterfly/Crab,
    LONG yon) `detect_prz()` PRZ olayi bu dip barinin +-`window` bar
    civarinda olustuysa 1, olusmadiysa 0."""
    from src.analysis import harmonic_xabcd as hx

    try:
        events: list = []
        for params in (hx.ABCD_PRESET, *hx.HARMONIC_XABCD_PRESETS.values()):
            events.extend(hx.detect_prz(df, params))
    except Exception:
        return None
    return int(any(ev.direction > 0 and abs(ev.d_bar - low_bar) <= window for ev in events))
