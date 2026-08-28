"""Faz 5 (pair) testleri için paylaşılan sentetik OHLCV fixture'ları.

Tüm sabitler gerçek kod çalıştırılarak doğrulanmıştır (bkz. aynı ilke
tests/test_harmonics/test_schools.py'de) — sayılar SONUÇ, türetme süreci
değil.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

_TZ = "Europe/Istanbul"


def build_cointegrated_pair(
    n: int = 500, seed: int = 11, base_vol: float = 0.015,
    shock_amp: float = 0.3, shock_period: float = 100.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Y ve X, ORTAK bir random walk ("base") paylaşır (bu yüzden eşbütünleşik
    davranır — beta≈sabit); Y'ye ayrıca yumuşak bir sinüs "spread şoku"
    eklenir. Bu, spread'in periyodik olarak ±k eşiklerini aşıp geri dönmesini
    (hem "Y AL" hem "X AL" sinyalini) garanti eden KONTROLLÜ bir kurulumdur.
    Varsayılan parametrelerle (RelativeMomentumParams(window=40, k=2.0,
    beta_method='one', beta_window=200, min_periods=200)) tam olarak 5
    alternatif sinyal üretir (bkz. test_relative_momentum.py)."""
    rng = np.random.default_rng(seed)
    base = np.cumsum(rng.normal(0, base_vol, n))
    t = np.arange(n)
    shock = shock_amp * np.sin(2 * np.pi * t / shock_period)

    y_log = base + shock
    x_log = base.copy()
    y_close = 100.0 * np.exp(y_log)
    x_close = 50.0 * np.exp(x_log)

    index = pd.date_range("2024-01-01", periods=n, freq="D", tz=_TZ)
    return _ohlcv(y_close, index), _ohlcv(x_close, index)


def _ohlcv(close: np.ndarray, index: pd.DatetimeIndex) -> pd.DataFrame:
    open_ = np.empty_like(close)
    open_[0] = close[0]
    open_[1:] = close[:-1]
    high = np.maximum(open_, close) + 0.05
    low = np.minimum(open_, close) - 0.05
    volume = np.full(len(close), 1000.0)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume}, index=index
    )
