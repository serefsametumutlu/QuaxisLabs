"""Kanal grafiği — `boundary_pattern` komposerinin ince bir sarmalayıcısı.

Referans: `önemli/HRiOTwUbQAA9WKw.png` (yükselen kanal, alt bant teması).
Bu dosyanın kısalığı kasıtlı: kanal ile üçgen/kama/aralık AYNI şablonu
kullanır, fark yalnızca sınırların geometrisi. Ortak iş
`composers/boundary_pattern.py`'de bir kez yazıldı.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from tlab.chart.composers.boundary_pattern import compose as compose_boundary
from tlab.chart.contracts import BoundaryLine, BoundaryPattern, BoundaryTouch, ChartSignal
from tlab.chart.tokens import ThemeName
from tlab.indicators.trend.channel import Channel

_DIR_TR = {"yukselen": "YÜKSELEN KANAL", "alcalan": "ALÇALAN KANAL", "yatay": "YATAY KANAL"}


def to_pattern(ch: Channel) -> BoundaryPattern:
    role = "bullish" if ch.direction == "yukselen" else (
        "bearish" if ch.direction == "alcalan" else "accent"
    )
    signal = None
    if ch.current_touch is not None:
        cur = ch.current_touch
        alt = cur.side == "lower"
        signal = ChartSignal(
            t=cur.bar_time, price=cur.price,
            text=f"GÜNCEL TEMAS · {'L' if alt else 'U'}{cur.index}",
            role="bullish" if alt else "bearish", below=alt,
        )
    return BoundaryPattern(
        kind="kanal",
        title=_DIR_TR[ch.direction],
        state=ch.state,
        boundaries=(
            BoundaryLine(
                points=ch.upper_at, role=role, name="Üst Sınır", dash="dash",
                touches=tuple(
                    BoundaryTouch(t.bar_time, t.price, f"U{t.index}", True)
                    for t in ch.upper_touches
                ),
            ),
            BoundaryLine(
                points=ch.lower_at, role=role, name="Alt Sınır", dash="dash",
                touches=tuple(
                    BoundaryTouch(t.bar_time, t.price, f"L{t.index}", False)
                    for t in ch.lower_touches
                ),
            ),
        ),
        facts=(
            ("Eğim", f"{ch.slope_per_bar:+.4f}/bar"),
            ("Genişlik", f"%{ch.width_pct * 100:.1f}"),
            ("Temas", f"{len(ch.upper_touches)} üst / {len(ch.lower_touches)} alt"),
        ),
        signal=signal,
        bars_ago=ch.bars_ago,
    )


def compose(
    df: pd.DataFrame, ch: Channel, *, symbol: str, timeframe: str = "1G",
    theme: ThemeName = "light", width: int = 1600, height: int = 900,
) -> go.Figure:
    return compose_boundary(
        df, to_pattern(ch), symbol=symbol, timeframe=timeframe,
        theme=theme, width=width, height=height, lower_panel="macd",
    )
