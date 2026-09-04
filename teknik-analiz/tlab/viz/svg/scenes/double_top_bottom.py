"""`patterns.double_top_bottom` -> saf SVG sahne.

Referans: `docs/design/grafik_stil_vitrini.html::sceneDoubleTopBottom`
(satır ~764-844) -- hologram/boyun/rozet/kırılım-onay-hedef görsel dili
BİREBİR buradan port edildi. Fark: veri artık UYDURMA değil gerçek
`IndicatorResult`tan geliyor -- hologram poligonu, boyun/hedef `Level`,
"1"/"2" rozet `Marker`, kırılım/onay/AL-SAT olayları `result.signals`dan
okunuyor; hiçbir sihirli sayı YOK -- artifact'in sahne-özel el-ayarlı
ofsetlerinin aksine, TÜM değişken-konumlu etiketler (boyun yazısı, kırılım,
onay, hedef metni, hedef rozeti, AL/SAT) `layout.py::resolve_collisions`e
verilir (rozet dahil -- 1. iterasyonda el ile konumlanan hedef rozeti
panel kenarını taşıyordu, bkz. `docs/design/iterasyon/` notları).

Pencere seçimi -- CLAUDE.md'nin "Faz 0.5'te bulunan, henüz kapatılmamış"
listesindeki **BULUNAN HATA 2**nin (`tail(last_n)` sabit penceresi eski
sinyalleri kadraj dışına atıyordu) bu sahnedeki çözümü: sabit "son N bar"
yerine seçilen formasyonun p1 pivotundan son sinyaline kadar SIĞACAK bir
pencere seçilir (bkz. `_pattern_window`) -- "sinyal tarihine yakınlaş"
yaklaşımı, roadmap'in Faz 3/4 için önerdiği tam çözüm."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tlab.core.types import IndicatorResult, Level, Marker, Polygon, Signal
from tlab.viz.svg.axes import price_labels, x_labels
from tlab.viz.svg.candles import draw_candles
from tlab.viz.svg.layout import LabelBox, Placement, leader_line, resolve_collisions
from tlab.viz.svg.prim import glow_filter_defs, pill, svg_circle, svg_line, svg_poly, svg_text
from tlab.viz.svg.scale import Chart, bar_index, pad_range
from tlab.viz.svg.scenes.base import PanelOut, SceneOut, TwoUpOut
from tlab.viz.svg.theme import SVGTheme

_W, _H = 486.0, 380.0
_LABEL_TR = {"short": "ÇİFT TEPE", "long": "ÇİFT DİP"}


@dataclass(frozen=True)
class _PatternGroup:
    pattern_id: str
    direction: str  # "long" | "short"
    neckline: Level
    target: Level
    hologram: Polygon
    p1: Marker
    p2: Marker
    breakout: Signal | None
    retest: Signal | None
    completed: Signal | None
    invalidated: Signal | None
    expired: Signal | None
    entry_marker: Marker | None
    last_time: pd.Timestamp


def _strip(label: str, suffix: str) -> str | None:
    return label[: -len(suffix)] if label.endswith(suffix) else None


def _group_patterns(result: IndicatorResult) -> dict[str, _PatternGroup]:
    necklines: dict[str, Level] = {}
    targets: dict[str, Level] = {}
    for lv in result.levels:
        pid = _strip(lv.label, "_neckline")
        if pid is not None:
            necklines[pid] = lv
            continue
        pid = _strip(lv.label, "_target")
        if pid is not None:
            targets[pid] = lv

    holograms = {
        pid: poly
        for poly in result.polygons
        if (pid := _strip(poly.label, "_hologram")) is not None
    }

    vertices: dict[str, dict[str, Marker]] = {}
    entry_markers: dict[str, Marker] = {}
    for m in result.markers:
        if m.kind.startswith("pattern_vertex:"):
            vertices.setdefault(m.kind.split(":", 1)[1], {})[m.text] = m
        elif m.kind.startswith("pattern_entry_"):
            entry_markers[m.kind.split(":", 1)[1]] = m

    signals_by_pid: dict[str, list[Signal]] = {}
    for sig in result.signals:
        pid = sig.payload.get("pattern_id")
        if pid is not None:
            signals_by_pid.setdefault(pid, []).append(sig)

    groups: dict[str, _PatternGroup] = {}
    for pid, neckline in necklines.items():
        target = targets.get(pid)
        hologram = holograms.get(pid)
        verts = vertices.get(pid, {})
        p1, p2 = verts.get("1"), verts.get("2")
        if target is None or hologram is None or p1 is None or p2 is None:
            continue
        pid_signals = sorted(signals_by_pid.get(pid, []), key=lambda s: s.bar_time)
        if not pid_signals:
            continue
        def _find(suffix: str, _signals: list[Signal] = pid_signals) -> Signal | None:
            return next((s for s in _signals if s.payload["event"].endswith(suffix)), None)

        breakout = _find("_confirmed")
        retest = _find("_retest_hold")
        completed = _find("_target_reached")
        invalidated = _find("_invalidated")
        expired = _find("_expired")
        direction = "short" if target.price < neckline.price else "long"
        groups[pid] = _PatternGroup(
            pattern_id=pid, direction=direction, neckline=neckline, target=target,
            hologram=hologram, p1=p1, p2=p2, breakout=breakout, retest=retest,
            completed=completed, invalidated=invalidated, expired=expired,
            entry_marker=entry_markers.get(pid), last_time=pid_signals[-1].bar_time,
        )
    return groups


def _latest(groups: dict[str, _PatternGroup], direction: str) -> _PatternGroup | None:
    candidates = [g for g in groups.values() if g.direction == direction]
    if not candidates:
        return None
    return max(candidates, key=lambda g: g.p2.t)


def _pattern_window(
    df: pd.DataFrame, group: _PatternGroup, *, pad_before: int = 8, pad_after: int = 12,
) -> pd.DataFrame:
    i1 = bar_index(df, group.p1.t)
    i2 = bar_index(df, group.last_time)
    lo = max(0, i1 - pad_before)
    hi = min(len(df) - 1, i2 + pad_after)
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


@dataclass(frozen=True)
class _LabelStyle:
    color_attr: str
    kind: str = "text"  # "text" | "pill"
    mono: bool = True


def _panel_svg(window: pd.DataFrame, group: _PatternGroup, theme: SVGTheme, filter_id: str) -> str:
    i_max = len(window) - 1

    def pos(t: pd.Timestamp) -> int:
        return bar_index(window, t)

    lo, hi = pad_range(float(window["low"].min()), float(window["high"].max()), 0.1)
    target_price = group.target.price
    if group.direction == "short" and target_price < lo:
        lo = target_price - (hi - lo) * 0.08
    if group.direction == "long" and target_price > hi:
        hi = target_price + (hi - lo) * 0.08

    chart = Chart(
        w=_W, h=_H, margin_l=44, margin_r=12, margin_t=20, margin_b=28,
        i_domain=(0, i_max), p_domain=(lo, hi),
    )

    fill_op = 0.26 if theme.key == "dark" else 0.19
    badge_text = "#0a0c10" if theme.key == "dark" else "#ffffff"
    label_prefix = _LABEL_TR[group.direction]

    s = glow_filter_defs(filter_id, enabled=theme.glow)
    s += price_labels(chart, theme, 4)
    s += x_labels(chart, _pick_x_ticks(window), theme)
    s += draw_candles(window, chart, theme)

    # --- hologram: 5 köşeli, boyun seviyesine oturan M/W silueti ---
    holo_pts = [(chart.x(pos(t)), chart.y(p)) for t, p in group.hologram.points]
    s += svg_poly(
        "polygon", holo_pts, fill=theme.accent2, opacity=fill_op,
        stroke=theme.accent2, width=1.6, dash="2,2",
    )

    # --- boyun çizgisi (Level'ın kendi start/end'i -- extend-only) ---
    neck_p = group.neckline.price
    neck_start_pos = pos(group.neckline.start) if group.neckline.start is not None else 0
    s += svg_line(
        chart.x(neck_start_pos), chart.y(neck_p), chart.inner_x1, chart.y(neck_p),
        stroke=theme.neckline, width=1.4,
    )

    # --- "1"/"2" rozet daireleri (gerçek pivot konumları) ---
    badge_dy = -14 if group.direction == "short" else 14
    for marker in (group.p1, group.p2):
        mx, my = chart.x(pos(marker.t)), chart.y(marker.price)
        badge_y = my + badge_dy
        s += svg_circle(
            mx, badge_y, 9, fill=theme.accent, stroke=theme.card_bg, stroke_width=2,
            filter_url=f"url(#{filter_id})" if theme.glow else None,
        )
        s += svg_text(
            mx, badge_y + 3.5, marker.text, fill=badge_text, size=10.5,
            family=theme.mono, anchor="middle", weight=800,
        )

    # --- kırılım/onay içi dolu/boş daireler (küçük ikon, collision'a girmez) ---
    if group.breakout is not None:
        bx = chart.x(pos(group.breakout.bar_time))
        s += svg_circle(bx, chart.y(neck_p), 4, fill=theme.demand, opacity=0.9)
    if group.retest is not None:
        rx = chart.x(pos(group.retest.bar_time))
        s += svg_circle(
            rx, chart.y(neck_p), 3.4, fill="none", stroke=theme.demand, stroke_width=1.8,
        )

    # --- çakışabilecek TÜM etiketler tek bir havuzda -- layout.py'nin
    #     gerçek işi burada: hiçbiri elle konumlanmıyor. ---
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

    neck_anchor_x = chart.x(min(neck_start_pos + 2, i_max))
    add(
        "Boyun Çizgisi", neck_anchor_x, chart.y(neck_p), 78, 14, 1,
        _LabelStyle("muted", mono=False), _ABOVE_BELOW,
    )

    if group.breakout is not None:
        bx = chart.x(pos(group.breakout.bar_time))
        add(
            "Kırılım", bx, chart.y(neck_p), 56, 14, 3,
            _LabelStyle("demand", mono=False), _ABOVE_BELOW,
        )

    if group.retest is not None:
        rx = chart.x(pos(group.retest.bar_time))
        add(
            "Onay: Test Tuttu", rx, chart.y(neck_p), 96, 14, 3,
            _LabelStyle("demand", mono=False), _BELOW_ABOVE,
        )

    last_x = chart.x(min(pos(group.last_time) + 4, i_max))

    # Durum rozeti -- `tlab/core/pattern_state.py::SUFFIX_LABEL_TR` ile AYNI
    # sözlük: bir formasyon KIRILMADAN (breakout/retest yok) "ONAY" demek
    # yanıltıcıdır; GEÇERSİZ/SÜRESİ DOLDU'da artık hedefin bir anlamı yok
    # (o yüzden hedef çizgisi/metni de bu iki durumda ÇİZİLMEZ).
    show_target = True
    if group.completed is not None:
        state_suffix, badge_fill_attr = "HEDEFE ULAŞTI", "demand"
    elif group.invalidated is not None:
        state_suffix, badge_fill_attr, show_target = "GEÇERSİZ", "resistance", False
    elif group.expired is not None:
        state_suffix, badge_fill_attr, show_target = "SÜRESİ DOLDU", "muted", False
    elif group.retest is not None or group.breakout is not None:
        state_suffix, badge_fill_attr = "ONAY", "accent"
    else:
        state_suffix, badge_fill_attr = "OLUŞUYOR", "muted"

    if show_target:
        target_label = f"Hedef: {target_price:.1f}"
        add(target_label, last_x, chart.y(target_price), 88, 16, 4, _LabelStyle("demand"))

    state_text = f"{label_prefix} · {state_suffix}"
    add(
        state_text, last_x, chart.y(target_price), 148, 20, 6,
        _LabelStyle(badge_fill_attr, kind="pill"),
    )

    if group.entry_marker is not None:
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
                fill=color, text_fill=badge_text, family=theme.mono, size=9.5, weight=700,
            )
        else:
            s += leader_line(placed, stroke=color)
            s += svg_text(
                placed.x + placed.box.w / 2, placed.y + placed.box.h / 2 + 3.5, placed.box.text,
                fill=color, size=9.5, family=theme.mono if style.mono else theme.font_body,
                anchor="middle", weight=700,
            )

    # --- hedef çizgisi (kesikli, boyundan hedefe) -- yalnızca hedefin hâlâ
    #     anlamlı olduğu durumlarda (GEÇERSİZ/SÜRESİ DOLDU'da çizilmez) ---
    if show_target:
        s += svg_line(
            last_x, chart.y(neck_p), last_x, chart.y(target_price),
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
    top = _latest(groups, "short")
    bottom = _latest(groups, "long")

    if top is None and bottom is None:
        panel = _empty_panel(theme, "Çift tepe/dip adayı yok")
        return SceneOut(
            title=f"{result.symbol} — Çift Tepe / Çift Dip", subtitle="Aday bulunamadı", badge=None,
            panels=[PanelOut(vb=(_W, _H), svg=panel)],
        )

    two_up: list[TwoUpOut] = []
    if top is not None:
        window = _pattern_window(df, top)
        top_svg = _panel_svg(window, top, theme, "gDa")
        two_up.append(TwoUpOut(vb=(_W, _H), svg=top_svg, cap=f"{result.symbol} · Çift Tepe"))
    if bottom is not None:
        window = _pattern_window(df, bottom)
        bottom_svg = _panel_svg(window, bottom, theme, "gDb")
        two_up.append(TwoUpOut(vb=(_W, _H), svg=bottom_svg, cap=f"{result.symbol} · Çift Dip"))

    if len(two_up) == 1:
        only = two_up[0]
        return SceneOut(
            title=f"{result.symbol} — {only.cap.split('· ')[-1]}",
            subtitle="İki eş-seviye uç + tek boyun çizgisi", badge=None,
            panels=[PanelOut(vb=only.vb, svg=only.svg)],
        )

    return SceneOut(
        title="Klasik Formasyonlar — Çift Tepe / Çift Dip",
        subtitle=(
            "İki eş-seviye uç + tek boyun çizgisi "
            "(hologram boyun seviyesine OTURUR, kendi kendini kesmez)"
        ),
        badge=None, two_up=two_up,
    )
