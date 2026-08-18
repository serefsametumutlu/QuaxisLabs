"""src/analysis/momentum_confluence_factors.py testleri."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.momentum_confluence_factors import ALL_FEATURES, extract_features


def _ohlcv(n: int) -> pd.DataFrame:
    close = 100.0 + np.cumsum(np.sin(np.linspace(0, 10, n)))
    return pd.DataFrame(
        {
            "time": pd.date_range("2024-01-01", periods=n, freq="1D", tz="UTC"),
            "open": close - 0.3,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": np.full(n, 1000.0),
        }
    )


def test_extract_features_tum_anahtarlari_uretir():
    df = _ohlcv(250)
    row = {
        "sig_signal_bar": 220,
        "sig_ema_spread_pct": 0.5,
        "sig_volume_ratio": 2.1,
        "sig_downward_streak_before_flip": 12,
        "sig_wt1_at_signal": np.nan,  # V1 sinyali -- her zaman NaN
    }
    feats = extract_features(row, df)
    assert set(feats.keys()) == set(ALL_FEATURES)
    assert feats["wt1_at_signal"] is None  # NaN -> None cevrimi
    assert feats["ema_spread_pct"] == 0.5
    assert feats["rsi14"] is not None
    assert feats["above_sma200"] in (0, 1)


def test_extract_features_look_ahead_yok():
    """signal_bar SONRASINDAKI barlar gostergeleri ETKILEMEMELI -- ayni
    df'i signal_bar+1'e kadar kirpip ayni sonucu almaliyiz."""
    df = _ohlcv(250)
    row = {
        "sig_signal_bar": 100,
        "sig_ema_spread_pct": 0.3,
        "sig_volume_ratio": 1.8,
        "sig_downward_streak_before_flip": 5,
        "sig_wt1_at_signal": -3.2,
    }
    full = extract_features(row, df)
    truncated = extract_features(row, df.iloc[:101].reset_index(drop=True))
    assert full["rsi14"] == truncated["rsi14"]
    assert full["adx14"] == truncated["adx14"]
