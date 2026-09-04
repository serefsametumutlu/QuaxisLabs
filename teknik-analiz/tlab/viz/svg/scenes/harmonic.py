"""`harmonic.*` -> saf SVG sahne (Faz 4a).

Referans: `docs/design/grafik_stil_vitrini.html::harmonicPanel`/
`sceneHarmonic` (satır ~420-487) -- XAB/BCD üçgenleri, X-A-B-C-D zinciri,
PRZ bandı, durum rozeti BİREBİR buradan port edildi. Fark: veri artık
UYDURMA değil `HarmonicIndicator`'ın gerçek çıktısından geliyor.

`tlab/indicators/harmonics/scanner_indicator.py::compute()` HER adayı TEK
bir döngüde işler ve `polygons`/`levels`/`markers`e HER ZAMAN sabit sayıda
öğe ekler (2 polygon: xab+bcd; 6 level: prz_low+prz_high+4 fib; 1 marker:
"D: ... [durum]") -- bu POZİSYONEL paralellik `_group_candidates`'ın
marker'ı doğru adaya eşlemesi için kullanılır (marker.kind yalnızca
"harmonic_{state}" taşır, pattern_id İÇERMEZ).

Fib merdiveni (`_fib_{oran}` son ekli Level'lar) gerçek veride VAR ama bu
ilk portta ÇİZİLMİYOR -- artifact'in `harmonicPanel`i de çizmiyor, sahneyi
BİREBİR portlamak öncelikliydi. Gelecekte `swingfib` sahnesindeki merdiven
diliyle eklenebilir (ayrı bir iterasyon)."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tlab.core.types import IndicatorResult, Level, Marker, Polygon
from tlab.viz.svg.axes import price_labels, x_labels
from tlab.viz.svg.candles import draw_candles
from tlab.viz.svg.layout import LabelBox, Placement, leader_line, resolve_collisions
from tlab.viz.svg.prim import (
    glow_filter_defs,
    outline_pill,
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

_W, _H = 486.0, 400.0
_Point = tuple[pd.Timestamp, float]

_STATE_LABEL_TR = {
    "pending": "BEKLEMEDE", "active": "AKTİF", "confirmed": "TAMAMLANDI",
    "invalidated": "GEÇERSİZ", "expired": "SÜRESİ DOLDU",
}


@dataclass(frozen=True)
class _LabelStyle:
    color_attr: str
    kind: str  # "vertex" | "prz" | "pill" | "hint"


@dataclass(frozen=True)
class _Candidate:
    pid: str
    school: str
    pattern: str
    state: str
    x: _Point
    a: _Point
    b: _Point
    c: _Point
    prz_low: float
    prz_high: float
    prz_center: _Point
    d_price: float
    last_time: pd.Timestamp


def _strip(label: str, suffix: str) -> str | None:
    return label[: -len(suffix)] if label.endswith(suffix) else None


def _group_candidates(result: IndicatorResult) -> list[_Candidate]:
    xab_by_pid: dict[str, Polygon] = {}
    bcd_by_pid: dict[str, Polygon] = {}
    order: list[str] = []
    for poly in result.polygons:
        pid = _strip(poly.label, "_xab")
        if pid is not None:
            xab_by_pid[pid] = poly
            if pid not in order:
                order.append(pid)
            continue
        pid = _strip(poly.label, "_bcd")
        if pid is not None:
            bcd_by_pid[pid] = poly

    prz_low_by_pid: dict[str, Level] = {}
    prz_high_by_pid: dict[str, Level] = {}
    for lv in result.levels:
        pid = _strip(lv.label, "_prz_low")
        if pid is not None:
            prz_low_by_pid[pid] = lv
            continue
        pid = _strip(lv.label, "_prz_high")
        if pid is not None:
            prz_high_by_pid[pid] = lv

    d_markers: list[Marker] = [m for m in result.markers if m.kind.startswith("harmonic_")]

    candidates: list[_Candidate] = []
    for i, pid in enumerate(order):
        xab = xab_by_pid.get(pid)
        bcd = bcd_by_pid.get(pid)
        prz_low = prz_low_by_pid.get(pid)
        prz_high = prz_high_by_pid.get(pid)
        if xab is None or bcd is None or prz_low is None or prz_high is None or i >= len(d_markers):
            continue
        marker = d_markers[i]
        state = marker.kind.split("_", 1)[1]
        meta = result.last_state.get(pid, {})
        x_pt, a_pt, b_pt = xab.points
        _b2, c_pt, center_pt = bcd.points
        candidates.append(
            _Candidate(
                pid=pid, school=str(meta.get("school", "")), pattern=str(meta.get("pattern", "")),
                state=state, x=x_pt, a=a_pt, b=b_pt, c=c_pt,
                prz_low=prz_low.price, prz_high=prz_high.price, prz_center=center_pt,
                d_price=marker.price, last_time=marker.t,
            )
        )
    return candidates


def _pick(
    candidates: list[_Candidate], states: set[str], *, exclude_pid: str | None = None,
) -> _Candidate | None:
    matches = [c for c in candidates if c.state in states and c.pid != exclude_pid]
    if not matches:
        return None
    return max(matches, key=lambda c: c.last_time)


def _pattern_window(
    df: pd.DataFrame, cand: _Candidate, *, pad_before: int = 6, pad_after: int = 10,
) -> pd.DataFrame:
    key_times = [cand.x[0], cand.a[0], cand.b[0], cand.c[0], cand.prz_center[0], cand.last_time]
    positions = [bar_index(df, t) for t in key_times]
    lo = max(0, min(positions) - pad_before)
    hi = min(len(df) - 1, max(positions) + pad_after)
    return df.iloc[lo : hi + 1]


def _pick_x_ticks(window: pd.DataFrame) -> list[tuple[float, str]]:
    n = len(window)
    if n < 2:
        return []
    positions = sorted({0, (n - 1) // 2, n - 1})
    return [
        (float(pos), pd.Timestamp(window.index[pos]).strftime("%b").capitalize())
        for pos in positions
    ]


def _panel_svg(window: pd.DataFrame, cand: _Candidate, theme: SVGTheme, filter_id: str) -> str:
    i_max = len(window) - 1

    def pos(t: pd.Timestamp) -> int:
        return bar_index(window, t)

    def P(pt: _Point) -> tuple[float, float]:
        t, p = pt
        return chart.x(pos(t)), chart.y(p)

    show_d = cand.state != "pending"
    key_prices = [cand.x[1], cand.a[1], cand.b[1], cand.c[1], cand.prz_low, cand.prz_high]
    if show_d:
        key_prices.append(cand.d_price)
    else:
        key_prices.append(cand.prz_center[1])
    lo, hi = pad_range(
        min(float(window["low"].min()), *key_prices),
        max(float(window["high"].max()), *key_prices),
        0.1,
    )
    chart = Chart(
        w=_W, h=_H, margin_l=46, margin_r=96, margin_t=20, margin_b=30,
        i_domain=(0, i_max), p_domain=(lo, hi),
    )

    fill_op = 0.13 if theme.key == "dark" else 0.09
    badge_text = "#0a0c10" if theme.key == "dark" else "#ffffff"

    s = glow_filter_defs(filter_id, enabled=theme.glow)
    s += price_labels(chart, theme, 4)
    s += x_labels(chart, _pick_x_ticks(window), theme)
    s += draw_candles(window, chart, theme)

    d_point: _Point | None = (cand.prz_center[0], cand.d_price) if show_d else None
    proj_to = cand.prz_center

    s += svg_poly("polygon", [P(cand.x), P(cand.a), P(cand.b)], fill=theme.accent2, opacity=fill_op)
    last_vertex = d_point or proj_to
    s += svg_poly(
        "polygon", [P(cand.b), P(cand.c), P(last_vertex)],
        fill=theme.accent2, opacity=fill_op,
        dash=None if d_point else "2,2",
        stroke=None if d_point else theme.accent2,
        width=None if d_point else 0.8,
    )
    chain = [cand.x, cand.a, cand.b, cand.c] + ([d_point] if d_point else [])
    s += svg_poly(
        "polyline", [P(pt) for pt in chain], stroke=theme.accent2, width=1.6,
        filter_url=f"url(#{filter_id})" if theme.glow else None,
    )
    if not d_point:
        cx, cy = P(cand.c)
        px, py = P(proj_to)
        s += svg_line(cx, cy, px, py, stroke=theme.accent2, width=1.4, dash="3,3", opacity=0.75)

    xbx1, xby1 = P(cand.x)
    xbx2, xby2 = P(cand.b)
    s += svg_line(xbx1, xby1, xbx2, xby2, stroke=theme.muted, width=1, dash="2,3", opacity=0.55)

    for _label, pt in [("X", cand.x), ("A", cand.a), ("B", cand.b), ("C", cand.c)] + (
        [("D", d_point)] if d_point else []
    ):
        x, y = P(pt)
        s += svg_circle(x, y, 3.2, fill=theme.card_bg, stroke=theme.accent2, stroke_width=1.6)

    prz_x0 = chart.x(pos(cand.c[0]))
    prz_hi_y, prz_lo_y = chart.y(cand.prz_high), chart.y(cand.prz_low)
    s += svg_rect(
        prz_x0, prz_hi_y, chart.inner_x1 - prz_x0, prz_lo_y - prz_hi_y,
        fill=theme.accent, opacity=0.12,
    )
    s += svg_line(
        prz_x0, prz_hi_y, chart.inner_x1, prz_hi_y,
        stroke=theme.accent, width=1, dash="3,3", opacity=0.7,
    )
    s += svg_line(
        prz_x0, prz_lo_y, chart.inner_x1, prz_lo_y,
        stroke=theme.accent, width=1, dash="3,3", opacity=0.7,
    )

    # X/A/B/C/D vertex etiketleri, PRZ etiketi ve D rozeti/ipucu metni HEPSİ
    # `resolve_collisions`e veriliyor -- 2. iterasyonda D'nin küçük harf
    # etiketiyle büyük rozeti (ikisi de D noktasının HEMEN ALTINA/ÜSTÜNE
    # elle konumlanınca) üst üste biniyordu; PRZ dar bir bant olduğu için
    # etiketi de sık sık D'ye yakın düşüyor. Faz 3'ün double_top_bottom
    # sahnesindeki AYNI ders: hiçbir değişken-konumlu öğe elle yerleştirilmez.
    boxes: list[LabelBox] = []
    styles: dict[str, _LabelStyle] = {}

    def add(
        box_id: str, text: str, ax: float, ay: float, w: float, h: float, priority: int,
        style: _LabelStyle, hints: tuple[Placement, ...] = ("above", "below", "right", "left"),
    ) -> None:
        boxes.append(
            LabelBox(
                anchor_x=ax, anchor_y=ay, w=w, h=h, text=box_id,
                priority=priority, placement_hints=hints,
            )
        )
        styles[box_id] = style
        texts[box_id] = text

    texts: dict[str, str] = {}

    for label, pt in [("X", cand.x), ("A", cand.a), ("B", cand.b), ("C", cand.c)] + (
        [("D", d_point)] if d_point else []
    ):
        x, y = P(pt)
        above = label in ("A", "C", "D")
        vertex_hints: tuple[Placement, ...] = ("above", "below") if above else ("below", "above")
        add(
            f"vertex_{label}", label, x, y, 14, 14, 5,
            _LabelStyle("text", "vertex"), hints=vertex_hints,
        )

    prz_label = f"Hedef Bölge (PRZ): {cand.prz_low:.2f}–{cand.prz_high:.2f}"
    add(
        "prz_label", prz_label, prz_x0 + 5, prz_hi_y, 190, 14, 4,
        _LabelStyle("accent", "prz"), hints=("above", "below"),
    )

    state_label = _STATE_LABEL_TR.get(cand.state, cand.state.upper())
    if d_point:
        dx, dy = P(d_point)
        pill_text = f"D: {cand.d_price:.2f} · {state_label}"
        add(
            "d_pill", pill_text, dx, dy + 16, 168, 21, 6, _LabelStyle("accent", "pill"),
            hints=("below", "above", "right", "left"),
        )
    else:
        s += outline_pill(
            chart.inner_x0 + 6, chart.inner_y0 + 6, 60, 19, state_label,
            color=theme.accent2, family=theme.mono,
        )
        hint = "→ Buraya girerse tepki/dönüş aranır"
        add(
            "hint", hint, prz_x0 + 5, prz_lo_y, 210, 12, 3,
            _LabelStyle("text_muted", "hint"), hints=("below", "above"),
        )

    bounds = (
        chart.inner_x0, chart.inner_y0,
        chart.inner_x1 - chart.inner_x0, chart.inner_y1 - chart.inner_y0,
    )
    collision = resolve_collisions(boxes, bounds)
    for placed in collision.placed:
        box_id = placed.box.text
        style = styles[box_id]
        text = texts[box_id]
        color = getattr(theme, style.color_attr)
        if style.kind == "pill":
            s += leader_line(placed, stroke=color)
            s += pill(
                placed.x, placed.y, placed.box.w, placed.box.h, text,
                fill=color, text_fill=badge_text, family=theme.mono, size=9.5, weight=700,
            )
        elif style.kind == "vertex":
            s += leader_line(placed, stroke=color)
            s += svg_text(
                placed.x + placed.box.w / 2, placed.y + placed.box.h - 3, text,
                fill=theme.text, size=12, family=theme.font_display, anchor="middle", weight=700,
            )
        elif style.kind == "prz":
            s += leader_line(placed, stroke=color)
            s += svg_text(
                placed.x, placed.y + placed.box.h - 3, text,
                fill=color, size=9.5, family=theme.mono, weight=700,
            )
        else:  # hint
            s += leader_line(placed, stroke=color)
            s += svg_text(
                placed.x, placed.y + placed.box.h - 3, text,
                fill=color, size=9, family=theme.font_body, opacity=0.9,
            )

    return s


def _empty_panel(theme: SVGTheme, message: str) -> str:
    return svg_text(
        _W / 2, _H / 2, message, fill=theme.text_muted, size=12,
        family=theme.font_body, anchor="middle",
    )


def _caption(symbol: str, cand: _Candidate) -> str:
    state_label = _STATE_LABEL_TR.get(cand.state, cand.state.upper())
    return f"{symbol} · {cand.school}/{cand.pattern} [{state_label}]"


def build(result: IndicatorResult, df: pd.DataFrame, theme: SVGTheme) -> SceneOut:
    candidates = _group_candidates(result)
    if not candidates:
        panel = _empty_panel(theme, "Harmonik aday yok")
        return SceneOut(
            title=f"{result.symbol} — Harmonik Formasyon", subtitle="Aday bulunamadı", badge=None,
            panels=[PanelOut(vb=(_W, _H), svg=panel)],
        )

    completed = _pick(candidates, {"confirmed"}) or _pick(candidates, {"invalidated", "expired"})
    completed_pid = completed.pid if completed else None
    active = _pick(candidates, {"active", "pending"}, exclude_pid=completed_pid)

    two_up: list[TwoUpOut] = []
    if completed is not None:
        window = _pattern_window(df, completed)
        svg = _panel_svg(window, completed, theme, "gHa")
        two_up.append(TwoUpOut(vb=(_W, _H), svg=svg, cap=_caption(result.symbol, completed)))
    if active is not None:
        window = _pattern_window(df, active)
        svg = _panel_svg(window, active, theme, "gHb")
        two_up.append(TwoUpOut(vb=(_W, _H), svg=svg, cap=_caption(result.symbol, active)))

    if len(two_up) == 1:
        only = two_up[0]
        return SceneOut(
            title=f"{result.symbol} — Harmonik Formasyon", subtitle=only.cap, badge=None,
            panels=[PanelOut(vb=only.vb, svg=only.svg)],
        )

    return SceneOut(
        title=f"{result.symbol} — Harmonik Formasyon (İki Durum)",
        subtitle="Solda tamamlanmış/geçersizleşmiş, sağda hâlâ oluşan aday",
        badge=None, two_up=two_up,
    )
