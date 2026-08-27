"""Scott Carney ekolü — PRZ kesişim (intersection), tolerance ±0.03.

Gartley/Bat/Crab/Deep Crab/Butterfly klasik XABCD retracement kalıpları
(c_beyond_a=False); Shark, C'nin A'yı aştığı (c_beyond_a=True) 0-X-A-B-C
yapısı — D projeksiyonu XA yerine 0X ve BC bacaklarının kesişimidir.
"""

from __future__ import annotations

from tlab.indicators.harmonics.schools.base import HarmonicSchool, PatternSpec

_TOL = 0.03


def _pt(v: float, tol: float = _TOL) -> tuple[float, float]:
    return (v - tol, v + tol)


class CarneySchool(HarmonicSchool):
    name = "carney"
    tolerance = _TOL

    def __init__(self) -> None:
        self.patterns = {
            "gartley": PatternSpec(
                name="gartley", xab=_pt(0.618), abc=(0.382, 0.886),
                d_components=(("xa_ret", 0.786 - _TOL, 0.786 + _TOL), ("bc_ext", 1.13, 1.618)),
                prz_method="intersection", invalidation=("xa_ret", 1.0),
            ),
            "bat": PatternSpec(
                name="bat", xab=(0.382, 0.50), abc=(0.382, 0.886),
                d_components=(("xa_ret", 0.886 - _TOL, 0.886 + _TOL), ("bc_ext", 1.618, 2.618)),
                prz_method="intersection", invalidation=("xa_ret", 1.0),
            ),
            "crab": PatternSpec(
                name="crab", xab=(0.382, 0.618), abc=(0.382, 0.886),
                d_components=(("xa_ext", 1.618 - _TOL, 1.618 + _TOL), ("bc_ext", 2.24, 3.618)),
                prz_method="intersection", invalidation=("xa_ext", 2.0),
            ),
            "deep_crab": PatternSpec(
                name="deep_crab", xab=_pt(0.886), abc=(0.382, 0.886),
                d_components=(("xa_ext", 1.618 - _TOL, 1.618 + _TOL), ("bc_ext", 2.24, 3.618)),
                prz_method="intersection", invalidation=("xa_ext", 2.0),
                extra={
                    "assumed": "abc/bc_ext aralığı crab ile aynı alındı "
                    "(spesifikasyonda verilmemiş)",
                },
            ),
            "butterfly": PatternSpec(
                name="butterfly", xab=_pt(0.786), abc=(0.382, 0.886),
                d_components=(("xa_ext", 1.27 - _TOL, 1.27 + _TOL), ("bc_ext", 1.618, 2.24)),
                prz_method="intersection", invalidation=("xa_ext", 1.618),
            ),
            "shark": PatternSpec(
                name="shark", xab=None, abc=(1.13, 1.618),
                d_components=(("0x_proj", 0.886, 1.13), ("bc_ext", 1.618, 2.24)),
                prz_method="intersection", c_beyond_a_required=True, requires_zero=True,
                invalidation=("bc_ext", 2.618),
            ),
        }
