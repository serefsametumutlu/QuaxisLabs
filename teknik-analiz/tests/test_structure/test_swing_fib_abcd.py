"""SwingFibABCD: AB=CD hedef durum makinesi (pending/active/completed/
invalidated), Fibonacci extend-only seti, fib_touch ve repaint testleri."""

from __future__ import annotations

import pytest

from tests.test_structure.fixtures import build_abcd_ohlcv, build_registry_smoke_ohlcv
from tlab.core.errors import RegistryError
from tlab.core.indicator import registry
from tlab.indicators.structure.swing_fib_abcd import SwingFibABCD, SwingFibABCDParams
from tlab.testing.repaint import repaint_test


def _run() -> tuple[list, list]:
    df = build_abcd_ohlcv()
    result = SwingFibABCD(SwingFibABCDParams(left=2, right=2, zigzag_method="fixed"))(df)
    return result.signals, result.levels


def test_first_triple_ratio_1_0_reaches_completed() -> None:
    signals, _ = _run()
    ratio_1_0 = [
        s for s in signals
        if s.payload.get("triple_id") == "abcd_2_11_15" and s.payload.get("ratio") == 1.0
    ]
    states = [s.state for s in ratio_1_0]
    assert states == ["pending", "active", "completed"]
    assert ratio_1_0[-1].payload["event"] == "abcd_target_reached"
    assert ratio_1_0[0].payload["harmonic_unit"] == pytest.approx(30.0, abs=0.5)


def test_first_triple_higher_ratios_invalidated_by_new_triple() -> None:
    signals, _ = _run()
    for ratio_key in (1.272, 1.618):
        chain = [
            s for s in signals
            if s.payload.get("triple_id") == "abcd_2_11_15" and s.payload.get("ratio") == ratio_key
        ]
        assert chain[-1].state == "invalidated"
        assert chain[-1].payload["reason"] == "superseded_by_new_triple"


def test_second_triple_starts_pending_after_first_invalidated() -> None:
    signals, _ = _run()
    second = [s for s in signals if s.payload.get("triple_id") == "abcd_15_25_30"]
    assert len(second) == 3  # yalnızca 3 ratio'nun pending açılışı, fixture bu kadarını kapsıyor
    assert all(s.state == "pending" for s in second)


def test_target_levels_have_d_label_and_bullish_style() -> None:
    _, levels = _run()
    d_levels = [lv for lv in levels if lv.label.startswith("D (hedef)")]
    assert len(d_levels) == 6  # 2 üçlü x 3 oran
    assert all(lv.style == "bullish" for lv in d_levels)  # A=low -> yükseliş yapısı


def _d_level_for(levels: list, signals: list, triple_id: str, ratio: float):
    pending = next(
        s for s in signals
        if s.payload.get("triple_id") == triple_id and s.payload.get("ratio") == ratio
        and s.state == "pending"
    )
    target_price = pending.payload["target_price"]
    return next(
        lv for lv in levels
        if lv.start == pending.bar_time and lv.price == pytest.approx(target_price)
    )


def test_d_target_level_end_closes_on_completion_or_invalidation() -> None:
    """Faz 7'de gerçek veriyle render edilirken bulunan bir hata için
    regresyon: `Level.end` hiç set edilmiyordu (hep None) — bu yüzden
    TAMAMLANMIŞ/GEÇERSİZLEŞMİŞ eski hedefler bile grafiğin sonuna kadar
    uzuyordu. `end`, extend-only ilkesiyle (bkz. ranges.py/zones.py'deki
    Box.t1) çözüm barına SABİTLENMELİ; hâlâ açık bir hedef None kalmalı."""
    signals, levels = _run()

    completed = next(
        s for s in signals
        if s.payload.get("triple_id") == "abcd_2_11_15" and s.payload.get("ratio") == 1.0
        and s.state == "completed"
    )
    lv_completed = _d_level_for(levels, signals, "abcd_2_11_15", 1.0)
    assert lv_completed.end == completed.bar_time

    for ratio_key in (1.272, 1.618):
        invalidated = next(
            s for s in signals
            if s.payload.get("triple_id") == "abcd_2_11_15" and s.payload.get("ratio") == ratio_key
            and s.state == "invalidated"
        )
        lv_invalidated = _d_level_for(levels, signals, "abcd_2_11_15", ratio_key)
        assert lv_invalidated.end == invalidated.bar_time

    # ikinci (son) üçlü fixture bitene kadar hiç çözülmüyor (bkz.
    # test_second_triple_starts_pending_after_first_invalidated) -> açık kalmalı.
    for ratio_key in (1.0, 1.272, 1.618):
        lv_open = _d_level_for(levels, signals, "abcd_15_25_30", ratio_key)
        assert lv_open.end is None


def test_fib_touch_signals_present_and_completed_state() -> None:
    signals, _ = _run()
    touches = [s for s in signals if s.payload.get("event") == "fib_touch"]
    assert len(touches) > 0
    assert all(s.state == "completed" for s in touches)
    assert {t.payload["level"] for t in touches} <= {0.618, 0.786}


def test_swing_fib_abcd_passes_repaint() -> None:
    """cut_points, SON zigzag noktasının finalized_idx'inden (43) İTİBAREN
    seçilir — bkz. scanner_indicator.py'deki (Faz 3) aynı desendeki "aday
    havuzu" notu: bir Level/Line/Signal ancak KENDİ finalized_idx'inden
    itibaren "var" sayılabilir, daha erken bir kesitte henüz görünmemesi
    repaint hatası DEĞİLDİR."""
    df = build_abcd_ohlcv()
    indicator = SwingFibABCD(SwingFibABCDParams(left=2, right=2, zigzag_method="fixed"))
    report = repaint_test(indicator, df, cut_points=list(range(44, len(df) + 1)))
    assert report.passed, report.mismatches


def test_registers_in_registry() -> None:
    """Varsayılan parametrelerle (registry.register() sample_df'i başka
    hiçbir override almadan çalıştırır) temiz bir repaint_test PASS'ı
    gerektiği için, build_abcd_ohlcv yerine kafa+uzun-monoton-kuyruk
    fixture'ı kullanılır (bkz. fixtures.py docstring'i)."""
    df = build_registry_smoke_ohlcv()
    try:
        registry.register(SwingFibABCD(), df)
    except RegistryError as exc:
        if "zaten kayıtlı" not in str(exc):
            raise  # baska test dosyasi (tlab.indicators.bootstrap) zaten kaydetmis olabilir
    assert registry.get("structure.swing_fib_abcd") is SwingFibABCD
