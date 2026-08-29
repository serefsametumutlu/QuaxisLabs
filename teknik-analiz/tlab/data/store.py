"""Parquet tabanlı OHLCV önbelleği ve artımlı güncelleme.

data/ohlcv/{market}/{symbol}/{tf}.parquet. 4H her zaman 1H'den, W1 her zaman
1D'den türetilir ve kaynakları güncellendiğinde yeniden üretilir — asla
doğrudan sağlayıcıdan çekilmez.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from tlab.core.types import Market, Timeframe, validate_ohlcv
from tlab.data.providers.base import DataProvider
from tlab.data.resample import resample_to_4h, resample_to_w1
from tlab.data.settings import Settings, load_settings

DEFAULT_DATA_ROOT = Path("data/ohlcv")
OVERLAP_BARS = 5
_RAW_TIMEFRAMES = (Timeframe.H1, Timeframe.D1)


def _parquet_path(root: Path, market: Market, symbol: str, timeframe: Timeframe) -> Path:
    return root / market.value / symbol / f"{timeframe.value}.parquet"


class Store:
    """1H/1D ham veriyi provider'dan çeker, 4H'yi 1H'den türetir; parquet'e yazar."""

    def __init__(
        self,
        provider: DataProvider,
        root: Path = DEFAULT_DATA_ROOT,
        settings: Settings | None = None,
    ) -> None:
        self._provider = provider
        self._root = root
        self._settings = settings or load_settings()

    def get(
        self, symbol: str, timeframe: Timeframe, market: Market, last_n: int | None = None
    ) -> pd.DataFrame:
        path = _parquet_path(self._root, market, symbol, timeframe)
        if not path.exists():
            raise FileNotFoundError(
                f"{symbol} ({timeframe.value}) için cache yok, önce update() çağrılmalı: {path}"
            )
        df = pd.read_parquet(path)
        return df.tail(last_n) if last_n is not None else df

    def update(
        self,
        symbol: str,
        market: Market,
        start: datetime,
        end: datetime | None = None,
        timeframes: tuple[Timeframe, ...] = _RAW_TIMEFRAMES,
    ) -> None:
        """Ham (H1/D1) veriyi artımlı çeker, cache'i günceller.

        H1 güncellendiyse 4H otomatik olarak yeniden türetilir (asla
        doğrudan sağlayıcıdan çekilmez).
        """
        end = end or datetime.now(UTC)

        for tf in timeframes:
            self._update_one(symbol, market, tf, start, end)

        if Timeframe.H1 in timeframes:
            h1 = self.get(symbol, Timeframe.H1, market)
            h4 = resample_to_4h(h1, market, nasdaq_split=self._settings.nasdaq_4h_split)
            h4_path = _parquet_path(self._root, market, symbol, Timeframe.H4)
            h4_path.parent.mkdir(parents=True, exist_ok=True)
            h4.to_parquet(h4_path)

        if Timeframe.D1 in timeframes:
            d1 = self.get(symbol, Timeframe.D1, market)
            w1 = resample_to_w1(d1, market)
            w1_path = _parquet_path(self._root, market, symbol, Timeframe.W1)
            w1_path.parent.mkdir(parents=True, exist_ok=True)
            w1.to_parquet(w1_path)

    def _update_one(
        self, symbol: str, market: Market, tf: Timeframe, start: datetime, end: datetime
    ) -> None:
        path = _parquet_path(self._root, market, symbol, tf)
        path.parent.mkdir(parents=True, exist_ok=True)

        existing: pd.DataFrame | None = None
        fetch_start = start
        if path.exists():
            existing = pd.read_parquet(path)
            if len(existing) > 0:
                overlap_idx = max(len(existing) - OVERLAP_BARS, 0)
                fetch_start = existing.index[overlap_idx].to_pydatetime()

        fresh = self._provider.fetch(symbol, market, tf, fetch_start, end)

        if existing is not None and len(existing) > 0:
            fetch_start_ts = pd.Timestamp(fetch_start)
            if fetch_start_ts.tzinfo is None:
                fetch_start_ts = fetch_start_ts.tz_localize(existing.index.tz)
            combined = pd.concat([existing[existing.index < fetch_start_ts], fresh])
        else:
            combined = fresh

        combined = combined.sort_index()
        combined = combined[~combined.index.duplicated(keep="last")]
        validate_ohlcv(combined)
        combined.to_parquet(path)
