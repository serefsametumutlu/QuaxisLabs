"""Kullanıcı isteği (2026-08-12): dashboard.html'deki her satıra tıklanınca
açılan, TEK bir şirkete özel detay sayfası -- `src/render/dashboard.py` ile
BİREBİR AYNI iki-aşamalı desen (quaxis-mimari anayasa: render katmanı
HİÇBİR skor/formül YENİDEN HESAPLAMAZ, sadece var olan veriyi okur+biçimlendirir):

    1. build_company_detail_data(session, ticker, market) -- `MarketScanResult`
       satırını (mercekler_detay JSON blob'u DAHİL -- bkz. scripts/tarama_toplu.py
       ::_mercekler_detay/_component_to_dict, ZATEN o hissenin KENDİ değerleriyle
       üretilmiş `reasoning_tr` metinleri taşıyor) + `repository.get_financials()`
       çok-dönemli ham finansal veriyi bir dict'e çevirir.
    2. render_company_detail_html(data) -- Jinja2 ile tek-dosyalık, harici
       kaynak İÇERMEYEN HTML üretir (`_design_tokens.css` dashboard.html/card.html
       ile AYNI kaynaktan include edilir -- görsel kimlik tutarlılığı).

Dosya adı deseni: `output/detay/{market}_{ticker}.html` (bkz. detail_relative_path/
detail_output_path) -- dashboard.py bu İKİ yardımcıyı import ederek `detail_url`
alanını doldurur (TEK kaynak, path mantığı iki yerde TEKRARLANMAZ).

Finansal tablo özeti (Görev 1 madde 4) İSTİSNAİ bir durum gibi görünebilir:
`repository.get_financials()` HAM item_code->value sözlüğü döner, ama bu
item_code'lar `src/bot/pipeline.py::_standardize_to_records*()` tarafından
ZATEN "revenue"/"net_income"/"equity" gibi STANDART alan adlarına çevrilerek
yazılmıştır (bkz. o modülün üst notu + `compute_multi_lens_score_for_ticker()`
içindeki `financials_by_period = repository.get_financials(...)` çağrısının
DOĞRUDAN `calculator.analyze()`'a verilmesi) -- yani bu modülün DB'den okuyup
`calculator.analyze()`/`analyze_bank()`/`analyze_insurance()`/`analyze_financing()`/
`analyze_us()` çağırması YENİ bir hesaplama İCAT ETMEZ, pipeline.py'nin
ZATEN yaptığı AYNI saf-matematik dönüşümü (I/O'suz, `calculator.py` modül
docstring'i: "HİÇBİR LLM çağrısı yoktur ve src.fetchers/src.db import ETMEZ")
tekrar çağırır -- görevin kendi talimatı da BUNU açıkça istiyor ("calculator.py'nin
zaten hesapladığı alanlardan ... mevcut alanları TABLOLA").
"""

from __future__ import annotations

import dataclasses
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import jinja2
from sqlalchemy.orm import Session

import config
from src.analysis import calculator
from src.db import repository
from src.db.models import Company, MarketScanResult, utcnow_naive
from src.formatting import format_currency_short, format_number_tr, format_percent_tr

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(_TEMPLATE_DIR),
    autoescape=jinja2.select_autoescape(["html"]),
)

# src/render/dashboard.py::_BADGE_CLASS/_SIRKET_TURU_DISPLAY ile BİREBİR AYNI
# eşlemeler -- görsel kimlik tutarlılığı (bkz. o modülün üst notu). Burada
# KOPYALANIR (import EDİLMEZ) -- dashboard.py'nin alanları alt çizgiyle
# başlayan modül-içi sabitlerdir, card.py'deki build_bank/us/insurance
# context fonksiyonlarının da birbirinden bağımsız kendi küçük eşlemelerini
# tuttuğu desenle TUTARLI (proje kuralı: paralel context inşacılar arası
# ince eşlemeler ayrı tutulur, ORTAK olan sadece _line_item_row gibi gerçek
# hesaplama/formatlama mantığıdır -- burada YOK, sadece sabit sözlük).
_BADGE_CLASS: dict[str, str] = {
    "SAĞLAM": "saglam",
    "DENGELİ": "dengeli",
    "KARIŞIK": "karisik",
    "RİSKLİ": "riskli",
    "YETERSİZ VERİ": "yetersiz",
}

_SIRKET_TURU_DISPLAY: dict[str | None, str] = {
    "sanayi": "Sanayi",
    "abd_sanayi": "ABD Sanayi",
    "banka": "Banka",
    "sigorta": "Sigorta",
    "finansman": "Finansman",
    "gyo": "GYO",
    None: "—",
}

# (MarketScanResult sütun öneki [ASCII], mercekler_detay/label sözlük anahtarı
# [Türkçe glif], görüntü etiketi) -- src/render/dashboard.py::_MERCEK_ANAHTAR_ETIKET
# İLE AYNI ayrım gereksinimi: SQLAlchemy sütun adları ASCII ("deger_score"),
# ama mercekler_detay JSON'u VE görüntü etiketleri Türkçe glif kullanır
# ("değer") -- ikisi KARIŞTIRILIRSA getattr() AttributeError fırlatır.
_MERCEK_ANAHTAR_ETIKET: tuple[tuple[str, str, str], ...] = (
    ("deger", "değer", "Değer"),
    ("kalite", "kalite", "Kalite"),
    ("buyume", "büyüme", "Büyüme"),
    ("guvenlik", "güvenlik", "Güvenlik"),
)

# quarterly_series alan adlarından bazıları (banka: net_interest_income)
# calculator.FIELD_LABELS_TR içinde YOK (o sözlük SADECE income_statement/
# balance_sheet alanlarını kapsıyor, bkz. calculator.py card.py._build_chart
# çağrılarındaki "Net Faiz Geliri" başlığıyla AYNI, elle kopyalanan tek
# etiket) -- geri kalan tüm quarterly_series alanları (revenue/ebitda/
# net_income/loans/financing_revenue/gross_written_premiums/technical_balance)
# zaten FIELD_LABELS_TR'de VAR, burada TEKRARLANMAZ.
_QUARTERLY_FIELD_LABEL_FALLBACK: dict[str, str] = {
    "net_interest_income": "Net Faiz Geliri",
}

FAALIYET_RAPORU_PLACEHOLDER = (
    "Bu bölüm henüz araştırılmadı -- gelecek bir fazda faaliyet raporu/dipnot "
    "analizinden doldurulacak. Şu an burada gösterilecek gerçek bir bulgu yok."
)


def detail_relative_path(ticker: str, market: str) -> str:
    """`output/` klasörüne göre RELATİF yol (dashboard.html'in `<a href>`
    değeri için) -- `detail_output_path()` ile TEK kaynak, iki yerde
    (dashboard.py + company_detail.py) yol mantığı TEKRARLANMASIN diye."""
    return f"detay/{market}_{ticker}.html"


def detail_output_path(ticker: str, market: str) -> Path:
    return config.BASE_DIR / "output" / detail_relative_path(ticker, market)


def _num(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _tr_datetime(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%d.%m.%Y %H:%M")


def _decimal_or_none(value: str | None) -> Decimal | None:
    """`mercekler_detay` JSON'undaki sayısal alanlar `str()` olarak
    saklanmıştı (bkz. scripts/tarama_toplu.py::_component_to_dict --
    SQLite JSON sütunu Decimal'i SERİLEŞTİREMEZ) -- burada geri Decimal'e
    çevrilir ki `src.formatting` yardımcıları normal şekilde çalışsın."""
    if value is None:
        return None
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError):
        return None


def _mercek_summary(row: MarketScanResult, key: str) -> dict[str, Any] | None:
    score = getattr(row, f"{key}_score")
    badge = getattr(row, f"{key}_badge")
    coverage = getattr(row, f"{key}_coverage_pct")
    if score is None and badge is None:
        return None
    return {
        "score_display": format_number_tr(score, decimals=1) if score is not None else "N/A",
        "badge": badge,
        "badge_class": _BADGE_CLASS.get(badge or "", "yetersiz"),
        "data_coverage_pct_display": format_percent_tr(coverage, decimals=0) if coverage is not None else "—",
    }


def _mercek_components(row: MarketScanResult, key: str) -> list[dict[str, str]]:
    """`mercekler_detay[key]`'deki HER bileşeni (skor/ağırlık/katkı/hazır
    Türkçe gerekçe) tabloya hazır string'lere çevirir. Bu, kullanıcının
    "hangi formülle, hisseye özgü hangi değerle hesaplandı" sorusunun
    doğrudan cevabıdır -- `reasoning_tr` ZATEN o hissenin kendi verileriyle
    scorer.py tarafından üretilmiş bir cümledir, burada SADECE taşınır."""
    detay = row.mercekler_detay or {}
    bilesenler = detay.get(key, [])
    rows = []
    for b in bilesenler:
        score = _decimal_or_none(b.get("score"))
        weight_nominal = _decimal_or_none(b.get("weight_nominal"))
        weight_effective = _decimal_or_none(b.get("weight_effective"))
        contribution = _decimal_or_none(b.get("contribution"))
        rows.append({
            "name": b.get("name", "—"),
            "score_display": f"{format_number_tr(score, decimals=1)}/10" if score is not None else "N/A",
            "weight_nominal_display": f"%{format_number_tr(weight_nominal, decimals=0)}" if weight_nominal is not None else "—",
            "weight_effective_display": f"%{format_number_tr(weight_effective, decimals=1)}" if weight_effective is not None else "—",
            "contribution_display": format_number_tr(contribution, decimals=2) if contribution is not None else "N/A",
            "reasoning_tr": b.get("reasoning_tr") or "—",
            "veri_eksik": score is None,
        })
    return rows


def _carpanlar_block(row: MarketScanResult) -> dict[str, Any] | None:
    if row.current_price is None and row.market_cap is None and row.pe_ratio is None:
        return None
    symbol = "₺" if row.currency == "TRY" else ("$" if row.currency == "USD" else "")
    return {
        "price_display": f"{format_number_tr(row.current_price, decimals=2)} {symbol}".strip() if row.current_price is not None else "—",
        "market_cap_display": format_currency_short(row.market_cap, symbol=symbol) if row.market_cap is not None else "—",
        "pe_ratio_display": format_number_tr(row.pe_ratio, decimals=1) if row.pe_ratio is not None else "N/A",
        "pb_ratio_display": format_number_tr(row.pb_ratio, decimals=2) if row.pb_ratio is not None else "N/A",
        "ev_ebitda_display": format_number_tr(row.ev_ebitda, decimals=1) if row.ev_ebitda is not None else "N/A",
    }


def _period_label(period: tuple[int, int], market: str, is_annual_only: bool) -> str:
    """`src/render/card.py::_quarter_label`/`_fiscal_quarter_label`'ın BİREBİR
    aynı biçimlendirme mantığı -- KOPYALANDI (import EDİLMEDİ), card.py'nin
    kendisi de build_card_context()/build_us_card_context() arasında AYNI
    şekilde küçük yardımcıları TEKRAR tanımlıyor (proje deseni, mimari
    ihlal DEĞİL -- sadece bir sabit biçimlendirme kuralı, hesaplama yok)."""
    year, quarter = period
    if market == "NASDAQ":
        if is_annual_only:
            return f"FY{year % 100:02d}"
        return f"FY{year % 100:02d} Ç{quarter // 3}"
    return f"{quarter // 3}Ç{year % 100:02d}"


def _line_change_row(item: calculator.LineItemChange | None, currency_symbol: str, fallback_label: str) -> dict[str, str]:
    if item is None:
        return {"label": fallback_label, "current": "N/A", "comparison": "N/A", "change": "veri yok"}
    current = format_currency_short(item.current, symbol=currency_symbol) if item.current is not None else "N/A"
    comparison = format_currency_short(item.comparison, symbol=currency_symbol) if item.comparison is not None else "N/A"
    change = format_percent_tr(item.percent_change) if item.percent_change is not None else item.change_label
    return {"label": item.label_tr, "current": current, "comparison": comparison, "change": change}


def _summary_rows(section: Any, currency_symbol: str) -> list[dict[str, str]]:
    """`IncomeStatementSummary`/`BalanceSheetSummary` (VE banka/sigorta/
    finansman karşılıkları) dataclass'larını GENERİK olarak (alan adı
    SABİTLENMEDEN, `dataclasses.fields()` ile) satırlara çevirir -- 5
    şablonun HER BİRİ için ayrı ayrı elle eşleme YAZMAK yerine (calculator.py
    zaten her şablon için doğru LineItemChange nesnelerini üretiyor, bu
    fonksiyon SADECE onları taşır)."""
    rows = []
    for f in dataclasses.fields(section):
        item = getattr(section, f.name)
        fallback_label = calculator.FIELD_LABELS_TR.get(f.name, f.name)
        rows.append(_line_change_row(item, currency_symbol, fallback_label))
    return rows


def _quarterly_trend(quarterly_series: list, market: str, is_annual_only: bool, currency_symbol: str) -> list[dict[str, Any]]:
    if not quarterly_series:
        return []
    metric_fields = [f.name for f in dataclasses.fields(quarterly_series[0]) if f.name != "period"]
    trend = []
    for name in metric_fields:
        label = calculator.FIELD_LABELS_TR.get(name, _QUARTERLY_FIELD_LABEL_FALLBACK.get(name, name))
        points = []
        for point in quarterly_series:
            value = getattr(point, name)
            points.append({
                "period_label": _period_label(point.period, market, is_annual_only),
                "display": format_currency_short(value, symbol=currency_symbol) if value is not None else "N/A",
            })
        trend.append({"label": label, "points": points})
    return trend


def _build_financials_block(session: Session, row: MarketScanResult) -> dict[str, Any]:
    """Görev 1 madde 4: `get_financials()`'tan gelen çok-dönemli ham veriyi
    `calculator.py`'nin ZATEN tanımlı analyze*() fonksiyonlarına (şablona
    göre seçilir) verip SADECE üretilen alanları tabloya döker -- YENİ bir
    formül/eşik İCAT EDİLMEZ (bkz. modül üst notu)."""
    financials_by_period = repository.get_financials(session, row.ticker, n_periods=8)
    if not financials_by_period:
        return {
            "available": False,
            "income_rows": [], "balance_rows": [], "quarterly_trend": [],
            "note": "Bu şirket için veritabanında henüz çok-dönemli finansal tablo verisi yok.",
        }

    currency_symbol = "$" if row.currency == "USD" else "₺"
    template = row.template

    try:
        if template == "banka":
            company = session.get(Company, row.ticker)
            variant = "participation" if (company is not None and company.financial_group == "UFRS_KATILIM") else "conventional"
            analysis = calculator.analyze_bank(row.ticker, financials_by_period, bank_variant=variant)
        elif template == "sigorta":
            analysis = calculator.analyze_insurance(row.ticker, financials_by_period)
        elif template == "finansman":
            analysis = calculator.analyze_financing(row.ticker, financials_by_period)
        elif template == "abd_sanayi":
            analysis = calculator.analyze_us(row.ticker, financials_by_period)
        else:  # "sanayi" -- VE bilinmeyen/None şablonlarda GÜVENLİ varsayılan (BİST XI_29 en yaygın durum)
            analysis = calculator.analyze(row.ticker, financials_by_period)
    except Exception:  # noqa: BLE001 -- src/render/card.py::_company_logo_data_uri İLE AYNI ilke: bu SADECE
        # görüntüleme katmanındaki bir zenginleştirmedir (skor/rozet zaten row'da hazır, ETKİLENMEZ),
        # bir tickera özgü beklenmeyen veri şekli TÜM sayfanın render'ını ÇÖKERTMEMELİ -- açıkça
        # loglanır VE kullanıcıya DÜRÜST bir "işlenemedi" notu gösterilir (Kural 3: sessiz varsayılan
        # DEĞİL, görünür bir uyarı).
        logger.warning("%s icin finansal tablo ozeti islenemedi", row.ticker, exc_info=True)
        return {
            "available": False,
            "income_rows": [], "balance_rows": [], "quarterly_trend": [],
            "note": "Finansal tablo verisi işlenirken beklenmeyen bir durum oluştu -- skor/rozet bundan ETKİLENMEDİ.",
        }

    is_annual_only = getattr(analysis, "is_annual_only", False)
    return {
        "available": True,
        "currency_symbol": currency_symbol,
        "latest_period_display": _period_label(analysis.latest_period, row.market, is_annual_only),
        "income_rows": _summary_rows(analysis.income_statement, currency_symbol),
        "balance_rows": _summary_rows(analysis.balance_sheet, currency_symbol),
        "quarterly_trend": _quarterly_trend(analysis.quarterly_series, row.market, is_annual_only, currency_symbol),
        "note": None,
    }


def build_company_detail_data(session: Session, ticker: str, market: str, *, now: datetime | None = None) -> dict[str, Any] | None:
    """`MarketScanResult` + `mercekler_detay` + `get_financials()`'ı company
    detay sayfası şemasına çevirir. Satır YOKSA veya piyasa uyuşmuyorsa
    `None` döner (çağıran taraf -- ileride /telegram veya bir web route --
    404 benzeri bir yanıt üretebilsin diye)."""
    ticker = ticker.strip().upper()
    row = session.get(MarketScanResult, ticker)
    if row is None or row.market != market:
        return None

    now = now or utcnow_naive()
    has_snapshot = row.bilesik_score is not None or row.deger_score is not None or row.kalite_score is not None

    bilesik = None
    mercekler = None
    if has_snapshot:
        bilesik = {
            "score_display": format_number_tr(row.bilesik_score, decimals=1) if row.bilesik_score is not None else "N/A",
            "badge": row.bilesik_badge,
            "badge_class": _BADGE_CLASS.get(row.bilesik_badge or "", "yetersiz"),
            "data_coverage_pct_display": (
                format_percent_tr(row.bilesik_data_coverage_pct, decimals=0)
                if row.bilesik_data_coverage_pct is not None else "—"
            ),
            "dahil_edilen_mercekler": row.dahil_edilen_mercekler or [],
        }
        mercekler = {}
        for prefix, key, label in _MERCEK_ANAHTAR_ETIKET:
            summary = _mercek_summary(row, prefix)
            if summary is None:
                mercekler[key] = None
                continue
            summary["label"] = label
            summary["components"] = _mercek_components(row, key)
            mercekler[key] = summary

    return {
        "ticker": row.ticker,
        "company_name": row.company_name or row.ticker,
        "market": row.market,
        "ust_sektor": row.ust_sektor or "Sınıflandırılmamış",
        "sirket_turu_display": _SIRKET_TURU_DISPLAY.get(row.sirket_turu, row.sirket_turu or "—"),
        "template": row.template,
        "period_display": f"{row.year}/{row.period}" if row.year is not None and row.period is not None else "—",
        "scan_status": row.scan_status,
        "computed_at_display": _tr_datetime(row.computed_at),
        "generated_at_display": _tr_datetime(now),
        "bilesik": bilesik,
        "mercekler": mercekler,
        "carpanlar": _carpanlar_block(row),
        "financials": _build_financials_block(session, row),
        "faaliyet_raporu_placeholder": FAALIYET_RAPORU_PLACEHOLDER,
        "dashboard_relative_url": "../dashboard.html",
    }


def render_company_detail_html(data: dict[str, Any], template_name: str = "company_detail.html") -> str:
    template = _env.get_template(template_name)
    return template.render(data=data)


def build_and_write_company_detail(
    ticker: str, market: str, output_path: str | Path | None = None, *, session: Session | None = None,
) -> str | None:
    """Tek şirket için `output/detay/{market}_{ticker}.html` üretir --
    `src/render/dashboard.py::build_and_write_dashboard()`'ın tek-şirketlik
    karşılığı. Satır bulunamazsa `None` döner (dosya YAZILMAZ)."""
    if session is not None:
        data = build_company_detail_data(session, ticker, market)
    else:
        with repository.get_session() as owned_session:
            data = build_company_detail_data(owned_session, ticker, market)

    if data is None:
        return None

    out_path = Path(output_path) if output_path is not None else detail_output_path(ticker, market)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_company_detail_html(data)
    out_path.write_text(html, encoding="utf-8")
    return str(out_path)


def build_and_write_all_company_details(*, session: Session | None = None, output_dir: str | Path | None = None) -> list[str]:
    """Görev 2: HER `MarketScanResult` satırı için ayrı bir detay sayfası
    üretir -- `scripts/tarama_toplu.py` tarafından doldurulmuş TÜM satırları
    (BIST + NASDAQ) tarar, ağa GİTMEZ (SADECE DB okur, `build_and_write_
    dashboard()` ile AYNI "veri kaynağı zaten hazır" ilkesi).

    `output_dir` verilmezse varsayılan `output/detay/` kullanılır
    (`detail_output_path()`); testler VEYA `dashboard.py`'nin özel bir
    `output_path` ile çağrılması durumunda GERÇEK proje `output/` klasörünü
    KİRLETMEMEK için AYRI bir dizin geçirilebilir (dosya adı deseni --
    `{market}_{ticker}.html` -- AYNI kalır)."""
    if session is not None:
        return _write_all_details(session, output_dir)
    with repository.get_session() as owned_session:
        return _write_all_details(owned_session, output_dir)


def _write_all_details(session: Session, output_dir: str | Path | None = None) -> list[str]:
    written: list[str] = []
    for row in repository.get_market_scan_results(session):
        data = build_company_detail_data(session, row.ticker, row.market)
        if data is None:
            continue
        if output_dir is not None:
            out_path = Path(output_dir) / f"{row.market}_{row.ticker}.html"
        else:
            out_path = detail_output_path(row.ticker, row.market)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        html = render_company_detail_html(data)
        out_path.write_text(html, encoding="utf-8")
        written.append(str(out_path))
    return written


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Kullanım: python -m src.render.company_detail <TICKER> <BIST|NASDAQ>")
        raise SystemExit(1)
    yol = build_and_write_company_detail(sys.argv[1].upper(), sys.argv[2].upper())
    print(f"Detay sayfası üretildi: {yol}" if yol else "Satır bulunamadı.")
