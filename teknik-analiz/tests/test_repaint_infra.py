"""Faz 0 kanıt testleri: repaint test altyapısı, statik lint ve registry.

Bu dosya, altyapının kendisini doğrular: dürüst bir indikatör PASS almalı;
kasıtlı hileli indikatörler (pivot barına yazan, merkezi rolling kullanan)
FAIL almalı ve registry bunları reddetmeli.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests._sample_indicators import CenteredIndicator, CheatingIndicator, HonestIndicator
from tlab.core.errors import RegistryError
from tlab.core.indicator import Registry
from tlab.testing.fixtures import make_trend, make_zigzag
from tlab.testing.lint_lookahead import lint_file, lint_paths
from tlab.testing.repaint import repaint_test

# Peak, tail penceresinin (varsayılan 60) içine düşecek şekilde konumlandırıldı:
# n=150, tepe idx=130 -> partial'da tepeden sonraki barlar order(=5)'ten az
# olduğunda (cut=131..135) tepe henüz onaylanamaz; ama full'de zaten bilinir.
_PEAK_PIVOTS = [(0, 100.0), (60, 105.0), (100, 100.0), (130, 140.0), (149, 100.0)]


def test_honest_indicator_passes_repaint() -> None:
    df = make_trend(n=120, slope=0.05, noise=0.3, seed=3)
    report = repaint_test(HonestIndicator(), df)
    assert report.passed, report.mismatches
    assert report.stats["cuts_checked"] == 60


def test_cheating_indicator_fails_repaint() -> None:
    df = make_zigzag(_PEAK_PIVOTS, noise=0.0, seed=1)
    report = repaint_test(CheatingIndicator(), df, cut_points=list(range(128, 140)))
    assert not report.passed
    assert report.mismatches
    assert any("sonradan ortaya çıktı" in m for m in report.mismatches)


def test_centered_indicator_fails_repaint() -> None:
    df = make_trend(n=120, slope=0.05, noise=0.3, seed=5)
    report = repaint_test(CenteredIndicator(), df)
    assert not report.passed
    assert report.mismatches


def test_registry_rejects_cheating_indicator() -> None:
    df = make_zigzag(_PEAK_PIVOTS, noise=0.0, seed=1)
    reg = Registry()
    with pytest.raises(RegistryError):
        reg.register(CheatingIndicator, df)


def test_registry_accepts_honest_indicator() -> None:
    df = make_trend(n=120, slope=0.05, noise=0.3, seed=3)
    reg = Registry()
    reg.register(HonestIndicator, df)
    assert "test.honest_sma_cross" in reg.list()
    assert reg.list(category="testing") == ["test.honest_sma_cross"]


def test_registry_rejects_duplicate_name() -> None:
    df = make_trend(n=120, slope=0.05, noise=0.3, seed=3)
    reg = Registry()
    reg.register(HonestIndicator, df)
    with pytest.raises(RegistryError):
        reg.register(HonestIndicator, df)


def test_lint_flags_centered_rolling() -> None:
    sample_file = Path(__file__).parent / "_sample_indicators.py"
    issues = lint_file(sample_file)
    codes = {i.code for i in issues}
    assert "LA002" in codes  # rolling(center=True)
    assert "LA003" in codes  # argrelextrema kullanımı
    centered_issue = next(i for i in issues if i.code == "LA002")
    assert centered_issue.severity == "error"


def test_lint_paths_scopes_to_features_and_indicators(tmp_path: Path) -> None:
    (tmp_path / "tlab" / "indicators").mkdir(parents=True)
    (tmp_path / "tlab" / "other").mkdir(parents=True)

    bad_file = tmp_path / "tlab" / "indicators" / "bad.py"
    bad_file.write_text("x = series.shift(-1)\n", encoding="utf-8")

    ignored_file = tmp_path / "tlab" / "other" / "also_bad.py"
    ignored_file.write_text("x = series.shift(-1)\n", encoding="utf-8")

    issues = lint_paths(tmp_path)
    assert len(issues) == 1
    assert issues[0].code == "LA001"
    assert issues[0].severity == "error"
    assert "bad.py" in issues[0].file
