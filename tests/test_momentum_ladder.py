from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.momentum_ladder import Params, detect


def _df(close: np.ndarray) -> pd.DataFrame:
    n = len(close)
    return pd.DataFrame(
        {
            "time": pd.date_range("2024-01-01", periods=n, freq="1D", tz="UTC"),
            "open": close, "high": close + 0.3, "low": close - 0.3, "close": close,
            "volume": np.full(n, 1000.0),
        }
    )


def test_ustuste_artan_seri_long_uretir():
    close = np.linspace(100.0, 130.0, 40)
    df = _df(close)
    sigs = detect(df, Params())
    assert any(s.direction == 1 for s in sigs)


def test_ustuste_azalan_seri_short_uretir():
    close = np.linspace(130.0, 100.0, 40)
    df = _df(close)
    sigs = detect(df, Params())
    assert any(s.direction == -1 for s in sigs)


def test_yetersiz_bar_bos_liste():
    df = _df(np.full(10, 100.0))
    assert detect(df, Params()) == []
