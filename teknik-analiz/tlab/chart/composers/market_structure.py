"""Piyasa yapısı grafiği. Referans: `ornek1.png`.

Kullanıcının açık isteği: pivotlar arasında ZİGZAG ÇİZİLMEZ; tepelerin
üstüne aşağı bakan, diplerin altına yukarı bakan küçük üçgenler ve kısa
etiketler konur. BOS/CHoCH olayları, kırılan pivottan kırılım barına
uzanan kesikli yatay çizgilerle gösterilir.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from tlab.chart.frame import ChartFrame, Panel
from tlab.chart.marks import candles, line_series, pivot_markers, volume
from tlab.chart.tokens import METRICS, ThemeName, rgba, role_color
from tlab.indicators.structure.market_structure_v2 import MarketStructure

_BIAS_TR = {"yukselen": "YÜKSELEN YAPI", "alcalan": "ALÇALAN YAPI", "belirsiz": "BELİRSİZ YAPI"}


def compose(
    df: pd.DataFrame,
    ms: MarketStructure,
    *,
    symbol: str,
    timeframe: str = "1G",
    theme: ThemeName = "light",
    width: int = 1600,
    height: int = 880,
    max_points: int = 8,
    ma_period: int = 50,
) -> go.Figure:
    facts = [
        ("Periyot", timeframe),
        ("Yapı noktası", str(len(ms.points))),
        ("Olay", str(len(ms.events))),
    ]
    if ms.events:
        facts.append(("Son olay", f"{ms.events[-1].kind} {ms.events[-1].t.date()}"))
    if ms.bars_ago is not None:
        facts.append(("Sinyal yaşı", f"{ms.bars_ago} bar"))

    cf = ChartFrame(
        panels=[
            Panel("price", METRICS.panel_ratio_price + 0.10, "Fiyat"),
            Panel("volume", METRICS.panel_ratio_sub, "Hacim"),
        ],
        theme=theme, width=width, height=height,
        title=f"{symbol} — PİYASA YAPISI — {_BIAS_TR[ms.bias]}",
        subtitle="  |  ".join(f"{k}: {v}" for k, v in facts),
    )

    candles(cf, df)

    # TEK bir hareketli ortalama (referans ornek1.png'de de tek mor çizgi).
    # Birden fazla MA grafiği kalabalıklaştırıyor.
    ma = df["close"].rolling(ma_period).mean()
    line_series(
        cf, df.index, ma, "price", name=f"MA{ma_period}", role="accent", width=1.6,
    )

    # Pivot üçgenleri — ZİGZAG YOK. Yalnızca SON `max_points` tanesi:
    # 25-34 noktanın hepsi çizilince grafik okunmaz hâle geliyor.
    shown = ms.points[-max_points:]
    pivot_markers(cf, [(p.t, p.price, p.label) for p in shown])

    # BOS / CHoCH — kırılan pivottan kırılım barına uzanan kesikli yatay
    for e in ms.events:
        role = "bullish" if e.direction == "up" else "bearish"
        color = role_color(theme, role)
        arrow = "↑" if e.direction == "up" else "↓"
        cf.add(
            go.Scatter(
                x=[e.from_t, e.t], y=[e.price, e.price], mode="lines",
                line=dict(color=rgba(color, 0.75), width=1.4, dash="dash"),
                name=e.kind, hoverinfo="skip", showlegend=False,
            ),
            "price", observe=[e.price],
        )
        cf.fig.add_annotation(
            x=e.t, y=e.price, xref=cf.xref("price"), yref=cf.yref("price"),
            text=f"<b>{e.kind}{arrow}</b>", showarrow=False,
            xanchor="left", yanchor="middle", xshift=4,
            font=dict(family=METRICS.font_family, size=9, color=color),
        )

    volume(cf, df, panel="volume", ma=21)
    return cf.finish()
