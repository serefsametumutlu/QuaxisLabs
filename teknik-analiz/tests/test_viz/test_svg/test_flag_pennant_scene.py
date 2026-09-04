"""`tlab/viz/svg/scenes/flag_pennant.py` -- Faz 4b'nin dördüncü sahnesi.

INTEM (1D, classic/dark) + DMSAS (1D, editorial) gerçek veriyle 3 iterasyon
geçti (bkz. `docs/design/iterasyon/iter{1,2,3}_flag_pennant_*`) -- YENİ bir
hata bulunmadı, kullanıcının 2026-09-04 geri bildirimindeki asıl şikayet
(`error/INTEM_patterns.flag_pennant_1d.png`: direğin pencerenin SOL
kenarından başlayıp öncesindeki mumların hiç görünmemesi) `_pattern_
window`nin `pad_before`sini direğin KENDİ başlangıcına (`pole.points[0][0]`)
göre hesaplayarak baştan önlendi (önceki 4 sahnenin `last_time`/yıllı-tarih
derslerinin de baştan uygulanmasıyla birlikte)."""

from __future__ import annotations

import pytest

from tests.test_patterns.test_flag_pennant import _pole_then_flat_flag_ohlcv
from tlab.indicators.patterns.flag_pennant import FlagPennantIndicator, FlagPennantParams
from tlab.testing.fixtures import make_trend
from tlab.viz.svg import render_svg, supports
from tlab.viz.svg.scale import bar_index
from tlab.viz.svg.scenes.flag_pennant import _group_patterns, _pattern_window, build
from tlab.viz.svg.theme import CLASSIC, DARK, EDITORIAL


def _result():
    df = _pole_then_flat_flag_ohlcv()
    params = FlagPennantParams(
        pole_bars=4, pole_atr=1.5, flag_min_bars=5, flag_max_bars=15, flag_atr=2.0,
    )
    result = FlagPennantIndicator(params)(df)
    result.symbol = "TEST"
    return result, df


def test_supports_reports_flag_pennant() -> None:
    assert supports("patterns.flag_pennant") is True


def test_group_has_pole_box_and_target() -> None:
    result, _ = _result()
    groups = _group_patterns(result)
    assert groups, "fixture en az bir grup üretmeli"
    for group in groups.values():
        assert group.pole.style == "pattern_pole"
        assert group.box.style == "pattern_consolidation"


def test_window_includes_bars_before_pole_start() -> None:
    """GERÇEK kullanıcı geri bildirimi (INTEM, 2026-09-04): direk pencerenin
    SOL kenarından başlıyor, öncesindeki mumlar hiç görünmüyordu."""
    result, df = _result()
    groups = _group_patterns(result)
    group = next(iter(groups.values()))
    window = _pattern_window(df, group)
    pole_start_pos = bar_index(window, group.pole.points[0][0])
    assert pole_start_pos > 0, "direk penceredeki İLK bar OLMAMALI, öncesinde pay olmalı"


@pytest.mark.parametrize("theme", [CLASSIC, DARK, EDITORIAL])
def test_render_svg_produces_well_formed_svg_in_all_three_themes(theme) -> None:
    result, df = _result()
    svg_text = render_svg(result, df, theme=theme)
    assert svg_text.startswith("<svg")
    assert svg_text.strip().endswith("</svg>")


def test_build_returns_panels_without_crash() -> None:
    result, df = _result()
    out = build(result, df, CLASSIC)
    assert out.panels is not None or out.two_up is not None


def test_build_empty_result_shows_placeholder() -> None:
    from tlab.core.types import IndicatorResult, Timeframe

    empty = IndicatorResult(
        indicator="patterns.flag_pennant", version="1", params_hash="x", symbol="TEST",
        timeframe=Timeframe.D1,
    )
    df = make_trend(n=30, slope=0.0, noise=0.5, seed=2)
    out = build(empty, df, CLASSIC)
    assert out.panels is not None and len(out.panels) == 1
    assert out.two_up is None
