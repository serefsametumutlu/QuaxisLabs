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
    stock_codes: str


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
    )


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

    to_date = date.today()
    from_date = to_date - timedelta(days=days)
    body = {
        "fromDate": from_date.isoformat(),
        "toDate": to_date.isoformat(),
        "mkkMemberOidList": [company.member_oid],
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


def get_top_disclosures(disclosures: list[Disclosure], limit: int = 5) -> list[Disclosure]:
    """Bildirimleri onem (yuksek once) + tarih (yeni once) sirasina gore
    siralar ve en fazla `limit` tanesini doner."""
    importance_rank = {IMPORTANCE_HIGH: 0, IMPORTANCE_LOW: 1}
    ranked = sorted(
        disclosures,
        key=lambda d: (importance_rank.get(d.importance, 1), -d.date.timestamp()),
    )
    return ranked[:limit]
