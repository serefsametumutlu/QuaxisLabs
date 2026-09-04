"""`tlab/viz/svg/scenes/weekly_channel.py` -- Faz 4a'nın altıncı sahnesi.

THYAO (1D, classic/dark) + TUCLK (1D, classic) gerçek veriyle 3 iterasyon
geçti (bkz. `docs/design/iterasyon/iter{1,2,3}_weekly_channel_*`) -- YENİ bir
hata bulunmadı (`swing_fib_abcd`/`golden_zone`/`supply_demand`'ın eksen/
etiket derslerinin baştan uygulanması sayesinde). `ChannelIndicator.
compute()` `Marker` üretmez, yalnızca `Signal` -- bu yüzden `_latest_event_
markers`'ın "yalnızca en son örnek" dedup mantığı burada özel olarak
test edilir (THYAO 1D'de 150 barlık pencerede onlarca dokunuş sinyali
üretebildiği GERÇEK ölçümle doğrulandı, PROGRESS_LOG'a bkz.)."""

from __future__ import annotations

import pandas as pd
import pytest

from tests.test_trend.test_weekly_channel import _trend_with_wobble
from tlab.core.types import IndicatorResult, Signal, Timeframe
from tlab.indicators.trend.weekly_channel import ChannelIndicator, ChannelParams
from tlab.viz.svg import render_svg, supports
from tlab.viz.svg.scenes.weekly_channel import (
    _channel_lines,
    _latest_event_markers,
    _window,
    build,
)
from tlab.viz.svg.theme import CLASSIC, DARK, EDITORIAL


def _result() -> tuple[IndicatorResult, pd.DataFrame]:
    df = _trend_with_wobble(n=80)
    result = ChannelIndicator(ChannelParams(n=20, k=1.5, rsi_window=5)).compute(df)
    result.symbol = "TEST"
    return result, df


def test_supports_reports_weekly_channel() -> None:
    assert supports("trend.weekly_channel") is True


def test_channel_lines_returns_current_lower_and_upper() -> None:
    result, _ = _result()
    lower, upper = _channel_lines(result)
    assert lower is not None and lower.label == "channel_current_lower"
    assert upper is not None and upper.label == "channel_current_upper"


def test_latest_event_markers_dedupes_to_one_per_event_type() -> None:
    """Gerçek THYAO ölçümünde (bkz. modül docstring'i) onlarca aynı-türden
    dokunuş sinyali penceredeki tek bir olay türü için üretilebiliyordu --
    yalnızca EN SON (en büyük bar_time) örnek dönmeli."""
    df = _trend_with_wobble(n=80)
    window = _window(df)
    early, late = window.index[10], window.index[20]
    signals = [
        Signal(early, early, "long", "active", 0.7, {"event": "channel_bottom_touch"}),
        Signal(late, late, "long", "active", 0.7, {"event": "channel_bottom_touch"}),
    ]
    result = IndicatorResult(
        indicator="trend.weekly_channel", version="1", params_hash="x", symbol="TEST",
        timeframe=Timeframe.D1, signals=signals,
    )
    picked = _latest_event_markers(result, window)
    assert len(picked) == 1
    assert picked[0].bar_time == late


@pytest.mark.parametrize("theme", [CLASSIC, DARK, EDITORIAL])
def test_render_svg_produces_well_formed_svg_in_all_three_themes(theme) -> None:
    result, df = _result()
    svg_text = render_svg(result, df, theme=theme)
    assert svg_text.startswith("<svg")
    assert svg_text.strip().endswith("</svg>")


def test_build_returns_main_and_sub_panel() -> None:
    result, df = _result()
    out = build(result, df, CLASSIC)
    assert out.side is None
    assert out.two_up is None
    assert out.panels is not None and len(out.panels) == 2
