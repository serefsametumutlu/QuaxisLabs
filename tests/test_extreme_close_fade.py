from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.extreme_close_fade import Params, detect


def _df(close: np.ndarray) -> pd.DataFrame:
    n = len(close)
    return pd.DataFrame(
        {
            "time": pd.date_range("2024-01-01", periods=n, freq="1D", tz="UTC"),
            "open": close, "high": close + 0.3, "low": close - 0.3, "close": close,
            "volume": np.full(n, 1000.0),
        }
    )


def test_yeni_zirve_kapanis_short_uretir():
    close = np.concatenate([np.full(20, 100.0), np.linspace(101.0, 115.0, 12)])
    df = _df(close)
    sigs = detect(df, Params(short_lookback=8, long_lookback=10))
    assert any(s.direction == -1 for s in sigs)


def test_yeni_dip_kapanis_long_uretir():
    close = np.concatenate([np.full(20, 100.0), np.linspace(99.0, 85.0, 12)])
    df = _df(close)
    sigs = detect(df, Params(short_lookback=8, long_lookback=10))
    assert any(s.direction == 1 for s in sigs)
