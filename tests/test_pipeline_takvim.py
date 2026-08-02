"""src/bot/pipeline.py'nin Faz 13 eklentisi: refresh_earnings_calendar() /
get_cached_earnings_calendar() / is_earnings_calendar_fresh() testleri.

Gerçek ağ isteği ATILMAZ -- earnings_calendar.fetch_upcoming_bist/nasdaq,
earnings_calendar.get_bist_top_market_cap_tickers ve kap.search_company
monkeypatch ile sahtelenir. Veritabanı izole bir tmp_path SQLite dosyasına
yönlendirilir (bkz. test_pipeline.py::izole_db ile AYNI desen).
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest

from src.bot import pipeline
from src.db import models, repository
from src.fetchers import earnings_calendar as ec
from src.fetchers import kap


@pytest.fixture()
def izole_db(monkeypatch, tmp_path):
    engine, session_factory = models.create_engine_and_session(f"sqlite:///{tmp_path / 'test_pipeline_takvim.db'}")
    models.init_db(engine)
    monkeypatch.setattr(repository, "DefaultSessionLocal", session_factory)
    monkeypatch.setattr(repository, "_default_db_initialized", True)
    return engine


def _sahte_bist_entry(ticker: str, gun: int) -> ec.EarningsDate:
    return ec.EarningsDate(
        ticker=ticker, company_name=f"{ticker} A.Ş.", market="BIST", period=(2026, 6),
        expected_date=date(2026, 8, gun), confidence=ec.CONFIDENCE_KESIN, source=ec.SOURCE_KAP_TAKVIM,
    )


def _sahte_nasdaq_entry(ticker: str, gun: int) -> ec.EarningsDate:
    return ec.EarningsDate(
        ticker=ticker, company_name=f"{ticker} Inc.", market="NASDAQ", period=(2026, 6),
        expected_date=date(2026, 8, gun), confidence=ec.CONFIDENCE_TAHMINI, source=ec.SOURCE_NASDAQ_API,
    )


def test_refresh_earnings_calendar_nasdaq_dbye_yazar(izole_db, monkeypatch) -> None:
    sahte_entries = [_sahte_nasdaq_entry("AAPL", 3), _sahte_nasdaq_entry("NVDA", 5)]
    monkeypatch.setattr(ec, "fetch_upcoming_nasdaq", lambda days_ahead=45: sahte_entries)

    count = pipeline.refresh_earnings_calendar("NASDAQ", days_ahead=45)

    assert count == 2
    cached = pipeline.get_cached_earnings_calendar("NASDAQ", days_ahead=30, today=date(2026, 8, 1))
    assert {e.ticker for e in cached} == {"AAPL", "NVDA"}


def test_refresh_earnings_calendar_bist_sirket_adlarini_kap_tan_cozer(izole_db, monkeypatch) -> None:
    monkeypatch.setattr(ec, "get_bist_top_market_cap_tickers", lambda limit=100: ["THYAO", "ASELS"])
    monkeypatch.setattr(kap, "search_company", lambda ticker: SimpleNamespace(name=f"{ticker} Gerçek Ad"))

    yakalanan_ticker_pairs = []

    def sahte_fetch_upcoming_bist(ticker_pairs, days_ahead=30, today=None):
        yakalanan_ticker_pairs.extend(ticker_pairs)
        return [_sahte_bist_entry(t, 4) for t, _ in ticker_pairs]

    monkeypatch.setattr(ec, "fetch_upcoming_bist", sahte_fetch_upcoming_bist)

    count = pipeline.refresh_earnings_calendar("BIST", bist_limit=2, days_ahead=45)

    assert count == 2
    assert yakalanan_ticker_pairs == [("THYAO", "THYAO Gerçek Ad"), ("ASELS", "ASELS Gerçek Ad")]


def test_refresh_earnings_calendar_ayni_donem_uzerine_yazar(izole_db, monkeypatch) -> None:
    """upsert_earnings_calendar (ticker, year, period) anahtarina gore
    calisir -- ayni donem icin IKINCI bir refresh, YENI satir DEGIL,
    MEVCUT satiri gunceller (bkz. repository.upsert_earnings_calendar)."""
    monkeypatch.setattr(ec, "fetch_upcoming_nasdaq", lambda days_ahead=45: [_sahte_nasdaq_entry("AAPL", 3)])
    pipeline.refresh_earnings_calendar("NASDAQ", days_ahead=45)

    monkeypatch.setattr(ec, "fetch_upcoming_nasdaq", lambda days_ahead=45: [_sahte_nasdaq_entry("AAPL", 7)])
    pipeline.refresh_earnings_calendar("NASDAQ", days_ahead=45)

    cached = pipeline.get_cached_earnings_calendar("NASDAQ", days_ahead=30, today=date(2026, 8, 1))
    assert len(cached) == 1
    assert cached[0].expected_date == date(2026, 8, 7)


def test_is_earnings_calendar_fresh_bos_iken_false(izole_db) -> None:
    assert pipeline.is_earnings_calendar_fresh("BIST") is False


def test_is_earnings_calendar_fresh_refresh_sonrasi_true(izole_db, monkeypatch) -> None:
    monkeypatch.setattr(ec, "fetch_upcoming_nasdaq", lambda days_ahead=45: [_sahte_nasdaq_entry("AAPL", 3)])
    pipeline.refresh_earnings_calendar("NASDAQ", days_ahead=45)
    assert pipeline.is_earnings_calendar_fresh("NASDAQ") is True
    assert pipeline.is_earnings_calendar_fresh("BIST") is False


def test_get_cached_earnings_calendar_pencere_disini_eler(izole_db, monkeypatch) -> None:
    monkeypatch.setattr(
        ec, "fetch_upcoming_nasdaq", lambda days_ahead=45: [_sahte_nasdaq_entry("AAPL", 3), _sahte_nasdaq_entry("NVDA", 25)]
    )
    pipeline.refresh_earnings_calendar("NASDAQ", days_ahead=45)

    cached = pipeline.get_cached_earnings_calendar("NASDAQ", days_ahead=5, today=date(2026, 8, 1))
    assert {e.ticker for e in cached} == {"AAPL"}
