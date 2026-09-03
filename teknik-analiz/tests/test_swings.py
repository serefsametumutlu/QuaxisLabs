"""tlab.features.swings için birim testleri (find_pivots, alternate_pivots,
label_structure, atr_zigzag) ve non-repaint property testi."""

from __future__ import annotations

import math

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tlab.features.swings import (
    Pivot,
    alternate_pivots,
    atr_zigzag,
    find_pivots,
    label_structure,
    significant_pivots,
)
from tlab.testing.fixtures import make_trend, make_zigzag


def _mk(bar_idx: int, price: float, kind: str, confirmed_idx: int) -> Pivot:
    return Pivot(
        bar_idx=bar_idx,
        bar_time=pd.Timestamp("2024-01-01") + pd.Timedelta(days=bar_idx),
        price=price,
        kind=kind,  # type: ignore[arg-type]
        confirmed_idx=confirmed_idx,
        confirmed_time=pd.Timestamp("2024-01-01") + pd.Timedelta(days=confirmed_idx),
    )


# --- find_pivots -------------------------------------------------------


def test_find_pivots_detects_known_pivots_at_correct_bars() -> None:
    pivots = [(0, 100.0), (20, 130.0), (40, 90.0), (60, 150.0), (80, 80.0)]
    df = make_zigzag(pivots, noise=0.0)
    left = right = 5

    result = find_pivots(df, left, right)
    by_idx = {(p.bar_idx, p.kind): p for p in result}

    assert (20, "high") in by_idx
    assert math.isclose(by_idx[(20, "high")].price, 130.0, abs_tol=1e-2)
    assert by_idx[(20, "high")].confirmed_idx == 25

    assert (40, "low") in by_idx
    assert math.isclose(by_idx[(40, "low")].price, 90.0, abs_tol=1e-2)
    assert by_idx[(40, "low")].confirmed_idx == 45

    assert (60, "high") in by_idx
    assert by_idx[(60, "high")].confirmed_idx == 65


def test_find_pivots_no_pivot_in_last_right_bars() -> None:
    pivots = [(0, 100.0), (20, 130.0), (40, 90.0), (60, 150.0), (80, 80.0)]
    df = make_zigzag(pivots, noise=0.0)
    left = right = 5

    result = find_pivots(df, left, right)
    n = len(df)
    assert all(p.bar_idx < n - right for p in result)


def test_find_pivots_requires_positive_windows() -> None:
    df = make_trend(n=30)
    try:
        find_pivots(df, 0, 3)
        raise AssertionError("beklenen ValueError fırlatılmadı")
    except ValueError:
        pass


# --- alternate_pivots ----------------------------------------------------


def test_alternate_pivots_cancels_lower_high_at_new_pivot_bar() -> None:
    raw = [
        _mk(5, 100.0, "high", 10),
        _mk(8, 105.0, "high", 13),  # daha yüksek high, ilkini iptal eder
        _mk(20, 90.0, "low", 25),  # zıt tür -> 105'lik high burada kesinleşir
    ]
    zigzag = alternate_pivots(raw, include_pending=False)

    assert len(zigzag) == 1
    assert zigzag[0].price == 105.0
    assert zigzag[0].bar_idx == 8
    assert zigzag[0].finalized_idx == 25  # iptal eden pivotun onay barı


def test_alternate_pivots_excludes_pending_tail_by_default() -> None:
    raw = [
        _mk(5, 100.0, "high", 10),
        _mk(20, 90.0, "low", 25),
    ]
    zigzag = alternate_pivots(raw, include_pending=False)
    assert len(zigzag) == 1
    assert zigzag[0].kind == "high"
    assert zigzag[0].finalized_idx == 25


def test_alternate_pivots_include_pending_appends_unfinalized_tail() -> None:
    raw = [
        _mk(5, 100.0, "high", 10),
        _mk(20, 90.0, "low", 25),
    ]
    zigzag = alternate_pivots(raw, include_pending=True)
    assert len(zigzag) == 2
    assert zigzag[-1].kind == "low"
    assert zigzag[-1].finalized_idx is None


def test_alternate_pivots_keeps_lower_low_run_extreme() -> None:
    raw = [
        _mk(5, 100.0, "high", 10),
        _mk(20, 90.0, "low", 25),
        _mk(22, 85.0, "low", 27),  # daha düşük low, öncekini iptal eder
        _mk(40, 110.0, "high", 45),
    ]
    zigzag = alternate_pivots(raw, include_pending=False)
    assert len(zigzag) == 2
    assert zigzag[1].kind == "low"
    assert zigzag[1].price == 85.0
    assert zigzag[1].bar_idx == 22
    assert zigzag[1].finalized_idx == 45


# --- label_structure -------------------------------------------------------


def test_label_structure_hh_hl_lh_ll() -> None:
    zigzag = alternate_pivots(
        [
            _mk(0, 100.0, "high", 5),
            _mk(10, 90.0, "low", 15),
            _mk(20, 110.0, "high", 25),  # HH (>100)
            _mk(30, 95.0, "low", 35),  # HL (>90)
            _mk(40, 105.0, "high", 45),  # LH (<110)
            _mk(50, 80.0, "low", 55),  # LL (<95)
        ],
        include_pending=True,
    )
    labeled = label_structure(zigzag)
    labels = [p.label for p in labeled]
    assert labels == [None, None, "HH", "HL", "LH", "LL"]


def test_label_structure_equal_price_is_not_higher() -> None:
    zigzag = alternate_pivots(
        [
            _mk(0, 100.0, "high", 5),
            _mk(10, 90.0, "low", 15),
            _mk(20, 100.0, "high", 25),  # eşit -> HH değil, LH
        ],
        include_pending=True,
    )
    labeled = label_structure(zigzag)
    assert labeled[-1].label == "LH"


# --- atr_zigzag -------------------------------------------------------


def test_atr_zigzag_finds_alternating_reversals() -> None:
    pivots = [(0, 100.0), (30, 140.0), (60, 90.0), (90, 150.0)]
    df = make_zigzag(pivots, noise=0.1, seed=11)

    result = atr_zigzag(df, atr_mult=1.5, atr_period=10)

    assert len(result) >= 2
    kinds = [p.kind for p in result]
    for a, b in zip(kinds, kinds[1:], strict=False):
        assert a != b  # zigzag doğası gereği ardışık iki pivot aynı türden olamaz
    for p in result:
        assert p.confirmed_idx > p.bar_idx


def test_atr_zigzag_empty_df_returns_empty() -> None:
    df = make_trend(n=1).iloc[:0]
    assert atr_zigzag(df) == []


# --- significant_pivots (Faz 0.5, A1) --------------------------------------


def test_significant_pivots_atr_matches_atr_zigzag_alternated() -> None:
    pivots = [(0, 100.0), (30, 140.0), (60, 90.0), (90, 150.0)]
    df = make_zigzag(pivots, noise=0.1, seed=11)

    result = significant_pivots(df, method="atr", atr_mult=1.5, atr_period=10)
    expected = alternate_pivots(atr_zigzag(df, atr_mult=1.5, atr_period=10))

    assert [(p.bar_idx, p.kind, p.finalized_idx) for p in result] == [
        (p.bar_idx, p.kind, p.finalized_idx) for p in expected
    ]


def test_significant_pivots_fixed_without_filter_matches_alternate_find_pivots() -> None:
    pivots = [(0, 100.0), (20, 130.0), (40, 90.0), (60, 150.0), (80, 80.0)]
    df = make_zigzag(pivots, noise=0.0)

    result = significant_pivots(df, method="fixed", left=5, right=5)
    expected = alternate_pivots(find_pivots(df, 5, 5))

    assert [(p.bar_idx, p.kind) for p in result] == [(p.bar_idx, p.kind) for p in expected]


def test_significant_pivots_fixed_min_swing_atr_drops_small_leg() -> None:
    # Büyük bir swing (0->20, +40) sonra KÜÇÜK bir geri çekilme (20->25, -2,
    # min_swing_atr eşiğinin altında kalacak kadar ufak — ardından TEKRAR
    # dönüp büyük bir yükselişe geçtiği için (25->50, +62) bar 25 GERÇEK bir
    # yerel dip). min_swing_atr olmadan 25'teki küçük dip AYRI bir zigzag
    # noktası olur; filtre AÇIKKEN o nokta ATLANMALI (önceki tepe [20] hâlâ
    # "pending" kalıp sonraki büyük yükselişle [50] eşleşmeli).
    # (55, 190): bar 50'nin bir yerel tepe olarak KESİNLEŞMESİ için right=2
    # kadar sonrasında (daha düşük) veri gerekiyor -- yoksa 50 serinin
    # ucunda kalır ve hiç onaylanmaz.
    pivots = [(0, 100.0), (20, 140.0), (25, 138.0), (50, 200.0), (55, 190.0)]
    df = make_zigzag(pivots, noise=0.0)

    unfiltered = significant_pivots(df, method="fixed", left=2, right=2)
    filtered = significant_pivots(df, method="fixed", left=2, right=2, min_swing_atr=50.0)

    assert any(p.bar_idx == 25 for p in unfiltered)
    assert not any(p.bar_idx == 25 for p in filtered)
    # 20'deki tepe hâlâ tutulmalı, ve 50'deki tepeye finalize olmalı.
    kept_high = next(p for p in filtered if p.bar_idx == 20)
    assert kept_high.kind == "high"


def test_significant_pivots_unknown_method_raises() -> None:
    df = make_trend(n=30)
    with pytest.raises(ValueError):
        significant_pivots(df, method="banana")  # type: ignore[arg-type]


@given(
    n=st.integers(min_value=40, max_value=100),
    seed=st.integers(min_value=0, max_value=5000),
)
@settings(max_examples=30, deadline=None)
def test_significant_pivots_fixed_min_swing_prefix_is_non_repainting(n: int, seed: int) -> None:
    """`significant_pivots(df[:cut], method="fixed", min_swing_atr=...)` bir
    ÖN EK üretmeli: tam seride görünen bir pivot, aynı bar_idx/kind/price ile
    prefix'te de görülüyorsa asla farklı bir DEĞERE sahip olmamalı (yalnızca
    henüz bilinmeyen SONRAKİ pivotlar prefix'te eksik olabilir)."""
    df = make_trend(n=n, slope=0.0, noise=1.5, seed=seed)
    cut = n // 2
    if cut <= 10:
        return

    partial = significant_pivots(df.iloc[:cut], method="fixed", left=2, right=2, min_swing_atr=1.0)
    full = significant_pivots(df, method="fixed", left=2, right=2, min_swing_atr=1.0)
    full_by_key = {(p.bar_idx, p.kind): p for p in full}

    for i, p in enumerate(partial):
        key = (p.bar_idx, p.kind)
        assert key in full_by_key, f"prefix'te var, tamda yok: {key}"
        assert math.isclose(p.price, full_by_key[key].price, rel_tol=1e-9)
        if i < len(partial) - 1:
            # Son eleman hariç (tail, prefix'e göre daha erken finalize
            # olabilir), sıralama da AYNI ön ek olmalı.
            assert full[i].bar_idx == p.bar_idx and full[i].kind == p.kind


# --- non-repaint property testi -------------------------------------------


@given(
    n=st.integers(min_value=30, max_value=100),
    seed=st.integers(min_value=0, max_value=5000),
    left=st.integers(min_value=1, max_value=5),
    right=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=40, deadline=None)
def test_find_pivots_prefix_results_are_subset_of_full(
    n: int, seed: int, left: int, right: int
) -> None:
    """find_pivots(df[:cut]) ⊆ find_pivots(df): onaylı pivotlar asla kaybolmaz/değişmez."""
    df = make_trend(n=n, slope=0.0, noise=1.5, seed=seed)
    cut = n // 2
    if cut <= left + right:
        return

    partial = find_pivots(df.iloc[:cut], left, right)
    full = find_pivots(df, left, right)
    full_by_key = {(p.bar_idx, p.kind, p.confirmed_idx): p for p in full}

    for p in partial:
        key = (p.bar_idx, p.kind, p.confirmed_idx)
        assert key in full_by_key, f"prefix'te var, tamda yok/farklı: {key}"
        assert math.isclose(p.price, full_by_key[key].price, rel_tol=1e-9)
