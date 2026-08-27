"""tlab.data.calendar için tatil/hafta sonu ve seans sınırı testleri."""

from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from tlab.core.types import Market
from tlab.data.calendar import is_half_day, is_trading_day, last_closed_session, session_bounds

TZ = ZoneInfo("Europe/Istanbul")


def test_fixed_holiday_is_not_trading_day() -> None:
    assert is_trading_day(date(2026, 1, 1), Market.BIST) is False  # Yılbaşı


def test_religious_holiday_is_not_trading_day() -> None:
    assert is_trading_day(date(2026, 3, 20), Market.BIST) is False  # Ramazan Bayramı


def test_weekend_is_not_trading_day() -> None:
    assert is_trading_day(date(2026, 8, 22), Market.BIST) is False  # Cumartesi


def test_ordinary_weekday_is_trading_day() -> None:
    assert is_trading_day(date(2026, 8, 24), Market.BIST) is True  # Pazartesi


def test_arife_is_half_day_but_still_trading() -> None:
    d = date(2026, 3, 19)  # Ramazan Bayramı Arifesi
    assert is_trading_day(d, Market.BIST) is True
    assert is_half_day(d, Market.BIST) is True
    _, close_at = session_bounds(d, Market.BIST)
    assert close_at.time() == time(12, 40)


def test_ordinary_day_session_bounds() -> None:
    d = date(2026, 8, 24)
    start, end = session_bounds(d, Market.BIST)
    assert start.time() == time(10, 0)
    assert end.time() == time(18, 0)
    assert start.tzinfo is not None


def test_last_closed_session_before_open() -> None:
    now = datetime(2026, 8, 24, 9, 0, tzinfo=TZ)  # Pazartesi, seans henüz açılmadı
    assert last_closed_session(now, Market.BIST) == date(2026, 8, 21)  # önceki Cuma


def test_last_closed_session_after_close() -> None:
    now = datetime(2026, 8, 24, 19, 0, tzinfo=TZ)
    assert last_closed_session(now, Market.BIST) == date(2026, 8, 24)
