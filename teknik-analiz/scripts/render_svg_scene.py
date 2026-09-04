"""SVG sahne doğrulama döngüsü: gerçek veriyle SVG üret, `resvg_py` ile
PNG'ye çevir, `docs/design/iterasyon/`e kaydet -- Faz 3'te `patterns.
double_top_bottom` için kullanıldı, Faz 4'te kalan 18 sahne portlanırken
AYNI döngü için tekrar kullanılabilir (yalnızca indikatör/params sabitlerini
değiştirmek yeterli).

Kullanım: `python scripts/render_svg_scene.py [SEMBOL] [TEMA] [ETİKET]`
(varsayılan: BAKAB classic iter1)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import resvg_py

from tlab.core.types import Market, Timeframe
from tlab.data.providers.yfinance_provider import YFinanceProvider
from tlab.data.store import Store
from tlab.indicators.patterns.double_top_bottom import (
    DoubleTopBottomIndicator,
    DoubleTopBottomParams,
)
from tlab.viz.svg import render_svg

OUT_DIR = Path(__file__).resolve().parents[1] / "docs" / "design" / "iterasyon"
OUT_DIR.mkdir(parents=True, exist_ok=True)

store = Store(YFinanceProvider())


def render_one(symbol: str, theme: str, tag: str) -> None:
    df = store.get(symbol, Timeframe.D1, Market.BIST)
    result = DoubleTopBottomIndicator(DoubleTopBottomParams())(df)
    result.symbol = symbol
    svg_text = render_svg(result, df, theme=theme)
    svg_path = OUT_DIR / f"{tag}_{symbol}_{theme}.svg"
    svg_path.write_text(svg_text, encoding="utf-8")
    png_bytes = resvg_py.svg_to_bytes(svg_string=svg_text)
    png_path = OUT_DIR / f"{tag}_{symbol}_{theme}.png"
    png_path.write_bytes(bytes(png_bytes))
    print(f"wrote {png_path}")


if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "BAKAB"
    theme = sys.argv[2] if len(sys.argv) > 2 else "classic"
    tag = sys.argv[3] if len(sys.argv) > 3 else "iter1"
    render_one(symbol, theme, tag)
