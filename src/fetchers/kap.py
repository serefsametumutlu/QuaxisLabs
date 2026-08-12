"""KAP (kap.org.tr) sirket bildirimlerini ceken ve onem derecesine gore
siniflandiran modul.

Kesif adiminda (scripts/explore_kap.py) TAVHL ve THYAO icin GERCEK canli
yanitlar incelendi (data/exploration/ altinda saklidir). Bu yanitlardan
dogrulanan gercekler:

- KAP sitesi Next.js ile yeniden yazilmis; eski "memberDisclosureQuery"
  tarzi uc nokta artik YOK. Gercek uc noktalar sitenin derlenmis JS
  bundle'lari taranarak bulundu:

    POST /tr/api/search/combined   {"keyword": "<hisse kodu, kucuk harf>"}
        -> hisse kodunu KAP'in ic uye kimligine (mkkMemberOid) esler.
        "companyOrFunds" kategorisindeki sonuclarda searchType == "C"
        (sirket) olanlar arasinda, cmpOrFundCode (virgulle ayrilmis,
        coklu pay sinifli sirketlerde birden fazla kod icerebilir, orn.
        "krdma,krdmb,krdmd") icinde aranan kod var mi diye kontrol edilir.

    POST /tr/api/disclosure/members/byCriteria
        {"fromDate":"YYYY-MM-DD","toDate":"YYYY-MM-DD","mkkMemberOidList":[oid]}
        -> bildirim listesi. ONEMLI: fromDate/toDate ISO formatinda
        (YYYY-MM-DD) OLMALI ve İKİSİ DE ZORUNLU; DD.MM.YYYY formati veya
        bu alanlarin hic gonderilmemesi HTTP 500 donduruyor (canli
        dogrulandi).

- Donen her satirda iki serbest metin alani var: "subject" (KAP'in resmi
  bildirim konusu/taksonomisi, orn. "Ihale Sureci / Sonucu") ve "summary"
  (sirketin yazdigi somut baslik, orn. "Kuveyt ... Terminal 2 ... Ihalesi").
  Bu modul subject'i KATEGORI, summary'yi BASLIK olarak esler. Daha
  ayrintili bir "ozet" (govde metni) bu liste uc noktasinda YOKTUR --
  onu almak icin PDF detay sayfasini indirip metin cikarmak gerekir, bu
  faz kapsaminda degildir; bu yuzden Disclosure.summary alani baslikla
  ayni metni tasir (bkz. Disclosure.summary docstring'i).

- Bildirim detay sayfasi: https://www.kap.org.tr/tr/Bildirim/{disclosureIndex}

- Turkce buyuk/kucuk harf tuzagi: Python'un standart str.lower() metodu
  'İ' harfini 'i' + COMBINING DOT ABOVE (U+0307) seklinde iki karaktere
  cevirir (locale-bagimsiz Unicode kurali), bu da "İhale".lower() icinde
  duz "ihale" alt dizisinin ARTIK GECMEMESINE sebep olur -- canli veride
  dogrulandi ("İhale Sureci / Sonucu" kategorisi). Bu yuzden anahtar
  kelime eslemesi icin ozel bir _turkish_lower() kullanilir.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

import config

logger = logging.getLogger(__name__)

KAP_BASE = "https://www.kap.org.tr/tr"
SEARCH_ENDPOINT = f"{KAP_BASE}/api/search/combined"
DISCLOSURES_ENDPOINT = f"{KAP_BASE}/api/disclosure/members/byCriteria"
DISCLOSURE_DETAIL_URL_TEMPLATE = f"{KAP_BASE}/Bildirim/{{disclosure_index}}"

# (Faz 16, Derin Kart -- sektör ortalaması) BİST şirketlerinin sektör
# sınıflandırması -- bkz. scripts/explore_kap_sektor.py modül üst notu:
# AYRI bir "sektör API'si" YOKTUR, bu sayfanın kendi HTML'ine (Next.js RSC
# push payload) gömülü olarak gelir, canlı doğrulandı (2026-08-03).
SEKTORLER_URL = "https://kap.org.tr/tr/Sektorler"

# scripts/explore_kap_sektor.py::_FINE_SECTOR_PATTERN ile AYNI -- ince
# ("sectorName") sektör alanlı gömülü şirket nesnelerini yakalar (veri
# sayfanın Next.js RSC push string'i içinde ÇİFT ESCAPED, \" olarak gelir).
_FINE_SECTOR_PATTERN = re.compile(
    r'\{\\"sectorName\\":\\"[^"]*?\\".*?\\"stockCode\\":\\"[^"]*?\\".*?\\"kapTypes\\":\[[^\]]*?\]\}'
)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Referer": f"{KAP_BASE}/",
}

_PUBLISH_DATE_FORMAT = "%d.%m.%Y %H:%M:%S"


# --- Hata siniflari -----------------------------------------------------


class KapError(Exception):
    """KAP fetcher'i icin taban hata sinifi."""


class KapCompanyNotFoundError(KapError):
    """Verilen hisse kodu KAP sirket/fon aramasinda bulunamadi."""


class KapNetworkError(KapError):
    """KAP'a ag seviyesinde ulasilamadi veya yanit beklenmeyen bicimde geldi."""


# --- Onem siniflandirmasi (kural tabanli, LLM'siz) -----------------------------------------------------

IMPORTANCE_HIGH = "yuksek"
IMPORTANCE_LOW = "dusuk"

# Bu kalip listesi kategori (subject) + baslik (summary) metninde aranir;
# herhangi biri gecerse bildirim "yuksek" onem olarak etiketlenir. Liste
# kasitli olarak gorevde verilenlerle sinirli tutuldu (varsayimsal kelime
# eklenmedi); genisletmek gerekirse burasi tek guncelleme noktasidir.
IMPORTANT_KEYWORDS: tuple[str, ...] = (
    "sözleşme",
    "ihale",
    "anlaşma",
    "yatırım",
    "ortaklık",
    "satın alma",
    "birleşme",
    "temettü",
    "pay geri alım",
    "sermaye artırımı",
    "önemli nitelikte işlem",
    "iş ilişkisi",
)

# Bazi anahtar kelimeler Turkce'nin eklemeli yapisi yuzunden ALAKASIZ bir
# kelimenin ICINDE alt dize olarak geciyor (orn. "yatırım" -> "yatırımcı").
# "Yatırımcı Bülteni" (rutin, aylik) TUM sirketlerde en sik goru len KAP
# basligidir; bu yanlis pozitif duzeltilmezse get_top_disclosures() pratikte
# hep rutin bultenlerle dolar (canli TAVHL verisiyle dogrulandi). Eslesme
# kontrolunden ONCE bu alakasiz kelimeler metinden cikarilir.
_KEYWORD_FALSE_POSITIVE_EXCLUSIONS: dict[str, tuple[str, ...]] = {
    "yatırım": ("yatırımcı",),
}


def _turkish_lower(text: str) -> str:
    """Python'un str.lower() metodu 'İ' -> 'i' + COMBINING DOT ABOVE uretir,
    bu da ASCII alt dize aramasini bozar (bkz. modul docstring'i). Bu
    fonksiyon Turkce buyuk I/İ harflerini ASCII-uyumlu kucuk harfe cevirir.
    """
    return text.replace("İ", "i").replace("I", "ı").lower()


def classify_importance(category: str, title: str) -> str:
    """Kategori + baslik metninde IMPORTANT_KEYWORDS'ten biri geciyorsa
    'yuksek', gecmiyorsa (rutin bildirimler: ozel durum aciklamasi genel,
    kayit belgesi, faaliyet raporu, devre kesici duyurulari vb.) 'dusuk'
    doner.
    """
    haystack = _turkish_lower(f"{category} {title}")
    for keyword in IMPORTANT_KEYWORDS:
        keyword_lower = _turkish_lower(keyword)
        cleaned_haystack = haystack
        for exclusion in _KEYWORD_FALSE_POSITIVE_EXCLUSIONS.get(keyword, ()):
            cleaned_haystack = cleaned_haystack.replace(_turkish_lower(exclusion), "")
        if keyword_lower in cleaned_haystack:
            return IMPORTANCE_HIGH
    return IMPORTANCE_LOW


# --- Veri modelleri -----------------------------------------------------


@dataclass(frozen=True)
class CompanyMatch:
    member_oid: str
    name: str
    ticker_codes: tuple[str, ...]


@dataclass(frozen=True)
class Disclosure:
    date: datetime  # tarih (publishDate, DD.MM.YYYY HH:MM:SS -> datetime)
    title: str  # baslik (API "summary" alani -- somut, sirketin yazdigi metin)
    category: str  # kategori (API "subject" alani -- KAP resmi bildirim konusu)
    summary: str  # ozet -- bu API'de ayri bir govde metni yok, title ile AYNIDIR
    url: str
    importance: str  # IMPORTANCE_HIGH | IMPORTANCE_LOW
    is_late: bool
    disclosure_index: int
    stock_codes: str  # bildirimi YAYINLAYAN uyenin kendi kodu (orn. "A1CAP, ACP")
    # Faz 20 (halka arz izahnamesi kesfi): bildirimin KONUSU olan sirket(ler) --
    # bir ARACI KURUM kendi profilinden bir BASKA sirketin (henuz kendi KAP
    # profili/borsa kaydi olmayabilecek bir halka arz adayinin) izahnamesini
    # yayinladiginda `stock_codes` ARACININ kodunu tasir, hedef sirketin kodu
    # SADECE bu alanda (API "relatedStocks") gelir -- CANLI dogrulandi
    # (A1CAP'in KARCL icin yayinladigi izahname: stock_codes="A1CAP, ACP",
    # related_stocks="KARCL, VKY, ZRY"). Varsayilan bos string -- bu alan
    # EKLENMEDEN once olusturulmus cagrilar/testler BOZULMAZ.
    related_stocks: str = ""
    # Faz 20 devamı (2026-08-07): bildirimi YAYINLAYAN KAP üyesinin RESMİ
    # unvanı (API "kapTitle" alanı, örn. "TERA YATIRIM MENKUL DEĞERLER A.Ş.").
    # `fetch_all_disclosures()` (üye kısıtlaması OLMADAN, TÜM üyeleri tarayan
    # tek istek) ile bulunan izahnamelerde "Aracı Kurum" adını göstermek için
    # gerekli -- eski `UNDERWRITER_MEMBERS` sabit listesinden GELMİYOR artık
    # (bkz. kap_ipo.py modül üst notu, o liste ASLA eksiksiz olamıyordu).
    filer_name: str = ""


# --- HTTP katmani -----------------------------------------------------


@retry(
    reraise=True,
    stop=stop_after_attempt(config.HTTP_MAX_RETRIES),
    wait=wait_fixed(config.HTTP_RATE_LIMIT_DELAY_SECONDS),
    retry=retry_if_exception_type(httpx.RequestError),
)
def _post_json(url: str, body: dict) -> object:
    try:
        response = httpx.post(url, json=body, headers=_HEADERS, timeout=config.HTTP_TIMEOUT_SECONDS)
    except httpx.RequestError as exc:
        logger.warning("KAP istegi basarisiz, yeniden denenecek: %s", exc)
        raise

    if response.status_code != 200:
        raise KapNetworkError(f"KAP beklenmeyen HTTP durum kodu dondurdu: {response.status_code}")

    try:
        return response.json()
    except ValueError as exc:
        raise KapNetworkError(
            "KAP yaniti JSON olarak ayristirilamadi (endpoint sema degistirmis olabilir)."
        ) from exc


@retry(
    reraise=True,
    stop=stop_after_attempt(config.HTTP_MAX_RETRIES),
    wait=wait_fixed(config.HTTP_RATE_LIMIT_DELAY_SECONDS),
    retry=retry_if_exception_type(httpx.RequestError),
)
def _get(url: str, params: dict | None = None) -> httpx.Response:
    """`_post_json()` ile AYNI ilke ama GET için -- Faz 20'de bildirim detay
    sayfası/dosya indirme gibi GET-tabanlı uç noktalar için eklendi
    (`kap_fund_portfolio.py`'nin kendi `_get()`'iyle AYNI davranış, tek
    kaynağa taşındı)."""
    try:
        response = httpx.get(url, params=params, headers=_HEADERS, timeout=config.HTTP_TIMEOUT_SECONDS)
    except httpx.RequestError as exc:
        logger.warning("KAP GET isteği başarısız, yeniden denenecek: %s", exc)
        raise
    if response.status_code != 200:
        raise KapNetworkError(f"KAP beklenmeyen HTTP durum kodu döndürdü: {response.status_code}")
    return response


def _unescape_next_js_string(html_text: str) -> str:
    """`kap_fund_portfolio.py`'den TAŞINDI (Faz 20) -- KAP'ın Next.js RSC
    payload'ı JSON'u bir JS string literali İÇİNDE taşıyor, iç JSON'un
    tırnak işaretleri `\\"` olarak escape'lenmiş geliyor."""
    return html_text.replace('\\"', '"').replace("\\\\", "\\")


_ATTACHMENT_RE = re.compile(r'"attachments":\[\{"objId":"([^"]+)","fileName":"([^"]+)"')
_FILE_DOWNLOAD_TEMPLATE = f"{KAP_BASE}/api/file/download/{{obj_id}}"


def fetch_disclosure_attachment_pdf(disclosure_index: int) -> bytes | None:
    """Bir bildirimin detay sayfasından İLK ekli PDF'i indirir -- Faz 17'de
    `kap_fund_portfolio.py` içinde AYNI mantıkla yazılmıştı, Faz 20'de
    (halka arz izahnamesi de AYNI mekanizmayı kullandığı için) buraya da
    eklendi.

    ⚠️ BİLİNÇLİ KÜÇÜK KOD TEKRARI: `kap_fund_portfolio._fetch_attachment_pdf()`
    kasıtlı olarak BURAYA yönlendirilip SİLİNMEDİ -- o modülün testleri
    `kfp._get`'i (bu modülün `kap._get`'İNDEN AYRI bir isim) monkeypatch
    ediyor; tam bir "tek kaynağa taşıma" refactoru o testlerin çoğunu
    (özellikle `test_fetch_latest_portfolio_uctan_uca` gibi tek bir sahte
    `_get` ile 3 farklı URL'i birden yöneten entegrasyon testlerini)
    riske atardı. Fonksiyonun kendisi ~15 satır ve DAVRANIŞ olarak
    BİREBİR aynı -- ikisi de AYNI canlı doğrulanmış mekanizmayı (bildirim
    detay sayfası -> attachments -> file/download) izliyor, formül/mantık
    olarak SAPMA riski yok. Ekli dosya yoksa/PDF değilse None döner
    (Kural 9 -- ikincil bir zenginleştirme, hata FIRLATMAZ)."""
    response = _get(DISCLOSURE_DETAIL_URL_TEMPLATE.format(disclosure_index=disclosure_index))
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


# --- Faaliyet raporu keşfi (docs/spec/spec_veri_tamlik_yol_haritasi.md
# §Faaliyet Raporu / Dipnot Araştırması, "Önerilen somut ilk adım" madde 1)
# ------------------------------------------------------------------------
#
# CANLI DOĞRULANDI (2026-08-12, THYAO, son 365 gün): KAP kategori adı TAM
# OLARAK "Faaliyet Raporu (Konsolide)" -- hem ÜÇ AYLIK "Yönetim Kurulu
# Faaliyet Raporu" bildirimlerini (SPK Seri:II No:14.1 Tebliği formatı,
# yapısal/kısa) HEM DE yıllık "Entegre Faaliyet Raporu" bildirimini (glossy/
# sürdürülebilirlik ağırlıklı, çok daha uzun) AYNI kategoride taşıyor --
# görev talimatının istediği basit "category/title içinde anahtar kelime"
# eşleşmesi (en güncel bildirim seçilir) bu ikisi arasında AYRIM YAPMAZ,
# spec'in kendisi de bunu istemiyor (bkz. spec madde 1: "EN GÜNCEL ilgili
# bildirim").
_ANNUAL_REPORT_KEYWORDS: tuple[str, ...] = ("faaliyet raporu", "yıllık rapor")

# CANLI ÖLÇÜLDÜ (2026-08-12, THYAO): `fetch_disclosures_by_oid()`'a
# days=400 verilince KAP `/api/disclosure/members/byCriteria` uç noktası
# HTTP 500 döndürüyor (muhtemelen sunucu tarafı bir pencere sınırı --
# `fetch_all_disclosures()`'ın 2000 satır kesme sınırından FARKLI bir
# kısıt); days=365 SORUNSUZ çalıştı (90 bildirim, hem üç aylık hem yıllık
# faaliyet raporu KAYDINI kapsadı). Bu yüzden varsayılan pencere 365 gün --
# yaklaşık bir takvim yılı, yıllık raporun (genelde Şubat-Mart'ta yayınlanır)
# HER ZAMAN pencere içinde kalmasını sağlar.
_ANNUAL_REPORT_DISCOVERY_DAYS = 365


def find_latest_annual_report_disclosure(disclosures: list[Disclosure]) -> Disclosure | None:
    """`disclosures` (ZATEN tarihe göre AZALAN sıralı -- bkz.
    `fetch_disclosures_by_oid()`) içinde kategori/başlık metninde
    `_ANNUAL_REPORT_KEYWORDS`'ten biri geçen EN GÜNCEL bildirimi döner;
    hiçbiri eşleşmiyorsa `None` (Kural 3 -- uydurma yapılmaz, çağıran taraf
    -- `src/ai/kar_kaynagi.py` -- bu durumda dürüst bir placeholder ile
    devam eder).

    Saf filtre -- ağa GİTMEZ, sadece VERİLEN bir liste üzerinde çalışır; bu
    yüzden `fetch_latest_annual_report_pdf()`'ten AYRI, tek başına test
    edilebilir bir fonksiyon olarak tutuldu."""
    for d in disclosures:
        haystack = _turkish_lower(f"{d.category} {d.title}")
        if any(keyword in haystack for keyword in _ANNUAL_REPORT_KEYWORDS):
            return d
    return None


def fetch_latest_annual_report_pdf(
    ticker: str, days: int = _ANNUAL_REPORT_DISCOVERY_DAYS
) -> tuple[Disclosure, bytes] | None:
    """`fetch_disclosures()` + `find_latest_annual_report_disclosure()` +
    `fetch_disclosure_attachment_pdf()`'i BİRLEŞTİREN tek bir yardımcı --
    YENİ bir mimari bileşen DEĞİL, üç MEVCUT fonksiyonun birleşimi (spec
    madde 1: "bu, MEVCUT iki fonksiyonun BİRLEŞTİRİLMESİDİR").

    Uygun bir bildirim BULUNAMAZSA veya bulunan bildirimin eki PDF
    DEĞİLSE/YOKSA `None` döner (Kural 3 -- hata FIRLATILMAZ, çağıran taraf
    dürüst bir placeholder ile devam eder).

    Hatalar:
        KapCompanyNotFoundError / KapNetworkError: `fetch_disclosures()` ile AYNI
        (bunlar GERÇEK ağ/şirket-bulunamadı hatalarıdır, yutulmaz)."""
    disclosures = fetch_disclosures(ticker, days=days)
    target = find_latest_annual_report_disclosure(disclosures)
    if target is None:
        logger.info("%s icin son %s gunde faaliyet raporu/yillik rapor bildirimi bulunamadi.", ticker, days)
        return None

    pdf_bytes = fetch_disclosure_attachment_pdf(target.disclosure_index)
    if pdf_bytes is None:
        logger.info(
            "%s faaliyet raporu bildirimi (idx=%s) icin ekli PDF bulunamadi.", ticker, target.disclosure_index
        )
        return None
    return target, pdf_bytes


def search_company_by_name(query: str) -> list[CompanyMatch]:
    """`search_company()`'nin serbest-metin (tam ticker eşleşmesi GEREKMEYEN)
    varyantı -- Faz 20: halka arza aracılık eden kurumların KAP oid'ini
    kendi TİCKER kodlarını EZBERE bilmeden (Kural 3: uydurma yapılmaz),
    kurum ADIYLA çözmek için. AYNI `SEARCH_ENDPOINT`i kullanır, SADECE
    `searchType=='C'` (şirket) sonuçlarını döner -- `search_company()` ile
    AYNI filtre, sadece "TEK bir tam eşleşme ZORUNLU" kısıtı KALDIRILDI
    (birden fazla veya sıfır sonuç dönebilir, çağıran taraf seçer/doğrular).
    """
    payload = _post_json(SEARCH_ENDPOINT, {"keyword": query.strip()})
    if not isinstance(payload, list):
        raise KapNetworkError("KAP arama yanıtı beklenmeyen biçimde (liste değil).")

    companies = next((c.get("results", []) for c in payload if c.get("category") == "companyOrFunds"), [])
    return [
        CompanyMatch(
            member_oid=row["memberOrFundOid"],
            name=row.get("searchValue", ""),
            ticker_codes=tuple((row.get("cmpOrFundCode") or "").split(",")),
        )
        for row in companies
        if row.get("searchType") == "C"
    ]


def _parse_sector_map(html_text: str) -> dict[str, str]:
    """kap.org.tr/tr/Sektorler sayfasının HTML'inden (Next.js RSC push
    payload'ına ÇİFT ESCAPED gömülü JSON nesnelerinden) ticker -> ince
    sektör adı haritasını çıkarır -- SAF ayrıştırma, ağ erişimi YOK (bkz.
    scripts/explore_kap_sektor.py modül üst notu, canlı doğrulandı)."""
    sector_map: dict[str, str] = {}
    for match in _FINE_SECTOR_PATTERN.findall(html_text):
        unescaped = match.replace('\\"', '"')
        try:
            obj = json.loads(unescaped)
        except json.JSONDecodeError:
            continue
        sector = obj.get("sectorName")
        if not sector:
            continue
        for code in (obj.get("stockCode") or "").split(","):
            code = code.strip()
            if code:
                sector_map[code] = sector
    return sector_map


@retry(
    reraise=True,
    stop=stop_after_attempt(config.HTTP_MAX_RETRIES),
    wait=wait_fixed(config.HTTP_RATE_LIMIT_DELAY_SECONDS),
    retry=retry_if_exception_type(httpx.RequestError),
)
def fetch_sector_map() -> dict[str, str]:
    """TÜM BIST şirketleri için ticker -> ince sektör adı (KAP'ın kendi
    büyük harfli yazımıyla, örn. "ULAŞTIRMA VE DEPOLAMA") döner.

    ⚠️ Bu TEK istek ~640 şirketin TAMAMINI döner (bkz.
    scripts/explore_kap_sektor.py) -- bu yüzden pipeline.py'nin ana
    (tek-ticker) akışından HER SEFERİNDE ÇAĞRILMAZ; ayrı, zamanlanmış bir
    süreçte (scripts/refresh_sector_cache.py, refresh_takvim_cache.py ile
    AYNI ilke) çağrılıp DB'ye toplu yazılır. Faz 16.5'ten itibaren (kullanıcı
    raporu: normal bot kullanımıyla eklenen yeni şirketlerin sektörü hiç
    dolmuyordu) `pipeline._ensure_sector_populated()` da bunu çağırır --
    AMA SADECE ilgili şirketin `sector` alanı hâlâ `None` ise (yani yeni
    eklenmiş/hiç senkronize edilmemiş bir şirket), rutin/tekrarlanan
    sorgularda TEKRAR ÇAĞRILMAZ (Kural 9: yardımcı veri ana boru hattını
    bloklamaz, hata olursa sessizce atlanır).

    SADECE BIST kapsar -- NASDAQ şirketleri için bu kaynak KULLANILAMAZ.

    Hatalar:
        KapNetworkError: Ağ hatası veya beklenmeyen yanıt biçimi.
    """
    try:
        response = httpx.get(SEKTORLER_URL, headers=_HEADERS, timeout=config.HTTP_TIMEOUT_SECONDS, follow_redirects=True)
    except httpx.RequestError as exc:
        logger.warning("KAP Sektörler sayfası isteği başarısız, yeniden denenecek: %s", exc)
        raise

    if response.status_code != 200:
        raise KapNetworkError(f"KAP Sektörler sayfası beklenmeyen HTTP durum kodu döndürdü: {response.status_code}")

    response.encoding = "utf-8"
    sector_map = _parse_sector_map(response.text)

    if not sector_map:
        raise KapNetworkError(
            "KAP Sektörler sayfasından hiçbir şirket ayrıştırılamadı -- sayfanın iç yapısı değişmiş olabilir."
        )
    return sector_map


# --- Faz 2 (docs/spec/spec_sektor_evren.md) -- ortak sektör taksonomisi --------


# Ortak 11-grup üst-sektör taksonomisi (GICS'in sadeleştirilmiş hali, spec
# "Ortak üst-sektör taksonomisi" bölümü BİREBİR) -- hem BİST (KAP ince
# sektör) hem NASDAQ (SIC kodu) bu KAPALI kümeye eşlenir.
UST_SEKTOR_DEGERLERI: tuple[str, ...] = (
    "Enerji",
    "Ana Metaller ve Madencilik",
    "Sanayi",
    "Tüketici (Döngüsel)",
    "Tüketici (Temel)",
    "Sağlık",
    "Finans",
    "Teknoloji",
    "İletişim",
    "Kamu Hizmetleri",
    "Gayrimenkul/GYO",
)

# KAP'ın kap.org.tr/tr/Sektorler sayfasından canlı çekilen 48 benzersiz ince
# sektör adının ("sectorName", Company.sector) ortak üst-sektöre eşlemesi --
# spec "KAP → Üst-Sektör Eşleme Tablosu" BİREBİR (tahmine dayalı DEĞİL,
# sayfadan türetildi). Yeni bir KAP kategorisi (nadir) bu sözlükte YOKSA
# ust_sektor=None döner (uydurma YAPILMAZ, Kural 3) -- bkz. ust_sektor_for_kap().
KAP_SEKTOR_TO_UST_SEKTOR: dict[str, str] = {
    "TARIM VE HAYVANCILIK AVCILIK VE İLGİLİ HİZMET FAALİYETLERİ": "Tüketici (Temel)",
    "BALIKÇILIK VE SU ÜRÜNLERİ": "Tüketici (Temel)",
    "HAM PETROL VE DOĞAL GAZ ÇIKARTILMASI": "Enerji",
    "KÖMÜR VE LİNYİT MADENCİLİĞİ": "Enerji",
    "METAL CEVHERİ MADENCİLİĞİ": "Ana Metaller ve Madencilik",
    "DİĞER MADENCİLİK VE TAŞ OCAKÇILIĞI": "Ana Metaller ve Madencilik",
    "GIDA, İÇECEK VE TÜTÜN": "Tüketici (Temel)",
    "TEKSTİL, GİYİM EŞYASI VE DERİ": "Tüketici (Döngüsel)",
    "ORMAN ÜRÜNLERİ VE MOBİLYA": "Tüketici (Döngüsel)",
    "KAĞIT VE KAĞIT ÜRÜNLERİ BASIM": "Ana Metaller ve Madencilik",
    "YAYIMCILIK": "İletişim",
    "TELEKOMÜNİKASYON": "İletişim",
    # KAP bu kategoride rafineri/ilaç/kimya şirketlerini AYNI kovaya koyuyor
    # -- varsayılan (bu üç GICS sektöründen en yaygını) korunur, bilinen
    # istisnalar KAP_TICKER_SECTOR_OVERRIDES ile elle düzeltilir (bkz. spec
    # "Ticker-düzeyi override (KAP)" notu).
    "KİMYA İLAÇ PETROL LASTİK VE PLASTİK ÜRÜNLER": "Ana Metaller ve Madencilik",
    "TAŞ VE TOPRAĞA DAYALI": "Ana Metaller ve Madencilik",
    "ANA METAL SANAYİ": "Ana Metaller ve Madencilik",
    "METAL EŞYA MAKİNE ELEKTRİKLİ CİHAZLAR VE ULAŞIM ARAÇLARI": "Sanayi",
    "DİĞER İMALAT SANAYİİ": "Sanayi",
    "ELEKTRİK GAZ VE BUHAR": "Kamu Hizmetleri",
    "İNŞAAT VE BAYINDIRLIK İŞLERİ": "Sanayi",
    "TOPTAN TİCARET": "Tüketici (Döngüsel)",
    "PERAKENDE TİCARET": "Tüketici (Döngüsel)",
    "ULAŞTIRMA VE DEPOLAMA": "Sanayi",
    "KONAKLAMA": "Tüketici (Döngüsel)",
    "YİYECEK VE İÇECEK HİZMETLERİ": "Tüketici (Döngüsel)",
    "SEYAHAT ACENTESİ, TUR OPERATÖRÜ VE DİĞER REZERVASYON HİZMETLERİ İLE İLGİLİ FAALİYETLER": "Tüketici (Döngüsel)",
    "BANKALAR": "Finans",
    "ARACI KURUMLAR": "Finans",
    "SİGORTA ŞİRKETLERİ": "Finans",
    "FİNANSAL KİRALAMA VE FAKTORİNG ŞİRKETLERİ": "Finans",
    "FİNANSMAN ŞİRKETLERİ": "Finans",
    "VARLIK YÖNETİM ŞİRKETLERİ": "Finans",
    "MENKUL KIYMET YATIRIM ORTAKLIKLARI": "Finans",
    "GİRİŞİM SERMAYESİ YATIRIM ORTAKLIKLARI": "Finans",
    "HOLDİNGLER VE YATIRIM ŞİRKETLERİ": "Finans",
    "GAYRİMENKUL FAALİYETLERİ": "Gayrimenkul/GYO",
    "GAYRİMENKUL YATIRIM ORTAKLIKLARI": "Gayrimenkul/GYO",
    "KİRALAMA VE LEASING FAALİYETLERİ": "Finans",
    "BÜRO YÖNETİMİ, BÜRO DESTEĞİ VE DİĞER ŞİRKET DESTEK FAALİYETLERİ": "Sanayi",
    "BİLGİ HİZMET FAALİYETLERİ": "Teknoloji",
    "BİLİŞİM": "Teknoloji",
    "HUKUK VE MUHASEBE FAALİYETLERİ": "Sanayi",
    "MİMARLIK VE MÜHENDİSLİK FAALİYETLERİ; TEKNİK MUAYENE VE ANALİZ": "Sanayi",
    "REKLAMCILIK VE PAZAR ARAŞTIRMASI": "İletişim",
    "İNSAN SAĞLIĞI VE SOSYAL HİZMETLER": "Sağlık",
    "SAVUNMA": "Sanayi",
    "SPOR FAALİYETLERİ EĞLENCE VE OYUN FAALİYETLERİ": "Tüketici (Döngüsel)",
    "SPOR EĞLENCE BOŞ ZAMANLARI DEĞERLENDİRME HİZMETLERİ": "Tüketici (Döngüsel)",
    "YARATICI SANATLAR GÖSTERİ SANATLARI VE EĞLENCE FAALİYETLERİ": "İletişim",
}

# Ticker-düzeyi override (spec "Ticker-düzeyi override (KAP)" notu BİREBİR):
# TUPRS "KİMYA İLAÇ PETROL LASTİK VE PLASTİK ÜRÜNLER" ince kategorisinde ama
# GERÇEK iş modeli rafineri (Enerji) -- varsayılan eşlemeden İSTİSNA.
#
# docs/spec/spec_sektor_inceltme.md (2026-08-12, CANLI kap_sektor_map.json
# doğrulamalı) -- İKİ YENİ istisna, TUPRS ile AYNI desen:
#
# TAVHL (Bulgu 2, öncelik YÜKSEK): KAP'ta "HOLDİNGLER VE YATIRIM ŞİRKETLERİ"
# ince kategorisinde (-> ust_sektor="Finans"), TAV Havalimanları Holding'in
# GERÇEK iş modeli TEK-iş (havalimanı işletmeciliği) -- hukuki KABUK
# (holding yapısı) ile GERÇEK iş modeli arasındaki fark burada somutlaşıyor
# (KCHOL/SAHOL'un AKSİNE, onlar GERÇEKTEN çok-sektörlü). "Sanayi"ye taşınır
# (THYAO/PGSUS/CLEBI ile AYNI havuz -- Bulgu 1'in "havacılık ekosistemi"
# üçlüsü, istatistiksel n büyür).
#
# DEVA/GENKM/SANFM/ONCSM/MEDTR (spec "Benzer potansiyel iyileştirmeler"
# madde 2, GERÇEK istatistiksel kazanım -- n=5, sektor-siniflandirma skill
# madde 1'in n≥5 eşiğini TAM karşılar): "KİMYA İLAÇ PETROL LASTİK VE
# PLASTİK ÜRÜNLER" ince kategorisi kimyasal/petrol/lastik/plastik
# ÜRETİCİLERİ (AKSA, PETKM, BRISA gibi -- GERÇEKTEN "Ana Metaller ve
# Madencilik") ile ilaç ÜRETİCİLERİ'ni (bu 5 şirket) AYNI kovada tutuyor --
# GICS'te ilaç üretimi AÇIKÇA "Sağlık" (Health Care) sektörüdür.
KAP_TICKER_SECTOR_OVERRIDES: dict[str, str] = {
    "TUPRS": "Enerji",  # rafineri — KAP'ın "Kimya İlaç Petrol..." ince kategorisi
    # bu şirketi ilaç/kimya şirketleriyle aynı kovaya koyuyor
    "TAVHL": "Sanayi",  # TAV Havalimanları Holding — hukuki kabuk "Holding", gerçek iş tek-kollu havalimanı işletmeciliği
    "DEVA": "Sağlık",  # Deva Holding — ilaç üreticisi
    "GENKM": "Sağlık",  # Gen İlaç — ilaç üreticisi
    "SANFM": "Sağlık",  # Sanifarma — ilaç üreticisi
    "ONCSM": "Sağlık",  # Oncosem Onkoloji — ilaç üreticisi
    "MEDTR": "Sağlık",  # Meditera — ilaç üreticisi
}

# docs/spec/spec_sektor_inceltme.md "Seçenek B" (görsel-amaçlı alt-etiket,
# ÖNERİLEN çözüm) -- THYAO/PGSUS/CLEBI/TAVHL kullanıcı gözünde "aynı
# sektör" olarak algılanıyor ama n=4 (sektor-siniflandirma skill madde 1'in
# n≥5 kısıtının ALTINDA) -- istatistiksel sektöre-göreli karşılaştırma
# (ust_sektor, `valuation.py`'nin peer havuzu) BU sözlükten ETKİLENMEZ,
# HİÇBİR sorguya karışmaz (SADECE görüntüleme amaçlı, Kural 3: n=4 ile
# istatistik ÜRETİLMEZ, sadece İSİMLENDİRME iyileştirilir).
#
# DB ŞEMASI/migration/refresh_universe.py'ye BİLEREK DOKUNULMADI (spec'in
# önerdiği `Company.ekosistem_etiketi` sütunu YERİNE, TUPRS/TAVHL'deki
# `KAP_TICKER_SECTOR_OVERRIDES` deseniyle AYNI ilkeyle SAF ticker->etiket
# statik sözlüğü kullanılır) -- gerekçe: (a) statik/ticker-anahtarlı bir
# eşleme için DB'de ayrı bir sütun/migration/senkronizasyon adımı GEREKMEZ
# (aynı bilginin iki kopyası, biri kod-içi biri DB'de, senkron kalma riski
# taşırdı), (b) bu turda DB şemasına dokunmama kısıtı (arka planda süren
# iki uzun tarama süreciyle REKABET ETMEME) uygulandı. Dashboard/detay
# sayfası render katmanı (SAF I/O'suz okuma) bu sözlüğü DOĞRUDAN import
# eder (bkz. src/render/dashboard.py, src/render/company_detail.py).
KAP_TICKER_EKOSISTEM_ETIKETI: dict[str, str] = {
    "THYAO": "Havacılık",
    "PGSUS": "Havacılık",
    "CLEBI": "Havacılık",
    "TAVHL": "Havacılık",
}


def ekosistem_etiketi_for_ticker(ticker: str) -> str | None:
    """`KAP_TICKER_EKOSISTEM_ETIKETI`'nin ticker normalizasyonlu sarmalayıcısı
    -- görsel-amaçlı, İSTATİSTİKSEL `ust_sektor`'e ASLA karışmaz (bkz. sözlük
    üstü not). Bilinmeyen ticker için `None` döner (Kural 3, uydurma etiket
    YOK)."""
    return KAP_TICKER_EKOSISTEM_ETIKETI.get(ticker.strip().upper())


def ust_sektor_for_kap(ticker: str, fine_sector: str) -> str | None:
    """Ticker + KAP ince sektör adından ortak üst-sektörü türetir.

    Kural sırası (spec "Kural sırası" ile aynı ilke): `KAP_TICKER_SECTOR_OVERRIDES`
    içinde ticker varsa o KULLANILIR; yoksa `KAP_SEKTOR_TO_UST_SEKTOR[fine_sector]`
    denenir; ikisi de yoksa None döner (Kural 3 -- uydurma YAPILMAZ, kart
    "N/A" gösterir; bkz. spec "Kenar durumlar": KAP ince sektörü bilinmeyen/
    yeni bir kategoriyse).
    """
    override = KAP_TICKER_SECTOR_OVERRIDES.get(ticker.strip().upper())
    if override is not None:
        return override
    return KAP_SEKTOR_TO_UST_SEKTOR.get(fine_sector)


# KAP ince sektöründen ANALİZ ÖNCESİ (financial_group henüz bilinmeden)
# KESİN olarak türetilebilen sirket_turu değerleri -- spec "Önemli asimetri"
# notu: bu 4 kategori KAP'ta "zaten ayrık" (başka hiçbir ince kategoriyle
# karışmaz). Diğer Finans/Gayrimenkul-GYO üst-sektöründeki ince kategoriler
# (aracı kurum, holding, leasing, MKYO, girişim sermayesi YO, gayrimenkul
# faaliyetleri) buraya KASITLI OLARAK eklenmedi -- bkz. sirket_turu_on_tahmin_from_kap().
_KAP_FINE_SECTOR_TO_SIRKET_TURU_KESIN: dict[str, str] = {
    "BANKALAR": "banka",
    "SİGORTA ŞİRKETLERİ": "sigorta",
    "FİNANSMAN ŞİRKETLERİ": "finansman",
    "GAYRİMENKUL YATIRIM ORTAKLIKLARI": "gyo",
}

# sirket_turu ön-tahmininin "sanayi" VARSAYILAMAYACAĞI üst-sektörler (spec:
# "sanayi = ... KAP ince sektör Finans/Gayrimenkul/GYO grubunda DEĞİLSE").
_SIRKET_TURU_ONTAHMIN_DISI_UST_SEKTORLER = frozenset({"Finans", "Gayrimenkul/GYO"})


def sirket_turu_on_tahmin_from_kap(fine_sector: str) -> str | None:
    """Spec "Şirket türü tanımı ve kaynağı" tablosunun BİST kolonu, ANALİZ
    ÖNCESİ (evren-doldurma anında, financial_group henüz `None` olabilir)
    ön-tahmini -- bkz. spec "Önemli asimetri" notu: `financial_group`
    dolduğunda (analiz sonrası) KESİN değer bu ön-tahminin ÜZERİNE YAZILIR
    (bu fonksiyon o yeniden-türetmeyi YAPMAZ, Faz 3'ün pipeline entegrasyonu
    konusudur -- bu spec sadece ön-tahmin fonksiyonunu sağlar).

    - KAP ince sektör BANKALAR/SİGORTA ŞİRKETLERİ/FİNANSMAN ŞİRKETLERİ/
      GAYRİMENKUL YATIRIM ORTAKLIKLARI ise -> doğrudan (KAP'ta zaten ayrık)
      karşılık gelen değer -- analiz gerekmeden KESİNDİR.
    - Üst-sektörü Finans/Gayrimenkul-GYO OLAN ama yukarıdaki 4 kategoriden
      biri OLMAYAN ince sektörler (aracı kurum, holding, leasing, MKYO,
      girişim sermayesi YO, gayrimenkul faaliyetleri) -> None: KAP ince
      sektöründen banka/sigorta/finansman ayrımı YAPILAMAZ (spec: bu ayrım
      SADECE financial_group ile KESİNLEŞİR), uydurma yapılmaz (Kural 3).
    - Aksi halde (üst-sektör Finans/GYO DIŞINDA) -> 'sanayi' ön-tahmini.
    - KAP ince sektörü hiç tanınmıyorsa (KAP_SEKTOR_TO_UST_SEKTOR'da yok) -> None.
    """
    kesin = _KAP_FINE_SECTOR_TO_SIRKET_TURU_KESIN.get(fine_sector)
    if kesin is not None:
        return kesin
    ust_sektor = KAP_SEKTOR_TO_UST_SEKTOR.get(fine_sector)
    if ust_sektor is None:
        return None
    if ust_sektor in _SIRKET_TURU_ONTAHMIN_DISI_UST_SEKTORLER:
        return None
    return "sanayi"


def normalize_ticker(ticker: str) -> str:
    """'THYAO.IS' -> 'thyao', 'BIMAS' -> 'bımas' seklinde KAP aramasinin
    bekledigi kucuk harfli koda cevirir.

    CANLI HATA (kullanıcı raporu, 2026-08-02 — Faz 13 takvim doğrulaması):
    KAP'in arama API'si "I" harfini TÜRKÇE kurala göre NOKTASIZ "ı"ya çevirip
    dönüyor (örn. BİM'in kodu "bımas" olarak geliyor, bkz. modül üst notu
    ve `_turkish_lower()`), ama bu fonksiyon eskiden düz Python `.lower()`
    kullanıyordu ("bimas", NOKTALI i) — ikisi BAYT OLARAK FARKLI karakter
    olduğu için `search_company()`'deki eşleşme SESSİZCE hiç tutmuyordu.
    Bu, "I" harfi içeren HER ticker'ı (BIMAS, ISCTR, ENKAI, ISBTR, SISE gibi
    — Türkiye'nin en büyük şirketlerinden birçoğu) etkiliyordu:
    `KapCompanyNotFoundError` fırlatılıyor, bu şirketler KAP'a bağlı HER
    özellikten (bildirimler, takvim vb.) SESSİZCE düşüyordu. Suffix (".IS")
    temizliği Türkçe dönüşümden ÖNCE yapılır (suffix ASCII'dir, ".is" ARAMASI
    kendisi Türkçe dönüşümden ETKİLENMEMELİDİR — aksi halde ".IS" -> ".ıs"
    olur ve endswith kontrolü KIRILIR). Girdi önce `.upper()` ile büyük
    harfe çevrilir ki küçük harfle yazılmış bir ticker ("bimas") da büyük
    harfli girdiyle ("BIMAS") AYNI sonucu üretsin — ticker'lar kanonik
    olarak HER ZAMAN büyük harfle yazılır."""
    code = ticker.strip().upper()
    if code.endswith(".IS"):
        code = code[:-3]
    return _turkish_lower(code)


def search_company(ticker: str) -> CompanyMatch:
    """Hisse kodunu KAP'in ic uye kimligine (mkkMemberOid) esler.

    Hatalar:
        KapCompanyNotFoundError: 'companyOrFunds' sonuclarinda tam eslesme yok.
        KapNetworkError: Ag hatasi veya beklenmeyen yanit.
    """
    normalized = normalize_ticker(ticker)
    payload = _post_json(SEARCH_ENDPOINT, {"keyword": normalized})

    if not isinstance(payload, list):
        raise KapNetworkError("KAP arama yaniti beklenmeyen bicimde (liste degil).")

    companies = next((c.get("results", []) for c in payload if c.get("category") == "companyOrFunds"), [])

    for row in companies:
        if row.get("searchType") != "C":
            continue
        codes = tuple((row.get("cmpOrFundCode") or "").split(","))
        if normalized in codes:
            return CompanyMatch(
                member_oid=row["memberOrFundOid"],
                name=row.get("searchValue", ""),
                ticker_codes=codes,
            )

    raise KapCompanyNotFoundError(
        f"'{ticker}' KAP sirket aramasinda bulunamadi. Hisse kodunu kontrol edin."
    )


def _parse_publish_date(raw_value: str) -> datetime:
    return datetime.strptime(raw_value, _PUBLISH_DATE_FORMAT)


def _row_to_disclosure(row: dict) -> Disclosure:
    category = row.get("subject") or ""
    title = row.get("summary") or row.get("kapTitle") or category
    disclosure_index = row["disclosureIndex"]

    return Disclosure(
        date=_parse_publish_date(row["publishDate"]),
        title=title,
        category=category,
        summary=title,
        url=DISCLOSURE_DETAIL_URL_TEMPLATE.format(disclosure_index=disclosure_index),
        importance=classify_importance(category, title),
        is_late=bool(row.get("isLate", False)),
        disclosure_index=disclosure_index,
        stock_codes=row.get("stockCodes") or "",
        related_stocks=row.get("relatedStocks") or "",
        filer_name=row.get("kapTitle") or "",
    )


def fetch_disclosures_by_oid(member_oid: str, days: int = 90) -> list[Disclosure]:
    """`fetch_disclosures()` ile AYNI istegi, hisse kodu yerine KAP'in ic
    uye kimligini (mkkMemberOid) dogrudan alarak yapar -- kap_fund_portfolio.py
    fonlar/kurucu sirketler icin `search_company()`'yi (sadece searchType=='C'
    filtreler) DEGIL, kendi arama sonucundaki oid'i dogrudan kullanmak
    zorunda oldugu icin bu ayri, dusuk seviyeli fonksiyon dislariya acildi.

    Hatalar:
        KapNetworkError: Ag hatasi veya beklenmeyen yanit.
    """
    to_date = date.today()
    from_date = to_date - timedelta(days=days)
    body = {
        "fromDate": from_date.isoformat(),
        "toDate": to_date.isoformat(),
        "mkkMemberOidList": [member_oid],
    }
    payload = _post_json(DISCLOSURES_ENDPOINT, body)

    if isinstance(payload, dict):
        error_message = payload.get("errorMessage", "bilinmeyen hata")
        raise KapNetworkError(f"KAP bildirim sorgusu basarisiz: {error_message}")
    if not isinstance(payload, list):
        raise KapNetworkError("KAP bildirim yaniti beklenmeyen bicimde (liste degil).")

    disclosures = [_row_to_disclosure(row) for row in payload]
    disclosures.sort(key=lambda d: d.date, reverse=True)
    return disclosures


# CANLI KEŞFEDİLDİ (Faz 20, kullanıcı raporu üzerine, 2026-08-07):
# `mkkMemberOidList` alanı BOŞ liste/hiç verilmezse endpoint TÜM KAP
# üyelerinin bildirimlerini döner (üye kısıtlaması YOK) -- bu, `kap_ipo.py`'nin
# ÖNCEKİ turdaki sabit `UNDERWRITER_MEMBERS` (~22 kurum) listesini TARAYAN
# yaklaşımının YERİNİ alır: o liste kaçınılmaz olarak eksikti (kullanıcı
# raporu: Tera Yatırım -- Çitlekçi'nin izahnamesini yayınlayan kurum --
# listede YOKTU; TSKB gibi tipik bir "aracı kurum" bile sayılmayan bir üye
# de -- Bewen'in izahnamesini yayınlamış -- ASLA akla gelmezdi). Tek istekte
# TÜM piyasa taranır (~1-2 saniye, 22 kurumun ~45-60 saniyelik sıralı
# taramasından KAT KAT hızlı).
# ⚠️ SINIR (CANLI ölçüldü): yanıt tam olarak **2000 satırda KESİLİYOR**
# (14 ve 30 günlük pencereler İKİSİ DE tam 2000 döndü, 7 gün 1878 ile
# sınırın ALTINDA kaldı) -- bu yüzden `_MAX_SAFE_ALL_DISCLOSURES_DAYS`
# ile pencere sınırlanır, sınıra ulaşılırsa (Kural 3: sessizce yanlış
# sonuç ÜRETİLMEZ) bir uyarı loglanır.
_MAX_SAFE_ALL_DISCLOSURES_DAYS = 10
_ALL_DISCLOSURES_TRUNCATION_ROW_COUNT = 2000


def fetch_all_disclosures(days: int = 7) -> list[Disclosure]:
    """TÜM KAP üyelerinin son `days` gündeki bildirimlerini TEK istekte
    döner (üye/oid GEREKMEZ). `days` `_MAX_SAFE_ALL_DISCLOSURES_DAYS`'i
    aşarsa (CANLI ölçülen 2000 satır kesme sınırına çarpma riski) ValueError
    fırlatır -- çağıran taraf bilerek daha uzun bir pencere istiyorsa
    `fetch_disclosures_by_oid()`/üye-bazlı tarama kullanmalı.

    Hatalar:
        ValueError: `days` güvenli sınırı aşıyor.
        KapNetworkError: Ağ hatası veya beklenmeyen yanıt.
    """
    if days > _MAX_SAFE_ALL_DISCLOSURES_DAYS:
        raise ValueError(
            f"fetch_all_disclosures: days={days} güvenli sınırı ({_MAX_SAFE_ALL_DISCLOSURES_DAYS}) aşıyor "
            "-- KAP yanıtı 2000 satırda kesiliyor, daha uzun pencere için üye-bazlı tarama kullan."
        )

    to_date = date.today()
    from_date = to_date - timedelta(days=days)
    body = {
        "fromDate": from_date.isoformat(),
        "toDate": to_date.isoformat(),
        "mkkMemberOidList": [],
    }
    payload = _post_json(DISCLOSURES_ENDPOINT, body)

    if isinstance(payload, dict):
        error_message = payload.get("errorMessage", "bilinmeyen hata")
        raise KapNetworkError(f"KAP bildirim sorgusu basarisiz: {error_message}")
    if not isinstance(payload, list):
        raise KapNetworkError("KAP bildirim yaniti beklenmeyen bicimde (liste degil).")

    if len(payload) >= _ALL_DISCLOSURES_TRUNCATION_ROW_COUNT:
        logger.warning(
            "fetch_all_disclosures: yanıt tam %s satır döndü -- KAP'ın kesme sınırına ULAŞILMIŞ olabilir, "
            "bazı bildirimler eksik kalmış olabilir (days=%s).",
            len(payload),
            days,
        )

    disclosures = [_row_to_disclosure(row) for row in payload]
    disclosures.sort(key=lambda d: d.date, reverse=True)
    return disclosures


def fetch_disclosures(ticker: str, days: int = 90) -> list[Disclosure]:
    """Bir BIST sirketinin son `days` gunun KAP bildirimlerini ceker ve
    onem derecesine gore etiketler (en yeni -> en eski siralanmis doner).

    Hatalar:
        KapCompanyNotFoundError: Hisse kodu KAP'ta bulunamadi.
        KapNetworkError: Ag hatasi veya beklenmeyen yanit.
    """
    company = search_company(ticker)
    logger.info("KAP eslesmesi bulundu: %s (oid=%s)", company.name, company.member_oid)

    time.sleep(config.HTTP_RATE_LIMIT_DELAY_SECONDS)

    return fetch_disclosures_by_oid(company.member_oid, days=days)


def get_top_disclosures(disclosures: list[Disclosure], limit: int = 5) -> list[Disclosure]:
    """Bildirimleri onem (yuksek once) + tarih (yeni once) sirasina gore
    siralar ve en fazla `limit` tanesini doner."""
    importance_rank = {IMPORTANCE_HIGH: 0, IMPORTANCE_LOW: 1}
    ranked = sorted(
        disclosures,
        key=lambda d: (importance_rank.get(d.importance, 1), -d.date.timestamp()),
    )
    return ranked[:limit]
