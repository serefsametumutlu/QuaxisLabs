"""src/fetchers/yahoo_quote.py testleri.

Kural 11: ağ isteği ATILMAZ -- `yahoo_quote._request_chart` monkeypatch
ile sahte JSON yanıtı döner. Bu modül Faz 19'da CANLI bir kullanıcı
hatasından (OZATD %2,55 gösterirken gerçek kapanış %8,41 idi -- kök neden
isyatirim'in bir gün gecikmeli olması) doğdu, bkz. modül üst notu.

2026-08-06: İKİNCİ bir CANLI hata (TLY fon tahmini Fintables'ın %10 katı
büyük çıkması) bu modülün "None kapanışları FİLTRELE, son iki GEÇERLİ
değeri kullan" davranışının KENDİSİNİN kök neden olduğunu ortaya çıkardı
-- Yahoo'nun TÜM `.IS` sembolleri için bir günü (05/08) None döndürdüğü
gözlemlendi, eski kod bu durumda 2 gün öncesine atlayıp aradaki günün
hareketini "bugünkü" getiriye sızdırıyordu. `test_fetch_daily_return_
none_kapanislari_atlar` bu YANLIŞ davranışı doğruladığı için KALDIRILDI,
yerine yeni davranışı (ardışık son iki POZİSYONDAN biri None ise None
döner, daha eskiye ATLANMAZ) doğrulayan testler eklendi.
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


def test_fetch_daily_return_ardisik_ikiliden_biri_none_ise_atlanmaz_none_doner(monkeypatch):
    """CANLI hata (2026-08-06, TLY fon tahmini): Yahoo TÜM .IS sembolleri
    için bir günü None döndürdüğünde ESKİ kod 2 gün öncesine atlayıp
    aradaki günün GERÇEK ama 'eski haber' hareketini bugünkü getiriye
    sızdırıyordu (OZATD +%7,4 'bugünkü' gösterirken gerçek anlık değişim
    -%0,06 idi). Artık 2 gün öncesine ATLANMAZ, None döner."""
    monkeypatch.setattr(yahoo_quote, "_request_chart", lambda symbol: _fake_chart_payload([100.0, None, 110.0]))

    result = yahoo_quote.fetch_daily_return("TEST", suffix=".IS")

    assert result is None


def test_fetch_daily_return_son_iki_pozisyon_dolu_ise_hesaplanir(monkeypatch):
    """Aradaki eski günlerde None olsa bile, SON İKİ pozisyon doluysa
    (bugün + dün) normal şekilde hesaplanır -- sadece bu ikiliye atlama
    davranışı kaldırıldı."""
    monkeypatch.setattr(yahoo_quote, "_request_chart", lambda symbol: _fake_chart_payload([100.0, None, 90.0, 99.0]))

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
