"""`structure.market_structure` -> saf SVG sahne (Faz 4d, `ornek1.png`
standardı — `docs/GORSEL_HATA_TESHISI.md` bölüm 4/5).

`structure.market_structure` gerçek bir CATALOG göstergesi DEĞİL —
`structure.price_structure` (trend çizgileri) + `structure.supply_demand`
(varsayılan `method="pivot"`) + TAZE hesaplanan BOS/CHoCH (`tlab/features/
market_structure.py`) + pivot yapı etiketleri (HH/HL/LH/LL) + tek bir
EMA-50 çizgisini birleştiren sentetik bir isim (bkz. `tlab/viz/live.py::
compute_market_structure_merged`, `structure.report`/`confluence`'ın AYNI
"post-processing köprüsü" deseni).

Referans `ornek1.png`/`ornek2.png`'den BİLİNÇLİ sapmalar:
1. Pivot etiketleri artık BİRLEŞTİRİCİ ZİGZAG ÇİZGİSİ TAŞIMAZ — yalnızca
   küçük bir üçgen + kısa metin (kullanıcının kendi ifadesi: "bizim gibi
   oradan oraya çizgi götürmüyor, tepelerine ve diplerine küçük üçgenle ve
   yazıyla resmetmiş"). `swing_fib_abcd.py`/`report.py`'nin eski nokta+metin
   deseninin YERİNE geçer (bu ikisi BİLİNÇLİ OLARAK değiştirilmedi — kendi
   sahnelerinin farklı bir amacı var, VAH/POC/fib merdiveni).
2. Trend çizgisi rengi ornek1'in "düşen=mor/magenta" özel tonunu DEĞİL,
   tema sözleşmesindeki `up`/`down` (yön anlamı taşıyan, LOAD-BEARING
   renkler — mumlarla AYNI) kullanır: yükselen=yeşil, düşen=kırmızı. Yeni
   bir tema tokenı icat etmek yerine mevcut 3-temalı sözleşmeye sadık
   kalındı.
3. BOS/CHoCH seviyeleri `Level(style=ev.kind)` olarak taşınır; yalnızca
   PENCEREDEKİ en fazla `_MAX_MS_EVENTS` en güncel olay çizilir (declutter,
   `report.py`/`swing_fib_abcd.py`'nin "yalnızca en güncel grup" ilkesiyle
   AYNI kategori)."""

from __future__ import annotations

import pandas as pd

from tlab.core.types import IndicatorResult
from tlab.viz.svg.axes import price_labels, right_label, x_labels
from tlab.viz.svg.candles import draw_candles
from tlab.viz.svg.layout import LabelBox, Placement, leader_line, resolve_collisions
from tlab.viz.svg.prim import svg_line, svg_rect, svg_text, svg_triangle
from tlab.viz.svg.scale import Chart, bar_index, pad_range
from tlab.viz.svg.scenes.base import PanelOut, SceneOut
from tlab.viz.svg.theme import SVGTheme

_W, _H = 820.0, 460.0
_LAST_N = 150
_MAX_SWING_LABELS = 8
_MAX_TRENDLINES_PER_DIR = 2
_MAX_MS_EVENTS = 4
_MAX_BROKEN_ZONES_SHOWN = 2
_TRI_SIZE = 4.5

_SWING_HINTS: dict[str, tuple[Placement, ...]] = {
    "HH": ("above", "below"), "LH": ("above", "below"),
    "HL": ("below", "above"), "LL": ("below", "above"),
}


def _window(df: pd.DataFrame) -> pd.DataFrame:
    return df.iloc[-_LAST_N:] if len(df) > _LAST_N else df


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


_PROJECTION_CAP = 3  # report.py::_most_touched_line ile AYNI kural (Faz 7,
# kısa/dik bacakların sınırsız eğimle gerçek dışı büyümesi bulunup
# düzeltilmişti) -- burada da yalnızca projeksiyonu pencerenin sağ kenarına
# ULAŞABİLEN (3x bacak süresi içinde) çizgiler aday sayılır.


def _nearest_open_zones(result: IndicatorResult) -> list:
    """`supply_demand.py`'nin AYNI ilkesi (bkz. o dosyanın docstring'i):
    TÜM açık bölgeleri değil, yalnızca indikatörün KENDİ ATR-normalize "en
    yakın" seçimini (`last_state["nearest_demand"/"nearest_supply"]`)
    çizer -- pivot yöntemi çok sayıda üst üste binen küçük bölge
    üretebiliyor (2026-09-05, THYAO'da GÖRÜLEREK bulundu: aynı anda 3 açık
    demand kutusu neredeyse aynı fiyat bandında sağ kenarı doldurup
    okunaksız bir yığın oluşturuyordu)."""
    zones = []
    for key in ("nearest_demand", "nearest_supply"):
        info = result.last_state.get(key)
        if not info:
            continue
        kind = "demand" if key == "nearest_demand" else "supply"
        match = next(
            (
                bx for bx in result.boxes
                if bx.style == kind
                and abs(bx.low - info["low"]) < 1e-6 and abs(bx.high - info["high"]) < 1e-6
            ),
            None,
        )
        if match is not None:
            zones.append(match)
    return zones


def _recent_broken_zones(result: IndicatorResult, window: pd.DataFrame) -> list:
    candidates = [
        bx for bx in result.boxes
        if bx.style in ("demand_broken", "supply_broken")
        and bx.t0 <= window.index[-1] and bx.t1 >= window.index[0]
    ]
    return sorted(candidates, key=lambda bx: bx.t1, reverse=True)[:_MAX_BROKEN_ZONES_SHOWN]


def _top_trendlines(
    result: IndicatorResult, df: pd.DataFrame, win_start: pd.Timestamp, last_bar_idx: int
) -> list:
    """`Line.touches`e göre en çok temaslı en fazla `_MAX_TRENDLINES_PER_
    DIR` yükselen + aynı sayıda düşen çizgi — ekranı temassız/zayıf
    adaylarla doldurmamak için (spec: "aynı anda çizilecek trend çizgisi
    sayısını sınırla")."""
    candidates = []
    for ln in result.lines:
        if ln.style not in ("resistance", "support") or ln.direction is None:
            continue
        if ln.points[-1][0] < win_start:
            continue
        (t1, _), (t2, _) = ln.points[0], ln.points[-1]
        b1, b2 = bar_index(df, t1), bar_index(df, t2)
        if b2 + _PROJECTION_CAP * max(1, b2 - b1) < last_bar_idx:
            continue
        candidates.append(ln)
    rising = sorted(
        (ln for ln in candidates if ln.direction == "rising"),
        key=lambda ln: ln.touches or 0, reverse=True,
    )[:_MAX_TRENDLINES_PER_DIR]
    falling = sorted(
        (ln for ln in candidates if ln.direction == "falling"),
        key=lambda ln: ln.touches or 0, reverse=True,
    )[:_MAX_TRENDLINES_PER_DIR]
    return rising + falling


def _trend_label(ln) -> str:
    yon = "YÜKSELEN TREND" if ln.direction == "rising" else "DÜŞEN TREND"
    durum = "KIRILMIŞ" if ln.broken else "AKTİF"
    return f"{yon} | {durum} | TEMAS: {ln.touches or 0}"


def build(result: IndicatorResult, df: pd.DataFrame, theme: SVGTheme) -> SceneOut:
    window = _window(df)
    window_offset = len(df) - len(window)
    win_start = window.index[0]
    i_max = len(window) - 1

    def full_pos(t: pd.Timestamp) -> float:
        return bar_index(df, t) - window_offset

    lo, hi = pad_range(float(window["low"].min()), float(window["high"].max()), 0.08)
    zones = _nearest_open_zones(result) + _recent_broken_zones(result, window)
    zones = [bx for bx in zones if bx.high >= lo and bx.low <= hi]

    chart = Chart(
        w=_W, h=_H, margin_l=48, margin_r=118, margin_t=20, margin_b=28,
        i_domain=(0, i_max), p_domain=(lo, hi),
    )

    s = price_labels(chart, theme, 5)
    s += x_labels(chart, _pick_x_ticks(window), theme)

    # Arz/talep bölgeleri EN ALTTA (mumların/çizgilerin arkasında kalsın).
    zone_boxes_svg = ""
    zone_labels_svg = ""
    for bx in zones:
        broken = bx.style.endswith("_broken")
        color = theme.demand if bx.style.startswith("demand") else theme.supply
        x0 = max(chart.x(full_pos(bx.t0)), chart.inner_x0)
        y0, y1 = chart.y(bx.low), chart.y(bx.high)
        if broken:
            x1 = chart.x(full_pos(bx.t1))
            zone_boxes_svg += svg_rect(
                x0, y1, max(x1 - x0, 2), y0 - y1,
                fill="none", stroke=color, stroke_width=1, dash="3,2", opacity=0.5,
            )
            continue
        zone_boxes_svg += svg_rect(
            x0, y1, chart.inner_x1 - x0, y0 - y1,
            fill=color, opacity=0.16 if theme.key == "dark" else 0.13,
        )
        zone_boxes_svg += svg_line(x0, y0, chart.inner_x1, y0, stroke=color, width=1, opacity=0.55)
        zone_boxes_svg += svg_line(x0, y1, chart.inner_x1, y1, stroke=color, width=1, opacity=0.55)
        # Etiket ÇİZİM ALANININ DIŞINDA, sağ kenar boşluğunda -- ornek1.png'nin
        # "SUPPLY / ARZ" + fiyat aralığı iki satırlı yerleşimi.
        kind_tr = "DEMAND / TALEP" if bx.style.startswith("demand") else "SUPPLY / ARZ"
        mid_y = (y0 + y1) / 2
        zone_labels_svg += right_label(
            chart, mid_y - 6, kind_tr, theme, fill=color, size=9, weight=700,
        )
        zone_labels_svg += right_label(
            chart, mid_y + 6, f"{bx.low:.2f} - {bx.high:.2f}", theme,
            fill=theme.text_muted, size=8.5,
        )
    s += zone_boxes_svg
    s += draw_candles(window, chart, theme)

    # Tek hareketli ortalama (EMA-50) -- fiyatı takip eden TAM polyline
    # (K1'in `renderer.py` düzeltmesiyle AYNI ilke: yalnızca ilk+son nokta
    # DEĞİL, serinin TAMAMI).
    for ln in result.lines:
        if ln.style != "single_ma":
            continue
        pts = [(full_pos(t), p) for t, p in ln.points if t >= win_start]
        if len(pts) < 2:
            continue
        xs = [chart.x(i) for i, _ in pts]
        ys = [chart.y(p) for _, p in pts]
        path = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys, strict=True))
        s += f'<polyline points="{path}" fill="none" stroke="{theme.accent2}" stroke-width="2"/>'

    # Temas-sayılı trend çizgileri (en fazla 2 yükselen + 2 düşen).
    last_bar_idx = bar_index(df, window.index[-1])
    for ln in _top_trendlines(result, df, win_start, last_bar_idx):
        (t1, p1), (t2, p2) = ln.points[0], ln.points[-1]
        x1, y1 = chart.x(full_pos(t1)), chart.y(p1)
        x2 = chart.inner_x1
        # `Line` (tlab.core.types) `Trendline`nin (features/trendlines.py)
        # `value_at()`'ini TAŞIMAZ -- eğim iki noktadan burada türetilir,
        # pencerenin sağ kenarına kadar projekte edilir (report.py'nin AYNI
        # "3x bacak süresi" sınırı burada YOK -- çizgi zaten yalnızca EN ÇOK
        # temaslı 2+2 aday arasından seçildiği için aşırı kısa/dik bir bacak
        # bu havuza girmesi olası değil).
        slope = (p2 - p1) / max(1e-9, full_pos(t2) - full_pos(t1))
        y2 = chart.y(p1 + slope * (i_max - full_pos(t1)))
        color = theme.up if ln.direction == "rising" else theme.down
        s += svg_line(x1, y1, x2, y2, stroke=color, width=2, dash="2,3", opacity=0.9)
        s += svg_text(
            (x1 + x2) / 2, min(y1, y2) - 8, _trend_label(ln), fill=color, size=10,
            family=theme.font_body, weight=700, anchor="middle",
        )

    # BOS/CHoCH -- kırılan seviyeden kesikli yatay çizgi + işaret.
    _ms_styles = ("bos_up", "bos_down", "choch_up", "choch_down")
    ms_levels = [lv for lv in result.levels if lv.style in _ms_styles]
    ms_levels = [
        lv for lv in ms_levels if lv.start is not None and lv.start >= win_start
    ][-_MAX_MS_EVENTS:]
    for lv in ms_levels:
        color = theme.up if lv.style.endswith("_up") else theme.down
        x0 = chart.x(full_pos(lv.start))
        x1 = chart.x(full_pos(lv.end)) if lv.end is not None else chart.inner_x1
        y = chart.y(lv.price)
        s += svg_line(x0, y, x1, y, stroke=color, width=1.3, dash="4,3", opacity=0.8)

    # 2026-09-05, GERÇEK bir hata BAKAB'da GÖRÜLEREK bulundu: birden fazla
    # BOS/CHoCH olayı zaman/fiyatça birbirine yakınsa (`bar_idx=X+4,y-6`
    # sabit ofsetiyle) etiketler ÜST ÜSTE BİNİYORDU ("CHoCH↓CHoCH↓" okunamaz
    # hâle geliyordu) -- swing etiketleriyle AYNI `resolve_collisions`
    # havuzuna alındı.
    ms_markers = [
        m for m in result.markers
        if m.kind.startswith("ms_") and m.t >= win_start
    ][-_MAX_MS_EVENTS:]
    ms_boxes: list[LabelBox] = []
    for m in ms_markers:
        x, y = chart.x(bar_index(window, m.t)), chart.y(m.price)
        ms_boxes.append(
            LabelBox(
                anchor_x=x, anchor_y=y, w=len(m.text) * 6.2 + 4, h=13, text=m.text,
                priority=2, placement_hints=("above", "right", "below", "left"),
            )
        )
    ms_collision = resolve_collisions(ms_boxes, bounds=(
        chart.inner_x0, chart.inner_y0,
        chart.inner_x1 - chart.inner_x0, chart.inner_y1 - chart.inner_y0,
    ))
    for i, placed in enumerate(ms_collision.placed):
        m = ms_markers[i]
        color = theme.up if "up" in m.kind else theme.down
        s += leader_line(placed, stroke=color, opacity=0.5)
        s += svg_text(
            placed.x, placed.y + placed.box.h - 3, m.text, fill=color, size=10,
            family=theme.font_body, weight=700 if m.text.endswith("AKTİF") else 600,
        )

    # Pivot üçgenleri (HH/LH altın, tepe aşağı bakar, pivotun ÜSTÜNDE; HL/LL
    # ikincil vurgu rengi, tepe yukarı bakar, pivotun ALTINDA) -- birleştirici
    # zigzag çizgisi YOK (kullanıcının açık reddi, modül docstring'ine bkz.).
    swing_markers = [
        m for m in result.markers
        if m.kind == "structure_label" and m.t >= win_start and m.text in _SWING_HINTS
    ][-_MAX_SWING_LABELS:]

    boxes: list[LabelBox] = []
    for i, m in enumerate(swing_markers):
        x, y = chart.x(bar_index(window, m.t)), chart.y(m.price)
        gold = m.text in ("HH", "LH")
        tri_y = y - _TRI_SIZE * 2.4 if gold else y + _TRI_SIZE * 2.4
        s += svg_triangle(
            x, tri_y, _TRI_SIZE, "down" if gold else "up",
            fill=theme.accent if gold else theme.accent2,
        )
        boxes.append(
            LabelBox(
                anchor_x=x, anchor_y=tri_y, w=18, h=12, text=f"swing_{i}", priority=1,
                placement_hints=_SWING_HINTS[m.text],
            )
        )
    bounds = (
        chart.inner_x0, chart.inner_y0,
        chart.inner_x1 - chart.inner_x0, chart.inner_y1 - chart.inner_y0,
    )
    collision = resolve_collisions(boxes, bounds)
    for i, placed in enumerate(collision.placed):
        m = swing_markers[i]
        gold = m.text in ("HH", "LH")
        s += leader_line(placed, stroke=theme.text_muted)
        s += svg_text(
            placed.x + placed.box.w / 2, placed.y + placed.box.h - 2, m.text,
            fill=theme.accent if gold else theme.accent2, size=9.5,
            family=theme.mono, anchor="middle", weight=700,
        )

    s += zone_labels_svg

    return SceneOut(
        title=f"{result.symbol} — Piyasa Yapısı (SMC)",
        subtitle="Pivot yapı + BOS/CHoCH + arz/talep + trend çizgisi",
        badge=None,
        panels=[PanelOut(vb=(_W, _H), svg=s)],
    )
