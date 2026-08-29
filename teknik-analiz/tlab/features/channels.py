"""Kanal araçları: regresyon kanalı, pivot kanalı, dondurulmuş kanal, konum.

Non-repaint: `regression_channel`'da bar `t`'nin kanalı yalnızca [t-n+1, t]
penceresinden hesaplanır (trailing OLS) — pencere kaydıkça geçmiş bar `t`'nin
kendi kanal değeri bir daha DEĞİŞMEZ (fixed-window OLS, sonradan gelen barlar
geçmiş fit'i etkilemez). `pivot_channel` trendlines.build_trendlines ile AYNI
"aday havuzu" + extend-only touches/broken_at mimarisini paylaşır (bkz. o
modülün docstring'i — hangi (p1,p2) çiftinin öne çıkacağı df büyüdükçe
değişebilir, bu bir repaint hatası DEĞİLDİR).

`RegressionChannel` dataclass'ı (mid/upper/lower pd.Series) genel bir "bant"
kabı olarak `channel_position`'da hem regresyon hem pivot kanalları için
yeniden kullanılır (bkz. `pivot_channel_series`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

from tlab.features.swings import Pivot
from tlab.features.volatility import atr

ChannelBreakDirection = Literal["up", "down"]


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


@dataclass(frozen=True)
class FrozenChannel:
    """`regression_channel`'ın t barındaki fit'ini [t-n+1, t] uçlu iki
    noktalı bir çizgi setine dondurur — indikatör bunu sinyal barında
    extend_right=False bir Line olarak çizip bir daha GÜNCELLEMEMELİDİR
    (bkz. Faz 8C weekly_channel). mid/upper/lower her biri (t0_değeri,
    t1_değeri) çifti; regression_channel(df,n,k).{mid,upper,lower}.iloc[t]
    ile t1_değeri BİREBİR eşleşir (aynı OLS fit'i, yalnızca uç noktaları
    açık taşır)."""

    t0: pd.Timestamp
    t1: pd.Timestamp
    mid: tuple[float, float]
    upper: tuple[float, float]
    lower: tuple[float, float]


def frozen_channel_at(df: pd.DataFrame, t: int, n: int = 100, k: float = 2.0) -> FrozenChannel:
    """`regression_channel`ın t barındaki OLS fit'ini bağımsız olarak yeniden
    hesaplayıp [t-n+1, t] pencerenin İKİ UCUNDAKİ değerlerle döner (t1 ucu,
    aynı parametrelerle regression_channel(df,n,k)'nin t'deki değerine eşit
    olmalı — bkz. testler). t < n-1 ise ValueError (yetersiz pencere)."""
    if t < n - 1:
        raise ValueError(f"t={t} için [t-n+1, t] penceresi df'nin başından taşıyor (n={n})")

    close = df["close"].to_numpy(dtype=float)
    log_close = np.log(close)
    t0_idx = t - n + 1
    window = log_close[t0_idx : t + 1]

    x = np.arange(n, dtype=float)
    x_mean = x.mean()
    x_centered = x - x_mean
    x_var = float((x_centered**2).sum())
    y_mean = window.mean()
    slope = float((x_centered * (window - y_mean)).sum() / x_var)
    intercept = y_mean - slope * x_mean
    fitted = slope * x + intercept
    resid_std = float((window - fitted).std(ddof=0))

    mid_log0, mid_log1 = intercept, slope * (n - 1) + intercept
    return FrozenChannel(
        t0=df.index[t0_idx],
        t1=df.index[t],
        mid=(float(np.exp(mid_log0)), float(np.exp(mid_log1))),
        upper=(float(np.exp(mid_log0 + k * resid_std)), float(np.exp(mid_log1 + k * resid_std))),
        lower=(float(np.exp(mid_log0 - k * resid_std)), float(np.exp(mid_log1 - k * resid_std))),
    )


@dataclass(frozen=True)
class Channel:
    """İki onaylı swing low'dan (p1,p2) geçen alt çizgi + p1..p2 aralığındaki
    en yüksek high'a teğet, alt çizgiye PARALEL üst çizgi. Ofset (üst-alt
    dikey mesafe) created_idx'te (p2.confirmed_idx) SABİTLENİR — sonradan
    gelen daha yüksek bir high bu kanalı GENİŞLETMEZ (trendlines.Trendline
    ile aynı "bir kez kurulur, extend-only izlenir" mimarisi)."""

    p1: Pivot
    p2: Pivot
    slope: float
    lower_intercept: float
    upper_intercept: float
    created_idx: int
    upper_touches: tuple[int, ...]
    lower_touches: tuple[int, ...]
    broken_at: int | None
    broken_direction: ChannelBreakDirection | None

    def lower_at(self, idx: int) -> float:
        return self.slope * idx + self.lower_intercept

    def upper_at(self, idx: int) -> float:
        return self.slope * idx + self.upper_intercept


def pivot_channel(
    df: pd.DataFrame,
    pivots: list[Pivot],
    tol_atr: float = 0.3,
    confirm_bars: int = 1,
    atr_period: int = 14,
    max_channels: int | None = None,
) -> list[Channel]:
    """Onaylı swing low ikililerinden (p1,p2) kanal adayları kurar; alt
    çizgi p1->p2, üst çizgi [p1.bar_idx, created_idx] aralığındaki en yüksek
    high'a teğet paralel çizgidir. created_idx'ten (p2.confirmed_idx) itibaren
    bar-bar izlenir: TEMAS ilgili sınıra tol_atr*ATR içinde ve henüz aşılmamış;
    KIRILIM kapanış bir sınırın ötesinde `confirm_bars` ardışık barda (üst
    kırılım ve alt kırılım ayrı sayaçlarla izlenir, ikisi aynı anda
    olamayacağı için çakışma yok). Kırılan kanal için izleme durur.

    max_channels verilirse kırılmamış + en çok toplam temaslı + en uzun
    süreli öncelikli sıralamayla üstten kesilir (build_trendlines._select_top
    ile aynı sezgi)."""
    lows = sorted((p for p in pivots if p.kind == "low"), key=lambda p: p.bar_idx)
    n = len(df)
    atr_series = atr(df, atr_period)
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    close = df["close"].to_numpy()

    channels: list[Channel] = []
    for i, p1 in enumerate(lows):
        for p2 in lows[i + 1 :]:
            if p2.bar_idx == p1.bar_idx:
                continue
            slope = (p2.price - p1.price) / (p2.bar_idx - p1.bar_idx)
            lower_intercept = p1.price - slope * p1.bar_idx
            created_idx = p2.confirmed_idx
            if created_idx >= n:
                continue

            offset = max(
                high[bi] - (slope * bi + lower_intercept)
                for bi in range(p1.bar_idx, created_idx + 1)
            )
            if offset <= 0:
                continue
            upper_intercept = lower_intercept + offset

            upper_touches: list[int] = []
            lower_touches: list[int] = []
            broken_at: int | None = None
            broken_direction: ChannelBreakDirection | None = None
            streak_up = 0
            streak_down = 0

            for t in range(created_idx, n):
                a = atr_series.iloc[t]
                if pd.isna(a):
                    continue
                tol = tol_atr * a
                lower_val = slope * t + lower_intercept
                upper_val = slope * t + upper_intercept

                if close[t] > upper_val:
                    streak_up += 1
                    streak_down = 0
                    if streak_up >= confirm_bars:
                        broken_at, broken_direction = t, "up"
                        break
                elif close[t] < lower_val:
                    streak_down += 1
                    streak_up = 0
                    if streak_down >= confirm_bars:
                        broken_at, broken_direction = t, "down"
                        break
                else:
                    streak_up = 0
                    streak_down = 0
                    if abs(high[t] - upper_val) <= tol:
                        upper_touches.append(t)
                    if abs(low[t] - lower_val) <= tol:
                        lower_touches.append(t)

            channels.append(
                Channel(
                    p1=p1,
                    p2=p2,
                    slope=slope,
                    lower_intercept=lower_intercept,
                    upper_intercept=upper_intercept,
                    created_idx=created_idx,
                    upper_touches=tuple(upper_touches),
                    lower_touches=tuple(lower_touches),
                    broken_at=broken_at,
                    broken_direction=broken_direction,
                )
            )

    if max_channels is not None:
        channels = _select_top_channels(channels, max_channels)
    return channels


def _select_top_channels(channels: list[Channel], max_channels: int) -> list[Channel]:
    def sort_key(ch: Channel) -> tuple[int, int, int]:
        broken_rank = 0 if ch.broken_at is None else 1
        n_touches = len(ch.upper_touches) + len(ch.lower_touches)
        last_bar = ch.broken_at if ch.broken_at is not None else max(
            (ch.upper_touches[-1] if ch.upper_touches else ch.created_idx),
            (ch.lower_touches[-1] if ch.lower_touches else ch.created_idx),
        )
        duration = last_bar - ch.created_idx
        return (broken_rank, -n_touches, -duration)

    return sorted(channels, key=sort_key)[:max_channels]


def pivot_channel_series(df: pd.DataFrame, channel: Channel) -> RegressionChannel:
    """`Channel`'ı (index-tabanlı slope/intercept) mid/upper/lower pd.Series
    'e çevirir — `channel_position` ve dış tüketiciler regression/pivot
    kanalıyla AYNI arayüzü kullanabilsin diye. created_idx'ten önceki barlar
    NaN'dır (kanal henüz yok)."""
    n = len(df)
    idx = df.index
    lower = np.full(n, np.nan)
    upper = np.full(n, np.nan)
    mid = np.full(n, np.nan)
    for t in range(channel.created_idx, n):
        lo, hi = channel.lower_at(t), channel.upper_at(t)
        lower[t], upper[t], mid[t] = lo, hi, (lo + hi) / 2
    return RegressionChannel(
        mid=pd.Series(mid, index=idx),
        upper=pd.Series(upper, index=idx),
        lower=pd.Series(lower, index=idx),
    )


def channel_position(df: pd.DataFrame, channel: RegressionChannel) -> pd.Series:
    """close'un kanal içindeki konumu: 0=alt sınır, 1=üst sınır. Sınırlama
    (clip) YAPILMAZ — fiyat kanal dışına taştığında <0 veya >1 döner (bu,
    kırılım tespitine bilgi kaybetmeden bırakılır). upper==lower olan
    (dejenere) barlarda NaN."""
    span = channel.upper - channel.lower
    return (df["close"] - channel.lower) / span.replace(0.0, np.nan)
