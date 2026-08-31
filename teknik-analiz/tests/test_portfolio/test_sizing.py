"""tlab.portfolio.sizing — FORMÜL ZİNCİRİ adım 1-8 (11/DISIPLIN-03/04,
ORAN-05)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from tlab.portfolio.sizing import (
    PositionSizingParams,
    annualised_cash_vol_target,
    compute_subsystem_position,
    compute_volatility_scalar,
    daily_cash_vol_target,
    instrument_currency_volatility,
    instrument_value_volatility,
    load_portfolio_config,
    price_volatility,
)


def test_compute_subsystem_position_matches_book_example() -> None:
    """Kabul kriteri #2: K3 Bölüm 2 örneği (WTI ham petrol, forecast=-6,
    volatility scalar=93.52) -> subsystem position. Kitap görüntülenen
    (2 ondalığa yuvarlanmış) değeri "-56.11" diye veriyor; TAM formülle
    (-6*93.52/10) sonuç -56.112'dir — testimiz TAM formülü doğrular."""
    result = compute_subsystem_position(forecast=-6, volatility_scalar=93.52)
    assert result == pytest.approx(-56.112, abs=1e-6)
    assert round(result, 2) == -56.11  # kitabın gösterdiği yuvarlanmış değer


def test_subsystem_position_equals_volatility_scalar_at_target_forecast() -> None:
    """FORMÜL ZİNCİRİ adım 8'in doğrulaması: forecast=+10 (varsayılan hedef)
    iken pozisyon TAM olarak volatility scalar'a eşit olmalı."""
    assert compute_subsystem_position(forecast=10.0, volatility_scalar=42.0) == pytest.approx(42.0)


def test_formula_chain_is_self_consistent_synthetic_example() -> None:
    """**DÜRÜST NOT**: K3 çıkarımı WTI örneğinin block_value/price_vol/fx
    ham girdilerini YAKALAMADI (yalnızca nihai volatility_scalar=93.52
    rapor edilmiş) — bu yüzden block_value->volatility_scalar zincirinin
    KENDİSİ kitabın raw sayılarıyla doğrulanamıyor. Bunun yerine, zincirin
    her adımının birbiriyle TUTARLI (kendi formülüne göre doğru)
    çalıştığını KONTROLLÜ (uydurma değil, biz seçtiğimiz) bir sentetik
    örnekle doğruluyoruz."""
    pct_vol_target = 0.20
    trading_capital = 1_000_000.0
    block_value = 1000.0
    price_vol = 1.5  # fiyat puanı/gün
    fx_rate = 1.0

    ann_target = annualised_cash_vol_target(pct_vol_target, trading_capital)
    assert ann_target == pytest.approx(200_000.0)

    daily_target = daily_cash_vol_target(ann_target)
    assert daily_target == pytest.approx(200_000.0 / 16.0)

    currency_vol = instrument_currency_volatility(price_vol, block_value)
    assert currency_vol == pytest.approx(1500.0)

    value_vol = instrument_value_volatility(currency_vol, fx_rate)
    assert value_vol == pytest.approx(1500.0)

    scalar = compute_volatility_scalar(daily_target, value_vol)
    assert scalar == pytest.approx(daily_target / 1500.0)

    forecast = 6.0
    position = compute_subsystem_position(forecast, scalar)
    assert position == pytest.approx((forecast * scalar) / 10.0)


def test_price_volatility_is_price_points_not_percent() -> None:
    """Girdiler notu: `close.diff()` bazlı (YÜZDE DEĞİL) — sabit adımlı bir
    fiyat serisinde std sıfıra yakın olmalı, büyük sabit adımlarda da
    (%'ye normalize edilmeden) fark açıkça görülebilmeli."""
    idx = pd.date_range("2024-01-01", periods=60, freq="D")
    close = pd.Series(np.linspace(100, 130, 60), index=idx)  # sabit adım
    df = pd.DataFrame({"close": close})
    vol = price_volatility(df, PositionSizingParams(vol_window=10))
    valid = vol.dropna()
    assert (valid < 1e-6).all()


def test_price_volatility_ewma_method_available() -> None:
    idx = pd.date_range("2024-01-01", periods=80, freq="D")
    rng = np.random.default_rng(5)
    close = pd.Series(100 + np.cumsum(rng.normal(0, 1, 80)), index=idx)
    df = pd.DataFrame({"close": close})
    vol = price_volatility(df, PositionSizingParams(vol_method="ewma", vol_ewma_span=20))
    assert vol.dropna().gt(0).all()


def test_load_portfolio_config_raises_when_null(tmp_path: Path) -> None:
    """`pct_vol_target`/`trading_capital` kullanıcı tarafından doldurulmadan
    (null) sessizce bir fabrika varsayımına DÜŞÜLMEMELİ."""
    cfg_path = tmp_path / "portfolio.yaml"
    payload = yaml.dump({"pct_vol_target": None, "trading_capital": None})
    cfg_path.write_text(payload, encoding="utf-8")
    with pytest.raises(ValueError):
        load_portfolio_config(cfg_path)


def test_load_portfolio_config_returns_values_when_filled(tmp_path: Path) -> None:
    cfg_path = tmp_path / "portfolio.yaml"
    cfg_path.write_text(
        yaml.dump({"pct_vol_target": 0.20, "trading_capital": 500_000.0}), encoding="utf-8"
    )
    cfg = load_portfolio_config(cfg_path)
    assert cfg["pct_vol_target"] == 0.20
    assert cfg["trading_capital"] == 500_000.0


def test_default_portfolio_yaml_is_placeholder_and_raises() -> None:
    """Repo'daki gerçek `config/portfolio.yaml` HENÜZ kullanıcı tarafından
    doldurulmadı (bkz. spec 'VERİ BAĞIMLILIĞI') — varsayılan yol da
    ValueError fırlatmalı, sessizce geçmemeli."""
    with pytest.raises(ValueError):
        load_portfolio_config()
