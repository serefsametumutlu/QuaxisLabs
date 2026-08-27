"""Fibonacci oran hesaplamaları — saf fonksiyonlar, veri/zaman bilgisi taşımaz.

Bu modül yalnızca fiyat aritmetiği yapar; hangi barda hesaplandığı/onaylandığı
(non-repaint zamanlama) çağıran katmanın (indicators) sorumluluğundadır —
burada üretilen seviyeler zaman içermez, dict[float, float] (oran -> fiyat).
"""

from __future__ import annotations

DEFAULT_RETRACEMENT_LEVELS: tuple[float, ...] = (0.236, 0.382, 0.5, 0.618, 0.786, 0.886, 1.0)
DEFAULT_EXTENSION_LEVELS: tuple[float, ...] = (1.0, 1.272, 1.414, 1.618, 2.0, 2.24, 2.618)
DEFAULT_PROJECTION_RATIOS: tuple[float, ...] = (1.0, 1.272, 1.618)


def retracement(
    p0: float, p1: float, levels: tuple[float, ...] = DEFAULT_RETRACEMENT_LEVELS
) -> dict[float, float]:
    """p0->p1 hareketinin geri çekilme (retracement) seviyeleri.

    p1'den p0 yönüne doğru levels oranı kadar geri gidilen fiyatlar döner
    (0.0 -> p1, 1.0 -> p0). p0/p1 sırası yön belirtir (p1>p0 ise yukarı
    hareket, seviyeler p1'in altında; p1<p0 ise tersi).
    """
    span = p1 - p0
    return {lv: p1 - lv * span for lv in levels}


def extension(
    p0: float, p1: float, levels: tuple[float, ...] = DEFAULT_EXTENSION_LEVELS
) -> dict[float, float]:
    """p0->p1 hareketinin p1'den ötesine uzantı (extension) seviyeleri.

    1.0 -> p1 (hareketin kendisi), levels arttıkça p1'den p0->p1 yönünde
    daha ileriye giden fiyatlar döner.
    """
    span = p1 - p0
    return {lv: p0 + lv * span for lv in levels}


def projection_abcd(
    a: float, b: float, c: float, ratios: tuple[float, ...] = DEFAULT_PROJECTION_RATIOS
) -> dict[float, float]:
    """AB bacağının BC'den itibaren CD olarak projeksiyonuyla D adayları.

    D = c + ratio * (b - a) — yani CD bacağı, AB'nin ratio katı kadar (AB
    ile aynı yönde) C'den itibaren uzanır. ratios=(1.0,) klasik AB=CD'yi verir.
    """
    ab = b - a
    return {r: c + r * ab for r in ratios}


def ratio(a: float, b: float, c: float) -> float:
    """BC bacağının AB bacağına oranı: |c-b| / |b-a|. AB=0 ise 0.0 döner."""
    ab = abs(b - a)
    if ab == 0:
        return 0.0
    return abs(c - b) / ab


def within(x: float, lo: float, hi: float, tol: float = 0.0, tol_kind: str = "abs") -> bool:
    """x, [lo,hi] aralığında (tol payıyla genişletilmiş) mi?

    tol_kind="abs": aralık [lo-tol, hi+tol]. tol_kind="rel": aralık
    genişliği kadar oransal pay, [lo - tol*(hi-lo), hi + tol*(hi-lo)].
    lo>hi verilirse otomatik olarak sıralanır.
    """
    if lo > hi:
        lo, hi = hi, lo
    if tol_kind == "rel":
        pad = tol * (hi - lo)
    else:
        pad = tol
    return (lo - pad) <= x <= (hi + pad)
