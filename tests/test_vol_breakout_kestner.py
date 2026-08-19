from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.vol_breakout_kestner import Params, detect


def _df(close: np.ndarray) -> pd.DataFrame:
    n = len(close)
    return pd.DataFrame(
        {
            "time": pd.date_range("2024-01-01", periods=n, freq="1D", tz="UTC"),
            "open": close, "high": close + 0.3, "low": close - 0.3, "close": close,
            "volume": np.full(n, 1000.0),
        }
    )


def test_ani_sicrama_long_tetikler():
    close = np.concatenate([np.full(30, 100.0), [112.0]])  # ATR dusuk, sonra buyuk sicrama
    df = _df(close)
    sigs = detect(df, Params(vol_mult=1.0))
    assert any(s.direction == 1 for s in sigs)
    sig = [s for s in sigs if s.direction == 1][-1]
    assert sig.sl < sig.entry_ref < sig.tp1 < sig.tp2


def test_duz_seride_sinyal_yok():
    close = np.full(30, 100.0)
    df = _df(close)
    assert detect(df, Params()) == []
