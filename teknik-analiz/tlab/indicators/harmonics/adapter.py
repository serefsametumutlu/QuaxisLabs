"""Harmonik `Candidate` -> grafik sözleşmesi (`XabcdPattern`) adaptörü.

Mevcut harmonik motor zaten X-A-B-C adaylarını, oranları ve durum
zincirini üretiyor (`geometry.py`, `state.py`). Eksik olan, bunu ÇİZİM
katmanının anlayacağı tipli bir sonuca çevirmekti — eskiden jenerik
`Line`/`Marker` torbasına düzleştiriliyor ve renderer'da anlamını
kaybediyordu.

Bu modül o çeviriyi yapar. Hesap YAPMAZ: oranlar ve PRZ, çağıranın
verdiği okul yapılandırmasından gelir.
"""

from __future__ import annotations

import pandas as pd

from tlab.chart.contracts import XabcdPattern, XabcdPoint
from tlab.indicators.harmonics.geometry import Candidate

# Geri çekilme merdiveni — X-A bacağı üzerinden
_FIB = ((0.0, "0.0 (A)"), (0.382, "0.382"), (0.5, "0.500"),
        (0.618, "0.618"), (0.786, "0.786"), (1.0, "1.0 (X)"),
        (1.272, "1.272 (D hedefi)"), (1.618, "1.618 (max risk)"))


def to_pattern(
    cand: Candidate,
    *,
    school: str,
    pattern_name: str,
    state: str,
    df: pd.DataFrame,
    prz: tuple[float, float] | None = None,
    theoretical_d: float | None = None,
    actual_d_time: pd.Timestamp | None = None,
    actual_d_price: float | None = None,
) -> XabcdPattern:
    pts = tuple(
        XabcdPoint(p.bar_time, float(p.price), lb)
        for p, lb in ((cand.x, "X"), (cand.a, "A"), (cand.b, "B"), (cand.c, "C"))
    )

    # Fibo merdiveni X-A bacağı üzerine kurulur; 0.0 = A ucu, 1.0 = X ucu.
    xa_lo, xa_hi = sorted((float(cand.x.price), float(cand.a.price)))
    span = xa_hi - xa_lo
    a_is_high = float(cand.a.price) > float(cand.x.price)

    def at(r: float) -> float:
        return (xa_hi - span * r) if a_is_high else (xa_lo + span * r)

    fib = tuple((r, at(r), lb) for r, lb in _FIB)

    d = None
    if actual_d_time is not None and actual_d_price is not None:
        d = XabcdPoint(actual_d_time, float(actual_d_price), "D")

    anchor = d.t if d is not None else cand.c.bar_time
    bars_ago = int((df.index > anchor).sum())

    return XabcdPattern(
        school=school, pattern_name=pattern_name, direction=cand.direction,
        points=pts, state=state, prz=prz, theoretical_d=theoretical_d,
        actual_d=d, fib_levels=fib,
        ratios=(("AB/XA", f"{cand.ab_xa:.3f}"), ("BC/AB", f"{cand.bc_ab:.3f}")),
        bars_ago=bars_ago,
    )
