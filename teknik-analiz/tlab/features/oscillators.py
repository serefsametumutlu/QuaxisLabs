"""Momentum osilatörleri (MACD, RSI, Stochastic) — hepsi yalnızca geçmişe bakar.

Kesişim (cross) sinyalleri için tlab.features.ma.crossovers yeniden
kullanılabilir (ör. crossovers(macd.macd, macd.signal)); burada
tekrarlanmaz.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tlab.features.ma import ema


@dataclass(frozen=True)
class Macd:
    macd: pd.Series
    signal: pd.Series
    histogram: pd.Series


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Macd:
    fast_ema = ema(series, fast)
    slow_ema = ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal)
    return Macd(macd=macd_line, signal=signal_line, histogram=macd_line - signal_line)


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Wilder'ın RSI'ı — kazanç/kayıpların Wilder düzleştirmesi (ATR ile aynı yöntem)."""
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, float("nan"))
    result = 100.0 - (100.0 / (1.0 + rs))
    return result.where(avg_loss != 0.0, 100.0)  # kayıp yok -> RSI=100


@dataclass(frozen=True)
class Stochastic:
    k: pd.Series
    d: pd.Series


def stochastic(df: pd.DataFrame, k_window: int = 14, d_window: int = 3) -> Stochastic:
    lowest_low = df["low"].rolling(k_window).min()
    highest_high = df["high"].rolling(k_window).max()
    denom = (highest_high - lowest_low).replace(0.0, float("nan"))
    k = 100.0 * (df["close"] - lowest_low) / denom
    d = k.rolling(d_window).mean()
    return Stochastic(k=k, d=d)
