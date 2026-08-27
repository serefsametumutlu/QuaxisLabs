"""tlab.features.zones için birim testleri ve repaint (extend-only) testi."""

from __future__ import annotations

from dataclasses import dataclass
from zoneinfo import ZoneInfo

import pandas as pd

from tlab.core.indicator import BaseIndicator
from tlab.core.params import BaseParams, params_hash
from tlab.core.types import Box, IndicatorMeta, IndicatorResult, Timeframe
from tlab.features.swings import Pivot
from tlab.features.zones import cluster_zones
from tlab.testing.repaint import repaint_test

TZ = ZoneInfo("Europe/Istanbul")


def _build_zone_scenario(n: int = 25) -> pd.DataFrame:
    """t=0-11: düz taban (ATR≈2 stabilize olsun). t=12-13: bölge içi
    (temas). t=14: dışarı (tek bar, onaylanmaz). t=15: içeri döner.
    t=16-17: dışarı, breakout_confirm=2 ile t=17'de onaylanır (yön: up)."""
    idx = pd.date_range("2024-01-02 10:00", periods=n, freq="1D", tz=TZ)
    close = {t: 90.0 for t in range(12)}
    close.update({12: 100.5, 13: 100.0, 14: 105.0, 15: 100.5, 16: 105.0, 17: 106.0})
    for t in range(18, n):
        close[t] = 106.0 + (t - 17)

    high = {t: close[t] + 1.0 for t in range(n)}
    low = {t: close[t] - 1.0 for t in range(n)}

    return pd.DataFrame(
        {
            "open": [close[t] for t in range(n)],
            "high": [high[t] for t in range(n)],
            "low": [low[t] for t in range(n)],
            "close": [close[t] for t in range(n)],
            "volume": [1000.0] * n,
        },
        index=idx,
    )


def _mk_pivot(bar_idx: int, price: float, confirmed_idx: int, idx: pd.DatetimeIndex) -> Pivot:
    return Pivot(
        bar_idx=bar_idx, bar_time=idx[bar_idx], price=price, kind="high",
        confirmed_idx=confirmed_idx, confirmed_time=idx[confirmed_idx],
    )


def _scenario_pivots(idx: pd.DatetimeIndex) -> list[Pivot]:
    return [
        _mk_pivot(5, 100.0, 7, idx),
        _mk_pivot(10, 101.0, 12, idx),  # 100 ile kümelenir -> min_pivots=2, bölge t=12'de doğar
        _mk_pivot(20, 150.0, 22, idx),  # uzak, ayrı (tek üyeli, hiç olgunlaşmayan) küme
    ]


def _kwargs() -> dict:
    return {"min_pivots": 2, "atr_mult": 1.0, "breakout_confirm": 2, "atr_period": 3}


# --- cluster_zones -------------------------------------------------------


def test_cluster_zones_forms_at_kth_pivot_with_correct_center() -> None:
    df = _build_zone_scenario()
    pivots = _scenario_pivots(df.index)
    zones = cluster_zones(df, pivots, **_kwargs())

    assert len(zones) == 1
    z = zones[0]
    assert z.center == 100.5  # (100+101)/2
    assert z.formed_idx == 12  # ikinci pivotun (101) confirmed_idx'i
    assert z.member_bar_idxs == (5, 10)


def test_cluster_zones_far_pivot_never_reaches_min_pivots() -> None:
    df = _build_zone_scenario()
    pivots = _scenario_pivots(df.index)
    zones = cluster_zones(df, pivots, **_kwargs())
    assert all(150.0 not in (z.center,) for z in zones)  # 150'lik tek üyeli küme hiç olgunlaşmadı


def test_cluster_zones_touches_and_breakout() -> None:
    df = _build_zone_scenario()
    pivots = _scenario_pivots(df.index)
    z = cluster_zones(df, pivots, **_kwargs())[0]

    assert z.touches == (12, 13, 15)
    assert z.broken_at == 17
    assert z.broken_direction == "up"


def test_cluster_zones_insufficient_min_pivots_yields_no_zone() -> None:
    df = _build_zone_scenario()
    pivots = _scenario_pivots(df.index)
    zones = cluster_zones(df, pivots, min_pivots=3, atr_mult=1.0, breakout_confirm=2, atr_period=3)
    assert zones == []


# --- prefix-tutarlılık (repaint-safety) ------------------------------------


def test_zone_bounds_and_touches_prefix_consistent_across_truncation() -> None:
    df = _build_zone_scenario()
    pivots = _scenario_pivots(df.index)
    full = cluster_zones(df, pivots, **_kwargs())[0]

    partial = cluster_zones(df.iloc[:15], pivots, **_kwargs())[0]
    assert partial.center == full.center
    assert partial.thickness == full.thickness
    assert partial.formed_idx == full.formed_idx
    assert partial.touches == tuple(t for t in full.touches if t < 15)
    assert partial.broken_at is None  # t=17'ye henüz ulaşılmadı


# --- mini-indikatör repaint testi (Box: extend-only) -----------------------


@dataclass(frozen=True)
class ZoneParams(BaseParams):
    pass


class ZoneIndicator(BaseIndicator):
    """cluster_zones'u Box olarak sarmalar — repaint_test'in extend-only
    kontrolü (t1 büyür, low/high sabit) doğrudan doğrulama sağlar."""

    meta = IndicatorMeta(
        name="test.zone",
        version="0.1.0",
        category="testing",
        description="Faz 2 zones.py repaint kanıt sarmalayıcısı.",
        supported_timeframes=(Timeframe.D1, Timeframe.H4),
    )

    def __init__(self, pivots: list[Pivot]) -> None:
        self.params = ZoneParams()
        self._pivots = pivots

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        zones = cluster_zones(df, self._pivots, **_kwargs())
        boxes = [
            Box(
                t0=z.formed_time,
                t1=df.index[z.touches[-1]] if z.touches else z.formed_time,
                low=z.low, high=z.high,
                label=f"zone_{z.formed_idx}", style="zone",
            )
            for z in zones
        ]
        return IndicatorResult(
            indicator=self.meta.name, version=self.meta.version,
            params_hash=params_hash(self.params), symbol="TEST", timeframe=Timeframe.D1,
            boxes=boxes,
        )


def test_zone_indicator_passes_repaint() -> None:
    df = _build_zone_scenario()
    pivots = _scenario_pivots(df.index)
    all_zones = cluster_zones(df, pivots, **_kwargs())
    safe_start = max(z.formed_idx for z in all_zones) + 1

    indicator = ZoneIndicator(pivots)
    report = repaint_test(indicator, df, cut_points=list(range(safe_start, len(df) + 1)))
    assert report.passed, report.mismatches
