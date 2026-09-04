"""Saf SVG string üreteçleri -- hiç durum tutmaz, hesap yapmaz.

`docs/design/grafik_stil_vitrini.html` (artifact, satır ~176-227)'deki
`attrs`/`fnum`/`svgLine`/`svgRect`/`svgPoly`/`svgText`/`svgCircle`/`pill`
fonksiyonlarının birebir Python karşılığı. XML kaçışı (& < > " ') metin
içeriğinde ZORUNLU -- sembol adları/etiketler veri kaynaklı olabilir.
"""

from __future__ import annotations

from typing import Any, Literal

PolyKind = Literal["polygon", "polyline"]


def _fnum(n: float) -> str:
    r = round(float(n), 2)
    if r == int(r):
        return str(int(r))
    return str(r)


def _attrs(o: dict[str, Any]) -> str:
    parts = [f'{k}="{v}"' for k, v in o.items() if v is not None and v != ""]
    return " ".join(parts)


def escape_xml(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def svg_line(
    x1: float, y1: float, x2: float, y2: float, *,
    stroke: str = "#000", width: float = 1.0, dash: str | None = None,
    opacity: float | None = None, cap: str = "butt", filter_url: str | None = None,
) -> str:
    attrs = _attrs({
        "stroke": stroke, "stroke-width": width, "stroke-dasharray": dash,
        "opacity": opacity, "stroke-linecap": cap, "filter": filter_url,
    })
    return f'<line x1="{_fnum(x1)}" y1="{_fnum(y1)}" x2="{_fnum(x2)}" y2="{_fnum(y2)}" {attrs}/>'


def svg_rect(
    x: float, y: float, w: float, h: float, *,
    fill: str = "none", stroke: str | None = None, stroke_width: float | None = None,
    dash: str | None = None, opacity: float | None = None, rx: float | None = None,
    filter_url: str | None = None,
) -> str:
    if h < 0:
        y += h
        h = -h
    attrs = _attrs({
        "fill": fill, "stroke": stroke, "stroke-width": stroke_width, "stroke-dasharray": dash,
        "opacity": opacity, "rx": rx, "filter": filter_url,
    })
    hh = _fnum(max(h, 0.6))
    return f'<rect x="{_fnum(x)}" y="{_fnum(y)}" width="{_fnum(w)}" height="{hh}" {attrs}/>'


def svg_poly(
    kind: PolyKind, pts: list[tuple[float, float]], *,
    fill: str = "none", stroke: str | None = None, width: float | None = None,
    dash: str | None = None, opacity: float | None = None, filter_url: str | None = None,
) -> str:
    d = " ".join(f"{_fnum(p[0])},{_fnum(p[1])}" for p in pts)
    attrs = _attrs({
        "fill": fill, "stroke": stroke, "stroke-width": width, "stroke-dasharray": dash,
        "opacity": opacity, "stroke-linejoin": "round", "filter": filter_url,
    })
    return f'<{kind} points="{d}" {attrs}/>'


def svg_text(
    x: float, y: float, text: str, *,
    fill: str = "#000", size: float = 11, anchor: str = "start",
    family: str | None = None, weight: int | str | None = None,
    spacing: str | None = None, opacity: float | None = None,
) -> str:
    esc = escape_xml(text)
    attrs = _attrs({
        "fill": fill, "font-size": size, "text-anchor": anchor, "font-family": family,
        "font-weight": weight, "letter-spacing": spacing, "opacity": opacity,
    })
    return f'<text x="{_fnum(x)}" y="{_fnum(y)}" {attrs}>{esc}</text>'


def svg_circle(
    cx: float, cy: float, r: float, *,
    fill: str = "none", stroke: str | None = None, stroke_width: float | None = None,
    opacity: float | None = None, filter_url: str | None = None,
) -> str:
    attrs = _attrs({
        "fill": fill, "stroke": stroke, "stroke-width": stroke_width,
        "opacity": opacity, "filter": filter_url,
    })
    return f'<circle cx="{_fnum(cx)}" cy="{_fnum(cy)}" r="{_fnum(r)}" {attrs}/>'


def pill(
    x: float, y: float, w: float, h: float, text: str, *,
    fill: str | None = None, stroke: str | None = None, stroke_width: float | None = None,
    dash: str | None = None, opacity: float | None = None, text_fill: str | None = None,
    family: str | None = None, size: float = 10.5, weight: int | str = 600,
    spacing: str | None = None,
) -> str:
    rect = svg_rect(
        x, y, w, h, fill=fill or "none", stroke=stroke, stroke_width=stroke_width,
        dash=dash, rx=h / 2, opacity=opacity,
    )
    label = svg_text(
        x + w / 2, y + h / 2 + size * 0.36, text,
        fill=text_fill or "#000", size=size, anchor="middle", family=family,
        weight=weight, spacing=spacing,
    )
    return rect + label


def outline_pill(
    x: float, y: float, w: float, h: float, text: str, *,
    color: str, family: str | None = None, size: float = 9.5, weight: int | str = 700,
) -> str:
    """Artifact'in `outlinePill`i -- içi boş, kesikli çerçeveli rozet (ör.
    henüz oluşmakta olan bir formasyon için "AKTİF" etiketi)."""
    return pill(
        x, y, w, h, text, fill="none", stroke=color, stroke_width=1.3, dash="3,2",
        text_fill=color, family=family, size=size, weight=weight,
    )


def glow_filter_defs(filter_id: str, *, enabled: bool) -> str:
    if not enabled:
        return ""
    return (
        f'<filter id="{filter_id}" x="-60%" y="-60%" width="220%" height="220%">'
        '<feGaussianBlur stdDeviation="2.4" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
    )


def group(inner: str, **attrs: Any) -> str:
    return f"<g {_attrs(attrs)}>{inner}</g>"


def defs(inner: str) -> str:
    return f"<defs>{inner}</defs>"
