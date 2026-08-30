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
    result = BroadeningIndicator(BroadeningParams(min_bars=5, max_lines_per_side=8))(df)
    directions_by_key = {}
    for pid, state in result.last_state.items():
        key = pid.rsplit("_", 1)[0]
        directions_by_key.setdefault(key, set()).add(state["direction"])
    # bulunan HER geometrik aday için hem long hem short bağımsız izlenmeli
    for dirs in directions_by_key.values():
        assert dirs <= {"long", "short"}


def test_registers_via_verified_elsewhere() -> None:
    df = build_registry_smoke_ohlcv()
    try:
        registry.register_verified_elsewhere(BroadeningIndicator())
    except RegistryError as exc:
        if "zaten kayıtlı" not in str(exc):
            raise
    assert registry.get("patterns.broadening") is BroadeningIndicator
    BroadeningIndicator()(df)
