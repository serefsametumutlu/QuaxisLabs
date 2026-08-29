"""structure.golden_zone için birim testleri + repaint testi.

Elle inşa edilmiş senaryo: X(low)@2=100, A(high)@10=130 -> altın bölge
band=(106.42, 111.46) (0.618/0.786). A, bir SONRAKİ (zıt türde) pivot
KESİNLEŞTİĞİNDE finalize olur (bkz. `swings.alternate_pivots`) — bu
yüzden tarama `born = A.finalized_idx`'ten başlar, A'nın kendi bar'ından
DEĞİL (non-repaint: bkz. modül docstring'i)."""

from __future__ import annotations

from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from tests.test_structure.fixtures import build_registry_smoke_ohlcv
from tlab.core.errors import RegistryError
from tlab.core.indicator import registry
from tlab.indicators.structure.golden_zone import GoldenZoneIndicator, GoldenZoneParams
from tlab.testing.repaint import repaint_test

TZ = ZoneInfo("Europe/Istanbul")

_BASE_ROWS: list[tuple[float, float, float, float]] = [
    (112, 112, 113, 111),
    (112, 110, 113, 109),
    (110, 101, 111, 100),  # X low pivot (price=100)
    (101, 103, 104, 100.9),
    (103, 105, 106, 102.5),
    (105, 110, 111, 104),
    (110, 116, 117, 109),
    (116, 121, 122, 115),
    (121, 126, 127, 120),
    (126, 129, 129.5, 125),
    (129, 130, 130, 128),  # A high pivot (price=130)
    (130, 127, 130, 126),
    (127, 122, 128, 121),
]


def _df_from_rows(rows: list[tuple[float, float, float, float]]) -> pd.DataFrame:
    idx = pd.date_range("2024-01-02 10:00", periods=len(rows), freq="1D", tz=TZ)
    return pd.DataFrame(
        [{"open": o, "close": c, "high": h, "low": lo, "volume": 1000.0} for o, c, h, lo in rows],
        index=idx,
    )


def _build_touch_reaction_success_scenario() -> pd.DataFrame:
    """13-16: A'yı finalize eden düşük pivot (idx15, price=107) oluşana
    kadar düşüş. 17: born barı + DOKUNUŞ (bant içine giriyor). 18: REAKSİYON
    (bant üstüne boğa kapanışı). 21: BAŞARI (kapanış swing high'ı [130] aşıyor).
    21'i onaylayan yeni bir tepe pivotu (idx21) da bu swing'in bandını 23'te
    kapatır (sonraki swing'e devrediyor)."""
    rows = [
        *_BASE_ROWS,
        (122, 118, 123, 117),  # 13
        (118, 112, 119, 108),  # 14
        (112, 109, 113, 107),  # 15 -- düşük pivot (finalize A@17)
        (109, 111, 112, 108.5),  # 16
        (111, 110, 112, 109.5),  # 17 -- born, DOKUNUŞ
        (110, 120, 121, 109),  # 18 -- REAKSİYON
        (120, 124, 125, 119),  # 19
        (124, 128, 129, 123),  # 20
        (128, 133, 134, 127),  # 21 -- BAŞARI + yeni tepe pivotu
        (133, 130, 133, 128),  # 22
        (130, 128, 131, 127),  # 23
        (128, 126, 129, 124),  # 24
        (126, 124, 127, 122),  # 25
    ]
    return _df_from_rows(rows)


def _build_fail_scenario() -> pd.DataFrame:
    """13-16: sert düşüş, bandın TAMAMEN altına iniyor (dokunuş bile olmadan)
    -> idx16 düşük pivotu A'yı 18'de finalize ediyor; born=18'de kapanış
    zaten bant altında -> FAIL, hiç DOKUNUŞ olmadan."""
    rows = [
        *_BASE_ROWS,
        (122, 105, 123, 99),  # 13
        (105, 95, 106, 90),  # 14
        (95, 92, 96, 88),  # 15
        (92, 90, 93, 87),  # 16 -- düşük pivot (finalize A@18)
        (90, 91, 92, 89),  # 17
        (91, 93, 94, 90),  # 18 -- born, FAIL (dokunuş yok)
    ]
    return _df_from_rows(rows)


def _params() -> GoldenZoneParams:
    return GoldenZoneParams(left=2, right=2)


def _events(df: pd.DataFrame) -> list[dict]:
    result = GoldenZoneIndicator(_params()).compute(df)
    return [s.payload for s in result.signals]


# --- bant hesaplaması --------------------------------------------------


def test_golden_zone_box_bounds_match_fibonacci_band() -> None:
    df = _build_touch_reaction_success_scenario()
    result = GoldenZoneIndicator(_params()).compute(df)
    band_box = next(b for b in result.boxes if b.style == "golden_zone")
    assert band_box.low == pytest.approx(106.42, abs=0.01)
    assert band_box.high == pytest.approx(111.46, abs=0.01)


def test_golden_zone_box_closes_when_next_swing_finalizes() -> None:
    """Süperseded olan bant, son bara DEĞİL, kendisini kapatan yeni swing'in
    onay barına sabitlenmeli (extend-only, sınırsız uzamamalı)."""
    df = _build_touch_reaction_success_scenario()
    result = GoldenZoneIndicator(_params()).compute(df)
    band_box = next(b for b in result.boxes if b.style == "golden_zone")
    assert band_box.t1 == df.index[23]
    assert band_box.t1 != df.index[-1]


# --- sinyal olayları ---------------------------------------------------


def test_golden_zone_touch_then_reaction_then_success() -> None:
    """Senaryo, aynı zamanda ARADAKİ (high@10 -> low@15) düşüş swing'ini
    (swing_id=2) de üretir — bu BAĞIMSIZ ve BEKLENEN bir sonuçtur (her
    ardışık zigzag bacağı kendi bandını üretir), bu test yalnızca asıl ilgi
    duyulan İLK (yükseliş) swing'in (swing_id=1) olay sırasını doğrular."""
    events = _events(_build_touch_reaction_success_scenario())
    ordered = [
        e["event"] for e in events
        if e.get("event", "").startswith("golden_zone") and e.get("swing_id") == 1
    ]
    assert ordered == [
        "golden_zone_touch", "golden_zone_reaction", "golden_zone_success",
    ]


def test_golden_zone_touch_bar_is_born_bar() -> None:
    df = _build_touch_reaction_success_scenario()
    result = GoldenZoneIndicator(_params()).compute(df)
    touch = next(s for s in result.signals if s.payload.get("event") == "golden_zone_touch")
    assert touch.bar_time == df.index[17]
    assert touch.direction == "long"


def test_golden_zone_reaction_and_success_bars() -> None:
    df = _build_touch_reaction_success_scenario()
    result = GoldenZoneIndicator(_params()).compute(df)
    reaction = next(s for s in result.signals if s.payload.get("event") == "golden_zone_reaction")
    success = next(s for s in result.signals if s.payload.get("event") == "golden_zone_success")
    assert reaction.bar_time == df.index[18]
    assert success.bar_time == df.index[21]
    assert success.state == "completed"


def test_golden_zone_fail_without_prior_touch() -> None:
    events = _events(_build_fail_scenario())
    fail_events = [e for e in events if e.get("event") == "golden_zone_fail"]
    touch_events = [e for e in events if e.get("event") == "golden_zone_touch"]
    assert len(fail_events) == 1
    assert touch_events == []


def test_golden_zone_fail_bar_and_direction() -> None:
    df = _build_fail_scenario()
    result = GoldenZoneIndicator(_params()).compute(df)
    fail = next(s for s in result.signals if s.payload.get("event") == "golden_zone_fail")
    assert fail.bar_time == df.index[18]
    assert fail.direction == "short"  # uptrend bandı başarısız -> ters yön
    assert fail.state == "invalidated"


# --- filtre / last_state -------------------------------------------------


def test_min_swing_atr_filters_tiny_swings() -> None:
    df = _build_touch_reaction_success_scenario()
    strict = GoldenZoneIndicator(GoldenZoneParams(left=2, right=2, min_swing_atr=1000.0))
    result = strict.compute(df)
    assert result.boxes == []
    assert result.signals == []


def test_last_state_reflects_open_band() -> None:
    df = _build_fail_scenario()
    result = GoldenZoneIndicator(_params()).compute(df)
    # fail sonrası bu swing artık "done" ama df'nin geri kalanında yeni bir
    # swing YOK -> last_state hâlâ bu (kapanmamış/başarısız) banda ait olmalı.
    assert result.last_state["band_low"] is not None
    assert result.last_state["band_high"] is not None


# --- repaint ---------------------------------------------------------------


def test_golden_zone_passes_repaint() -> None:
    """cut_points, SON ilgili zigzag pivotunun (high@21) finalized_idx'inden
    (23) İTİBAREN seçilir — bkz. swing_fib_abcd'nin aynı desendeki notu:
    ara kesitlerde YENİ swing çizgileri belirmesi (points[0][0] tabanlı Line
    diffing'in "aday havuzu" sınırlaması) gerçek bir repaint hatası değildir,
    yalnızca zigzag TAMAMEN durağanlaştıktan sonraki kesitler test edilir."""
    df = _build_touch_reaction_success_scenario()
    indicator = GoldenZoneIndicator(_params())
    report = repaint_test(indicator, df, cut_points=list(range(24, len(df) + 1)))
    assert report.passed, report.mismatches


def test_registers_in_registry() -> None:
    df = build_registry_smoke_ohlcv()
    try:
        registry.register(GoldenZoneIndicator(), df)
    except RegistryError as exc:
        if "zaten kayıtlı" not in str(exc):
            raise
    assert registry.get("structure.golden_zone") is GoldenZoneIndicator
