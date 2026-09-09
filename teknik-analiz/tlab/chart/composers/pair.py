"""Çift (pairs trading) grafiği. Referans: `önemli/HRcUk75bgAApv6n.png`.

Dört panel: normalize fiyatlar, portföy performansı, z-skor + işlemler,
Pair Health (rolling korelasyon + beta, ÇİFT EKSEN).

Referanstaki iki ayırt edici öğe burada da var:
  - düşey REJİM GÖLGELERİ (dört panelin arkasında),
  - dördüncü panelde ÇİFT y ekseni: solda korelasyon, sağda beta.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go

from tlab.chart.frame import ChartFrame, Panel
from tlab.chart.marks import guide_level, line_series, regime_shading
from tlab.chart.tokens import METRICS, ThemeName, role_color
from tlab.features.pair_health import PairHealth

_VERDICT_TR = {
    "saglikli": "SAĞLIKLI", "izlemede": "İZLEMEDE", "bozulmus": "BOZULMUŞ",
}


@dataclass(frozen=True)
class PairTrade:
    t: pd.Timestamp
    z: float
    leg: str            # hangi bacak alınıyor
    side: str           # "long" | "short"


@dataclass(frozen=True)
class PairView:
    y_symbol: str
    x_symbol: str
    y_norm: pd.Series
    x_norm: pd.Series
    equity: pd.Series
    benchmark: pd.Series
    zscore: pd.Series
    corr: pd.Series
    beta: pd.Series
    trades: tuple[PairTrade, ...]
    health: PairHealth
    entry_z: float = 2.0
    regimes: tuple[tuple[pd.Timestamp, pd.Timestamp, str], ...] = ()

    def __post_init__(self) -> None:
        if self.y_symbol == self.x_symbol:
            raise ValueError("çiftin iki bacağı aynı sembol olamaz")


def compose(
    pv: PairView,
    *,
    theme: ThemeName = "dark",
    width: int = 1700,
    height: int = 980,
) -> go.Figure:
    h = pv.health
    facts = [
        ("Sağlık", _VERDICT_TR[h.verdict]),
        ("Korelasyon", f"{h.corr_now:.2f} (uzun {h.corr_long:.2f})"),
        ("Beta", f"{h.beta_now:.2f} ± {h.beta_std:.2f}"),
        ("Yarı ömür", "—" if h.half_life != h.half_life else f"{h.half_life:.0f} bar"),
        ("Z", f"{float(pv.zscore.iloc[-1]):+.2f}"),
    ]
    subtitle = "  |  ".join(f"{k}: {v}" for k, v in facts)
    if h.reasons:
        subtitle += "  |  ⚠ " + "; ".join(h.reasons)

    cf = ChartFrame(
        panels=[
            Panel("norm", 0.27, "Normalize 100"),
            Panel("equity", 0.24, "Portföy"),
            Panel("z", 0.24, "Z"),
            # Referans HRcUk75bgAApv6n: Corr SOLDA, Beta SAĞDA.
            Panel(
                "health", 0.25, "Korelasyon",
                secondary_y=True, y_side="left", secondary_title="Beta",
            ),
        ],
        theme=theme, width=width, height=height,
        title=f"{pv.y_symbol} ↔ {pv.x_symbol} — ÇİFT SAĞLIĞI: {_VERDICT_TR[h.verdict]}",
        subtitle=subtitle,
    )

    if pv.regimes:
        regime_shading(cf, list(pv.regimes))

    # 1) Normalize fiyatlar
    line_series(cf, pv.y_norm.index, pv.y_norm, "norm",
                name=f"{pv.y_symbol} (Y)", role="accent")
    line_series(cf, pv.x_norm.index, pv.x_norm, "norm",
                name=f"{pv.x_symbol} (X)", role="neutral")

    # 2) Portföy vs 50/50 al-tut
    line_series(cf, pv.equity.index, pv.equity, "equity", name="Strateji", role="bullish",
                width=2.0, fmt=",.0f")
    line_series(cf, pv.benchmark.index, pv.benchmark, "equity", name="50/50 Al-Tut",
                role="neutral", dash="dash", fmt=",.0f")

    # 3) Z-skor + eşikler + işlemler
    line_series(cf, pv.zscore.index, pv.zscore, "z", name="Z-Skor", role="warn")
    guide_level(cf, pv.entry_z, "z", dash="dash")
    guide_level(cf, -pv.entry_z, "z", dash="dash")
    guide_level(cf, 0.0, "z", dash="solid")

    for side, symbol, role in (("long", "triangle-up", "bullish"),
                               ("short", "triangle-down", "bearish")):
        group = [t for t in pv.trades if t.side == side]
        if not group:
            continue
        color = role_color(theme, role)
        cf.add(
            go.Scatter(
                x=[t.t for t in group], y=[t.z for t in group],
                mode="markers+text",
                marker=dict(symbol=symbol, size=11, color=color),
                text=[f"{t.leg} AL" for t in group],
                textposition="top center" if side == "long" else "bottom center",
                textfont=dict(family=METRICS.font_mono, size=9, color=color),
                name=f"{side} giriş",
                hovertemplate="%{text} · Z=%{y:+.2f}<extra></extra>", showlegend=False,
            ),
            "z",
        )

    # 4) Pair Health — ÇİFT EKSEN: solda korelasyon, sağda beta
    line_series(cf, pv.corr.index, pv.corr, "health", name="Rolling Korelasyon",
                role="accent", fmt=".2f")
    cf.add(
        go.Scatter(
            x=pv.beta.index, y=pv.beta, mode="lines", name="Rolling Beta",
            line=dict(color=role_color(theme, "warn"), width=METRICS.line_series),
            hovertemplate="Beta: %{y:.2f}<extra></extra>", showlegend=False,
        ),
        "health", observe=pv.beta, secondary=True,
    )
    return cf.finish()
