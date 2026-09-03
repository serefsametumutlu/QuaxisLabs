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


def test_dashboard_lists_run_table_on_strategy_screen(isolated_results_db: Path) -> None:
    """2026-09-02 (sidebar/ekran mimarisi düzeltmesi): "Taramalar" tablosu
    artık varsayılan ekran olan Ekran 1'de (Strateji Seç) — `st.tabs`
    yerine `st.session_state["screen"]`'in sürdüğü tek-ekran render'da bir
    script koşusu yalnızca O ANKİ ekranı çizer."""
    at = AppTest.from_file(str(_DASHBOARD_PATH), default_timeout=60)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    run_tables = [d for d in at.dataframe if "Tarih" in d.value.columns]
    assert len(run_tables) == 1
    assert list(run_tables[0].value["Tarih"]) == ["2026-08-30"]


def test_dashboard_lists_seeded_signal_on_results_screen(isolated_results_db: Path) -> None:
    """Ekran 2 (Sonuç Listesi) — `active_run_id` set edilip o ekrana
    geçildiğinde sinyal tablosu tam okunur İndikatör adıyla görünmeli
    (bkz. `labels_tr.py::INDICATOR_DISPLAY_TR`)."""
    at = AppTest.from_file(str(_DASHBOARD_PATH), default_timeout=60)
    at.run()
    at.session_state["screen"] = "results"
    at.session_state["active_run_id"] = "bist_2026-08-30"
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    signal_tables = [d for d in at.dataframe if "Olay" in d.value.columns]
    assert len(signal_tables) == 1
    df = signal_tables[0].value
    assert list(df["Sembol"]) == ["BAKAB"]
    assert list(df["Olay"]) == ["tobo_confirmed"]
    assert list(df["İndikatör"]) == ["Omuz-Baş-Omuz / TOBO"]


def test_dashboard_has_dark_mode_toggle(isolated_results_db: Path) -> None:
    """2026-09-02 (kullanıcı geri bildirimi — "dark light düğmeli bir buton
    olmalıydı sağ yukarı da onu da bulamıyorum"): eskiden sidebar'a gömülü
    3-seçenekli bir `st.selectbox` idi (bulunamıyordu) — artık sayfanın en
    üstünde, `dark_mode` anahtarlı bir `st.toggle`."""
    at = AppTest.from_file(str(_DASHBOARD_PATH), default_timeout=60)
    at.run()
    toggles = [t for t in at.toggle if t.key == "dark_mode"]
    assert len(toggles) == 1
    assert toggles[0].value is False


def test_dashboard_sidebar_strategy_menu_present(isolated_results_db: Path) -> None:
    """2026-09-02 (kullanıcı geri bildirimi — sol menü + "Stratejiler"
    akordeon): `config/scans.yaml` preset'leri + preset'i olmayan
    kategoriler için CATALOG yedek girdileri (ör. Harmonik Formasyon) sol
    menüde kategoriye göre gruplanmış `st.expander`'lar içinde, her biri
    kendi `strat_{id}` anahtarlı butonuyla görünür — tıklamak DOĞRUDAN
    taramayı BAŞLATMAZ, önce Strateji Detayı ekranına geçer."""
    at = AppTest.from_file(str(_DASHBOARD_PATH), default_timeout=60)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    strat_buttons = [b for b in at.sidebar.button if b.key and b.key.startswith("strat_")]
    assert len(strat_buttons) > 0
    # Harmonik hiçbir preset'te temsil edilmiyor (bkz. config/scans.yaml) —
    # CATALOG yedeği devreye girip en az bir harmonik ekolü göstermeli.
    assert any(b.key.startswith("strat_harmonic.") for b in strat_buttons)


def test_symbol_entry_without_cached_data_shows_graceful_error(
    isolated_results_db: Path,
) -> None:
    """Grafik bölümü sinyal listesinden BAĞIMSIZ çalışır: bir sembol
    girildiğinde (yerel parquet önbelleği olmasa bile) sayfa ÇÖKMEMELİ,
    anlaşılır bir `st.error` göstermeli. Ekran 3'e (Grafik Detayı) doğrudan
    `session_state` ile geçilir (2026-09-02, `st.tabs` yerine tek-ekran
    render — bkz. modül docstring'i)."""
    at = AppTest.from_file(str(_DASHBOARD_PATH), default_timeout=60)
    at.run()
    at.session_state["screen"] = "chart"
    at.run()
    at.text_input[0].set_value("BAKAB").run()
    assert not at.exception, [str(e) for e in at.exception]
    assert any("Grafik oluşturulamadı" in e.value for e in at.error)


def test_dashboard_shows_empty_state_without_any_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    at = AppTest.from_file(str(_DASHBOARD_PATH), default_timeout=60)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    infos = [i.value for i in at.info]
    assert any("Henüz tamamlanmış bir tarama yok" in text for text in infos)
