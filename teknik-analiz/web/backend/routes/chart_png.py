"""GET /api/chart.png — grafiği sunucu tarafında statik bir PNG olarak üretir.

**Faz 3 (2026-09-04) — SVG-öncelikli rasterleştirme:** SVG sahnesi
portlanmış bir gösterge istenirse (`tlab/viz/svg::supports`), PNG artık
Plotly/kaleido'nun headless-Chromium turu YERİNE `tlab/viz/svg`nin ürettiği
SVG metninin `resvg_py` ile rasterleştirilmesinden gelir (spec: "chart_png.py
KALSIN ama artık SVG'yi rasterleştirsin, kaleido devre dışı" — TANI_VE_
YOL_HARITASI_v2.md Faz 3, 3D). Henüz portlanmamış göstergeler (Faz 4 bekliyor)
eski Plotly + kaleido yoluna DÜŞER — `render_live(engine="svg")` bunu zaten
kendi içinde yapıyor, burası yalnızca dönen değerin `str` (SVG) mi yoksa
`go.Figure` (Plotly) mi olduğuna göre rasterleştirme yolunu seçer.

Kullanıcı geri bildirimi: grafik TradingView tarzı etkileşimli bir JS
widget'ı DEĞİL, Python'ın ürettiği SABİT bir görsel gibi gelmeli — mumları/
çizgileri "biz kendimiz" çizmeli. Plotly yoluna düşen göstergeler için bu
zaten `renderer.py`'nin (declutter/stagger/panel başlıkları/hacim profili)
işi; web katmanı burada YENİDEN İCAT ETMEK yerine `render_live`'ı DOĞRUDAN
çağırır."""

from __future__ import annotations

import resvg_py
from fastapi import APIRouter, HTTPException, Response

from tlab.viz.live import render_live

router = APIRouter(tags=["chart_png"])

_THEME_MAP = {"dark": "dark", "classic": "light", "editorial": "paper"}


@router.get("/chart.png")
def get_chart_png(
    symbol: str, tf: str, indicator: str, market: str = "bist", theme: str = "dark"
) -> Response:
    resolved_theme = _THEME_MAP.get(theme, "dark")
    try:
        fig = render_live(indicator, symbol, tf, market, theme=resolved_theme, engine="svg")
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, f"Veri bulunamadı: {exc}") from exc

    if isinstance(fig, str):
        png_bytes = bytes(resvg_py.svg_to_bytes(svg_string=fig))
    else:
        png_bytes = fig.to_image(format="png", scale=2)
    # `structure.report` gibi göstergeler (price_structure'ın O(n²) trendline
    # üretimi) birkaç saniye sürebiliyor — tarayıcı aynı URL'i (görüntüleme +
    # "PNG indir" ikinci bir fetch) kısa süre içinde tekrar isterse sunucuda
    # YENİDEN ÇİZMEK yerine kendi önbelleğinden döndürsün diye kısa bir
    # Cache-Control eklendi (query string zaten doğal bir önbellek anahtarı).
    return Response(
        content=png_bytes, media_type="image/png", headers={"Cache-Control": "private, max-age=300"}
    )
