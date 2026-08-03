"""Faz 15: Teknik Analiz kartı context builder'ı.

src/render/card.py ve src/render/calendar_card.py ile AYNI ilke: bu modül
HİÇBİR sayı HESAPLAMAZ -- src.analysis.technical.compute_snapshot() zaten
hesaplanmış bir TechnicalSnapshot verir, burada SADECE Türkçe biçimlendirme
+ görsel konumlandırma (SVG çizgi grafiği koordinatları, 52 hafta çubuğu
yüzdesi) yapılır. Koordinat/yüzde ÖLÇEKLEME işlemi card.py'nin
_build_chart()'ının (bar grafik için pos_pct/neg_pct üretmesi) AYNI
ilkesidir -- render katmanının "biçimlendirme" sayılan, "hesaplama"
SAYILMAYAN tek istisnası budur (01_MIMARI.md/04_KART_VE_GORSEL.md'de zaten
kabul edilmiş bir emsal).

BAĞLAYICI KISITLAR (YENI_FAZ_PROMPTLARI.md Faz 15 -- burada da geçerli):
  K1. Bu kart temel analiz (card.html) kartından GÖRSEL OLARAK AÇIKÇA
      AYRI bir kimlik taşır (mor/mavi aksan, "TEKNİK GÖRÜNÜM" başlığı) ve
      HİÇBİR skor/puan İÇERMEZ.
  K2. "Al/Sat/Tut" sinyali ÜRETİLMEZ. RSI/Bollinger için gösterilen
      "Aşırı Alım/Satım Bölgesi" etiketleri bir EYLEM ÖNERİSİ DEĞİL, sadece
      değerin Wilder'in (RSI) ve Bollinger'in (bantlar) KENDİ yayınladığı
      klasik eşiklere (70/30, üst/alt bant) göre HANGİ BÖLGEDE olduğunu
      bildiren bir OLGUDUR.
  K4. Kartta yasal uyarıya (Kural 10) EK olarak "geçmiş performans gelecek
      getirinin göstergesi değildir" uyarısı bulunur.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from src.analysis.technical import TechnicalSnapshot
from src.formatting import format_number_tr, format_percent_tr

_DISCLAIMER = "Bu içerik yatırım tavsiyesi değildir; yatırım kararı için profesyonel danışmanlık alınmalıdır."
_PAST_PERFORMANCE_WARNING = "Geçmiş performans gelecekteki getirinin göstergesi değildir."

_MARKET_LABELS: dict[str, str] = {"BIST": "BİST", "NASDAQ": "NASDAQ"}
_DATA_SOURCE_NOTES: dict[str, str] = {
    "BIST": "İş Yatırım (HisseTekil, düzeltilmiş seri)",
    "NASDAQ": "Yahoo Finance (chart API)",
}

# RSI'in KENDİ standart esikleri -- Wilder'in orijinal onerisi (1978).
_RSI_ASIRI_ALIM_ESIGI = Decimal(70)
_RSI_ASIRI_SATIM_ESIGI = Decimal(30)

# ADX'in KENDİ standart esikleri -- Wilder'in orijinal onerisi (1978, RSI'in
# 70/30'u gibi tartismasiz standart): <20 zayif/yatay, 20-25 gelisen trend,
# >25 guclu trend. Yon ICERMEZ (K2) -- sadece trendin GUCU hakkinda bir olgu.
_ADX_GUCLU_TREND_ESIGI = Decimal(25)
_ADX_GELISEN_TREND_ESIGI = Decimal(20)

# Fiyat cizgi grafigindeki hafif referans (gridline) sayisi -- min/max
# disinda araya esit araliklarla yerlestirilen, okumayi kolaylastiran ama
# gorseli kirletmeyen (recessive) yatay cizgiler.
_CHART_GRIDLINE_LEVELS = (Decimal("0.25"), Decimal("0.5"), Decimal("0.75"))

# Fiyat cizgi grafigi SVG viewBox boyutlari (CSS px degil -- viewBox
# birimidir, sablonda <svg viewBox="0 0 {W} {H}"> ile olceklenir).
_CHART_VIEWBOX_WIDTH = 1000
_CHART_VIEWBOX_HEIGHT = 320
_CHART_PADDING = 12  # ust/alt kucuk bosluk -- cizgiler viewBox kenarina yapismasin


def _num(value: Decimal | None, decimals: int = 2) -> str:
    return format_number_tr(value, decimals) if value is not None else "N/A"


def _pct(value: Decimal | None, decimals: int = 1) -> str:
    return format_percent_tr(value, decimals) if value is not None else "N/A"


def _price(value: Decimal | None, market: str, decimals: int = 2) -> str:
    if value is None:
        return "N/A"
    if market == "NASDAQ":
        return f"${format_number_tr(value, decimals)}"
    return f"{format_number_tr(value, decimals)} ₺"


def _price_display(price: Decimal | None, market: str) -> str | None:
    if price is None:
        return None
    return _price(price, market)


def _rsi_zone(rsi: Decimal | None) -> tuple[str, str]:
    """(etiket, css_sinifi) -- bkz. modul ust notu K2."""
    if rsi is None:
        return "N/A", "neutral"
    if rsi >= _RSI_ASIRI_ALIM_ESIGI:
        return "Aşırı Alım Bölgesi", "extreme"
    if rsi <= _RSI_ASIRI_SATIM_ESIGI:
        return "Aşırı Satım Bölgesi", "extreme"
    return "Nötr Bölge", "neutral"


def _bollinger_zone(price: Decimal, bb_upper: Decimal | None, bb_lower: Decimal | None) -> tuple[str, str]:
    """bkz. modul ust notu K2 -- sadece fiyatin bantlara GORE konumu."""
    if bb_upper is None or bb_lower is None:
        return "N/A", "neutral"
    if price > bb_upper:
        return "Üst Bandın Üzerinde", "extreme"
    if price < bb_lower:
        return "Alt Bandın Altında", "extreme"
    return "Bantlar İçinde", "neutral"


def _adx_zone(adx: Decimal | None) -> tuple[str, str]:
    """ADX'in KENDİ standart esiklerine (Wilder 1978) gore trend GUCU olgusu
    -- bkz. modul ust notu K2, RSI/Bollinger bolge etiketleriyle AYNI ilke
    (bir yon/AL-SAT sinyali degil, sadece hangi esik araliginda oldugu)."""
    if adx is None:
        return "N/A", "neutral"
    if adx >= _ADX_GUCLU_TREND_ESIGI:
        return "Güçlü Trend", "extreme"
    if adx >= _ADX_GELISEN_TREND_ESIGI:
        return "Gelişen Trend", "neutral"
    return "Zayıf / Yatay Piyasa", "neutral"


def _cross_display(state: str | None, recent: bool) -> tuple[str, str | None, str]:
    """(deger_metni, not_metni, not_sinifi) -- Golden/Death Cross OLGUSU
    (bkz. technical.sma_cross_state() K2 notu). "positive"/"negative"
    siniflari technical_card.html :root'unda ZATEN tanimli --positive/
    --negative token'larini kullanir (yeni renk İCAT edilmedi)."""
    if state == "golden":
        note = "Yakın Zamanda Oluştu" if recent else None
        return "Altın Kesişim (Golden Cross)", note, "positive"
    if state == "death":
        note = "Yakın Zamanda Oluştu" if recent else None
        return "Ölüm Kesişimi (Death Cross)", note, "negative"
    return "N/A", None, "neutral"


def _row(label: str, value_display: str, note_display: str | None = None, note_class: str | None = None) -> dict:
    return {"label": label, "value_display": value_display, "note_display": note_display, "note_class": note_class}


def _group(title: str, rows: list[dict]) -> dict:
    return {"title": title, "rows": rows}


def _build_indicator_groups(snapshot: TechnicalSnapshot, market: str) -> list[dict]:
    """Gosterge tablosunu TEK duz liste yerine kategorilere ayirir (arastirma
    bulgusu: Trend/Momentum/Volatilite gruplamasi bilissel yuku azaltir --
    bkz. YENI_FAZ_PROMPTLARI.md arastirma raporu). Her grup en az bir
    sinyal-degil-olgu (K2) iceriyorsa etiketli gosterilir."""
    adx_zone_label, adx_zone_class = _adx_zone(snapshot.adx_14)
    cross_value, cross_note, cross_class = _cross_display(snapshot.sma_cross_state, snapshot.sma_cross_recent)
    rsi_zone_label, rsi_zone_class = _rsi_zone(snapshot.rsi_14)
    bb_zone_label, bb_zone_class = _bollinger_zone(snapshot.price, snapshot.bb_upper, snapshot.bb_lower)

    return [
        _group(
            "Trend",
            [
                _row("SMA 20", _price(snapshot.sma_20, market)),
                _row("SMA 50", _price(snapshot.sma_50, market)),
                _row("SMA 200", _price(snapshot.sma_200, market)),
                _row("Fiyat / SMA200 Farkı", _pct(snapshot.price_vs_sma200_pct)),
                _row("EMA 12", _price(snapshot.ema_12, market)),
                _row("EMA 26", _price(snapshot.ema_26, market)),
                _row("ADX (14) — Trend Gücü", _num(snapshot.adx_14, 1), adx_zone_label, adx_zone_class),
                _row("SMA50/200 Kesişimi", cross_value, cross_note, cross_class),
            ],
        ),
        _group(
            "Momentum",
            [
                _row("RSI (14)", _num(snapshot.rsi_14, 1), rsi_zone_label, rsi_zone_class),
                _row("MACD Çizgisi", _num(snapshot.macd_line)),
                _row("MACD Sinyal", _num(snapshot.macd_signal)),
                _row("MACD Histogram", _num(snapshot.macd_histogram)),
            ],
        ),
        _group(
            "Volatilite",
            [
                _row("Bollinger Üst Bandı", _price(snapshot.bb_upper, market)),
                _row("Bollinger Orta Bandı", _price(snapshot.bb_middle, market)),
                _row("Bollinger Alt Bandı", _price(snapshot.bb_lower, market), bb_zone_label, bb_zone_class),
                _row("ATR (14)", _price(snapshot.atr_14, market)),
            ],
        ),
    ]


def _scale_series_to_points(series: tuple[Decimal | None, ...], min_v: Decimal, span: Decimal, n: int) -> str | None:
    if n <= 1 or not any(v is not None for v in series):
        return None
    usable_height = Decimal(_CHART_VIEWBOX_HEIGHT - 2 * _CHART_PADDING)
    points = []
    for i, value in enumerate(series):
        if value is None:
            continue
        x = Decimal(i) / Decimal(n - 1) * _CHART_VIEWBOX_WIDTH
        y = _CHART_PADDING + (usable_height - (value - min_v) / span * usable_height)
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points) if points else None


def _build_chart_gridlines(min_v: Decimal, span: Decimal, market: str) -> list[dict]:
    """Fiyat araliginin icine esit araliklarla yerlestirilen, okumayi
    kolaylastiran ama gorseli kirletmeyen (recessive) yatay referans
    cizgileri -- bkz. dataviz ilkesi "grid/axes recessive". SADECE
    KONUMLANDIRMA/OLCEKLEME (mevcut _scale_series_to_points ile AYNI
    istisna, bkz. modul ust notu); yeni bir gosterge HESAPLANMAZ."""
    usable_height = Decimal(_CHART_VIEWBOX_HEIGHT - 2 * _CHART_PADDING)
    lines = []
    for level in _CHART_GRIDLINE_LEVELS:
        price_at_level = min_v + span * level
        y = _CHART_PADDING + (usable_height - level * usable_height)
        lines.append({"y": f"{y:.1f}", "price_display": _price(price_at_level, market)})
    return lines


def _build_price_chart(snapshot: TechnicalSnapshot, market: str) -> dict:
    closes = snapshot.chart_closes
    n = len(closes)
    if n < 2:
        return {"has_data": False}

    all_values = list(closes) + [v for v in snapshot.chart_sma50 if v is not None] + [v for v in snapshot.chart_sma200 if v is not None]
    max_v, min_v = max(all_values), min(all_values)
    span = (max_v - min_v) or Decimal(1)

    return {
        "has_data": True,
        "viewbox_width": _CHART_VIEWBOX_WIDTH,
        "viewbox_height": _CHART_VIEWBOX_HEIGHT,
        "close_points": _scale_series_to_points(closes, min_v, span, n),
        "sma50_points": _scale_series_to_points(snapshot.chart_sma50, min_v, span, n),
        "sma200_points": _scale_series_to_points(snapshot.chart_sma200, min_v, span, n),
        "gridlines": _build_chart_gridlines(min_v, span, market),
        "price_max_display": _num(max_v),
        "price_min_display": _num(min_v),
        "start_date_display": snapshot.chart_dates[0].strftime("%d.%m.%Y"),
        "end_date_display": snapshot.chart_dates[-1].strftime("%d.%m.%Y"),
    }


def _build_week52_bar(snapshot: TechnicalSnapshot, market: str) -> dict:
    if snapshot.week52_high is None or snapshot.week52_low is None or snapshot.week52_position_pct is None:
        return {"has_data": False}

    # Konum yuzdesi tanim geregi [0,100] icinde kalir (bkz. technical.py);
    # yine de gorsel cubugun tasmamasi icin savunmaci sekilde sinirlandirilir.
    clamped_pct = max(Decimal(0), min(Decimal(100), snapshot.week52_position_pct))
    return {
        "has_data": True,
        "low_display": _price(snapshot.week52_low, market),
        "high_display": _price(snapshot.week52_high, market),
        "position_pct": float(clamped_pct),
        "position_display": _pct(snapshot.week52_position_pct),
    }


def _build_volume_strip(snapshot: TechnicalSnapshot) -> dict:
    if snapshot.avg_volume_20 is None or snapshot.volume_ratio_pct is None:
        return {"has_data": False}

    # Cubuk gorseli %200'de doyar (deger yine de sayisal olarak ayrica
    # gosterilir) -- salt gorsel taskin/olcek amacli, herhangi bir esik
    # yorumu/sinyal DEGIL.
    bar_pct = float(min(snapshot.volume_ratio_pct, Decimal(200)) / Decimal(2))
    return {
        "has_data": True,
        "last_volume_display": format_number_tr(snapshot.last_volume, 0),
        "avg_volume_display": format_number_tr(snapshot.avg_volume_20, 0),
        "ratio_display": _pct(snapshot.volume_ratio_pct),
        "bar_pct": bar_pct,
    }


def build_technical_context(
    snapshot: TechnicalSnapshot | None,
    ticker: str,
    market: str,
    company_name: str | None = None,
    now: datetime | None = None,
) -> dict:
    """`snapshot`: src.analysis.technical.compute_snapshot() çıktısı (yeterli
    fiyat geçmişi yoksa None). None ise kart yine üretilir ama
    `has_data=False` ile "yeterli veri yok" durumunu gösterir (Kural 3:
    uydurma yapmak yerine dürüstçe eksikliği bildirir)."""
    now = now or datetime.now()
    market_label = _MARKET_LABELS.get(market, market)
    data_sources_note = _DATA_SOURCE_NOTES.get(market, market)

    base = {
        "ticker": ticker,
        "market_label": market_label,
        "company_name": company_name,
        "report_timestamp": now.strftime("%d.%m.%Y %H:%M"),
        "data_sources_note": data_sources_note,
        "disclaimer": _DISCLAIMER,
        "past_performance_warning": _PAST_PERFORMANCE_WARNING,
    }

    if snapshot is None:
        return {**base, "has_data": False}

    return {
        **base,
        "has_data": True,
        "as_of_date_display": snapshot.as_of_date.strftime("%d.%m.%Y"),
        "price_display": _price_display(snapshot.price, market),
        "indicator_groups": _build_indicator_groups(snapshot, market),
        "price_chart": _build_price_chart(snapshot, market),
        "week52_bar": _build_week52_bar(snapshot, market),
        "volume_strip": _build_volume_strip(snapshot),
    }
