"""src.analysis.wavelet_trend_rider testleri -- sentetik DataFrame'ler,
gercek ag/dosya I/O YOK (bkz. test_momentum_confluence.py ile AYNI ilke)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.analysis.wavelet_trend_rider import Params, _daily_series_aligned, _wavelet_denoise, detect


def _ohlcv_4h(close: np.ndarray, start: str = "2024-01-01") -> pd.DataFrame:
    n = len(close)
    high = close + 0.5
    low = close - 0.5
    return pd.DataFrame(
        {
            "time": pd.date_range(start, periods=n, freq="4h", tz="UTC"),
            "open": close,
            "high": high,
            "low": low,
            "close": close,
            "volume": np.full(n, 1000.0),
        }
    )


def _ohlcv_1d(close: np.ndarray, start: str = "2024-01-01") -> pd.DataFrame:
    n = len(close)
    return pd.DataFrame(
        {
            "time": pd.date_range(start, periods=n, freq="1D", tz="UTC"),
            "open": close,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": np.full(n, 1000.0),
        }
    )


def test_wavelet_denoise_kisa_seride_cokmez_aynen_doner():
    prices = np.array([10.0, 11.0, 10.5])
    out = _wavelet_denoise(prices, wavelet="db8", level=4, mode="soft")
    assert np.allclose(out, prices)


def test_daily_series_aligned_ayni_gunu_asla_gormez():
    daily_times = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]).tz_localize("UTC")
    daily_df = pd.DataFrame({"time": daily_times})
    daily_values = np.array([100.0, 200.0, 300.0])

    # 2024-01-02 09:00 -- AYNI gunun (01-02) barindan ONCE, gorebilecegi
    # TEK gunluk deger 01-01'in degeri (100.0) olmali, 01-02'nin (200.0) DEGIL.
    bar_times = pd.Series(pd.to_datetime(["2024-01-02 09:00"]).tz_localize("UTC"))
    out = _daily_series_aligned(bar_times, daily_df, daily_values)
    assert out[0] == 100.0


def test_daily_series_aligned_ilk_gunden_once_nan():
    daily_times = pd.to_datetime(["2024-01-05"]).tz_localize("UTC")
    daily_df = pd.DataFrame({"time": daily_times})
    daily_values = np.array([100.0])
    bar_times = pd.Series(pd.to_datetime(["2024-01-01 09:00"]).tz_localize("UTC"))
    out = _daily_series_aligned(bar_times, daily_df, daily_values)
    assert np.isnan(out[0])


def test_yetersiz_veri_bos_liste_doner():
    df = _ohlcv_4h(np.full(10, 100.0))
    df_daily = _ohlcv_1d(np.full(5, 100.0))
    assert detect(df, df_daily) == []


def test_gurultulu_yukselen_trendde_long_sinyali_uretilir():
    # Duz/kesintisiz bir ustel yukselis RSI'yi ~100'de doyurup rsi_upper (70)
    # filtresini HER ZAMAN reddeder (gercekci DEGIL) -- gercekci gurultulu
    # bir surukleme+oynaklik serisi kullanilir (RSI zaman zaman <70'e doner).
    rng = np.random.RandomState(42)
    n = 500
    rets_4h = rng.normal(0.0015, 0.012, n)
    close_4h = 100.0 * np.cumprod(1 + rets_4h)
    df = _ohlcv_4h(close_4h)

    n_1d = 250
    rets_1d = rng.normal(0.0015, 0.012, n_1d)
    close_1d = 100.0 * np.cumprod(1 + rets_1d)
    df_daily = _ohlcv_1d(close_1d)

    signals = detect(df, df_daily, Params())
    assert len(signals) > 0
    sig = signals[-1]
    assert sig.direction == 1
    assert sig.sl < sig.entry_ref < sig.tp1 < sig.tp2
    assert sig.adx > Params().adx_threshold


def test_duz_yatay_seride_sinyal_uretilmez():
    n = 300
    close_4h = np.full(n, 100.0) + np.random.RandomState(0).normal(0, 0.01, n)
    df = _ohlcv_4h(close_4h)
    df_daily = _ohlcv_1d(np.full(150, 100.0))
    signals = detect(df, df_daily, Params())
    assert signals == []
