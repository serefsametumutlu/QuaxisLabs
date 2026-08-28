"""run_eod: ağa çıktığı (store.update()) için @pytest.mark.network — varsayılan
`pytest -m "not network"` koşusunda ATLANIR."""

from __future__ import annotations

import warnings

import pytest

from tlab.scanner.eod import run_eod
from tlab.scanner.results import ResultsStore


@pytest.mark.network
def test_run_eod_small_universe_and_idempotent_second_run(tmp_path) -> None:
    db_path = tmp_path / "results.db"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        report1 = run_eod(
            market="bist", universe_override=["TCELL", "ISCTR"],
            indicator_names=["harmonic.pesavento"], results_db=db_path, force=True,
        )
        report2 = run_eod(
            market="bist", universe_override=["TCELL", "ISCTR"],
            indicator_names=["harmonic.pesavento"], results_db=db_path, force=False,
        )

    assert report1["status"] == "completed"
    assert report1["n_errors"] == 0
    assert report2["status"] == "skipped_existing"
    assert report2["run_id"] == report1["run_id"]

    store = ResultsStore(db_path=db_path)
    assert store.get_run(report1["run_id"]) is not None
    store.close()


@pytest.mark.network
def test_run_eod_notify_hook_called(tmp_path) -> None:
    calls: list[tuple[str, dict]] = []

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        run_eod(
            market="bist", universe_override=["TCELL"],
            indicator_names=["harmonic.pesavento"], results_db=tmp_path / "r2.db",
            force=True, notify=lambda event, payload: calls.append((event, payload)),
        )

    assert calls
    assert calls[0][0] == "eod_completed"
    assert calls[0][1]["status"] == "completed"
