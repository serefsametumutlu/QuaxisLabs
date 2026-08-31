"""Volatilite hedefleme + pozisyon boyutlama: forecast'tan alt-sistem
(subsystem) pozisyonuna (Faz 10, K3/Carver çıkarımı).

Kaynak: `bilgi-bankasi/teknik/11/{DISIPLIN-03,DISIPLIN-04,ORAN-05}` +
"FORMÜL ZİNCİRİ" (Bölüm 2, adım 1-8). `config/portfolio.yaml`'dan okunan
`pct_vol_target`/`trading_capital` kullanıcıya özgü risk parametreleridir —
bkz. `load_portfolio_config`."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from tlab.core.params import BaseParams

ANNUALIZATION_SQRT_DIVISOR = 16.0  # 11/ORAN-05 (256 iş günü varsayımı -> sqrt(256)=16)

_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "portfolio.yaml"


@dataclass(frozen=True)
class PositionSizingParams(BaseParams):
    vol_window: int = 25  # 11/ORAN-05 (basit hareketli ortalama)
    vol_method: str = "sma"  # "sma" | "ewma"
    vol_ewma_span: int = 36  # 11/ORAN-05 (eşdeğer EWMA)
    annualization_sqrt_divisor: float = ANNUALIZATION_SQRT_DIVISOR
    target_abs_forecast: float = 10.0  # 11/KURAL-01 (subsystem position formülü)


def price_volatility(df: pd.DataFrame, params: PositionSizingParams | None = None) -> pd.Series:
    """Günlük fiyat oynaklığı — FİYAT PUANI cinsinden (`close.diff()` bazlı,
    YÜZDE DEĞİL). `block_value` (para/puan) ile çarpılıp para birimi riskine
    çevrileceği için (FORMÜL ZİNCİRİ adım 2-3) tlab'ın diğer %-getiri tabanlı
    göstergelerinden (`features/volatility.py::realized_vol`) KASITLI OLARAK
    farklı bir birim taşır."""
    p = params or PositionSizingParams()
    diff = df["close"].diff()
    if p.vol_method == "ewma":
        return diff.ewm(span=p.vol_ewma_span, min_periods=p.vol_ewma_span).std()
    return diff.rolling(p.vol_window, min_periods=p.vol_window).std()


def instrument_currency_volatility(
    price_vol: pd.Series | float, block_value: float
) -> pd.Series | float:
    """FORMÜL ZİNCİRİ adım 3. Spot enstrümanlar (BIST hisse/kripto) için
    `block_value=1.0` basitleştirmesi kullanılabilir (bkz. spec, "VERİ
    BAĞIMLILIĞI" — vadeli işlem/kaldıraç çarpanları bu projenin kapsamı DIŞI)."""
    return price_vol * block_value


def instrument_value_volatility(
    currency_vol: pd.Series | float, fx_rate: float = 1.0
) -> pd.Series | float:
    """FORMÜL ZİNCİRİ adım 4 — hesap para birimine çevrilir. Aynı para
    biriminde işlem gören enstrümanlar için `fx_rate=1.0` varsayılan."""
    return currency_vol * fx_rate


def annualised_cash_vol_target(pct_vol_target: float, trading_capital: float) -> float:
    """FORMÜL ZİNCİRİ adım 5 (11/DISIPLIN-03/04)."""
    return pct_vol_target * trading_capital


def daily_cash_vol_target(
    annualised_target: float, divisor: float = ANNUALIZATION_SQRT_DIVISOR
) -> float:
    """FORMÜL ZİNCİRİ adım 6 (11/ORAN-05)."""
    return annualised_target / divisor


def compute_volatility_scalar(
    daily_target: float, instrument_value_vol: pd.Series | float
) -> pd.Series | float:
    """FORMÜL ZİNCİRİ adım 7 — forecast'tan BAĞIMSIZ saf risk-eşleme çarpanı
    ("tüm sermayeyi TEK enstrümana yatırsaydın kaç blok tutman gerekirdi")."""
    return daily_target / instrument_value_vol


def compute_subsystem_position(
    forecast: pd.Series | float,
    volatility_scalar: pd.Series | float,
    target_abs_forecast: float = 10.0,
) -> pd.Series | float:
    """FORMÜL ZİNCİRİ adım 8 — `(forecast × volatility_scalar) / target_abs_
    forecast`. forecast=+target_abs_forecast (varsayılan +10) iken pozisyon
    TAM olarak volatility_scalar'a eşittir."""
    return (forecast * volatility_scalar) / target_abs_forecast


def load_portfolio_config(path: Path | None = None) -> dict[str, Any]:
    """`config/portfolio.yaml`'dan `pct_vol_target`/`trading_capital` okur.
    Biri doldurulmamışsa (null) AÇIK bir `ValueError` fırlatır — sessizce
    fabrika varsayımına DÜŞÜLMEZ (bu ikisi kullanıcının hesap büyüklüğü/risk
    toleransı — dışsal bir girdi, bkz. spec 'VERİ BAĞIMLILIĞI')."""
    p = path or _DEFAULT_CONFIG_PATH
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    for key in ("pct_vol_target", "trading_capital"):
        if data.get(key) is None:
            raise ValueError(
                f"config/portfolio.yaml'da '{key}' ayarlanmamış — kullanıcı kendi risk "
                "toleransına göre doldurmalı (bkz. 11/DISIPLIN-03, Tablo 25/26)."
            )
    return data
