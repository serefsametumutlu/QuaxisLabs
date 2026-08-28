"""Gün sonu (EOD) akışı: takvim → veri güncelleme → veri kalitesi →
tarama → kalıcılaştırma → diff → rapor → bildirim hook'u.

Aynı gün ikinci koşu: `run_id` tarihe göre sabittir (`{market}_{date}`).
`force=False` iken zaten `completed` bir run varsa ATLANIR (yeniden
koşulmaz, mevcut run_id ile mevcut sonuç döner); `force=True` iken
üzerine yazılır (aynı run_id, sinyaller INSERT OR REPLACE ile güncellenir).
"""

from __future__ import annotations

import json
import logging
import subprocess
from collections.abc import Callable
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from tlab.core.types import Market, Timeframe
from tlab.data.calendar import is_trading_day, last_closed_session
from tlab.data.providers.yfinance_provider import YFinanceProvider
from tlab.data.store import Store
from tlab.data.universe import load_universe
from tlab.indicators.bootstrap import CATALOG
from tlab.scanner import engine
from tlab.scanner.results import DEFAULT_DB_PATH, DiffReport, ResultsStore, RunRecord

DEFAULT_LOG_DIR = Path("outputs") / "logs"

NotifyHook = Callable[[str, dict[str, Any]], None]


def _noop_notify(event: str, payload: dict[str, Any]) -> None:
    """Bildirim hook'u — Telegram entegrasyonu sonra buraya bağlanacak."""
    return


def _git_sha() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
            timeout=5, check=False,
        )
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def _setup_logger(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(f"tlab.eod.{log_path.stem}")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console)
    return logger


def run_eod(
    market: str,
    date_: date | None = None,
    force: bool = False,
    indicator_names: list[str] | None = None,
    timeframes: tuple[str, ...] = ("4h", "1d"),
    pairs: list[tuple[str, str]] | None = None,
    notify: NotifyHook = _noop_notify,
    results_db: Path | None = None,
    universe_override: list[str] | None = None,
) -> dict[str, Any]:
    mkt = Market(market.lower())
    target_date = date_ or last_closed_session(datetime.now(UTC), mkt)
    run_id = f"{mkt.value}_{target_date.isoformat()}"
    logger = _setup_logger(DEFAULT_LOG_DIR / f"eod_{target_date.isoformat()}.log")

    results_store = ResultsStore(db_path=results_db or DEFAULT_DB_PATH)

    if not is_trading_day(target_date, mkt):
        logger.info("EOD atlandı: %s işlem günü değil (%s)", target_date, mkt.value)
        return {"run_id": run_id, "status": "skipped_holiday", "date": target_date.isoformat()}

    existing = results_store.get_run(run_id)
    if existing is not None and existing.status == "completed" and not force:
        logger.info("EOD atlandı: %s için zaten tamamlanmış bir run var (force=False)", run_id)
        return {"run_id": run_id, "status": "skipped_existing"}

    indicator_names = indicator_names or list(CATALOG.keys())
    tf_map = {"1h": Timeframe.H1, "4h": Timeframe.H4, "1d": Timeframe.D1}
    tf_enums = [tf_map[tf.lower()] for tf in timeframes]
    universe = universe_override if universe_override is not None else load_universe(mkt)

    logger.info("EOD başlıyor: %s %s, evren=%d sembol", mkt.value, target_date, len(universe))

    results_store.start_run(
        RunRecord(
            run_id=run_id, started_at=datetime.now(UTC).isoformat(), finished_at=None,
            market=mkt.value, timeframes=list(timeframes), universe_size=len(universe),
            indicator_names=indicator_names, git_sha=_git_sha(), status="running",
        )
    )

    logger.info("Veri güncelleniyor (1H,1D; 4H türetilir) ...")
    provider = YFinanceProvider()
    store = Store(provider)
    update_failures: list[str] = []
    for symbol in universe:
        try:
            store.update(symbol, mkt, datetime(2020, 1, 1, tzinfo=UTC), datetime.now(UTC))
        except Exception as exc:  # noqa: BLE001 — tek sembol hatası taramayı durdurmamalı
            update_failures.append(symbol)
            logger.warning("Veri güncelleme hatası %s: %s", symbol, exc)
    if update_failures:
        logger.warning("%d sembol güncellenemedi: %s", len(update_failures), update_failures)

    logger.info("Tarama çalıştırılıyor ...")
    scan = engine.run(
        run_id=run_id, universe=universe, timeframes=tf_enums, indicator_names=indicator_names,
        market=mkt, pairs=pairs or [],
        progress=lambda done, total: logger.info("  ilerleme: %d/%d", done, total),
    )
    logger.info(
        "Tarama tamamlandı: %d sonuç, %d hata", len(scan.results), scan.error_count,
    )

    results_store.persist(run_id, [r.to_symbol_indicator_run() for r in scan.results])
    results_store.persist_data_quality(run_id, scan.data_quality)
    results_store.finish_run(run_id, datetime.now(UTC).isoformat(), "completed")

    diff_report: DiffReport | None = None
    previous_runs = [
        r for r in results_store.list_runs(mkt.value, status="completed") if r != run_id
    ]
    if previous_runs:
        previous_run_id = previous_runs[0]
        diff_report = results_store.diff(previous_run_id, run_id)
        logger.info(
            "Diff (%s -> %s): %d yeni sinyal, %d durum geçişi, %d KAYBOLAN sinyal",
            previous_run_id, run_id, len(diff_report.new_signals),
            len(diff_report.transitions), len(diff_report.missing_signals),
        )
        if diff_report.has_repaint_alarm:
            logger.error(
                "REPAINT ALARMI: %d sinyal önceki run'da vardı, bu run'da YOK — "
                "bkz. diff_report.missing_signals", len(diff_report.missing_signals),
            )

    report = {
        "run_id": run_id, "status": "completed", "date": target_date.isoformat(),
        "market": mkt.value, "universe_size": len(universe),
        "n_results": len(scan.results), "n_errors": scan.error_count,
        "n_new_signals": len(diff_report.new_signals) if diff_report else None,
        "n_transitions": len(diff_report.transitions) if diff_report else None,
        "repaint_alarm": diff_report.has_repaint_alarm if diff_report else False,
    }
    report_path = Path("outputs") / "reports" / f"eod_{run_id}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Rapor yazıldı: %s", report_path)

    notify("eod_completed", report)
    results_store.close()
    return report
