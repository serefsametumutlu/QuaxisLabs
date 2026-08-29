"""tlab.features.hs_pattern için birim testleri + hypothesis tabanlı
"kesik seri sonuçları ⊆ tam seri sonuçları" özellik testi (find_hs)."""

from __future__ import annotations

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tlab.features.hs_pattern import HSPattern, find_hs, neckline_value_at
from tlab.features.swings import Pivot, alternate_pivots, find_pivots
from tlab.testing.fixtures import make_trend


def _pivot(bar_idx: int, price: float, kind: str, confirmed_offset: int = 2) -> Pivot:
    return Pivot(
        bar_idx=bar_idx,
        bar_time=pd.Timestamp("2024-01-01") + pd.Timedelta(days=bar_idx),
        price=price,
        kind=kind,  # type: ignore[arg-type]
        confirmed_idx=bar_idx + confirmed_offset,
        confirmed_time=pd.Timestamp("2024-01-01") + pd.Timedelta(days=bar_idx + confirmed_offset),
    )


def _tobo_pivots() -> list[Pivot]:
    return [
        _pivot(0, 90.0, "low"),
        _pivot(5, 100.0, "high"),
        _pivot(10, 80.0, "low"),  # head — en düşük
        _pivot(15, 101.0, "high"),
        _pivot(20, 91.0, "low"),
    ]


def _obo_pivots() -> list[Pivot]:
    return [
        _pivot(0, 110.0, "high"),
        _pivot(5, 100.0, "low"),
        _pivot(10, 130.0, "high"),  # head — en yüksek
        _pivot(15, 99.0, "low"),
        _pivot(20, 109.0, "high"),
    ]


# --- TOBO ----------------------------------------------------------------


def test_find_hs_tobo_detects_pattern_with_correct_geometry() -> None:
    patterns = find_hs(_tobo_pivots(), kind="tobo")
    assert len(patterns) == 1
    p = patterns[0]
    assert p.kind == "tobo"
    assert p.l1.price == 90.0 and p.l3.price == 91.0
    assert p.head.price == 80.0
    assert p.neckline_slope == pytest.approx(0.1)
    assert p.depth == pytest.approx(20.5)
    assert p.target == pytest.approx(122.0)
    assert p.created_idx == p.l3.confirmed_idx == 22


def test_neckline_value_at_passes_through_h1_and_h2() -> None:
    p = find_hs(_tobo_pivots(), kind="tobo")[0]
    assert neckline_value_at(p, p.h1.bar_idx) == pytest.approx(p.h1.price)
    assert neckline_value_at(p, p.h2.bar_idx) == pytest.approx(p.h2.price)


def test_find_hs_tobo_head_not_deepest_rejected() -> None:
    pivots = _tobo_pivots()
    # head'i sığlaştır (artık l1/l3'ten daha düşük değil)
    pivots[2] = _pivot(10, 95.0, "low")
    assert find_hs(pivots, kind="tobo") == []


def test_find_hs_neck_slope_too_steep_rejected() -> None:
    pivots = _tobo_pivots()
    pivots[3] = _pivot(15, 140.0, "high")  # boyun artık çok eğik
    assert find_hs(pivots, kind="tobo", neck_slope_max=0.01) == []


def test_find_hs_asymmetric_shoulders_rejected() -> None:
    pivots = _tobo_pivots()
    pivots[4] = _pivot(20, 60.0, "low")  # sağ omuz çok daha derin, simetri bozuk
    assert find_hs(pivots, kind="tobo", sym_tol=0.1) == []


def test_find_hs_wrong_kind_sequence_no_match() -> None:
    """obo pivotları tobo aranınca bulunamaz."""
    assert find_hs(_obo_pivots(), kind="tobo") == []


# --- OBO -------------------------------------------------------------------


def test_find_hs_obo_detects_pattern_with_correct_geometry() -> None:
    patterns = find_hs(_obo_pivots(), kind="obo")
    assert len(patterns) == 1
    p = patterns[0]
    assert p.kind == "obo"
    assert p.head.price == 130.0
    assert p.neckline_slope == pytest.approx(-0.1)
    assert p.depth == pytest.approx(30.5)
    assert p.target == pytest.approx(68.0)


def test_find_hs_invalid_kind_raises() -> None:
    with pytest.raises(ValueError):
        find_hs(_tobo_pivots(), kind="up")  # type: ignore[arg-type]


def test_find_hs_short_pivot_list_returns_empty() -> None:
    assert find_hs(_tobo_pivots()[:4], kind="tobo") == []


# --- prefix/subset özelliği (hypothesis) ------------------------------------


def _pattern_key(p: HSPattern) -> tuple[int, int, int, int]:
    return (p.l1.bar_idx, p.head.bar_idx, p.l3.bar_idx, p.created_idx)


@given(
    n=st.integers(min_value=60, max_value=150),
    seed=st.integers(min_value=0, max_value=3000),
)
@settings(max_examples=25, deadline=None)
def test_find_hs_prefix_results_are_subset_of_full(n: int, seed: int) -> None:
    """Yalnızca daha ERKEN onaylanmış pivotlarla bulunan HSPattern'ler, TÜM
    pivotlarla bulunanların bir ALT KÜMESİDİR — sonradan gelen pivotlar
    geçmişte zaten tespit edilmiş bir paterni asla YOK ETMEZ/DEĞİŞTİRMEZ."""
    df = make_trend(n=n, slope=0.0, noise=2.0, seed=seed)
    raw = find_pivots(df, left=2, right=2)
    zigzag = alternate_pivots(raw)
    if len(zigzag) < 5:
        return

    cut_confirmed = zigzag[len(zigzag) // 2].confirmed_idx
    partial_pivots = [p for p in zigzag if p.confirmed_idx <= cut_confirmed]

    # Gevşek eşikler: daha çok aday üretip özelliği daha sık egzersiz eder.
    full = find_hs(zigzag, kind="tobo", sym_tol=2.0, neck_slope_max=1.0)
    partial = find_hs(partial_pivots, kind="tobo", sym_tol=2.0, neck_slope_max=1.0)

    full_keys = {_pattern_key(p) for p in full}
    for p in partial:
        assert _pattern_key(p) in full_keys
