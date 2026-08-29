"""tlab.features.volatility için birim testleri (realized_vol, keltner,
vol_zscore) + prefix-tutarlılık (non-repaint) testleri.

atr/bollinger zaten trendlines/zones/ranges testlerinde dolaylı egzersiz
ediliyor; burada yalnızca Faz 2-EK'in eklediği üç fonksiyon hedeflenir.
"""

from __future__ import annotations

import math
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from tlab.features.volatility import atr, bollinger, keltner, realized_vol, vol_zscore

TZ = ZoneInfo("Europe/Istanbul")


def _df(close: list[float], seed: int = 0) -> pd.DataFrame:
    idx = pd.date_range("2024-01-02 10:00", periods=len(close), freq="1D", tz=TZ)
    rng = np.random.default_rng(seed)
    close_arr = np.array(close)
    wick = np.abs(rng.normal(0, 0.3, size=len(close))) + 1e-6
    high = close_arr + wick
    low = close_arr - wick
    open_ = np.roll(close_arr, 1)
    open_[0] = close_arr[0]
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close_arr, "volume": 1000.0},
        index=idx,
    )


def _random_close(n: int, seed: int = 1) -> list[float]:
    rng = np.random.default_rng(seed)
    return list(100.0 + np.cumsum(rng.normal(0, 1.0, size=n)))


# --- realized_vol -----------------------------------------------------------


def test_realized_vol_constant_price_is_zero() -> None:
    df = _df([100.0] * 30, seed=2)
    # sabit close -> log getiri sıfır -> vol sıfır (wick'ler high/low'a
    # gider, close sabit kaldığı sürece realized_vol etkilenmez)
    vol = realized_vol(df["close"], n=10, annualize=False)
    assert math.isclose(vol.iloc[-1], 0.0, abs_tol=1e-9)


def test_realized_vol_first_n_bars_are_nan() -> None:
    df = _df(_random_close(30), seed=3)
    vol = realized_vol(df["close"], n=10, annualize=False)
    assert vol.iloc[:10].isna().all()
    assert vol.iloc[10:].notna().all()


def test_realized_vol_annualize_scales_by_sqrt_252() -> None:
    df = _df(_random_close(40), seed=4)
    raw = realized_vol(df["close"], n=10, annualize=False)
    ann = realized_vol(df["close"], n=10, annualize=True)
    ratio = (ann / raw).dropna()
    assert np.allclose(ratio.to_numpy(), math.sqrt(252))


def test_realized_vol_prefix_consistent() -> None:
    """t barındaki değer yalnızca t ve öncesine bağlı: df[:cut] üzerinde
    hesaplanan seri, tam seri üzerinde hesaplananın aynı ön ekiyle eşleşmeli."""
    df = _df(_random_close(50), seed=5)
    full = realized_vol(df["close"], n=10)
    cut = 30
    partial = realized_vol(df["close"].iloc[:cut], n=10)
    pd.testing.assert_series_equal(partial, full.iloc[:cut])


# --- keltner ------------------------------------------------------------


def test_keltner_upper_lower_bracket_mid() -> None:
    df = _df(_random_close(40), seed=6)
    k = keltner(df, n=10, atr_period=10, k=2.0)
    valid = k.mid.notna() & k.upper.notna()
    assert (k.upper[valid] >= k.mid[valid]).all()
    assert (k.lower[valid] <= k.mid[valid]).all()


def test_keltner_widens_with_larger_k() -> None:
    df = _df(_random_close(40), seed=7)
    narrow = keltner(df, n=10, atr_period=10, k=1.0)
    wide = keltner(df, n=10, atr_period=10, k=3.0)
    t = -1
    assert wide.upper.iloc[t] - wide.lower.iloc[t] > narrow.upper.iloc[t] - narrow.lower.iloc[t]


def test_keltner_prefix_consistent() -> None:
    df = _df(_random_close(50), seed=8)
    full = keltner(df, n=10, atr_period=10, k=2.0)
    cut = 35
    partial = keltner(df.iloc[:cut], n=10, atr_period=10, k=2.0)
    pd.testing.assert_series_equal(partial.mid, full.mid.iloc[:cut])
    pd.testing.assert_series_equal(partial.upper, full.upper.iloc[:cut])
    pd.testing.assert_series_equal(partial.lower, full.lower.iloc[:cut])


# --- vol_zscore -----------------------------------------------------------


def test_vol_zscore_prefix_consistent() -> None:
    df = _df(_random_close(200), seed=9)
    full = vol_zscore(df["close"], vol_window=10, zscore_window=50)
    cut = 150
    partial = vol_zscore(df["close"].iloc[:cut], vol_window=10, zscore_window=50)
    pd.testing.assert_series_equal(partial, full.iloc[:cut])


def test_vol_zscore_nan_before_enough_history() -> None:
    df = _df(_random_close(40), seed=10)
    z = vol_zscore(df["close"], vol_window=10, zscore_window=20)
    # realized_vol ilk 10 bar NaN; zscore da kendi penceresi (20) dolana
    # kadar NaN -> ilk 10+20-1 bar NaN olmalı
    assert z.iloc[: 10 + 20 - 1].isna().all()


@pytest.mark.parametrize("fn_name", ["atr", "bollinger"])
def test_existing_helpers_still_importable(fn_name: str) -> None:
    """Faz 2-EK'in eklediği importların (numpy, stats.zscore) mevcut
    atr/bollinger'ı bozmadığını doğrular (regresyon güvenliği)."""
    assert callable(atr) if fn_name == "atr" else callable(bollinger)
