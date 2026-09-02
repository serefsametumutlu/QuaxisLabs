"""POST /api/scan/start, GET /api/scan/status — yeni bir tarama TETİKLER.

`tlab/scanner/eod.py::run_eod()` tam evrende (648 sembol × birden fazla
zaman dilimi × ~25 indikatör) dakikalarca sürebilen SENKRON bir işlem —
bunu doğrudan bir HTTP isteği içinde çalıştırmak istekte zaman aşımına
(hem FastAPI'nin hem tarayıcının) çarpar. Bu yüzden `threading.Thread`
içinde ARKA PLANDA çalıştırılır; bu modül yalnızca bellek-içi bir durum
sözlüğü tutar ("başladı/çalışıyor/bitti/hata") — kalıcı bir iş kuyruğu
DEĞİL (uvicorn `--reload` ile yeniden başlarsa durum sıfırlanır, bu
tek-kullanıcılı yerel bir araç için kabul edilebilir bir sınırlama)."""

from __future__ import annotations

import threading
import traceback
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from tlab.indicators.bootstrap import CATALOG
from tlab.indicators.pairs.discovery import load_pairs_yaml
from tlab.scanner.eod import run_eod

router = APIRouter(tags=["scan_trigger"])

_JOBS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()


def _run_job(job_id: str, market: str, force: bool, indicator_names: list[str] | None) -> None:
    with _LOCK:
        _JOBS[job_id]["status"] = "running"
    try:
        # 2026-09-03 GERÇEK HATA: bu eskiden `pairs=` hiç geçmiyordu, bu
        # yüzden `pair.*` göstergeleri web'den başlatılan HER taramada boş
        # dönüyordu (CLI'nin `tlab eod` komutu `config/pairs.yaml`'ı zaten
        # okuyordu, web tarafı bunu hiç yapmıyordu — kullanıcı "pair
        # kısmında hiç sinyal yok" diye bildirdi). `load_pairs_yaml()` artık
        # ikisi arasında paylaşılan TEK kaynak (`tlab/indicators/pairs/
        # discovery.py`).
        result = run_eod(
            market, force=force, indicator_names=indicator_names, pairs=load_pairs_yaml()
        )
        with _LOCK:
            _JOBS[job_id]["status"] = "completed"
            _JOBS[job_id]["result"] = {
                "run_id": result.get("run_id"),
                "status": result.get("status"),
            }
            _JOBS[job_id]["finished_at"] = datetime.now(UTC).isoformat()
    except Exception as exc:  # noqa: BLE001 -- arka plan iş; hatayı duraklama olarak taşımalı
        with _LOCK:
            _JOBS[job_id]["status"] = "failed"
            _JOBS[job_id]["error"] = f"{exc}"
            _JOBS[job_id]["traceback"] = traceback.format_exc()
            _JOBS[job_id]["finished_at"] = datetime.now(UTC).isoformat()


@router.post("/scan/start")
def start_scan(
    market: str = "bist", force: bool = False, category: str | None = None
) -> dict[str, str]:
    # Aynı piyasa için ZATEN çalışan bir iş varsa yenisini başlatma —
    # `run_eod` kendi içinde de idempotent (force=False iken aynı gün
    # ikinci koşuyu atlar) ama gereksiz paralel iş yaratmayı burada
    # baştan önlemek daha temiz.
    with _LOCK:
        for job in _JOBS.values():
            if job["market"] == market and job["status"] == "running":
                return {"job_id": job["job_id"], "status": "already_running"}

    indicator_names: list[str] | None = None
    if category:
        indicator_names = [spec.name for spec in CATALOG.values() if spec.category == category]
        if not indicator_names:
            raise HTTPException(404, f"Bilinmeyen kategori: {category}")
        # `ResultsStore.persist()` UPSERT'tir (bkz. `tlab/scanner/results.py`,
        # DELETE yok) — bu yüzden bugün ZATEN tam bir tarama tamamlanmış olsa
        # bile, yalnızca BU kategorinin göstergelerini yeniden koşup üzerine
        # yazmak GÜVENLİ (diğer göstergelerin sinyalleri dokunulmadan kalır).
        # `force=True` bu yüzden kategori-bazlı taramada HER ZAMAN zorlanır —
        # aksi halde `run_eod` "bugün zaten tamamlanmış" deyip hiç çalışmaz.
        force = True

    job_id = uuid.uuid4().hex[:12]
    with _LOCK:
        _JOBS[job_id] = {
            "job_id": job_id,
            "market": market,
            "category": category,
            "status": "queued",
            "started_at": datetime.now(UTC).isoformat(),
        }
    thread = threading.Thread(
        target=_run_job, args=(job_id, market, force, indicator_names), daemon=True
    )
    thread.start()
    return {"job_id": job_id, "status": "queued"}


@router.get("/scan/status")
def scan_status(job_id: str) -> dict[str, Any]:
    with _LOCK:
        job = _JOBS.get(job_id)
    if job is None:
        raise HTTPException(404, f"Bilinmeyen job_id: {job_id}")
    return job


@router.get("/scan/jobs")
def list_jobs(market: str | None = None) -> list[dict[str, Any]]:
    with _LOCK:
        jobs = list(_JOBS.values())
    if market:
        jobs = [j for j in jobs if j["market"] == market]
    return sorted(jobs, key=lambda j: j["started_at"], reverse=True)
