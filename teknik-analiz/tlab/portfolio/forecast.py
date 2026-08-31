"""Forecast birleştirme: scalar/cap ZATEN uygulanmış kural forecast'larını
(ör. `trend.ewmac`'in `series["ewmac_combined"]`si) TEK bir kombine
forecast'a indirger (Faz 10, K3/Carver çıkarımı).

Kaynak: `bilgi-bankasi/teknik/11/{KURAL-01,ORAN-01,ORAN-02,ORAN-03,ORAN-04,
DISIPLIN-01,DISIPLIN-02}`. Zincir (11/DISIPLIN-02): ağırlıklı ortalama →
diversification multiplier (`risk.py::diversification_multiplier`, rolling
korelasyon — yalnızca t ve öncesi, non-repaint) → `[-cap,+cap]` kırpma."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from tlab.core.params import BaseParams
from tlab.portfolio.risk import diversification_multiplier


@dataclass(frozen=True)
class CombineForecastsParams(BaseParams):
    target_abs_forecast: float = 10.0  # 11/KURAL-01
    cap: float = 20.0  # 11/KURAL-01
    max_diversification_multiplier: float = 2.5  # 11/ORAN-02
    # TASARIM KARARI — kaynak atfı YOK: K3 kitap-metni forecast'lar arası
    # rolling korelasyon için spesifik bir pencere vermiyor; `xsec.
    # rolling_alpha_beta`'nın (Faz 8D) kullandığı orta-vadeli pencerelerle
    # tutarlı bir varsayılan seçildi.
    correlation_window: int = 120


def combine_forecasts(
    forecasts: dict[str, pd.Series],
    forecast_weights: dict[str, float],
    params: CombineForecastsParams | None = None,
) -> pd.Series:
    """11/DISIPLIN-02 zinciri. `forecast_weights` toplamı 1.0 (±1e-6) OLMALI,
    aksi halde `ValueError` (KURAL-02'nin "ağırlıklar toplamı %100" şartı).

    Tek kural verildiğinde (`forecast_weights={rule: 1.0}`) çeşitlendirme
    çarpanı TANIM GEREĞİ 1.0'dır (rolling korelasyona hiç GEREK yok) — çıktı,
    girdi forecast'ın (zaten scalar/cap uygulanmış olduğu varsayılarak)
    `[-cap,+cap]`e kırpılmış AYNISI olur."""
    p = params or CombineForecastsParams()
    total_w = sum(forecast_weights.values())
    if abs(total_w - 1.0) > 1e-6:
        raise ValueError(f"forecast_weights toplamı 1.0 olmalı, {total_w} bulundu")
    if set(forecast_weights) != set(forecasts):
        raise ValueError("forecast_weights ve forecasts anahtarları eşleşmeli")

    names = list(forecast_weights.keys())
    df = pd.concat({name: forecasts[name] for name in names}, axis=1)
    w = np.array([forecast_weights[name] for name in names], dtype=float)
    raw_combined = df.mul(w, axis=1).sum(axis=1)

    if len(names) == 1:
        return raw_combined.clip(-p.cap, p.cap)

    multiplier = pd.Series(np.nan, index=df.index)
    win = p.correlation_window
    for t in range(win - 1, len(df)):
        window_df = df.iloc[t - win + 1 : t + 1]
        corr = window_df.corr().to_numpy()
        if np.isnan(corr).any():
            continue
        multiplier.iloc[t] = diversification_multiplier(w, corr, p.max_diversification_multiplier)

    return (raw_combined * multiplier).clip(-p.cap, p.cap)
