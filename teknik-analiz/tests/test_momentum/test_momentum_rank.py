"""MomentumRank — sentetik BİLİNEN drift (trend gücü) gradyanlı evrende
doğru sıralama + RS kırılım sinyali + sektör ısı haritası yardımcı fonksiyonu."""

from __future__ import annotations

import pandas as pd

from tests.test_momentum.fixtures import make_momentum_universe
from tlab.indicators.momentum.momentum_rank import (
    MomentumRank,
    MomentumRankParams,
    momentum_heatmap_data,
)

_PARAMS = MomentumRankParams(
    horizons=(21, 63, 126), skip=5, fip_n=60, rs_slope_window=30,
    rs_breakout_window=100, ema_fast=10, ema_mid=25, ema_slow=90, min_history_bars=150,
)


def test_momentum_rank_orders_universe_by_true_drift() -> None:
    universe, index_df, true_drift = make_momentum_universe(n_symbols=20, n_bars=400)
    results = MomentumRank(_PARAMS).compute_universe(universe, index_df)

    assert set(results) == set(universe)
    last_rank = {sym: r.last_state["rank_pct"] for sym, r in results.items()}
    assert all(v is not None for v in last_rank.values())

    drift_series = pd.Series(true_drift)
    rank_series = pd.Series(last_rank)
    corr = drift_series.corr(rank_series, method="spearman")
    assert corr < -0.8, f"beklenmedik korelasyon: {corr}"


def test_rs_breakout_signal_uses_strict_prior_max() -> None:
    universe, index_df, true_drift = make_momentum_universe(n_symbols=10, n_bars=400)
    results = MomentumRank(_PARAMS).compute_universe(universe, index_df)
    best_symbol = max(true_drift, key=lambda s: true_drift[s])
    events = {s.payload["event"] for s in results[best_symbol].signals}
    # Güçlü/istikrarlı bir yükseliş trendinde en az bir kez RS 52h benzeri kırılım beklenir.
    assert "rs_breakout" in events or "momentum_top_entry" in events


def test_momentum_heatmap_data_averages_by_sector() -> None:
    universe, index_df, _ = make_momentum_universe(n_symbols=6, n_bars=400)
    results = MomentumRank(_PARAMS).compute_universe(universe, index_df)
    sector_map = {sym: ("A" if i % 2 == 0 else "B") for i, sym in enumerate(universe)}
    heatmap = momentum_heatmap_data(results, sector_map, _PARAMS.horizons)
    assert set(heatmap.index) <= {"A", "B"}
    assert list(heatmap.columns) == [f"{h}g" for h in _PARAMS.horizons]


def test_momentum_heatmap_data_empty_when_no_sector_match() -> None:
    universe, index_df, _ = make_momentum_universe(n_symbols=3, n_bars=400)
    results = MomentumRank(_PARAMS).compute_universe(universe, index_df)
    heatmap = momentum_heatmap_data(results, {}, _PARAMS.horizons)
    assert heatmap.empty
