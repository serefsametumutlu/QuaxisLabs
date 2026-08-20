"""src.analysis.order_block_zones testleri -- sentetik DataFrame'ler,
gercek ag/dosya I/O YOK."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.order_block_zones import (
    Params,
    _find_bullish_order_blocks,
    nearest_unmitigated_zone,
    zone_state_at,
)


def _df(open_: list[float], high: list[float], low: list[float], close: list[float], volume: list[float] | None = None) -> pd.DataFrame:
    n = len(close)
    return pd.DataFrame(
        {
            "time": pd.date_range("2020-01-01", periods=n, freq="1D", tz="UTC"),
            "open": open_, "high": high, "low": low, "close": close,
            "volume": volume if volume is not None else [1_000_000.0] * n,
        }
    )


def _flat_base_then_displacement(base_len: int = 6, base_price: float = 100.0, n_lead: int = 60) -> pd.DataFrame:
    """Isinma (ATR hesabi icin duz-ama-hafif-oynak fiyat) + sikisik bir taban
    + guclu bir yukselen yer-degistirme mumu -- Order Block tespiti icin
    minimal gecerli senaryo."""
    rng = np.random.RandomState(3)
    lead_close = base_price + np.cumsum(rng.normal(0, 0.3, n_lead))
    lead_open = lead_close + rng.normal(0, 0.1, n_lead)
    lead_high = np.maximum(lead_open, lead_close) + 0.3
    lead_low = np.minimum(lead_open, lead_close) - 0.3

    # kirmizi (dusen) koken mumu -- taban SONUNDA
    base_close = np.full(base_len, base_price)
    base_open = base_price + 0.2  # kirmizi: close<open (SON bar taban+koken)
    base_high = base_close + 0.5
    base_low = base_close - 0.5
    base_open_arr = np.full(base_len, base_price + 0.1)

    # guclu yukselen yer-degistirme -- buyuk govde, kapanis tabanin cok ustunde
    disp_open = base_price
    disp_close = base_price + 15.0  # buyuk govde
    disp_high = disp_close + 0.2
    disp_low = disp_open - 0.2

    open_ = np.concatenate([lead_open, base_open_arr, [disp_open]])
    high = np.concatenate([lead_high, base_high, [disp_high]])
    low = np.concatenate([lead_low, base_low, [disp_low]])
    close = np.concatenate([lead_close, base_close, [disp_close]])
    return _df(open_.tolist(), high.tolist(), low.tolist(), close.tolist())


def test_gecerli_senaryoda_order_block_tespit_edilir():
    df = _flat_base_then_displacement()
    zones = _find_bullish_order_blocks(df)
    assert len(zones) > 0
    z = zones[0]
    assert z.zone_low < z.zone_high
    assert z.quality >= 0


def test_zone_state_olusumdan_once_unmitigated():
    df = _flat_base_then_displacement()
    zones = _find_bullish_order_blocks(df)
    assert zones
    z = zones[0]
    close = df["close"].to_numpy(dtype=float)
    assert zone_state_at(z, close, z.displacement_bar - 1) == "UNMITIGATED"


def test_zone_state_kapanis_icinden_geçince_mitigated():
    close = np.array([100.0, 100.0, 100.0, 120.0, 130.0, 90.0])  # bar5 kapanis zone_low'un ALTINDA
    from src.analysis.order_block_zones import OrderBlockZone

    zone = OrderBlockZone(origin_bar=1, displacement_bar=3, zone_low=95.0, zone_high=101.0, quality=50, has_fvg=False, base_bars=5)
    assert zone_state_at(zone, close, 5) == "MITIGATED"


def test_zone_state_kapanis_icinde_kalinca_tested():
    close = np.array([100.0, 100.0, 100.0, 120.0, 130.0, 98.0])  # bar5 kapanis [95,101] ICINDE
    from src.analysis.order_block_zones import OrderBlockZone

    zone = OrderBlockZone(origin_bar=1, displacement_bar=3, zone_low=95.0, zone_high=101.0, quality=50, has_fvg=False, base_bars=5)
    assert zone_state_at(zone, close, 5) == "TESTED"


def test_nearest_unmitigated_zone_dusuk_kaliteyi_eler():
    from src.analysis.order_block_zones import OrderBlockZone

    close = np.full(20, 100.0)
    low_quality = OrderBlockZone(origin_bar=1, displacement_bar=3, zone_low=99.0, zone_high=101.0, quality=10, has_fvg=False, base_bars=5)
    result = nearest_unmitigated_zone([low_quality], close, as_of_bar=10, price=100.0, atr_val=1.0, min_quality=50)
    assert result is None


def test_nearest_unmitigated_zone_yeterli_kalitede_bulunur():
    from src.analysis.order_block_zones import OrderBlockZone

    # Fiyat yer-degistirmeden (bar3) SONRA hep 105'te kalir -- zone [99,101]
    # DISINDA, HICBIR zaman dokunulmaz (gercekten UNMITIGATED kalir).
    close = np.array([100.0, 99.5, 100.0, 105.0] + [105.0] * 16)
    zone = OrderBlockZone(origin_bar=1, displacement_bar=3, zone_low=99.0, zone_high=101.0, quality=60, has_fvg=False, base_bars=5)
    result = nearest_unmitigated_zone([zone], close, as_of_bar=10, price=105.0, atr_val=1.0, min_quality=50)
    assert result is not None
    found_zone, dist_atr = result
    assert found_zone is zone
    assert dist_atr == 4.0  # 105 - 101 = 4, /ATR(1.0) = 4


def test_henuz_olusmamis_bolge_dislanir():
    from src.analysis.order_block_zones import OrderBlockZone

    close = np.full(20, 100.0)
    zone = OrderBlockZone(origin_bar=15, displacement_bar=18, zone_low=99.0, zone_high=101.0, quality=90, has_fvg=False, base_bars=5)
    result = nearest_unmitigated_zone([zone], close, as_of_bar=5, price=100.0, atr_val=1.0, min_quality=50)
    assert result is None


def test_duz_seride_yer_degistirme_yok_bos_liste():
    df = _df([100.0] * 60, [100.5] * 60, [99.5] * 60, [100.0] * 60)
    assert _find_bullish_order_blocks(df) == []
