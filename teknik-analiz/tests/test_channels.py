"""tlab.features.channels için birim testleri: regression_channel (mevcut,
Faz 8A'da eklenmişti — burada yalnızca frozen_channel_at ile tutarlılığı test
edilir), frozen_channel_at, pivot_channel (dokunuş/kırılım + prefix-tutarlılık,
trendlines.py testleriyle AYNI desen) ve channel_position.
"""

from __future__ import annotations

from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from tlab.features.channels import (
    channel_position,
    frozen_channel_at,
    pivot_channel,
    pivot_channel_series,
    regression_channel,
)
from tlab.features.swings import Pivot

TZ = ZoneInfo("Europe/Istanbul")


# --- pivot_channel: elle inşa edilmiş senaryo -------------------------------
#
# Alt çizgi p1=(5,100)->p2=(15,110): lower_val(t) = t + 95. Bar 10'da en
# yüksek high (offset=15) -> upper_val(t) = t + 110. created_idx=17 (p2.
# confirmed_idx). t=19'da üst dokunuş, t=23'te alt dokunuş, t=26-27'de
# (confirm_bars=2) yukarı kırılım.


def _lower_val(t: int) -> float:
    return t + 95.0


def _upper_val(t: int) -> float:
    return t + 110.0


def _build_channel_scenario() -> tuple[pd.DataFrame, list[Pivot]]:
    n = 30
    idx = pd.date_range("2024-01-02 10:00", periods=n, freq="1D", tz=TZ)

    close: dict[int, float] = {}
    high: dict[int, float] = {}
    low: dict[int, float] = {}

    for t in range(0, 10):
        close[t] = _lower_val(t)
        high[t] = close[t] + 1.0
        low[t] = close[t] - 1.0
    # bar 10: en yüksek high -> offset=15 (upper_val - lower_val)
    close[10] = _lower_val(10)
    high[10] = close[10] + 15.0
    low[10] = close[10] - 1.0
    for t in range(11, 18):  # created_idx=17 dahil, mid-pozisyon (dokunuş/kırılım yok)
        close[t] = _lower_val(t) + 7.0
        high[t] = close[t] + 1.0
        low[t] = close[t] - 1.0

    for t in (18, 20, 21, 22, 24, 25):  # "uzak" barlar
        close[t] = _lower_val(t) + 7.0
        high[t] = close[t] + 1.0
        low[t] = close[t] - 1.0

    close[19] = _upper_val(19) - 0.5  # üst dokunuş
    high[19] = _upper_val(19) - 0.05
    low[19] = close[19] - 1.0

    close[23] = _lower_val(23) + 0.5  # alt dokunuş
    low[23] = _lower_val(23) - 0.05
    high[23] = close[23] + 1.0

    close[26] = _upper_val(26) + 10.0  # kırılım başlangıcı
    high[26] = close[26] + 1.0
    low[26] = close[26] - 1.0
    close[27] = _upper_val(27) + 10.0  # kırılım onayı (confirm_bars=2)
    high[27] = close[27] + 1.0
    low[27] = close[27] - 1.0
    close[28] = 150.0
    high[28] = 151.0
    low[28] = 149.0
    close[29] = 152.0
    high[29] = 153.0
    low[29] = 151.0

    df = pd.DataFrame(
        {
            "open": [close[t] for t in range(n)],
            "high": [high[t] for t in range(n)],
            "low": [low[t] for t in range(n)],
            "close": [close[t] for t in range(n)],
            "volume": [1000.0] * n,
        },
        index=idx,
    )

    p1 = Pivot(
        bar_idx=5, bar_time=idx[5], price=100.0, kind="low",
        confirmed_idx=7, confirmed_time=idx[7],
    )
    p2 = Pivot(
        bar_idx=15, bar_time=idx[15], price=110.0, kind="low",
        confirmed_idx=17, confirmed_time=idx[17],
    )
    return df, [p1, p2]


def test_pivot_channel_builds_parallel_tangent_upper() -> None:
    df, pivots = _build_channel_scenario()
    channels = pivot_channel(df, pivots, confirm_bars=2)
    assert len(channels) == 1
    ch = channels[0]
    assert ch.slope == pytest.approx(1.0)
    assert ch.lower_intercept == pytest.approx(95.0)
    assert ch.upper_intercept == pytest.approx(110.0)  # offset=15, teğet bar 10
    assert ch.created_idx == 17


def test_pivot_channel_detects_touches_and_break() -> None:
    df, pivots = _build_channel_scenario()
    ch = pivot_channel(df, pivots, confirm_bars=2)[0]
    assert ch.upper_touches == (19,)
    assert ch.lower_touches == (23,)
    assert ch.broken_at == 27
    assert ch.broken_direction == "up"


@pytest.mark.parametrize("cut", [17, 18, 19, 20, 24, 27, 28, 30])
def test_pivot_channel_prefix_consistent(cut: int) -> None:
    df, pivots = _build_channel_scenario()
    full_ch = pivot_channel(df, pivots, confirm_bars=2)[0]

    partial_channels = pivot_channel(df.iloc[:cut], pivots, confirm_bars=2)
    if not partial_channels:
        assert cut <= pivots[1].confirmed_idx
        return
    partial_ch = partial_channels[0]

    assert partial_ch.upper_touches == tuple(t for t in full_ch.upper_touches if t < cut)
    assert partial_ch.lower_touches == tuple(t for t in full_ch.lower_touches if t < cut)
    if full_ch.broken_at is not None and full_ch.broken_at < cut:
        assert partial_ch.broken_at == full_ch.broken_at
    else:
        assert partial_ch.broken_at is None
    # slope/intercept hiçbir kesitte değişmez (p1/p2 zaten sabit veriliyor)
    assert partial_ch.slope == full_ch.slope
    assert partial_ch.upper_intercept == full_ch.upper_intercept


def test_pivot_channel_max_channels_limits_output() -> None:
    df, pivots = _build_channel_scenario()
    # 3. bir low pivot ekleyerek ikinci bir aday (p1,p3) yaratılır
    extra = Pivot(
        bar_idx=20, bar_time=df.index[20], price=_lower_val(20), kind="low",
        confirmed_idx=22, confirmed_time=df.index[22],
    )
    channels = pivot_channel(df, [*pivots, extra], confirm_bars=2, max_channels=1)
    assert len(channels) == 1


# --- channel_position -------------------------------------------------------


def test_channel_position_zero_at_lower_one_at_upper() -> None:
    df, pivots = _build_channel_scenario()
    ch = pivot_channel(df, pivots, confirm_bars=2)[0]
    series_band = pivot_channel_series(df, ch)

    t = 20  # created_idx sonrası, henüz kırılmamış
    probe = df.copy()
    probe.loc[df.index[t], "close"] = series_band.lower.iloc[t]
    pos_lower = channel_position(probe, series_band)
    assert pos_lower.iloc[t] == pytest.approx(0.0)

    probe.loc[df.index[t], "close"] = series_band.upper.iloc[t]
    pos_upper = channel_position(probe, series_band)
    assert pos_upper.iloc[t] == pytest.approx(1.0)


def test_channel_position_nan_before_channel_exists() -> None:
    df, pivots = _build_channel_scenario()
    ch = pivot_channel(df, pivots, confirm_bars=2)[0]
    series_band = pivot_channel_series(df, ch)
    pos = channel_position(df, series_band)
    assert pos.iloc[: ch.created_idx].isna().all()


# --- frozen_channel_at -------------------------------------------------------


def _random_df(n: int, seed: int = 1) -> pd.DataFrame:
    idx = pd.date_range("2024-01-02 10:00", periods=n, freq="1D", tz=TZ)
    rng = np.random.default_rng(seed)
    close = 100.0 + np.cumsum(rng.normal(0, 1.0, size=n))
    wick = np.abs(rng.normal(0, 0.3, size=n)) + 1e-6
    return pd.DataFrame(
        {
            "open": close, "high": close + wick, "low": close - wick,
            "close": close, "volume": 1000.0,
        },
        index=idx,
    )


def test_frozen_channel_at_matches_regression_channel_tail_value() -> None:
    df = _random_df(60, seed=11)
    n, k, t = 20, 2.0, 45
    rc = regression_channel(df, n=n, k=k)
    frozen = frozen_channel_at(df, t=t, n=n, k=k)

    assert frozen.t1 == df.index[t]
    assert frozen.mid[1] == pytest.approx(rc.mid.iloc[t])
    assert frozen.upper[1] == pytest.approx(rc.upper.iloc[t])
    assert frozen.lower[1] == pytest.approx(rc.lower.iloc[t])


def test_frozen_channel_at_t0_is_window_start() -> None:
    df = _random_df(60, seed=12)
    n, t = 15, 40
    frozen = frozen_channel_at(df, t=t, n=n)
    assert frozen.t0 == df.index[t - n + 1]


def test_frozen_channel_at_raises_when_window_unavailable() -> None:
    df = _random_df(10, seed=13)
    with pytest.raises(ValueError):
        frozen_channel_at(df, t=3, n=20)


def test_frozen_channel_at_is_pure_function_of_past_bars() -> None:
    """t barındaki dondurulmuş kanal, t'den SONRAKİ barlar değişse/eklense
    bile aynı kalmalı (yalnızca [t-n+1, t] kullanılır)."""
    df = _random_df(60, seed=14)
    n, t = 20, 45
    frozen_full = frozen_channel_at(df, t=t, n=n)
    frozen_truncated = frozen_channel_at(df.iloc[: t + 1], t=t, n=n)
    assert frozen_full == frozen_truncated
