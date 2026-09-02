"""GET /api/report — seçili göstergeye göre Gemini tabanlı doğal-dil "quant
raporu". `structure.report` seçiliyken ZENGİN özel yola (`generate_quant_
report`, ps+sf sonucu), diğer HERHANGİ bir gösterge için genel yedek yola
(`generate_indicator_report`, `build_generic_summary_lines`) düşer — AYNI
dispatch `tlab/dashboard.py::_render_ai_report_button`'da da kullanılıyor,
burada TEKRAR YAZILMADI, yalnızca web için tekrarlandı (Streamlit'e bağımlı
olmadan). Yeniden hesap YOK.

API anahtarı ortamda `GEMINI_API_KEY` olarak YOKSA, kullanıcının AYRI bir
projesindeki (`bilanco-radar`) `.env` dosyasından okunur — bu proje daha
önce AYNI anahtarı AYNI şekilde (yalnızca ortam değişkeni olarak, hiçbir
dosyaya/commit'e yazılmadan) kullanmıştı."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

from tlab.viz.live import STRUCTURE_REPORT_NAME, compute_live, compute_structure_report
from tlab.viz.quant_report import (
    generate_indicator_report,
    generate_pair_report,
    generate_quant_report,
)

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
def get_report(symbol: str, tf: str, indicator: str, market: str = "bist") -> dict[str, object]:
    _ensure_gemini_key()
    model = os.environ.get("GEMINI_MODEL") or None
    try:
        if indicator == STRUCTURE_REPORT_NAME:
            ps_result, sf_result, df = compute_structure_report(symbol, tf, market)
            report = generate_quant_report(ps_result, sf_result, df, symbol=symbol, model=model)
        else:
            result, df = compute_live(indicator, symbol, tf, market)
            if df is None:
                # 2026-09-03: eskiden burada 422 "desteklenmiyor" dönüyordu --
                # pair göstergeleri artık kendi AI rapor yoluna sahip (bkz.
                # `generate_pair_report`), df'siz de çalışır.
                report = generate_pair_report(result, symbol=symbol, model=model)
            else:
                report = generate_indicator_report(result, df, symbol=symbol, model=model)
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
