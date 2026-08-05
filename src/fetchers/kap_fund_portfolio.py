"""KAP (Kamuyu Aydınlatma Platformu) yatırım fonu "Portföy Dağılım Raporu"
fetcher'ı.

Faz 17 keşif adımında (bkz. scripts/explore_kap_fon.py, orada ayrıntılı
bulgular var) CANLI test edilen ve DOĞRULANAN gerçekler:

- KAP'ın mevcut arama uç noktası (`kap.py::SEARCH_ENDPOINT`, zaten
  şirketler için kullanılıyor) FONLARI da tanıyor -- `searchType` alanı
  fonlar için `"F"` (şirketler `"C"`). Örnek: "afa" araması
  `{"searchValue":"AK PORTFÖY AMERİKA YABANCI HİSSE SENEDİ FONU",
  "searchType":"F","memberOrFundOid":"33E5FED7E40B00EAE0530A4A622B2AEA"}`
  döndü.
- 🚨 KRİTİK BULGU: `kap.py::DISCLOSURES_ENDPOINT` (`disclosure/members/
  byCriteria`) bu fon oid'i ile (90/180/365 gün pencereleri denendi)
  HER SEFERİNDE BOŞ liste döndü. Fonun KURUCUSU olan portföy yönetim
  şirketinin (AK PORTFÖY YÖNETİMİ A.Ş.) KENDİ KAP kaydı da bulundu ve
  GERÇEKTEN bildirimleri var (60 günde 7 bildirim) ama HİÇBİRİ "Portföy
  Dağılım Raporu" değil -- hepsi şirketin kendi kurumsal bildirimleri
  (Faaliyet Raporu, Finansal Rapor, Şirket Genel Bilgi Formu).
- Bu test edilen ÖRNEKTE (AK PORTFÖY / AFA) hisse bazlı fon portföy
  dağılımı KAP'ın public disclosure API'si üzerinden GÜVENİLİR ŞEKİLDE
  BULUNAMADI -- ne fonun oid'i ne kurucusunun oid'i altında böyle bir
  bildirime rastlanmadı. `kap.org.tr/tr/YatirimFonlari` navigasyon linki
  de tarayıcıda 404 gözlendi (bu gözlem bir tarayıcı oturumu çökmesiyle
  aynı ana denk geldiği için TAM güvenilir sayılmıyor).

🚨 SONUÇ (Kural 3: uydurma veriyle DEVAM EDİLMEDİ): Bu oturumda GERÇEK
bir "Portföy Dağılım Raporu" örneğine hiç ULAŞILAMADIĞI için, raporun
İÇERİK BİÇİMİ (HTML mi PDF mi), hisse bazlı satırların ayrıştırılabilir
olup olmadığı ve yayın sıklığı/gecikmesi bu oturumda DOĞRULANAMADI.
Bu modül bu yüzden SADECE doğrulanmış KAP arama/bildirim uç noktalarını
kullanarak böyle bir bildirimi ARAMAYI dener (bu kısım GERÇEKTEN
çalışır) -- bulursa bile GÜVENİLİR bir ayrıştırma garantisi
VERMEDİĞİNDEN (hiç örnek görülmedi) `fetch_latest_portfolio()` bulunan
bildirimin varlığını LOGLAR ama holdings ayrıştırması YAPMADAN None
döner. Gerçek bir örnek rapor bulunduğunda (Kural 3 gereği önce
scripts/explore_kap_fon.py ile canlı doğrulanıp) bu modül genişletilmeli.

Faz 18/19 kapsam önerisi: hisse bazlı fon içeriği bu kaynaktan güvenilir
şekilde alınamadığı için, o fazların kapsamı TEFAS'ın sınıf-bazlı varlık
dağılımına (bulunabilirse, bkz. tefas.py) ve/veya farklı bir veri
kaynağına göre YENİDEN değerlendirilmelidir.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

import config
from src.fetchers import kap

logger = logging.getLogger(__name__)

# scripts/explore_kap_fon.py ile AYNI liste -- bir bildirim başlığının
# "Portföy Dağılım Raporu" olup olmadığını sezmek için kullanılır.
_PORTFOLIO_REPORT_HINTS = ("portföy dağılım", "portfoy dagilim", "portföy bilgi", "portföy raporu")


# --- Hata sınıfları -----------------------------------------------------


class KapFundPortfolioError(Exception):
    """KAP fon portföy fetcher'ı için taban hata sınıfı."""


class FundNotFoundError(KapFundPortfolioError):
    """Verilen fon kodu KAP arama sonuçlarında (searchType='F') bulunamadı."""


# --- Veri modelleri -----------------------------------------------------


@dataclass(frozen=True)
class Holding:
    instrument_type: str  # "hisse" | "tahvil" | "repo" | ...
    ticker: str | None  # hisse ise BİST kodu
    name: str
    weight_pct: Decimal


@dataclass(frozen=True)
class FundPortfolio:
    fund_code: str
    report_date: date  # raporun AİT OLDUĞU tarih
    publish_date: date
    holdings: list[Holding]
    staleness_days: int  # bugün - report_date


# --- KAP fon arama -----------------------------------------------------


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


def _find_founder_company(fund_name: str) -> dict | None:
    """Fon unvanından portföy yönetim şirketini (kurucu) KAP şirket
    aramasında bulmayı dener -- fonların kendi oid'i altında hiç bildirim
    olmayabileceği CANLI doğrulandığı için (bkz. modül üst notu), kurucu
    şirketin oid'i de ikincil bir arama noktası olarak denenir. Bulunamazsa
    None döner (Kural 9: yardımcı arama, ana akışı bloklamaz)."""
    # Fon unvanı genelde "<KURUCU> ... FONU" biçimindedir (örn. "AK PORTFÖY
    # AMERİKA YABANCI HİSSE SENEDİ FONU" -> kurucu "AK PORTFÖY"). Kesin bir
    # ayraç YOK (Kural 3: varsayımsal ayrıştırma yapılmaz) -- bu yüzden
    # unvanın İLK İKİ kelimesiyle arama yapılır, KAP'ın kendi arama motoru
    # geri kalanı eşler.
    words = fund_name.strip().split()
    if len(words) < 2:
        return None
    query = " ".join(words[:2])
    try:
        payload = kap._post_json(kap.SEARCH_ENDPOINT, {"keyword": kap._turkish_lower(query)})
    except kap.KapError as exc:
        logger.warning("KAP kurucu şirket araması başarısız (yardımcı adım, atlanıyor): %s", exc)
        return None

    if not isinstance(payload, list):
        return None
    rows = next((c.get("results", []) for c in payload if c.get("category") == "companyOrFunds"), [])
    for row in rows:
        if row.get("searchType") == "C" and "portföy yönetimi" in (row.get("searchValue") or "").lower():
            return row
    return None


def _find_portfolio_disclosure(member_oid: str, days: int) -> dict | None:
    """Verilen KAP üye oid'inin bildirimleri arasında başlığı/konusu
    `_PORTFOLIO_REPORT_HINTS`'ten birini içeren EN YENİ bildirimi arar.
    Bulunamazsa None döner (Kural 9)."""
    disclosures = kap.fetch_disclosures_by_oid(member_oid, days=days)
    haystack_hint = _PORTFOLIO_REPORT_HINTS
    for disclosure in disclosures:
        haystack = kap._turkish_lower(f"{disclosure.category} {disclosure.title}")
        if any(hint in haystack for hint in haystack_hint):
            return disclosure
    return None


def fetch_latest_portfolio(fund_code: str) -> FundPortfolio | None:
    """Bir fonun EN GÜNCEL hisse-bazlı portföy dağılım raporunu aramaya
    çalışır.

    🚨 Bu oturumda test edilen örnekte (AFA) böyle bir bildirim ne fonun
    kendi KAP kaydı ne de kurucusunun kaydı altında BULUNAMADI (bkz. modül
    üst notu) -- bu fonksiyon bu yüzden GÜVENİLİR BİR ŞEKİLDE her zaman
    None dönebilir. Eğer arama bir eşleşme BULURSA bile (başka bir fon
    için mümkün olabilir), bu modül raporun İÇERİĞİNİ (hisse satırları)
    AYRIŞTIRMAZ -- çünkü hiçbir gerçek örnek üzerinde bu biçim CANLI
    doğrulanmadı (Kural 3). Bu durumda bir uyarı loglanır ve YİNE None
    döner; gelecekte gerçek bir örnek bulunduğunda ayrıştırma eklenmelidir.

    Hatalar fırlatmaz -- yardımcı/ikincil bir veri kaynağıdır (Kural 9),
    her hata durumunda loglanıp None döner.
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
    fund_name = fund_row.get("searchValue", "")

    try:
        disclosure = _find_portfolio_disclosure(fund_oid, days=config.KAP_LOOKBACK_DAYS * 4)
    except kap.KapError as exc:
        logger.warning("KAP fon bildirimleri çekilemedi (%s): %s", fund_code, exc)
        disclosure = None

    if disclosure is None:
        time.sleep(config.HTTP_RATE_LIMIT_DELAY_SECONDS)
        founder = _find_founder_company(fund_name)
        if founder is not None:
            try:
                disclosure = _find_portfolio_disclosure(founder["memberOrFundOid"], days=90)
            except kap.KapError as exc:
                logger.warning("KAP kurucu şirket bildirimleri çekilemedi: %s", exc)
                disclosure = None

    if disclosure is None:
        logger.info(
            "'%s' için KAP'ta 'Portföy Dağılım Raporu' benzeri bir bildirim bulunamadı "
            "(fonun kendi kaydı VE kurucusunun kaydı denendi). Bu, TEFAS'ın "
            "sınıf-bazlı varlık dağılımı DIŞINDA hisse-bazlı içeriğin bu "
            "oturumda güvenilir şekilde alınamadığını doğrular.",
            fund_code,
        )
        return None

    logger.warning(
        "'%s' için KAP'ta olası bir portföy dağılım bildirimi BULUNDU (%s, %s) ama "
        "bu bildirimin GERÇEK içerik biçimi (HTML/PDF) hiç canlı doğrulanmadığı için "
        "ayrıştırma YAPILMADI (Kural 3) -- None dönüyor. Bkz. src/fetchers/"
        "kap_fund_portfolio.py modül üst notu.",
        fund_code,
        disclosure.url,
        disclosure.date,
    )
    return None
