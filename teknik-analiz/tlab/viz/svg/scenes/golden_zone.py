"""`structure.golden_zone` -> saf SVG sahne (Faz 4a, 4/6).

Referans: `docs/design/grafik_stil_vitrini_files/saved_resource.html::
sceneGoldenSupply`nin SOL yarısı (satır 682-699, `chL`/`left`) -- altın
bölge (0.618-0.786) bandı + 0.5 fib çizgisi + reaksiyon işareti.

**Mimari sapma (bilinçli, `docs/PROGRESS_LOG.md`nin 2026-09-04 "swing_fib_
abcd sahnesi" girdisinde önceden not edildi):** artifact'in `sceneGoldenSupply`si
İKİ FARKLI sembolü (ALARK golden zone solda, ASELS arz-talep sağda) yan yana
gösteren bir VİTRİN DEMOSU -- gerçek katalogda `structure.golden_zone` ve
`structure.supply_demand` AYRI iki indikatör, `tlab/viz/svg/__init__.py::
_SCENES` de `result.indicator` başına TEK sahne bekliyor. `live.py::
render_structure_report_live`'ın kendi docstring'i (2026-08-30 "deneme + geri
alma" notu) bu ikisinin BİLİNÇLİ olarak ayrı/temiz grafiklerde kalmasını
istiyor -- bu yüzden iki AYRI sahne dosyası yazıldı, artifact'in iki-sembollü
`twoUp` yerleşimi PORTLANMADI.

Declutter: `GoldenZoneIndicator.compute()` HER ardışık zigzag (X,A) çifti için
bir bant üretir (geçmiş, süperseded bantlar dahil) -- yalnızca EN GÜNCEL
(hâlâ açık, `t1 >= pencerenin son barı`) bant çizilir, `report.py::_active_box`
ile AYNI "hâlâ aktif" testi (kopya değil, ayrı yazıldı -- sahneler birbirini
import etmez)."""

from __future__ import annotations

import pandas as pd

from tlab.core.types import Box, IndicatorResult, Level, Marker
from tlab.viz.svg.axes import price_labels, x_labels
from tlab.viz.svg.candles import draw_candles
from tlab.viz.svg.prim import svg_circle, svg_line, svg_rect, svg_text
from tlab.viz.svg.scale import Chart, bar_index, pad_range
from tlab.viz.svg.scenes.base import PanelOut, SceneOut
from tlab.viz.svg.theme import SVGTheme

_W, _H = 620.0, 420.0
_LAST_N = 150

_MARKER_COLOR = {
    "golden_zone_reaction": "accent",
    "golden_zone_success": "up",
    "golden_zone_fail": "down",
}


def _window(df: pd.DataFrame) -> pd.DataFrame:
    return df.iloc[-_LAST_N:] if len(df) > _LAST_N else df


def _active_box(result: IndicatorResult, style: str, window: pd.DataFrame) -> Box | None:
    last_bar = window.index[-1]
    candidates = [bx for bx in result.boxes if bx.style == style and bx.t1 >= last_bar]
    if not candidates:
        return None
    return max(candidates, key=lambda bx: bx.t0)


def _half_level(result: IndicatorResult, active: Box) -> Level | None:
    return next(
        (
            lv for lv in result.levels
            if lv.label == "fib_0.5" and lv.start == active.t0
        ),
        None,
    )


def _zone_markers(result: IndicatorResult) -> list[Marker]:
    """`Marker` kendi `swing_id`sini taşımaz (yalnızca `Signal.payload` taşır)
    -- yalnızca ZAMAN aralığına göre filtrelemek (aktif kutunun t0-t1'i)
    1. iterasyonda GERÇEK bir hataya yol açtı: içi içe/çakışan eski bir
    swing'in REAKSİYON/BAŞARILI/BAŞARISIZ işareti de aynı aralığa düşüp
    aktif bölgenin işaretiyle ÜST ÜSTE biniyordu. Doğru eşleşme: en büyük
    `swing_id`ye sahip sinyallerin (compute() sırayla i=1..n ürettiği için
    bu HER ZAMAN en güncel/aktif swing'tir) bar_time'larına karşılık gelen
    marker'lar."""
    ids = [int(s.payload["swing_id"]) for s in result.signals if "swing_id" in s.payload]
    if not ids:
        return []
    active_id = max(ids)
    marker_events = ("golden_zone_reaction", "golden_zone_fail", "golden_zone_success")
    active_bar_times = {
        s.bar_time for s in result.signals
        if s.payload.get("swing_id") == active_id and s.payload.get("event") in marker_events
    }
    return [m for m in result.markers if m.kind in _MARKER_COLOR and m.t in active_bar_times]


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


def build(result: IndicatorResult, df: pd.DataFrame, theme: SVGTheme) -> SceneOut:
    window = _window(df)
    window_offset = len(df) - len(window)
    i_max = len(window) - 1

    def full_pos(t: pd.Timestamp) -> float:
        return bar_index(df, t) - window_offset

    active = _active_box(result, "golden_zone", window)
    alt = _active_box(result, "golden_zone_alt", window)
    half = _half_level(result, active) if active is not None else None
    markers = _zone_markers(result)

    key_prices = [float(window["low"].min()), float(window["high"].max())]
    if active is not None:
        key_prices += [active.low, active.high]
    if alt is not None:
        key_prices += [alt.low, alt.high]
    lo, hi = pad_range(min(key_prices), max(key_prices), 0.08)

    chart = Chart(
        w=_W, h=_H, margin_l=48, margin_r=14, margin_t=20, margin_b=28,
        i_domain=(0, i_max), p_domain=(lo, hi),
    )

    s = price_labels(chart, theme, 4)
    s += x_labels(chart, _pick_x_ticks(window), theme)
    s += draw_candles(window, chart, theme)

    if active is not None:
        zx0 = max(chart.x(full_pos(active.t0)), chart.inner_x0)
        zy0, zy1 = chart.y(active.low), chart.y(active.high)
        s += svg_rect(
            zx0, zy1, chart.inner_x1 - zx0, zy0 - zy1,
            fill=theme.accent, opacity=0.14 if theme.key == "dark" else 0.11,
        )
        s += svg_line(
            zx0, zy0, chart.inner_x1, zy0, stroke=theme.accent, width=1, dash="3,3", opacity=0.7,
        )
        s += svg_line(
            zx0, zy1, chart.inner_x1, zy1, stroke=theme.accent, width=1, dash="3,3", opacity=0.7,
        )
        # Etiket kutunun ÜSTÜNE değil İÇİNE konur -- 4. iterasyonda (THYAO
        # dark) GERÇEK bir hata bulundu: downtrend'de "BAŞARISIZ" işareti de
        # kutunun üst kenarına yakın (kutunun içine değil dışına, fiyat üst
        # sınırı kırdığı için) düşüyor, dışarıdaki etiket onunla üst üste
        # biniyordu. Kutunun içi (marker'lar zaten dışarıda kalıyor,
        # aşağıdaki yön mantığına bkz.) her zaman boş kalan tek yer.
        s += svg_text(
            zx0 + 6, zy1 + 14, "ALTIN BÖLGE · 0.618–0.786",
            fill=theme.accent, size=9.5, family=theme.font_body, weight=700,
        )

    if alt is not None:
        ax0 = max(chart.x(full_pos(alt.t0)), chart.inner_x0)
        ay0, ay1 = chart.y(alt.low), chart.y(alt.high)
        s += svg_rect(
            ax0, ay1, chart.inner_x1 - ax0, ay0 - ay1,
            fill=theme.muted, opacity=0.25 if theme.key == "dark" else 0.35,
        )

    if half is not None:
        x0 = max(chart.x(full_pos(half.start)), chart.inner_x0) if half.start else chart.inner_x0
        y = chart.y(half.price)
        s += svg_line(
            x0, y, chart.inner_x1, y, stroke=theme.text_faint, width=1, dash="2,3", opacity=0.6,
        )
        s += svg_text(
            chart.inner_x1 - 4, y - 5, f"0.5 · {half.price:.2f}",
            fill=theme.text_muted, size=9, family=theme.mono, anchor="end",
        )

    for m in markers:
        if m.t not in window.index:
            continue
        x, y = chart.x(bar_index(window, m.t)), chart.y(m.price)
        color = getattr(theme, _MARKER_COLOR[m.kind])
        s += svg_circle(x, y, 4, fill="none", stroke=color, stroke_width=2)
        # Etiket yönü fiyatın kutuya göre konumuna bağlı -- bir REAKSİYON/
        # BAŞARILI/BAŞARISIZ kutunun dışına (üstüne veya altına) taşınca
        # (ör. downtrend'de "BAŞARISIZ" kutunun ÜST kenarını kırar) etiket
        # o yöne, kutudan UZAKLAŞARAK yerleşir -- "ALTIN BÖLGE" etiketi artık
        # kutunun İÇİNDE olduğu için bu ikisi asla aynı bandı paylaşmaz.
        above = active is not None and m.price >= active.high
        dy = -10 if above else 18
        s += svg_text(
            x, y + dy, m.text, fill=color, size=9.5, family=theme.font_body,
            anchor="middle", weight=600,
        )

    return SceneOut(
        title=f"{result.symbol} — Golden Zone",
        subtitle="Fibonacci altın bölge (0.618–0.786) geri çekilme bandı",
        badge=None,
        panels=[PanelOut(vb=(_W, _H), svg=s)],
    )
