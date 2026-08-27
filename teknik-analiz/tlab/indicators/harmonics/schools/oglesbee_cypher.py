"""Darren Oglesbee — Cypher. C, A'yı aşar (c_beyond_a=True); D, XC bacağının
%78.6 geri çekilmesidir (tek seviye, single_pm_tol)."""

from __future__ import annotations

from tlab.indicators.harmonics.schools.base import HarmonicSchool, PatternSpec

_TOL = 0.04


class CypherSchool(HarmonicSchool):
    name = "cypher"
    tolerance = _TOL

    def __init__(self) -> None:
        self.patterns = {
            "cypher": PatternSpec(
                name="cypher", xab=(0.382, 0.618), abc=(1.272, 1.414),
                d_components=(("xc_ret", 0.786 - _TOL, 0.786 + _TOL),),
                prz_method="single_pm_tol", c_beyond_a_required=True,
                invalidation=("xc_ret", 1.0),
            ),
        }
