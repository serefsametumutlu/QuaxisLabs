"""Yahoo Finance chart uç noktasından GÜNCEL (bugünkü) günlük getiri --
Faz 19, kullanıcı raporuyla bulunan KRİTİK bir düzeltme.

🚨 CANLI HATA (2026-08-05): `src.bot.fund_pipeline` önceden BİST hisseleri
için `isyatirim.fetch_price_history()`'yi kullanıyordu -- CANLI doğrulandı,
bu uç nokta BUGÜNÜN kapanışını YAYINLAMIYOR, en güncel satırı DÜNÜN
kapanışı (bir tam gün gecikmeli). Kullanıcı somut bir örnekle yakaladı:
OZATD bugün %8,41 ile kapanmışken kart %2,55 gösteriyordu -- bu, isyatirim
verisiyle 03/08→04/08 (dünkü) getiriydi, 04/08→05/08 (bugünkü) DEĞİL.

Yahoo Finance'in `v8/finance/chart/{ticker}.IS` uç noktası (NASDAQ için
zaten `sec_edgar.py`'de KULLANILAN, aynı public/kimliksiz API) CANLI test
edildi: OZATD.IS için 05/08 kapanışı (4477,5) MEVCUT ve (4477,5/4130,0-1)
*100 = %8,417 -- kullanıcının bildirdiği %8,41 ile (yuvarlama farkı hariç)
BİREBİR eşleşti. Bu yüzden BİST günlük getirisi ARTIK BU modülden alınır
-- `isyatirim.py` diğer TÜM kullanımlarında (teknik analiz, 400 günlük
seri) DEĞİŞTİRİLMEDİ, çünkü o akışlarda "bugünün getirisi" değil uzun
geçmiş seri önemlidir ve isyatirim'in gecikmesi sonuç etkilemez.

⚠️ Piyasa AÇIKKEN Yahoo'nun 'close' alanı o anki ANLIK/güncel fiyatı
taşır (gerçek kapanış DEĞİL, gün bitene kadar değişebilir) -- bu modül
"o ana kadarki en güncel fiyat" sağlar, gerçek zamanlı/15-dk-gecikmeli
garantisi VERMEZ (Yahoo'nun kendi gecikme politikası bilinmiyor, Kural 8).
"""

from __future__ import annotations

import logging
from decimal import Decimal

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

import config

logger = logging.getLogger(__name__)

_CHART_ENDPOINT = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}


class YahooQuoteError(Exception):
    """Yahoo chart fetcher'ı için taban hata sınıfı."""


class YahooQuoteNetworkError(YahooQuoteError):
    """Ağ hatası veya beklenmeyen yanıt biçimi."""


@retry(
    reraise=True,
    stop=stop_after_attempt(config.HTTP_MAX_RETRIES),
    wait=wait_fixed(config.HTTP_RATE_LIMIT_DELAY_SECONDS),
    retry=retry_if_exception_type(httpx.RequestError),
)
def _request_chart(symbol: str) -> dict:
    url = _CHART_ENDPOINT.format(ticker=symbol)
    try:
        response = httpx.get(
            url, params={"range": "5d", "interval": "1d"}, headers=_HEADERS, timeout=config.HTTP_TIMEOUT_SECONDS
        )
    except httpx.RequestError as exc:
        logger.warning("Yahoo chart isteği başarısız (%s), yeniden denenecek: %s", symbol, exc)
        raise
    if response.status_code != 200:
        raise YahooQuoteNetworkError(f"Yahoo chart beklenmeyen HTTP durum kodu döndürdü: {response.status_code} ({symbol})")
    try:
        return response.json()
    except ValueError as exc:
        raise YahooQuoteNetworkError(f"Yahoo chart yanıtı JSON olarak ayrıştırılamadı ({symbol}).") from exc


def fetch_daily_return(ticker: str, suffix: str = "") -> Decimal | None:
    """`ticker + suffix` (BİST için `suffix=".IS"`, örn. "OZATD.IS")
    sembolünün EN GÜNCEL iki günlük kapanışından yüzde getiriyi döner.

    Bu YARDIMCI/İKİNCİL bir veridir (Kural 9) -- ağ/parse hatası VEYA
    yetersiz veri (< 2 geçerli kapanış) SESSİZCE None ile sonuçlanır,
    hata FIRLATILMAZ; çağıran taraf (fon tahmini) bunu "fiyatlandırılamadı"
    sayar.
    """
    symbol = f"{ticker.strip().upper()}{suffix}"
    try:
        payload = _request_chart(symbol)
    except (YahooQuoteError, httpx.RequestError) as exc:
        logger.warning("%s için Yahoo günlük getirisi çekilemedi: %s", symbol, exc)
        return None

    try:
        result = payload["chart"]["result"][0]
        closes = result["indicators"]["quote"][0]["close"]
    except (KeyError, IndexError, TypeError) as exc:
        logger.warning("%s için Yahoo chart yanıtı beklenmeyen biçimde: %s", symbol, exc)
        return None

    valid_closes = [c for c in closes if c is not None]
    if len(valid_closes) < 2:
        return None

    prev_price, last_price = valid_closes[-2], valid_closes[-1]
    if not prev_price:
        return None
    return (Decimal(str(last_price)) / Decimal(str(prev_price)) - Decimal(1)) * Decimal(100)
