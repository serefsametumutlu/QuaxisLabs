"""TradingView scanner uc noktasindan BIST hisseleri icin TOPLU (tek
istekte birden fazla sembol) gunluk % degisim -- Faz 19.1 (2026-08-06,
kullanici raporu) ikinci duzeltme turu.

🚨 NEDEN GEREKTI: `yahoo_quote.fetch_daily_return()` (bkz. o modulun ust
notu #2) GUNLUK BAR dizisinden hesap yapiyor -- bu dizi SADECE
GERCEKLESEN bir islemde guncelleniyor. Az islem goren BIST hisselerinde
(orn. OZATD) bu, ayni fiyatin DAKIKALARCA/SAATLERCE degismeden kalmasina
ve/veya borsa geneli bir veri bosluguna (bkz. yahoo_quote.py) yol
aciyordu. CANLI KIYASLANDI (2026-08-06, fvt.com.tr'nin kendi "KAP
Dagilimina Gore" tahminiyle): TradingView'in `change` alani FVT'nin
gosterdigi rakamlarla Yahoo'dan cok daha yakin cikiyor (DSTKF: TradingView
+%7,74 vs FVT +%7,37 vs Yahoo +%4,05; HEDEF: TradingView -%9,94 = FVT'nin
kendi ekran goruntusundeki -%9,94 ile BIREBIR).

Yanit meta verisinde `update_mode: "delayed_streaming_900"` donuyor --
yani 15 DAKIKA gecikmeli CANLI akis. Bu, fvt.com.tr sitesinin kendi
belirttigi "Veriler 15 dakika gecikmelidir" notuyla BIREBIR ortusuyor
(bkz. `scripts/explore_tradingview_quote.py`, `data/exploration/
tradingview_scanner_quote_*.json`) -- muhtemelen ayni sinif/saglayicidan
gelen bir veri, salt tesaduf DEGIL.

Bu uc nokta proje icinde ZATEN GUVENILIR/kullanimda: `company_logo.py`
(scanner.tradingview.com/symbol) ve `earnings_calendar.py`
(scanner.tradingview.com/turkey/scan, BIST piyasa degeri siralamasi icin)
AYNI aileyi kullaniyor -- Kural 3 anlaminda tamamen yeni/dogrulanmamis
bir kaynak DEGIL.

TOPLU sorgu avantaji: fon basina TEK bir istekle TUM hisse holding'lerinin
getirisi cekilebiliyor (eskiden `yahoo_quote` ile HER ticker icin AYRI bir
istek/thread gerekiyordu, bkz. `fund_pipeline._PRICE_FETCH_MAX_WORKERS`
ust notu -- 24 kalemli TLY icin ONCEDEN paralel bile onlarca saniye
surebiliyordu).

Bu modul BILEREK savunmaci: TUM hatalar (ag, parse, HTTP durum kodu)
SESSIZCE bos sozluk doner -- fon tahmini IKINCIL/deneysel bir ozellik
(Kural 9), cagiran taraf (`fund_pipeline.py`) eksik kalan ticker'lari
otomatik `yahoo_quote` yedegine dusurur.
"""

from __future__ import annotations

import logging
from decimal import Decimal

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

import config

logger = logging.getLogger(__name__)

_SCAN_ENDPOINT = "https://scanner.tradingview.com/turkey/scan"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.tradingview.com/",
}


class TradingViewQuoteError(Exception):
    """TradingView scanner fetcher'ı için taban hata sınıfı."""


@retry(
    reraise=True,
    stop=stop_after_attempt(config.HTTP_MAX_RETRIES),
    wait=wait_fixed(config.HTTP_RATE_LIMIT_DELAY_SECONDS),
    retry=retry_if_exception_type(httpx.RequestError),
)
def _request_scan(tickers: list[str]) -> dict:
    body = {
        "symbols": {"tickers": [f"BIST:{t}" for t in tickers]},
        "columns": ["change"],
    }
    try:
        response = httpx.post(_SCAN_ENDPOINT, json=body, headers=_HEADERS, timeout=config.HTTP_TIMEOUT_SECONDS)
    except httpx.RequestError as exc:
        logger.warning("TradingView scanner isteği başarısız, yeniden denenecek: %s", exc)
        raise
    if response.status_code != 200:
        raise TradingViewQuoteError(f"TradingView scanner beklenmeyen HTTP durum kodu döndürdü: {response.status_code}")
    try:
        return response.json()
    except ValueError as exc:
        raise TradingViewQuoteError("TradingView scanner yanıtı JSON olarak ayrıştırılamadı.") from exc


def fetch_daily_returns(tickers: list[str]) -> dict[str, Decimal]:
    """Verilen BİST ticker'ları için TEK istekte günlük %değişimi döner.

    Argümanlar:
        tickers: "BIST:" ön eki OLMADAN, örn. ["OZATD", "THYAO"].

    Dönen değer:
        {ticker: Decimal(yüzde_değişim)} -- TradingView'de bulunamayan
        (yanlış kod, fon-içinde-fon TEFAS kodu gibi borsa dışı semboller,
        vb.) ticker'lar sözlükte YOK olur, hata FIRLATILMAZ (Kural 9).
        Ağ/parse hatasında BOŞ sözlük döner -- çağıran taraf (Kural 9)
        bunu "bu turdaki tüm hisseler fiyatlandırılamadı" sayıp
        `yahoo_quote` yedeğine düşer.
    """
    unique_tickers = sorted({t.strip().upper() for t in tickers if t and t.strip()})
    if not unique_tickers:
        return {}

    try:
        payload = _request_scan(unique_tickers)
    except (TradingViewQuoteError, httpx.RequestError) as exc:
        logger.warning("TradingView scanner'dan günlük getiri çekilemedi: %s", exc)
        return {}

    results: dict[str, Decimal] = {}
    for row in payload.get("data", []):
        symbol = row.get("s", "")
        values = row.get("d")
        if not symbol.startswith("BIST:") or not values:
            continue
        ticker = symbol.split(":", 1)[1]
        change = values[0]
        if change is None:
            continue
        try:
            results[ticker] = Decimal(str(change))
        except (ValueError, ArithmeticError):
            logger.warning("%s için TradingView 'change' alanı sayısal değil: %r", ticker, change)

    return results
