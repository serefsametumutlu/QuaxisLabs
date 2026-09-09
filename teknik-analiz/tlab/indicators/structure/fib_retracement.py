"""Fibonacci geri çekilmesi — BASKIN swing üzerine kurulur.

Kullanıcının `golden_zone` şikâyeti (2026-09-05): *"golden zone neredeyse
tepede geliyor ... tamamen bir rezillik"*. Sebebi, bölgenin SON küçük
salınım üzerine kurulmasıydı; oysa geri çekilme, grafiğe hâkim olan
hareketin üzerine kurulmalı.

Bu modül bu yüzden swing'i BÜYÜKLÜĞE göre seçer: onaylanmış pivotlar
arasındaki en geniş fiyat bacağını alır, en yenisini değil. `min_span_atr`
ile bacağın ATR cinsinden anlamlı olması da şart koşulur.

Hesap yapar, çizmez.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tlab.features.swings import Pivot, alternate_pivots, find_pivots

# (oran, etiket) — 1.272/1.618 uzantıları hedef/risk olarak eklenir
_RATIOS: tuple[tuple[float, str], ...] = (
    (0.0, "0.0"), (0.236, "0.236"), (0.382, "0.382"), (0.5, "0.500"),
    (0.618, "0.618"), (0.786, "0.786"), (1.0, "1.0"),
)
_EXTENSIONS: tuple[tuple[float, str], ...] = ((1.272, "1.272 (hedef)"), (1.618, "1.618 (risk)"))


@dataclass(frozen=True)
class FibLevel:
    ratio: float
    price: float
    label: str


@dataclass(frozen=True)
class FibRetracement:
    start_time: pd.Timestamp
    start_price: float
    end_time: pd.Timestamp
    end_price: float
    direction: str                      # "up" (dip->tepe) | "down"
    levels: tuple[FibLevel, ...]
    golden_low: float                   # 0.382–0.618 bandının alt/üstü
    golden_high: float
    in_golden_zone: bool                # son kapanış bandın içinde mi

    @property
    def span(self) -> float:
        return abs(self.end_price - self.start_price)


def _atr(df: pd.DataFrame, period: int = 14) -> float:
    h, low, c = df["high"], df["low"], df["close"]
    prev = c.shift(1)
    tr = pd.concat([h - low, (h - prev).abs(), (low - prev).abs()], axis=1).max(axis=1)
    return float(tr.ewm(alpha=1 / period, adjust=False).mean().iloc[-1])


def detect_fib_retracement(
    df: pd.DataFrame, *, left: int = 3, right: int = 3, min_span_atr: float = 6.0,
) -> FibRetracement | None:
    """Grafiğe hâkim olan son anlamlı bacağı bulup fibo merdivenini kurar."""
    if len(df) < 60:
        return None

    zig = alternate_pivots(find_pivots(df, left=left, right=right))
    if len(zig) < 2:
        return None

    atr = _atr(df)
    if atr <= 0:
        return None

    # BASKIN bacak: ardışık pivot çiftleri arasında en geniş olanı.
    # "En yeni" DEĞİL -- şikâyetin kaynağı tam olarak buydu.
    best: tuple[Pivot, Pivot] | None = None
    best_span = 0.0
    for a, b in zip(zig, zig[1:], strict=False):
        span = abs(b.price - a.price)
        if span > best_span:
            best, best_span = (a, b), span
    if best is None or best_span < min_span_atr * atr:
        return None

    a, b = best
    direction = "up" if b.price > a.price else "down"
    lo, hi = (a.price, b.price) if direction == "up" else (b.price, a.price)
    span = hi - lo

    def price_at(ratio: float) -> float:
        # oran 0 = hareketin BİTTİĞİ uç, 1 = BAŞLADIĞI uç (geri çekilme yönü)
        return hi - span * ratio if direction == "up" else lo + span * ratio

    levels = [FibLevel(r, price_at(r), lb) for r, lb in _RATIOS]
    levels += [FibLevel(r, price_at(r), lb) for r, lb in _EXTENSIONS]

    g1, g2 = price_at(0.382), price_at(0.618)
    golden_low, golden_high = min(g1, g2), max(g1, g2)
    last_close = float(df["close"].iloc[-1])

    return FibRetracement(
        start_time=a.bar_time, start_price=float(a.price),
        end_time=b.bar_time, end_price=float(b.price),
        direction=direction, levels=tuple(levels),
        golden_low=golden_low, golden_high=golden_high,
        in_golden_zone=golden_low <= last_close <= golden_high,
    )
