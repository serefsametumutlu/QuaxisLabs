"""POST /api/pairs/refresh, GET /api/pairs/refresh/status — `config/pairs.
yaml`'ı arka planda yeniden üretir.

`scan_trigger.py`nin AYNI thread+iş-durum deseni (BIST evreninin tamamını
fiyatlayıp `discover_pairs`i koşmak dakikalarca sürebilir, bu yüzden bir
HTTP isteği içinde senkron çalıştırılamaz).

2026-09-04 kullanıcı isteği: `config/pairs.yaml`nin kendi notu "KALICI BİR
ONAY DEĞİL, periyodik olarak yeniden koşulmalı" diyor ama bu yeniden koşma
elle (`python scripts/pair_denetim.py`) yapılıyordu — kullanıcı web
arayüzünde, her arbitraj taramasından ÖNCE basabileceği bir buton istedi."""

from __future__ import annotations

import threading
import traceback
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from tlab.indicators.pairs.refresh import refresh_pairs_yaml

router = APIRouter(tags=["pairs_refresh"])

_JOBS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()


def _run_job(job_id: str) -> None:
    with _LOCK:
        _JOBS[job_id]["status"] = "running"
    try:
        result = refresh_pairs_yaml()
        with _LOCK:
            _JOBS[job_id]["status"] = "completed"
            _JOBS[job_id]["result"] = result
            _JOBS[job_id]["finished_at"] = datetime.now(UTC).isoformat()
    except Exception as exc:  # noqa: BLE001 -- arka plan iş; hatayı duraklama olarak taşımalı
        with _LOCK:
            _JOBS[job_id]["status"] = "failed"
            _JOBS[job_id]["error"] = f"{exc}"
            _JOBS[job_id]["traceback"] = traceback.format_exc()
            _JOBS[job_id]["finished_at"] = datetime.now(UTC).isoformat()


@router.post("/pairs/refresh")
def start_pairs_refresh() -> dict[str, str]:
    with _LOCK:
        for job in _JOBS.values():
            if job["status"] in ("queued", "running"):
                return {"job_id": job["job_id"], "status": "already_running"}

    job_id = uuid.uuid4().hex[:12]
    with _LOCK:
        _JOBS[job_id] = {
            "job_id": job_id, "status": "queued",
            "started_at": datetime.now(UTC).isoformat(),
        }
    thread = threading.Thread(target=_run_job, args=(job_id,), daemon=True)
    thread.start()
    return {"job_id": job_id, "status": "queued"}


@router.get("/pairs/refresh/status")
def pairs_refresh_status(job_id: str) -> dict[str, Any]:
    with _LOCK:
        job = _JOBS.get(job_id)
    if job is None:
        raise HTTPException(404, f"Bilinmeyen job_id: {job_id}")
    return job
