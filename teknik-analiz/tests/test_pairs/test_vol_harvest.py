"""pair.vol_harvest testleri: ağırlık fonksiyonu, duraklama sinyali,
kayıt (repaint_test), non-repaint payload regresyonu."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tests.test_pairs.fixtures import build_cointegrated_pair
from tlab.indicators.pairs.vol_harvest import (
    VolHarvestPair,
    VolHarvestParams,
    _target_weight_from_z,
)
from tlab.testing.repaint import repaint_test

_DEFAULT_PARAMS = VolHarvestParams(
    window=40, beta_window=40, min_periods=40, check_stride=15, vol_regime_filter=False,
)


def test_linear_weight_function_monotonic_and_clipped() -> None:
    p = VolHarvestParams(weight_fn="linear", slope=0.15, w_min=0.1, w_max=0.9)
    assert _target_weight_from_z(0.0, p) == pytest.approx(0.5)
    assert _target_weight_from_z(2.0, p) == pytest.approx(0.5 - 0.3)
    assert _target_weight_from_z(-2.0, p) == pytest.approx(0.5 + 0.3)
    # Aşırı büyük |z| -> w_min/w_max'a kırpılmalı.
    assert _target_weight_from_z(20.0, p) == pytest.approx(p.w_min)
    assert _target_weight_from_z(-20.0, p) == pytest.approx(p.w_max)


def test_grid_weight_function_steps() -> None:
    p = VolHarvestParams(
        weight_fn="grid", grid_levels=(1.0, 2.0), grid_step=0.1, w_min=0.05, w_max=0.95,
    )
    assert _target_weight_from_z(0.5, p) == pytest.approx(0.5)  # hiçbir eşik aşılmadı
    assert _target_weight_from_z(1.5, p) == pytest.approx(0.4)  # 1 eşik (1.0) aşıldı
    assert _target_weight_from_z(2.5, p) == pytest.approx(0.3)  # 2 eşik (1.0, 2.0) aşıldı
    assert _target_weight_from_z(-1.5, p) == pytest.approx(0.6)  # yön ters


def test_vol_harvest_compute_runs_on_cointegrated_pair() -> None:
    df_y, df_x = build_cointegrated_pair(n=300, seed=5)
    result = VolHarvestPair(_DEFAULT_PARAMS)(df_y, context={"x": df_x})
    assert result.last_state["rebalance_count"] >= 1
    assert 0.0 <= result.last_state["w_actual"] <= 1.0 or result.last_state["w_actual"] is None
    assert len(result.series["z"]) == len(result.series["w_target"])


def test_pause_triggers_on_broken_cointegration() -> None:
    """Y ve X'i BAĞIMSIZ (paylaşılan ortak trend yok) rastgele yürüyüşler
    yaparak eşbütünleşimi kasıtlı olarak bozar — ADF p-değeri yüksek
    kalmalı, en az bir 'harvest_paused' sinyali beklenir."""
    rng = np.random.default_rng(7)
    n = 300
    index = pd.date_range("2024-01-01", periods=n, freq="D", tz="Europe/Istanbul")
    y_close = 100.0 * np.exp(np.cumsum(rng.normal(0, 0.02, n)))
    x_close = 50.0 * np.exp(np.cumsum(rng.normal(0, 0.02, n)))

    def _ohlcv(close: np.ndarray) -> pd.DataFrame:
        open_ = np.roll(close, 1)
        open_[0] = close[0]
        high = np.maximum(open_, close) + 0.05
        low = np.minimum(open_, close) - 0.05
        return pd.DataFrame(
            {"open": open_, "high": high, "low": low, "close": close, "volume": 1000.0},
            index=index,
        )

    params = VolHarvestParams(
        window=40, beta_window=40, min_periods=40, check_stride=10,
        adf_pause_p=0.10, vol_regime_filter=False,
    )
    result = VolHarvestPair(params)(_ohlcv(y_close), context={"x": _ohlcv(x_close)})
    events = {s.payload["event"] for s in result.signals}
    assert "harvest_paused" in events


def test_registers_cleanly_with_repaint_test() -> None:
    df_y, df_x = build_cointegrated_pair(n=400, seed=3)
    report = repaint_test(
        VolHarvestPair(_DEFAULT_PARAMS), df_y, context={"x": df_x}, tail=30,
    )
    assert report.passed, report.mismatches


def test_pause_signal_payload_is_stable_at_emission_time() -> None:
    """Regresyon: pause/resume Signal'lerinin payload'ı (adf_pvalue/halflife)
    döngü SONUNDAKİ son değeri DEĞİL, sinyalin AİT OLDUĞU bardaki değeri
    taşımalı (kayıt sırasında bulunan gerçek hata — bkz. vol_harvest.py
    commit notu). Bu, tam ve kesilmiş serinin AYNI ilk pause sinyali için
    AYNI payload'ı üretmesiyle dolaylı olarak doğrulanır."""
    df_y, df_x = build_cointegrated_pair(n=300, seed=13)
    indicator = VolHarvestPair(_DEFAULT_PARAMS)
    full = indicator(df_y, context={"x": df_x})
    pause_signals = [s for s in full.signals if s.payload["event"] == "harvest_paused"]
    if not pause_signals:
        pytest.skip("bu sentetik veri hiç duraklama üretmedi")
    first_pause = pause_signals[0]
    cut = df_y.index.get_loc(first_pause.bar_time) + 5
    partial = indicator(df_y.iloc[:cut], context={"x": df_x.loc[df_x.index <= df_y.index[cut - 1]]})
    partial_pause = next(
        s for s in partial.signals if s.payload["event"] == "harvest_paused"
    )
    assert partial_pause.payload == first_pause.payload
