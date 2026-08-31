"""trend.ewmac testleri: forecast kırpma sınırı, sıfır-kesişim sinyali,
registry kaydı (repaint_test)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from tests.test_trend.fixtures import build_noisy_uptrend
from tlab.indicators.trend.ewmac import EWMACIndicator, EwmacParams
from tlab.testing.repaint import repaint_test


def test_forecast_bounded_by_cap() -> None:
    df = build_noisy_uptrend(n=400)
    params = EwmacParams(cap=20.0)
    result = EWMACIndicator(params)(df)
    combined = result.series["ewmac_combined"].dropna()
    assert (combined.abs() <= 20.0 + 1e-9).all()
    for name, series in result.series.items():
        if name.startswith("ewmac_") and name not in ("ewmac_combined", "ewmac_zero"):
            assert (series.dropna().abs() <= 20.0 + 1e-9).all(), name


def test_bullish_signal_fires_on_zero_upcross() -> None:
    # Uzun düşüş sonra güçlü yükseliş -> combined forecast negatiften pozitife geçmeli.
    down = np.linspace(200, 100, 200)
    up = np.linspace(100, 400, 250)
    close = np.concatenate([down, up])
    idx = pd.date_range("2024-01-02", periods=len(close), freq="1D", tz="Europe/Istanbul")
    ohlcv = pd.DataFrame(
        {"open": close, "high": close + 0.1, "low": close - 0.1, "close": close,
         "volume": np.full(len(close), 1000.0)},
        index=idx,
    )
    result = EWMACIndicator()(ohlcv)
    events = {s.payload["event"] for s in result.signals}
    assert "ewmac_bullish" in events


def test_registers_cleanly_with_repaint_test() -> None:
    df = build_noisy_uptrend(n=400)
    report = repaint_test(EWMACIndicator(), df, tail=40)
    assert report.passed, report.mismatches
