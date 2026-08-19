"""VCP -- Volatility Contraction Pattern (Mark Minervini kokenli, "51
Trading Strategies" kitabinda da anlatilan; kullanicinin masaustu
arastirmasi, 2026-08-19). SAF MATEMATIK, I/O YOK.

Mantik: yukselis trendinde ardisik 3 geri cekilme (pivot-tepe -> pivot-dip
ciftleri), HER BIRI ONCEKINDEN (1) daha SIG (kucuk yuzde), (2) daha KISA
surede TAMAMLANIYOR, VE (3) daha DUSUK hacimle gerceklesiyor (satis baskisi
azaliyor -- "sikismis" bir taban). Son (en sik) gerilemeden sonra, desen
direncinin USTUNE hacim patlamali (>=1.5x SMA20) yesil mumla KIRILIM
gelirse LONG.

`abcd_pattern.pivot_high/pivot_low` REUSE edilir (Pine-parity pivot
tespiti, ayni fonksiyon `harmonic_xabcd.py`/`rsi_mw_pattern.py`de de
kullanilir) -- pivot ONAY gecikmesi (`L` bar) burada da GECERLIDIR, desen
sadece TUM 3 pivot cifti ONAYLANDIKTAN sonra taninir (look-ahead YOK)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.analysis.abcd_pattern import atr_wilder, pivot_high, pivot_low

OHLC_COLUMNS = ("time", "open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class Params:
    pivot_lookback: int = 3
    max_breakout_wait_bars: int = 20
    vol_sma_len: int = 20
    vol_breakout_mult: float = 1.5
    atr_period: int = 14
    sl_atr_mult: float = 1.0  # SL zaten son (en sik) dip -- ATR SADECE ek tampon
    tp1_r: float = 1.5
    tp2_r: float = 3.0


@dataclass(frozen=True)
class Signal:
    direction: int  # HER ZAMAN +1 (kaynakta SADECE LONG kirilim var)
    signal_bar: int
    signal_time: pd.Timestamp
    entry_ref: float
    fill_ref: float
    tp1: float
    tp2: float
    sl: float
    resistance: float
    n_pullbacks: int = 3


def _pivot_points(arr: np.ndarray, lookback: int) -> list[tuple[int, float]]:
    out: list[tuple[int, float]] = []
    for i in range(len(arr)):
        if not np.isnan(arr[i]):
            out.append((i - lookback, float(arr[i])))
    return out


def detect(df: pd.DataFrame, params: Params = Params()) -> list[Signal]:
    n = len(df)
    time_col = df["time"]
    open_ = df["open"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    volume = df["volume"].to_numpy(dtype=float)
    atr = atr_wilder(df, params.atr_period)
    vol_sma = pd.Series(volume).rolling(params.vol_sma_len).mean().to_numpy()

    L = params.pivot_lookback
    highs = _pivot_points(pivot_high(high, L), L)
    lows = _pivot_points(pivot_low(low, L), L)

    merged: list[tuple[int, float, str]] = sorted(
        [(b, p, "H") for b, p in highs] + [(b, p, "L") for b, p in lows], key=lambda t: t[0]
    )

    signals: list[Signal] = []
    already_signaled_until = -1

    for k in range(len(merged) - 5):
        h0b, h0p, t0 = merged[k]
        l1b, l1p, t1 = merged[k + 1]
        h1b, h1p, t2 = merged[k + 2]
        l2b, l2p, t3 = merged[k + 3]
        h2b, h2p, t4 = merged[k + 4]
        l3b, l3p, t5 = merged[k + 5]
        if (t0, t1, t2, t3, t4, t5) != ("H", "L", "H", "L", "H", "L"):
            continue
        if h0p <= 0 or h1p <= 0 or h2p <= 0:
            continue

        depth1, depth2, depth3 = (h0p - l1p) / h0p, (h1p - l2p) / h1p, (h2p - l3p) / h2p
        if not (depth1 > depth2 > depth3 > 0):
            continue
        dur1, dur2, dur3 = l1b - h0b, l2b - h1b, l3b - h2b
        if not (dur1 >= dur2 >= dur3 > 0):
            continue
        if any(b < 0 for b in (h0b, l1b, h1b, l2b, h2b, l3b)):
            continue

        vol1 = float(np.mean(volume[h0b:l1b])) if l1b > h0b else np.nan
        vol2 = float(np.mean(volume[h1b:l2b])) if l2b > h1b else np.nan
        vol3 = float(np.mean(volume[h2b:l3b])) if l3b > h2b else np.nan
        if not (vol1 > vol2 > vol3 > 0):
            continue

        resistance = float(max(h0p, h1p, h2p))
        confirm_bar = l3b + L  # l3'un ONAY bari -- desen ANCAK bu barda "bilinir"
        wait_end = min(confirm_bar + params.max_breakout_wait_bars, n)

        for i in range(max(confirm_bar, already_signaled_until + 1), wait_end):
            if np.isnan(atr[i]) or atr[i] <= 0 or np.isnan(vol_sma[i]) or vol_sma[i] <= 0:
                continue
            breakout = (
                close[i] > resistance
                and close[i] > open_[i]
                and volume[i] >= params.vol_breakout_mult * vol_sma[i]
            )
            if not breakout:
                continue

            entry_ref = float(close[i])
            fill_bar = i + 1
            fill_ref = float(open_[fill_bar]) if fill_bar < n else float("nan")
            sl = min(l3p, entry_ref - params.sl_atr_mult * atr[i])
            risk = entry_ref - sl
            if risk <= 0:
                break
            tp1 = entry_ref + risk * params.tp1_r
            tp2 = entry_ref + risk * params.tp2_r

            signals.append(
                Signal(
                    direction=1, signal_bar=i, signal_time=time_col.iloc[i],
                    entry_ref=entry_ref, fill_ref=fill_ref, tp1=float(tp1), tp2=float(tp2), sl=float(sl),
                    resistance=resistance,
                )
            )
            already_signaled_until = i
            break

    signals.sort(key=lambda s: s.signal_bar)
    return signals
