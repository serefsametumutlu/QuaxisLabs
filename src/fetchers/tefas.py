"""TEFAS (Türkiye Elektronik Fon Alım Satım Platformu, tefas.gov.tr)
yatırım fonu veri fetcher'ı.

Faz 17 keşif adımında (bkz. scripts/explore_tefas.py, orada ayrıntılı
bulgular var) CANLI doğrulanan gerçekler:

- TEFAS'ın eski uç noktaları (fundturkey.com.tr/api/DB/BindHistoryInfo vb.)
  EMEKLİYE AYRILMIŞ; yeni backend `tefas.gov.tr/api/funds/` ve
  `tefas.gov.tr/api/statistics/tefas/` altında.
- TEFAS'ın `/tr/...` SAYFALARI bir bot koruması (F5/Distil tipi JS meydan
  okuması) ARKASINDADIR -- ama `/api/funds/*` ve `/api/statistics/tefas/*`
  JSON uç noktaları KORUMASIZDIR, düz httpx isteğiyle CANLI doğrulandı.
- 🚨 KRİTİK KISIT (görev tanımının varsaydığı gibi DOĞRULANDI): TEFAS'ın
  GÜVENİLİR şekilde çekilebilen `fonBilgiGetir` uç noktası varlık
  dağılımı DÖNDÜRMEZ. Sınıf-bazlı (hisse/tahvil/repo vb.) dağılım
  sayfanın sunucu-taraflı render (RSC) payload'ına gömülü geliyor ama
  bunun API'sinin (dagilimSiraliGetirT) doğru istek gövdesi bu oturumda
  BULUNAMADI (NullPointerException) ve bir Playwright yedeği de WAF
  tarafından reddedildi -- bu yüzden `FundInfo.allocation` HER ZAMAN boş
  sözlük döner (Kural 3: emin olunmayan veri uydurulmaz).
- Aynı nedenle fiyat GEÇMİŞİ (`fonFiyatBilgiGetir` çoklu-dönem) ve getiri
  bilgisi (`fonGetiriBazliBilgiGetir`) için de doğru istek gövdesi
  BULUNAMADI -- `fetch_fund_returns()`/`fetch_price_history()` bu yüzden
  HER ZAMAN boş/None döner, loglanır, hata FIRLATMAZ (Kural 9).
- Fiyat AÇIKLANMA ZAMANLAMASI (T+1 sabah mı, aynı gün akşam mı) bu
  oturumda DOĞRULANAMADI -- `fonBilgiGetir` yanıtında fiyata ait bir
  tarih alanı YOK, bu netleştirme gelecek bir faza bırakıldı.

Ne ÇALIŞIYOR (CANLI doğrulandı, AFA fonuyla):
  - search_fund(): `getFplFonList` (TÜM TEFAS fon evreni, tek istek) +
    Python'da alt-dize eşleme.
  - fetch_fund_info(): `fonBilgiGetir` (fiyat, günlük getiri, pay adet,
    toplam değer, kategori, yatırımcı sayısı, pazar payı) + kurucu adı
    için `getFplFonList` evren listesinden eşleme.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

import config
from src.fetchers import kap

logger = logging.getLogger(__name__)

FUNDS_BASE = "https://www.tefas.gov.tr/api/funds"
STATISTICS_BASE = "https://www.tefas.gov.tr/api/statistics/tefas"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Referer": "https://www.tefas.gov.tr/tr/fon-detayli-analiz/",
    "Origin": "https://www.tefas.gov.tr",
}


# --- Hata sınıfları -----------------------------------------------------


class TefasError(Exception):
    """TEFAS fetcher'ı için taban hata sınıfı."""


class TefasFundNotFoundError(TefasError):
    """Verilen fon kodu TEFAS fon evreninde/fonBilgiGetir yanıtında bulunamadı."""


class TefasNetworkError(TefasError):
    """TEFAS'a ağ seviyesinde ulaşılamadı veya yanıt beklenmeyen biçimde geldi."""


# --- Veri modelleri -----------------------------------------------------


@dataclass(frozen=True)
class FundMatch:
    code: str
    name: str
    founder: str | None
    status: str | None  # "AKTİF" | diğer -- getFplFonList "durum" alanı


@dataclass(frozen=True)
class FundInfo:
    code: str
    name: str
    founder: str | None
    type: str | None  # TEFAS "fonKategori" (örn. "Hisse Senedi Fonu")
    price: Decimal | None
    price_date: date | None  # fonBilgiGetir bu tarihi DÖNMÜYOR -- her zaman None (bkz. modül üst notu)
    total_value: Decimal | None
    investor_count: int | None
    allocation: dict[str, Decimal] = field(default_factory=dict)  # sınıf bazlı -- HER ZAMAN boş (bkz. modül üst notu)


@dataclass(frozen=True)
class FundReturns:
    d1: Decimal | None
    w1: Decimal | None
    m1: Decimal | None
    m3: Decimal | None
    m6: Decimal | None
    y1: Decimal | None
    y3: Decimal | None
    y5: Decimal | None
    ytd: Decimal | None


# --- HTTP katmanı -----------------------------------------------------


@retry(
    reraise=True,
    stop=stop_after_attempt(config.HTTP_MAX_RETRIES),
    wait=wait_fixed(config.HTTP_RATE_LIMIT_DELAY_SECONDS),
    retry=retry_if_exception_type(httpx.RequestError),
)
def _post_json(url: str, body: dict) -> dict:
    try:
        response = httpx.post(url, json=body, headers=_HEADERS, timeout=config.HTTP_TIMEOUT_SECONDS)
    except httpx.RequestError as exc:
        logger.warning("TEFAS isteği başarısız, yeniden denenecek: %s", exc)
        raise

    if response.status_code != 200:
        raise TefasNetworkError(f"TEFAS beklenmeyen HTTP durum kodu döndürdü: {response.status_code}")

    try:
        return response.json()
    except ValueError as exc:
        raise TefasNetworkError(
            "TEFAS yanıtı JSON olarak ayrıştırılamadı (uç nokta şeması değişmiş olabilir)."
        ) from exc


def _to_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _to_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# --- Fon evreni (arama için) -----------------------------------------------------


def _fetch_fund_universe() -> list[dict]:
    """`getFplFonList` -- parametresiz istekte TÜM TEFAS fon evrenini
    (kod/unvan/kurucu/operatör/durum) tek seferde döner (CANLI doğrulandı,
    2026-08-05: 1031 fon). search_fund() ve fetch_fund_info()'nun kurucu
    adı eşlemesi bunu kullanır.

    ⚠️ Bu TEK istek TÜM evreni döner -- her çağrıda TEKRAR tekrar
    istenmemesi gerekir (kap.py::fetch_sector_map ile AYNI ilke); ama bu
    fazda ayrı bir önbellek katmanı KURULMADI (küçük/hafif bir JSON, ~1000
    satır), çağıran taraf isterse kendi önbelleğini ekleyebilir.

    Hatalar:
        TefasNetworkError: Ağ hatası veya beklenmeyen yanıt biçimi.
    """
    payload = _post_json(f"{STATISTICS_BASE}/getFplFonList", {})
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise TefasNetworkError("TEFAS fon evreni yanıtı beklenmeyen biçimde (liste değil).")
    return rows


def search_fund(query: str) -> list[FundMatch]:
    """Fon kodu veya adıyla arama yapar (TEFAS'ın kendi arama uç noktasının
    -- fonUnvanAra -- gerçek istek gövdesi bu oturumda bulunamadığı için,
    bkz. scripts/explore_tefas.py -- bunun yerine tam fon evreni tek
    seferde çekilip Python'da alt-dize eşlemesi yapılır).

    Hatalar:
        TefasNetworkError: Ağ hatası veya beklenmeyen yanıt biçimi.
    """
    # Turkce buyuk/kucuk harf tuzagi (kap.py::_turkish_lower ile AYNI sebep):
    # Python'un standart str.upper()'i 'i' -> 'I' (ASCII) uretir, ama fon
    # unvanlarindaki gercek Turkce metin 'İ' (noktali buyuk I) icerir --
    # "amerika".upper() ("AMERIKA") "AMERİKA" icinde GECMEZ. Bu yuzden
    # kucuk harfe (Turkce kurallariyla) normalize edilip oyle karsilastirilir.
    normalized = kap._turkish_lower(query.strip())
    if not normalized:
        return []

    matches: list[FundMatch] = []
    for row in _fetch_fund_universe():
        code = row.get("fonKod") or ""
        name = row.get("unvan") or ""
        if normalized in kap._turkish_lower(code) or normalized in kap._turkish_lower(name):
            matches.append(
                FundMatch(
                    code=code,
                    name=name,
                    founder=row.get("kurucuAd"),
                    status=row.get("durum"),
                )
            )
    return matches


def fetch_fund_info(code: str) -> FundInfo:
    """Bir fonun GÜNCEL bilgilerini döner (`fonBilgiGetir`, CANLI
    doğrulandı) -- fiyat, günlük getiri (fetch_fund_returns'e KARIŞTIRILMASIN,
    bu SADECE günlük değişim), pay adedi, toplam (portföy) değer, kategori,
    yatırımcı sayısı, pazar payı. Kurucu adı AYRI bir istekle (fon evreni)
    eşlenir -- fonBilgiGetir bu alanı DÖNMÜYOR.

    `price_date` ve `allocation` HER ZAMAN None/boş döner -- TEFAS'ın bu
    alanları güvenilir şekilde veren uç noktaları bu oturumda bulunamadı
    (bkz. modül üst notu, Kural 3: emin olunmayan veri uydurulmaz).

    Hatalar:
        TefasFundNotFoundError: Fon kodu TEFAS'ta bulunamadı.
        TefasNetworkError: Ağ hatası veya beklenmeyen yanıt biçimi.
    """
    normalized = code.strip().upper()
    payload = _post_json(f"{FUNDS_BASE}/fonBilgiGetir", {"fonKodu": normalized})
    rows = payload.get("resultList")
    if not rows:
        raise TefasFundNotFoundError(f"'{code}' TEFAS'ta bulunamadı (fonBilgiGetir boş döndü).")

    row = rows[0]

    founder: str | None = None
    try:
        for universe_row in _fetch_fund_universe():
            if (universe_row.get("fonKod") or "").upper() == normalized:
                founder = universe_row.get("kurucuAd")
                break
    except TefasError as exc:
        # Kurucu adı ikincil/yardımcı bir alandır -- ana fon bilgisini bloklamaz (Kural 9).
        logger.warning("TEFAS fon evreni (kurucu adı için) çekilemedi, 'founder' None kalacak: %s", exc)

    return FundInfo(
        code=row.get("fonKodu", normalized),
        name=row.get("fonUnvan", ""),
        founder=founder,
        type=row.get("fonKategori"),
        price=_to_decimal(row.get("sonFiyat")),
        price_date=None,
        total_value=_to_decimal(row.get("portBuyukluk")),
        investor_count=_to_int(row.get("yatirimciSayi")),
        allocation={},
    )


def fetch_fund_returns(code: str) -> FundReturns:
    """Bir fonun çok-dönemli getiri bilgisini (1G/1H/1A/3A/6A/1Y/3Y/5Y/YB)
    döner.

    🚨 TEFAS'ın bu veriyi veren uç noktasının (fonGetiriBazliBilgiGetir /
    fonTurDnmGetiriGetir) doğru istek gövdesi bu oturumda BULUNAMADI --
    veri sayfanın sunucu-taraflı render payload'ına gömülü geliyor
    (`periyodikData`, CANLI görüldü) ama bu bot korumasının ARKASINDA,
    güvenilir şekilde otomatikleştirilemedi (bkz. modül üst notu). Bu
    yüzden fonksiyon HER ZAMAN tüm alanları None olan bir FundReturns
    döner -- hata FIRLATMAZ (Kural 9: yardımcı veri ana akışı bloklamaz),
    sadece loglar. Gelecekte doğru uç nokta bulunursa BURASI güncellenmeli.
    """
    logger.warning(
        "TEFAS getiri API'sinin istek gövdesi bu oturumda doğrulanamadı (bkz. "
        "scripts/explore_tefas.py) -- '%s' için tüm getiri alanları None dönüyor.",
        code,
    )
    return FundReturns(d1=None, w1=None, m1=None, m3=None, m6=None, y1=None, y3=None, y5=None, ytd=None)


def fetch_price_history(code: str, months: int) -> list[tuple[date, Decimal]]:
    """Bir fonun geçmiş fiyat serisini (son `months` ay, TEFAS'ın sabit
    geriye-bakış enum'u {1,3,6,12,36,60} ay ile sınırlı) döner.

    🚨 TEFAS'ın fiyat geçmişi uç noktasının (fonFiyatBilgiGetir, çoklu
    dönem) doğru istek gövdesi bu oturumda BULUNAMADI -- tüm denemeler
    "Sistem Hatası!!" döndü (bkz. modül üst notu). Bu yüzden fonksiyon
    HER ZAMAN boş liste döner -- hata FIRLATMAZ (Kural 9), sadece loglar.
    Gelecekte doğru uç nokta bulunursa BURASI güncellenmeli.
    """
    logger.warning(
        "TEFAS fiyat geçmişi API'sinin istek gövdesi bu oturumda doğrulanamadı (bkz. "
        "scripts/explore_tefas.py) -- '%s' için boş liste dönüyor.",
        code,
    )
    return []
