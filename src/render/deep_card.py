""""Derin Kart" (Çok Dönemli Temel Analiz) context builder'ı.

src/render/card.py ve src/render/technical_card.py ile AYNI ilke: bu modül
HİÇBİR sayı HESAPLAMAZ -- src.analysis.trends.compute_multi_period_trend()
zaten hesaplanmış bir `MultiPeriodTrend` verir, burada SADECE Türkçe
biçimlendirme + SVG koordinat/yüzde ÖLÇEKLEME (card.py/technical_card.py'de
zaten kabul edilmiş, "render katmanının biçimlendirme sayılan tek istisnası"
emsali, bkz. 04_KART_VE_GORSEL.md) yapılır.

Bu kart, tek çeyreklik "Bilanço Analizi" kartının (card.html) YANINA, "bu
şirket ZAMAN İÇİNDE nasıl bir seyir izliyor" sorusunu cevaplamak için
eklenir (kullanıcı isteği: "Temel Analiz" butonu tek çeyreklik kartla AYNI
görseli tekrarlıyordu, farklılaştırılması istendi). Görsel kimlik BİLEREK
card.html ile AYNI aileden (amber #f59e0b aksan, koyu tema) -- teknik
kartın (mor/indigo) AKSİNE, bu kart temel analiz ailesinin bir PARÇASI.

Kart tasarımı (2026-08-03, kullanıcının referans görseli -- references/temel.png):
her metrik AYRI, başlıklı bir grafik kartı olarak gösterilir -- tam ızgara
(yatay+dikey), her veri noktasında daire işaretleyici, x-ekseninde HER
noktada çeyrek etiketi, y-ekseninde "güzel" (1/2/5/10 katları) yuvarlak
sayılarla tam görünür eksen, altta renkli daire + etiketli legend. Marj/
oran metrikleri (Brüt-FAVÖK-Net Marj, Cari Oran, Kaldıraç, ROE) İKİ çizgi
gösterebilir: taranan hisse (amber, "self") + sektör ortalaması (mavi,
"sector", varsa -- bkz. src.analysis.trends.compute_sector_average()).
Hasılat (mutlak, para birimi) İSE HER ZAMAN TEK çizgidir -- farklı
büyüklükteki şirketlerin mutlak hasılatını karşılaştırmak yanıltıcı olurdu
(bkz. trends.compute_sector_average() docstring'i).

Kapsam: SADECE sanayi/ticaret (XI_29) ve US_GAAP (NASDAQ sanayi) alan
adlarıyla çalışır -- bkz. src/analysis/trends.py modül notu. Banka/sigorta
(UFRS/UFRS_K) bu kartı DESTEKLEMEZ (farklı alan şeması); çağıran taraf
(telegram_bot.py) sadece uygun `financial_group` için "🔬 Detaylı Analiz"
butonunu gösterir.

BİLEREK KAPSAM DIŞI bırakılan bölüm: "Değerleme çarpanlarının tarihsel
bandı" (P/E, P/B'nin zaman içindeki seyri) -- her dönem için o ANKİ fiyatı
dönem sonu tarihiyle eşleştirmek + o tarihteki pay sayısını doğrulamak
gerektirir, bu oturumda GÜVENİLİR bir yöntem kurulamadı (Kural 3: yanlış
rakamdan iyidir). Bkz. PROJE_HAFIZASI/06_BILINEN_SORUNLAR.md §B23.
"""

from __future__ import annotations

import math
from datetime import datetime
from decimal import ROUND_FLOOR, Decimal

from src.analysis.calculator import Period
from src.analysis.trends import MultiPeriodTrend, PeriodTrendPoint, SeasonalityGroup, SectorAveragePoint
from src.analysis.valuation import ValuationAssessment
from src.formatting import format_currency_short, format_number_tr, format_percent_tr
from src.render import valuation_view

_DISCLAIMER = "Bu içerik yatırım tavsiyesi değildir; yatırım kararı için profesyonel danışmanlık alınmalıdır."

_MARKET_LABELS: dict[str, str] = {"BIST": "BİST", "NASDAQ": "NASDAQ"}
_MARKET_CURRENCY: dict[str, str] = {"BIST": "₺", "NASDAQ": "$"}

# SVG viewBox boyutlari -- technical_card.py ile AYNI ilke (viewBox birimi,
# CSS px degil; sablonda genisligi %100 olceklenir). Her grafik artik TAM
# GENISLIK (2x2 grid DEGIL) -- reference gorseldeki gibi 8-12 nokta x-ekseninde
# rahat sigsin diye. Kenar boşlukları ASİMETRİK: sol tarafta y-ekseni
# etiketleri ("1.234,5 mr ₺" gibi uzun olabilir), altta x-ekseni etiketleri
# için yer bırakılır (reference görseldeki gibi TAM ızgara: hem yatay hem
# dikey ince çizgiler + eksen dışına taşmayan etiketler).
_CHART_VIEWBOX_WIDTH = 1100
_CHART_VIEWBOX_HEIGHT = 260
_PAD_LEFT = 88
_PAD_RIGHT = 20
_PAD_TOP = 16
_PAD_BOTTOM = 34
_TARGET_TICK_COUNT = 5

# En az bu kadar (gercek, None olmayan) veri noktasi yoksa bir bolum
# "yeterli veri/gecmis yok" olarak isaretlenir (K4).
_MIN_CHART_POINTS = 2


def _period_label(period: Period) -> str:
    year, quarter = period
    return f"{quarter // 3}Ç{year % 100:02d}"


def _currency_symbol(market: str) -> str:
    return _MARKET_CURRENCY.get(market, "₺")


def _fmt_currency(value: Decimal | None, market: str) -> str:
    return format_currency_short(value, symbol=_currency_symbol(market)) if value is not None else "N/A"


def _fmt_pct(value: Decimal | None, decimals: int = 1) -> str:
    return format_percent_tr(value, decimals) if value is not None else "N/A"


def _fmt_ratio(value: Decimal | None) -> str:
    # CANLI KULLANICI GERI BILDIRIMI (2026-08-04): "x" ibaresi (orn. "5,30x")
    # gereksiz/kalabalik bulundu -- SADECE sayi gosterilsin istendi.
    return format_number_tr(value, 2) if value is not None else "N/A"


def _fmt_score(value: Decimal | None) -> str:
    return f"{format_number_tr(value, 2)}/10" if value is not None else "N/A"


def _nice_ticks(min_v: Decimal, max_v: Decimal, target_count: int = _TARGET_TICK_COUNT) -> list[Decimal]:
    """[min_v, max_v] aralığını kapsayan "güzel" (1/2/5/10 katları) yuvarlak
    eksen tikleri üretir -- card.py::_nice_axis_step() ile AYNI ilke
    (Fintables referans kartlarındaki gibi 25/20/15/10/5/0 türü yuvarlak
    sayılar), ama SADECE 0'dan yukarı DEĞİL, HERHANGİ bir [min,max] aralığı
    için genelleştirilmiş (marj/net kâr gibi seriler NEGATİF olabilir,
    bkz. modül üst notu -- referans görseldeki "Net Kar Marjı" grafiği de
    negatif bölgeye iner)."""
    if min_v == max_v:
        # Tek bir sabit deger -- etrafina kucuk bir pay birak.
        pad = abs(min_v) / 10 if min_v != 0 else Decimal(1)
        min_v, max_v = min_v - pad, max_v + pad

    span = max_v - min_v
    rough_step = float(span) / max(target_count - 1, 1)
    magnitude = Decimal(10) ** math.floor(math.log10(rough_step))
    normalized = rough_step / float(magnitude)
    if normalized <= 1:
        nice_multiplier = Decimal(1)
    elif normalized <= 2:
        nice_multiplier = Decimal(2)
    elif normalized <= 5:
        nice_multiplier = Decimal(5)
    else:
        nice_multiplier = Decimal(10)
    step = nice_multiplier * magnitude

    tick = (min_v / step).to_integral_value(rounding=ROUND_FLOOR) * step
    ticks = []
    while tick <= max_v + step / 2:
        ticks.append(tick)
        tick += step
        if len(ticks) > target_count + 4:  # guvenlik siniri, sonsuz donguye karsi
            break
    return ticks


def _build_chart(
    series_specs: list[tuple[str, str, list[Decimal | None]]],
    x_labels: list[str],
    value_fmt,
) -> dict:
    """Bir ya da iki çizgili (AYNI ölçekte) SAF SVG çizgi grafiği için veri
    hazırlar -- tam ızgara, köşe noktalarında daire işaretleyici, x-ekseninde
    HER noktada etiket, y-ekseninde "güzel" yuvarlak sayılar (bkz.
    _nice_ticks()). `series_specs`: [(key, label, values)] -- `key`
    "self"/"sector" (tekil hisse/sektör ortalaması) ya da mevsimsellik/skor
    gibi tek-seri grafiklerde herhangi bir sabit ad olabilir.

    Bir seri içindeki None değerler ATLANIR (o noktada ne çizgi ne daire
    çizilir). Tüm seriler TAMAMEN None ise ya da `x_labels` 2'den azsa
    `has_data=False` döner (K4 -- tek nokta bir "trend" GRAFİĞİ sayılmaz)."""
    n = len(x_labels)
    all_values = [v for _, _, values in series_specs for v in values if v is not None]
    if n < _MIN_CHART_POINTS or not all_values:
        return {"has_data": False}

    ticks = _nice_ticks(min(all_values), max(all_values))
    min_v, max_v = ticks[0], ticks[-1]
    span = (max_v - min_v) or Decimal(1)
    usable_height = Decimal(_CHART_VIEWBOX_HEIGHT - _PAD_TOP - _PAD_BOTTOM)
    usable_width = Decimal(_CHART_VIEWBOX_WIDTH - _PAD_LEFT - _PAD_RIGHT)
    plot_top, plot_bottom = Decimal(_PAD_TOP), Decimal(_CHART_VIEWBOX_HEIGHT - _PAD_BOTTOM)
    plot_left, plot_right = Decimal(_PAD_LEFT), Decimal(_CHART_VIEWBOX_WIDTH - _PAD_RIGHT)

    def _x(i: int) -> Decimal:
        return plot_left + (Decimal(i) / Decimal(n - 1) * usable_width if n > 1 else Decimal(0))

    def _y(v: Decimal) -> Decimal:
        return plot_top + (usable_height - (v - min_v) / span * usable_height)

    lines = []
    for key, label, values in series_specs:
        points = [(_x(i), _y(v)) for i, v in enumerate(values) if v is not None]
        polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in points) if points else None
        markers = [{"x": f"{x:.1f}", "y": f"{y:.1f}"} for x, y in points]
        lines.append({"key": key, "label": label, "points": polyline, "markers": markers})

    gridlines = [
        {
            "y": f"{_y(t):.1f}",
            "display": value_fmt(t),
            "x1": f"{plot_left:.1f}",
            "x2": f"{plot_right:.1f}",
            "label_x": f"{plot_left - 8:.1f}",
        }
        for t in ticks
    ]
    x_ticks = [
        {"x": f"{_x(i):.1f}", "label": label, "y1": f"{plot_top:.1f}", "y2": f"{plot_bottom:.1f}"}
        for i, label in enumerate(x_labels)
    ]

    return {
        "has_data": True,
        "viewbox_width": _CHART_VIEWBOX_WIDTH,
        "viewbox_height": _CHART_VIEWBOX_HEIGHT,
        "x_label_y": f"{plot_bottom + 18:.1f}",
        "lines": lines,
        "gridlines": gridlines,
        "x_ticks": x_ticks,
    }


def _self_and_sector_specs(
    points: tuple[PeriodTrendPoint, ...],
    field: str,
    ticker: str,
    sector_average: dict[Period, SectorAveragePoint],
    sector_label: str | None,
) -> list[tuple[str, str, list[Decimal | None]]]:
    """Bir oran/marj metriği için (self, [sector]) seri listesini kurar --
    sektör ortalaması SADECE veri varsa (`sector_average` doluysa) ikinci
    seri olarak eklenir, yoksa TEK çizgi (self) döner."""
    specs = [("self", ticker, [getattr(p, field) for p in points])]
    if sector_average:
        sector_values = [
            getattr(sector_average[p.period], field) if p.period in sector_average else None for p in points
        ]
        if any(v is not None for v in sector_values):
            specs.append(("sector", sector_label or "Sektör Ortalaması", sector_values))
    return specs


def _build_metric_chart(
    title: str,
    subtitle: str,
    points: tuple[PeriodTrendPoint, ...],
    field: str,
    ticker: str,
    sector_average: dict[Period, SectorAveragePoint],
    sector_label: str | None,
    value_fmt,
) -> dict:
    labels = [_period_label(p.period) for p in points]
    specs = _self_and_sector_specs(points, field, ticker, sector_average, sector_label)
    return {"title": title, "subtitle": subtitle, "chart": _build_chart(specs, labels, value_fmt)}


def _build_revenue_chart(points: tuple[PeriodTrendPoint, ...], ticker: str, market: str) -> dict:
    """Çeyreklik Satışlar -- HER ZAMAN TEK çizgi (bkz. modül üst notu:
    mutlak/para birimi değerler şirketler arası karşılaştırılamaz)."""
    labels = [_period_label(p.period) for p in points]
    specs = [("self", ticker, [p.revenue for p in points])]
    currency_fmt = lambda v: _fmt_currency(v, market)  # noqa: E731
    return {"title": "Çeyreklik Satışlar", "subtitle": "Hasılat", "chart": _build_chart(specs, labels, currency_fmt)}


def _build_score_history_chart(score_history: list[tuple[datetime, float]], ticker: str) -> dict:
    if len(score_history) < _MIN_CHART_POINTS:
        return {"has_data": False}
    labels = [dt.strftime("%d.%m.%y") for dt, _ in score_history]
    values = [Decimal(str(score)) for _, score in score_history]
    return _build_chart([("self", ticker, values)], labels, _fmt_score)


def _build_seasonality_charts(seasonality: tuple[SeasonalityGroup, ...], ticker: str, market: str) -> list[dict]:
    currency_fmt = lambda v: _fmt_currency(v, market)  # noqa: E731
    charts = []
    for group in seasonality:
        labels = [str(year) for year in group.years]
        title = f"{group.quarter_number // 3}. Çeyrek — Yıllar Arası Hasılat"
        chart = _build_chart([("self", ticker, list(group.revenues))], labels, currency_fmt)
        charts.append({"title": title, "chart": chart})
    return charts


def _build_valuation_context(assessment: ValuationAssessment | None, market: str) -> dict:
    """"Değerleme Analizi" paneli için context -- HEM Derin Kart HEM Bilanço
    kartının (`card.py`) PAYLAŞTIĞI `src.render.valuation_view.build_valuation_view()`'e
    ince bir sarmalayıcı (Kural 4: render katmanı hiçbir oran HESAPLAMAZ,
    formatlama mantığı İKİ KEZ YAZILMASIN diye tek yerde tutulur)."""
    return valuation_view.build_valuation_view(assessment, market)


def build_deep_card_context(
    trend: MultiPeriodTrend | None,
    score_history: list[tuple[datetime, float]],
    ticker: str,
    market: str,
    company_name: str | None = None,
    sector_average: dict[Period, SectorAveragePoint] | None = None,
    sector_name: str | None = None,
    peer_count: int = 0,
    valuation_assessment: ValuationAssessment | None = None,
    now: datetime | None = None,
) -> dict:
    """`trend`: src.analysis.trends.compute_multi_period_trend() çıktısı
    (yeterli finansal veri yoksa None). `score_history`:
    repository.get_score_history() çıktısı (eskiden yeniye). `sector_average`:
    src.analysis.trends.compute_sector_average() çıktısı (peer yoksa
    None/boş -- bu durumda TÜM oran grafikleri otomatik olarak TEK çizgiye
    düşer, bkz. _self_and_sector_specs()). `peer_count`: çağıran tarafın
    (repository.get_sector_peer_tickers() ile) bulduğu TOPLAM karşılaştırma
    şirketi sayısı -- SectorAveragePoint.peer_count'tan (dönem bazlı, hangi
    peer'in HANGİ döneme veri sağladığını sayar) BİLEREK AYRI tutulur:
    peer'ler her dönemde MÜKEMMEL örtüşmeyebilir (biri bir çeyreği
    kaçırmış olabilir), bu durumda dönem-bazlı max() yanıltıcı şekilde
    düşük çıkardı (CANLI gözlemlendi: 2 peer'li TATGD'de max=1). Başlıkta
    HER ZAMAN "kaç şirketle karşılaştırılıyor" sorusunun DOĞRU cevabı
    gösterilir. `valuation_assessment`: src.analysis.valuation.
    compute_valuation_assessment() çıktısı (peer/fiyat verisi yoksa None) --
    "Değerleme Analizi" paneli (sektöre göre ucuz/pahalı + momentum + ima
    edilen hedef fiyat), mevcut Bilanço Skoru'ndan BAĞIMSIZ (bkz. modül üst
    notu). Hepsi bu fonksiyona HAZIR gelir -- burada YENİDEN hesaplama
    YAPILMAZ."""
    now = now or datetime.now()
    market_label = _MARKET_LABELS.get(market, market)
    sector_average = sector_average or {}
    sector_label = f"Sektör Ort. ({sector_name})" if sector_name else "Sektör Ortalaması"

    base = {
        "ticker": ticker,
        "market_label": market_label,
        "company_name": company_name,
        "sector_name": sector_name,
        "peer_count": peer_count,
        "report_timestamp": now.strftime("%d.%m.%Y %H:%M"),
        "disclaimer": _DISCLAIMER,
    }

    if trend is None or not trend.points:
        return {**base, "has_data": False}

    points = trend.points
    period_count = len(points)

    metric_charts = [
        _build_revenue_chart(points, ticker, market),
        _build_metric_chart("Brüt Kâr Marjı (Çeyreklik)", "", points, "gross_margin_pct", ticker, sector_average, sector_label, _fmt_pct),
        _build_metric_chart("FAVÖK Marjı (Çeyreklik)", "", points, "ebitda_margin_pct", ticker, sector_average, sector_label, _fmt_pct),
        _build_metric_chart("Net Kâr Marjı (Çeyreklik)", "", points, "net_margin_pct", ticker, sector_average, sector_label, _fmt_pct),
        _build_metric_chart("Cari Oran", "Dönen Varlıklar / Kısa Vadeli Yükümlülükler", points, "current_ratio", ticker, sector_average, sector_label, _fmt_ratio),
        _build_metric_chart("Kaldıraç Oranı", "Net Borç / FAVÖK (TTM)", points, "net_debt_to_ebitda", ticker, sector_average, sector_label, _fmt_ratio),
        _build_metric_chart("Özkaynak Kârlılığı (ROE)", "TTM net kâr / güncel özkaynak", points, "roe_pct", ticker, sector_average, sector_label, _fmt_pct),
    ]

    return {
        **base,
        "has_data": True,
        "period_count": period_count,
        "period_range_display": f"{_period_label(points[0].period)} — {_period_label(points[-1].period)}",
        "metric_charts": metric_charts,
        "score_history_chart": _build_score_history_chart(score_history, ticker),
        "seasonality_charts": _build_seasonality_charts(trend.seasonality, ticker, market),
        "valuation": _build_valuation_context(valuation_assessment, market),
    }
