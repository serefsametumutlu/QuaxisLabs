"""Harmonik testleri için paylaşılan yardımcılar."""

from __future__ import annotations

from zoneinfo import ZoneInfo

import pandas as pd

from tlab.features.fibonacci import ratio
from tlab.features.swings import Pivot
from tlab.indicators.harmonics.geometry import Candidate

TZ = ZoneInfo("Europe/Istanbul")


def _seg(v0: float, v1: float, steps: int) -> list[float]:
    return [v0 + (v1 - v0) * k / steps for k in range(steps)]


def build_gartley_ohlcv() -> pd.DataFrame:
    """Gerçek find_pivots/generate_candidates zincirinden geçen, doğrulanmış
    bir bull Gartley (Carney/Pesavento/Gilmore ortak) OHLCV serisi.

    X=100@bar5, A=120@bar10, B=107.64@bar15, C=116.64@bar20 (wick offset
    ±1.5 hesaba katılarak close değerleri seçildi — bkz. session notları).
    PRZ [103.68,104.88]'e bar24-28 arası temas eder (ACTIVE, born_idx=28'de
    aynı bara denk gelir), bar30'da kapanış PRZ üstüne çıkar (CONFIRMED,
    close_reversal + reversal_bars=1)."""
    close: list[float] = []
    close += _seg(151.5, 101.5, 5)
    close += _seg(101.5, 118.5, 5)
    close += _seg(118.5, 109.14, 5)
    close += _seg(109.14, 115.14, 5)
    close += _seg(115.14, 105.0, 4)
    close += [104.5, 104.28, 104.0, 104.28, 104.5]
    close += _seg(104.5, 130.0, 6)
    close += [130.0] * 3

    n = len(close)
    idx = pd.date_range("2024-01-02 00:00", periods=n, freq="4h", tz=TZ)
    high = [c + 1.5 for c in close]
    low = [c - 1.5 for c in close]
    return pd.DataFrame(
        {"open": close, "high": high, "low": low, "close": close, "volume": [1000.0] * n},
        index=idx,
    )


def _pivot(bar_idx: int, price: float, kind: str, finalized_at: int) -> Pivot:
    idx = pd.date_range("2024-01-02 00:00", periods=finalized_at + 1, freq="4h", tz=TZ)
    return Pivot(
        bar_idx=bar_idx, bar_time=idx[bar_idx], price=price, kind=kind,
        confirmed_idx=bar_idx + 1, confirmed_time=idx[min(bar_idx + 1, finalized_at)],
        finalized_idx=finalized_at, finalized_time=idx[finalized_at],
    )


def make_candidate(
    x: float, a: float, b: float, c: float, *, zero: float | None = None,
    bar_gap: int = 5, direction: str | None = None,
) -> Candidate:
    """Yalnızca fiyatlardan (X,A,B,C, opsiyonel 0) bar_idx'leri otomatik
    atanmış bir Candidate kurar — schools.match() testleri için tam
    OHLCV/zigzag kurmaya gerek bırakmaz."""
    has_zero = zero is not None
    z_idx, x_idx, a_idx, b_idx, c_idx = (
        [0, bar_gap, 2 * bar_gap, 3 * bar_gap, 4 * bar_gap] if has_zero
        else [None, 0, bar_gap, 2 * bar_gap, 3 * bar_gap]
    )
    finalized_at = c_idx + 1

    x_kind = "low" if a > x else "high"
    a_kind = "high" if x_kind == "low" else "low"
    b_kind = x_kind
    c_kind = a_kind

    zero_pivot = _pivot(z_idx, zero, a_kind, finalized_at) if has_zero else None
    x_pivot = _pivot(x_idx, x, x_kind, finalized_at)
    a_pivot = _pivot(a_idx, a, a_kind, finalized_at)
    b_pivot = _pivot(b_idx, b, b_kind, finalized_at)
    c_pivot = _pivot(c_idx, c, c_kind, finalized_at)

    inferred_direction = direction or ("bullish" if x_kind == "low" else "bearish")

    def _more_extreme(ref: Pivot, new: Pivot) -> bool:
        return new.price > ref.price if new.kind == "high" else new.price < ref.price

    return Candidate(
        pattern_id=f"test_{x_idx}_{a_idx}_{b_idx}_{c_idx}",
        zero=zero_pivot, x=x_pivot, a=a_pivot, b=b_pivot, c=c_pivot,
        direction=inferred_direction,
        ab_xa=ratio(x, a, b), bc_ab=ratio(a, b, c),
        c_beyond_a=_more_extreme(a_pivot, c_pivot), b_beyond_x=_more_extreme(x_pivot, b_pivot),
        bars_xa=a_idx - x_idx, bars_ab=b_idx - a_idx, bars_bc=c_idx - b_idx,
        born_idx=c_pivot.finalized_idx, born_time=c_pivot.finalized_time,
        gap_after_c=False, wide_bar_at_c=False, fast_cd_formation=False,
    )
