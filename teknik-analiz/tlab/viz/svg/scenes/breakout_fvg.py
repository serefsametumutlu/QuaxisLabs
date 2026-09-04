"""`patterns.breakout_fvg` -> saf SVG sahne (Faz 4b, YENİ strateji, 6/6).

`double_top_bottom.py`/`flag_pennant.py`nin AYNI görsel dili (grup->en
güncel long/short->twoUp, tek etiket havuzu `resolve_collisions`e), ama
`BreakoutFvgIndicator`nin kendi sözleşmesine uyarlandı: hologram/boyun YOK
-- İKİ kutu (`_consolidation` -- konsolidasyon aralığı, `_fvg` -- 3 mumlu
Fair Value Gap bölgesi) + zincirin 5 aşamasını (konsolidasyon→kırılım→FVG
oluşumu→retest→onay) gösteren durum rozeti. FVG kutusu, `patterns_geom`
sınır çizgileri gibi eğik DEĞİL -- iki komşu mumun DOKUNMADIĞI sabit bir
fiyat bandı (bkz. `breakout_fvg.py`nin kendi docstring'i, ICT/"Smart Money
Concepts" kaynak notu)."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tlab.core.types import Box, IndicatorResult, Level, Marker
from tlab.viz.svg.axes import price_labels, x_labels
from tlab.viz.svg.candles import draw_candles
from tlab.viz.svg.layout import LabelBox, Placement, leader_line, resolve_collisions
from tlab.viz.svg.prim import glow_filter_defs, pill, svg_circle, svg_poly, svg_rect, svg_text
from tlab.viz.svg.scale import Chart, bar_index, pad_range
from tlab.viz.svg.scenes.base import PanelOut, SceneOut, TwoUpOut
from tlab.viz.svg.theme import SVGTheme

_W, _H = 486.0, 380.0


@dataclass(frozen=True)
class _PatternGroup:
    pattern_id: str
    direction: str
    consolidation: Box
    fvg: Box | None
    target: Level | None
    state: str
    event: str
    entry_marker: Marker | None
    last_time: pd.Timestamp


def _strip(label: str, suffix: str) -> str | None:
    return label[: -len(suffix)] if label.endswith(suffix) else None


def _group_patterns(result: IndicatorResult) -> dict[str, _PatternGroup]:
    consolidations = {
        pid: bx for bx in result.boxes if (pid := _strip(bx.label, "_consolidation")) is not None
    }
    fvgs = {pid: bx for bx in result.boxes if (pid := _strip(bx.label, "_fvg")) is not None}
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
        consolidation = consolidations.get(pid)
        last_time = last_signal_time.get(pid)
        if consolidation is None or last_time is None:
            continue
        groups[pid] = _PatternGroup(
            pattern_id=pid, direction=info["direction"], consolidation=consolidation,
            fvg=fvgs.get(pid), target=targets.get(pid), state=info["state"], event=info["event"],
            entry_marker=entry_markers.get(pid), last_time=last_time,
        )
    return groups


def _latest(groups: dict[str, _PatternGroup], direction: str) -> _PatternGroup | None:
    candidates = [g for g in groups.values() if g.direction == direction]
    if not candidates:
        return None
    return max(candidates, key=lambda g: g.last_time)


def _pattern_window(
    df: pd.DataFrame, group: _PatternGroup, *, pad_before: int = 4, pad_after: int = 6,
) -> pd.DataFrame:
    start_idx = bar_index(df, group.consolidation.t0)
    last_idx = bar_index(df, group.last_time)
    lo = max(0, start_idx - pad_before)
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


def _signal_time(result: IndicatorResult, pid: str, suffix: str) -> pd.Timestamp | None:
    return next(
        (
            s.bar_time for s in result.signals
            if s.payload.get("pattern_id") == pid and s.payload.get("suffix") == suffix
        ),
        None,
    )


def _panel_svg(
    result: IndicatorResult, window: pd.DataFrame, group: _PatternGroup, theme: SVGTheme,
    filter_id: str,
) -> str:
    i_max = len(window) - 1

    def pos(t: pd.Timestamp) -> int:
        return bar_index(window, t)

    key_prices = [float(window["low"].min()), float(window["high"].max())]
    key_prices += [group.consolidation.low, group.consolidation.high]
    if group.fvg is not None:
        key_prices += [group.fvg.low, group.fvg.high]
    target_price = group.target.price if group.target is not None else None
    if target_price is not None and 0 < target_price:
        # Diğer 5 sahnenin (swing_fib_abcd/wedge_triangle/broadening/...)
        # AYNI dersi: yalnızca ekranın doğal aralığına düşen bir hedef
        # eksene katılır, aksi halde mumlar sıkışırdı.
        natural_lo, natural_hi = pad_range(min(key_prices), max(key_prices), 0.1)
        if natural_lo <= target_price <= natural_hi:
            key_prices.append(target_price)
    lo, hi = pad_range(min(key_prices), max(key_prices), 0.1)

    chart = Chart(
        w=_W, h=_H, margin_l=44, margin_r=12, margin_t=20, margin_b=28,
        i_domain=(0, i_max), p_domain=(lo, hi),
    )

    box_op = 0.22 if theme.key == "dark" else 0.16
    fvg_op = 0.32 if theme.key == "dark" else 0.24
    badge_text = "#0a0c10" if theme.key == "dark" else "#ffffff"

    s = glow_filter_defs(filter_id, enabled=theme.glow)
    s += price_labels(chart, theme, 4)
    s += x_labels(chart, _pick_x_ticks(window), theme)
    s += draw_candles(window, chart, theme)

    cx0, cx1 = chart.x(pos(group.consolidation.t0)), chart.x(pos(group.consolidation.t1))
    cy0, cy1 = chart.y(group.consolidation.low), chart.y(group.consolidation.high)
    s += svg_rect(
        cx0, cy1, cx1 - cx0, cy0 - cy1, fill=theme.accent2, opacity=box_op,
        stroke=theme.accent2, dash="2,2", stroke_width=1.2,
    )

    if group.fvg is not None:
        fx0, fx1 = chart.x(pos(group.fvg.t0)), chart.x(pos(group.fvg.t1))
        fy0, fy1 = chart.y(group.fvg.low), chart.y(group.fvg.high)
        fvg_color = theme.demand if group.direction == "long" else theme.supply
        s += svg_rect(fx0, fy1, max(fx1 - fx0, 2), fy0 - fy1, fill=fvg_color, opacity=fvg_op)

    breakout_t = _signal_time(result, group.pattern_id, "breakout")
    retest_t = _signal_time(result, group.pattern_id, "retest")
    marker_color = theme.demand if group.direction == "long" else theme.supply
    if breakout_t is not None and breakout_t in window.index:
        bx = chart.x(pos(breakout_t))
        by = chart.y(float(window.loc[breakout_t, "close"]))
        s += svg_circle(bx, by, 4, fill=marker_color, opacity=0.9)
    if retest_t is not None and retest_t in window.index and group.fvg is not None:
        rx = chart.x(pos(retest_t))
        ry = chart.y((group.fvg.low + group.fvg.high) / 2)
        s += svg_circle(rx, ry, 3.4, fill="none", stroke=marker_color, stroke_width=1.8)

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

    add(
        "Konsolidasyon", cx0 + 2, chart.y(group.consolidation.high), 84, 14, 1,
        _LabelStyle("text_muted", mono=False), _ABOVE_BELOW,
    )
    if group.fvg is not None:
        fx0 = chart.x(pos(group.fvg.t0))
        add(
            "FVG", fx0, chart.y((group.fvg.low + group.fvg.high) / 2), 34, 14, 2,
            _LabelStyle("text_muted", mono=False), ("right", "left"),
        )
    if breakout_t is not None and breakout_t in window.index:
        bx = chart.x(pos(breakout_t))
        add(
            "Kırılım", bx, chart.y(float(window.loc[breakout_t, "close"])), 56, 14, 3,
            _LabelStyle("demand" if group.direction == "long" else "supply", mono=False),
            _ABOVE_BELOW,
        )
    if retest_t is not None and retest_t in window.index and group.fvg is not None:
        rx = chart.x(pos(retest_t))
        add(
            "Retest", rx, chart.y((group.fvg.low + group.fvg.high) / 2), 56, 14, 3,
            _LabelStyle("demand" if group.direction == "long" else "supply", mono=False),
            _BELOW_ABOVE,
        )

    last_x_time = window.index[-1]
    last_x = chart.x(min(pos(last_x_time), i_max))
    show_target = (
        group.target is not None and group.state not in ("invalidated", "expired")
        and target_price is not None and lo <= target_price <= hi
    )
    if show_target and target_price is not None:
        add(
            f"Hedef: {target_price:.1f}", last_x, chart.y(target_price), 88, 16, 4,
            _LabelStyle("demand"),
        )

    state_marker = _find_marker(result, group.pattern_id, group.state)
    state_text = state_marker.text if state_marker is not None else group.event
    fill_attr = {
        "completed": "demand", "invalidated": "resistance", "expired": "muted",
        "confirmed": "accent", "active": "accent2", "pending": "muted",
    }.get(group.state, "accent")
    anchor_price = target_price if (show_target and target_price is not None) else (
        group.fvg.high if group.fvg is not None else group.consolidation.high
    )
    add(
        state_text, last_x, chart.y(anchor_price), 210, 20, 6,
        _LabelStyle(fill_attr, kind="pill"),
    )

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
    scene_label = "Kırılım + FVG"

    if long_g is None and short_g is None:
        panel = _empty_panel(theme, "Kırılım+FVG adayı yok")
        return SceneOut(
            title=f"{result.symbol} — {scene_label}", subtitle="Aday bulunamadı", badge=None,
            panels=[PanelOut(vb=(_W, _H), svg=panel)],
        )

    two_up: list[TwoUpOut] = []
    if long_g is not None:
        window = _pattern_window(df, long_g)
        svg = _panel_svg(result, window, long_g, theme, "gBFa")
        two_up.append(TwoUpOut(vb=(_W, _H), svg=svg, cap=f"{result.symbol} · Yükseliş adayı"))
    if short_g is not None:
        window = _pattern_window(df, short_g)
        svg = _panel_svg(result, window, short_g, theme, "gBFb")
        two_up.append(TwoUpOut(vb=(_W, _H), svg=svg, cap=f"{result.symbol} · Düşüş adayı"))

    if len(two_up) == 1:
        only = two_up[0]
        return SceneOut(
            title=f"{result.symbol} — {scene_label}", subtitle=only.cap.split("· ")[-1], badge=None,
            panels=[PanelOut(vb=only.vb, svg=only.svg)],
        )

    return SceneOut(
        title=f"{result.symbol} — {scene_label}",
        subtitle="Konsolidasyon kırılımı + Fair Value Gap retest/onay", badge=None, two_up=two_up,
    )
