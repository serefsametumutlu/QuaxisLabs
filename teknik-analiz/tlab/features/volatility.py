"""Paylaşılan oynaklık yardımcıları (yalnızca geriye bakan)."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


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
