"""src/bot/fund_pipeline.py -- `_price_changes_for_portfolio()` testleri.

Kural 11: ağ isteği ATILMAZ -- `tradingview_quote.fetch_daily_returns`/
`yahoo_quote.fetch_daily_return`/`tefas.fetch_fund_returns` monkeypatch
ile sahtelenir. Bu dosya Faz 19.1'in ikinci turunda (2026-08-06,
TradingView'in birincil kaynak olması) YENİ eklendi -- bu fonksiyonun
DAHA ÖNCE hiç ayrı bir test dosyası YOKTU (bkz. `08_DEGISIKLIK_GUNLUGU.md`).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from src.bot import fund_pipeline
from src.fetchers import kap_fund_portfolio as kfp, tefas, tradingview_quote, yahoo_quote


def _portfolio(holdings: list[kfp.Holding]) -> kfp.FundPortfolio:
    return kfp.FundPortfolio(
        fund_code="TEST", report_date=date(2026, 7, 31), publish_date=date(2026, 7, 31), holdings=holdings, staleness_days=6
    )


def test_price_changes_hisse_ticker_tradingviewden_gelirse_yahoo_hic_cagrilmaz(monkeypatch):
    """Kullanıcı Kararı #8: TradingView TOPLU sorgusu bir ticker'ı
    döndürdüyse, o ticker için Yahoo yedeğine HİÇ düşülmemeli."""
    portfolio = _portfolio([kfp.Holding(instrument_type="hisse", ticker="OZATD", name="Ozata", weight_pct=Decimal("34.27"))])

    monkeypatch.setattr(tradingview_quote, "fetch_daily_returns", lambda tickers: {"OZATD": Decimal("-0.17")})

    def _yahoo_should_not_be_called(ticker, suffix=""):
        raise AssertionError("TradingView zaten bulmuşken Yahoo çağrılmamalı")

    monkeypatch.setattr(yahoo_quote, "fetch_daily_return", _yahoo_should_not_be_called)

    result = fund_pipeline._price_changes_for_portfolio(portfolio)

    assert result == {"OZATD": Decimal("-0.17")}


def test_price_changes_tradingview_bulamazsa_yahoo_yedegine_duser(monkeypatch):
    """TradingView'in bulamadığı bir hisse (nadiren -- kayıtlı olmayan bir
    sembol) SADECE o ticker için Yahoo'ya düşürülmeli."""
    portfolio = _portfolio(
        [
            kfp.Holding(instrument_type="hisse", ticker="OZATD", name="Ozata", weight_pct=Decimal("34.27")),
            kfp.Holding(instrument_type="hisse", ticker="GARIPTX", name="Garip", weight_pct=Decimal("1.00")),
        ]
    )

    monkeypatch.setattr(tradingview_quote, "fetch_daily_returns", lambda tickers: {"OZATD": Decimal("-0.17")})
    monkeypatch.setattr(
        yahoo_quote, "fetch_daily_return", lambda ticker, suffix="": Decimal("2.5") if ticker == "GARIPTX" else None
    )

    result = fund_pipeline._price_changes_for_portfolio(portfolio)

    assert result == {"OZATD": Decimal("-0.17"), "GARIPTX": Decimal("2.5")}


def test_price_changes_fon_icinde_fon_tradingviewe_hic_gonderilmez_tefastan_gelir(monkeypatch):
    """Fon-içinde-fon (instrument_type='fon') ticker'ları BİST hissesi
    OLMADIĞI için TradingView'e hiç gönderilmemeli, TEFAS'tan çekilmeli."""
    portfolio = _portfolio([kfp.Holding(instrument_type="fon", ticker="PCS", name="Alt Fon", weight_pct=Decimal("5.00"))])

    captured_tv_tickers: list[str] = []
    monkeypatch.setattr(
        tradingview_quote,
        "fetch_daily_returns",
        lambda tickers: captured_tv_tickers.extend(tickers) or {},
    )
    fake_returns = tefas.FundReturns(d1=Decimal("0.42"), w1=None, m1=None, m3=None, m6=None, y1=None, ytd=None, y3=None, y5=None)
    monkeypatch.setattr(tefas, "fetch_fund_returns", lambda ticker: fake_returns)

    result = fund_pipeline._price_changes_for_portfolio(portfolio)

    assert captured_tv_tickers == []
    assert result == {"PCS": Decimal("0.42")}


def test_price_changes_bos_portfoy_bos_sozluk_doner():
    assert fund_pipeline._price_changes_for_portfolio(_portfolio([])) == {}
