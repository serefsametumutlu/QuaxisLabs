"""`tlab/viz/svg/scenes/swing_fib_abcd.py` -- Faz 4a'nın üçüncü sahnesi.

THYAO (1D, dark/editorial) + BAKAB (1D, editorial) gerçek veriyle 3 iterasyon
geçti (bkz. `docs/design/iterasyon/iter{1..3}_swing_fib_abcd_*`) -- 1.
iterasyonda GERÇEK bir hata bulundu: D-hedef fiyatları (3 farklı oran,
1.0/1.272/1.618) y-ekseni hesabına dahil edilince en agresif oran (1.618)
ekranın "doğal" mum aralığının çok dışına düşüp tüm mumları ekranın küçük
bir üst şeridine sıkıştırıyordu. Düzeltme: D-hedefleri y-ekseni hesabından
çıkarıldı, yalnızca ekranın doğal aralığına düşenler çizilir -- aşağıdaki
`test_out_of_range_target_is_silently_skipped` bunu kilitler."""

from __future__ import annotations

import pandas as pd
import pytest

from tests.test_structure.fixtures import build_abcd_ohlcv
from tlab.core.types import IndicatorResult, Level, Marker, Timeframe
from tlab.indicators.structure.swing_fib_abcd import SwingFibABCD, SwingFibABCDParams
from tlab.viz.svg import render_svg, supports
from tlab.viz.svg.scenes.swing_fib_abcd import _fib_ladder, _latest_targets, _pick_x_ticks, build
from tlab.viz.svg.theme import CLASSIC, DARK, EDITORIAL


def _result() -> tuple[IndicatorResult, pd.DataFrame]:
    df = build_abcd_ohlcv()
    result = SwingFibABCD(SwingFibABCDParams(left=2, right=2, zigzag_method="fixed"))(df)
    result.symbol = "TEST"
    return result, df


def test_supports_reports_swing_fib_abcd() -> None:
    assert supports("structure.swing_fib_abcd") is True


def test_pick_x_ticks_dedupes_consecutive_month_labels() -> None:
    df = build_abcd_ohlcv()
    ticks = _pick_x_ticks(df, n=5)
    texts = [t for _, t in ticks]
    assert len(texts) == len(set(texts)), f"ardışık yinelenen etiket: {texts}"


def test_latest_targets_only_returns_second_triples_group() -> None:
    """Fixture'ın 1. üçlüsü (abcd_2_11_15) idx30'da 2. üçlü (abcd_15_25_30)
    doğunca invalidated oluyor -- yalnızca 2. üçlünün 3 hedefi dönmeli."""
    result, _ = _result()
    targets = _latest_targets(result)
    triple_ids = {lv.label for lv in targets}
    assert len(targets) == 3
    d_all = [lv for lv in result.levels if lv.label.startswith("D (hedef)")]
    assert len(d_all) == 6
    assert triple_ids <= {lv.label for lv in d_all}
    # 2. üçlünün başlangıcı (start) TÜMÜNDE aynı (C barı) olmalı, en büyük
    latest_start = max(lv.start for lv in d_all if lv.start is not None)
    assert all(lv.start == latest_start for lv in targets)


def test_fib_ladder_only_includes_open_ended_levels() -> None:
    result, _ = _result()
    ladder = _fib_ladder(result)
    assert ladder, "en yeni bacağın fib merdiveni boş olmamalı"
    assert all(lv.end is None for lv in ladder)
    all_fib = [
        lv for lv in result.levels if lv.style in ("fib_retracement", "fib_extension")
    ]
    assert len(ladder) < len(all_fib), "eski bacakların fib seti elenmeli"


def test_out_of_range_target_is_silently_skipped() -> None:
    """1. iterasyonda bulunan GERÇEK hata: aşırı uzak bir D hedefi y-ekseni
    hesabına dahil edilirse tüm mumları sıkıştırıyordu. Artık ekranın doğal
    aralığının dışına düşen bir hedef ne eksene ne SVG çıktısına yansımalı."""
    df = build_abcd_ohlcv()
    far_level = Level(
        price=10.0,  # window'un gerçek fiyat aralığının (100-150) çok altında
        label="D (hedef): 10.00", style="bullish", start=df.index[30], end=None,
    )
    near_marker = Marker(t=df.index[30], price=122.0, text="HL", kind="structure_label")
    result = IndicatorResult(
        indicator="structure.swing_fib_abcd", version="1", params_hash="x", symbol="TEST",
        timeframe=Timeframe.D1, levels=[far_level], markers=[near_marker],
    )
    out = build(result, df, CLASSIC)
    svg_text = out.panels[0].svg
    assert "10.00" not in svg_text
    # eksen aşırı genişlememeli: fiyat aralığı hâlâ makul (100-150 civarı)
    assert "500.0" not in svg_text and "-50.0" not in svg_text


@pytest.mark.parametrize("theme", [CLASSIC, DARK, EDITORIAL])
def test_render_svg_produces_well_formed_svg_in_all_three_themes(theme) -> None:
    result, df = _result()
    svg_text = render_svg(result, df, theme=theme)
    assert svg_text.startswith("<svg")
    assert svg_text.strip().endswith("</svg>")


def test_build_returns_single_panel() -> None:
    result, df = _result()
    out = build(result, df, CLASSIC)
    assert out.side is None
    assert out.two_up is None
    assert out.panels is not None and len(out.panels) == 1
