"""Evren-geneli (cross-sectional) rölatif güç/alfa/momentum yardımcıları.

`rolling_alpha_beta`/`information_ratio`/`momentum_horizons`/`fip`/`rs_line`
TEK bir sembolün (returns_i/price) bir endekse (returns_m/index) göre zaman
serisini işler — hepsi yalnızca `rolling()`/pozitif `shift()` kullanır
(non-repaint). `rank_pct` ise gerçekten evren-geneli: bir anlık görüntüdeki
{sembol: değer} sözlüğünü percentile rank'e çevirir — bu, Faz 8D'nin
"universe-level" tarama katmanının (bkz. CLAUDE.md Faz 8D notu) her
sembolün rolling_alpha_beta/momentum_horizons çıktısını TEK bir bardaki
değere indirgeyip topladıktan SONRA çağıracağı adım.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RollingAlphaBeta:
    alpha: pd.Series
    beta: pd.Series
    t_stat: pd.Series  # alpha'nın t-istatistiği (OLS intercept SE'sine göre)


def rolling_alpha_beta(
    returns_i: pd.Series, returns_m: pd.Series, window: int
) -> RollingAlphaBeta:
    """returns_i = alpha + beta*returns_m + eps regresyonunun, her bar için
    son `window` bar üzerinden trailing OLS'i (channels.regression_channel
    ile AYNI "her t kendi sabit penceresini fit eder" deseni). t_stat,
    alpha'nın klasik OLS intercept standart hatasına göre t-istatistiğidir:
    SE(alpha) = resid_std * sqrt(1/n + x_mean^2/Sxx), dof=window-2.

    returns_i/returns_m FARKLI index'e sahip olabilir (iki farklı sembol/
    endeks serisi) — yalnızca ORTAK tarihler kullanılır (inner join)."""
    common_idx = returns_i.index.intersection(returns_m.index).sort_values()
    y_full = returns_i.reindex(common_idx).to_numpy(dtype=float)
    x_full = returns_m.reindex(common_idx).to_numpy(dtype=float)
    n = len(common_idx)

    alpha = np.full(n, np.nan)
    beta = np.full(n, np.nan)
    t_stat = np.full(n, np.nan)
    dof = window - 2

    if window >= 2 and dof > 0:
        for t in range(window - 1, n):
            y = y_full[t - window + 1 : t + 1]
            x = x_full[t - window + 1 : t + 1]
            x_mean, y_mean = x.mean(), y.mean()
            x_centered = x - x_mean
            x_var = float((x_centered**2).sum())
            if x_var == 0:
                continue
            b = float((x_centered * (y - y_mean)).sum() / x_var)
            a = y_mean - b * x_mean
            resid = y - (a + b * x)
            resid_var = float((resid**2).sum() / dof)
            se_alpha = math.sqrt(resid_var * (1.0 / window + x_mean**2 / x_var))
            alpha[t] = a
            beta[t] = b
            t_stat[t] = (a / se_alpha) if se_alpha > 0 else np.nan

    return RollingAlphaBeta(
        alpha=pd.Series(alpha, index=common_idx),
        beta=pd.Series(beta, index=common_idx),
        t_stat=pd.Series(t_stat, index=common_idx),
    )


def information_ratio(
    returns_i: pd.Series, returns_m: pd.Series, window: int, annualize: bool = True
) -> pd.Series:
    """Rolling IR = mean(aktif_getiri)/std(aktif_getiri), aktif_getiri =
    returns_i - returns_m (ortak tarihlerde). annualize=True ise sqrt(252)
    ile ölçeklenir (realized_vol ile aynı varsayım — günlük bar)."""
    common_idx = returns_i.index.intersection(returns_m.index).sort_values()
    active = returns_i.reindex(common_idx) - returns_m.reindex(common_idx)
    mean = active.rolling(window, min_periods=window).mean()
    std = active.rolling(window, min_periods=window).std(ddof=0)
    ir = mean / std.replace(0.0, np.nan)
    if annualize:
        ir = ir * math.sqrt(252)
    return ir


def momentum_horizons(
    prices: pd.Series, horizons: tuple[int, ...] = (21, 63, 126, 252), skip: int = 21
) -> dict[int, pd.Series]:
    """Her ufuk `h` için: price[t-skip]/price[t-skip-h] - 1 — klasik
    "12-1" akademik momentum kurgusu (en güncel `skip` barı DIŞLAYARAK
    kısa-vadeli tersine dönüş etkisinden kaçınmak için). Yalnızca pozitif
    `shift()` kullanır (shift(skip), shift(h)) — non-repaint."""
    shifted = prices.shift(skip)
    return {h: shifted / shifted.shift(h) - 1.0 for h in horizons}


def fip(returns: pd.Series, n: int) -> pd.Series:
    """Frog-In-The-Pan tutarlılık ölçüsü (Da, Gurun, Warachka 2014):
    sign(n-günlük kümülatif getiri) * (negatif gün oranı - pozitif gün oranı).

    Düşük |FIP| (getiri işaretiyle AYNI yönde çok az ters gün) -> "yumuşak,
    tutarlı" trend; yüksek |FIP| ile zıt işaret -> "sıçramalı" trend
    (momentum literatüründe daha ZAYIF devam beklentisi). Yalnızca trailing
    `rolling()` kullanır."""
    cum_ret = (1.0 + returns).rolling(n, min_periods=n).apply(
        lambda x: float(np.prod(x) - 1.0), raw=True
    )
    sign = np.sign(cum_ret)
    pos_frac = returns.gt(0).rolling(n, min_periods=n).mean()
    neg_frac = returns.lt(0).rolling(n, min_periods=n).mean()
    return sign * (neg_frac - pos_frac)


def rs_line(price: pd.Series, index: pd.Series) -> pd.Series:
    """Rölatif Güç çizgisi = price/index (ortak tarihlerde). Ham oran
    serisidir — eğim/regresyon (RS'nin kendi trendi) çağıranın (ör. Faz 8D
    momentum_rank) sorumluluğunda."""
    common_idx = price.index.intersection(index.index).sort_values()
    return price.reindex(common_idx) / index.reindex(common_idx)


def rank_pct(values: dict[str, float]) -> dict[str, float]:
    """{sembol: değer} sözlüğünü percentile rank'e (0..100) çevirir: EN
    YÜKSEK değer rank_pct≈0, EN DÜŞÜK değer rank_pct≈100 (tek eleman ->0).
    'top_pct' filtreleri (Faz 8D alpha_rank/momentum_rank) `rank_pct <=
    top_pct` biçiminde kullanır — bu yüzden yön BİLEREK ters çevrilmiştir
    (en iyi performans = en küçük rank_pct)."""
    if not values:
        return {}
    s = pd.Series(values)
    ranks = s.rank(ascending=False, method="average")  # 1 = en yüksek değer
    n = len(s)
    pct = (ranks - 1) / max(n - 1, 1) * 100.0
    return pct.to_dict()
