"""Faz 8D görev notu madde 6: "universe-level repaint testi (evren
sözlüğünün her df'si aynı cut'ta kesilir; rank'lar kesik ⊆ tam)" —
`tlab/testing/repaint.py::universe_repaint_test` ile AlphaRank/MomentumRank
için doğrulama. Küçük evren/pencere (hız için) — mantık büyük evrenden
bağımsız."""

from __future__ import annotations

from tests.test_momentum.fixtures import make_alpha_universe, make_momentum_universe
from tlab.indicators.momentum.alpha_rank import AlphaRank, AlphaRankParams
from tlab.indicators.momentum.momentum_rank import MomentumRank, MomentumRankParams
from tlab.testing.repaint import universe_repaint_test


def test_alpha_rank_universe_repaint() -> None:
    universe, index_df, _ = make_alpha_universe(n_symbols=6, n_bars=200)
    params = AlphaRankParams(
        windows=(20, 40), min_liquidity_try=0.0, liquidity_window=5, min_history_bars=60,
    )
    indicator = AlphaRank(params)
    cut_dates = list(index_df.index[-15::3])
    report = universe_repaint_test(indicator, universe, index_df, cut_dates=cut_dates)
    assert report.passed, report.mismatches


def test_momentum_rank_universe_repaint() -> None:
    universe, index_df, _ = make_momentum_universe(n_symbols=6, n_bars=200)
    params = MomentumRankParams(
        horizons=(10, 20), skip=2, fip_n=20, rs_slope_window=15, rs_breakout_window=40,
        ema_fast=5, ema_mid=10, ema_slow=30, min_history_bars=60,
    )
    indicator = MomentumRank(params)
    cut_dates = list(index_df.index[-15::3])
    report = universe_repaint_test(indicator, universe, index_df, cut_dates=cut_dates)
    assert report.passed, report.mismatches
