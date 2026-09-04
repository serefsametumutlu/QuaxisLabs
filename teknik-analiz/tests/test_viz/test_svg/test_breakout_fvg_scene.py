"""`tlab/viz/svg/scenes/breakout_fvg.py` -- Faz 4b'nin SON sahnesi,
YENİ `patterns.breakout_fvg` stratejisi için.

BAKAB (1D, classic) + KRPLS (1D, dark) + CELHA (1D, editorial) gerçek
veriyle 3 iterasyon geçti (bkz. `docs/design/iterasyon/iter{1,2,3}_
breakout_fvg_*`) -- üç FARKLI terminal durum gözlemlendi (FVG oluşmadan
süresi dolma, retest sonrası geçersizleşme, hedefe kadar tam zincir) ve
hiçbiri çökmedi/YENİ bir hata bulunmadı (önceki 5 sahnenin `last_time`/
yıllı-tarih/negatif-hedef derslerinin baştan uygulanması sayesinde)."""

from __future__ import annotations

import pytest

from tests.test_patterns.test_breakout_fvg import (
    _consolidation_breakout_fvg_retest_confirm_ohlcv,
    _params,
)
from tlab.indicators.patterns.breakout_fvg import BreakoutFvgIndicator
from tlab.testing.fixtures import make_trend
from tlab.viz.svg import render_svg, supports
from tlab.viz.svg.scenes.breakout_fvg import _group_patterns, build
from tlab.viz.svg.theme import CLASSIC, DARK, EDITORIAL


def _result():
    df = _consolidation_breakout_fvg_retest_confirm_ohlcv()
    result = BreakoutFvgIndicator(_params()).compute(df)
    result.symbol = "TEST"
    return result, df


def test_supports_reports_breakout_fvg() -> None:
    assert supports("patterns.breakout_fvg") is True


def test_group_reaches_confirmed_with_fvg_box() -> None:
    result, _ = _result()
    groups = _group_patterns(result)
    assert groups, "fixture en az bir grup üretmeli"
    group = next(iter(groups.values()))
    assert group.state == "confirmed"
    assert group.fvg is not None
    assert group.fvg.low == 100.5
    assert group.fvg.high == 101.0


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


def test_build_handles_expired_without_fvg_gracefully() -> None:
    """GERÇEK gözlem (1. iterasyon, BAKAB): bir aday hiç FVG oluşmadan
    (`fvg is None`) SÜRESİ DOLDU durumuna geçebiliyor -- sahne çökmemeli,
    FVG kutusu HİÇ çizilmemeli."""
    from tlab.indicators.patterns.breakout_fvg import BreakoutFvgParams

    df = make_trend(n=80, slope=0.0, noise=1.0, seed=99)
    params = BreakoutFvgParams(
        consolidation_bars=10, box_atr_max=1.0, breakout_search_bars=5,
        min_fvg_atr=5.0,  # imkansız derecede yüksek -- FVG asla bulunamaz
        fvg_search_bars=3, atr_period=5,
    )
    result = BreakoutFvgIndicator(params).compute(df)
    result.symbol = "TEST"
    out = build(result, df, CLASSIC)
    assert out.panels is not None or out.two_up is not None


def test_build_empty_result_shows_placeholder() -> None:
    from tlab.core.types import IndicatorResult, Timeframe

    empty = IndicatorResult(
        indicator="patterns.breakout_fvg", version="1", params_hash="x", symbol="TEST",
        timeframe=Timeframe.D1,
    )
    df = make_trend(n=30, slope=0.0, noise=0.5, seed=2)
    out = build(empty, df, CLASSIC)
    assert out.panels is not None and len(out.panels) == 1
    assert out.two_up is None
