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

🚨 KULLANICI KARARI #3 (2026-08-05, aynı oturum): TÜREV bölümünün ayrı
ayrıştırılması KALDIRILDI. Gerekçe: (a) CANLI gözlemde ağırlığı ihmal
edilebilir düzeyde (PHE'de %0,01), (b) İKİ farklı alt-yapısı (futures
satırı + "VIOP Nakit Teminatı" mini-ayrıştırıcısı) kod karmaşıklığına
oranla değer katmıyor, (c) Faz 18 doğrulamasında TÜREV ayrıştırması HER
ZAMAN "bulunamadı" ya da "grup toplamı sapıyor" uyarısı üretti (bkz.
`data/exploration/fon_tahmini_dogrulama_raporu.txt` log'u) -- yani zaten
FİİLEN hiç veri katkısı yapmıyordu, sadece log gürültüsüydü. TÜREV artık
`_PARSEABLE_SECTIONS`'ta YOK; TÜREV başlığı YİNE DE `_ALL_SECTION_HEADERS`
listesinde TUTULUYOR (SADECE bir bölüm SINIRI/terminator olarak -- HİSSE
veya DİĞER bölümünün TÜREV başlığına taşıp yanlış satır karıştırmasını
ÖNLEMEK için, bkz. `_extract_section_words`). TÜREV'in küçük ağırlığı
artık ayrıştırılmıyor bile olsa, portföyün TOPLAM %100'e tamamlanması
etkilenmiyor: parçalanmamış TÜM fark (türev dahil) tek bir "nakit"
residual satırına düşüyor (bkz. `_parse_portfolio_pdf`).

🚨 KULLANICI KARARI #9 (2026-08-06, kullanıcı fvt.com.tr'nin "AI Tahmin
Ağı" görselini paylaşıp HMV'yi de fiyatladıklarını fark etmesiyle
bulundu): TLY'nin Temmuz 2026 raporunda "DİĞER" bölümü HMV (%5,62) ve T3B
(%0,01) adlı iki fon-içinde-fon satırı içeriyordu ama `_FUND_TICKER_RE`
SADECE PHE'deki "PCS-PUSULA..." gibi kurucu adı EKLENMİŞ (tire+isim)
kodları eşleştiriyordu -- HMV/T3B TİRE OLMADAN, TEK BAŞINA yazılmıştı
(CANLI PDF'te doğrulandı: `data/exploration/kap_portfoy_tly_2026_07_text.txt`).
Sonuç: "DİĞER" bölümünün grup toplamı %0 çıkıp TAMAMEN reddediliyordu
(Kural 3 -- yanlış rakamdan iyidir), bu iki fon TAMAMEN "nakit" residual'e
düşüyordu (fiyatlandırılamıyor, %0 getiri VARSAYILIYORDU) -- oysa ikisi
de GERÇEK, GÜNLÜK NAV'ı olan TEFAS fonları (`tefas.fetch_fund_returns()`
ile CANLI doğrulandı: HMV d1=-%0,70, T3B d1=+%2,00 -- fvt.com.tr'nin
ekran görüntüsündeki -%0,70/+%2,00 ile BİREBİR eşleşti). `_FUND_TICKER_RE`
artık HEM tire+isim HEM tek başına (T3B gibi harf+rakam karışık) kodları
kabul ediyor. CANLI doğrulandı: TLY'nin kapsanan ağırlığı (covered_weight)
artık %81,83'ten ~%87,5'e çıkıyor.
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
# "PCS-PUSULA..." (PHE) gibi kurucu adı EKLENMİŞ kodları HEM "HMV"/"T3B"
# (TLY, 2026-08-06 kullanıcı raporu -- bkz. modül üst notu Kullanıcı
# Kararı #9) gibi TEK BAŞINA (tire/isim OLMADAN) yazılan kodları KAPSAR --
# ikinci biçim ÖNCEDEN eşleşmiyordu, bu yüzden TLY'nin "DİĞER" bölümü
# (HMV+T3B, %5,63 ağırlık) grup toplamı %0 çıkıp TAMAMEN reddediliyordu.
_FUND_TICKER_RE = re.compile(r"^[A-Z0-9]{2,6}(-.*)?$")
_ISIN_RE = re.compile(r"^TR[A-Z0-9]{10,11}$")
_PURE_INT_RE = re.compile(r"^\d{5,10}$")  # borsa sözleşme no gibi virgülsüz tam sayı -- atlanır
# TÜREV artık AYRIŞTIRILMIYOR (bkz. modül üst notu, Kullanıcı Kararı #3) ama
# HİSSE/DİĞER bölümlerinin TÜREV başlığına TAŞMAMASI için bölüm SINIRI
# (terminator) olarak listede TUTULUYOR.
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
# (1pt yeterli); DİĞER (fon) bölümünde ~2pt fark GÖZLEMLENDİ -- tek bir ortak
# tolerans HİSSE'de YANLIŞ satır birleşmelerine yol açtığı için (CANLI
# gözlemlendi) bölüm bazında AYRI tutuluyor.
_PARSEABLE_SECTIONS = (
    ("HİSSE SENETLERİ", "hisse", _STOCK_TICKER_RE, 1, _ISIN_RE),
    ("DİĞER", "fon", _FUND_TICKER_RE, 3, _ISIN_RE),
)
_GROUP_TOTAL_TOLERANCE = Decimal("3.0")  # grup toplamı %100'den en fazla bu kadar sapabilir
# CANLI gözlem (2026-08-05, PBR): bir hissenin (DSTKF) ikinci lot satırı
# sayfa sınırında farklı bir 'TL' işareti geometrisiyle basılmış, bu
# yüzden grup toplamı %97,60 (eskiden %2,0 toleransla REDDEDİLİYORDU).
# %3,0'a genişletmek bu ve benzer sayfa-sınırı kayıplarını (küçük, tek
# satırlık) veri ATMADAN kabul ediyor -- gerçekten bozuk ayrıştırmalar
# (ör. AEV'nin %13,87'si) YİNE DE bu toleransın ÇOK dışında kalıp
# reddedilmeye devam ediyor.
# Bölümler AYRI AYRI geçerliyken BİRLİKTE %100'ü bu kadara kadar aşarsa
# (Kullanıcı Kararı #4, bkz. `_parse_portfolio_pdf`) veri ATILMAZ,
# ORANTISAL olarak yeniden ölçeklenir -- CANLI gözlemlenen iki durumdan
# (PUK %103,23, PHE Temmuz %103,68) daha geniş bir pay bırakır.
_MAX_OVERAGE_FOR_RESCALE = Decimal("8.0")


# --- Hata sınıfları -----------------------------------------------------


class KapFundPortfolioError(Exception):
    """KAP fon portföy fetcher'ı için taban hata sınıfı."""


class FundNotFoundError(KapFundPortfolioError):
    """Verilen fon kodu KAP arama sonuçlarında (searchType='F') bulunamadı."""


# --- Veri modelleri -----------------------------------------------------


@dataclass(frozen=True)
class Holding:
    instrument_type: str  # "hisse" | "fon" (fon-içinde-fon) | "nakit" (residual sözde-satır, bkz. modül üst notu)
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
    decimal_parser=_to_decimal,
) -> list[Holding]:
    """Bir bölümün (HİSSE SENETLERİ / DİĞER / TÜREV) kelime listesini
    satır satır ayrıştırır, her benzersiz (ticker, kimlik) için lot'ları
    toplayarak NET ağırlığı hesaplar. `id_re` HİSSE/DİĞER'de gerçek ISIN
    (`_ISIN_RE`), TÜREV'de kontrat kodu (`_CONTRACT_CODE_RE`) arar.
    `decimal_parser`: CANLI gözlem (2026-08-05, IJC -- Kullanıcı Kararı
    #6) bazı fonlar AYNI 8-kolonlu format 1 GEOMETRİSİNİ kullanırken
    sayıları ULUSLARARASI (nokta ondalık) yazıyor -- `_parse_portfolio_pdf`
    Türkçe (`_to_decimal`) yorum başarısız olursa `_to_decimal_international`
    ile YENİDEN dener (bkz. o fonksiyonun çağrı yeri).

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

        group_pct = decimal_parser(first_line[5]["text"])
        weight_pct = decimal_parser(first_line[7]["text"])
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


# --- PDF ayrıştırma (İKİNCİ ŞABLON -- "A) HİSSE SENETLERİ" harfli liste) ----------------------------------------


# 🚨 KULLANICI KARARI #5 (2026-08-05, hedef 15 fon teşhisinde bulundu):
# LTL/PBR/DFI/SNY/RSK/YIT/IJC'nin `_PARSEABLE_SECTIONS` (yukarısı, PHE/
# TLY şablonu) ile 0 holding döndürmesi ÜZERİNE ilk turda "farklı PMC
# şablonları var, tek oturumda çözülemez" denip VAZGEÇİLMİŞTİ. Kullanıcı
# BUNA İTİRAZ ETTİ ("başkaları bu fonları da analiz edebiliyor, sen de
# yapabilirsin") -- CANLI incelemede (page.extract_text() TAM sayfa,
# ilk turda SADECE ilk 1000 karakter bakılmıştı, kök hata BUYDU) DFI/
# SNY/RSK'nin GERÇEKTEN hisse verisi TAŞIDIĞI görüldü, sadece TAMAMEN
# FARKLI bir tabloda:
#   "3- FON PORTFÖY DEĞERİ TABLOSU" başlığı altında "A) HİSSE SENETLERİ",
#   "B) VARANTLAR", "C) DEVLET TAHVİLİ VE BONOLAR" ... şeklinde HARFLİ
#   bir kategori listesi var (format 1'in "HİSSE SENETLERİ"/"DİĞER"/
#   "GRUP TOPLAMI" adlı başlıklarından TAMAMEN FARKLI). Satır başına
#   TEK bir yüzde kolonu var (format 1'in 3 kolonundan farklı -- CANLI
#   doğrulandı: RSK'de bu kolon zaten FON TOPLAM DEĞERİ'ne göre, "GRUP
#   TOPLAMI"na göre DEĞİL, `Holding.weight_pct` ile AYNI anlam). Sayılar
#   ULUSLARARASI (nokta ondalık, virgül binlik) yazılıyor -- format 1'in
#   Türkçe (virgül ondalık) TERSİ, `_to_decimal_international()` ile
#   AYRI ayrıştırılır. Öz-doğrulama farklı: "TOPLAM:" satırının KENDİ
#   nominal+rayiç toplamları, satır satır toplanan nominal+rayiç
#   değerleriyle KARŞILAŞTIRILIR (RSK'de CANLI doğrulandı: rakam rakam
#   BİREBİR eşleşti) -- format 1'deki "grup %100'e yakın mı" yerine.
#
# Bu ikinci şablon SADECE format 1 (`_PARSEABLE_SECTIONS`) HİÇ hisse
# holding'i DÖNDÜRMEDİYSE bir FALLBACK olarak denenir (bkz.
# `_parse_portfolio_pdf`) -- format 1 zaten bir şeyler bulduysa (PHE/
# TLY/PUK/KHA gibi) bu ikinci denemeye HİÇ gerek yoktur.
_LETTERED_SECTION_MARKER_RE = re.compile(r"^[A-Z]\)$")
_LETTERED_NUMBER_RE = re.compile(r"^-?[\d,]+\.\d{2}%?$")
_LETTERED_NUMBER_FRAGMENT_RE = re.compile(r"^-?[\d,.]+%?$")  # kesirli/tam sayi FRAGMANLARINI da yakalar (isim SUTUNU x0'i fondan foNA KAYDIGI icin)
_LETTERED_HEADER_SKIP_WORDS = frozenset({"HİSSE", "SENETLERİ", "TOPLAM:", "TOPLAM"})


def _to_decimal_international(text: str) -> Decimal | None:
    """`_to_decimal()`'in ULUSLARARASI (virgül binlik, nokta ondalık)
    biçim karşılığı -- ikinci şablonun sayı gösterimi Türkçe (format 1)
    ile TAM TERS (bkz. modül üst notu, Kullanıcı Kararı #5)."""
    try:
        return Decimal(text.rstrip("%").replace(",", ""))
    except (InvalidOperation, ValueError):
        return None


def _extract_lettered_hisse_words(pdf: "pdfplumber.PDF") -> list[dict]:
    """'A) HİSSE SENETLERİ' ile bir SONRAKİ harfli başlık ('B)' vb.)
    arasındaki kelimeleri toplar -- bu başlık YOKSA (fon bu ikinci
    şablonu KULLANMIYORSA) boş liste döner."""
    PAGE_OFFSET = 100_000
    collected: list[dict] = []
    in_section = False

    for page_index, page in enumerate(pdf.pages):
        words = page.extract_words()
        for i, word in enumerate(words):
            if not in_section:
                if (
                    word["text"] == "A)"
                    and i + 2 < len(words)
                    and words[i + 1]["text"] == "HİSSE"
                    and words[i + 2]["text"] == "SENETLERİ"
                ):
                    in_section = True
                continue
            if _LETTERED_SECTION_MARKER_RE.match(word["text"]):
                in_section = False
                break
            adjusted = dict(word)
            adjusted["top"] = word["top"] + page_index * PAGE_OFFSET
            collected.append(adjusted)
        if not in_section and collected:
            break

    return collected


def _parse_lettered_hisse_rows(words: list[dict]) -> list[Holding]:
    """`_extract_lettered_hisse_words()`'ün ürettiği kelime listesini
    satır satır ayrıştırır. Öz-doğrulama (Kural 3): satır satır toplanan
    nominal + rayiç değerleri, PDF'in KENDİ 'TOPLAM:' satırındaki iki
    toplamla (±%0,5 bağıl tolerans, yuvarlama payı) eşleşmelidir --
    tutmuyorsa boş liste döner (bkz. modül üst notu)."""
    if not words:
        return []

    row_starts = [
        i
        for i, w in enumerate(words)
        if 50 <= w["x0"] <= 110 and w["text"] not in _LETTERED_HEADER_SKIP_WORDS and _STOCK_TICKER_RE.match(w["text"])
    ]
    if not row_starts:
        return []

    toplam_word = next((w for w in words if w["text"] == "TOPLAM:"), None)
    if toplam_word is None:
        return []
    toplam_numbers = sorted(
        (w for w in words if abs(w["top"] - toplam_word["top"]) < 1 and _LETTERED_NUMBER_RE.match(w["text"])),
        key=lambda w: w["x0"],
    )
    if len(toplam_numbers) != 2:
        return []
    toplam_nominal = _to_decimal_international(toplam_numbers[0]["text"])
    toplam_rayic = _to_decimal_international(toplam_numbers[1]["text"])
    if toplam_nominal is None or toplam_rayic is None:
        return []

    aggregated: dict[str, Decimal] = {}
    names: dict[str, str] = {}
    nominal_sum = Decimal(0)
    rayic_sum = Decimal(0)

    for idx, start_i in enumerate(row_starts):
        start_top = words[start_i]["top"]
        natural_end = words[row_starts[idx + 1]]["top"] if idx + 1 < len(row_starts) else toplam_word["top"]
        end_top = min(natural_end, start_top + _MAX_ROW_SPAN)
        block = [w for w in words if start_top - 1 <= w["top"] < end_top]

        ticker = words[start_i]["text"]
        numeric_fields = sorted(
            (w for w in block if abs(w["top"] - start_top) < 1 and _LETTERED_NUMBER_RE.match(w["text"])),
            key=lambda w: w["x0"],
        )
        if len(numeric_fields) != 3:  # nominal, rayic, yuzde -- baska sayida ise guvenilir ayristiramiyoruz
            continue
        nominal = _to_decimal_international(numeric_fields[0]["text"])
        rayic = _to_decimal_international(numeric_fields[1]["text"])
        weight_pct = _to_decimal_international(numeric_fields[2]["text"])
        if nominal is None or rayic is None or weight_pct is None:
            continue

        # CANLI gözlem (DFI): nominal/rayiç/yüzde kolonlarının x0'i FON'DAN
        # FONA kayabiliyor (RSK'de x0=364+, DFI'de x0=331+) -- bu yüzden
        # isim sütunu SABİT bir x0 üst sınırıyla DEĞİL, sayı GİBİ görünen
        # HER kelimeyi (x0'dan BAĞIMSIZ) dışlayarak ayrıştırılır.
        name_words = [
            w
            for w in block
            if 100 < w["x0"] < 360
            and w["text"] not in _LETTERED_HEADER_SKIP_WORDS
            and not _LETTERED_NUMBER_FRAGMENT_RE.match(w["text"])
        ]
        name_words.sort(key=lambda w: (w["top"], w["x0"]))
        name = " ".join(w["text"] for w in name_words).strip()

        nominal_sum += nominal
        rayic_sum += rayic
        aggregated[ticker] = aggregated.get(ticker, Decimal(0)) + weight_pct
        if name:
            names[ticker] = name

    if not aggregated:
        return []

    # Oz-dogrulama: PDF'in KENDI 'TOPLAM:' satiriyla karsilastir (Kural 3).
    for label, computed, expected in (("nominal", nominal_sum, toplam_nominal), ("rayiç", rayic_sum, toplam_rayic)):
        if expected == 0:
            continue
        relative_diff = abs(computed - expected) / abs(expected)
        if relative_diff > Decimal("0.005"):
            logger.warning(
                "KAP portföy dağılım PDF'inin (harfli şablon) HİSSE SENETLERİ bölümü '%s' toplamı "
                "PDF'in kendi 'TOPLAM:' satırıyla tutmuyor (hesaplanan=%s, PDF=%s) -- ayrıştırma "
                "GÜVENİLİR DEĞİL, boş liste dönüyor (Kural 3).",
                label,
                computed,
                expected,
            )
            return []

    return [
        Holding(instrument_type="hisse", ticker=ticker, name=names.get(ticker, ""), weight_pct=weight)
        for ticker, weight in sorted(aggregated.items(), key=lambda kv: -kv[1])
    ]


def _parse_portfolio_pdf(pdf_bytes: bytes) -> list[Holding]:
    """PDF'teki ayrıştırılabilir bölümleri (`_PARSEABLE_SECTIONS` --
    HİSSE SENETLERİ + DİĞER/fon-içinde-fon) satır satır ayrıştırır. HER
    BÖLÜM kendi grup toplamıyla AYRI AYRI öz-doğrulanır (bkz.
    `_parse_section_rows`) -- bir bölüm güvenilmez çıkarsa SADECE o bölüm
    atlanır, diğerleri yine döner. TÜREV bölümü ARTIK ayrıştırılmıyor
    (bkz. modül üst notu, Kullanıcı Kararı #3) -- ağırlığı diğer nakit/
    alacak/borç kalemleriyle BİRLİKTE residual'a düşer.

    Kalan fark (100 - toplam ağırlık) menkul kıymet OLMAYAN nakit/alacak/
    borç kalemlerini (fonun "IV-FON TOPLAM DEĞERİ TABLOSU"sundaki
    B..G satırları, ARTIK TÜREV'i de İÇEREREK) temsil eder -- bunlar tek
    tek itemize EDİLEMEDİĞİ için TEK bir `instrument_type="nakit"`
    sözde-satırı olarak eklenir (bkz. modül üst notu). ⚠️ Bu residual
    SADECE en az bir gerçek bölüm başarıyla ayrıştırıldıysa eklenir --
    HİÇBİR bölüm ayrıştırılamazsa (`all_holdings` boşsa) residual da
    eklenmez (aksi halde "%100 nakit" gibi YANLIŞ bir izlenim verirdi,
    Kural 3).

    🚨 KULLANICI KARARI #4 (2026-08-05, hedef 15 fon teşhisinde bulundu,
    AYNI GÜN İÇİNDE DÜZELTİLDİ): PUK'ta HİSSE (%93,13) + DİĞER/fon
    (%10,10) toplamı %103,23 çıktı -- HER İKİ bölüm de KENDİ "GRUP
    TOPLAMI" öz-doğrulamasını AYRI AYRI geçmişti (bkz.
    `_parse_section_rows`, ±`_GROUP_TOTAL_TOLERANCE` ile), ama BİRLİKTE
    %100'ü aşıyorlardı. İLK düzeltme (toplam >102 ise TÜM portföyü BOŞ
    döndür) çok AGRESİF çıktı: `scripts/validate_fon_tahmini.py`
    yeniden çalıştırılınca PHE'nin TEMMUZ raporu da %103,68 ile AYNI
    eşiği geçip TAMAMEN ELENDİ -- oysa PHE en TİTİZ doğrulanmış fondu
    (bkz. `src/analysis/fund_estimator.py` üst notu). Kök neden: iki
    AYRI bölümün kendi ±2 toleransı BİRLEŞİNCE (istatistiksel olarak)
    ±4'e kadar BİRİKEBİLİR -- bu, gerçek bir çift-sayım/yanlış-kolon
    hatasından ZORUNLU olarak AYIRT edilemez, sadece TEK bir fonun (ör.
    PUK) hangisi olduğu bu oturumda DOĞRULANAMADI.

    Bu yüzden ARTIK: toplam 100'ü `_GROUP_TOTAL_TOLERANCE` kadar aşan
    AMA `_MAX_OVERAGE_FOR_RESCALE` içinde kalan durumlarda TÜM ağırlıklar
    ORANTISAL olarak 100'e YENİDEN ÖLÇEKLENİR (veri ATILMAZ, sadece
    normalize edilir) -- bu, göreceli katkı oranlarını KORUR ve iki
    bağımsız-doğru bölümün toleranslarının üst üste binmesi durumunda
    veri kaybını ÖNLER. SADECE bu üst sınırı da AŞAN (muhtemelen GERÇEK
    bir ayrıştırma hatası, ör. AEV'nin "fon" bölümünün %13,87 toplaması
    gibi -- ki o zaten KENDİ bölüm-içi kontrolünde YAKALANIR, buraya
    hiç ulaşmaz) durumlarda TÜM portföy boş döner. Her iki durum da
    AÇIKÇA loglanır (Kural 3: sessiz normalize/ret YOK).
    """
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            all_holdings: list[Holding] = []
            for section_start, instrument_type, ticker_re, row_tolerance, id_re in _PARSEABLE_SECTIONS:
                words = _extract_section_words(pdf, section_start)
                if not words:
                    logger.info("PDF'te '%s' bölümü bulunamadı.", section_start)
                    continue
                all_holdings.extend(_parse_section_rows(words, ticker_re, instrument_type, row_tolerance, id_re))

            # Kullanıcı Kararı #5 (bkz. `_parse_lettered_hisse_rows` üst
            # notu): format 1 HİÇ "hisse" holding'i bulamadıysa (bazı
            # fonlar -- DFI/SNY/RSK gibi -- HİÇ "HİSSE SENETLERİ"/"DİĞER"
            # adlı bölüm KULLANMIYOR, bunun yerine "A) HİSSE SENETLERİ"
            # harfli bir liste kullanıyor), İKİNCİ bir şablonla FALLBACK
            # denenir. Format 1 zaten bir şeyler bulduysa (PHE/TLY/PUK/
            # KHA gibi) bu denemeye HİÇ gerek yoktur.
            if not any(h.instrument_type == "hisse" for h in all_holdings):
                lettered_words = _extract_lettered_hisse_words(pdf)
                if lettered_words:
                    all_holdings.extend(_parse_lettered_hisse_rows(lettered_words))

            # Kullanıcı Kararı #6 (2026-08-05, IJC'de bulundu): bazı
            # fonlar format 1'in AYNI 8-kolonlu geometrisini kullanır
            # ama sayıları ULUSLARARASI (nokta ondalık) yazar -- Türkçe
            # yorum group_pct'i YANLIŞ hesaplayıp öz-doğrulamada
            # reddedilir. Format 1 VE harfli fallback İKİSİ DE hiç
            # "hisse" bulamadıysa, AYNI HİSSE SENETLERİ bölümü
            # `_to_decimal_international` ile YENİDEN denenir.
            if not any(h.instrument_type == "hisse" for h in all_holdings):
                hisse_words = _extract_section_words(pdf, "HİSSE SENETLERİ")
                if hisse_words:
                    all_holdings.extend(
                        _parse_section_rows(
                            hisse_words, _STOCK_TICKER_RE, "hisse", 1, _ISIN_RE, decimal_parser=_to_decimal_international
                        )
                    )
    except Exception as exc:  # pdfplumber bozuk/beklenmeyen bir PDF'te cesitli hatalar firlatabilir
        logger.warning("KAP portföy dağılım PDF'i açılamadı/ayrıştırılamadı: %s", exc)
        return []

    if all_holdings:
        total = sum(h.weight_pct for h in all_holdings)
        residual = Decimal(100) - total
        if total > Decimal(100) + _GROUP_TOTAL_TOLERANCE:
            if total <= Decimal(100) + _MAX_OVERAGE_FOR_RESCALE:
                # Bolumler ayri ayri gecerli ama BIRLIKTE hafifce %100'u
                # asiyor (Kullanici Karari #4, DUZELTILMIS) -- veriyi
                # ATMAK yerine ORANTISAL olarak 100'e yeniden olcekle.
                logger.warning(
                    "KAP portföy dağılım PDF'inde ayrıştırılan toplam ağırlık %%100'ü aşıyor (%s) -- "
                    "bölümler ayrı ayrı tutarlı olduğu için TÜM ağırlıklar orantısal olarak 100'e "
                    "yeniden ölçeklendi (veri atılmadı).",
                    total,
                )
                scale = Decimal(100) / total
                all_holdings = [
                    Holding(instrument_type=h.instrument_type, ticker=h.ticker, name=h.name, weight_pct=h.weight_pct * scale)
                    for h in all_holdings
                ]
            else:
                # Asirilik makul bir yeniden-olcekleme ile ACIKLANAMAYACAK
                # kadar buyuk -- muhtemelen gercek bir ayristirma hatasi,
                # TUM portfoy guvenilmez sayilir (Kural 3).
                logger.warning(
                    "KAP portföy dağılım PDF'inde ayrıştırılan toplam ağırlık %%100'ü anlamlı ölçüde "
                    "aşıyor (%s) -- yeniden ölçekleme ile açıklanamayacak kadar büyük bir sapma, "
                    "TÜM portföy boş dönüyor (Kural 3).",
                    total,
                )
                return []
        elif Decimal("0.005") < residual <= Decimal(100):
            all_holdings.append(
                Holding(instrument_type="nakit", ticker=None, name="Nakit ve Diğer Varlıklar (kalan)", weight_pct=residual)
            )
        elif residual < Decimal("-0.5"):
            # 100'ü asan ama tolerans icinde kalan (residual eklenemeyecek
            # kadar negatif ama yukaridaki esikleri gecmeyen) ARA durum --
            # residual EKLENMEZ, mevcut (hafifce sisirilmis) holdings AYNEN
            # doner, durum loglanir (Kural 3: sessiz kalinmaz).
            logger.warning(
                "KAP portföy dağılım PDF'inde ayrıştırılan toplam ağırlık %%100'ü hafifçe aşıyor (%s) "
                "-- residual 'nakit' satırı eklenmedi.",
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
