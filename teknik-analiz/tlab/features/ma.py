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


def kama(series: pd.Series, er_window: int = 10, fast: int = 2, slow: int = 30) -> pd.Series:
    """Kaufman Adaptive Moving Average (Faz 8D, ch1 STRAT atfı).

    Verimlilik oranı (efficiency ratio) ER = |net değişim| / toplam mutlak
    değişim (er_window penceresinde) — trend güçlüyse ER~1 (hızlı MA'ya
    yakın davranır), yatay/gürültülüyse ER~0 (yavaş MA'ya yakın davranır).
    Smoothing constant SC = (ER*(fast_sc-slow_sc)+slow_sc)^2, fast_sc/slow_sc
    klasik EMA span->alpha dönüşümüyle (2/(n+1)). KAMA[t] = KAMA[t-1] +
    SC[t]*(close[t]-KAMA[t-1]) — özyinelemeli ama yalnızca t-1 ve öncesini
    kullanır (non-repaint); ilk değer er_window'daki ilk kapanışa sabitlenir."""
    change = (series - series.shift(er_window)).abs()
    volatility = series.diff().abs().rolling(er_window).sum()
    er = (change / volatility.replace(0.0, np.nan)).fillna(0.0)
    fast_sc = 2.0 / (fast + 1)
    slow_sc = 2.0 / (slow + 1)
    sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2

    values = np.full(len(series), np.nan)
    if len(series) > er_window:
        values[er_window] = series.iloc[er_window]
        sc_arr = sc.to_numpy()
        close_arr = series.to_numpy()
        for i in range(er_window + 1, len(series)):
            values[i] = values[i - 1] + sc_arr[i] * (close_arr[i] - values[i - 1])
    return pd.Series(values, index=series.index)


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
