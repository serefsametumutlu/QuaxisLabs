"""patterns.breakout_fvg testleri — YENİ strateji (Faz 4b). `_find_
consolidation_box`/`_find_fvg` saf/deterministik fonksiyonlar oldukları
için doğrudan (whitebox) test edilir; asıl ilgi tam zincirin (konsolidasyon
→ kırılım → FVG → retest → onay) elle inşa edilmiş bir senaryoda uçtan uca
DOĞRU sırayla ilerlediği ve gerçekçi/gürültülü veride çökmeden çalıştığıdır
(`test_wedge.py`/`test_broadening.py` ile AYNI felsefe)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from tests.test_structure.fixtures import build_registry_smoke_ohlcv
from tlab.core.errors import RegistryError
from tlab.core.indicator import registry
from tlab.indicators.patterns.breakout_fvg import (
    BreakoutFvgIndicator,
    BreakoutFvgParams,
    _find_consolidation_box,
    _find_fvg,
)
from tlab.testing.fixtures import make_trend

_TZ = "Europe/Istanbul"


def _row(o: float, c: float, h: float, low: float) -> dict:
    return {"open": o, "close": c, "high": h, "low": low, "volume": 1000.0}


def _consolidation_breakout_fvg_retest_confirm_ohlcv() -> pd.DataFrame:
    """0-9: dar konsolidasyon (yükseklik 1.0). 10: kırılım (kapanış kutu
    üstüne). 9-10-11 üçlüsü bullish FVG oluşturur (high[9]=100.5 <
    low[11]=101.0, boşluk=[100.5,101.0]). 12: trend devam. 13: FVG
    bölgesine RETEST (low=100.3..high=101.2, [100.5,101.0]i kapsıyor).
    14: kapanış FVG'nin üstüne dönüp ONAY verir."""
    rows = [
        _row(100, 100, 100.5, 99.5),  # 0
        _row(100, 100.2, 100.5, 99.6),  # 1
        _row(100.2, 99.9, 100.4, 99.5),  # 2
        _row(99.9, 100.1, 100.5, 99.6),  # 3
        _row(100.1, 100, 100.4, 99.5),  # 4
        _row(100, 99.8, 100.3, 99.6),  # 5
        _row(99.8, 100.1, 100.5, 99.7),  # 6
        _row(100.1, 100, 100.4, 99.6),  # 7
        _row(100, 99.9, 100.3, 99.5),  # 8
        _row(99.9, 100, 100.5, 99.5),  # 9 -- konsolidasyon son barı (born_idx)
        _row(100, 104, 104.5, 99.8),  # 10 -- KIRILIM (close>box_high=100.5)
        _row(104, 108, 108.5, 101.0),  # 11 -- FVG'nin 3. mumu (low=101.0)
        _row(108, 110, 111, 107.5),  # 12 -- devam
        _row(110, 100.7, 101.2, 100.3),  # 13 -- RETEST (FVG [100.5,101.0]e dokunur)
        _row(100.7, 103, 103.5, 100.5),  # 14 -- ONAY (kapanış FVG üstüne döner)
        _row(103, 104, 104.5, 102.5),  # 15
    ]
    idx = pd.date_range("2024-01-02", periods=len(rows), freq="1D", tz=_TZ)
    return pd.DataFrame(rows, index=idx)


def _params(**overrides) -> BreakoutFvgParams:
    base = dict(
        consolidation_bars=10, box_atr_max=2.0, breakout_search_bars=5,
        min_fvg_atr=0.05, fvg_search_bars=5, max_bars_to_retest=5, confirm_bars=1,
        atr_period=3,
    )
    base.update(overrides)
    return BreakoutFvgParams(**base)


def test_find_consolidation_box_detects_tight_range() -> None:
    df = _consolidation_breakout_fvg_retest_confirm_ohlcv()
    from tlab.features.volatility import atr

    atr_series = atr(df, 3)
    result = _find_consolidation_box(
        df["high"].to_numpy(), df["low"].to_numpy(), atr_series, 9, _params(),
    )
    assert result is not None
    born_idx, box_high, box_low = result
    assert born_idx == 9
    assert box_high == 100.5
    assert box_low == 99.5


def test_find_fvg_detects_bullish_gap_after_breakout() -> None:
    df = _consolidation_breakout_fvg_retest_confirm_ohlcv()
    from tlab.features.volatility import atr

    atr_series = atr(df, 3)
    result = _find_fvg(
        df["high"].to_numpy(), df["low"].to_numpy(), 10, "long", atr_series, len(df), _params(),
    )
    assert result is not None
    fvg_i, gap_low, gap_high = result
    assert fvg_i == 10  # orta mum -- i-1=9. mumun high'ı, i+1=11. mumun low'u
    assert gap_low == 100.5
    assert gap_high == 101.0


def test_full_chain_reaches_confirmed_in_correct_order() -> None:
    df = _consolidation_breakout_fvg_retest_confirm_ohlcv()
    result = BreakoutFvgIndicator(_params()).compute(df)
    assert result.last_state, "en az bir aday üretilmeli"
    pid, info = next(iter(result.last_state.items()))
    assert info["state"] == "confirmed"
    assert info["direction"] == "long"

    chain = sorted(
        (s for s in result.signals if s.payload.get("pattern_id") == pid),
        key=lambda s: s.bar_time,
    )
    suffixes = [s.payload["suffix"] for s in chain]
    assert suffixes == ["pending", "breakout", "fvg_formed", "retest", "confirmed"]
    # Non-repaint: FVG ancak 3. mum (idx11) KAPANDIĞINDA bilinir.
    fvg_sig = next(s for s in chain if s.payload["suffix"] == "fvg_formed")
    assert fvg_sig.bar_time == df.index[11]


def test_entry_marker_survives_target_reached_completion() -> None:
    """K3 düzeltmesi (2026-09-05, bkz. docs/GORSEL_HATA_TESHISI.md): eskiden
    `if last_sig.state == "confirmed":` yalnızca state TAM "confirmed" iken
    doğruydu -- hedefe ulaşılıp state "completed" olunca (last_sig artık
    target_reached barı) AL/SAT işareti TAMAMEN KAYBOLUYORDU. Fixture'a
    hedefi (105.0 = box_yükseklik(1.0) + close[breakout]=104) aşan ek
    barlar eklenip regresyon doğrulanır: AL hâlâ ONAY (confirm) barında."""
    df = _consolidation_breakout_fvg_retest_confirm_ohlcv()
    extra_idx = pd.date_range(df.index[-1] + pd.Timedelta(days=1), periods=3, freq="1D", tz=_TZ)
    extra = pd.DataFrame(
        [
            _row(104, 105.5, 106, 103.5),
            _row(105.5, 106, 106.5, 105),
            _row(106, 106.5, 107, 105.5),
        ],
        index=extra_idx,
    )
    df = pd.concat([df, extra])
    result = BreakoutFvgIndicator(_params()).compute(df)
    pid, info = next(iter(result.last_state.items()))
    assert info["state"] == "completed"

    confirm_sig = next(s for s in result.signals if s.payload["event"].endswith("_confirmed"))
    entry = next(m for m in result.markers if m.kind.startswith("pattern_entry_long:"))
    assert entry.t == confirm_sig.bar_time  # AL, last_sig (hedef barı) DEĞİL

    target_level = next(lv for lv in result.levels if lv.label == f"{pid}_target")
    assert target_level.start == confirm_sig.bar_time

    kinds = {m.kind.split(":", 1)[0] for m in result.markers}
    assert "pattern_breakout" in kinds
    assert "pattern_retest_ok" in kinds
    assert "pattern_target_hit" in kinds


def test_no_target_or_entry_marker_when_never_confirmed() -> None:
    """K3 düzeltmesi: retest süresi dolup aday hiç onaylanmadan (confirmed'a
    hiç ulaşmadan) "expired" olursa ne hedef Level'i ne de AL/SAT/KIRILIM/
    ONAY/HEDEF marker'ı üretilmemeli -- yalnızca genel durum rozeti kalır."""
    df = _consolidation_breakout_fvg_retest_confirm_ohlcv()
    result = BreakoutFvgIndicator(_params(max_bars_to_retest=1)).compute(df)
    assert result.last_state
    assert all(info["state"] == "expired" for info in result.last_state.values())
    assert not any(lv.label.endswith("_target") for lv in result.levels)
    for prefix in (
        "pattern_entry_", "pattern_breakout:", "pattern_retest_ok:", "pattern_target_hit:",
    ):
        assert not any(m.kind.startswith(prefix) for m in result.markers)


def test_consolidation_box_low_high_frozen_at_birth() -> None:
    """`_find_consolidation_box` yalnızca [start, end_idx] penceresini
    kullanır -- df daha da uzasa (yeni barlar eklense) AYNI born_idx için
    AYNI box_high/box_low dönmeli (geriye yazım yok)."""
    df = _consolidation_breakout_fvg_retest_confirm_ohlcv()
    extra_rows = [{"open": 104, "close": 104, "high": 104.5, "low": 103.5, "volume": 1000.0}] * 5
    extra_idx = pd.date_range(df.index[-1] + pd.Timedelta(days=1), periods=5, freq="1D", tz=_TZ)
    df_extended = pd.concat([df, pd.DataFrame(extra_rows, index=extra_idx)])

    from tlab.features.volatility import atr

    atr_full = atr(df_extended, 3)
    result_full = _find_consolidation_box(
        df_extended["high"].to_numpy(), df_extended["low"].to_numpy(), atr_full, 9, _params(),
    )
    atr_short = atr(df, 3)
    result_short = _find_consolidation_box(
        df["high"].to_numpy(), df["low"].to_numpy(), atr_short, 9, _params(),
    )
    assert result_full == result_short


def test_runs_and_produces_valid_signal_contract() -> None:
    df = make_trend(n=200, slope=0.05, noise=1.4, seed=17)
    result = BreakoutFvgIndicator(BreakoutFvgParams()).compute(df)
    assert result.indicator == "patterns.breakout_fvg"
    for sig in result.signals:
        assert "event" in sig.payload and "pattern_id" in sig.payload
        valid_states = ("pending", "active", "confirmed", "invalidated", "completed", "expired")
        assert sig.state in valid_states
        assert sig.detected_at == sig.bar_time
    for box in result.boxes:
        assert box.style in ("pattern_consolidation", "pattern_fvg")
        assert box.low <= box.high


def test_no_consolidation_found_produces_empty_result() -> None:
    """Sürekli aynı yönde giden, hiç dar konsolidasyon oluşturmayan bir
    seri -- çökmemeli, yalnızca boş sonuç dönmeli."""
    n = 60
    close = np.linspace(100, 100 + n * 3, n)  # her bar ~3 birim, ATR'ye göre HER ZAMAN geniş
    idx = pd.date_range("2024-01-02", periods=n, freq="1D", tz=_TZ)
    df = pd.DataFrame(
        {
            "open": close, "close": close,
            "high": close + 0.2, "low": close - 0.2, "volume": 1000.0,
        },
        index=idx,
    )
    params = BreakoutFvgParams(consolidation_bars=10, box_atr_max=0.3)
    result = BreakoutFvgIndicator(params).compute(df)
    assert result.last_state == {}
    assert result.boxes == []


def test_registers_via_verified_elsewhere() -> None:
    df = build_registry_smoke_ohlcv()
    try:
        registry.register_verified_elsewhere(BreakoutFvgIndicator())
    except RegistryError as exc:
        if "zaten kayıtlı" not in str(exc):
            raise
    assert registry.get("patterns.breakout_fvg") is BreakoutFvgIndicator
    BreakoutFvgIndicator()(df)
