"""Evren taraması — alpha ve momentum sıralaması.

`momentum.alpha_rank` ve `momentum.momentum_rank` göstergelerinin çıktısı
tek bir sembolün grafiği değil, TÜM EVRENİN dağılımıdır. Bu yüzden bu
komposer mum çizmez: dağılım + sıralama gösterir.

Kullanıcının isteği (ilk mesaj): alpha dağılımı ve momentum ısı haritası
web arayüzünde ayrı bir "BİST taraması" bölümü olsun.

Not: `momentum` göstergeleri Jegadeesh-Titman 12-1 çerçevesindedir —
son ay ATLANIR (kısa vadeli tersine dönüş etkisini dışlamak için). Bu
komposer o kuralı UYGULAMAZ, yalnızca gelen skorları çizer; kural
gösterge katmanının işidir.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from tlab.chart.frame import ChartFrame, Panel
from tlab.chart.tokens import METRICS, ThemeName, rgba, role_color


@dataclass(frozen=True)
class UniverseScan:
    metric_name: str                # "Alpha" | "Momentum (12-1)"
    scores: pd.Series               # index = sembol
    sectors: pd.Series | None = None
    top_n: int = 15
    as_of: str = ""

    def __post_init__(self) -> None:
        if self.scores.empty:
            raise ValueError("boş evren taraması çizilemez")
        if self.sectors is not None and not self.scores.index.equals(self.sectors.index):
            raise ValueError("skor ve sektör dizinleri aynı olmalı")


def compose(
    scan: UniverseScan,
    *,
    market: str = "BİST",
    theme: ThemeName = "light",
    width: int = 1600,
    height: int = 900,
) -> go.Figure:
    s = scan.scores.dropna().sort_values(ascending=False)
    top = s.head(scan.top_n)
    bottom = s.tail(scan.top_n)

    cf = ChartFrame(
        panels=[
            Panel("dist", 0.40, "Sembol sayısı"),
            Panel("rank", 0.60, scan.metric_name),
        ],
        theme=theme, width=width, height=height,
        title=f"{market} EVREN TARAMASI — {scan.metric_name.upper()}",
        subtitle=(
            f"Sembol: {len(s)}  |  Medyan: {s.median():.2f}  |  "
            f"En iyi: {s.index[0]} ({s.iloc[0]:.2f})  |  "
            f"En kötü: {s.index[-1]} ({s.iloc[-1]:.2f})"
            + (f"  |  {scan.as_of}" if scan.as_of else "")
        ),
        rangeselector=False,
    )

    # 1) Dağılım — evrenin şekli. Tek bir skorun anlamı ancak dağılım
    #    içindeki yeriyle okunur.
    counts, edges = np.histogram(s.to_numpy(), bins=28)
    centers = (edges[:-1] + edges[1:]) / 2
    colors = [
        role_color(theme, "bullish" if c >= 0 else "bearish") for c in centers
    ]
    cf.add(
        go.Bar(
            x=centers, y=counts,
            marker=dict(color=[rgba(c, 0.65) for c in colors], line=dict(width=0)),
            name="Dağılım",
            hovertemplate=f"{scan.metric_name}: %{{x:.2f}}<br>Sembol: %{{y}}<extra></extra>",
            showlegend=False,
        ),
        "dist", observe=counts,
    )
    for q, lbl in ((s.median(), "Medyan"), (s.quantile(0.9), "P90"), (s.quantile(0.1), "P10")):
        cf.fig.add_shape(
            type="line", xref=cf.xref("dist"), x0=q, x1=q,
            yref=f"{cf.yref('dist')} domain", y0=0, y1=1,
            line=dict(color=rgba(cf.pal.text_muted, 0.6), width=1, dash="dash"),
        )
        cf.fig.add_annotation(
            x=q, y=1, xref=cf.xref("dist"), yref=f"{cf.yref('dist')} domain",
            text=f"{lbl} {q:.2f}", showarrow=False, yanchor="bottom",
            font=dict(family=METRICS.font_family, size=METRICS.font_label,
                      color=cf.pal.text_muted),
        )

    # 2) Sıralama — en iyi ve en kötü N
    ranked = pd.concat([bottom.iloc[::-1], top.iloc[::-1]])
    bar_colors = [
        rgba(role_color(theme, "bullish" if v >= 0 else "bearish"), 0.85) for v in ranked
    ]
    # Sembol ZATEN y ekseninde yazıyor; çubuğun üstüne tekrar yazmak
    # hem gereksiz hem de negatif çubuklarda "outside" konum sola taşıp
    # eksen etiketlerinin üstüne biniyordu. Çubuğun İÇİNE yalnızca sektör.
    text = (
        [str(scan.sectors[sym]) for sym in ranked.index]
        if scan.sectors is not None else ["" for _ in ranked.index]
    )
    cf.add(
        go.Bar(
            x=ranked.to_numpy(), y=list(ranked.index), orientation="h",
            marker=dict(color=bar_colors, line=dict(width=0)),
            text=text, textposition="inside", insidetextanchor="start",
            textfont=dict(family=METRICS.font_family, size=METRICS.font_label,
                          color=cf.pal.bg),
            name=scan.metric_name,
            hovertemplate="%{y} · %{text}: %{x:.2f}<extra></extra>", showlegend=False,
        ),
        "rank", observe=ranked,
    )

    fig = cf.finish()
    # Sıralama panelinde x zaman DEĞİL: ortak x ayarları (rangebreaks,
    # spike) burada anlamsız, temizlenir.
    r = cf.row("rank")
    fig.layout[f"xaxis{r}"].update(rangebreaks=[], showspikes=False, type="linear")
    fig.layout["xaxis"].update(rangebreaks=[], showspikes=False, type="linear")
    fig.layout[f"yaxis{r}"].update(
        showticklabels=True, side="left", autorange="reversed", type="category",
    )
    fig.update_layout(hovermode="closest", bargap=0.15)
    return fig
