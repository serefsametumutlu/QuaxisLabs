"""Non-repainting destek/direnç bölgesi (zone) tespiti.

Onaylı pivotlar confirmed_idx sırasına göre işlenir; ATR tabanlı bant
genişliği içindeki fiyatlar aynı kümeye (basit 1D kümeleme, sklearn yok)
katılır. Bölge, kümeye k'inci (min_pivots) pivot katıldığı BARDA (o pivotun
confirmed_idx'i) doğar — center/thickness o anda sabitlenir, bir daha
değişmez. Bölge doğduktan sonra artık yeni pivot ABSORBE ETMEZ; bundan
sonraki her bar için (formed_idx'ten itibaren) temas/kırılım
ranges.detect_ranges ile AYNI desenle (extend-only touches, confirm_bars'lı
kırılım) izlenir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import pandas as pd

from tlab.features.swings import Pivot
from tlab.features.volatility import atr

BreakDirection = Literal["up", "down"]


@dataclass(frozen=True)
class Zone:
    center: float
    thickness: float
    low: float
    high: float
    formed_idx: int
    formed_time: pd.Timestamp
    member_bar_idxs: tuple[int, ...]
    touches: tuple[int, ...]
    broken_at: int | None
    broken_direction: BreakDirection | None


@dataclass
class _FormingCluster:
    member_prices: list[float] = field(default_factory=list)
    member_bar_idxs: list[int] = field(default_factory=list)

    @property
    def center(self) -> float:
        return sum(self.member_prices) / len(self.member_prices)


def cluster_zones(
    df: pd.DataFrame,
    pivots: list[Pivot],
    min_pivots: int = 2,
    atr_mult: float = 0.5,
    breakout_confirm: int = 1,
    atr_period: int = 14,
) -> list[Zone]:
    """pivots (herhangi sırada olabilir) confirmed_idx'e göre işlenir. Her
    pivot, MEVCUT (henüz min_pivots'e ulaşmamış) kümelerden fiyatına en
    yakın olanına, bant genişliği (atr_mult * o pivotun kendi confirmed_idx
    'indeki ATR'si) içindeyse katılır; yoksa yeni bir küme başlatır. Kümeye
    k'inci pivot katıldığında bölge doğar ve küme kapanır (artık büyümez)."""
    n = len(df)
    atr_series = atr(df, atr_period)
    ordered = sorted(pivots, key=lambda p: (p.confirmed_idx, p.bar_idx))

    forming: list[_FormingCluster] = []
    formed: list[tuple[float, float, int, tuple[int, ...]]] = []

    for p in ordered:
        if p.confirmed_idx >= n:
            continue
        a = atr_series.iloc[p.confirmed_idx]
        if pd.isna(a):
            continue
        band = atr_mult * a

        best: _FormingCluster | None = None
        best_dist = float("inf")
        for c in forming:
            dist = abs(p.price - c.center)
            if dist <= band and dist < best_dist:
                best, best_dist = c, dist

        if best is None:
            best = _FormingCluster()
            forming.append(best)
        best.member_prices.append(p.price)
        best.member_bar_idxs.append(p.bar_idx)

        if len(best.member_prices) >= min_pivots:
            formed.append((best.center, band, p.confirmed_idx, tuple(best.member_bar_idxs)))
            forming.remove(best)

    return _track_zones(df, formed, breakout_confirm)


def _track_zones(
    df: pd.DataFrame,
    formed: list[tuple[float, float, int, tuple[int, ...]]],
    breakout_confirm: int,
) -> list[Zone]:
    n = len(df)
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    close = df["close"].to_numpy()

    zones: list[Zone] = []
    for center, thickness, formed_idx, member_bar_idxs in formed:
        zone_low = center - thickness / 2
        zone_high = center + thickness / 2

        touches: list[int] = []
        broken_at: int | None = None
        broken_direction: BreakDirection | None = None
        break_streak = 0

        for t in range(formed_idx, n):
            c = close[t]
            beyond = c > zone_high or c < zone_low
            near = low[t] <= zone_high and high[t] >= zone_low
            if beyond:
                break_streak += 1
                if break_streak >= breakout_confirm:
                    broken_at = t
                    broken_direction = "up" if c > zone_high else "down"
                    break
            else:
                break_streak = 0
                if near:
                    touches.append(t)

        zones.append(
            Zone(
                center=center,
                thickness=thickness,
                low=zone_low,
                high=zone_high,
                formed_idx=formed_idx,
                formed_time=df.index[formed_idx],
                member_bar_idxs=member_bar_idxs,
                touches=tuple(touches),
                broken_at=broken_at,
                broken_direction=broken_direction,
            )
        )

    return zones
