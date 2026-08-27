"""1H OHLCV'den non-repainting 4H bar üretimi.

BIST hizalama: TradingView'daki gerçek 4H bar sınırları 09:00/13:00/17:00
(kullanıcı gözlemi) — seans 10:00'da başladığı için ilk dilim [09:00,13:00)
yalnızca 10:00-13:00 verisini taşır, üçüncü dilim [17:00,21:00) ise seans
18:00/18:05'te bittiği için yalnızca 17:00-18:00 verisini taşır. Bu, dilimin
"kapalı" sayılması için 4 saatlik pencerenin tamamının dolmasını GEREKTİRMEZ:
bir dilim, o günün seansı kapandığında artık hiç yeni 1H bar alamayacağı için
kesin (final) kabul edilir — bkz. is_closed hesaplaması.

NASDAQ hizalama: TradingView ile karşılaştırılıp doğrulanmadı (bkz. proje
notu — öncelik BIST). Varsayılan "session_aligned" ([09:30,13:30),
[13:30,17:30)) veya settings.yaml'da "equal_split" ([09:30,12:45),
[12:45,16:00)) seçilebilir.

Kural: resample ASLA ileri bakan hizalama yapmaz — bir dilim yalnızca kendi
başlangıç anından önceki/eşit zamanlı 1H barlardan oluşur (label='left',
closed='left' mantığı).
"""

from __future__ import annotations

from datetime import datetime, time, timedelta

import pandas as pd

from tlab.core.types import Market, validate_ohlcv
from tlab.data.calendar import session_bounds
from tlab.data.settings import NasdaqSplit

_BIST_GRID: tuple[time, ...] = (time(9, 0), time(13, 0), time(17, 0), time(21, 0))
_NASDAQ_GRID_SESSION_ALIGNED: tuple[time, ...] = (time(9, 30), time(13, 30), time(17, 30))
_NASDAQ_GRID_EQUAL_SPLIT: tuple[time, ...] = (time(9, 30), time(12, 45), time(16, 0))


def _grid_for(market: Market, nasdaq_split: NasdaqSplit) -> tuple[time, ...]:
    if market is Market.BIST:
        return _BIST_GRID
    if nasdaq_split == "equal_split":
        return _NASDAQ_GRID_EQUAL_SPLIT
    return _NASDAQ_GRID_SESSION_ALIGNED


def _floor_to_grid(ts: pd.Timestamp, grid: tuple[time, ...]) -> pd.Timestamp:
    d = ts.date()
    candidates = [datetime.combine(d, t, tzinfo=ts.tzinfo) for t in grid]
    below = [c for c in candidates if c <= ts]
    if below:
        return pd.Timestamp(max(below))
    prev_day = d - timedelta(days=1)
    return pd.Timestamp(datetime.combine(prev_day, grid[-1], tzinfo=ts.tzinfo))


def resample_to_4h(
    df_1h: pd.DataFrame,
    market: Market,
    *,
    now: datetime | None = None,
    nasdaq_split: NasdaqSplit = "session_aligned",
    drop_open: bool = True,
) -> pd.DataFrame:
    """1H OHLCV'yi 4H'ye indirger; açık (kapanmamış) dilimler varsayılan olarak düşürülür.

    now: kapanma kontrolü için referans an (varsayılan: gerçek zaman). Testte
    deterministik sonuç için sabit bir now geçilmelidir.
    drop_open=False verilirse açık dilimler is_closed=False ile tutulur
    (yalnızca test/hata ayıklama amaçlı — indikatöre asla açık bar gitmemeli).
    """
    validate_ohlcv(df_1h)
    if df_1h.empty:
        return df_1h.copy()

    tz = df_1h.index.tz
    now_ts = pd.Timestamp(now) if now is not None else pd.Timestamp.now(tz=tz)
    if now_ts.tzinfo is None:
        now_ts = now_ts.tz_localize(tz)
    else:
        now_ts = now_ts.tz_convert(tz)

    grid = _grid_for(market, nasdaq_split)
    df = df_1h.sort_index()
    bucket_start = pd.Index(df.index.map(lambda ts: _floor_to_grid(ts, grid)), name="bucket_start")

    bars = df.groupby(bucket_start).agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
    )

    grid_step = timedelta(hours=4)
    bucket_ends = bars.index.to_series().apply(lambda t: t + grid_step)
    session_closes = bars.index.to_series().apply(
        lambda t: session_bounds(t.date(), market)[1]
    )
    is_closed = (now_ts >= bucket_ends) | (now_ts >= session_closes)
    bars = bars.copy()
    bars["is_closed"] = is_closed.to_numpy()

    if drop_open:
        bars = bars[bars["is_closed"]].drop(columns="is_closed")

    return bars
