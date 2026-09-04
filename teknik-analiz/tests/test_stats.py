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
from tlab.features.stats import (
    adf_pvalue,
    benjamini_hochberg,
    engle_granger_pvalue,
    halflife,
    log_spread,
    ols_spread,
    rolling_beta,
    rolling_corr,
    zscore,
)
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


# --- engle_granger_pvalue (Faz 2, 2A) --------------------------------------


def test_engle_granger_pvalue_detects_cointegrated_pair() -> None:
    rng = np.random.default_rng(21)
    n = 300
    x = np.cumsum(rng.normal(0, 1, n)) + 50
    # y, x'in gürültülü bir katı -- gerçek bir kointegre çift
    y = 2.0 * x + rng.normal(0, 0.5, n)
    p = engle_granger_pvalue(_series(list(y)), _series(list(x)))
    assert p < 0.05


def test_engle_granger_pvalue_high_for_independent_random_walks() -> None:
    rng = np.random.default_rng(21)
    n = 300
    y = np.cumsum(rng.normal(0, 1, n)) + 50
    x = np.cumsum(rng.normal(0, 1, n)) + 50
    p = engle_granger_pvalue(_series(list(y)), _series(list(x)))
    assert p > 0.3


def test_engle_granger_pvalue_much_stricter_than_raw_adfuller() -> None:
    """Faz 2 tanısının (b) bulgusu: ham adfuller, TAHMİN EDİLMİŞ bir OLS
    kalıntısına uygulandığında engle_granger_pvalue'dan SİSTEMATİK olarak
    daha düşük (daha "durağan görünen") p döner -- iki BAĞIMSIZ rastgele
    yürüyüşte bile. Tek bir örneklemde bunu doğrudan kanıtlamak gürültülü
    olabilir, bu yüzden birkaç tohumun ORTALAMASI karşılaştırılır."""
    diffs = []
    for seed in range(30, 35):
        rng = np.random.default_rng(seed)
        n = 250
        y = np.cumsum(rng.normal(0, 1, n)) + 50
        x = np.cumsum(rng.normal(0, 1, n)) + 50
        y_s, x_s = _series(list(y)), _series(list(x))
        spread, _alpha, _beta = ols_spread(y_s, x_s)
        raw_p = adf_pvalue(spread)
        eg_p = engle_granger_pvalue(y_s, x_s)
        diffs.append(eg_p - raw_p)
    assert sum(diffs) / len(diffs) > 0  # engle_granger ORTALAMADA daha yüksek/gevşek değil sıkı


def test_engle_granger_pvalue_raises_for_too_few_observations() -> None:
    with pytest.raises(ValueError):
        engle_granger_pvalue(_series([1.0, 2.0]), _series([1.0, 2.0]))


# --- ols_spread (Faz 2, 2A) --------------------------------------------------


def test_ols_spread_recovers_known_alpha_beta() -> None:
    x = _series([float(i) for i in range(1, 51)])
    # log(y) = 0.3 + 1.5*log(x) tam olarak (gürültüsüz) -- spread sıfır, alpha/beta tam
    y = _series([math.exp(0.3 + 1.5 * math.log(i)) for i in range(1, 51)])
    spread, alpha, beta = ols_spread(y, x)
    assert math.isclose(alpha, 0.3, abs_tol=1e-6)
    assert math.isclose(beta, 1.5, abs_tol=1e-6)
    assert spread.abs().max() < 1e-6


def test_ols_spread_raises_for_constant_x() -> None:
    x = _series([5.0] * 10)
    y = _series([float(i) for i in range(1, 11)])
    with pytest.raises(ValueError):
        ols_spread(y, x)


# --- benjamini_hochberg (Faz 2, 2A) -----------------------------------------


def test_benjamini_hochberg_known_worked_example() -> None:
    """Elle hesaplanmış klasik bir BH-FDR örneği (m=10, q=0.05):
    sıralı p = [0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205,
    0.212, 0.216] -- eşikler k/10*0.05 = [.005,.01,.015,.02,.025,.03,
    .035,.04,.045,.05]. p_(k)<=eşik yalnızca k=1,2'de sağlanır (0.001<=.005,
    0.008<=.01) -- k=3'te 0.039>.015 (sağlanmıyor). BH kuralı EN BÜYÜK
    sağlayan k'yı alır -> yalnızca ilk 2 reddedilir."""
    pvalues = [0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.216]
    reject = benjamini_hochberg(pvalues, q=0.05)
    assert list(reject) == [True, True, False, False, False, False, False, False, False, False]


def test_benjamini_hochberg_all_pass_when_all_pvalues_tiny() -> None:
    pvalues = [0.001, 0.002, 0.003]
    reject = benjamini_hochberg(pvalues, q=0.05)
    assert all(reject)


def test_benjamini_hochberg_none_pass_when_all_pvalues_large() -> None:
    pvalues = [0.5, 0.6, 0.7]
    reject = benjamini_hochberg(pvalues, q=0.05)
    assert not any(reject)


def test_benjamini_hochberg_empty_input() -> None:
    assert list(benjamini_hochberg([], q=0.05)) == []


def test_benjamini_hochberg_more_lenient_than_bonferroni() -> None:
    """BH-FDR, AYNI q/alpha için Bonferroni'den her zaman EN AZ o kadar
    gevşektir (BH eşiği Bonferroni'nin q/m'sinden k arttıkça büyür)."""
    rng = np.random.default_rng(9)
    pvalues = rng.uniform(0, 0.1, 50)
    bh = benjamini_hochberg(pvalues, q=0.05)
    bonferroni = pvalues <= (0.05 / len(pvalues))
    assert bh.sum() >= bonferroni.sum()
    assert all(b for b, is_bonf in zip(bh, bonferroni, strict=True) if is_bonf)


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
