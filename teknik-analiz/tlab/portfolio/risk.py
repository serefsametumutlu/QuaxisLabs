"""Portföy riski: diversification multiplier, position inertia, nihai
enstrüman pozisyonu (Faz 10, K3/Carver çıkarımı).

Kaynak atıfları `bilgi-bankasi/teknik/11/<KOD>` biçiminde (bilanco-radar
repo, `bilgi-bankasi/teknik/11_carver_systematic.md`):
- `diversification_multiplier`: 11/ORAN-03 (kesin formül + Tablo 18)
- `round_target_position`/`apply_position_inertia`: 11/"FORMÜL ZİNCİRİ"
  (Bölüm 2, adım 12-13)
- `portfolio_instrument_position`: 11/"FORMÜL ZİNCİRİ" adım 11

Bu formül AYNI zamanda `forecast.py`'nin forecast diversification
multiplier'ı için de kullanılır (11/ORAN-03: "HEM forecast HEM instrument
diversification multiplier için AYNI formül, girdi matrisi değişir")."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from tlab.core.params import BaseParams


@dataclass(frozen=True)
class PortfolioRiskParams(BaseParams):
    max_diversification_multiplier: float = 2.5  # 11/ORAN-02, ORAN-03
    position_inertia_pct: float = 0.10  # 11/"FORMÜL ZİNCİRİ" adım 13


def diversification_multiplier(
    weights: np.ndarray | pd.Series,
    corr_matrix: np.ndarray | pd.DataFrame,
    max_multiplier: float = 2.5,
) -> float:
    """11/ORAN-03 kesin formülü: `1 / sqrt(W · H · Wᵀ)`. Negatif korelasyonlar
    hesap ÖNCESİ sıfıra taban değeri verilir (kitabın açık şartı — aksi halde
    çarpan tehlikeli derecede şişer). Sonuç `max_multiplier`e (varsayılan 2.5,
    11/ORAN-02) kırpılır."""
    w = np.asarray(weights, dtype=float)
    h = np.asarray(corr_matrix, dtype=float)
    if w.ndim != 1 or h.shape != (len(w), len(w)):
        raise ValueError("weights uzunluğu corr_matrix boyutuyla eşleşmeli")
    h = np.clip(h, 0.0, None)
    variance = float(w @ h @ w)
    if variance <= 0:
        return max_multiplier
    return min(1.0 / math.sqrt(variance), max_multiplier)


def round_target_position(position: float) -> int:
    """11/"FORMÜL ZİNCİRİ" adım 12 — İLK ve TEK yuvarlama noktası (önceki
    hiçbir adımda yuvarlama YAPILMAZ)."""
    return int(round(position))


def apply_position_inertia(
    current_position: float, target_position: float, inertia_pct: float = 0.10
) -> float:
    """11/"FORMÜL ZİNCİRİ" adım 13 — güncel pozisyon, hedefin `inertia_pct`
    içindeyse (bant genişliği = `inertia_pct * |target|`) İŞLEM YAPILMAZ,
    güncel pozisyon KORUNUR; aksi halde hedefe geçilir. `target_position=0`
    dejenere durumunda bant sıfırdır (herhangi bir açık pozisyon kapatılır —
    kitap bu kenar durumu için ayrı bir kural vermiyor, "hedefin İÇİNDE"
    tanımının doğal uzantısı)."""
    band = inertia_pct * abs(target_position)
    if abs(current_position - target_position) <= band:
        return current_position
    return target_position


def portfolio_instrument_position(
    subsystem_position: float,
    instrument_weight: float,
    instrument_diversification_multiplier: float,
) -> float:
    """11/"FORMÜL ZİNCİRİ" adım 11 — `subsystem_position × instrument_weight ×
    instrument_diversification_multiplier`. Yuvarlama BURADA yapılmaz (adım
    12, `round_target_position` AYRI çağrılır)."""
    return subsystem_position * instrument_weight * instrument_diversification_multiplier
