"""Cift RSI (coklu-zaman-dilimi RSI konfluensiyonu) -- "51 Trading
Strategies" (Aseem Singhal) kaynakli (kullanicinin masaustu arastirmasi,
2026-08-19). SAF MATEMATIK, I/O YOK.

Mantik: DUSUK zaman diliminde (4H) RSI14 asiri-satimdan (<30) yukari
KESIYORKEN, YUKSEK zaman diliminde (1D) RSI14>50 ise LONG (buyuk resim
hala yukselen egilimde, kucuk resim sadece gecici bir soguma yasadi --
gurultu filtrelenir). SHORT simetrigi: 4H RSI asiri-alimdan (>70) asagi
keserken 1D RSI<50. `wavelet_trend_rider.py`nin coklu-zaman-dilimi
hizalama ilkesiyle AYNI (gunluk deger, o gunden KESINLIKLE ONCEKI son
kapanmis gunluk bardan alinir -- look-ahead YOK)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.analysis.abcd_factor_analysis import _rsi_wilder
from src.analysis.abcd_pattern import atr_wilder

OHLC_COLUMNS = ("time", "open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class Params:
    rsi_period: int = 14
    oversold: float = 30.0
    overbought: float = 70.0
    daily_midline: float = 50.0
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
    rsi_ltf: float
    rsi_htf: float


def _daily_aligned(bar_times: pd.Series, daily_df: pd.DataFrame, daily_values: np.ndarray) -> np.ndarray:
    """`wavelet_trend_rider._daily_series_aligned` ile AYNI ilke (bagimsiz
    kopya -- `momentum_confluence_variants.py`nin kendi RSI/EMA kopyalarini
    tutma gerekcesiyle AYNI, cross-module coupling YOK)."""
    if daily_df.empty:
        return np.full(len(bar_times), np.nan)
    daily_dates = pd.to_datetime(daily_df["time"]).dt.tz_localize(None).dt.normalize().to_numpy()
    bar_dates = pd.to_datetime(bar_times).dt.tz_localize(None).dt.normalize().to_numpy()
    idx = np.searchsorted(daily_dates, bar_dates, side="left") - 1
    out = np.full(len(bar_times), np.nan)
    valid = idx >= 0
    out[valid] = daily_values[idx[valid]]
    return out


def detect(df: pd.DataFrame, df_daily: pd.DataFrame, params: Params = Params()) -> list[Signal]:
    n = len(df)
    time_col = df["time"]
    open_ = df["open"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    atr = atr_wilder(df, params.atr_period)
    rsi_ltf = _rsi_wilder(close, params.rsi_period)

    daily_rsi_series = _rsi_wilder(df_daily["close"].to_numpy(dtype=float), params.rsi_period) if not df_daily.empty else np.array([])
    rsi_htf = _daily_aligned(time_col, df_daily, daily_rsi_series)

    signals: list[Signal] = []
    for i in range(1, n):
        if any(np.isnan(v) for v in (rsi_ltf[i], rsi_ltf[i - 1], rsi_htf[i], atr[i])) or atr[i] <= 0:
            continue
        long_ok = (
            params.enable_long and rsi_ltf[i - 1] < params.oversold and rsi_ltf[i] >= params.oversold
            and rsi_htf[i] > params.daily_midline
        )
        short_ok = (
            params.enable_short and rsi_ltf[i - 1] > params.overbought and rsi_ltf[i] <= params.overbought
            and rsi_htf[i] < params.daily_midline
        )
        if not (long_ok or short_ok):
            continue
        direction = 1 if long_ok else -1

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
                rsi_ltf=float(rsi_ltf[i]), rsi_htf=float(rsi_htf[i]),
            )
        )
    return signals
