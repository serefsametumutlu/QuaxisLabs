"""Sınır-çizgili formasyonların ORTAK grafiği.

Tek komposer, altı göstergeyi karşılar: yatay aralık, kanal, üçgen, kama,
genişleyen formasyon, kırılım. Referans görsellerde de durum budur —
`HRiOTwUbQAA9WKw` (kanal) ile `HRiPy4qbUAA1bKc` (üçgen) aynı şablonun iki
örneği.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from tlab.chart.contracts import BoundaryPattern
from tlab.chart.frame import ChartFrame, Panel
from tlab.chart.marks import (
    Touch, boundary, candles, guide_level, line_series, signal_box, volume, zone_band,
)
from tlab.chart.tokens import METRICS, ThemeName


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    return (100 - 100 / (1 + gain / loss.replace(0, pd.NA))).fillna(50.0)


def macd(close: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    fast = close.ewm(span=12, adjust=False).mean()
    slow = close.ewm(span=26, adjust=False).mean()
    line = fast - slow
    signal = line.ewm(span=9, adjust=False).mean()
    return line, signal, line - signal


def compose(
    df: pd.DataFrame,
    pat: BoundaryPattern,
    *,
    symbol: str,
    timeframe: str = "1G",
    theme: ThemeName = "light",
    width: int = 1600,
    height: int = 900,
    lower_panel: str = "rsi",          # "rsi" | "macd" | "none"
) -> go.Figure:
    panels = [
        Panel("price", METRICS.panel_ratio_price, "Fiyat"),
        Panel("volume", METRICS.panel_ratio_sub, "Hacim"),
    ]
    if lower_panel == "rsi":
        panels.append(Panel("rsi", METRICS.panel_ratio_sub, "RSI", y_range=(0, 100)))
    elif lower_panel == "macd":
        panels.append(Panel("macd", METRICS.panel_ratio_sub, "MACD"))

    facts = list(pat.facts)
    facts.insert(0, ("Periyot", timeframe))
    if pat.bars_ago is not None:
        # Kullanıcının 1 numaralı kuralı: sinyalin YAŞI görünür olmalı.
        facts.append(("Sinyal yaşı", f"{pat.bars_ago} bar"))
    subtitle = "  |  ".join(f"{k}: {v}" for k, v in facts)

    cf = ChartFrame(
        panels=panels, theme=theme, width=width, height=height,
        title=f"{symbol} — {pat.title} — {pat.state}",
        subtitle=subtitle,
    )

    if pat.band is not None:
        lo, hi = pat.band
        zone_band(cf, lo, hi, role=pat.band_role, label=pat.band_label or pat.kind.upper())

    candles(cf, df)

    for b in pat.boundaries:
        boundary(
            cf, list(b.points), role=b.role, name=b.name, dash=b.dash,
            touches=[Touch(t.t, t.price, t.label, t.above) for t in b.touches],
        )

    if pat.signal is not None:
        s = pat.signal
        cf.add(
            go.Scatter(
                x=[s.t], y=[s.price], mode="markers",
                marker=dict(
                    symbol="triangle-up" if s.below else "triangle-down",
                    size=METRICS.marker_signal,
                    color=cf.pal.bullish if s.role == "bullish" else cf.pal.bearish,
                ),
                name=s.text, hovertemplate=f"{s.text}: %{{y:,.2f}}<extra></extra>",
                showlegend=False,
            ),
            "price",
        )
        signal_box(cf, s.t, s.price, text=s.text, role=s.role, below=s.below)

    volume(cf, df, panel="volume", ma=21)

    if lower_panel == "rsi":
        warm = 42
        r = rsi(df["close"]).iloc[warm:]
        line_series(cf, r.index, r, "rsi", name="RSI(14)", role="accent", fmt=".1f")
        guide_level(cf, 70, "rsi")
        guide_level(cf, 30, "rsi")
    elif lower_panel == "macd":
        warm = 60
        line, sig, hist = (s.iloc[warm:] for s in macd(df["close"]))
        cf.add(
            go.Bar(
                x=hist.index, y=hist, name="MACD Hist",
                marker=dict(
                    color=[cf.pal.candle_up if v >= 0 else cf.pal.candle_down for v in hist],
                    line=dict(width=0),
                ),
                hovertemplate="Hist: %{y:.3f}<extra></extra>", showlegend=False,
            ),
            "macd", observe=hist,
        )
        line_series(cf, line.index, line, "macd", name="MACD", role="accent", fmt=".3f")
        line_series(cf, sig.index, sig, "macd", name="Sinyal", role="warn", fmt=".3f")

    return cf.finish()
