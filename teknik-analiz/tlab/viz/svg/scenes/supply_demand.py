"""`structure.supply_demand` -> saf SVG sahne (Faz 4a, 5/6).

Referans: `docs/design/grafik_stil_vitrini_files/saved_resource.html::
sceneGoldenSupply`nin SAĞ yarısı (satır 701-716, `chR`/`right`) -- taze
talep bölgesi (dolu kutu) + kırılmış arz (kesikli çerçeve) + reaksiyon
işareti.

Mimari not (bkz. `golden_zone.py`nin AYNI docstring paragrafı): artifact'in
`sceneGoldenSupply`si iki farklı sembolü yan yana gösteren bir VİTRİN DEMOSU;
`structure.golden_zone` ile `structure.supply_demand` gerçek katalogda AYRI
iki indikatör ve `live.py`nin BİLİNÇLİ "ayrı kalsın" kararı gereği burada da
AYRI bir sahne dosyası olarak portlandı.

Declutter: `SupplyDemandIndicator.compute()` `max_zones` (varsayılan 12)
kadar bölge üretebilir -- kırılan bir bölge `style`i `{kind}_broken`e döner
ve BİR DAHA "aktif" sayılmaz (bkz. modül docstring'i, "aday havuzu" istisnası).
Yalnızca HÂLÂ KIRILMAMIŞ (`style in ("demand","supply")`) bölgeler dolu
kutu olarak, penceredeki EN FAZLA 2 kırılmış bölge (en yeni `t1`) referans
için soluk/kesikli çerçeve olarak çizilir -- ne tüm 12 bölge (okunamaz
kalabalık) ne SIFIR geçmiş bağlamı (harmonik/report sahnelerinin "yalnızca
en güncel grup" ilkesinden bilinçli bir sapma, çünkü burada birden fazla
EŞ ZAMANLI açık bölge -- ör. bir demand + bir supply -- olması NORMAL ve
BİLGİLENDİRİCİ, tek bir "en güncel" grup kavramı burada uygun değil)."""

from __future__ import annotations

import pandas as pd

from tlab.core.types import Box, IndicatorResult
from tlab.viz.svg.axes import price_labels, right_label, x_labels
from tlab.viz.svg.candles import draw_candles
from tlab.viz.svg.prim import svg_circle, svg_line, svg_rect
from tlab.viz.svg.scale import Chart, bar_index, pad_range
from tlab.viz.svg.scenes.base import PanelOut, SceneOut
from tlab.viz.svg.theme import SVGTheme

_W, _H = 700.0, 440.0
_LAST_N = 150
_MAX_BROKEN_SHOWN = 2
_MARGIN_R = 110.0  # Faz 4d (2026-09-05): eskiden 14 -- etiketler ÇİZİM
# ALANININ İÇİNDE, bölgenin kendi kenarına yapışık duruyordu. `ornek1.png`
# standardı etiketleri sağ kenar BOŞLUĞUNDA ister (`market_structure.py`nin
# AYNI kararı) -- bölge şekli hâlâ tam genişlikte çizilir, yalnızca METİN
# taşındı.

_MARKER_COLOR = {"sd_reaction": "accent", "sd_broken": "text_muted"}


def _window(df: pd.DataFrame) -> pd.DataFrame:
    return df.iloc[-_LAST_N:] if len(df) > _LAST_N else df


def _nearest_open_zones(result: IndicatorResult) -> list[Box]:
    """Tüm açık (kırılmamış) bölgeleri değil, yalnızca `compute()`'un KENDİ
    ATR-normalize "en yakın" seçimini (`last_state["nearest_demand"/
    "nearest_supply"]`) çizer. 2. iterasyonda GERÇEK bir tasarım sorunu
    bulundu: THYAO'nun Ocak'tan beri kırılmamış ama güncel fiyattan 3.1 ATR
    uzaktaki bir talep bölgesi, pencerenin doğal fiyat aralığının çoğunu
    boş bırakarak grafiği anlamsızca geriyordu -- golden_zone/report
    sahnelerinin "yalnızca tek, en güncel/en yakın odak" ilkesiyle AYNI
    çözüm burada da uygulandı (indikatörün KENDİ ATR-mesafe hesabı yeniden
    üretilmedi, olduğu gibi kullanıldı)."""
    zones: list[Box] = []
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


def _recent_broken_zones(result: IndicatorResult, window: pd.DataFrame) -> list[Box]:
    candidates = [
        bx for bx in result.boxes
        if bx.style in ("demand_broken", "supply_broken")
        and bx.t0 <= window.index[-1] and bx.t1 >= window.index[0]
    ]
    return sorted(candidates, key=lambda bx: bx.t1, reverse=True)[:_MAX_BROKEN_SHOWN]


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

    # Y-ekseni SADECE mum aralığından kurulur -- swing_fib_abcd sahnesinde
    # (1. iterasyon) bulunan AYNI ders: bir bölgenin fiyatını eksen hesabına
    # katmak, o bölge mevcut fiyattan çok uzaktaysa (ör. derin, taze bir
    # talep bölgesi) mumları ekranın küçük bir üst şeridine sıkıştırıyordu
    # (1. iterasyonda THYAO'da GERÇEKTEN gözlemlendi). Yalnızca ekranın
    # doğal aralığına düşen (kısmen de olsa çakışan) bölgeler çizilir.
    lo, hi = pad_range(float(window["low"].min()), float(window["high"].max()), 0.08)
    open_zones = [bx for bx in _nearest_open_zones(result) if bx.high >= lo and bx.low <= hi]
    broken_zones = [
        bx for bx in _recent_broken_zones(result, window) if bx.high >= lo and bx.low <= hi
    ]

    chart = Chart(
        w=_W, h=_H, margin_l=48, margin_r=_MARGIN_R, margin_t=20, margin_b=28,
        i_domain=(0, i_max), p_domain=(lo, hi),
    )

    s = price_labels(chart, theme, 4)
    s += x_labels(chart, _pick_x_ticks(window), theme)
    s += draw_candles(window, chart, theme)

    zone_spans: list[tuple[pd.Timestamp, pd.Timestamp]] = []

    for bx in broken_zones:
        color = theme.demand if bx.style == "demand_broken" else theme.supply
        x0 = max(chart.x(full_pos(bx.t0)), chart.inner_x0)
        x1 = chart.x(full_pos(bx.t1))
        y0, y1 = chart.y(bx.low), chart.y(bx.high)
        s += svg_rect(
            x0, y1, max(x1 - x0, 2), y0 - y1,
            fill="none", stroke=color, stroke_width=1, dash="3,2", opacity=0.55,
        )
        mid_y = (y0 + y1) / 2
        kind_tr = "DEMAND / TALEP" if bx.style == "demand_broken" else "SUPPLY / ARZ"
        s += right_label(chart, mid_y - 6, kind_tr, theme, fill=color, size=8.5, weight=700)
        s += right_label(
            chart, mid_y + 6, f"{bx.low:.2f}-{bx.high:.2f} · kırıldı", theme,
            fill=theme.text_muted, size=7.5,
        )
        zone_spans.append((bx.t0, bx.t1))

    for bx in open_zones:
        color = theme.demand if bx.style == "demand" else theme.supply
        x0 = max(chart.x(full_pos(bx.t0)), chart.inner_x0)
        y0, y1 = chart.y(bx.low), chart.y(bx.high)
        s += svg_rect(
            x0, y1, chart.inner_x1 - x0, y0 - y1,
            fill=color, opacity=0.18 if theme.key == "dark" else 0.14,
        )
        s += svg_line(x0, y0, chart.inner_x1, y0, stroke=color, width=1, opacity=0.6)
        s += svg_line(x0, y1, chart.inner_x1, y1, stroke=color, width=1, opacity=0.6)
        # Etiket ÇİZİM ALANININ DIŞINDA, sağ kenar boşluğunda -- `ornek1.
        # png`nin "SUPPLY / ARZ" + fiyat aralığı iki satırlı yerleşimi
        # (`market_structure.py`nin AYNI kararı, bkz. o dosyanın docstring'i).
        kind_tr = "TALEP" if bx.style == "demand" else "ARZ"
        fresh_tr = "TAZE" if "taze" in bx.label else "TEST EDİLDİ"
        mid_y = (y0 + y1) / 2
        s += right_label(
            chart, mid_y - 6, f"{'DEMAND' if bx.style == 'demand' else 'SUPPLY'} / {kind_tr}",
            theme, fill=color, size=9, weight=700,
        )
        s += right_label(
            chart, mid_y + 6, f"{bx.low:.2f} - {bx.high:.2f} · {fresh_tr}", theme,
            fill=theme.text_muted, size=8,
        )
        zone_spans.append((bx.t0, bx.t1))

    # Yalnızca ÇİZİLEN bölgelerin zaman aralığına düşen işaretler gösterilir
    # -- 1. iterasyonda "yetim" işaretler (hangi bölgeye ait olduğu belirsiz,
    # o bölge y-ekseni dışına düşüp hiç çizilmemiş olsa bile işaretin kendisi
    # yine de görünüyordu) GERÇEKTEN gözlemlendi.
    for m in result.markers:
        if m.kind not in _MARKER_COLOR or m.t not in window.index:
            continue
        if not any(t0 <= m.t <= t1 for t0, t1 in zone_spans):
            continue
        x, y = chart.x(bar_index(window, m.t)), chart.y(m.price)
        color = getattr(theme, _MARKER_COLOR[m.kind])
        s += svg_circle(x, y, 4, fill="none", stroke=color, stroke_width=2)

    return SceneOut(
        title=f"{result.symbol} — Arz-Talep Bölgeleri",
        subtitle="Taban + patlama tabanlı arz/talep bölgeleri",
        badge=None,
        panels=[PanelOut(vb=(_W, _H), svg=s)],
    )
