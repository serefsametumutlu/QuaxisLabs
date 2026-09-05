"""`tlab/viz/svg/scenes/supply_demand.py` -- Faz 4a'nın beşinci sahnesi.

THYAO (1D, classic/dark) + BAKAB (1D, editorial) gerçek veriyle 3 iterasyon
geçti (bkz. `docs/design/iterasyon/iter{1,2,3}_supply_demand_*`). 1.
iterasyonda ÜÇ gerçek sorun bulundu: (1) bölge fiyatları y-ekseni hesabına
dahil edilince mumlar sıkışıyordu -- swing_fib_abcd'nin AYNI dersi burada
da uygulandı (eksen yalnızca mum aralığından); (2) sağ kenara çok yakın
doğan bir bölgenin etiketi panel dışına taşıp kırpılıyordu -- etiket artık
yetersiz alanda sağa hizalanıyor; (3) hangi bölgeye ait olduğu belirsiz
"yetim" işaretler (zamanca çakışan ama y-ekseni dışına düşmüş eski bir
bölgeye ait) görünüyordu -- artık yalnızca ÇİZİLEN bölgelerin zaman
aralığına düşen işaretler gösteriliyor. THYAO'da AYRICA gerçek bir tasarım
gerginliği fark edildi (bkz. `_nearest_open_zones` docstring'i): tüm açık
bölgeler yerine yalnızca indikatörün KENDİ `nearest_demand`/`nearest_supply`
seçimi çizilir."""

from __future__ import annotations

import pandas as pd
import pytest

from tests.test_structure.test_supply_demand import _build_scenario, _compute
from tlab.core.types import Box, IndicatorResult, Marker, Timeframe
from tlab.testing.fixtures import make_trend
from tlab.viz.svg import render_svg, supports
from tlab.viz.svg.scenes.supply_demand import _nearest_open_zones, build
from tlab.viz.svg.theme import CLASSIC, DARK, EDITORIAL


def _result() -> tuple[IndicatorResult, pd.DataFrame]:
    df = _build_scenario()
    result = _compute(df)
    result.symbol = "TEST"
    return result, df


def test_supports_reports_supply_demand() -> None:
    assert supports("structure.supply_demand") is True


def test_nearest_open_zones_matches_last_state_not_all_open_boxes() -> None:
    """Fixture'da kırılan demand supply'a flip ediyor -- yalnızca o flip
    zone (last_state['nearest_supply']) dönmeli, demand tarafı None."""
    result, _ = _result()
    zones = _nearest_open_zones(result)
    assert len(zones) == 1
    assert zones[0].style == "supply"
    assert zones[0].low == pytest.approx(99.5)
    assert zones[0].high == pytest.approx(100.5)


def test_out_of_range_zone_excluded_from_axis_and_output() -> None:
    """1. iterasyonda GERÇEK bir hata bulundu (THYAO): mevcut fiyattan çok
    uzak bir bölgeyi y-ekseni hesabına katmak mumları ekranın küçük bir üst
    şeridine sıkıştırıyordu. Artık pencerenin doğal aralığının (mum
    low/high) tamamen dışında kalan bir bölge ne eksene ne çıktıya
    yansımalı."""
    df = make_trend(n=60, slope=0.0, noise=0.5, seed=11)
    far_zone = Box(
        t0=df.index[5], t1=df.index[-1], low=1.0, high=2.0,
        label="DEMAND (taze) | 40.0 ATR", style="demand",
    )
    result = IndicatorResult(
        indicator="structure.supply_demand", version="1", params_hash="x", symbol="TEST",
        timeframe=Timeframe.D1,
        boxes=[far_zone],
        last_state={
            "nearest_demand": {"low": 1.0, "high": 2.0, "distance_atr": 40.0, "fresh": True},
            "nearest_supply": None,
        },
    )
    out = build(result, df, CLASSIC)
    svg_text = out.panels[0].svg
    assert "TALEP BÖLGESİ" not in svg_text


def test_orphan_marker_outside_drawn_zones_is_excluded() -> None:
    """1. iterasyonda GERÇEK bir hata: bir bölge y-ekseni dışına düşüp hiç
    çizilmese bile, o bölgeye ait bir REAKSİYON/KIRILDI işareti yine de
    görünüyordu. Artık yalnızca ÇİZİLEN bölgelerin zaman aralığına düşen
    işaretler gösterilir."""
    df = make_trend(n=60, slope=0.0, noise=0.5, seed=11)
    orphan_marker = Marker(
        t=df.index[30], price=float(df["close"].iloc[30]), text="REAKSİYON", kind="sd_reaction",
    )
    result = IndicatorResult(
        indicator="structure.supply_demand", version="1", params_hash="x", symbol="TEST",
        timeframe=Timeframe.D1, boxes=[], markers=[orphan_marker], last_state={},
    )
    out = build(result, df, CLASSIC)
    svg_text = out.panels[0].svg
    assert "REAKSİYON" not in svg_text


@pytest.mark.parametrize("theme", [CLASSIC, DARK, EDITORIAL])
def test_render_svg_produces_well_formed_svg_in_all_three_themes(theme) -> None:
    result, df = _result()
    svg_text = render_svg(result, df, theme=theme)
    assert svg_text.startswith("<svg")
    assert svg_text.strip().endswith("</svg>")


def test_broken_zones_are_never_drawn_even_if_present_in_result() -> None:
    """GERÇEK hata (2026-09-05, ASTOR/CGCAM/INTEM 4H/KCHOL kullanıcı geri
    bildirimi): kırılmış bölgeler (özellikle `flip=True`nin ÜRETTİĞİ, AYNI
    [low,high] ile karşıt türde yeni bir bölgeye dönüşen çiftler) grafiği
    "her yerde alakasız kesikli çizgiler" hâline getiriyordu -- artık
    `result.boxes`'ta kaç tane `*_broken` olursa olsun HİÇBİRİ çizilmez,
    yalnızca `nearest_demand`/`nearest_supply` (en fazla 1+1) çizilir."""
    df = make_trend(n=60, slope=0.0, noise=0.5, seed=11)
    close = float(df["close"].iloc[-1])
    open_demand = Box(
        t0=df.index[5], t1=df.index[-1], low=close - 2.0, high=close - 1.0,
        label="DEMAND (taze)", style="demand",
    )
    # AYNI [low,high] ile bir "kırılmış" supply -- flip mekanizmasının
    # ürettiği türden bir çift (gerçek veride GÖZLEMLENDİ).
    broken_supply = Box(
        t0=df.index[0], t1=df.index[20], low=close - 2.0, high=close - 1.0,
        label="SUPPLY (kırıldı)", style="supply_broken",
    )
    result = IndicatorResult(
        indicator="structure.supply_demand", version="1", params_hash="x", symbol="TEST",
        timeframe=Timeframe.D1,
        boxes=[open_demand, broken_supply],
        last_state={
            "nearest_demand": {
                "low": close - 2.0, "high": close - 1.0, "distance_atr": 0.1, "fresh": True,
            },
            "nearest_supply": None,
        },
    )
    out = build(result, df, CLASSIC)
    svg_text = out.panels[0].svg
    assert "kırıldı" not in svg_text
    assert "SUPPLY" not in svg_text
    assert "DEMAND" in svg_text


def test_build_returns_single_panel_without_side_or_two_up() -> None:
    result, df = _result()
    out = build(result, df, CLASSIC)
    assert out.side is None
    assert out.two_up is None
    assert out.panels is not None and len(out.panels) == 1
