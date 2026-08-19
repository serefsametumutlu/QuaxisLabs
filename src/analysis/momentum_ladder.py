"""Uc Sira Ust Uste (Three in a Row) -- coklu-gecikme momentum merdiveni,
Lars Kestner "Nicel Trading Stratejileri" (kullanicinin masaustu arastirmasi,
2026-08-19). SAF MATEMATIK, I/O YOK.

Mantik: HICBIR indikator yok -- SADECE artan gecikmelerde ustuste 3 pozitif
momentum okumasi: close[i] > close[i-lag1] > close[i-lag2] > close[i-lag3]
(varsayilan lag=5/10/15). Kitaptaki ifade: "basitligine ragmen sasirtici
derecede guclu". Mevcut TUM sistemlerden (TRF/EMA, WaveTrend, harmonik,
wavelet) YAPISAL olarak farkli -- crossover/osilator/kanal DEGIL, saf
"yon-tutarliligi coklu olcek" filtresi."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.analysis.abcd_pattern import atr_wilder

OHLC_COLUMNS = ("time", "open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class Params:
    lag1: int = 5
    lag2: int = 10
    lag3: int = 15
    enable_long: bool = True
    enable_short: bool = True
    atr_period: int = 14
    sl_atr_mult: float = 1.5
    tp1_r: float = 1.0
    tp2_r: float = 2.0


@dataclass(frozen=True)
class Signal:
    direction: int
    signal_bar: int
    signal_time: pd.Timestamp
    entry_ref: float
    fill_ref: float
    tp1: float
    tp2: float
    sl: float


def detect(df: pd.DataFrame, params: Params = Params()) -> list[Signal]:
    n = len(df)
    time_col = df["time"]
    open_ = df["open"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    atr = atr_wilder(df, params.atr_period)
    lag3 = params.lag3

    signals: list[Signal] = []
    for i in range(lag3, n):
        c0, c1, c2, c3 = close[i], close[i - params.lag1], close[i - params.lag2], close[i - params.lag3]
        long_ok = params.enable_long and (c0 > c1 > c2 > c3)
        short_ok = params.enable_short and (c0 < c1 < c2 < c3)
        if not (long_ok or short_ok):
            continue
        direction = 1 if long_ok else -1

        if np.isnan(atr[i]) or atr[i] <= 0:
            continue
        entry_ref = float(close[i])
        fill_bar = i + 1
        fill_ref = float(open_[fill_bar]) if fill_bar < n else float("nan")
        risk = params.sl_atr_mult * atr[i]
        sl = entry_ref - direction * risk
        tp1 = entry_ref + direction * risk * params.tp1_r
        tp2 = entry_ref + direction * risk * params.tp2_r

        signals.append(
            Signal(
                direction=direction, signal_bar=i, signal_time=time_col.iloc[i],
                entry_ref=entry_ref, fill_ref=fill_ref, tp1=float(tp1), tp2=float(tp2), sl=float(sl),
            )
        )
    return signals
