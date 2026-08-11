"""Faz 3c: `src/db/repository.py`'ye eklenen DÖNEM BAZLI sektör metrik
önbelleği (`SectorMetricCache`) ve `(ust_sektor, sirket_turu)` bazlı
peer sorgusunun (`get_sector_peer_tickers_v2`) testleri.

Her test kendi izole SQLite dosyasını kullanır (tmp_path) -- mevcut
tests/test_db.py fixture deseniyle AYNI ilke.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest

from src.db import models, repository
from src.db.models import utcnow_naive


@pytest.fixture()
def session(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'test.db'}"
    engine, session_factory = models.create_engine_and_session(db_url)
    models.init_db(engine)
    db_session = session_factory()
    yield db_session
    db_session.close()


# --- get_sector_peer_tickers_v2 -----------------------------------------------------


def test_get_sector_peer_tickers_v2_ust_sektor_ve_sirket_turu_bazli_bulur(session) -> None:
    for ticker in ("THYAO", "PGSUS", "TUPRS", "AKBNK"):
        repository.upsert_financials(session, ticker, [(2026, 3, "revenue", "Satislar", Decimal("100"))])
    repository.upsert_sector_taxonomy(session, "THYAO", market="BIST", ust_sektor="Sanayi", sirket_turu="sanayi")
    repository.upsert_sector_taxonomy(session, "PGSUS", market="BIST", ust_sektor="Sanayi", sirket_turu="sanayi")
    repository.upsert_sector_taxonomy(session, "TUPRS", market="BIST", ust_sektor="Enerji", sirket_turu="sanayi")
    repository.upsert_sector_taxonomy(session, "AKBNK", market="BIST", ust_sektor="Finans", sirket_turu="banka")
    session.commit()

    peers = repository.get_sector_peer_tickers_v2(session, "Sanayi", "sanayi", exclude_ticker="THYAO")
    assert peers == ["PGSUS"]


def test_get_sector_peer_tickers_v2_iki_piyasayi_birlikte_gorur(session) -> None:
    repository.upsert_financials(session, "THYAO", [(2026, 3, "revenue", "Satislar", Decimal("100"))], market="BIST")
    repository.upsert_financials(session, "AAPL", [(2026, 3, "revenue", "Satislar", Decimal("100"))], market="NASDAQ")
    repository.upsert_sector_taxonomy(session, "THYAO", market="BIST", ust_sektor="Teknoloji", sirket_turu="sanayi")
    repository.upsert_sector_taxonomy(session, "AAPL", market="NASDAQ", ust_sektor="Teknoloji", sirket_turu="sanayi")
    session.commit()

    peers_hepsi = repository.get_sector_peer_tickers_v2(session, "Teknoloji", "sanayi")
    assert set(peers_hepsi) == {"THYAO", "AAPL"}

    peers_sadece_nasdaq = repository.get_sector_peer_tickers_v2(session, "Teknoloji", "sanayi", market="NASDAQ")
    assert peers_sadece_nasdaq == ["AAPL"]


def test_get_sector_peer_tickers_v2_sektor_bossa_bos_liste(session) -> None:
    peers = repository.get_sector_peer_tickers_v2(session, "Sağlık", "sanayi")
    assert peers == []


# --- get_sector_metric_cache / save_sector_metric_cache -----------------------------------------------------


def test_sector_metric_cache_yoksa_none(session) -> None:
    cached = repository.get_sector_metric_cache(session, "Sanayi", "sanayi", "ebitda_margin_current", (2026, 3))
    assert cached is None


def test_sector_metric_cache_save_sonra_okunabilir(session) -> None:
    repository.save_sector_metric_cache(
        session, "Sanayi", "sanayi", "ebitda_margin_current", (2026, 3), n=8, medyan=Decimal("15.5"), mad=Decimal("3.2")
    )
    cached = repository.get_sector_metric_cache(session, "Sanayi", "sanayi", "ebitda_margin_current", (2026, 3))
    assert cached is not None
    assert cached.n == 8
    assert cached.medyan == Decimal("15.5")
    assert cached.mad == Decimal("3.2")


def test_sector_metric_cache_ayni_anahtar_uzerine_yazar_yeni_satir_acmaz(session) -> None:
    repository.save_sector_metric_cache(session, "Sanayi", "sanayi", "roe_annualized", (2026, 3), n=5, medyan=Decimal("10"), mad=Decimal("2"))
    repository.save_sector_metric_cache(session, "Sanayi", "sanayi", "roe_annualized", (2026, 3), n=6, medyan=Decimal("11"), mad=Decimal("2.5"))
    cached = repository.get_sector_metric_cache(session, "Sanayi", "sanayi", "roe_annualized", (2026, 3))
    assert cached.n == 6
    assert cached.medyan == Decimal("11")

    from sqlalchemy import select
    from src.db.models import SectorMetricCache
    tum_satirlar = session.execute(select(SectorMetricCache)).scalars().all()
    assert len(tum_satirlar) == 1


def test_sector_metric_cache_eski_kayit_max_age_asilinca_none_doner(session) -> None:
    row = repository.save_sector_metric_cache(
        session, "Sanayi", "sanayi", "net_margin_current", (2026, 3), n=5, medyan=Decimal("5"), mad=Decimal("1")
    )
    row.updated_at = utcnow_naive() - timedelta(hours=48)
    session.commit()

    cached = repository.get_sector_metric_cache(session, "Sanayi", "sanayi", "net_margin_current", (2026, 3), max_age_hours=12)
    assert cached is None


def test_sector_metric_cache_farkli_metric_farkli_satir(session) -> None:
    repository.save_sector_metric_cache(session, "Sanayi", "sanayi", "roe_annualized", (2026, 3), n=5, medyan=Decimal("10"), mad=Decimal("2"))
    repository.save_sector_metric_cache(session, "Sanayi", "sanayi", "ebitda_margin_current", (2026, 3), n=5, medyan=Decimal("20"), mad=Decimal("4"))
    roe = repository.get_sector_metric_cache(session, "Sanayi", "sanayi", "roe_annualized", (2026, 3))
    favok = repository.get_sector_metric_cache(session, "Sanayi", "sanayi", "ebitda_margin_current", (2026, 3))
    assert roe.medyan == Decimal("10")
    assert favok.medyan == Decimal("20")
