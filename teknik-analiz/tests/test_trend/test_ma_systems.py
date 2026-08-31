"""trend.ma_systems testleri: kesişim, sıralama (stack) durumu, bant
sıkışma/genişleme + registry kaydı (repaint_test)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from tests.test_trend.fixtures import build_noisy_uptrend
from tlab.indicators.trend.ma_systems import MASystems, MASystemsParams


def test_crossover_signal_direction() -> None:
    # W-şekilli seri (aşağı-yukarı-aşağı-yukarı): SMA(2) SMA(4)'ü hem
    # yukarı hem aşağı en az bir kez kesmeli.
    close = np.concatenate(
        [
            np.linspace(120, 80, 15), np.linspace(80, 130, 15),
            np.linspace(130, 90, 15), np.linspace(90, 140, 15),
        ]
    )
    idx = pd.date_range("2024-01-02", periods=len(close), freq="1D", tz="Europe/Istanbul")
    ohlcv = pd.DataFrame(
        {"open": close, "high": close + 0.1, "low": close - 0.1, "close": close,
         "volume": np.full(len(close), 1000.0)},
        index=idx,
    )
    params = MASystemsParams(periods=(2, 4), ma_type="sma", squeeze_window=10)
    result = MASystems(params)(ohlcv)
    events = {s.payload["event"] for s in result.signals}
    assert "ma_cross_2_4_bull" in events
    assert "ma_cross_2_4_bear" in events


def test_stack_state_bull_when_perfectly_ascending() -> None:
    close = np.linspace(100, 300, 250)  # sürekli, güçlü yükseliş -> bull_stack beklenir
    idx = pd.date_range("2024-01-02", periods=len(close), freq="1D", tz="Europe/Istanbul")
    ohlcv = pd.DataFrame(
        {"open": close, "high": close + 0.1, "low": close - 0.1, "close": close,
         "volume": np.full(len(close), 1000.0)},
        index=idx,
    )
    params = MASystemsParams(periods=(5, 10, 20), squeeze_window=30)
    result = MASystems(params)(ohlcv)
    assert result.last_state["stack_state"] == "bull_stack"


def test_squeeze_expansion_signal_after_flat_then_breakout() -> None:
    flat = np.full(150, 100.0)
    breakout = 100.0 + np.arange(1, 40) * 2.0
    close = np.concatenate([flat, breakout])
    idx = pd.date_range("2024-01-02", periods=len(close), freq="1D", tz="Europe/Istanbul")
    ohlcv = pd.DataFrame(
        {"open": close, "high": close + 0.1, "low": close - 0.1, "close": close,
         "volume": np.full(len(close), 1000.0)},
        index=idx,
    )
    params = MASystemsParams(periods=(5, 10, 20), squeeze_window=50, squeeze_quantile=0.5)
    result = MASystems(params)(ohlcv)
    events = {s.payload["event"] for s in result.signals}
    assert "squeeze_expansion" in events


def test_signals_are_non_repaint_across_cuts() -> None:
    """`MASystems` `register_verified_elsewhere` kullanır (bkz. modül
    docstring'i — yalnızca büyüyen MA overlay `Line`'ı generic testi yanlış
    tetikler); SİNYALLERİN gerçek non-repaint'liği burada hedefli olarak
    doğrulanır: her kesim noktasında üretilen sinyaller, tam koşunun o ana
    kadar ürettiği sinyallerin AYNISI olmalı."""
    df = build_noisy_uptrend(n=300)
    indicator = MASystems()
    full = indicator(df)

    def key(s):
        return (s.bar_time, s.payload.get("event"))

    for cut in range(200, 300, 15):
        partial = indicator(df.iloc[:cut])
        cut_time = df.index[cut - 1]
        full_upto = {key(s) for s in full.signals if s.detected_at <= cut_time}
        partial_keys = {key(s) for s in partial.signals}
        assert partial_keys == full_upto, (cut, partial_keys ^ full_upto)
