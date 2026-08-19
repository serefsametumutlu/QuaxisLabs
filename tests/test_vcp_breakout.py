from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.vcp_breakout import Params, _pivot_points, detect
from src.analysis.abcd_pattern import pivot_low


def _df(close: np.ndarray, volume: np.ndarray | None = None) -> pd.DataFrame:
    n = len(close)
    return pd.DataFrame(
        {
            "time": pd.date_range("2024-01-01", periods=n, freq="1D", tz="UTC"),
            "open": close, "high": close + 0.3, "low": close - 0.3, "close": close,
            "volume": volume if volume is not None else np.full(n, 1000.0),
        }
    )


def test_pivot_points_bos_diziden_bos_liste_doner():
    assert _pivot_points(np.full(10, np.nan), 3) == []


def test_yetersiz_veri_bos_liste():
    df = _df(np.full(20, 100.0))
    assert detect(df, Params()) == []


def test_gercekci_seride_cokmeden_calisir():
    rng = np.random.RandomState(6)
    n = 400
    close = 100.0 * np.cumprod(1 + rng.normal(0.0008, 0.015, n))
    volume = np.abs(rng.normal(1_000_000, 200_000, n))
    df = _df(close, volume)
    sigs = detect(df, Params())
    assert isinstance(sigs, list)
    for s in sigs:
        assert s.direction == 1
        assert s.sl < s.entry_ref < s.tp1 < s.tp2
