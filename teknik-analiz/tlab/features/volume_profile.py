"""Hacim profili (volume profile) — saf, geriye dönük pencere hesaplaması.

Bu modül zaman/onay kavramı taşımaz: df_window çağıran tarafından seçilmiş,
SABİT (genişlemeyen) geriye dönük bir pencere olmalıdır — non-repaint
sorumluluğu çağırana aittir (bkz. fibonacci.py ile aynı felsefe).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit


@dataclass(frozen=True)
class VolumeProfile:
    price_bins: tuple[float, ...]  # her bin'in orta fiyatı
    volumes: tuple[float, ...]
    poc: float  # en yüksek hacimli bin'in orta fiyatı (Point of Control)
    value_area_low: float
    value_area_high: float
    gaussian_mu: float | None
    gaussian_sigma: float | None


def profile(df_window: pd.DataFrame, bins: int = 24, value_area_pct: float = 0.70) -> VolumeProfile:
    """Pencere içindeki barların hacmini fiyat bin'lerine dağıtır.

    Basitleştirme: her barın TÜM hacmi, o barın tipik fiyatına
    ((high+low+close)/3) karşılık gelen TEK bin'e yazılır (barın kendi
    high-low aralığına orantılı dağıtım yapılmaz).
    value_area: POC'tan başlayıp, hacmi yüksek komşu bin'e doğru genişleyerek
    toplam hacmin value_area_pct'ine ulaşana kadar büyütülen ARALIKSIZ aralık.
    gaussian_fit: scipy curve_fit ile Gauss eğrisi uydurması; yakınsamazsa
    (gaussian_mu, gaussian_sigma) = (None, None).
    """
    if len(df_window) == 0:
        raise ValueError("df_window boş olamaz")

    low = float(df_window["low"].min())
    high = float(df_window["high"].max())
    if high <= low:
        high = low + 1e-6

    edges = np.linspace(low, high, bins + 1)
    volumes = np.zeros(bins)
    typical = (df_window["high"] + df_window["low"] + df_window["close"]) / 3.0
    bin_idx = np.clip(np.digitize(typical.to_numpy(), edges) - 1, 0, bins - 1)
    for i, v in zip(bin_idx, df_window["volume"].to_numpy(), strict=True):
        volumes[i] += v

    centers = (edges[:-1] + edges[1:]) / 2.0
    poc_idx = int(np.argmax(volumes))

    va_low, va_high = _value_area(edges, volumes, poc_idx, value_area_pct)
    mu, sigma = _fit_gaussian(centers, volumes)

    return VolumeProfile(
        price_bins=tuple(float(c) for c in centers),
        volumes=tuple(float(v) for v in volumes),
        poc=float(centers[poc_idx]),
        value_area_low=va_low,
        value_area_high=va_high,
        gaussian_mu=mu,
        gaussian_sigma=sigma,
    )


def _value_area(
    edges: np.ndarray, volumes: np.ndarray, poc_idx: int, pct: float
) -> tuple[float, float]:
    total = float(volumes.sum())
    if total <= 0:
        return float(edges[poc_idx]), float(edges[poc_idx + 1])

    target = pct * total
    lo_idx, hi_idx = poc_idx, poc_idx
    acc = float(volumes[poc_idx])

    while acc < target and (lo_idx > 0 or hi_idx < len(volumes) - 1):
        vol_below = volumes[lo_idx - 1] if lo_idx > 0 else -1.0
        vol_above = volumes[hi_idx + 1] if hi_idx < len(volumes) - 1 else -1.0
        if vol_above >= vol_below:
            hi_idx += 1
            acc += volumes[hi_idx]
        else:
            lo_idx -= 1
            acc += volumes[lo_idx]

    return float(edges[lo_idx]), float(edges[hi_idx + 1])


def find_hvn_nodes(
    volumes: tuple[float, ...], top_n: int = 3, min_ratio: float = 0.55
) -> tuple[int, ...]:
    """Yüksek Hacim Düğümü (HVN) bin indekslerini döner — yerel maksimum
    (komşularından düşük olmayan) VE hacmi en yoğun bin'in en az `min_ratio`
    katı olan bin'ler adaydır, en yoğun `top_n` tanesi (artan indeks sırasında)
    döner. POC/value_area'dan BAĞIMSIZ, saf histogram tepe-noktası tespiti
    (referans ekran görüntüsündeki "HVN" vurgusu — value area sınırıyla
    örtüşebilir ama aynı şey değildir, bir dağılımın birden fazla tepesi
    olabilir)."""
    if not volumes:
        return ()
    peak = max(volumes)
    if peak <= 0:
        return ()
    threshold = peak * min_ratio
    n = len(volumes)
    candidates = [
        i for i, v in enumerate(volumes)
        if v >= threshold
        and (i == 0 or v >= volumes[i - 1])
        and (i == n - 1 or v >= volumes[i + 1])
    ]
    candidates.sort(key=lambda i: volumes[i], reverse=True)
    return tuple(sorted(candidates[:top_n]))


def _gaussian(x: np.ndarray, amplitude: float, mu: float, sigma: float) -> np.ndarray:
    return amplitude * np.exp(-0.5 * ((x - mu) / sigma) ** 2)


def _fit_gaussian(centers: np.ndarray, volumes: np.ndarray) -> tuple[float | None, float | None]:
    if len(centers) < 3 or float(volumes.sum()) <= 0:
        return None, None

    span = centers[-1] - centers[0]
    p0 = [float(volumes.max()), float(centers[int(np.argmax(volumes))]), max(span / 4.0, 1e-6)]
    try:
        popt, _ = curve_fit(_gaussian, centers, volumes, p0=p0, maxfev=2000)
    except (RuntimeError, ValueError):
        return None, None

    _, mu, sigma = popt
    return float(mu), float(abs(sigma))
