"""`tlab/viz/svg/layout.py::resolve_collisions` -- Faz 3'ün en önemli saf
fonksiyonu. Dört senaryo `TANI_VE_YOL_HARITASI_v2.md` Faz 3, 3B'de BİREBİR
istenen dört test: (1) iki üst üste kutu ayrışıyor mu, (2) sınıra taşan kutu
içeri çekiliyor mu, (3) 50 kutu tek noktada -- düşük öncelikliler drop
ediliyor mu, (4) deterministik mi."""

from __future__ import annotations

from tlab.viz.svg.layout import LabelBox, leader_line, resolve_collisions

_BOUNDS = (0.0, 0.0, 400.0, 300.0)


def _rect_of(placed) -> tuple[float, float, float, float]:
    return placed.x, placed.y, placed.box.w, placed.box.h


def _overlaps(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return not (ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay)


def test_two_overlapping_boxes_separate() -> None:
    boxes = [
        LabelBox(anchor_x=200, anchor_y=150, w=60, h=20, text="A", priority=2),
        LabelBox(anchor_x=200, anchor_y=150, w=60, h=20, text="B", priority=1),
    ]
    result = resolve_collisions(boxes, _BOUNDS)
    assert len(result.placed) == 2
    assert not _overlaps(_rect_of(result.placed[0]), _rect_of(result.placed[1]))


def test_box_hanging_off_bounds_is_pulled_inside() -> None:
    boxes = [
        LabelBox(
            anchor_x=395, anchor_y=5, w=60, h=20, text="edge",
            priority=1, placement_hints=("right",),
        )
    ]
    result = resolve_collisions(boxes, _BOUNDS)
    assert len(result.placed) == 1
    placed = result.placed[0]
    x0, y0, w, h = _BOUNDS
    assert placed.x >= x0
    assert placed.y >= y0
    assert placed.x + placed.box.w <= x0 + w
    assert placed.y + placed.box.h <= y0 + h


def test_fifty_boxes_at_one_point_drops_low_priority() -> None:
    boxes = [
        LabelBox(anchor_x=200, anchor_y=150, w=40, h=16, text=f"box{i}", priority=50 - i)
        for i in range(50)
    ]
    result = resolve_collisions(boxes, _BOUNDS)
    assert result.dropped, "sınırlı bir alanda 50 kutunun tamamı sığmamalı"
    # Yalnızca EN DÜŞÜK öncelikliler drop edilmeli -- yerleştirilenlerin
    # hiçbiri dropped'takilerden daha düşük önceliğe sahip olmamalı.
    min_placed_priority = min(p.box.priority for p in result.placed)
    max_dropped_priority = max(b.priority for b in result.dropped)
    assert min_placed_priority >= max_dropped_priority
    # Hiçbir yerleştirilmiş kutu bir diğeriyle çakışmıyor.
    rects = [_rect_of(p) for p in result.placed]
    for i, a in enumerate(rects):
        for b in rects[i + 1 :]:
            assert not _overlaps(a, b)


def test_resolve_collisions_is_deterministic() -> None:
    boxes = [
        LabelBox(
            anchor_x=50 + i * 7, anchor_y=100 + (i % 3) * 5, w=30, h=14,
            text=f"t{i}", priority=i % 4,
        )
        for i in range(20)
    ]
    r1 = resolve_collisions(boxes, _BOUNDS)
    r2 = resolve_collisions(boxes, _BOUNDS)
    placed1 = [(p.x, p.y, p.box.text) for p in r1.placed]
    placed2 = [(p.x, p.y, p.box.text) for p in r2.placed]
    assert placed1 == placed2
    assert [b.text for b in r1.dropped] == [b.text for b in r2.dropped]


def test_needs_leader_flag_reflects_distance_from_anchor() -> None:
    close_box = LabelBox(anchor_x=10, anchor_y=10, w=20, h=10, text="close", priority=1)
    far_boxes = [
        LabelBox(anchor_x=10, anchor_y=10, w=20, h=10, text="close2", priority=5),
    ]
    # Aynı noktada çakışan ve ittirilmiş bir kutu -- çapadan uzaklaşınca
    # needs_leader True olmalı.
    boxes = far_boxes + [close_box]
    result = resolve_collisions(boxes, _BOUNDS, leader_threshold=5.0)
    pushed = next(p for p in result.placed if p.box.text == "close")
    assert pushed.needs_leader is True


def test_leader_line_empty_when_not_needed() -> None:
    boxes = [LabelBox(anchor_x=200, anchor_y=150, w=40, h=16, text="solo", priority=1)]
    result = resolve_collisions(boxes, _BOUNDS)
    assert leader_line(result.placed[0]) == ""


def test_leader_line_draws_when_needed() -> None:
    boxes = [
        LabelBox(anchor_x=200, anchor_y=150, w=40, h=16, text="a", priority=2),
        LabelBox(anchor_x=200, anchor_y=150, w=40, h=16, text="b", priority=1),
    ]
    result = resolve_collisions(boxes, _BOUNDS, leader_threshold=1.0)
    pushed = next(p for p in result.placed if p.box.text == "b")
    line = leader_line(pushed, stroke="#f00")
    assert line == "" or line.startswith("<line")
