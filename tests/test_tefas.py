"""src/fetchers/tefas.py testleri.

Kural 11: hicbir ag istegi ATILMAZ -- HTTP katmanindaki `_post_json`
fonksiyonu monkeypatch ile sahte JSON payload'lari dondurecek sekilde
degistirilir; sadece ayristirma/donusum mantigi test edilir. Sahte
payload'lar scripts/explore_tefas.py ile CANLI dogrulanan gercek AFA
yanit semasindan alinmistir (bkz. data/exploration/tefas_findings_notes.md).
"""

from __future__ import annotations

from datetime import date
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


# --- fetch_price_history / fetch_fund_returns --------
# CANLI doğrulandı (2026-08-05, Faz 18 hazırlığı): fonFiyatBilgiGetir'in
# GERÇEK istek gövdesinde eksik olan "dil" alanı bulundu (bkz. tefas.py
# modül üst notu) -- artık ÇALIŞIYOR. fetch_fund_returns() bunun üzerine
# kurulu; hesaplanan d1 (%0,4057) PHE için fonBilgiGetir'in kendi
# "gunlukGetiri" alanıyla (aynı gün CANLI çekildi) BİREBİR eşleşti.

_D = Decimal  # kisa takma ad -- asagidaki test verilerinde okunabilirlik icin


def _price_row(tarih: str, fiyat: float) -> dict:
    return {"fonKodu": "PHE", "tarih": tarih, "fiyat": fiyat}


def test_fetch_price_history_gunluk_seriyi_dogru_ayristirir(monkeypatch):
    payload = {
        "errorCode": None,
        "resultList": [
            _price_row("2026-07-06", 3.751613),
            _price_row("2026-08-05", 3.835123),
        ],
    }
    captured = {}

    def _fake_post_json(url, body):
        captured["url"] = url
        captured["body"] = body
        return payload

    monkeypatch.setattr(tefas, "_post_json", _fake_post_json)

    history = tefas.fetch_price_history("phe", months=1)

    assert captured["url"].endswith("/fonFiyatBilgiGetir")
    assert captured["body"] == {"fonKodu": "PHE", "dil": "TR", "periyod": 1}
    assert history == [
        (date(2026, 7, 6), Decimal("3.751613")),
        (date(2026, 8, 5), Decimal("3.835123")),
    ]


def test_fetch_price_history_ay_sayisi_en_yakin_enuma_yuvarlanir(monkeypatch):
    captured = {}
    monkeypatch.setattr(tefas, "_post_json", lambda url, body: captured.update(body) or {"resultList": []})

    tefas.fetch_price_history("PHE", months=2)

    assert captured["periyod"] == 3  # {1,3,6,12,36,60} enum'unda 2'yi karsilayan en kucuk deger


def test_fetch_price_history_sifir_fiyatli_satiri_atlar(monkeypatch):
    """CANLI gözlemlendi (5 yıllık istekte): fonun ilk işlem gününden
    ÖNCEye ait dolgu satırlarında fiyat 0 geliyor -- Kural 3 gereği
    gerçek bir işlem değil, atlanır."""
    payload = {"resultList": [_price_row("2024-01-01", 0), _price_row("2024-01-02", 1.5)]}
    monkeypatch.setattr(tefas, "_post_json", lambda url, body: payload)

    history = tefas.fetch_price_history("PHE", months=60)

    assert history == [(date(2024, 1, 2), Decimal("1.5"))]


def test_fetch_fund_returns_yetersiz_veride_tum_alanlar_none_doner(monkeypatch):
    monkeypatch.setattr(tefas, "fetch_price_history", lambda code, months: [])

    assert tefas.fetch_fund_returns("PHE") == tefas.FundReturns(
        d1=None, w1=None, m1=None, m3=None, m6=None, y1=None, y3=None, y5=None, ytd=None
    )


def test_fetch_fund_returns_gunluk_getiriyi_dogru_hesaplar(monkeypatch):
    """CANLI çapraz doğrulama: PHE için hesaplanan d1 (%0,4057...),
    fonBilgiGetir'in kendi 'gunlukGetiri' alanıyla (0,4057) aynı gün
    BİREBİR eşleşti (bkz. tefas.py modül üst notu)."""
    history = [
        (date(2026, 8, 4), _D("3.81962677417716324870002400262")),
        (date(2026, 8, 5), _D("3.835123")),
    ]
    monkeypatch.setattr(tefas, "fetch_price_history", lambda code, months: history)

    returns = tefas.fetch_fund_returns("PHE")

    assert round(returns.d1, 4) == _D("0.4057")


def test_fetch_fund_returns_ytd_dogru_hesaplar(monkeypatch):
    history = [
        (date(2025, 12, 31), _D("2.0")),
        (date(2026, 6, 1), _D("2.5")),
        (date(2026, 8, 5), _D("3.0")),
    ]
    monkeypatch.setattr(tefas, "fetch_price_history", lambda code, months: history)

    returns = tefas.fetch_fund_returns("PHE")

    assert returns.ytd == _D("50")  # (3.0/2.0 - 1) * 100


def test_fetch_fund_returns_yetersiz_derinlikte_uzun_donem_none_kalir(monkeypatch):
    """5 yıllık veri derinliği yoksa (CANLI gözlemlendi: TEFAS ~600 günle
    sınırlı) y3/y5 UYDURULMAZ, None kalır (Kural 3)."""
    history = [(date(2026, 7, 1), _D("1.0")), (date(2026, 8, 5), _D("1.1"))]
    monkeypatch.setattr(tefas, "fetch_price_history", lambda code, months: history)

    returns = tefas.fetch_fund_returns("PHE")

    assert returns.y3 is None
    assert returns.y5 is None
    assert returns.m1 is not None
