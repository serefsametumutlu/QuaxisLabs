"""trend.weekly_channel için testler.

`_scan()` (dokunuş/kırılım sayaç mantığı) doğrudan ELLE İNŞA EDİLMİŞ bir
`RegressionChannel` (upper/lower sabit Series) ile test edilir — bu,
`regression_channel`'ın KENDİ OLS hesabından (zaten `test_channels.py`'de
doğrulandı) tamamen BAĞIMSIZ, yalnızca bu indikatörün sayaç/eşik/yön
mantığını izole eder. Regresyon fit'inin gerçek entegrasyonu (frozen/
current çizgiler, `channel_position`) ayrı, gerçekçi sentetik seriyle
test edilir.
"""

from __future__ import annotations

from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from tlab.core.types import IndicatorResult
from tlab.features.channels import RegressionChannel
from tlab.indicators.trend.weekly_channel import ChannelIndicator, ChannelParams, _scan

TZ = ZoneInfo("Europe/Istanbul")


def _df(rows: list[tuple[float, float, float, float]]) -> pd.DataFrame:
    idx = pd.date_range("2024-01-02 10:00", periods=len(rows), freq="1D", tz=TZ)
    return pd.DataFrame(
        [{"open": o, "close": c, "high": h, "low": low} for o, c, h, low in rows],
        index=idx,
    )


def _flat_band(n: int, upper: float = 110.0, lower: float = 90.0) -> RegressionChannel:
    idx = pd.date_range("2024-01-02 10:00", periods=n, freq="1D", tz=TZ)
    return RegressionChannel(
        mid=pd.Series((upper + lower) / 2, index=idx),
        upper=pd.Series(upper, index=idx),
        lower=pd.Series(lower, index=idx),
    )


# --- min_prev_touches gating ------------------------------------------------


def _touch_scenario_df() -> pd.DataFrame:
    rows = [
        (100, 100, 105, 95),  # RSI ısınma
        (100, 100, 105, 95),  # RSI ısınma
        (100, 100, 105, 95),
        (100, 100, 105, 91),  # dokunuş #1
        (100, 100, 105, 95),
        (100, 100, 105, 91),  # dokunuş #2
        (100, 100, 105, 95),
        (100, 100, 105, 91),  # dokunuş #3
        (100, 100, 105, 95),
        (100, 100, 105, 95),
    ]
    return _df(rows)


def test_bottom_touch_suppressed_until_min_prev_touches() -> None:
    df = _touch_scenario_df()
    band = _flat_band(len(df))
    p = ChannelParams(min_prev_touches=2, rsi_max=100.0, touch_tol=0.05, rsi_window=3)
    signals, bottom_touches, _ = _scan(df, band, p, valid_from=0)

    touch_signals = [s for s in signals if s.payload.get("event") == "channel_bottom_touch"]
    assert bottom_touches == 3  # sayaç, sinyal üretilmese bile HER dokunuşta artar
    assert len(touch_signals) == 1
    assert touch_signals[0].payload["touch_no"] == 3
    assert touch_signals[0].bar_time == df.index[7]


def test_bottom_touch_all_fire_when_min_prev_touches_zero() -> None:
    df = _touch_scenario_df()
    band = _flat_band(len(df))
    p = ChannelParams(min_prev_touches=0, rsi_max=100.0, touch_tol=0.05, rsi_window=3)
    signals, _, _ = _scan(df, band, p, valid_from=0)
    touch_signals = [s for s in signals if s.payload.get("event") == "channel_bottom_touch"]
    assert len(touch_signals) == 3
    assert [s.payload["touch_no"] for s in touch_signals] == [1, 2, 3]


# --- rsi_max gating (yalnızca dip dokunuşu) --------------------------------


def test_bottom_touch_gated_by_rsi_max() -> None:
    df = _touch_scenario_df()
    band = _flat_band(len(df))
    permissive_p = ChannelParams(min_prev_touches=0, rsi_max=100.0, rsi_window=3)
    strict_p = ChannelParams(min_prev_touches=0, rsi_max=0.0, rsi_window=3)
    permissive = _scan(df, band, permissive_p, 0)[0]
    strict = _scan(df, band, strict_p, 0)[0]

    assert any(s.payload.get("event") == "channel_bottom_touch" for s in permissive)
    assert not any(s.payload.get("event") == "channel_bottom_touch" for s in strict)


def test_top_touch_not_gated_by_rsi() -> None:
    """rsi_max yalnızca dip dokunuşuna uygulanır (spec: 'kanal dibi' odaklı) —
    tepe dokunuşu RSI'dan bağımsız çalışmalı."""
    rows = [
        (100, 100, 105, 95),
        (100, 100, 109, 95),  # tepe dokunuşu #1
        (100, 100, 105, 95),
    ]
    df = _df(rows)
    band = _flat_band(len(df))
    p = ChannelParams(min_prev_touches=0, rsi_max=0.0, rsi_window=2)
    signals, _, top_touches = _scan(df, band, p, valid_from=0)
    assert top_touches == 1
    assert any(s.payload.get("event") == "channel_top_touch" for s in signals)


# --- kırılım -----------------------------------------------------------


def test_channel_break_up_and_down_directions() -> None:
    rows = [
        (100, 100, 105, 95),
        (100, 115, 116, 110),  # kırılım YUKARI
        (115, 88, 92, 85),  # kırılım AŞAĞI
    ]
    df = _df(rows)
    band = _flat_band(len(df))
    p = ChannelParams(confirm_bars=1, rsi_max=100.0, rsi_window=2)
    signals, _, _ = _scan(df, band, p, valid_from=0)

    up = next(s for s in signals if s.payload.get("event") == "channel_break_up")
    down = next(s for s in signals if s.payload.get("event") == "channel_break_down")
    assert up.direction == "long"
    assert down.direction == "short"
    assert up.bar_time == df.index[1]
    assert down.bar_time == df.index[2]


def test_channel_break_requires_confirm_bars_streak() -> None:
    rows = [
        (100, 100, 105, 95),
        (100, 115, 116, 110),  # 1. kırılım barı (confirm_bars=2 -> henüz onaylanmaz)
        (115, 118, 119, 112),  # 2. ardışık bar -> onaylanır
    ]
    df = _df(rows)
    band = _flat_band(len(df))
    p = ChannelParams(confirm_bars=2, rsi_max=100.0, rsi_window=2)
    signals, _, _ = _scan(df, band, p, valid_from=0)
    breaks = [s for s in signals if s.payload.get("event") == "channel_break_up"]
    assert len(breaks) == 1
    assert breaks[0].bar_time == df.index[2]


# --- gerçekçi seri: frozen/current çizgiler + last_state --------------------


def _trend_with_wobble(n: int = 80, seed: int = 3) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    close = 100 + 0.2 * t + 4.0 * np.sin(2 * np.pi * t / 15) + rng.normal(0, 0.2, n)
    idx = pd.date_range("2024-01-02 10:00", periods=n, freq="1D", tz=TZ)
    open_ = np.roll(close, 1)
    open_[0] = close[0]
    high = np.maximum(open_, close) + 0.3
    low = np.minimum(open_, close) - 0.3
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": 1000.0}, index=idx
    )


def test_frozen_channel_line_immutable_across_truncation() -> None:
    """Geçmiş bir sinyal barındaki dondurulmuş çizgi, df daha da uzasa bile
    DEĞİŞMEMELİ — `frozen_channel_at`'in kendi (zaten test_channels.py'de
    doğrulanmış) "yalnızca geçmişe bakar" özelliğinin bu indikatör
    seviyesindeki entegrasyon kanıtı."""
    df = _trend_with_wobble(n=80)
    params = ChannelParams(n=20, k=1.5, method="regression", rsi_window=5)
    full = ChannelIndicator(params).compute(df)

    frozen_full = {ln.label: ln.points for ln in full.lines if ln.style == "channel_frozen"}
    assert frozen_full  # en az bir dondurulmuş çizgi üretilmiş olmalı

    some_label = next(iter(frozen_full))
    bar_idx = int(some_label.rsplit("_", 1)[-1])

    truncated = df.iloc[: bar_idx + 5]
    partial = ChannelIndicator(params).compute(truncated)
    frozen_partial = {ln.label: ln.points for ln in partial.lines if ln.style == "channel_frozen"}

    if some_label in frozen_partial:
        assert frozen_partial[some_label] == frozen_full[some_label]


def test_current_channel_line_present_and_labeled() -> None:
    df = _trend_with_wobble(n=80)
    result = ChannelIndicator(ChannelParams(n=20, k=1.5, rsi_window=5)).compute(df)
    current_lines = [ln for ln in result.lines if ln.style == "channel_current"]
    assert len(current_lines) == 2  # upper + lower
    assert all(ln.extend_right is False for ln in current_lines)


def test_last_state_fields() -> None:
    df = _trend_with_wobble(n=80)
    result = ChannelIndicator(ChannelParams(n=20, k=1.5, rsi_window=5)).compute(df)
    ls = result.last_state
    assert -50.0 <= ls["position_pct"] <= 150.0  # bant dışına taşabilir, ham konum
    assert isinstance(ls["slope"], float)
    assert set(ls["touches"]) == {"bottom", "top"}
    assert ls["at_bottom"] == (ls["position_pct"] < 15.0)


def test_channel_position_series_in_result() -> None:
    df = _trend_with_wobble(n=80)
    result = ChannelIndicator(ChannelParams(n=20, k=1.5, rsi_window=5)).compute(df)
    assert "channel_position" in result.series
    assert result.series_layout == {"channel_position": ["channel_position"]}


# --- pivot yöntemi (temel bağlantı) ----------------------------------------


def test_pivot_method_runs_and_produces_channel_lines() -> None:
    df = _trend_with_wobble(n=80, seed=5)
    params = ChannelParams(method="pivot", left=2, right=2, rsi_window=5)
    result = ChannelIndicator(params).compute(df)
    assert isinstance(result, IndicatorResult)
    channel_lines = [ln for ln in result.lines if ln.style == "channel"]
    # pivot_channel hiç kanal bulamayabilir (gerçek veri bağımlı) -- yalnızca
    # çökmediğini ve arayüze uyduğunu doğrula.
    assert len(channel_lines) in (0, 2)


def test_indicator_interface_compliance() -> None:
    """ChannelIndicator generic Registry.register() ile KAYDEDİLMEZ (bkz.
    modül docstring'i — 'güncel kanal' çizgisi kasıtlı olarak her barda
    değişir). Arayüz uyumluluğu doğrudan doğrulanır."""
    df = _trend_with_wobble(n=80)
    result = ChannelIndicator()(df)
    assert isinstance(result, IndicatorResult)
    assert result.indicator == "trend.weekly_channel"
