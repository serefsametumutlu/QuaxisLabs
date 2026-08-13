"""SPEC: docs/spec/spec_dashboard.md -- `scripts/tarama_toplu.py` testleri
(hata sınıflandırma, upsert entegrasyonu, `_resolve_targets`).

Gerçek ağ isteği ATILMAZ -- `pipeline.compute_multi_lens_score_for_ticker`
monkeypatch ile sahtelenir (tests/test_pipeline_multi_lens.py'nin
`izole_db` deseniyle AYNI ilke)."""

from __future__ import annotations

from decimal import Decimal

import pytest

import config
from src.analysis import calculator, lens_bilesik_skor
from src.analysis.lens_common import ComponentScore, ScoreResult
from src.bot import pipeline
from src.db import models, repository

import scripts.tarama_toplu as tarama_toplu


@pytest.fixture()
def izole_db(monkeypatch, tmp_path):
    engine, session_factory = models.create_engine_and_session(f"sqlite:///{tmp_path / 'test_tarama_toplu.db'}")
    models.init_db(engine)
    monkeypatch.setattr(repository, "DefaultSessionLocal", session_factory)
    monkeypatch.setattr(repository, "_default_db_initialized", True)
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")
    return engine


def _lens_sonucu(skor: Decimal, template: str, coverage_pct: Decimal = Decimal(100)) -> ScoreResult:
    return ScoreResult(
        ticker="TEST", period=(2026, 6), template=template, total_score=skor,
        badge="DENGELİ", data_coverage_pct=coverage_pct, data_sufficient=True,
        components=[ComponentScore(name="X", score=skor, weight_nominal=Decimal(100), weight_effective=Decimal(100), contribution=skor, reasoning_tr="açıklama")],
    )


def _fake_sonuc(ticker: str = "THYAO", market: str = "BIST") -> pipeline.MultiLensScoreResult:
    deger = _lens_sonucu(Decimal("8"), "değer", coverage_pct=Decimal("88"))
    kalite = _lens_sonucu(Decimal("6"), "kalite", coverage_pct=Decimal("100"))
    buyume = _lens_sonucu(Decimal("5"), "büyüme", coverage_pct=Decimal("62"))
    guvenlik = _lens_sonucu(Decimal("7"), "güvenlik", coverage_pct=Decimal("100"))
    bilesik = lens_bilesik_skor.hesapla_bilesik_skor(ticker, (2026, 6), deger, kalite, buyume, guvenlik)
    vm = calculator.ValuationMetrics(
        price=Decimal("305.50"), share_capital=Decimal("1000000"), market_cap=Decimal("305500000"),
        net_debt=Decimal("1000"), enterprise_value=Decimal("306500000"),
        pe_ratio=Decimal("6.8"), pb_ratio=Decimal("2.1"), ev_ebitda=Decimal("4.3"),
        ev_revenue=Decimal("1.2"), price_to_operating_profit=Decimal("5.5"),
    )
    return pipeline.MultiLensScoreResult(
        ticker=ticker, market=market, period=(2026, 6), company_name="Test A.Ş.",
        price=Decimal("305.50"), bilesik=bilesik, valuation_metrics=vm, template="sanayi",
    )


# --- _scan_one: başarılı tarama -----------------------------------------------------


def test_scan_one_basarili_tarama_market_scan_result_upsert_eder(izole_db, monkeypatch) -> None:
    monkeypatch.setattr(pipeline, "compute_multi_lens_score_for_ticker", lambda ticker, market: _fake_sonuc(ticker, market))
    with repository.get_session() as session:
        repository.upsert_sector_taxonomy(session, "THYAO", market="BIST", ust_sektor="Sanayi", sirket_turu="sanayi")
        session.commit()

    status = tarama_toplu._scan_one("THYAO", "BIST")

    assert status == "ok"
    with repository.get_session() as session:
        row = session.get(models.MarketScanResult, "THYAO")
        assert row.scan_status == "ok"
        assert row.template == "sanayi"
        assert row.currency == "TRY"
        assert row.pe_ratio == Decimal("6.8000")
        assert row.bilesik_data_coverage_pct is not None
        assert row.mercekler_detay["değer"][0]["name"] == "X"
        assert row.mercekler_detay["değer"][0]["score"] == "8"  # Decimal -> str, JSON-safe


# --- _scan_one: tarihsel_skorlar (docs/spec/spec_veri_tamlik_yol_haritasi.md §Skor Geçmişi) --------------


def _fake_tarihsel_snapshot(period: tuple[int, int], skor: Decimal, price: Decimal | None = None) -> pipeline.HistoricalLensSnapshot:
    return pipeline.HistoricalLensSnapshot(
        period=period, period_label=pipeline.quarter_label(period),
        deger_score=skor, deger_badge="DENGELİ", kalite_score=skor, kalite_badge="DENGELİ",
        buyume_score=skor, buyume_badge="DENGELİ", guvenlik_score=skor, guvenlik_badge="DENGELİ",
        bilesik_score=skor, bilesik_badge="DENGELİ", price=price,
    )


def test_scan_one_tarihsel_skorlar_db_ye_yazilir_eskiden_yeniye_siralanir(izole_db, monkeypatch) -> None:
    monkeypatch.setattr(pipeline, "compute_multi_lens_score_for_ticker", lambda ticker, market: _fake_sonuc(ticker, market))
    # compute_historical_lens_scores_for_ticker GÜNCEL dönemi İLK sırada
    # döner (bkz. pipeline.py docstring'i) -- _tarihsel_skorlar_to_list bunu
    # TERS çevirip ESKİDEN YENİYE saklamalı.
    monkeypatch.setattr(
        pipeline, "compute_historical_lens_scores_for_ticker",
        lambda sonuc, max_historical=3: [
            _fake_tarihsel_snapshot((2026, 6), Decimal("8")),
            _fake_tarihsel_snapshot((2026, 3), Decimal("7")),
            _fake_tarihsel_snapshot((2025, 12), Decimal("6")),
        ],
    )
    with repository.get_session() as session:
        repository.upsert_sector_taxonomy(session, "THYAO", market="BIST", ust_sektor="Sanayi", sirket_turu="sanayi")
        session.commit()

    status = tarama_toplu._scan_one("THYAO", "BIST")

    assert status == "ok"
    with repository.get_session() as session:
        row = session.get(models.MarketScanResult, "THYAO")
        assert row.tarihsel_skorlar is not None
        assert [d["donem"] for d in row.tarihsel_skorlar] == ["2025/12", "2026/3", "2026/6"]
        assert row.tarihsel_skorlar[-1]["bilesik_score"] == "8"  # Decimal -> str, JSON-safe
        assert row.tarihsel_skorlar[0]["donem_label"] == pipeline.quarter_label((2025, 12))


def test_scan_one_tarihsel_skorlar_hata_verirse_ana_tarama_etkilenmez(izole_db, monkeypatch) -> None:
    """Kural 9 (ikincil/ek veri): compute_historical_lens_scores_for_ticker
    PATLARSA bile ana 'ok' tarama sonucu/skorları ETKİLENMEMELİ, sadece
    tarihsel_skorlar boş liste olarak kalmalı."""
    monkeypatch.setattr(pipeline, "compute_multi_lens_score_for_ticker", lambda ticker, market: _fake_sonuc(ticker, market))

    def patlayan(sonuc, max_historical=3):
        raise RuntimeError("beklenmedik tarihsel hesap hatası")

    monkeypatch.setattr(pipeline, "compute_historical_lens_scores_for_ticker", patlayan)
    with repository.get_session() as session:
        repository.upsert_sector_taxonomy(session, "THYAO", market="BIST", ust_sektor="Sanayi", sirket_turu="sanayi")
        session.commit()

    status = tarama_toplu._scan_one("THYAO", "BIST")

    assert status == "ok"
    with repository.get_session() as session:
        row = session.get(models.MarketScanResult, "THYAO")
        assert row.scan_status == "ok"
        assert row.bilesik_score is not None  # ana skor ETKİLENMEDİ
        assert row.tarihsel_skorlar == []


def test_scan_one_ticker_not_found_veri_yok_yazar(izole_db, monkeypatch) -> None:
    def patlayan(ticker, market):
        raise pipeline.TickerNotFoundError(f"{ticker} bulunamadı")

    monkeypatch.setattr(pipeline, "compute_multi_lens_score_for_ticker", patlayan)

    status = tarama_toplu._scan_one("YOKYOK", "BIST")

    assert status == "veri_yok"
    with repository.get_session() as session:
        row = session.get(models.MarketScanResult, "YOKYOK")
        assert row.scan_status == "veri_yok"


def test_scan_one_unsupported_company_type_desteklenmiyor_yazar(izole_db, monkeypatch) -> None:
    def patlayan(ticker, market):
        raise pipeline.UnsupportedCompanyTypeError(f"{ticker} desteklenmiyor")

    monkeypatch.setattr(pipeline, "compute_multi_lens_score_for_ticker", patlayan)

    status = tarama_toplu._scan_one("ARAKUR", "BIST")

    assert status == "desteklenmiyor"
    with repository.get_session() as session:
        row = session.get(models.MarketScanResult, "ARAKUR")
        assert row.scan_status == "desteklenmiyor"
        assert "desteklenmiyor" in row.error_detail


def test_scan_one_beklenmeyen_hata_script_cokmez_hata_yazar(izole_db, monkeypatch) -> None:
    def patlayan(ticker, market):
        raise RuntimeError("ağ zaman aşımı")

    monkeypatch.setattr(pipeline, "compute_multi_lens_score_for_ticker", patlayan)

    status = tarama_toplu._scan_one("AGSORUNU", "BIST")

    assert status == "hata"
    with repository.get_session() as session:
        row = session.get(models.MarketScanResult, "AGSORUNU")
        assert row.scan_status == "hata"
        assert "ağ zaman aşımı" in row.error_detail


def test_scan_one_hata_sonrasi_eski_basarili_skor_korunur(izole_db, monkeypatch) -> None:
    monkeypatch.setattr(pipeline, "compute_multi_lens_score_for_ticker", lambda ticker, market: _fake_sonuc(ticker, market))
    with repository.get_session() as session:
        repository.upsert_sector_taxonomy(session, "THYAO", market="BIST", ust_sektor="Sanayi", sirket_turu="sanayi")
        session.commit()
    tarama_toplu._scan_one("THYAO", "BIST")
    with repository.get_session() as session:
        eski_bilesik = session.get(models.MarketScanResult, "THYAO").bilesik_score

    def patlayan(ticker, market):
        raise RuntimeError("gecici ag hatasi")

    monkeypatch.setattr(pipeline, "compute_multi_lens_score_for_ticker", patlayan)
    status = tarama_toplu._scan_one("THYAO", "BIST")

    assert status == "hata"
    with repository.get_session() as session:
        row = session.get(models.MarketScanResult, "THYAO")
        assert row.bilesik_score == eski_bilesik


# --- _run_batch: dry-run hesaplama YAPMAZ -----------------------------------------------------


def test_run_batch_dry_run_pipeline_hic_cagirmaz(izole_db, monkeypatch) -> None:
    def patlayan(*args, **kwargs):
        raise AssertionError("dry-run sirasinda pipeline COGRILMAMALIYDI")

    monkeypatch.setattr(pipeline, "compute_multi_lens_score_for_ticker", patlayan)

    counts = tarama_toplu._run_batch(["THYAO", "ASELS"], "BIST", dry_run=True)

    assert counts == {"ok": 0, "hata": 0, "desteklenmiyor": 0, "veri_yok": 0}


# --- _resolve_targets -----------------------------------------------------


def test_resolve_targets_bist30() -> None:
    assert tarama_toplu._resolve_targets(None, "bist30") == [("BIST", tarama_toplu.BIST30_PILOT)]


def test_resolve_targets_nasdaq30() -> None:
    assert tarama_toplu._resolve_targets(None, "nasdaq30") == [("NASDAQ", tarama_toplu.NASDAQ30_PILOT)]


def test_resolve_targets_pilot_varsayilan_iki_piyasa() -> None:
    hedefler = tarama_toplu._resolve_targets(None, "pilot")
    assert hedefler == [("BIST", tarama_toplu.BIST30_PILOT), ("NASDAQ", tarama_toplu.NASDAQ30_PILOT)]


def test_resolve_targets_pilot_market_ile_daraltilir() -> None:
    assert tarama_toplu._resolve_targets("bist", "pilot") == [("BIST", tarama_toplu.BIST30_PILOT)]


def test_resolve_targets_tam_db_kuyrugu_isaretlenir_none_liste() -> None:
    hedefler = tarama_toplu._resolve_targets("bist", "tam")
    assert hedefler == [("BIST", None)]


def test_resolve_targets_bist30_pilot_listeleri_cakismaz_ve_beklenen_uzunluktadir() -> None:
    assert len(tarama_toplu.BIST30_PILOT) == 32
    assert len(set(tarama_toplu.BIST30_PILOT)) == 32
    assert len(tarama_toplu.NASDAQ30_PILOT) == 30
    assert len(set(tarama_toplu.NASDAQ30_PILOT)) == 30
