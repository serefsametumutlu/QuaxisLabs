"""Piksel ölçekleme -- artifact'in `makeChart`/`niceTicks` karşılığı.

X ekseni BAR-İNDEKSLİDİR (zaman değil) -- `Chart.i_domain` bar pozisyonu
(0..n-1) taşır, gerçek tarihler yalnızca etiket metninde görünür. Bu, hafta
sonu/seans dışı boşlukları otomatik olarak GÖSTERMEZ hâle getirir: `df`
zaten yalnızca gerçek seans barlarını içerdiği için ardışık pozisyonlar
arasında hiç boşluk yoktur (mevcut Plotly `renderer.py`'nin `rangebreaks`
ile elle çözdüğü sorunun bar-indeksli eksende DOĞAL çözümü)."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Chart:
    w: float
    h: float
    margin_l: float
    margin_r: float
    margin_t: float
    margin_b: float
    i_domain: tuple[float, float]
    p_domain: tuple[float, float]

    @property
    def inner_x0(self) -> float:
        return self.margin_l

    @property
    def inner_x1(self) -> float:
        return self.w - self.margin_r

    @property
    def inner_y0(self) -> float:
        return self.margin_t

    @property
    def inner_y1(self) -> float:
        return self.h - self.margin_b

    def x(self, i: float) -> float:
        i0, i1 = self.i_domain
        if i1 == i0:
            return self.inner_x0
        return self.inner_x0 + (i - i0) / (i1 - i0) * (self.inner_x1 - self.inner_x0)

    def y(self, p: float) -> float:
        p0, p1 = self.p_domain
        if p1 == p0:
            return self.inner_y1
        return self.inner_y1 - (p - p0) / (p1 - p0) * (self.inner_y1 - self.inner_y0)


def nice_ticks(lo: float, hi: float, n: int) -> list[float]:
    if hi <= lo or n <= 0:
        return []
    raw = (hi - lo) / n
    mag = 10.0 ** math.floor(math.log10(raw))
    norm = raw / mag
    step = (10.0 if norm > 5 else 5.0 if norm > 2 else 2.0 if norm > 1 else 1.0) * mag
    start = math.ceil(lo / step) * step
    out: list[float] = []
    v = start
    while v <= hi + step * 1e-9:
        out.append(round(v, 6))
        v += step
    return out


def pad_range(lo: float, hi: float, frac: float = 0.08) -> tuple[float, float]:
    pad = (hi - lo) * frac
    if pad == 0:
        pad = max(abs(hi), 1.0) * frac
    return lo - pad, hi + pad


def bar_index(df: pd.DataFrame, timestamp: pd.Timestamp) -> int:
    """`df.index`teki bir zaman damgasının pozisyonel (0-tabanlı) bar
    indeksi -- tüm primitif (Level/Line/Box/Polygon/Marker) zaman damgaları
    çizimden önce buradan geçmelidir."""
    loc = df.index.get_loc(timestamp)
    if isinstance(loc, slice):
        return loc.start
    return int(loc)
