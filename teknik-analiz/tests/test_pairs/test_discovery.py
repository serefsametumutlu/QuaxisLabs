"""discovery.py: eşbütünleşik çift ekranı + sektör filtresi.

Faz 2, 2B (2026-09-04): `discover_pairs`'in varsayılanları artık `fdr_q=0.05`
+ `oos_split=0.5` içeriyor (bkz. discovery.py docstring'i) -- bu dosyanın
ÇEKİRDEK eşbütünleşme-algılama testleri (aşağıdaki ilk 4 fonksiyon) BİLİNÇLİ
OLARAK `fdr_q=None, oos_split=None` geçiriyor (tek bir küçük sentetik
örneklemde FDR'nin M=1 istatistiksel gücü neredeyse anlamsız, OOS split ise
250 barlık yarıların fixture'ın periyodik şok desenini (100 bar periyot)
seyreltmesi riskini taşır) -- Šidák/FDR/OOS'un KENDİSİ ayrı, özel testlerle
(aşağıda) doğrulanıyor."""

from __future__ import annotations

import warnings

import pytest

from tests.test_pairs.fixtures import build_cointegrated_pair
from tlab.indicators.pairs.discovery import discover_pairs, load_economic_link_map


def test_finds_the_known_cointegrated_pair() -> None:
    df_y, df_x = build_cointegrated_pair()
    prices = {"YT": df_y["close"], "XT": df_x["close"]}
    sector_map = {"YT": "Test", "XT": "Test"}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        candidates = discover_pairs(
            prices, sector_map=sector_map, corr_min=0.2, adf_max=0.10,
            halflife_range=(1.0, 400.0), same_sector_only=True, fdr_q=None, oos_split=None,
        )
    assert len(candidates) == 1
    c = candidates[0]
    assert {c.symbol_y, c.symbol_x} == {"YT", "XT"}
    assert 0.0 <= c.adf_pvalue < 0.10
    assert c.fdr_passed is None
    assert c.adf_p_is is None and c.adf_p_oos is None


def test_unrelated_random_walks_are_not_flagged() -> None:
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(3)
    index = pd.date_range("2024-01-01", periods=400, freq="D", tz="Europe/Istanbul")
    a = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.01, 400))), index=index)
    b = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.01, 400))), index=index)
    sector_map = {"A": "Test", "B": "Test"}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        candidates = discover_pairs(
            {"A": a, "B": b}, sector_map=sector_map, corr_min=0.7, adf_max=0.05,
            same_sector_only=True, fdr_q=None, oos_split=None,
        )
    assert candidates == []


def test_unknown_sector_excludes_symbol_when_same_sector_only() -> None:
    df_y, df_x = build_cointegrated_pair()
    prices = {"YT": df_y["close"], "XT": df_x["close"]}
    sector_map = {"YT": "Bankacılık"}  # XT bilinmeyen sektör -> haric tutulmali
    candidates = discover_pairs(
        prices, sector_map=sector_map, same_sector_only=True, corr_min=0.1, adf_max=1.0,
        fdr_q=None, oos_split=None,
    )
    assert candidates == []


def test_same_sector_pair_is_considered() -> None:
    df_y, df_x = build_cointegrated_pair()
    prices = {"YT": df_y["close"], "XT": df_x["close"]}
    sector_map = {"YT": "Bankacılık", "XT": "Bankacılık"}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        candidates = discover_pairs(
            prices, sector_map=sector_map, same_sector_only=True,
            corr_min=0.2, adf_max=0.10, halflife_range=(1.0, 400.0),
            fdr_q=None, oos_split=None,
        )
    assert len(candidates) == 1


# --- Faz 2, 2B -- Šidák + FDR + OOS + economic_link_map --------------------


def test_sidak_adjustment_makes_adf_pvalue_larger_than_raw() -> None:
    """p_adjusted = 1-(1-p_raw)^2 HER ZAMAN p_raw'dan BÜYÜK (ya da eşit,
    p_raw=0 durumunda) -- iki yönün minimumunu almanın şişirdiği alfa'nın
    KONSERVATİF bir düzeltmesi."""
    df_y, df_x = build_cointegrated_pair()
    prices = {"YT": df_y["close"], "XT": df_x["close"]}
    sector_map = {"YT": "Test", "XT": "Test"}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        candidates = discover_pairs(
            prices, sector_map=sector_map, corr_min=0.2, adf_max=0.99,
            halflife_range=(1.0, 400.0), same_sector_only=True, fdr_q=None, oos_split=None,
        )
    assert len(candidates) == 1
    c = candidates[0]
    assert c.p_adjusted == c.adf_pvalue
    assert c.p_adjusted >= c.p_raw
    if c.p_raw > 0:
        assert c.p_adjusted > c.p_raw


def test_oos_split_requires_cointegration_in_both_halves() -> None:
    """Faz 2, 2B: `oos_split` verildiğinde ADAY hem in-sample hem out-of-
    sample'da eşiği geçmeli. Fixture'ın GERÇEK eşbütünleşik yapısı 250
    barlık her iki yarıda da (base random walk ortak) hâlâ geçerli olmalı
    -- `adf_p_is`/`adf_p_oos` ikisi de doldurulmuş ve eşiğin altında olmalı."""
    df_y, df_x = build_cointegrated_pair(n=500)
    prices = {"YT": df_y["close"], "XT": df_x["close"]}
    sector_map = {"YT": "Test", "XT": "Test"}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # corr_min=0.1: 250 barlık YARILARDA ölçülen korelasyon (0.17), tam
        # 500 barlık örneklemden (0.2 eşiği kolayca geçen) DAHA DÜŞÜK --
        # beklenen bir örneklem-boyutu etkisi, eşik buna göre gevşetildi.
        candidates = discover_pairs(
            prices, sector_map=sector_map, corr_min=0.1, adf_max=0.20,
            halflife_range=(1.0, 400.0), same_sector_only=True, fdr_q=None,
            oos_split=0.5, min_overlap_bars=100,
        )
    assert len(candidates) == 1
    c = candidates[0]
    assert c.adf_p_is is not None and c.adf_p_is < 0.20
    assert c.adf_p_oos is not None and c.adf_p_oos < 0.20


def test_oos_split_none_means_full_sample_single_window() -> None:
    """`oos_split=None` -- eski davranış, `adf_p_is`/`adf_p_oos` doldurulmaz."""
    df_y, df_x = build_cointegrated_pair()
    prices = {"YT": df_y["close"], "XT": df_x["close"]}
    sector_map = {"YT": "Test", "XT": "Test"}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        candidates = discover_pairs(
            prices, sector_map=sector_map, corr_min=0.2, adf_max=0.10,
            halflife_range=(1.0, 400.0), same_sector_only=True, fdr_q=None, oos_split=None,
        )
    assert len(candidates) == 1
    assert candidates[0].adf_p_is is None
    assert candidates[0].adf_p_oos is None


def test_fdr_reports_n_tests_and_fdr_passed() -> None:
    """`fdr_q` verildiğinde `n_tests` (bu koşuda denenen TOPLAM kombinasyon
    sayısı) ve `fdr_passed` doldurulmalı. Tek kombinasyonluk (2 sembol)
    bir evrende n_tests=1, BH eşiği o TEK p'nin kendisi (k/m*q = 1/1*q = q)
    -- adf_max gevşek tutulup p_adjusted q'nun altında kalacak şekilde
    kurgulandı, fdr_passed True olmalı."""
    df_y, df_x = build_cointegrated_pair()
    prices = {"YT": df_y["close"], "XT": df_x["close"]}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        candidates = discover_pairs(
            prices, corr_min=0.2, adf_max=0.5, halflife_range=(1.0, 400.0),
            same_sector_only=False, fdr_q=0.5, oos_split=None,
        )
    assert len(candidates) == 1
    c = candidates[0]
    assert c.n_tests == 1
    assert c.fdr_passed is True


def test_fdr_can_reject_a_candidate_that_passes_adf_max_alone() -> None:
    """Sıkı bir `fdr_q`, gevşek bir `adf_max`'ı geçen bir adayı YİNE DE
    eleyebilmeli -- FDR, adf_max'tan BAĞIMSIZ ek bir kapı. `build_
    cointegrated_pair`'in GÜÇLÜ varsayılan sinyali (p≈1e-15) herhangi bir
    makul fdr_q'yu geçer -- burada BİLEREK ZAYIF bir eşbütünleşme (küçük
    ortak bileşen + büyük kendine özgü gürültü, p_adjusted≈0.08) kurgulandı."""
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(42)
    n = 300
    base = np.cumsum(rng.normal(0, 0.01, n))
    y_log = base + np.cumsum(rng.normal(0, 0.03, n)) * 0.3
    x_log = base + np.cumsum(rng.normal(0, 0.03, n)) * 0.3
    idx = pd.date_range("2024-01-01", periods=n, freq="D", tz="Europe/Istanbul")
    prices = {
        "Y": pd.Series(100 * np.exp(y_log), index=idx),
        "X": pd.Series(50 * np.exp(x_log), index=idx),
    }
    sector_map = {"Y": "Test", "X": "Test"}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        accepted_without_fdr = discover_pairs(
            prices, sector_map=sector_map, corr_min=0.5, adf_max=0.99,
            halflife_range=(0.0, 10_000.0), same_sector_only=True, fdr_q=None, oos_split=None,
        )
        rejected_with_fdr = discover_pairs(
            prices, corr_min=0.5, adf_max=0.99, halflife_range=(0.0, 10_000.0),
            same_sector_only=False, fdr_q=0.01, oos_split=None,
        )
    assert len(accepted_without_fdr) == 1  # adf_max tek başına kabul ediyor
    assert rejected_with_fdr == []  # fdr_q=0.01 AYNI adayı eliyor


def test_economic_link_map_includes_pair_outside_shared_sector() -> None:
    """`same_sector_only=True` iken farklı sektörlerdeki iki sembol normalde
    dışlanır -- `economic_link_map`'te eşleşiyorlarsa DAHİL edilmeli."""
    df_y, df_x = build_cointegrated_pair()
    prices = {"YT": df_y["close"], "XT": df_x["close"]}
    sector_map = {"YT": "Bankacılık", "XT": "Sanayi"}  # FARKLI sektörler
    link_map = {"YT": {"XT"}}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        candidates = discover_pairs(
            prices, sector_map=sector_map, same_sector_only=True,
            economic_link_map=link_map,
            corr_min=0.2, adf_max=0.10, halflife_range=(1.0, 400.0),
            fdr_q=None, oos_split=None,
        )
    assert len(candidates) == 1


def test_economic_link_map_does_not_bypass_sector_filter_when_unrelated() -> None:
    """`economic_link_map` verilmiş ama bu ÇİFTİ içermiyorsa, farklı
    sektörler hâlâ dışlanmalı (varsayılan davranış korunuyor)."""
    df_y, df_x = build_cointegrated_pair()
    prices = {"YT": df_y["close"], "XT": df_x["close"]}
    sector_map = {"YT": "Bankacılık", "XT": "Sanayi"}
    link_map = {"ABCD": {"EFGH"}}  # bu çiftle ilgisiz
    candidates = discover_pairs(
        prices, sector_map=sector_map, same_sector_only=True,
        economic_link_map=link_map,
        corr_min=0.1, adf_max=1.0, fdr_q=None, oos_split=None,
    )
    assert candidates == []


def test_whole_universe_mode_requires_fdr_q() -> None:
    """Faz 2, 2B "SEKTÖR MU TÜM EVREN Mİ" kararı: `same_sector_only=False`
    iken `fdr_q=None` -- düzeltmesiz binlerce kombinasyonluk bir aramanın
    güvenilmez olması -- `ValueError` fırlatmalı."""
    df_y, df_x = build_cointegrated_pair()
    prices = {"YT": df_y["close"], "XT": df_x["close"]}
    with pytest.raises(ValueError, match="fdr_q"):
        discover_pairs(prices, same_sector_only=False, fdr_q=None)


def test_load_economic_link_map_missing_file_returns_empty_dict(tmp_path) -> None:  # type: ignore[no-untyped-def]
    result = load_economic_link_map(str(tmp_path / "does_not_exist.yaml"))
    assert result == {}


def test_load_economic_link_map_parses_groups_symmetrically(tmp_path) -> None:  # type: ignore[no-untyped-def]
    p = tmp_path / "links.yaml"
    p.write_text("links:\n  - [A, B, C]\n", encoding="utf-8")
    result = load_economic_link_map(str(p))
    assert result == {"A": {"B", "C"}, "B": {"A", "C"}, "C": {"A", "B"}}
