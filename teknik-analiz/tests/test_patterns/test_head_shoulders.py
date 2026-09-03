"""patterns.head_shoulders testleri.

Elle inşa edilmiş bir TOBO senaryosu (`_tobo_ohlcv`; pivotlar GERÇEK
`find_pivots`/`alternate_pivots`/`find_hs` çalıştırılarak doğrulanmıştır):
l1(idx2,97) -> h1(idx7,117) -> head(idx12,88) -> h2(idx16,116) ->
l3(idx20,95, `finalized_idx=23`'te PENDING doğar — idx21'deki küçük tepe
l3'ü finalize eder) -> idx24'te boyun kırılımı (kapanış 118>~115) ->
idx29'da hedefe ulaşma (kapanış 148>=146).

`test_pending_born_at_l3_finalized_idx_not_confirmed_idx` bu modülü
yazarken bulunan GERÇEK hatayı (bkz. head_shoulders.py docstring'i) kilitler:
`HSPattern.created_idx` (=l3.confirmed_idx=22) YANLIŞ born barı olurdu —
doğrusu `l3.finalized_idx` (23)'tür."""

from __future__ import annotations

import pandas as pd
import pytest

from tests.test_structure.fixtures import build_registry_smoke_ohlcv
from tlab.core.errors import RegistryError
from tlab.core.indicator import registry
from tlab.indicators.patterns.head_shoulders import HeadShouldersIndicator, HeadShouldersParams
from tlab.testing.repaint import repaint_test

_TZ = "Europe/Istanbul"

_ROWS: list[tuple[float, float, float, float]] = [
    (105, 104, 106, 103),
    (104, 101, 105, 100),
    (101, 98, 102, 97),      # l1 low=97 (idx2)
    (98, 100, 101, 98.5),
    (100, 103, 104, 99.5),
    (103, 108, 109, 102),
    (108, 113, 114, 107),
    (113, 116, 117, 112),    # h1 high=117 (idx7)
    (116, 113, 117, 112),
    (113, 108, 114, 107),
    (108, 102, 109, 101),
    (102, 95, 103, 94),
    (95, 90, 96, 88),        # head low=88 (idx12)
    (90, 93, 94, 89),
    (93, 100, 101, 92),
    (100, 110, 111, 99),
    (110, 116, 117, 108),    # h2 high=116 (idx16)
    (116, 112, 117, 110),
    (112, 105, 113, 104),
    (105, 99, 106, 97),
    (99, 96, 100, 95),       # l3 low=95 (idx20, confirmed_idx=22)
    (96, 101, 108, 95.5),    # l3'ü finalize eden küçük tepe (finalized_idx=23)
    (101, 99, 101.5, 98),
    (99, 103, 104, 98.5),    # born (idx23): l3.finalized_idx
    (103, 118, 119, 102),    # boyun kırılımı (idx24)
    (118, 124, 125, 117),
    (124, 130, 131, 123),
    (130, 138, 139, 129),
    (138, 144, 145, 137),
    (144, 148, 149, 143),    # hedefe ulaşma (idx29)
]


def _tobo_ohlcv() -> pd.DataFrame:
    """`open` kasıtlı olarak `close`'a EŞİTLENİR (bu indikatör `open`
    kolonunu hiç okumaz) — yalnızca `high`/`low`/`close` pivot/kırılım
    geometrisi için özenle seçilmiştir, `validate_ohlcv`'in `low<=close<=high`
    şartını basitçe garanti eder."""
    idx = pd.date_range("2024-01-02", periods=len(_ROWS), freq="1D", tz=_TZ)
    return pd.DataFrame(
        [{"open": c, "close": c, "high": h, "low": lo, "volume": 1000.0} for _o, c, h, lo in _ROWS],
        index=idx,
    )


def _params() -> HeadShouldersParams:
    return HeadShouldersParams(left=2, right=2, kind="tobo")


def test_pending_born_at_l3_finalized_idx_not_confirmed_idx() -> None:
    df = _tobo_ohlcv()
    result = HeadShouldersIndicator(_params()).compute(df)
    pending = next(s for s in result.signals if s.payload["event"] == "tobo_pending")
    assert pending.bar_time == df.index[23]
    assert pending.bar_time != df.index[22]  # l3.confirmed_idx -- YANLIŞ olurdu


def test_neckline_break_confirms_and_reaches_target() -> None:
    df = _tobo_ohlcv()
    result = HeadShouldersIndicator(_params()).compute(df)
    confirmed = next(s for s in result.signals if s.payload["event"] == "tobo_confirmed")
    completed = next(s for s in result.signals if s.state == "completed")
    assert confirmed.bar_time == df.index[24]
    assert confirmed.payload["break_price"] == pytest.approx(118.0)
    assert completed.bar_time == df.index[29]
    assert completed.payload["target"] == pytest.approx(146.0, abs=0.5)


def test_shoulder_markers_present() -> None:
    df = _tobo_ohlcv()
    result = HeadShouldersIndicator(_params()).compute(df)
    texts = {m.text for m in result.markers}
    assert {"SOL OMUZ", "BAŞ", "SAĞ OMUZ"} <= texts


def test_asymmetric_shoulder_time_ratio_filters_pattern_out() -> None:
    """Sol omuz->baş ve baş->sağ omuz süreleri (10 bar / 8 bar) aslında
    (0.5,2.0) bandına GİRER — çok dar bir bant (0.9,1.1) ile filtrelenmesi
    beklenir (10/8=1.25 > 1.1)."""
    df = _tobo_ohlcv()
    params = HeadShouldersParams(left=2, right=2, shoulder_time_ratio=(0.9, 1.1))
    result = HeadShouldersIndicator(params).compute(df)
    assert result.signals == []


def test_kind_both_also_scans_obo_independently() -> None:
    df = _tobo_ohlcv()
    result = HeadShouldersIndicator(HeadShouldersParams(left=2, right=2, kind="both")).compute(df)
    assert any(s.payload["pattern_name"] == "tobo" for s in result.signals)


def test_hologram_polygon_traces_close_path_l1_to_l3() -> None:
    """2026-09-03: hologram artık yalnızca 5 zigzag köşesini (L1-H1-Baş-H2-L3)
    DÜZ ÇİZGİLERLE birleştirip L3'ten L1'e kapatan bir çokgen DEĞİL — bu,
    omuz tepeleri (L1/L3) boyun çukurlarının (H1/H2) ÜSTÜNDE ama Baş'ın
    ALTINDA olduğu için kendi kendini kesen ("bowtie") bir şekil üretiyordu
    (kullanıcı: hologram "yarım"/ters görünüyor). Artık L1->L3 arası GERÇEK
    kapanış fiyatı yolunu izliyor (`double_top_bottom.py`'deki aynı düzeltme)."""
    df = _tobo_ohlcv()
    result = HeadShouldersIndicator(_params()).compute(df)
    hologram = next(p for p in result.polygons if p.style == "pattern_hologram")
    prices = [price for _t, price in hologram.points]
    close = df["close"].to_numpy()
    assert prices == pytest.approx(list(close[2:21]))
    assert hologram.points[0][0] == df.index[2]  # l1
    assert hologram.points[-1][0] == df.index[20]  # l3


def test_registers_in_registry() -> None:
    df = build_registry_smoke_ohlcv()
    try:
        registry.register(HeadShouldersIndicator(), df)
    except RegistryError as exc:
        if "zaten kayıtlı" not in str(exc):
            raise
    assert registry.get("patterns.head_shoulders") is HeadShouldersIndicator


def test_passes_repaint() -> None:
    df = _tobo_ohlcv()
    cut_points = list(range(25, len(df) + 1))
    report = repaint_test(HeadShouldersIndicator(_params()), df, cut_points=cut_points)
    assert report.passed, report.mismatches
