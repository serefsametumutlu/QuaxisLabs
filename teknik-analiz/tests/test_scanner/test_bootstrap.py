"""tlab.indicators.bootstrap: tüm katalog indikatörleri registry'ye
kaydolabilmeli (regresyon testi — Faz 6'nın kendisini kırdığı bir hataydı:
gerçek/gürültülü veri kullanmak `Registry.register()`'ın varsayılan
repaint_test penceresini "aday havuzu" zamanlama sorunuyla tetikliyordu)."""

from __future__ import annotations

from tlab.core.indicator import registry
from tlab.core.types import Timeframe
from tlab.indicators.bootstrap import CATALOG, populate_registry, scaled_factory
from tlab.indicators.patterns.double_top_bottom import DoubleTopBottomParams
from tlab.indicators.patterns.wedge import WedgeParams


def test_all_catalog_indicators_register_cleanly() -> None:
    populate_registry()
    assert set(CATALOG) <= set(registry.list())


def test_second_call_is_idempotent() -> None:
    populate_registry()
    populate_registry()  # ikinci çağrı hata fırlatmamalı ("zaten kayıtlı" yutulur)
    assert set(CATALOG) <= set(registry.list())


def test_catalog_has_expected_categories() -> None:
    categories = {spec.category for spec in CATALOG.values()}
    assert categories == {"harmonics", "structure", "pair", "trend", "patterns", "momentum"}
    assert sum(1 for s in CATALOG.values() if s.category == "harmonics") == 8
    assert CATALOG["pair.relative_momentum"].needs_context is True
    assert CATALOG["pair.vol_harvest"].needs_context is True
    assert CATALOG["structure.swing_fib_abcd"].needs_context is False


def test_universe_indicators_flagged_needs_universe() -> None:
    assert CATALOG["momentum.alpha_rank"].needs_universe is True
    assert CATALOG["momentum.momentum_rank"].needs_universe is True
    assert CATALOG["trend.ma_systems"].needs_universe is False
    assert CATALOG["trend.ewmac"].needs_universe is False


# --- scaled_factory (Faz 0.5, A2) -------------------------------------------


def test_scaled_factory_scales_bar_fields_for_h4() -> None:
    indicator = scaled_factory("patterns.double_top_bottom", Timeframe.H4)
    assert indicator.params.min_bars_between == DoubleTopBottomParams().min_bars_between * 6


def test_scaled_factory_is_identity_at_d1() -> None:
    indicator = scaled_factory("patterns.wedge", Timeframe.D1)
    assert indicator.params.min_bars == WedgeParams().min_bars
    assert indicator.params.max_apex_bars == WedgeParams().max_apex_bars


def test_scaled_factory_divides_for_w1() -> None:
    indicator = scaled_factory("patterns.wedge", Timeframe.W1)
    assert indicator.params.min_bars == max(1, round(WedgeParams().min_bars / 5))
