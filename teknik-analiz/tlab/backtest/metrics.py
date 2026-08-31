"""Fitting disiplini + hız limiti (speed limit) metrikleri (Faz 10, K3/Carver
çıkarımı). Bu modül kod SEVİYESİNDE bir sinyal/indikatör DEĞİL — bir
stratejinin backtest SONUÇLARINI (Sharpe, ciro, maliyet) K3'ün disiplin
tablolarına göre DEĞERLENDİREN salt-fonksiyon araçlarıdır (bkz. `docs/spec/
tlab_10_portfolio.md`).

Kaynak: `bilgi-bankasi/teknik/11/{DISIPLIN-09..12,ORAN-08..10,PSK-01,PSK-02}`."""

from __future__ import annotations

import math
from dataclasses import dataclass

# 11/ORAN-10 (Ch.2, s.46-48) — DOĞRULANMIŞ SABİT, ulaşılabilir Sharpe beklentileri.
ACHIEVABLE_SHARPE_REFERENCE: dict[str, float] = {
    "single_stock_long": 0.15,
    "diversified_stocks_same_country": 0.20,
    "global_diversified_equity_index": 0.25,
    "multi_asset_static": 0.40,
    "single_instrument_dynamic": 0.40,
    "multi_asset_dynamic": 0.80,
    "semi_automatic_single_instrument": 0.25,
    "semi_automatic_multi_asset": 0.50,
}

# 11/ORAN-08 (Tablo 4, s.60) — DOĞRULANMIŞ SABİT: {kural_sayısı: {yıl: min_sharpe}}.
MIN_SHARPE_THRESHOLD: dict[int, dict[int, float]] = {
    1: {1: 1.5, 5: 0.7, 10: 0.5, 30: 0.4},
    5: {1: 2.3, 5: 1.1, 10: 0.8, 30: 0.5},
    10: {1: 2.8, 5: 1.2, 10: 0.8, 30: 0.6},
    50: {1: 3.4, 5: 1.5, 10: 1.0, 30: 0.6},
    100: {1: 3.4, 5: 1.5, 10: 1.1, 30: 0.7},
}

# 11/DISIPLIN-08 (Tablo 14, s.90) — DOĞRULANMIŞ SABİT, kötümserlik faktörü.
PESSIMISM_FACTOR: dict[str, float] = {
    "single_period_optimization_sharpe_in_sample": 0.25,
    "single_period_optimization_out_of_sample": 0.75,
    "bootstrapping_in_sample": 0.60,
    "bootstrapping_out_of_sample": 0.75,
    "handcrafting_no_sharpe_in_sample": 0.70,
    "handcrafting_with_sharpe_in_sample": 0.65,
}


def min_sharpe_threshold(n_rules_tested: int, years_of_data: float) -> float:
    """11/ORAN-08 — tablodaki EN KÜÇÜK (kural_sayısı, yıl) hücresine
    yuvarlar (güvenli/muhafazakâr taraf): `n_rules_tested`'den BÜYÜK-VEYA-
    EŞİT ilk sütun, `years_of_data`'dan BÜYÜK-VEYA-EŞİT ilk satır seçilir.
    Tablo dışına taşan değerler (ör. 200 kural, 50 yıl) EN BÜYÜK tanımlı
    hücreye düşer (kitap daha fazlasını vermiyor, düşürülmez)."""
    rule_keys = sorted(MIN_SHARPE_THRESHOLD)
    rule_key = next((k for k in rule_keys if n_rules_tested <= k), rule_keys[-1])
    year_table = MIN_SHARPE_THRESHOLD[rule_key]
    year_keys = sorted(year_table)
    year_key = next((y for y in year_keys if years_of_data <= y), year_keys[-1])
    return year_table[year_key]


@dataclass(frozen=True)
class SpeedLimitParams:
    cost_budget_fraction: float = 1.0 / 3.0  # 11/DISIPLIN-12
    realistic_precost_sr: float = 0.40  # 11/ORAN-10 (staunch systems trader varsayılanı)


@dataclass(frozen=True)
class SpeedLimitResult:
    cost_budget_sr_per_year: float
    speed_limit_roundtrips_per_year: float
    actual_roundtrips_per_year: float
    actual_cost_sr_per_year: float
    within_limit: bool


def speed_limit_check(
    actual_roundtrips_per_year: float,
    cost_per_roundtrip_sr: float,
    params: SpeedLimitParams | None = None,
) -> SpeedLimitResult:
    """11/DISIPLIN-12 — bir stratejinin fiili ciro/maliyet oranını hız
    limitine göre değerlendirir. `cost_per_roundtrip_sr`: TEK bir round-trip
    işlemin Sharpe-birimindeki maliyeti (enstrümana özgü, DIŞARIDAN verilir
    — kitap yalnızca TEK bir örnek enstrüman için değer veriyor, TÜM
    enstrümanlar için genellenebilir sabit bir tablo YOK).

    **DÜRÜST NOT**: kitabın kendi Euro Stoxx örneği ("hız limiti = 0.13/
    0.002 = yılda 65 round-trip") görüntülenen (2 ondalığa YUVARLANMIŞ)
    `0.13` değerini kullanır; bu fonksiyon TAM kesirle (`1/3 × 0.40 =
    0.1333...`) hesaplar — sonuç `≈66.67` olur, kitabın kendi yuvarlama
    zincirinin ARTEFAKTI olan `65` DEĞİL (bkz. testler)."""
    p = params or SpeedLimitParams()
    cost_budget = p.cost_budget_fraction * p.realistic_precost_sr
    speed_limit = cost_budget / cost_per_roundtrip_sr if cost_per_roundtrip_sr > 0 else math.inf
    actual_cost_sr = actual_roundtrips_per_year * cost_per_roundtrip_sr
    return SpeedLimitResult(
        cost_budget_sr_per_year=cost_budget,
        speed_limit_roundtrips_per_year=speed_limit,
        actual_roundtrips_per_year=actual_roundtrips_per_year,
        actual_cost_sr_per_year=actual_cost_sr,
        within_limit=actual_roundtrips_per_year <= speed_limit,
    )
