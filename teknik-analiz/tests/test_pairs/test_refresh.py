"""`tlab/indicators/pairs/refresh.py` -- `config/pairs.yaml`'ı yeniden üreten
`write_pairs_yaml`'ın saf-yazma davranışı.

2026-09-04: bu mantık eskiden yalnızca `scripts/pair_denetim.py`nin (pytest
kapsamı DIŞINDaki bir CLI betiği) içinde tanımlıydı -- web'in "Çift
Listesini Yenile" butonu (`web/backend/routes/pairs_refresh.py`) da AYNI
fonksiyonu çağırdığı için artık `tlab/` paketinin bir parçası ve test
kapsamında."""

from __future__ import annotations

from pathlib import Path

from tlab.indicators.pairs.discovery import PairCandidate, load_pairs_yaml
from tlab.indicators.pairs.refresh import write_pairs_yaml


def _candidate(y: str, x: str) -> PairCandidate:
    return PairCandidate(
        symbol_y=y, symbol_x=x, corr=0.91, adf_pvalue=0.02, halflife=12.5,
        beta=0.87, n_bars=600, p_raw=0.01, p_adjusted=0.02, n_tests=100,
        fdr_passed=True,
    )


def test_write_pairs_yaml_round_trips_with_load_pairs_yaml(tmp_path: Path) -> None:
    out = tmp_path / "pairs.yaml"
    candidates = [_candidate("AKBNK", "GARAN"), _candidate("SISE", "CIMSA")]
    write_pairs_yaml(str(out), candidates, fdr_q=0.05, oos_split=None)

    loaded = load_pairs_yaml(str(out))
    assert loaded == [("AKBNK", "GARAN"), ("SISE", "CIMSA")]


def test_write_pairs_yaml_header_documents_the_run_settings(tmp_path: Path) -> None:
    out = tmp_path / "pairs.yaml"
    write_pairs_yaml(str(out), [_candidate("A", "B")], fdr_q=0.05, oos_split=0.5)
    text = out.read_text(encoding="utf-8")
    assert "fdr_q=0.05" in text
    assert "oos_split=0.5" in text


def test_write_pairs_yaml_empty_candidates_produces_empty_list(tmp_path: Path) -> None:
    out = tmp_path / "pairs.yaml"
    write_pairs_yaml(str(out), [], fdr_q=None, oos_split=None)
    assert load_pairs_yaml(str(out)) == []
