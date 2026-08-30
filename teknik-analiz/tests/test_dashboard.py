"""`tlab/dashboard.py` (Streamlit tarama panosu) için duman testi.

Gerçek bir tarayıcı/oturum GEREKMEZ — `streamlit.testing.v1.AppTest` script'i
in-process çalıştırıp DOM benzeri bir öğe ağacı üretir. `ResultsStore`'un
varsayılan yolu (`outputs/results.db`, CWD'ye göre) kullanıcının GERÇEK
sonuç veritabanını KİRLETMESİN diye `monkeypatch.chdir` ile izole bir
`tmp_path` içinde, önceden doldurulmuş sahte bir DB üzerinde çalıştırılır."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from tlab.core.types import IndicatorResult, Signal, Timeframe
from tlab.scanner.results import ResultsStore, RunRecord, SymbolIndicatorRun

_DASHBOARD_PATH = Path(__file__).resolve().parents[1] / "tlab" / "dashboard.py"


def _seed_results_db(base_dir: Path) -> None:
    store = ResultsStore(db_path=base_dir / "outputs" / "results.db")
    store.start_run(
        RunRecord(
            run_id="bist_2026-08-30", started_at=datetime.now(UTC).isoformat(), finished_at=None,
            market="bist", timeframes=["1d"], universe_size=1,
            indicator_names=["patterns.head_shoulders"], git_sha=None, status="running",
        )
    )
    signal = Signal(
        bar_time=datetime(2026, 8, 20, tzinfo=UTC), detected_at=datetime(2026, 8, 20, tzinfo=UTC),
        direction="long", state="confirmed", score=0.6,
        payload={
            "pattern_id": "tobo_1_2_3", "pattern_name": "tobo",
            "event": "tobo_confirmed", "target": 50.0,
        },
    )
    result = IndicatorResult(
        indicator="patterns.head_shoulders", version="0.1.0", params_hash="x",
        symbol="BAKAB", timeframe=Timeframe.D1, signals=[signal],
        last_state={"tobo_1_2_3": {"state": "confirmed"}},
    )
    store.persist(
        "bist_2026-08-30",
        [
            SymbolIndicatorRun(
                symbol="BAKAB", market="bist", timeframe="1d", indicator="patterns.head_shoulders",
                params_hash="x", result=result, error=None,
            )
        ],
    )
    store.finish_run("bist_2026-08-30", datetime.now(UTC).isoformat(), "completed")
    store.close()


@pytest.fixture
def isolated_results_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    _seed_results_db(tmp_path)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_dashboard_runs_without_exception(isolated_results_db: Path) -> None:
    at = AppTest.from_file(str(_DASHBOARD_PATH), default_timeout=60)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]


def test_dashboard_lists_seeded_signal(isolated_results_db: Path) -> None:
    at = AppTest.from_file(str(_DASHBOARD_PATH), default_timeout=60)
    at.run()
    assert len(at.dataframe) == 1
    df = at.dataframe[0].value
    assert list(df["Sembol"]) == ["BAKAB"]
    assert list(df["Olay"]) == ["tobo_confirmed"]


def test_dashboard_shows_empty_state_without_any_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    at = AppTest.from_file(str(_DASHBOARD_PATH), default_timeout=60)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    infos = [i.value for i in at.info]
    assert any("Henüz tamamlanmış bir tarama yok" in text for text in infos)
