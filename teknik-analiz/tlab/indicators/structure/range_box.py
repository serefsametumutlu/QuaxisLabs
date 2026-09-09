"""Yatay sıkışma (aralık) tespiti — destek/direnç ve TEMAS noktaları.

Referans görsel: `önemli/HRjNKRZWAAAhfSy.png` ve `önemli/HRihBa2WIAIZjP_.png`
— sınır çizgisinin kaç swing'e dokunarak oluştuğu, her temasın kendi
numarasıyla (U1..Un / L1..Ln) işaretlenmiş.

Tekrar-boyama (repaint) sözleşmesi: bir temas ancak onu üreten pivot
ONAYLANDIKTAN sonra (`confirmed_idx`) var sayılır; `bar_idx`'e geri dönük
yazılmaz. Aralığın kendisi de yalnızca son onaylanmış pivota kadar olan
veriden hesaplanır.

Bu modül HESAP yapar, ÇİZMEZ. Çizimi `tlab/chart/composers/range_box.py`
yapar ve buradan yalnızca `RangeBox` tipini alır.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from tlab.features.swings import Pivot, find_pivots


@dataclass(frozen=True)
class RangeTouch:
    bar_time: pd.Timestamp
    confirmed_time: pd.Timestamp
    price: float
    index: int          # 1'den başlar -> "U1", "L3"


@dataclass(frozen=True)
class RangeBox:
    """Tipli sonuç. Jenerik bir primitif torbası DEĞİL: komposer bu tipin
    alanlarını çizer, dolayısıyla 'eksik stil adı griye düştü' türü bir
    hata mümkün değildir."""

    support: float
    resistance: float
    upper_touches: tuple[RangeTouch, ...]
    lower_touches: tuple[RangeTouch, ...]
    start_time: pd.Timestamp
    end_time: pd.Timestamp
    height_pct: float
    state: str          # "gelisiyor" | "olgun" | "kirildi_yukari" | "kirildi_asagi"

    @property
    def touch_count(self) -> int:
        return len(self.upper_touches) + len(self.lower_touches)


def _cluster(pivots: list[Pivot], tol_pct: float) -> tuple[list[Pivot], float]:
    """Fiyatı birbirine `tol_pct` kadar yakın pivotların EN KALABALIK
    kümesini ve o kümenin SEVİYESİNİ döndürür.

    Bir sınır çizgisi ancak birden çok swing aynı seviyeye dokunduğunda
    anlamlıdır (CMT Association: düzgün bir trend/kanal çizgisi "benzer
    büyüklükteki destek/direnç pivotlarını" bağlar).

    Seviye, kümenin ORTALAMASI olarak alınır — tüm pivotlar arasından
    alınan bir medyan DEĞİL. Aksi hâlde çizgi, kendisine "temas ettiği"
    söylenen noktaların uzağından geçer (ilk denemede tam olarak bu
    oldu: U1/U3/U6 çizginin altında kaldı).

    Eşitlik durumunda daha DAR yayılımlı küme kazanır: aynı sayıda
    temastan, çizgiye gerçekten yapışık olanı seçilir.
    """
    if not pivots:
        return [], float("nan")
    best: list[Pivot] = []
    best_spread = float("inf")
    for anchor in pivots:
        band = anchor.price * tol_pct
        group = [p for p in pivots if abs(p.price - anchor.price) <= band]
        if not group:
            continue
        level = sum(p.price for p in group) / len(group)
        spread = max(abs(p.price - level) for p in group)
        if len(group) > len(best) or (len(group) == len(best) and spread < best_spread):
            best, best_spread = group, spread
    level = sum(p.price for p in best) / len(best)
    return sorted(best, key=lambda p: p.bar_idx), float(level)


def detect_range_box(
    df: pd.DataFrame,
    *,
    left: int = 3,
    right: int = 3,
    tol_pct: float = 0.012,
    min_touches_per_side: int = 2,
    max_height_pct: float = 0.30,
) -> RangeBox | None:
    """Son yatay aralığı bulur. Bulamazsa `None` — 'her ne olursa olsun bir
    şey çiz' davranışı YOKTUR (kullanıcı: "güncel yakın bir sinyal yoksa
    göstermesin hiçbir şey")."""
    if len(df) < (left + right + 20):
        return None

    pivots = find_pivots(df, left=left, right=right)
    highs = [p for p in pivots if p.kind == "high"]
    lows = [p for p in pivots if p.kind == "low"]

    upper, resistance = _cluster(highs, tol_pct)
    lower, support = _cluster(lows, tol_pct)
    if len(upper) < min_touches_per_side or len(lower) < min_touches_per_side:
        return None

    if resistance <= support:
        return None

    height_pct = (resistance - support) / support
    if height_pct > max_height_pct:
        return None

    start = min(upper[0].bar_time, lower[0].bar_time)
    end = max(upper[-1].bar_time, lower[-1].bar_time)

    # aralık kurulduktan SONRAKİ kapanışlarla durum belirle
    after = df.loc[df.index > end, "close"]
    if len(after) and float(after.iloc[-1]) > resistance:
        state = "kirildi_yukari"
    elif len(after) and float(after.iloc[-1]) < support:
        state = "kirildi_asagi"
    elif len(upper) + len(lower) >= 6:
        state = "olgun"
    else:
        state = "gelisiyor"

    def pack(ps: list[Pivot]) -> tuple[RangeTouch, ...]:
        return tuple(
            RangeTouch(
                bar_time=p.bar_time, confirmed_time=p.confirmed_time,
                price=float(p.price), index=i,
            )
            for i, p in enumerate(ps, start=1)
        )

    return RangeBox(
        support=support, resistance=resistance,
        upper_touches=pack(upper), lower_touches=pack(lower),
        start_time=start, end_time=end,
        height_pct=height_pct, state=state,
    )
