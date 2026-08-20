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
]
CATEGORICAL_FEATURES: list[str] = [
    "macd_hist_sign", "macd_hist_rising", "adx_rising", "higher_low",
    "momentum_signal_nearby", "harmonic_signal_nearby",
]


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

    prior_high_price = row.get("prior_high_price")
    prior_low_price = row.get("prior_low_price")
    if prior_high_price is not None and prior_low_price is not None:
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
    features["higher_low"] = int(low_price > float(prev_low)) if prev_low is not None else None

    prior_high_bar = row.get("prior_high_bar")
    features["bars_since_prior_high"] = int(low_bar - int(prior_high_bar)) if prior_high_bar is not None else None

    features["momentum_signal_nearby"] = _momentum_signal_nearby(df, low_bar)
    features["harmonic_signal_nearby"] = _harmonic_signal_nearby(df, low_bar)

    return features


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
