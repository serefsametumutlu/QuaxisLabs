"""`patterns.head_shoulders` -> saf SVG sahne (Faz 4b, "classic"/TOBO-OBO,
3/6).

Referans: `docs/design/grafik_stil_vitrini_files/saved_resource.html::
sceneClassicPatterns` (satır ~724) + `head_shoulders.py`nin KENDİ
docstring'i (2026-09-04, kullanıcının TradingView'de elle çizip
paylaştığı referansa göre): ÜÇ AYRI, apeksi omuz/baş noktasına bakan ters
üçgen (sol omuz / baş / sağ omuz), komşu üçgenler H1/H2 boyun noktalarını
PAYLAŞIR -- `wedge_triangle.py`/`double_top_bottom.py`nin AYNI görsel dili
(hologram+boyun+kırılım+onay+durum rozeti+hedef), ayrı yazıldı ("sahneler
birbirini import etmez"). double_top_bottom'dan fark: boyun (`neckline`)
Level DEĞİL bir `Line` (eğilebilir, `extend_right=True`); 3 vertex marker'ı
"1"/"2" DEĞİL gerçek TR metin ("SOL OMUZ"/"BAŞ"/"SAĞ OMUZ"); kırılım
seviyesi boyun eğimine göre İKİ farklı kural izler (`break_rule` sinyal
payload'ında: boyun aşağı/yatay eğimliyse boynun kendisi, YUKARI eğimliyse
sağ omuz-baş arası tepenin [h2] SABİT fiyatı -- bkz. modülün "Bulkowski"
notu)."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tlab.core.types import IndicatorResult, Level, Line, Marker, Polygon
from tlab.viz.svg.axes import price_labels, x_labels
from tlab.viz.svg.candles import draw_candles
from tlab.viz.svg.layout import LabelBox, Placement, leader_line, resolve_collisions
from tlab.viz.svg.prim import glow_filter_defs, pill, svg_circle, svg_line, svg_poly, svg_text
from tlab.viz.svg.scale import Chart, bar_index, pad_range
from tlab.viz.svg.scenes.base import PanelOut, SceneOut, TwoUpOut
from tlab.viz.svg.theme import SVGTheme

_W, _H = 486.0, 380.0


@dataclass(frozen=True)
class _PatternGroup:
    pattern_id: str
    direction: str
    neckline: Line
    hologram: tuple[Polygon, ...]
    target: Level
    state: str
    event: str
    break_rule: str
    vertices: dict[str, Marker]
    entry_marker: Marker | None
    last_time: pd.Timestamp


def _strip(label: str, suffix: str) -> str | None:
    return label[: -len(suffix)] if label.endswith(suffix) else None


def _line_value_at(line: Line, df: pd.DataFrame, t: pd.Timestamp) -> float:
    """`wedge_triangle.py::_line_value_at` ile AYNI (`Trendline.value_at`in
    slope*idx+intercept formülü), ayrı yazıldı."""
    (t1, p1), (t2, p2) = line.points
    i1, i2 = bar_index(df, t1), bar_index(df, t2)
    i = bar_index(df, t)
    if i2 == i1:
        return p1
    slope = (p2 - p1) / (i2 - i1)
    return p1 + slope * (i - i1)


def _group_patterns(result: IndicatorResult) -> dict[str, _PatternGroup]:
    necklines = {
        pid: ln for ln in result.lines if (pid := _strip(ln.label, "_neckline")) is not None
    }
    holograms: dict[str, list[Polygon]] = {}
    for poly in result.polygons:
        pid = _strip(poly.label, "_hologram")
        if pid is not None:
            holograms.setdefault(pid, []).append(poly)
    targets = {
        pid: lv for lv in result.levels if (pid := _strip(lv.label, "_target")) is not None
    }
    vertices: dict[str, dict[str, Marker]] = {}
    entry_markers: dict[str, Marker] = {}
    for m in result.markers:
        if m.kind.startswith("pattern_vertex:"):
            vertices.setdefault(m.kind.split(":", 1)[1], {})[m.text] = m
        elif m.kind.startswith("pattern_entry_"):
            entry_markers[m.kind.split(":", 1)[1]] = m

    last_signal_time: dict[str, pd.Timestamp] = {}
    break_rule_by_pid: dict[str, str] = {}
    for sig in result.signals:
        pid = sig.payload.get("pattern_id")
        if pid is None:
            continue
        if pid not in last_signal_time or sig.bar_time > last_signal_time[pid]:
            last_signal_time[pid] = sig.bar_time
        if "break_rule" in sig.payload:
            break_rule_by_pid[pid] = sig.payload["break_rule"]

    groups: dict[str, _PatternGroup] = {}
    for pid, info in result.last_state.items():
        neckline = necklines.get(pid)
        holo = holograms.get(pid)
        target = targets.get(pid)
        verts = vertices.get(pid, {})
        last_time = last_signal_time.get(pid)
        if neckline is None or not holo or target is None or last_time is None:
            continue
        if not all(k in verts for k in ("SOL OMUZ", "BAŞ", "SAĞ OMUZ")):
            continue
        groups[pid] = _PatternGroup(
            pattern_id=pid, direction=info["direction"], neckline=neckline,
            hologram=tuple(holo), target=target, state=info["state"], event=info["event"],
            break_rule=break_rule_by_pid.get(pid, "neckline"), vertices=verts,
            entry_marker=entry_markers.get(pid), last_time=last_time,
        )
    return groups


def _latest(groups: dict[str, _PatternGroup], direction: str) -> _PatternGroup | None:
    candidates = [g for g in groups.values() if g.direction == direction]
    if not candidates:
        return None
    return max(candidates, key=lambda g: g.last_time)


def _pattern_window(
    df: pd.DataFrame, group: _PatternGroup, *, pad_before: int = 4, pad_after: int = 8,
) -> pd.DataFrame:
    idxs = [bar_index(df, t) for poly in group.hologram for t, _ in poly.points]
    idxs.append(bar_index(df, group.last_time))
    lo = max(0, min(idxs) - pad_before)
    hi = min(len(df) - 1, max(idxs) + pad_after)
    return df.iloc[lo : hi + 1]


def _pick_x_ticks(window: pd.DataFrame) -> list[tuple[float, str]]:
    n = len(window)
    if n < 2:
        return []
    positions = sorted({0, (n - 1) // 2, n - 1})
    return [
        (float(pos), pd.Timestamp(window.index[pos]).strftime("%b '%y").capitalize())
        for pos in positions
    ]


@dataclass(frozen=True)
class _LabelStyle:
    color_attr: str
    kind: str = "text"
    mono: bool = True


def _find_marker(result: IndicatorResult, pid: str, state: str) -> Marker | None:
    return next((m for m in result.markers if m.kind == f"pattern_{state}:{pid}"), None)


def _break_value_at(group: _PatternGroup, df: pd.DataFrame, t: pd.Timestamp) -> float:
    if group.break_rule == "right_armpit":
        return group.neckline.points[1][1]  # h2.price, SABİT
    return _line_value_at(group.neckline, df, t)


def _panel_svg(
    result: IndicatorResult, window: pd.DataFrame, group: _PatternGroup, theme: SVGTheme,
    filter_id: str, full_df: pd.DataFrame,
) -> str:
    i_max = len(window) - 1

    def pos(t: pd.Timestamp) -> int:
        return bar_index(window, t)

    lo, hi = pad_range(float(window["low"].min()), float(window["high"].max()), 0.1)
    target_price = group.target.price
    if 0 < target_price < lo:
        lo = target_price - (hi - lo) * 0.08
    if target_price > hi:
        hi = target_price + (hi - lo) * 0.08

    chart = Chart(
        w=_W, h=_H, margin_l=44, margin_r=12, margin_t=20, margin_b=28,
        i_domain=(0, i_max), p_domain=(lo, hi),
    )

    fill_op = 0.24 if theme.key == "dark" else 0.17
    badge_text = "#0a0c10" if theme.key == "dark" else "#ffffff"

    s = glow_filter_defs(filter_id, enabled=theme.glow)
    s += price_labels(chart, theme, 4)
    s += x_labels(chart, _pick_x_ticks(window), theme)
    s += draw_candles(window, chart, theme)

    for poly in group.hologram:
        pts = [(chart.x(pos(t)), chart.y(p)) for t, p in poly.points]
        s += svg_poly(
            "polygon", pts, fill=theme.accent2, opacity=fill_op,
            stroke=theme.accent2, width=1.6, dash="2,2",
        )

    (nt1, np1), (nt2, np2) = group.neckline.points
    neck_x1, neck_x2 = chart.x(pos(nt1)), chart.x(pos(nt2))
    s += svg_line(neck_x1, chart.y(np1), neck_x2, chart.y(np2), stroke=theme.neckline, width=1.4)
    if group.neckline.extend_right and neck_x2 < chart.inner_x1:
        s += svg_line(
            neck_x2, chart.y(np2), chart.inner_x1,
            chart.y(_line_value_at(group.neckline, full_df, window.index[-1])),
            stroke=theme.neckline, width=1.4,
        )

    last_x_time = window.index[-1]

    confirm_marker = _find_marker(result, group.pattern_id, "confirmed")
    retest_bar_time = next(
        (
            s2.bar_time for s2 in result.signals
            if s2.payload.get("pattern_id") == group.pattern_id
            and s2.payload.get("event", "").endswith("_retest_hold")
        ),
        None,
    )
    if confirm_marker is not None and confirm_marker.t in window.index:
        bx = chart.x(pos(confirm_marker.t))
        by = chart.y(_break_value_at(group, full_df, confirm_marker.t))
        s += svg_circle(bx, by, 4, fill=theme.demand, opacity=0.9)
    if retest_bar_time is not None and retest_bar_time in window.index:
        rx = chart.x(pos(retest_bar_time))
        ry = chart.y(_break_value_at(group, full_df, retest_bar_time))
        s += svg_circle(rx, ry, 3.4, fill="none", stroke=theme.demand, stroke_width=1.8)

    boxes: list[LabelBox] = []
    styles: dict[str, _LabelStyle] = {}
    _ABOVE_BELOW: tuple[Placement, ...] = ("above", "below")
    _BELOW_ABOVE: tuple[Placement, ...] = ("below", "above")
    _ALL_HINTS: tuple[Placement, ...] = ("above", "below", "right", "left")

    def add(
        text: str, ax: float, ay: float, w: float, h: float, priority: int,
        style: _LabelStyle, hints: tuple[Placement, ...] = _ALL_HINTS,
    ) -> None:
        boxes.append(
            LabelBox(
                anchor_x=ax, anchor_y=ay, w=w, h=h, text=text,
                priority=priority, placement_hints=hints,
            )
        )
        styles[text] = style

    # 4. iterasyonda GERÇEK bir hata bulundu (CEMTS, dar bir TOBO): üç
    # vertex etiketi AYNI önceliği (2) paylaşınca, dar geometride collision
    # motoru "BAŞ"ı (formasyonun EN karakteristik noktası) düşürüp "SOL
    # OMUZ"/"SAĞ OMUZ"u tutabiliyordu -- görsel olarak yanıltıcı. 5.
    # iterasyonda İKİNCİ bir hata bulundu: `LabelBox.priority`nin "büyük =
    # daha önemli" sözleşmesini (bkz. layout.py docstring'i) TERSİNDEN
    # uygulamıştım (1 verip DAHA AZ korumuştum) -- "BAŞ" artık omuzlardan
    # (2) DAHA YÜKSEK öncelikli (3), sıkışınca önce omuzlar düşer.
    vertex_above = {"SOL OMUZ": False, "BAŞ": True, "SAĞ OMUZ": False}
    vertex_priority = {"BAŞ": 3}
    for label, marker in group.vertices.items():
        if marker.t not in window.index:
            continue
        vx, vy = chart.x(pos(marker.t)), chart.y(marker.price)
        s += svg_circle(vx, vy, 2.6, fill=theme.text)
        above = vertex_above.get(label, True)
        hints = _ABOVE_BELOW if above else _BELOW_ABOVE
        priority = vertex_priority.get(label, 2)
        add(label, vx, vy, 62, 14, priority, _LabelStyle("text_muted", mono=False), hints)

    if confirm_marker is not None and confirm_marker.t in window.index:
        bx = chart.x(pos(confirm_marker.t))
        by = chart.y(_break_value_at(group, full_df, confirm_marker.t))
        add("Kırılım", bx, by, 56, 14, 3, _LabelStyle("demand", mono=False), _ABOVE_BELOW)
    if retest_bar_time is not None and retest_bar_time in window.index:
        rx = chart.x(pos(retest_bar_time))
        ry = chart.y(_break_value_at(group, full_df, retest_bar_time))
        add("Onay: Test Tuttu", rx, ry, 96, 14, 3, _LabelStyle("demand", mono=False), _BELOW_ABOVE)

    last_x = chart.x(min(pos(last_x_time), i_max))
    show_target = group.state not in ("invalidated", "expired") and target_price > 0
    if show_target:
        add(
            f"Hedef: {target_price:.1f}", last_x, chart.y(target_price), 88, 16, 4,
            _LabelStyle("demand"),
        )

    state_marker = _find_marker(result, group.pattern_id, group.state)
    state_text = state_marker.text if state_marker is not None else group.event
    fill_attr = {
        "completed": "demand", "invalidated": "resistance", "expired": "muted",
        "confirmed": "accent", "pending": "muted",
    }.get(group.state, "accent")
    add(state_text, last_x, chart.y(target_price), 150, 20, 6, _LabelStyle(fill_attr, kind="pill"))

    if group.entry_marker is not None and group.entry_marker.t in window.index:
        ex, ey = chart.x(pos(group.entry_marker.t)), chart.y(group.entry_marker.price)
        entry_tri = [(ex - 6, ey + 11), (ex + 6, ey + 11), (ex, ey - 1)]
        s += svg_poly("polygon", entry_tri, fill=theme.demand)
        add(group.entry_marker.text, ex, ey, 30, 16, 7, _LabelStyle("demand"), _BELOW_ABOVE)

    bounds = (
        chart.inner_x0, chart.inner_y0,
        chart.inner_x1 - chart.inner_x0, chart.inner_y1 - chart.inner_y0,
    )
    collision = resolve_collisions(boxes, bounds)
    for placed in collision.placed:
        style = styles[placed.box.text]
        color = getattr(theme, style.color_attr)
        if style.kind == "pill":
            s += leader_line(placed, stroke=color)
            s += pill(
                placed.x, placed.y, placed.box.w, placed.box.h, placed.box.text,
                fill=color, text_fill=badge_text, family=theme.mono, size=9, weight=700,
            )
        else:
            s += leader_line(placed, stroke=color)
            s += svg_text(
                placed.x + placed.box.w / 2, placed.y + placed.box.h / 2 + 3.5, placed.box.text,
                fill=color, size=9.5, family=theme.mono if style.mono else theme.font_body,
                anchor="middle", weight=700,
            )

    if show_target:
        s += svg_line(
            last_x, chart.y(_break_value_at(group, full_df, last_x_time)),
            last_x, chart.y(target_price),
            stroke=theme.demand, width=1.3, dash="2,3", opacity=0.8,
        )

    return s


def _empty_panel(theme: SVGTheme, message: str) -> str:
    return svg_text(
        _W / 2, _H / 2, message, fill=theme.text_muted, size=12,
        family=theme.font_body, anchor="middle",
    )


def build(result: IndicatorResult, df: pd.DataFrame, theme: SVGTheme) -> SceneOut:
    groups = _group_patterns(result)
    long_g = _latest(groups, "long")
    short_g = _latest(groups, "short")
    scene_label = "OBO / TOBO"

    if long_g is None and short_g is None:
        panel = _empty_panel(theme, "OBO/TOBO adayı yok")
        return SceneOut(
            title=f"{result.symbol} — {scene_label}", subtitle="Aday bulunamadı", badge=None,
            panels=[PanelOut(vb=(_W, _H), svg=panel)],
        )

    two_up: list[TwoUpOut] = []
    if long_g is not None:
        window = _pattern_window(df, long_g)
        svg = _panel_svg(result, window, long_g, theme, "gHSa", df)
        two_up.append(TwoUpOut(vb=(_W, _H), svg=svg, cap=f"{result.symbol} · TOBO"))
    if short_g is not None:
        window = _pattern_window(df, short_g)
        svg = _panel_svg(result, window, short_g, theme, "gHSb", df)
        two_up.append(TwoUpOut(vb=(_W, _H), svg=svg, cap=f"{result.symbol} · OBO"))

    if len(two_up) == 1:
        only = two_up[0]
        return SceneOut(
            title=f"{result.symbol} — {only.cap.split('· ')[-1]}",
            subtitle="Üç ters üçgen (sol omuz/baş/sağ omuz) + boyun çizgisi", badge=None,
            panels=[PanelOut(vb=only.vb, svg=only.svg)],
        )

    return SceneOut(
        title=f"{result.symbol} — {scene_label}",
        subtitle="Üç ters üçgen (sol omuz/baş/sağ omuz) + boyun çizgisi", badge=None, two_up=two_up,
    )
