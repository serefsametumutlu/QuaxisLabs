"""tlab.features.zones_sd::find_pivot_zones / _cluster_pivot_zones için
birim testleri — pivot-çıpalı arz/talep bölgeleri (Faz 4d, `find_bases`/
`find_impulses`/`make_sd_zones`'a ALTERNATİF yöntem).

Sabit true-range (high-low=2.0, close=100 sabit) kullanılır ki ATR
warmup'tan hemen sonra TAM 2.0'da otursun (Wilder EMA'nın bir sabit seri
üzerindeki davranışı) — bölge yüksekliği/kümeleme toleransı elle
doğrulanabilsin."""

from __future__ import annotations

from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from tlab.features.swings import Pivot
from tlab.features.volatility import atr
from tlab.features.zones_sd import find_pivot_zones

TZ = ZoneInfo("Europe/Istanbul")
N = 20
ATR_PERIOD = 3


def _pivot(
    kind: str, price: float, bar_idx: int, confirmed_idx: int, idx: pd.DatetimeIndex,
) -> Pivot:
    return Pivot(
        bar_idx=bar_idx, bar_time=idx[bar_idx], price=price, kind=kind,  # type: ignore[arg-type]
        confirmed_idx=confirmed_idx, confirmed_time=idx[confirmed_idx],
    )


def _flat_df() -> pd.DataFrame:
    idx = pd.date_range("2024-01-02 10:00", periods=N, freq="1D", tz=TZ)
    return pd.DataFrame(
        {
            "open": [100.0] * N, "high": [101.0] * N, "low": [99.0] * N,
            "close": [100.0] * N, "volume": [1000.0] * N,
        },
        index=idx,
    )


def test_close_pivots_of_same_kind_merge_into_one_zone() -> None:
    df = _flat_df()
    idx = df.index
    demand_pivot = _pivot("low", 90.0, 3, 4, idx)
    supply_pivot_1 = _pivot("high", 110.0, 5, 6, idx)
    supply_pivot_2 = _pivot("high", 110.5, 10, 12, idx)  # gap 0.5 < cluster_atr*ATR(1.0)

    zones = find_pivot_zones(
        df, [demand_pivot, supply_pivot_1, supply_pivot_2],
        cluster_atr=0.5, atr_period=ATR_PERIOD,
    )

    supply = [z for z in zones if z.kind == "supply"]
    demand = [z for z in zones if z.kind == "demand"]
    assert len(supply) == 1
    assert len(demand) == 1

    merged = supply[0]
    assert merged.low == pytest.approx(108.0)
    assert merged.high == pytest.approx(110.5)
    assert merged.created_idx == 6  # kümedeki EN ERKEN pivot
    assert merged.base_bars == 2

    d = demand[0]
    assert d.low == pytest.approx(90.0)
    assert d.high == pytest.approx(92.0)
    assert d.created_idx == 4


def test_far_apart_pivots_of_same_kind_stay_separate() -> None:
    df = _flat_df()
    idx = df.index
    supply_pivot_1 = _pivot("high", 110.0, 5, 6, idx)
    supply_pivot_2 = _pivot("high", 130.0, 10, 12, idx)  # çok uzak, birleşmemeli

    zones = find_pivot_zones(
        df, [supply_pivot_1, supply_pivot_2], cluster_atr=0.5, atr_period=ATR_PERIOD,
    )
    assert len(zones) == 2
    assert {round(z.high, 1) for z in zones} == {110.0, 130.0}


def test_supply_zone_sits_below_pivot_high_demand_above_pivot_low() -> None:
    """Çıpa: swing HIGH -> supply (dış kenar = pivot fiyatı, İÇ KENAR
    aşağıda); swing LOW -> demand (dış kenar = pivot fiyatı, iç kenar
    yukarıda)."""
    df = _flat_df()
    idx = df.index
    high_pivot = _pivot("high", 110.0, 5, 6, idx)
    low_pivot = _pivot("low", 90.0, 8, 9, idx)

    zones = find_pivot_zones(df, [low_pivot, high_pivot], atr_period=ATR_PERIOD)
    supply = next(z for z in zones if z.kind == "supply")
    demand = next(z for z in zones if z.kind == "demand")

    assert supply.high == pytest.approx(110.0)
    assert supply.low < supply.high
    assert demand.low == pytest.approx(90.0)
    assert demand.high > demand.low


def test_zone_height_is_capped_at_height_cap_atr() -> None:
    df = _flat_df()
    idx = df.index
    # ctx_bars penceresindeki avg_range sabit 2.0 (ATR de 2.0) -- height_cap_atr
    # düşürülünce bölge yüksekliği o tavana KELEPÇELENMELİ.
    high_pivot = _pivot("high", 110.0, 5, 6, idx)
    zones = find_pivot_zones(
        df, [high_pivot], height_cap_atr=0.5, atr_period=ATR_PERIOD,
    )
    assert zones[0].high - zones[0].low == pytest.approx(1.0)  # 0.5 * ATR(2.0)


def _regime_change_df() -> pd.DataFrame:
    """İlk 15 bar YÜKSEK volatilite (high-low=20), son 15 bar DÜŞÜK
    volatilite (high-low=2) -- ATR(period=3) 15 düşük-vol bardan sonra
    ~2.0'a yakınsar (Wilder EMA, alpha=1/3, (2/3)^15≈0.002)."""
    n = 30
    idx = pd.date_range("2024-01-02 10:00", periods=n, freq="1D", tz=TZ)
    high = [120.0] * 15 + [101.0] * 15
    low = [100.0] * 15 + [99.0] * 15
    return pd.DataFrame(
        {"open": 100.0, "high": high, "low": low, "close": 100.0, "volume": 1000.0}, index=idx,
    )


def test_height_cap_uses_current_atr_not_historical_atr_at_pivot_time() -> None:
    """GERÇEK hata (2026-09-05, INTEM 4H kullanıcı geri bildirimi): eskiden
    tavan HER pivotun KENDİ (tarihsel) ATR'sine göre değerlendiriliyordu --
    yüksek volatiliteli bir dönemde doğan iki pivot, O DÖNEMİN geniş
    ATR'sine göre kolayca birleşip dev bir bölge üretebiliyordu, ama
    GÜNÜMÜZÜN (df'in son barındaki) çok daha düşük ATR'sine göre bu
    aynı bölge orantısız kalın kalıyordu. Artık tavan HER ZAMAN güncel
    ATR'ye göre -- bu iki pivot ARTIK BİRLEŞMEMELİ (kümeleme toleransı da
    güncel ATR'ye göre daraldı) ve HER BİRİNİN yüksekliği güncel ATR'ye
    göre kelepçelenmeli."""
    df = _regime_change_df()
    idx = df.index
    # İkisi de YÜKSEK volatilite döneminde (bar 3, 8) doğan, fiyatça 10
    # puan ayrı iki HIGH pivot -- eski (tarihsel ATR~20) mantıkla kolayca
    # birleşirdi (tol=0.5*20=10 >= gap), yeni (güncel ATR~2) mantıkla
    # birleşmemeli (tol=0.5*2=1.0 < gap).
    p1 = _pivot("high", 110.0, 3, 4, idx)
    p2 = _pivot("high", 120.0, 8, 9, idx)

    zones = find_pivot_zones(
        df, [p1, p2], cluster_atr=0.5, height_cap_atr=2.75, atr_period=3,
    )
    supply = [z for z in zones if z.kind == "supply"]
    assert len(supply) == 2, "yüksek-tarihsel-ATR ile birleşmemeli"

    current_atr = float(atr(df, 3).iloc[-1])
    assert current_atr < 5.0, "test varsayımı: ATR düşük-vol rejimine yakınsamış olmalı"
    for z in supply:
        assert (z.high - z.low) == pytest.approx(2.75 * current_atr, abs=1e-6)


def test_pivots_before_atr_warmup_are_skipped() -> None:
    df = _flat_df()
    idx = df.index
    too_early = _pivot("high", 110.0, 0, 1, idx)  # confirmed_idx < atr_period(3) -> NaN ATR
    zones = find_pivot_zones(df, [too_early], atr_period=ATR_PERIOD)
    assert zones == []
