"""`tlab/viz/svg/scale.py` -- `Chart`/`nice_ticks`/`pad_range`/`bar_index`."""

from __future__ import annotations

import pandas as pd
import pytest

from tlab.viz.svg.scale import Chart, bar_index, nice_ticks, pad_range


def _chart() -> Chart:
    return Chart(
        w=500, h=400, margin_l=40, margin_r=10, margin_t=20, margin_b=30,
        i_domain=(0, 100), p_domain=(10, 20),
    )


def test_chart_inner_bounds() -> None:
    ch = _chart()
    assert ch.inner_x0 == 40
    assert ch.inner_x1 == 490
    assert ch.inner_y0 == 20
    assert ch.inner_y1 == 370


def test_chart_x_maps_domain_endpoints() -> None:
    ch = _chart()
    assert ch.x(0) == pytest.approx(ch.inner_x0)
    assert ch.x(100) == pytest.approx(ch.inner_x1)


def test_chart_y_is_inverted() -> None:
    ch = _chart()
    # düşük fiyat -> alt (büyük y piksel), yüksek fiyat -> üst (küçük y piksel)
    assert ch.y(10) == pytest.approx(ch.inner_y1)
    assert ch.y(20) == pytest.approx(ch.inner_y0)


def test_nice_ticks_returns_round_steps() -> None:
    ticks = nice_ticks(0, 100, 5)
    assert ticks == [0.0, 20.0, 40.0, 60.0, 80.0, 100.0]


def test_nice_ticks_empty_when_degenerate() -> None:
    assert nice_ticks(10, 10, 5) == []
    assert nice_ticks(10, 20, 0) == []


def test_pad_range_expands_symmetrically() -> None:
    lo, hi = pad_range(100, 200, 0.1)
    assert lo == pytest.approx(90)
    assert hi == pytest.approx(210)


def test_bar_index_returns_position() -> None:
    idx = pd.date_range("2024-01-01", periods=5, freq="1D", tz="UTC")
    df = pd.DataFrame({"close": range(5)}, index=idx)
    assert bar_index(df, idx[3]) == 3
