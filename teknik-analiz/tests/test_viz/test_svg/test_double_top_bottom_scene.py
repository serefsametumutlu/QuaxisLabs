"""`tlab/viz/svg/scenes/double_top_bottom.py` -- Faz 3'ün "tek sahnelik
kanıtı". Fixture, `tests/test_patterns/test_double_top_bottom.py`deki
GERÇEK pivotlarla doğrulanmış aynı çift-dip senaryosunu kullanır (dip1->
boyun->dip2->kırılım->hedefe ulaşma) -- burada AYRICA render edilebilir mi
diye test edilir."""

from __future__ import annotations

import pandas as pd
import pytest

from tlab.core.types import Timeframe
from tlab.indicators.patterns.double_top_bottom import (
    DoubleTopBottomIndicator,
    DoubleTopBottomParams,
)
from tlab.viz.svg import render_svg, supports
from tlab.viz.svg.scenes.double_top_bottom import _group_patterns, build
from tlab.viz.svg.theme import CLASSIC, DARK, EDITORIAL

_TZ = "Europe/Istanbul"

_ROWS: list[tuple[float, float, float, float]] = [
    (105, 104, 106, 103),
    (104, 101, 105, 100),
    (101, 98, 102, 97),
    (98, 100, 101, 98.5),
    (100, 103, 104, 99.5),
    (103, 108, 109, 102),
    (108, 113, 114, 107),
    (113, 116, 117, 112),
    (116, 113, 117, 112),
    (113, 110, 114, 109),
    (110, 105, 111, 104),
    (105, 101, 106, 100),
    (101, 97, 102, 96),
    (97, 100, 101, 96.5),
    (100, 104, 105, 99.5),
    (104, 100, 104.5, 99),
    (100, 98, 101, 97.5),
    (98, 103, 104, 97),
    (103, 110, 111, 102),
    (110, 118, 119, 109),
    (118, 123, 124, 117),
    (123, 128, 129, 122),
    (128, 132, 133, 127),
    (132, 138, 139, 131),
]


def _ohlcv() -> pd.DataFrame:
    idx = pd.date_range("2024-01-02", periods=len(_ROWS), freq="1D", tz=_TZ)
    return pd.DataFrame(
        [{"open": c, "close": c, "high": h, "low": lo, "volume": 1000.0} for _o, c, h, lo in _ROWS],
        index=idx,
    )


def _params() -> DoubleTopBottomParams:
    return DoubleTopBottomParams(
        left=2, right=2, zigzag_method="fixed",
        min_bars_between=10, prior_trend_lookback=3, prior_trend_min_tstat=0.5,
        min_rise_between_pct=0.0, min_depth_pct=0.0, min_depth_atr=0.0,
    )


def _result_and_df():
    df = _ohlcv()
    result = DoubleTopBottomIndicator(_params()).compute(df)
    result.symbol = "TESTX"
    assert result.timeframe == Timeframe.D1
    return result, df


def test_supports_reports_double_top_bottom() -> None:
    assert supports("patterns.double_top_bottom") is True
    # Faz 4a'da portlandı -- artık desteklenen bir indikatör (bkz.
    # tests/test_viz/test_svg/test_harmonic_scene.py).
    assert supports("harmonic.carney") is True
    # henüz portlanmamış bir gösterge -- False kalmalı.
    assert supports("trend.weekly_channel") is False


def test_group_patterns_finds_double_bottom_group() -> None:
    result, _df = _result_and_df()
    groups = _group_patterns(result)
    assert len(groups) == 1
    group = next(iter(groups.values()))
    assert group.direction == "long"
    assert group.breakout is not None
    assert group.completed is not None


def test_build_returns_single_panel_when_only_one_direction() -> None:
    result, df = _result_and_df()
    out = build(result, df, CLASSIC)
    assert out.panels is not None
    assert out.two_up is None
    assert len(out.panels) == 1
    # sahne yalnızca İÇ içerik döner, dış <svg> etiketi render_svg'de eklenir
    assert "<svg" not in out.panels[0].svg


@pytest.mark.parametrize("theme", [CLASSIC, DARK, EDITORIAL])
def test_render_svg_produces_well_formed_svg_in_all_three_themes(theme) -> None:
    result, df = _result_and_df()
    svg_text = render_svg(result, df, theme=theme)
    assert svg_text.startswith("<svg")
    assert svg_text.strip().endswith("</svg>")
    assert svg_text.count("<svg") >= 2  # dış + en az bir iç panel


def test_render_svg_raises_for_unported_indicator() -> None:
    result, df = _result_and_df()
    result.indicator = "trend.weekly_channel"
    with pytest.raises(ValueError, match="henüz portlanmadı"):
        render_svg(result, df)


def test_render_svg_empty_panel_when_no_pattern_candidates() -> None:
    df = _ohlcv()
    result = DoubleTopBottomIndicator(DoubleTopBottomParams(min_bars_between=10_000)).compute(df)
    result.symbol = "EMPTYX"
    svg_text = render_svg(result, df, theme="classic")
    assert "Çift tepe/dip adayı yok" in svg_text
