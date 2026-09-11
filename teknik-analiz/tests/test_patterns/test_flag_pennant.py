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
from tlab.core.types import Timeframe
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


def test_for_timeframe_widens_flag_atr_on_h4() -> None:
    """docs/KALAN_ISLER.md madde 3 -- `breakout_fvg.py`'nin AYNI kök
    nedeni: `flag_atr` bir ORAN, `_BAR_FIELDS` DEĞİL, `flag_min_bars`in
    D1->4H ölçeklemesi (5->15, ×3) `flag_atr`ı (1.5) SABİT bırakıyordu --
    648 sembollik gerçek `tlab eod` koşusunda 4H = 3 aday/1 sembol
    (D1 = 3403/593) olarak DOĞRULANDI. D1 (scale=1.0) DEĞİŞMEMELİ."""
    base = FlagPennantParams()
    d1 = base.for_timeframe(Timeframe.D1)
    h4 = base.for_timeframe(Timeframe.H4)
    assert d1.flag_atr == base.flag_atr == 1.5
    assert h4.flag_atr > base.flag_atr
    assert h4.flag_min_bars == base.flag_min_bars * 3


def test_is_htf_false_for_normal_sized_pole() -> None:
    """docs/KALAN_ISLER.md madde 2.3 -- `_pole_then_flat_flag_ohlcv`'nin
    direği ~%18 (varsayılan `htf_pct=0.30`'un altında), HTF SAYILMAMALI."""
    df = _pole_then_flat_flag_ohlcv()
    params = FlagPennantParams(
        pole_bars=4, pole_atr=1.5, flag_min_bars=5, flag_max_bars=15, flag_atr=2.0,
    )
    result = FlagPennantIndicator(params)(df)
    assert result.last_state
    assert all(info["is_htf"] is False for info in result.last_state.values())
    assert all(s.payload.get("is_htf") is False for s in result.signals)


def test_marks_is_htf_when_pole_far_exceeds_threshold() -> None:
    """AYNI fixture, `htf_pct` KASITLI OLARAK direğin kendi büyüklüğünün
    (~%18) altına çekildi -- `is_htf` hem `last_state`de hem sinyal
    payload'ında True olmalı (extra_payload'ın TÜM sinyallere yayıldığı
    doğrulanır, `pattern_state.py::track_breakout_pattern`)."""
    df = _pole_then_flat_flag_ohlcv()
    params = FlagPennantParams(
        pole_bars=4, pole_atr=1.5, flag_min_bars=5, flag_max_bars=15, flag_atr=2.0,
        htf_pct=0.10,
    )
    result = FlagPennantIndicator(params)(df)
    assert result.last_state
    assert all(info["is_htf"] is True for info in result.last_state.values())
    assert result.signals
    assert all(s.payload.get("is_htf") is True for s in result.signals)


def test_no_target_or_entry_marker_while_still_pending() -> None:
    """K3 düzeltmesi (2026-09-05, bkz. docs/GORSEL_HATA_TESHISI.md):
    `confirm_signal()` None dönerse (aday hiç kırılmadan, hâlâ PENDING) ne
    hedef Level'i ne AL/SAT/KIRILIM/ONAY/HEDEF marker'ı üretilmemeli --
    `_pole_then_flat_flag_ohlcv`in df'i, kırılım (idx20+) barlarından ÖNCE
    kesilir."""
    df = _pole_then_flat_flag_ohlcv().iloc[:20]
    params = FlagPennantParams(
        pole_bars=4, pole_atr=1.5, flag_min_bars=5, flag_max_bars=15, flag_atr=2.0,
    )
    result = FlagPennantIndicator(params)(df)
    assert result.last_state
    assert all(info["state"] == "pending" for info in result.last_state.values())
    assert not any(lv.style == "pattern_target" for lv in result.levels)
    for prefix in (
        "pattern_entry_", "pattern_breakout:", "pattern_retest_ok:", "pattern_target_hit:",
    ):
        assert not any(m.kind.startswith(prefix) for m in result.markers)


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
