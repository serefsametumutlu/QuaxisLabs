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
    """2026-09-01: sidebar'a bir "Taramalar" tablosu eklendiği için artık
    sayfada BİRDEN FAZLA `st.dataframe` var — `AppTest`'in dataframe
    proxy'si `key=` parametresini yansıtmıyor (denendi, hep `None` döner),
    bu yüzden doğru tablo KOLON ADLARINA göre bulunur, sabit bir index'e
    göre DEĞİL (kaç dataframe önce geldiği ileride tekrar değişebilir)."""
    at = AppTest.from_file(str(_DASHBOARD_PATH), default_timeout=60)
    at.run()
    signal_tables = [d for d in at.dataframe if "Olay" in d.value.columns]
    assert len(signal_tables) == 1
    df = signal_tables[0].value
    assert list(df["Sembol"]) == ["BAKAB"]
    assert list(df["Olay"]) == ["tobo_confirmed"]
    run_tables = [d for d in at.dataframe if "Tarih" in d.value.columns]
    assert len(run_tables) == 1
    assert list(run_tables[0].value["Tarih"]) == ["2026-08-30"]


def test_dashboard_has_theme_selector_with_three_options(isolated_results_db: Path) -> None:
    """2026-09-01: 3 tasarım dili ("Grafik Stil Vitrini" mockup'ının gerçek
    koda aktarımı) — sidebar'da bir tema seçici olmalı, hiçbiri
    `render_live`'a geçmeden ÖNCEKİ hâlde YOKTU."""
    at = AppTest.from_file(str(_DASHBOARD_PATH), default_timeout=60)
    at.run()
    theme_radios = [r for r in at.radio if r.label == "Tasarım"]
    assert len(theme_radios) == 1
    assert theme_radios[0].options == ["Klasik Beyaz Rapor", "Terminal Koyu", "Kağıt Rapor"]


def test_dashboard_scan_preset_selector_present(isolated_results_db: Path) -> None:
    """2026-09-01: `config/scans.yaml` preset'lerinden biriyle SINIRLI bir
    tarama çalıştırma seçeneği (kullanıcı isteği: "taramaları ayrı ayrı
    yapabilmeliyim") — preset açıklamaları yüklenip bir selectbox olarak
    sunulmalı."""
    at = AppTest.from_file(str(_DASHBOARD_PATH), default_timeout=60)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    preset_boxes = [s for s in at.selectbox if s.label == "Tarama Türü"]
    assert len(preset_boxes) == 1
    assert len(preset_boxes[0].options) > 0


def test_symbol_entry_without_cached_data_shows_graceful_error(
    isolated_results_db: Path,
) -> None:
    """Grafik bölümü sinyal listesinden BAĞIMSIZ çalışır: bir sembol
    girildiğinde (yerel parquet önbelleği olmasa bile) sayfa ÇÖKMEMELİ,
    anlaşılır bir `st.error` göstermeli."""
    at = AppTest.from_file(str(_DASHBOARD_PATH), default_timeout=60)
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
