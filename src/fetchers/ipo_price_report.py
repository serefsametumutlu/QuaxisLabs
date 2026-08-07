"""Halka arz "Fiyat Tespit Raporu"ndan (bağımsız değerleme kuruluşunun
hazırladığı, izahnameye ek rapor) DAR kapsamlı finansal büyüklük çekimi --
Faz 20.5 (2026-08-07 devamı).

── NEDEN AYRI BİR MODÜL (kap_ipo.py'ye EKLENMEDİ) ──
`kap_ipo.py`'nin ayrıştırdığı "Sulanma Etkisi Analizi"/26.5/27.3/28.2
bölümleri SPK'nın Pay Tebliği'yle ZORUNLU KILINAN, madde numarası TÜM
izahnamelerde AYNI olan standart metinlerdir -- yüksek güvenilirlik.
Fiyat Tespit Raporu ise HER halka arz için AYRI bir değerleme kuruluşu
tarafından hazırlanır; içindekiler yapısı benzer olsa da (bkz. VEYAS
örneği: "4. Finansal Veriler" -> "4.1. Bilanço"/"4.2. Gelir Tablosu")
tablo biçimlendirmesi hazırlayana göre DEĞİŞEBİLİR -- bu modül BİLİNÇLİ
olarak DAR tutulur: SADECE net etiket eşleşmesi olan 4 kalem (Toplam
Varlıklar, Özkaynaklar, Hasılat, Brüt Kâr) + kolon sayısı TAM
beklenenle (Bilanço: 4, Gelir Tablosu: 5) eşleşmiyorsa None (Kural 3).

── KEŞİF ──
Bu belge, ana izahnameyle AYNI aracı kurumun KAP profilinde, GENELLİKLE
AYNI "İzahname (SPK Tarafından Onaylanan)" kategorisi altında, başlığında
"Fiyat Tespit Raporu" geçen AYRI bir bildirim olarak yayınlanır (bkz.
`kap_ipo.py` modül üst notu -- KARCL örneğinde "...+ fiyat tespit raporu +
halka arz sonuçları dosya indeksleriyle GERÇEKTEN bulundu" ifadesiyle
CANLI doğrulanmıştı, o turda ayrıştırılmamıştı).

── KURAL 3 DOĞRULAMA ──
`scripts/explore_ipo_price_report.py` ile VEYAS'ın (Türker Vangölü Enerji)
zaten indirilmiş `data/exploration/veyas_fiyat_tespit_raporu_full.txt`
metni ayrıştırılıp kullanıcının paylaştığı REFERANS görseldeki gerçek
VEYAS rakamlarıyla (Hasılat 26.652.218 bin TL, 2026/3A Ciro 5.775.822 bin
TL, Brüt Kâr 2.469.357 bin TL, Ciro artışı %13,6, Brüt kâr artışı %113,5,
Toplam varlıklar 30.121.124 bin TL, Özkaynaklar 15.590.464 bin TL) rakam
rakam BİREBİR eşleşti (bkz. explore scripti çıktısı).

── OPERASYONEL VERİLER BİLİNÇLİ OLARAK KAPSAM DIŞI ──
Nüfus/aktif tüketici sayısı gibi kalemler ("2. Şirket ve Faaliyetleri
Hakkında Bilgiler"/"3. Sektörel Bilgiler" bölümlerinde) SEKTÖRE ÖZGÜ
serbest metindir -- elektrik dağıtım şirketi için "tüketici sayısı"
anlamlıyken bir e-ticaret şirketi için "aktif kullanıcı" olabilir. Standart
bir başlık/etiket YOK, otomatik+genel bir eşleme YANLIŞ rakam riski taşır
-- bu modül bunu ÜRETMEZ (Kural 3).
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from io import BytesIO

import pdfplumber

from src.fetchers import kap
from src.fetchers.kap_ipo import IzahnameDisclosure

logger = logging.getLogger(__name__)

# 🚨 CANLI HATA + DÜZELTME (2026-08-07, otuz birinci tur, kullanıcı raporu:
# "KPEKS ve VEYAS'ta hâlâ eksik geliyor"): find_price_report_disclosure_index()
# şimdiye kadar bildirimi SADECE _IZAHNAME_CATEGORY içinde arıyordu -- ama
# KAP, Fiyat Tespit Raporu'nu KENDİ AYRI kategorisinde ("Fiyat Tespit Raporu")
# yayınlıyor, izahname kategorisinin İÇİNDE DEĞİL. CANLI 4/4 örnekte doğrulandı
# (KPEKS/VEYAS/BEWEN/CITAS -- hepsinin "Fiyat Tespit Raporu" başlıklı bildirimi
# `d.category == "Fiyat Tespit Raporu"`, ASLA izahname kategorisinde değil).
# Sonuç: bu fonksiyon KURULUŞUNDAN BERİ hiçbir zaman gerçek bir sonuç
# DÖNDÜREMİYORDU -- daha önce VEYAS için yapılan "rakam rakam doğrulama"
# (bkz. modül üst notu) SADECE `extract_price_report_financials()`'ın kendi
# ayrıştırma mantığını, ELLE indirilmiş bir dosyayla test etmişti; bu keşif
# (discovery) fonksiyonu CANLI uçtan uca hiç doğrulanmamıştı. "Operasyonel ve
# Finansal Veriler" bölümünün kartlarda İSTİSNASIZ boş çıkmasının kök nedeni
# BUYDU.
_PRICE_REPORT_CATEGORY = "Fiyat Tespit Raporu"
_PRICE_REPORT_KEYWORD_RE = re.compile(r"fiyat tespit raporu", re.IGNORECASE)
_COURTESY_DELAY_SECONDS = 0.4
_DISCOVERY_DAYS = 60  # kap_ipo._find_use_of_proceeds_disclosure_index ile AYNI pencere (tek üye taraması, fetch_all_disclosures'ın 2000-satır sınırına TABİ DEĞİL)


class KapIpoPriceReportError(Exception):
    """Bu modül için taban hata sınıfı."""


def _to_decimal(text: str) -> Decimal | None:
    """`kap_ipo._to_decimal()` ile AYNI Türkçe sayı formatı -- tek kaynak
    yerine burada da tanımlanmasının nedeni, kap_ipo.py'nin KENDİ üst
    notunda açıklanan ilkenin AYNISI: bu modül kap_ipo'nun izahname
    ayrıştırma mantığına DEĞİL, farklı bir belgeye dayanıyor."""
    cleaned = text.strip().rstrip("%").strip()
    if not cleaned:
        return None
    try:
        return Decimal(cleaned.replace(".", "").replace(",", "."))
    except InvalidOperation:
        return None


def _pdf_bytes_to_text(pdf_bytes: bytes) -> str:
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


# --- Keşif (aracı kurumun profilinde "Fiyat Tespit Raporu" başlıklı bildirim) ------------------


def _resolve_underwriter_oid(exact_name: str) -> str | None:
    """`kap_ipo._resolve_underwriter_oid()` ile AYNI mantık -- Kural 9:
    bulunamazsa None, TÜM keşif ÇÖKMEZ."""
    try:
        results = kap.search_company_by_name(exact_name)
    except kap.KapError as exc:
        logger.warning("%s için KAP araması başarısız: %s", exact_name, exc)
        return None
    normalized_target = exact_name.strip().upper()
    for r in results:
        if r.name.strip().upper() == normalized_target:
            return r.member_oid
    return None


def find_price_report_disclosure_index(disclosure: IzahnameDisclosure) -> int | None:
    """Ana izahnameyle AYNI aracı kurumun profilinde, AYNI hedef ticker için
    başlığında "Fiyat Tespit Raporu" geçen bildirimi bulur. Bulunamazsa
    (Kural 9 -- bu YARDIMCI/İKİNCİL bir veri kaynağıdır) None döner."""
    oid = _resolve_underwriter_oid(disclosure.underwriter_name)
    if oid is None:
        return None
    try:
        disclosures = kap.fetch_disclosures_by_oid(oid, days=_DISCOVERY_DAYS)
    except kap.KapError as exc:
        logger.warning("%s için Fiyat Tespit Raporu taraması başarısız: %s", disclosure.underwriter_name, exc)
        return None

    primary_ticker = disclosure.target_tickers[0] if disclosure.target_tickers else ""
    for d in disclosures:
        related = {t.strip() for t in d.related_stocks.split(",") if t.strip()}
        if primary_ticker not in related:
            continue
        # Birincil eşleşme: KAP'ın kendi kategori adı (4/4 canlı örnekte
        # doğrulandı). Başlık regex'i İKİNCİL/yedek kontrol olarak kalır --
        # kategori adı ileride değişirse/farklı bir aracı kurum farklı
        # etiketlerse yine de yakalanabilsin diye (Kural 9 ruhu: tek bir
        # koşula aşırı güvenme).
        if d.category == _PRICE_REPORT_CATEGORY or _PRICE_REPORT_KEYWORD_RE.search(d.title):
            return d.disclosure_index
    return None


# --- PDF ayrıştırma (4.1 Bilanço + 4.2 Gelir Tablosu, SADECE 4 net kalem) ----------------------

_TR_NUM = r"-?\d{1,3}(?:\.\d{3})*(?:,\d+)?"
_DATE_TOKEN = r"(\d{2}\.\d{2}\.\d{4})"

# CANLI DOĞRULANDI (VEYAS Fiyat Tespit Raporu, satır 1489-1557/2067-2101):
# "Varlıklar 31.12.2023 31.12.2024 31.12.2025 31.03.2026" başlık satırı ile
# 4 dönemli Bilanço; "Toplam varlıklar"/"Özkaynaklar" etiketleri TEK satırda
# TAM 4 sayı taşıyor, satır bu 4 sayıdan SONRA biter (`$` ile sınırlanır --
# kolon sayısı beklenenden FAZLA/AZ ise regex hiç eşleşmez, Kural 3).
_BALANCE_HEADER_RE = re.compile(r"^Varlıklar\s+" + _DATE_TOKEN + r"\s+" + _DATE_TOKEN + r"\s+" + _DATE_TOKEN + r"\s+" + _DATE_TOKEN + r"\s*$", re.MULTILINE)
_TOTAL_ASSETS_RE = re.compile(r"^Toplam varlıklar\s+(" + _TR_NUM + r")\s+(" + _TR_NUM + r")\s+(" + _TR_NUM + r")\s+(" + _TR_NUM + r")\s*$", re.MULTILINE | re.IGNORECASE)
_TOTAL_EQUITY_RE = re.compile(r"^Özkaynaklar\s+(" + _TR_NUM + r")\s+(" + _TR_NUM + r")\s+(" + _TR_NUM + r")\s+(" + _TR_NUM + r")\s*$", re.MULTILINE | re.IGNORECASE)

# CANLI DOĞRULANDI (aynı belge, satır 2067-2101): Gelir Tablosu 5 dönemli
# ([1]=2 yıl önce TY, [2]=1 yıl önce TY, [3]=güncel TY, [4]=önceki yılın AYNI
# ara dönemi, [5]=güncel ara dönem) -- YoY büyüme için [4]/[5] karşılaştırılır.
_GROSS_PROFIT_LABEL = r"Brüt\s+[Kk](?:ar|âr)"
_REVENUE_ROW_RE = re.compile(r"^Hasılat\s+(" + _TR_NUM + r")\s+(" + _TR_NUM + r")\s+(" + _TR_NUM + r")\s+(" + _TR_NUM + r")\s+(" + _TR_NUM + r")\s*$", re.MULTILINE | re.IGNORECASE)
_GROSS_PROFIT_ROW_RE = re.compile(r"^" + _GROSS_PROFIT_LABEL + r"\s+(" + _TR_NUM + r")\s+(" + _TR_NUM + r")\s+(" + _TR_NUM + r")\s+(" + _TR_NUM + r")\s+(" + _TR_NUM + r")\s*$", re.MULTILINE)


@dataclass(frozen=True)
class PriceReportFinancials:
    period_label: str | None  # örn. "31.03.2026" (güncel ara dönem)
    full_year_label: str | None  # örn. "2025" (en son tam yıl)
    revenue_latest_interim: Decimal | None
    revenue_prior_year_interim: Decimal | None
    revenue_full_year: Decimal | None
    gross_profit_latest_interim: Decimal | None
    gross_profit_prior_year_interim: Decimal | None
    total_assets: Decimal | None
    total_equity: Decimal | None


def extract_price_report_financials(text: str) -> PriceReportFinancials:
    """Fiyat Tespit Raporu düz metninden `PriceReportFinancials`i üretir --
    SAF ayrıştırma, ağ erişimi YOK. Her alan, beklenen etiket+kolon sayısı
    TAM eşleşmezse (Kural 3) None kalır."""
    header_match = _BALANCE_HEADER_RE.search(text)
    period_label = header_match.group(4) if header_match else None
    full_year_label = header_match.group(3)[-4:] if header_match else None

    total_assets = None
    match = _TOTAL_ASSETS_RE.search(text)
    if match:
        total_assets = _to_decimal(match.group(4))

    total_equity = None
    match = _TOTAL_EQUITY_RE.search(text)
    if match:
        total_equity = _to_decimal(match.group(4))

    revenue_full_year = revenue_prior_year_interim = revenue_latest_interim = None
    match = _REVENUE_ROW_RE.search(text)
    if match:
        revenue_full_year = _to_decimal(match.group(3))
        revenue_prior_year_interim = _to_decimal(match.group(4))
        revenue_latest_interim = _to_decimal(match.group(5))

    gross_profit_prior_year_interim = gross_profit_latest_interim = None
    match = _GROSS_PROFIT_ROW_RE.search(text)
    if match:
        gross_profit_prior_year_interim = _to_decimal(match.group(4))
        gross_profit_latest_interim = _to_decimal(match.group(5))

    return PriceReportFinancials(
        period_label=period_label,
        full_year_label=full_year_label,
        revenue_latest_interim=revenue_latest_interim,
        revenue_prior_year_interim=revenue_prior_year_interim,
        revenue_full_year=revenue_full_year,
        gross_profit_latest_interim=gross_profit_latest_interim,
        gross_profit_prior_year_interim=gross_profit_prior_year_interim,
        total_assets=total_assets,
        total_equity=total_equity,
    )


def fetch_and_parse_price_report(disclosure: IzahnameDisclosure) -> PriceReportFinancials | None:
    """Fiyat Tespit Raporu'nu bulup indirir ve ayrıştırır. Bu, YARDIMCI/
    İKİNCİL bir veri kaynağıdır (Kural 9) -- bulunamazsa/indirilemezse/
    hata olursa None döner, halka arz kartının ANA akışını BLOKLAMAZ."""
    try:
        disclosure_index = find_price_report_disclosure_index(disclosure)
        if disclosure_index is None:
            logger.info("%s için Fiyat Tespit Raporu bulunamadı, o bölüm olmadan devam ediliyor.", disclosure.target_tickers)
            return None
        pdf_bytes = kap.fetch_disclosure_attachment_pdf(disclosure_index)
        if pdf_bytes is None:
            return None
        time.sleep(_COURTESY_DELAY_SECONDS)
        text = _pdf_bytes_to_text(pdf_bytes)
        return extract_price_report_financials(text)
    except Exception:  # noqa: BLE001 -- Kural 9: bu bölüm ikincildir, hata TÜM sonucu ÇÖKERTMEMELİ
        logger.warning("Fiyat Tespit Raporu çekilirken/ayrıştırılırken hata oluştu, o bölüm olmadan devam ediliyor.", exc_info=True)
        return None
