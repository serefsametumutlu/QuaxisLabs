"""`structure.report` -> saf SVG sahne (Faz 4a).

Referans: `docs/design/grafik_stil_vitrini.html::sceneReport` (satır ~492-568)
-- ana panel (mumlar + tek DİRENÇ trend çizgisi [solid + sağa dashed
projeksiyon] + tek DESTEK BÖLGESİ kutusu + VAH/POC/VAL seviyeleri + son
birkaç HH/HL/LH/LL swing etiketi), sağda DİKEY hacim profili paneli (HVN
barları farklı renkte + Gauss eğrisi), altta RSI(14) paneli (70/30 eşikleri).

`structure.report` gerçek bir CATALOG göstergesi DEĞİL -- `structure.
price_structure` + `structure.swing_fib_abcd`'i TEK bir `IndicatorResult`ta
birleştiren sentetik bir isim (bkz. `tlab/viz/live.py::
compute_structure_report_merged` -- `web/backend/routes/chart.py`nin ZATEN
yaptığı AYNI birleştirme, burada TEK NOKTAYA taşındı). Bu sahne o BİRLEŞİK
result'ı alır; `result.series["vp_bins"/"vp_volumes"/"vp_gauss"/"vp_hvn"]`
FİYAT-indeksli (zaman DEĞİL, bkz. `price_structure.py` docstring'i) --
side panel bunları kendi p_domain'ine göre çizer, X ekseni hiç kullanmaz.

Artifact'ten BİLİNÇLİ sapma: trendline projeksiyonu artifact'in sınırsız
eğim uzatmasını DEĞİL, `renderer.py::Line.extend_right`'ın Faz 7'de bulunan
"kısa/dik bacak gerçek dışı büyütüyor" dersini izler -- uzatma yalnızca
PENCERENİN sağ kenarına kadar (chart genişliği zaten doğal bir üst sınır)."""

from __future__ import annotations

import re

import pandas as pd

from tlab.core.types import IndicatorResult
from tlab.viz.svg.axes import price_labels, x_labels
from tlab.viz.svg.candles import draw_candles
from tlab.viz.svg.layout import LabelBox, Placement, leader_line, resolve_collisions
from tlab.viz.svg.prim import svg_circle, svg_line, svg_poly, svg_rect, svg_text
from tlab.viz.svg.scale import Chart, bar_index, pad_range
from tlab.viz.svg.scenes.base import PanelOut, SceneOut
from tlab.viz.svg.theme import SVGTheme

_MAIN_W, _MAIN_H = 780.0, 420.0
_SIDE_W, _SIDE_H = 190.0, 420.0
_RSI_W, _RSI_H = 780.0, 96.0
_LAST_N = 150
_MAX_SWING_LABELS = 6

_SWING_HINTS: dict[str, tuple[Placement, ...]] = {
    "HH": ("above", "below"), "LH": ("above", "below"),
    "HL": ("below", "above"), "LL": ("below", "above"),
}


def _window(df: pd.DataFrame) -> pd.DataFrame:
    return df.iloc[-_LAST_N:] if len(df) > _LAST_N else df


_TOUCHES_RE = re.compile(r"Temas:(\d+)")


_PROJECTION_CAP = 3  # renderer.py::Line uzatma kuralıyla AYNI (Faz 7, kısa/dik
# bacakların sınırsız eğimle gerçek dışı büyümesi bulunup düzeltilmişti)


def _most_touched_line(result: IndicatorResult, style: str, df: pd.DataFrame, last_bar_idx: int):
    """En çok temas edilen, KIRILMAMIŞ trend çizgisini seçer -- 2. şart
    ("reach") ile ilk denemede bulunan GERÇEK bir hatayı kapatır: en çok
    temas edilen çizgi genelde çok ESKİ (kısa ömürlü, ör. 4 barlık) bir
    çizgiydi -- kendi eğimiyle bugüne kadar projekte edilince (`renderer.
    py`nin AYNI 3x kuralı OLMADAN) fiyat 560 TL gibi ekran dışı bir değere
    savruluyordu, THYAO 1D'de GERÇEKTEN gözlemlendi (çizgi "seçiliyor" ama
    hiç GÖRÜNMÜYORDU). Yalnızca projeksiyonu bugüne ULAŞABİLEN (3x bacak
    süresi içinde) çizgiler aday sayılır."""
    candidates = []
    for ln in result.lines:
        if ln.style != style or ln.label.startswith("Kırılım"):
            continue
        (t1, _), (t2, _) = ln.points
        b1, b2 = bar_index(df, t1), bar_index(df, t2)
        reach = b2 + _PROJECTION_CAP * max(1, b2 - b1)
        if reach >= last_bar_idx:
            candidates.append(ln)
    if not candidates:
        return None

    def touches(ln) -> int:
        m = _TOUCHES_RE.search(ln.label)
        return int(m.group(1)) if m else 0

    return max(candidates, key=touches)


def _active_box(result: IndicatorResult, style: str, window: pd.DataFrame):
    """`_zones()`nin kendi sözleşmesi: `t1` KIRILMAMIŞ bir bölge için
    df'in SON barına eşittir (bkz. price_structure.py::_zones) -- bu
    yüzden `t1 >= pencerenin son barı` "hâlâ aktif" ile EŞDEĞERDİR. İlk
    denemede bu kontrol YOKTU, kırılmış (aynı bar içinde bile) bir bölge
    "Destek Bölgesi" olarak çizilebiliyordu (THYAO 1D'de GERÇEKTEN
    gözlemlendi: 8 bölgenin TAMAMI aynı barda kırılmıştı, t0==t1)."""
    last_bar = window.index[-1]
    candidates = [bx for bx in result.boxes if bx.style == style and bx.t1 >= last_bar]
    if not candidates:
        return None
    return max(candidates, key=lambda bx: bx.t0)


def _pick_x_ticks(window: pd.DataFrame, n: int = 5) -> list[tuple[float, str]]:
    """4H'te 150 bar ~3 ay tutuyor -- 5 eşit-aralıklı pozisyon aynı aya iki
    kez düşebiliyordu ("Tem '26" iki kez, GERÇEKTEN gözlemlendi). Ardışık
    AYNI etiket metnini üreten pozisyon atlanır (non-repaint'i etkilemez,
    yalnızca hangi etiketlerin gösterileceğini seçer)."""
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
) -> tuple[str, tuple[float, float]]:
    i_max = len(window) - 1
    win_start = window.index[0]
    window_offset = len(df) - len(window)

    last_bar_idx = bar_index(df, window.index[-1])
    resistance = _most_touched_line(result, "resistance", df, last_bar_idx)
    support_zone = _active_box(result, "support_zone", window)
    poc = next((lv for lv in result.levels if lv.label == "POC"), None)
    vah = next((lv for lv in result.levels if lv.label == "VAH"), None)
    val = next((lv for lv in result.levels if lv.label == "VAL"), None)

    key_prices = [float(window["low"].min()), float(window["high"].max())]
    if resistance is not None:
        key_prices += [resistance.points[0][1], resistance.points[1][1]]
    if support_zone is not None:
        key_prices += [support_zone.low, support_zone.high]
    for lv in (poc, vah, val):
        if lv is not None:
            key_prices.append(lv.price)
    lo, hi = pad_range(min(key_prices), max(key_prices), 0.07)

    chart = Chart(
        w=_MAIN_W, h=_MAIN_H, margin_l=48, margin_r=16, margin_t=18, margin_b=26,
        i_domain=(0, i_max), p_domain=(lo, hi),
    )

    def pos(t: pd.Timestamp) -> int:
        return bar_index(window, t)

    def full_pos(t: pd.Timestamp) -> float:
        """`window`da bulunmayan (penceresen ÖNCEKİ) zaman damgaları için
        de çalışır -- trend çizgisi/bölge başlangıcı sık sık 150-bar'lık
        pencereden ÖNCE oluşur, `extend_right`/hâlâ-aktif yüzünden yine de
        çizilmesi gerekir (bkz. yukarıdaki `_most_touched_line`/
        `_active_box` docstring'leri)."""
        return bar_index(df, t) - window_offset

    s = price_labels(chart, theme, 5)
    s += x_labels(chart, _pick_x_ticks(window), theme)
    s += draw_candles(window, chart, theme)

    if resistance is not None:
        (t1, p1), (t2, p2) = resistance.points
        b1, b2 = bar_index(df, t1), bar_index(df, t2)
        x1, y1 = chart.x(full_pos(t1)), chart.y(p1)
        x2, y2 = chart.x(full_pos(t2)), chart.y(p2)
        s += svg_line(x1, y1, x2, y2, stroke=theme.resistance, width=1.5)
        # Etiket, çizginin GÖRÜNÜR bir noktasına konur -- p1/p2 sık sık
        # pencereden ÖNCE (ekran dışı solda) kalıyor, orada bırakılırsa
        # etiket hiç görünmezdi (THYAO 1D'de GERÇEKTEN gözlemlendi).
        label_x, label_y, label_anchor = max(x2, chart.inner_x0), y2, "start"
        if t2 < window.index[-1]:
            reach_bar = b2 + _PROJECTION_CAP * max(1, b2 - b1)
            x_cap = chart.x(reach_bar - window_offset)
            x_end = min(chart.inner_x1, x_cap)
            slope = (p2 - p1) / (x2 - x1) if x2 != x1 else 0.0
            y_end = y2 + slope * (x_end - x2)
            s += svg_line(
                x2, y2, x_end, y_end,
                stroke=theme.resistance, width=1.3, dash="4,3", opacity=0.65,
            )
            # Etiket her zaman panel içinde kalsın diye: uzatma panelin sağ
            # kenarında kesildiyse ("kapak" devrede) etiket SOLA doğru
            # büyür (anchor=end), aksi hâlde her zamanki gibi SAĞA.
            if x_end >= chart.inner_x1 - 0.5:
                label_x, label_y, label_anchor = x_end - 4, y_end, "end"
            else:
                label_x, label_y = x_end, y_end
        s += svg_text(
            label_x + (0 if label_anchor == "end" else 6), label_y - 6, resistance.label,
            fill=theme.resistance, size=9.5, family=theme.font_body, opacity=0.85,
            anchor=label_anchor,
        )

    if support_zone is not None:
        zx0 = max(chart.x(full_pos(support_zone.t0)), chart.inner_x0)
        zy0, zy1 = chart.y(support_zone.low), chart.y(support_zone.high)
        s += svg_rect(
            zx0, zy1, chart.inner_x1 - zx0, zy0 - zy1,
            fill=theme.support, opacity=0.14 if theme.key == "dark" else 0.11,
        )
        s += svg_line(zx0, zy0, chart.inner_x1, zy0, stroke=theme.support, width=1, opacity=0.55)
        s += svg_line(zx0, zy1, chart.inner_x1, zy1, stroke=theme.support, width=1, opacity=0.55)
        s += svg_text(
            zx0 + 6, zy1 - 6, "Destek Bölgesi",
            fill=theme.support, size=9.5, family=theme.font_body, opacity=0.85,
        )

    for lv, strong in ((vah, False), (poc, True), (val, False)):
        if lv is None:
            continue
        y = chart.y(lv.price)
        s += svg_line(
            chart.inner_x0 + 12, y, chart.inner_x1, y,
            stroke=theme.accent if strong else theme.text_faint,
            width=1.6 if strong else 1, dash=None if strong else "2,3", opacity=0.75,
        )
        s += svg_text(
            chart.inner_x1 - 4, y - 4, lv.label,
            fill=theme.accent if strong else theme.text_muted, size=9.5, family=theme.mono,
            anchor="end", weight=700 if strong else 500,
        )

    swing_markers = [
        m for m in result.markers
        if m.kind == "structure_label" and m.t >= win_start and m.text in _SWING_HINTS
    ][-_MAX_SWING_LABELS:]
    boxes: list[LabelBox] = []
    anchors: dict[str, tuple[float, float]] = {}
    for i, m in enumerate(swing_markers):
        box_id = f"swing_{i}"
        x, y = chart.x(pos(m.t)), chart.y(m.price)
        anchors[box_id] = (x, y)
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

    return s, (lo, hi)


def _side_panel(result: IndicatorResult, price_domain: tuple[float, float], theme: SVGTheme) -> str:
    vp_bins = result.series.get("vp_bins")
    vp_volumes = result.series.get("vp_volumes")
    vp_hvn = result.series.get("vp_hvn")
    vp_gauss = result.series.get("vp_gauss")
    lo, hi = price_domain
    sch = Chart(
        w=_SIDE_W, h=_SIDE_H, margin_l=6, margin_r=46, margin_t=18, margin_b=26,
        i_domain=(0, 1), p_domain=(lo, hi),
    )
    if vp_bins is None or vp_volumes is None or vp_bins.empty:
        return svg_text(
            sch.inner_x0, 12, "Hacim profili yok",
            fill=theme.text_muted, size=9.5, family=theme.font_body, weight=600,
        )

    prices = sorted(float(p) for p in vp_bins.tolist())
    bin_step = (prices[1] - prices[0]) if len(prices) >= 2 else (hi - lo) / 20.0
    bin_h_px = abs(sch.y(prices[0]) - sch.y(prices[0] + bin_step))
    bar_max_w = sch.inner_x1 - sch.inner_x0 - 4
    max_v = float(vp_volumes.max()) if len(vp_volumes) else 0.0

    s = ""
    if max_v > 0:
        for price in prices:
            if not (lo <= price <= hi):
                continue
            vol = float(vp_volumes.loc[price])
            is_hvn = vp_hvn is not None and float(vp_hvn.loc[price]) > 0.5
            y = sch.y(price) - bin_h_px / 2
            w = (vol / max_v) * bar_max_w
            s += svg_rect(
                sch.inner_x0, y + bin_h_px * 0.14, w, bin_h_px * 0.72,
                fill=theme.up if is_hvn else theme.accent2,
                opacity=0.85 if is_hvn else 0.35,
                rx=2 if theme.radius > 6 else 0,
            )
        if vp_gauss is not None and not vp_gauss.empty:
            gauss_pts = [
                (sch.inner_x0 + (float(vp_gauss.loc[p]) / max_v) * bar_max_w * 0.98, sch.y(p))
                for p in prices if lo <= p <= hi
            ]
            if len(gauss_pts) >= 2:
                s += svg_poly("polyline", gauss_pts, stroke=theme.accent, width=1.6, opacity=0.9)

    s += svg_text(
        sch.inner_x0, 12, "Hacim Profili",
        fill=theme.text_muted, size=9.5, family=theme.font_body, weight=600,
    )
    return s


def _rsi_panel(result: IndicatorResult, window: pd.DataFrame, theme: SVGTheme) -> str:
    i_max = len(window) - 1
    rsi = result.series.get("rsi_14")
    rch = Chart(
        w=_RSI_W, h=_RSI_H, margin_l=48, margin_r=16, margin_t=12, margin_b=18,
        i_domain=(0, i_max), p_domain=(15, 85),
    )
    s = svg_line(
        rch.inner_x0, rch.y(70), rch.inner_x1, rch.y(70),
        stroke=theme.resistance, width=1, dash="3,3", opacity=0.5,
    )
    s += svg_line(
        rch.inner_x0, rch.y(30), rch.inner_x1, rch.y(30),
        stroke=theme.demand, width=1, dash="3,3", opacity=0.5,
    )
    if rsi is not None:
        rsi_window = rsi.reindex(window.index).dropna()
        pts = [
            (rch.x(bar_index(window, t)), rch.y(max(15.0, min(85.0, float(v)))))
            for t, v in rsi_window.items()
        ]
        if len(pts) >= 2:
            s += svg_poly("polyline", pts, stroke=theme.accent2, width=1.5)
    s += svg_text(
        rch.inner_x0, 11, "RSI (14)",
        fill=theme.text_muted, size=9.5, family=theme.font_body, weight=600,
    )
    return s


def build(result: IndicatorResult, df: pd.DataFrame, theme: SVGTheme) -> SceneOut:
    window = _window(df)
    main_svg, price_domain = _main_panel(result, df, window, theme)
    side_svg = _side_panel(result, price_domain, theme)
    rsi_svg = _rsi_panel(result, window, theme)
    return SceneOut(
        title=f"{result.symbol} — Fiyat Yapısı Raporu",
        subtitle="Yapı · Trend · Hacim Profili · RSI",
        badge=None,
        panels=[
            PanelOut(vb=(_MAIN_W, _MAIN_H), svg=main_svg),
            PanelOut(vb=(_RSI_W, _RSI_H), svg=rsi_svg),
        ],
        side=PanelOut(vb=(_SIDE_W, _SIDE_H), svg=side_svg),
    )
