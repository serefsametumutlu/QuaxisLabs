"""`confluence` -> saf SVG sahne (Faz 4a, SON sahne — 6/6 tamamlandı).

Referans: `tlab/viz/renderer.py::render_reversal_map` (Faz 8E'de yazılmış
Plotly karşılığı — vitrin `sceneReversalMap`sinden DEĞİL, doğrudan projenin
KENDİ onaylı Plotly tasarımından port edildi, çünkü `confluence` görev
metninin kendi ürettiği gerçek bir `IndicatorResult` sözleşmesi taşıyor).
Katmanlı bölgeler (opaklık = ağırlık, `result.last_state["zones"]`) +
"DİPTE OLASI: X | N kaynak" marker'ı + kaynak açıklama kutusu + sağda
yoğunluk profili (`vp_bins`/`vp_volumes` — `report.py`nin hacim profili
paneliyle AYNI sözleşme, ama HVN/Gauss YOK, bkz. confluence.py docstring'i).

`confluence` CATALOG göstergesi DEĞİL -- `tlab/viz/live.py::
compute_reversal_map` (bu faz eklendi) çoklu-kaynak `sources` sözlüğünü
canlı kurup `build_reversal_map`'i çağırır.

BİLİNÇLİ tasarım farkı (diğer 5 sahneden): y-ekseni yalnızca mum aralığından
DEĞİL, TÜM bölge fiyatlarından da kurulur -- swing_fib_abcd/golden_zone/
supply_demand'da uzak bir seviyeyi eksene katmak "gürültü" sayılıp
dışlanmıştı, ama BURADA "kapanışın altındaki TÜM potansiyel destek
seviyelerini göster" sahnenin TEK amacı -- uzak bir bölgeyi gizlemek
sahnenin kendi işlevini (yoğunluk haritası) bozardı."""

from __future__ import annotations

import pandas as pd

from tlab.core.types import IndicatorResult
from tlab.viz.svg.axes import price_labels, x_labels
from tlab.viz.svg.candles import draw_candles
from tlab.viz.svg.prim import pill, svg_rect, svg_text
from tlab.viz.svg.scale import Chart, bar_index, pad_range
from tlab.viz.svg.scenes.base import PanelOut, SceneOut
from tlab.viz.svg.theme import SVGTheme

_MAIN_W, _MAIN_H = 700.0, 440.0
_SIDE_W, _SIDE_H = 180.0, 440.0
_LAST_N = 150


def _window(df: pd.DataFrame) -> pd.DataFrame:
    return df.iloc[-_LAST_N:] if len(df) > _LAST_N else df


def _main_panel(
    result: IndicatorResult, df: pd.DataFrame, window: pd.DataFrame, theme: SVGTheme,
) -> tuple[str, tuple[float, float]]:
    i_max = len(window) - 1
    zones = sorted(result.last_state.get("zones") or [], key=lambda z: z["weight_norm"])

    key_prices = [float(window["low"].min()), float(window["high"].max())]
    key_prices += [z["low"] for z in zones] + [z["high"] for z in zones]
    swing_price = result.last_state.get("swing_low_price")
    if swing_price is not None:
        key_prices.append(float(swing_price))
    lo, hi = pad_range(min(key_prices), max(key_prices), 0.08)

    chart = Chart(
        w=_MAIN_W, h=_MAIN_H, margin_l=48, margin_r=14, margin_t=20, margin_b=28,
        i_domain=(0, i_max), p_domain=(lo, hi),
    )

    s = price_labels(chart, theme, 5)
    s += x_labels(chart, _pick_x_ticks(window), theme)
    s += draw_candles(window, chart, theme)

    for zone in zones:
        opacity = 0.06 + 0.40 * float(zone["weight_norm"])
        y0, y1 = chart.y(zone["low"]), chart.y(zone["high"])
        s += svg_rect(
            chart.inner_x0, y1, chart.inner_x1 - chart.inner_x0, y0 - y1,
            fill=theme.demand, opacity=opacity,
        )

    swing_marker = next(
        (m for m in result.markers if m.kind == "reversal_map_swing_low"), None,
    )
    if swing_marker is not None and swing_marker.t in window.index:
        x, y = chart.x(bar_index(window, swing_marker.t)), chart.y(swing_marker.price)
        bw = min(220.0, chart.inner_x1 - chart.inner_x0 - 8)
        bx = min(max(x - bw / 2, chart.inner_x0 + 4), chart.inner_x1 - bw - 4)
        # -44: pill kendi yüksekliği (20) + altındaki kaynak-etiketi kutusuyla
        # (bkz. aşağıdaki "caption") çakışmaması için ekstra pay.
        by = min(y + 14, chart.inner_y1 - 44)
        s += pill(
            bx, by, bw, 20, swing_marker.text,
            fill=theme.demand, text_fill="#ffffff" if theme.key != "neon" else theme.demand,
            family=theme.mono, size=9.5, weight=700,
        )

    # 1. iterasyonda GERÇEK bir hata bulundu: kaynak metni panelin
    # ALTINDAKİ x-ekseni ay etiketleriyle (chart.inner_y1+22) NEREDEYSE AYNI
    # y konumundaydı, ikisi üst üste binip okunamaz oluyordu. Artık panelin
    # İÇİNE, sol-alt köşeye yarı saydam bir arkaplan kutusuyla konur --
    # `render_reversal_map`in (Plotly) `bgcolor=with_alpha(...)` etiket
    # kutusuyla AYNI çözüm.
    sources = result.last_state.get("sources", "")
    caption = f"Dönüş kaynakları: {sources}"
    caption_w = min(chart.inner_x1 - chart.inner_x0 - 8, 8.0 + len(caption) * 4.6)
    s += svg_rect(
        chart.inner_x0 + 2, chart.inner_y1 - 20, caption_w, 16,
        fill=theme.card_bg, opacity=0.85 if theme.key != "neon" else 0.35,
    )
    s += svg_text(
        chart.inner_x0 + 6, chart.inner_y1 - 8, caption,
        fill=theme.text_muted, size=9, family=theme.font_body,
    )

    return s, (lo, hi)


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


def _side_panel(result: IndicatorResult, price_domain: tuple[float, float], theme: SVGTheme) -> str:
    vp_bins = result.series.get("vp_bins")
    vp_volumes = result.series.get("vp_volumes")
    lo, hi = price_domain
    sch = Chart(
        w=_SIDE_W, h=_SIDE_H, margin_l=6, margin_r=10, margin_t=20, margin_b=40,
        i_domain=(0, 1), p_domain=(lo, hi),
    )
    if vp_bins is None or vp_volumes is None or vp_bins.empty:
        return svg_text(
            sch.inner_x0, 12, "Yoğunluk verisi yok",
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
            if vol <= 0:
                continue
            y = sch.y(price) - bin_h_px / 2
            w = (vol / max_v) * bar_max_w
            s += svg_rect(
                sch.inner_x0, y + bin_h_px * 0.14, w, bin_h_px * 0.72,
                fill=theme.demand, opacity=0.35, rx=2 if theme.radius > 6 else 0,
            )
    s += svg_text(
        sch.inner_x0, 12, "Yoğunluk Profili",
        fill=theme.text_muted, size=9.5, family=theme.font_body, weight=600,
    )
    return s


def build(result: IndicatorResult, df: pd.DataFrame, theme: SVGTheme) -> SceneOut:
    window = _window(df)
    main_svg, price_domain = _main_panel(result, df, window, theme)
    side_svg = _side_panel(result, price_domain, theme)
    return SceneOut(
        title=f"{result.symbol} — Dönüş Haritası (Confluence)",
        subtitle="Golden zone + arz-talep + harmonik PRZ + kanal dibi çakışması",
        badge=None,
        panels=[PanelOut(vb=(_MAIN_W, _MAIN_H), svg=main_svg)],
        side=PanelOut(vb=(_SIDE_W, _SIDE_H), svg=side_svg),
    )
