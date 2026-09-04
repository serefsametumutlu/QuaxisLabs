"""Fiyat/tarih ekseni etiketleri -- artifact'in `priceLabels`/`xLabels`/
`rightLabel`/`panelLabel` karşılığı.

Tarih etiketleri hafta sonu/seans dışı boşlukları göstermez: X ekseni
zaten bar-indeksli (bkz. `scale.py` docstring'i), bu yüzden çağıran taraf
yalnızca pencerelenmiş `df.index`ten pozisyon seçip gerçek tarihi metne
çevirir -- burada ayrıca bir "boşluk atlatma" mantığı GEREKMEZ."""

from __future__ import annotations

from collections.abc import Callable

from tlab.viz.svg.prim import svg_line, svg_text
from tlab.viz.svg.scale import Chart, nice_ticks
from tlab.viz.svg.theme import SVGTheme


def price_labels(
    chart: Chart, theme: SVGTheme, n: int, fmt: Callable[[float], str] | None = None,
) -> str:
    lo, hi = chart.p_domain
    out: list[str] = []
    for p in nice_ticks(lo, hi, n):
        y = chart.y(p)
        out.append(svg_line(chart.inner_x0, y, chart.inner_x1, y, stroke=theme.grid, width=1))
        text = fmt(p) if fmt else f"{p:.1f}"
        out.append(
            svg_text(
                chart.inner_x0 - 10, y + 3.5, text,
                fill=theme.text_muted, size=10, family=theme.mono, anchor="end",
            )
        )
    return "".join(out)


def x_labels(chart: Chart, entries: list[tuple[float, str]], theme: SVGTheme) -> str:
    out: list[str] = []
    for i, t in entries:
        out.append(
            svg_text(
                chart.x(i), chart.inner_y1 + 22, t,
                fill=theme.text_muted, size=10, family=theme.font_body, anchor="middle",
            )
        )
    return "".join(out)


def right_label(
    chart: Chart, y: float, text: str, theme: SVGTheme, *,
    fill: str | None = None, size: float = 10.5, weight: int | str | None = None,
) -> str:
    return svg_text(
        chart.inner_x1 + 10, y + 3.5, text,
        fill=fill or theme.text_muted, size=size, family=theme.mono, anchor="start", weight=weight,
    )


def panel_label(x: float, y: float, text: str, theme: SVGTheme) -> str:
    return svg_text(x, y, text, fill=theme.text_muted, size=9.5, family=theme.font_body, weight=600)
