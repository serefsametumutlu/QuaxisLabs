"""KAP (Kamuyu Aydınlatma Platformu) yatırım fonu "Portföy Dağılım Raporu"
fetcher'ı -- hisse bazlı fon içeriği.

Faz 17 keşif turunda (ilk keşif, bkz. scripts/explore_kap_fon.py) YANLIŞ bir
sonuca varılmıştı: `kap.py::DISCLOSURES_ENDPOINT` (`disclosure/members/
byCriteria`, BIST şirketleri için kullanılan uç nokta) fon oid'leriyle
sorgulanınca HER ZAMAN boş liste döndü, bu yüzden "hisse bazlı fon içeriği
KAP'ta bulunamıyor" sonucuna varılmıştı.

🚨 KULLANICI DÜZELTMESİ (2026-08-05, aynı oturum): kullanıcı fvt.com.tr
üzerinden GERÇEK bir örnek paylaştı (PHE fonu, "PHE - PORTFÖY DAĞILIM
RAPORU TEMMUZ 2026") ve bunun KAP'ta GERÇEKTEN var olduğunu gösterdi. Kök
neden bulundu: fon bildirimleri `disclosure/members/byCriteria` API'si
YERİNE KAP'ın KLASİK arama sayfası üzerinden sorgulanmalıymış:

    GET https://kap.org.tr/tr/bildirim-sorgu-sonuc
        ?srcbar=Y&cmp=N&cat=2&m=<fonun mkkMemberOid'i>

CANLI doğrulandı: bu tek uç nokta TLY/AFA/PBR/PHE'nin TÜMÜNDE gerçek
"Portföy Dağılım Raporu" bildirimleri döndürüyor (aylık yayınlanıyor).
Yanıt HTML'i içinde `"data":[{"disclosureBasic":{...}}]` JSON dizisi
gömülü geliyor (bot koruması YOK, düz `httpx` ile çalışıyor).

Bildirim detay sayfası (`kap.org.tr/tr/Bildirim/{index}`) içinde ekli PDF
dosyasının indirme linki: `"attachments":[{"objId":"...","fileName":"..."}]`
-> `https://kap.org.tr/tr/api/file/download/{objId}`.

PDF İÇERİĞİ: HER HİSSE için ayrı satır (ISIN kodu, BİST kodu, şirket adı,
nominal değer, alış tarihi/fiyatı, toplam değer, 3 AYRI yüzde kolonu) --
CANLI doğrulandı, PHE Temmuz 2026 raporunda 21 farklı hisse, satın alma
"lot"ları bazında (aynı hisse birden fazla satırda -- farklı tarihte
alınan/satılan lotlar) listeleniyor.

⚠️ ÜÇ YÜZDE KOLONUNUN ANLAMI (PHE Temmuz 2026 ile CANLI doğrulandı, Kural 3):
PDF'in "GRUP TOPLAMI" satırı Hisse Senetleri grubu için üç toplam veriyor:
100,00 / 78,89 / 77,05. Parser'ın çıkardığı 3 kolonun (sıradaki 5./6./7.
sayısal alan) TOPLAMLARI da BİREBİR bu üç değere eşleşti:
  - 5. kolon ("GRUP %"): grup İÇİNDE bu hissenin payı -- grup toplamı HER
    ZAMAN %100 (bu, evrensel bir öz-doğrulama imkanı verir, aşağı bkz.)
  - 6. kolon ("TOPLAM FPD GÖRE"): Fon PORTFÖY Değeri'ne göre pay (nakit/
    alacak-borç hariç, sadece portföydeki varlıklara göre)
  - 7. kolon ("TOPLAM FTD GÖRE"): Fon TOPLAM Değeri'ne göre pay -- TEFAS'ın
    `varlikData.portfoyOrani` alanıyla AYNI anlamı taşır (fonun TÜM NAV'ına
    göre ağırlık), bu yüzden `Holding.weight_pct` İÇİN BU kolon kullanılır.
  Çapraz doğrulama: 6. kolon toplamı (78,89) × (Fon Portföy Değeri/Fon
  Toplam Değeri = %97,66, PDF'in kendi IV. tablosundan) = 77,05 (7. kolon
  toplamı) -- 2 ONDALIKLA BİREBİR tutarlı.

⚠️ AMA BU ŞEMA HER FON İÇİN AYNI ÇIKMADI: TLY'nin Temmuz 2026 raporunda
AYNI parser 5. kolon toplamını 199,77 verdi (100 olması gerekirken) --
kök neden sayfa sınırındaki bir satırın (HMV) adının bir SONRAKİ sayfanın
başlığına taşmasıydı, sabit bir üst satır-aralığı sınırıyla (`_MAX_ROW_SPAN`)
düzeltildi. Kural 3 gereği YANLIŞ rakamla devam EDİLMEDİ:
`_parse_portfolio_pdf()` her bölümün grup toplamının %100'e
(±`_GROUP_TOTAL_TOLERANCE`) yakın olduğunu DOĞRULAR -- tutmuyorsa o
bölümün holdings'i BOŞ döner, hata FIRLATMAZ, sadece loglar (Kural 9).

🚨 KULLANICI DÜZELTMESİ #2 (aynı oturum): kullanıcı raporun SADECE HİSSE
değil, fon-içinde-fon gibi BAŞKA enstrüman türleri de içerdiğini ve
toplamın %77,05 (sadece hisse) DEĞİL %100'e (fonun TAMAMI) tamamlanması
gerektiğini belirtti -- HAKLI. PHE Temmuz 2026'da PDF'in "IV-FON TOPLAM
DEĞERİ TABLOSU"su incelenince tam resim ortaya çıktı:
  - HİSSE SENETLERİ: %77,05 (Fon Toplam Değeri'ne göre)
  - TÜREV (VIOP Futures + Nakit Teminatı): ~%0,01 (ÇOK küçük, bu
    oturumda AYRI bir parser YAZILMADI -- karmaşık/nadir bir yapı)
  - DİĞER (bu örnekte "Y.Fonu Türk" -- başka fonların payları, örn.
    "PCS-PUSULA PORTFÖY ÜÇÜNCÜ HİSSE SENEDİ SERBEST FON"): %20,60
  - Toplam (Hisse+Türev+Diğer) = %97,66 = PDF'in kendi "A-)FON PORTFÖY
    DEĞERİ" satırıyla BİREBİR eşleşti.
  - Kalan %2,34 menkul kıymet DEĞİL -- fonun nakit/alacak/borç
    kalemleri (HAZIR DEĞERLER +%0,03, ALACAKLAR +%13,89, BORÇLAR
    -%11,58 vb.) -- tek tek "holding" olarak İZLENEMEZ, doğası gereği.
`_parse_portfolio_pdf()` artık HEM "HİSSE SENETLERİ" HEM "DİĞER"
bölümünü ayrıştırıyor (`instrument_type="hisse"`/`"fon"`), HER BÖLÜM
KENDİ GRUP TOPLAMIYLA AYRI AYRI öz-doğrulanıyor (PHE'de DİĞER de %20,60
ile BİREBİR eşleşti). TÜREV bölümü (genelde ihmal edilebilir büyüklükte)
bu oturumda KAPSAM DIŞI bırakıldı -- gelecekte eklenebilir.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

import httpx
import pdfplumber
from io import BytesIO
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

import config
from src.fetchers import kap

logger = logging.getLogger(__name__)

_SEARCH_RESULT_ENDPOINT = "https://kap.org.tr/tr/bildirim-sorgu-sonuc"
_FILE_DOWNLOAD_TEMPLATE = "https://kap.org.tr/tr/api/file/download/{obj_id}"

_PORTFOLIO_REPORT_TITLE = "Portföy Dağılım Raporu"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.kap.org.tr/",
}

# PDF satır ayrıştırma sabitleri -- PHE (Temmuz 2026) ve TLY (Temmuz 2026)
# raporlarıyla CANLI kalibre edildi (bkz. modül üst notu).
_STOCK_TICKER_RE = re.compile(r"^[A-ZÇĞİÖŞÜ]{2,6}\d?$")  # "AKSEN", "ALKLC" gibi
_FUND_TICKER_RE = re.compile(r"^[A-Z]{2,6}-")  # "PCS-PUSULA..." gibi -- fon-icinde-fon satirlari
_ISIN_RE = re.compile(r"^TR[A-Z0-9]{10,11}$")
_PURE_INT_RE = re.compile(r"^\d{5,10}$")  # borsa sözleşme no gibi virgülsüz tam sayı -- atlanır
_ALL_SECTION_HEADERS = (
    "BORÇLANMA SENETLERİ",
    "KİRA SERTİFİKALARI",
    "TÜREV",
    "DİĞER",
    "TAKAS",
)
# (bölüm başlığı, ayrıştırma başlarken aranan enstrüman tipi, satır-başlangıcı
# ticker deseni, satır-içi dikey tolerans) -- HİSSE SENETLERİ + DİĞER
# (fon-içinde-fon) bu oturumda ayrıştırılıyor; TÜREV (genelde ihmal
# edilebilir büyüklükte, çok farklı bir satır yapısı) BİLİNÇLİ olarak
# kapsam dışı (bkz. modül üst notu). Dikey tolerans CANLI kalibre edildi:
# HİSSE bölümünde ticker/TL/sayılar TAM AYNI 'top' değerinde (tolerans 1pt
# yeterli); DİĞER (fon) bölümünde ~2pt fark GÖZLEMLENDİ (PCS-PUSULA örneği)
# -- tek bir ortak tolerans kullanmak HİSSE'de YANLIŞ satır birleşmelerine
# yol açtığı için (CANLI gözlemlendi) bölüm bazında AYRI tutuluyor.
_PARSEABLE_SECTIONS = (
    ("HİSSE SENETLERİ", "hisse", _STOCK_TICKER_RE, 1),
    ("DİĞER", "fon", _FUND_TICKER_RE, 3),
)
_GROUP_TOTAL_TOLERANCE = Decimal("2.0")  # grup toplamı %100'den en fazla bu kadar sapabilir


# --- Hata sınıfları -----------------------------------------------------


class KapFundPortfolioError(Exception):
    """KAP fon portföy fetcher'ı için taban hata sınıfı."""


class FundNotFoundError(KapFundPortfolioError):
    """Verilen fon kodu KAP arama sonuçlarında (searchType='F') bulunamadı."""


# --- Veri modelleri -----------------------------------------------------


@dataclass(frozen=True)
class Holding:
    instrument_type: str  # "hisse" | "fon" (fon-içinde-fon) -- bkz. modül üst notu; TÜREV/nakit KAPSAM DIŞI
    ticker: str | None  # BİST kodu (hisse) veya TEFAS fon kodu (fon)
    name: str
    weight_pct: Decimal  # Fon Toplam Değeri'ne göre pay (TEFAS portfoyOrani ile AYNI anlam)


@dataclass(frozen=True)
class FundPortfolio:
    fund_code: str
    report_date: date  # raporun AİT OLDUĞU dönem sonu (örn. 2026-07-31)
    publish_date: date
    holdings: list[Holding]
    staleness_days: int  # bugün - report_date


# --- HTTP katmanı -----------------------------------------------------


@retry(
    reraise=True,
    stop=stop_after_attempt(config.HTTP_MAX_RETRIES),
    wait=wait_fixed(config.HTTP_RATE_LIMIT_DELAY_SECONDS),
    retry=retry_if_exception_type(httpx.RequestError),
)
def _get(url: str, params: dict | None = None) -> httpx.Response:
    try:
        response = httpx.get(url, params=params, headers=_HEADERS, timeout=config.HTTP_TIMEOUT_SECONDS, follow_redirects=True)
    except httpx.RequestError as exc:
        logger.warning("KAP fon portföy isteği başarısız, yeniden denenecek: %s", exc)
        raise
    if response.status_code != 200:
        raise KapFundPortfolioError(f"KAP beklenmeyen HTTP durum kodu döndürdü: {response.status_code} ({url})")
    return response


def _unescape_next_js_string(html_text: str) -> str:
    """KAP'ın Next.js RSC payload'ı JSON'u bir JS string literali İÇİNDE
    taşıyor (`self.__next_f.push([1,"..."])`), bu yüzden iç JSON'un tırnak
    işaretleri `\\"` olarak escape'lenmiş geliyor -- kap.py'nin sektör
    haritası ayrıştırmasıyla AYNI desen (orada çift escape, burada tek)."""
    return html_text.replace('\\"', '"').replace("\\\\", "\\")


# --- Fon arama + bildirim listesi -----------------------------------------------------


def _search_fund(fund_code: str) -> dict:
    """`kap.py::SEARCH_ENDPOINT`'i kullanarak fon kodunu KAP'ın
    'companyOrFunds' sonuçlarında arar, `searchType == "F"` ve
    `cmpOrFundCode` eşleşen ilk satırı döner.

    Hatalar:
        FundNotFoundError: Fon kodu bulunamadı.
        kap.KapNetworkError: Ağ hatası veya beklenmeyen yanıt biçimi.
    """
    normalized = kap.normalize_ticker(fund_code)
    payload = kap._post_json(kap.SEARCH_ENDPOINT, {"keyword": normalized})

    if not isinstance(payload, list):
        raise kap.KapNetworkError("KAP fon arama yanıtı beklenmeyen biçimde (liste değil).")

    rows = next((c.get("results", []) for c in payload if c.get("category") == "companyOrFunds"), [])
    for row in rows:
        if row.get("searchType") != "F":
            continue
        codes = tuple((row.get("cmpOrFundCode") or "").split(","))
        if normalized in codes:
            return row

    raise FundNotFoundError(f"'{fund_code}' KAP fon aramasında bulunamadı (searchType='F').")


_DISCLOSURE_ROW_RE = re.compile(
    r'"disclosureBasic":\{"publishDate":"([^"]+)","disclosureIndex":(\d+)[^{}]*?"title":"([^"]+)"[^{}]*?'
    r'"summary":"([^"]*)"[^{}]*?"year":(\d+),"period":(\d+)'
)


def _find_latest_portfolio_disclosure(fund_oid: str) -> dict | None:
    """`bildirim-sorgu-sonuc` sayfasını fonun oid'i ile sorgular, gömülü
    `disclosureBasic` kayıtları arasından en YENİ "Portföy Dağılım Raporu"nu
    döner. Bulunamazsa None döner (Kural 9).

    CANLI doğrulandı (2026-08-05): TLY/AFA/PBR/PHE'nin hepsinde bu sorgu
    gerçek "Portföy Dağılım Raporu" bildirimleri döndürdü -- eski
    `disclosure/members/byCriteria` API'sinin AKSİNE (bkz. modül üst notu).
    """
    response = _get(_SEARCH_RESULT_ENDPOINT, params={"srcbar": "Y", "cmp": "N", "cat": "2", "m": fund_oid})
    text = _unescape_next_js_string(response.text)

    matches = _DISCLOSURE_ROW_RE.findall(text)
    candidates = [m for m in matches if m[2] == _PORTFOLIO_REPORT_TITLE]
    if not candidates:
        return None

    def _publish_dt(row: tuple) -> datetime:
        return datetime.strptime(row[0], "%d.%m.%Y %H:%M:%S")

    latest = max(candidates, key=_publish_dt)
    publish_date_str, disclosure_index, _title, summary, year, period = latest
    return {
        "disclosure_index": int(disclosure_index),
        "publish_date": _publish_dt(latest).date(),
        "summary": summary,
        "year": int(year),
        "period": int(period),  # ay numarasi (1-12)
    }


_ATTACHMENT_RE = re.compile(r'"attachments":\[\{"objId":"([^"]+)","fileName":"([^"]+)"')


def _fetch_attachment_pdf(disclosure_index: int) -> bytes | None:
    """Bildirim detay sayfasından ekli PDF'in objId'sini bulup indirir.
    Ekli dosya yoksa/PDF değilse None döner (Kural 9)."""
    response = _get(kap.DISCLOSURE_DETAIL_URL_TEMPLATE.format(disclosure_index=disclosure_index))
    text = _unescape_next_js_string(response.text)

    match = _ATTACHMENT_RE.search(text)
    if not match:
        logger.info("Bildirim %s için ekli dosya bulunamadı.", disclosure_index)
        return None
    obj_id, file_name = match.groups()
    if not file_name.lower().endswith(".pdf"):
        logger.info("Bildirim %s ekindeki dosya PDF değil (%s), atlanıyor.", disclosure_index, file_name)
        return None

    pdf_response = _get(_FILE_DOWNLOAD_TEMPLATE.format(obj_id=obj_id))
    return pdf_response.content


# --- PDF ayrıştırma (hisse satırları) -----------------------------------------------------


def _to_decimal(text: str) -> Decimal | None:
    try:
        return Decimal(text.replace(".", "").replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def _extract_section_words(pdf: "pdfplumber.PDF", section_start: str) -> list[dict]:
    """TÜM sayfalardaki kelimeleri, SADECE `section_start` başlığının
    başlangıcı ile bir sonraki bilinen bölüm başlığı arasında kalanları,
    sayfa sınırları arasında da doğru sıralama korunacak şekilde
    (her sayfaya büyük bir 'top' ofseti eklenerek) toplar.

    `_PARSEABLE_SECTIONS`'taki HER bölüm için AYRI AYRI çağrılır -- örn.
    "DİĞER" araması "HİSSE SENETLERİ" satırlarını YAKALAMAZ, tam tersi de
    geçerli (section_start'ın KENDİSİ terminator listesinden çıkarılır)."""
    PAGE_OFFSET = 100_000  # tek bir sayfanın gercek yuksekligini asan guvenli bir aralik
    terminators = [h for h in _ALL_SECTION_HEADERS if h != section_start]
    section_words = section_start.split()  # örn. ["HİSSE","SENETLERİ"] veya ["DİĞER"]

    collected: list[dict] = []
    in_section = False

    for page_index, page in enumerate(pdf.pages):
        words = page.extract_words()
        page_text = page.extract_text() or ""
        if not in_section and section_start not in page_text:
            continue

        for word in words:
            text = word["text"]
            if not in_section:
                if text in section_words and section_start in page_text:
                    in_section = True
                else:
                    continue
            if any(header.split()[0] in text for header in terminators):
                in_section = False
                continue
            adjusted = dict(word)
            adjusted["top"] = word["top"] + page_index * PAGE_OFFSET
            collected.append(adjusted)

        if not in_section and collected:
            break  # bolum bu sayfada kapandiysa sonraki sayfalari tarama

    return collected


# Bir satirin (isim + ISIN dahil) en fazla ~10 satir/120pt kadar surmesi
# beklenir (en uzun isim bile CANLI ornekte 5-6 satirdan kisaydi) -- bu ust
# sinir olmadan, bir BOLUMUN SON satiri icin bir sonraki satir bulunamayinca
# (idx+1 yok) araligin bir SONRAKI SAYFANIN basligina/sutun basliklarina
# TASMASI riski var (CANLI gozlemlendi: PHE'de BALSU, TLY'de HMV).
_MAX_ROW_SPAN = 120


def _parse_section_rows(words: list[dict], ticker_re: re.Pattern, instrument_type: str, row_tolerance: int = 1) -> list[Holding]:
    """Bir bölümün (HİSSE SENETLERİ veya DİĞER) kelime listesini satır
    satır ayrıştırır, her benzersiz (ticker, ISIN) için lot'ları toplayarak
    NET ağırlığı hesaplar.

    Öz-doğrulama (Kural 3): "GRUP %" kolonunun (her zaman kendi grubu
    içinde toplamı %100 olması gereken kolon) toplamı `_GROUP_TOTAL_TOLERANCE`
    içinde değilse BOŞ liste döner -- yanlış/güvenilmez rakam üretmek
    yerine hiç veri döndürmemeyi tercih eder.
    """
    if not words:
        return []

    row_starts = []
    for i, word in enumerate(words):
        if 18 <= word["x0"] <= 22 and ticker_re.match(word["text"]):
            for candidate in words[i : i + 3]:
                if (
                    abs(candidate["top"] - word["top"]) < row_tolerance
                    and 99 <= candidate["x0"] <= 102
                    and candidate["text"] == "TL"
                ):
                    row_starts.append(i)
                    break

    group_pct_total = Decimal(0)
    aggregated: dict[tuple[str, str], Decimal] = {}
    names: dict[tuple[str, str], str] = {}

    for idx, start_i in enumerate(row_starts):
        start_top = words[start_i]["top"]
        natural_end = words[row_starts[idx + 1]]["top"] if idx + 1 < len(row_starts) else start_top + _MAX_ROW_SPAN
        end_top = min(natural_end, start_top + _MAX_ROW_SPAN)
        block = [w for w in words if start_top - 3 <= w["top"] < end_top]

        raw_ticker = words[start_i]["text"]
        ticker = raw_ticker.split("-")[0]  # fon satırlarında "PCS-PUSULA..." -> "PCS"
        isin = next((w["text"] for w in block if _ISIN_RE.match(w["text"])), None)
        if isin is None:
            continue

        first_line = [w for w in block if abs(w["top"] - start_top) < row_tolerance and w["x0"] > 110]
        first_line = [
            w
            for w in first_line
            if not _PURE_INT_RE.match(w["text"])
            and not _ISIN_RE.match(w["text"])
            and any(ch.isdigit() for ch in w["text"])  # "PUSULA" gibi metin (kurucu adının basi) sayisal DEGIL -- atlanir
        ]
        first_line.sort(key=lambda w: w["x0"])
        if len(first_line) != 8:
            continue  # beklenmeyen kolon sayisi -- bu satiri guvenilir sekilde ayristiramiyoruz (Kural 3)

        name_end_top = end_top - 3
        name_words = [
            w
            for w in block
            if start_top - 3 <= w["top"] < name_end_top
            and 108 < w["x0"] < 350
            and not _ISIN_RE.match(w["text"])
            and w["text"] != "TL"
        ]
        name_words.sort(key=lambda w: (w["top"], w["x0"]))
        name = " ".join(w["text"] for w in name_words).strip()

        group_pct = _to_decimal(first_line[5]["text"])
        weight_pct = _to_decimal(first_line[7]["text"])
        if group_pct is None or weight_pct is None:
            continue

        group_pct_total += group_pct
        key = (ticker, isin)
        aggregated[key] = aggregated.get(key, Decimal(0)) + weight_pct
        if name:
            names[key] = name

    if not aggregated:
        return []

    if abs(group_pct_total - Decimal(100)) > _GROUP_TOTAL_TOLERANCE:
        logger.warning(
            "KAP portföy dağılım PDF'inin '%s' bölümü grup toplamı beklenenden (%%100) "
            "sapıyor (%s) -- ayrıştırma bu bölüm için GÜVENİLİR DEĞİL, boş liste dönüyor (Kural 3).",
            instrument_type,
            group_pct_total,
        )
        return []

    return [
        Holding(instrument_type=instrument_type, ticker=ticker, name=names.get((ticker, isin), ""), weight_pct=weight)
        for (ticker, isin), weight in sorted(aggregated.items(), key=lambda kv: -kv[1])
    ]


def _parse_portfolio_pdf(pdf_bytes: bytes) -> list[Holding]:
    """PDF'teki ayrıştırılabilir bölümleri (`_PARSEABLE_SECTIONS` --
    HİSSE SENETLERİ + DİĞER/fon-içinde-fon) satır satır ayrıştırır. HER
    BÖLÜM kendi grup toplamıyla AYRI AYRI öz-doğrulanır (bkz.
    `_parse_section_rows`) -- bir bölüm güvenilmez çıkarsa SADECE o bölüm
    atlanır, diğerleri yine döner.

    ⚠️ Sonucun toplamı fonun TAMAMINI (%100) KAPSAMAYABİLİR: TÜREV
    (genelde ihmal edilebilir) bu oturumda ayrıştırılmıyor, ayrıca
    fonun nakit/alacak/borç kalemleri (menkul kıymet OLMAYAN kısım)
    doğası gereği "holding" olarak izlenemez (bkz. modül üst notu).
    """
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            all_holdings: list[Holding] = []
            for section_start, instrument_type, ticker_re, row_tolerance in _PARSEABLE_SECTIONS:
                words = _extract_section_words(pdf, section_start)
                if not words:
                    logger.info("PDF'te '%s' bölümü bulunamadı.", section_start)
                    continue
                all_holdings.extend(_parse_section_rows(words, ticker_re, instrument_type, row_tolerance))
    except Exception as exc:  # pdfplumber bozuk/beklenmeyen bir PDF'te cesitli hatalar firlatabilir
        logger.warning("KAP portföy dağılım PDF'i açılamadı/ayrıştırılamadı: %s", exc)
        return []

    return sorted(all_holdings, key=lambda h: -h.weight_pct)


# --- Genel API -----------------------------------------------------


def fetch_latest_portfolio(fund_code: str) -> FundPortfolio | None:
    """Bir fonun EN GÜNCEL hisse-bazlı "Portföy Dağılım Raporu"nu KAP'tan
    çeker ve ayrıştırır.

    Hatalar fırlatmaz -- yardımcı/ikincil bir veri kaynağıdır (Kural 9);
    fon bulunamazsa, hiç rapor yoksa, PDF indirilemezse veya ayrıştırma
    güvenilir sonuç vermezse None döner, sebep loglanır.
    """
    try:
        fund_row = _search_fund(fund_code)
    except FundNotFoundError:
        logger.warning("'%s' KAP fon aramasında bulunamadı.", fund_code)
        return None
    except kap.KapError as exc:
        logger.warning("KAP fon araması başarısız oldu: %s", exc)
        return None

    fund_oid = fund_row["memberOrFundOid"]

    try:
        disclosure = _find_latest_portfolio_disclosure(fund_oid)
    except (kap.KapError, KapFundPortfolioError) as exc:
        logger.warning("KAP fon bildirimleri çekilemedi (%s): %s", fund_code, exc)
        return None

    if disclosure is None:
        logger.info("'%s' için KAP'ta hiç 'Portföy Dağılım Raporu' bulunamadı.", fund_code)
        return None

    try:
        pdf_bytes = _fetch_attachment_pdf(disclosure["disclosure_index"])
    except (kap.KapError, KapFundPortfolioError) as exc:
        logger.warning("KAP portföy dağılım raporu PDF'i indirilemedi (%s): %s", fund_code, exc)
        return None

    if pdf_bytes is None:
        return None

    holdings = _parse_portfolio_pdf(pdf_bytes)

    year, month = disclosure["year"], disclosure["period"]
    next_month_first = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    report_date = next_month_first - timedelta(days=1)  # raporun ait oldugu ayin son gunu

    return FundPortfolio(
        fund_code=fund_code.strip().upper(),
        report_date=report_date,
        publish_date=disclosure["publish_date"],
        holdings=holdings,
        staleness_days=(date.today() - report_date).days,
    )
