"""src/fetchers/kap_fund_portfolio.py testleri.

Kural 11: hicbir ag istegi ATILMAZ -- kap._post_json ve kap.fetch_disclosures_by_oid
monkeypatch ile sahte yanitlar donecek sekilde degistirilir. Sahte payload'lar
scripts/explore_kap_fon.py ile CANLI dogrulanan gercek AFA/AK PORTFOY
YONETIMI senaryosundan alinmistir (bkz. o scriptin modul ust notu):
ne fonun kendi KAP kaydinda ne kurucusunun kaydinda 'Portföy Dağılım
Raporu' bulunamadi -- bu, bu modulun ANA/beklenen davranisidir.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from src.fetchers import kap
from src.fetchers import kap_fund_portfolio as kfp


_AFA_SEARCH_RESULT = {
    "searchValue": "AK PORTFÖY AMERİKA YABANCI HİSSE SENEDİ FONU",
    "searchType": "F",
    "memberOrFundOid": "33E5FED7E40B00EAE0530A4A622B2AEA",
    "cmpOrFundCode": "afa",
}

_AK_PORTFOY_FOUNDER_RESULT = {
    "searchValue": "AK PORTFÖY YÖNETİMİ A.Ş.",
    "searchType": "C",
    "memberOrFundOid": "4028e4a240e8d16e0140e8f3623d0043",
    "cmpOrFundCode": "akp",
}


def _search_payload(*rows):
    return [
        {"category": "combined", "results": []},
        {"category": "subjects", "results": []},
        {"category": "companyOrFunds", "results": list(rows)},
    ]


def test_fetch_latest_portfolio_hicbir_yerde_bulunamazsa_none_doner(monkeypatch):
    """CANLI doğrulanan gerçek senaryo (AFA): fonun oid'i VE kurucusunun
    oid'i altında da bildirim yok -- fonksiyon None dönmeli, hata FIRLATMAMALI."""

    def _fake_post_json(url, body):
        if url == kap.SEARCH_ENDPOINT:
            keyword = body["keyword"]
            if keyword == "afa":
                return _search_payload(_AFA_SEARCH_RESULT)
            return _search_payload(_AK_PORTFOY_FOUNDER_RESULT)
        raise AssertionError(f"beklenmeyen uc nokta: {url}")

    monkeypatch.setattr(kap, "_post_json", _fake_post_json)
    monkeypatch.setattr(kap, "fetch_disclosures_by_oid", lambda member_oid, days=90: [])
    monkeypatch.setattr(kfp.time, "sleep", lambda seconds: None)

    result = kfp.fetch_latest_portfolio("AFA")

    assert result is None


def test_fetch_latest_portfolio_fon_kodu_bulunamazsa_none_doner(monkeypatch):
    monkeypatch.setattr(kap, "_post_json", lambda url, body: _search_payload())

    assert kfp.fetch_latest_portfolio("YOKTUR123") is None


def test_fetch_latest_portfolio_agsal_hatada_cokme_yok_none_doner(monkeypatch):
    def _patlar(url, body):
        raise kap.KapNetworkError("test ağ hatası")

    monkeypatch.setattr(kap, "_post_json", _patlar)

    assert kfp.fetch_latest_portfolio("AFA") is None


def test_fetch_latest_portfolio_eslesen_baslikli_bildirim_bulunursa_yine_none_doner_ama_loglanir(monkeypatch, caplog):
    """Kural 3: eşleşen bir başlık BULUNSA bile (bu oturumda hiç
    canlı örnek görülmediği için) içerik ayrıştırılmaz, None döner --
    ama aramanın gerçekten çalıştığı bir uyarı logunda görünür olmalı."""
    matching_disclosure = kap.Disclosure(
        date=datetime(2026, 7, 5, 18, 0, 0),
        title="Temmuz 2026 Portföy Dağılım Raporu",
        category="Fon Bülteni",
        summary="Temmuz 2026 Portföy Dağılım Raporu",
        url="https://www.kap.org.tr/tr/Bildirim/1234567",
        importance=kap.IMPORTANCE_LOW,
        is_late=False,
        disclosure_index=1234567,
        stock_codes="afa",
    )

    def _fake_post_json(url, body):
        return _search_payload(_AFA_SEARCH_RESULT)

    monkeypatch.setattr(kap, "_post_json", _fake_post_json)
    monkeypatch.setattr(kap, "fetch_disclosures_by_oid", lambda member_oid, days=90: [matching_disclosure])
    monkeypatch.setattr(kfp.time, "sleep", lambda seconds: None)

    with caplog.at_level("WARNING"):
        result = kfp.fetch_latest_portfolio("AFA")

    assert result is None
    assert any("BULUNDU" in record.message for record in caplog.records)
