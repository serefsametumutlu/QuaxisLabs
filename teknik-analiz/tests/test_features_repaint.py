"""Faz 2 özellik fonksiyonlarını sarmalayan mini-indikatörlerle repaint testleri.

Bu indikatörler üretim kodu değildir; yalnızca tlab.testing.repaint.repaint_test
altyapısının özellik fonksiyonlarının non-repaint olduğunu doğrulamasını
sağlamak için var. repaint_test yalnızca signals/levels/lines/boxes/polygons'u
karşılaştırır (markers'ı KARŞILAŞTIRMAZ) — bu yüzden dinamik/onaylanan her şey
Signal (tam eşitlik) veya Box (extend-only) olarak ifade edilir.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tlab.core.indicator import BaseIndicator
from tlab.core.params import BaseParams, params_hash
from tlab.core.types import IndicatorMeta, IndicatorResult, Level, Signal, Timeframe
from tlab.features.fibonacci import retracement
from tlab.features.swings import EqPolicy, alternate_pivots, find_pivots, label_structure
from tlab.testing.fixtures import make_zigzag
from tlab.testing.repaint import repaint_test


@dataclass(frozen=True)
class SwingZigzagParams(BaseParams):
    left: int = 3
    right: int = 3
    eq_policy: EqPolicy = "nonstrict"


class SwingZigzagIndicator(BaseIndicator):
    """find_pivots -> alternate_pivots -> label_structure zincirini sarmalar.

    Her kesinleşmiş (finalized) zigzag pivotu bir Signal olarak yayınlanır:
    bar_time=pivotun oluştuğu bar, detected_at=finalized_time (kesinleştiği
    bar). repaint_test bu ikisini ayrı ayrı karşılaştırdığı için, "iptal"
    senaryosunun doğru barda gerçekleştiğini de kanıtlar.
    """

    meta = IndicatorMeta(
        name="test.swing_zigzag",
        version="0.1.0",
        category="testing",
        description="Faz 2 swings.py repaint kanıt sarmalayıcısı.",
        supported_timeframes=(Timeframe.D1, Timeframe.H4),
    )

    def __init__(self, params: SwingZigzagParams | None = None) -> None:
        self.params = params or SwingZigzagParams()

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        raw = find_pivots(df, self.params.left, self.params.right, self.params.eq_policy)
        zigzag = label_structure(alternate_pivots(raw, include_pending=False))

        signals = [
            Signal(
                bar_time=p.bar_time,
                detected_at=p.finalized_time,  # type: ignore[arg-type]
                direction="short" if p.kind == "high" else "long",
                state="confirmed",
                score=1.0,
                payload={"price": p.price, "label": p.label or ""},
            )
            for p in zigzag
        ]

        return IndicatorResult(
            indicator=self.meta.name,
            version=self.meta.version,
            params_hash=params_hash(self.params),
            symbol="TEST",
            timeframe=Timeframe.D1,
            signals=signals,
        )


def test_swing_zigzag_indicator_passes_repaint() -> None:
    pivots = [
        (0, 100.0), (15, 130.0), (30, 90.0), (45, 150.0),
        (60, 80.0), (75, 140.0), (90, 95.0), (105, 160.0),
    ]
    df = make_zigzag(pivots, noise=0.3, seed=21)
    report = repaint_test(SwingZigzagIndicator(), df, tail=40)
    assert report.passed, report.mismatches


@dataclass(frozen=True)
class FibRetracementParams(BaseParams):
    left: int = 3
    right: int = 3


class FibRetracementIndicator(BaseIndicator):
    """Ardışık her kesinleşmiş zigzag pivot çifti için fibonacci retracement
    seviyelerini Level olarak yayınlar. price/label/start üçlüsü, ikinci
    pivot kesinleştiği anda sabitlenir ve bir daha değişmez — repaint_test'in
    tam eşitlik kontrolü bunu sıkı şekilde doğrular."""

    meta = IndicatorMeta(
        name="test.fib_retracement",
        version="0.1.0",
        category="testing",
        description="Faz 2 fibonacci.py + swings.py repaint kanıt sarmalayıcısı.",
        supported_timeframes=(Timeframe.D1, Timeframe.H4),
    )

    def __init__(self, params: FibRetracementParams | None = None) -> None:
        self.params = params or FibRetracementParams()

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        raw = find_pivots(df, self.params.left, self.params.right)
        zigzag = alternate_pivots(raw, include_pending=False)

        levels: list[Level] = []
        for prev, curr in zip(zigzag, zigzag[1:], strict=False):
            fib = retracement(prev.price, curr.price)
            for r, price in fib.items():
                levels.append(
                    Level(price=price, label=f"fib_{r}_{prev.bar_idx}_{curr.bar_idx}",
                          style="dashed", start=curr.finalized_time)
                )

        return IndicatorResult(
            indicator=self.meta.name,
            version=self.meta.version,
            params_hash=params_hash(self.params),
            symbol="TEST",
            timeframe=Timeframe.D1,
            levels=levels,
        )


def test_fib_retracement_indicator_passes_repaint() -> None:
    pivots = [
        (0, 100.0), (15, 130.0), (30, 90.0), (45, 150.0),
        (60, 80.0), (75, 140.0), (90, 95.0), (105, 160.0),
    ]
    df = make_zigzag(pivots, noise=0.3, seed=21)
    report = repaint_test(FibRetracementIndicator(), df, tail=40)
    assert report.passed, report.mismatches
