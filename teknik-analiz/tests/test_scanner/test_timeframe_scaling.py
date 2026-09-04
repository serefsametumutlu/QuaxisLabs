"""Faz 0.5, A2 — `scanner/engine.py::_scaled_indicator`'ın gerçekten
`BaseParams.for_timeframe`'i uyguladığının regresyon testi. Ağdan bağımsız:
`CATALOG`'daki gerçek `patterns.double_top_bottom` göstergesinin gerçek
(_BAR_FIELDS'li) Params sınıfını kullanır, ama veri çekmez."""

from __future__ import annotations

from tlab.core.types import Timeframe
from tlab.indicators.patterns.double_top_bottom import DoubleTopBottomParams
from tlab.scanner.engine import _scaled_indicator


def test_scaled_indicator_multiplies_bar_field_by_three_for_4h() -> None:
    """Faz 1, 1D düzeltmesi: bkz. `tlab/core/params.py::_TF_BAR_SCALE`."""
    indicator = _scaled_indicator("patterns.double_top_bottom", Timeframe.H4)
    default_prior_trend_lookback = DoubleTopBottomParams().prior_trend_lookback
    assert indicator.params.prior_trend_lookback == default_prior_trend_lookback * 3


def test_scaled_indicator_leaves_min_bars_between_unscaled() -> None:
    """Faz 1, 1D (2026-09-04, docs/spec/FORMASYON_DENETIM_v2.md): `min_bars_
    between` `_BAR_FIELDS`'ten ÇIKARILDI -- ATR-zigzag pivot aralığı bar
    sayısı olarak zaman diliminden bağımsız ölçüldü (medyan 1D=27.5,
    4H=29), takvimsel ölçekleme `patterns.double_top_bottom`'u 4H'te
    SIFIRLIYORDU (125->0, 120 gerçek BIST sembolünde)."""
    indicator = _scaled_indicator("patterns.double_top_bottom", Timeframe.H4)
    assert indicator.params.min_bars_between == DoubleTopBottomParams().min_bars_between


def test_scaled_indicator_leaves_1d_unchanged() -> None:
    indicator = _scaled_indicator("patterns.double_top_bottom", Timeframe.D1)
    default_min_bars_between = DoubleTopBottomParams().min_bars_between
    assert indicator.params.min_bars_between == default_min_bars_between


def test_scaled_indicator_does_not_scale_unrelated_fields() -> None:
    indicator = _scaled_indicator("patterns.double_top_bottom", Timeframe.H4)
    assert indicator.params.eq_tol == DoubleTopBottomParams().eq_tol
    assert indicator.params.atr_period == DoubleTopBottomParams().atr_period
