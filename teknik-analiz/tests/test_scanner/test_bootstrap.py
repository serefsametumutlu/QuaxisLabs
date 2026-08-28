"""tlab.indicators.bootstrap: tüm katalog indikatörleri registry'ye
kaydolabilmeli (regresyon testi — Faz 6'nın kendisini kırdığı bir hataydı:
gerçek/gürültülü veri kullanmak `Registry.register()`'ın varsayılan
repaint_test penceresini "aday havuzu" zamanlama sorunuyla tetikliyordu)."""

from __future__ import annotations

from tlab.core.indicator import registry
from tlab.indicators.bootstrap import CATALOG, populate_registry


def test_all_catalog_indicators_register_cleanly() -> None:
    populate_registry()
    assert set(CATALOG) <= set(registry.list())


def test_second_call_is_idempotent() -> None:
    populate_registry()
    populate_registry()  # ikinci çağrı hata fırlatmamalı ("zaten kayıtlı" yutulur)
    assert set(CATALOG) <= set(registry.list())


def test_catalog_has_expected_categories() -> None:
    categories = {spec.category for spec in CATALOG.values()}
    assert categories == {"harmonics", "structure", "pair", "trend"}
    assert sum(1 for s in CATALOG.values() if s.category == "harmonics") == 8
    assert CATALOG["pair.relative_momentum"].needs_context is True
    assert CATALOG["structure.swing_fib_abcd"].needs_context is False
