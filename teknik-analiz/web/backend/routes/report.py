"""GET /api/report — bir sembol için `tlab/viz/quant_report.py`'nin ürettiği
Gemini tabanlı doğal-dil "quant raporu" (bkz. `tlab quant-report` CLI'sı ile
AYNI motor). Yeniden hesap/prompt YOK — mevcut `generate_quant_report()`
DOĞRUDAN çağrılır.

API anahtarı ortamda `GEMINI_API_KEY` olarak YOKSA, kullanıcının AYRI bir
projesindeki (`bilanco-radar`) `.env` dosyasından okunur — bu proje daha
önce AYNI anahtarı AYNI şekilde (yalnızca ortam değişkeni olarak, hiçbir
dosyaya/commit'e yazılmadan) kullanmıştı (bkz. CLAUDE.md, "LLM sağlayıcısı
Gemini'ye geçirildi" bölümü)."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

from tlab.viz.live import compute_structure_report
from tlab.viz.quant_report import generate_quant_report

router = APIRouter(tags=["report"])

_BILANCO_RADAR_ENV = Path(r"C:\Users\Samet\Desktop\Temel Analiz\bilanco-radar\.env")


def _ensure_gemini_key() -> None:
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return
    if not _BILANCO_RADAR_ENV.exists():
        return
    for line in _BILANCO_RADAR_ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key in ("GEMINI_API_KEY", "GEMINI_MODEL") and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")


@router.get("/report")
def get_report(symbol: str, tf: str, market: str = "bist") -> dict[str, object]:
    _ensure_gemini_key()
    try:
        ps_result, sf_result, df = compute_structure_report(symbol, tf, market)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, f"Veri bulunamadı: {exc}") from exc

    model = os.environ.get("GEMINI_MODEL") or None
    report = generate_quant_report(ps_result, sf_result, df, symbol=symbol, model=model)
    return {
        "text": report.text,
        "used_ai": report.used_ai,
        "provider": report.provider,
        "note": report.note,
    }
