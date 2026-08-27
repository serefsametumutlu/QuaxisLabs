"""Paylaşılan oynaklık yardımcıları (yalnızca geriye bakan)."""

from __future__ import annotations

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
