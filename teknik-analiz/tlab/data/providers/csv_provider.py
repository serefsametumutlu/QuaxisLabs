"""Kullanıcı CSV/parquet dosyalarından okuyan sağlayıcı.

İleride TradingView export ve Fintables köprüsü için kullanılacak. Kolon
başlıkları Türkçe/İngilizce ve büyük-küçük harf duyarsız eşlenir.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from tlab.core.types import Market, Timeframe, validate_ohlcv
from tlab.data.providers.base import DataProvider

_COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "datetime": ("datetime", "date", "time", "tarih", "zaman"),
    "open": ("open", "acilis", "açılış", "açilis"),
    "high": ("high", "yuksek", "yüksek"),
    "low": ("low", "dusuk", "düşük"),
    "close": ("close", "kapanis", "kapanış"),
    "volume": ("volume", "hacim"),
}


def _resolve_columns(columns: list[str]) -> dict[str, str]:
    """Serbest başlıkları (TR/EN, büyük-küçük harf duyarsız) standart isimlere eşler."""
    lower = {c: c.strip().lower() for c in columns}
    resolved: dict[str, str] = {}
    for standard, aliases in _COLUMN_ALIASES.items():
        match = next((orig for orig, low in lower.items() if low in aliases), None)
        if match is None:
            raise ValueError(
                f"Kolon eşlemesi bulunamadı: '{standard}' (mevcut kolonlar: {columns})"
            )
        resolved[standard] = match
    return resolved


class CSVProvider(DataProvider):
    """{data_dir}/{symbol}_{timeframe}.(csv|parquet) dosyalarından okur."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = Path(data_dir)

    def fetch(
        self,
        symbol: str,
        market: Market,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        path_parquet = self._data_dir / f"{symbol}_{timeframe.value}.parquet"
        path_csv = self._data_dir / f"{symbol}_{timeframe.value}.csv"
        if path_parquet.exists():
            raw = pd.read_parquet(path_parquet)
        elif path_csv.exists():
            raw = pd.read_csv(path_csv)
        else:
            raise FileNotFoundError(
                f"{symbol} ({timeframe.value}) için CSV/parquet bulunamadı: {self._data_dir}"
            )

        columns = _resolve_columns(list(raw.columns))
        df = raw.rename(columns={v: k for k, v in columns.items()})
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.set_index("datetime")[["open", "high", "low", "close", "volume"]]
        df = self._normalize_tz(df, market)

        start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(end)
        if start_ts.tzinfo is None:
            start_ts = start_ts.tz_localize(df.index.tz)
        if end_ts.tzinfo is None:
            end_ts = end_ts.tz_localize(df.index.tz)
        df = df.loc[(df.index >= start_ts) & (df.index <= end_ts)]

        validate_ohlcv(df)
        return df
