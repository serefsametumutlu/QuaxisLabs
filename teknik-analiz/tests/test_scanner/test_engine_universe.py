"""Faz 8D: `scanner/engine.py`'nin "universe" kategorisi (`needs_universe`)
işi (`_run_universe_worker`) + düz `IndicatorRunResult` listesine açma
(`_universe_result_to_runs`). Gerçek ağ/parquet CACHE'İ gerektirmez —
`_fetch_and_prepare` monkeypatch'lenir (sentetik veri, `tests/
test_momentum/fixtures.py`'den)."""

from __future__ import annotations

import pytest

from tests.test_momentum.fixtures import make_alpha_universe
from tlab.core.types import Market
from tlab.data.universe import BENCHMARK_SYMBOL
from tlab.scanner import engine


@pytest.fixture
def _synthetic(monkeypatch: pytest.MonkeyPatch):
    universe, index_df, _ = make_alpha_universe(n_symbols=5, n_bars=300)
    bench_symbol = BENCHMARK_SYMBOL[Market.BIST]

    def fake_fetch(symbol, market, timeframe, lookback_bars, drop_open_bar):
        if symbol == bench_symbol:
            return index_df
        if symbol in universe:
            return universe[symbol]
        raise FileNotFoundError(symbol)

    monkeypatch.setattr(engine, "_fetch_and_prepare", fake_fetch)
    return universe


def test_run_universe_worker_reports_per_symbol_errors(_synthetic: dict) -> None:
    symbols = list(_synthetic) + ["MISSING"]
    raw = engine._run_universe_worker(
        "momentum.alpha_rank", "bist", "1D", symbols, 600, True,
    )
    assert raw["error"] is None
    assert raw["symbol_errors"] == {"MISSING": "FileNotFoundError: MISSING"}
    assert set(raw["symbol_results"]) <= set(_synthetic)
    assert len(raw["symbol_results"]) > 0


def test_universe_result_to_runs_flattens_results_and_errors(_synthetic: dict) -> None:
    symbols = list(_synthetic) + ["MISSING"]
    raw = engine._run_universe_worker(
        "momentum.alpha_rank", "bist", "1D", symbols, 600, True,
    )
    runs = engine._universe_result_to_runs(raw)
    ok_runs = [r for r in runs if r.error is None]
    err_runs = [r for r in runs if r.error is not None]

    assert len(ok_runs) == len(raw["symbol_results"])
    assert len(err_runs) == 1
    assert err_runs[0].symbol == "MISSING"
    assert all(r.result is not None and r.params_hash for r in ok_runs)


def test_universe_worker_top_level_error_becomes_single_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broken_fetch(*args, **kwargs):
        raise ValueError("endeks verisi yok")

    monkeypatch.setattr(engine, "_fetch_and_prepare", broken_fetch)
    raw = engine._run_universe_worker("momentum.alpha_rank", "bist", "1D", ["TCELL"], 600, True)
    runs = engine._universe_result_to_runs(raw)
    assert len(runs) == 1
    assert runs[0].error is not None
    assert runs[0].symbol.startswith("__universe__:")
