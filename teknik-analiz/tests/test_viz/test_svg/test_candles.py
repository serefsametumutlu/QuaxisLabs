"""`tlab/viz/svg/candles.py::draw_candles`."""

from __future__ import annotations

import pandas as pd

from tlab.viz.svg.candles import draw_candles
from tlab.viz.svg.scale import Chart
from tlab.viz.svg.theme import CLASSIC


def _df() -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=3, freq="1D", tz="UTC")
    return pd.DataFrame(
        {
            "open": [10.0, 12.0, 9.0],
            "high": [13.0, 13.0, 10.0],
            "low": [9.0, 11.0, 8.0],
            "close": [12.0, 11.0, 9.5],
            "volume": [100, 100, 100],
        },
        index=idx,
    )


def _chart() -> Chart:
    return Chart(
        w=300, h=200, margin_l=20, margin_r=20, margin_t=10, margin_b=10,
        i_domain=(0, 2), p_domain=(8, 14),
    )


def test_draw_candles_emits_one_line_and_rect_per_bar() -> None:
    out = draw_candles(_df(), _chart(), CLASSIC)
    assert out.count("<line") == 3
    assert out.count("<rect") == 3


def test_draw_candles_uses_up_down_colors() -> None:
    out = draw_candles(_df(), _chart(), CLASSIC)
    assert CLASSIC.up in out  # bar 0: close(12) >= open(10)
    assert CLASSIC.down in out  # bar 1: close(11) < open(12)
