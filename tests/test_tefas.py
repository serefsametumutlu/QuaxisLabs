"""src/fetchers/tefas.py testleri.

Kural 11: hicbir ag istegi ATILMAZ -- HTTP katmanindaki `_post_json`
fonksiyonu monkeypatch ile sahte JSON payload'lari dondurecek sekilde
degistirilir; sadece ayristirma/donusum mantigi test edilir. Sahte
payload'lar scripts/explore_tefas.py ile CANLI dogrulanan gercek AFA
yanit semasindan alinmistir (bkz. data/exploration/tefas_findings_notes.md).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.fetchers import tefas


_AFA_BILGI_PAYLOAD = {
    "errorCode": None,
    "errorMessage": None,
    "resultList": [
        {
            "fonKodu": "AFA",
            "fonUnvan": "AK PORTFÖY AMERİKA YABANCI HİSSE SENEDİ FONU",
            "sonFiyat": 1.259391,
            "gunlukGetiri": 1.2529,
            "payAdet": 4228739149,
            "portBuyukluk": 5325636562.29,
            "fonKategori": "Hisse Senedi Fonu",
            "kategoriDerece": 27,
            "kategoriFonSay": 195,
            "yatirimciSayi": 45243,
            "pazarPayi": 2.37,
        }
    ],
}

_UNIVERSE_PAYLOAD = {
    "errorCode": None,
    "errorMessage": None,
    "data": [
        {
            "fonKod": "AFA",
            "unvan": "AK PORTFÖY AMERİKA YABANCI HİSSE SENEDİ FONU",
            "kurucuKod": "AKP",
            "kurucuAd": "AK PORTFÖY YÖNETİMİ A.Ş.",
            "oprKod": "AKY",
            "oprAd": "AK YATIRIM MENKUL DEĞERLER A.Ş.",
            "durum": "AKTİF",
            "tarih": "04/11/2019 21:33:47",
        },
        {
            "fonKod": "AAL",
            "unvan": "ATA PORTFÖY PARA PİYASASI (TL) FONU",
            "kurucuKod": "APY",
            "kurucuAd": "ATA PORTFÖY YÖNETİMİ A.Ş.",
            "oprKod": "ATA",
            "oprAd": "ATA YATIRIM MENKUL KIYMETLER A.Ş.",
            "durum": "AKTİF",
            "tarih": "08/06/2020 21:33:04",
        },
    ],
}


def _install_fakes(monkeypatch, bilgi_payload=_AFA_BILGI_PAYLOAD, universe_payload=_UNIVERSE_PAYLOAD):
    def _fake_post_json(url, body):
        if url.endswith("/fonBilgiGetir"):
            return bilgi_payload
        if url.endswith("/getFplFonList"):
            return universe_payload
        raise AssertionError(f"beklenmeyen uc nokta: {url}")

    monkeypatch.setattr(tefas, "_post_json", _fake_post_json)


# --- search_fund --------------------------------------------


def test_search_fund_kod_ile_eslesir(monkeypatch):
    _install_fakes(monkeypatch)

    matches = tefas.search_fund("AFA")

    assert len(matches) == 1
    assert matches[0].code == "AFA"
    assert matches[0].founder == "AK PORTFÖY YÖNETİMİ A.Ş."
    assert matches[0].status == "AKTİF"


def test_search_fund_ad_ile_eslesir_buyuk_kucuk_harf_duyarsiz(monkeypatch):
    _install_fakes(monkeypatch)

    matches = tefas.search_fund("amerika")

    assert len(matches) == 1
    assert matches[0].code == "AFA"


def test_search_fund_bos_sorguda_bos_liste_doner(monkeypatch):
    _install_fakes(monkeypatch)

    assert tefas.search_fund("   ") == []


def test_search_fund_eslesme_yoksa_bos_liste_doner(monkeypatch):
    _install_fakes(monkeypatch)

    assert tefas.search_fund("YOKTUR123") == []


# --- fetch_fund_info --------------------------------------------


def test_fetch_fund_info_alanlari_dogru_esler(monkeypatch):
    _install_fakes(monkeypatch)

    info = tefas.fetch_fund_info("AFA")

    assert info.code == "AFA"
    assert info.name == "AK PORTFÖY AMERİKA YABANCI HİSSE SENEDİ FONU"
    assert info.founder == "AK PORTFÖY YÖNETİMİ A.Ş."
    assert info.type == "Hisse Senedi Fonu"
    assert info.price == Decimal("1.259391")
    assert info.total_value == Decimal("5325636562.29")
    assert info.investor_count == 45243
    # Bilinçli sınırlar (bkz. modül üst notu, Kural 3):
    assert info.price_date is None
    assert info.allocation == {}


def test_fetch_fund_info_kucuk_harfli_kod_normalize_edilir(monkeypatch):
    captured = {}

    def _fake_post_json(url, body):
        if url.endswith("/fonBilgiGetir"):
            captured["fonKodu"] = body["fonKodu"]
            return _AFA_BILGI_PAYLOAD
        return _UNIVERSE_PAYLOAD

    monkeypatch.setattr(tefas, "_post_json", _fake_post_json)

    tefas.fetch_fund_info("afa")

    assert captured["fonKodu"] == "AFA"


def test_fetch_fund_info_bos_resultlist_hata_firlatir(monkeypatch):
    monkeypatch.setattr(
        tefas,
        "_post_json",
        lambda url, body: {"errorCode": None, "errorMessage": None, "resultList": []},
    )

    with pytest.raises(tefas.TefasFundNotFoundError):
        tefas.fetch_fund_info("YOKTUR")


def test_fetch_fund_info_universe_hatasinda_founder_none_kalir_cokme_yok(monkeypatch):
    """Kurucu adi ikincil bir alandir -- evren istegi patlarsa ana bilgi
    YINE dönmeli (Kural 9: yardımcı veri ana akışı bloklamaz)."""

    def _fake_post_json(url, body):
        if url.endswith("/fonBilgiGetir"):
            return _AFA_BILGI_PAYLOAD
        raise tefas.TefasNetworkError("test ag hatasi")

    monkeypatch.setattr(tefas, "_post_json", _fake_post_json)

    info = tefas.fetch_fund_info("AFA")

    assert info.code == "AFA"
    assert info.founder is None


# --- fetch_fund_returns / fetch_price_history (bilinçli olarak dogrulanamayan uc noktalar) --------


def test_fetch_fund_returns_tum_alanlar_none_doner():
    """Kural 3: TEFAS getiri API'sinin istek govdesi bu oturumda
    bulunamadigi icin (bkz. modul ust notu) fonksiyon HER ZAMAN None
    alanli bir FundReturns doner, hata FIRLATMAZ."""
    returns = tefas.fetch_fund_returns("AFA")

    assert returns == tefas.FundReturns(
        d1=None, w1=None, m1=None, m3=None, m6=None, y1=None, y3=None, y5=None, ytd=None
    )


def test_fetch_price_history_bos_liste_doner():
    assert tefas.fetch_price_history("AFA", months=3) == []
