"""src/analysis/vrp.py testleri -- tamamen sentetik veri, network YOK
(bu modül zaten SAF/I/O'suz, ağ mocklamaya gerek yok)."""

from __future__ import annotations

import numpy as np
import pytest

from src.analysis import vrp


def test_realized_volatility_bilinen_diziyle_elle_hesapla():
    rng = np.random.default_rng(42)
    log_returns = rng.normal(0, 0.01, size=30)

    result = vrp.realized_volatility(log_returns, window=21)

    expected = np.std(log_returns[-21:], ddof=1) * np.sqrt(252) * 100.0
    assert result == pytest.approx(expected)


def test_realized_volatility_yetersiz_veri_none_doner():
    assert vrp.realized_volatility(np.zeros(10), window=21) is None


def test_rolling_realized_volatility_ilk_pencere_nan_sonrasi_realized_ile_esit():
    rng = np.random.default_rng(7)
    log_returns = rng.normal(0, 0.01, size=50)

    rolling = vrp.rolling_realized_volatility(log_returns, window=21)

    assert np.all(np.isnan(rolling[:20]))
    for i in range(20, 50):
        expected = vrp.realized_volatility(log_returns[: i + 1], window=21)
        assert rolling[i] == pytest.approx(expected)


def _simulate_garch11(n: int, omega: float, alpha: float, beta: float, seed: int) -> np.ndarray:
    """Bilinen (omega,alpha,beta) ile GERÇEK bir GARCH(1,1) DGP simüle eder
    -- `fit_garch11`in bunu geri kazanabildiğini doğrulamak için."""
    rng = np.random.default_rng(seed)
    h = np.empty(n)
    eps = np.empty(n)
    h[0] = omega / (1 - alpha - beta)
    eps[0] = rng.normal(0, np.sqrt(h[0]))
    for t in range(1, n):
        h[t] = omega + alpha * eps[t - 1] ** 2 + beta * h[t - 1]
        eps[t] = rng.normal(0, np.sqrt(h[t]))
    return eps


def test_fit_garch11_bilinen_dgp_parametreleri_makul_toleransla_kapar():
    """500 gunluk pencerede GARCH(1,1) MLE'nin gercek (omega,alpha,beta)'yi
    TAM olarak kurtarmasi beklenmez (literaturde bilinen kucuk-orneklem
    gurultusu) -- burada asil test DEJENERE OLMAYAN, MAKUL bir fit uretmesi:
    ikili kalicilik (alpha+beta) durgan ve gercek degere yakin, hicbir
    parametre 0/0.999 sinirina YAPISMAMIS olmali."""
    true_omega, true_alpha, true_beta = 1e-6, 0.10, 0.85
    eps = _simulate_garch11(3000, true_omega, true_alpha, true_beta, seed=123)

    fit = vrp.fit_garch11(eps)

    assert fit is not None
    assert np.isfinite(fit.log_likelihood)
    assert fit.alpha + fit.beta < 0.999
    assert fit.alpha == pytest.approx(true_alpha, abs=0.10)
    assert (fit.alpha + fit.beta) == pytest.approx(true_alpha + true_beta, abs=0.20)


def test_fit_garch11_yetersiz_veri_none_doner():
    assert vrp.fit_garch11(np.random.default_rng(1).normal(0, 0.01, 100)) is None


def test_fit_garch11_tek_asiri_aykiri_deger_sonlu_kalir():
    rng = np.random.default_rng(9)
    log_returns = rng.normal(0, 0.01, size=600)
    log_returns[300] = 5.0  # %500 tek-gun sicramasi (winsorize UST katmanda, burada dogrudan fit)

    fit = vrp.fit_garch11(log_returns)

    assert fit is not None
    assert np.isfinite(fit.omega)
    assert np.isfinite(fit.alpha)
    assert np.isfinite(fit.beta)
    assert np.isfinite(fit.log_likelihood)


def test_compute_vrp_negatif_isaret_iv_dusukse():
    assert vrp.compute_vrp(iv_annualized_pct=20.0, rv_annualized_pct=35.0) == pytest.approx(-15.0)
    assert vrp.compute_vrp(iv_annualized_pct=40.0, rv_annualized_pct=25.0) == pytest.approx(15.0)


def test_compute_vrp_snapshot_look_ahead_guvenligi():
    rng = np.random.default_rng(55)
    log_returns = rng.normal(0, 0.015, size=400)
    closes_a = 100 * np.exp(np.cumsum(log_returns))
    # ayni gecmis, ama SONRASINA cok farkli/asiri gelecek fiyatlar eklendi
    future_calm = closes_a[-1] * np.exp(np.cumsum(rng.normal(0, 0.001, size=50)))
    future_wild = closes_a[-1] * np.exp(np.cumsum(rng.normal(0, 0.08, size=50)))
    closes_calm_future = np.concatenate([closes_a, future_calm])
    closes_wild_future = np.concatenate([closes_a, future_wild])

    as_of_idx = len(closes_a) - 1
    snap_a = vrp.compute_vrp_snapshot(closes_calm_future, as_of_idx)
    snap_b = vrp.compute_vrp_snapshot(closes_wild_future, as_of_idx)

    assert snap_a.rv_annualized_pct == snap_b.rv_annualized_pct
    assert snap_a.iv_proxy_annualized_pct == snap_b.iv_proxy_annualized_pct
    assert snap_a.vrp == snap_b.vrp


def test_compute_vrp_snapshot_yetersiz_veride_tum_alanlar_none():
    closes = 100 + np.cumsum(np.random.default_rng(3).normal(0, 1, size=50))
    snap = vrp.compute_vrp_snapshot(closes, as_of_idx=49)

    assert snap.rv_annualized_pct is None
    assert snap.iv_proxy_annualized_pct is None
    assert snap.vrp is None
    assert snap.garch is None


def test_compute_vrp_snapshot_yeterli_veride_dolu_snapshot_doner():
    rng = np.random.default_rng(88)
    log_returns = rng.normal(0.0002, 0.02, size=600)
    closes = 50 * np.exp(np.cumsum(log_returns))

    snap = vrp.compute_vrp_snapshot(closes, as_of_idx=len(closes) - 1)

    assert snap.rv_annualized_pct is not None
    assert snap.iv_proxy_annualized_pct is not None
    assert snap.vrp is not None
    assert snap.garch is not None
    assert snap.vrp == pytest.approx(snap.iv_proxy_annualized_pct - snap.rv_annualized_pct)
