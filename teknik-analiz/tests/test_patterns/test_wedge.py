"""patterns.wedge / patterns.triangle testleri.

`build_trendlines`/`converging_lines`/`classify` zaten kendi test
dosyalarında (tests/test_trendlines.py, tests/test_patterns_geom.py)
kapsamlı doğrulanmış — burada asıl ilgi WedgeIndicator'ın bunları DOĞRU
BAĞLADIĞI (şekil filtreleri, yön seçimi, PatternTrackingConfig kurulumu)
ve gerçekçi/gürültülü veride ÇÖKMEDEN çalıştığıdır. `_passes_shape_filters`/
`_direction_candidates`/`_normalized_ratio` saf fonksiyonlar olduğu için
doğrudan (whitebox) test edilir."""

from __future__ import annotations

import pandas as pd
import pytest

from tests.test_structure.fixtures import build_registry_smoke_ohlcv
from tlab.core.errors import RegistryError
from tlab.core.indicator import registry
from tlab.features.patterns_geom import converging_lines
from tlab.features.swings import Pivot
from tlab.features.trendlines import Trendline
from tlab.indicators.patterns.wedge import (
    WedgeIndicator,
    WedgeParams,
    _direction_candidates,
    _normalized_ratio,
    _passes_shape_filters,
)
from tlab.testing.fixtures import make_trend


def _pivot(bar_idx: int, price: float, kind: str = "high") -> Pivot:
    return Pivot(
        bar_idx=bar_idx, bar_time=pd.Timestamp("2024-01-01") + pd.Timedelta(days=bar_idx),
        price=price, kind=kind, confirmed_idx=bar_idx + 3,
        confirmed_time=pd.Timestamp("2024-01-01") + pd.Timedelta(days=bar_idx + 3),
    )


def _line(slope: float, intercept: float, kind: str, p1: Pivot, p2: Pivot) -> Trendline:
    return Trendline(
        p1=p1, p2=p2, slope=slope, intercept=intercept, kind=kind,
        touches=(), broken_at=None, created_idx=p2.confirmed_idx,
    )


# --- _normalized_ratio ---------------------------------------------------


def test_normalized_ratio_is_symmetric_and_bounded() -> None:
    assert _normalized_ratio(-2.0, -1.0) == pytest.approx(0.5)
    assert _normalized_ratio(-1.0, -2.0) == pytest.approx(0.5)
    assert _normalized_ratio(0.0, 0.0) == 1.0


# --- _passes_shape_filters -------------------------------------------------


def test_passes_shape_filters_rejects_too_few_distinct_pivots() -> None:
    p1 = _pivot(0, 130.0, "high")
    p2 = _pivot(20, 120.0, "high")
    # lower çizgi AYNI pivotları paylaşıyor (gerçekte imkansız ama sınır testi)
    upper = _line(-0.5, 130.0, "resistance", p1, p2)
    lower = _line(-0.2, 100.0, "support", p1, p2)
    conv = converging_lines(upper, lower)
    params = WedgeParams(min_pivots=4)
    assert _passes_shape_filters(conv, upper, lower, params) is False


def test_passes_shape_filters_accepts_valid_falling_wedge_geometry() -> None:
    up1, up2 = _pivot(0, 130.0, "high"), _pivot(20, 110.0, "high")
    lo1, lo2 = _pivot(5, 100.0, "low"), _pivot(25, 95.0, "low")
    upper = _line(-1.0, 130.0, "resistance", up1, up2)  # dik düşüş
    lower = _line(-0.25, 101.25, "support", lo1, lo2)  # ılımlı düşüş
    conv = converging_lines(upper, lower)
    assert conv.is_converging is True
    params = WedgeParams(min_pivots=4, min_bars=5, max_apex_bars=200, slope_ratio_range=(0.1, 1.0))
    assert _passes_shape_filters(conv, upper, lower, params) is True


def test_passes_shape_filters_rejects_apex_too_far() -> None:
    up1, up2 = _pivot(0, 101.0, "high"), _pivot(20, 100.0, "high")
    lo1, lo2 = _pivot(5, 90.0, "low"), _pivot(25, 90.5, "low")
    upper = _line(-0.05, 101.0, "resistance", up1, up2)
    lower = _line(0.02, 89.9, "support", lo1, lo2)
    conv = converging_lines(upper, lower)
    params = WedgeParams(max_apex_bars=10)
    assert _passes_shape_filters(conv, upper, lower, params) is False


def test_passes_shape_filters_rejects_out_of_band_slope_ratio() -> None:
    up1, up2 = _pivot(0, 130.0, "high"), _pivot(20, 110.0, "high")
    lo1, lo2 = _pivot(5, 100.0, "low"), _pivot(25, 95.0, "low")
    upper = _line(-1.0, 130.0, "resistance", up1, up2)
    lower = _line(-0.05, 100.25, "support", lo1, lo2)  # çok daha yatay -> ratio çok küçük
    conv = converging_lines(upper, lower)
    params = WedgeParams(min_pivots=4, min_bars=5, max_apex_bars=200, slope_ratio_range=(0.3, 1.0))
    assert _passes_shape_filters(conv, upper, lower, params) is False


# --- _direction_candidates -------------------------------------------------


def test_direction_candidates_falling_wedge_is_long_only() -> None:
    up, lo = object(), object()
    candidates = _direction_candidates("falling_wedge", up, lo)  # type: ignore[arg-type]
    assert [c[0] for c in candidates] == ["long"]
    assert candidates[0][1] is up and candidates[0][2] is lo


def test_direction_candidates_rising_wedge_is_short_only() -> None:
    up, lo = object(), object()
    candidates = _direction_candidates("rising_wedge", up, lo)  # type: ignore[arg-type]
    assert [c[0] for c in candidates] == ["short"]
    assert candidates[0][1] is lo and candidates[0][2] is up


def test_direction_candidates_sym_triangle_is_bidirectional() -> None:
    up, lo = object(), object()
    candidates = _direction_candidates("sym_triangle", up, lo)  # type: ignore[arg-type]
    assert {c[0] for c in candidates} == {"long", "short"}


# --- entegrasyon: çökmeden çalışma + geçerli payload -----------------------


def _valid_wedge_ohlcv() -> pd.DataFrame:
    """Gerçekçi gürültülü bir trend serisi — kesin bir takoz garanti EDİLMEZ,
    yalnızca indikatörün gerçek/gürültülü veride hatasız çalıştığı ve
    ürettiği HER sinyalin geçerli bir payload sözleşmesi taşıdığı doğrulanır
    (`test_trend/test_breakouts.py::test_smoke_many_break_types_fire...`
    ile AYNI felsefe)."""
    return make_trend(n=200, slope=0.05, noise=1.2, seed=11)


@pytest.mark.parametrize("mode", ["wedge", "triangle"])
def test_indicator_runs_and_produces_valid_signal_contract(mode: str) -> None:
    df = _valid_wedge_ohlcv()
    result = WedgeIndicator(mode, WedgeParams())(df)
    assert result.indicator == f"patterns.{mode}"
    for sig in result.signals:
        assert "event" in sig.payload and "pattern_id" in sig.payload and "target" in sig.payload
        assert sig.state in ("pending", "confirmed", "completed", "invalidated", "expired")
        assert sig.detected_at == sig.bar_time


def test_registers_via_verified_elsewhere() -> None:
    df = build_registry_smoke_ohlcv()
    try:
        registry.register_verified_elsewhere(WedgeIndicator("wedge"))
    except RegistryError as exc:
        if "zaten kayıtlı" not in str(exc):
            raise
    assert registry.get("patterns.wedge") is WedgeIndicator
    # sağlık kontrolü: register_verified_elsewhere repaint_test ÇALIŞTIRMAZ,
    # bu yüzden ayrıca gerçek bir compute() çağrısının çökmediğini doğrula.
    WedgeIndicator("wedge")(df)
