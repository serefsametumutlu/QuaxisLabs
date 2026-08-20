"""Buyuk Yukselis Onculu Stratejisi -- `rally_precursor.py`nin tam BIST
kesif analizinden (657 sembol, 16237 aday, %50 esik, 2026-08-20) HOLDOUT'TA
DOGRULANMIS kosullardan kurulu YENI, somut bir strateji. SAF MATEMATIK,
I/O YOK (`abcd_pattern.py` ile AYNI katman ilkesi).

## Kaynak -- HANGI kosullar, NEDEN secildi

`docs/spec/RALLY_PRECURSOR_ARASTIRMASI.md`deki 35 ozellikten SADECE
kronolojik holdout'ta da (egitimde DEGIL) dogrulanan 7'si "guvenilir"
sayildi -- geri kalan 28'i (RSI/MACD/ADX/Fibonacci/higher-low/mevcut-
dedektor-ortusumu DAHIL) ya train'de FDR esigini gecmedi ya da holdout'ta
dogrulanamadi ("muhtemelen sans" etiketiyle raporda KALDI, silinmedi).
Bu 7'den, en GUCLU 4'u bu stratejinin CEKIRDEK puanlama kosullari, kalan
3'u ISTEGE BAGLI/bilgilendirici (opsiyonel bonus veya sadece teshis):

  1. **vol_dryup_min_ratio** (en buyuk etki, r=0.153): dip'e giden son 10
     barin hacmi, taban(50 bar)a gore CIDDI sekilde KURUMUS mu (<=0.45).
     "Firtina oncesi sessizlik" -- klasik ama BU VERIDE GERCEKTEN olculmus.
  2. **demand_zone_proximity_atr** (2. en buyuk etki, r=0.219, ama daha
     kucuk n -- sadece bir Order Block bulunabilen adaylarda olculebiliyor):
     dip, `order_block_zones.py`nin tespit ettigi bir talep bolgesine
     ATR cinsinden yakin mi (<=3.0). MEVCUTSA guclu bir onay, YOKSA
     (Order Block bulunamadi) NOTR sayilir -- disleyici DEGIL.
  3. **gap_into_low_pct** (r=0.078): dip barina GAP-DOWN ile mi girildi
     (<=-0.3%) -- kapitulasyon imzasi.
  4. **atr_pctrank** (r=0.077): dip aninda oynaklik, sembolun KENDI
     252-gunluk gecmisine gore yuzdelik sirada YUKSEK mi (>=0.55).

  BONUS/teshis (skor'a KATILMAZ, sadece Signal alaninda raporlanir):
  5. atr_pct_of_price (r=0.086, ama yon-tutarli, kaba bir onay)
  6. stoch_k (r=0.035, cok zayif, dusuk-guven)
  7. dist_from_ema20_pct (r=0.043, zayif, "pivot-dip zaten EMA20 altinda"
     yapisal onyargisiyla KARISIK olabilir -- ayrica belirtildi)

## ⚠️ "Golden ratio" (Fibonacci 0.618) bulgusu -- NEGATIF, ACIKCA raporlanir

Kesif analizinde `fib_dist_from_618` train'de FDR esigini bile GECEMEDI
(q=0.177). Bu, kullanicinin "altin oran ne" sorusuna VERIYE-DAYALI durust
cevap: BU VERIDE, BU TANIMLA, Fibonacci 0.618 seviyesi rastgele bir
seviyeden ISTATISTIKSEL olarak AYIRT EDILEMEDI. Bu yuzden strateji
Fibonacci'yi CEKIRDEK kosul olarak KULLANMAZ (disaridan bir kaynak
raporunun da AYNI sonuca ulastigi not edildi, bkz. arastirma raporu).

## Skor esigi -- NEDEN 3/4

`min_score=3` (4 cekirdek kosuldan en az 3'u), sinyal sikligini kullanicinin
istedigi "yilda 2-3" civarina YAKLASTIRMAK icin secildi (tam BIST backtesti
`scripts/rally_precursor_strategy_backtest.py`de dogrulanir -- GERCEK
sinyal sikligi/capture-rate/PF orada RAPORLANIR, burada VARSAYILMAZ).
`min_score` parametrik -- kullanici 2/4 (daha sik, daha gevsek) veya 4/4
(daha nadir, daha siki) deneyebilir.

## Pivot dip tespiti + TP/SL

`abcd_pattern.pivot_low` (Pine-parity, `pivot_lookback` bar ONAY gecikmesi
-- `rsi_mw_pattern.py`/`vcp_breakout.py` ile AYNI desen) kullanilir. TP/SL
ATR-tabanli, proje standardi R-katli yapida (`momentum_confluence.py`/
`wavelet_trend_rider.py` ile AYNI ilke) -- BU stratejinin hedefi BUYUK
hareketler oldugu icin TP1/TP2 digerlerinden DAHA GENIS (2R/4R)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.analysis.abcd_pattern import atr_wilder, pivot_low

OHLC_COLUMNS = ("time", "open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class Params:
    pivot_lookback: int = 10
    min_score: int = 3  # 4 cekirdek kosuldan en az kaci saglanmali
    vol_dryup_max_ratio: float = 0.45
    demand_zone_max_atr: float = 3.0
    gap_max_pct: float = -0.3  # bundan KUCUK-ESIT (daha negatif) olmali
    atr_pctrank_min: float = 0.55
    atr_period: int = 14
    sl_atr_mult: float = 1.5
    tp1_r: float = 2.0
    tp2_r: float = 4.0


@dataclass(frozen=True)
class Signal:
    direction: int  # HER ZAMAN +1 (LONG -- kesif analizi SADECE dip/yukselis baslangicini olctu)
    signal_bar: int
    signal_time: pd.Timestamp
    entry_ref: float
    fill_ref: float
    tp1: float
    tp2: float
    sl: float
    score: int  # 0-4, kac CEKIRDEK kosul saglandi
    # --- teshis/bonus alanlari (skor'a KATILMAZ, bilgi amacli) ---
    vol_dryup_min_ratio: float | None
    demand_zone_proximity_atr: float | None
    gap_into_low_pct: float | None
    atr_pctrank: float | None


def _vol_dryup_min_ratio(volume: np.ndarray, vol_sma20: np.ndarray, low_bar: int) -> float | None:
    start = max(0, low_bar - 9)
    seg_vol = volume[start : low_bar + 1]
    seg_sma = vol_sma20[start : low_bar + 1]
    with np.errstate(divide="ignore", invalid="ignore"):
        ratios = seg_vol / seg_sma
    valid = ratios[np.isfinite(ratios)]
    return float(valid.min()) if len(valid) > 0 else None


def _gap_into_low_pct(open_: np.ndarray, close: np.ndarray, low_bar: int) -> float | None:
    if low_bar < 1 or np.isnan(open_[low_bar]) or close[low_bar - 1] == 0:
        return None
    return float((open_[low_bar] - close[low_bar - 1]) / close[low_bar - 1] * 100.0)


def detect(df: pd.DataFrame, params: Params = Params()) -> list[Signal]:
    """`df` = herhangi bir OHLCV serisi (backtestte 1D, kesif analiziyle
    AYNI zaman dilimi tutarliligi icin). `order_block_zones.py` OPSIYONEL
    -- import basarisiz/yavas olursa demand-zone kosulu NOTR (None) sayilir,
    STRATEJI CALISMAYA devam eder (bkz. modul ust notu Kural 9 disiplini)."""
    n = len(df)
    L = params.pivot_lookback
    if n <= 2 * L + 50:
        return []

    time_col = df["time"]
    open_ = df["open"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    volume = df["volume"].to_numpy(dtype=float)

    atr14 = atr_wilder(df, params.atr_period)
    vol_sma20 = pd.Series(volume).rolling(20).mean().to_numpy()
    atr_ratio = atr14 / close
    atr_rank = pd.Series(atr_ratio).rolling(120, min_periods=60).rank(pct=True).to_numpy()

    pl = pivot_low(low, L)

    try:
        from src.analysis.order_block_zones import _find_bullish_order_blocks, nearest_unmitigated_zone

        zones = _find_bullish_order_blocks(df)
    except Exception:
        zones = None
        nearest_unmitigated_zone = None  # type: ignore[assignment]

    signals: list[Signal] = []
    for i in range(n):
        if np.isnan(pl[i]):
            continue
        low_bar = i - L
        signal_bar = i  # pivot ONAY bari (Pine-parity, mevcut proje deseniyle AYNI)
        if signal_bar >= n or low_bar < 0:
            continue
        low_price = float(low[low_bar])
        atr_at_low = atr14[low_bar]
        if np.isnan(atr_at_low) or atr_at_low <= 0:
            continue

        dryup = _vol_dryup_min_ratio(volume, vol_sma20, low_bar)
        gap_pct = _gap_into_low_pct(open_, close, low_bar)
        pctrank = float(atr_rank[low_bar]) if not np.isnan(atr_rank[low_bar]) else None

        dz_dist: float | None = None
        if zones and nearest_unmitigated_zone is not None:
            result = nearest_unmitigated_zone(zones, close, as_of_bar=low_bar, price=low_price, atr_val=float(atr_at_low))
            dz_dist = result[1] if result is not None else None

        score = 0
        score += int(dryup is not None and dryup <= params.vol_dryup_max_ratio)
        score += int(dz_dist is not None and dz_dist <= params.demand_zone_max_atr)
        score += int(gap_pct is not None and gap_pct <= params.gap_max_pct)
        score += int(pctrank is not None and pctrank >= params.atr_pctrank_min)

        if score < params.min_score:
            continue

        entry_ref = float(close[signal_bar])
        fill_bar = signal_bar + 1
        fill_ref = float(open_[fill_bar]) if fill_bar < n else float("nan")
        risk = params.sl_atr_mult * atr_at_low
        sl = entry_ref - risk
        tp1 = entry_ref + risk * params.tp1_r
        tp2 = entry_ref + risk * params.tp2_r

        signals.append(
            Signal(
                direction=1, signal_bar=signal_bar, signal_time=time_col.iloc[signal_bar],
                entry_ref=entry_ref, fill_ref=fill_ref, tp1=float(tp1), tp2=float(tp2), sl=float(sl),
                score=score,
                vol_dryup_min_ratio=dryup, demand_zone_proximity_atr=dz_dist,
                gap_into_low_pct=gap_pct, atr_pctrank=pctrank,
            )
        )

    return signals
