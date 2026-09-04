"""`tlab/viz/svg/scenes/broadening.py` -- Faz 4b'nin ikinci sahnesi.

BAKAB (1D, classic) + EMNIS (1D, dark) + KRPLS (1D, editorial) gerçek
veriyle 4 iterasyon geçti (bkz. `docs/design/iterasyon/iter{1,2,3,4}_
broadening_*`). 2. iterasyonda (EMNIS) GERÇEK bir hata bulundu:
`BroadeningIndicator`'ın "ölçülü hareket" hedefi (break_line ± height)
NEGATİF çıkabiliyor (fiziksel olarak anlamsız bir fiyat) -- kök neden
`BroadeningIndicator`nin kendisinde (kapsam dışı, `docs/PROGRESS_LOG.md`ye
"BULUNAN HATA" olarak yazıldı, indikatör DÜZELTİLMEDİ), ama sahne tarafı
negatif bir hedefi ne göstermeli ne eksen hesabına katmalı -- aksi hâlde
hem yanıltıcı hem mumları sıkıştırıyordu (swing_fib_abcd'nin AYNI "ekrana
sığmayanı sessizce atla" ilkesi, `wedge_triangle.py`ye de tutarlılık için
uygulandı)."""

from __future__ import annotations

import pytest

from tlab.core.types import IndicatorResult, Level, Line, Marker, Polygon, Signal, Timeframe
from tlab.indicators.patterns.broadening import BroadeningIndicator, BroadeningParams
from tlab.testing.fixtures import make_trend
from tlab.viz.svg import render_svg, supports
from tlab.viz.svg.scenes.broadening import _group_patterns, build
from tlab.viz.svg.theme import CLASSIC, DARK, EDITORIAL


def _result():
    df = make_trend(n=250, slope=0.0, noise=2.0, seed=5)
    params = BroadeningParams(min_bars=5, max_lines_per_side=8, zigzag_method="fixed")
    result = BroadeningIndicator(params)(df)
    result.symbol = "TEST"
    return result, df


def test_supports_reports_broadening() -> None:
    assert supports("patterns.broadening") is True


def test_group_last_time_is_the_actual_last_signal_not_birth_bar() -> None:
    result, _ = _result()
    groups = _group_patterns(result)
    assert groups, "fixture en az bir grup üretmeli (bkz. modül docstring'i)"
    for pid, group in groups.items():
        pid_signals = sorted(
            (s for s in result.signals if s.payload.get("pattern_id") == pid),
            key=lambda s: s.bar_time,
        )
        assert group.last_time == pid_signals[-1].bar_time


def test_negative_target_is_not_shown_or_expanding_axis() -> None:
    """GERÇEK hata (2. iterasyon, EMNIS): `BroadeningIndicator`nin "ölçülü
    hareket" hedefi negatif çıkabiliyordu -- ne "Hedef: ..." metninde ne
    eksen hesabında görünmeli. Gerçek indikatör her zaman negatif bir aday
    üretmediği için (fixture'a bağlı) burada sentetik ama GERÇEKÇİ bir
    `IndicatorResult` kullanılır -- `wedge_fib_abcd` sahnesindeki AYNI
    "senaryoyu doğrudan kur" yaklaşımı."""
    df = make_trend(n=60, slope=0.0, noise=0.5, seed=11)
    t0, t1, tc = df.index[5], df.index[20], df.index[25]
    upper = Line(points=((t0, 110.0), (t1, 130.0)), label="pat_upper", style="pattern_boundary")
    lower = Line(points=((t0, 90.0), (t1, 60.0)), label="pat_lower", style="pattern_boundary")
    hologram = Polygon(
        points=(upper.points[0], upper.points[1], lower.points[1], lower.points[0]),
        label="pat_hologram", style="pattern_hologram",
    )
    target = Level(price=-25.0, label="pat_long_target", style="pattern_target", start=tc)
    sig = Signal(
        bar_time=tc, detected_at=tc, direction="long", state="pending", score=0.5,
        payload={"pattern_id": "pat_long", "event": "broadening_top_pending"},
    )
    result = IndicatorResult(
        indicator="patterns.broadening", version="1", params_hash="x", symbol="TEST",
        timeframe=Timeframe.D1, signals=[sig], levels=[target], lines=[upper, lower],
        polygons=[hologram], markers=[Marker(t=tc, price=100.0, text="x", kind="noop")],
        last_state={
            "pat_long": {"direction": "long", "state": "pending", "event": sig.payload["event"]},
        },
    )
    out = build(result, df, CLASSIC)
    svg_text = "".join(p.svg for p in (out.panels or [])) + "".join(
        tu.svg for tu in (out.two_up or [])
    )
    assert "Hedef: -" not in svg_text


@pytest.mark.parametrize("theme", [CLASSIC, DARK, EDITORIAL])
def test_render_svg_produces_well_formed_svg_in_all_three_themes(theme) -> None:
    result, df = _result()
    svg_text = render_svg(result, df, theme=theme)
    assert svg_text.startswith("<svg")
    assert svg_text.strip().endswith("</svg>")


def test_build_returns_panels_without_crash() -> None:
    result, df = _result()
    out = build(result, df, CLASSIC)
    assert out.panels is not None or out.two_up is not None


def test_build_empty_result_shows_placeholder() -> None:
    from tlab.core.types import IndicatorResult, Timeframe

    empty = IndicatorResult(
        indicator="patterns.broadening", version="1", params_hash="x", symbol="TEST",
        timeframe=Timeframe.D1,
    )
    df = make_trend(n=30, slope=0.0, noise=0.5, seed=2)
    out = build(empty, df, CLASSIC)
    assert out.panels is not None and len(out.panels) == 1
    assert out.two_up is None
