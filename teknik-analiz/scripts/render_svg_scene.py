"""SVG sahne doğrulama döngüsü: gerçek veriyle SVG üret, `resvg_py` ile
PNG'ye çevir, `docs/design/iterasyon/`e kaydet -- Faz 3'te `patterns.
double_top_bottom` için kullanıldı, Faz 4'te kalan sahneler portlanırken
AYNI döngü için tekrar kullanılabilir (yalnızca indikatör/params sabitlerini
değiştirmek yeterli).

Kullanım: `python scripts/render_svg_scene.py [İNDİKATÖR] [SEMBOL] [TF]
[TEMA] [ETİKET]` (varsayılan: patterns.double_top_bottom BAKAB 1D classic
iter1)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import resvg_py

from tlab.core.types import Market, Timeframe
from tlab.data.providers.yfinance_provider import YFinanceProvider
from tlab.data.store import Store
from tlab.indicators.bootstrap import scaled_factory
from tlab.viz.live import (
    REVERSAL_MAP_NAME,
    STRUCTURE_REPORT_NAME,
    compute_reversal_map,
    compute_structure_report_merged,
)
from tlab.viz.svg import render_svg

OUT_DIR = Path(__file__).resolve().parents[1] / "docs" / "design" / "iterasyon"
OUT_DIR.mkdir(parents=True, exist_ok=True)

store = Store(YFinanceProvider())
_TF_MAP = {"1D": Timeframe.D1, "4H": Timeframe.H4}


def render_one(indicator: str, symbol: str, tf_label: str, theme: str, tag: str) -> None:
    if indicator == STRUCTURE_REPORT_NAME:
        # "structure.report" iki ayrı indikatörün (price_structure +
        # swing_fib_abcd) BİRLEŞİMİ -- scaled_factory tek-indikatör
        # varsayımıyla çalışmaz, live.py'nin kendi birleştiricisi kullanılır.
        result, df = compute_structure_report_merged(symbol, tf_label, "bist")
    elif indicator == REVERSAL_MAP_NAME:
        result, df = compute_reversal_map(symbol, tf_label, "bist")
    else:
        tf = _TF_MAP[tf_label]
        df = store.get(symbol, tf, Market.BIST)
        inst = scaled_factory(indicator, tf)
        result = inst(df)
        result.symbol = symbol
        result.timeframe = tf
    svg_text = render_svg(result, df, theme=theme)
    scene_tag = indicator.split(".")[-1]
    svg_path = OUT_DIR / f"{tag}_{scene_tag}_{symbol}_{tf_label}_{theme}.svg"
    svg_path.write_text(svg_text, encoding="utf-8")
    png_bytes = resvg_py.svg_to_bytes(svg_string=svg_text)
    png_path = OUT_DIR / f"{tag}_{scene_tag}_{symbol}_{tf_label}_{theme}.png"
    png_path.write_bytes(bytes(png_bytes))
    print(f"wrote {png_path}")


if __name__ == "__main__":
    indicator = sys.argv[1] if len(sys.argv) > 1 else "patterns.double_top_bottom"
    symbol = sys.argv[2] if len(sys.argv) > 2 else "BAKAB"
    tf_label = sys.argv[3] if len(sys.argv) > 3 else "1D"
    theme = sys.argv[4] if len(sys.argv) > 4 else "classic"
    tag = sys.argv[5] if len(sys.argv) > 5 else "iter1"
    render_one(indicator, symbol, tf_label, theme, tag)
