"""pairs_engine.py: sermaye korunumu, komisyon muhasebesi, metrikler."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tlab.backtest.pairs_engine import (
    run_pair_backtest,
    run_pair_backtest_market_neutral,
    run_pair_backtest_weighted,
)


def _idx(n: int) -> pd.DatetimeIndex:
    return pd.date_range("2024-01-01", periods=n, freq="D", tz="Europe/Istanbul")


def test_no_position_until_first_signal_stays_flat_at_start_capital() -> None:
    index = _idx(5)
    y = pd.Series([100.0, 102, 104, 106, 108], index=index)
    x = pd.Series([50.0, 50, 50, 50, 50], index=index)
    holding = pd.Series([np.nan, np.nan, np.nan, np.nan, np.nan], index=index)
    result = run_pair_backtest(y, x, holding, start_capital=100_000.0, commission_bps=10)
    assert (result.portfolio == 100_000.0).all()
    assert result.n_trades == 0
    assert result.net_pnl == 0.0


def test_single_switch_pays_commission_exactly_once() -> None:
    """İlk giriş — SATILACAK bir pozisyon yok, yalnızca TEK taraflı (alım)
    komisyonu uygulanır."""
    index = _idx(3)
    y = pd.Series([100.0, 100.0, 100.0], index=index)
    x = pd.Series([50.0, 50.0, 50.0], index=index)
    holding = pd.Series([1.0, 1.0, 1.0], index=index)
    result = run_pair_backtest(y, x, holding, start_capital=100_000.0, commission_bps=100)
    expected = 100_000.0 * (1 - 0.01)
    assert np.allclose(result.portfolio.to_numpy(), expected)


def test_round_trip_commission_charged_on_both_legs() -> None:
    """Y'den X'e geçiş: SATIŞ (Y) + ALIM (X) komisyonu — iki taraflı."""
    index = _idx(2)
    y = pd.Series([100.0, 100.0], index=index)
    x = pd.Series([50.0, 50.0], index=index)
    holding_y_first = pd.Series([1.0, 1.0], index=index)
    entry = run_pair_backtest(y, x, holding_y_first, start_capital=100_000.0, commission_bps=100)
    after_one_leg = entry.portfolio.iloc[-1]

    index3 = _idx(3)
    y3 = pd.Series([100.0, 100.0, 100.0], index=index3)
    x3 = pd.Series([50.0, 50.0, 50.0], index=index3)
    holding_switch = pd.Series([1.0, 0.0, 0.0], index=index3)
    result = run_pair_backtest(y3, x3, holding_switch, start_capital=100_000.0, commission_bps=100)
    after_two_legs = result.portfolio.iloc[-1]

    # after_one_leg zaten TEK komisyon içeriyor (giriş); geçiş SATIŞ+ALIM
    # olmak üzere İKİ AYRI komisyon daha ekler.
    assert after_two_legs == pytest.approx(after_one_leg * (1 - 0.01) ** 2)
    assert result.n_trades == 2


def test_buyhold_5050_splits_capital_evenly_at_start() -> None:
    index = _idx(3)
    y = pd.Series([100.0, 110.0, 120.0], index=index)
    x = pd.Series([50.0, 45.0, 55.0], index=index)
    holding = pd.Series([1.0, 1.0, 1.0], index=index)
    result = run_pair_backtest(y, x, holding, start_capital=100_000.0, commission_bps=0)
    assert result.buyhold_5050.iloc[0] == pytest.approx(100_000.0)
    expected_last = 0.5 * 100_000.0 * (120 / 100) + 0.5 * 100_000.0 * (55 / 50)
    assert result.buyhold_5050.iloc[-1] == pytest.approx(expected_last)


def test_next_open_execution_uses_bar_after_signal() -> None:
    index = _idx(4)
    y = pd.Series([100.0, 100.0, 100.0, 100.0], index=index)
    y_open = pd.Series([100.0, 100.0, 110.0, 100.0], index=index)
    x = pd.Series([50.0, 50.0, 50.0, 50.0], index=index)
    holding = pd.Series([np.nan, 1.0, 1.0, 1.0], index=index)
    result = run_pair_backtest(
        y, x, holding, start_capital=100_000.0, commission_bps=0,
        execution="next_open", y_open=y_open,
    )
    assert result.trades[0].entry_price == pytest.approx(110.0)
    assert result.trades[0].entry_idx == 2


def test_max_drawdown_on_known_sequence() -> None:
    """100 -> 120 -> 90 -> 130: tepe 120'den 90'a düşüş -25%."""
    index = _idx(4)
    y = pd.Series([100.0, 120.0, 90.0, 130.0], index=index)
    x = pd.Series([50.0, 50.0, 50.0, 50.0], index=index)
    holding = pd.Series([1.0, 1.0, 1.0, 1.0], index=index)
    result = run_pair_backtest(y, x, holding, start_capital=100_000.0, commission_bps=0)
    assert result.max_drawdown == pytest.approx(-25.0)
    assert result.win_rate == 0.0  # pozisyon hiç kapanmadı (n_trades=1, closed trade yok)


# --- run_pair_backtest_weighted (Faz 8E) --------------------------------


def test_weighted_actual_weight_always_between_zero_and_one() -> None:
    index = _idx(30)
    rng = np.random.default_rng(1)
    y = pd.Series(100.0 * np.cumprod(1 + rng.normal(0, 0.02, 30)), index=index)
    x = pd.Series(100.0 * np.cumprod(1 + rng.normal(0, 0.02, 30)), index=index)
    target = pd.Series(0.5, index=index)
    target.iloc[10:] = 0.75
    target.iloc[20:] = 0.25
    result = run_pair_backtest_weighted(y, x, target, start_capital=100_000.0, commission_bps=10)
    assert result.actual_weight.between(0.0, 1.0).all()


def test_weighted_no_rebalance_within_band_charges_commission_once() -> None:
    """Hedef ağırlık HİÇ değişmiyor VE fiyat hareketleri drift'i band
    içinde tutuyor -> yalnızca İLK (giriş) komisyonu ödenir, sermaye
    sonrasında YALNIZCA fiyat hareketiyle değişir (korunum)."""
    index = _idx(10)
    y = pd.Series(100.0, index=index)  # sabit fiyat -> hiç drift yok
    x = pd.Series(50.0, index=index)
    target = pd.Series(0.5, index=index)
    result = run_pair_backtest_weighted(
        y, x, target, start_capital=100_000.0, commission_bps=100, rebalance_band=0.05,
    )
    assert result.rebalance_count == 1  # yalnızca başlangıç tahsisi
    expected = 100_000.0 * (1 - 0.01)  # tek taraflı %1 komisyon
    assert np.allclose(result.portfolio.to_numpy(), expected)


def test_weighted_rebalance_triggers_when_band_exceeded() -> None:
    index = _idx(5)
    y = pd.Series([100.0] * 5, index=index)
    x = pd.Series([50.0] * 5, index=index)
    target = pd.Series(0.5, index=index)
    target.iloc[2:] = 0.9  # bandı (0.05) çok aşan bir hedef sıçraması
    result = run_pair_backtest_weighted(
        y, x, target, start_capital=100_000.0, commission_bps=10, rebalance_band=0.05,
    )
    assert result.rebalance_count == 2  # başlangıç + 1 rebalans
    assert bool(result.rebalanced.iloc[2])
    assert not result.rebalanced.iloc[3]
    assert result.actual_weight.iloc[2] == pytest.approx(0.9, abs=1e-6)


# --- run_pair_backtest_market_neutral (Faz 2, 2C) ---------------------------


def test_market_neutral_no_position_stays_flat_at_start_capital() -> None:
    index = _idx(5)
    y = pd.Series([100.0, 102, 104, 106, 108], index=index)
    x = pd.Series([50.0, 50, 50, 50, 50], index=index)
    position = pd.Series([np.nan] * 5, index=index)
    beta = pd.Series([2.0] * 5, index=index)
    result = run_pair_backtest_market_neutral(y, x, position, beta, start_capital=100_000.0)
    assert (result.portfolio == 100_000.0).all()
    assert result.n_trades == 0


def test_market_neutral_round_trip_with_price_reverting_returns_full_principal() -> None:
    """Faz 2, 2C GERÇEK bir muhasebe hatasını kilitleyen regresyon testi:
    ilk uygulamada pozisyon KAPANDIĞINDA yalnızca gerçekleşen PnL nakite
    eklenip pozisyona YATIRILAN ANAPARA (position_gross) unutuluyordu --
    fiyat giriş seviyesine dönüp PnL=0 olduğunda bile portföy 0'a
    düşüyordu. Y 100->110->100 (X sabit): PnL=0, komisyon=0 -> tam anapara
    (100.000) geri dönmeli."""
    index = _idx(3)
    y = pd.Series([100.0, 110.0, 100.0], index=index)
    x = pd.Series([50.0, 50.0, 50.0], index=index)
    position = pd.Series([1.0, 1.0, 0.0], index=index)
    beta = pd.Series([2.0, 2.0, 2.0], index=index)
    result = run_pair_backtest_market_neutral(
        y, x, position, beta, start_capital=100_000.0, commission_bps=0,
    )
    assert result.portfolio.iloc[0] == pytest.approx(100_000.0)
    assert result.portfolio.iloc[1] == pytest.approx(103_333.33, abs=0.5)
    assert result.portfolio.iloc[2] == pytest.approx(100_000.0, abs=1e-6)
    assert result.n_trades == 1
    assert result.trades[0].pnl == pytest.approx(0.0, abs=1e-6)


def test_market_neutral_long_y_short_x_profits_when_y_rises_x_flat() -> None:
    index = _idx(2)
    y = pd.Series([100.0, 110.0], index=index)
    x = pd.Series([50.0, 50.0], index=index)
    position = pd.Series([1.0, 1.0], index=index)
    beta = pd.Series([2.0, 2.0], index=index)
    result = run_pair_backtest_market_neutral(
        y, x, position, beta, start_capital=100_000.0, commission_bps=0,
    )
    # gross=100000, n_y=100000/3=33333.33 -> shares_y=333.333; Y +10 -> +3333.33
    assert result.portfolio.iloc[-1] == pytest.approx(103_333.33, abs=0.5)


def test_market_neutral_short_y_long_x_profits_when_y_falls() -> None:
    index = _idx(2)
    y = pd.Series([100.0, 90.0], index=index)
    x = pd.Series([50.0, 50.0], index=index)
    position = pd.Series([-1.0, -1.0], index=index)
    beta = pd.Series([2.0, 2.0], index=index)
    result = run_pair_backtest_market_neutral(
        y, x, position, beta, start_capital=100_000.0, commission_bps=0,
    )
    # short Y: Y düşünce KAZANÇ. shares_y=333.333, düşüş -10 -> +3333.33
    assert result.portfolio.iloc[-1] == pytest.approx(103_333.33, abs=0.5)


def test_market_neutral_commission_charged_once_on_entry() -> None:
    index = _idx(2)
    y = pd.Series([100.0, 100.0], index=index)
    x = pd.Series([50.0, 50.0], index=index)
    position = pd.Series([1.0, 1.0], index=index)
    beta = pd.Series([2.0, 2.0], index=index)
    result = run_pair_backtest_market_neutral(
        y, x, position, beta, start_capital=100_000.0, commission_bps=100,
    )
    expected = 100_000.0 * (1 - 0.01)
    assert result.portfolio.iloc[-1] == pytest.approx(expected)


def test_market_neutral_invalid_beta_skips_entry() -> None:
    """beta<=0 -- geçersiz/anlamsız hedge -- pozisyon AÇILMAZ, nakitte kalınır."""
    index = _idx(3)
    y = pd.Series([100.0, 110.0, 120.0], index=index)
    x = pd.Series([50.0, 50.0, 50.0], index=index)
    position = pd.Series([1.0, 1.0, 1.0], index=index)
    beta = pd.Series([-1.0, -1.0, -1.0], index=index)
    result = run_pair_backtest_market_neutral(y, x, position, beta, start_capital=100_000.0)
    assert (result.portfolio == 100_000.0).all()
    assert result.n_trades == 0


def test_market_neutral_flip_direction_closes_and_reopens() -> None:
    """+1 -> -1 doğrudan geçiş: eski pozisyon KAPANIR, YENİ (ters) pozisyon
    AÇILIR -- iki ayrı trade (bkz. n_trades)."""
    index = _idx(3)
    y = pd.Series([100.0, 100.0, 100.0], index=index)
    x = pd.Series([50.0, 50.0, 50.0], index=index)
    position = pd.Series([1.0, -1.0, -1.0], index=index)
    beta = pd.Series([2.0, 2.0, 2.0], index=index)
    result = run_pair_backtest_market_neutral(
        y, x, position, beta, start_capital=100_000.0, commission_bps=0,
    )
    assert result.n_trades == 2
    assert result.trades[0].direction == "long_y_short_x"
    assert result.trades[0].exit_idx is not None  # ilk pozisyon KAPANDI
    assert result.trades[1].direction == "short_y_long_x"
    assert result.trades[1].exit_idx is None  # ikinci pozisyon dizinin sonunda HÂLÂ açık
    assert result.trades[1].pnl is None


def test_weighted_harvest_is_zero_when_never_rebalanced() -> None:
    """Statik al-tut ile hiç rebalans yapılmayan bir strateji AYNI
    portföyü üretir -> harvest tam olarak sıfır olmalı (izole edilen
    'aktif rebalans alfası' YOK çünkü hiç rebalans yapılmadı)."""
    index = _idx(10)
    rng = np.random.default_rng(2)
    y = pd.Series(100.0 * np.cumprod(1 + rng.normal(0, 0.01, 10)), index=index)
    x = pd.Series(50.0 * np.cumprod(1 + rng.normal(0, 0.01, 10)), index=index)
    target = pd.Series(0.5, index=index)
    result = run_pair_backtest_weighted(
        y, x, target, start_capital=100_000.0, commission_bps=0, rebalance_band=1.0,
    )
    assert result.rebalance_count == 1
    np.testing.assert_allclose(result.harvest.to_numpy(), 0.0, atol=1e-6)
