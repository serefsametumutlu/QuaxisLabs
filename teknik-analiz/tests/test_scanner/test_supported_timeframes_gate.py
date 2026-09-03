"""Faz 0.5, A3 — `engine.run()`'ın `IndicatorMeta.supported_timeframes`
kapısı: desteklenmeyen bir (gösterge, tf) çifti için HİÇ İŞ AÇILMAMALI.
Tamamen çevrimdışı — desteklenmeyen çift zaten hiçbir veri çekimine
ulaşmadığı için `universe=[]` yeterli."""

from __future__ import annotations

from tlab.core.types import Market, Timeframe
from tlab.scanner import engine


def test_d1_only_indicator_skipped_at_h4() -> None:
    scan = engine.run(
        run_id="test_gate", universe=[], timeframes=[Timeframe.H4],
        indicator_names=["momentum.alpha_rank"], market=Market.BIST, workers=1,
    )
    assert scan.results == []
    assert scan.skipped_unsupported == [
        {"indicator": "momentum.alpha_rank", "timeframe": "4H"}
    ]


def test_w1_only_capable_indicator_not_skipped_at_supported_tf() -> None:
    """trend.weekly_channel (W1, D1) destekler -- D1 istenirse ATLANMAMALI
    (gerçek veri gerekmez, universe=[] ile hiç iş üretilmez ama gate'in
    KENDİSİ tetiklenmemeli)."""
    scan = engine.run(
        run_id="test_gate_ok", universe=[], timeframes=[Timeframe.D1],
        indicator_names=["trend.weekly_channel"], market=Market.BIST, workers=1,
    )
    assert scan.skipped_unsupported == []


def test_mixed_timeframes_only_skips_unsupported_one() -> None:
    scan = engine.run(
        run_id="test_gate_mixed", universe=[], timeframes=[Timeframe.D1, Timeframe.H4],
        indicator_names=["momentum.momentum_rank"], market=Market.BIST, workers=1,
    )
    assert scan.skipped_unsupported == [
        {"indicator": "momentum.momentum_rank", "timeframe": "4H"}
    ]
