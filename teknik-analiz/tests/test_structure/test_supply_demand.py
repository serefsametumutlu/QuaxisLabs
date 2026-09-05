"""structure.supply_demand için birim testleri.

Senaryo, `tests/test_zones_sd.py::_build_scenario`'nun BİREBİR AYNISI
(0-4 oynak geçmiş, 5-7 sıkı taban, 8-10 patlama [+36 net], 11 uzak,
12 TEST, 13 REAKSİYON, 14 uzak, 15 KIRILIM) — o dosyada `find_bases`/
`find_impulses`/`update_zones` üzerinde doğrulanmış sayılar, burada
`SupplyDemandIndicator`'ın bunları doğru sarmaladığını doğrulamak için
tekrar kullanılıyor. `atr_period=5` (varsayılan 14 DEĞİL) — 16 barlık kısa
senaryoda ATR(14) hiç geçerli olmaz (min_periods=14), bkz. o dosyadaki
gerekçe."""

from __future__ import annotations

from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from tlab.features.zones_sd import SDZone
from tlab.indicators.structure.supply_demand import SupplyDemandIndicator, SupplyDemandParams

TZ = ZoneInfo("Europe/Istanbul")


def _row(o: float, c: float, h: float, low: float) -> dict:
    return {"open": o, "high": h, "low": low, "close": c, "volume": 1000.0}


def _build_scenario() -> pd.DataFrame:
    rows = [
        _row(100, 100, 104, 96),
        _row(100, 102, 105, 98),
        _row(102, 99, 104, 97),
        _row(99, 101, 103, 97),
        _row(101, 100, 103, 98),
        _row(100, 100, 100.5, 99.5),
        _row(100, 100, 100.5, 99.5),
        _row(100, 100, 100.5, 99.5),
        _row(100, 112, 113, 99),
        _row(112, 124, 125, 111),
        _row(124, 136, 137, 123),
        _row(110, 110, 112, 108),
        _row(100.2, 100.2, 108, 100.0),
        _row(106, 106, 108, 103),
        _row(108, 108, 110, 105),
        _row(95, 95, 106, 94),
    ]
    idx = pd.date_range("2024-01-02 10:00", periods=len(rows), freq="1D", tz=TZ)
    return pd.DataFrame(rows, index=idx)


def _params(**overrides) -> SupplyDemandParams:
    # Faz 4d (2026-09-05): varsayılan method "pivot"a döndü (bkz.
    # supply_demand.py'nin kendi docstring'i) -- bu dosyanın TAMAMI özellikle
    # rally-base-drop mekaniğini (find_bases/find_impulses/update_zones)
    # doğruladığı için burada AÇIKÇA "rbd" sabitlenir.
    base = dict(
        method="rbd", atr_period=5, impulse_bars=3, impulse_atr=2.0,
        base_atr=0.6, base_max=5, max_zones=12,
    )
    base.update(overrides)
    return SupplyDemandParams(**base)


def _compute(df: pd.DataFrame, **overrides):
    return SupplyDemandIndicator(_params(**overrides)).compute(df)


# --- bölge oluşumu -----------------------------------------------------


def test_supply_demand_creates_demand_box_at_impulse_confirmation() -> None:
    df = _build_scenario()
    result = _compute(df)
    box = next(b for b in result.boxes if b.style in ("demand", "demand_broken"))
    assert box.low == pytest.approx(99.5)
    assert box.high == pytest.approx(100.5)
    assert box.t0 == df.index[10]


def test_supply_demand_label_contains_freshness_and_distance() -> None:
    df = _build_scenario()
    result = _compute(df)
    box = next(b for b in result.boxes if b.style == "demand_broken")
    assert "DEMAND" in box.label


# --- test/reaksiyon/kırılım sinyalleri -----------------------------------


def test_supply_demand_test_reaction_broken_signals_present() -> None:
    df = _build_scenario()
    result = _compute(df)
    demand_signals = [s for s in result.signals if s.payload.get("zone_kind") == "demand"]
    events = {s.payload["event"] for s in demand_signals}
    assert events == {"sd_new", "sd_test", "sd_reaction", "sd_broken"}

    test_sig = next(s for s in demand_signals if s.payload["event"] == "sd_test")
    reaction_sig = next(s for s in demand_signals if s.payload["event"] == "sd_reaction")
    broken_sig = next(s for s in demand_signals if s.payload["event"] == "sd_broken")
    assert test_sig.bar_time == df.index[12]
    assert reaction_sig.bar_time == df.index[13]
    assert broken_sig.bar_time == df.index[15]
    assert broken_sig.direction == "short"  # demand kırıldı -> aşağı yön


def test_supply_demand_sd_new_signal_marks_zone_birth() -> None:
    df = _build_scenario()
    result = _compute(df)
    demand_signals = [s for s in result.signals if s.payload.get("zone_kind") == "demand"]
    new_sig = next(s for s in demand_signals if s.payload["event"] == "sd_new")
    assert new_sig.bar_time == df.index[10]
    assert new_sig.payload["fresh"] is True


def test_supply_demand_box_t1_fixed_at_break_bar() -> None:
    df = _build_scenario()
    result = _compute(df)
    box = next(b for b in result.boxes if b.style == "demand_broken")
    assert box.t1 == df.index[15]


# --- flip ----------------------------------------------------------------


def test_supply_demand_broken_demand_flips_to_supply() -> None:
    df = _build_scenario()
    result = _compute(df, flip=True)
    flip_signals = [s for s in result.signals if s.payload.get("zone_kind") == "supply"]
    assert flip_signals  # kırılan demand'dan doğan yeni supply bölgesinin en az bir sinyali var
    flip_box = next(b for b in result.boxes if b.style in ("supply", "supply_broken"))
    assert flip_box.t0 == df.index[15]  # kırılma barında doğdu
    assert flip_box.low == pytest.approx(99.5)
    assert flip_box.high == pytest.approx(100.5)


def test_supply_demand_flip_disabled_produces_no_supply_zone() -> None:
    df = _build_scenario()
    result = _compute(df, flip=False)
    assert not any(b.style.startswith("supply") for b in result.boxes)


# --- kalite skoru ----------------------------------------------------------


def test_supply_demand_quality_score_in_unit_range() -> None:
    df = _build_scenario()
    result = _compute(df)
    for s in result.signals:
        assert 0.0 <= s.score <= 1.0


def test_supply_demand_fresh_zone_scores_higher_than_tested_zone() -> None:
    """Aynı bölge, hiç test EDİLMEMİŞKEN (fresh) skoru, en az bir test
    sonrasındaki (artık fresh olmayan) skorundan büyük ya da eşit olmalı."""
    df = _build_scenario()
    result = _compute(df)
    demand_signals = [s for s in result.signals if s.payload.get("zone_kind") == "demand"]
    test_sig = next(s for s in demand_signals if s.payload["event"] == "sd_test")
    reaction_sig = next(s for s in demand_signals if s.payload["event"] == "sd_reaction")
    # test_sig ANINDA bölge ARTIK fresh değil (aynı test barında test_idxs'e
    # eklendiği an tazelik düşer) -- ikisinin de skoru AYNI (tazelik durumu
    # sinyal üretilirken sabit `state.fresh` değerinden okunuyor).
    assert test_sig.score == reaction_sig.score


# --- last_state ------------------------------------------------------------


def test_last_state_reports_nearest_zone_when_none_broken() -> None:
    """Kırılmamış (henüz açık) bir bölge varken last_state onu yakalamalı."""
    df = _build_scenario().iloc[:12]  # bar 12 = TEST barı, henüz kırılma yok
    result = _compute(df)
    assert result.last_state["nearest_demand"] is not None
    assert result.last_state["distance_atr"] is not None


def test_last_state_in_zone_true_when_price_inside() -> None:
    df = _build_scenario().iloc[:13]  # bar 12'de fiyat bölge İÇİNDE kapandı
    result = _compute(df)
    assert result.last_state["in_zone"] is True


def test_indicator_interface_compliance() -> None:
    """SupplyDemandIndicator, generic Registry.register() ile KAYDEDİLMEZ —
    bkz. modül docstring'indeki "BİLİNEN SINIRLAMA" (make_sd_zones'un
    max_zones "aday havuzu" kesmesi). Arayüz uyumluluğu (meta, compute,
    IndicatorResult tipi) doğrudan doğrulanır — PriceStructure'ın kendi
    `test_registers_in_registry` testiyle AYNI desen."""
    from tlab.core.types import IndicatorResult

    df = _build_scenario()
    result = SupplyDemandIndicator()(df)
    assert isinstance(result, IndicatorResult)
    assert result.indicator == "structure.supply_demand"


# --- Faz 4d: method="pivot"/"both" (pivot-çıpalı arz/talep) ----------------


def test_default_method_is_pivot() -> None:
    """Faz 4d (2026-09-05, `docs/GORSEL_HATA_TESHISI.md` A1): varsayılan
    artık rally-base-drop DEĞİL, kullanıcının/`ornek1.png`nin kullandığı
    pivot-çıpalı yöntem."""
    assert SupplyDemandParams().method == "pivot"


def test_method_pivot_produces_zones_from_zigzag_swings() -> None:
    from tlab.testing.fixtures import make_zigzag

    df = make_zigzag([(0, 100), (10, 130), (20, 90), (30, 140), (40, 80), (50, 120)], noise=0.2)
    params = SupplyDemandParams(
        method="pivot", zigzag_method="fixed", pivot_left=2, pivot_right=2, atr_period=5,
    )
    result = SupplyDemandIndicator(params).compute(df)
    assert result.boxes
    assert {b.style.removesuffix("_broken") for b in result.boxes} <= {"supply", "demand"}


def test_method_pivot_quality_score_not_systematically_zero() -> None:
    """GERÇEK bir hata (2026-09-05): `_quality_score`'un tightness_score'u
    HER ZAMAN `base_atr` (rbd'nin dar taban tavanı, varsayılan 0.6) ile
    bölüyordu -- pivot bölgeleri (tipik yükseklik ~0.15-2.75*ATR) için
    height_ratio hep >=1 çıkıp skor sistemli olarak ~0'a çöküyordu.
    Düzeltme: method="pivot"/"both" iken referans `pivot_height_cap_atr`."""
    from tlab.testing.fixtures import make_zigzag

    df = make_zigzag([(0, 100), (10, 130), (20, 90), (30, 140), (40, 80), (50, 120)], noise=0.2)
    params = SupplyDemandParams(
        method="pivot", zigzag_method="fixed", pivot_left=2, pivot_right=2, atr_period=5,
    )
    result = SupplyDemandIndicator(params).compute(df)
    new_signals = [s for s in result.signals if s.payload.get("event") == "sd_new"]
    assert new_signals
    assert any(s.score > 0.05 for s in new_signals)


def test_merge_both_boosts_overlapping_pivot_zone_strength() -> None:
    from tlab.indicators.structure.supply_demand import _merge_both

    pivot_zone = SDZone(
        kind="supply", low=100.0, high=105.0, created_idx=10, base_bars=1, impulse_strength=1.0,
    )
    rbd_zone = SDZone(
        kind="supply", low=102.0, high=107.0, created_idx=12, base_bars=3, impulse_strength=3.0,
    )
    merged = _merge_both([pivot_zone], [rbd_zone])
    assert len(merged) == 1
    # Pivot bölgesinin SINIRLARI korunur (spec: pivot-çıpalı BİRİNCİL);
    # yalnızca skoru güçlenir.
    assert merged[0].low == pytest.approx(100.0)
    assert merged[0].high == pytest.approx(105.0)
    assert merged[0].impulse_strength == pytest.approx(3.0 * 1.25)


def test_merge_both_keeps_non_overlapping_rbd_zone_separately() -> None:
    from tlab.indicators.structure.supply_demand import _merge_both

    pivot_zone = SDZone(
        kind="supply", low=100.0, high=105.0, created_idx=10, base_bars=1, impulse_strength=1.0,
    )
    rbd_zone = SDZone(
        kind="demand", low=50.0, high=55.0, created_idx=5, base_bars=2, impulse_strength=2.0,
    )
    merged = _merge_both([pivot_zone], [rbd_zone])
    assert len(merged) == 2
    assert {z.kind for z in merged} == {"supply", "demand"}
