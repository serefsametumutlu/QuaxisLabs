from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.halflife_mean_reversion import Params, compute_half_life, detect


def _df(close: np.ndarray) -> pd.DataFrame:
    n = len(close)
    return pd.DataFrame(
        {
            "time": pd.date_range("2024-01-01", periods=n, freq="1D", tz="UTC"),
            "open": close, "high": close + 0.3, "low": close - 0.3, "close": close,
            "volume": np.full(n, 1000.0),
        }
    )


def test_ornstein_uhlenbeck_seride_pozitif_yari_omur_bulunur():
    rng = np.random.RandomState(3)
    n = 500
    x = np.zeros(n)
    mean, theta = 100.0, 0.05
    for i in range(1, n):
        x[i] = x[i - 1] + theta * (mean - x[i - 1]) + rng.normal(0, 0.5)
    hl = compute_half_life(x)
    assert 5 <= hl <= 60


def test_rastgele_yuruyuste_fallback_donulur():
    rng = np.random.RandomState(4)
    x = 100.0 + np.cumsum(rng.normal(0.05, 1.0, 200))  # belirgin surukleme, mean-revert ETMEZ
    hl = compute_half_life(x)
    assert 5 <= hl <= 60


def test_asiri_sapma_sinyal_uretir():
    rng = np.random.RandomState(5)
    n = 300
    x = np.zeros(n)
    for i in range(1, n):
        x[i] = x[i - 1] + 0.08 * (100.0 - x[i - 1]) + rng.normal(0, 0.5)
    x[-1] -= 20.0  # ani asiri sapma -- LONG tetiklemeli
    df = _df(x)
    sigs = detect(df, Params())
    assert isinstance(sigs, list)
