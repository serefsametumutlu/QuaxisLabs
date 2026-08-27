"""Non-repainting konsolidasyon kutusu (range) tespiti.

Bir kutu, son `min_bars` barın (high-low) genişliği atr_mult*ATR'den DAR ise
AÇILIR — ama bu ancak pencere TAMAMLANDIKTAN bir bar SONRA (detected_idx =
t0+min_bars) bilinir/onaylanır; kutunun sınırları (high/low) pencerenin
kendi high/low'udur ve bir daha DEĞİŞMEZ. detected_idx'ten itibaren her
barda fiyat kutu içindeyse t1 ilerler (extend-only); kapanış kutu dışında
`breakout_confirm` ardışık barda kalırsa breakout onaylanır ve kutu kapanır
(bir daha güncellenmez).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from tlab.features.volatility import atr

BreakoutDirection = Literal["up", "down"]


@dataclass(frozen=True)
class Range:
    """Bir konsolidasyon kutusu.

    t0_idx/t0_time: pencerenin (kutu sınırlarını belirleyen) ilk barı.
    detected_idx/detected_time: kutunun VAR OLDUĞUNUN bilindiği bar
    (t0_idx + min_bars — pencere tamamlandıktan bir bar sonra).
    t1_idx/t1_time: fiyatın kutu içinde kaldığı bilinen SON bar
    (extend-only, yalnızca ilerler).
    breakout_idx/breakout_direction: kırılımın onaylandığı bar ve yönü
    (bir kez atanır, bir daha değişmez); henüz kırılmadıysa None.
    """

    t0_idx: int
    t0_time: pd.Timestamp
    high: float
    low: float
    detected_idx: int
    detected_time: pd.Timestamp
    t1_idx: int
    t1_time: pd.Timestamp
    breakout_idx: int | None
    breakout_direction: BreakoutDirection | None


def detect_ranges(
    df: pd.DataFrame,
    min_bars: int = 10,
    atr_mult: float = 1.5,
    breakout_confirm: int = 1,
    atr_period: int = 14,
) -> list[Range]:
    """Olası her pencere başlangıcı (t0) için bağımsız olarak kutu adaylığı
    kontrol edilir — üst üste binen kutular oluşabilir, seçim/eleme bu
    fonksiyonun sorumluluğunda değildir (bkz. trendlines.build_trendlines'ın
    aksine, burada seçim kriteri istenmedi)."""
    n = len(df)
    if n < min_bars + 1:
        return []

    atr_series = atr(df, atr_period)
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    close = df["close"].to_numpy()

    ranges: list[Range] = []
    for t0 in range(0, n - min_bars):
        window_end = t0 + min_bars - 1  # pencerenin son barı (dahil)
        a = atr_series.iloc[window_end]
        if pd.isna(a):
            continue

        window_high = float(high[t0 : window_end + 1].max())
        window_low = float(low[t0 : window_end + 1].min())
        if (window_high - window_low) >= atr_mult * a:
            continue

        detected_idx = t0 + min_bars
        if detected_idx >= n:
            continue

        t1_idx = window_end  # pencere barları tanım gereği zaten kutu içinde
        breakout_idx: int | None = None
        breakout_direction: BreakoutDirection | None = None
        break_streak = 0

        for t in range(detected_idx, n):
            c = close[t]
            if window_low <= c <= window_high:
                break_streak = 0
                t1_idx = t
                continue
            break_streak += 1
            if break_streak >= breakout_confirm:
                breakout_idx = t
                breakout_direction = "up" if c > window_high else "down"
                break

        ranges.append(
            Range(
                t0_idx=t0,
                t0_time=df.index[t0],
                high=window_high,
                low=window_low,
                detected_idx=detected_idx,
                detected_time=df.index[detected_idx],
                t1_idx=t1_idx,
                t1_time=df.index[t1_idx],
                breakout_idx=breakout_idx,
                breakout_direction=breakout_direction,
            )
        )

    return ranges
