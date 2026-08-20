"""src.analysis.wavelet_trend_rider_variants testleri -- sentetik
DataFrame'ler, gercek ag/dosya I/O YOK."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.wavelet_trend_rider import Params, detect
from src.analysis.wavelet_trend_rider_variants import VariantFlags, detect_variant


def _ohlcv_4h(close: np.ndarray, open_: np.ndarray | None = None, volume: np.ndarray | None = None, start: str = "2024-01-01") -> pd.DataFrame:
    n = len(close)
    o = open_ if open_ is not None else close
    return pd.DataFrame(
        {
            "time": pd.date_range(start, periods=n, freq="4h", tz="UTC"),
            "open": o,
            "high": np.maximum(o, close) + 0.5,
            "low": np.minimum(o, close) - 0.5,
            "close": close,
            "volume": volume if volume is not None else np.full(n, 1000.0),
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


def _noisy_uptrend(n: int = 500, seed: int = 42) -> np.ndarray:
    rng = np.random.RandomState(seed)
    rets = rng.normal(0.0015, 0.012, n)
    return 100.0 * np.cumprod(1 + rets)


def test_baseline_variant_detect_ile_BIREBIR_ayni_sinyal_uretir():
    close_4h = _noisy_uptrend(500, 42)
    df = _ohlcv_4h(close_4h)
    close_1d = _noisy_uptrend(250, 43)
    df_daily = _ohlcv_1d(close_1d)

    baseline_signals = detect(df, df_daily, Params())
    variant_signals = detect_variant(df, df_daily, Params(), VariantFlags(name="BASELINE"))

    assert len(baseline_signals) == len(variant_signals)
    assert len(baseline_signals) > 0
    for a, b in zip(baseline_signals, variant_signals):
        assert a.signal_bar == b.signal_bar
        assert a.entry_ref == b.entry_ref
        assert a.sl == b.sl


def test_max_extension_filtre_asiri_uzamis_sinyalleri_eler():
    close_4h = _noisy_uptrend(500, 42)
    df = _ohlcv_4h(close_4h)
    close_1d = _noisy_uptrend(250, 43)
    df_daily = _ohlcv_1d(close_1d)

    baseline = detect_variant(df, df_daily, Params(), VariantFlags(name="BASELINE"))
    strict = detect_variant(df, df_daily, Params(), VariantFlags(name="STRICT", max_extension_atr=0.1))

    assert len(strict) <= len(baseline)
    for s in strict:
        assert s.dist_from_denoised_atr <= 0.1


def test_min_pullback_filtre_pullbacksiz_sinyalleri_eler():
    close_4h = _noisy_uptrend(500, 42)
    df = _ohlcv_4h(close_4h)
    close_1d = _noisy_uptrend(250, 43)
    df_daily = _ohlcv_1d(close_1d)

    baseline = detect_variant(df, df_daily, Params(), VariantFlags(name="BASELINE"))
    strict = detect_variant(df, df_daily, Params(), VariantFlags(name="STRICT", min_pullback_bars=3))

    assert len(strict) <= len(baseline)
    for s in strict:
        assert s.pullback_bars >= 3


def test_exclude_new_high_yeni_tepe_sinyallerini_eler():
    close_4h = _noisy_uptrend(500, 42)
    df = _ohlcv_4h(close_4h)
    close_1d = _noisy_uptrend(250, 43)
    df_daily = _ohlcv_1d(close_1d)

    signals = detect_variant(df, df_daily, Params(), VariantFlags(name="STRICT", exclude_new_high_20=True))
    for s in signals:
        assert s.is_new_high_20 is False


def test_adx_tavan_yuksek_adx_sinyallerini_eler():
    close_4h = _noisy_uptrend(500, 42)
    df = _ohlcv_4h(close_4h)
    close_1d = _noisy_uptrend(250, 43)
    df_daily = _ohlcv_1d(close_1d)

    signals = detect_variant(df, df_daily, Params(), VariantFlags(name="STRICT", adx_ceiling=25.0))
    for s in signals:
        assert s.adx <= 25.0


def test_rsi_override_daha_siki_esik_uygular():
    close_4h = _noisy_uptrend(500, 42)
    df = _ohlcv_4h(close_4h)
    close_1d = _noisy_uptrend(250, 43)
    df_daily = _ohlcv_1d(close_1d)

    loose = detect_variant(df, df_daily, Params(), VariantFlags(name="LOOSE", rsi_upper_override=70.0))
    strict = detect_variant(df, df_daily, Params(), VariantFlags(name="STRICT", rsi_upper_override=40.0))
    assert len(strict) <= len(loose)


def test_yetersiz_veri_bos_liste():
    df = _ohlcv_4h(np.full(10, 100.0))
    df_daily = _ohlcv_1d(np.full(5, 100.0))
    assert detect_variant(df, df_daily, Params(), VariantFlags(name="BASELINE")) == []
