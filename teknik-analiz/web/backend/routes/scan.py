"""GET /api/runs, GET /api/signals — mevcut tarama sonuçlarını (`outputs/
results.db`, `tlab/scanner/results.py::ResultsStore`) tarayıcıya JSON olarak
sunar. Yeni bir tarama TETİKLEMEZ — bkz. `scan_trigger.py`.

DÜRÜST NOT: tarama tetikleme (arka plan iş kuyruğu, ilerleme çubuğu vb.)
bu turun kapsamı DIŞINDA — `run_eod()` dakikalarca sürebilen senkron bir
işlem, bunu web isteği içinde çalıştırmak HTTP timeout'una çarpar. Kullanıcı
şimdilik `tlab eod --market bist` komutunu kendi terminalinden çalıştırmalı;
bu sayfa yalnızca SONUÇLARI görüntüler."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from tlab.indicators.bootstrap import CATALOG
from tlab.scanner.results import ResultsStore
from tlab.viz.labels_tr import tr_indicator, tr_pattern_name

router = APIRouter(tags=["scan"])


def _store() -> ResultsStore:
    return ResultsStore()


def _indicators_for_category(category: str) -> tuple[str, ...]:
    names = tuple(spec.name for spec in CATALOG.values() if spec.category == category)
    if not names:
        raise HTTPException(404, f"Bilinmeyen kategori: {category}")
    return names


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
    category: str | None = None,
    direction: str | None = None,
    symbol: str | None = None,
    all_states: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, object]:
    store = _store()
    if store.get_run(run_id) is None:
        raise HTTPException(404, f"Bilinmeyen run_id: {run_id}")
    # `category` ile `indicator` AYNI anda verilirse `indicator` daha
    # SPESİFİK kabul edilip kategori filtresi görmezden gelinir — frontend
    # ikisini birbirini dışlayan iki seçenek olarak sunuyor (bkz. scan/page.tsx).
    indicators = _indicators_for_category(category) if (category and not indicator) else None
    rows, total = store.latest_signals(
        run_id,
        market=market,
        timeframe=tf.upper() if tf else None,
        indicator=indicator,
        indicators=indicators,
        direction=direction,
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
        indicator_name = r["indicator"]
        # 2026-09-02: kullanıcı "patterns.head_shoulders yazıyor mesela dosya
        # ismi bu düzenli görünsün" dedi — ham katalog adı yerine Türkçe
        # görünen ad; harmonik satırlarda EKOL adı yerine gerçek PATERN
        # ŞEKLİNİ (payload.pattern_name, `TrackingConfig.pattern_name`'den)
        # önceliklendiriyoruz — kullanıcının "carney/pesavento yerine
        # gartley/crab/butterfly gibi ayıralım" isteğine yanıt.
        pattern_name = payload.get("pattern_name")
        pattern_label = (
            tr_pattern_name(str(pattern_name))
            if indicator_name.startswith("harmonic.") and pattern_name
            else None
        )
        signals.append(
            {
                "symbol": r["symbol"],
                "timeframe": r["timeframe"],
                "indicator": indicator_name,
                "display_name": pattern_label or tr_indicator(indicator_name),
                "pattern_label": pattern_label,
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
