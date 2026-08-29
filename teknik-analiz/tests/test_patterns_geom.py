"""tlab.features.patterns_geom için birim testleri: converging_lines
(eğim oranı/apex/yakınsama) ve classify() (7 desen türü + flag/pennant'ın
pole_range'e bağlı koşullu davranışı)."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from tlab.features.patterns_geom import (
    ClassifyParams,
    classify,
    converging_lines,
)
from tlab.features.swings import Pivot
from tlab.features.trendlines import Trendline

_DUMMY_PIVOT = Pivot(
    bar_idx=0, bar_time=pd.Timestamp("2024-01-01"), price=0.0, kind="high",
    confirmed_idx=0, confirmed_time=pd.Timestamp("2024-01-01"),
)


def _line(
    slope: float, intercept: float, kind: str = "resistance", created_idx: int = 0
) -> Trendline:
    return Trendline(
        p1=_DUMMY_PIVOT, p2=_DUMMY_PIVOT, slope=slope, intercept=intercept, kind=kind,  # type: ignore[arg-type]
        touches=(), broken_at=None, created_idx=created_idx,
    )


# --- converging_lines --------------------------------------------------


def test_converging_lines_opposite_slopes_converge_with_correct_apex() -> None:
    upper = _line(slope=-1.0, intercept=110.0)  # 110 - t
    lower = _line(slope=1.0, intercept=90.0)  # 90 + t
    conv = converging_lines(upper, lower)

    assert conv.is_converging is True
    assert conv.apex_idx == pytest.approx(10.0)
    assert conv.apex_price == pytest.approx(100.0)
    assert conv.slope_ratio == pytest.approx(1.0)


def test_converging_lines_diverging_gap_not_converging() -> None:
    upper = _line(slope=1.0, intercept=110.0)  # gap büyüyor (upper daha dik yukarı)
    lower = _line(slope=0.0, intercept=90.0)
    conv = converging_lines(upper, lower)
    assert conv.is_converging is False


def test_converging_lines_parallel_has_no_apex() -> None:
    upper = _line(slope=1.0, intercept=110.0)
    lower = _line(slope=1.0, intercept=90.0)
    conv = converging_lines(upper, lower)
    assert conv.apex_idx is None
    assert conv.apex_price is None
    assert conv.is_converging is False


def test_converging_lines_apex_behind_created_idx_not_converging() -> None:
    """Apex zaten GEÇMİŞTEYSE (created_idx'ten önce), ileriye dönük bir
    yakınsama senaryosu değildir."""
    upper = _line(slope=1.0, intercept=-5.0, created_idx=20)  # apex=-15 < created_idx
    lower = _line(slope=2.0, intercept=10.0, created_idx=20)
    conv = converging_lines(upper, lower)
    assert conv.apex_idx == pytest.approx(-15.0)
    assert conv.is_converging is False


def test_converging_lines_created_idx_is_max_of_both() -> None:
    upper = _line(slope=-1.0, intercept=110.0, created_idx=5)
    lower = _line(slope=1.0, intercept=90.0, created_idx=12)
    conv = converging_lines(upper, lower)
    assert conv.created_idx == 12


def test_safe_ratio_zero_denominator() -> None:
    upper = _line(slope=1.0, intercept=110.0)
    lower = _line(slope=0.0, intercept=90.0)
    conv = converging_lines(upper, lower)
    assert conv.slope_ratio == math.inf


# --- classify: 5 temel şekil --------------------------------------------


def test_classify_sym_triangle() -> None:
    conv = converging_lines(_line(-1.0, 110.0), _line(1.0, 90.0))
    assert classify(conv) == "sym_triangle"


def test_classify_asc_triangle() -> None:
    conv = converging_lines(_line(0.0, 110.0), _line(1.0, 90.0))
    assert classify(conv) == "asc_triangle"


def test_classify_desc_triangle() -> None:
    conv = converging_lines(_line(-1.0, 110.0), _line(0.0, 90.0))
    assert classify(conv) == "desc_triangle"


def test_classify_falling_wedge() -> None:
    conv = converging_lines(_line(-2.0, 130.0), _line(-1.0, 100.0))
    assert classify(conv) == "falling_wedge"


def test_classify_rising_wedge() -> None:
    conv = converging_lines(_line(1.0, 10.0), _line(2.0, -5.0))
    assert classify(conv) == "rising_wedge"


def test_classify_non_converging_same_direction_wedge_candidate_is_none() -> None:
    """Aynı yönlü ama YAKINSAMAYAN (paralel olmayan, ıraksayan) çizgiler
    wedge SAYILMAZ."""
    conv = converging_lines(_line(2.0, 130.0), _line(1.0, 100.0))  # gap büyüyor
    assert classify(conv) is None


# --- classify: flag/pennant (pole_range'e bağlı) ------------------------


def test_classify_sym_triangle_without_pole_stays_sym_triangle() -> None:
    conv = converging_lines(_line(-1.0, 110.0), _line(1.0, 90.0))
    assert classify(conv, pole_range=None) == "sym_triangle"


def test_classify_sym_triangle_small_with_pole_becomes_pennant() -> None:
    conv = converging_lines(_line(-1.0, 110.0), _line(1.0, 90.0))  # height=20 @created_idx=0
    assert classify(conv, pole_range=100.0) == "pennant"  # 20 <= 0.5*100


def test_classify_sym_triangle_large_relative_to_pole_stays_sym_triangle() -> None:
    conv = converging_lines(_line(-1.0, 110.0), _line(1.0, 90.0))  # height=20
    assert classify(conv, pole_range=20.0) == "sym_triangle"  # 20 > 0.5*20=10


def test_classify_near_parallel_channel_is_none_without_pole() -> None:
    conv = converging_lines(_line(1.0, 110.0), _line(1.0, 90.0))  # tam paralel, ıraksamıyor
    assert classify(conv, pole_range=None) is None


def test_classify_near_parallel_channel_small_with_pole_becomes_flag() -> None:
    conv = converging_lines(_line(1.0, 110.0), _line(1.0, 90.0))  # height=20
    assert classify(conv, pole_range=100.0) == "flag"


def test_classify_custom_params_flat_ratio() -> None:
    """flat_ratio büyütülünce, hafif eğimli bir çizgi de 'düz' sayılabilir."""
    conv = converging_lines(_line(-0.05, 110.0), _line(1.0, 90.0))
    default = classify(conv)  # 0.05, 1.0'ın %15'inden (0.15) küçük -> zaten flat
    assert default == "asc_triangle"

    strict = classify(conv, params=ClassifyParams(flat_ratio=0.01))
    assert strict == "sym_triangle"  # artık 'düz' sayılmıyor, iki eğim de yönlü
