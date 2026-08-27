"""tlab.features.oscillators için birim testleri ve repaint testi."""

from __future__ import annotations

import math
from dataclasses import dataclass
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from tlab.core.indicator import BaseIndicator
from tlab.core.params import BaseParams, params_hash
from tlab.core.types import IndicatorMeta, IndicatorResult, Signal, Timeframe
from tlab.features.ma import crossovers
from tlab.features.oscillators import macd, rsi, stochastic
from tlab.testing.repaint import repaint_test

TZ = ZoneInfo("Europe/Istanbul")


def _series(values: list[float]) -> pd.Series:
    idx = pd.date_range("2024-01-02 10:00", periods=len(values), freq="1D", tz=TZ)
    return pd.Series(values, index=idx)


# --- macd -------------------------------------------------------------


def test_macd_histogram_equals_macd_minus_signal() -> None:
    s = _series([100.0 + i * 0.5 for i in range(60)])
    result = macd(s, fast=6, slow=13, signal=5)
    diff = (result.macd - result.signal).dropna()
    hist = result.histogram.dropna()
    assert np.allclose(diff.to_numpy(), hist.to_numpy())


def test_macd_positive_in_sustained_uptrend() -> None:
    s = _series([100.0 + i * 1.0 for i in range(60)])
    result = macd(s, fast=6, slow=13, signal=5)
    assert result.macd.iloc[-1] > 0


# --- rsi -------------------------------------------------------------


def test_rsi_all_gains_is_100() -> None:
    s = _series([100.0 + i for i in range(20)])
    result = rsi(s, window=14)
    assert math.isclose(result.iloc[-1], 100.0)


def test_rsi_all_losses_is_0() -> None:
    s = _series([100.0 - i for i in range(20)])
    result = rsi(s, window=14)
    assert math.isclose(result.iloc[-1], 0.0)


# --- stochastic -------------------------------------------------------------


def test_stochastic_known_value() -> None:
    idx = pd.date_range("2024-01-02 10:00", periods=3, freq="1D", tz=TZ)
    df = pd.DataFrame(
        {
            "open": [9.0, 11.0, 10.0], "high": [10.0, 12.0, 11.0], "low": [8.0, 9.0, 7.0],
            "close": [9.0, 11.0, 10.0], "volume": [1000.0] * 3,
        },
        index=idx,
    )
    result = stochastic(df, k_window=3, d_window=2)
    # lowest_low=7, highest_high=12, denom=5, k=(10-7)/5*100=60
    assert math.isclose(result.k.iloc[2], 60.0)


# --- mini-indikatör repaint testi (MACD x sinyal kesişimi) ------------------


@dataclass(frozen=True)
class MacdCrossParams(BaseParams):
    fast: int = 6
    slow: int = 13
    signal: int = 5


class MacdCrossIndicator(BaseIndicator):
    """MACD çizgisinin sinyal çizgisini kestiği barlarda Signal üretir."""

    meta = IndicatorMeta(
        name="test.macd_cross",
        version="0.1.0",
        category="testing",
        description="Faz 2 oscillators.py (macd) + ma.py (crossovers) repaint kanıt sarmalayıcısı.",
        supported_timeframes=(Timeframe.D1, Timeframe.H4),
    )

    def __init__(self, params: MacdCrossParams | None = None) -> None:
        self.params = params or MacdCrossParams()

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        m = macd(df["close"], self.params.fast, self.params.slow, self.params.signal)
        cross = crossovers(m.macd, m.signal)

        signals: list[Signal] = []
        for t in df.index:
            direction = cross.loc[t]
            if pd.isna(direction):
                continue
            side = "long" if direction == "up" else "short"
            signals.append(Signal(t, t, side, "active", 1.0, {"macd": float(m.macd.loc[t])}))

        return IndicatorResult(
            indicator=self.meta.name, version=self.meta.version,
            params_hash=params_hash(self.params), symbol="TEST", timeframe=Timeframe.D1,
            signals=signals,
        )


def test_macd_cross_indicator_passes_repaint() -> None:
    rng = np.random.default_rng(9)
    idx = pd.date_range("2024-01-02 10:00", periods=100, freq="1D", tz=TZ)
    close = 100.0 + np.cumsum(rng.normal(0, 1.2, 100))
    df = pd.DataFrame(
        {"open": close, "high": close + 0.5, "low": close - 0.5, "close": close, "volume": 1000.0},
        index=idx,
    )
    report = repaint_test(MacdCrossIndicator(), df, tail=50)
    assert report.passed, report.mismatches
