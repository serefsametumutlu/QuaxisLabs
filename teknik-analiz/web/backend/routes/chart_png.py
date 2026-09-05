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
        # GERÇEK bir hata (2026-09-05, kullanıcı geri bildirimi — TOBO.png/
        # intem_cnali.png [TradingView'ın KENDİ ekran görüntüleri] referans
        # gösterilip "cam gibi net olmalı" denildi): SVG sahneleri ~700-820px
        # native genişlikte üretiliyor, ama frontend'in `<img className=
        # "w-full">`si bunu panel genişliğine (tipik 900-1400+ CSS piksel,
        # Retina/HiDPI ekranda 2x DEVICE piksel) GERDİĞİ için görsel
        # sistemli olarak bulanıklaşıyordu -- Plotly yolu zaten `scale=2`
        # kullanıyordu, SVG yolunda BUNUN KARŞILIĞI HİÇ YOKTU (`resvg_py.
        # svg_to_bytes`'a zoom hiç verilmiyordu, yani DAİMA native 1x).
        # zoom=3 native genişliği ~2100-2460px'e çıkarır -- büyük panel +
        # Retina ekranda bile upsampling gerekmez.
        png_bytes = bytes(resvg_py.svg_to_bytes(svg_string=fig, zoom=3.0))
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
