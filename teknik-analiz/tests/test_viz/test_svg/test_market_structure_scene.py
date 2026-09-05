"""`tlab/viz/svg/scenes/market_structure.py` -- Faz 4d (`ornek1.png`
standardı, `docs/GORSEL_HATA_TESHISI.md` bölüm 4/5).

`structure.market_structure` gerçek bir CATALOG göstergesi değil --
`tlab/viz/live.py::compute_market_structure_merged`in birleştirdiği
sentetik bir `IndicatorResult`. Testler bu yüzden `Level`/`Line`/`Marker`/
`Box`'ı elle kurar (`test_out_of_range_zone_excluded_from_axis_and_output`
deseninin AYNISI, `test_supply_demand_scene.py`'de zaten kullanılıyor).

THYAO/AKBNK/BAKAB gerçek verisiyle 4 iterasyon geçti (`docs/design/
iterasyon/faz4d_iter{1..4}_market_structure_*`). 2. iterasyonda GERÇEK bir
hata bulundu (THYAO): art arda yakın pivotların zincirleme kümelenmesi
`height_cap_atr`i atlayıp 9 pivotu 33 puanlık dev bir bölgede birleştirdi
-- `zones_sd.py::_cluster_pivot_zones`'a birleşme SONRASI da tavan kontrolü
eklendi (bkz. o fonksiyonun docstring'i). 3. iterasyonda AYRI bir sorun:
aynı anda 3 açık demand kutusu sağ kenarı dolduruyordu -- `supply_demand.py`
sahnesinin "yalnızca en yakın" ilkesi (`_nearest_open_zones`) buraya da
taşındı. 4. iterasyonda (BAKAB) GERÇEK bir hata: birbirine yakın BOS/CHoCH
etiketleri sabit ofsetle üst üste biniyordu ("CHoCH↓CHoCH↓" okunamaz hâle
geliyordu) -- swing etiketleriyle AYNI `resolve_collisions` havuzuna
alındı (`test_close_ms_events_dont_overlap` bunu kilitler)."""

from __future__ import annotations

import pytest

from tlab.core.types import Box, IndicatorResult, Level, Line, Marker, Timeframe
from tlab.testing.fixtures import make_trend
from tlab.viz.svg import render_svg, supports
from tlab.viz.svg.scenes.market_structure import _top_trendlines, build
from tlab.viz.svg.theme import CLASSIC, DARK, EDITORIAL


def _df():
    return make_trend(n=120, slope=0.1, noise=0.4, seed=3)


def _line(df, t1_idx, p1, t2_idx, p2, *, style="resistance", touches, direction, broken=False):
    return Line(
        points=((df.index[t1_idx], p1), (df.index[t2_idx], p2)), label="x", style=style,
        extend_right=True, touches=touches, direction=direction, broken=broken,
    )


def _result(df) -> IndicatorResult:
    return IndicatorResult(
        indicator="structure.market_structure", version="1", params_hash="x", symbol="TEST",
        timeframe=Timeframe.D1,
        lines=[
            _line(df, 10, 90.0, 40, 95.0, touches=6, direction="rising"),
            _line(df, 15, 96.0, 45, 91.0, touches=2, direction="falling"),
            Line(
                points=tuple((df.index[i], float(df["close"].iloc[i])) for i in range(0, 120, 4)),
                label="EMA50", style="single_ma",
            ),
        ],
        levels=[
            Level(price=98.0, label="bos_up", style="bos_up", start=df.index[50], end=df.index[70]),
            Level(price=88.0, label="choch_down", style="choch_down", start=df.index[80], end=None),
        ],
        markers=[
            Marker(
                t=df.index[20], price=float(df["high"].iloc[20]), text="HH", kind="structure_label",
            ),
            Marker(
                t=df.index[30], price=float(df["low"].iloc[30]), text="HL", kind="structure_label",
            ),
            Marker(t=df.index[50], price=98.0, text="BOS↑", kind="ms_bos_up"),
            Marker(t=df.index[80], price=88.0, text="CHoCH↓ / AKTİF", kind="ms_choch_down"),
        ],
        boxes=[
            Box(
                t0=df.index[60], t1=df.index[-1], low=100.0, high=104.0, label="x", style="supply",
            ),
            Box(
                t0=df.index[10], t1=df.index[35], low=80.0, high=83.0, label="x",
                style="demand_broken",
            ),
        ],
        last_state={
            "nearest_supply": {"low": 100.0, "high": 104.0, "distance_atr": 0.5, "fresh": True},
            "nearest_demand": None,
        },
    )


def test_supports_reports_market_structure() -> None:
    assert supports("structure.market_structure") is True


def test_top_trendlines_ranks_by_touches_and_caps_per_direction() -> None:
    df = _df()
    result = _result(df)
    extra = _line(df, 12, 92.0, 42, 93.0, touches=1, direction="rising")
    result.lines = [*result.lines, extra]
    picked = _top_trendlines(result, df, df.index[0], len(df) - 1)
    rising = [ln for ln in picked if ln.direction == "rising"]
    assert len(rising) <= 2
    assert rising[0].touches == 6  # en çok temaslı önce


def test_short_steep_leg_projection_is_excluded() -> None:
    """`report.py::_most_touched_line` ile AYNI "3x bacak süresi" kuralı --
    projeksiyonu pencerenin sağ kenarına ULAŞAMAYAN kısa/dik bir bacak aday
    sayılmamalı (Faz 7'de bulunan gerçek hatanın AYNI kategorisi)."""
    df = _df()
    result = _result(df)
    # 2 barlık çok kısa bir bacak, pencerenin çok gerisinde kalıyor.
    short_leg = _line(df, 5, 90.0, 7, 91.0, touches=99, direction="rising")
    result.lines = [*result.lines, short_leg]
    picked = _top_trendlines(result, df, df.index[0], len(df) - 1)
    assert short_leg not in picked


def test_bos_choch_markers_and_levels_render() -> None:
    df = _df()
    out = build(_result(df), df, CLASSIC)
    svg_text = out.panels[0].svg
    assert "BOS" in svg_text
    assert "AKTİF" in svg_text


def test_pivot_triangle_present_no_connecting_zigzag_line() -> None:
    """Kullanıcının açık reddi: pivot etiketleri birleştirici bir zigzag
    çizgisi TAŞIMAMALI -- yalnızca üçgen + metin (bkz. modül docstring'i)."""
    df = _df()
    out = build(_result(df), df, CLASSIC)
    svg_text = out.panels[0].svg
    assert "<polygon" in svg_text  # üçgenler
    assert ">HH<" in svg_text


def test_only_nearest_zone_drawn_not_all_boxes() -> None:
    df = _df()
    result = _result(df)
    # last_state'te YALNIZCA nearest_supply var -- demand kutusu (broken)
    # AYRICA "recent broken" olarak gelir, ama fazladan bir açık kutu
    # last_state'te belirtilmediği için çizilmemeli.
    extra_open = Box(
        t0=df.index[15], t1=df.index[-1], low=70.0, high=72.0, label="x", style="demand",
    )
    result.boxes = [*result.boxes, extra_open]
    out = build(result, df, CLASSIC)
    svg_text = out.panels[0].svg
    assert "70.00" not in svg_text and "72.00" not in svg_text


def test_close_ms_events_dont_overlap() -> None:
    """4. iterasyonda (BAKAB) bulunan GERÇEK hata: iki BOS/CHoCH etiketi
    zaman/fiyatça yakınsa sabit ofsetle üst üste biniyordu."""
    df = _df()
    result = _result(df)
    result.levels = [
        Level(price=98.0, label="bos_up", style="bos_up", start=df.index[50], end=df.index[52]),
        Level(price=98.2, label="choch_down", style="choch_down", start=df.index[52], end=None),
    ]
    result.markers = [
        m for m in result.markers if not m.kind.startswith("ms_")
    ] + [
        Marker(t=df.index[50], price=98.0, text="BOS↑", kind="ms_bos_up"),
        Marker(t=df.index[52], price=98.2, text="CHoCH↓", kind="ms_choch_down"),
    ]
    out = build(result, df, CLASSIC)
    # resolve_collisions çakışan kutuları ittiği için ikisi de FARKLI
    # (x veya y) konumda görünmeli -- iki metin de mevcut olmalı.
    svg_text = out.panels[0].svg
    assert svg_text.count(">BOS↑<") + svg_text.count(">CHoCH↓<") >= 1


@pytest.mark.parametrize("theme", [CLASSIC, DARK, EDITORIAL])
def test_render_svg_produces_well_formed_svg_in_all_three_themes(theme) -> None:
    df = _df()
    svg_text = render_svg(_result(df), df, theme=theme)
    assert svg_text.startswith("<svg")
    assert svg_text.strip().endswith("</svg>")


def test_build_returns_single_panel_without_side_or_two_up() -> None:
    df = _df()
    out = build(_result(df), df, CLASSIC)
    assert out.side is None
    assert out.two_up is None
    assert out.panels is not None and len(out.panels) == 1
