"""BIST ve NASDAQ hisseleri icin BIRLESIK gunluk OHLCV gecmisi fetcher'i
(Faz 15 - Teknik Analiz).

Piyasaya ozgu HTTP/ayristirma mantigi zaten var olan fetcher'larda yasar
(src/fetchers/isyatirim.py::fetch_price_history, src/fetchers/sec_edgar.py::
fetch_price_history) -- bu modul sadece ikisini TEK bir tipe (OhlcvBar)
dispatch eden ince bir katmandir; ayni sekilde src/bot/pipeline.py'nin
market'e gore analyze()/analyze_us() arasinda dallanmasiyla AYNI ilke.

Iki kaynagin veri seklinin FARKLARI (Kural 3 geregi burada acikca belgelenir,
gizlenmez):
  - BIST (isyatirim.fetch_price_history): 'open' HER ZAMAN None (uc nokta
    acilis fiyati dondurmuyor); hacim TL cinsinden islem hacmidir (adet degil).
  - NASDAQ (sec_edgar.fetch_price_history): 'open' DOLU (Yahoo chart tam
    OHLCV donuyor); hacim ADET (islem gorendisi hisse sayisi) cinsindendir.
Src/analysis/technical.py'deki HICBIR gosterge (SMA/EMA/RSI/MACD/Bollinger/
ATR/52 hafta/hacim orani) acilis fiyatina ihtiyac DUYMAZ ve hacim SADECE
kendi 20 gunluk ortalamasiyla ORANLANIR (birimler arasi karsilastirma
YAPILMAZ) -- bu yuzden iki kaynak arasindaki birim farki asagi akista
(technical.py, kart) bir sorun TESKIL ETMEZ.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from src.fetchers import isyatirim, sec_edgar

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OhlcvBar:
    """Tek bir gunluk mum. `open` piyasaya gore None olabilir (bkz. modul notu)."""

    trade_date: date
    open: Decimal | None
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


def fetch_ohlcv(ticker: str, market: str, days: int = 400) -> list[OhlcvBar]:
    """Son `days` gunun gunluk OHLCV serisini artan tarih sirasinda doner.

    `days=400`: 200 gunluk hareketli ortalama (SMA200) icin en az 200 bar +
    bir yillik grafik/52 hafta yuksek-dusuk hesaplarken haftasonu/tatil
    bosluklarini tolere edecek tampon (Faz 15 gorev talimatinin gerekcesi).

    Sirket icin veri yoksa VEYA ag hatasi olusursa BOS liste doner -- bu
    supplementary/ikincil bir veridir (Kural 9), cagiran taraf (pipeline/kart
    orkestrasyonu) bunun icin ASLA akisi bloke ETMEMELIDIR; teknik kart
    "yeterli veri yok" olarak uretilir.

    Hatalar: FIRLATMAZ.
    """
    if market == "NASDAQ":
        raw_bars = sec_edgar.fetch_price_history(ticker, days=days)
    else:
        raw_bars = isyatirim.fetch_price_history(ticker, days=days)

    bars = [
        OhlcvBar(
            trade_date=raw["date"],
            open=raw["open"],
            high=raw["high"],
            low=raw["low"],
            close=raw["close"],
            volume=raw["volume"],
        )
        for raw in raw_bars
    ]
    bars.sort(key=lambda bar: bar.trade_date)
    return bars
