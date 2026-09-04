"""Mum gövdesi + fitil çizimi -- artifact'in `drawCandles` karşılığı.

Gövde min 1.1px, fitil ayrı `<line>`, yukarı/aşağı renkleri temadan --
artifact'la birebir aynı ilkeler."""

from __future__ import annotations

import pandas as pd

from tlab.viz.svg.prim import svg_line, svg_rect
from tlab.viz.svg.scale import Chart
from tlab.viz.svg.theme import SVGTheme


def draw_candles(
    df: pd.DataFrame, chart: Chart, theme: SVGTheme, width_frac: float | None = None,
) -> str:
    """`df`nin POZİSYONEL sırası (0..n-1) `chart.i_domain`e karşılık gelir
    -- çağıran taraf zaten pencerelenmiş bir df vermelidir."""
    cw = width_frac if width_frac is not None else theme.candle_w
    step_px = chart.x(1) - chart.x(0)
    half_w = max(0.9, step_px * cw / 2)
    out: list[str] = []
    for pos, (_, row) in enumerate(df.iterrows()):
        x = chart.x(pos)
        up = row["close"] >= row["open"]
        color = theme.up if up else theme.down
        out.append(
            svg_line(
                x, chart.y(float(row["high"])), x, chart.y(float(row["low"])),
                stroke=color, width=max(1.0, half_w * 0.22), opacity=theme.wick_opacity,
            )
        )
        top = chart.y(float(max(row["open"], row["close"])))
        bot = chart.y(float(min(row["open"], row["close"])))
        out.append(
            svg_rect(x - half_w, top, half_w * 2, max(1.1, bot - top), fill=color, rx=0.6)
        )
    return "".join(out)
