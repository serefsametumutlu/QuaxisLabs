"""`structure.swing_fib_abcd` -> saf SVG sahne (Faz 4a, 3/6).

Referans: `docs/design/grafik_stil_vitrini_files/saved_resource.html::
sceneSwingFib` (satır 643-677) -- swing zigzag zinciri + HH/HL/LH/LL
etiketleri + AB=CD D-hedef projeksiyonu (yatay çizgi + etiket) + en güncel
bacağın Fibonacci retracement/uzatım merdiveni (0.618/0.786 altın vurgu).

Artifact'ten BİLİNÇLİ sapmalar:
1. Artifact'in D-hedefi UYDURMA bir eğik ("A-B eğimiyle projekte edilmiş")
   çizgiydi -- gerçekte `SwingFibABCD.compute()`'un ürettiği `Level` YATAY
   bir fiyat seviyesidir (`price`, `start`=C barı, `end`=None [hâlâ açık]
   veya tamamlanma/geçersizleşme barı) -- artifact'in eğik çizgisi değil,
   `report.py`nin VAH/POC/VAL çizgileriyle AYNI yatay-seviye deseni izlendi.
2. Yalnızca EN GÜNCEL üçlünün (en büyük `start`) hedefleri çizilir --
   `report.py::_declutter` ilkesiyle AYNI (eski üçlülerin hedefleri, hangi
   adaya ait oldukları bağlamı taşımadığı için saf gürültü).
3. Fibonacci merdiveni yalnızca `end is None` olan Level'lar -- `_fibonacci_
   levels`'ın kendi sözleşmesi zaten yalnızca EN YENİ bacağın `end=None`
   kaldığını garanti ediyor (bkz. o fonksiyonun docstring'i), ayrı bir
   gruplama/en-güncel-seçme adımı GEREKMİYOR.
4. Swing HH/HL/LH/LL etiketleri `report.py::_main_panel`nin AYNI
   `resolve_collisions` desenini kullanır (kopya-yapıştır değil, aynı
   mantık ayrı ayrı yazıldı -- `tlab/viz/svg/scenes/*` modülleri bilinçli
   olarak birbirini import etmez, bkz. harmonik ekollerin "ekoller
   birbirini import etmez" ilkesiyle AYNI izolasyon kararı)."""

from __future__ import annotations

import re

import pandas as pd

from tlab.core.types import IndicatorResult, Level
from tlab.viz.svg.axes import price_labels, right_label, x_labels
from tlab.viz.svg.candles import draw_candles
from tlab.viz.svg.layout import LabelBox, Placement, leader_line, resolve_collisions
from tlab.viz.svg.prim import svg_circle, svg_line, svg_text
from tlab.viz.svg.scale import Chart, bar_index, pad_range
from tlab.viz.svg.scenes.base import PanelOut, SceneOut
from tlab.viz.svg.theme import SVGTheme

_W, _H = 780.0, 460.0
_LAST_N = 150
_MAX_SWING_LABELS = 6

_SWING_HINTS: dict[str, tuple[Placement, ...]] = {
    "HH": ("above", "below"), "LH": ("above", "below"),
    "HL": ("below", "above"), "LL": ("below", "above"),
}

_GOLD_RATIOS = {0.618, 0.786}
_FIB_RATIO_RE = re.compile(r"^fib_([\d.]+)$")


def _window(df: pd.DataFrame) -> pd.DataFrame:
    return df.iloc[-_LAST_N:] if len(df) > _LAST_N else df


def _pick_x_ticks(window: pd.DataFrame, n: int = 5) -> list[tuple[float, str]]:
    """report.py::_pick_x_ticks ile AYNI ("Tem '26" ardışık tekrarı hatası
    burada da mümkün, aynı savunma tekrarlanır)."""
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


def _latest_targets(result: IndicatorResult) -> list[Level]:
    d_levels = [lv for lv in result.levels if lv.style in ("bullish", "bearish")]
    starts = [lv.start for lv in d_levels if lv.start is not None]
    if not starts:
        return []
    latest_start = max(starts)
    return [lv for lv in d_levels if lv.start == latest_start]


def _fib_ladder(result: IndicatorResult) -> list[Level]:
    return [
        lv for lv in result.levels
        if lv.style in ("fib_retracement", "fib_extension") and lv.end is None
    ]


def build(result: IndicatorResult, df: pd.DataFrame, theme: SVGTheme) -> SceneOut:
    window = _window(df)
    window_offset = len(df) - len(window)
    win_start = window.index[0]
    i_max = len(window) - 1

    def full_pos(t: pd.Timestamp) -> float:
        return bar_index(df, t) - window_offset

    targets = _latest_targets(result)
    ladder = _fib_ladder(result)
    swing_markers = [
        m for m in result.markers
        if m.kind == "structure_label" and m.t >= win_start and m.text in _SWING_HINTS
    ][-_MAX_SWING_LABELS:]

    # D-hedef fiyatları BİLİNÇLİ OLARAK y-ekseni hesabına DAHİL EDİLMEZ --
    # 3 farklı oran (1.0/1.272/1.618) fiyatça çok ayrışabiliyor, en agresif
    # (1.618) genelde ekranın "doğal" aralığının çok dışında kalıyor; onu
    # da sığdırmaya çalışmak mumları ekranın küçük bir üst şeridine
    # sıkıştırıyordu (1. iterasyonda THYAO'da GERÇEKTEN gözlemlendi -- 350-250
    # TL'lik mum aralığı 360-230'a genişleyip grafiğin alt üçte biri boş
    # kalıyordu). Yalnızca ekranın DOĞAL aralığına düşen hedefler çizilir
    # (aşağıdaki döngüde sessizce atlanır) -- report.py'nin VAH/POC/VAL'i
    # asla ekseni yeniden ölçeklendirmemesiyle AYNI ilke.
    key_prices = [float(window["low"].min()), float(window["high"].max())]
    key_prices += [lv.price for lv in ladder]
    key_prices += [m.price for m in swing_markers]
    lo, hi = pad_range(min(key_prices), max(key_prices), 0.08)

    chart = Chart(
        w=_W, h=_H, margin_l=48, margin_r=94, margin_t=20, margin_b=28,
        i_domain=(0, i_max), p_domain=(lo, hi),
    )

    s = price_labels(chart, theme, 5)
    s += x_labels(chart, _pick_x_ticks(window), theme)
    s += draw_candles(window, chart, theme)

    for ln in result.lines:
        if ln.style != "swing":
            continue
        (t1, p1), (t2, p2) = ln.points
        x1, y1 = chart.x(full_pos(t1)), chart.y(p1)
        x2, y2 = chart.x(full_pos(t2)), chart.y(p2)
        s += svg_line(x1, y1, x2, y2, stroke=theme.accent2, width=1.4, opacity=0.85)

    for lv in ladder:
        ratio_match = _FIB_RATIO_RE.match(lv.label)
        ratio_val = float(ratio_match.group(1)) if ratio_match else None
        gold = ratio_val in _GOLD_RATIOS
        x0 = max(chart.x(full_pos(lv.start)), chart.inner_x0) if lv.start else chart.inner_x0
        y = chart.y(lv.price)
        s += svg_line(
            x0, y, chart.inner_x1, y,
            stroke=theme.accent if gold else theme.muted, width=1,
            dash="2,3", opacity=0.85 if gold else 0.5,
        )
        ratio_text = f"{ratio_val:.3f}" if ratio_val is not None else lv.label
        s += right_label(
            chart, y, f"{ratio_text} · {lv.price:.2f}", theme,
            fill=theme.accent if gold else theme.text_faint, size=9.5, weight=700 if gold else 400,
        )

    for lv in targets:
        if not (lo <= lv.price <= hi):
            continue
        color = theme.up if lv.style == "bullish" else theme.down
        x0 = chart.x(full_pos(lv.start)) if lv.start else chart.inner_x0
        x1 = chart.x(full_pos(lv.end)) if lv.end is not None else chart.inner_x1
        y = chart.y(lv.price)
        s += svg_line(x0, y, x1, y, stroke=color, width=1.6, dash="4,3", opacity=0.85)
        s += right_label(chart, y, lv.label, theme, fill=color, size=10, weight=700)

    boxes: list[LabelBox] = []
    for i, m in enumerate(swing_markers):
        box_id = f"swing_{i}"
        x, y = chart.x(bar_index(window, m.t)), chart.y(m.price)
        boxes.append(
            LabelBox(
                anchor_x=x, anchor_y=y, w=22, h=14, text=box_id, priority=1,
                placement_hints=_SWING_HINTS[m.text],
            )
        )
        s += svg_circle(x, y, 2.6, fill=theme.text)
    bounds = (
        chart.inner_x0, chart.inner_y0,
        chart.inner_x1 - chart.inner_x0, chart.inner_y1 - chart.inner_y0,
    )
    collision = resolve_collisions(boxes, bounds)
    for i, placed in enumerate(collision.placed):
        m = swing_markers[i]
        s += leader_line(placed, stroke=theme.text_muted)
        s += svg_text(
            placed.x + placed.box.w / 2, placed.y + placed.box.h - 3, m.text,
            fill=theme.text_muted, size=10, family=theme.mono, anchor="middle", weight=600,
        )

    return SceneOut(
        title=f"{result.symbol} — Swing Yapısı ve AB=CD Analizi",
        subtitle="Fibonacci geri çekilme / uzatım merdiveni",
        badge=None,
        panels=[PanelOut(vb=(_W, _H), svg=s)],
    )
