"""Store.update artımlı güncelleme idempotentliği ve get() testleri."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from tlab.core.types import Market, Timeframe
from tlab.data.providers.base import DataProvider
from tlab.data.settings import Settings
from tlab.data.store import Store

TZ = ZoneInfo("Europe/Istanbul")
TRADING_DAYS = ["2026-08-24", "2026-08-25"]  # Pazartesi, Salı — tatil/hafta sonu değil


class FakeProvider(DataProvider):
    """Deterministik sentetik OHLCV üreten test sağlayıcısı (ağ gerektirmez)."""

    def fetch(self, symbol, market, timeframe, start, end) -> pd.DataFrame:
        if timeframe is Timeframe.H1:
            rows = [
                (pd.Timestamp(f"{day} {h:02d}:00", tz=TZ), h)
                for day in TRADING_DAYS
                for h in range(10, 18)
            ]
        else:
            rows = [(pd.Timestamp(f"{day} 00:00", tz=TZ), 0) for day in TRADING_DAYS]

        start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(end)
        if start_ts.tzinfo is None:
            start_ts = start_ts.tz_localize(TZ)
        if end_ts.tzinfo is None:
            end_ts = end_ts.tz_localize(TZ)
        rows = [(ts, v) for ts, v in rows if start_ts <= ts <= end_ts]
        if not rows:
            raise ValueError("aralıkta sentetik veri yok")

        records = [
            {
                "open": 100.0 + v, "high": 101.0 + v,
                "low": 99.0 + v, "close": 100.5 + v, "volume": 1000.0,
            }
            for _, v in rows
        ]
        df = pd.DataFrame(records, index=pd.DatetimeIndex([ts for ts, _ in rows]))
        return self._finalize(df, market)


@pytest.fixture
def store(tmp_path: Path) -> Store:
    settings = Settings()
    return Store(FakeProvider(), root=tmp_path, settings=settings)


def test_update_writes_h1_h4_d1(store: Store) -> None:
    start = datetime(2026, 8, 23, 12, 0, tzinfo=UTC)  # Istanbul (+3) 24 Ağustos 00:00'dan önce
    end = datetime(2026, 8, 25, 23, 0, tzinfo=UTC)
    store.update("TESTSYM", Market.BIST, start, end)

    h1 = store.get("TESTSYM", Timeframe.H1, Market.BIST)
    h4 = store.get("TESTSYM", Timeframe.H4, Market.BIST)
    d1 = store.get("TESTSYM", Timeframe.D1, Market.BIST)

    assert len(h1) == 16  # 2 gün x 8 bar
    assert len(h4) > 0
    assert len(d1) == 2


def test_update_is_idempotent_no_duplicate_index(store: Store) -> None:
    start = datetime(2026, 8, 23, 12, 0, tzinfo=UTC)  # Istanbul (+3) 24 Ağustos 00:00'dan önce
    end = datetime(2026, 8, 25, 23, 0, tzinfo=UTC)
    store.update("TESTSYM", Market.BIST, start, end)
    store.update("TESTSYM", Market.BIST, start, end)  # aynı aralık için tekrar

    h1 = store.get("TESTSYM", Timeframe.H1, Market.BIST)
    assert not h1.index.has_duplicates
    assert len(h1) == 16


def test_get_last_n(store: Store) -> None:
    start = datetime(2026, 8, 23, 12, 0, tzinfo=UTC)  # Istanbul (+3) 24 Ağustos 00:00'dan önce
    end = datetime(2026, 8, 25, 23, 0, tzinfo=UTC)
    store.update("TESTSYM", Market.BIST, start, end)

    tail = store.get("TESTSYM", Timeframe.H1, Market.BIST, last_n=3)
    assert len(tail) == 3


def test_get_missing_raises(store: Store) -> None:
    with pytest.raises(FileNotFoundError):
        store.get("YOK", Timeframe.H1, Market.BIST)
