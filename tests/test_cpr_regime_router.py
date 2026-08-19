from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.cpr_regime_router import Params, detect


def _df(n: int, rng: np.random.RandomState) -> pd.DataFrame:
    close = 100.0 * np.cumprod(1 + rng.normal(0.0005, 0.01, n))
    open_ = close * (1 + rng.normal(0, 0.002, n))
    high = np.maximum(open_, close) * 1.005
    low = np.minimum(open_, close) * 0.995
    return pd.DataFrame(
        {
            "time": pd.date_range("2023-01-01", periods=n, freq="1D", tz="UTC"),
            "open": open_, "high": high, "low": low, "close": close,
            "volume": np.full(n, 1000.0),
        }
    )


def test_calisir_ve_gecerli_sinyaller_uretir():
    df = _df(400, np.random.RandomState(1))
    sigs = detect(df, Params())
    assert isinstance(sigs, list)
    for s in sigs:
        assert s.cpr_regime in ("DAR_MOMENTUM", "GENIS_ORTALAMAYA_DONUS")
        assert s.sl < s.entry_ref < s.tp1 <= s.tp2 or s.sl < s.entry_ref  # temel tutarlilik


def test_yetersiz_veri_bos_liste():
    df = _df(5, np.random.RandomState(2))
    assert detect(df, Params()) == []
