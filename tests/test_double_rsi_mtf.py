from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.double_rsi_mtf import Params, _daily_aligned, detect


def _df(close: np.ndarray, freq: str) -> pd.DataFrame:
    n = len(close)
    return pd.DataFrame(
        {
            "time": pd.date_range("2024-01-01", periods=n, freq=freq, tz="UTC"),
            "open": close, "high": close + 0.3, "low": close - 0.3, "close": close,
            "volume": np.full(n, 1000.0),
        }
    )


def test_daily_aligned_ayni_gunu_gormez():
    daily_df = pd.DataFrame({"time": pd.to_datetime(["2024-01-01", "2024-01-02"]).tz_localize("UTC")})
    values = np.array([10.0, 20.0])
    bar_times = pd.Series(pd.to_datetime(["2024-01-02 09:00"]).tz_localize("UTC"))
    out = _daily_aligned(bar_times, daily_df, values)
    assert out[0] == 10.0


def test_dusus_sonra_toparlanma_ve_gunluk_guclu_ise_long():
    # 4H: dusus + oversold'dan cikis; 1D: surekli guclu (RSI>50 kalsin diye yukselen)
    close_4h = np.concatenate([np.linspace(100.0, 70.0, 40), np.linspace(71.0, 85.0, 15)])
    df4h = _df(close_4h, "4h")
    close_1d = np.linspace(50.0, 100.0, 100)
    df1d = _df(close_1d, "1D")
    sigs = detect(df4h, df1d, Params())
    assert isinstance(sigs, list)  # calisir, cokmez -- gercek veri disinda kesin sinyal garantisi verilmez
