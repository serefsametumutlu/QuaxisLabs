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
  - TÜREV (VIOP Futures + Nakit Teminatı): ~%0,01
  - DİĞER (bu örnekte "Y.Fonu Türk" -- başka fonların payları, örn.
    "PCS-PUSULA PORTFÖY ÜÇÜNCÜ HİSSE SENEDİ SERBEST FON"): %20,60
  - Toplam (Hisse+Türev+Diğer) = "A-)FON PORTFÖY DEĞERİ" = %97,66
  - Kalan %2,34 menkul kıymet DEĞİL -- fonun nakit/alacak/borç
    kalemleri (B-)HAZIR DEĞERLER +%0,03, C-)ALACAKLAR +%13,89,
    E-)BORÇLAR -%11,58 vb., "IV-FON TOPLAM DEĞERİ TABLOSU"dan) -- tek
    tek "holding" olarak İZLENEMEZ (kaç ayrı kalem olduğu itemize
    EDİLMİYOR) ama TOPLAM etkisi tek bir "nakit" sözde-satırı
    (`instrument_type="nakit"`) olarak eklenir.
`_parse_portfolio_pdf()` HİSSE + DİĞER + TÜREV (`instrument_type=
"türev"`) bölümlerini AYRI AYRI (her biri kendi grup toplamıyla)
ayrıştırıp öz-doğruluyor, ARDINDAN kalan farkı (100 - toplam) TEK bir
"nakit" sözde-satırı olarak ekliyor -- nihai toplam PHE'de %100,00'e
ulaşıyor (kendi IV-tablosundaki B..G kalemlerinin toplamıyla tutarlı).

🚨 TÜREV bölümünün İKİ alt-yapısı VAR, hisse/fon satır biçiminden
FARKLI: Futures satırı ("F_XU0300826") ticker+TL işaretiyle BAŞLAR ama
gerçek bir ISIN (TR...) YERİNE kontrat kodu TEKRARLANIYOR --
`_CONTRACT_CODE_RE` ile eşleştirilip pseudo-kimlik olarak kullanılıyor.
"VIOP Nakit Teminatı" satırının ise ticker+TL işareti HİÇ YOK (3
kelimelik düz bir etiket, sadece 4 sayısal alan) -- genel satır
ayrıştırıcıya UYMUYOR, `_parse_viop_cash_collateral()` adlı ayrı, küçük
bir yardımcıyla TEK bir toplam değer olarak okunuyor.
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
_FUTURES_TICKER_RE = re.compile(r"^F_[A-Z0-9]+$")  # "F_XU0300826" gibi -- VIOP futures kontrati
_ISIN_RE = re.compile(r"^TR[A-Z0-9]{10,11}$")
_CONTRACT_CODE_RE = re.compile(r"^F_[A-Z0-9]+$")  # futures satirinda ISIN YERINE kontrat kodu tekrarlanir
_PURE_INT_RE = re.compile(r"^\d{5,10}$")  # borsa sözleşme no gibi virgülsüz tam sayı -- atlanır
_ALL_SECTION_HEADERS = (
    "BORÇLANMA SENETLERİ",
    "KİRA SERTİFİKALARI",
    "TÜREV",
    "DİĞER",
    "TAKAS",
)
# (bölüm başlığı, enstrüman tipi, satır-başlangıcı ticker deseni, satır-içi
# dikey tolerans, "ISIN" yerine kullanılacak kimlik deseni) -- dikey tolerans
# CANLI kalibre edildi: HİSSE'de ticker/TL/sayılar TAM AYNI 'top' değerinde
# (1pt yeterli); DİĞER (fon) ve TÜREV (futures) bölümlerinde ~2pt fark
# GÖZLEMLENDİ -- tek bir ortak tolerans HİSSE'de YANLIŞ satır birleşmelerine
# yol açtığı için (CANLI gözlemlendi) bölüm bazında AYRI tutuluyor.
_PARSEABLE_SECTIONS = (
    ("HİSSE SENETLERİ", "hisse", _STOCK_TICKER_RE, 1, _ISIN_RE),
    ("DİĞER", "fon", _FUND_TICKER_RE, 3, _ISIN_RE),
    ("TÜREV", "türev", _FUTURES_TICKER_RE, 3, _CONTRACT_CODE_RE),
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


def _publish_dt(row: tuple) -> datetime:
    return datetime.strptime(row[0], "%d.%m.%Y %H:%M:%S")


def find_portfolio_disclosures(fund_oid: str) -> list[dict]:
    """`bildirim-sorgu-sonuc` sayfasını fonun oid'i ile sorgular, gömülü
    `disclosureBasic` kayıtları arasından TÜM "Portföy Dağılım Raporu"
    bildirimlerini (en yeniden en eskiye sıralı) döner -- boşsa boş liste.

    CANLI doğrulandı (2026-08-05): TLY/AFA/PBR/PHE'nin hepsinde bu sorgu
    gerçek "Portföy Dağılım Raporu" bildirimleri döndürdü -- eski
    `disclosure/members/byCriteria` API'sinin AKSİNE (bkz. modül üst notu).

    Faz 18 geriye dönük doğrulama (`scripts/validate_fon_tahmini.py`)
    İÇİN eklendi -- TEK bir "en güncel" rapor YETMEZ, geçmiş bir tarih
    için "O TARİHTE YAYINLANMIŞ OLAN en güncel rapor"ı bulabilmek
    (look-ahead bias YAPMADAN, bkz. `scripts/validate_fon_tahmini.py`
    üst notu) TÜM listeye ihtiyaç duyar.
    """
    response = _get(_SEARCH_RESULT_ENDPOINT, params={"srcbar": "Y", "cmp": "N", "cat": "2", "m": fund_oid})
    text = _unescape_next_js_string(response.text)

    matches = _DISCLOSURE_ROW_RE.findall(text)
    candidates = [m for m in matches if m[2] == _PORTFOLIO_REPORT_TITLE]

    disclosures = [
        {
            "disclosure_index": int(disclosure_index),
            "publish_date": _publish_dt(m).date(),
            "summary": summary,
            "year": int(year),
            "period": int(period),
        }
        for m in candidates
        for (publish_date_str, disclosure_index, _title, summary, year, period) in [m]
    ]
    disclosures.sort(key=lambda d: d["publish_date"], reverse=True)
    return disclosures


def _find_latest_portfolio_disclosure(fund_oid: str) -> dict | None:
    """`find_portfolio_disclosures()`'ın en yenisini döner, yoksa None."""
    disclosures = find_portfolio_disclosures(fund_oid)
    return disclosures[0] if disclosures else None


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


def _parse_section_rows(
    words: list[dict],
    ticker_re: re.Pattern,
    instrument_type: str,
    row_tolerance: int = 1,
    id_re: re.Pattern = _ISIN_RE,
) -> list[Holding]:
    """Bir bölümün (HİSSE SENETLERİ / DİĞER / TÜREV) kelime listesini
    satır satır ayrıştırır, her benzersiz (ticker, kimlik) için lot'ları
    toplayarak NET ağırlığı hesaplar. `id_re` HİSSE/DİĞER'de gerçek ISIN
    (`_ISIN_RE`), TÜREV'de kontrat kodu (`_CONTRACT_CODE_RE`) arar.

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
        item_id = next((w["text"] for w in block if id_re.match(w["text"])), None)
        if item_id is None:
            continue

        first_line = [w for w in block if abs(w["top"] - start_top) < row_tolerance and w["x0"] > 110]
        first_line = [
            w
            for w in first_line
            if not _PURE_INT_RE.match(w["text"])
            and not id_re.match(w["text"])
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
            and not id_re.match(w["text"])
            and w["text"] != "TL"
        ]
        name_words.sort(key=lambda w: (w["top"], w["x0"]))
        name = " ".join(w["text"] for w in name_words).strip()

        group_pct = _to_decimal(first_line[5]["text"])
        weight_pct = _to_decimal(first_line[7]["text"])
        if group_pct is None or weight_pct is None:
            continue

        group_pct_total += group_pct
        key = (ticker, item_id)
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
        Holding(instrument_type=instrument_type, ticker=ticker, name=names.get((ticker, item_id), ""), weight_pct=weight)
        for (ticker, item_id), weight in sorted(aggregated.items(), key=lambda kv: -kv[1])
    ]


def _parse_viop_cash_collateral(turev_words: list[dict]) -> Holding | None:
    """'VIOP Nakit Teminatı' satırı diğer TÜM satırlardan FARKLI bir
    yapıya sahiptir -- ticker+"TL" işareti YOK (sadece 3 kelimelik düz
    bir etiket, "VIOP Nakit Teminatı"), sadece 2 sayısal (nominal +
    toplam değer) VE 2 yüzde alanı var (8 DEĞİL) -- bu yüzden genel
    `_parse_section_rows()`'a UYMAZ, ayrı bir mini-ayrıştırıcı gerekir.
    Etiket İKİ KEZ görünür (önce salt başlık satırı, sonra veri satırı,
    CANLI gözlemlendi) -- sayısal içeriği OLAN satır alınır."""
    for word in turev_words:
        if word["text"] != "VIOP" or word["x0"] > 22:
            continue
        row_top = word["top"]
        same_line = [w for w in turev_words if abs(w["top"] - row_top) < 3]
        numeric = [w for w in same_line if w["x0"] > 300 and any(ch.isdigit() for ch in w["text"])]
        if len(numeric) < 2:
            continue  # bu sadece etiket satırı, veri satırı DEĞİL
        numeric.sort(key=lambda w: w["x0"])
        weight_pct = _to_decimal(numeric[-1]["text"])  # son sayısal alan = fon toplam değerine göre pay
        if weight_pct is None:
            continue
        return Holding(instrument_type="türev", ticker=None, name="VIOP Nakit Teminatı", weight_pct=weight_pct)
    return None


def _parse_portfolio_pdf(pdf_bytes: bytes) -> list[Holding]:
    """PDF'teki ayrıştırılabilir bölümleri (`_PARSEABLE_SECTIONS` --
    HİSSE SENETLERİ + DİĞER/fon-içinde-fon + TÜREV) satır satır
    ayrıştırır. HER BÖLÜM kendi grup toplamıyla AYRI AYRI öz-doğrulanır
    (bkz. `_parse_section_rows`) -- bir bölüm güvenilmez çıkarsa SADECE o
    bölüm atlanır, diğerleri yine döner. TÜREV'in "VIOP Nakit Teminatı"
    alt-kalemi farklı bir satır yapısına sahip olduğu için AYRI bir
    mini-ayrıştırıcıyla (`_parse_viop_cash_collateral`) okunur.

    Kalan fark (100 - toplam ağırlık) menkul kıymet OLMAYAN nakit/alacak/
    borç kalemlerini (fonun "IV-FON TOPLAM DEĞERİ TABLOSU"sundaki
    B..G satırları) temsil eder -- bunlar tek tek itemize EDİLEMEDİĞİ
    için TEK bir `instrument_type="nakit"` sözde-satırı olarak eklenir
    (bkz. modül üst notu). ⚠️ Bu residual SADECE en az bir gerçek bölüm
    başarıyla ayrıştırıldıysa eklenir -- HİÇBİR bölüm ayrıştırılamazsa
    (`all_holdings` boşsa) residual da eklenmez (aksi halde "%100 nakit"
    gibi YANLIŞ bir izlenim verirdi, Kural 3).
    """
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            all_holdings: list[Holding] = []
            turev_words: list[dict] = []
            for section_start, instrument_type, ticker_re, row_tolerance, id_re in _PARSEABLE_SECTIONS:
                words = _extract_section_words(pdf, section_start)
                if section_start == "TÜREV":
                    turev_words = words
                if not words:
                    logger.info("PDF'te '%s' bölümü bulunamadı.", section_start)
                    continue
                all_holdings.extend(_parse_section_rows(words, ticker_re, instrument_type, row_tolerance, id_re))

            viop_holding = _parse_viop_cash_collateral(turev_words)
            if viop_holding is not None:
                all_holdings.append(viop_holding)
    except Exception as exc:  # pdfplumber bozuk/beklenmeyen bir PDF'te cesitli hatalar firlatabilir
        logger.warning("KAP portföy dağılım PDF'i açılamadı/ayrıştırılamadı: %s", exc)
        return []

    if all_holdings:
        total = sum(h.weight_pct for h in all_holdings)
        residual = Decimal(100) - total
        if Decimal("0.005") < residual <= Decimal(100):
            all_holdings.append(
                Holding(instrument_type="nakit", ticker=None, name="Nakit ve Diğer Varlıklar (kalan)", weight_pct=residual)
            )
        elif residual < Decimal("-0.5"):
            # Ayrıştırılan toplam %100'ü ANLAMLI ölçüde asiyorsa (mukerrer
            # sayim / bir bolumun yanlis ayristirilmasi ihtimali) residual
            # EKLENMEZ ve durum loglanir -- Kural 3.
            logger.warning(
                "KAP portföy dağılım PDF'inde ayrıştırılan toplam ağırlık %%100'ü aşıyor (%s) -- "
                "residual 'nakit' satırı eklenmedi, bir bölümde mükerrer sayım olabilir.",
                total,
            )

    return sorted(all_holdings, key=lambda h: -h.weight_pct)


# --- Genel API -----------------------------------------------------


def report_period_end(year: int, month: int) -> date:
    next_month_first = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return next_month_first - timedelta(days=1)  # raporun ait oldugu ayin son gunu


def resolve_fund_oid(fund_code: str) -> str | None:
    """`_search_fund()`'ı sarar, SADECE oid'i döner -- bulunamazsa/hata
    olursa None (Kural 9). `scripts/validate_fon_tahmini.py` gibi
    çağıranların oid'i tek seferde çözüp `find_portfolio_disclosures()`
    ile TEKRAR TEKRAR kullanabilmesi için (her seferinde `_search_fund`
    tekrar çağrılmasın diye) dışarıya açıldı."""
    try:
        return _search_fund(fund_code)["memberOrFundOid"]
    except FundNotFoundError:
        logger.warning("'%s' KAP fon aramasında bulunamadı.", fund_code)
        return None
    except kap.KapError as exc:
        logger.warning("KAP fon araması başarısız oldu: %s", exc)
        return None


def fetch_portfolio_by_disclosure(fund_code: str, disclosure: dict, as_of: date | None = None) -> FundPortfolio | None:
    """Belirli bir bildirimin (bkz. `find_portfolio_disclosures()`
    çıktısı) ekli PDF'ini indirip ayrıştırır. `as_of` verilirse
    `staleness_days` o tarihe göre hesaplanır (GERİYE DÖNÜK doğrulama
    için -- bkz. `scripts/validate_fon_tahmini.py`); verilmezse bugüne
    göre hesaplanır (CANLI kullanım).

    Hatalar fırlatmaz (Kural 9) -- PDF indirilemez/ayrıştırılamazsa None.
    """
    try:
        pdf_bytes = _fetch_attachment_pdf(disclosure["disclosure_index"])
    except (kap.KapError, KapFundPortfolioError) as exc:
        logger.warning("KAP portföy dağılım raporu PDF'i indirilemedi (%s): %s", fund_code, exc)
        return None
    if pdf_bytes is None:
        return None

    holdings = _parse_portfolio_pdf(pdf_bytes)
    report_date = report_period_end(disclosure["year"], disclosure["period"])
    reference_date = as_of if as_of is not None else date.today()

    return FundPortfolio(
        fund_code=fund_code.strip().upper(),
        report_date=report_date,
        publish_date=disclosure["publish_date"],
        holdings=holdings,
        staleness_days=(reference_date - report_date).days,
    )


def fetch_latest_portfolio(fund_code: str) -> FundPortfolio | None:
    """Bir fonun EN GÜNCEL hisse-bazlı "Portföy Dağılım Raporu"nu KAP'tan
    çeker ve ayrıştırır.

    Hatalar fırlatmaz -- yardımcı/ikincil bir veri kaynağıdır (Kural 9);
    fon bulunamazsa, hiç rapor yoksa, PDF indirilemezse veya ayrıştırma
    güvenilir sonuç vermezse None döner, sebep loglanır.
    """
    fund_oid = resolve_fund_oid(fund_code)
    if fund_oid is None:
        return None

    try:
        disclosure = _find_latest_portfolio_disclosure(fund_oid)
    except (kap.KapError, KapFundPortfolioError) as exc:
        logger.warning("KAP fon bildirimleri çekilemedi (%s): %s", fund_code, exc)
        return None

    if disclosure is None:
        logger.info("'%s' için KAP'ta hiç 'Portföy Dağılım Raporu' bulunamadı.", fund_code)
        return None

    return fetch_portfolio_by_disclosure(fund_code, disclosure)
