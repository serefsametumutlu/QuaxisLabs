"""`tlab/viz/svg/scenes/head_shoulders.py` -- Faz 4b'nin "classic" (TOBO/OBO)
sahnesi.

CEMTS (1D, classic/dark) + ODAS (1D, editorial) gerçek veriyle 6 iterasyon
geçti (bkz. `docs/design/iterasyon/iter{1,2,3,5,6}_head_shoulders_*`). 4/5.
iterasyonlarda "BAŞ" etiketinin dar bir TOBO'da (CEMTS) görünmediği
düşünüldü -- önce `LabelBox.priority`yi (yanlışlıkla TERS yönde, "küçük=
önemli" sanılarak) değiştirdim, sonra `layout.py`nin KENDİ docstring'inin
"büyük=daha önemli" sözleşmesini fark edip düzelttim. 6. iterasyonda SVG
metnini doğrudan inceleyince "BAŞ"ın ASLINDA HER ZAMAN doğru konumda
render edildiği (küçük/sıkışık PNG önizlemesinde okunamadığı) anlaşıldı --
öncelik değişikliği yine de mantıklı bir iyileştirme olarak (formasyonun
en karakteristik noktası artık en korunaklı) TUTULDU."""

from __future__ import annotations

import pytest

from tests.test_patterns.test_head_shoulders import _params, _tobo_ohlcv
from tlab.indicators.patterns.head_shoulders import HeadShouldersIndicator
from tlab.viz.svg import render_svg, supports
from tlab.viz.svg.scenes.head_shoulders import _group_patterns, build
from tlab.viz.svg.theme import CLASSIC, DARK, EDITORIAL


def _result():
    df = _tobo_ohlcv()
    result = HeadShouldersIndicator(_params()).compute(df)
    result.symbol = "TEST"
    return result, df


def test_supports_reports_head_shoulders() -> None:
    assert supports("patterns.head_shoulders") is True


def test_group_has_three_hologram_triangles_and_three_vertices() -> None:
    result, _ = _result()
    groups = _group_patterns(result)
    assert groups, "fixture en az bir grup üretmeli"
    for group in groups.values():
        assert len(group.hologram) == 3
        assert set(group.vertices) == {"SOL OMUZ", "BAŞ", "SAĞ OMUZ"}


def test_group_last_time_is_the_actual_last_signal() -> None:
    result, _ = _result()
    groups = _group_patterns(result)
    for pid, group in groups.items():
        pid_signals = sorted(
            (s for s in result.signals if s.payload.get("pattern_id") == pid),
            key=lambda s: s.bar_time,
        )
        assert group.last_time == pid_signals[-1].bar_time


def test_bas_vertex_label_is_present_in_rendered_svg() -> None:
    """4/5. iterasyonda "BAŞ" etiketinin kaybolduğu SANILMIŞTI (küçük PNG
    önizlemesinde okunamıyordu) -- gerçekte HER ZAMAN render ediliyordu.
    Bu regresyon SVG metnini doğrudan inceleyerek doğrular, PNG'ye
    güvenmez."""
    result, df = _result()
    out = build(result, df, CLASSIC)
    svg_text = "".join(p.svg for p in (out.panels or [])) + "".join(
        tu.svg for tu in (out.two_up or [])
    )
    assert "BAŞ" in svg_text
    assert "SOL OMUZ" in svg_text


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
    from tlab.testing.fixtures import make_trend

    empty = IndicatorResult(
        indicator="patterns.head_shoulders", version="1", params_hash="x", symbol="TEST",
        timeframe=Timeframe.D1,
    )
    df = make_trend(n=30, slope=0.0, noise=0.5, seed=2)
    out = build(empty, df, CLASSIC)
    assert out.panels is not None and len(out.panels) == 1
    assert out.two_up is None
