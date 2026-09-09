"""Çift sağlığı — bir istatistiksel arbitraj çiftinin BUGÜN hâlâ
işlenebilir olup olmadığı.

Kullanıcının verdiği çerçeve (2026-09-08), aynen uygulanıyor:

  *"Eşbütünleşme bize 'bu iki hisse geçmişte anlamlı bir çift miydi'
  sorusunun cevabını verir. Rolling Correlation ise 'bu çift hâlâ
  birlikte hareket ediyor mu' sorusunu cevaplar. Beta stabilitesi
  ilişkinin karakterinin değişip değişmediğini gösterir. Half Life ise
  aralarındaki sapmanın ne kadar sürede normale dönme eğiliminde
  olduğunu anlatır."*

Mimarideki yeri: eşbütünleşme ÇİFTİ SEÇER (`config/pairs.yaml` üretimi),
çift sağlığı o çiftin TARAMA ANINDA işlenebilir olup olmadığına karar
verir. Bu, `pairs.yaml`'daki 606 çiftin gürültü sorununa BH-FDR'ye ek
ikinci bir elektir.

Hesap yapar, çizmez.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PairHealth:
    corr_now: float             # son pencere korelasyonu
    corr_long: float            # uzun dönem korelasyon
    corr_drop: float            # uzun - kısa (pozitifse bozulma)
    beta_now: float
    beta_std: float             # beta'nın kendi oynaklığı (stabilite)
    half_life: float            # bar cinsinden; nan = ortalamaya dönmüyor
    score: float                # 0..1
    verdict: str                # "saglikli" | "izlemede" | "bozulmus"
    reasons: tuple[str, ...]


def rolling_correlation(
    y: pd.Series, x: pd.Series, windows: tuple[int, ...] = (30, 60, 90)
) -> dict[int, pd.Series]:
    """Getiriler üzerinden hareketli korelasyon.

    Kullanıcı: *"Korelasyonu bütün geçmiş için tek bir sayı olarak
    hesaplamak yerine son otuz, altmış veya doksan günlük hareketli
    pencereler üzerinden sürekli yeniden hesaplarız."*
    """
    ry, rx = y.pct_change(), x.pct_change()
    return {w: ry.rolling(w).corr(rx) for w in windows}


def rolling_beta(y: pd.Series, x: pd.Series, window: int = 60) -> pd.Series:
    """Hareketli beta — getiriler üzerinden (fiyat seviyeleri üzerinden
    DEĞİL; seviye regresyonu sahte bir istikrar gösterir)."""
    ry, rx = y.pct_change(), x.pct_change()
    cov = ry.rolling(window).cov(rx)
    var = rx.rolling(window).var()
    return cov / var.replace(0.0, np.nan)


def half_life(spread: pd.Series) -> float:
    """Ornstein-Uhlenbeck yarı ömrü: sapma ne kadar sürede yarıya iner.

    Δs_t = λ·s_{t-1} + ε üzerinden; λ < 0 ise ortalamaya dönüş vardır ve
    yarı ömür = -ln(2)/λ. λ >= 0 ise NaN (dönüş yok).
    """
    s = spread.dropna()
    if len(s) < 30:
        return float("nan")
    lag = s.shift(1).dropna()
    delta = (s - s.shift(1)).dropna()
    lag, delta = lag.align(delta, join="inner")
    if len(lag) < 20 or float(lag.var()) == 0.0:
        return float("nan")
    lam = float(np.polyfit(lag.to_numpy(), delta.to_numpy(), 1)[0])
    if lam >= 0:
        return float("nan")
    return float(-np.log(2.0) / lam)


# UYARI: yarı ömür TEK BAŞINA ortalamaya dönüş kanıtı DEĞİLDİR. Saf bir
# rastgele yürüyüşte bile OU regresyonu küçük negatif bir λ üretir
# (Dickey-Fuller yanlılığı) ve sonlu bir yarı ömür çıkar. Bu oturumda
# ölçüldü: bağımsız iki rastgele yürüyüşten kurulan sahte bir çift,
# yalnızca yarı ömre bakıldığında testi geçiyordu. Bu yüzden aşağıdaki
# `assess`, KORELASYONU birincil kapı sayar.


def assess(
    y: pd.Series,
    x: pd.Series,
    spread: pd.Series,
    *,
    short_window: int = 30,
    long_window: int = 250,
    beta_window: int = 60,
    min_corr: float = 0.45,
    max_corr_drop: float = 0.30,
    max_beta_std: float = 0.35,
    max_half_life: float = 45.0,
) -> PairHealth:
    """Dört ölçüyü tek bir sağlık kararına indirger."""
    ry, rx = y.pct_change(), x.pct_change()
    corr_now = float(ry.tail(short_window).corr(rx.tail(short_window)))
    corr_long = float(ry.tail(long_window).corr(rx.tail(long_window)))
    drop = (corr_long - corr_now) if np.isfinite(corr_now) and np.isfinite(corr_long) else np.nan

    beta_s = rolling_beta(y, x, beta_window).dropna()
    beta_now = float(beta_s.iloc[-1]) if len(beta_s) else float("nan")
    beta_std = float(beta_s.tail(long_window).std()) if len(beta_s) else float("nan")

    hl = half_life(spread)

    reasons: list[str] = []
    checks = 0
    passed = 0

    for ok, msg in (
        (np.isfinite(corr_now) and corr_now >= min_corr,
         f"korelasyon düşük ({corr_now:.2f} < {min_corr:.2f})"),
        (not np.isfinite(drop) or drop <= max_corr_drop,
         f"korelasyon bozuluyor (uzun {corr_long:.2f} → kısa {corr_now:.2f})"),
        (np.isfinite(beta_std) and beta_std <= max_beta_std,
         f"beta kararsız (std {beta_std:.2f} > {max_beta_std:.2f})"),
        (np.isfinite(hl) and hl <= max_half_life,
         "sapma makul sürede dönmüyor"
         if not np.isfinite(hl) else f"yarı ömür uzun ({hl:.0f} bar)"),
    ):
        checks += 1
        if ok:
            passed += 1
        else:
            reasons.append(msg)

    score = passed / checks

    # Korelasyon BİRİNCİL kapıdır. Kullanıcının çerçevesi: eşbütünleşme
    # "geçmişte anlamlı bir çift miydi", rolling korelasyon "BUGÜN hâlâ
    # birlikte hareket ediyor mu" sorusunu cevaplar. İkincisi hayırsa
    # çift işlenebilir değildir -- diğer ölçüler ne derse desin.
    corr_ok = bool(np.isfinite(corr_now) and corr_now >= min_corr)
    if not corr_ok:
        verdict = "bozulmus"
    elif score >= 0.99:
        verdict = "saglikli"
    elif score >= 0.5:
        verdict = "izlemede"
    else:
        verdict = "bozulmus"

    return PairHealth(
        corr_now=corr_now, corr_long=corr_long,
        corr_drop=float(drop) if np.isfinite(drop) else float("nan"),
        beta_now=beta_now, beta_std=beta_std, half_life=hl,
        score=score, verdict=verdict, reasons=tuple(reasons),
    )
