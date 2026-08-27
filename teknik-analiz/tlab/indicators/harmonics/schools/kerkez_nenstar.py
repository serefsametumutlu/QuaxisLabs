"""Nenad Kerkez — Nen Star. C, A'yı aşar; D = XA'nın 1.272 uzantısı ile
BC'nin 1.618-2.0 uzantısının kesişimi. Ek teyit: D barında EMA(20)/EMA(50)
trend yönüyle uyumlu VE MACD histogramı dönüş yönünde (aynı bardaki
değerler — ileri bakmaz, her ikisi de yalnızca t ve öncesini kullanan
ma.ema/oscillators.macd üzerinden hesaplanır)."""

from __future__ import annotations

import pandas as pd

from tlab.features.ma import ema
from tlab.features.oscillators import macd
from tlab.indicators.harmonics.geometry import Candidate
from tlab.indicators.harmonics.schools.base import HarmonicSchool, PatternSpec

_TOL = 0.04


class NenStarSchool(HarmonicSchool):
    name = "nenstar"
    tolerance = _TOL

    def __init__(self) -> None:
        self.patterns = {
            "nenstar": PatternSpec(
                name="nenstar", xab=(0.382, 0.618), abc=(1.272, 1.414),
                d_components=(("xa_ext", 1.272 - _TOL, 1.272 + _TOL), ("bc_ext", 1.618, 2.0)),
                prz_method="intersection", c_beyond_a_required=True,
                invalidation=("xa_ext", 1.618),
            ),
        }

    def extra_confirmation(self, df: pd.DataFrame, candidate: Candidate, t: int) -> bool:
        close = df["close"].iloc[: t + 1]
        if len(close) < 50:
            return False
        ema20 = ema(close, 20).iloc[-1]
        ema50 = ema(close, 50).iloc[-1]
        m = macd(close)
        hist = m.histogram.iloc[-1]
        if pd.isna(ema20) or pd.isna(ema50) or pd.isna(hist):
            return False
        if candidate.direction == "bullish":
            return bool(ema20 > ema50 and hist > 0)
        return bool(ema20 < ema50 and hist < 0)
