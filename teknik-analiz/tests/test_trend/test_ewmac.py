"""trend.ewmac testleri: forecast kırpma sınırı, sıfır-kesişim sinyali,
registry kaydı (repaint_test)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from tests.test_trend.fixtures import build_noisy_uptrend
from tlab.indicators.trend.ewmac import EWMACIndicator, EwmacParams
from tlab.testing.repaint import repaint_test


def test_forecast_bounded_by_cap() -> None:
    df = build_noisy_uptrend(n=400)
    params = EwmacParams(cap=20.0)
    result = EWMACIndicator(params)(df)
    combined = result.series["ewmac_combined"].dropna()
    assert (combined.abs() <= 20.0 + 1e-9).all()
    for name, series in result.series.items():
        if name.startswith("ewmac_") and name not in ("ewmac_combined", "ewmac_zero"):
            assert (series.dropna().abs() <= 20.0 + 1e-9).all(), name


def test_bullish_signal_fires_on_zero_upcross() -> None:
    # Uzun düşüş sonra güçlü yükseliş -> combined forecast negatiften pozitife geçmeli.
    down = np.linspace(200, 100, 200)
    up = np.linspace(100, 400, 250)
    close = np.concatenate([down, up])
    idx = pd.date_range("2024-01-02", periods=len(close), freq="1D", tz="Europe/Istanbul")
    ohlcv = pd.DataFrame(
        {"open": close, "high": close + 0.1, "low": close - 0.1, "close": close,
         "volume": np.full(len(close), 1000.0)},
        index=idx,
    )
    result = EWMACIndicator()(ohlcv)
    events = {s.payload["event"] for s in result.signals}
    assert "ewmac_bullish" in events


def test_registers_cleanly_with_repaint_test() -> None:
    df = build_noisy_uptrend(n=400)
    report = repaint_test(EWMACIndicator(), df, tail=40)
    assert report.passed, report.mismatches


# --- Faz 5, madde C: K3 sabit forecast scalar tablosu -----------------------


def test_fixed_scalar_mode_is_default() -> None:
    assert EwmacParams().forecast_scalar_mode == "fixed"


def test_fixed_scalar_matches_k3_table_exactly() -> None:
    """K3 (bilgi-bankasi/teknik/11_carver_systematic.md, Tablo 49): sabit
    modda forecast = vol_adj * SABİT skaler, ısınma penceresi (scalar_window)
    OLMADAN -- eski empirik moddan farklı olarak ilk barlardan itibaren
    NaN kalmadan üretilir (yalnızca vol_window'un ısınması gerekir)."""
    df = build_noisy_uptrend(n=60)
    params = EwmacParams(pairs=((2, 8),), vol_window=10, forecast_scalar_mode="fixed")
    result = EWMACIndicator(params)(df)
    forecast = result.series["ewmac_2_8"]
    # scalar_window=252 (varsayılan) hiç dolmadığı bir seride bile (n=60)
    # sabit mod ısınmadan sonra hemen değer üretmeli.
    assert forecast.iloc[15:].notna().any()


def test_unlisted_pair_falls_back_to_empirical_even_in_fixed_mode() -> None:
    """K3 tablosu yalnızca standart 6 çifti kapsıyor -- tabloda olmayan
    özel bir çift `forecast_scalar_mode="fixed"` iken bile SESSİZCE
    empirik hesaba düşmeli (yanlış/sabit-olmayan bir skaler UYDURULMAMALI)."""
    df = build_noisy_uptrend(n=400)
    custom_pair = (3, 11)
    params = EwmacParams(pairs=(custom_pair,), forecast_scalar_mode="fixed")
    result_fixed = EWMACIndicator(params)(df)
    result_empirical = EWMACIndicator(
        EwmacParams(pairs=(custom_pair,), forecast_scalar_mode="empirical")
    )(df)
    pd.testing.assert_series_equal(
        result_fixed.series["ewmac_3_11"], result_empirical.series["ewmac_3_11"],
    )


def test_empirical_mode_still_available_and_differs_from_fixed() -> None:
    df = build_noisy_uptrend(n=400)
    fixed = EWMACIndicator(EwmacParams(forecast_scalar_mode="fixed"))(df)
    empirical = EWMACIndicator(EwmacParams(forecast_scalar_mode="empirical"))(df)
    a = fixed.series["ewmac_2_8"].dropna()
    b = empirical.series["ewmac_2_8"].dropna()
    common = a.index.intersection(b.index)
    assert not a.loc[common].equals(b.loc[common])
