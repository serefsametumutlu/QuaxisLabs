"""patterns.flag_pennant testleri. Direk tespiti `zones_sd.find_impulses`'in
DOĞRUDAN kullanımı olduğu için (zaten test_zones_sd.py'de doğrulandı) burada
odak: (1) direk sonrası dar/sakin bir konsolidasyonun gerçekten PENDING
ürettiği elle inşa edilmiş bir senaryo, (2) gerçekçi veride çökmeden
çalışma + geçerli sinyal sözleşmesi."""

from __future__ import annotations

import numpy as np
import pandas as pd

from tests.test_structure.fixtures import build_registry_smoke_ohlcv
from tlab.core.errors import RegistryError
from tlab.core.indicator import registry
from tlab.indicators.patterns.flag_pennant import FlagPennantIndicator, FlagPennantParams
from tlab.testing.fixtures import make_trend

_TZ = "Europe/Istanbul"


def _pole_then_flat_flag_ohlcv() -> pd.DataFrame:
    """0-9: sakin taban. 10-14: güçlü yukarı direk (net ~+18, ATR'ye göre
    büyük). 15-19: dar/yatay konsolidasyon (bayrak). 20+: direk yönünde
    kırılım + devam."""
    closes = [100.0] * 10
    closes += list(np.linspace(100, 118, 6))[1:]  # direk: idx10..14
    closes += [117.5, 118.2, 117.8, 118.3, 117.9]  # bayrak: idx15..19
    closes += list(np.linspace(118, 135, 8))[1:]  # kırılım + devam
    close = np.array(closes)
    n = len(close)
    index = pd.date_range("2024-01-02", periods=n, freq="1D", tz=_TZ)
    open_ = np.empty_like(close)
    open_[0] = close[0]
    open_[1:] = close[:-1]
    high = np.maximum(open_, close) + 0.15
    low = np.minimum(open_, close) - 0.15
    volume = np.concatenate([
        np.full(10, 1000.0), np.full(5, 5000.0), np.full(5, 800.0), np.full(7, 4000.0),
    ])
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume}, index=index
    )


def test_finds_bull_flag_after_pole_and_confirms_breakout() -> None:
    df = _pole_then_flat_flag_ohlcv()
    params = FlagPennantParams(
        pole_bars=4, pole_atr=1.5, flag_min_bars=5, flag_max_bars=15, flag_atr=2.0,
    )
    result = FlagPennantIndicator(params)(df)
    confirmed = [
        s for s in result.signals
        if s.payload["event"].endswith("_confirmed") and s.direction == "long"
    ]
    assert confirmed, "yukarı yönlü direk sonrası bir bayrak/flama kırılımı beklenirdi"
    assert confirmed[0].payload["pattern_name"] in ("bayrak", "flama")


def test_runs_and_produces_valid_signal_contract() -> None:
    df = make_trend(n=200, slope=0.06, noise=1.3, seed=31)
    result = FlagPennantIndicator(FlagPennantParams())(df)
    assert result.indicator == "patterns.flag_pennant"
    for sig in result.signals:
        assert sig.payload["pattern_name"] in ("bayrak", "flama")
        assert "target" in sig.payload


def test_registers_via_verified_elsewhere() -> None:
    df = build_registry_smoke_ohlcv()
    try:
        registry.register_verified_elsewhere(FlagPennantIndicator())
    except RegistryError as exc:
        if "zaten kayıtlı" not in str(exc):
            raise
    assert registry.get("patterns.flag_pennant") is FlagPennantIndicator
    FlagPennantIndicator()(df)
