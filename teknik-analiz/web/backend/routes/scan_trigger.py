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

from tlab.scanner.eod import run_eod

router = APIRouter(tags=["scan_trigger"])

_JOBS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()


def _run_job(job_id: str, market: str, force: bool) -> None:
    with _LOCK:
        _JOBS[job_id]["status"] = "running"
    try:
        result = run_eod(market, force=force)
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
def start_scan(market: str = "bist", force: bool = False) -> dict[str, str]:
    # Aynı piyasa için ZATEN çalışan bir iş varsa yenisini başlatma —
    # `run_eod` kendi içinde de idempotent (force=False iken aynı gün
    # ikinci koşuyu atlar) ama gereksiz paralel iş yaratmayı burada
    # baştan önlemek daha temiz.
    with _LOCK:
        for job in _JOBS.values():
            if job["market"] == market and job["status"] == "running":
                return {"job_id": job["job_id"], "status": "already_running"}

    job_id = uuid.uuid4().hex[:12]
    with _LOCK:
        _JOBS[job_id] = {
            "job_id": job_id,
            "market": market,
            "status": "queued",
            "started_at": datetime.now(UTC).isoformat(),
        }
    thread = threading.Thread(target=_run_job, args=(job_id, market, force), daemon=True)
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
