"""tlab.scanner.confluence — birim testleri (elle inşa edilmiş kaynak
IndicatorResult'larla, gerçek alt-indikatör hesabından BAĞIMSIZ) +
`tests/test_scanner/test_engine_and_results.py`'nin AYNI "önbellek varsa"
deseniyle gerçek veri smoke testi."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tlab.core.types import Box, IndicatorResult, Level, Line, Timeframe
from tlab.scanner.confluence import ConfluenceParams, _freshness, build_reversal_map

_TZ = "Europe/Istanbul"


def _ohlcv(close: np.ndarray, index: pd.DatetimeIndex) -> pd.DataFrame:
    open_ = np.roll(close, 1)
    open_[0] = close[0]
    high = np.maximum(open_, close) + 0.5
    low = np.minimum(open_, close) - 0.5
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": 1000.0}, index=index
    )


def _fake_result(
    boxes: list[Box] | None = None, levels: list[Level] | None = None,
    lines: list[Line] | None = None, last_state: dict | None = None,
    indicator: str = "structure.supply_demand", timeframe: Timeframe = Timeframe.D1,
) -> IndicatorResult:
    return IndicatorResult(
        indicator=indicator, version="0.1.0", params_hash="h", symbol="TEST",
        timeframe=timeframe, boxes=boxes or [], levels=levels or [], lines=lines or [],
        last_state=last_state or {},
    )


def _make_dipping_series() -> pd.DataFrame:
    """Düşüp sonra dönen, NET bir swing low + onu FİNALİZE eden bir swing
    high içeren seri (left/right=3 ile kesin onaylanır — `alternate_pivots`
    zıt türde bir SONRAKİ pivot olmadan bir pivotu `finalized_idx` ile
    işaretlemez, bkz. swings.py docstring'i)."""
    down = np.linspace(120, 100, 40)
    up = np.linspace(100.5, 130, 55)  # tam bir bar farkla ayrık minimum (düz dip DEĞİL)
    pullback = np.linspace(129, 125, 15)  # low pivotu FİNALİZE eden bir high yaratır
    close = np.concatenate([down, up, pullback])
    idx = pd.date_range("2024-01-01", periods=len(close), freq="D", tz=_TZ)
    return _ohlcv(close, idx)


def test_freshness_decays_exponentially() -> None:
    now = pd.Timestamp("2024-06-01", tz=_TZ)
    born_now = now
    born_old = now - pd.Timedelta(days=45)  # tam bir yarı-ömür
    assert _freshness(born_now, now, 45.0) == pytest.approx(1.0)
    assert _freshness(born_old, now, 45.0) == pytest.approx(0.5, rel=1e-6)


def test_build_reversal_map_finds_support_candidate_below_close() -> None:
    df = _make_dipping_series()
    close = float(df["close"].iloc[-1])
    born = df.index[10]

    # Kapanışın ALTINDA bir "demand" bölgesi -> aday olmalı.
    below_box = Box(
        t0=born, t1=df.index[-1], low=close - 20, high=close - 15, label="DEMAND", style="demand"
    )
    # Kapanışın ÜSTÜNDE bir "demand" bölgesi -> ELENMELİ (destek-only kapsam).
    above_box = Box(
        t0=born, t1=df.index[-1], low=close + 5, high=close + 10, label="DEMAND", style="demand"
    )
    sd_result = _fake_result(boxes=[below_box, above_box])

    result = build_reversal_map(
        "TEST", "1D", df, {"structure.supply_demand": sd_result}, ConfluenceParams()
    )

    assert result.indicator == "confluence"
    assert result.last_state["n_candidates"] == 1
    assert len(result.boxes) == 1
    assert result.boxes[0].high <= close


def test_broken_supply_demand_zone_excluded() -> None:
    df = _make_dipping_series()
    close = float(df["close"].iloc[-1])
    born = df.index[10]
    broken_box = Box(
        t0=born, t1=df.index[-1], low=close - 10, high=close - 5,
        label="DEMAND (kırık)", style="demand_broken",
    )
    sd_result = _fake_result(boxes=[broken_box])
    result = build_reversal_map(
        "TEST", "1D", df, {"structure.supply_demand": sd_result}, ConfluenceParams()
    )
    assert result.last_state["n_candidates"] == 0


def test_harmonic_invalidated_prz_excluded() -> None:
    df = _make_dipping_series()
    close = float(df["close"].iloc[-1])
    lo, hi = close - 10, close - 5
    levels = [
        Level(price=lo, label="p1_prz_low", style="dotted"),
        Level(price=hi, label="p1_prz_high", style="dotted"),
    ]
    invalid_result = _fake_result(
        levels=levels, last_state={"p1": {"state": "invalidated"}}, indicator="harmonic.pesavento",
    )
    result = build_reversal_map(
        "TEST", "1D", df, {"harmonic.pesavento": invalid_result}, ConfluenceParams()
    )
    assert result.last_state["n_candidates"] == 0

    active_result = _fake_result(
        levels=levels, last_state={"p1": {"state": "active"}}, indicator="harmonic.pesavento",
    )
    result2 = build_reversal_map(
        "TEST", "1D", df, {"harmonic.pesavento": active_result}, ConfluenceParams()
    )
    assert result2.last_state["n_candidates"] == 1


def test_zones_weight_sum_matches_series_density_at_overlap() -> None:
    """Aynı bucket'ı kapsayan İKİ kaynağın ağırlıkları TOPLANMALI (yoğunluk
    profili basit bir katkı toplamıdır)."""
    df = _make_dipping_series()
    close = float(df["close"].iloc[-1])
    born = df.index[10]
    box1 = Box(
        t0=born, t1=df.index[-1], low=close - 6, high=close - 4, label="A", style="demand"
    )
    box2 = Box(
        t0=born, t1=df.index[-1], low=close - 6, high=close - 4, label="B", style="golden_zone"
    )
    result = build_reversal_map(
        "TEST", "1D", df,
        {"structure.supply_demand": _fake_result(boxes=[box1]),
         "structure.golden_zone": _fake_result(boxes=[box2], indicator="structure.golden_zone")},
        ConfluenceParams(),
    )
    zones = result.last_state["zones"]
    assert len(zones) == 2
    total_weight = sum(z["weight"] for z in zones)
    vp_volumes = result.series["vp_volumes"]
    # -6..-4 aralığındaki bucket'ların en yüksek yoğunluğu, iki kaynağın
    # toplam ağırlığından BÜYÜK olamaz (üst sınır — her bucket en fazla
    # kesişen kaynakların toplamını alır).
    assert vp_volumes.max() <= total_weight + 1e-9
    assert vp_volumes.max() > 0


def test_last_confirmed_swing_low_detects_known_dip() -> None:
    df = _make_dipping_series()
    result = build_reversal_map("TEST", "1D", df, {}, ConfluenceParams(swing_left=3, swing_right=3))
    assert result.last_state["swing_low_price"] is not None
    # Bilinen dip ~100 civarında (bar 40, close=100.0'a yakın).
    assert abs(result.last_state["swing_low_price"] - 100.0) < 2.0


_SMALL_UNIVERSE = ["TCELL", "ISCTR"]


def _has_cache() -> bool:
    from tlab.core.types import Market
    from tlab.data.providers.yfinance_provider import YFinanceProvider
    from tlab.data.store import Store

    store = Store(YFinanceProvider())
    try:
        for sym in _SMALL_UNIVERSE:
            store.get(sym, Timeframe.D1, Market.BIST)
        return True
    except FileNotFoundError:
        return False


@pytest.mark.skipif(not _has_cache(), reason="TCELL/ISCTR 1D önbelleği yok")
def test_build_reversal_map_end_to_end_with_real_indicators() -> None:
    from tlab.core.types import Market
    from tlab.data.providers.yfinance_provider import YFinanceProvider
    from tlab.data.store import Store
    from tlab.indicators.bootstrap import CATALOG

    store = Store(YFinanceProvider())
    symbol = "TCELL"
    df = store.get(symbol, Timeframe.D1, Market.BIST)

    sources = {}
    for name in ["structure.supply_demand", "structure.golden_zone", "structure.price_structure"]:
        instance = CATALOG[name].factory()
        r = instance(df)
        r.symbol = symbol
        sources[name] = r

    result = build_reversal_map(symbol, "1D", df, sources, ConfluenceParams())
    assert result.indicator == "confluence"
    assert 0.0 <= result.last_state["bottom_probability"] <= 1.0
    assert "vp_bins" in result.series and "vp_volumes" in result.series
