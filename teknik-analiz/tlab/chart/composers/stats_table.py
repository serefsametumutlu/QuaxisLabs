"""Backtest istatistik tablosu. Referans: `önemli/HRt3uuwaEAAWAgK.png`.

Terminal tarzı, tek renkli-genişlikli tablo. Satırlar değerin işaretine
göre renklenir: pozitif yeşil, negatif kırmızı, nötr düz.

`önemli/` klasöründeki tek hiç yapılmamış görsel buydu.
"""

from __future__ import annotations

from dataclasses import dataclass

import plotly.graph_objects as go

from tlab.chart.tokens import METRICS, ThemeName, palette, rgba, role_color


@dataclass(frozen=True)
class StatRow:
    label: str
    value: str
    unit: str = ""
    sign: int = 0        # +1 iyi, -1 kötü, 0 nötr

    def __post_init__(self) -> None:
        if self.sign not in (-1, 0, 1):
            raise ValueError(f"sign -1/0/+1 olmalı — alınan {self.sign}")


@dataclass(frozen=True)
class StatsTable:
    title: str
    headline: str
    rows: tuple[StatRow, ...]

    def __post_init__(self) -> None:
        if not self.rows:
            raise ValueError("boş istatistik tablosu çizilemez")


def compose(
    table: StatsTable,
    *,
    theme: ThemeName = "dark",
    width: int = 900,
    row_height: int = 30,
) -> go.Figure:
    p = palette(theme)
    m = METRICS

    def row_color(sign: int) -> str:
        if sign > 0:
            return role_color(theme, "bullish")
        if sign < 0:
            return role_color(theme, "bearish")
        return p.text

    def row_fill(sign: int) -> str:
        if sign > 0:
            return rgba(role_color(theme, "bullish"), 0.10)
        if sign < 0:
            return rgba(role_color(theme, "bearish"), 0.10)
        return "rgba(0,0,0,0)"

    labels = [r.label for r in table.rows]
    values = [r.value for r in table.rows]
    units = [r.unit for r in table.rows]
    fills = [row_fill(r.sign) for r in table.rows]
    colors = [row_color(r.sign) for r in table.rows]

    header_h = 96
    height = header_h + row_height * (len(table.rows) + 1) + 24

    fig = go.Figure(
        data=[
            go.Table(
                columnwidth=[46, 34, 24],
                header=dict(
                    values=["<b>METRİK</b>", "<b>DEĞER</b>", "<b>AÇIKLAMA</b>"],
                    fill_color=rgba(p.text_muted, 0.16),
                    line_color=rgba(p.axis, 0.6),
                    align=["left", "center", "center"],
                    font=dict(family=m.font_mono, size=12, color=p.text),
                    height=row_height,
                ),
                cells=dict(
                    values=[labels, values, units],
                    fill_color=[fills, fills, fills],
                    line_color=rgba(p.axis, 0.35),
                    align=["left", "center", "center"],
                    font=dict(family=m.font_mono, size=12, color=[colors, colors, colors]),
                    height=row_height,
                ),
            )
        ]
    )

    fig.update_layout(
        width=width, height=height,
        paper_bgcolor=p.bg, plot_bgcolor=p.bg,
        margin=dict(l=10, r=10, t=header_h, b=10),
        font=dict(family=m.font_mono, size=12, color=p.text),
    )
    # Başlık şeridi — referanstaki çerçeveli iki satır
    fig.add_annotation(
        x=0.5, y=1.0, xref="paper", yref="paper", yshift=62,
        xanchor="center", yanchor="middle", showarrow=False,
        text=f"<b>{table.title}</b>",
        font=dict(family=m.font_mono, size=14, color=role_color(theme, "accent")),
        bgcolor=rgba(role_color(theme, "accent"), 0.10),
        bordercolor=role_color(theme, "accent"), borderwidth=1, borderpad=6,
        width=width - 40,
    )
    fig.add_annotation(
        x=0.5, y=1.0, xref="paper", yref="paper", yshift=28,
        xanchor="center", yanchor="middle", showarrow=False,
        text=table.headline,
        font=dict(family=m.font_mono, size=12, color=role_color(theme, "warn")),
        bgcolor=rgba(role_color(theme, "warn"), 0.08),
        bordercolor=rgba(role_color(theme, "warn"), 0.5), borderwidth=1, borderpad=5,
        width=width - 40,
    )
    return fig
