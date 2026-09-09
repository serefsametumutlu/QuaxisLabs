"""Yatay aralık grafiği. Referans: `önemli/HRjNKRZWAAAhfSy.png`."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from tlab.chart.frame import ChartFrame, Panel
from tlab.chart.marks import (
    Touch, boundary, candles, guide_level, line_series, pivot_markers,
    signal_box, volume, zone_band,
)
from tlab.chart.tokens import METRICS, ThemeName, role_color
from tlab.indicators.structure.range_box import RangeBox

_STATE_TR = {
    "gelisiyor": "GELİŞİYOR",
    "olgun": "OLGUN",
    "kirildi_yukari": "YUKARI KIRILDI",
    "kirildi_asagi": "AŞAĞI KIRILDI",
}


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss.replace(0, pd.NA)
    return (100 - 100 / (1 + rs)).fillna(50.0)


def compose(
    df: pd.DataFrame,
    box: RangeBox,
    *,
    symbol: str,
    timeframe: str = "1G",
    theme: ThemeName = "light",
    width: int = 1600,
    height: int = 900,
) -> go.Figure:
    cf = ChartFrame(
        panels=[
            Panel("price", METRICS.panel_ratio_price, "Fiyat"),
            Panel("volume", METRICS.panel_ratio_sub, "Hacim"),
            Panel("rsi", METRICS.panel_ratio_sub, "RSI", y_range=(0, 100)),
        ],
        theme=theme, width=width, height=height,
        title=f"{symbol} — YATAY ARALIK — {_STATE_TR[box.state]}",
        subtitle=(
            f"Periyot: {timeframe}  |  Destek: {box.support:,.2f}  |  "
            f"Direnç: {box.resistance:,.2f}  |  Yükseklik: %{box.height_pct * 100:.1f}  |  "
            f"Temas: {len(box.upper_touches)} üst / {len(box.lower_touches)} alt  |  "
            f"Kuruluş: {box.start_time.date()}"
        ),
    )

    # 1) Bant — tüm genişlikte, yumuşak; etiket sağ kenar boşluğunda
    zone_band(
        cf, box.support, box.resistance,
        role="accent", label=f"ARALIK · {box.touch_count} TEMAS",
    )

    # 2) Mumlar
    candles(cf, df)

    # 3) Sınırlar — YALNIZCA formasyonun kendi x aralığında
    x0, x1 = box.start_time, df.index[-1]
    boundary(
        cf, [(x0, box.resistance), (x1, box.resistance)],
        role="bearish", name="Direnç",
        touches=[
            Touch(t.bar_time, t.price, f"U{t.index}", above=True)
            for t in box.upper_touches
        ],
    )
    boundary(
        cf, [(x0, box.support), (x1, box.support)],
        role="bullish", name="Destek",
        touches=[
            Touch(t.bar_time, t.price, f"L{t.index}", above=False)
            for t in box.lower_touches
        ],
    )

    # 4) Güncel temas — son onaylanmış alt temas, sinyal kutusuyla
    if box.lower_touches and box.state in ("olgun", "gelisiyor"):
        last = box.lower_touches[-1]
        cf.add(
            go.Scatter(
                x=[last.bar_time], y=[last.price], mode="markers",
                marker=dict(
                    symbol="triangle-up", size=METRICS.marker_signal,
                    color=role_color(theme, "bullish"),
                ),
                name="Güncel temas",
                hovertemplate="Güncel temas: %{y:.2f}<extra></extra>", showlegend=False,
            ),
            "price",
        )
        signal_box(
            cf, last.bar_time, last.price,
            text=f"DESTEK TEMASI · L{last.index}", role="bullish", below=True,
        )

    # 5) Alt paneller
    volume(cf, df, panel="volume", ma=21)
    # RSI ısınma barları çizilmez: EWM ilk barlarda 0/100'e yapışır, bu
    # gerçek bir aşırı alım/satım değil, hesabın kendi artefaktıdır.
    warmup = 14 * 3
    rsi = _rsi(df["close"]).iloc[warmup:]
    line_series(cf, rsi.index, rsi, "rsi", name="RSI(14)", role="accent", fmt=".1f")
    guide_level(cf, 70, "rsi")
    guide_level(cf, 30, "rsi")

    return cf.finish()
