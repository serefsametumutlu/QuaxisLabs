"""tlab web arayüzü — FastAPI backend.

İnce bir sunum katmanı: tlab'ın mevcut Python hesap motorunu (`tlab/viz/live.py`,
`tlab/indicators/bootstrap.py`, `tlab/data/universe.py`) DOĞRUDAN import edip JSON
olarak dışa verir. Burada YENİDEN HESAP yapılmaz — yalnızca mevcut fonksiyonların
dönüşü serileştirilir. Grafik çizimi (mum + overlay) tarayıcıda (Next.js +
lightweight-charts) yapılır; bu backend hiçbir PNG üretmez.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from web.backend.routes import catalog, chart, universe

app = FastAPI(title="tlab web API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(catalog.router, prefix="/api")
app.include_router(universe.router, prefix="/api")
app.include_router(chart.router, prefix="/api")


@app.get("/api/health")
def health() -> dict[str, bool]:
    return {"ok": True}
