"""`tlab/viz/svg/scenes/golden_zone.py` -- Faz 4a'nın dördüncü sahnesi.

THYAO (1D, classic/dark) + BAKAB (1D, editorial) gerçek veriyle 5 iterasyon
geçti (bkz. `docs/design/iterasyon/iter{1,2,3,5}_golden_zone_*`) -- 1.
iterasyonda GERÇEK bir hata bulundu: `Marker` kendi `swing_id`sini taşımaz,
yalnızca ZAMAN aralığına göre filtrelemek eski/çakışan bir swing'in
REAKSİYON/BAŞARILI/BAŞARISIZ işaretini de aktif bölgeye karıştırıyordu.
4. iterasyonda (THYAO dark) İKİNCİ bir hata bulundu: "ALTIN BÖLGE" etiketi
ile bölge dışına taşan bir marker etiketi (downtrend'de "BAŞARISIZ" bölgenin
ÜST kenarını kırar) üst üste biniyordu. Aşağıdaki testler ikisini de
kilitler -- gerçek fixture `tests/test_structure/test_golden_zone.py::
_build_touch_reaction_success_scenario`den (swing_id=1: dokunuş+reaksiyon+
başarı; swing_id=2: başarısızlık) alınır, iki swing'in zaman aralıkları
KASITLI OLARAK ÇAKIŞIR (bu yüzden 1. iterasyondaki hatayı gerçekten
yeniden üretir)."""

from __future__ import annotations

import pandas as pd
import pytest

from tests.test_structure.test_golden_zone import (
    _build_touch_reaction_success_scenario,
    _params,
)
from tlab.core.types import IndicatorResult
from tlab.indicators.structure.golden_zone import GoldenZoneIndicator
from tlab.viz.svg import render_svg, supports
from tlab.viz.svg.scenes.golden_zone import _active_box, _half_level, _zone_markers, build
from tlab.viz.svg.theme import CLASSIC, DARK, EDITORIAL


def _result() -> tuple[IndicatorResult, pd.DataFrame]:
    df = _build_touch_reaction_success_scenario()
    result = GoldenZoneIndicator(_params()).compute(df)
    result.symbol = "TEST"
    return result, df


def test_supports_reports_golden_zone() -> None:
    assert supports("structure.golden_zone") is True


def test_active_box_is_the_open_swing_not_the_superseded_one() -> None:
    result, df = _result()
    active = _active_box(result, "golden_zone", df)
    assert active is not None
    assert active.t1 == df.index[-1]
    # fixture'ın 2. (açık) swing'i, ilkinden DAHA GEÇ başlar
    first_box = min((b for b in result.boxes if b.style == "golden_zone"), key=lambda b: b.t0)
    assert active.t0 > first_box.t0


def test_zone_markers_excludes_superseded_swings_reaction_and_success() -> None:
    """GERÇEK hata (1. iterasyon): fixture'ın 1. swing'inin (REAKSİYON+
    BAŞARILI, swing_id=1) zaman aralığı 2. swing'in (BAŞARISIZ, swing_id=2)
    aralığıyla ÇAKIŞIYOR -- yalnızca zamana göre filtrelemek ikisini de
    döndürürdü. Doğru sonuç: yalnızca en büyük swing_id'nin (aktif/2)
    işareti."""
    result, _ = _result()
    markers = _zone_markers(result)
    kinds = {m.kind for m in markers}
    assert kinds == {"golden_zone_fail"}


def test_half_level_matches_active_swing_start() -> None:
    result, df = _result()
    active = _active_box(result, "golden_zone", df)
    half = _half_level(result, active)
    assert half is not None
    assert half.start == active.t0
    assert half.end is None  # hâlâ açık swing


@pytest.mark.parametrize("theme", [CLASSIC, DARK, EDITORIAL])
def test_render_svg_produces_well_formed_svg_in_all_three_themes(theme) -> None:
    result, df = _result()
    svg_text = render_svg(result, df, theme=theme)
    assert svg_text.startswith("<svg")
    assert svg_text.strip().endswith("</svg>")


def test_build_returns_single_panel_without_side_or_two_up() -> None:
    result, df = _result()
    out = build(result, df, CLASSIC)
    assert out.side is None
    assert out.two_up is None
    assert out.panels is not None and len(out.panels) == 1
