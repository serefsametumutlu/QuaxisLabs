"""M&W RSI Deseni -- cift-dip/cift-tepe paterni FIYAT uzerinde DEGIL, RSI
SERISI uzerinde arandigi bir yaklasim ("51 Trading Strategies", kullanicinin
masaustu arastirmasi, 2026-08-19). SAF MATEMATIK, I/O YOK.

Mantik: `abcd_pattern.pivot_low`/`pivot_high` (ayni Pine-parity pivot
tespiti) FIYAT yerine RSI14 DIZISINE uygulanir. Iki ardisik RSI pivot-dibi
IKISI de asiri-satim (<30) bolgesinde VE ikincisi birinciden YUKSEKSE
("W" sekli, RSI'nin kendi ic yapisinda pozitif ivme) -> LONG. Simetri:
iki ardisik RSI pivot-tepesi IKISI de asiri-alim (>70) VE ikincisi
birinciden DUSUKSE ("M") -> SHORT. Harmonik modulundeki B->D RSI
uyumsuzlugundan (rastgele iki fiyat pivotu karsilastirir) FARKLI --
burada karsilastirilan iki nokta ozellikle RSI'nin KENDI asiri-bolge
donuslerinden secilir."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.analysis.abcd_pattern import atr_wilder, pivot_high, pivot_low
from src.analysis.abcd_factor_analysis import _rsi_wilder

OHLC_COLUMNS = ("time", "open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class Params:
    rsi_period: int = 14
    pivot_lookback: int = 3
    oversold: float = 35.0
    overbought: float = 65.0
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
    rsi_pivot_1: float
    rsi_pivot_2: float


def detect(df: pd.DataFrame, params: Params = Params()) -> list[Signal]:
    n = len(df)
    time_col = df["time"]
    open_ = df["open"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    atr = atr_wilder(df, params.atr_period)
    rsi = _rsi_wilder(close, params.rsi_period)

    rsi_filled = np.where(np.isnan(rsi), 50.0, rsi)  # pivot fonksiyonlari NaN kabul etmez
    L = params.pivot_lookback
    piv_lo = pivot_low(rsi_filled, L)
    piv_hi = pivot_high(rsi_filled, L)

    signals: list[Signal] = []
    last_lo: float | None = None
    last_hi: float | None = None

    for i in range(n):
        if not np.isnan(piv_lo[i]):
            v = float(piv_lo[i])
            if params.enable_long and last_lo is not None and last_lo < params.oversold and v < params.oversold and v > last_lo:
                if not (np.isnan(atr[i]) or atr[i] <= 0):
                    entry_ref = float(close[i])
                    fill_bar = i + 1
                    fill_ref = float(open_[fill_bar]) if fill_bar < n else float("nan")
                    risk = params.sl_atr_mult * atr[i]
                    sl = entry_ref - risk
                    signals.append(
                        Signal(
                            direction=1, signal_bar=i, signal_time=time_col.iloc[i],
                            entry_ref=entry_ref, fill_ref=fill_ref,
                            tp1=float(entry_ref + risk * params.tp1_r), tp2=float(entry_ref + risk * params.tp2_r),
                            sl=float(sl), rsi_pivot_1=last_lo, rsi_pivot_2=v,
                        )
                    )
            last_lo = v

        if not np.isnan(piv_hi[i]):
            v = float(piv_hi[i])
            if params.enable_short and last_hi is not None and last_hi > params.overbought and v > params.overbought and v < last_hi:
                if not (np.isnan(atr[i]) or atr[i] <= 0):
                    entry_ref = float(close[i])
                    fill_bar = i + 1
                    fill_ref = float(open_[fill_bar]) if fill_bar < n else float("nan")
                    risk = params.sl_atr_mult * atr[i]
                    sl = entry_ref + risk
                    signals.append(
                        Signal(
                            direction=-1, signal_bar=i, signal_time=time_col.iloc[i],
                            entry_ref=entry_ref, fill_ref=fill_ref,
                            tp1=float(entry_ref - risk * params.tp1_r), tp2=float(entry_ref - risk * params.tp2_r),
                            sl=float(sl), rsi_pivot_1=last_hi, rsi_pivot_2=v,
                        )
                    )
            last_hi = v

    signals.sort(key=lambda s: s.signal_bar)
    return signals
