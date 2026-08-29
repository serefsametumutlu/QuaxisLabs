"""Paylaşılan oynaklık yardımcıları (yalnızca geriye bakan)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from tlab.features.stats import zscore


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Wilder'ın Average True Range'i.

    True Range = max(high-low, |high-prev_close|, |low-prev_close|).
    ATR, TR'nin Wilder düzleştirmesiyle (alpha=1/period) hesaplanan hareketli
    ortalamasıdır — yalnızca t ve öncesi barları kullanır, geriye bakış yok.
    İlk `period` bar NaN'dır (yeterli geçmiş yok).
    """
    if len(df) == 0:
        return pd.Series(dtype=float, index=df.index)

    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    tr.iloc[0] = df["high"].iloc[0] - df["low"].iloc[0]
    return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()


@dataclass(frozen=True)
class Bollinger:
    mid: pd.Series
    upper: pd.Series
    lower: pd.Series
    bandwidth: pd.Series


def bollinger(series: pd.Series, n: int = 20, k: float = 2.0) -> Bollinger:
    """Orta bant = SMA(n); üst/alt = orta ± k·std(n) (nüfus std, ddof=0 —
    TradingView/çoğu platformun varsayılanıyla eşleşir). `bandwidth` =
    (üst-alt)/orta — sıkışma (squeeze) tespiti için (bkz. bb_break, Faz 8A).
    Yalnızca trailing `rolling()` kullanır, geriye bakış yok."""
    mid = series.rolling(n, min_periods=n).mean()
    std = series.rolling(n, min_periods=n).std(ddof=0)
    upper = mid + k * std
    lower = mid - k * std
    bandwidth = (upper - lower) / mid
    return Bollinger(mid=mid, upper=upper, lower=lower, bandwidth=bandwidth)


def realized_vol(close: pd.Series, n: int = 20, annualize: bool = True) -> pd.Series:
    """Log-getiri std'sinin rolling penceresi (n bar). annualize=True ise
    yıllıklaştırma faktörü sqrt(252) ile çarpılır (BIST/NASDAQ günlük bar
    varsayımı — 4H/haftalık gibi başka periyotlarda çağıran kendi faktörünü
    uygulamalı, bu fonksiyon periyot bilmez). ddof=0 (bollinger ile tutarlı)."""
    log_ret = np.log(close / close.shift(1))
    vol = log_ret.rolling(n, min_periods=n).std(ddof=0)
    if annualize:
        vol = vol * np.sqrt(252)
    return vol


@dataclass(frozen=True)
class Keltner:
    mid: pd.Series
    upper: pd.Series
    lower: pd.Series


def keltner(df: pd.DataFrame, n: int = 20, atr_period: int = 10, k: float = 2.0) -> Keltner:
    """Orta bant = EMA(close, n); üst/alt = orta ± k·ATR(atr_period).
    ATR zaten yalnızca geçmişe bakar (bkz. `atr()`), EMA de trailing
    `ewm(adjust=False)` kullanır — ikisi de non-repaint."""
    mid = df["close"].ewm(span=n, min_periods=n, adjust=False).mean()
    a = atr(df, atr_period)
    upper = mid + k * a
    lower = mid - k * a
    return Keltner(mid=mid, upper=upper, lower=lower)


def vol_zscore(close: pd.Series, vol_window: int = 20, zscore_window: int = 100) -> pd.Series:
    """realized_vol'un kendi rolling z-skoru — "oynaklık şu an tarihine göre
    ne kadar yüksek/düşük" sorusu için (ör. sıkışma/patlama rejim filtresi).
    İki ayrı pencere: önce vol_window barlık realized vol hesaplanır, sonra
    bu serinin zscore_window barlık z-skoru alınır (stats.zscore, rolling —
    non-repaint)."""
    vol = realized_vol(close, vol_window)
    return zscore(vol, zscore_window)
