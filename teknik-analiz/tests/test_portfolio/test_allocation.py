"""tlab.portfolio.allocation — 11/KURAL-05 (handcrafting), ORAN-07 (Tablo 8).

**DÜRÜST NOT**: `docs/spec/tlab_10_portfolio.md`'nin taslak kabul kriteri #3
16-varlıklı bir örneği (Tablo 10/11) de istiyordu — ama bu tablolar K3'ün
hedefli çıkarımına DAHİL EDİLMEDİ (`bilgi-bankasi/teknik/11_carver_
systematic.md`'de yalnızca Tablo 8/12/14 var, 10/11 YOK). Faz 8A/8E'deki
AYNI "eksik dış referans" emsaliyle: 16-varlıklı senaryo test EDİLMEDİ,
genel özyinelemeli algoritma yalnızca DOĞRULANABİLİR (Tablo 8) örneklerle
test edildi."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tlab.portfolio.allocation import (
    apply_sharpe_adjustment,
    handcraft_weights,
    periodic_handcraft_schedule,
)
from tlab.testing.repaint import allocation_repaint_test


def _corr_df(assets: list[str], pairs: dict[tuple[str, str], float]) -> pd.DataFrame:
    n = len(assets)
    m = pd.DataFrame(np.eye(n), index=assets, columns=assets)
    for (a, b), v in pairs.items():
        m.loc[a, b] = v
        m.loc[b, a] = v
    return m


def test_flat_three_asset_matches_book_example_regardless_of_column_order() -> None:
    """Kabul kriteri #3 (birinci yarı): US 20yıl bond/S&P 500/NASDAQ,
    Bond-SP500≈0.0, Bond-Nasdaq≈0.0, SP500-Nasdaq≈0.9 -> Tablo 8 satırı
    (0.0,0.9,0.0) -> %27/%46/%27 (Bond en YÜKSEK ağırlığı alır, çünkü diğer
    ikisiyle neredeyse hiç korele değil). Sembol SIRASINDAN bağımsız
    olmalı (permütasyon aramasının doğruluğunu da doğrular)."""
    pairs = {("Bond", "SP500"): 0.0, ("Bond", "Nasdaq"): 0.0, ("SP500", "Nasdaq"): 0.9}
    for order in [
        ["Bond", "SP500", "Nasdaq"],
        ["SP500", "Nasdaq", "Bond"],
        ["Nasdaq", "Bond", "SP500"],
    ]:
        corr = _corr_df(order, pairs)
        w = handcraft_weights(corr)
        assert w["Bond"] == pytest.approx(0.46, abs=1e-9)
        assert w["SP500"] == pytest.approx(0.27, abs=1e-9)
        assert w["Nasdaq"] == pytest.approx(0.27, abs=1e-9)
        assert sum(w.values()) == pytest.approx(1.0)


def test_grouped_two_level_matches_book_example() -> None:
    """Kabul kriteri #3 (ikinci yarı): Bond kendi grubunda, {SP500,Nasdaq}
    başka bir grupta -> üst seviyede 2 grup (Bond-vs-equities korelasyonu
    ~0.0) %50/%50, equities grubu İÇİNDE 2 varlık her zaman %50/%50 ->
    nihai %50/%25/%25."""
    pairs = {("Bond", "SP500"): 0.0, ("Bond", "Nasdaq"): 0.0, ("SP500", "Nasdaq"): 0.9}
    corr = _corr_df(["Bond", "SP500", "Nasdaq"], pairs)
    w = handcraft_weights(corr, groups=[["Bond"], ["SP500", "Nasdaq"]])
    assert w["Bond"] == pytest.approx(0.50, abs=1e-9)
    assert w["SP500"] == pytest.approx(0.25, abs=1e-9)
    assert w["Nasdaq"] == pytest.approx(0.25, abs=1e-9)


@pytest.mark.parametrize(
    "ab,ac,bc,expected",
    [
        (0.0, 0.5, 0.0, (0.30, 0.40, 0.30)),
        (0.5, 0.0, 0.5, (0.37, 0.26, 0.37)),
        (0.0, 0.5, 0.9, (0.45, 0.45, 0.10)),
        (0.9, 0.0, 0.9, (0.39, 0.22, 0.39)),
        (0.5, 0.9, 0.5, (0.29, 0.42, 0.29)),
        (0.9, 0.5, 0.9, (0.42, 0.16, 0.42)),
    ],
)
def test_all_table8_three_asset_rows(
    ab: float, ac: float, bc: float, expected: tuple[float, float, float]
) -> None:
    corr = _corr_df(["A", "B", "C"], {("A", "B"): ab, ("A", "C"): ac, ("B", "C"): bc})
    w = handcraft_weights(corr)
    assert (w["A"], w["B"], w["C"]) == pytest.approx(expected, abs=1e-9)


def test_single_asset_gets_full_weight() -> None:
    corr = pd.DataFrame([[1.0]], index=["X"], columns=["X"])
    assert handcraft_weights(corr) == {"X": 1.0}


def test_two_asset_group_always_fifty_fifty_regardless_of_correlation() -> None:
    for corr_val in (0.0, 0.5, 0.95):
        corr = _corr_df(["X", "Y"], {("X", "Y"): corr_val})
        w = handcraft_weights(corr)
        assert w == pytest.approx({"X": 0.5, "Y": 0.5})


def test_equal_correlation_n_assets_get_equal_weight() -> None:
    assets = ["A", "B", "C", "D", "E"]
    m = np.full((len(assets), len(assets)), 0.4)
    np.fill_diagonal(m, 1.0)
    corr = pd.DataFrame(m, index=assets, columns=assets)
    w = handcraft_weights(corr)
    for a in assets:
        assert w[a] == pytest.approx(0.2)


def test_four_plus_unequal_correlation_without_groups_raises() -> None:
    """11/KURAL-05 adım 4: kitap N>=4 farklı-korelasyonlu bir otomatik
    gruplama algoritması vermiyor — `groups` verilmeden ValueError."""
    assets = ["A", "B", "C", "D"]
    corr = pd.DataFrame(
        [[1.0, 0.1, 0.9, 0.0], [0.1, 1.0, 0.2, 0.5], [0.9, 0.2, 1.0, 0.3], [0.0, 0.5, 0.3, 1.0]],
        index=assets, columns=assets,
    )
    with pytest.raises(ValueError):
        handcraft_weights(corr)


def test_negative_correlation_floored_before_lookup() -> None:
    """Negatif korelasyon sıfıra taban değeri verilir — negatif AB ile
    AB=0.0 AYNI sonucu üretmeli (11/KURAL-05 adım 5)."""
    corr_neg = _corr_df(["A", "B", "C"], {("A", "B"): -0.5, ("A", "C"): 0.5, ("B", "C"): -0.5})
    corr_zero = _corr_df(["A", "B", "C"], {("A", "B"): 0.0, ("A", "C"): 0.5, ("B", "C"): 0.0})
    assert handcraft_weights(corr_neg) == pytest.approx(handcraft_weights(corr_zero))


def test_apply_sharpe_adjustment_renormalizes() -> None:
    base = {"A": 0.5, "B": 0.5}
    adjusted = apply_sharpe_adjustment(base, {"A": 1.2, "B": 0.8})
    assert sum(adjusted.values()) == pytest.approx(1.0)
    assert adjusted["A"] > adjusted["B"]


def test_periodic_schedule_is_piecewise_constant_and_recompute_dates() -> None:
    idx = pd.date_range("2020-01-01", periods=400, freq="D")
    rng = np.random.default_rng(11)
    returns = pd.DataFrame(
        {"A": rng.normal(0, 1, 400), "B": rng.normal(0, 1, 400), "C": rng.normal(0, 1, 400)},
        index=idx,
    )
    recompute_dates = [idx[150], idx[250], idx[350]]
    schedule = periodic_handcraft_schedule(returns, recompute_dates, correlation_window=100)
    assert set(schedule) == set(recompute_dates)
    for w in schedule.values():
        assert sum(w.values()) == pytest.approx(1.0)


def test_periodic_schedule_skips_recompute_dates_with_insufficient_history() -> None:
    idx = pd.date_range("2020-01-01", periods=50, freq="D")
    rng = np.random.default_rng(2)
    returns = pd.DataFrame({"A": rng.normal(0, 1, 50), "B": rng.normal(0, 1, 50)}, index=idx)
    schedule = periodic_handcraft_schedule(returns, [idx[10]], correlation_window=100)
    assert schedule == {}


def test_allocation_repaint_test_passes_for_periodic_schedule() -> None:
    """Kabul kriteri #6: periyodik tahsis şeması gerçek bir non-repaint
    sözleşmesi taşımalı — `allocation_repaint_test` bunu doğrular."""
    idx = pd.date_range("2020-01-01", periods=400, freq="D")
    rng = np.random.default_rng(9)
    returns = pd.DataFrame(
        {"A": rng.normal(0, 1, 400), "B": rng.normal(0, 1, 400), "C": rng.normal(0, 1, 400)},
        index=idx,
    )
    recompute_dates = [idx[150], idx[200], idx[250], idx[300], idx[350]]

    def compute(dates: list[pd.Timestamp]) -> dict[pd.Timestamp, dict[str, float]]:
        return periodic_handcraft_schedule(returns, dates, correlation_window=100)

    report = allocation_repaint_test(compute, recompute_dates)
    assert report.passed, report.mismatches
