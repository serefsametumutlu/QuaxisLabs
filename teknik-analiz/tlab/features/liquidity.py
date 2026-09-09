"""Corwin–Schultz (2012) yüksek-düşük bid-ask spread tahmincisi.

Kullanıcının verdiği çerçeve (2026-09-08) aynen uygulanıyor:

  *"Corwin-Schultz hisse yükselecek mi düşecek mi demez. Sadece hareketin
  kalitesini anlatır. Fiyatın yönü söyler. Spread tahtanın sağlığını
  söyler. Sigma hareketin sertliğini söyler."*

Kaynak: Corwin, S. A. & Schultz, P. (2012), "A Simple Way to Estimate
Bid-Ask Spreads from Daily High and Low Prices", Journal of Finance
67(2), 719-760.

    β = [ln(H_t/L_t)]² + [ln(H_{t+1}/L_{t+1})]²
    γ = [ln(H⁽²⁾/L⁽²⁾)]²      H⁽²⁾=max(H_t,H_{t+1}), L⁽²⁾=min(L_t,L_{t+1})
    α = (√(2β) − √β)/(3 − 2√2) − √(γ/(3 − 2√2))
    S = 2(e^α − 1)/(1 + e^α)

Negatif iki-günlük tahminler, Corwin'in kendi notundaki tavsiyeye uyarak
SIFIRA çekilir (atılmaz) — atmak örneklemi yukarı yanlı hâle getirir.

Hesap yapar, çizmez.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

_K = 3.0 - 2.0 * np.sqrt(2.0)


@dataclass(frozen=True)
class LiquidityState:
    spread_now: float
    spread_mean: float
    spread_median: float
    spread_p75: float
    spread_p90: float
    sigma_now: float
    sigma_mean: float
    regime: str          # dört hâlden biri
    note: str


def corwin_schultz(
    df: pd.DataFrame, *, window: int = 21, clamp_negative: bool = True,
) -> tuple[pd.Series, pd.Series]:
    """(spread, sigma) — ikisi de oransal (0.02 = %2)."""
    h, low_ = df["high"].astype(float), df["low"].astype(float)
    if (low_ <= 0).any():
        raise ValueError("low <= 0 olan bar var; Corwin-Schultz log alır")

    hl = np.log(h / low_) ** 2
    beta = hl + hl.shift(-1)                       # t ve t+1'in tek-gün kareleri

    h2 = pd.concat([h, h.shift(-1)], axis=1).max(axis=1)
    l2 = pd.concat([low_, low_.shift(-1)], axis=1).min(axis=1)
    gamma = np.log(h2 / l2) ** 2

    alpha = (np.sqrt(2.0 * beta) - np.sqrt(beta)) / _K - np.sqrt(gamma / _K)
    spread = 2.0 * (np.exp(alpha) - 1.0) / (1.0 + np.exp(alpha))
    if clamp_negative:
        spread = spread.clip(lower=0.0)

    # Volatilite bileşeni: β'nın beklenen değeri iki günlük varyansı
    # taşır; Parkinson sabiti k2 = √(8/π) ile günlük σ'ya çevrilir.
    #
    # NOT: makalenin σ denklemi γ terimini de içeren daha uzun bir biçimde
    # verilir. Buradaki biçim β tabanlı yaklaşımdır ve SPREAD tahminini
    # etkilemez (α yalnızca β ve γ'dan gelir). Üretimde σ'yı ölçüt olarak
    # kullanmadan önce makaleden birebir doğrulanmalı.
    k2 = np.sqrt(8.0 / np.pi)
    sigma = np.sqrt(np.maximum(beta / 2.0, 0.0)) / k2

    # `beta` t+1'i kullandığı için tahmin t+1 barında BİLİNİR; bir bar
    # ileri kaydırılır ki geleceğe bakılmasın (tekrar-boyama yasağı).
    spread = spread.shift(1)
    sigma = sigma.shift(1)

    return (
        spread.rolling(window).mean().rename("spread"),
        sigma.rolling(window).mean().rename("sigma"),
    )


def assess(spread: pd.Series, sigma: pd.Series) -> LiquidityState:
    """Kullanıcının dört hâlli okuma tablosu."""
    s = spread.dropna()
    v = sigma.dropna()
    if len(s) < 30 or len(v) < 30:
        raise ValueError("değerlendirme için en az 30 geçerli bar gerekli")

    s_now, v_now = float(s.iloc[-1]), float(v.iloc[-1])
    s_med, v_med = float(s.median()), float(v.median())
    s_hi, v_hi = s_now > s_med, v_now > v_med

    if not s_hi and not v_hi:
        regime, note = "likit_sakin", "Likidite iyi, piyasa sakin. En rahat yapı."
    elif not s_hi and v_hi:
        regime, note = "likit_sert", "Tahta likit ama fiyat hareketi sert."
    elif s_hi and not v_hi:
        regime, note = "ince_sakin", (
            "Fiyat sakin görünüyor ama tahta incelmiş — GİZLİ LİKİDİTE RİSKİ. "
            "Düşük volatiliteyi tek başına olumlu okumak yanıltıcı."
        )
    else:
        regime, note = "ince_sert", "Hem likidite bozuk hem hareket sert. En riskli yapı."

    return LiquidityState(
        spread_now=s_now, spread_mean=float(s.mean()), spread_median=s_med,
        spread_p75=float(s.quantile(0.75)), spread_p90=float(s.quantile(0.90)),
        sigma_now=v_now, sigma_mean=float(v.mean()), regime=regime, note=note,
    )
