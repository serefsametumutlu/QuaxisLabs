"""tlab.features.fibonacci için birim testleri (saf aritmetik, veri bağımsız)."""

from __future__ import annotations

import math

from tlab.features.fibonacci import extension, projection_abcd, ratio, retracement, within


def test_retracement_up_move_levels_below_p1() -> None:
    levels = retracement(100.0, 200.0, levels=(0.0, 0.5, 1.0))
    assert math.isclose(levels[0.0], 200.0)
    assert math.isclose(levels[0.5], 150.0)
    assert math.isclose(levels[1.0], 100.0)


def test_retracement_down_move_levels_above_p1() -> None:
    levels = retracement(200.0, 100.0, levels=(0.0, 0.618, 1.0))
    assert math.isclose(levels[0.0], 100.0)
    assert math.isclose(levels[1.0], 200.0)
    assert 100.0 < levels[0.618] < 200.0


def test_extension_levels_beyond_p1() -> None:
    levels = extension(100.0, 150.0, levels=(1.0, 1.618, 2.0))
    assert math.isclose(levels[1.0], 150.0)
    assert math.isclose(levels[2.0], 200.0)
    assert 150.0 < levels[1.618] < 200.0


def test_projection_abcd_classic_ab_equals_cd() -> None:
    # A=100, B=150 (AB=50), C=120 -> D adayı (ratio=1.0) = 120+50=170
    d = projection_abcd(100.0, 150.0, 120.0, ratios=(1.0,))
    assert math.isclose(d[1.0], 170.0)


def test_ratio_basic() -> None:
    assert math.isclose(ratio(100.0, 150.0, 175.0), 0.5)  # BC=25, AB=50


def test_ratio_zero_ab_returns_zero() -> None:
    assert ratio(100.0, 100.0, 150.0) == 0.0


def test_within_absolute_tolerance() -> None:
    assert within(105.0, 100.0, 110.0, tol=0.0)
    assert not within(95.0, 100.0, 110.0, tol=4.0)
    assert within(96.0, 100.0, 110.0, tol=5.0)


def test_within_relative_tolerance() -> None:
    # aralık genişliği 10, tol=0.1 -> pay=1 -> [99, 111]
    assert within(99.5, 100.0, 110.0, tol=0.1, tol_kind="rel")
    assert not within(98.0, 100.0, 110.0, tol=0.1, tol_kind="rel")


def test_within_handles_reversed_bounds() -> None:
    assert within(105.0, 110.0, 100.0)
