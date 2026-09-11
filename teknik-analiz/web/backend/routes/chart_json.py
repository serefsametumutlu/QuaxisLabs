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

from tlab.chart.composers.boundary_pattern import compose as compose_boundary_pattern
from tlab.chart.composers.broadening import compose as compose_broadening
from tlab.chart.composers.channel import compose as compose_channel
from tlab.chart.composers.fib_retracement import compose as compose_fib
from tlab.chart.composers.neckline import compose as compose_neckline
from tlab.chart.composers.pair import compose as compose_pair
from tlab.chart.composers.pole_flag import compose as compose_pole_flag
from tlab.chart.composers.price_structure import compose as compose_price_structure
from tlab.chart.composers.series_overlay import compose as compose_overlay
from tlab.chart.composers.triangle import compose as compose_triangle
from tlab.chart.composers.wedge import compose as compose_wedge
from tlab.chart.composers.xabcd import compose as compose_xabcd
from tlab.chart.composers.zones import compose as compose_zones
from tlab.chart.tokens import ThemeName
from tlab.indicators.harmonics.adapter import result_to_pattern as adapt_harmonic
from tlab.indicators.momentum.chart_adapter import (
    alpha_rank_to_overlay,
    momentum_rank_to_overlay,
)
from tlab.indicators.pairs.chart_adapter import to_view as adapt_pair
from tlab.indicators.patterns.boundary_adapter import to_pattern as adapt_boundary
from tlab.indicators.patterns.flag_adapter import to_pattern as adapt_flag
from tlab.indicators.patterns.fvg_adapter import to_pattern as adapt_fvg
from tlab.indicators.patterns.neckline_adapter import to_pattern as adapt_neckline
from tlab.indicators.structure.chart_adapter import (
    golden_zone_to_fib,
    price_structure_to_report,
    supply_demand_to_zones,
    swing_fib_abcd_to_pattern,
)
from tlab.indicators.trend.breakout_adapter import to_pattern as adapt_breakout
from tlab.indicators.trend.chart_adapter import (
    ewmac_to_overlay,
    ma_systems_to_overlay,
    weekly_channel_to_channel,
)
from tlab.viz.live import compute_live, compute_pair_live

router = APIRouter(tags=["chart_json"])

_THEME_MAP: dict[str, ThemeName] = {"dark": "dark", "classic": "light", "editorial": "paper"}

# indikatör adı -> (adaptör, komposer).
#
# Adaptör `IndicatorResult`i TİPLİ bir sözleşmeye çevirir (hesap yapmaz,
# tarayıcının KENDİ geometrisini okur), komposer yalnızca çizer. Aşama
# B'de her yeni gösterge burada TEK bir satır ekler; akışın geri kalanı
# DEĞİŞMEZ. Frontend bu sözlüğü `/api/catalog`un `interactive` alanı
# üzerinden görür — orada ELLE tutulan ikinci bir liste YOK.
_SUPPORTED = {
    "patterns.triangle": (adapt_boundary, compose_triangle),
    "patterns.wedge": (adapt_boundary, compose_wedge),
    "patterns.broadening": (adapt_boundary, compose_broadening),
    # 8 harmonik okulun HEPSİ `HarmonicIndicator`ın tek çıktı biçimini
    # paylaşır -> tek adaptör, tek komposer.
    "harmonic.carney": (adapt_harmonic, compose_xabcd),
    "harmonic.pesavento": (adapt_harmonic, compose_xabcd),
    "harmonic.gilmore": (adapt_harmonic, compose_xabcd),
    "harmonic.cypher": (adapt_harmonic, compose_xabcd),
    "harmonic.nenstar": (adapt_harmonic, compose_xabcd),
    "harmonic.navarro200": (adapt_harmonic, compose_xabcd),
    "harmonic.five_zero": (adapt_harmonic, compose_xabcd),
    "harmonic.three_drives": (adapt_harmonic, compose_xabcd),
    # trend -- seri bindirmeleri
    "trend.ma_systems": (ma_systems_to_overlay, compose_overlay),
    "trend.ewmac": (ewmac_to_overlay, compose_overlay),
    # boyun cizgili donus formasyonlari -- iki gosterge TEK adaptor
    "patterns.head_shoulders": (adapt_neckline, compose_neckline),
    "patterns.double_top_bottom": (adapt_neckline, compose_neckline),
    # arz/talep bolgeleri
    "patterns.flag_pennant": (adapt_flag, compose_pole_flag),
    "patterns.breakout_fvg": (adapt_fvg, compose_boundary_pattern),
    "structure.supply_demand": (supply_demand_to_zones, compose_zones),
    "structure.golden_zone": (golden_zone_to_fib, compose_fib),
    # haftalik kanal -- yalnizca GUNCEL kanal (frozen olanlar cizilmez)
    "trend.weekly_channel": (weekly_channel_to_channel, compose_channel),
    # kirilim -- ~20 turden EN YUKSEK kaliteli GUNCEL olan (bkz. adaptor)
    "trend.breakouts": (adapt_breakout, compose_boundary_pattern),
    # evren gostergeleri -- tum evren hesaplanir, live.py onbellekler
    "momentum.alpha_rank": (alpha_rank_to_overlay, compose_overlay),
    "momentum.momentum_rank": (momentum_rank_to_overlay, compose_overlay),
    # AB=CD -- X'SIZ 4 noktali; ayni komposer, farkli iskelet
    "structure.swing_fib_abcd": (swing_fib_abcd_to_pattern, compose_xabcd),
    # yapi raporu -- kendi komposeri (trend cizgisi + bolge + POC/VAH/VAL)
    "structure.price_structure": (price_structure_to_report, compose_price_structure),
    # pair -- AYRI akis (asagi bak): iki sembol, `df` yok
    "pair.relative_momentum": (adapt_pair, compose_pair),
    "pair.vol_harvest": (adapt_pair, compose_pair),
}

# Pair gostergeleri farkli bir akis kullanir:
#  * veri: `compute_pair_live` (Y ve X HAM serileri de doner),
#  * komposer imzasi `df` ALMAZ -- pair grafigi tek sembolun
#    mumlarini cizmez, iki normalize seri + z-skor + ozkaynak cizer.
_PAIR = {"pair.relative_momentum", "pair.vol_harvest"}


@router.get("/chart.json")
def get_chart_json(
    symbol: str, tf: str, indicator: str, market: str = "bist", theme: str = "dark",
    max_bars_ago: int | None = 60,
) -> Response:
    entry = _SUPPORTED.get(indicator)
    if entry is None:
        raise HTTPException(422, f"{indicator} henüz tlab/chart'a bağlanmadı")
    adapt, compose = entry
    resolved_theme = _THEME_MAP.get(theme, "dark")

    if indicator in _PAIR:
        try:
            result, df_y, df_x = compute_pair_live(indicator, symbol, tf, market)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(404, f"Veri bulunamadı: {exc}") from exc
        view = adapt(result, df_y, df_x)
        if view is None:
            raise HTTPException(404, f"{symbol} için {indicator} görünümü kurulamadı")
        fig = compose(view, theme=resolved_theme)
        return Response(content=pio.to_json(fig), media_type="application/json")

    try:
        result, df = compute_live(indicator, symbol, tf, market)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, f"Veri bulunamadı: {exc}") from exc
    if df is None:
        raise HTTPException(422, f"{indicator} bu modda desteklenmiyor")

    pat = adapt(result, df)
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
    # `getattr`: her sözleşme `bars_ago` TAŞIMAZ -- `structure.supply_demand`
    # adaptörü `list[Zone]` döndürüyor ve `pat.bars_ago` AttributeError
    # veriyordu (rota 500'e düşüyordu). Yaşı olmayan sonuçlarda tazelik
    # kapısı UYGULANMAZ; bölgeler zaten "şu an geçerli olanlar".
    bars_ago = getattr(pat, "bars_ago", None)
    if max_bars_ago is not None and bars_ago is not None and bars_ago > max_bars_ago:
        raise HTTPException(
            404,
            f"{symbol} için en güncel {indicator} sinyali {bars_ago} bar önce "
            f"(sınır: {max_bars_ago} bar) -- bayat sinyal çizilmez",
        )

    fig = compose(df, pat, symbol=symbol, timeframe=tf.upper(), theme=resolved_theme)
    return Response(content=pio.to_json(fig), media_type="application/json")
