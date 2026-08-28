"""Çift (pair) keşfi — statik bir ekran/tarama, indikatör DEĞİLDİR.

Verilen bir sembol listesinde (varsayılan: aynı sektör) TÜM ikili kombinasyonları
tarar; korelasyon + ADF eşbütünleşme testi + yarı ömür (halflife) eşiklerinden
geçenleri "aday çift" olarak raporlar.

**KRİTİK DİSİPLİN NOTU (bilgi-bankasi/teknik/kod/ch02_pairs_arbitraj.md,
DISIPLIN-06):** `find_cointegrated_pairs` benzeri bir tarama, backtest ile
AYNI zaman penceresinde yapılırsa bu bir SEÇİM ÖNYARGISI (selection
look-ahead) türüdür — "bu çift eşbütünleşikti" iddiası kısmen gelecek
bilgisiyle kirlenmiş olur. Bu modülün çıktısı bu yüzden KALICI BİR ONAY
DEĞİL, yalnızca ANLIK BİR TARAMA sonucudur — periyodik olarak yeniden
koşulmalı ve `RelativeMomentumPair`'in kendi sinyal penceresiyle KARIŞTIRIL-
MAMALIDIR. Daha titiz bir gelecek sürüm için (Johansen/VECM, STRAT-10)
bkz. aynı dosyadaki STRAT-10 notu — bu, discovery.py'nin doğal bir sonraki
adımıdır.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from tlab.features.stats import adf_pvalue, halflife, log_spread, rolling_beta


@dataclass(frozen=True)
class PairCandidate:
    symbol_y: str
    symbol_x: str
    corr: float
    adf_pvalue: float
    halflife: float
    beta: float
    n_bars: int


def _single_beta(y_log: pd.Series, x_log: pd.Series) -> float:
    """Tüm hizalanmış pencere üzerinden TEK (sabit) OLS beta — discovery bir
    anlık tarama olduğu için rolling'e gerek yok, tüm pencere kullanılabilir."""
    window = len(y_log)
    beta_series = rolling_beta(y_log, x_log, window)
    value = beta_series.iloc[-1]
    return float(value) if not pd.isna(value) else float("nan")


def discover_pairs(
    prices: dict[str, pd.Series],
    corr_min: float = 0.7,
    adf_max: float = 0.05,
    halflife_range: tuple[float, float] = (5.0, 60.0),
    min_overlap_bars: int = 120,
    sector_map: dict[str, str] | None = None,
    same_sector_only: bool = True,
) -> list[PairCandidate]:
    """`prices`: sembol -> kapanış fiyatı Series (index datetime, hizalanmamış
    olabilir — her çift kendi içinde inner-join ile hizalanır).

    `sector_map` verilmezse VEYA bir sembol map'te YOKSA (bilinmeyen sektör),
    o sembol `same_sector_only=True` iken taramaya DAHİL EDİLMEZ (varsayılan
    sektöre atanarak uydurulmaz) — bkz. modül docstring'i, "bilmediğin
    sektörleri boş bırak" ilkesi.
    """
    symbols = sorted(prices.keys())
    candidates: list[PairCandidate] = []

    for sym_a, sym_b in itertools.combinations(symbols, 2):
        if same_sector_only:
            sector_a = (sector_map or {}).get(sym_a)
            sector_b = (sector_map or {}).get(sym_b)
            if sector_a is None or sector_b is None or sector_a != sector_b:
                continue

        # Engle-Granger regresyonu YÖN-BAĞIMLIDIR (Y~X ile X~Y, sonlu
        # örneklemde FARKLI ADF sonuçları verebilir) — ikisi de denenir,
        # eşikleri geçen (ve varsa daha düşük adf_p'li) yön raporlanır.
        best: PairCandidate | None = None
        for sym_y, sym_x in ((sym_a, sym_b), (sym_b, sym_a)):
            candidate = _evaluate_pair(
                sym_y, sym_x, prices[sym_y], prices[sym_x],
                corr_min, adf_max, halflife_range, min_overlap_bars,
            )
            if candidate is not None and (best is None or candidate.adf_pvalue < best.adf_pvalue):
                best = candidate
        if best is not None:
            candidates.append(best)

    return sorted(candidates, key=lambda c: c.adf_pvalue)


def _evaluate_pair(
    sym_y: str, sym_x: str, y_raw: pd.Series, x_raw: pd.Series,
    corr_min: float, adf_max: float, halflife_range: tuple[float, float], min_overlap_bars: int,
) -> PairCandidate | None:
    common = y_raw.index.intersection(x_raw.index)
    if len(common) < min_overlap_bars:
        return None

    y = y_raw.loc[common].astype(float)
    x = x_raw.loc[common].astype(float)
    y_log = np.log(y.where(y > 0))
    x_log = np.log(x.where(x > 0))
    if y_log.isna().any() or x_log.isna().any():
        return None

    corr = float(y_log.corr(x_log))
    if corr < corr_min:
        return None

    beta = _single_beta(y_log, x_log)
    if math.isnan(beta):
        return None
    spread = log_spread(y, x, beta)

    try:
        adf_p = adf_pvalue(spread)
    except ValueError:
        return None
    if adf_p >= adf_max:
        return None

    try:
        hl = halflife(spread)
    except ValueError:
        return None
    if not (halflife_range[0] <= hl <= halflife_range[1]):
        return None

    return PairCandidate(
        symbol_y=sym_y, symbol_x=sym_x, corr=corr, adf_pvalue=adf_p,
        halflife=hl, beta=beta, n_bars=len(common),
    )


def load_sector_map(path: str) -> dict[str, str]:
    """config/sectors_bist.yaml'ı okur: {sembol: sektor} düz sözlüğü döner.
    YAML'da sembol -> sektör YOKSA (dosyada geçmiyorsa) bu sembol map'te hiç
    bulunmaz — discover_pairs bunu 'bilinmeyen sektör' sayıp dışlar."""
    import yaml

    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    mapping: dict[str, str] = {}
    for sector, symbols in raw.get("sectors", {}).items():
        for sym in symbols or []:
            mapping[sym] = sector
    return mapping


def format_report(candidates: list[PairCandidate]) -> str:
    if not candidates:
        return "Aday çift bulunamadı (eşikleri gevşetmeyi veya evreni genişletmeyi düşünün)."
    lines = [
        f"{'Y':<8} {'X':<8} {'corr':>7} {'adf_p':>8} {'halflife':>9} {'beta':>8} {'bar':>6}",
        "-" * 58,
    ]
    for c in candidates:
        lines.append(
            f"{c.symbol_y:<8} {c.symbol_x:<8} {c.corr:>7.3f} {c.adf_pvalue:>8.4f} "
            f"{c.halflife:>9.1f} {c.beta:>8.3f} {c.n_bars:>6}"
        )
    return "\n".join(lines)
