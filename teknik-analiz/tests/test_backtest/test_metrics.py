"""tlab.backtest.metrics — 11/DISIPLIN-12 (hız limiti), ORAN-08 (min Sharpe
eşiği)."""

from __future__ import annotations

import math

import pytest

from tlab.backtest.metrics import (
    MIN_SHARPE_THRESHOLD,
    SpeedLimitParams,
    min_sharpe_threshold,
    speed_limit_check,
)


def test_min_sharpe_threshold_exact_table_cells() -> None:
    for n_rules, year_table in MIN_SHARPE_THRESHOLD.items():
        for years, expected in year_table.items():
            assert min_sharpe_threshold(n_rules, years) == expected


def test_min_sharpe_threshold_rounds_up_to_next_defined_cell() -> None:
    # 3 kural -> tabloda tanımlı en yakın büyük satır 5; 7 yıl -> en yakın büyük 10.
    assert min_sharpe_threshold(3, 7) == MIN_SHARPE_THRESHOLD[5][10]


def test_min_sharpe_threshold_out_of_table_uses_largest_defined_cell() -> None:
    assert min_sharpe_threshold(500, 100) == MIN_SHARPE_THRESHOLD[100][30]


def test_speed_limit_matches_precise_fraction_not_book_rounded_display() -> None:
    """11/DISIPLIN-12: kitabın Euro Stoxx örneği görüntülenen 0.13/0.002=65
    diyor (2 ondalığa yuvarlanmış maliyet bütçesiyle) — TAM kesirle
    (1/3*0.40=0.1333...) doğru değer ~66.67'dir. Fonksiyonumuz TAM
    formülü uygular, kitabın yuvarlama artefaktını DEĞİL."""
    result = speed_limit_check(actual_roundtrips_per_year=60, cost_per_roundtrip_sr=0.002)
    assert result.cost_budget_sr_per_year == pytest.approx((1 / 3) * 0.40)
    assert result.speed_limit_roundtrips_per_year == pytest.approx(66.6667, abs=0.01)
    assert result.within_limit is True


def test_speed_limit_flags_overtrading() -> None:
    result = speed_limit_check(actual_roundtrips_per_year=500, cost_per_roundtrip_sr=0.002)
    assert result.within_limit is False
    assert result.actual_cost_sr_per_year == pytest.approx(1.0)


def test_speed_limit_zero_cost_gives_infinite_limit() -> None:
    result = speed_limit_check(actual_roundtrips_per_year=1000, cost_per_roundtrip_sr=0.0)
    assert math.isinf(result.speed_limit_roundtrips_per_year)
    assert result.within_limit is True


def test_speed_limit_semi_automatic_params() -> None:
    params = SpeedLimitParams(realistic_precost_sr=0.25)
    result = speed_limit_check(
        actual_roundtrips_per_year=10, cost_per_roundtrip_sr=0.002, params=params
    )
    assert result.cost_budget_sr_per_year == pytest.approx((1 / 3) * 0.25)
