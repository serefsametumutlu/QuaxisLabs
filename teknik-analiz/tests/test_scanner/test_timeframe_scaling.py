"""Faz 0.5, A2 — `scanner/engine.py::_scaled_indicator`'ın gerçekten
`BaseParams.for_timeframe`'i uyguladığının regresyon testi. Ağdan bağımsız:
`CATALOG`'daki gerçek `patterns.double_top_bottom` göstergesinin gerçek
(_BAR_FIELDS'li) Params sınıfını kullanır, ama veri çekmez."""

from __future__ import annotations

from tlab.core.types import Timeframe
from tlab.indicators.patterns.double_top_bottom import DoubleTopBottomParams
from tlab.scanner.engine import _scaled_indicator


def test_scaled_indicator_multiplies_bar_field_by_six_for_4h() -> None:
    indicator = _scaled_indicator("patterns.double_top_bottom", Timeframe.H4)
    default_min_bars_between = DoubleTopBottomParams().min_bars_between
    assert indicator.params.min_bars_between == default_min_bars_between * 6


def test_scaled_indicator_leaves_1d_unchanged() -> None:
    indicator = _scaled_indicator("patterns.double_top_bottom", Timeframe.D1)
    default_min_bars_between = DoubleTopBottomParams().min_bars_between
    assert indicator.params.min_bars_between == default_min_bars_between


def test_scaled_indicator_does_not_scale_unrelated_fields() -> None:
    indicator = _scaled_indicator("patterns.double_top_bottom", Timeframe.H4)
    assert indicator.params.eq_tol == DoubleTopBottomParams().eq_tol
    assert indicator.params.atr_period == DoubleTopBottomParams().atr_period
