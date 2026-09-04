"""`trend.weekly_channel` -> saf SVG sahne (Faz 4a, 6/6... yalnızca `reversal_
map` kaldı).

Referans: `docs/design/grafik_stil_vitrini_files/saved_resource.html::
sceneWeeklyChannel` (satır 1171-1203) -- ana panel (mum + güncel kanal) +
alt panelde "Kanal İçi Pozisyon" osilatörü.

BİLİNÇLİ sapma: artifact eski (soluk) + güncel (belirgin) İKİ kanal
gösteriyordu -- gerçek `ChannelIndicator.compute()` (regresyon modu)
`channel_frozen_*` stilinde HER dokunuş/kırılım sinyali barı için AYRI bir
dondurulmuş kanal üretir (THYAO 1D'de GERÇEK veriyle ölçüldü: 206 satır) --
bunların TAMAMINI çizmek okunamaz bir kalabalık olurdu, TEK bir "eski"
kanalı seçmek için de tutarlı bir kriter yok (görev metninde belirtilmemiş).
Karar: yalnızca `channel_current_lower/upper` (regresyon modu) veya
`channel_lower/upper` (pivot modu, `style="channel"`) çizilir -- HER İKİ
mod da AYNI şekilde ele alınır, `frozen` olanlar bu ilk portta HİÇ ÇİZİLMEZ.

`ChannelIndicator.compute()` sinyal başına `Marker` ÜRETMEZ (yalnızca
`Signal`) -- bu yüzden işaretlerin fiyat konumu pencerenin KENDİ mum
verisinden türetilir (dokunuş -> o barın low/high'ı, kırılım -> close).
Declutter: yalnızca HER olay türünün (break_up/break_down/bottom_touch/
top_touch) penceredeki EN SON örneği gösterilir -- `ChannelIndicator`
THYAO 1D'de 150 barlık pencerede bile onlarca dokunuş sinyali üretebiliyor
(gerçek veriyle ölçüldü), tümünü çizmek report.py/golden_zone'un "yalnızca
en güncel" ilkesini ihlal ederdi."""

from __future__ import annotations

import pandas as pd

from tlab.core.types import IndicatorResult, Line, Signal
from tlab.viz.svg.axes import price_labels, x_labels
from tlab.viz.svg.candles import draw_candles
from tlab.viz.svg.prim import svg_circle, svg_line, svg_poly, svg_text
from tlab.viz.svg.scale import Chart, bar_index, pad_range
from tlab.viz.svg.scenes.base import PanelOut, SceneOut
from tlab.viz.svg.theme import SVGTheme

_MAIN_W, _MAIN_H = 780.0, 400.0
_SUB_W, _SUB_H = 780.0, 100.0
_LAST_N = 150

_EVENT_STYLE: dict[str, tuple[str, str]] = {
    # event -> (renk_attr, fiyat_kaynağı)
    "channel_bottom_touch": ("demand", "low"),
    "channel_top_touch": ("supply", "high"),
    "channel_break_up": ("up", "close"),
    "channel_break_down": ("down", "close"),
}


def _window(df: pd.DataFrame) -> pd.DataFrame:
    return df.iloc[-_LAST_N:] if len(df) > _LAST_N else df


def _channel_lines(result: IndicatorResult) -> tuple[Line | None, Line | None]:
    live_styles = ("channel_current", "channel")
    lower = next(
        (ln for ln in result.lines if ln.style in live_styles and ln.label.endswith("lower")),
        None,
    )
    upper = next(
        (ln for ln in result.lines if ln.style in live_styles and ln.label.endswith("upper")),
        None,
    )
    return lower, upper


def _latest_event_markers(result: IndicatorResult, window: pd.DataFrame) -> list[Signal]:
    win_start = window.index[0]
    latest: dict[str, Signal] = {}
    for sig in result.signals:
        event = sig.payload.get("event")
        in_window = sig.bar_time >= win_start and sig.bar_time in window.index
        if event not in _EVENT_STYLE or not in_window:
            continue
        if event not in latest or sig.bar_time > latest[event].bar_time:
            latest[event] = sig
    return list(latest.values())


def _pick_x_ticks(window: pd.DataFrame, n: int = 5) -> list[tuple[float, str]]:
    m = len(window)
    if m < 2:
        return []
    positions = sorted({round(k * (m - 1) / (n - 1)) for k in range(n)})
    out: list[tuple[float, str]] = []
    last_text: str | None = None
    for pos in positions:
        text = pd.Timestamp(window.index[pos]).strftime("%b '%y").capitalize()
        if text == last_text:
            continue
        out.append((float(pos), text))
        last_text = text
    return out


def _main_panel(
    result: IndicatorResult, df: pd.DataFrame, window: pd.DataFrame, theme: SVGTheme,
) -> str:
    i_max = len(window) - 1
    window_offset = len(df) - len(window)

    def full_pos(t: pd.Timestamp) -> float:
        return bar_index(df, t) - window_offset

    lower, upper = _channel_lines(result)
    key_prices = [float(window["low"].min()), float(window["high"].max())]
    if lower is not None:
        key_prices += [p for _, p in lower.points]
    if upper is not None:
        key_prices += [p for _, p in upper.points]
    lo, hi = pad_range(min(key_prices), max(key_prices), 0.08)

    chart = Chart(
        w=_MAIN_W, h=_MAIN_H, margin_l=48, margin_r=16, margin_t=20, margin_b=28,
        i_domain=(0, i_max), p_domain=(lo, hi),
    )

    s = price_labels(chart, theme, 5)
    s += x_labels(chart, _pick_x_ticks(window), theme)
    s += draw_candles(window, chart, theme)

    for ln in (lower, upper):
        if ln is None:
            continue
        (t1, p1), (t2, p2) = ln.points
        x1, y1 = chart.x(full_pos(t1)), chart.y(p1)
        x2, y2 = chart.x(full_pos(t2)), chart.y(p2)
        s += svg_line(x1, y1, x2, y2, stroke=theme.accent, width=1.6)
    if upper is not None:
        (_, _), (t2, p2) = upper.points
        x2, y2 = chart.x(full_pos(t2)), chart.y(p2)
        s += svg_text(
            x2 - 4, y2 - 8, "Güncel Kanal",
            fill=theme.accent, size=9.5, family=theme.font_body, weight=700, anchor="end",
        )

    for sig in _latest_event_markers(result, window):
        event = sig.payload["event"]
        color_attr, price_field = _EVENT_STYLE[event]
        color = getattr(theme, color_attr)
        price = float(window.loc[sig.bar_time, price_field])
        x, y = chart.x(bar_index(window, sig.bar_time)), chart.y(price)
        s += svg_circle(x, y, 4.5, fill="none", stroke=color, stroke_width=2)

    return s


def _sub_panel(result: IndicatorResult, window: pd.DataFrame, theme: SVGTheme) -> str:
    i_max = len(window) - 1
    pos_series = result.series.get("channel_position")
    p_lo, p_hi = -0.2, 1.2
    sch = Chart(
        w=_SUB_W, h=_SUB_H, margin_l=48, margin_r=16, margin_t=14, margin_b=18,
        i_domain=(0, i_max), p_domain=(p_lo, p_hi),
    )
    s = svg_line(
        sch.inner_x0, sch.y(1.0), sch.inner_x1, sch.y(1.0),
        stroke=theme.text_faint, width=1, dash="2,3", opacity=0.5,
    )
    s += svg_line(
        sch.inner_x0, sch.y(0.0), sch.inner_x1, sch.y(0.0),
        stroke=theme.text_faint, width=1, dash="2,3", opacity=0.5,
    )
    if pos_series is not None:
        windowed = pos_series.reindex(window.index).dropna()
        pts = [
            (sch.x(bar_index(window, t)), sch.y(max(p_lo, min(p_hi, float(v)))))
            for t, v in windowed.items()
        ]
        if len(pts) >= 2:
            s += svg_poly("polyline", pts, stroke=theme.accent2, width=1.5)
    s += svg_text(
        sch.inner_x0, 11, "Kanal İçi Pozisyon",
        fill=theme.text_muted, size=9.5, family=theme.font_body, weight=600,
    )
    return s


def build(result: IndicatorResult, df: pd.DataFrame, theme: SVGTheme) -> SceneOut:
    window = _window(df)
    main_svg = _main_panel(result, df, window, theme)
    sub_svg = _sub_panel(result, window, theme)
    return SceneOut(
        title=f"{result.symbol} — Trend Kanalı",
        subtitle="Regresyon kanalı · kanal içi pozisyon",
        badge=None,
        panels=[
            PanelOut(vb=(_MAIN_W, _MAIN_H), svg=main_svg),
            PanelOut(vb=(_SUB_W, _SUB_H), svg=sub_svg),
        ],
    )
