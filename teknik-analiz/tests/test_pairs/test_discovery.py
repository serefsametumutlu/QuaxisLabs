"""discovery.py: eşbütünleşik çift ekranı + sektör filtresi."""

from __future__ import annotations

import warnings

from tests.test_pairs.fixtures import build_cointegrated_pair
from tlab.indicators.pairs.discovery import discover_pairs


def test_finds_the_known_cointegrated_pair() -> None:
    df_y, df_x = build_cointegrated_pair()
    prices = {"YT": df_y["close"], "XT": df_x["close"]}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        candidates = discover_pairs(
            prices, corr_min=0.2, adf_max=0.10, halflife_range=(1.0, 400.0),
            same_sector_only=False,
        )
    assert len(candidates) == 1
    c = candidates[0]
    assert {c.symbol_y, c.symbol_x} == {"YT", "XT"}
    assert 0.0 <= c.adf_pvalue < 0.10


def test_unrelated_random_walks_are_not_flagged() -> None:
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(3)
    index = pd.date_range("2024-01-01", periods=400, freq="D", tz="Europe/Istanbul")
    a = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.01, 400))), index=index)
    b = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.01, 400))), index=index)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        candidates = discover_pairs(
            {"A": a, "B": b}, corr_min=0.7, adf_max=0.05, same_sector_only=False,
        )
    assert candidates == []


def test_unknown_sector_excludes_symbol_when_same_sector_only() -> None:
    df_y, df_x = build_cointegrated_pair()
    prices = {"YT": df_y["close"], "XT": df_x["close"]}
    sector_map = {"YT": "Bankacılık"}  # XT bilinmeyen sektör -> haric tutulmali
    candidates = discover_pairs(
        prices, sector_map=sector_map, same_sector_only=True, corr_min=0.1, adf_max=1.0,
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
        )
    assert len(candidates) == 1
