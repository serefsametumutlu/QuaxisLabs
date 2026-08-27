"""resample_to_4h için: dilim hizalaması, açık bar düşürme, sızıntı testleri."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from tlab.core.types import Market
from tlab.data.resample import resample_to_4h

TZ = ZoneInfo("Europe/Istanbul")


def _bar(hour: int, day: str = "2026-08-24") -> dict:
    ts = pd.Timestamp(f"{day} {hour:02d}:00", tz=TZ)
    o = 100.0 + hour
    return {
        "datetime": ts, "open": o, "high": o + 1,
        "low": o - 1, "close": o + 0.5, "volume": 1000.0 + hour,
    }


def _make_df(hours: list[int], day: str = "2026-08-24") -> pd.DataFrame:
    if not hours:
        index = pd.DatetimeIndex([], tz=TZ, name="datetime")
        cols = {"open": [], "high": [], "low": [], "close": [], "volume": []}
        return pd.DataFrame(cols, index=index)
    rows = [_bar(h, day) for h in hours]
    df = pd.DataFrame(rows).set_index("datetime")
    return df


def test_bist_bucket_boundaries_09_13_17() -> None:
    """Tam bir işlem günü (10-17) üç dilime ayrılmalı: [09,13), [13,17), [17,21)."""
    df = _make_df(list(range(10, 18)))  # 10..17
    now = datetime(2026, 8, 25, 9, 0, tzinfo=TZ)  # ertesi gün — seans kesin kapandı
    bars = resample_to_4h(df, Market.BIST, now=now)

    expected_starts = [
        pd.Timestamp("2026-08-24 09:00", tz=TZ),
        pd.Timestamp("2026-08-24 13:00", tz=TZ),
        pd.Timestamp("2026-08-24 17:00", tz=TZ),
    ]
    assert list(bars.index) == expected_starts

    first = bars.loc[expected_starts[0]]
    assert first["open"] == _bar(10)["open"]
    assert first["close"] == _bar(12)["close"]
    assert first["high"] == max(_bar(h)["high"] for h in (10, 11, 12))
    assert first["low"] == min(_bar(h)["low"] for h in (10, 11, 12))
    assert first["volume"] == sum(_bar(h)["volume"] for h in (10, 11, 12))

    last = bars.loc[expected_starts[2]]
    assert last["open"] == _bar(17)["open"] == last["close"] - 0.5


def test_last_short_bucket_closes_when_session_ends_even_if_grid_open() -> None:
    """[17,21) dilimi, seans 18:00'de kapandığı için 21:00 grid sınırı beklenmeden kapanmalı."""
    df = _make_df(list(range(10, 18)))
    now = datetime(2026, 8, 24, 18, 30, tzinfo=TZ)  # seans kapandı, grid (21:00) henüz dolmadı
    bars = resample_to_4h(df, Market.BIST, now=now)
    assert pd.Timestamp("2026-08-24 17:00", tz=TZ) in bars.index


def test_open_bucket_dropped_by_default() -> None:
    """Henüz kapanmamış (o gün devam eden) son dilim varsayılan olarak düşürülmeli."""
    df = _make_df([10, 11, 12, 13])  # 13:00 dilimine yalnızca bar[13] girdi
    now = datetime(2026, 8, 24, 13, 30, tzinfo=TZ)  # seans devam ediyor (kapanış 18:00)

    bars_default = resample_to_4h(df, Market.BIST, now=now)
    assert pd.Timestamp("2026-08-24 09:00", tz=TZ) in bars_default.index
    assert pd.Timestamp("2026-08-24 13:00", tz=TZ) not in bars_default.index

    bars_full = resample_to_4h(df, Market.BIST, now=now, drop_open=False)
    open_row = bars_full.loc[pd.Timestamp("2026-08-24 13:00", tz=TZ)]
    assert bool(open_row["is_closed"]) is False
    closed_row = bars_full.loc[pd.Timestamp("2026-08-24 09:00", tz=TZ)]
    assert bool(closed_row["is_closed"]) is True


def test_no_bar_leaks_data_outside_its_1h_window() -> None:
    """Her 4H barın OHLC'si yalnızca kendi dilimindeki 1H barlardan türemeli."""
    df = _make_df(list(range(10, 18)))
    now = datetime(2026, 8, 25, 9, 0, tzinfo=TZ)
    bars = resample_to_4h(df, Market.BIST, now=now)

    windows = {
        pd.Timestamp("2026-08-24 09:00", tz=TZ): (10, 11, 12),
        pd.Timestamp("2026-08-24 13:00", tz=TZ): (13, 14, 15, 16),
        pd.Timestamp("2026-08-24 17:00", tz=TZ): (17,),
    }
    for bucket_start, hours in windows.items():
        row = bars.loc[bucket_start]
        assert row["high"] == max(_bar(h)["high"] for h in hours)
        assert row["low"] == min(_bar(h)["low"] for h in hours)


def test_empty_input_returns_empty() -> None:
    df = _make_df([])
    bars = resample_to_4h(df, Market.BIST)
    assert bars.empty


@pytest.mark.parametrize("split", ["session_aligned", "equal_split"])
def test_nasdaq_split_modes_produce_two_buckets(split: str) -> None:
    ny_tz = ZoneInfo("America/New_York")
    rows = []
    for hour, minute in [(9, 30), (10, 30), (11, 30), (12, 30), (13, 30), (14, 30), (15, 30)]:
        ts = pd.Timestamp(f"2026-08-24 {hour:02d}:{minute:02d}", tz=ny_tz)
        o = 100.0 + hour
        rows.append(
            {
                "datetime": ts, "open": o, "high": o + 1,
                "low": o - 1, "close": o + 0.5, "volume": 100.0,
            }
        )
    df = pd.DataFrame(rows).set_index("datetime")
    now = datetime(2026, 8, 25, 9, 0, tzinfo=ny_tz)
    bars = resample_to_4h(df, Market.NASDAQ, now=now, nasdaq_split=split)
    assert len(bars) == 2
