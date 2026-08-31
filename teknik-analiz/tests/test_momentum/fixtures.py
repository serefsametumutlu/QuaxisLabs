"""Faz 8D (momentum.alpha_rank/momentum_rank) için sentetik, BİLİNEN
alfa/momentum gradyanlı evren üreticisi — gerçek sıralamanın (rank_pct)
doğru yönde çalıştığını iddia edebilmek için her sembole DETERMİNİSTİK bir
"gerçek" alfa/trend gücü atanır (gürültüye göre yeterince büyük, ki sıralama
neredeyse gürültüsüz ayırt edilebilsin)."""

from __future__ import annotations

import numpy as np
import pandas as pd

_TZ = "Europe/Istanbul"


def _ohlcv_from_close(close: np.ndarray, index: pd.DatetimeIndex, volume: float) -> pd.DataFrame:
    open_ = np.empty_like(close)
    open_[0] = close[0]
    open_[1:] = close[:-1]
    high = np.maximum(open_, close) + 0.01
    low = np.minimum(open_, close) - 0.01
    return pd.DataFrame(
        {
            "open": open_, "high": high, "low": low, "close": close,
            "volume": np.full(len(close), volume),
        },
        index=index,
    )


def make_alpha_universe(
    n_symbols: int = 20, n_bars: int = 400, noise: float = 0.004, seed: int = 11,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame, dict[str, float]]:
    """Her sembole (index'ten bağımsız) DETERMİNİSTİK bir günlük alfa
    (`true_alpha[symbol]`) atanır — sembol `i`: alpha_daily = (i - n/2) *
    0.0006, beta=1.0 (sabit, alfa farkını izole etmek için). Döner:
    ({sembol: df}, index_df, {sembol: true_alpha_daily})."""
    rng = np.random.default_rng(seed)
    index = pd.date_range("2023-01-02", periods=n_bars, freq="1D", tz=_TZ)
    index_ret = rng.normal(0.0003, 0.01, n_bars)
    index_close = 100.0 * np.cumprod(1.0 + index_ret)
    index_df = _ohlcv_from_close(index_close, index, volume=1_000_000.0)

    universe: dict[str, pd.DataFrame] = {}
    true_alpha: dict[str, float] = {}
    for i in range(n_symbols):
        symbol = f"SYM{i:02d}"
        alpha_daily = (i - n_symbols / 2) * 0.0006
        beta = 1.0
        symbol_noise = rng.normal(0, noise, n_bars)
        symbol_ret = alpha_daily + beta * index_ret + symbol_noise
        close = 50.0 * np.cumprod(1.0 + symbol_ret)
        universe[symbol] = _ohlcv_from_close(close, index, volume=200_000.0)
        true_alpha[symbol] = alpha_daily
    return universe, index_df, true_alpha


def make_momentum_universe(
    n_symbols: int = 20, n_bars: int = 400, noise: float = 0.01, seed: int = 23,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame, dict[str, float]]:
    """Her sembole DETERMİNİSTİK bir günlük drift (`true_drift[symbol]`)
    atanır: sembol `i`: drift = (i - n/2) * 0.0008 — yüksek `i` -> güçlü
    yükseliş trendi -> yüksek momentum skoru (düşük rank_pct) BEKLENİR."""
    rng = np.random.default_rng(seed)
    index = pd.date_range("2023-01-02", periods=n_bars, freq="1D", tz=_TZ)
    index_ret = rng.normal(0.0002, 0.008, n_bars)
    index_close = 100.0 * np.cumprod(1.0 + index_ret)
    index_df = _ohlcv_from_close(index_close, index, volume=1_000_000.0)

    universe: dict[str, pd.DataFrame] = {}
    true_drift: dict[str, float] = {}
    for i in range(n_symbols):
        symbol = f"SYM{i:02d}"
        drift = (i - n_symbols / 2) * 0.0008
        symbol_noise = rng.normal(0, noise, n_bars)
        symbol_ret = drift + symbol_noise
        close = 50.0 * np.cumprod(1.0 + symbol_ret)
        universe[symbol] = _ohlcv_from_close(close, index, volume=200_000.0)
        true_drift[symbol] = drift
    return universe, index_df, true_drift
