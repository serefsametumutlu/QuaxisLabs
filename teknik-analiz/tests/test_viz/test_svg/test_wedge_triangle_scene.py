"""`tlab/viz/svg/scenes/wedge_triangle.py` -- Faz 4b'nin ilk sahnesi,
`patterns.wedge` VE `patterns.triangle` için (AYNI modül, `harmonic.*`nin 8
ekolü TEK sahneyi paylaşmasıyla AYNI ilke).

TUCLK (1D, classic) + GARAN (1D, dark, `patterns.triangle`) + YKSLN (1D,
editorial) gerçek veriyle 3 iterasyon geçti (bkz. `docs/design/iterasyon/
iter{1,2,3}_wedge_*`/`iter3_triangle_GARAN_*`). 1. iterasyonda İKİ gerçek
hata bulundu: (1) `_PatternGroup.last_time` formasyonun DOĞUM barına
(`target.start`) düşüyordu ("OLUŞUYOR" durumunda `target.end` de None
olduğu için) -- hedef etiketi/AL rozeti panelin SAĞ kenarına yanlış
konumlanıyordu; doğrusu `double_top_bottom.py`deki gibi pattern_id'nin
GERÇEK en son sinyalinin bar_time'ı. (2) X-ekseni ay etiketleri yılsız
("%b") idi -- TUCLK'ın takozu (CLAUDE.md'nin bilinen "18 ay" notuyla
tutarlı) birden fazla yıla yayılınca "Oca...Ara...Oca" gibi belirsiz
etiketler üretiyordu, `"%b '%y"`ye çevrildi."""

from __future__ import annotations

import pandas as pd
import pytest

from tlab.indicators.patterns.wedge import WedgeIndicator, WedgeParams
from tlab.testing.fixtures import make_trend
from tlab.viz.svg import render_svg, supports
from tlab.viz.svg.scenes.wedge_triangle import _group_patterns, build
from tlab.viz.svg.theme import CLASSIC, DARK, EDITORIAL


def _ohlcv_for_pivots(n: int = 200) -> pd.DataFrame:
    """`tests/test_patterns/test_wedge.py::_pivot`in bar_time'ları
    (`pd.Timestamp("2024-01-01") + Timedelta(days=bar_idx)`, tz-NAIVE) ile
    hizalı, KENDİ df'imiz -- `make_trend()` tz-AWARE (Europe/Istanbul)
    ürettiği için `bar_index(df, pivot.bar_time)` uyuşmazlığı (`KeyError`)
    çıkarırdı; indikatör testi bu uyuşmazlığı hiç FARK ETMEZ (yalnızca
    tuple'ları yapısal karşılaştırır), sahne KODU ise gerçek `bar_index`
    çağrısı yaptığı için (gerçek veride HER ZAMAN geçerli olan bir varsayım)
    burada kendi uyumlu df'imizi kurmak gerekiyor."""
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    values = [100.0 + 0.02 * i for i in range(n)]
    return pd.DataFrame(
        {
            "open": values, "close": values,
            "high": [v + 1.0 for v in values], "low": [v - 1.0 for v in values],
            "volume": 1000.0,
        },
        index=idx,
    )


def _falling_wedge_result(monkeypatch: pytest.MonkeyPatch):
    """`tests/test_patterns/test_wedge.py::test_hologram_polygon_matches_
    boundary_line_corners`nin AYNI monkeypatch deseni -- gürültülü rastgele
    veri bir takoz GARANTİ etmediği için (o dosyanın üst yorumu), gerçek
    `WedgeIndicator.compute()`i sahte ama GEÇERLİ bir (upper, lower) çizgi
    çiftiyle çalıştırıp deterministik, GERÇEK bir IndicatorResult üretir."""
    from tests.test_patterns.test_wedge import _line, _pivot

    up1, up2 = _pivot(0, 130.0, "high"), _pivot(20, 110.0, "high")
    lo1, lo2 = _pivot(5, 100.0, "low"), _pivot(25, 95.0, "low")
    upper = _line(-1.0, 130.0, "resistance", up1, up2)
    lower = _line(-0.25, 101.25, "support", lo1, lo2)

    def _fake_build_trendlines(df, pivots, kind, **kwargs):
        return [upper] if kind == "resistance" else [lower]

    monkeypatch.setattr(
        "tlab.indicators.patterns.wedge.build_trendlines", _fake_build_trendlines,
    )
    df = _ohlcv_for_pivots(200)
    params = WedgeParams(min_pivots=4, min_bars=5, max_apex_bars=200, slope_ratio_range=(0.1, 1.0))
    result = WedgeIndicator("wedge", params).compute(df)
    result.symbol = "TEST"
    return result, df


def test_supports_reports_wedge_and_triangle() -> None:
    assert supports("patterns.wedge") is True
    assert supports("patterns.triangle") is True


def test_group_last_time_is_the_actual_last_signal_not_birth_bar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GERÇEK hata (1. iterasyon, TUCLK): `last_time` `target.start`a
    (doğum barı) düşüyordu. Doğrusu: en son sinyalin bar_time'ı."""
    result, df = _falling_wedge_result(monkeypatch)
    groups = _group_patterns(result)
    assert groups, "en az bir grup üretilmeli"
    for pid, group in groups.items():
        pid_signals = sorted(
            (s for s in result.signals if s.payload.get("pattern_id") == pid),
            key=lambda s: s.bar_time,
        )
        assert group.last_time == pid_signals[-1].bar_time
        assert group.last_time != group.target.start, (
            "last_time doğum barına (target.start) DÜŞMEMELİ"
        )


def test_pick_x_ticks_includes_year() -> None:
    """GERÇEK hata (1. iterasyon, TUCLK): yılsız `"%b"` etiketleri birden
    fazla yıla yayılan bir pencerede belirsizdi."""
    from tlab.viz.svg.scenes.wedge_triangle import _pick_x_ticks

    idx = pd.date_range("2024-01-02", periods=400, freq="D", tz="Europe/Istanbul")
    window = pd.DataFrame({"close": range(400)}, index=idx)
    ticks = _pick_x_ticks(window)
    assert ticks
    assert all("'" in text for _, text in ticks)


@pytest.mark.parametrize("theme", [CLASSIC, DARK, EDITORIAL])
def test_render_svg_produces_well_formed_svg_in_all_three_themes(
    theme, monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, df = _falling_wedge_result(monkeypatch)
    svg_text = render_svg(result, df, theme=theme)
    assert svg_text.startswith("<svg")
    assert svg_text.strip().endswith("</svg>")


def test_triangle_indicator_name_uses_same_scene(monkeypatch: pytest.MonkeyPatch) -> None:
    result, df = _falling_wedge_result(monkeypatch)
    result.indicator = "patterns.triangle"
    svg_text = render_svg(result, df, theme=CLASSIC)
    assert svg_text.startswith("<svg")


def test_build_returns_panels_without_crash(monkeypatch: pytest.MonkeyPatch) -> None:
    result, df = _falling_wedge_result(monkeypatch)
    out = build(result, df, CLASSIC)
    assert out.panels is not None or out.two_up is not None


def test_build_empty_result_shows_placeholder() -> None:
    from tlab.core.types import IndicatorResult, Timeframe

    empty = IndicatorResult(
        indicator="patterns.wedge", version="1", params_hash="x", symbol="TEST",
        timeframe=Timeframe.D1,
    )
    df = make_trend(n=30, slope=0.0, noise=0.5, seed=2)
    out = build(empty, df, CLASSIC)
    assert out.panels is not None and len(out.panels) == 1
    assert out.two_up is None
