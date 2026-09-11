"""Fibonacci geri çekilmesi grafiği. Referans: `önemli/HRhIeAdbcAAL2_B.png`.

Kullanıcının açık isteği (2026-09-05):
  *"ayrıca fibo da çizilmeli ve fiyatlar fibo değerleri yazılmalı"*
ve `0.5 - 261.75` gibi anlaşılmaz etiketlerin yerine referanstaki
`0.618: 185.00` biçimi.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from tlab.chart.frame import ChartFrame, Panel
from tlab.chart.marks import candles, fib_ladder, signal_box, volume, zone_band
from tlab.chart.tokens import METRICS, ThemeName, role_color
from tlab.indicators.structure.fib_retracement import FibRetracement


def compose(
    df: pd.DataFrame,
    fib: FibRetracement,
    *,
    symbol: str,
    timeframe: str = "1G",
    theme: ThemeName = "light",
    width: int = 1600,
    height: int = 880,
) -> go.Figure:
    yon = "YÜKSELİŞ" if fib.direction == "up" else "DÜŞÜŞ"
    durum = "ALTIN BÖLGEDE" if fib.in_golden_zone else "BÖLGE DIŞINDA"

    cf = ChartFrame(
        panels=[
            Panel("price", METRICS.panel_ratio_price + 0.10, "Fiyat"),
            Panel("volume", METRICS.panel_ratio_sub, "Hacim"),
        ],
        theme=theme, width=width, height=height,
        title=f"{symbol} — FİBONACCİ GERİ ÇEKİLME ({yon}) — {durum}",
        subtitle=(
            f"Periyot: {timeframe}  |  Bacak: {fib.start_price:,.2f} → {fib.end_price:,.2f}  |  "
            f"Genişlik: {fib.span:,.2f}  |  "
            f"Altın bölge: {fib.golden_low:,.2f} – {fib.golden_high:,.2f}  |  "
            f"{fib.start_time.date()} → {fib.end_time.date()}"
        ),
    )

    # 1) Altın bölge (0.382–0.618) — sağ kenarda etiketli
    # Kenar çizgisi YOK: 0.382 ve 0.618 fibo çizgileri bandın sınırlarını
    # zaten çiziyor; ikisi birden çizilince çift çizgi görünüyordu.
    zone_band(
        cf, fib.golden_low, fib.golden_high,
        role="warn", label="ALTIN BÖLGE", border=False,
    )

    # 2) Mumlar
    candles(cf, df)

    # 3) Baskın bacak — kesikli, ince; formasyonun kaynağını gösterir
    cf.add(
        go.Scatter(
            x=[fib.start_time, fib.end_time], y=[fib.start_price, fib.end_price],
            mode="lines+markers", name="Baskın bacak",
            line=dict(color=role_color(theme, "neutral"), width=1.6, dash="dash"),
            marker=dict(size=7, symbol="circle-open",
                        color=role_color(theme, "neutral"), line=dict(width=1.6)),
            hovertemplate="Bacak ucu: %{y:,.2f}<extra></extra>", showlegend=False,
        ),
        "price",
        observe=[fib.start_price, fib.end_price],
    )

    # 4) Fibo merdiveni — her seviye kendi renginde, etiket SAĞDA "oran: fiyat"
    fib_ladder(cf, [(lv.ratio, lv.price, lv.label) for lv in fib.levels])

    # 5) Fiyat altın bölgedeyse sinyal kutusu
    if fib.in_golden_zone:
        signal_box(
            cf, df.index[-1], float(df["close"].iloc[-1]),
            text="ALTIN BÖLGE TEPKİSİ",
            role="bullish" if fib.direction == "up" else "bearish",
            below=fib.direction == "up",
        )

    # Swing'e odaklan; fib merdiveni zaten bu bacaktan türüyor.
    cf.focus(df, min(fib.start_time, fib.end_time), max(fib.start_time, fib.end_time))

    volume(cf, df, panel="volume", ma=21)
    return cf.finish()
