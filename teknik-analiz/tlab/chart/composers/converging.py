"""Üçgen / kama / genişleyen formasyon grafiği.

`boundary_pattern` komposerinin ince bir sarmalayıcısı — tıpkı
`channel.py` gibi. Bu dosyanın kısalığı kasıtlı: beş formasyon türü de
aynı şablonu kullanır, fark yalnızca sınırların geometrisi ve vurgu
rengidir.

Referanslar: `önemli/HRiPy4qbUAA1bKc.png` (simetrik üçgen),
`önemli/HRihBa2WIAIZjP_.png` (alçalan üçgen, numaralı temaslar).
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from tlab.chart.composers.boundary_pattern import compose as compose_boundary
from tlab.chart.contracts import BoundaryLine, BoundaryPattern, BoundaryTouch, ChartSignal
from tlab.chart.tokens import Role, ThemeName
from tlab.indicators.patterns.converging import ConvergingPattern

_KIND_TR = {
    "simetrik_ucgen": "SİMETRİK ÜÇGEN",
    "yukselen_ucgen": "YÜKSELEN ÜÇGEN",
    "alcalan_ucgen": "ALÇALAN ÜÇGEN",
    "yukselen_kama": "YÜKSELEN KAMA",
    "alcalan_kama": "ALÇALAN KAMA",
    "genisleyen": "GENİŞLEYEN FORMASYON",
}
_STATE_TR = {
    "olusuyor": "OLUŞUYOR",
    "onaylandi": "KIRILIM ONAYLANDI",
    "suresi_doldu": "SÜRESİ DOLDU",
}


def to_pattern(cp: ConvergingPattern) -> BoundaryPattern:
    role: Role = "bullish" if cp.direction == "long" else (
        "bearish" if cp.direction == "short" else "accent"
    )
    signal = None
    if cp.breakout is not None:
        t, price = cp.breakout
        up = cp.breakout_side == "upper"
        signal = ChartSignal(
            t=t, price=price,
            text="AL / KIRILIM" if up else "SAT / KIRILIM",
            role="bullish" if up else "bearish", below=up,
        )

    facts = [
        ("Süre", f"{cp.bars} bar"),
        ("Genişlik değişimi", f"%{cp.width_change_pct * 100:+.0f}"),
        ("Temas", f"{len(cp.upper_touches)} üst / {len(cp.lower_touches)} alt"),
    ]
    if cp.vol_contraction == cp.vol_contraction:      # NaN değilse
        facts.append(("Hacim daralması", f"{cp.vol_contraction:.2f}x"))
    if cp.target is not None:
        facts.append(("Hedef", f"{cp.target:,.2f}"))

    return BoundaryPattern(
        kind=cp.kind,
        title=_KIND_TR[cp.kind],
        state=_STATE_TR[cp.state],
        boundaries=(
            BoundaryLine(
                points=cp.upper, role=role, name="Üst Sınır", dash="solid",
                touches=tuple(
                    BoundaryTouch(t.bar_time, t.price, f"U{t.index}", True)
                    for t in cp.upper_touches
                ),
            ),
            BoundaryLine(
                points=cp.lower, role=role, name="Alt Sınır", dash="solid",
                touches=tuple(
                    BoundaryTouch(t.bar_time, t.price, f"L{t.index}", False)
                    for t in cp.lower_touches
                ),
            ),
        ),
        facts=tuple(facts),
        signal=signal,
        bars_ago=cp.bars_ago,
    )


def compose(
    df: pd.DataFrame, cp: ConvergingPattern, *, symbol: str, timeframe: str = "1G",
    theme: ThemeName = "light", width: int = 1600, height: int = 900,
) -> go.Figure:
    return compose_boundary(
        df, to_pattern(cp), symbol=symbol, timeframe=timeframe,
        theme=theme, width=width, height=height, lower_panel="rsi",
    )
