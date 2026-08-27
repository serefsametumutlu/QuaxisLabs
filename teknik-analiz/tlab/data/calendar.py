"""Piyasa takvimi: seans saatleri, resmi tatiller, son kapanmış seans.

pandas_market_calendars kullanılmaz (ek bağımlılık istenmiyor); tatil listesi
config/holidays_tr.yaml'dan okunur (yalnızca BIST), seans saatleri burada
sabit tanımlıdır.

BIST seans yapısı: sürekli işlem 10:00–18:00 (tek seans, öğle arası yok).
09:55–10:00 (açılış) ve 18:00–18:05 (kapanış) tek fiyat müzayedesi/"karanlık
oda" aralıklarıdır; sürekli OHLCV verisine dahil değildir, bu yüzden seans
sınırları 10:00/18:00 olarak alınır. Kaynak: kullanıcı gözlemi (TradingView).
"""

from __future__ import annotations

import functools
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from tlab.core.types import Market

DEFAULT_HOLIDAYS_PATH = Path(__file__).resolve().parents[2] / "config" / "holidays_tr.yaml"

MARKET_TZ: dict[Market, ZoneInfo] = {
    Market.BIST: ZoneInfo("Europe/Istanbul"),
    Market.NASDAQ: ZoneInfo("America/New_York"),
}

SESSION_HOURS: dict[Market, tuple[time, time]] = {
    Market.BIST: (time(10, 0), time(18, 0)),
    Market.NASDAQ: (time(9, 30), time(16, 0)),
}

_BIST_HALF_DAY_CLOSE = time(12, 40)
_MAX_LOOKBACK_DAYS = 30


@functools.lru_cache(maxsize=4)
def _load_holidays(market: Market, path: Path = DEFAULT_HOLIDAYS_PATH) -> dict[date, dict]:
    """market için {tarih: kayıt} sözlüğü döner. Şu an yalnızca BIST doldurulur."""
    if market is not Market.BIST or not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    holidays: dict[date, dict] = {}
    for _year, entries in raw.get("bist", {}).items():
        for entry in entries:
            d = date.fromisoformat(entry["date"])
            holidays[d] = entry
    return holidays


def is_half_day(d: date, market: Market) -> bool:
    """d, arife/yarım gün seansı mı (yalnızca BIST için anlamlı)."""
    return bool(_load_holidays(market).get(d, {}).get("half_day", False))


def is_trading_day(d: date, market: Market) -> bool:
    """d'nin işlem günü olup olmadığını döner (hafta sonu ve tam gün resmi tatil hariç).

    Arife/yarım gün kayıtları burada tatil SAYILMAZ — seans kısalır ama gün
    işlem günüdür (bkz. session_bounds).
    """
    if d.weekday() >= 5:
        return False
    entry = _load_holidays(market).get(d)
    return entry is None or bool(entry.get("half_day", False))


def session_bounds(d: date, market: Market) -> tuple[datetime, datetime]:
    """d günü için seans başlangıç/bitiş zamanlarını (tz-aware) döner.

    Yarım gün (arife) ise bitiş saati öne çekilir (BIST: 12:40). d'nin işlem
    günü olup olmadığı burada kontrol edilmez — çağıran is_trading_day ile
    önce doğrulamalı.
    """
    tz = MARKET_TZ[market]
    open_t, close_t = SESSION_HOURS[market]
    if market is Market.BIST and is_half_day(d, market):
        close_t = _BIST_HALF_DAY_CLOSE
    start = datetime.combine(d, open_t, tzinfo=tz)
    end = datetime.combine(d, close_t, tzinfo=tz)
    return start, end


def last_closed_session(now: datetime, market: Market) -> date:
    """now anında en son tamamen kapanmış seansın tarihini döner."""
    tz = MARKET_TZ[market]
    local_now = now.astimezone(tz)
    d = local_now.date()
    for _ in range(_MAX_LOOKBACK_DAYS):
        if is_trading_day(d, market):
            _, close_at = session_bounds(d, market)
            if local_now >= close_at:
                return d
        d = d - timedelta(days=1)
    raise RuntimeError(
        f"{market}: son {_MAX_LOOKBACK_DAYS} gün içinde kapanmış bir seans bulunamadı "
        "— tatil takvimi hatalı olabilir"
    )
