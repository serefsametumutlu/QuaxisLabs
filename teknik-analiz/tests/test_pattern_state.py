"""tlab.core.pattern_state için birim testleri — Faz 8B'nin 5 pattern
indikatörünün (wedge/head_shoulders/flag_pennant/double_top_bottom/
broadening) paylaştığı ortak durum makinesi. Sentetik, elle kontrol edilen
close/high/low dizileriyle 5 uç (PENDING'den başlayarak CONFIRMED, RETEST_HOLD,
TARGET_REACHED, INVALIDATED, EXPIRED) ayrı ayrı doğrulanır."""

from __future__ import annotations

import pandas as pd
import pytest

from tlab.core.pattern_state import PatternTrackingConfig, marker_text, track_breakout_pattern

_TZ = "Europe/Istanbul"


def _df(closes: list[float]) -> pd.DataFrame:
    n = len(closes)
    index = pd.date_range("2024-01-02", periods=n, freq="1D", tz=_TZ)
    close = pd.Series(closes)
    high = close + 0.5
    low = close - 0.5
    data = {"high": high.to_numpy(), "low": low.to_numpy(), "close": close.to_numpy()}
    return pd.DataFrame(data, index=index)


def _cfg(**overrides) -> PatternTrackingConfig:
    defaults = dict(
        pattern_id="p1", pattern_name="test_shape", direction="long",
        break_line=lambda t: 100.0, target=105.0, confirm_bars=1,
        max_bars_to_confirm=None, retest_tol_atr=0.3,
        atr_series=pd.Series([1.0] * 20), score=0.5, invalidation_check=None,
    )
    defaults.update(overrides)
    return PatternTrackingConfig(**defaults)


def test_born_bar_always_emits_pending_first() -> None:
    df = _df([95, 96, 97])
    signals = track_breakout_pattern(df, 0, _cfg())
    assert signals[0].state == "pending"
    assert signals[0].bar_time == df.index[0]
    assert signals[0].payload["event"] == "test_shape_pending"


def test_confirm_then_target_reached() -> None:
    df = _df([95, 95, 101, 103, 110])
    signals = track_breakout_pattern(df, 0, _cfg())
    events = [s.payload["event"] for s in signals]
    assert events == ["test_shape_pending", "test_shape_confirmed", "test_shape_target_reached"]
    assert signals[1].bar_time == df.index[2]
    assert signals[1].state == "confirmed"
    assert signals[-1].state == "completed"
    assert signals[-1].bar_time == df.index[4]


def test_confirm_bars_requires_consecutive_closes() -> None:
    """confirm_bars=2: 101 (1. bar) sonrası 99'a (line altına) düşüş serіyi
    bozar -> yalnızca 103,105'in üst üste geldiği barda onaylanır."""
    df = _df([95, 101, 99, 103, 105])
    signals = track_breakout_pattern(df, 0, _cfg(confirm_bars=2))
    confirmed = next(s for s in signals if s.payload["event"] == "test_shape_confirmed")
    assert confirmed.bar_time == df.index[4]


def test_retest_hold_after_confirmation() -> None:
    df = _df([95, 101, 103, 100.2, 108])
    signals = track_breakout_pattern(df, 0, _cfg())
    events = [s.payload["event"] for s in signals]
    assert "test_shape_retest_hold" in events
    retest = next(s for s in signals if s.payload["event"] == "test_shape_retest_hold")
    assert retest.bar_time == df.index[3]
    assert retest.state == "confirmed"


def test_retest_only_fires_once() -> None:
    df = _df([95, 101, 100.1, 103, 100.2, 108])
    signals = track_breakout_pattern(df, 0, _cfg())
    retest_events = [s for s in signals if s.payload["event"] == "test_shape_retest_hold"]
    assert len(retest_events) == 1


def test_invalidation_before_confirmation() -> None:
    df = _df([95, 90, 85])
    signals = track_breakout_pattern(df, 0, _cfg(invalidation_check=lambda t, hi, lo: lo < 88))
    assert signals[-1].state == "invalidated"
    assert signals[-1].payload["event"] == "test_shape_invalidated"
    assert signals[-1].bar_time == df.index[2]


def test_invalidation_only_checked_while_pending() -> None:
    """Onaydan SONRA invalidation_check artık HİÇ çağrılmaz (kırılım kesinleşti)."""
    df = _df([95, 101, 50, 50])  # confirm@1, sonra çöküş -- ama artık invalidated OLMAMALI
    signals = track_breakout_pattern(
        df, 0, _cfg(invalidation_check=lambda t, hi, lo: lo < 88)
    )
    assert all(s.state != "invalidated" for s in signals)


def test_expired_when_no_confirmation_within_window() -> None:
    df = _df([95, 96, 97, 98])
    signals = track_breakout_pattern(df, 0, _cfg(max_bars_to_confirm=1))
    assert signals[-1].state == "expired"
    assert signals[-1].bar_time == df.index[2]  # bars_since_born=2 > 1


def test_pending_when_data_runs_out_before_anything_happens() -> None:
    df = _df([95, 96, 97])
    signals = track_breakout_pattern(df, 0, _cfg())
    assert len(signals) == 1
    assert signals[0].state == "pending"


def test_short_direction_confirms_below_line() -> None:
    df = _df([105, 105, 99, 85])
    cfg = _cfg(direction="short", target=90.0)
    signals = track_breakout_pattern(df, 0, cfg)
    confirmed = next(s for s in signals if s.payload["event"] == "test_shape_confirmed")
    assert confirmed.bar_time == df.index[2]
    completed = next(s for s in signals if s.state == "completed")
    assert completed.bar_time == df.index[3]


def test_extra_payload_is_merged_into_every_event() -> None:
    df = _df([95, 101])
    signals = track_breakout_pattern(df, 0, _cfg(extra_payload={"height": 42.0}))
    assert all(s.payload.get("height") == 42.0 for s in signals)


def test_born_idx_offset_into_longer_series() -> None:
    """born_idx=0 olmak zorunda değil — taranan aralık [born_idx, n) olmalı,
    born_idx'ten ÖNCEKİ barlar hiç dikkate alınmamalı."""
    df = _df([999, 999, 95, 101, 103])  # ilk iki bar tuzak: line'ın çok üstünde
    signals = track_breakout_pattern(df, 2, _cfg())
    assert signals[0].bar_time == df.index[2]
    confirmed = next(s for s in signals if s.payload["event"] == "test_shape_confirmed")
    assert confirmed.bar_time == df.index[3]


# --- marker_text ---------------------------------------------------------


def test_marker_text_translates_known_suffix() -> None:
    text = marker_text("ALÇALAN TAKOZ", "falling_wedge_confirmed", "falling_wedge")
    assert text == "ALÇALAN TAKOZ [ONAY]"


def test_marker_text_falls_back_to_upper_suffix_if_unknown() -> None:
    assert marker_text("X", "x_mystery", "x") == "X [MYSTERY]"


@pytest.mark.parametrize(
    "closes,cfg_kwargs,expected_last_event",
    [
        ([95, 101, 96], {}, "test_shape_confirmed"),
    ],
)
def test_parametrized_smoke(closes, cfg_kwargs, expected_last_event) -> None:
    df = _df(closes)
    signals = track_breakout_pattern(df, 0, _cfg(**cfg_kwargs))
    assert signals[-1].payload["event"] == expected_last_event
