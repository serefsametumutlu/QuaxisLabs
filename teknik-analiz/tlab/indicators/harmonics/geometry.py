"""Ortak harmonik aday geometrisi (X-A-B-C + opsiyonel öncü '0' noktası).

Bir aday, ancak C pivotu KESİNLEŞTİĞİ barda (c.finalized_idx) doğar — bu
yüzden girdi zigzag'i `alternate_pivots(pivots)` (include_pending=False,
varsayılan) ile üretilmiş, yalnızca kesinleşmiş pivotlardan oluşmalıdır.
Ekole özel kabul/ret mantığı burada YOKTUR (bkz. schools/base.py) — bu
modül yalnızca ham oranları ve bayrakları hesaplar; her ekol kendi
PatternSpec'ine göre süzer. Shark ve five_zero gibi ekoller X'ten önceki
pivotu ('0') candidate.zero üzerinden kullanır; diğerleri yok sayar.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from tlab.features.fibonacci import ratio
from tlab.features.swings import Pivot

Direction = Literal["bullish", "bearish"]


@dataclass(frozen=True)
class Candidate:
    """Tek bir X-A-B-C adayı (D henüz bilinmiyor — PENDING/ACTIVE/CONFIRMED
    durumu ayrıca state.py'de izlenir)."""

    pattern_id: str
    zero: Pivot | None
    x: Pivot
    a: Pivot
    b: Pivot
    c: Pivot
    direction: Direction
    ab_xa: float
    bc_ab: float
    c_beyond_a: bool
    b_beyond_x: bool
    bars_xa: int
    bars_ab: int
    bars_bc: int
    born_idx: int
    born_time: pd.Timestamp
    # CD-bacağı genişleme ipuçları (kitap Ch.4 "CD Leg Variations") — c
    # barında zaten bilinen, yalnızca geçmişe bakan bayraklar.
    gap_after_c: bool
    wide_bar_at_c: bool
    fast_cd_formation: bool


def _more_extreme(ref: Pivot, new: Pivot) -> bool:
    """new, ref ile AYNI türden (ikisi de high ya da ikisi de low) ve ref'ten
    daha ekstrem mi? (alternate_pivots'taki mantıkla aynı)."""
    if new.kind == "high":
        return new.price > ref.price
    return new.price < ref.price


def generate_candidates(df: pd.DataFrame, zigzag: list[Pivot]) -> list[Candidate]:
    """Kesinleşmiş zigzag üzerinde ardışık 4'lü pencerelerden (X,A,B,C) aday üretir.

    zigzag confirmed_idx/bar_idx sırasında olmalı (alternate_pivots'un
    döndürdüğü sıra). Her candidate.born_idx = c.finalized_idx; df sınırları
    dışında kalan (finalized_idx >= len(df)) adaylar üretilmez — ama zaten
    finalized_idx tanımı gereği df içinde bir bardır (finalize eden pivot
    df'in bir barında onaylanmıştır).
    """
    candidates: list[Candidate] = []
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    open_ = df["open"].to_numpy()
    close = df["close"].to_numpy()
    n = len(df)

    for i in range(len(zigzag) - 3):
        x, a, b, c = zigzag[i], zigzag[i + 1], zigzag[i + 2], zigzag[i + 3]
        zero = zigzag[i - 1] if i - 1 >= 0 else None

        if c.finalized_idx is None or c.finalized_idx >= n:
            continue

        direction: Direction = "bullish" if x.kind == "low" else "bearish"

        # CD-bacağı ipuçları: B'den C'ye kadarki barlar arasında (c dahil).
        gap_after_c = False
        wide_bar_at_c = False
        if c.bar_idx > b.bar_idx and c.bar_idx < n:
            prev_close = close[c.bar_idx - 1]
            gap_after_c = (open_[c.bar_idx] > prev_close) if c.kind == "high" else (
                open_[c.bar_idx] < prev_close
            )
            # "normalin 2 katı geniş bar": C barının range'i, X-A-B-C'nin
            # kendi barlarındaki ortalama range'in 2 katından fazla mı?
            span_idxs = range(x.bar_idx, c.bar_idx + 1)
            ranges = [high[j] - low[j] for j in span_idxs]
            avg_range = sum(ranges) / len(ranges) if ranges else 0.0
            wide_bar_at_c = avg_range > 0 and (high[c.bar_idx] - low[c.bar_idx]) >= 2.0 * avg_range

        fast_cd_formation = (c.finalized_idx - c.bar_idx) <= 2
        zero_tag = zero.bar_idx if zero else "N"

        candidates.append(
            Candidate(
                pattern_id=f"{zero_tag}_{x.bar_idx}_{a.bar_idx}_{b.bar_idx}_{c.bar_idx}",
                zero=zero,
                x=x,
                a=a,
                b=b,
                c=c,
                direction=direction,
                ab_xa=ratio(x.price, a.price, b.price),
                bc_ab=ratio(a.price, b.price, c.price),
                c_beyond_a=_more_extreme(a, c),
                b_beyond_x=_more_extreme(x, b),
                bars_xa=a.bar_idx - x.bar_idx,
                bars_ab=b.bar_idx - a.bar_idx,
                bars_bc=c.bar_idx - b.bar_idx,
                born_idx=c.finalized_idx,
                born_time=c.finalized_time,
                gap_after_c=gap_after_c,
                wide_bar_at_c=wide_bar_at_c,
                fast_cd_formation=fast_cd_formation,
            )
        )

    return candidates
