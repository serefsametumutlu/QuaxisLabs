"""tlab.indicators.harmonics.prz için birim testleri."""

from __future__ import annotations

import math

from tests.test_harmonics.fixtures import make_candidate
from tlab.indicators.harmonics.prz import compute_prz, project_ratio


def test_compute_prz_single_pm_tol() -> None:
    cand = make_candidate(100.0, 120.0, 107.64, 116.64)
    prz = compute_prz(cand, (("xa_ret", 0.756, 0.816),), "single_pm_tol")
    assert prz is not None
    assert math.isclose(prz.low, 103.68, abs_tol=1e-9)
    assert math.isclose(prz.high, 104.88, abs_tol=1e-9)
    assert math.isclose(prz.center, 104.28, abs_tol=1e-9)


def test_compute_prz_intersection_overlapping() -> None:
    cand = make_candidate(100.0, 120.0, 107.64, 116.64)
    prz = compute_prz(cand, (("xa_ret", 0.756, 0.816), ("bc_ext", 1.13, 1.618)), "intersection")
    assert prz is not None
    assert prz.low <= prz.center <= prz.high


def test_compute_prz_intersection_non_overlapping_returns_none() -> None:
    cand = make_candidate(100.0, 120.0, 109.0, 123.3)  # nenstar fixture
    # Kasıtlı olarak Carney'nin gartley bileşenleriyle dener (uyuşmayan bantlar)
    prz = compute_prz(cand, (("xa_ret", 0.756, 0.816), ("bc_ext", 5.0, 6.0)), "intersection")
    assert prz is None


def test_compute_prz_empty_components_returns_none() -> None:
    cand = make_candidate(100.0, 120.0, 107.64, 116.64)
    assert compute_prz(cand, (), "single_pm_tol") is None


def test_project_ratio_matches_compute_prz_band_edges() -> None:
    cand = make_candidate(100.0, 120.0, 107.64, 116.64)
    at_756 = project_ratio(cand, "xa_ret", 0.756)
    at_816 = project_ratio(cand, "xa_ret", 0.816)
    assert math.isclose(at_756, 104.88, abs_tol=1e-9)
    assert math.isclose(at_816, 103.68, abs_tol=1e-9)


def test_abcd_leg_uses_classic_projection_formula() -> None:
    # D = C + ratio*(B-A)
    cand = make_candidate(100.0, 120.0, 94.56, 112.368)  # three_drives fixture
    d = project_ratio(cand, "abcd", 1.272)
    expected = 112.368 + 1.272 * (94.56 - 120.0)
    assert math.isclose(d, expected, abs_tol=1e-6)
