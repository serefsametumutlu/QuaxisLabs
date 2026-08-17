"""ABCD Formasyon kartı context builder'ı (Faz 5 — kart tasarımı).

Mimari kararlar: `docs/spec/spec_abcd_mimari_kararlar.md` (Karar 1/2).

  Karar 1 (K2) -- Bu kart "deneysel sinyal üretici" bir özelliktir, temel
  (card.html) ve teknik (technical_card.html) kartlardan GÖRSEL OLARAK
  AÇIKÇA ayrışan üçüncü bir kimlik taşır (amber/turuncu aksan + üst bantta
  "⚠ DENEYSEL SİNYAL" rozeti). `src.analysis.abcd_pattern`'in ürettiği
  yönlü BUY/SELL sinyali, temel/teknik-olgu skorlarından TAMAMEN
  BAĞIMSIZDIR -- kart bunu hem görsel kimlikle hem metinle (disclaimer +
  ayrı bir "deneysel formasyon" notuyla) açıkça belirtir.

  Karar 2 -- `src.analysis.abcd_pattern` KASITLI olarak float kullanır
  (Pine parity). Bu modül, Karar 2'nin tanımladığı TEK render sınırıdır:
  `Signal`'in float alanları (a_price..d_price, entry_ref, tp1, tp2, sl,
  bc_ratio, cd_ratio) SADECE burada `Decimal(str(...))`'a çevrilip Türkçe
  string'e formatlanır. Bu float değerler `scorer.py`/`calculator.py`'ye
  ASLA sızmaz (bu modülün import ettiği tek domain nesnesi `Signal`'dir).

card.py/technical_card.py ile AYNI genel ilke: bu modül şablonun
GÖSTERECEĞİ hiçbir sayıyı YENİDEN İCAT ETMEZ -- `Signal` (abcd_pattern.detect())
zaten hesaplanmış nihai değerleri taşır, burada SADECE (a) Türkçe
biçimlendirme ve (b) candlestick/formasyon/TP-SL çizgilerinin SVG
koordinatlarına ÖLÇEKLENMESİ yapılır -- `technical_card.py`'nin
`_scale_series_to_points()`/`_value_to_y()` ile AYNI "biçimlendirme
sayılan, hesaplama SAYILMAYAN" render istisnası (bkz. o modülün üst notu).

`bars`: çağıran taraf tarafından ZATEN hazırlanmış OHLCV kayıtlarının
listesi (`src.analysis.abcd_pattern.OHLC_COLUMNS` alanlarını taşıyan
dict'ler, artan zamana sıralı). Bu modül bars'ı ÇEKMEZ/DÖNÜŞTÜRMEZ, sadece
verildiği haliyle kullanır. `signal.a_bar/b_bar/c_bar/d_bar`, bu AYNI
`bars` listesinin indeksleridir (abcd_pattern.detect()'in girdisi olan
DataFrame ile bire bir aynı sıradadır) -- çağıran taraf bunu garanti eder.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from src.analysis.abcd_pattern import Signal
from src.formatting import format_number_tr, format_percent_tr

_DISCLAIMER = "Bu içerik yatırım tavsiyesi değildir; yatırım kararı için profesyonel danışmanlık alınmalıdır."
_EXPERIMENTAL_NOTE = (
    "Bu deneysel bir formasyon tespitidir, temel/teknik analiz skorlarından bağımsızdır."
)

_MARKET_LABELS: dict[str, str] = {"BIST": "BİST", "NASDAQ": "NASDAQ"}
_DATA_SOURCE_NOTES: dict[str, str] = {
    "BIST": "Yahoo Finance (yfinance, deneysel ABCD veri katmanı)",
    "NASDAQ": "Yahoo Finance (yfinance)",
}
_TF_LABELS: dict[str, str] = {
    "1d": "Günlük",
    "1D": "Günlük",
    "1wk": "Haftalık",
    "1W": "Haftalık",
    "60m": "60 Dakika",
    "1h": "60 Dakika",
    "60": "60 Dakika",  # abcd_data.TIMEFRAMES kodu (bot buradan çağırır)
    "120m": "120 Dakika",
    "2h": "120 Dakika",
    "120": "120 Dakika",
    "240m": "240 Dakika",
    "4h": "240 Dakika",
    "240": "240 Dakika",
}

# SVG viewBox boyutları (CSS px değil -- viewBox birimi, technical_card.py
# ile AYNI ölçekleme ilkesi). Sağ tarafta ENTRY/TP1/TP2/SL çizgi
# etiketlerinin sığması için ayrı bir "etiket şeridi" (_LABEL_RESERVE)
# bırakılır -- mumlar bu alana TAŞMAZ.
_CHART_VIEWBOX_WIDTH = 1200
_CHART_VIEWBOX_HEIGHT = 460
_CHART_PAD_TOP = 20
_CHART_PAD_BOTTOM = 28
_CHART_PAD_LEFT = 8
_LABEL_RESERVE = 168

_CHART_GRIDLINE_LEVELS = (Decimal("0.25"), Decimal("0.5"), Decimal("0.75"))

# ABCD nokta etiketlerinin mumdan dikey uzaklığı (viewBox birimi).
_POINT_LABEL_OFFSET = 22


def _d(value: float | None) -> Decimal | None:
    """`Signal`'in float alanını Decimal'e çevirir -- Karar 2'nin tanımladığı
    TEK render sınırı burasıdır (bkz. modül üst notu). `str(value)` ile
    çevrilir (doğrudan `Decimal(value)` float ikili temsilinin gürültüsünü
    (örn. 0.1 -> 0.1000000000000000055511151231257827021181583404541015625)
    Decimal'e taşır; `str()` insan-okunur ondalık temsili korur)."""
    if value is None:
        return None
    try:
        if value != value:  # NaN kontrolü (math.isnan importu gerektirmeden)
            return None
    except TypeError:
        pass
    return Decimal(str(value))


def _price(value: float | None, market: str, decimals: int = 2) -> str:
    dec = _d(value)
    if dec is None:
        return "N/A"
    if market == "NASDAQ":
        return f"${format_number_tr(dec, decimals)}"
    return f"{format_number_tr(dec, decimals)} ₺"


def _pct_ratio(ratio: float | None) -> str:
    """0-1 aralığındaki bir oranı (bc_ratio/cd_ratio) yüzde string'ine
    çevirir -- `technical_card.py::_pct`'in yaptığı "değeri OLDUĞU GİBİ
    göster" işleminin ölçek birimi farkı (oran -> yüzde) dışında AYNISI."""
    dec = _d(ratio)
    if dec is None:
        return "N/A"
    return format_percent_tr(dec * 100, 1)


def _format_bar_date(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        try:
            return value.strftime("%d.%m.%Y")
        except (ValueError, TypeError):
            pass
    return str(value)[:10]


def _scale_x(index: int, n: int, plot_width: float) -> Decimal:
    slot = Decimal(plot_width) / Decimal(n)
    return Decimal(_CHART_PAD_LEFT) + slot * (Decimal(index) + Decimal("0.5"))


def _scale_y(price: Decimal, min_v: Decimal, span: Decimal) -> Decimal:
    usable_height = Decimal(_CHART_VIEWBOX_HEIGHT - _CHART_PAD_TOP - _CHART_PAD_BOTTOM)
    return Decimal(_CHART_PAD_TOP) + (usable_height - (price - min_v) / span * usable_height)


def _build_candles(bars: list[dict], n: int, plot_width: float, min_v: Decimal, span: Decimal) -> list[dict]:
    slot = Decimal(plot_width) / Decimal(n)
    body_width = slot * Decimal("0.62")
    candles = []
    prev_close: Decimal | None = None
    for i, bar in enumerate(bars):
        close = _d(bar.get("close"))
        if close is None:
            prev_close = None
            continue
        open_ = _d(bar.get("open"))
        # BIST günlük veride (Karar 3) open HER ZAMAN None olabilir --
        # bu durumda muma bir gövde yerine "doji" (kapanışta düz çizgi)
        # çizilir, bar sessizce ATLANMAZ (kart görsel olarak tam kalır).
        if open_ is None:
            open_ = prev_close if prev_close is not None else close
        high = _d(bar.get("high")) or max(open_, close)
        low = _d(bar.get("low")) or min(open_, close)

        x_center = _scale_x(i, n, plot_width)
        is_bull = close >= open_
        body_top_price = max(open_, close)
        body_bottom_price = min(open_, close)
        y_body_top = _scale_y(body_top_price, min_v, span)
        y_body_bottom = _scale_y(body_bottom_price, min_v, span)
        body_height = y_body_bottom - y_body_top
        if body_height < Decimal("1.4"):
            body_height = Decimal("1.4")

        candles.append(
            {
                "x": f"{x_center:.1f}",
                "wick_y1": f"{_scale_y(high, min_v, span):.1f}",
                "wick_y2": f"{_scale_y(low, min_v, span):.1f}",
                "body_x": f"{(x_center - body_width / 2):.1f}",
                "body_y": f"{y_body_top:.1f}",
                "body_width": f"{body_width:.1f}",
                "body_height": f"{body_height:.1f}",
                "is_bull": is_bull,
            }
        )
        prev_close = close
    return candles


def _build_gridlines(min_v: Decimal, span: Decimal, market: str) -> list[dict]:
    lines = []
    for level in _CHART_GRIDLINE_LEVELS:
        price_at_level = min_v + span * level
        y = _scale_y(price_at_level, min_v, span)
        lines.append({"y": f"{y:.1f}", "price_display": _price(float(price_at_level), market)})
    return lines


def _abcd_point(
    label: str, bar_index: int, price: float, bars: list[dict], n: int, plot_width: float, min_v: Decimal, span: Decimal, above: bool
) -> dict:
    clamped = max(0, min(n - 1, bar_index))
    x = _scale_x(clamped, n, plot_width)
    y = _scale_y(_d(price), min_v, span)
    label_y = y - _POINT_LABEL_OFFSET if above else y + _POINT_LABEL_OFFSET
    bar_date = _format_bar_date(bars[clamped].get("time")) if 0 <= clamped < len(bars) else ""
    return {
        "label": label,
        "x": f"{x:.1f}",
        "y": f"{y:.1f}",
        "label_y": f"{label_y:.1f}",
        "above": above,
        "bar_date_display": bar_date,
    }


def _build_chart(bars: list[dict], signal: Signal, market: str) -> dict:
    n = len(bars)
    if n < 2:
        return {"has_data": False}

    plot_width = _CHART_VIEWBOX_WIDTH - _CHART_PAD_LEFT - _LABEL_RESERVE

    prices: list[Decimal] = []
    for bar in bars:
        for key in ("open", "high", "low", "close"):
            v = _d(bar.get(key))
            if v is not None:
                prices.append(v)
    for v in (signal.a_price, signal.b_price, signal.c_price, signal.d_price, signal.entry_ref, signal.tp1, signal.tp2, signal.sl):
        dv = _d(v)
        if dv is not None:
            prices.append(dv)

    if not prices:
        return {"has_data": False}

    min_v, max_v = min(prices), max(prices)
    span = (max_v - min_v) or Decimal(1)
    # Formasyon/TP-SL çizgileri mum aralığının dışına taşabilir -- üstte/
    # altta ince bir nefes payı (span'ın %6'sı) bırakılır ki çizgiler
    # viewBox kenarına yapışmasın.
    breathing = span * Decimal("0.06")
    min_v -= breathing
    max_v += breathing
    span = max_v - min_v

    candles = _build_candles(bars, n, plot_width, min_v, span)
    gridlines = _build_gridlines(min_v, span, market)

    is_bull = signal.direction == 1
    a_above, b_above, c_above, d_above = (True, False, True, False) if is_bull else (False, True, False, True)

    points = [
        _abcd_point("A", signal.a_bar, signal.a_price, bars, n, plot_width, min_v, span, a_above),
        _abcd_point("B", signal.b_bar, signal.b_price, bars, n, plot_width, min_v, span, b_above),
        _abcd_point("C", signal.c_bar, signal.c_price, bars, n, plot_width, min_v, span, c_above),
        _abcd_point("D", signal.d_bar, signal.d_price, bars, n, plot_width, min_v, span, d_above),
    ]
    px = {p["label"]: p for p in points}

    triangle_abc = " ".join(f"{px[l]['x']},{px[l]['y']}" for l in ("A", "B", "C"))
    triangle_bcd = " ".join(f"{px[l]['x']},{px[l]['y']}" for l in ("B", "C", "D"))

    d_x = float(px["D"]["x"])
    line_x_end = _CHART_PAD_LEFT + plot_width

    def _level_line(price: float | None, css_class: str, label_text: str) -> dict | None:
        dec = _d(price)
        if dec is None:
            return None
        y = _scale_y(dec, min_v, span)
        return {
            "x_start": f"{d_x:.1f}",
            "x_end": f"{line_x_end:.1f}",
            "y": f"{y:.1f}",
            "css_class": css_class,
            "label_text": label_text,
            "price_display": _price(price, market),
        }

    return {
        "has_data": True,
        "viewbox_width": _CHART_VIEWBOX_WIDTH,
        "viewbox_height": _CHART_VIEWBOX_HEIGHT,
        "label_column_x": f"{(line_x_end + 10):.1f}",
        "candles": candles,
        "gridlines": gridlines,
        "triangle_abc_points": triangle_abc,
        "triangle_bcd_points": triangle_bcd,
        "abcd_points": points,
        "entry_line": _level_line(signal.entry_ref, "entry", "ENTRY"),
        "tp1_line": _level_line(signal.tp1, "tp1", "TP1"),
        "tp2_line": _level_line(signal.tp2, "tp2", "TP2"),
        "sl_line": _level_line(signal.sl, "sl", "SL"),
        "start_date_display": _format_bar_date(bars[0].get("time")),
        "end_date_display": _format_bar_date(bars[-1].get("time")),
    }


def build_abcd_card_context(
    bars: list[dict],
    signal: Signal,
    ticker: str,
    market: str,
    tf: str,
    company_name: str | None = None,
    now: datetime | None = None,
) -> dict:
    """`bars`: OHLCV dict listesi (bkz. modül üst notu). `signal`:
    `src.analysis.abcd_pattern.detect()`'in döndürdüğü onaylanmış TEK bir
    `Signal` (kart, TEK formasyonu gösterir -- birden çok sinyal varsa
    çağıran taraf hangisinin gösterileceğine karar verir, bu fonksiyon
    seçim YAPMAZ). `tf`: zaman dilimi kodu (örn. "1d", "4h") --
    `_TF_LABELS`'te yoksa ham string olduğu gibi gösterilir."""
    now = now or datetime.now()
    market_label = _MARKET_LABELS.get(market, market)
    tf_label = _TF_LABELS.get(tf, tf)
    is_bull = signal.direction == 1

    return {
        "ticker": ticker,
        "company_name": company_name,
        "market_label": market_label,
        "tf_label": tf_label,
        "report_timestamp": now.strftime("%d.%m.%Y %H:%M"),
        "data_sources_note": _DATA_SOURCE_NOTES.get(market, market),
        "disclaimer": _DISCLAIMER,
        "experimental_note": _EXPERIMENTAL_NOTE,
        "direction": "BUY" if is_bull else "SELL",
        "direction_label": "AL (BUY) SİNYALİ" if is_bull else "SAT (SELL) SİNYALİ",
        "direction_class": "bull" if is_bull else "bear",
        "signal_date_display": _format_bar_date(signal.signal_time),
        "entry_display": _price(signal.entry_ref, market),
        "tp1_display": _price(signal.tp1, market),
        "tp2_display": _price(signal.tp2, market),
        "sl_display": _price(signal.sl, market),
        "bc_ratio_display": _pct_ratio(signal.bc_ratio),
        "cd_ratio_display": _pct_ratio(signal.cd_ratio),
        "abcd_table": [
            {"label": "A", "price_display": _price(signal.a_price, market), "date_display": _format_bar_date(bars[signal.a_bar].get("time")) if 0 <= signal.a_bar < len(bars) else ""},
            {"label": "B", "price_display": _price(signal.b_price, market), "date_display": _format_bar_date(bars[signal.b_bar].get("time")) if 0 <= signal.b_bar < len(bars) else ""},
            {"label": "C", "price_display": _price(signal.c_price, market), "date_display": _format_bar_date(bars[signal.c_bar].get("time")) if 0 <= signal.c_bar < len(bars) else ""},
            {"label": "D", "price_display": _price(signal.d_price, market), "date_display": _format_bar_date(bars[signal.d_bar].get("time")) if 0 <= signal.d_bar < len(bars) else ""},
        ],
        "chart": _build_chart(bars, signal, market),
    }
