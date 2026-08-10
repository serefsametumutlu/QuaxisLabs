"""src/analysis/merton.py testleri -- Merton DD/EDF modelinin iteratif
çözümünü kullanıcının kendi (2026-08-08) elle çalışılmış örneğine karşı
doğrular: A0=100, sigmaA=%25, D=80, r=%5, T=1 -> DD≈0,97, EDF≈%17."""

from __future__ import annotations

import math
from decimal import Decimal

from src.analysis.merton import annualized_equity_volatility, compute_merton_dd_edf

_D = Decimal("80")
_R = Decimal("5")


def _forward_equity_and_vol(asset_value: float, asset_vol: float, debt: float, r: float) -> tuple[float, float]:
    """Kullanicinin ornegindeki (A0, sigmaA) ciftinden Black-Scholes ile
    E, sigmaE turetir -- ters yonlu (E, sigmaE) -> (A0, sigmaA) cozumunun
    doğru A0/sigmaA'ya geri donup donmedigini test etmek icin."""
    normal = __import__("statistics").NormalDist(0, 1)
    d1 = (math.log(asset_value / debt) + (r + 0.5 * asset_vol**2)) / asset_vol
    d2 = d1 - asset_vol
    equity = asset_value * normal.cdf(d1) - debt * math.exp(-r) * normal.cdf(d2)
    sigma_e = normal.cdf(d1) * asset_vol * asset_value / equity
    return equity, sigma_e


def test_compute_merton_dd_edf_kullanicinin_ornegini_geri_cikarir():
    equity, sigma_e = _forward_equity_and_vol(100.0, 0.25, 80.0, 0.05)
    result = compute_merton_dd_edf(
        Decimal(str(round(equity, 6))), _D, Decimal(str(round(sigma_e * 100, 6))), _R
    )
    assert result is not None
    assert result.converged is True
    # Kullanicinin elle hesapladigi DD=0.97, EDF=%17 -- iteratif cozumun
    # yuvarlama farkiyla (%5 bagil tolerans) geri donmesi beklenir.
    assert abs(float(result.distance_to_default) - 0.97) < 0.05
    assert abs(float(result.default_probability_pct) - 17.0) < 2.0
    assert abs(float(result.asset_value) - 100.0) < 1.0


def test_compute_merton_dd_edf_none_girdide_none_doner():
    assert compute_merton_dd_edf(None, _D, Decimal(30), _R) is None
    assert compute_merton_dd_edf(Decimal(100), None, Decimal(30), _R) is None
    assert compute_merton_dd_edf(Decimal(100), _D, None, _R) is None
    assert compute_merton_dd_edf(Decimal(100), _D, Decimal(0), _R) is None
    assert compute_merton_dd_edf(Decimal(-5), _D, Decimal(30), _R) is None


def test_compute_merton_dd_edf_dusuk_kaldirac_yuksek_dd_verir():
    """Borcu ozkaynagina gore cok kucuk bir sirket -- yuksek DD (guvenli), dusuk EDF beklenir."""
    result = compute_merton_dd_edf(Decimal(10000), Decimal(500), Decimal(30), _R)
    assert result is not None
    assert result.distance_to_default > 3
    assert result.default_probability_pct < 5


def test_annualized_equity_volatility_yetersiz_veride_none_doner():
    assert annualized_equity_volatility([Decimal(10)] * 50) is None


def test_annualized_equity_volatility_sabit_fiyatta_sifira_yakin():
    closes = [Decimal(100)] * 130
    vol = annualized_equity_volatility(closes)
    assert vol is not None
    assert vol == Decimal("0")
