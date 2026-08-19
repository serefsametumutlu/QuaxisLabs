"""Hacim Profili (Volume Profile) -- POC/VAH/VAL. SAF MATEMATIK, I/O YOK
(`abcd_pattern.py` ile AYNI katman ilkesi).

Motivasyon (2026-08-19, kullanicinin harici arastirma kaynagi --
`ULTIMATE_5_STRATEGIES.md §4 MMR/Microstructure Mean-Reverter`): gercek
emir defteri (LOB) verisi YOK (yfinance sadece OHLCV verir), ama HACIM
PROFILI (bir fiyat araligina o barin toplam hacminin ORANTILI dagitilmasi)
OHLCV'den yaklasiklikla turetilebilir -- "en cok islem gorern fiyat" (POC)
ve "hacmin %70'ini kapsayan bant" (Value Area, VAH/VAL) boylece destek/
direnc seviyeleri olarak kullanilabilir, ozel bir veri kaynagi GEREKMEZ.

Yaklasiklik notu: her barin hacmi, o barin [low,high] araligina UNIFORM
dagitilir (TPO/gercek tick-bazli profil DEGIL -- gercek intrabar fiyat
dagilimi bilinmiyor, bu STANDART bir yaklasiklik, bkz. MMR spec'inin
`calculate_market_profile` fonksiyonu -- AYNI ilke, burada vektorize
edildi performans icin).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class VolumeProfile:
    poc: float  # Point of Control -- en yuksek hacimli fiyat
    vah: float  # Value Area High
    val: float  # Value Area Low


def compute_volume_profile(
    high: np.ndarray, low: np.ndarray, volume: np.ndarray, n_bins: int = 50, value_area_pct: float = 0.70
) -> VolumeProfile | None:
    """Verilen pencere (zaten dilimlenmis high/low/volume dizileri) icin
    POC/VAH/VAL. Gecersiz/yetersiz pencerede (tum barlar sifir araliga
    sahip, veya bos) None doner -- FIRLATMAZ."""
    n = len(high)
    if n == 0:
        return None

    lo = float(np.min(low))
    hi = float(np.max(high))
    if not (hi > lo):
        return None

    bin_edges = np.linspace(lo, hi, n_bins + 1)
    bin_volume = np.zeros(n_bins)

    for i in range(n):
        bar_lo, bar_hi, vol = float(low[i]), float(high[i]), float(volume[i])
        if vol <= 0 or not (bar_hi > bar_lo):
            continue
        first_bin = int(np.searchsorted(bin_edges, bar_lo, side="right") - 1)
        last_bin = int(np.searchsorted(bin_edges, bar_hi, side="right") - 1)
        first_bin = max(0, min(first_bin, n_bins - 1))
        last_bin = max(0, min(last_bin, n_bins - 1))
        span = last_bin - first_bin + 1
        bin_volume[first_bin : last_bin + 1] += vol / span

    total_vol = float(bin_volume.sum())
    if total_vol <= 0:
        return None

    poc_bin = int(np.argmax(bin_volume))
    poc = float((bin_edges[poc_bin] + bin_edges[poc_bin + 1]) / 2.0)

    order = np.argsort(bin_volume)[::-1]
    cum = 0.0
    included = []
    target = total_vol * value_area_pct
    for b in order:
        included.append(b)
        cum += bin_volume[b]
        if cum >= target:
            break

    vah = float(bin_edges[max(included) + 1])
    val = float(bin_edges[min(included)])
    return VolumeProfile(poc=poc, vah=vah, val=val)


def rolling_volume_profile(
    high: np.ndarray, low: np.ndarray, volume: np.ndarray, lookback: int = 20, n_bins: int = 50, value_area_pct: float = 0.70
) -> list[VolumeProfile | None]:
    """`compute_volume_profile`in kayan-pencere hali -- her bar `i` icin
    SADECE `[i-lookback, i)` (kendisi HARIC, look-ahead YOK) kullanilir.
    Ilk `lookback` bar icin None (henuz hesaplanamadi)."""
    n = len(high)
    out: list[VolumeProfile | None] = [None] * n
    for i in range(lookback, n):
        window = slice(i - lookback, i)
        out[i] = compute_volume_profile(high[window], low[window], volume[window], n_bins=n_bins, value_area_pct=value_area_pct)
    return out
