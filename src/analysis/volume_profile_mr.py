"""Hacim Profili Ortalamaya Dönüş (Volume Profile Mean-Reversion) -- YENI
STRATEJI (2026-08-19, kullanici istegi: "farkli kosullar altinda... yeni
strateji uret"). SAF MANTIK, I/O YOK (`abcd_pattern.py` ile AYNI katman
ilkesi) -- `volume_profile.py`yi (POC/VAH/VAL) ve `regime_filters.py`yi
(Hurst -- SADECE mean-reversion rejiminde guvenilir olmali) birlestirir.

Motivasyon: `ULTIMATE_5_STRATEGIES.md §4 Microstructure Mean-Reverter
(MMR)`den uyarlandi -- gercek LOB/bid-ask verisi YOK, bunun yerine hacim
profili (OHLCV'den turetilebilir) destek/direnc seviyesi olarak kullanilir.

Sinyal: fiyat Value Area Low (VAL) altina indi + RSI(5) asiri satimda +
donus mumu (kapanis>acilis) + (opsiyonel) Hurst<0.45 rejim filtresi.
TP1=POC, TP2=VAH, SL=VAL-atr_mult*ATR. `abcd_backtest.backtest_symbol` ile
DOGRUDAN uyumlu (Signal alan-adi duck-typing, `momentum_confluence.Signal`
ile AYNI ilke)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.analysis.abcd_pattern import atr_wilder
from src.analysis.regime_filters import MEAN_REVERSION_THRESHOLD, rolling_hurst
from src.analysis.volume_profile import rolling_volume_profile


@dataclass(frozen=True)
class Params:
    vp_lookback: int = 20
    vp_bins: int = 30
    value_area_pct: float = 0.70
    rsi_period: int = 5
    rsi_oversold: float = 30.0
    atr_period: int = 14
    sl_atr_mult: float = 1.0
    require_hurst_mr: bool = False
    hurst_window: int = 50
    hurst_max_lag: int = 15


@dataclass(frozen=True)
class Signal:
    """`abcd_backtest.backtest_symbol` ile duck-typing uyumlu (bkz.
    `momentum_confluence.Signal` ile AYNI alan sozlesmesi)."""

    direction: int  # HER ZAMAN +1 (sadece LONG -- MMR spec'inin short kolu bu ilk surumde PORTLANMADI)
    signal_bar: int
    signal_time: pd.Timestamp
    entry_ref: float
    fill_ref: float
    tp1: float
    tp2: float
    sl: float
    poc: float
    val: float
    vah: float


def _rsi(close: np.ndarray, period: int) -> np.ndarray:
    n = len(close)
    rsi = np.full(n, np.nan)
    if n <= period:
        return rsi
    delta = np.diff(close)
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)
    avg_gain = np.full(n, np.nan)
    avg_loss = np.full(n, np.nan)
    avg_gain[period] = gain[:period].mean()
    avg_loss[period] = loss[:period].mean()
    alpha = 1.0 / period
    for i in range(period + 1, n):
        avg_gain[i] = avg_gain[i - 1] + (gain[i - 1] - avg_gain[i - 1]) * alpha
        avg_loss[i] = avg_loss[i - 1] + (loss[i - 1] - avg_loss[i - 1]) * alpha
    with np.errstate(divide="ignore", invalid="ignore"):
        rs = avg_gain / avg_loss
        rsi = 100.0 - 100.0 / (1.0 + rs)
    rsi = np.where(avg_loss == 0, 100.0, rsi)
    rsi = np.where(np.isnan(avg_gain), np.nan, rsi)
    return rsi


def detect(df: pd.DataFrame, params: Params = Params()) -> list[Signal]:
    n = len(df)
    time_col = df["time"]
    open_ = df["open"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    volume = df["volume"].to_numpy(dtype=float)

    profiles = rolling_volume_profile(high, low, volume, lookback=params.vp_lookback, n_bins=params.vp_bins, value_area_pct=params.value_area_pct)
    rsi = _rsi(close, params.rsi_period)
    atr14 = atr_wilder(df, params.atr_period)
    hurst = rolling_hurst(close, window=params.hurst_window, max_lag=params.hurst_max_lag) if params.require_hurst_mr else None

    signals: list[Signal] = []
    for i in range(n - 1):
        vp = profiles[i]
        if vp is None:
            continue
        if np.isnan(rsi[i]) or np.isnan(atr14[i]) or atr14[i] <= 0:
            continue

        below_val = close[i] < vp.val
        oversold = rsi[i] < params.rsi_oversold
        reversal_candle = close[i] > open_[i]
        if not (below_val and oversold and reversal_candle):
            continue
        if params.require_hurst_mr and not (hurst[i] < MEAN_REVERSION_THRESHOLD):
            continue

        entry_ref = float(close[i])
        fill_ref = float(open_[i + 1])
        sl = vp.val - params.sl_atr_mult * atr14[i]
        if sl >= entry_ref or not (entry_ref < vp.poc <= vp.vah):
            continue  # dejenere/ters siralanmis hedefler -- guvenli atla

        signals.append(
            Signal(
                direction=1,
                signal_bar=i,
                signal_time=time_col.iloc[i],
                entry_ref=entry_ref,
                fill_ref=fill_ref,
                tp1=float(vp.poc),
                tp2=float(vp.vah),
                sl=float(sl),
                poc=float(vp.poc),
                val=float(vp.val),
                vah=float(vp.vah),
            )
        )

    return signals
