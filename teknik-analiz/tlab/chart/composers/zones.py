"""Arz/talep bölgeleri grafiği.

Kullanıcı isteği (2026-09-08): *"sade ve temiz bir şey olmalı ... her
grafikte sadece sağ tarafına mesela demand zone yazmalı ve o aralıktaki
değerler yazılmalı"*. Referans olarak paylaştığı koyu temalı grafikte
tek bir yeşil kutu ve sağda aralık değerleri var — başka hiçbir şey yok.

Bu yüzden: kutu + orta çizgi + SAĞ KENARDA ad ve aralık. Grafiğin içine
etiket basılmaz.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from tlab.chart.frame import ChartFrame, Panel
from tlab.chart.marks import candles, volume
from tlab.chart.tokens import METRICS, ThemeName, rgba, role_color
from tlab.indicators.structure.zones_v2 import Zone

_FRESH_TR = {"taze": "TAZE", "test_edildi": "TEST EDİLDİ", "kirildi": "KIRILDI"}


def compose(
    df: pd.DataFrame,
    zones: list[Zone],
    *,
    symbol: str,
    timeframe: str = "1G",
    theme: ThemeName = "light",
    width: int = 1600,
    height: int = 860,
) -> go.Figure:
    n_arz = sum(1 for z in zones if z.kind == "arz")
    n_talep = len(zones) - n_arz

    cf = ChartFrame(
        panels=[
            Panel("price", METRICS.panel_ratio_price + 0.12, "Fiyat"),
            Panel("volume", METRICS.panel_ratio_sub, "Hacim"),
        ],
        theme=theme, width=width, height=height,
        title=f"{symbol} — ARZ / TALEP BÖLGELERİ",
        subtitle=(
            f"Periyot: {timeframe}  |  {n_arz} arz  |  {n_talep} talep  |  "
            f"Son fiyat: {float(df['close'].iloc[-1]):,.2f}"
        ),
    )

    # Bölgeler mumların ALTINDA — kutular mumları örtmesin
    for z in zones:
        # arz KIRMIZI, talep YEŞİL (kullanıcının açık isteği)
        role = "bearish" if z.kind == "arz" else "bullish"
        color = role_color(theme, role)
        cf.fig.add_shape(
            type="rect", xref=f"{cf.xref('price')} domain", x0=0, x1=1,
            yref=cf.yref("price"), y0=z.low, y1=z.high,
            fillcolor=rgba(color, 0.11), line=dict(color=rgba(color, 0.5), width=1),
            layer="below",
        )
        # orta çizgi — referanstaki kesikli eksen
        cf.fig.add_shape(
            type="line", xref=f"{cf.xref('price')} domain", x0=0, x1=1,
            yref=cf.yref("price"), y0=z.mid, y1=z.mid,
            line=dict(color=rgba(color, 0.45), width=1, dash="dash"), layer="below",
        )
        cf.edge_label(
            "price", z.mid,
            f"<b>{'SUPPLY / ARZ' if z.kind == 'arz' else 'DEMAND / TALEP'}</b><br>"
            f"{z.low:,.2f} – {z.high:,.2f}<br>"
            f"{_FRESH_TR[z.freshness]} · {z.touches} temas",
            color, weight=2,
        )
        next(p for p in cf.panels if p.name == "price").observe([z.low, z.high])

    candles(cf, df)
    volume(cf, df, panel="volume", ma=21)
    return cf.finish()
