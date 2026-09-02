"""yfinance tabanlı OHLCV veri sağlayıcısı.

yfinance, 60m (1H) çözünürlükte yalnızca son ~730 günü döndürür (Yahoo Finance
API kısıtı — daha eski başlangıç tarihi istense de sağlayıcı sessizce daha
yakın bir tarihten başlar). Bu yüzden tam 1H geçmişi tek seferde alınamaz;
store.update() artımlı çağrılarla zaman içinde cache'i genişletir. fetch()
istenen başlangıçla fiilen dönen başlangıcı karşılaştırıp fark varsa uyarır.

adjusted=True (ayarlanmış kapanış) istendiğinde open/high/low/close tutarlı
kalsın diye (validate_ohlcv'nin high>=max(open,close) kuralı) iki ayrı çağrı
yapılır: biri auto_adjust=True ile tüm OHLC'yi orantılı ayarlar, diğeri
auto_adjust=False ile yalnızca ham kapanışı (close_raw) almak içindir. Tek
çağrıda auto_adjust=False bırakıp yalnızca close'u ayarlamak, split sonrası
high < close gibi şema ihlallerine yol açabileceğinden tercih edilmedi.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from tlab.core.types import Market, Timeframe
from tlab.data.providers.base import DataProvider, to_provider_symbol
from tlab.data.settings import Settings, load_settings

logger = logging.getLogger(__name__)

_YF_INTERVAL: dict[Timeframe, str] = {
    Timeframe.H1: "60m",
    Timeframe.D1: "1d",
}

# 2026-09-03 GERÇEK HATA: modülün kendi docstring'i yfinance'ın 730 günden
# eski bir `start` istendiğinde SESSİZCE daha yakın bir tarihten başladığını
# varsayıyordu (`_warn_if_truncated` bu varsayıma göre yazılmıştı) — ama
# `start` PENCERENİN TAMAMEN DIŞINDAysa (ör. hiç cache'i olmayan bir sembol
# için `store.update()`'in sabit `datetime(2020,1,1)` başlangıcı), yfinance
# sessizce kısaltmıyor, TÜMÜYLE BOŞ dönüyor — `raw.empty` → `ValueError`
# ("veri dönmedi"). Gerçek veride 648 sembolün 583'ünde bu yüzden 1H/4H
# hiç cache'lenemiyordu. `start`'ı indirmeden ÖNCE pencereye kelepçelemek
# (clamp) bu tam-boş-dönüş durumunu baştan önlüyor.
_H1_MAX_LOOKBACK_DAYS = 729


class YFinanceProvider(DataProvider):
    """yfinance.download üzerinden 1H ve 1D OHLCV verisi çeker."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or load_settings()

    def fetch(
        self,
        symbol: str,
        market: Market,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        if timeframe not in _YF_INTERVAL:
            raise ValueError(
                f"YFinanceProvider yalnızca {list(_YF_INTERVAL)} destekler, alınan: {timeframe}"
            )

        yf_symbol = to_provider_symbol(symbol, market)
        interval = _YF_INTERVAL[timeframe]
        adjusted = self._settings.adjusted

        if timeframe is Timeframe.H1:
            min_start = end - timedelta(days=_H1_MAX_LOOKBACK_DAYS)
            if start < min_start:
                start = min_start

        raw = yf.download(
            yf_symbol,
            start=start,
            end=end,
            interval=interval,
            auto_adjust=adjusted,
            progress=False,
            multi_level_index=False,
        )
        if raw.empty:
            raise ValueError(f"{yf_symbol} ({timeframe.value}) için veri dönmedi")

        if timeframe is Timeframe.H1:
            self._warn_if_truncated(raw.index[0], start, yf_symbol)

        df = raw.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].copy()

        if adjusted:
            raw_unadjusted = yf.download(
                yf_symbol,
                start=start,
                end=end,
                interval=interval,
                auto_adjust=False,
                progress=False,
                multi_level_index=False,
            )
            df["close_raw"] = raw_unadjusted["Close"].reindex(df.index)
        else:
            df["close_raw"] = df["close"]

        return self._finalize(df, market)

    def _warn_if_truncated(
        self, actual_start: pd.Timestamp, wanted_start: datetime, yf_symbol: str
    ) -> None:
        wanted_ts = pd.Timestamp(wanted_start)
        if actual_start.tzinfo is not None and wanted_ts.tzinfo is None:
            wanted_ts = wanted_ts.tz_localize(actual_start.tzinfo)
        if actual_start > wanted_ts:
            logger.warning(
                "%s: yfinance 1H verisi %s'den önceye gitmiyor (istenen: %s) — "
                "~%d günlük sağlayıcı limiti",
                yf_symbol,
                actual_start,
                wanted_ts,
                self._settings.yfinance_h1_max_lookback_days,
            )
