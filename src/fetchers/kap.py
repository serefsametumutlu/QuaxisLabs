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

import logging
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


def normalize_ticker(ticker: str) -> str:
    """'THYAO.IS' -> 'thyao' seklinde KAP aramasinin bekledigi kucuk harfli koda cevirir."""
    code = ticker.strip().lower()
    if code.endswith(".is"):
        code = code[: -len(".is")]
    return code


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
