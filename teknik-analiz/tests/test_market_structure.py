"""tlab.features.market_structure için birim + prefix-tutarlılık testleri.

Senaryo elle inşa edilir (trendlines/zones_sd testleriyle AYNI desen):
close serisi 4 farklı kırılım türünü (BOS-yukarı, CHoCH-aşağı, BOS-aşağı,
CHoCH-yukarı) TEK bir zaman çizelgesinde, kesin barlarda tetikler."""

from __future__ import annotations

from zoneinfo import ZoneInfo

import pandas as pd

from tlab.features.market_structure import StructureEvent, detect_market_structure
from tlab.features.swings import Pivot

TZ = ZoneInfo("Europe/Istanbul")

N = 32


def _pivot(
    kind: str, price: float, bar_idx: int, confirmed_idx: int, idx: pd.DatetimeIndex,
) -> Pivot:
    return Pivot(
        bar_idx=bar_idx, bar_time=idx[bar_idx], price=price, kind=kind,  # type: ignore[arg-type]
        confirmed_idx=confirmed_idx, confirmed_time=idx[confirmed_idx],
    )


def _scenario() -> tuple[pd.DataFrame, list[Pivot]]:
    idx = pd.date_range("2024-01-02 10:00", periods=N, freq="1D", tz=TZ)
    close = {i: 100.0 for i in range(N)}
    close[15] = 115.0  # p1(high=110) kırılır -> BOS_up
    close[19] = 107.0
    close[20] = 107.0
    close[21] = 107.0
    close[22] = 100.0  # p4(low=105) kırılır -> CHoCH_down
    close[27] = 90.0  # p5(low=98) kırılır -> BOS_down
    close[30] = 125.0  # p3(high=120) kırılır -> CHoCH_up

    df = pd.DataFrame(
        {
            "open": [close[t] for t in range(N)],
            "high": [close[t] + 1.0 for t in range(N)],
            "low": [close[t] - 1.0 for t in range(N)],
            "close": [close[t] for t in range(N)],
            "volume": [1000.0] * N,
        },
        index=idx,
    )

    pivots = [
        _pivot("high", 110.0, 3, 6, idx),
        _pivot("low", 95.0, 8, 11, idx),
        _pivot("high", 120.0, 16, 18, idx),
        _pivot("low", 105.0, 17, 19, idx),
        _pivot("low", 98.0, 23, 24, idx),
    ]
    return df, pivots


def test_first_break_is_bos_not_choch() -> None:
    df, pivots = _scenario()
    events = detect_market_structure(df, pivots)
    assert events[0].kind == "bos_up"
    assert events[0].bar_idx == 15
    assert events[0].level == 110.0


def test_reversal_after_established_trend_is_choch() -> None:
    df, pivots = _scenario()
    events = detect_market_structure(df, pivots)
    choch_down = [e for e in events if e.kind == "choch_down"]
    assert len(choch_down) == 1
    assert choch_down[0].bar_idx == 22
    assert choch_down[0].level == 105.0


def test_continuation_in_established_trend_is_bos() -> None:
    df, pivots = _scenario()
    events = detect_market_structure(df, pivots)
    bos_down = [e for e in events if e.kind == "bos_down"]
    assert len(bos_down) == 1
    assert bos_down[0].bar_idx == 27
    assert bos_down[0].level == 98.0


def test_second_reversal_is_choch_up() -> None:
    df, pivots = _scenario()
    events = detect_market_structure(df, pivots)
    choch_up = [e for e in events if e.kind == "choch_up"]
    assert len(choch_up) == 1
    assert choch_up[0].bar_idx == 30
    assert choch_up[0].level == 120.0


def test_full_event_sequence() -> None:
    df, pivots = _scenario()
    events = detect_market_structure(df, pivots)
    assert [e.kind for e in events] == ["bos_up", "choch_down", "bos_down", "choch_up"]


def test_direction_and_is_bos_properties() -> None:
    ev = StructureEvent(
        kind="choch_up", bar_idx=0, bar_time=pd.Timestamp("2024-01-01"),
        level=1.0, source_pivot=_pivot("high", 1.0, 0, 0, pd.date_range("2024-01-01", periods=1)),
    )
    assert ev.direction == "up"
    assert ev.is_bos is False


def test_no_pivots_means_no_events() -> None:
    df, _ = _scenario()
    assert detect_market_structure(df, []) == []


def test_prefix_consistency_repaint() -> None:
    """Kesik df'lerde üretilen olaylar, tam df'nin AYNI barlardaki
    olaylarıyla birebir aynı olmalı (klasik repaint_test'in pivot-tabanlı
    saf fonksiyonlar için elle uygulanan hâli — bkz. trendlines.py/
    zones_sd.py'nin AYNI test deseni)."""
    df, pivots = _scenario()
    full_events = detect_market_structure(df, pivots)

    for cut in (16, 23, 28, N):
        partial_df = df.iloc[:cut]
        partial_pivots = [p for p in pivots if p.confirmed_idx < cut]
        partial_events = detect_market_structure(partial_df, partial_pivots)
        expected = [e for e in full_events if e.bar_idx < cut]
        assert partial_events == expected, f"cut={cut}"
