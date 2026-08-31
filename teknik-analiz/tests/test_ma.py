"""tlab.features.ma için birim testleri."""

from __future__ import annotations

import math
from zoneinfo import ZoneInfo

import pandas as pd

from tlab.features.ma import crossovers, ema, hull, kama, sma, wma

TZ = ZoneInfo("Europe/Istanbul")


def _series(values: list[float]) -> pd.Series:
    idx = pd.date_range("2024-01-02 10:00", periods=len(values), freq="1D", tz=TZ)
    return pd.Series(values, index=idx)


def test_sma_known_value() -> None:
    s = _series([1.0, 2.0, 3.0, 4.0])
    result = sma(s, window=2)
    assert math.isclose(result.iloc[1], 1.5)
    assert math.isclose(result.iloc[3], 3.5)
    assert pd.isna(result.iloc[0])


def test_ema_converges_to_constant() -> None:
    s = _series([5.0] * 20)
    result = ema(s, span=5)
    assert math.isclose(result.iloc[-1], 5.0, abs_tol=1e-9)


def test_wma_known_value() -> None:
    s = _series([1.0, 2.0, 3.0])
    result = wma(s, window=2)
    # ağırlık [1,2]: (1*1 + 2*2)/3 = 5/3 (idx1), (1*2 + 2*3)/3 = 8/3 (idx2)
    assert math.isclose(result.iloc[1], 5.0 / 3.0)
    assert math.isclose(result.iloc[2], 8.0 / 3.0)


def test_hull_tracks_perfectly_linear_series_exactly() -> None:
    s = _series([float(i) for i in range(1, 15)])
    result = hull(s, window=4)
    for i in range(4, len(s)):
        assert math.isclose(result.iloc[i], s.iloc[i], abs_tol=1e-9), i


def test_crossovers_detects_up_and_down() -> None:
    fast = _series([1.0, 3.0, 1.0, 3.0, 1.0])
    slow = _series([2.0, 2.0, 2.0, 2.0, 2.0])
    result = crossovers(fast, slow)
    assert result.iloc[1] == "up"  # 1<2 -> 3>2
    assert result.iloc[2] == "down"  # 3>2 -> 1<2
    assert result.iloc[3] == "up"
    assert pd.isna(result.iloc[0])


def test_kama_converges_to_constant() -> None:
    s = _series([5.0] * 40)
    result = kama(s, er_window=10)
    assert math.isclose(result.iloc[-1], 5.0, abs_tol=1e-9)
    assert pd.isna(result.iloc[9])  # er_window=10 -> ilk gerçek değer indeks 10'da


def test_kama_tracks_faster_in_strong_trend_than_in_choppy_series() -> None:
    """Verimlilik oranı (ER) güçlü/net trendde ~1'e, gürültülü/yatay
    seride ~0'a yakın olmalı -> KAMA trendli seride SMA'dan daha HIZLI,
    gürültülü seride daha YAVAŞ (SMA'ya daha yakın) tepki vermeli."""
    n = 60
    trend = _series([100.0 + i for i in range(n)])
    choppy = _series([100.0 + (10.0 if i % 2 == 0 else -10.0) for i in range(n)])

    kama_trend = kama(trend, er_window=10, fast=2, slow=30)
    kama_choppy = kama(choppy, er_window=10, fast=2, slow=30)

    # Trendli seride KAMA son bara (uzak SMA'dan) yakın kalmalı (hızlı takip).
    assert abs(kama_trend.iloc[-1] - trend.iloc[-1]) < 5.0
    # Gürültülü/yatay (zikzak) seride ER~0 -> KAMA neredeyse HİÇ hareket
    # etmemeli (ilk geçerli değerinden çok az sapmalı) — mutlak 100 çıpası
    # DEĞİL, KENDİ ilk değerine göre "yavaşlık" ölçülür.
    first_valid = kama_choppy.dropna().iloc[0]
    assert abs(kama_choppy.iloc[-1] - first_valid) < 5.0
