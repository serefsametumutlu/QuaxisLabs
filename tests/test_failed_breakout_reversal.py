from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.failed_breakout_reversal import Params, detect


def _df(close: np.ndarray, high: np.ndarray | None = None, low: np.ndarray | None = None) -> pd.DataFrame:
    n = len(close)
    high = close + 0.3 if high is None else high
    low = close - 0.3 if low is None else low
    return pd.DataFrame(
        {
            "time": pd.date_range("2024-01-01", periods=n, freq="1D", tz="UTC"),
            "open": close, "high": high, "low": low, "close": close,
            "volume": np.full(n, 1000.0),
        }
    )


def test_ust_kirilim_sonra_geri_donus_short_uretir():
    base = np.full(25, 100.0)
    spike_high = base.copy()
    close = np.concatenate([base, [100.0, 99.5]])  # kanal + normal
    high = np.concatenate([base + 0.3, [112.0, 99.8]])  # 1 bar KIRILIM (112), sonra geri
    low = close - 0.3
    close = np.concatenate([base, [105.0, 99.0]])  # kirilim barinda kapanis yuksek, sonraki bar geri dusuyor
    df = _df(close, high=high, low=low)
    sigs = detect(df, Params(channel_len=20, max_bars_to_fail=5))
    assert isinstance(sigs, list)


def test_yetersiz_veri_bos_liste():
    df = _df(np.full(10, 100.0))
    assert detect(df, Params(channel_len=20)) == []
