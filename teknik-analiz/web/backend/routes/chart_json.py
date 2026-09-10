"""GET /api/chart.json — `tlab/chart`'ın (tipli komposer) ürettiği Plotly
figürünü JSON olarak döner; frontend'de plotly.js ile ETKİLEŞİMLİ çizilir
(hover/crosshair/zaman düğmeleri — `/api/chart.png`'nin sabit PNG'sinden
FARKLI, bkz. `ChartPlotly.tsx`).

**Aşama A (`YURUTME_PROMPTLARI.md`) — dikey dilim.** Boru hattı henüz
kanıtlanmadığı için YALNIZCA `patterns.triangle` desteklenir; başka bir
gösterge istenirse 422 + açık mesaj döner. Aşama B'de `_SUPPORTED`e diğer
19 gösterge eklenecek (her biri kendi adaptörüyle).

Akış (HESAP burada YAPILMAZ, yalnızca mevcut parçalar birleştirilir):
`compute_live` (Store + CATALOG, `tlab/viz/live.py`'nin ZATEN var olan
"sembolden canlı sonuca" kısayolu) → `boundary_adapter.to_pattern` (tarayıcının
KENDİ geometrisini `BoundaryPattern`e çevirir) → `composers.triangle.compose`
(yalnızca çizer) → `plotly.io.to_json` (numpy-güvenli serileştirme —
`fig.to_plotly_json()`'un düz `dict`i FastAPI'nin varsayılan JSON
serileştiricisinde numpy dizileriyle çöker, bu yüzden Plotly'nin KENDİ
encoder'ı kullanılır).
"""

from __future__ import annotations

import plotly.io as pio
from fastapi import APIRouter, HTTPException, Response

from tlab.chart.composers.broadening import compose as compose_broadening
from tlab.chart.composers.triangle import compose as compose_triangle
from tlab.chart.composers.wedge import compose as compose_wedge
from tlab.chart.tokens import ThemeName
from tlab.indicators.patterns.boundary_adapter import to_pattern
from tlab.viz.live import compute_live

router = APIRouter(tags=["chart_json"])

_THEME_MAP: dict[str, ThemeName] = {"dark": "dark", "classic": "light", "editorial": "paper"}

# indikatör adı -> o adaptörün ürettiği tipli sonucu çizen `compose()`.
# Aşama B'de her yeni gösterge burada bir satır ekler (kendi adaptörü +
# komposer eşleşmesiyle) — akışın geri kalanı DEĞİŞMEZ.
_SUPPORTED = {
    "patterns.triangle": compose_triangle,
    "patterns.wedge": compose_wedge,
    "patterns.broadening": compose_broadening,
}


@router.get("/chart.json")
def get_chart_json(
    symbol: str, tf: str, indicator: str, market: str = "bist", theme: str = "dark",
    max_bars_ago: int | None = 60,
) -> Response:
    compose = _SUPPORTED.get(indicator)
    if compose is None:
        raise HTTPException(422, f"{indicator} henüz tlab/chart'a bağlanmadı")
    resolved_theme = _THEME_MAP.get(theme, "dark")

    try:
        result, df = compute_live(indicator, symbol, tf, market)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, f"Veri bulunamadı: {exc}") from exc
    if df is None:
        raise HTTPException(422, f"{indicator} bu modda desteklenmiyor")

    pat = to_pattern(result, df)
    if pat is None:
        # Kural (KOMPOSER_HARITASI.md): "güncel yakın bir sinyal yoksa
        # göstermesin hiçbir şey" — burada karşılığı boş bir grafik DEĞİL,
        # net bir 404: frontend bunu "sinyal yok" olarak ayrı gösterir.
        raise HTTPException(404, f"{symbol} için güncel/geçerli bir {indicator} sinyali yok")

    # Tazelik kapısı. `/scan`'den (3 bar) DAHA GENİŞ ve bu BİLİNÇLİ:
    #
    # `/scan` "bugün ne yapılabilir" listesi -- orada 3 bar doğru. Grafik
    # sayfasında ise kullanıcı ZATEN bu sembolü ve bu göstergeyi seçmiş;
    # 4 barlık bir ONAY sinyalini 404'e çevirmek "eksik sinyal" üretir
    # (ölçüldü: takoz fikstürünün 4 barlık ONAY'ı 3-bar kapısına takılıyordu).
    # Asıl DOĞRULUK filtresi burada tazelik değil, durum makinesi:
    # `select_latest` zaten `invalidated`/`expired` adayları hiç döndürmüyor,
    # yani gelen aday KENDİ ufku içinde hâlâ geçerli. 60 bar (~3 ay, 1G)
    # bunun üstüne "artık bakmaya değmez" sınırı koyar ve kullanıcının
    # şikâyet ettiği vakayı (BARMA, "Sinyal yaşı: 262 bar") hâlâ engeller.
    # Sinyalin YAŞI grafiğin üst satırında zaten yazıyor. `None` kapatır,
    # istenirse sorgu parametresiyle daraltılır (?max_bars_ago=3).
    if max_bars_ago is not None and pat.bars_ago is not None and pat.bars_ago > max_bars_ago:
        raise HTTPException(
            404,
            f"{symbol} için en güncel {indicator} sinyali {pat.bars_ago} bar önce "
            f"(sınır: {max_bars_ago} bar) -- bayat sinyal çizilmez",
        )

    fig = compose(df, pat, symbol=symbol, timeframe=tf.upper(), theme=resolved_theme)
    return Response(content=pio.to_json(fig), media_type="application/json")
