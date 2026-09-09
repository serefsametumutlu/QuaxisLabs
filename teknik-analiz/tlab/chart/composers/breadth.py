"""Piyasa genişliği — yükseliş kaç hisseye yayıldı?

Kaynak: "Fiyatın Ardında" raporu, *"Endeks yükselirken katılım zayıf
kalıyor"*. İki ölçü birlikte okunur:

  - **Kümülatif yükselen-düşen farkı (A-D çizgisi)**: her gün yükselen ve
    düşen hisse sayısı farkının birikimli toplamı.
  - **50 günlük ortalamasının üzerindeki hisse oranı.**

Raporun kilit tespiti: *"endeks görünümü toparlansa bile hisselerin çoğu
henüz aynı yönde hareket etmiyor"* — yani endeks ile genişlik AYRIŞABİLİR
ve ayrışma önemlidir. Bu yüzden endeks üstte, genişlik altta, aynı x
ekseninde çizilir; ayrışma gözle görülür.

Hesap yapmaz, çizer.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go

from tlab.chart.frame import ChartFrame, Panel
from tlab.chart.marks import guide_level, line_series
from tlab.chart.tokens import METRICS, ThemeName


@dataclass(frozen=True)
class BreadthView:
    index_name: str
    index_close: pd.Series
    ad_cumulative: pd.Series        # kümülatif yükselen-düşen farkı
    pct_above_ma: pd.Series         # 0..100
    ma_period: int = 50
    universe_size: int = 0

    def __post_init__(self) -> None:
        if self.pct_above_ma.dropna().empty:
            raise ValueError("boş genişlik serisi")
        hi = float(self.pct_above_ma.max())
        if hi <= 1.0:
            raise ValueError("pct_above_ma yüzde olmalı (0-100), oran değil")


def compose(
    bv: BreadthView,
    *,
    theme: ThemeName = "light",
    width: int = 1600,
    height: int = 880,
) -> go.Figure:
    ad_last = float(bv.ad_cumulative.dropna().iloc[-1])
    pct_last = float(bv.pct_above_ma.dropna().iloc[-1])

    if pct_last >= 60 and ad_last > 0:
        durum = "GENİŞ KATILIM"
    elif pct_last <= 40 or ad_last < 0:
        durum = "KATILIM ZAYIF"
    else:
        durum = "KARARSIZ"

    cf = ChartFrame(
        panels=[
            Panel("index", 0.44, bv.index_name),
            Panel("ad", 0.28, "Kümülatif A-D"),
            Panel("pct", 0.28, f"MA{bv.ma_period} üzeri %", y_range=(0, 100)),
        ],
        theme=theme, width=width, height=height,
        title=f"PİYASA GENİŞLİĞİ — {durum}",
        subtitle=(
            f"{bv.index_name}  |  Evren: {bv.universe_size or len(bv.index_close)} hisse  |  "
            f"Kümülatif A-D: {ad_last:+,.0f}  |  "
            f"MA{bv.ma_period} üzeri: %{pct_last:.0f}  |  "
            "Endeks ile genişlik ayrışıyorsa yükseliş dar bir gruba dayanıyor olabilir"
        ),
    )

    line_series(cf, bv.index_close.index, bv.index_close, "index",
                name=bv.index_name, role="neutral", width=1.8, fmt=",.0f")

    cf.add(
        go.Scatter(
            x=bv.ad_cumulative.index, y=bv.ad_cumulative, mode="lines",
            name="Kümülatif A-D", fill="tozeroy",
            line=dict(color=cf.pal.accent, width=1.6),
            fillcolor=f"rgba(0,0,0,0)",
            hovertemplate="A-D: %{y:+,.0f}<extra></extra>", showlegend=False,
        ),
        "ad", observe=bv.ad_cumulative,
    )
    guide_level(cf, 0.0, "ad", dash="solid")

    line_series(cf, bv.pct_above_ma.index, bv.pct_above_ma, "pct",
                name=f"MA{bv.ma_period} üzeri %", role="warn", fmt=".0f")
    for lvl in (40.0, 60.0):
        guide_level(cf, lvl, "pct")

    return cf.finish()
