"""Faz 6: küçük evren uçtan uca, idempotentlik, diff (yeni sinyal + durum
geçişi), kaybolan-sinyal (repaint alarmı) testi.

Ağdan bağımsız: TCELL/ISCTR için önceki fazlarda zaten indirilip
`data/ohlcv/` altında önbelleklenmiş gerçek veri kullanılır (`Store.get`
sadece parquet okur, ağa çıkmaz) — bu yüzden bu dosyadaki testler
`@pytest.mark.network` DEĞİLDİR."""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from tlab.core.types import Market, Timeframe
from tlab.data.providers.yfinance_provider import YFinanceProvider
from tlab.data.store import Store
from tlab.scanner import engine
from tlab.scanner.results import ResultsStore, RunRecord

_SMALL_UNIVERSE = ["TCELL", "ISCTR", "AKBNK", "GARAN"]
_INDICATORS = ["harmonic.pesavento", "structure.swing_fib_abcd"]


def _has_cache() -> bool:
    store = Store(YFinanceProvider())
    try:
        for sym in _SMALL_UNIVERSE:
            store.get(sym, Timeframe.D1, Market.BIST)
        return True
    except FileNotFoundError:
        return False


pytestmark = pytest.mark.skipif(
    not _has_cache(), reason="TCELL/ISCTR/AKBNK/GARAN 1D önbelleği yok (önceki fazlarda indirildi)"
)


def _run_small_scan(run_id: str) -> engine.ScanRun:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return engine.run(
            run_id=run_id, universe=_SMALL_UNIVERSE, timeframes=[Timeframe.D1],
            indicator_names=_INDICATORS, market=Market.BIST, lookback_bars=300, workers=2,
        )


def test_small_universe_end_to_end(tmp_path: Path) -> None:
    scan = _run_small_scan("test_e2e")
    assert len(scan.results) == len(_SMALL_UNIVERSE) * len(_INDICATORS)
    assert scan.error_count == 0
    assert len(scan.data_quality) == len(_SMALL_UNIVERSE)

    store = ResultsStore(db_path=tmp_path / "r.db", json_root=tmp_path / "json")
    store.start_run(
        RunRecord(
            run_id="test_e2e", started_at="2026-01-01T00:00:00", finished_at=None,
            market="bist", timeframes=["1d"], universe_size=len(_SMALL_UNIVERSE),
            indicator_names=_INDICATORS, git_sha=None, status="running",
        )
    )
    store.persist("test_e2e", [r.to_symbol_indicator_run() for r in scan.results])
    store.finish_run("test_e2e", "2026-01-01T00:05:00", "completed")

    rows = store.query(run_id="test_e2e")
    assert len(rows) > 0
    assert store.latest_run("bist") == "test_e2e"

    # Faz 8E — read_result/list_symbol_indicators (confluence.py'nin ihtiyaç
    # duyduğu, results.db'den TAM IndicatorResult geri okuma yolu).
    triples = store.list_symbol_indicators("test_e2e", timeframe="1D")
    assert ("TCELL", "1D", "harmonic.pesavento") in triples
    result = store.read_result("test_e2e", "TCELL", "1D", "harmonic.pesavento")
    assert result is not None
    assert result.indicator == "harmonic.pesavento"
    assert store.read_result("test_e2e", "TCELL", "1D", "does.not.exist") is None

    store.close()


def test_persist_is_idempotent_on_identical_data(tmp_path: Path) -> None:
    """Aynı önbellek verisiyle iki ayrı koşu -> signals tablosu, run_id
    hariç, BİREBİR aynı satırları üretmeli."""
    scan1 = _run_small_scan("run_a")
    scan2 = _run_small_scan("run_b")

    store = ResultsStore(db_path=tmp_path / "r.db", json_root=tmp_path / "json")
    for run_id, scan in (("run_a", scan1), ("run_b", scan2)):
        store.start_run(
            RunRecord(
                run_id=run_id, started_at="2026-01-01T00:00:00", finished_at=None,
                market="bist", timeframes=["1d"], universe_size=len(_SMALL_UNIVERSE),
                indicator_names=_INDICATORS, git_sha=None, status="running",
            )
        )
        store.persist(run_id, [r.to_symbol_indicator_run() for r in scan.results])
        store.finish_run(run_id, "2026-01-01T00:05:00", "completed")

    def _strip_run_id(rows: list[dict]) -> list[tuple]:
        return sorted(
            (
                r["symbol"], r["timeframe"], r["indicator"],
                r["pattern_id"], r["state"], r["bar_time"],
            )
            for r in rows
        )

    rows_a = store.query(run_id="run_a")
    rows_b = store.query(run_id="run_b")
    assert _strip_run_id(rows_a) == _strip_run_id(rows_b)
    store.close()


def test_diff_shows_only_new_signals_after_persisting_same_run_twice(tmp_path: Path) -> None:
    """Aynı taramayı run_a ve run_b olarak kaydedip diff alınırsa: aynı veri
    olduğu için "yeni sinyal"/"durum geçişi" OLMAMALI, "kaybolan sinyal" de
    OLMAMALI (repaint alarmı tetiklenmemeli)."""
    scan = _run_small_scan("same_scan")
    store = ResultsStore(db_path=tmp_path / "r.db", json_root=tmp_path / "json")
    for run_id in ("run_a", "run_b"):
        store.start_run(
            RunRecord(
                run_id=run_id, started_at="2026-01-01T00:00:00", finished_at=None,
                market="bist", timeframes=["1d"], universe_size=len(_SMALL_UNIVERSE),
                indicator_names=_INDICATORS, git_sha=None, status="running",
            )
        )
        store.persist(run_id, [r.to_symbol_indicator_run() for r in scan.results])
        store.finish_run(run_id, "2026-01-01T00:05:00", "completed")

    diff = store.diff("run_a", "run_b")
    assert diff.new_signals == []
    assert diff.missing_signals == []
    assert not diff.has_repaint_alarm
    store.close()


def test_diff_detects_repaint_alarm_on_injected_missing_signal(tmp_path: Path) -> None:
    """Sahte bir sinyal doğrudan run_a'ya enjekte edilip run_b'de OLMADIĞINDA
    diff.missing_signals bunu yakalamalı (repaint alarmı)."""
    store = ResultsStore(db_path=tmp_path / "r.db", json_root=tmp_path / "json")
    for run_id in ("run_a", "run_b"):
        store.start_run(
            RunRecord(
                run_id=run_id, started_at="2026-01-01T00:00:00", finished_at=None,
                market="bist", timeframes=["1d"], universe_size=1,
                indicator_names=["harmonic.pesavento"], git_sha=None, status="running",
            )
        )
    store._conn.execute(  # noqa: SLF001 -- test icin dogrudan satir enjeksiyonu
        "INSERT INTO signals (run_id, symbol, market, timeframe, indicator, params_hash, "
        "bar_time, detected_at, direction, state, score, pattern_id, payload_json) "
        "VALUES ('run_a','FAKE','bist','1d','harmonic.pesavento','h1',"
        "'2026-01-01T00:00:00','2026-01-01T00:00:00','long','confirmed',0.9,'ghost','{}')"
    )
    store._conn.commit()
    store.finish_run("run_a", "2026-01-01T00:05:00", "completed")
    store.finish_run("run_b", "2026-01-01T00:05:00", "completed")

    diff = store.diff("run_a", "run_b")
    assert diff.has_repaint_alarm
    assert len(diff.missing_signals) == 1
    assert diff.missing_signals[0]["pattern_id"] == "ghost"
    store.close()
