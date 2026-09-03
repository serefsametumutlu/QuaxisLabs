"""Faz 0.5, A3 — `viz/live.py::compute_live`/`compute_structure_report`'ın
`supported_timeframes` kapısı. Gerçek veriye ULAŞMADAN (kapı store.get()'ten
ÖNCE tetiklenir) net bir ValueError beklenir -- ağdan bağımsız."""

from __future__ import annotations

import pytest

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
