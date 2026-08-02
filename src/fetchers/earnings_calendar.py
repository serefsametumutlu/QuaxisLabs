"""Faz 12: "Yaklaşan Bilanço Tarihleri" veri katmanı.

BIST için "hangi şirket ne zaman bilanço açıklayacak" sorusuna cevap veren
TEK bir resmi API YOK (bkz. scripts/explore_kap_takvim.py canlı keşfi,
2026-08-02). Bu modül ÜÇ yaklaşımı BİRLEŞTİRİR ve her tahmine bir GÜVEN
SEVİYESİ atar (bkz. CONFIDENCE_* sabitleri) -- tahmini bir tarih ASLA
kesinmiş gibi sunulmaz (Kural 3 ruhu):

  1. KESİN (CONFIDENCE_KESIN) -- şirketin KENDİ KAP "Finansal Takvim"
     bildirimi (bkz. _parse_finansal_takvim_html). CANLI DOĞRULANDI: TAVHL
     (disclosure_index=1630730) ve ASELS (1635301) bu bildirimi yayınlıyor;
     her ikisinde de "Planlanan KAP'ta İlan Tarihi" alanı gerçek yayın
     tarihiyle (TAVHL: 28.07.2026 planlanan → 28.07.2026 gerçekleşen)
     BİREBİR eşleşti. AMA bu bildirim OPSİYONELDİR -- THYAO son 365 günde
     HİÇ yayınlamamış (canlı doğrulandı) -- bu yüzden fallback GEREKLİ.

  2. TAHMİNİ (CONFIDENCE_TAHMINI) -- şirketin geçmiş 4-8 çeyrekte "Finansal
     Rapor" (FR) bildirimini dönem sonundan KAÇ GÜN SONRA yayınladığının
     MEDYANI (bkz. historical_publish_lag_days). CANLI doğrulandı: THYAO
     medyan ~37 gün, TAVHL ~27,5 gün, ASELS ~35,5 gün -- şirkete göre
     TUTARLI bir örüntü var.

  3. SON TARİH (CONFIDENCE_SON_TARIH) -- SPK II-14.1 Tebliği'nin YASAL
     bildirim süresi (bkz. legal_deadline). HER ZAMAN hesaplanabilir
     (fallback'in fallback'i) ama şirketler genelde bu son tarihten ÇOK
     ÖNCE açıklar -- kullanıcıya "en geç bu tarih" olarak sunulmalı,
     "muhtemel tarih" olarak DEĞİL.

NASDAQ için: api.nasdaq.com/api/calendar/earnings?date=YYYY-MM-DD (Nasdaq'ın
kendi web sitesinin kullandığı, resmi/belgelenmiş OLMAYAN ama TradingView'in
logo/scanner uç noktalarıyla AYNI ilkeyle -- ücretsiz, kayıt gerektirmeyen,
kod kırılırsa sessizce None/boş liste dönen -- kullanılan bir uç nokta).
CANLI KARŞILAŞTIRMA (2026-08-02): Finnhub'ın ücretsiz katmanı API anahtarı
GEREKTİRİYOR (401 "Please use an API key" -- kayıt/friction), Yahoo'nun
quoteSummary uç noktası (yfinance'in de altta kullandığı) artık bir "crumb"
(oturum tabanlı CSRF token) İSTİYOR (401 "Invalid Crumb" -- ekstra çerez/
oturum yönetimi gerektirir, projenin "ek bağımlılık/karmaşıklık yok" ilkesine
aykırı). api.nasdaq.com HİÇBİRİNİ gerektirmiyor ve GÜNLÜK bazda TÜM piyasanın
takvimini TEK istekte döndürüyor (per-ticker sorgu GEREKMİYOR) -- bu üçü
arasında en basit ve en güvenilir seçenek.

⚠️ NASDAQ verisi "confirmed" vs "estimated" ayrımı İÇERMİYOR (canlı
doğrulandı -- JSON şemasında böyle bir alan YOK) -- bu yüzden TÜM NASDAQ
kayıtları CONFIDENCE_TAHMINI olarak işaretlenir (Nasdaq'ın kendisi de bu
tarihleri hem şirket beyanı hem analist tahminiyle karıştırıyor, biz ayırt
edemiyoruz -- Kural 3: emin olunmayan bir kesinlik iddia edilmez).
"""

from __future__ import annotations

import logging
import statistics
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

import config
from src.fetchers import kap, kap_financials

logger = logging.getLogger(__name__)

Period = tuple[int, int]

CONFIDENCE_KESIN = "kesin"
CONFIDENCE_TAHMINI = "tahmini"
CONFIDENCE_SON_TARIH = "son_tarih"

SOURCE_KAP_TAKVIM = "KAP Finansal Takvim bildirimi"
SOURCE_GECMIS_MEDYAN = "geçmiş yayın medyanı"
SOURCE_SPK_SURESI = "SPK II-14.1 Tebliği"
SOURCE_NASDAQ_API = "NASDAQ takvim API"

_NASDAQ_CALENDAR_ENDPOINT = "https://api.nasdaq.com/api/calendar/earnings"
_NASDAQ_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


class EarningsCalendarError(Exception):
    """Bu modul icin taban hata sinifi."""


@dataclass(frozen=True)
class EarningsDate:
    ticker: str
    company_name: str
    market: str  # "BIST" | "NASDAQ"
    period: Period  # hangi donemin bilancosu (yil, ceyrek_sonu_ay*: 3/6/9/12)
    expected_date: date
    confidence: str  # CONFIDENCE_KESIN | CONFIDENCE_TAHMINI | CONFIDENCE_SON_TARIH
    source: str


_QUARTER_END_MONTH_DAY: dict[int, tuple[int, int]] = {3: (3, 31), 6: (6, 30), 9: (9, 30), 12: (12, 31)}


def _quarter_end_date(year: int, period: int) -> date:
    month, day = _QUARTER_END_MONTH_DAY[period]
    return date(year, month, day)


def _next_period(period: Period) -> Period:
    year, quarter = period
    return (year, quarter + 3) if quarter != 12 else (year + 1, 3)


# --- Türkiye resmi tatil listesi + SPK son bildirim tarihi (Yaklaşım 2) -----------------------------------------------------

# CANLI doğrulandı (web araması, 2026-08-02, hurriyet.com.tr): Ramazan/Kurban
# Bayramı tarihleri İslami takvime göre HER YIL DEĞİŞİR (Gregoryen takvimde
# ~11 gün ÖNE kayar) -- bu liste SADECE 2026 için geçerlidir, YIL BAŞINA
# güncellenmesi gerekir (sabit ulusal tatiller değişmez, dini bayramlar
# değişir).
_TR_RESMI_TATILLER_2026: frozenset[date] = frozenset(
    {
        date(2026, 1, 1),  # Yılbaşı
        date(2026, 3, 20), date(2026, 3, 21), date(2026, 3, 22),  # Ramazan Bayramı
        date(2026, 4, 23),  # Ulusal Egemenlik ve Çocuk Bayramı
        date(2026, 5, 1),  # Emek ve Dayanışma Günü
        date(2026, 5, 19),  # Atatürk'ü Anma, Gençlik ve Spor Bayramı
        date(2026, 5, 27), date(2026, 5, 28), date(2026, 5, 29), date(2026, 5, 30),  # Kurban Bayramı
        date(2026, 7, 15),  # Demokrasi ve Millî Birlik Günü
        date(2026, 8, 30),  # Zafer Bayramı
        date(2026, 10, 29),  # Cumhuriyet Bayramı
    }
)


def _is_tr_non_business_day(d: date) -> bool:
    return d.weekday() >= 5 or d in _TR_RESMI_TATILLER_2026


def _roll_forward_to_business_day(d: date) -> date:
    """SPK II-14.1 Tebliği Madde 10/3, 11/3: son bildirim günü resmi tatile
    denk gelirse, tatili takip eden ilk iş günü son bildirim tarihidir
    (CANLI doğrulandı, lexpera.com.tr konsolide metin, 2026-08-02)."""
    while _is_tr_non_business_day(d):
        d += timedelta(days=1)
    return d


# CANLI doğrulandı (lexpera.com.tr konsolide metin, 2026-08-02):
#   Madde 10 (yıllık): konsolide olmayan 60 gün, konsolide 70 gün.
#   Madde 11 (ara dönem, 3/6/9 aylık): konsolide olmayan 30 gün, konsolide 40 gün.
#   Madde 11/2: sınırlı bağımsız denetime tabi ara dönem raporlarda BORSADA
#     İŞLEM GÖREN işletmeler için +10 gün (diğer işletmeler için +15 gün).
# BIST'te işlem gören TÜM şirketler için ara dönem finansal tablolar SPK/KGK
# düzenlemeleri gereği sınırlı bağımsız denetime tabidir (piyasa pratiği) --
# bu yüzden ara dönem hesaplamasında +10 gün VARSAYILAN olarak uygulanır.
# Yıllık raporlar TAM bağımsız denetime tabidir, bu ek süre ZATEN 60/70 gün
# içine dahildir (ayrıca +10/+15 EKLENMEZ).
_YASAL_SURE_GUN: dict[tuple[bool, bool], int] = {
    # (yillik_mi, konsolide_mi) -> gun
    (True, False): 60,
    (True, True): 70,
    (False, False): 30 + 10,
    (False, True): 40 + 10,
}


def legal_deadline(period: Period, *, is_consolidated: bool = True) -> date:
    """SPK II-14.1 Tebliği'ne göre YASAL SON bildirim tarihini hesaplar
    (Yaklaşım 2 -- her zaman hesaplanabilir fallback, bkz. modül üst notu).
    Şirketlerin BÜYÜK ÇOĞUNLUĞU konsolide finansal tablo hazırladığı için
    `is_consolidated` varsayılanı True'dur."""
    year, quarter = period
    period_end = _quarter_end_date(year, quarter)
    is_annual = quarter == 12
    gun = _YASAL_SURE_GUN[(is_annual, is_consolidated)]
    return _roll_forward_to_business_day(period_end + timedelta(days=gun))


# --- Yaklaşım 1: KAP "Finansal Takvim" bildirimi -----------------------------------------------------

_TAKVIM_ROW_TAGS: tuple[str, ...] = ("oda_FirstQuarter", "oda_SecondQuarter", "oda_ThirdQuarter", "oda_Annual")


def _parse_tr_date(text: str) -> date | None:
    text = text.strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%d/%m/%Y").date()
    except ValueError:
        return None


def _period_from_end_date(period_end: date) -> Period | None:
    for candidate_period, (month, day) in _QUARTER_END_MONTH_DAY.items():
        if period_end.month == month and period_end.day == day:
            return (period_end.year, candidate_period)
    return None


def _parse_finansal_takvim_html(html: str) -> list[tuple[Period, date]]:
    """'Finansal Takvim' bildirim sayfasından (dönem, planlanan_ilan_tarihi)
    çiftlerini çıkarır -- CANLI DOĞRULANDI (TAVHL disclosure_index=1630730,
    ASELS disclosure_index=1635301, bkz. scripts/explore_kap_takvim.py).
    Sayfa, kap_financials._extract_rows ile AYNI 'data-input-row' taxonomy
    tablo yapısını kullanır ama değerler DECIMAL DEĞİL tarih (DD/MM/YYYY) --
    bu yüzden ayrı bir ayrıştırıcı gerekir. Hangi çeyreği/yılı kapsadığı
    şirketin KENDİ 'oda_FirstQuarter/.../Annual' etiketinden DEĞİL, "Dönem
    Bitiş Tarihi" (2. kolon) değerinden türetilir -- ASELS'in Dönem
    Başlangıç Tarihi (01/04/2026, TEK çeyrek) TAVHL'ninkinden (01/01/2026,
    YTD) FARKLI olsa bile Dönem Bitiş Tarihi (30/06/2026) HER İKİSİNDE DE
    aynı ve güvenilir bir çeyrek-sonu göstergesidir."""
    unescaped = html.replace("\\u003c", "<").replace("\\u003e", ">").replace("\\u0027", "'")
    soup = BeautifulSoup(unescaped, "html.parser")

    results: list[tuple[Period, date]] = []
    for row in soup.select("tr.data-input-row"):
        name_div = row.select_one(".taxonomy-field-name")
        if not name_div:
            continue
        tag = name_div.text.split("|")[0].strip()
        if tag not in _TAKVIM_ROW_TAGS:
            continue

        cell_texts = [
            (cell.select_one(".taxonomy-label-field").text.strip() if cell.select_one(".taxonomy-label-field") else "")
            for cell in row.select(".taxonomy-context-value")
        ]
        if len(cell_texts) != 3:
            continue

        period_end = _parse_tr_date(cell_texts[1])
        expected_date = _parse_tr_date(cell_texts[2])
        if period_end is None or expected_date is None:
            continue
        period = _period_from_end_date(period_end)
        if period is None:
            continue
        results.append((period, expected_date))
    return results


def fetch_kap_financial_calendar(ticker: str, days: int = 180) -> list[tuple[Period, date]]:
    """Bir BIST şirketinin son `days` günlük KAP bildirimlerinde "Finansal
    Takvim" kategorisinde bulduğu TÜM (dönem, planlanan_tarih) çiftlerini
    döner (boş liste: hiç yayınlanmamış -- OPSİYONEL bir bildirim, bkz.
    modül üst notu THYAO örneği). Ağ/ayrıştırma hatalarında SESSİZCE boş
    liste döner (bu KESİN veri kaynağıdır ama TEK kaynak DEĞİLDİR --
    caller'ın Yaklaşım 2/3'e düşebilmesi için ASLA istisna fırlatmaz)."""
    try:
        disclosures = kap.fetch_disclosures(ticker, days=days)
    except kap.KapError as exc:
        logger.info("%s için KAP Finansal Takvim bildirimi aranamadı: %s", ticker, exc)
        return []

    results: list[tuple[Period, date]] = []
    for d in disclosures:
        if d.category != "Finansal Takvim":
            continue
        try:
            html = kap_financials.fetch_disclosure_html(d.disclosure_index)
        except Exception as exc:  # noqa: BLE001 -- kesif KAYNAGIDIR, pipeline'i BLOKE ETMEMELI
            logger.info("%s için Finansal Takvim sayfası (index=%s) çekilemedi: %s", ticker, d.disclosure_index, exc)
            continue
        results.extend(_parse_finansal_takvim_html(html))
    return results


# --- Yaklaşım 3: geçmiş yayın davranışı medyanı -----------------------------------------------------


def historical_publish_lag_days(ticker: str, days: int = 365) -> list[int]:
    """Bir şirketin geçmiş "Finansal Rapor" (FR) bildirimlerinin, ait
    oldukları takvim çeyreğinin BİTİŞİNDEN kaç gün SONRA yayınlandığını
    listeler (CANLI doğrulandı: THYAO [29,36,38,63], TAVHL [23,27,28,49],
    ASELS [28,35,36,55] -- bkz. scripts/explore_kap_takvim.py). Aynı (yıl,
    kap_period) için birden fazla bildirim varsa (Konsolide/Solo çifti gibi)
    EN ERKEN yayınlanan baz alınır. Hiçbir FR bulunamazsa boş liste döner."""
    try:
        company = kap.search_company(ticker)
        rows = kap_financials._fetch_disclosures_raw(company.member_oid, days)
    except Exception as exc:  # noqa: BLE001 -- bu bir TAHMIN KAYNAGIDIR, pipeline'i BLOKE ETMEMELI
        logger.info("%s için geçmiş yayın gecikmesi hesaplanamadı: %s", ticker, exc)
        return []

    fr_rows = [r for r in rows if r.get("disclosureCategory") == "FR" and r.get("year") and r.get("period")]
    earliest_by_raw_period: dict[tuple[int, int], datetime] = {}
    for r in fr_rows:
        try:
            publish_date = datetime.strptime(r["publishDate"], "%d.%m.%Y %H:%M:%S")
        except (KeyError, ValueError):
            continue
        raw_key = (r["year"], r["period"])
        if raw_key not in earliest_by_raw_period or publish_date < earliest_by_raw_period[raw_key]:
            earliest_by_raw_period[raw_key] = publish_date

    lags: list[int] = []
    for publish_date in earliest_by_raw_period.values():
        inferred_period = kap_financials._infer_period_from_publish_date(publish_date)
        q_end = _quarter_end_date(*inferred_period)
        lags.append((publish_date.date() - q_end).days)
    return lags


# --- Orkestrasyon: BIST -----------------------------------------------------


def resolve_bist_earnings_date(ticker: str, company_name: str) -> EarningsDate | None:
    """Bir BIST şirketi için SIRADAKİ (henüz KAP'ta yayınlanmamış) çeyreğin
    beklenen bilanço tarihini üç yaklaşımı ÖNCELİK SIRASINA göre birleştirerek
    hesaplar: KESİN (Finansal Takvim) > TAHMİNİ (geçmiş medyan) > SON TARİH
    (SPK yasal süre, her zaman hesaplanabilir). Şirketin en son yayınladığı
    dönem `kap_financials.find_latest_financial_report()` ile bulunamazsa
    (365 gün içinde hiç FR yoksa) None döner -- hedef çeyrek belirlenemez."""
    try:
        latest_ref = kap_financials.find_latest_financial_report(ticker)
    except Exception as exc:  # noqa: BLE001 -- takvim İKİNCİL bir ozelliktir, pipeline'i BLOKE ETMEMELI
        logger.info("%s için en son yayınlanan dönem bulunamadı: %s", ticker, exc)
        return None
    if latest_ref is None:
        return None

    target_period = _next_period(latest_ref.period)

    for period, expected_date in fetch_kap_financial_calendar(ticker):
        if period == target_period:
            return EarningsDate(
                ticker=ticker, company_name=company_name, market="BIST", period=target_period,
                expected_date=expected_date, confidence=CONFIDENCE_KESIN, source=SOURCE_KAP_TAKVIM,
            )

    lags = historical_publish_lag_days(ticker)
    if lags:
        median_lag = round(statistics.median(lags))
        expected_date = _quarter_end_date(*target_period) + timedelta(days=median_lag)
        return EarningsDate(
            ticker=ticker, company_name=company_name, market="BIST", period=target_period,
            expected_date=expected_date, confidence=CONFIDENCE_TAHMINI, source=SOURCE_GECMIS_MEDYAN,
        )

    return EarningsDate(
        ticker=ticker, company_name=company_name, market="BIST", period=target_period,
        expected_date=legal_deadline(target_period), confidence=CONFIDENCE_SON_TARIH, source=SOURCE_SPK_SURESI,
    )


def fetch_upcoming_bist(tickers: list[tuple[str, str]], days_ahead: int = 30, today: date | None = None) -> list[EarningsDate]:
    """`tickers`: [(ticker, company_name), ...] listesi (bkz. modül üst notu
    -- BIST için "kim ne zaman açıklar" broadcast eden bir API yok, bu yüzden
    NASDAQ'ın aksine PER-TICKER sorgu gerekir; hangi evrenin taranacağına
    CALLER karar verir, bkz. get_bist_top_market_cap_tickers()). Her ticker
    için `resolve_bist_earnings_date()` çağrılır, sonuç `today`..`today+days_ahead`
    aralığına DÜŞMÜYORSA elenir. Ağır bir işlemdir (ticker başına 1-4 KAP
    isteği) -- `repository.is_earnings_calendar_fresh()` ile günde 1 kez
    sınırlanması ÖNERİLİR (bkz. modül üst notu)."""
    reference_day = today if today is not None else date.today()
    end_day = reference_day + timedelta(days=days_ahead)

    results: list[EarningsDate] = []
    for ticker, company_name in tickers:
        try:
            entry = resolve_bist_earnings_date(ticker, company_name)
        except Exception:  # noqa: BLE001 -- tek bir sirketin hatasi TUM taramayi DURDURMAMALI
            logger.exception("%s için takvim hesaplanırken beklenmeyen hata", ticker)
            continue
        if entry is not None and reference_day <= entry.expected_date <= end_day:
            results.append(entry)

    results.sort(key=lambda e: e.expected_date)
    return results


@retry(
    reraise=True,
    stop=stop_after_attempt(config.HTTP_MAX_RETRIES),
    wait=wait_fixed(config.HTTP_RATE_LIMIT_DELAY_SECONDS),
    retry=retry_if_exception_type(httpx.RequestError),
)
def _request_bist_screener(limit: int) -> dict:
    body = {
        "filter": [{"left": "exchange", "operation": "equal", "right": "BIST"}],
        "columns": ["name"],
        "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
        "range": [0, limit],
    }
    response = httpx.post("https://scanner.tradingview.com/turkey/scan", json=body, timeout=config.HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def get_bist_top_market_cap_tickers(limit: int = 100) -> list[str]:
    """TradingView tarama uç noktasından PİYASA DEĞERİNE göre ilk `limit`
    BIST sembolünü getirir.

    ⚠️ Bu, Borsa İstanbul'un RESMİ "BIST 100" endeks üyeliği DEĞİLDİR --
    o endeks likidite/serbest dolaşım gibi ek kriterlerle Borsa İstanbul
    tarafından periyodik olarak belirlenir ve bunun için ücretsiz, kayıt
    gerektirmeyen bir API bulunamadı (Faz 12 keşif kapsamında arandı).
    Piyasa değerine göre sıralama, kapsamı MAKUL ölçüde geniş tutan
    (Kural: "30 şirketle sınırlama yapma") ama YANLIŞ bir kesinlik iddia
    ETMEYEN bir YAKLAŞTIRMADIR -- kullanıcıya "BIST 100" olarak SUNULMAMALI,
    "piyasa değerine göre ilk N şirket" olarak sunulmalı.

    Ağ hatasında boş liste döner (bu YARDIMCI bir kapsam-belirleme
    fonksiyonudur, pipeline'ı bloke etmemeli)."""
    try:
        payload = _request_bist_screener(limit)
    except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as exc:
        logger.warning("BIST piyasa değeri sıralaması alınamadı: %s", exc)
        return []
    rows = payload.get("data", [])
    return [row["d"][0] for row in rows if row.get("d")]


# --- Orkestrasyon: NASDAQ -----------------------------------------------------

_NASDAQ_MONTH_TO_QUARTER: dict[str, int] = {
    "Jan": 3, "Feb": 3, "Mar": 3,
    "Apr": 6, "May": 6, "Jun": 6,
    "Jul": 9, "Aug": 9, "Sep": 9,
    "Oct": 12, "Nov": 12, "Dec": 12,
}


def _period_from_fiscal_quarter_ending(text: str) -> Period | None:
    """'Jun/2026' -> (2026, 6) -- Nasdaq'ın döndürdüğü ayı en yakın TAKVİM
    çeyrek sonuna eşler (şirketin kendi mali çeyrek numarasına DEĞİL, bkz.
    modül üst notu -- burada sadece HANGİ takvim çeyreğinin raporlandığını
    bilmek yeterli, card.py'deki 'FYyy Çn' etiketleme mantığı BURADA
    KULLANILMAZ)."""
    try:
        month_str, year_str = text.split("/")
        return (int(year_str), _NASDAQ_MONTH_TO_QUARTER[month_str])
    except (ValueError, KeyError):
        return None


@retry(
    reraise=True,
    stop=stop_after_attempt(config.HTTP_MAX_RETRIES),
    wait=wait_fixed(config.HTTP_RATE_LIMIT_DELAY_SECONDS),
    retry=retry_if_exception_type(httpx.RequestError),
)
def _request_nasdaq_calendar_day(day: date) -> dict:
    response = httpx.get(
        _NASDAQ_CALENDAR_ENDPOINT, params={"date": day.isoformat()}, headers=_NASDAQ_HEADERS,
        timeout=config.HTTP_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def fetch_upcoming_nasdaq(days_ahead: int = 30, today: date | None = None) -> list[EarningsDate]:
    """api.nasdaq.com/api/calendar/earnings uç noktasını `today`'den
    `today+days_ahead`'e kadar HER GÜN için ayrı ayrı sorgular (bu uç nokta
    per-ticker DEĞİL per-gün çalışır -- TÜM piyasanın o günkü takvimini TEK
    istekte döner, bkz. modül üst notu). Bir günün isteği başarısız olursa
    (ağ hatası, beklenmeyen şema) o gün SESSİZCE atlanır, tarama devam eder
    -- tek bir günün hatası TÜM 30 günlük taramayı DURDURMAMALI."""
    reference_day = today if today is not None else date.today()
    results: list[EarningsDate] = []

    for offset in range(days_ahead + 1):
        day = reference_day + timedelta(days=offset)
        try:
            payload = _request_nasdaq_calendar_day(day)
        except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as exc:
            logger.info("NASDAQ takvimi %s için alınamadı, atlanıyor: %s", day, exc)
            continue

        rows = (payload.get("data") or {}).get("rows") or []
        for row in rows:
            symbol = row.get("symbol")
            name = row.get("name")
            fiscal_quarter_ending = row.get("fiscalQuarterEnding")
            if not symbol or not name or not fiscal_quarter_ending:
                continue
            period = _period_from_fiscal_quarter_ending(fiscal_quarter_ending)
            if period is None:
                continue
            results.append(
                EarningsDate(
                    ticker=symbol, company_name=name, market="NASDAQ", period=period,
                    expected_date=day, confidence=CONFIDENCE_TAHMINI, source=SOURCE_NASDAQ_API,
                )
            )

    results.sort(key=lambda e: e.expected_date)
    return results
