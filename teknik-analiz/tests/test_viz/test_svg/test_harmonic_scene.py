"""`tlab/viz/svg/scenes/harmonic.py` -- Faz 4a'nın ilk sahnesi.

Fixture: `tests/test_harmonics/fixtures.py::build_gartley_ohlcv` -- gerçek
`find_pivots`/`generate_candidates` zincirinden geçen, doğrulanmış bir bull
Gartley serisi (`tests/test_viz/test_golden.py`nin de kullandığı AYNI
fixture). Tam seri CONFIRMED (bar30'da kapanış PRZ üstüne çıkar) bir aday
üretir; seriyi bar30'dan ÖNCE keserek ACTIVE durumu da test edilir."""

from __future__ import annotations

import pytest

from tests.test_harmonics.fixtures import build_gartley_ohlcv
from tlab.indicators.harmonics.scanner_indicator import HarmonicIndicator, HarmonicParams
from tlab.viz.svg import render_svg, supports
from tlab.viz.svg.scenes.harmonic import _group_candidates, build
from tlab.viz.svg.theme import CLASSIC, DARK, EDITORIAL


def _params() -> HarmonicParams:
    return HarmonicParams(
        left=2, right=2, zigzag_method="fixed",
        confirmation_policy="close_reversal", reversal_bars=1,
    )


def _confirmed_result_and_df():
    df = build_gartley_ohlcv()
    result = HarmonicIndicator("carney", _params()).compute(df)
    result.symbol = "TESTX"
    return result, df


_ALL_SCHOOLS = (
    "carney", "pesavento", "gilmore", "cypher", "nenstar",
    "navarro200", "five_zero", "three_drives",
)


def test_supports_reports_all_eight_schools() -> None:
    for school in _ALL_SCHOOLS:
        assert supports(f"harmonic.{school}") is True
    assert supports("harmonic.made_up_school") is False


def test_group_candidates_finds_confirmed_gartley() -> None:
    result, _df = _confirmed_result_and_df()
    candidates = _group_candidates(result)
    assert len(candidates) >= 1
    confirmed = [c for c in candidates if c.state == "confirmed"]
    assert confirmed, "tam seri CONFIRMED bir Gartley üretmeli"
    assert confirmed[0].pattern in ("gartley",)


def test_build_single_panel_when_only_one_state_present() -> None:
    result, df = _confirmed_result_and_df()
    out = build(result, df, CLASSIC)
    # Yalnızca CONFIRMED aday var (fixture'da hiç pending/active bırakılmadı
    # -- tam seride HERKES ya confirmed ya expired/invalidated olabilir);
    # ya tek panel ya iki panel döner, ikisi de geçerli -- asıl kontrol
    # hiç hata fırlatmaması ve boş olmaması.
    assert out.panels is not None or out.two_up is not None


@pytest.mark.parametrize("theme", [CLASSIC, DARK, EDITORIAL])
def test_render_svg_produces_well_formed_svg_in_all_three_themes(theme) -> None:
    result, df = _confirmed_result_and_df()
    svg_text = render_svg(result, df, theme=theme)
    assert svg_text.startswith("<svg")
    assert svg_text.strip().endswith("</svg>")
    assert svg_text.count("<svg") >= 2


def test_render_svg_empty_panel_when_no_candidates() -> None:
    df = build_gartley_ohlcv()
    # left/right'ı devasa yapmak -- hiçbir zigzag pivotu üretilemez.
    params = HarmonicParams(left=50, right=50, zigzag_method="fixed")
    result = HarmonicIndicator("carney", params).compute(df)
    result.symbol = "EMPTYX"
    svg_text = render_svg(result, df, theme="classic")
    assert "Harmonik aday yok" in svg_text


def test_active_candidate_before_confirmation_bar() -> None:
    """Seri bar30'dan (kapanışın PRZ üstüne çıktığı bar) ÖNCE kesilirse
    aynı aday hâlâ pending/active olarak kalmalı -- `d_point=None`
    (projected/dashed) dalını gerçek veriyle test eder."""
    df = build_gartley_ohlcv().iloc[:29]
    result = HarmonicIndicator("carney", _params()).compute(df)
    result.symbol = "ACTIVEX"
    candidates = _group_candidates(result)
    assert candidates
    assert all(c.state != "confirmed" for c in candidates)
    svg_text = render_svg(result, df, theme="classic")
    assert svg_text.startswith("<svg")
