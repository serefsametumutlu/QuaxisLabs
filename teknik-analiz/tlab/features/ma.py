"""Hareketli ortalamalar ve kesişim tespiti — hepsi yalnızca geçmişe bakar."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window).mean()


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def wma(series: pd.Series, window: int) -> pd.Series:
    """Doğrusal ağırlıklı hareketli ortalama (en yeni bar en ağır: 1..window)."""
    weights = np.arange(1, window + 1, dtype=float)
    return series.rolling(window).apply(
        lambda x: float(np.dot(x, weights) / weights.sum()), raw=True
    )


def hull(series: pd.Series, window: int) -> pd.Series:
    """Hull Moving Average: WMA(2*WMA(n/2) - WMA(n), round(sqrt(n)))."""
    half = max(1, round(window / 2))
    sqrt_w = max(1, round(math.sqrt(window)))
    raw = 2.0 * wma(series, half) - wma(series, window)
    return wma(raw, sqrt_w)


def crossovers(fast: pd.Series, slow: pd.Series) -> pd.Series:
    """Her barda kesişim yönü: fast slow'u yukarı kestiyse "up", aşağı
    kestiyse "down", aksi halde NaN (object dtype — pandas, boş object
    Series'i bile None yerine NaN ile doldurur; pd.isna() ile kontrol et)."""
    diff = fast - slow
    prev_diff = diff.shift(1)
    up = (diff > 0) & (prev_diff <= 0)
    down = (diff < 0) & (prev_diff >= 0)

    result = pd.Series(None, index=fast.index, dtype=object)
    result[up.fillna(False)] = "up"
    result[down.fillna(False)] = "down"
    return result
