"""AlphaRank — sentetik BİLİNEN alfa gradyanlı evrende doğru sıralama
(Faz 8D görev notu madde 6) + likidite filtresi + `compute_universe`
sözleşmesi (dönen sözlük `universe`'in alt kümesi)."""

from __future__ import annotations

import pandas as pd

from tests.test_momentum.fixtures import make_alpha_universe
from tlab.indicators.momentum.alpha_rank import AlphaRank, AlphaRankParams

_PARAMS = AlphaRankParams(
    windows=(30, 60, 90), min_liquidity_try=0.0, liquidity_window=10, min_history_bars=100,
)


def test_alpha_rank_orders_universe_by_true_alpha() -> None:
    universe, index_df, true_alpha = make_alpha_universe(n_symbols=20, n_bars=400)
    results = AlphaRank(_PARAMS).compute_universe(universe, index_df)

    assert set(results) == set(universe)
    last_rank = {sym: r.last_state["rank_pct"] for sym, r in results.items()}
    assert all(v is not None for v in last_rank.values())

    alpha_series = pd.Series(true_alpha)
    rank_series = pd.Series(last_rank)
    corr = alpha_series.corr(rank_series, method="spearman")
    # Yüksek alfa -> DÜŞÜK rank_pct (en iyi = en küçük) -> negatif korelasyon beklenir.
    assert corr < -0.85, f"beklenmedik korelasyon: {corr}"

    best_symbol = max(true_alpha, key=lambda s: true_alpha[s])
    worst_symbol = min(true_alpha, key=lambda s: true_alpha[s])
    assert last_rank[best_symbol] < last_rank[worst_symbol]


def test_alpha_entry_signal_fires_somewhere_in_universe() -> None:
    # NOT: en yüksek alfalı sembol, ölçülebilir İLK bardan itibaren zaten
    # top_pct İÇİNDE olabilir (`before` NaN -> "giriş" tanımsız, repaint
    # değil — bkz. alpha_rank.py). Bu yüzden TEK bir sembole değil, evrenin
    # TAMAMINA bakılır: sentetik alfa gradyanı (bazı semboller sınıra
    # yakın) en az bir gerçek giriş/çıkış geçişi üretmeli.
    universe, index_df, true_alpha = make_alpha_universe(n_symbols=20, n_bars=400)
    results = AlphaRank(_PARAMS).compute_universe(universe, index_df)
    all_events = {
        s.payload["event"] for r in results.values() for s in r.signals
    }
    assert "alpha_entry" in all_events


def test_liquidity_filter_excludes_illiquid_symbols() -> None:
    universe, index_df, _ = make_alpha_universe(n_symbols=8, n_bars=200)
    strict_params = AlphaRankParams(
        windows=(30, 60), min_liquidity_try=1e12, liquidity_window=10, min_history_bars=100,
    )
    results = AlphaRank(strict_params).compute_universe(universe, index_df)
    assert all(r.last_state["rank_pct"] is None for r in results.values())
    assert all(r.last_state["liquidity_ok"] is False for r in results.values())


def test_compute_universe_result_is_subset_of_input() -> None:
    universe, index_df, _ = make_alpha_universe(n_symbols=5, n_bars=50)  # yetersiz geçmiş
    results = AlphaRank(_PARAMS).compute_universe(universe, index_df)
    assert set(results) <= set(universe)
    assert results == {}  # min_history_bars=100 > 50 bar -> hiçbir sembol yeterli değil
