"""GET /api/share-text — bir SEMBOLÜ (tek göstergenin grafiğini açmaya
GEREK KALMADAN) çoklu-gösterge taramasından geçirip, `quant_report.py`nin
AYNI "insan/quant sesi" LLM çekirdeğiyle X'te paylaşılabilir TEK bir metin
üretir. Dashboard'daki/`/report`'taki mevcut "yapay zeka rapor"tan (tek
göstergenin ZATEN açık olduğu grafiğe bağlı) BİLİNÇLİ OLARAK AYRI bir akış
-- kullanıcı yalnızca bir sembol adı yazıp doğrudan paylaşılabilir bir
metin istedi (bkz. `tlab/viz/share_text.py` docstring'i)."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

from tlab.viz.share_text import generate_share_text

router = APIRouter(tags=["share_text"])

_BILANCO_RADAR_ENV = Path(r"C:\Users\Samet\Desktop\Temel Analiz\bilanco-radar\.env")


def _ensure_gemini_key() -> None:
    """`web/backend/routes/report.py`deki AYNI bootstrap -- iki route da
    aynı ortam-değişkeni kaynağını (kardeş `bilanco-radar` projesinin
    `.env`'i) paylaşıyor, burada TEKRARLANDI (o dosyaya bağımlılık
    eklemeden, her iki route da bağımsız kalabilsin diye)."""
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


@router.get("/share-text")
def get_share_text(symbol: str, market: str = "bist") -> dict[str, object]:
    _ensure_gemini_key()
    model = os.environ.get("GEMINI_MODEL") or None
    try:
        report = generate_share_text(symbol, market, model=model)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, f"Veri bulunamadı: {exc}") from exc

    return {
        "text": report.text,
        "used_ai": report.used_ai,
        "provider": report.provider,
        "note": report.note,
    }
