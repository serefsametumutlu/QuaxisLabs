"""patterns.broadening testleri — `diverging_lines` zaten test_patterns_geom.py'de
doğrulandı; burada asıl ilgi BroadeningIndicator'ın onu doğru bağladığı ve
gerçekçi veride çökmeden, geçerli bir sinyal sözleşmesiyle çalıştığıdır."""

from __future__ import annotations

from tests.test_structure.fixtures import build_registry_smoke_ohlcv
from tlab.core.errors import RegistryError
from tlab.core.indicator import registry
from tlab.indicators.patterns.broadening import BroadeningIndicator, BroadeningParams
from tlab.testing.fixtures import make_trend


def test_runs_and_produces_valid_signal_contract() -> None:
    df = make_trend(n=200, slope=0.03, noise=1.5, seed=21)
    result = BroadeningIndicator(BroadeningParams())(df)
    assert result.indicator == "patterns.broadening"
    for sig in result.signals:
        assert sig.payload["pattern_name"] in ("broadening_top", "broadening_bottom")
        assert sig.payload["event"].startswith(sig.payload["pattern_name"])
        assert sig.direction in ("long", "short")


def test_both_directions_tracked_when_pattern_found() -> None:
    df = make_trend(n=250, slope=0.0, noise=2.0, seed=5)
    # Faz 0.5: sistem varsayılanı zigzag_method="atr" bu belirli seed'de
    # broadening'in ihtiyaç duyduğu min_pivots kadar pivot üretmiyor; bu test
    # geometriyi (hologram şekli) hedeflediği için eski "fixed" davranışına
    # sabitlendi.
    params = BroadeningParams(min_bars=5, max_lines_per_side=8, zigzag_method="fixed")
    result = BroadeningIndicator(params)(df)
    directions_by_key = {}
    for pid, state in result.last_state.items():
        key = pid.rsplit("_", 1)[0]
        directions_by_key.setdefault(key, set()).add(state["direction"])
    # bulunan HER geometrik aday için hem long hem short bağımsız izlenmeli
    for dirs in directions_by_key.values():
        assert dirs <= {"long", "short"}


def test_hologram_polygon_matches_boundary_line_corners() -> None:
    """2026-09-01: hologram dolgusu `_upper`/`_lower` sınır çizgileri için
    ZATEN üretilen aynı 4 ankor noktasını çevre sırasıyla birleştirmeli."""
    df = make_trend(n=250, slope=0.0, noise=2.0, seed=5)
    # Faz 0.5: sistem varsayılanı zigzag_method="atr" bu belirli seed'de
    # broadening'in ihtiyaç duyduğu min_pivots kadar pivot üretmiyor; bu test
    # geometriyi (hologram şekli) hedeflediği için eski "fixed" davranışına
    # sabitlendi.
    params = BroadeningParams(min_bars=5, max_lines_per_side=8, zigzag_method="fixed")
    result = BroadeningIndicator(params)(df)
    assert result.polygons, "bu fixture en az bir aday üretmeli (bkz. yorum)"
    for poly in result.polygons:
        assert poly.style == "pattern_hologram"
        key = poly.label.removesuffix("_hologram")
        upper = next(line for line in result.lines if line.label == f"{key}_upper")
        lower = next(line for line in result.lines if line.label == f"{key}_lower")
        assert poly.points == (
            upper.points[0], upper.points[1], lower.points[1], lower.points[0],
        )


def test_max_bars_filters_out_too_long_spans() -> None:
    """Faz 1, 1C sonrası (BULUNAN HATA 3): `test_both_directions_tracked_
    when_pattern_found` ile AYNI fixture/params GERÇEK adaylar üretiyor
    (max_bars=0/varsayılan -- 64 hologram); `max_bars=1` gibi imkânsız
    derecede düşük bir üst sınır HEPSİNİ elemeli."""
    df = make_trend(n=250, slope=0.0, noise=2.0, seed=5)
    params = BroadeningParams(min_bars=5, max_lines_per_side=8, zigzag_method="fixed", max_bars=1)
    result = BroadeningIndicator(params)(df)
    assert result.polygons == []
    assert result.signals == []


def test_max_bars_zero_means_unlimited() -> None:
    df = make_trend(n=250, slope=0.0, noise=2.0, seed=5)
    params = BroadeningParams(min_bars=5, max_lines_per_side=8, zigzag_method="fixed", max_bars=0)
    result = BroadeningIndicator(params)(df)
    assert result.polygons != []


def test_registers_via_verified_elsewhere() -> None:
    df = build_registry_smoke_ohlcv()
    try:
        registry.register_verified_elsewhere(BroadeningIndicator())
    except RegistryError as exc:
        if "zaten kayıtlı" not in str(exc):
            raise
    assert registry.get("patterns.broadening") is BroadeningIndicator
    BroadeningIndicator()(df)
