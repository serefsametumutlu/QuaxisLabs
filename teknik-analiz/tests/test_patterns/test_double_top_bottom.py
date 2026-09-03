"""patterns.double_top_bottom testleri.

Elle inşa edilmiş bir çift dip senaryosu (`_double_bottom_ohlcv`, pivotlar
GERÇEK `find_pivots`/`alternate_pivots` çalıştırılarak doğrulanmıştır —
bkz. yorumlar): dip1(idx2, 97) -> boyun(idx7, 117) -> dip2(idx12, 96,
`finalized_idx=16`'da PENDING doğar) -> idx19'da boyun kırılımı (kapanış
118>117) -> idx23'te hedefe ulaşma (kapanış 138>=137.5)."""

from __future__ import annotations

import pandas as pd
import pytest

from tests.test_structure.fixtures import build_registry_smoke_ohlcv
from tlab.core.errors import RegistryError
from tlab.core.indicator import registry
from tlab.indicators.patterns.double_top_bottom import (
    DoubleTopBottomIndicator,
    DoubleTopBottomParams,
)
from tlab.testing.repaint import repaint_test

_TZ = "Europe/Istanbul"

_ROWS: list[tuple[float, float, float, float]] = [
    (105, 104, 106, 103),
    (104, 101, 105, 100),
    (101, 98, 102, 97),      # dip1 low=97 (idx2)
    (98, 100, 101, 98.5),
    (100, 103, 104, 99.5),
    (103, 108, 109, 102),
    (108, 113, 114, 107),
    (113, 116, 117, 112),    # boyun (neckline) high=117 (idx7)
    (116, 113, 117, 112),
    (113, 110, 114, 109),
    (110, 105, 111, 104),
    (105, 101, 106, 100),
    (101, 97, 102, 96),      # dip2 low=96 (idx12)
    (97, 100, 101, 96.5),
    (100, 104, 105, 99.5),   # ufak ara tepe (dip2'yi finalize eder, idx14)
    (104, 100, 104.5, 99),
    (100, 98, 101, 97.5),    # born (idx16): dip2.finalized_idx
    (98, 103, 104, 97),
    (103, 110, 111, 102),
    (110, 118, 119, 109),    # boyun kırılımı: kapanış 118>117 (idx19)
    (118, 123, 124, 117),
    (123, 128, 129, 122),
    (128, 132, 133, 127),
    (132, 138, 139, 131),    # hedefe ulaşma: kapanış 138>=137.5 (idx23)
]


def _double_bottom_ohlcv() -> pd.DataFrame:
    """`open` kasıtlı olarak `close`'a EŞİTLENİR (bu indikatör `open`
    kolonunu hiç okumaz) — yalnızca `high`/`low`/`close` pivot/kırılım
    geometrisi için özenle seçilmiştir, `validate_ohlcv`'in `low<=close<=high`
    şartını basitçe garanti eder."""
    idx = pd.date_range("2024-01-02", periods=len(_ROWS), freq="1D", tz=_TZ)
    return pd.DataFrame(
        [{"open": c, "close": c, "high": h, "low": lo, "volume": 1000.0} for _o, c, h, lo in _ROWS],
        index=idx,
    )


def _params() -> DoubleTopBottomParams:
    return DoubleTopBottomParams(left=2, right=2)


def test_pending_born_at_p2_finalized_idx() -> None:
    df = _double_bottom_ohlcv()
    result = DoubleTopBottomIndicator(_params()).compute(df)
    pending = next(s for s in result.signals if s.payload["event"] == "double_bottom_pending")
    assert pending.bar_time == df.index[16]
    assert pending.direction == "long"


def test_neckline_break_confirms_at_expected_bar() -> None:
    df = _double_bottom_ohlcv()
    result = DoubleTopBottomIndicator(_params()).compute(df)
    confirmed = next(s for s in result.signals if s.payload["event"] == "double_bottom_confirmed")
    assert confirmed.bar_time == df.index[19]
    assert confirmed.payload["neckline"] == pytest.approx(117.0)


def test_target_is_neckline_plus_depth_and_reached() -> None:
    df = _double_bottom_ohlcv()
    result = DoubleTopBottomIndicator(_params()).compute(df)
    completed = next(s for s in result.signals if s.state == "completed")
    assert completed.payload["target"] == pytest.approx(137.5, abs=0.01)
    assert completed.bar_time == df.index[23]


def test_entry_marker_emitted_at_confirmation() -> None:
    """2026-09-04: kullanıcı "nerede AL sinyali geldiğini de yazman
    gerekiyor" dedi -- head_shoulders.py'deki AYNI marker altyapısı,
    tüm patterns/*.py dosyalarına portlandı."""
    df = _double_bottom_ohlcv()
    result = DoubleTopBottomIndicator(_params()).compute(df)
    entry = next(m for m in result.markers if m.kind.startswith("pattern_entry_long:"))
    assert entry.text == "AL"
    completed = next(s for s in result.signals if s.state == "completed")
    assert entry.t == completed.bar_time


def test_no_double_top_false_positive_for_asymmetric_neckline_peaks() -> None:
    """idx7(117)/idx14(105) tepe çifti eq_tol'u (varsayılan 0.02) çok aşıyor
    (~%11) -> hiç double_top adayı üretilmemeli."""
    df = _double_bottom_ohlcv()
    result = DoubleTopBottomIndicator(_params()).compute(df)
    assert all(s.payload["pattern_name"] != "double_top" for s in result.signals)


def test_eq_tol_too_strict_filters_out_pair() -> None:
    df = _double_bottom_ohlcv()
    strict = DoubleTopBottomIndicator(DoubleTopBottomParams(left=2, right=2, eq_tol=0.001))
    result = strict.compute(df)
    assert result.signals == []


def test_hologram_polygon_traces_close_path_p1_to_p2() -> None:
    """Hologram artık düz 3 köşeli bir üçgen DEĞİL, p1->p2 arası GERÇEK
    kapanış fiyatı yolunu izliyor (2026-09-03, bkz. modül yorumu) — bu
    yüzden nokta sayısı bar aralığı kadar (idx2..idx12 dahil = 11)."""
    df = _double_bottom_ohlcv()
    result = DoubleTopBottomIndicator(_params()).compute(df)
    hologram = next(p for p in result.polygons if p.style == "pattern_hologram")
    prices = [price for _t, price in hologram.points]
    close = df["close"].to_numpy()
    assert prices == pytest.approx(list(close[2:13]))
    assert hologram.points[0][0] == df.index[2]
    assert hologram.points[-1][0] == df.index[12]


def test_registers_in_registry() -> None:
    df = build_registry_smoke_ohlcv()
    try:
        registry.register(DoubleTopBottomIndicator(), df)
    except RegistryError as exc:
        if "zaten kayıtlı" not in str(exc):
            raise
    assert registry.get("patterns.double_top_bottom") is DoubleTopBottomIndicator


def test_passes_repaint() -> None:
    """cut_points, boyun kırılımı ve hedef barlarının HEPSİNİN zaten
    gerçekleştiği son barlardan seçilir (golden_zone.py'nin aynı deseni)."""
    df = _double_bottom_ohlcv()
    cut_points = list(range(20, len(df) + 1))
    report = repaint_test(DoubleTopBottomIndicator(_params()), df, cut_points=cut_points)
    assert report.passed, report.mismatches
