"""GET /api/runs, GET /api/signals — mevcut tarama sonuçlarını (`outputs/
results.db`, `tlab/scanner/results.py::ResultsStore`) tarayıcıya JSON olarak
sunar. Yeni bir tarama TETİKLEMEZ (bkz. modül docstring notu aşağıda) —
yalnızca `tlab eod`/`tlab scan` CLI'sinin ZATEN ürettiği sonuçları listeler.

DÜRÜST NOT: tarama tetikleme (arka plan iş kuyruğu, ilerleme çubuğu vb.)
bu turun kapsamı DIŞINDA — `run_eod()` dakikalarca sürebilen senkron bir
işlem, bunu web isteği içinde çalıştırmak HTTP timeout'una çarpar. Kullanıcı
şimdilik `tlab eod --market bist` komutunu kendi terminalinden çalıştırmalı;
bu sayfa yalnızca SONUÇLARI görüntüler."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from tlab.scanner.results import ResultsStore

router = APIRouter(tags=["scan"])


def _store() -> ResultsStore:
    return ResultsStore()


@router.get("/runs")
def list_runs(market: str = "bist") -> list[dict[str, object]]:
    store = _store()
    run_ids = store.list_runs(market)
    out = []
    for run_id in run_ids:
        rec = store.get_run(run_id)
        if rec is None:
            continue
        out.append(
            {
                "run_id": rec.run_id,
                "started_at": rec.started_at,
                "finished_at": rec.finished_at,
                "market": rec.market,
                "timeframes": rec.timeframes,
                "universe_size": rec.universe_size,
                "status": rec.status,
            }
        )
    return out


@router.get("/signals")
def list_signals(
    run_id: str,
    market: str | None = None,
    tf: str | None = None,
    indicator: str | None = None,
    symbol: str | None = None,
    all_states: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, object]:
    store = _store()
    if store.get_run(run_id) is None:
        raise HTTPException(404, f"Bilinmeyen run_id: {run_id}")
    rows, total = store.latest_signals(
        run_id,
        market=market,
        timeframe=tf.upper() if tf else None,
        indicator=indicator,
        symbol=symbol,
        states=None if all_states else ("confirmed", "completed"),
        limit=min(limit, 500),
        offset=offset,
    )
    signals = []
    for r in rows:
        payload = {}
        try:
            payload = json.loads(r.get("payload_json") or "{}")
        except json.JSONDecodeError:
            pass
        signals.append(
            {
                "symbol": r["symbol"],
                "timeframe": r["timeframe"],
                "indicator": r["indicator"],
                "state": r["state"],
                "direction": r["direction"],
                "score": r["score"],
                "bar_time": r["bar_time"],
                "detected_at": r["detected_at"],
                "pattern_id": r["pattern_id"],
                "payload": payload,
            }
        )
    return {"signals": signals, "total": total, "limit": limit, "offset": offset}
