"""Faz 0, İş 1 — sinyal tazeliği: `engine.py::_add_bars_ago` + `ResultsStore`
`bars_ago` kolonu/`max_bars_ago` filtresi.

Ağdan ve gerçek veri önbelleğinden BAĞIMSIZ: `tlab/testing/fixtures.py`'nin
sentetik OHLCV'si ve elle kurulmuş `IndicatorResult`/`Signal` nesneleri
kullanılır."""

from __future__ import annotations

from pathlib import Path

from tlab.core.types import IndicatorResult, Signal, Timeframe
from tlab.scanner import engine
from tlab.scanner.results import ResultsStore, RunRecord, SymbolIndicatorRun
from tlab.testing.fixtures import make_trend


def _result_with_signal_at(df, pos: int, indicator: str = "test.bars_ago") -> IndicatorResult:
    bar_time = df.index[pos]
    return IndicatorResult(
        indicator=indicator, version="0.1.0", params_hash="h1",
        symbol="TEST", timeframe=Timeframe.D1,
        signals=[
            Signal(
                bar_time=bar_time, detected_at=bar_time, direction="long",
                state="confirmed", score=0.9, payload={},
            )
        ],
    )


def test_add_bars_ago_last_bar_is_zero() -> None:
    df = make_trend(n=50)
    result = _result_with_signal_at(df, pos=len(df) - 1)
    engine._add_bars_ago(result, df)
    assert result.signals[0].payload["bars_ago"] == 0


def test_add_bars_ago_counts_bars_not_calendar_days() -> None:
    df = make_trend(n=50)
    result = _result_with_signal_at(df, pos=len(df) - 6)
    engine._add_bars_ago(result, df)
    assert result.signals[0].payload["bars_ago"] == 5


def test_add_bars_ago_noop_on_empty_df_or_no_signals() -> None:
    df = make_trend(n=50)
    empty_result = IndicatorResult(
        indicator="test.bars_ago", version="0.1.0", params_hash="h1",
        symbol="TEST", timeframe=Timeframe.D1, signals=[],
    )
    engine._add_bars_ago(empty_result, df)  # patlamamalı
    assert empty_result.signals == []

    result = _result_with_signal_at(df, pos=len(df) - 1)
    engine._add_bars_ago(result, df.iloc[:0])
    assert "bars_ago" not in result.signals[0].payload


def _persist_one(store: ResultsStore, run_id: str, df, pos: int, bars_ago: int | None) -> None:
    result = _result_with_signal_at(df, pos=pos)
    if bars_ago is not None:
        result.signals[0].payload["bars_ago"] = bars_ago
    item = SymbolIndicatorRun(
        symbol="TEST", market="bist", timeframe="1D", indicator="test.bars_ago",
        params_hash="h1", result=result, error=None,
    )
    store.start_run(
        RunRecord(
            run_id=run_id, started_at="2026-01-01T00:00:00", finished_at=None,
            market="bist", timeframes=["1d"], universe_size=1,
            indicator_names=["test.bars_ago"], git_sha=None, status="running",
        )
    )
    store.persist(run_id, [item])
    store.finish_run(run_id, "2026-01-01T00:05:00", "completed")


def test_persist_writes_bars_ago_column(tmp_path: Path) -> None:
    store = ResultsStore(db_path=tmp_path / "r.db", json_root=tmp_path / "json")
    df = make_trend(n=50)
    _persist_one(store, "run_a", df, pos=len(df) - 1, bars_ago=2)
    rows = store.query(run_id="run_a")
    assert len(rows) == 1
    assert rows[0]["bars_ago"] == 2
    store.close()


def test_latest_signals_max_bars_ago_none_keeps_old_behavior(tmp_path: Path) -> None:
    store = ResultsStore(db_path=tmp_path / "r.db", json_root=tmp_path / "json")
    df = make_trend(n=50)
    _persist_one(store, "run_a", df, pos=len(df) - 1, bars_ago=50)
    rows, total = store.latest_signals("run_a", max_bars_ago=None)
    assert total == 1
    assert len(rows) == 1
    store.close()


def test_latest_signals_filters_by_max_bars_ago(tmp_path: Path) -> None:
    store = ResultsStore(db_path=tmp_path / "r.db", json_root=tmp_path / "json")
    df = make_trend(n=50)
    _persist_one(store, "run_a", df, pos=len(df) - 1, bars_ago=1)
    rows, total = store.latest_signals("run_a", max_bars_ago=3)
    assert total == 1
    assert rows[0]["bars_ago"] == 1

    rows, total = store.latest_signals("run_a", max_bars_ago=0)
    assert total == 0
    assert rows == []
    store.close()


def test_latest_signals_excludes_null_bars_ago_when_filtering(tmp_path: Path) -> None:
    """Migrasyon öncesi (bars_ago hiç hesaplanmamış) satırların yaşı
    BİLİNMİYOR -- max_bars_ago verildiğinde bunlar DIŞLANIR (sessizce
    "taze" sayılıp gösterilmezler, ki bu YANLIŞ pozitiften daha güvenli)."""
    store = ResultsStore(db_path=tmp_path / "r.db", json_root=tmp_path / "json")
    df = make_trend(n=50)
    _persist_one(store, "run_a", df, pos=len(df) - 1, bars_ago=None)
    rows, total = store.latest_signals("run_a", max_bars_ago=3)
    assert total == 0

    rows, total = store.latest_signals("run_a", max_bars_ago=None)
    assert total == 1
    store.close()
