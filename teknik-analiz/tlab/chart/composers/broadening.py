"""Genişleyen formasyon grafiği — `patterns.broadening`.

`boundary_pattern` komposerinin ince bir sarmalayıcısı. Girdi zaten tipli
`BoundaryPattern` — `tlab/indicators/patterns/boundary_adapter.py::
to_pattern(BroadeningIndicator()(df), df)` çağrısından gelir (bu dosya
HESAP YAPMAZ, yalnızca çizer).
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from tlab.chart.composers.boundary_pattern import compose as compose_boundary
from tlab.chart.contracts import BoundaryPattern
from tlab.chart.tokens import ThemeName


def compose(
    df: pd.DataFrame, pat: BoundaryPattern, *, symbol: str, timeframe: str = "1G",
    theme: ThemeName = "light", width: int = 1600, height: int = 900,
) -> go.Figure:
    return compose_boundary(
        df, pat, symbol=symbol, timeframe=timeframe,
        theme=theme, width=width, height=height, lower_panel="rsi",
    )
