"""Cache'ten veri okuyup bir indikatörü ÇALIŞTIRIP render eden ince yardımcı.

`renderer.py`'nin kendisi hesap yapmaz (yalnızca zaten üretilmiş bir
`IndicatorResult`'ı çizer) — burası ise `tlab plot` CLI komutu ile
`report.py::ensure_chart`'ın PAYLAŞTIĞI, "sembol adından canlı grafiğe" kısa
yolu barındırır (CATALOG + Store + render tek yerde)."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from tlab.core.types import IndicatorResult, Market, Timeframe
from tlab.data.providers.yfinance_provider import YFinanceProvider
from tlab.data.store import Store
from tlab.indicators.bootstrap import CATALOG
from tlab.indicators.pairs.relative_momentum import RelativeMomentumPair, RelativeMomentumParams
from tlab.viz.renderer import render
from tlab.viz.themes import Theme

_TF_MAP = {"1H": Timeframe.H1, "4H": Timeframe.H4, "1D": Timeframe.D1, "W1": Timeframe.W1}


def compute_live(
    indicator_name: str, symbol: str, timeframe: str, market: str
) -> tuple[IndicatorResult, pd.DataFrame | None]:
    """`symbol` pair indikatörler için "Y/X" biçiminde olmalı (ör. "TCELL/ISCTR").
    Dönen df, pair modunda None'dır (renderer bu modda df istemez)."""
    if indicator_name not in CATALOG:
        raise ValueError(f"Bilinmeyen indikatör: {indicator_name} (bkz. tlab list-indicators)")
    spec = CATALOG[indicator_name]
    mkt = Market(market.lower())
    tf = _TF_MAP.get(timeframe.upper())
    if tf is None:
        raise ValueError(f"Geçersiz tf: {timeframe} (1h|4h|1d bekleniyor)")
    store = Store(YFinanceProvider())

    if spec.needs_context:
        if "/" not in symbol:
            raise ValueError("Pair indikatörler için symbol 'Y/X' biçiminde olmalı")
        y_sym, x_sym = symbol.split("/", 1)
        instance = (
            RelativeMomentumPair(RelativeMomentumParams(y_symbol=y_sym, x_symbol=x_sym))
            if indicator_name == "pair.relative_momentum"
            else spec.factory()
        )
        df_y = store.get(y_sym, tf, mkt)
        df_x = store.get(x_sym, tf, mkt)
        result = instance(df_y, context={"x": df_x})
        result.symbol = symbol
        return result, None

    instance = spec.factory()
    df = store.get(symbol, tf, mkt)
    result = instance(df)
    result.symbol = symbol
    return result, df


def render_live(
    indicator_name: str, symbol: str, timeframe: str, market: str,
    *, theme: Theme | str | None = "auto", last_n: int | None = None, declutter: bool = True,
) -> go.Figure:
    result, df = compute_live(indicator_name, symbol, timeframe, market)
    return render(result, df, theme=theme, last_n=last_n, declutter=declutter)
