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

🚨 CANLI HATA #2 (2026-08-06, kullanıcı raporu -- TLY fon tahmini
Fintables'ın "AI Tahmini"nden [%0,17] KAT KAT büyük [%3,14] çıkıyordu):
`fetch_daily_return()` ESKİDEN "close" dizisindeki None'ları FİLTRELEYİP
son İKİ GEÇERLİ değeri kullanıyordu ("bir tatil gününü atla" senaryosu
için tasarlanmıştı). CANLI teşhis: 2026-08-06'da Yahoo'nun TÜM `.IS`
sembolleri (THYAO/GARAN dahil, sadece küçük/likit olmayan hisselere özgü
DEĞİL) için 2026-08-05 kapanışı None geliyordu -- muhtemelen Yahoo'nun
BIST veri beslemesinde GEÇİCİ bir boşluk/gecikme (AAPL/NASDAQ'ta AYNI anda
HİÇBİR boşluk YOKTU, yani borsaya özgü bir sağlayıcı sorunu). Eski kod bu
durumda 2 gün öncesine (04/08) atlayıp 04/08→06/08 arasındaki TÜM hareketi
(gerçekte 05/08'de ZATEN gerçekleşmiş, "eski haber" olan bir fiyat sıçraması
dahil) "BUGÜNKÜ getiri" gibi sunuyordu -- OZATD örneğinde tek başına +%7,4
"bugünkü değişim" üretti, gerçek anlık değişim (Fintables) ise -%0,06 idi.
Bu, projenin `isyatirim.py` ile yaşadığı "dünkü veri" hatasının (bkz.
`PROJE_HAFIZASI/06_BILINEN_SORUNLAR.md` §B30, ilk CANLI hata) BİREBİR AYNI
sınıfta, farklı bir kaynaktan (Yahoo) gelen tekrarıydı. **Düzeltme**: artık
None'lar FİLTRELENMEZ -- SADECE dizinin son İKİ pozisyonu (bugün + dün
OLMASI gereken bar) kullanılır; ikisinden biri None ise (veri sağlayıcı
boşluğu VEYA piyasa bugün için henüz güncellenmedi) SESSİZCE `None` döner
(Kural 3: 2 gün öncesine atlayıp yanlış/şişirilmiş bir "günlük" getiri
üretmektense hiç üretmemek tercih edilir).
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

    ⚠️ Dizinin SADECE son iki POZİSYONU (bugün + dün olması gereken bar)
    kullanılır -- daha eskiye ATLANMAZ. Biri None ise (veri sağlayıcı
    boşluğu VEYA piyasa henüz güncellenmedi) None döner; aksi halde 2 gün
    öncesine sessizce atlamak, aradaki günün GERÇEK (ama "eski haber" olan)
    fiyat hareketini "bugünkü" getiriye SIZDIRIR (CANLI hata, bkz. modül
    üst notu #2).

    Bu YARDIMCI/İKİNCİL bir veridir (Kural 9) -- ağ/parse hatası VEYA
    yetersiz/boşluklu veri SESSİZCE None ile sonuçlanır, hata FIRLATILMAZ;
    çağıran taraf (fon tahmini) bunu "fiyatlandırılamadı" sayar.
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

    if len(closes) < 2:
        return None

    prev_price, last_price = closes[-2], closes[-1]
    if prev_price is None or last_price is None:
        logger.info("%s için ardışık son iki günlük kapanıştan biri eksik (None) -- güvenilir bir 'bugünkü getiri' hesaplanamıyor.", symbol)
        return None
    if not prev_price:
        return None
    return (Decimal(str(last_price)) / Decimal(str(prev_price)) - Decimal(1)) * Decimal(100)
