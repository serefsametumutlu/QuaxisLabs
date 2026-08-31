"""Faz 8D evren-geneli görselleri — duman testi (hesap değil, salt Plotly
figürünün hatasız üretilmesi; sayısal doğruluk `test_momentum/` altında)."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from tests.test_momentum.fixtures import make_alpha_universe, make_momentum_universe
from tlab.indicators.momentum.alpha_rank import AlphaRank, AlphaRankParams
from tlab.indicators.momentum.momentum_rank import (
    MomentumRank,
    MomentumRankParams,
    momentum_heatmap_data,
)
from tlab.viz.universe_charts import render_alpha_scatter, render_momentum_heatmap


def test_render_alpha_scatter_smoke() -> None:
    universe, index_df, _ = make_alpha_universe(n_symbols=8, n_bars=300)
    params = AlphaRankParams(windows=(30, 60), min_liquidity_try=0.0, min_history_bars=100)
    results = AlphaRank(params).compute_universe(universe, index_df)
    fig = render_alpha_scatter(results)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1


def test_render_momentum_heatmap_smoke() -> None:
    universe, index_df, _ = make_momentum_universe(n_symbols=6, n_bars=300)
    params = MomentumRankParams(
        horizons=(21, 63), skip=5, rs_slope_window=30, rs_breakout_window=100,
        min_history_bars=100,
    )
    results = MomentumRank(params).compute_universe(universe, index_df)
    sector_map = {sym: ("A" if i % 2 == 0 else "B") for i, sym in enumerate(universe)}
    heatmap_df = momentum_heatmap_data(results, sector_map, params.horizons)
    fig = render_momentum_heatmap(heatmap_df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1


def test_render_momentum_heatmap_handles_empty_frame() -> None:
    empty = pd.DataFrame(columns=["21g", "63g"])
    fig = render_momentum_heatmap(empty)
    assert isinstance(fig, go.Figure)
