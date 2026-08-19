"""src.analysis.regime_filters testleri."""

from __future__ import annotations

import numpy as np
import pytest

from src.analysis.regime_filters import (
    MEAN_REVERSION_THRESHOLD,
    TREND_THRESHOLD,
    classify_regime,
    hurst_exponent,
    rolling_hurst,
)


def test_yetersiz_veride_notr_0_5_doner():
    assert hurst_exponent(np.array([1.0, 2.0, 3.0]), max_lag=50) == 0.5


def test_sabit_seride_firlatmaz_ve_sonuc_sonludur():
    series = np.full(200, 100.0)
    h = hurst_exponent(series, max_lag=50)
    assert np.isfinite(h)
    assert abs(h) < 0.1  # dejenere/duz seri -- guclu bir yon iddia ETMEMELI


def test_guclu_trend_seride_hurst_yuksek():
    # Trend = KALICI (pozitif oz-korelasyonlu) getiriler ile insa edilir --
    # duz bir dogru + kucuk gurultu DEGIL: bu yontem (lag-fark std'si) sabit
    # bir surukleme'yi (deterministic drift) mean-centered std() ile
    # OTOMATIK eler (bkz. modul ust notu, "genellestirilmis Hurst" tanimi) --
    # gercek piyasa trendleri momentum/kalicilik ile modellenir, duz bir
    # dogruyla DEGIL.
    rng = np.random.default_rng(42)
    n = 600
    returns = np.empty(n)
    returns[0] = rng.normal(0, 1.0)
    for i in range(1, n):
        returns[i] = 0.9 * returns[i - 1] + rng.normal(0, 1.0)  # pozitif oz-korelasyon = kalicilik
    series = 100.0 + np.cumsum(returns)
    h = hurst_exponent(series, max_lag=50)
    assert h > TREND_THRESHOLD


def test_mean_reverting_seride_hurst_dusuk():
    rng = np.random.default_rng(7)
    n = 400
    # AR(1), guclu negatif-ozilasyon (phi negatif -> ortalamaya hizli donus)
    series = np.empty(n)
    series[0] = 100.0
    phi = -0.6
    for i in range(1, n):
        series[i] = 100.0 + phi * (series[i - 1] - 100.0) + rng.normal(0, 1.0)
    h = hurst_exponent(series, max_lag=50)
    assert h < MEAN_REVERSION_THRESHOLD


def test_rolling_hurst_ilk_pencere_notr():
    closes = np.linspace(100, 150, 150)
    out = rolling_hurst(closes, window=100, max_lag=30)
    assert np.all(out[:100] == 0.5)
    assert len(out) == 150


def test_rolling_hurst_look_ahead_yok():
    """Serinin SONUNU degistirmek, ERKEN barlardaki hurst degerini
    ETKILEMEMELI (look-ahead guvenligi)."""
    rng = np.random.default_rng(1)
    base = 100.0 + np.cumsum(rng.normal(0, 1.0, 250))
    out_a = rolling_hurst(base, window=100, max_lag=30)

    modified = base.copy()
    modified[-10:] = modified[-10:] + 1000.0  # sadece son 10 bari boz
    out_b = rolling_hurst(modified, window=100, max_lag=30)

    assert np.allclose(out_a[:200], out_b[:200])


@pytest.mark.parametrize(
    "h,expected",
    [(0.7, "TREND"), (0.3, "MEAN_REVERSION"), (0.5, "RANDOM_WALK"), (0.56, "TREND"), (0.44, "MEAN_REVERSION")],
)
def test_classify_regime(h, expected):
    assert classify_regime(h) == expected
