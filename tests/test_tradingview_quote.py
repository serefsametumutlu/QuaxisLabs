"""src/fetchers/tradingview_quote.py testleri.

Kural 11: ağ isteği ATILMAZ -- `tradingview_quote._request_scan`
monkeypatch ile sahte JSON yanıtı döner. Bu modül Faz 19.1'de (2026-08-06,
ikinci tur) CANLI kıyaslamayla (fvt.com.tr'nin "KAP Dağılımına Göre"
rakamları) `yahoo_quote`'un az işlem gören hisselerde bayat kaldığının
görülmesinden doğdu, bkz. modül üst notu.
"""

from __future__ import annotations

from decimal import Decimal

from src.fetchers import tradingview_quote


def _fake_scan_payload(rows: dict[str, float | None]) -> dict:
    return {
        "totalCount": len(rows),
        "data": [{"s": f"BIST:{ticker}", "d": [change]} for ticker, change in rows.items()],
    }


def test_fetch_daily_returns_gercek_dstkf_hedef_orneği(monkeypatch):
    """CANLI doğrulama (2026-08-06): TradingView DSTKF için +%7,74, HEDEF
    için -%9,94 döndü -- fvt.com.tr'nin kendi ekran görüntüsündeki
    rakamlarla (sırasıyla +%7,37 ve -%9,94) Yahoo'dan çok daha yakın/
    birebir eşleşti."""
    monkeypatch.setattr(
        tradingview_quote, "_request_scan", lambda tickers: _fake_scan_payload({"DSTKF": 7.7396, "HEDEF": -9.9393})
    )

    result = tradingview_quote.fetch_daily_returns(["DSTKF", "HEDEF"])

    assert result["DSTKF"] == Decimal("7.7396")
    assert result["HEDEF"] == Decimal("-9.9393")


def test_fetch_daily_returns_bulunamayan_ticker_sozlukte_yok(monkeypatch):
    """TradingView'de bulunamayan (fon-içinde-fon TEFAS kodu gibi borsa
    dışı) ticker'lar yanıtta hiç dönmez -- hata FIRLATILMAZ, sözlükte
    sadece bulunanlar olur."""
    monkeypatch.setattr(tradingview_quote, "_request_scan", lambda tickers: _fake_scan_payload({"OZATD": 1.5}))

    result = tradingview_quote.fetch_daily_returns(["OZATD", "OLMAYAN"])

    assert result == {"OZATD": Decimal("1.5")}


def test_fetch_daily_returns_bos_liste_bos_sozluk_doner():
    assert tradingview_quote.fetch_daily_returns([]) == {}


def test_fetch_daily_returns_ag_hatasi_bos_sozluk_doner(monkeypatch):
    def _raise(tickers):
        raise tradingview_quote.TradingViewQuoteError("boom")

    monkeypatch.setattr(tradingview_quote, "_request_scan", _raise)

    assert tradingview_quote.fetch_daily_returns(["OZATD"]) == {}


def test_fetch_daily_returns_change_none_ise_atlanir(monkeypatch):
    """Bazı satırlarda 'change' alanı None gelebilir (örn. o gün hiç
    işlem görmemiş bir sembol) -- bu ticker sözlükte YOK olur, 0
    VARSAYILMAZ (Kural 3: fiyatlandırılamadı sayılmalı, sessizce 0 getiri
    UYDURULMAMALI)."""
    monkeypatch.setattr(tradingview_quote, "_request_scan", lambda tickers: _fake_scan_payload({"OZATD": None}))

    assert tradingview_quote.fetch_daily_returns(["OZATD"]) == {}


def test_fetch_daily_returns_ticker_kucuk_harfle_verilse_bile_buyuk_harfe_cevirir(monkeypatch):
    captured = {}

    def _fake(tickers):
        captured["tickers"] = tickers
        return _fake_scan_payload({"OZATD": 1.0})

    monkeypatch.setattr(tradingview_quote, "_request_scan", _fake)

    tradingview_quote.fetch_daily_returns(["ozatd"])

    assert captured["tickers"] == ["OZATD"]
