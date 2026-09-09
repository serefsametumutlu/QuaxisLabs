"""Piyasa yapısı: HH/LH/HL/LL + BOS / CHoCH.

Referans: `ornek1.png`. Kullanıcı: *"HL ve LH noktalarını da çok güzel
görselleştirmiş, bizim gibi oradan oraya çizgi götürmüyor; tepelerine ve
diplerine küçük üçgenle ve yazıyla resmetmiş — birebir bu şekilde
istiyorum"*.

Tanımlar:
  BOS  (Break of Structure)   — trend YÖNÜNDE bir yapı kırılımı: yükselen
                                yapıda son HH'in kapanışla aşılması.
  CHoCH (Change of Character) — trend ALEYHİNE ilk kırılım: yükselen
                                yapıda son HL'in kapanışla kırılması.
                                Yön değişiminin ilk işareti.

Tekrar-boyama yasağı: her olay, kırılımın gerçekleştiği KAPANIŞ barında
doğar; kırılan pivotun barına geri yazılmaz.

Hesap yapar, çizmez.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tlab.features.swings import alternate_pivots, find_pivots, label_structure


def _atr(df: pd.DataFrame, period: int = 14) -> float:
    h, low, c = df["high"], df["low"], df["close"]
    prev = c.shift(1)
    tr = pd.concat([h - low, (h - prev).abs(), (low - prev).abs()], axis=1).max(axis=1)
    return float(tr.ewm(alpha=1 / period, adjust=False).mean().iloc[-1])


@dataclass(frozen=True)
class StructurePoint:
    t: pd.Timestamp
    price: float
    label: str          # "HH" | "LH" | "HL" | "LL"


@dataclass(frozen=True)
class StructureEvent:
    t: pd.Timestamp
    price: float
    kind: str           # "BOS" | "CHoCH"
    direction: str      # "up" | "down"
    from_t: pd.Timestamp


@dataclass(frozen=True)
class MarketStructure:
    points: tuple[StructurePoint, ...]
    events: tuple[StructureEvent, ...]
    bias: str           # "yukselen" | "alcalan" | "belirsiz"
    bars_ago: int | None


def detect_structure(
    df: pd.DataFrame, *, left: int = 3, right: int = 3, max_events: int = 4,
    min_swing_atr: float = 2.5,
) -> MarketStructure | None:
    if len(df) < 60:
        return None

    # ANLAMLI pivotlar. Ham `find_pivots(3,3)` 100 barda ~14.5 pivot
    # üretiyor; hepsini etiketlemek grafiğin sağ tarafını okunmaz bir
    # etiket yığınına çeviriyordu (ilk çizimde tam olarak bu oldu).
    #
    # `significant_pivots` bu iş için fazla agresif (düzgün bir kanalda
    # eşikten bağımsız 5 pivot veriyor, yapı etiketlemesine yetmiyor).
    # Bunun yerine zigzag üzerinde AYARLANABİLİR bir ATR süzgeci: bir
    # pivot, kendinden önce TUTULAN pivota göre yeterince büyük bir
    # salınım yaptıysa tutulur.
    raw = alternate_pivots(find_pivots(df, left=left, right=right))
    a = _atr(df)
    if a > 0 and raw:
        kept = [raw[0]]
        for piv in raw[1:]:
            if abs(piv.price - kept[-1].price) >= min_swing_atr * a:
                kept.append(piv)
        if len(kept) >= 4:
            raw = kept
    zig = label_structure(raw)
    labelled = [p for p in zig if p.label]
    if len(labelled) < 4:
        return None

    points = tuple(
        StructurePoint(p.bar_time, float(p.price), str(p.label)) for p in labelled
    )

    close = df["close"]
    events: list[StructureEvent] = []

    for p in labelled:
        # Kırılım YALNIZCA pivot onaylandıktan SONRAKİ barlarda aranır.
        start = p.confirmed_idx + 1
        if start >= len(df):
            continue
        after = close.iloc[start:]
        if p.label in ("HH", "LH"):
            hit = after[after > p.price]
            direction = "up"
            kind = "BOS" if p.label == "HH" else "CHoCH"
        else:
            hit = after[after < p.price]
            direction = "down"
            kind = "BOS" if p.label == "LL" else "CHoCH"
        if len(hit):
            events.append(
                StructureEvent(
                    t=hit.index[0], price=float(p.price), kind=kind,
                    direction=direction, from_t=p.bar_time,
                )
            )

    events.sort(key=lambda e: e.t)
    events = events[-max_events:]

    last = labelled[-1].label
    prev = labelled[-2].label if len(labelled) >= 2 else None
    if {last, prev} <= {"HH", "HL"}:
        bias = "yukselen"
    elif {last, prev} <= {"LL", "LH"}:
        bias = "alcalan"
    else:
        bias = "belirsiz"

    bars_ago = int((df.index > events[-1].t).sum()) if events else None
    return MarketStructure(
        points=points, events=tuple(events), bias=bias, bars_ago=bars_ago,
    )
