"""Saf SVG çizim motoru -- Faz 3.

`render_svg(result, df, theme, last_n)` bir `IndicatorResult`'ı doğrudan
SVG metnine çevirir; Plotly'ye hiç uğramaz. Mimari kural DEĞİŞMEDİ: bu
katman HESAP YAPMAZ, yalnızca zaten üretilmiş primitifleri (Level/Line/
Box/Polygon/Marker/Signal) çizer.

Sahne kaydı `_SCENES`te `IndicatorResult.indicator` adına göre yapılır --
henüz portlanmamış bir gösterge için `ValueError` fırlatılır, çağıran taraf
(`tlab/viz/live.py::render_live`) bunu yakalayıp Plotly'e düşer (Faz 4
boyunca iki motor yan yana yaşar)."""

from __future__ import annotations

import pandas as pd

from tlab.core.types import IndicatorResult
from tlab.viz.svg.scenes import double_top_bottom as _double_top_bottom
from tlab.viz.svg.scenes.base import SceneOut
from tlab.viz.svg.theme import SVGTheme, resolve_svg_theme

_SCENES = {"patterns.double_top_bottom": _double_top_bottom}

_GAP = 16.0


def supports(indicator_name: str) -> bool:
    return indicator_name in _SCENES


def _panel_svg_tag(w: float, h: float, x: float, y: float, inner: str, theme: SVGTheme) -> str:
    bg = "" if theme.key == "neon" else f'<rect width="{w}" height="{h}" fill="{theme.card_bg}"/>'
    return f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{bg}{inner}</svg>'


def _wrap_svg(scene_out: SceneOut, theme: SVGTheme) -> str:
    parts: list[str] = []
    if scene_out.two_up:
        two_up_panels = scene_out.two_up
        total_w = sum(tu.vb[0] for tu in two_up_panels) + _GAP * (len(two_up_panels) - 1)
        total_h = max(tu.vb[1] for tu in two_up_panels)
        xoff = 0.0
        for tu in two_up_panels:
            parts.append(_panel_svg_tag(tu.vb[0], tu.vb[1], xoff, 0.0, tu.svg, theme))
            xoff += tu.vb[0] + _GAP
    else:
        v_panels = scene_out.panels or []
        total_w = max((pv.vb[0] for pv in v_panels), default=486.0)
        total_h = sum(pv.vb[1] for pv in v_panels) + _GAP * max(0, len(v_panels) - 1)
        yoff = 0.0
        for pv in v_panels:
            parts.append(_panel_svg_tag(pv.vb[0], pv.vb[1], 0.0, yoff, pv.svg, theme))
            yoff += pv.vb[1] + _GAP

    inner = "".join(parts)
    page_bg = f'<rect width="{total_w}" height="{total_h}" fill="{theme.page_bg}"/>'
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w} {total_h}" '
        f'width="{total_w}" height="{total_h}">{page_bg}{inner}</svg>'
    )


def render_svg(
    result: IndicatorResult, df: pd.DataFrame, theme: str | SVGTheme = "classic",
    last_n: int | None = None,
) -> str:
    """`last_n` şu an yalnızca API uyumluluğu için tutulur -- portlanmış
    tek sahne (`double_top_bottom`) kendi otomatik pencereleme mantığını
    (`_pattern_window`) kullanır; gelecekteki sahneler (Faz 4) bu parametreyi
    kendi ihtiyaçlarına göre kullanabilir."""
    svg_theme = resolve_svg_theme(theme)
    module = _SCENES.get(result.indicator)
    if module is None:
        raise ValueError(
            f"'{result.indicator}' için SVG sahnesi henüz portlanmadı "
            f"(bkz. tlab/viz/svg/scenes/) -- desteklenenler: {sorted(_SCENES)}"
        )
    scene_out = module.build(result, df, svg_theme)
    return _wrap_svg(scene_out, svg_theme)
