"""`tlab.core.params.BaseParams.for_timeframe` (Faz 0.5, A2) testleri."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from tlab.core.params import BaseParams
from tlab.core.types import Timeframe


@dataclass(frozen=True)
class _DummyParams(BaseParams):
    min_bars: int = 15
    max_bars: int = 90
    unrelated: float = 0.5
    _BAR_FIELDS: ClassVar[frozenset[str]] = frozenset({"min_bars", "max_bars"})


@dataclass(frozen=True)
class _NoBarFieldsParams(BaseParams):
    value: int = 42


def test_for_timeframe_d1_is_identity() -> None:
    p = _DummyParams()
    scaled = p.for_timeframe(Timeframe.D1)
    assert scaled is p  # 1.0 çarpanı -- yeni kopya oluşturulmamalı


def test_for_timeframe_h4_multiplies_by_six() -> None:
    p = _DummyParams(min_bars=15, max_bars=90)
    scaled = p.for_timeframe(Timeframe.H4)
    assert scaled.min_bars == 90
    assert scaled.max_bars == 540
    assert scaled.unrelated == 0.5  # _BAR_FIELDS'te değil -- DEĞİŞMEMELİ


def test_for_timeframe_h1_multiplies_by_24() -> None:
    p = _DummyParams(min_bars=15, max_bars=90)
    scaled = p.for_timeframe(Timeframe.H1)
    assert scaled.min_bars == 360
    assert scaled.max_bars == 2160


def test_for_timeframe_w1_divides_by_five_and_rounds() -> None:
    p = _DummyParams(min_bars=15, max_bars=7)
    scaled = p.for_timeframe(Timeframe.W1)
    assert scaled.min_bars == 3  # round(15/5) = 3
    assert scaled.max_bars == 1  # round(7/5) = round(1.4) = 1


def test_for_timeframe_never_scales_below_one() -> None:
    p = _DummyParams(min_bars=1, max_bars=2)
    scaled = p.for_timeframe(Timeframe.W1)
    assert scaled.min_bars >= 1
    assert scaled.max_bars >= 1


def test_for_timeframe_no_bar_fields_is_identity_for_any_tf() -> None:
    p = _NoBarFieldsParams(value=7)
    for tf in (Timeframe.H1, Timeframe.H4, Timeframe.D1, Timeframe.W1):
        assert p.for_timeframe(tf) is p


def test_for_timeframe_returns_frozen_instance_of_same_type() -> None:
    p = _DummyParams()
    scaled = p.for_timeframe(Timeframe.H4)
    assert isinstance(scaled, _DummyParams)
    assert scaled is not p
