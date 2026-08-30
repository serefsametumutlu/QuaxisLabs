"""HarmonicIndicator için uçtan uca repaint testi (8 ekol) + durum geçişi
doğrulaması. cut_points, adayın gerçekten doğduğu bardan (born_idx=28)
İTİBAREN seçilir — bkz. scanner_indicator.py'nin modül docstring'indeki
Polygon/Line diffing sınırlaması (trendlines.py/zones.py ile aynı desen)."""

from __future__ import annotations

import pytest

from tests.test_harmonics.fixtures import build_gartley_ohlcv
from tlab.indicators.harmonics.scanner_indicator import HarmonicIndicator, HarmonicParams
from tlab.testing.repaint import repaint_test

_SCHOOLS = [
    "carney", "pesavento", "gilmore", "cypher", "nenstar",
    "navarro200", "five_zero", "three_drives",
]


def test_gartley_state_transitions_on_known_fixture() -> None:
    df = build_gartley_ohlcv()
    params = HarmonicParams(left=2, right=2, confirmation_policy="close_reversal", reversal_bars=1)
    indicator = HarmonicIndicator("carney", params)
    result = indicator(df)

    gartley_signals = [
        s for s in result.signals
        if s.payload.get("pattern_id") == "N_5_10_15_20"
        and s.payload.get("pattern_name") == "gartley"
    ]
    states = [s.state for s in gartley_signals]
    assert states == ["pending", "active", "confirmed"]
    assert gartley_signals[0].payload["prz_low"] == pytest.approx(103.68)
    assert gartley_signals[0].payload["prz_high"] == pytest.approx(104.88)
    assert gartley_signals[-1].detected_at == df.index[30]


def test_xa_fib_ladder_present_for_known_candidate() -> None:
    """2026-08-30: kullanıcı geri bildirimi — harmonik grafiklerde fib
    çizgileri hiç yoktu. `HarmonicIndicator` artık her aday için XA
    bacağının standart geri çekilme basamaklarını (`fibonacci.retracement`'ın
    doğrudan sarmalanması, YENİ bir hesap yöntemi DEĞİL) `Level` olarak
    yayınlıyor — PRZ'nin NEDEN o bantta olduğunu görsel olarak gerekçelendirir."""
    df = build_gartley_ohlcv()
    params = HarmonicParams(left=2, right=2, confirmation_policy="close_reversal", reversal_bars=1)
    indicator = HarmonicIndicator("carney", params)
    result = indicator(df)

    fib_levels = [
        lv for lv in result.levels
        if lv.style == "fib_retracement" and "N_5_10_15_20" in lv.label
    ]
    ratios = {float(lv.label.rsplit("_", 1)[-1]) for lv in fib_levels}
    assert ratios == {0.382, 0.5, 0.618, 0.786}
    # Her seviye adayın doğduğu barda (born_time) başlamalı — PRZ ile AYNI
    # zamanlama sözleşmesi (D henüz oluşmasa bile X,A,B,C'den deterministik).
    assert len({lv.start for lv in fib_levels}) == 1


@pytest.mark.parametrize("school", _SCHOOLS)
def test_harmonic_indicator_passes_repaint(school: str) -> None:
    df = build_gartley_ohlcv()
    params = HarmonicParams(left=2, right=2, confirmation_policy="close_reversal", reversal_bars=1)
    indicator = HarmonicIndicator(school, params)
    report = repaint_test(indicator, df, cut_points=list(range(29, len(df) + 1)))
    assert report.passed, report.mismatches


@pytest.mark.parametrize(
    "policy", ["close_reversal", "xb_break", "pivot", "school"]
)
def test_harmonic_indicator_passes_repaint_for_all_confirmation_policies(policy: str) -> None:
    df = build_gartley_ohlcv()
    params = HarmonicParams(left=2, right=2, confirmation_policy=policy, reversal_bars=1)
    indicator = HarmonicIndicator("carney", params)
    report = repaint_test(indicator, df, cut_points=list(range(29, len(df) + 1)))
    assert report.passed, report.mismatches


def test_signals_alone_are_repaint_safe_across_full_range() -> None:
    """Signal.detected_at doğru bar'ı taşıdığı için, Polygon/Line'daki
    'aday havuzu' sınırlaması olmadan TÜM cut aralığında bile sinyaller
    tutarlı olmalı (bu, sınırlamanın gerçek bir repaint hatası olmadığının
    ayrı bir kanıtı)."""
    df = build_gartley_ohlcv()
    params = HarmonicParams(left=2, right=2, confirmation_policy="close_reversal", reversal_bars=1)
    indicator = HarmonicIndicator("carney", params)

    full = indicator(df)
    for cut in range(20, len(df) + 1):
        partial = indicator(df.iloc[:cut])
        cut_time = df.index[cut - 1]
        full_upto = [s for s in full.signals if s.detected_at <= cut_time]
        assert len(partial.signals) == len(full_upto), f"cut={cut}"
