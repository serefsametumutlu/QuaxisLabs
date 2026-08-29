"""tlab.features.xsec için birim testleri."""

from __future__ import annotations

import math
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from tlab.features.xsec import (
    fip,
    information_ratio,
    momentum_horizons,
    rank_pct,
    rolling_alpha_beta,
    rs_line,
)

TZ = ZoneInfo("Europe/Istanbul")


def _idx(n: int, start: str = "2024-01-02 10:00") -> pd.DatetimeIndex:
    return pd.date_range(start, periods=n, freq="1D", tz=TZ)


# --- rolling_alpha_beta ------------------------------------------------


def test_rolling_alpha_beta_recovers_known_alpha_beta() -> None:
    n = 200
    rng = np.random.default_rng(1)
    returns_m = pd.Series(rng.normal(0, 0.01, size=n), index=_idx(n))
    tiny_noise = rng.normal(0, 1e-8, size=n)
    returns_i = pd.Series(0.5 * returns_m.to_numpy() + 0.02 + tiny_noise, index=_idx(n))

    result = rolling_alpha_beta(returns_i, returns_m, window=50)
    assert result.alpha.iloc[-1] == pytest.approx(0.02, abs=1e-4)
    assert result.beta.iloc[-1] == pytest.approx(0.5, abs=1e-4)
    assert result.t_stat.iloc[-1] > 100  # neredeyse gürültüsüz fit -> çok büyük t


def test_rolling_alpha_beta_first_bars_are_nan() -> None:
    n = 60
    rng = np.random.default_rng(2)
    s = pd.Series(rng.normal(0, 0.01, size=n), index=_idx(n))
    result = rolling_alpha_beta(s, s, window=20)
    assert result.alpha.iloc[:19].isna().all()
    assert result.alpha.iloc[19:].notna().all()


def test_rolling_alpha_beta_aligns_on_common_index() -> None:
    n = 40
    idx_full = _idx(n)
    rng = np.random.default_rng(3)
    returns_i = pd.Series(rng.normal(0, 0.01, size=n), index=idx_full)
    returns_m = pd.Series(rng.normal(0, 0.01, size=n - 5), index=idx_full[5:])
    result = rolling_alpha_beta(returns_i, returns_m, window=10)
    assert len(result.alpha) == n - 5


def test_rolling_alpha_beta_prefix_consistent() -> None:
    n = 80
    rng = np.random.default_rng(4)
    returns_m = pd.Series(rng.normal(0, 0.01, size=n), index=_idx(n))
    returns_i = pd.Series(0.3 * returns_m.to_numpy() + rng.normal(0, 0.005, size=n), index=_idx(n))
    full = rolling_alpha_beta(returns_i, returns_m, window=20)
    cut = 50
    partial = rolling_alpha_beta(returns_i.iloc[:cut], returns_m.iloc[:cut], window=20)
    pd.testing.assert_series_equal(partial.alpha, full.alpha.iloc[:cut])
    pd.testing.assert_series_equal(partial.beta, full.beta.iloc[:cut])


# --- information_ratio ---------------------------------------------------


def test_information_ratio_positive_for_consistent_outperformance() -> None:
    n = 100
    rng = np.random.default_rng(5)
    returns_m = pd.Series(rng.normal(0, 0.01, size=n), index=_idx(n))
    returns_i = returns_m + 0.005 + rng.normal(0, 1e-6, size=n)
    ir = information_ratio(returns_i, returns_m, window=30, annualize=False)
    assert ir.iloc[-1] > 100  # sabit pozitif aktif getiri, ~sıfır std


def test_information_ratio_annualize_scales_by_sqrt_252() -> None:
    n = 60
    rng = np.random.default_rng(6)
    returns_m = pd.Series(rng.normal(0, 0.01, size=n), index=_idx(n))
    returns_i = returns_m + rng.normal(0.001, 0.01, size=n)
    raw = information_ratio(returns_i, returns_m, window=20, annualize=False)
    ann = information_ratio(returns_i, returns_m, window=20, annualize=True)
    ratio = (ann / raw).dropna()
    assert np.allclose(ratio.to_numpy(), math.sqrt(252))


# --- momentum_horizons -----------------------------------------------------


def test_momentum_horizons_known_geometric_growth() -> None:
    n = 100
    growth = 1.01
    prices = pd.Series([growth**t for t in range(n)], index=_idx(n))
    result = momentum_horizons(prices, horizons=(21,), skip=21)
    mom21 = result[21]
    assert mom21.iloc[-1] == pytest.approx(growth**21 - 1.0)


def test_momentum_horizons_returns_all_requested_keys() -> None:
    n = 300
    prices = pd.Series(100.0 + np.arange(n, dtype=float), index=_idx(n))
    result = momentum_horizons(prices, horizons=(21, 63, 126, 252), skip=21)
    assert set(result.keys()) == {21, 63, 126, 252}


# --- fip ---------------------------------------------------------------


def test_fip_perfectly_smooth_uptrend_is_minus_one() -> None:
    n = 30
    returns = pd.Series([0.01] * n, index=_idx(n))
    result = fip(returns, n=20)
    assert result.iloc[-1] == pytest.approx(-1.0)


def test_fip_choppier_uptrend_is_higher_than_smooth() -> None:
    n = 30
    smooth = pd.Series([0.01] * n, index=_idx(n))
    # net pozitif ama yarısı negatif gün -> daha "sıçramalı"
    choppy_vals = [0.05 if i % 2 == 0 else -0.03 for i in range(n)]
    choppy = pd.Series(choppy_vals, index=_idx(n))

    fip_smooth = fip(smooth, n=20).iloc[-1]
    fip_choppy = fip(choppy, n=20).iloc[-1]
    assert fip_choppy > fip_smooth


# --- rs_line -----------------------------------------------------------


def test_rs_line_simple_ratio() -> None:
    idx = _idx(5)
    price = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0], index=idx)
    index = pd.Series([100.0, 100.0, 100.0, 100.0, 100.0], index=idx)
    rs = rs_line(price, index)
    assert rs.iloc[0] == pytest.approx(0.10)
    assert rs.iloc[-1] == pytest.approx(0.14)


def test_rs_line_aligns_on_common_index() -> None:
    idx = _idx(10)
    price = pd.Series(range(10), index=idx, dtype=float)
    index = pd.Series(range(10), index=idx, dtype=float) + 1.0
    rs = rs_line(price.iloc[2:], index.iloc[:8])
    assert len(rs) == 6  # kesişim: [2,7]


# --- rank_pct -----------------------------------------------------------


def test_rank_pct_highest_value_is_zero() -> None:
    result = rank_pct({"A": 10.0, "B": 5.0, "C": 20.0})
    assert result["C"] == pytest.approx(0.0)
    assert result["A"] == pytest.approx(50.0)
    assert result["B"] == pytest.approx(100.0)


def test_rank_pct_ties_get_average_rank() -> None:
    result = rank_pct({"A": 10.0, "B": 10.0})
    assert result["A"] == pytest.approx(50.0)
    assert result["B"] == pytest.approx(50.0)


def test_rank_pct_single_symbol_is_zero() -> None:
    assert rank_pct({"A": 5.0}) == {"A": 0.0}


def test_rank_pct_empty_dict() -> None:
    assert rank_pct({}) == {}
