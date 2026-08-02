"""Sirket logolarini TradingView'in scanner sorgu + logo CDN uc noktalarindan
ceker, diskte KALICI olarak onbellege alir. BIST VE NASDAQ (Faz 10) destekler.

Bu uc noktalar TradingView tarafindan resmi/belgelenmis DEGIL. Onceki
surumde kullanilan symbol_search/v3 uc noktasi artik nginx seviyesinde
KALICI 403 donuyor (IP/istek imzasi fark etmeksizin); bu yuzden
scanner.tradingview.com/symbol uc noktasina gecildi -- tek sembol icin
dogrudan logoid dondurur ve ayni kisitlamaya tabi degil (logo CDN'in
kendisi -- s3-symbol-logo.tradingview.com -- de bu kisitlamaya tabi
degil). Bu yuzden modul BILEREK savunmaci: her hata SESSIZCE None
doner, CardRenderError FIRLATILMAZ -- logo karti KIRACAK kadar kritik
bir bilgi degil, sadece kozmetik bir zenginlestirme.

Faz 10 (NASDAQ): TradingView'in sembol borsasi ONEKI gerektirir (BIST icin
sabit "BIST", ABD icin TEK bir onek YETERLI DEGIL -- CANLI dogrulandi:
"NASDAQ:AAPL"/"NASDAQ:NVDA"/"NASDAQ:INTC" calisiyor ama "NASDAQ:JPM" 404
donuyor, JPM "NYSE:JPM" ile bulunuyor). Bu yuzden `market="NASDAQ"` icin
ONCE "NASDAQ:" sonra "NYSE:" denenir (_EXCHANGE_CANDIDATES) -- projenin
resmi NASDAQ evrenindeki 10 hisse (AAPL/TSLA/NVDA/MSFT/GOOGL/AMZN/META/
NFLX/AMD/PYPL) HEPSI NASDAQ borsasinda, bu yuzden ilk denemede bulunur;
NYSE fallback'i sadece genellik/saglamlik icin.

Onbellek stratejisi (data/logos/{TICKER}.svg BIST icin, data/logos/{MARKET}_{TICKER}.svg
NASDAQ icin -- iki market arasinda dosya adi CAKISMASINI ONLEMEK icin, bkz.
repository.TickerMarketConflictError ile AYNI ilke) GECICI hatalari (agresif
rate-limit, aginin o an ulasilamaz olmasi) KALICI "bu hisse icin logo
yok" sonucundan AYIRT EDER: yalnizca arama uc noktasi (denenen TUM borsa
oneklerinde) basariyla yanit verip eslesme BULAMADIYSA bos bir dosya
yazilarak kalici olarak isaretlenir; agdaki gecici bir hata ONBELLEGE
YAZILMAZ, bir sonraki istekte tekrar denenir.
"""

from __future__ import annotations

import base64
import logging
import re
from pathlib import Path

import httpx

import config

logger = logging.getLogger(__name__)

_SEARCH_ENDPOINT = "https://scanner.tradingview.com/symbol"
_LOGO_CDN_TEMPLATE = "https://s3-symbol-logo.tradingview.com/{logoid}--big.svg"
_LOGO_DIR = config.DATA_DIR / "logos"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.tradingview.com/",
}

# BIST hisse kodlari 2-6 harf/rakamdir; gelisigüzel girdiyi dis servise
# gondermeden once eleyip gereksiz istek yapmayi onler.
_TICKER_RE = re.compile(r"^[A-Z0-9]{2,10}$")

# market -> denenecek TradingView borsa onekleri (sirayla, ilk logoid
# donduren kazanir). CANLI dogrulandi (bkz. modul ust notu).
_EXCHANGE_CANDIDATES: dict[str, list[str]] = {
    "BIST": ["BIST"],
    "NASDAQ": ["NASDAQ", "NYSE"],
}


def _cache_path(ticker: str, market: str) -> Path:
    if market == "BIST":
        return _LOGO_DIR / f"{ticker}.svg"
    return _LOGO_DIR / f"{market}_{ticker}.svg"


def _to_data_uri(svg_bytes: bytes) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg_bytes).decode("ascii")


def _resolve_logoid(ticker: str, market: str) -> tuple[str | None, bool]:
    """(logoid, arama_basarili_mi) doner. Arama basarisiz olduysa (agdaki
    gecici bir hata) ikinci deger False'tur -- caller bu durumda onbellege
    HICBIR SEY yazmamali. TUM borsa onekleri (bkz. _EXCHANGE_CANDIDATES)
    basariyla denendi ama eslesme yoksa (None, True) doner -- bu KALICI
    bir "logo yok" sonucudur."""
    for exchange in _EXCHANGE_CANDIDATES.get(market, [market]):
        params = {"symbol": f"{exchange}:{ticker}", "fields": "logoid"}
        try:
            resp = httpx.get(_SEARCH_ENDPOINT, params=params, headers=_HEADERS, timeout=config.HTTP_TIMEOUT_SECONDS)
            if resp.status_code == 404:
                continue
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            logger.info(
                "%s icin logo aranamadi (%s:%s sembol aramasi basarisiz, sonraki istekte tekrar denenecek)",
                ticker, exchange, ticker,
            )
            return None, False

        logoid = data.get("logoid")
        if logoid:
            return logoid, True

    return None, True


def _download_logo(logoid: str) -> bytes | None:
    try:
        resp = httpx.get(
            _LOGO_CDN_TEMPLATE.format(logoid=logoid), headers=_HEADERS, timeout=config.HTTP_TIMEOUT_SECONDS
        )
        resp.raise_for_status()
        return resp.content
    except Exception:
        logger.info("logoid=%s icin logo indirilemedi (sonraki istekte tekrar denenecek)", logoid)
        return None


def fetch_logo_data_uri(ticker: str, market: str = "BIST") -> str | None:
    """`ticker` icin sirket logosunu base64 SVG data URI olarak doner.
    `market`: "BIST" (varsayilan) veya "NASDAQ" (Faz 10, bkz. modul ust
    notu -- birden fazla borsa oneki denenir). Bulunamazsa, gecersiz bir
    kodsa veya herhangi bir agirlik hatasi olursa None doner -- caller
    (src.render.card) bu durumda karti logosuz render eder."""
    ticker = ticker.strip().upper()
    if not _TICKER_RE.match(ticker):
        return None

    cache_file = _cache_path(ticker, market)
    if cache_file.exists():
        svg_bytes = cache_file.read_bytes()
        return _to_data_uri(svg_bytes) if svg_bytes else None

    logoid, search_succeeded = _resolve_logoid(ticker, market)
    if logoid is None:
        if search_succeeded:
            _LOGO_DIR.mkdir(parents=True, exist_ok=True)
            cache_file.write_bytes(b"")
        return None

    svg_bytes = _download_logo(logoid)
    if svg_bytes is None:
        return None

    _LOGO_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_bytes(svg_bytes)
    return _to_data_uri(svg_bytes)
