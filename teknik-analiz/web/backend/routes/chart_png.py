"""GET /api/chart.png — grafiği tlab'ın KENDİ, zaten olgunlaşmış Plotly
tabanlı `tlab/viz/renderer.py` motoruyla sunucu tarafında statik bir PNG
olarak üretir.

Kullanıcı geri bildirimi: grafik TradingView tarzı etkileşimli bir JS
widget'ı DEĞİL, Python'ın ürettiği SABİT bir görsel gibi gelmeli — mumları/
çizgileri "biz kendimiz" (tlab'ın kendi renderer'ı, üçüncü parti bir grafik
kütüphanesinin varsayılan stiline bağımlı olmadan) çizmeli. Bu motor zaten
BUNU yapıyor (declutter/stagger/panel başlıkları/hacim profili — hepsi
`renderer.py`'de, aylar süren ayrı bir çalışmanın ürünü) — web katmanı
burada YENİDEN İCAT ETMEK yerine onu DOĞRUDAN çağırır."""

from __future__ import annotations

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
        fig = render_live(indicator, symbol, tf, market, theme=resolved_theme)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, f"Veri bulunamadı: {exc}") from exc

    png_bytes = fig.to_image(format="png", scale=2)
    # `structure.report` gibi göstergeler (price_structure'ın O(n²) trendline
    # üretimi) birkaç saniye sürebiliyor — tarayıcı aynı URL'i (görüntüleme +
    # "PNG indir" ikinci bir fetch) kısa süre içinde tekrar isterse sunucuda
    # YENİDEN ÇİZMEK yerine kendi önbelleğinden döndürsün diye kısa bir
    # Cache-Control eklendi (query string zaten doğal bir önbellek anahtarı).
    return Response(
        content=png_bytes, media_type="image/png", headers={"Cache-Control": "private, max-age=300"}
    )
