"""tlab.features.ranges için birim testleri ve repaint (extend-only) testi."""

from __future__ import annotations

from dataclasses import dataclass
from zoneinfo import ZoneInfo

import pandas as pd

from tlab.core.indicator import BaseIndicator
from tlab.core.params import BaseParams, params_hash
from tlab.core.types import Box, IndicatorMeta, IndicatorResult, Timeframe
from tlab.features.ranges import detect_ranges
from tlab.testing.repaint import repaint_test

TZ = ZoneInfo("Europe/Istanbul")


def _build_range_scenario(n: int = 15) -> pd.DataFrame:
    """Bar 0-4: dar aralık (kutu adayı). 5-7: kutu içinde kalır (t1 uzar).
    8: kutu dışı (tek bar, onaylanmaz). 9: içeri döner. 10-11: kutu dışı,
    breakout_confirm=2 ile 11'de onaylanır (yön: up)."""
    idx = pd.date_range("2024-01-02 10:00", periods=n, freq="1D", tz=TZ)
    close = {t: 100.0 for t in range(8)}
    close[8] = 105.0
    close[9] = 100.0
    close[10] = 105.0
    close[11] = 106.0
    for t in range(12, n):
        close[t] = 106.0 + (t - 11)

    high = {t: close[t] + 1.0 for t in range(n)}
    low = {t: close[t] - 1.0 for t in range(n)}

    df = pd.DataFrame(
        {
            "open": [close[t] for t in range(n)],
            "high": [high[t] for t in range(n)],
            "low": [low[t] for t in range(n)],
            "close": [close[t] for t in range(n)],
            "volume": [1000.0] * n,
        },
        index=idx,
    )
    return df


def _params() -> dict:
    return {"min_bars": 5, "atr_mult": 1.5, "breakout_confirm": 2, "atr_period": 3}


# --- detect_ranges -------------------------------------------------------


def test_detect_ranges_finds_tight_window_and_bounds() -> None:
    df = _build_range_scenario()
    ranges = detect_ranges(df, **_params())
    box = next(r for r in ranges if r.t0_idx == 0)

    assert box.high == 101.0
    assert box.low == 99.0
    assert box.detected_idx == 5


def test_detect_ranges_t1_extends_through_single_bar_excursion() -> None:
    df = _build_range_scenario()
    ranges = detect_ranges(df, **_params())
    box = next(r for r in ranges if r.t0_idx == 0)

    assert box.t1_idx == 9  # tek barlık dış çıkış (8) onaylanmadı, 9'da içeri döndü


def test_detect_ranges_breakout_confirmed_after_streak() -> None:
    df = _build_range_scenario()
    ranges = detect_ranges(df, **_params())
    box = next(r for r in ranges if r.t0_idx == 0)

    assert box.breakout_idx == 11
    assert box.breakout_direction == "up"


def test_detect_ranges_insufficient_data_returns_empty() -> None:
    df = _build_range_scenario(n=15).iloc[:4]
    assert detect_ranges(df, min_bars=5) == []


def test_detect_ranges_bounds_never_change_across_truncation() -> None:
    df = _build_range_scenario()
    full = next(r for r in detect_ranges(df, **_params()) if r.t0_idx == 0)
    partial = next(r for r in detect_ranges(df.iloc[:9], **_params()) if r.t0_idx == 0)

    assert partial.high == full.high
    assert partial.low == full.low
    assert partial.detected_idx == full.detected_idx
    assert partial.t1_idx <= full.t1_idx  # yalnızca ileriye doğru büyüyebilir
    assert partial.breakout_idx is None  # bar 9'da henüz kırılım onaylanmadı


# --- mini-indikatör repaint testi (Box: extend-only) -----------------------


@dataclass(frozen=True)
class RangeParams(BaseParams):
    pass


class RangeIndicator(BaseIndicator):
    """detect_ranges'i Box olarak sarmalar — repaint_test'in extend-only
    kontrolü (t1 büyür, low/high sabit) doğrudan doğrulama sağlar."""

    meta = IndicatorMeta(
        name="test.range",
        version="0.1.0",
        category="testing",
        description="Faz 2 ranges.py repaint kanıt sarmalayıcısı.",
        supported_timeframes=(Timeframe.D1, Timeframe.H4),
    )

    def __init__(self) -> None:
        self.params = RangeParams()

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        ranges = detect_ranges(df, **_params())
        boxes = [
            Box(
                t0=r.t0_time, t1=r.t1_time, low=r.low, high=r.high,
                label=f"range_{r.t0_idx}", style="range",
            )
            for r in ranges
        ]
        return IndicatorResult(
            indicator=self.meta.name, version=self.meta.version,
            params_hash=params_hash(self.params), symbol="TEST", timeframe=Timeframe.D1,
            boxes=boxes,
        )


def test_range_indicator_passes_repaint() -> None:
    df = _build_range_scenario()
    all_ranges = detect_ranges(df, **_params())
    # Box, t0 (pencere başlangıcı) itibariyle "varmış gibi" filtrelenir ama
    # aslında detected_idx'te üretilir (bkz. trendlines.py'deki aynı bilinen
    # sınırlama) — güvenli kesim noktaları, TÜM kutuların zaten tespit
    # edildiği ilk bardan başlatılır.
    safe_start = max(r.detected_idx for r in all_ranges) + 1

    indicator = RangeIndicator()
    report = repaint_test(indicator, df, cut_points=list(range(safe_start, len(df) + 1)))
    assert report.passed, report.mismatches
