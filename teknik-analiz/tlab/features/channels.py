"""Regresyon kanalı — her bar için son `n` bar üzerinden log-fiyat OLS'i.

Faz 2-EK'in tam kapsamı (pivot_channel, frozen_channel_at, channel_position)
henüz yazılmadı — bu modül yalnızca Faz 8A'nın `channel_break_up/down` için
gerektirdiği minimum: `regression_channel`. Diğerleri ayrı bir takip işi.

Non-repaint: bar `t`'nin kanalı yalnızca [t-n+1, t] penceresinden hesaplanır
(trailing OLS) — pencere kaydıkça geçmiş bar `t`'nin kendi kanal değeri bir
daha DEĞİŞMEZ (fixed-window OLS, sonradan gelen barlar geçmiş fit'i etkilemez).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RegressionChannel:
    mid: pd.Series
    upper: pd.Series
    lower: pd.Series


def regression_channel(df: pd.DataFrame, n: int = 100, k: float = 2.0) -> RegressionChannel:
    """Her `t >= n-1` için log(close)[t-n+1:t+1] üzerinde OLS; orta = t'deki
    fit değeri, üst/alt = orta ± k·residual_std (nüfus std). İlk `n-1` bar
    NaN (yeterli pencere yok)."""
    close = df["close"].to_numpy(dtype=float)
    log_close = np.log(close)
    m = len(df)

    mid = np.full(m, np.nan)
    upper = np.full(m, np.nan)
    lower = np.full(m, np.nan)

    if m >= n and n >= 2:
        x = np.arange(n, dtype=float)
        x_mean = x.mean()
        x_centered = x - x_mean
        x_var = float((x_centered**2).sum())

        for t in range(n - 1, m):
            window = log_close[t - n + 1 : t + 1]
            y_mean = window.mean()
            slope = float((x_centered * (window - y_mean)).sum() / x_var)
            intercept = y_mean - slope * x_mean
            fitted = slope * x + intercept
            resid_std = float((window - fitted).std(ddof=0))
            mid_log = slope * x[-1] + intercept
            mid[t] = np.exp(mid_log)
            upper[t] = np.exp(mid_log + k * resid_std)
            lower[t] = np.exp(mid_log - k * resid_std)

    idx = df.index
    return RegressionChannel(
        mid=pd.Series(mid, index=idx),
        upper=pd.Series(upper, index=idx),
        lower=pd.Series(lower, index=idx),
    )
