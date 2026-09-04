"""`patterns.flag_pennant` -> saf SVG sahne (Faz 4b, "flag_pennant", 4/6).

`double_top_bottom.py`/`wedge_triangle.py`nin AYNI görsel dili (grup->en
güncel long/short->twoUp, tek etiket havuzu `resolve_collisions`e), ama
`FlagPennantIndicator`nin kendi sözleşmesine uyarlandı: hologram `Polygon`
YOK -- konsolidasyon kanalı (OLS fiti, doğum barında DONDURULMUŞ) bir
`Line` olarak DIŞA AÇILMAZ, yalnızca ekseni-hizalı bir `Box` (`_consolidation`)
verilir (bkz. `flag_pennant.py`nin kendi docstring'i, "kanal saf bir OLS
fiti, sentetik Trendline nesnesi üretmek gereksiz dolaylama olurdu"). Bu
yüzden kırılım/onay işaretlerinin Y konumu GERÇEK eğik kırılım çizgisi
değil, kutunun kendi üst/alt kenarı (`box.high`/`box.low`) ile YAKLAŞIK
gösterilir -- bu, primitiflerin (IndicatorResult) ötesine geçip uydurma
bir değer hesaplamaktan (görev metninin yasakladığı) kaçınmanın BİLİNÇLİ
bedeli.

Direk (`pole`, `Line`, style="pattern_pole") ayrı bir birincil öğe --
`error/INTEM_patterns.flag_pennant_1d.png`de (kullanıcı geri bildirimi,
2026-09-04) direğin pencerenin SOL kenarından başladığı, öncesindeki
birkaç mumun hiç görünmediği fark edildi; bu sahne direğin başlangıcından
ÖNCE de birkaç bar pay bırakır (`_pattern_window`nin `pad_before`si
direğin `t0`ına göre, yalnızca konsolidasyonun doğum barına göre DEĞİL)."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tlab.core.types import Box, IndicatorResult, Level, Line, Marker
from tlab.viz.svg.axes import price_labels, x_labels
from tlab.viz.svg.candles import draw_candles
from tlab.viz.svg.layout import LabelBox, Placement, leader_line, resolve_collisions
from tlab.viz.svg.prim import (
    glow_filter_defs,
    pill,
    svg_circle,
    svg_line,
    svg_poly,
    svg_rect,
    svg_text,
)
from tlab.viz.svg.scale import Chart, bar_index, pad_range
from tlab.viz.svg.scenes.base import PanelOut, SceneOut, TwoUpOut
from tlab.viz.svg.theme import SVGTheme

_W, _H = 486.0, 380.0
_LABEL_TR = {"bayrak": "BAYRAK", "flama": "FLAMA"}


@dataclass(frozen=True)
class _PatternGroup:
    pattern_id: str
    direction: str
    shape: str
    pole: Line
    box: Box
    target: Level
    state: str
    event: str
    entry_marker: Marker | None
    last_time: pd.Timestamp


def _strip(label: str, suffix: str) -> str | None:
    return label[: -len(suffix)] if label.endswith(suffix) else None


def _group_patterns(result: IndicatorResult) -> dict[str, _PatternGroup]:
    poles = {pid: ln for ln in result.lines if (pid := _strip(ln.label, "_pole")) is not None}
    boxes = {
        pid: bx for bx in result.boxes if (pid := _strip(bx.label, "_consolidation")) is not None
    }
    targets = {
        pid: lv for lv in result.levels if (pid := _strip(lv.label, "_target")) is not None
    }
    entry_markers: dict[str, Marker] = {}
    for m in result.markers:
        if m.kind.startswith("pattern_entry_"):
            entry_markers[m.kind.split(":", 1)[1]] = m

    last_signal_time: dict[str, pd.Timestamp] = {}
    for sig in result.signals:
        pid = sig.payload.get("pattern_id")
        if pid is None:
            continue
        if pid not in last_signal_time or sig.bar_time > last_signal_time[pid]:
            last_signal_time[pid] = sig.bar_time

    groups: dict[str, _PatternGroup] = {}
    for pid, info in result.last_state.items():
        pole, box, target = poles.get(pid), boxes.get(pid), targets.get(pid)
        last_time = last_signal_time.get(pid)
        if pole is None or box is None or target is None or last_time is None:
            continue
        groups[pid] = _PatternGroup(
            pattern_id=pid, direction=info["direction"], shape=info["shape"],
            pole=pole, box=box, target=target, state=info["state"], event=info["event"],
            entry_marker=entry_markers.get(pid), last_time=last_time,
        )
    return groups


def _latest(groups: dict[str, _PatternGroup], direction: str) -> _PatternGroup | None:
    candidates = [g for g in groups.values() if g.direction == direction]
    if not candidates:
        return None
    return max(candidates, key=lambda g: g.last_time)


def _pattern_window(
    df: pd.DataFrame, group: _PatternGroup, *, pad_before: int = 6, pad_after: int = 8,
) -> pd.DataFrame:
    pole_start_idx = bar_index(df, group.pole.points[0][0])
    last_idx = bar_index(df, group.last_time)
    lo = max(0, pole_start_idx - pad_before)
    hi = min(len(df) - 1, last_idx + pad_after)
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


def _panel_svg(
    result: IndicatorResult, window: pd.DataFrame, group: _PatternGroup, theme: SVGTheme,
    filter_id: str,
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
    pole_color = theme.demand if group.direction == "long" else theme.supply

    s = glow_filter_defs(filter_id, enabled=theme.glow)
    s += price_labels(chart, theme, 4)
    s += x_labels(chart, _pick_x_ticks(window), theme)
    s += draw_candles(window, chart, theme)

    (pt1, pp1), (pt2, pp2) = group.pole.points
    s += svg_line(
        chart.x(pos(pt1)), chart.y(pp1), chart.x(pos(pt2)), chart.y(pp2),
        stroke=pole_color, width=2.0, opacity=0.9,
        filter_url=f"url(#{filter_id})" if theme.glow else None,
    )

    bx0, bx1 = chart.x(pos(group.box.t0)), chart.x(pos(group.box.t1))
    by0, by1 = chart.y(group.box.low), chart.y(group.box.high)
    s += svg_rect(
        bx0, by1, bx1 - bx0, by0 - by1, fill=theme.accent2, opacity=fill_op,
        stroke=theme.accent2, dash="2,2", stroke_width=1.2,
    )

    edge_price = group.box.high if group.direction == "long" else group.box.low
    edge_y = chart.y(edge_price)

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
        s += svg_circle(bx, edge_y, 4, fill=theme.demand, opacity=0.9)
    if retest_bar_time is not None and retest_bar_time in window.index:
        rx = chart.x(pos(retest_bar_time))
        s += svg_circle(rx, edge_y, 3.4, fill="none", stroke=theme.demand, stroke_width=1.8)

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

    shape_label_tr = _LABEL_TR.get(group.shape, group.shape.upper())
    add(
        shape_label_tr, chart.x(pos(group.box.t0)) + 2, chart.y(group.box.high), 60, 14, 1,
        _LabelStyle("text_muted", mono=False), _ABOVE_BELOW,
    )

    if confirm_marker is not None and confirm_marker.t in window.index:
        bx = chart.x(pos(confirm_marker.t))
        add("Kırılım", bx, edge_y, 56, 14, 3, _LabelStyle("demand", mono=False), _ABOVE_BELOW)
    if retest_bar_time is not None and retest_bar_time in window.index:
        rx = chart.x(pos(retest_bar_time))
        add(
            "Onay: Test Tuttu", rx, edge_y, 96, 14, 3,
            _LabelStyle("demand", mono=False), _BELOW_ABOVE,
        )

    last_x_time = window.index[-1]
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
    add(state_text, last_x, chart.y(target_price), 170, 20, 6, _LabelStyle(fill_attr, kind="pill"))

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
            last_x, edge_y, last_x, chart.y(target_price),
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
    scene_label = "Bayrak / Flama"

    if long_g is None and short_g is None:
        panel = _empty_panel(theme, "Bayrak/Flama adayı yok")
        return SceneOut(
            title=f"{result.symbol} — {scene_label}", subtitle="Aday bulunamadı", badge=None,
            panels=[PanelOut(vb=(_W, _H), svg=panel)],
        )

    two_up: list[TwoUpOut] = []
    if long_g is not None:
        window = _pattern_window(df, long_g)
        svg = _panel_svg(result, window, long_g, theme, "gFa")
        two_up.append(TwoUpOut(vb=(_W, _H), svg=svg, cap=f"{result.symbol} · Yükseliş adayı"))
    if short_g is not None:
        window = _pattern_window(df, short_g)
        svg = _panel_svg(result, window, short_g, theme, "gFb")
        two_up.append(TwoUpOut(vb=(_W, _H), svg=svg, cap=f"{result.symbol} · Düşüş adayı"))

    if len(two_up) == 1:
        only = two_up[0]
        return SceneOut(
            title=f"{result.symbol} — {scene_label}", subtitle=only.cap.split("· ")[-1], badge=None,
            panels=[PanelOut(vb=only.vb, svg=only.svg)],
        )

    return SceneOut(
        title=f"{result.symbol} — {scene_label}",
        subtitle="Direk + dar konsolidasyon devam formasyonu", badge=None, two_up=two_up,
    )
