"""src.analysis.volume_profile testleri."""

from __future__ import annotations

import numpy as np

from src.analysis.volume_profile import compute_volume_profile, rolling_volume_profile


def test_bos_pencerede_none():
    assert compute_volume_profile(np.array([]), np.array([]), np.array([])) is None


def test_dejenere_sabit_fiyatta_none():
    high = np.full(10, 100.0)
    low = np.full(10, 100.0)
    volume = np.full(10, 1000.0)
    assert compute_volume_profile(high, low, volume) is None


def test_poc_en_yuksek_hacimli_bolgeye_yakin():
    # Cogu hacim 100-101 araliginda yogunlasiyor, birkac bar 90/110'da az hacimle.
    high = np.array([110.0, 101.0, 101.0, 101.0, 101.0, 90.0])
    low = np.array([109.0, 100.0, 100.0, 100.0, 100.0, 89.0])
    volume = np.array([10.0, 500.0, 500.0, 500.0, 500.0, 10.0])
    vp = compute_volume_profile(high, low, volume, n_bins=50)
    assert vp is not None
    assert 99.5 <= vp.poc <= 101.5


def test_vah_val_poc_yapisal_siralama():
    rng = np.random.default_rng(3)
    n = 40
    mid = 100 + np.cumsum(rng.normal(0, 0.3, n))
    high = mid + np.abs(rng.normal(0, 0.5, n))
    low = mid - np.abs(rng.normal(0, 0.5, n))
    volume = rng.uniform(100, 1000, n)
    vp = compute_volume_profile(high, low, volume, n_bins=30)
    assert vp is not None
    assert vp.val <= vp.poc <= vp.vah


def test_value_area_hacmin_en_az_hedeflenen_orani_kapsar():
    rng = np.random.default_rng(5)
    n = 60
    mid = 100 + np.cumsum(rng.normal(0, 0.2, n))
    high = mid + np.abs(rng.normal(0, 0.4, n))
    low = mid - np.abs(rng.normal(0, 0.4, n))
    volume = rng.uniform(100, 1000, n)
    n_bins = 40
    vp = compute_volume_profile(high, low, volume, n_bins=n_bins, value_area_pct=0.70)
    assert vp is not None

    bin_edges = np.linspace(float(np.min(low)), float(np.max(high)), n_bins + 1)
    bin_volume = np.zeros(n_bins)
    for i in range(n):
        first_bin = max(0, min(int(np.searchsorted(bin_edges, low[i], side="right") - 1), n_bins - 1))
        last_bin = max(0, min(int(np.searchsorted(bin_edges, high[i], side="right") - 1), n_bins - 1))
        span = last_bin - first_bin + 1
        bin_volume[first_bin : last_bin + 1] += volume[i] / span
    total = bin_volume.sum()

    in_va_mask = (bin_edges[:-1] >= vp.val - 1e-9) & (bin_edges[1:] <= vp.vah + 1e-9)
    va_volume = bin_volume[in_va_mask].sum()
    assert va_volume / total >= 0.65  # ~%70 hedefine yakin (bin ayrikligi nedeniyle tolerans)


def test_rolling_volume_profile_ilk_pencere_none():
    n = 50
    high = np.full(n, 101.0)
    low = np.full(n, 99.0)
    volume = np.full(n, 100.0)
    out = rolling_volume_profile(high, low, volume, lookback=20)
    assert all(v is None for v in out[:20])
    assert out[20] is not None


def test_rolling_volume_profile_look_ahead_yok():
    rng = np.random.default_rng(9)
    n = 80
    mid = 100 + np.cumsum(rng.normal(0, 0.3, n))
    high = mid + np.abs(rng.normal(0, 0.5, n))
    low = mid - np.abs(rng.normal(0, 0.5, n))
    volume = rng.uniform(100, 1000, n)

    out_a = rolling_volume_profile(high, low, volume, lookback=20)

    high_mod, low_mod, volume_mod = high.copy(), low.copy(), volume.copy()
    high_mod[-5:] += 1000.0
    low_mod[-5:] += 1000.0
    out_b = rolling_volume_profile(high_mod, low_mod, volume_mod, lookback=20)

    for i in range(20, n - 5):
        assert out_a[i].poc == out_b[i].poc
