"""tlab.features.stats için birim ve prefix-tutarlılık (repaint) testleri."""

from __future__ import annotations

import math
from dataclasses import dataclass
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from tlab.core.indicator import BaseIndicator
from tlab.core.params import BaseParams, params_hash
from tlab.core.types import IndicatorMeta, IndicatorResult, Signal, Timeframe
from tlab.features.stats import adf_pvalue, halflife, log_spread, rolling_beta, rolling_corr, zscore
from tlab.testing.repaint import repaint_test

TZ = ZoneInfo("Europe/Istanbul")


def _series(values: list[float]) -> pd.Series:
    idx = pd.date_range("2024-01-02 10:00", periods=len(values), freq="1D", tz=TZ)
    return pd.Series(values, index=idx)


# --- zscore -------------------------------------------------------------


def test_zscore_known_value() -> None:
    s = _series([1.0, 2.0, 3.0, 4.0, 5.0])
    z = zscore(s, window=3)
    assert z.iloc[:2].isna().all()
    assert math.isclose(z.iloc[2], 1.0)  # [1,2,3]: mean=2, std=1, (3-2)/1=1


# --- log_spread -----------------------------------------------------------


def test_log_spread_scalar_beta() -> None:
    y = _series([100.0, 110.0])
    x = _series([50.0, 55.0])
    spread = log_spread(y, x, beta=1.0)
    assert math.isclose(spread.iloc[0], math.log(100.0) - math.log(50.0))


# --- rolling_beta / rolling_corr -------------------------------------------


def test_rolling_beta_perfect_linear_relationship() -> None:
    x = _series([float(i) for i in range(1, 11)])
    y = 2.0 * x
    beta = rolling_beta(y, x, window=3)
    assert beta.iloc[2:].apply(lambda v: math.isclose(v, 2.0, abs_tol=1e-9)).all()


def test_rolling_corr_perfect_positive_relationship() -> None:
    x = _series([float(i) for i in range(1, 11)])
    y = 2.0 * x
    corr = rolling_corr(y, x, window=3)
    assert corr.iloc[2:].apply(lambda v: math.isclose(v, 1.0, abs_tol=1e-9)).all()


@pytest.mark.parametrize("cut", [5, 7, 9])
def test_rolling_beta_prefix_consistent(cut: int) -> None:
    rng = np.random.default_rng(3)
    x = _series(list(np.cumsum(rng.normal(0, 1, 10)) + 50))
    y = _series(list(2.0 * x.to_numpy() + rng.normal(0, 0.01, 10)))

    full = rolling_beta(y, x, window=3)
    partial = rolling_beta(y.iloc[:cut], x.iloc[:cut], window=3)
    pd.testing.assert_series_equal(partial, full.iloc[:cut])


# --- halflife ---------------------------------------------------------------


def test_halflife_known_ar1_decay() -> None:
    phi = 0.9
    values = [100.0 * phi**t for t in range(30)]
    spread = _series(values)
    hl = halflife(spread)
    expected = math.log(2) / (1 - phi)
    assert math.isclose(hl, expected, rel_tol=1e-6)


def test_halflife_non_mean_reverting_returns_inf() -> None:
    # phi>=1 benzeri: artan (ıraksak) seri -> lambda>=0 -> sonsuz yarı ömür
    values = [100.0 + 2.0 * t for t in range(20)]
    spread = _series(values)
    assert halflife(spread) == math.inf


def test_halflife_requires_enough_observations() -> None:
    with pytest.raises(ValueError):
        halflife(_series([100.0]))


# --- adf_pvalue -------------------------------------------------------------


def test_adf_pvalue_mean_reverting_series_is_low() -> None:
    rng = np.random.default_rng(11)
    n = 300
    phi = 0.5
    values = np.zeros(n)
    for t in range(1, n):
        values[t] = phi * values[t - 1] + rng.normal(0, 1)
    p = adf_pvalue(_series(list(values)))
    assert p < 0.05


def test_adf_pvalue_random_walk_is_high() -> None:
    rng = np.random.default_rng(11)
    n = 300
    values = np.cumsum(rng.normal(0, 1, n))
    p = adf_pvalue(_series(list(values)))
    assert p > 0.3


# --- mini-indikatör repaint testi (zscore eşik geçişi) ---------------------


@dataclass(frozen=True)
class ZScoreCrossParams(BaseParams):
    window: int = 10
    threshold: float = 1.0


class ZScoreCrossIndicator(BaseIndicator):
    """Rolling zscore eşiği aştığında Signal üretir — rolling() doğası
    gereği geriye bakan olduğundan non-repaint olmalı."""

    meta = IndicatorMeta(
        name="test.zscore_cross",
        version="0.1.0",
        category="testing",
        description="Faz 2 stats.py (zscore) repaint kanıt sarmalayıcısı.",
        supported_timeframes=(Timeframe.D1, Timeframe.H4),
    )

    def __init__(self, params: ZScoreCrossParams | None = None) -> None:
        self.params = params or ZScoreCrossParams()

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        z = zscore(df["close"], self.params.window)
        signals: list[Signal] = []
        for t in df.index[self.params.window :]:
            v = z.loc[t]
            if pd.isna(v):
                continue
            if v > self.params.threshold:
                signals.append(Signal(t, t, "short", "active", 1.0, {"z": float(v)}))
            elif v < -self.params.threshold:
                signals.append(Signal(t, t, "long", "active", 1.0, {"z": float(v)}))

        return IndicatorResult(
            indicator=self.meta.name, version=self.meta.version,
            params_hash=params_hash(self.params), symbol="TEST", timeframe=Timeframe.D1,
            signals=signals,
        )


def test_zscore_cross_indicator_passes_repaint() -> None:
    rng = np.random.default_rng(5)
    idx = pd.date_range("2024-01-02 10:00", periods=80, freq="1D", tz=TZ)
    close = 100.0 + np.cumsum(rng.normal(0, 1.0, 80))
    df = pd.DataFrame(
        {"open": close, "high": close + 0.5, "low": close - 0.5, "close": close, "volume": 1000.0},
        index=idx,
    )
    report = repaint_test(ZScoreCrossIndicator(), df, tail=40)
    assert report.passed, report.mismatches
