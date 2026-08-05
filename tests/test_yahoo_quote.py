"""src/fetchers/yahoo_quote.py testleri.

Kural 11: ağ isteği ATILMAZ -- `yahoo_quote._request_chart` monkeypatch
ile sahte JSON yanıtı döner. Bu modül Faz 19'da CANLI bir kullanıcı
hatasından (OZATD %2,55 gösterirken gerçek kapanış %8,41 idi -- kök neden
isyatirim'in bir gün gecikmeli olması) doğdu, bkz. modül üst notu.
"""

from __future__ import annotations

from decimal import Decimal

from src.fetchers import yahoo_quote


def _fake_chart_payload(closes: list) -> dict:
    return {"chart": {"result": [{"indicators": {"quote": [{"close": closes}]}}]}}


def test_fetch_daily_return_gercek_ozatd_orneği(monkeypatch):
    """CANLI doğrulama (2026-08-05): OZATD.IS için Yahoo 4130,0 (04/08) ->
    4477,5 (05/08) döndü, kullanıcının bildirdiği %8,41 ile eşleşti."""
    monkeypatch.setattr(yahoo_quote, "_request_chart", lambda symbol: _fake_chart_payload([4027.5, 4130.0, 4477.5]))

    result = yahoo_quote.fetch_daily_return("OZATD", suffix=".IS")

    assert result is not None
    assert abs(result - Decimal("8.41")) < Decimal("0.01")


def test_fetch_daily_return_none_kapanislari_atlar(monkeypatch):
    """Yahoo tatil/eksik günler için 'close' alanında None döndürebilir --
    bunlar geçerli kapanış SAYILMAZ, son İKİ GEÇERLİ değer kullanılır."""
    monkeypatch.setattr(yahoo_quote, "_request_chart", lambda symbol: _fake_chart_payload([100.0, None, 110.0]))

    result = yahoo_quote.fetch_daily_return("TEST", suffix=".IS")

    assert result == Decimal("10")


def test_fetch_daily_return_yetersiz_veri_none_doner(monkeypatch):
    monkeypatch.setattr(yahoo_quote, "_request_chart", lambda symbol: _fake_chart_payload([110.0]))

    assert yahoo_quote.fetch_daily_return("TEST", suffix=".IS") is None


def test_fetch_daily_return_bos_yanit_none_doner(monkeypatch):
    monkeypatch.setattr(yahoo_quote, "_request_chart", lambda symbol: {"chart": {"result": [{}]}})

    assert yahoo_quote.fetch_daily_return("TEST", suffix=".IS") is None


def test_fetch_daily_return_ag_hatasi_none_doner(monkeypatch):
    def _raise(symbol):
        raise yahoo_quote.YahooQuoteNetworkError("boom")

    monkeypatch.setattr(yahoo_quote, "_request_chart", _raise)

    assert yahoo_quote.fetch_daily_return("TEST", suffix=".IS") is None


def test_fetch_daily_return_sembol_suffix_ekler(monkeypatch):
    captured = {}

    def _fake(symbol):
        captured["symbol"] = symbol
        return _fake_chart_payload([100.0, 105.0])

    monkeypatch.setattr(yahoo_quote, "_request_chart", _fake)

    yahoo_quote.fetch_daily_return("ozatd", suffix=".IS")

    assert captured["symbol"] == "OZATD.IS"
