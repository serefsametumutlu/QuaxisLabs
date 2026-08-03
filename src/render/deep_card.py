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

Kapsam: SADECE sanayi/ticaret (XI_29) ve US_GAAP (NASDAQ sanayi) alan
adlarıyla çalışır (revenue/gross_profit/operating_profit_ebitda_base/
depreciation_amortization/net_income/equity/financial_debt/cash/
financial_investments + "_cum" karşılıkları) -- bkz. src/analysis/trends.py
modül notu. Banka/sigorta (UFRS/UFRS_K) bu kartı DESTEKLEMEZ (farklı alan
şeması); çağıran taraf (telegram_bot.py) sadece uygun `financial_group`
için "🔬 Detaylı Analiz" butonunu gösterir.

BİLEREK KAPSAM DIŞI bırakılan bölüm: "Değerleme çarpanlarının tarihsel
bandı" (P/E, P/B'nin zaman içindeki seyri) -- her dönem için o ANKİ fiyatı
dönem sonu tarihiyle eşleştirmek + o tarihteki pay sayısını doğrulamak
gerektirir, bu oturumda GÜVENİLİR bir yöntem kurulamadı (Kural 3: yanlış
rakamdan iyidir). Bkz. PROJE_HAFIZASI/06_BILINEN_SORUNLAR.md §B22 (Bollinger
squeeze ile AYNI ilke: araştırmada değerli bulundu ama kasıtlı ertelendi).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from src.analysis.calculator import Period
from src.analysis.trends import MultiPeriodTrend, PeriodTrendPoint, SeasonalityGroup
from src.formatting import format_currency_short, format_number_tr, format_percent_tr

_DISCLAIMER = "Bu içerik yatırım tavsiyesi değildir; yatırım kararı için profesyonel danışmanlık alınmalıdır."

_MARKET_LABELS: dict[str, str] = {"BIST": "BİST", "NASDAQ": "NASDAQ"}
_MARKET_CURRENCY: dict[str, str] = {"BIST": "₺", "NASDAQ": "$"}

# SVG viewBox boyutlari -- technical_card.py ile AYNI ilke (viewBox birimi,
# CSS px degil; sablonda genisligi %100 olceklenir).
_CHART_VIEWBOX_WIDTH = 1000
_CHART_VIEWBOX_HEIGHT = 220
_CHART_PADDING = 10
_CHART_GRIDLINE_LEVELS = (Decimal("0.25"), Decimal("0.5"), Decimal("0.75"))

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
    return f"{format_number_tr(value, 2)}x" if value is not None else "N/A"


def _fmt_score(value: Decimal | None) -> str:
    return f"{format_number_tr(value, 2)}/10" if value is not None else "N/A"


def _build_chart(
    series_specs: list[tuple[str, str, list[Decimal | None]]],
    x_labels: list[str],
    value_fmt,
) -> dict:
    """Tek ya da çok çizgili (AYNI ölçekte) SAF SVG çizgi grafiği için veri
    hazırlar -- technical_card.py::_build_price_chart()'ın GENELLEŞTİRİLMİŞ
    hali (N adet adlandırılmış seri kabul eder). `value_fmt`: bir Decimal'i
    gridline/min-max etiketi için Türkçe stringe çevirir (çağıran tarafın
    o serinin BİRİMİNİ -- para/yüzde/oran -- bilmesi gerekir).

    Bir seri içindeki None değerler ATLANIR (polyline o noktada kesilir),
    tüm seriler TAMAMEN None ise ya da `x_labels` 2'den azsa `has_data=False`
    döner (K4 -- tek nokta bir "trend" GRAFİĞİ sayılmaz)."""
    n = len(x_labels)
    all_values = [v for _, _, values in series_specs for v in values if v is not None]
    if n < _MIN_CHART_POINTS or not all_values:
        return {"has_data": False}

    max_v, min_v = max(all_values), min(all_values)
    span = (max_v - min_v) or Decimal(1)
    usable_height = Decimal(_CHART_VIEWBOX_HEIGHT - 2 * _CHART_PADDING)

    def _scale(values: list[Decimal | None]) -> str | None:
        points = []
        for i, v in enumerate(values):
            if v is None:
                continue
            x = Decimal(i) / Decimal(n - 1) * _CHART_VIEWBOX_WIDTH
            y = _CHART_PADDING + (usable_height - (v - min_v) / span * usable_height)
            points.append(f"{x:.1f},{y:.1f}")
        return " ".join(points) if points else None

    lines = [{"key": key, "label": label, "points": _scale(values)} for key, label, values in series_specs]
    gridlines = []
    for level in _CHART_GRIDLINE_LEVELS:
        y = _CHART_PADDING + (usable_height - level * usable_height)
        gridlines.append({"y": f"{y:.1f}", "display": value_fmt(min_v + span * level)})

    return {
        "has_data": True,
        "viewbox_width": _CHART_VIEWBOX_WIDTH,
        "viewbox_height": _CHART_VIEWBOX_HEIGHT,
        "lines": lines,
        "gridlines": gridlines,
        "x_start_label": x_labels[0],
        "x_end_label": x_labels[-1],
        "max_display": value_fmt(max_v),
        "min_display": value_fmt(min_v),
    }


def _build_overview_charts(points: tuple[PeriodTrendPoint, ...], market: str) -> list[dict]:
    labels = [_period_label(p.period) for p in points]
    currency_fmt = lambda v: _fmt_currency(v, market)  # noqa: E731

    specs = [
        ("revenue", "Hasılat", [p.revenue for p in points]),
        ("ebitda", "FAVÖK", [p.ebitda for p in points]),
        ("net_income", "Net Kâr", [p.net_income for p in points]),
        ("equity", "Özkaynak", [p.equity for p in points]),
    ]
    return [
        {"title": title, "chart": _build_chart([(key, title, values)], labels, currency_fmt)}
        for key, title, values in specs
    ]


def _build_margin_chart(points: tuple[PeriodTrendPoint, ...]) -> dict:
    labels = [_period_label(p.period) for p in points]
    specs = [
        ("gross", "Brüt Marj", [p.gross_margin_pct for p in points]),
        ("ebitda", "FAVÖK Marjı", [p.ebitda_margin_pct for p in points]),
        ("net", "Net Marj", [p.net_margin_pct for p in points]),
    ]
    return _build_chart(specs, labels, _fmt_pct)


def _build_leverage_chart(points: tuple[PeriodTrendPoint, ...]) -> dict:
    labels = [_period_label(p.period) for p in points]
    specs = [("leverage", "Net Borç/FAVÖK", [p.net_debt_to_ebitda for p in points])]
    return _build_chart(specs, labels, _fmt_ratio)


def _build_roe_chart(points: tuple[PeriodTrendPoint, ...]) -> dict:
    labels = [_period_label(p.period) for p in points]
    specs = [("roe", "ROE", [p.roe_pct for p in points])]
    return _build_chart(specs, labels, _fmt_pct)


def _build_score_history_chart(score_history: list[tuple[datetime, float]]) -> dict:
    if len(score_history) < _MIN_CHART_POINTS:
        return {"has_data": False}
    labels = [dt.strftime("%d.%m.%y") for dt, _ in score_history]
    values = [Decimal(str(score)) for _, score in score_history]
    return _build_chart([("score", "Radar Skoru", values)], labels, _fmt_score)


def _build_seasonality_charts(seasonality: tuple[SeasonalityGroup, ...], market: str) -> list[dict]:
    currency_fmt = lambda v: _fmt_currency(v, market)  # noqa: E731
    charts = []
    for group in seasonality:
        labels = [str(year) for year in group.years]
        title = f"{group.quarter_number // 3}. Çeyrek — Yıllar Arası Hasılat"
        chart = _build_chart([("revenue", "Hasılat", list(group.revenues))], labels, currency_fmt)
        charts.append({"title": title, "chart": chart})
    return charts


def build_deep_card_context(
    trend: MultiPeriodTrend | None,
    score_history: list[tuple[datetime, float]],
    ticker: str,
    market: str,
    company_name: str | None = None,
    now: datetime | None = None,
) -> dict:
    """`trend`: src.analysis.trends.compute_multi_period_trend() çıktısı
    (yeterli finansal veri yoksa None). `score_history`:
    repository.get_score_history() çıktısı (eskiden yeniye). Her ikisi de
    bu fonksiyona HAZIR gelir -- burada YENİDEN hesaplama YAPILMAZ."""
    now = now or datetime.now()
    market_label = _MARKET_LABELS.get(market, market)

    base = {
        "ticker": ticker,
        "market_label": market_label,
        "company_name": company_name,
        "report_timestamp": now.strftime("%d.%m.%Y %H:%M"),
        "disclaimer": _DISCLAIMER,
    }

    if trend is None or not trend.points:
        return {**base, "has_data": False}

    points = trend.points
    period_count = len(points)

    return {
        **base,
        "has_data": True,
        "period_count": period_count,
        "period_range_display": f"{_period_label(points[0].period)} — {_period_label(points[-1].period)}",
        "overview_charts": _build_overview_charts(points, market),
        "margin_chart": _build_margin_chart(points),
        "leverage_chart": _build_leverage_chart(points),
        "roe_chart": _build_roe_chart(points),
        "score_history_chart": _build_score_history_chart(score_history),
        "seasonality_charts": _build_seasonality_charts(trend.seasonality, market),
    }
