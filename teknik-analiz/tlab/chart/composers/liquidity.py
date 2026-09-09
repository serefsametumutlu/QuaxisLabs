"""Likidite radarı — Corwin-Schultz. Referans: `önemli/HRb_x7YWYAA750T.png`.

Üç panel: fiyat (mum), spread (referans seviyeleriyle), sigma.
Kullanıcının vurgusu: bu bir AL-SAT göstergesi DEĞİL, işlem kalitesi
radarıdır. Başlık da bunu söyler.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from tlab.chart.frame import ChartFrame, Panel
from tlab.chart.marks import candles, line_series
from tlab.chart.tokens import METRICS, ThemeName, rgba, role_color
from tlab.features.liquidity import LiquidityState

_REGIME_TR = {
    "likit_sakin": "LİKİT & SAKİN", "likit_sert": "LİKİT & SERT",
    "ince_sakin": "İNCE TAHTA & SAKİN", "ince_sert": "İNCE TAHTA & SERT",
}
_REGIME_ROLE = {
    "likit_sakin": "bullish", "likit_sert": "accent",
    "ince_sakin": "warn", "ince_sert": "bearish",
}


def compose(
    df: pd.DataFrame,
    spread: pd.Series,
    sigma: pd.Series,
    st: LiquidityState,
    *,
    symbol: str,
    timeframe: str = "1G",
    window: int = 21,
    theme: ThemeName = "light",
    width: int = 1600,
    height: int = 940,
) -> go.Figure:
    role = _REGIME_ROLE[st.regime]

    cf = ChartFrame(
        panels=[
            Panel("price", 0.44, "Fiyat"),
            Panel("spread", 0.28, "Spread", y_tickformat=".1%"),
            Panel("sigma", 0.28, "Sigma", y_tickformat=".1%"),
        ],
        theme=theme, width=width, height=height,
        title=f"{symbol} — LİKİDİTE RADARI — {_REGIME_TR[st.regime]}",
        subtitle=(
            f"Periyot: {timeframe}  |  Pencere: {window} bar  |  "
            f"Spread: %{st.spread_now * 100:.2f} (ort %{st.spread_mean * 100:.2f})  |  "
            f"Sigma: %{st.sigma_now * 100:.2f}  |  {st.note}"
        ),
    )

    candles(cf, df)

    # Spread — dolgulu çizgi + referans seviyeleri
    color = role_color(theme, "bearish")
    cf.add(
        go.Scatter(
            x=spread.index, y=spread, mode="lines", name="Spread",
            line=dict(color=color, width=1.6),
            fill="tozeroy", fillcolor=rgba(color, 0.10),
            hovertemplate="Spread: %{y:.3%}<extra></extra>", showlegend=False,
        ),
        "spread", observe=spread,
    )
    for value, label, dash in (
        (st.spread_median, "Medyan", "dot"),
        (st.spread_mean, "Ortalama", "dash"),
        (st.spread_p75, "P75", "dash"),
        (st.spread_p90, "P90", "dash"),
    ):
        cf.fig.add_shape(
            type="line", xref=f"{cf.xref('spread')} domain", x0=0, x1=1,
            yref=cf.yref("spread"), y0=value, y1=value,
            line=dict(color=rgba(cf.pal.text_muted, 0.55), width=1, dash=dash),
            layer="below",
        )
        cf.edge_label("spread", value, f"{label}: %{value * 100:.2f}", cf.pal.text_muted)

    # Sigma
    line_series(cf, sigma.index, sigma, "sigma", name="Sigma", role="accent", fmt=".3%")

    # Güncel durumu vurgula: son nokta
    for panel, ser, r in (("spread", spread, "bearish"), ("sigma", sigma, "accent")):
        s = ser.dropna()
        if len(s):
            cf.add(
                go.Scatter(
                    x=[s.index[-1]], y=[float(s.iloc[-1])], mode="markers",
                    marker=dict(size=8, color=role_color(theme, r)),
                    name="Güncel", hovertemplate="%{y:.3%}<extra></extra>",
                    showlegend=False,
                ),
                panel,
            )

    cf.fig.add_annotation(
        x=0, y=1.0, xref="paper", yref="paper", xanchor="left", yanchor="bottom",
        yshift=2, showarrow=False,
        text="<i>Yön göstergesi değildir — işlem kalitesi ve likidite radarıdır.</i>",
        font=dict(family=METRICS.font_family, size=METRICS.font_label,
                  color=role_color(theme, role)),
    )
    return cf.finish()
