"""Asiri-Kapanis Ters-Yon (Countertrend Extreme-Close Fade) -- Robert Pardo
kokenli sistem (Building Winning Algorithmic Trading Systems, kullanicinin
masaustu arastirmasi, 2026-08-19). SAF MATEMATIK, I/O YOK.

Mantik: kapanis, son X barin EN YUKSEGI ise -> asiri uzama VAR say, SHORT
(fade); kapanis son Y barin EN DUSUGU ise -> LONG (fade). Kitabin kendi
walk-forward ornekinde net karli bulunmus (X~=7-9, Y~=5-17) -- bu port
X=8/Y=10 varsayilanini kullanir. Mevcut sistemlerin AKSINE (harmonik/
momentum DEVAM/donus ARAR) bu SALT "asiri uzama = tukenis" varsayimiyla
CALISIR, hicbir baska onay/osilator GEREKMEZ -- kasitli saf/basit."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.analysis.abcd_pattern import atr_wilder

OHLC_COLUMNS = ("time", "open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class Params:
    short_lookback: int = 8  # X -- en yuksek kapanis penceresi (SHORT tetigi)
    long_lookback: int = 10  # Y -- en dusuk kapanis penceresi (LONG tetigi)
    atr_period: int = 14
    sl_atr_mult: float = 1.5
    tp1_r: float = 1.0
    tp2_r: float = 2.0
    enable_long: bool = True
    enable_short: bool = True


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

    roll_max_close = pd.Series(close).rolling(params.short_lookback).max().to_numpy()
    roll_min_close = pd.Series(close).rolling(params.long_lookback).min().to_numpy()

    signals: list[Signal] = []
    for i in range(max(params.short_lookback, params.long_lookback), n):
        if np.isnan(atr[i]) or atr[i] <= 0:
            continue
        direction = 0
        if params.enable_short and close[i] >= roll_max_close[i]:
            direction = -1
        elif params.enable_long and close[i] <= roll_min_close[i]:
            direction = 1
        if direction == 0:
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
