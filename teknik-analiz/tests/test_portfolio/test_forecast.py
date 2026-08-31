"""tlab.portfolio.forecast — 11/DISIPLIN-02 (kombine forecast zinciri)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tlab.portfolio.forecast import CombineForecastsParams, combine_forecasts
from tlab.portfolio.risk import diversification_multiplier

_IDX = pd.date_range("2024-01-01", periods=200, freq="D")


def _make_forecast(seed: int, scale: float = 8.0) -> pd.Series:
    rng = np.random.default_rng(seed)
    raw = rng.normal(0, scale, size=len(_IDX))
    return pd.Series(raw, index=_IDX).clip(-20, 20)


def test_single_rule_weight_one_returns_input_unchanged() -> None:
    """Kabul kriteri #1: tek kural, weight=1.0 -> girdi forecast'ın (zaten
    scalar/cap uygulanmış varsayılarak) AYNISI, çeşitlendirme multiplier'ı
    hesaba HİÇ girmeden (tanım gereği 1.0)."""
    f = _make_forecast(1)
    out = combine_forecasts({"rule_a": f}, {"rule_a": 1.0})
    pd.testing.assert_series_equal(out, f.clip(-20, 20), check_names=False)


def test_weights_must_sum_to_one() -> None:
    f = _make_forecast(1)
    with pytest.raises(ValueError):
        combine_forecasts({"rule_a": f}, {"rule_a": 0.5})


def test_forecast_and_weight_keys_must_match() -> None:
    f = _make_forecast(1)
    with pytest.raises(ValueError):
        combine_forecasts({"rule_a": f}, {"rule_b": 1.0})


def test_combined_forecast_matches_manual_diversification_multiplier() -> None:
    """İki KISMEN korelasyonlu forecast serisi — bir bardaki kombine değeri,
    o bardaki trailing pencerenin GERÇEK korelasyonundan elle hesaplanan
    diversification multiplier'la BİREBİR eşleşmeli."""
    rng = np.random.default_rng(7)
    base = rng.normal(0, 6, size=len(_IDX))
    noise = rng.normal(0, 6, size=len(_IDX))
    f_a = pd.Series(base, index=_IDX).clip(-20, 20)
    f_b = pd.Series(0.6 * base + 0.4 * noise, index=_IDX).clip(-20, 20)

    params = CombineForecastsParams(correlation_window=60)
    out = combine_forecasts({"a": f_a, "b": f_b}, {"a": 0.5, "b": 0.5}, params)

    t = 150
    window = pd.concat({"a": f_a, "b": f_b}, axis=1).iloc[t - 59 : t + 1]
    corr = window.corr().to_numpy()
    w = np.array([0.5, 0.5])
    expected_mult = diversification_multiplier(w, corr, params.max_diversification_multiplier)
    raw = 0.5 * f_a.iloc[t] + 0.5 * f_b.iloc[t]
    expected = float(np.clip(raw * expected_mult, -params.cap, params.cap))
    assert out.iloc[t] == pytest.approx(expected, abs=1e-9)


def test_prefix_consistency_no_lookahead() -> None:
    """Standart BaseIndicator repaint_test bu fonksiyona doğrudan
    UYGULANAMAZ (forecast serisi üzerinde çalışır, IndicatorResult
    üretmez) — bu yüzden `features/*.py` desenindeki (bkz. CLAUDE.md) gibi
    hedefli bir walk-forward tutarlılık testi: kesik bir seride hesaplanan
    HER değer, tam seride AYNI barda hesaplanan değerle BİREBİR eşleşmeli."""
    rng = np.random.default_rng(3)
    f_a = pd.Series(rng.normal(0, 6, size=len(_IDX)), index=_IDX).clip(-20, 20)
    f_b = pd.Series(rng.normal(0, 6, size=len(_IDX)), index=_IDX).clip(-20, 20)
    params = CombineForecastsParams(correlation_window=40)

    full = combine_forecasts({"a": f_a, "b": f_b}, {"a": 0.5, "b": 0.5}, params)

    cut = 120
    partial = combine_forecasts(
        {"a": f_a.iloc[: cut + 1], "b": f_b.iloc[: cut + 1]}, {"a": 0.5, "b": 0.5}, params
    )
    pd.testing.assert_series_equal(partial, full.iloc[: cut + 1], check_names=False)
