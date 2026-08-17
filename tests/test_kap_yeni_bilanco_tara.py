"""`scripts/kap_yeni_bilanco_tara.py::_detect_bist_tickers_with_fresh_fr`
testleri -- gercek KAP ag istegi ATILMAZ (`kap.fetch_all_disclosures`
monkeypatch ile sahtelenir), gercek DB'ye DOKUNULMAZ (`tests/
test_tarama_toplu.py::izole_db` ile AYNI in-memory SQLite deseni)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

import config
from src.db import models, repository
from src.db.models import Company
from src.fetchers import kap

import scripts.kap_yeni_bilanco_tara as kap_yeni_bilanco_tara


@pytest.fixture()
def izole_db(monkeypatch, tmp_path):
    engine, session_factory = models.create_engine_and_session(f"sqlite:///{tmp_path / 'test_kap_yeni_bilanco.db'}")
    models.init_db(engine)
    monkeypatch.setattr(repository, "DefaultSessionLocal", session_factory)
    monkeypatch.setattr(repository, "_default_db_initialized", True)
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")
    return engine


def _disclosure(category: str, stock_codes: str, title: str = "baslik") -> kap.Disclosure:
    return kap.Disclosure(
        date=datetime(2026, 8, 17, 19, 0, tzinfo=timezone.utc),
        title=title,
        category=category,
        summary=title,
        url="https://www.kap.org.tr/tr/Bildirim/1",
        importance="IMPORTANCE_LOW",
        is_late=False,
        disclosure_index=1,
        stock_codes=stock_codes,
    )


def test_finansal_rapor_kategorisindeki_bilinen_ticker_tespit_edilir(izole_db, monkeypatch):
    with repository.get_session() as session:
        session.add(Company(ticker="THYAO", market="BIST"))
        session.commit()

    monkeypatch.setattr(
        kap, "fetch_all_disclosures",
        lambda days: [_disclosure("Finansal Rapor", "THYAO")],
    )

    hits = kap_yeni_bilanco_tara._detect_bist_tickers_with_fresh_fr(days=1)

    assert list(hits) == ["THYAO"]


def test_finansal_rapor_disindaki_kategori_yoksayilir(izole_db, monkeypatch):
    with repository.get_session() as session:
        session.add(Company(ticker="THYAO", market="BIST"))
        session.commit()

    monkeypatch.setattr(
        kap, "fetch_all_disclosures",
        lambda days: [_disclosure("Faaliyet Raporu", "THYAO"), _disclosure("Sorumluluk Beyanı", "THYAO")],
    )

    hits = kap_yeni_bilanco_tara._detect_bist_tickers_with_fresh_fr(days=1)

    assert hits == {}


def test_db_de_tanimadigimiz_ticker_sessizce_elenir(izole_db, monkeypatch):
    with repository.get_session() as session:
        session.add(Company(ticker="THYAO", market="BIST"))
        session.commit()

    monkeypatch.setattr(
        kap, "fetch_all_disclosures",
        lambda days: [_disclosure("Finansal Rapor", "BILINMEYEN")],
    )

    hits = kap_yeni_bilanco_tara._detect_bist_tickers_with_fresh_fr(days=1)

    assert hits == {}


def test_coklu_stock_codes_ayristirilir(izole_db, monkeypatch):
    with repository.get_session() as session:
        session.add(Company(ticker="THYAO", market="BIST"))
        session.add(Company(ticker="ASELS", market="BIST"))
        session.commit()

    monkeypatch.setattr(
        kap, "fetch_all_disclosures",
        lambda days: [_disclosure("Finansal Rapor", "THYAO, ASELS")],
    )

    hits = kap_yeni_bilanco_tara._detect_bist_tickers_with_fresh_fr(days=1)

    assert sorted(hits) == ["ASELS", "THYAO"]
