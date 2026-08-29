"""tlab.features.zones_sd için birim testleri: find_bases, find_impulses,
make_sd_zones (+ hypothesis subset özelliği), update_zones, golden_zone."""

from __future__ import annotations

from zoneinfo import ZoneInfo

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tlab.features.zones_sd import (
    SDZone,
    find_bases,
    find_impulses,
    golden_zone,
    make_sd_zones,
    update_zones,
)
from tlab.testing.fixtures import make_trend

TZ = ZoneInfo("Europe/Istanbul")


def _row(o: float, c: float, h: float, low: float) -> dict:
    return {"open": o, "high": h, "low": low, "close": c, "volume": 1000.0}


def _build_scenario() -> pd.DataFrame:
    """0-4: oynak geçmiş (ATR'yi besler). 5-7: sıkı taban (dar aralık).
    8-10: k=3 patlama (yukarı, net +36). 11: uzak. 12: TEST (bölgeye
    değer). 13: REAKSİYON (bölge üstüne kapanış). 14: uzak. 15: KIRILIM
    (bölge altına kapanış)."""
    rows = [
        _row(100, 100, 104, 96),
        _row(100, 102, 105, 98),
        _row(102, 99, 104, 97),
        _row(99, 101, 103, 97),
        _row(101, 100, 103, 98),
        _row(100, 100, 100.5, 99.5),
        _row(100, 100, 100.5, 99.5),
        _row(100, 100, 100.5, 99.5),
        _row(100, 112, 113, 99),
        _row(112, 124, 125, 111),
        _row(124, 136, 137, 123),
        _row(110, 110, 112, 108),
        _row(100.2, 100.2, 108, 100.0),
        _row(106, 106, 108, 103),
        _row(108, 108, 110, 105),
        _row(95, 95, 106, 94),
    ]
    idx = pd.date_range("2024-01-02 10:00", periods=len(rows), freq="1D", tz=TZ)
    return pd.DataFrame(rows, index=idx)


# --- find_bases / find_impulses (varlık odaklı — çakışan pencereler
# belgelendiği gibi BAĞIMSIZ adaylar ürettiği için tam liste eşitliği DEĞİL,
# beklenen adayın VARLIĞI kontrol edilir) ----------------------------------


def test_find_bases_detects_tight_window_ending_at_base() -> None:
    df = _build_scenario()
    bases = find_bases(df, base_max=5, base_atr=0.6, atr_period=5)
    assert any(b.t0_idx == 5 and b.t1_idx == 7 for b in bases)


def test_find_bases_rejects_wide_trending_series() -> None:
    df = make_trend(n=60, slope=0.5, noise=3.0, seed=1)
    bases = find_bases(df, base_max=5, base_atr=0.05, atr_period=14)
    assert bases == []


def test_find_impulses_detects_strong_directional_move() -> None:
    df = _build_scenario()
    impulses = find_impulses(df, k=3, impulse_atr=2.0, atr_period=5)
    assert any(i.t0_idx == 7 and i.t1_idx == 10 and i.direction == "up" for i in impulses)


def test_find_impulses_rejects_flat_series() -> None:
    df = make_trend(n=40, slope=0.0, noise=0.1, seed=2)
    impulses = find_impulses(df, k=3, impulse_atr=100.0, atr_period=14)
    assert impulses == []


def test_find_impulses_rejects_choppy_alternating_bodies() -> None:
    """Büyük net hareket ama gövdeler tutarlı yönlü DEĞİLSE (choppy) reddedilir."""
    df = _build_scenario()
    # t0=5,t1=8 penceresi: net=112-100=12 (güçlü) ama bar6/7 düz (yukarı
    # gövde SAYILMAZ) -> same_dir_bodies=1 < k-1=2 -> reddedilmeli.
    impulses = find_impulses(df, k=3, impulse_atr=2.0, atr_period=5)
    assert not any(i.t0_idx == 5 and i.t1_idx == 8 for i in impulses)


# --- make_sd_zones ----------------------------------------------------------


def test_make_sd_zones_builds_demand_zone_from_matched_base_and_impulse() -> None:
    df = _build_scenario()
    bases = find_bases(df, base_max=5, base_atr=0.6, atr_period=5)
    impulses = find_impulses(df, k=3, impulse_atr=2.0, atr_period=5)
    zones = make_sd_zones(bases, impulses)

    zone = next(z for z in zones if z.created_idx == 10)
    assert zone.kind == "demand"
    assert zone.low == pytest.approx(99.5)
    assert zone.high == pytest.approx(100.5)
    assert zone.base_bars == 3  # en uzun eşleşen taban (5,7) tercih edilmeli
    assert zone.fresh is True


def test_make_sd_zones_no_match_without_adjacent_base() -> None:
    from tlab.features.zones_sd import Impulse

    lone_impulse = Impulse(t0_idx=100, t1_idx=103, direction="up", strength=5.0)
    assert make_sd_zones([], [lone_impulse]) == []


def test_make_sd_zones_max_zones_prefers_strongest() -> None:
    from tlab.features.zones_sd import Base, Impulse

    bases = [Base(0, 2, 90.0, 91.0), Base(10, 12, 95.0, 96.0)]
    impulses = [
        Impulse(t0_idx=2, t1_idx=5, direction="up", strength=3.0),
        Impulse(t0_idx=12, t1_idx=15, direction="up", strength=10.0),
    ]
    zones = make_sd_zones(bases, impulses, max_zones=1)
    assert len(zones) == 1
    assert zones[0].impulse_strength == pytest.approx(10.0)


@given(
    n=st.integers(min_value=40, max_value=90),
    seed=st.integers(min_value=0, max_value=2000),
)
@settings(max_examples=20, deadline=None)
def test_make_sd_zones_prefix_results_are_subset_of_full(n: int, seed: int) -> None:
    """Kesik df'den bulunan bölgeler, tam df'den bulunanların bir ALT
    KÜMESİDİR — sonradan gelen barlar geçmişte zaten doğmuş bir bölgeyi
    yok etmez/değiştirmez."""
    df = make_trend(n=n, slope=0.05, noise=2.5, seed=seed)
    cut = n // 2
    if cut < 10:
        return

    def _zones_for(frame: pd.DataFrame) -> set[tuple]:
        bases = find_bases(frame, base_max=4, base_atr=1.0, atr_period=10)
        impulses = find_impulses(frame, k=3, impulse_atr=1.0, atr_period=10)
        zones = make_sd_zones(bases, impulses)
        return {(z.kind, z.low, z.high, z.created_idx, z.base_bars) for z in zones}

    full_keys = _zones_for(df)
    partial_keys = _zones_for(df.iloc[:cut])
    assert partial_keys <= full_keys


# --- update_zones ------------------------------------------------------------


def _demand_zone() -> SDZone:
    return SDZone(
        kind="demand", low=99.5, high=100.5, created_idx=10,
        base_bars=3, impulse_strength=4.0, fresh=True,
    )


def test_update_zones_records_test_then_reaction() -> None:
    df = _build_scenario()
    state = update_zones([_demand_zone()], df, t=13)[0]
    assert state.test_idxs == (12,)
    assert state.first_reaction_idx == 13
    assert state.broken_at is None
    assert state.fresh is False


def test_update_zones_records_break_and_stops_tracking() -> None:
    df = _build_scenario()
    state = update_zones([_demand_zone()], df, t=15)[0]
    assert state.broken_at == 15
    assert state.test_idxs == (12,)  # kırılımdan sonra artık iz sürülmez


def test_update_zones_before_created_idx_is_untouched() -> None:
    df = _build_scenario()
    state = update_zones([_demand_zone()], df, t=9)[0]
    assert state.test_idxs == ()
    assert state.fresh is True
    assert state.broken_at is None


def test_update_zones_extend_only_across_t() -> None:
    df = _build_scenario()
    early = update_zones([_demand_zone()], df, t=12)[0]
    late = update_zones([_demand_zone()], df, t=15)[0]
    assert set(early.test_idxs) <= set(late.test_idxs)
    if early.broken_at is not None:
        assert early.broken_at == late.broken_at


# --- golden_zone -------------------------------------------------------------


def test_golden_zone_uptrend_band_below_swing_end() -> None:
    lo, hi = golden_zone(100.0, 200.0, lo=0.618, hi=0.786)
    assert lo == pytest.approx(121.4)
    assert hi == pytest.approx(138.2)
    assert lo < hi < 200.0


def test_golden_zone_downtrend_band_above_swing_end() -> None:
    lo, hi = golden_zone(200.0, 100.0, lo=0.618, hi=0.786)
    assert lo == pytest.approx(161.8)
    assert hi == pytest.approx(178.6)
    assert 100.0 < lo < hi


def test_golden_zone_default_ratios() -> None:
    lo, hi = golden_zone(0.0, 100.0)
    assert lo == pytest.approx(21.4)
    assert hi == pytest.approx(38.2)
