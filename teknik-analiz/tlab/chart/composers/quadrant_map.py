"""Dört bölgeli balon haritası — evren taraması.

Kaynak: kullanıcının paylaştığı "Fiyatın Ardında" raporu. Raporda AYNI
görsel dilinin üç ayrı kullanımı var; hepsi bu tek komposerle çizilir:

  1. **Kalabalıklaşma haritası** — x: momentum, y: kalabalıklaşma,
     balon: hacim, renk: kurumsal akış.
     *"Güçlü yükseliş her zaman güvenli yükseliş değildir."*
  2. **Getiri–hacim haritası** — x: 1 aylık getiri, y: hacim z-skoru.
     *"Yükselişe işlem hacmi eşlik ediyor mu?"*
  3. **Yabancı payı haritası** — x: dönem sonu yabancı payı,
     y: son haftadaki değişim.
     *"Yabancı payının yüksek olması yeni alım geldiği anlamına gelmez."*

Ortak fikir: iki eksenin KESİŞİMİ, tek başına hiçbir eksenin
söylemediğini söyler. Bu yüzden dört bölge ayrı ayrı adlandırılır.

Hesap yapmaz, çizer.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from tlab.chart.tokens import METRICS, ThemeName, palette, rgba, role_color


@dataclass(frozen=True)
class QuadrantLabels:
    top_right: str
    top_left: str
    bottom_right: str
    bottom_left: str


@dataclass(frozen=True)
class QuadrantMap:
    title: str
    x_title: str
    y_title: str
    x: pd.Series                    # index = sembol
    y: pd.Series
    size: pd.Series | None = None   # balon büyüklüğü (ör. hacim)
    color: pd.Series | None = None  # +/- yönlü renk (ör. kurumsal akış)
    labels: QuadrantLabels | None = None
    x_center: float = 0.0
    y_center: float = 0.0
    annotate_top: int = 10          # kaç sembolün adı yazılsın
    note: str = ""

    def __post_init__(self) -> None:
        if not self.x.index.equals(self.y.index):
            raise ValueError("x ve y aynı sembol dizinine sahip olmalı")
        if self.x.empty:
            raise ValueError("boş harita çizilemez")


def compose(
    qm: QuadrantMap,
    *,
    theme: ThemeName = "light",
    width: int = 1500,
    height: int = 900,
) -> go.Figure:
    p = palette(theme)
    m = METRICS
    fig = go.Figure()

    xs, ys = qm.x.to_numpy(float), qm.y.to_numpy(float)
    x_pad = (np.nanmax(xs) - np.nanmin(xs)) * 0.10 or 1.0
    y_pad = (np.nanmax(ys) - np.nanmin(ys)) * 0.10 or 1.0
    x_rng = (np.nanmin(xs) - x_pad, np.nanmax(xs) + x_pad)
    y_rng = (np.nanmin(ys) - y_pad, np.nanmax(ys) + y_pad)

    # Bölge zeminleri — çok soluk; okumayı kolaylaştırır, veriyi örtmez
    for x0, x1, y0, y1, role in (
        (qm.x_center, x_rng[1], qm.y_center, y_rng[1], "warn"),      # sağ üst
        (x_rng[0], qm.x_center, qm.y_center, y_rng[1], "bearish"),   # sol üst
        (qm.x_center, x_rng[1], y_rng[0], qm.y_center, "bullish"),   # sağ alt
        (x_rng[0], qm.x_center, y_rng[0], qm.y_center, "neutral"),   # sol alt
    ):
        fig.add_shape(
            type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
            fillcolor=rgba(role_color(theme, role), 0.045),
            line=dict(width=0), layer="below",
        )

    for value, axis in ((qm.x_center, "x"), (qm.y_center, "y")):
        fig.add_shape(
            type="line", layer="below",
            **({"x0": value, "x1": value, "y0": y_rng[0], "y1": y_rng[1]}
               if axis == "x" else
               {"x0": x_rng[0], "x1": x_rng[1], "y0": value, "y1": value}),
            line=dict(color=rgba(p.text_muted, 0.55), width=1, dash="dash"),
        )

    if qm.size is not None:
        s = qm.size.reindex(qm.x.index).to_numpy(float)
        s = np.nan_to_num(s, nan=float(np.nanmedian(s)))
        sizes = 10 + 34 * (s - s.min()) / max(s.max() - s.min(), 1e-9)
    else:
        sizes = np.full(len(xs), 13.0)

    if qm.color is not None:
        c = qm.color.reindex(qm.x.index).to_numpy(float)
        colors = [
            rgba(role_color(theme, "bullish" if v >= 0 else "bearish"), 0.72)
            for v in np.nan_to_num(c)
        ]
        hover_extra = "<br>Akış: %{customdata:+.2f}"
        custom = np.nan_to_num(c)
    else:
        colors = [rgba(role_color(theme, "accent"), 0.65)] * len(xs)
        hover_extra = ""
        custom = None

    # En uçtaki semboller adlandırılır; hepsini yazmak haritayı boğar
    dist = np.hypot(
        (xs - qm.x_center) / max(np.nanstd(xs), 1e-9),
        (ys - qm.y_center) / max(np.nanstd(ys), 1e-9),
    )
    named = set(np.argsort(dist)[-qm.annotate_top:])
    text = [sym if i in named else "" for i, sym in enumerate(qm.x.index)]

    fig.add_trace(
        go.Scatter(
            x=xs, y=ys, mode="markers+text",
            marker=dict(size=sizes, color=colors,
                        line=dict(color=rgba(p.text, 0.30), width=1)),
            text=text, textposition="top center",
            textfont=dict(family=m.font_family, size=10, color=p.text),
            customdata=custom,
            hovertext=list(qm.x.index),
            hovertemplate=(
                "<b>%{hovertext}</b><br>"
                f"{qm.x_title}: %{{x:.2f}}<br>{qm.y_title}: %{{y:.2f}}"
                + hover_extra + "<extra></extra>"
            ),
            showlegend=False,
        )
    )

    if qm.labels is not None:
        for xa, ya, xanc, yanc, txt in (
            (x_rng[1], y_rng[1], "right", "top", qm.labels.top_right),
            (x_rng[0], y_rng[1], "left", "top", qm.labels.top_left),
            (x_rng[1], y_rng[0], "right", "bottom", qm.labels.bottom_right),
            (x_rng[0], y_rng[0], "left", "bottom", qm.labels.bottom_left),
        ):
            fig.add_annotation(
                x=xa, y=ya, xanchor=xanc, yanchor=yanc, showarrow=False,
                text=f"<b>{txt}</b>",
                font=dict(family=m.font_family, size=11, color=rgba(p.text_muted, 0.9)),
            )

    fig.update_layout(
        width=width, height=height,
        paper_bgcolor=p.bg, plot_bgcolor=p.panel_bg,
        font=dict(family=m.font_family, size=m.font_axis, color=p.text),
        margin=dict(l=70, r=40, t=86, b=64),
        hovermode="closest", showlegend=False,
        xaxis=dict(title=dict(text=qm.x_title), range=list(x_rng),
                   gridcolor=p.grid, zeroline=False, linecolor=p.axis),
        yaxis=dict(title=dict(text=qm.y_title), range=list(y_rng),
                   gridcolor=p.grid, zeroline=False, linecolor=p.axis),
    )
    fig.add_annotation(
        x=0, y=1, xref="paper", yref="paper", xanchor="left", yanchor="bottom",
        yshift=44, showarrow=False, text=f"<b>{qm.title}</b>",
        font=dict(family=m.font_family, size=m.font_title, color=p.text),
    )
    if qm.note:
        fig.add_annotation(
            x=0, y=1, xref="paper", yref="paper", xanchor="left", yanchor="bottom",
            yshift=22, showarrow=False, text=qm.note,
            font=dict(family=m.font_family, size=m.font_sub, color=p.text_muted),
        )
    return fig
