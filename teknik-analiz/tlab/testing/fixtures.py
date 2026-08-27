"""Deterministik sentetik OHLCV üreticiler (test/fixture amaçlı, üretim kodu değil)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from tlab.core.types import Timeframe

_TZ = "Europe/Istanbul"

_TF_FREQ: dict[Timeframe, str] = {
    Timeframe.H4: "4h",
    Timeframe.D1: "1D",
}


def _make_index(n: int, timeframe: Timeframe, start: str = "2024-01-02 10:00") -> pd.DatetimeIndex:
    return pd.date_range(start=start, periods=n, freq=_TF_FREQ[timeframe], tz=_TZ)


def _ohlc_from_close(
    close: np.ndarray, index: pd.DatetimeIndex, noise: float, seed: int
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    wick = np.abs(rng.normal(0, noise, size=len(close))) + 1e-6
    open_ = np.empty_like(close)
    open_[0] = close[0]
    open_[1:] = close[:-1]
    high = np.maximum(open_, close) + wick
    low = np.minimum(open_, close) - wick
    volume = rng.uniform(1_000, 10_000, size=len(close))
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=index,
    )


def make_trend(
    n: int = 200,
    slope: float = 0.1,
    noise: float = 0.5,
    timeframe: Timeframe = Timeframe.D1,
    start_price: float = 100.0,
    seed: int = 42,
) -> pd.DataFrame:
    """Doğrusal trend + küçük gürültü içeren sentetik OHLCV serisi."""
    rng = np.random.default_rng(seed)
    trend = start_price + slope * np.arange(n)
    close = trend + rng.normal(0, noise, size=n)
    index = _make_index(n, timeframe)
    return _ohlc_from_close(close, index, noise=max(noise, 1e-3), seed=seed + 1)


def make_zigzag(
    pivots: list[tuple[int, float]],
    noise: float = 0.05,
    timeframe: Timeframe = Timeframe.D1,
    seed: int = 7,
) -> pd.DataFrame:
    """Verilen (bar_idx, price) pivot noktalarını kesin içeren, aralarda
    lineer interpolasyon + küçük gürültülü seri üretir."""
    if len(pivots) < 2:
        raise ValueError("En az iki pivot noktası gerekli")
    ordered = sorted(pivots, key=lambda p: p[0])
    n = ordered[-1][0] + 1
    close = np.empty(n)
    for (i0, p0), (i1, p1) in zip(ordered[:-1], ordered[1:]):
        span = i1 - i0
        close[i0 : i1 + 1] = np.linspace(p0, p1, span + 1)

    rng = np.random.default_rng(seed)
    close = close + rng.normal(0, noise, size=n)
    for idx, price in ordered:
        close[idx] = price

    index = _make_index(n, timeframe)
    return _ohlc_from_close(close, index, noise=noise, seed=seed + 1)


def make_harmonic(
    pattern_ratios: dict[str, float],
    bullish: bool,
    x_price: float = 100.0,
    xa_length: float = 20.0,
    bar_spacing: int = 10,
    timeframe: Timeframe = Timeframe.D1,
    seed: int = 13,
) -> pd.DataFrame:
    """Verilen XA, AB/XA, BC/AB, CD/BC oranlarıyla X,A,B,C,D barlarını
    kesin olarak içeren sentetik seri üretir (Faz 3'te kullanılacak).

    pattern_ratios anahtarları: 'ab_xa', 'bc_ab', 'cd_bc'.
    """
    sign = 1.0 if bullish else -1.0
    x = x_price
    a = x + sign * xa_length
    ab = pattern_ratios["ab_xa"] * xa_length
    b = a - sign * ab
    bc = pattern_ratios["bc_ab"] * ab
    c = b + sign * bc
    cd = pattern_ratios["cd_bc"] * bc
    d = c - sign * cd

    pivots = [
        (0, x),
        (bar_spacing, a),
        (2 * bar_spacing, b),
        (3 * bar_spacing, c),
        (4 * bar_spacing, d),
    ]
    return make_zigzag(pivots, noise=0.02, timeframe=timeframe, seed=seed)
