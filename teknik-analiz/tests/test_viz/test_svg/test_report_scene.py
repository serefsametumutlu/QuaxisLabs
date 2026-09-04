"""`tlab/viz/svg/scenes/report.py` -- Faz 4a'nın ikinci sahnesi
(`structure.report`, `structure.price_structure` + `structure.swing_fib_abcd`
birleşimi).

THYAO 1D/4H gerçek verisiyle 5 iterasyon geçti (bkz. `docs/design/
iterasyon/iter{1..5}_report_*`) -- burada iki GERÇEK hatayı kilitleyen
regresyon testleri var: (1) `_most_touched_line` en çok temas edilen ama
KISA/ESKİ bir çizgiyi seçip bugüne projekte edince fiyatı ekran dışına
savuruyordu (renderer.py'nin Faz 7'de bulduğu AYNI "sınırsız eğim" sorunu,
farklı bir kaynaktan); (2) `_active_box` KIRILMIŞ (aynı barda bile) bir
bölgeyi hâlâ "Destek Bölgesi" olarak çiziyordu."""

from __future__ import annotations

import pytest

from tlab.core.types import Box, IndicatorResult, Line, Timeframe
from tlab.indicators.structure.price_structure import PriceStructure, PriceStructureParams
from tlab.indicators.structure.swing_fib_abcd import SwingFibABCD, SwingFibABCDParams
from tlab.testing.fixtures import make_trend
from tlab.viz.svg import render_svg, supports
from tlab.viz.svg.scale import bar_index
from tlab.viz.svg.scenes.report import (
    _active_box,
    _most_touched_line,
    _pick_x_ticks,
    _window,
    build,
)
from tlab.viz.svg.theme import CLASSIC, DARK, EDITORIAL


def _merged_result(df) -> IndicatorResult:
    ps = PriceStructure(PriceStructureParams())(df)
    sf = SwingFibABCD(SwingFibABCDParams())(df)
    merged = IndicatorResult(
        indicator="structure.report", version=ps.version, params_hash=ps.params_hash,
        symbol="TEST", timeframe=ps.timeframe,
        signals=ps.signals + sf.signals, levels=ps.levels + sf.levels,
        lines=ps.lines + sf.lines, boxes=ps.boxes, polygons=[],
        markers=ps.markers + sf.markers, series=ps.series, series_layout=ps.series_layout,
        last_state={**ps.last_state, **sf.last_state},
    )
    return merged


def _trend_df(n: int = 220, seed: int = 7):
    return make_trend(n=n, slope=0.12, noise=1.4, timeframe=Timeframe.D1, seed=seed)


def test_supports_reports_structure_report() -> None:
    assert supports("structure.report") is True


def test_pick_x_ticks_dedupes_consecutive_month_labels() -> None:
    """GERÇEK hata: THYAO 4H'te 5 eşit-aralıklı pozisyon aynı ayı ("Tem
    '26") iki kez üretiyordu."""
    df = _trend_df(n=30, seed=1)
    ticks = _pick_x_ticks(df, n=5)
    texts = [t for _, t in ticks]
    assert len(texts) == len(set(texts)), f"ardışık yinelenen etiket: {texts}"


def test_most_touched_line_rejects_line_whose_projection_cannot_reach_window() -> None:
    """GERÇEK hata (THYAO 1D): en çok temas edilen çizgi 4 barlık kısa bir
    bacaktan geliyordu -- 3x kuralıyla bile bugüne ULAŞAMIYORDU, yine de
    "seçiliyor" ve fiyatı ekran dışına savuran bir projeksiyon çiziyordu.
    Artık böyle bir çizgi HİÇ seçilmemeli."""
    df = _trend_df()
    t1, t2 = df.index[10], df.index[14]  # yalnızca 4 bar -- kısa bacak
    short_line = Line(
        points=((t1, 100.0), (t2, 101.0)), label="Direnç (Temas:9)", style="resistance",
    )
    result = IndicatorResult(
        indicator="structure.report", version="1", params_hash="x", symbol="TEST",
        timeframe=Timeframe.D1, lines=[short_line],
    )
    last_bar_idx = bar_index(df, df.index[-1])
    picked = _most_touched_line(result, "resistance", df, last_bar_idx)
    assert picked is None


def test_most_touched_line_accepts_line_whose_projection_reaches_window() -> None:
    df = _trend_df()
    t1, t2 = df.index[0], df.index[150]  # uzun bacak -- 3x'i son bara ulaşır
    long_line = Line(
        points=((t1, 100.0), (t2, 110.0)), label="Direnç (Temas:3)", style="resistance",
    )
    result = IndicatorResult(
        indicator="structure.report", version="1", params_hash="x", symbol="TEST",
        timeframe=Timeframe.D1, lines=[long_line],
    )
    last_bar_idx = bar_index(df, df.index[-1])
    picked = _most_touched_line(result, "resistance", df, last_bar_idx)
    assert picked is long_line


def test_active_box_excludes_zone_broken_before_window_end() -> None:
    """GERÇEK hata (THYAO 1D): `_zones()`'ün kendi sözleşmesine göre t1,
    kırılmamış bir bölge için df'in SON barına eşittir -- t1 pencerenin son
    barından ÖNCEYSE bölge zaten kırılmış demektir, "Destek Bölgesi" olarak
    çizilmemeli."""
    df = _trend_df()
    window = _window(df)
    broken_box = Box(
        t0=df.index[5], t1=df.index[6], low=95.0, high=97.0, label="x", style="support_zone",
    )
    result = IndicatorResult(
        indicator="structure.report", version="1", params_hash="x", symbol="TEST",
        timeframe=Timeframe.D1, boxes=[broken_box],
    )
    assert _active_box(result, "support_zone", window) is None


def test_active_box_accepts_zone_still_open_at_window_end() -> None:
    df = _trend_df()
    window = _window(df)
    active_box = Box(
        t0=df.index[5], t1=df.index[-1], low=95.0, high=97.0, label="x", style="support_zone",
    )
    result = IndicatorResult(
        indicator="structure.report", version="1", params_hash="x", symbol="TEST",
        timeframe=Timeframe.D1, boxes=[active_box],
    )
    assert _active_box(result, "support_zone", window) is active_box


@pytest.mark.parametrize("theme", [CLASSIC, DARK, EDITORIAL])
def test_render_svg_produces_well_formed_svg_in_all_three_themes(theme) -> None:
    df = _trend_df()
    result = _merged_result(df)
    svg_text = render_svg(result, df, theme=theme)
    assert svg_text.startswith("<svg")
    assert svg_text.strip().endswith("</svg>")
    # ana panel + RSI paneli + yan (hacim profili) paneli = 3 iç <svg>
    assert svg_text.count("<svg") >= 4


def test_build_includes_side_panel() -> None:
    df = _trend_df()
    result = _merged_result(df)
    out = build(result, df, CLASSIC)
    assert out.side is not None
    assert out.panels is not None and len(out.panels) == 2
