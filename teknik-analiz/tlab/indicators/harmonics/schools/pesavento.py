"""Larry Pesavento ekolü — PRZ tek-seviye±tolerans (single_pm_tol), ±0.05.

Carney'den ayrılan iki nokta: (1) daha geniş tolerans, (2) her formasyonda
AB=CD simetrisi zorunlu (D tahmini, CD/AB oranının 1.0/1.27/1.618'e yakın
olmasını da sağlamalı — bkz. _post_prz_match). Ek teyit (extra_confirmation)
X→B trend çizgisi kırılımıdır; asıl kırılım tespiti confirmation_policy=
"xb_break" ile scanner_indicator.py'de yapılır, burada yalnızca extra
teyit için de aynı yönü ister (school policy seçilirse).
"""

from __future__ import annotations

import pandas as pd

from tlab.indicators.harmonics.geometry import Candidate
from tlab.indicators.harmonics.prz import PRZ
from tlab.indicators.harmonics.schools.base import HarmonicSchool, PatternSpec

_TOL = 0.05
_AB_CD_RATIOS = (1.0, 1.27, 1.618)


def _pt(v: float, tol: float = _TOL) -> tuple[float, float]:
    return (v - tol, v + tol)


class PesaventoSchool(HarmonicSchool):
    name = "pesavento"
    tolerance = _TOL

    def __init__(self) -> None:
        self.patterns = {
            "gartley": PatternSpec(
                name="gartley", xab=_pt(0.618), abc=(0.382, 0.886),
                d_components=(("xa_ret", 0.786 - _TOL, 0.786 + _TOL),),
                prz_method="single_pm_tol", invalidation=("xa_ret", 1.0),
                extra={
                    "assumed": "abc aralığı Carney'den ödünç alındı "
                    "(spesifikasyonda C aralığı verilmemiş)",
                },
            ),
            "butterfly": PatternSpec(
                name="butterfly", xab=_pt(0.786), abc=(0.382, 0.886),
                d_components=(("xa_ext", 1.27, 1.618),),
                prz_method="single_pm_tol", invalidation=("xa_ext", 1.618),
            ),
        }

    def _post_prz_match(self, candidate: Candidate, spec: PatternSpec, prz: PRZ) -> bool:
        ab = abs(candidate.b.price - candidate.a.price)
        if ab == 0:
            return False
        cd_ab = abs(prz.center - candidate.c.price) / ab
        return any(abs(cd_ab - r) <= self.tolerance for r in _AB_CD_RATIOS)

    def extra_confirmation(self, df: pd.DataFrame, candidate: Candidate, t: int) -> bool:
        x, b = candidate.x, candidate.b
        slope = (b.price - x.price) / (b.bar_idx - x.bar_idx)
        intercept = x.price - slope * x.bar_idx
        line_val = slope * t + intercept
        close_t = float(df["close"].iloc[t])
        return close_t > line_val if candidate.direction == "bullish" else close_t < line_val
