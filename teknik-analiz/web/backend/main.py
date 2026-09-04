"""tlab web arayüzü — FastAPI backend.

İnce bir sunum katmanı: tlab'ın mevcut Python hesap motorunu (`tlab/viz/live.py`,
`tlab/viz/renderer.py`, `tlab/scanner/`) DOĞRUDAN çağırır. Grafik `/api/chart.png`
üzerinden tlab'ın KENDİ Plotly tabanlı renderer'ının ürettiği statik bir PNG
olarak sunulur (kullanıcı isteği: TradingView tarzı etkileşimli bir JS widget'ı
DEĞİL, Python'ın ürettiği sabit bir görsel) — hiçbir çizim mantığı burada
TEKRARLANMAZ.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from web.backend.routes import (
    catalog,
    chart,
    chart_png,
    chart_svg,
    guide,
    report,
    scan,
    scan_trigger,
    universe,
)

app = FastAPI(title="tlab web API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(catalog.router, prefix="/api")
app.include_router(universe.router, prefix="/api")
app.include_router(chart.router, prefix="/api")
app.include_router(chart_png.router, prefix="/api")
app.include_router(chart_svg.router, prefix="/api")
app.include_router(report.router, prefix="/api")
app.include_router(guide.router, prefix="/api")
app.include_router(scan.router, prefix="/api")
app.include_router(scan_trigger.router, prefix="/api")


@app.get("/api/health")
def health() -> dict[str, bool]:
    return {"ok": True}
