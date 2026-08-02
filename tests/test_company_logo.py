"""company_logo.py icindeki saf mantik fonksiyonlarinin birim testleri.

Ag erisimi gerektiren fetch_logo_data_uri()/_resolve_logoid()/_download_logo()
BU DOSYADA test EDILMEZ (bkz. modul docstring'i -- TradingView'in
belgelenmemis uc noktalarina bagimlidir, projenin geri kalanindaki
fetcher testleriyle AYNI ilke: canli veri demo scriptleriyle dogrulanir).
Burada SADECE market-farkli onbellek dosya yolu (Faz 10) test edilir.
"""

from __future__ import annotations

from src.fetchers.company_logo import _EXCHANGE_CANDIDATES, _LOGO_DIR, _cache_path


def test_cache_path_bist_market_ticker_ile_ayni_dosya_adini_kullanir() -> None:
    # Faz 9 ONCESI davranisla BIREBIR AYNI kalmali -- mevcut data/logos/*.svg
    # onbellegi (BIST icin) bu degisiklikle GECERSIZ OLMAMALI.
    assert _cache_path("THYAO", "BIST") == _LOGO_DIR / "THYAO.svg"


def test_cache_path_nasdaq_market_onekli_dosya_adi_kullanir() -> None:
    # BIST/NASDAQ arasinda dosya adi CAKISMASINI onlemek icin (bkz.
    # repository.TickerMarketConflictError ile AYNI ilke) market oneki eklenir.
    assert _cache_path("AAPL", "NASDAQ") == _LOGO_DIR / "NASDAQ_AAPL.svg"


def test_cache_path_bist_ve_nasdaq_ayni_ticker_icin_farkli_dosya() -> None:
    bist_path = _cache_path("TUPRS", "BIST")
    nasdaq_path = _cache_path("TUPRS", "NASDAQ")
    assert bist_path != nasdaq_path


def test_exchange_candidates_nasdaq_once_nasdaq_sonra_nyse_dener() -> None:
    # CANLI dogrulandi (bkz. modul ust notu): AAPL/NVDA/INTC "NASDAQ:" ile
    # bulunuyor, JPM SADECE "NYSE:" ile -- bu yuzden NASDAQ ONCE denenir.
    assert _EXCHANGE_CANDIDATES["NASDAQ"] == ["NASDAQ", "NYSE"]


def test_exchange_candidates_bist_tek_onek() -> None:
    assert _EXCHANGE_CANDIDATES["BIST"] == ["BIST"]
