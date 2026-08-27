"""Faz 0 repaint-test altyapısını doğrulamak için kullanılan örnek (sahte)
indikatörler — üretim kodu değildir, yalnızca testlerde kullanılır."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.signal import argrelextrema

from tlab.core.indicator import BaseIndicator
from tlab.core.params import BaseParams, params_hash
from tlab.core.types import IndicatorMeta, IndicatorResult, Signal, Timeframe


@dataclass(frozen=True)
class SmaCrossParams(BaseParams):
    fast: int = 5
    slow: int = 20


class HonestIndicator(BaseIndicator):
    """Dürüst SMA kesişimi: yalnızca geriye dönük (backward) rolling pencere
    ve pozitif shift kullanır — non-repaint olmalı."""

    meta = IndicatorMeta(
        name="test.honest_sma_cross",
        version="0.1.0",
        category="testing",
        description="SMA kesişimi — non-repaint kanıt indikatörü.",
        supported_timeframes=(Timeframe.D1, Timeframe.H4),
    )

    def __init__(self, params: SmaCrossParams | None = None) -> None:
        self.params = params or SmaCrossParams()

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        fast = df["close"].rolling(self.params.fast).mean()
        slow = df["close"].rolling(self.params.slow).mean()
        cross_up = (fast > slow) & (fast.shift(1) <= slow.shift(1))
        cross_down = (fast < slow) & (fast.shift(1) >= slow.shift(1))

        signals: list[Signal] = []
        for t in df.index[self.params.slow :]:
            if bool(cross_up.loc[t]):
                signals.append(
                    Signal(t, t, "long", "active", 1.0,
                           {"fast": float(fast.loc[t]), "slow": float(slow.loc[t])})
                )
            elif bool(cross_down.loc[t]):
                signals.append(
                    Signal(t, t, "short", "active", 1.0,
                           {"fast": float(fast.loc[t]), "slow": float(slow.loc[t])})
                )

        return IndicatorResult(
            indicator=self.meta.name,
            version=self.meta.version,
            params_hash=params_hash(self.params),
            symbol="TEST",
            timeframe=Timeframe.D1,
            signals=signals,
            series={"sma_fast": fast, "sma_slow": slow},
        )


@dataclass(frozen=True)
class PivotParams(BaseParams):
    order: int = 5


class CheatingIndicator(BaseIndicator):
    """HİLELİ: argrelextrema ile pivot bulur ama sinyali PİVOT BARININ
    kendisine yazar (onay barına değil — pivot + order olmalıydı).
    Repaint testinin FAIL'i doğru yakaladığını kanıtlamak için var."""

    meta = IndicatorMeta(
        name="test.cheating_pivot",
        version="0.1.0",
        category="testing",
        description="Kasıtlı hatalı (repaint eden) indikatör — yalnızca test amaçlı.",
        supported_timeframes=(Timeframe.D1,),
    )

    def __init__(self, params: PivotParams | None = None) -> None:
        self.params = params or PivotParams()

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        high = df["high"].to_numpy()
        order = self.params.order
        peak_idx = argrelextrema(high, np.greater_equal, order=order)[0]

        signals: list[Signal] = []
        for i in peak_idx:
            if order <= i <= len(high) - order - 1:
                t = df.index[i]
                signals.append(Signal(t, t, "short", "active", 1.0, {"price": float(high[i])}))

        return IndicatorResult(
            indicator=self.meta.name,
            version=self.meta.version,
            params_hash=params_hash(self.params),
            symbol="TEST",
            timeframe=Timeframe.D1,
            signals=signals,
        )


class CenteredIndicator(BaseIndicator):
    """HİLELİ: rolling(center=True) kullanarak merkezi (geleceğe bakan)
    ortalama üretir — hem repaint testi hem statik lint bunu yakalamalı."""

    meta = IndicatorMeta(
        name="test.centered_ma",
        version="0.1.0",
        category="testing",
        description="rolling(center=True) kötüye kullanımı — yalnızca test amaçlı.",
        supported_timeframes=(Timeframe.D1,),
    )

    def __init__(self, window: int = 5) -> None:
        self.params = SmaCrossParams(fast=window, slow=window)

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        centered = df["close"].rolling(self.params.fast, center=True).mean()
        cross = ((df["close"] > centered) & (df["close"].shift(1) <= centered.shift(1))).fillna(False)

        signals: list[Signal] = []
        for t in df.index[cross.to_numpy()]:
            signals.append(Signal(t, t, "long", "active", 1.0, {"centered": float(centered.loc[t])}))

        return IndicatorResult(
            indicator=self.meta.name,
            version=self.meta.version,
            params_hash=params_hash(self.params),
            symbol="TEST",
            timeframe=Timeframe.D1,
            signals=signals,
            series={"centered_ma": centered},
        )
