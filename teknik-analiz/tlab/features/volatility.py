"""Paylaşılan oynaklık yardımcıları (yalnızca geriye bakan)."""

from __future__ import annotations

import math
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


def garch11_forecast(
    returns: pd.Series, window: int = 252, refit_stride: int = 21, annualize: bool = True,
) -> pd.Series:
    """GARCH(1,1) koşullu oynaklık tahmini (Faz 8E — `arch` paketi).

    MLE fit HER barda tekrarlamak pahalı olduğu için yalnızca `refit_stride` barda
    bir yeniden fit edilir (`window` bar trailing pencereyle — yalnızca [t-window+1,t]
    kullanır, non-repaint). Aradaki barlarda son fit'in (omega, alpha, beta)
    parametreleriyle GARCH özyinelemesi (σ²_t = ω + α·ε²_{t-1} + β·σ²_{t-1}) İLERİ
    sarılır — ε_{t-1} her zaman GEÇMİŞ (t-1) getirisidir, σ²_{t-1} bir önceki barın
    DURUMUDUR; ikisi de yalnızca t'den ÖNCEki bilgidir. Getiriler `arch` paketinin
    MLE optimizasyonunun kararlılığı için ×100 ölçeklenir (yüzde), sonuç ÷100'e
    geri çevrilir. Fit ıraksarsa (`ConvergenceWarning`/istisna) o pencere için NaN
    döner (sessizce sıfır/uydurma değere düşülmez).
    """
    from arch import arch_model  # opsiyonel ağır bağımlılık — yalnızca burada import edilir

    n = len(returns)
    sigma = pd.Series(np.nan, index=returns.index)
    if n <= window:
        return sigma

    ret_pct = returns.to_numpy(dtype=float) * 100.0
    first_fit = window - 1
    omega = alpha = beta = None
    sigma2_state: float | None = None

    for t in range(first_fit, n):
        need_refit = omega is None or (t - first_fit) % refit_stride == 0
        if need_refit:
            window_ret = ret_pct[t - window + 1 : t + 1]
            if np.any(np.isnan(window_ret)):
                omega = alpha = beta = sigma2_state = None
                continue
            try:
                am = arch_model(window_ret, vol="GARCH", p=1, q=1, mean="Zero", rescale=False)
                res = am.fit(disp="off", show_warning=False)
                omega = float(res.params["omega"])
                alpha = float(res.params["alpha[1]"])
                beta = float(res.params["beta[1]"])
                sigma2_state = float(res.conditional_volatility[-1] ** 2)
            except Exception:  # noqa: BLE001 — MLE ıraksaması: bu bar NaN kalır, uydurma değer YOK
                omega = alpha = beta = sigma2_state = None
                continue
        else:
            eps_prev = ret_pct[t - 1]
            sigma2_state = omega + alpha * eps_prev**2 + beta * sigma2_state  # type: ignore[operator]

        sigma.iloc[t] = math.sqrt(sigma2_state) / 100.0

    if annualize:
        sigma = sigma * math.sqrt(252)
    return sigma


def vol_zscore(close: pd.Series, vol_window: int = 20, zscore_window: int = 100) -> pd.Series:
    """realized_vol'un kendi rolling z-skoru — "oynaklık şu an tarihine göre
    ne kadar yüksek/düşük" sorusu için (ör. sıkışma/patlama rejim filtresi).
    İki ayrı pencere: önce vol_window barlık realized vol hesaplanır, sonra
    bu serinin zscore_window barlık z-skoru alınır (stats.zscore, rolling —
    non-repaint)."""
    vol = realized_vol(close, vol_window)
    return zscore(vol, zscore_window)
