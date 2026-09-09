"""Seri bindirmeli göstergeler: MA sistemleri ve EWMAC.

Kullanıcının `ma_systems` şikâyeti: *"ne olduğuna dair hiçbir şey
anlamıyorum"* — ve grafikte MA çizgileri DÜMDÜZ yataydı. Kök nedeni
`renderer.py:1488`'deki K1 hatasıydı: her `Line`, ilk ve son noktasına
indirgeniyordu, dolayısıyla bütün bir EMA serisi tek bir yatay çizgiye
çöküyordu.

Burada o hata yapısal olarak imkânsız: `marks.line_series` x ve y'yi TAM
DİZİ olarak geçirir. Ayrıca her serinin son değeri sağ kenarda yazar, ki
hangi çizginin hangisi olduğu efsane okumadan anlaşılsın.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go

from tlab.chart.frame import ChartFrame, Panel
from tlab.chart.marks import candles, line_series, signal_box, volume
from tlab.chart.tokens import METRICS, Role, ThemeName, role_color


@dataclass(frozen=True)
class OverlaySeries:
    name: str
    values: pd.Series
    role: Role
    dash: str | None = None


@dataclass(frozen=True)
class SeriesOverlay:
    title: str
    state: str
    series: tuple[OverlaySeries, ...]
    sub_series: tuple[OverlaySeries, ...] = ()
    sub_title: str = ""
    signal_t: pd.Timestamp | None = None
    signal_price: float | None = None
    signal_text: str = ""
    signal_role: Role = "bullish"
    bars_ago: int | None = None

    def __post_init__(self) -> None:
        if not self.series:
            raise ValueError("en az bir bindirme serisi gerekli")


def ma_system(df: pd.DataFrame, periods: tuple[int, ...] = (8, 21, 55, 200)) -> SeriesOverlay:
    """Klasik EMA yelpazesi + dizilim durumu."""
    roles: tuple[Role, ...] = ("bullish", "accent", "warn", "neutral")
    ser = tuple(
        OverlaySeries(f"EMA{p}", df["close"].ewm(span=p, adjust=False).mean(), roles[i % len(roles)])
        for i, p in enumerate(periods)
    )
    last = [float(s.values.iloc[-1]) for s in ser]
    if all(last[i] > last[i + 1] for i in range(len(last) - 1)):
        state = "TAM YÜKSELİŞ DİZİLİMİ"
    elif all(last[i] < last[i + 1] for i in range(len(last) - 1)):
        state = "TAM DÜŞÜŞ DİZİLİMİ"
    else:
        state = "KARIŞIK DİZİLİM"
    return SeriesOverlay(title="MA SİSTEMİ", state=state, series=ser)


def compose(
    df: pd.DataFrame,
    ov: SeriesOverlay,
    *,
    symbol: str,
    timeframe: str = "1G",
    theme: ThemeName = "light",
    width: int = 1600,
    height: int = 880,
) -> go.Figure:
    panels = [
        Panel("price", METRICS.panel_ratio_price + (0.0 if ov.sub_series else 0.10), "Fiyat"),
        Panel("volume", METRICS.panel_ratio_sub, "Hacim"),
    ]
    if ov.sub_series:
        panels.append(Panel("sub", METRICS.panel_ratio_sub, ov.sub_title or "Gösterge"))

    facts = [("Periyot", timeframe)]
    facts += [(s.name, f"{float(s.values.iloc[-1]):,.2f}") for s in ov.series]
    if ov.bars_ago is not None:
        facts.append(("Sinyal yaşı", f"{ov.bars_ago} bar"))

    cf = ChartFrame(
        panels=panels, theme=theme, width=width, height=height,
        title=f"{symbol} — {ov.title} — {ov.state}",
        subtitle="  |  ".join(f"{k}: {v}" for k, v in facts),
    )

    candles(cf, df)

    for s in ov.series:
        # TAM DİZİ geçilir; iki uca indirgenmez (K1 hatası burada olamaz).
        line_series(
            cf, s.values.index, s.values, "price",
            name=s.name, role=s.role, width=1.5, dash=s.dash,
        )
        # Sağ kenarda serinin adı ve son değeri: hangi çizgi hangisi,
        # efsaneye bakmadan anlaşılsın.
        cf.edge_label(
            "price", float(s.values.iloc[-1]),
            f"{s.name}: {float(s.values.iloc[-1]):,.2f}", role_color(theme, s.role),
        )

    if ov.signal_t is not None and ov.signal_price is not None:
        signal_box(
            cf, ov.signal_t, ov.signal_price, text=ov.signal_text,
            role=ov.signal_role, below=ov.signal_role == "bullish",
        )

    volume(cf, df, panel="volume", ma=21)

    for s in ov.sub_series:
        line_series(
            cf, s.values.index, s.values, "sub", name=s.name, role=s.role, dash=s.dash,
        )

    return cf.finish()
