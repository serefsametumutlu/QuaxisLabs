"""resample_to_4h için: dilim hizalaması, açık bar düşürme, sızıntı testleri."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from tlab.core.types import Market
from tlab.data.resample import resample_to_4h, resample_to_w1

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


# --- resample_to_w1 --------------------------------------------------------


def _day_bar(day: str, val: float) -> dict:
    ts = pd.Timestamp(f"{day} 00:00", tz=TZ)
    return {
        "datetime": ts, "open": val, "high": val + 1,
        "low": val - 1, "close": val + 0.5, "volume": 1000.0 + val,
    }


def _make_daily_df(days: list[tuple[str, float]]) -> pd.DataFrame:
    if not days:
        index = pd.DatetimeIndex([], tz=TZ, name="datetime")
        cols = {"open": [], "high": [], "low": [], "close": [], "volume": []}
        return pd.DataFrame(cols, index=index)
    rows = [_day_bar(d, v) for d, v in days]
    return pd.DataFrame(rows).set_index("datetime")


def test_w1_groups_monday_to_friday() -> None:
    """Tam bir işlem haftası (Pzt-Cum) tek dilime toplanmalı; kapanış Cuma."""
    days = [
        ("2026-08-24", 10.0),  # Pzt
        ("2026-08-25", 11.0),  # Salı
        ("2026-08-26", 12.0),  # Çar
        ("2026-08-27", 13.0),  # Perş
        ("2026-08-28", 14.0),  # Cuma
    ]
    df = _make_daily_df(days)
    now = datetime(2026, 8, 31, 9, 0, tzinfo=TZ)  # ertesi Pazartesi — hafta kesin kapandı
    bars = resample_to_w1(df, Market.BIST, now=now)

    week_start = pd.Timestamp("2026-08-24", tz=TZ)
    assert list(bars.index) == [week_start]
    row = bars.loc[week_start]
    assert row["open"] == _day_bar("2026-08-24", 10.0)["open"]
    assert row["close"] == _day_bar("2026-08-28", 14.0)["close"]
    assert row["high"] == max(_day_bar(d, v)["high"] for d, v in days)
    assert row["low"] == min(_day_bar(d, v)["low"] for d, v in days)
    assert row["volume"] == sum(_day_bar(d, v)["volume"] for d, v in days)


def test_w1_closes_on_last_trading_day_when_friday_is_holiday() -> None:
    """2026-03-20 (Cuma) Ramazan Bayramı tatili — hafta 19'da (arife,
    yarım gün) kapanmış sayılmalı, 20'yi beklemeden."""
    days = [
        ("2026-03-16", 10.0),  # Pzt
        ("2026-03-17", 11.0),  # Salı
        ("2026-03-18", 12.0),  # Çar
        ("2026-03-19", 13.0),  # Perş — arife, yarım gün (kapanış 12:40)
    ]
    df = _make_daily_df(days)
    week_start = pd.Timestamp("2026-03-16", tz=TZ)

    still_open = resample_to_w1(df, Market.BIST, now=datetime(2026, 3, 19, 12, 0, tzinfo=TZ))
    assert week_start not in still_open.index  # yarım gün kapanışı henüz gelmedi

    closed = resample_to_w1(df, Market.BIST, now=datetime(2026, 3, 19, 12, 41, tzinfo=TZ))
    assert week_start in closed.index
    assert closed.loc[week_start, "close"] == _day_bar("2026-03-19", 13.0)["close"]


def test_w1_open_week_dropped_by_default() -> None:
    days = [("2026-08-24", 10.0), ("2026-08-25", 11.0)]  # Pzt, Salı — hafta sürüyor
    df = _make_daily_df(days)
    now = datetime(2026, 8, 25, 12, 0, tzinfo=TZ)
    week_start = pd.Timestamp("2026-08-24", tz=TZ)

    bars_default = resample_to_w1(df, Market.BIST, now=now)
    assert week_start not in bars_default.index

    bars_full = resample_to_w1(df, Market.BIST, now=now, drop_open=False)
    assert bool(bars_full.loc[week_start, "is_closed"]) is False


def test_w1_empty_input_returns_empty() -> None:
    df = _make_daily_df([])
    bars = resample_to_w1(df, Market.BIST)
    assert bars.empty
