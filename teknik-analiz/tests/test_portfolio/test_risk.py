"""tlab.portfolio.risk — 11/ORAN-03 (kesin formül + Tablo 18), position
inertia, portfolio_instrument_position."""

from __future__ import annotations

import numpy as np
import pytest

from tlab.portfolio.risk import (
    apply_position_inertia,
    diversification_multiplier,
    portfolio_instrument_position,
    round_target_position,
)


def _uniform_corr(n: int, corr: float) -> np.ndarray:
    m = np.full((n, n), corr)
    np.fill_diagonal(m, 1.0)
    return m


def test_diversification_multiplier_matches_table18_two_asset_half_corr() -> None:
    """Kabul kriteri #4: N=2, korelasyon 0.5 -> Tablo 18 değeri 1.15, ±0.02."""
    w = np.array([0.5, 0.5])
    h = _uniform_corr(2, 0.5)
    assert diversification_multiplier(w, h) == pytest.approx(1.15, abs=0.02)


@pytest.mark.parametrize(
    "n,corr,expected",
    [
        (2, 0.0, 1.41),
        (2, 1.0, 1.0),
        (3, 0.0, 1.73),
        (3, 0.25, 1.41),
        (4, 0.0, 2.0),
        (4, 0.5, 1.27),
        (5, 0.25, 1.58),
        (10, 0.25, 1.75),
    ],
)
def test_diversification_multiplier_matches_table18_other_rows(
    n: int, corr: float, expected: float
) -> None:
    """Tablo 18'in diğer satırları — kitabın KENDİ yaklaşık/yuvarlanmış
    değerleri olduğu için (eşit ağırlık + tek tip korelasyon varsayımı) daha
    gevşek bir tolerans (±0.05) kullanılır."""
    w = np.full(n, 1.0 / n)
    h = _uniform_corr(n, corr)
    assert diversification_multiplier(w, h) == pytest.approx(expected, abs=0.05)


def test_diversification_multiplier_negative_correlation_floored_at_zero() -> None:
    """11/ORAN-03: negatif korelasyon hesap ÖNCESİ sıfıra taban değeri
    verilir — floor uygulanmadan hesaplanan (daha yüksek) çarpanla
    KARIŞTIRILMAMALI."""
    w = np.array([0.5, 0.5])
    h_negative = np.array([[1.0, -0.5], [-0.5, 1.0]])
    h_zero = np.array([[1.0, 0.0], [0.0, 1.0]])
    assert diversification_multiplier(w, h_negative) == pytest.approx(
        diversification_multiplier(w, h_zero)
    )


def test_diversification_multiplier_capped_at_max() -> None:
    """Çok düşük korelasyonlu geniş bir küme, tavan (varsayılan 2.5,
    11/ORAN-02) ile sınırlanmalı."""
    w = np.full(50, 1.0 / 50)
    h = _uniform_corr(50, 0.0)
    assert diversification_multiplier(w, h) == 2.5


def test_diversification_multiplier_rejects_shape_mismatch() -> None:
    with pytest.raises(ValueError):
        diversification_multiplier(np.array([0.5, 0.5, 0.0]), _uniform_corr(2, 0.5))


def test_round_target_position_single_rounding_point() -> None:
    assert round_target_position(-56.112) == -56
    # banker's rounding kabul
    assert round_target_position(2.5) == 2 or round_target_position(2.5) == 3


def test_portfolio_instrument_position_is_pure_product() -> None:
    assert portfolio_instrument_position(93.52, 0.5, 1.15) == pytest.approx(93.52 * 0.5 * 1.15)


def test_apply_position_inertia_no_trade_within_band() -> None:
    """11/"FORMÜL ZİNCİRİ" adım 13: hedefin %10 içindeyse işlem YAPILMAZ."""
    result = apply_position_inertia(current_position=95.0, target_position=100.0, inertia_pct=0.10)
    assert result == 95.0  # |95-100|=5 <= 100*0.10=10 -> güncel pozisyon korunur


def test_apply_position_inertia_trades_when_band_exceeded() -> None:
    result = apply_position_inertia(current_position=80.0, target_position=100.0, inertia_pct=0.10)
    assert result == 100.0  # |80-100|=20 > 10 -> hedefe geçilir


def test_apply_position_inertia_zero_target_no_band() -> None:
    assert apply_position_inertia(5.0, target_position=0.0, inertia_pct=0.10) == 0.0
    assert apply_position_inertia(0.0, target_position=0.0, inertia_pct=0.10) == 0.0
