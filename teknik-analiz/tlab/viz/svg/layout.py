"""Etiket yerleşim motoru -- Faz 3'ün en önemli dosyası.

Plotly'de (ve artifact'in kendi el-ayarlı sahnelerinde) YOK olan şey:
genel amaçlı bir çakışma çözücü. `renderer.py`'deki `_stagger_yshifts`/
`_declutter_levels` bunun ilkel hâlleridir -- BİLGİ SİLEREK (yalnızca en
güncel grubu göster) çözüyorlardı. Bu motor "bilgi sil" yerine "yerini
bul, hâlâ sığmıyorsa öncelikle ele (drop)" ilkesiyle çalışır.

Algoritma (açgözlü + itme): `resolve_collisions` kutuları önceliğe göre
sıralar, her kutuyu tercih sırasına göre dener (above/below/right/left),
hiçbiri boşta değilse tercih ettiği yönde dikey adımlarla iter; hâlâ yer
bulamazsa (ör. 50 kutu tek noktada) kutu DROP edilir -- sessizce kaybolmaz,
`CollisionResult.dropped` içinde raporlanır."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal

from tlab.viz.svg.prim import svg_line

Placement = Literal["above", "below", "right", "left"]

_DEFAULT_HINTS: tuple[Placement, ...] = ("above", "below", "right", "left")


@dataclass(frozen=True)
class LabelBox:
    """Yerleştirilecek bir etiket kutusu.

    anchor_x/anchor_y: kutunun "bağlı" olduğu veri noktası (ör. kırılım
    barının fiyatı). w/h: kutunun piksel boyutu. priority: büyük = daha
    önemli (önce yerleştirilir, en son drop edilir). placement_hints:
    denenecek yönlerin TERCİH SIRASI."""

    anchor_x: float
    anchor_y: float
    w: float
    h: float
    text: str
    priority: int = 0
    placement_hints: tuple[Placement, ...] = _DEFAULT_HINTS
    id: str = ""


@dataclass(frozen=True)
class PlacedLabel:
    box: LabelBox
    x: float  # kutunun sol-üst köşesi
    y: float
    needs_leader: bool

    @property
    def center(self) -> tuple[float, float]:
        return self.x + self.box.w / 2, self.y + self.box.h / 2


@dataclass
class CollisionResult:
    placed: list[PlacedLabel] = field(default_factory=list)
    dropped: list[LabelBox] = field(default_factory=list)


_Rect = tuple[float, float, float, float]  # x, y, w, h


def _clip_into_bounds(x: float, y: float, w: float, h: float, bounds: _Rect) -> tuple[float, float]:
    x0, y0, bw, bh = bounds
    x1, y1 = x0 + bw, y0 + bh
    if w <= bw:
        if x < x0:
            x = x0
        if x + w > x1:
            x = x1 - w
    if h <= bh:
        if y < y0:
            y = y0
        if y + h > y1:
            y = y1 - h
    return x, y


def _overlaps(a: _Rect, b: _Rect) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return not (ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay)


def _candidate(box: LabelBox, hint: Placement, gap: float) -> tuple[float, float]:
    if hint == "above":
        return box.anchor_x - box.w / 2, box.anchor_y - box.h - gap
    if hint == "below":
        return box.anchor_x - box.w / 2, box.anchor_y + gap
    if hint == "right":
        return box.anchor_x + gap, box.anchor_y - box.h / 2
    return box.anchor_x - box.w - gap, box.anchor_y - box.h / 2  # left


def resolve_collisions(
    boxes: Sequence[LabelBox],
    bounds: _Rect,
    *,
    gap: float = 4.0,
    leader_threshold: float = 24.0,
    max_push: int = 60,
) -> CollisionResult:
    """Saf fonksiyon: girdi kutu listesi, çıktı yerleşim listesi. SVG'den
    tamamen bağımsız, deterministik (aynı girdi -> aynı çıktı -- Python'ın
    kararlı `sorted()`'ı + sabit iterasyon sırası bunu garanti eder)."""
    ordered = sorted(enumerate(boxes), key=lambda pair: (-pair[1].priority, pair[0]))
    placed_rects: list[_Rect] = []
    result = CollisionResult()

    for _, box in ordered:
        hints = box.placement_hints or _DEFAULT_HINTS
        found: tuple[float, float] | None = None

        for hint in hints:
            cx, cy = _candidate(box, hint, gap)
            cx, cy = _clip_into_bounds(cx, cy, box.w, box.h, bounds)
            if not any(_overlaps((cx, cy, box.w, box.h), r) for r in placed_rects):
                found = (cx, cy)
                break

        if found is None:
            base_hint = hints[0]
            bx, by = _candidate(box, base_hint, gap)
            step = box.h + 2.0
            direction = 1.0 if base_hint in ("below", "right") else -1.0
            for k in range(1, max_push + 1):
                if base_hint in ("above", "below"):
                    ny = by + direction * step * k
                    nx = bx
                else:
                    nx = bx + direction * step * k
                    ny = by
                cx, cy = _clip_into_bounds(nx, ny, box.w, box.h, bounds)
                if not any(_overlaps((cx, cy, box.w, box.h), r) for r in placed_rects):
                    found = (cx, cy)
                    break

        if found is None:
            result.dropped.append(box)
            continue

        fx, fy = found
        placed_rects.append((fx, fy, box.w, box.h))
        center_x, center_y = fx + box.w / 2, fy + box.h / 2
        dist = math.hypot(center_x - box.anchor_x, center_y - box.anchor_y)
        result.placed.append(
            PlacedLabel(box=box, x=fx, y=fy, needs_leader=dist > leader_threshold)
        )

    return result


def leader_line(
    placed: PlacedLabel, *, stroke: str = "#888", width: float = 1.0, opacity: float = 0.7,
) -> str:
    """Çapa noktasından kutunun EN YAKIN kenarına ince bir çizgi -- yalnızca
    `PlacedLabel.needs_leader` True iken bir şey döner (aksi hâlde boş
    string, çağıran taraf koşulsuz ekleyebilir)."""
    if not placed.needs_leader:
        return ""
    box = placed.box
    ex = min(max(box.anchor_x, placed.x), placed.x + box.w)
    ey = min(max(box.anchor_y, placed.y), placed.y + box.h)
    return svg_line(box.anchor_x, box.anchor_y, ex, ey, stroke=stroke, width=width, opacity=opacity)
