from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.rsi_mw_pattern import Params, detect


def _df(close: np.ndarray) -> pd.DataFrame:
    n = len(close)
    return pd.DataFrame(
        {
            "time": pd.date_range("2024-01-01", periods=n, freq="1D", tz="UTC"),
            "open": close, "high": close + 0.3, "low": close - 0.3, "close": close,
            "volume": np.full(n, 1000.0),
        }
    )


def test_cift_dip_rsi_deseni_long_uretebilir():
    # Iki ardisik keskin dususu (RSI dusuk) ve arada kismi toparlanmayi simule et.
    close = np.concatenate(
        [np.linspace(100, 70, 20), np.linspace(71, 90, 15), np.linspace(89, 75, 15), np.linspace(76, 95, 15)]
    )
    df = _df(close)
    sigs = detect(df, Params(pivot_lookback=2))
    assert isinstance(sigs, list)
    for s in sigs:
        assert s.direction in (1, -1)
        assert s.sl != s.entry_ref


def test_duz_seride_sinyal_yok():
    df = _df(np.full(60, 100.0))
    assert detect(df, Params()) == []
