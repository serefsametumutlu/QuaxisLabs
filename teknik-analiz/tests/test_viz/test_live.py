"""Faz 0.5, A3 — `viz/live.py::compute_live`/`compute_structure_report`'ın
`supported_timeframes` kapısı. Gerçek veriye ULAŞMADAN (kapı store.get()'ten
ÖNCE tetiklenir) net bir ValueError beklenir -- ağdan bağımsız."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from tlab.core.types import Timeframe
from tlab.testing.fixtures import make_trend
from tlab.viz.live import compute_live, compute_structure_report


def test_compute_live_raises_for_unsupported_timeframe() -> None:
    with pytest.raises(ValueError, match="çalışmıyor"):
        compute_live("momentum.alpha_rank", "TCELL", "4h", "bist")


def test_compute_live_raises_names_supported_timeframes_in_message() -> None:
    with pytest.raises(ValueError, match="1D"):
        compute_live("momentum.momentum_rank", "TCELL", "1h", "bist")


def test_compute_structure_report_raises_for_unsupported_timeframe() -> None:
    with pytest.raises(ValueError, match="çalışmıyor"):
        compute_structure_report("TCELL", "w1", "bist")


def test_compute_live_invalid_tf_string_still_raises_first() -> None:
    """Geçersiz bir tf string'i (desteklenmeyen bir tf DEĞİL, hiç
    tanınmayan bir tf), supported_timeframes kapısından ÖNCE, kendi
    mesajıyla reddedilmeli."""
    with pytest.raises(ValueError, match="Geçersiz tf"):
        compute_live("momentum.alpha_rank", "TCELL", "1m", "bist")


# --- 2026-09-04 GERÇEK HATA regresyon testleri --------------------------
#
# `IndicatorResult` üreten HER indikatörün kendi compute()'u `timeframe=
# Timeframe.D1`'i sabit yazıyordu (params hiçbir yerde tf'nin kendisini
# saklamıyor) -- `compute_live`/`compute_structure_report`, `result.symbol
# = symbol`'la AYNI desende, sonradan doğru tf'yi atıyor. `Store` burada
# MOCK'lanır (gerçek cache/ağ gerektirmez); gerçek `patterns.double_top_
# bottom`/`pair.relative_momentum` sentetik veri üzerinde ÇALIŞTIRILIR --
# amaç, o indikatörlerin KENDİ (yanlış) D1 sabitinin çağıran tarafından
# ezildiğini uçtan uca doğrulamak.


def test_compute_live_sets_result_timeframe_to_requested_tf() -> None:
    df = make_trend(n=200, timeframe=Timeframe.H4)
    with patch("tlab.viz.live.Store") as mock_store_cls:
        mock_store_cls.return_value.get.return_value = df
        result, _ = compute_live("patterns.double_top_bottom", "TEST", "4h", "bist")
    assert result.timeframe == Timeframe.H4


def test_compute_live_pair_indicator_sets_result_timeframe() -> None:
    df = make_trend(n=200, timeframe=Timeframe.H4)
    with patch("tlab.viz.live.Store") as mock_store_cls:
        mock_store_cls.return_value.get.return_value = df
        result, df_out = compute_live("pair.relative_momentum", "TEST/OTHER", "4h", "bist")
    assert result.timeframe == Timeframe.H4
    assert df_out is None


def test_compute_structure_report_sets_result_timeframe() -> None:
    df = make_trend(n=200, timeframe=Timeframe.H4)
    with patch("tlab.viz.live.Store") as mock_store_cls:
        mock_store_cls.return_value.get.return_value = df
        ps_result, sf_result, _ = compute_structure_report("TEST", "4h", "bist")
    assert ps_result.timeframe == Timeframe.H4
    assert sf_result.timeframe == Timeframe.H4
