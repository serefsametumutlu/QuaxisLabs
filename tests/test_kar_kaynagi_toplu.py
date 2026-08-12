"""scripts/kar_kaynagi_toplu.py testleri -- `--universe full` (kullanıcı
onaylı TAM BİST evrenine açılma, 2026-08-12) modunun DB kuyruğu doğru
filtrelediğini doğrular.

`test_tarama_toplu.py`'nin `izole_db` deseniyle AYNI ilke -- gerçek ağ
isteği ATILMAZ, `argparse.Namespace` doğrudan üretilir."""

from __future__ import annotations

import argparse

import pytest

from src.db import models, repository

import scripts.kar_kaynagi_toplu as kar_kaynagi_toplu
import scripts.tarama_toplu as tarama_toplu


@pytest.fixture()
def izole_db(monkeypatch, tmp_path):
    engine, session_factory = models.create_engine_and_session(f"sqlite:///{tmp_path / 'test_kar_kaynagi_toplu.db'}")
    models.init_db(engine)
    monkeypatch.setattr(repository, "DefaultSessionLocal", session_factory)
    monkeypatch.setattr(repository, "_default_db_initialized", True)
    return engine


def _make_ok_row(session, ticker: str, market: str = "BIST") -> None:
    repository.upsert_sector_taxonomy(session, ticker, market=market, ust_sektor="Sanayi", sirket_turu="sanayi")
    repository.upsert_market_scan_result(session, ticker, market, scan_status="ok")


# --- _resolve_tickers: --universe full -----------------------------------------------------


def test_resolve_tickers_full_sadece_ok_bist_doner(izole_db) -> None:
    with repository.get_session() as session:
        _make_ok_row(session, "THYAO")
        _make_ok_row(session, "ASELS")
        repository.upsert_sector_taxonomy(session, "SAHOL", market="BIST", ust_sektor="Sanayi", sirket_turu="sanayi")
        repository.upsert_market_scan_result(session, "SAHOL", "BIST", scan_status="hata")
        session.commit()

    args = argparse.Namespace(tickers=None, universe="full")

    assert kar_kaynagi_toplu._resolve_tickers(args) == ["ASELS", "THYAO"]  # alfabetik


def test_resolve_tickers_full_nasdaq_ok_satirlarini_disarida_birakir(izole_db) -> None:
    with repository.get_session() as session:
        _make_ok_row(session, "THYAO", market="BIST")
        repository.upsert_sector_taxonomy(session, "AAPL", market="NASDAQ", ust_sektor="Teknoloji", sirket_turu="sanayi")
        repository.upsert_market_scan_result(session, "AAPL", "NASDAQ", scan_status="ok")
        session.commit()

    args = argparse.Namespace(tickers=None, universe="full")

    assert kar_kaynagi_toplu._resolve_tickers(args) == ["THYAO"]


def test_resolve_tickers_full_bos_ise_bos_liste(izole_db) -> None:
    args = argparse.Namespace(tickers=None, universe="full")
    assert kar_kaynagi_toplu._resolve_tickers(args) == []


def test_resolve_tickers_pilot_davranisi_degismedi(izole_db) -> None:
    """Geriye dönük uyumluluk: `--universe full` eklenmesi `pilot`
    davranışını KIRMAMALI."""
    args = argparse.Namespace(tickers=None, universe="pilot")
    assert kar_kaynagi_toplu._resolve_tickers(args) == list(tarama_toplu.BIST30_PILOT)


def test_resolve_tickers_tickers_verilmisse_uppercase_donulur(izole_db) -> None:
    args = argparse.Namespace(tickers=["thyao", " sahol "], universe=None)
    assert kar_kaynagi_toplu._resolve_tickers(args) == ["THYAO", "SAHOL"]


def test_resolve_tickers_ikisi_de_yoksa_hata(izole_db) -> None:
    args = argparse.Namespace(tickers=None, universe=None)
    with pytest.raises(ValueError):
        kar_kaynagi_toplu._resolve_tickers(args)


# --- --limit bu modda da UYGULANIR (main() içindeki dilimleme mantığı,
# _resolve_tickers SONRASI çalışır -- burada dolaylı olarak doğrulanır) ----


def test_resolve_tickers_full_limit_uygulanmadan_once_tam_listeyi_doner(izole_db) -> None:
    """`--limit` `main()`'de `_resolve_tickers()`'ın DÖNDÜRDÜĞÜ listeye
    uygulanır (bkz. `main()`: `tickers = tickers[: args.limit]`) --
    `_resolve_tickers` kendisi limit UYGULAMAZ, bu test o sözleşmeyi
    doğrular (limit mantığının KENDİSİ `tarama_toplu.py` ile AYNI kalıp)."""
    with repository.get_session() as session:
        for ticker in ("AKBNK", "MGROS", "ZORLU"):
            _make_ok_row(session, ticker)
        session.commit()

    args = argparse.Namespace(tickers=None, universe="full")
    tickers = kar_kaynagi_toplu._resolve_tickers(args)
    assert len(tickers) == 3

    limited = tickers[:2]
    assert limited == ["AKBNK", "MGROS"]
