"""Faktör ısı haritası — hangi yatırım tarzı öne çıkıyor?

Kaynak: "Fiyatın Ardında" raporu, *"2026'da öne çıkan özellik: fiyat
momentumu"*. Harita, bir faktörü GÜÇLÜ taşıyan sepet ile ZAYIF taşıyan
sepet arasındaki getiri farkını gösterir.

Raporun uyarısı aynen taşınıyor: *"Rakamlar tek bir hissenin veya bütün
sepetin getirisi değil, iki karşıt sepet arasındaki performans
farkıdır."* Bu, hücrelerin yanlış okunmasını engelleyen kritik nottur.

Hesap yapmaz, çizer.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from tlab.chart.tokens import METRICS, ThemeName, palette, role_color


@dataclass(frozen=True)
class FactorHeatmap:
    spreads: pd.DataFrame          # satır = faktör, sütun = dönem; değer = yüksek-düşük farkı (%)
    title: str = "FAKTÖR SEPETLERİ — güçlü sepet eksi zayıf sepet"
    note: str = ""

    def __post_init__(self) -> None:
        if self.spreads.empty:
            raise ValueError("boş ısı haritası çizilemez")


def compose(
    fh: FactorHeatmap,
    *,
    theme: ThemeName = "light",
    width: int = 1300,
    height: int = 520,
) -> go.Figure:
    p = palette(theme)
    m = METRICS
    z = fh.spreads.to_numpy(float)
    lim = float(np.nanmax(np.abs(z))) or 1.0

    # Diverjan ölçek: kırmızı (zayıf sepet önde) → nötr → yeşil (güçlü önde)
    scale = [
        [0.0, role_color(theme, "bearish")],
        [0.5, p.panel_bg],
        [1.0, role_color(theme, "bullish")],
    ]

    fig = go.Figure(
        go.Heatmap(
            z=z, x=list(fh.spreads.columns), y=list(fh.spreads.index),
            colorscale=scale, zmid=0.0, zmin=-lim, zmax=lim,
            text=[[f"{v:+.1f}%" for v in row] for row in z],
            texttemplate="%{text}",
            textfont=dict(family=m.font_family, size=12),
            hovertemplate="%{y} · %{x}<br>Fark: %{z:+.1f}%<extra></extra>",
            colorbar=dict(
                title=dict(text="Fark %", font=dict(size=m.font_label, color=p.text_muted)),
                tickfont=dict(size=m.font_label, color=p.text_muted),
                outlinewidth=0, thickness=12,
            ),
            xgap=3, ygap=3,
        )
    )
    fig.update_layout(
        width=width, height=height,
        paper_bgcolor=p.bg, plot_bgcolor=p.panel_bg,
        font=dict(family=m.font_family, size=m.font_axis, color=p.text),
        margin=dict(l=150, r=90, t=88, b=54),
        xaxis=dict(side="top", showgrid=False, linecolor=p.axis,
                   tickfont=dict(color=p.text_muted)),
        yaxis=dict(autorange="reversed", showgrid=False, linecolor=p.axis,
                   tickfont=dict(color=p.text)),
    )
    fig.add_annotation(
        x=0, y=1, xref="paper", yref="paper", xanchor="left", yanchor="bottom",
        yshift=52, showarrow=False, text=f"<b>{fh.title}</b>",
        font=dict(family=m.font_family, size=m.font_title, color=p.text),
    )
    fig.add_annotation(
        x=0, y=1, xref="paper", yref="paper", xanchor="left", yanchor="bottom",
        yshift=32, showarrow=False,
        text=(fh.note or
              "Rakamlar tek bir hissenin veya sepetin getirisi DEĞİL, "
              "iki karşıt sepet arasındaki performans farkıdır."),
        font=dict(family=m.font_family, size=m.font_sub, color=p.text_muted),
    )
    return fig
