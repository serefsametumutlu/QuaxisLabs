"""Halka arz izahname kartının context builder'ı -- Faz 20 devamı (2026-08-06).

`card.py`/`fund_card.py`/`calendar_card.py` ile AYNI ilke: burada HİÇBİR sayı
HESAPLANMAZ -- `src.analysis.ipo_assessment.IpoAssessment` (zaten hesaplanmış)
ve `src.fetchers.kap_ipo.IpoFacts` (zaten ayrıştırılmış) sadece Türkçe
biçimlendirilip şablona hazır string olarak geçirilir (Kural 3: eksik alan
None ise `src.formatting` zaten "-" döner, burada UYDURMA YAPILMAZ).

Tasarım: kullanıcının paylaştığı referans görsel (üçüncü taraf bir halka arz
infografiği -- turuncu marka, ikon ızgarası, tahsisat/dağıtım tabloları)
YAPISAL olarak (bilgi kartı + tablo düzeni) esinlenmiştir ama piksel bazında
KOPYA DEĞİLDİR -- QuaxisLabs'ın KENDİ marka dili (logo/masthead/disclaimer,
projenin genelindeki dark glassmorphism/monospace tema, `fund_card.py` ile
AYNI renk paleti) kullanılır (bkz. `fund_card.py` modül üst notundaki AYNI
gerekçe: "içerik çalmış gibi görünmek istemem").
"""

from __future__ import annotations

import re
from datetime import date, datetime

from src.analysis.ipo_assessment import IpoAssessment
from src.fetchers.ipo_broker_page import SupplementaryIpoInfo
from src.fetchers.ipo_price_report import PriceReportFinancials
from src.fetchers.kap_ipo import IpoFacts, IzahnameDisclosure
from src.formatting import format_currency_short, format_number_tr, format_percent_tr

_AY_ADLARI_TR: dict[int, str] = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
    7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık",
}

_DISCLAIMER = "Bu içerik yatırım tavsiyesi değildir; yatırım kararı için profesyonel danışmanlık alınmalıdır."

# Talep toplama tarihi/günü, Katılım Endeksi uygunluğu, fiyat istikrarı gibi
# alanlar KAP'ın AYRI yayınladığı "Tasarruf Sahiplerine Satış Duyurusu"
# belgesinde yer alır -- bu belge canlı test edilen 3/3 örnekte (VEYAS/CITAS/
# BEWEN, 2026-08-07) taranmış görüntüden oluşuyor, OCR olmadan okunamıyor
# (bkz. kap_ipo.py modül üst notu). Bu alanlar için `ipo_broker_page.py`
# (halkarz.com, İKİNCİL kaynak) denenir; O DA bulamazsa (Kural 9) kullanıcı
# isteğiyle (2026-08-07, "N/A olacak değer varsa hiç gösterme, boşluk görmek
# istemiyorum") kartta o alan/bölüm TAMAMEN GİZLENİR -- placeholder/"-"
# GÖSTERİLMEZ.
_DATA_NOTES = (
    "Tahmini Dağıtım tablosu bir öngörü/tahmin DEĞİLDİR -- sadece \"bu kadar "
    "kişi başvurursa kişi başına kaç lot düşer\" sorusuna izahnamenin kendi "
    "rakamlarıyla, eşit dağıtım varsayımıyla cevap veren varsayımsal bir senaryodur.",
)

# Başlıktan şirket adını çıkarmak için -- CANLI gözlemlenen konvansiyonlar
# (bkz. kap_ipo.py modül üst notu, "_is_izahname_part"teki AYNI örnekler):
# "... Paylarının Halka Arzına İlişkin ..." (Quick/Saat ve Saat) VEYA
# doğrudan "... Halka Arzına İlişkin ..." (A1 Capital/KARCL) VEYA "Halka Arz"
# kelimesi hiç GEÇMEYİP doğrudan "... SPK Onaylı İzahname" ile biten başlıklar
# (Halk Yatırım/VEYAS, 2026-08-07 canlı bulundu). Eşleşmezse (Kural 3: uydurma
# yok) başlığın TAMAMI ham haliyle kullanılır.
_COMPANY_NAME_RE = re.compile(r"^(.*?)\s+Paylar[ıi]n[ıi]n\s+Halka\s+Arz", re.IGNORECASE)
_COMPANY_NAME_FALLBACK_RE = re.compile(r"^(.*?)\s+Halka\s+Arz", re.IGNORECASE)
_COMPANY_NAME_SPK_ONAYLI_RE = re.compile(r"^(.*?)\s+SPK\s+(Onaylı|Tarafından\s+Onaylanan)\s+İzahname", re.IGNORECASE)

# CANLI GÖZLEMLENDİ (2026-08-07, Bewen/Kapeks örnekleri): bazı başlıklarda
# yukarıdaki desenlerden HEMEN önce Türkçe iyelik eki ("A.Ş.'nin SPK Onaylı
# İzahnamesi hk") geliyor -- yakalanan grup "A.Ş.'nin" ile bitip şirket adını
# BOZUYORDU. Sadece bu son eki temizler, başka hiçbir kısaltma DOKUNULMAZ.
_TRAILING_POSSESSIVE_SUFFIX_RE = re.compile(r"'(nin|nın|nun|nün|un|ün)$", re.IGNORECASE)


def _derive_company_name(title: str) -> str:
    match = _COMPANY_NAME_RE.search(title) or _COMPANY_NAME_FALLBACK_RE.search(title) or _COMPANY_NAME_SPK_ONAYLI_RE.search(title)
    name = match.group(1).strip() if match else title.strip()
    return _TRAILING_POSSESSIVE_SUFFIX_RE.sub("", name).strip()


def _turkish_date_label(d: date) -> str:
    return f"{d.day:02d} {_AY_ADLARI_TR[d.month]} {d.year}"


def _allocation_rows(assessment: IpoAssessment) -> list[dict]:
    rows = [
        ("Yurt İçi Bireysel", assessment.allocation_retail_pct, assessment.allocation_retail_lot_count, "retail"),
        (
            "Yurt İçi Kurumsal",
            assessment.allocation_domestic_institutional_pct,
            assessment.allocation_domestic_institutional_lot_count,
            "domestic",
        ),
        (
            "Yurt Dışı Kurumsal",
            assessment.allocation_foreign_institutional_pct,
            assessment.allocation_foreign_institutional_lot_count,
            "foreign",
        ),
        (
            "Yüksek Başvurulu Yatırımcı",
            assessment.allocation_high_demand_pct,
            assessment.allocation_high_demand_lot_count,
            "high_demand",
        ),
        ("Diğer", assessment.allocation_other_pct, assessment.allocation_other_lot_count, "other"),
    ]
    return [
        {
            "label": label,
            "pct_display": format_percent_tr(pct, decimals=1),
            "pct_raw": float(pct) if pct is not None else 0.0,
            "lot_display": format_number_tr(lot, decimals=0) if lot is not None else None,
            "class": cls,
        }
        for label, pct, lot, cls in rows
        if pct is not None and pct > 0
    ]


def _estimated_distribution_rows(distribution: tuple[tuple[int, object, object], ...] | None) -> list[dict]:
    """`assessment.estimated_retail_distribution` VEYA (izahname okunamadığında)
    `supplementary.estimated_retail_distribution` -- İKİSİ DE AYNI şekilde
    (`ipo_assessment.estimate_retail_distribution()`ın döndürdüğü tuple),
    bu yüzden TEK bir formatlayıcı yeterli (2026-08-07, üçüncü tur)."""
    if not distribution:
        return []
    return [
        {
            "participants_display": format_number_tr(participants, decimals=0),
            "lot_display": format_number_tr(lot, decimals=0),
            "tl_display": f"{format_number_tr(tl, decimals=0)} TL",
        }
        for participants, lot, tl in distribution
    ]


def _use_of_proceeds_rows(assessment: IpoAssessment) -> list[dict]:
    if not assessment.top_use_of_proceeds:
        return []
    return [
        {"label": label, "pct_display": format_percent_tr(pct, decimals=1), "pct_raw": float(pct)}
        for label, pct in assessment.top_use_of_proceeds
    ]


def _dilution_row(label: str, before, after, decimals: int) -> dict | None:
    """`before`/`after` İKİSİ DE None ise satır TAMAMEN atlanır (kullanıcı
    isteği, 2026-08-07: "N/A olacak değer varsa hiç gösterme") -- bu SPK
    standardı tabloyu içermeyen bazı izahnamelerde (örn. Çitlekçi, "Sulanma
    Etkisi Analizi" başlığı hiç geçmiyor) tüm satırların boş "-/-" görünmesini
    önler."""
    if before is None and after is None:
        return None
    return {
        "label": label,
        "before_display": format_number_tr(before, decimals=decimals) if before is not None else "-",
        "after_display": format_number_tr(after, decimals=decimals) if after is not None else "-",
    }


def _use_of_proceeds_range_lines(use_of_proceeds_range: dict[str, str] | None) -> list[str] | None:
    """Ek-5/Ek-7 (kesin %) bulunamadığında ana izahnamenin 28.2 bölümünden
    gelen ARALIK formatlı fallback -- bar-fill grafiği YOK (aralık tek
    noktaya indirgenemez), `allocation_fallback_lines` ile AYNI düz metin
    satır deseni kullanılır (Faz 20.5)."""
    if not use_of_proceeds_range:
        return None
    return [f"{label}: {pct_range}" for label, pct_range in use_of_proceeds_range.items()]


def _operational_financial_rows(
    price_report: PriceReportFinancials | None,
    assessment: IpoAssessment,
    supplementary: SupplementaryIpoInfo | None = None,
) -> list[dict]:
    """"Operasyonel ve Finansal Veriler" bölümü -- Faz 20.5 (2026-08-07
    devamı). BİLİNÇLİ OLARAK SADECE Fiyat Tespit Raporu'ndan gelen
    STANDART finansal büyüklükler (Hasılat/Brüt Kâr/Toplam Varlıklar/
    Özkaynaklar) -- nüfus/aktif tüketici sayısı gibi SEKTÖRE ÖZGÜ
    "operasyonel" kalemler burada YOK (Kural 3, bkz. ipo_price_report.py
    modül üst notu). Her satır kendi verisi yoksa ATLANIR.

    2026-08-07 (otuz birinci tur): izahname/Fiyat Tespit Raporu'ndan TEK BİR
    satır bile üretilemezse (`price_report` `None` OLABİLİR YA DA -- CANLI
    KPEKS'te bulunan hata -- ayrıştırma denenip HİÇBİR alanı dolduramamış
    bir `PriceReportFinancials` nesnesi de OLABİLİR, `is None` kontrolü
    İKİNCİYİ YAKALAMIYORDU) halkarz.com'un "Finansal Tablo" widget'ından
    (Hasılat/Brüt Kâr, SADECE en son TAM YIL, YoY YOK -- bu widget'ta
    karşılaştırma dönemi bulunmuyor) DÜZ METİN yedeğine düşülür --
    `is_fallback=True` ile şablonda "kaynak: halkarz.com" işaretlenir
    (Kural 1/2: bu bizim hesabımız değil, siteden OLDUĞU GİBİ alıntı)."""
    rows: list[dict] = []
    if price_report is not None:
        if price_report.revenue_full_year is not None:
            label = f"Hasılat ({price_report.full_year_label})" if price_report.full_year_label else "Hasılat"
            rows.append({"label": label, "value_display": format_currency_short(price_report.revenue_full_year * 1000), "yoy_display": None, "yoy_class": "neutral"})
        if price_report.revenue_latest_interim is not None:
            label = f"Ciro ({price_report.period_label})" if price_report.period_label else "Ciro"
            yoy = assessment.revenue_yoy_growth_pct
            rows.append(
                {
                    "label": label,
                    "value_display": format_currency_short(price_report.revenue_latest_interim * 1000),
                    "yoy_display": format_percent_tr(yoy, decimals=1) if yoy is not None else None,
                    "yoy_class": "positive" if (yoy is not None and yoy >= 0) else ("negative" if yoy is not None else "neutral"),
                }
            )
        if price_report.gross_profit_latest_interim is not None:
            label = f"Brüt Kâr ({price_report.period_label})" if price_report.period_label else "Brüt Kâr"
            yoy = assessment.gross_profit_yoy_growth_pct
            rows.append(
                {
                    "label": label,
                    "value_display": format_currency_short(price_report.gross_profit_latest_interim * 1000),
                    "yoy_display": format_percent_tr(yoy, decimals=1) if yoy is not None else None,
                    "yoy_class": "positive" if (yoy is not None and yoy >= 0) else ("negative" if yoy is not None else "neutral"),
                }
            )
        if price_report.total_assets is not None:
            label = f"Toplam Varlıklar ({price_report.period_label})" if price_report.period_label else "Toplam Varlıklar"
            rows.append({"label": label, "value_display": format_currency_short(price_report.total_assets * 1000), "yoy_display": None, "yoy_class": "neutral"})
        if price_report.total_equity is not None:
            label = f"Özkaynaklar ({price_report.period_label})" if price_report.period_label else "Özkaynaklar"
            rows.append({"label": label, "value_display": format_currency_short(price_report.total_equity * 1000), "yoy_display": None, "yoy_class": "neutral"})

    if rows or supplementary is None:
        return rows

    # Fiyat Tespit Raporu HİÇ bulunamadı VEYA bulundu ama TEK BİR alanı bile
    # ayrıştırılamadı (KPEKS gibi, taranmış PDF) -- halkarz.com'un
    # "Finansal Tablo" widget'ına düş.
    period = supplementary.financial_table_period_label
    if supplementary.financial_table_revenue_full_year_text:
        label = f"Hasılat ({period})" if period else "Hasılat"
        rows.append({"label": label, "value_display": supplementary.financial_table_revenue_full_year_text, "yoy_display": None, "yoy_class": "neutral", "is_fallback": True})
    if supplementary.financial_table_gross_profit_full_year_text:
        label = f"Brüt Kâr ({period})" if period else "Brüt Kâr"
        rows.append({"label": label, "value_display": supplementary.financial_table_gross_profit_full_year_text, "yoy_display": None, "yoy_class": "neutral", "is_fallback": True})
    return rows


def _highlight_rows(
    offering_size_display: str,
    total_lot_display: str | None,
    has_capital_split: bool,
    is_pure_capital_increase: bool,
    capital_increase_pct_display: str,
    partner_sale_pct_display: str,
    allocation_rows: list[dict],
    price_stabilization_period_display: str | None,
    price_stabilization_source_pct_display: str | None,
    price_report: PriceReportFinancials | None,
) -> list[str]:
    """"Öne Çıkan Noktalar" -- kullanıcının paylaştığı referans görselden
    YAPISAL olarak esinlenen bölüm, ama İÇERİK olarak referanstan TAMAMEN
    FARKLI bir ilkeyle üretilir: referans görseldeki "dikkat çekicidir",
    "önce kote olması gereken görünümünde" gibi cümleler BİRİNCİ ŞAHIS/
    ÖZNEL bir yatırım kanaati taşıyor -- bu, `build_ipo_analysis_text()`'in
    "birinci şahıs kanaat üretmez" ilkesiyle (K2: Al/Sat/Tut sinyali yok)
    DOĞRUDAN ÇELİŞİR. Burada üretilen HER cümle SADECE zaten kartta
    başka yerde gösterilen, zaten hesaplanmış rakamların NÖTR bir
    özetidir -- yeni bir sayı/yargı ÜRETİLMEZ (Kural 1)."""
    rows: list[str] = []

    if offering_size_display != "-":
        lot_part = f", toplam {total_lot_display} Lot" if total_lot_display else ""
        rows.append(f"Halka arz büyüklüğü {offering_size_display}{lot_part} olarak planlanıyor.")

    if has_capital_split:
        if is_pure_capital_increase:
            rows.append("Arzın tamamı sermaye artırımı — halka arz gelirinin tamamı doğrudan şirketin kasasına giriyor.")
        else:
            rows.append(
                f"Halka arz gelirinin {capital_increase_pct_display}'i sermaye artırımından (şirkete yeni kaynak), "
                f"{partner_sale_pct_display}'i ortak satışından oluşuyor."
            )

    retail_row = next((r for r in allocation_rows if r["class"] == "retail"), None)
    if retail_row is not None:
        rows.append(f"Bireysel yatırımcı tahsisatı {retail_row['pct_display']}.")

    if price_stabilization_period_display or price_stabilization_source_pct_display:
        parts = [p for p in (price_stabilization_period_display, price_stabilization_source_pct_display) if p]
        rows.append(f"Fiyat istikrarı: {', '.join(parts)}.")

    if price_report is not None and price_report.revenue_full_year is not None and price_report.full_year_label:
        rows.append(f"{price_report.full_year_label} yılı hasılatı {format_currency_short(price_report.revenue_full_year * 1000)}.")

    return rows


def build_ipo_card_context(
    disclosure: IzahnameDisclosure,
    facts: IpoFacts,
    assessment: IpoAssessment,
    now: datetime | None = None,
    supplementary: SupplementaryIpoInfo | None = None,
    price_report: PriceReportFinancials | None = None,
) -> dict:
    now = now or datetime.now()
    company_name = _derive_company_name(disclosure.summary)
    primary_ticker = disclosure.target_tickers[0] if disclosure.target_tickers else "-"
    other_tickers = disclosure.target_tickers[1:]

    allocation_rows = _allocation_rows(assessment)
    use_of_proceeds_rows = _use_of_proceeds_rows(assessment)
    estimated_distribution_rows = _estimated_distribution_rows(assessment.estimated_retail_distribution)

    # --- Sermaye Artırımı vs Ortak Satışı -- izahnameden gelen None ise
    # (VEYAS gibi) halkarz.com'un "Halka Arz Şekli" bloğundan türetilen
    # yüzdeye düşülür (2026-08-07, üçüncü tur). ---
    if assessment.capital_increase_share_pct is not None:
        capital_pct = assessment.capital_increase_share_pct
        partner_pct = assessment.partner_sale_share_pct
        is_pure_capital_increase = assessment.is_pure_capital_increase
        capital_split_is_fallback = False
    elif supplementary and supplementary.capital_increase_pct_fallback is not None:
        capital_pct = supplementary.capital_increase_pct_fallback
        partner_pct = supplementary.partner_sale_pct_fallback
        is_pure_capital_increase = supplementary.is_pure_capital_increase_fallback
        capital_split_is_fallback = True
    else:
        capital_pct = None
        partner_pct = None
        is_pure_capital_increase = False
        capital_split_is_fallback = False
    has_capital_split = capital_pct is not None and partner_pct is not None

    # --- İkincil kaynak (halkarz.com) alanları -- HER biri ayrı ayrı None
    # olabilir (Kural 9), kullanıcı isteğiyle (2026-08-07) None olan alan
    # şablonda TAMAMEN GİZLENİR, placeholder GÖSTERİLMEZ.
    demand_period_display = supplementary.demand_period_display if supplementary else None
    demand_period_hours = supplementary.demand_period_hours if supplementary else None
    participation_compliant = supplementary.participation_index_compliant if supplementary else None
    participation_index_name = supplementary.participation_index_name if supplementary else None
    price_stabilization_note = supplementary.price_stabilization_note if supplementary else None
    sales_method_note = supplementary.sales_method_note if supplementary else None
    # --- 2026-08-07 (otuz birinci tur, kullanıcı referans görseli: VEYAS
    # infografiği) -- halkarz.com'da ZATEN duran ama önceki turlarda hiç
    # çekilmeyen alanlar: İskonto/Halka Açıklık/Pazar/Ek Pay. ---
    discount_pct_text = supplementary.discount_pct_text if supplementary else None
    free_float_pct_text = supplementary.free_float_pct_text if supplementary else None
    market_tier = supplementary.market_tier if supplementary else None
    additional_lot_text = supplementary.additional_lot_text if supplementary else None
    has_quick_info = any(
        [
            demand_period_display,
            participation_compliant is not None,
            price_stabilization_note,
            sales_method_note,
            discount_pct_text,
            free_float_pct_text,
        ]
    )

    # --- İzahname OCU'suz kalıp facts.offering_price/total_lot None
    # kaldığında (VEYAS gibi) halkarz.com'un DÜZ METİN rakamlarını FALLBACK
    # olarak kullan (2026-08-07, kullanıcı raporu: "VEYAS'ta hiçbir bilgi
    # çıkmadı"). Bu ASLA `facts`/`assessment`'ın gerçek bir Decimal
    # rakamının ÜZERİNE YAZMAZ -- SADECE o rakam None iken devreye girer,
    # ve kartta "kaynak: halkarz.com" ile AÇIKÇA işaretlenir (Kural 3)."""
    if facts.offering_price is not None:
        offering_price_display = f"{format_number_tr(facts.offering_price, decimals=2)} TL"
        offering_price_is_fallback = False
    elif supplementary and supplementary.offering_price_text:
        offering_price_display = supplementary.offering_price_text
        offering_price_is_fallback = True
    else:
        offering_price_display = "-"
        offering_price_is_fallback = False

    if assessment.total_lot_count is not None:
        total_lot_display = format_number_tr(assessment.total_lot_count, decimals=0)
        total_lot_is_fallback = False
    elif supplementary and supplementary.total_lot_text:
        total_lot_display = supplementary.total_lot_text
        total_lot_is_fallback = True
    else:
        total_lot_display = None
        total_lot_is_fallback = False

    if facts.offering_size is not None:
        offering_size_display = format_currency_short(facts.offering_size)
        offering_size_is_fallback = False
    elif supplementary and supplementary.offering_size_text:
        offering_size_display = supplementary.offering_size_text
        offering_size_is_fallback = True
    else:
        offering_size_display = "-"
        offering_size_is_fallback = False

    allocation_fallback_lines = supplementary.allocation_lines if (supplementary and not allocation_rows) else None
    # Tahmini Dağıtım fallback'i artık AYNI yapılandırılmış satır biçimini
    # kullanıyor (`ipo_assessment.estimate_retail_distribution()` ile
    # üretildiği için, bkz. ipo_broker_page.py) -- ayrı bir "ham metin"
    # bloğu YOK, primary/fallback AYNI tabloyla gösterilir (2026-08-07,
    # üçüncü tur: tutarlı/yuvarlak katılımcı senaryoları isteği).
    estimated_distribution_is_fallback = not estimated_distribution_rows and bool(
        supplementary and supplementary.estimated_retail_distribution
    )
    if estimated_distribution_is_fallback:
        estimated_distribution_rows = _estimated_distribution_rows(supplementary.estimated_retail_distribution)

    dilution_rows = [
        row
        for row in (
            _dilution_row("Özkaynaklar", facts.equity_before, facts.equity_after, 0),
            _dilution_row("Ödenmiş Sermaye", facts.paid_capital_before, facts.paid_capital_after, 0),
            _dilution_row("Pay Başına Defter Değeri", facts.book_value_per_share_before, facts.book_value_per_share_after, 4),
        )
        if row is not None
    ]
    dilution_mini_stats = [
        stat
        for stat in (
            {"label": "Mevcut Ortaklar Sulanma", "value": format_percent_tr(facts.dilution_existing_pct, decimals=2)}
            if facts.dilution_existing_pct is not None
            else None,
            {"label": "Yeni Ortaklar Sulanma", "value": format_percent_tr(facts.dilution_new_pct, decimals=2)}
            if facts.dilution_new_pct is not None
            else None,
            {"label": "Fiyat / Defter Değeri", "value": f"{format_number_tr(assessment.price_to_book_before, decimals=2)}x"}
            if assessment.price_to_book_before is not None
            else None,
            {"label": "Özkaynak Büyümesi", "value": format_percent_tr(assessment.equity_growth_pct, decimals=1)}
            if assessment.equity_growth_pct is not None
            else None,
        )
        if stat is not None
    ]

    # --- Fiyat İstikrarı (izahname 26.5, YAPISAL/PRİMER kaynak) -- Faz 20.5.
    # `price_stabilization_note` (halkarz.com, İKİNCİL, YUKARIDA zaten
    # tanımlı) İLE ÇAKIŞMAZ -- ikisi de bağımsız birer quick-tile olarak
    # gösterilir, biri diğerinin YERİNE geçmez (izahname okunabiliyorsa
    # genelde SADECE bu yapısal alan dolu olur, halkarz.com scanned/OCR'siz
    # izahnamelerde -- VEYAS gibi -- devreye girer, ikisinin AYNI ANDA dolu
    # olması NADİRDİR).
    price_stabilization_source_pct_display = (
        f"kaynağın %{format_percent_tr(facts.price_stabilization_source_pct, decimals=0).lstrip('%')}'i"
        if facts.price_stabilization_source_pct is not None
        else None
    )
    has_quick_info = has_quick_info or bool(
        facts.price_stabilization_period_display or price_stabilization_source_pct_display or facts.issuer_lockup_period_display
    )

    use_of_proceeds_range_lines = _use_of_proceeds_range_lines(facts.use_of_proceeds_range) if not use_of_proceeds_rows else None
    # 3. kademe yedek: Ek-5/Ek-7 (kesin %) YOK, ana izahnamenin 28.2 ARALIK
    # bölümü de OKUNAMADIYSA (izahname taranmış -- VEYAS gibi) halkarz.com'un
    # "Fonun Kullanım Yeri" serbest metnine düşülür (2026-08-07, otuz
    # birinci tur).
    use_of_proceeds_note = (
        supplementary.use_of_proceeds_note if (supplementary and not use_of_proceeds_rows and not use_of_proceeds_range_lines) else None
    )

    operational_financial_rows = _operational_financial_rows(price_report, assessment, supplementary)

    highlight_rows = _highlight_rows(
        offering_size_display=offering_size_display,
        total_lot_display=total_lot_display,
        has_capital_split=has_capital_split,
        is_pure_capital_increase=is_pure_capital_increase,
        capital_increase_pct_display=format_percent_tr(capital_pct, decimals=1),
        partner_sale_pct_display=format_percent_tr(partner_pct, decimals=1),
        allocation_rows=allocation_rows,
        price_stabilization_period_display=facts.price_stabilization_period_display,
        price_stabilization_source_pct_display=price_stabilization_source_pct_display,
        price_report=price_report,
    )

    return {
        "company_name": company_name,
        "primary_ticker": primary_ticker,
        "other_tickers_display": ", ".join(other_tickers) if other_tickers else None,
        # CANLI HATA (bkz. PROJE_HAFIZASI/06_BILINEN_SORUNLAR.md #16, AYNI
        # sınıf): Python'ın .title()/.lower()'ı "İ" harfini "i" + BİRLEŞTİRİCİ
        # NOKTA (U+0307) olarak bozuyor ("A1 CAPİTAL" -> "A1 Capi̇tal"). Unvan
        # KAP'ın kendi "kapTitle" alanından (`kap.Disclosure.filer_name`)
        # geliyor, zaten resmi/okunabilir -- BURADA hiç case dönüşümü
        # YAPILMAZ, olduğu gibi gösterilir.
        "underwriter_name": disclosure.underwriter_name,
        "market_tier": market_tier,
        "publish_date_label": _turkish_date_label(disclosure.publish_date),
        "report_timestamp": now.strftime("%d.%m.%Y %H:%M"),
        # --- Anahtar rakamlar --- ("_is_fallback" True ise halkarz.com'dan
        # geliyor, izahnameden DEĞİL -- şablon "kaynak: halkarz.com" gösterir
        "offering_price_display": offering_price_display,
        "offering_price_is_fallback": offering_price_is_fallback,
        "offering_size_display": offering_size_display,
        "offering_size_is_fallback": offering_size_is_fallback,
        "net_proceeds_display": format_currency_short(facts.net_offering_proceeds),
        "offering_cost_display": format_currency_short(facts.estimated_offering_cost),
        "total_lot_display": total_lot_display,
        "total_lot_is_fallback": total_lot_is_fallback,
        # --- Ek Pay (greenshoe/ek satış, halkarz.com) -- izahnamedeki
        # `total_lot_display` BİLİNÇLİ OLARAK bunu HARİÇ tutar (bkz.
        # ipo_broker_page.py `_strip_lot_suffix` üst notu), burada AYRI ve
        # AÇIKÇA etiketli bir ek bilgi olarak gösterilir. ---
        "additional_lot_display": additional_lot_text,
        # --- Talep toplama / Katılım Endeksi / satış yöntemi / İskonto /
        # Halka Açıklık (İKİNCİL kaynak: halkarz.com -- bkz. ipo_broker_page.py).
        # Her biri None olabilir, şablon bunları TEK TEK kontrol edip yoksa
        # hiç göstermez. ---
        "has_quick_info": has_quick_info,
        "demand_period_display": demand_period_display,
        "demand_period_hours": demand_period_hours,
        "participation_compliant": participation_compliant,
        "participation_index_name": participation_index_name,
        "price_stabilization_note": price_stabilization_note,
        "sales_method_note": sales_method_note,
        "discount_pct_text": discount_pct_text,
        "free_float_pct_text": free_float_pct_text,
        # --- Fiyat İstikrarı Detayı (izahname 26.5) + Taahhüt (27.3) --
        # PRİMER kaynak, halkarz.com'dan (yukarıdaki price_stabilization_note)
        # BAĞIMSIZ ayrı tile'lar (Faz 20.5). ---
        "price_stabilization_period_display": facts.price_stabilization_period_display,
        "price_stabilization_source_pct_display": price_stabilization_source_pct_display,
        "issuer_lockup_period_display": facts.issuer_lockup_period_display,
        # --- Sermaye artırımı vs ortak satışı ---
        "has_capital_split": has_capital_split,
        "capital_increase_pct_display": format_percent_tr(capital_pct, decimals=1),
        "partner_sale_pct_display": format_percent_tr(partner_pct, decimals=1),
        "capital_increase_pct_raw": float(capital_pct) if capital_pct is not None else 0.0,
        "is_pure_capital_increase": is_pure_capital_increase,
        "capital_split_is_fallback": capital_split_is_fallback,
        # --- Halka Arz Öncesi/Sonrası Karşılaştırma (sulanma etkisi) ---
        # Kural 3/kullanıcı isteği: hem satır hem mini-istatistik seviyesinde
        # None olan alan TAMAMEN GİZLENİR (bkz. _dilution_row()); ikisi de
        # boşsa (örn. Çitlekçi -- izahnamede "Sulanma Etkisi Analizi" başlığı
        # hiç geçmiyor) bölümün TAMAMI gizlenir.
        "dilution_rows": dilution_rows,
        "dilution_mini_stats": dilution_mini_stats,
        "is_dilution_section_empty": not dilution_rows and not dilution_mini_stats,
        # --- Tahsisat / Fon Kullanım Yeri ---
        "allocation_rows": allocation_rows,
        "is_allocation_empty": not allocation_rows,
        "allocation_fallback_lines": allocation_fallback_lines,
        "use_of_proceeds_rows": use_of_proceeds_rows,
        "is_use_of_proceeds_empty": not use_of_proceeds_rows,
        # 28.2 (ana izahname, ARALIK formatlı) fallback -- SADECE Ek-5/Ek-7
        # (yukarıdaki use_of_proceeds_rows) boşsa devreye girer (Faz 20.5).
        "use_of_proceeds_range_lines": use_of_proceeds_range_lines,
        # 3. kademe yedek (halkarz.com serbest metin) -- SADECE ikisi de
        # boşsa devreye girer (2026-08-07, otuz birinci tur).
        "use_of_proceeds_note": use_of_proceeds_note,
        # --- Tahmini Dağıtım (yurt içi bireysel, eşit dağıtım senaryosu) ---
        "estimated_distribution_rows": estimated_distribution_rows,
        "estimated_distribution_is_fallback": estimated_distribution_is_fallback,
        "is_estimated_distribution_empty": not estimated_distribution_rows,
        # --- Öne Çıkan Noktalar (Faz 20.5) -- SADECE zaten kartta gösterilen
        # rakamların nötr cümle özeti, yeni bir sayı/yargı ÜRETİLMEZ. ---
        "highlight_rows": highlight_rows,
        # --- Operasyonel ve Finansal Veriler (Faz 20.5, Fiyat Tespit Raporu) ---
        "operational_financial_rows": operational_financial_rows,
        "is_operational_financial_empty": not operational_financial_rows,
        "data_notes": _DATA_NOTES,
        "has_supplementary_source": supplementary is not None,
        "disclaimer": _DISCLAIMER,
    }


def build_ipo_share_text(context: dict) -> str:
    """Telegram'dan doğrudan kopyala-yapıştır edilebilecek, X/Twitter'a
    hazır özet metin -- `calendar_card.build_calendar_share_text()` ile
    AYNI ilke (kart context'i ZATEN Türkçe biçimlendirilmiş, burada SADECE
    string birleştirme yapılır, yeni bir sayı ÜRETİLMEZ)."""
    lines = [
        f"📋 {context['company_name']} ({context['primary_ticker']}) Halka Arz İnceleme",
        "",
    ]
    if context["demand_period_display"]:
        hours = f" ({context['demand_period_hours']})" if context["demand_period_hours"] else ""
        lines.append(f"🗓️ Talep Toplama: {context['demand_period_display']}{hours}")
    lines.append(f"💰 Halka Arz Fiyatı: {context['offering_price_display']}")
    ek_pay = f" (+{context['additional_lot_display']} Lot ek satış)" if context.get("additional_lot_display") else ""
    lines.append(f"📦 Halka Arz Büyüklüğü: {context['offering_size_display']} (Toplam {context['total_lot_display'] or '-'} Lot{ek_pay})")
    lines.append(f"🏦 Net Halka Arz Geliri: {context['net_proceeds_display']}")
    if context.get("discount_pct_text") or context.get("free_float_pct_text"):
        parcalar = [p for p in (
            f"İskonto {context['discount_pct_text']}" if context.get("discount_pct_text") else None,
            f"Halka Açıklık {context['free_float_pct_text']}" if context.get("free_float_pct_text") else None,
        ) if p]
        lines.append(f"📐 {' · '.join(parcalar)}")
    if context["participation_compliant"] is not None:
        durum = "Uygun" if context["participation_compliant"] else "Uygun Değil"
        endeks = f" ({context['participation_index_name']})" if context["participation_index_name"] else ""
        lines.append(f"🕌 Katılım Endeksi: {durum}{endeks}")
    lines.append(f"🏢 Konsorsiyum Lideri / Aracı Kurum: {context['underwriter_name']}")
    if context["has_capital_split"]:
        lines.append(
            f"🏗️ Sermaye Artırımı / Ortak Satışı: {context['capital_increase_pct_display']} / {context['partner_sale_pct_display']}"
        )
    if not context["is_allocation_empty"]:
        lines.append("")
        lines.append("📊 Dağıtım Yapısı:")
        lines.extend(
            f"  • {row['label']}: {row['pct_display']}" + (f" ({row['lot_display']} Lot)" if row["lot_display"] else "")
            for row in context["allocation_rows"]
        )
    if not context["is_estimated_distribution_empty"]:
        lines.append("")
        lines.append("🎲 Tahmini Dağıtım (Yurt İçi Bireysel, eşit dağıtım varsayımıyla):")
        lines.extend(
            f"  • {row['participants_display']} kişi katılırsa → kişi başı {row['lot_display']} Lot ({row['tl_display']})"
            for row in context["estimated_distribution_rows"]
        )
    if not context["is_use_of_proceeds_empty"]:
        lines.append("")
        lines.append("🎯 Fon Kullanım Yeri (öne çıkanlar):")
        lines.extend(f"  • {row['label']}: {row['pct_display']}" for row in context["use_of_proceeds_rows"])
    elif context.get("use_of_proceeds_range_lines"):
        lines.append("")
        lines.append("🎯 Halka Arz Gelirinin Kullanımı:")
        lines.extend(f"  • {line}" for line in context["use_of_proceeds_range_lines"])
    elif context.get("use_of_proceeds_note"):
        lines.append("")
        lines.append(f"🎯 Halka Arz Gelirinin Kullanımı: {context['use_of_proceeds_note']}")
    lines.append("")
    lines.append(f"📅 İzahname Onay/Yayın Tarihi: {context['publish_date_label']}")
    lines.append("")
    lines.append(context["disclaimer"])
    lines.append("@QuaxisLabs · Bilanço Radar")
    return "\n".join(lines)


def build_ipo_analysis_text(context: dict) -> str:
    """Paragraf biçiminde, DAHA UZUN bir "inceleme" metni üretir (kullanıcının
    paylaştığı örnek gibi: birkaç paragraflık, sosyal medyada paylaşılabilir
    bir anlatı). `build_ipo_share_text()`ten FARKI: burası sadece rakam
    listelemez, rakamları CÜMLELER içinde bağlar.

    ⚠️ BİLİNÇLİ SINIR: kullanıcının paylaştığı örnek metin ("ben bu iskontoyu
    inandırıcı bulmadım", "katılıp katılmama konusunda kararsızım" gibi)
    BİRİNCİ ŞAHIS, KİŞİSEL bir yatırım kanaati taşıyor -- bu metin öyle bir
    kanaat ÜRETMEZ (kullanıcının gerçek görüşüymüş gibi görünecek bir metni
    otomatik uydurmak yanıltıcı olur). Bunun yerine SADECE izahnamenin/
    hesaplanmış rakamların NÖTR bir anlatısını verir; nihai yorum/kanaat
    kullanıcıya bırakılır."""
    company = context["company_name"]
    ticker = context["primary_ticker"]

    paragraphs: list[str] = []

    intro = f"#{ticker} İnceleme\n\nSPK onaylı izahnamesine göre {company} halka arz sürecine hazırlanıyor."
    if context["demand_period_display"]:
        hours = f", {context['demand_period_hours']} saatleri arasında" if context["demand_period_hours"] else ""
        intro += f" Talep toplama {context['demand_period_display']} tarihlerinde{hours} gerçekleştirilecek."
    paragraphs.append(intro)

    # İzahnamenin PDF'i okunamadığında (bkz. §B31, VEYAS gibi taranmış/OCR'siz
    # örnekler) fiyat/büyüklük/lot ÜÇÜ DE None kalabilir -- bu durumda "- Lot'un
    # - fiyatla" gibi anlamsız bir cümle KURULMAZ, paragraf tamamen atlanır.
    if context["total_lot_display"] or context["offering_price_display"] != "-" or context["offering_size_display"] != "-":
        size_paragraph = (
            f"Halka arz {context['total_lot_display'] or '-'} Lot'un {context['offering_price_display']} fiyatla "
            f"satışıyla gerçekleşecek; arz büyüklüğü {context['offering_size_display']}."
        )
        if context["has_capital_split"]:
            if context["is_pure_capital_increase"]:
                size_paragraph += " Arzın tamamı sermaye artırımı -- yani halka arz gelirinin tamamı doğrudan şirketin kasasına giriyor."
            else:
                size_paragraph += (
                    f" Arzın {context['capital_increase_pct_display']}'i sermaye artırımı (şirkete giriyor), "
                    f"{context['partner_sale_pct_display']}'i ise mevcut ortak satışı."
                )
        paragraphs.append(size_paragraph)

    if not context["is_allocation_empty"]:
        allocation_text = "; ".join(
            f"{row['label']} %{row['pct_display'].lstrip('%')}" + (f" ({row['lot_display']} Lot)" if row["lot_display"] else "")
            for row in context["allocation_rows"]
        )
        paragraphs.append(f"Tahsisat yapısı şöyle: {allocation_text}.")

    if not context["is_use_of_proceeds_empty"]:
        use_text = "; ".join(f"{row['label']} %{row['pct_display'].lstrip('%')}" for row in context["use_of_proceeds_rows"])
        paragraphs.append(f"İzahnamenin Fon Kullanım Yeri Raporu'na göre öne çıkan kullanım alanları: {use_text}.")

    if context["sales_method_note"]:
        sales_method = context["sales_method_note"].rstrip(".; ")
        sentence = f"Satış yöntemi: {sales_method}."
        if context["price_stabilization_note"]:
            price_stabilization = context["price_stabilization_note"].rstrip(".; ")
            sentence += f" Fiyat istikrarı: {price_stabilization}."
        paragraphs.append(sentence)

    if context["participation_compliant"] is not None:
        endeks = f" ({context['participation_index_name']})" if context["participation_index_name"] else ""
        fiil = "uygun görülüyor" if context["participation_compliant"] else "uygun görülmüyor"
        paragraphs.append(f"Katılım Endeksi{endeks} kriterlerine göre bu halka arz {fiil}.")

    if not context["is_estimated_distribution_empty"]:
        sample = context["estimated_distribution_rows"][len(context["estimated_distribution_rows"]) // 2]
        paragraphs.append(
            "Yurt içi bireysel tarafta eşit dağıtım uygulanacak; örneğin "
            f"{sample['participants_display']} kişi başvurursa kişi başına yaklaşık {sample['lot_display']} Lot "
            f"({sample['tl_display']}) düşüyor (varsayımsal senaryo, gerçek başvuru sayısına göre değişir)."
        )

    paragraphs.append(context["disclaimer"])
    paragraphs.append("@QuaxisLabs · Bilanço Radar")
    return "\n\n".join(paragraphs)
