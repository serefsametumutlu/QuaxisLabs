"""Bryce Gilmore ekolü — Pesavento'nun fiyat oranlarını taban alır, üstüne
ZAMAN oranı şartı ekler (Time Bars): bars_cd/bars_ab ve bars_xd/bars_xa
standart Fibonacci oranlarına yakın olmalı. time_window(), bu iki bağımsız
zaman tahmininin (C'den ve X'ten) birleşimiyle D'nin beklendiği bar
aralığını verir; PRZ'ye bu pencere DIŞINDA gelen fiyat ACTIVE'e geçmez
(bkz. state.py), pencere kapanırsa EXPIRED olur.
"""

from __future__ import annotations

from tlab.indicators.harmonics.geometry import Candidate
from tlab.indicators.harmonics.schools.base import HarmonicSchool, PatternSpec

_TOL = 0.05
_TOL_TIME = 0.15
_CD_AB_RATIOS = (1.0, 1.272, 1.618)
_XD_XA_RATIOS = (0.618, 1.0, 1.618)


def _pt(v: float, tol: float = _TOL) -> tuple[float, float]:
    return (v - tol, v + tol)


class GilmoreSchool(HarmonicSchool):
    name = "gilmore"
    tolerance = _TOL

    def __init__(self) -> None:
        self.patterns = {
            "gartley": PatternSpec(
                name="gartley", xab=_pt(0.618), abc=(0.382, 0.886),
                d_components=(("xa_ret", 0.786 - _TOL, 0.786 + _TOL),),
                prz_method="single_pm_tol", invalidation=("xa_ret", 1.0),
            ),
            "butterfly": PatternSpec(
                name="butterfly", xab=_pt(0.786), abc=(0.382, 0.886),
                d_components=(("xa_ext", 1.27, 1.618),),
                prz_method="single_pm_tol", invalidation=("xa_ext", 1.618),
            ),
        }

    def time_window(self, candidate: Candidate, spec: PatternSpec) -> tuple[int, int] | None:
        from_ab = [candidate.c.bar_idx + round(r * candidate.bars_ab) for r in _CD_AB_RATIOS]
        from_xa = [candidate.x.bar_idx + round(r * candidate.bars_xa) for r in _XD_XA_RATIOS]
        estimates = from_ab + from_xa
        buffer = max(1, round(_TOL_TIME * candidate.bars_ab))
        min_idx = min(estimates) - buffer
        max_idx = max(estimates) + buffer
        return (max(0, min_idx - candidate.c.bar_idx), max(1, max_idx - candidate.c.bar_idx))
