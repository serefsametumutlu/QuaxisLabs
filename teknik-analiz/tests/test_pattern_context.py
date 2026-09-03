"""`tlab.features.pattern_context` (Faz 1, 1A) — üç paylaşılan bağlam
kontrolünün birim testleri. Sentetik, deterministik veriyle."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tlab.features.pattern_context import (
    breakout_volume_ok,
    pattern_depth_ok,
    prior_trend,
    rolling_trend_tstat,
)


def _trend_df(n: int, slope: float, noise: float = 0.0, seed: int = 1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100.0 + slope * np.arange(n) + rng.normal(0, noise, n)
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.DataFrame(
        {"open": close, "high": close + 0.1, "low": close - 0.1, "close": close,
         "volume": np.full(n, 1000.0)},
        index=idx,
    )


# --- rolling_trend_tstat ---------------------------------------------------


def test_rolling_trend_tstat_detects_rising_slope() -> None:
    # Tamamen doğrusal (sıfır kalıntı varyansı) bir seri se_b=0 -> t=nan
    # üretir (bölme-sıfıra koruması); gerçekçi olsun diye ufak bir gürültü.
    rng = np.random.default_rng(0)
    series = pd.Series(np.arange(30, dtype=float) + rng.normal(0, 0.01, 30))
    slope, tstat = rolling_trend_tstat(series, window=20)
    assert slope.iloc[-1] == pytest.approx(1.0, abs=0.01)
    assert tstat.iloc[-1] > 100  # neredeyse gürültüsüz doğrusal seri -> çok yüksek |t|


def test_rolling_trend_tstat_nan_before_window() -> None:
    series = pd.Series(np.arange(30, dtype=float))
    slope, _ = rolling_trend_tstat(series, window=20)
    assert slope.iloc[:19].isna().all()


# --- prior_trend -------------------------------------------------------


def test_prior_trend_detects_falling_trend_for_long() -> None:
    df = _trend_df(60, slope=-0.5, noise=0.01)
    ok, t = prior_trend(df, start_idx=59, lookback=20, direction="long")
    assert ok
    assert t < 0


def test_prior_trend_detects_rising_trend_for_short() -> None:
    df = _trend_df(60, slope=0.5, noise=0.01)
    ok, t = prior_trend(df, start_idx=59, lookback=20, direction="short")
    assert ok
    assert t > 0


def test_prior_trend_rejects_wrong_direction() -> None:
    df = _trend_df(60, slope=-0.5, noise=0.01)
    ok, _ = prior_trend(df, start_idx=59, lookback=20, direction="short")
    assert not ok


def test_prior_trend_rejects_flat_noisy_series() -> None:
    df = _trend_df(60, slope=0.0, noise=1.5, seed=7)
    ok, _ = prior_trend(df, start_idx=59, lookback=20, direction="long")
    assert not ok


def test_prior_trend_false_when_window_does_not_fit() -> None:
    df = _trend_df(10, slope=-0.5)
    ok, t = prior_trend(df, start_idx=5, lookback=20, direction="long")
    assert not ok
    assert t == 0.0


def test_prior_trend_respects_min_tstat_threshold() -> None:
    df = _trend_df(60, slope=-0.02, noise=2.0, seed=3)
    ok_loose, _ = prior_trend(df, start_idx=59, lookback=20, direction="long", min_tstat=0.01)
    ok_strict, _ = prior_trend(df, start_idx=59, lookback=20, direction="long", min_tstat=50.0)
    assert ok_loose
    assert not ok_strict


# --- pattern_depth_ok -----------------------------------------------------


def test_pattern_depth_ok_true_when_both_thresholds_met() -> None:
    assert pattern_depth_ok(depth=10.0, price=100.0, atr_at_birth=2.0, min_pct=0.03, min_atr=2.0)


def test_pattern_depth_ok_false_when_pct_threshold_fails() -> None:
    assert not pattern_depth_ok(depth=1.0, price=100.0, atr_at_birth=0.1, min_pct=0.03, min_atr=2.0)


def test_pattern_depth_ok_false_when_atr_threshold_fails_even_if_pct_passes() -> None:
    # depth = %5 (pct eşiğini geçer) ama atr_at_birth büyükse (min_atr katı
    # depth'i aşar) İKİSİ BİRDEN gerekli olduğu için yine False dönmeli.
    assert not pattern_depth_ok(
        depth=5.0, price=100.0, atr_at_birth=10.0, min_pct=0.03, min_atr=2.0
    )


def test_pattern_depth_ok_false_for_invalid_price_or_atr() -> None:
    assert not pattern_depth_ok(
        depth=10.0, price=0.0, atr_at_birth=2.0, min_pct=0.03, min_atr=2.0
    )
    assert not pattern_depth_ok(
        depth=10.0, price=100.0, atr_at_birth=0.0, min_pct=0.03, min_atr=2.0
    )
    assert not pattern_depth_ok(
        depth=10.0, price=100.0, atr_at_birth=float("nan"), min_pct=0.03, min_atr=2.0
    )


# --- breakout_volume_ok -----------------------------------------------------


def test_breakout_volume_ok_true_for_high_volume_breakout() -> None:
    volume = np.full(30, 1000.0)
    volume[25] = 3000.0
    assert breakout_volume_ok(volume, idx=25, ma_window=10, k=1.5)


def test_breakout_volume_ok_false_for_average_volume() -> None:
    volume = np.full(30, 1000.0)
    assert not breakout_volume_ok(volume, idx=25, ma_window=10, k=1.5)


def test_breakout_volume_ok_false_before_min_periods() -> None:
    volume = np.full(30, 1000.0)
    volume[2] = 5000.0
    assert not breakout_volume_ok(volume, idx=2, ma_window=10, k=1.5)


def test_breakout_volume_ok_false_for_out_of_range_idx() -> None:
    volume = np.full(10, 1000.0)
    assert not breakout_volume_ok(volume, idx=-1, ma_window=5, k=1.5)
    assert not breakout_volume_ok(volume, idx=100, ma_window=5, k=1.5)
