"""Veri sağlayıcı taban sınıfı ve sembol/saat dilimi normalizasyonu."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd

from tlab.core.types import Market, Timeframe, validate_ohlcv

MARKET_TZ: dict[Market, str] = {
    Market.BIST: "Europe/Istanbul",
    Market.NASDAQ: "America/New_York",
}


def to_provider_symbol(symbol: str, market: Market) -> str:
    """İç temsildeki sembolü (ör. "TCELL") sağlayıcının beklediği forma çevirir."""
    if market is Market.BIST:
        return f"{symbol}.IS"
    return symbol


class DataProvider(ABC):
    """Tüm veri sağlayıcılarının uyduğu sözleşme.

    fetch, validate_ohlcv'den geçmiş (şema/tutarlılık doğrulanmış), market'in
    yerel saat diliminde tz-aware bir OHLCV DataFrame döner.
    """

    @abstractmethod
    def fetch(
        self,
        symbol: str,
        market: Market,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        """symbol için [start, end] aralığında OHLCV verisi getirir."""

    @staticmethod
    def _normalize_tz(df: pd.DataFrame, market: Market) -> pd.DataFrame:
        """Index'i sırala, tekrarları at, market'in yerel saat dilimine çevir."""
        df = df.sort_index()
        df = df[~df.index.duplicated(keep="last")]
        tz = MARKET_TZ[market]
        if df.index.tz is None:
            df = df.tz_localize(tz)
        else:
            df = df.tz_convert(tz)
        return df

    @classmethod
    def _finalize(cls, df: pd.DataFrame, market: Market) -> pd.DataFrame:
        df = cls._normalize_tz(df, market)
        validate_ohlcv(df)
        return df
