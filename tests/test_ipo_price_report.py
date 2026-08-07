"""src/fetchers/ipo_price_report.py testleri -- Faz 20.5 (2026-08-07 devamı).

Kural 11: ağ isteği ATILMAZ. Ayrıştırma testleri GERÇEK, canlı çekilmiş bir
Fiyat Tespit Raporu kullanır (tests/fixtures/veyas_fiyat_tespit_raporu_2026_05.txt
-- Türker Vangölü Enerji Yatırım A.Ş./VEYAS) -- sonuçlar kullanıcının
paylaştığı REFERANS görseldeki gerçek VEYAS rakamlarıyla rakam rakam
doğrulanmıştır (bkz. scripts/explore_ipo_price_report.py, Kural 3).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from src.fetchers import kap
from src.fetchers import kap_ipo
from src.fetchers import ipo_price_report as ipr

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
VEYAS_PRICE_REPORT_TEXT = (FIXTURES_DIR / "veyas_fiyat_tespit_raporu_2026_05.txt").read_text(encoding="utf-8")


def _disclosure() -> kap_ipo.IzahnameDisclosure:
    return kap_ipo.IzahnameDisclosure(
        disclosure_indices=(1,),
        publish_date=date(2026, 5, 21),
        underwriter_name="HALK YATIRIM MENKUL DEĞERLER A.Ş.",
        target_tickers=("VEYAS",),
        summary="VEYAS Halka Arzına İlişkin Onaylı İzahname",
    )


# --- extract_price_report_financials -- GERÇEK VEYAS verisiyle, referans görselle rakam rakam ---


def test_extract_price_report_financials_veyas_birebir_dogru() -> None:
    """CANLI doğrulama: bu değerler kullanıcının paylaştığı VEYAS referans
    görselindeki "Operasyonel ve Finansal Veriler" bölümüyle birebir
    eşleşiyor (bkz. scripts/explore_ipo_price_report.py çıktısı)."""
    result = ipr.extract_price_report_financials(VEYAS_PRICE_REPORT_TEXT)

    assert result.period_label == "31.03.2026"
    assert result.full_year_label == "2025"
    assert result.revenue_full_year == Decimal("26652218")  # 2025 Hasılat: 26.652.218.000 TL
    assert result.revenue_latest_interim == Decimal("5775822")  # 2026/3A Ciro: 5.775.822.000 TL
    assert result.revenue_prior_year_interim == Decimal("5084478")
    assert result.gross_profit_latest_interim == Decimal("2469357")  # 2026/3A Brüt Kâr: 2.469.357.000 TL
    assert result.gross_profit_prior_year_interim == Decimal("1156369")
    assert result.total_assets == Decimal("30121124")  # Toplam varlıklar (31.03.2026): 30.121.124.000 TL
    assert result.total_equity == Decimal("15590464")  # Özkaynaklar (31.03.2026): 15.590.464.000 TL


def test_extract_price_report_financials_yoy_buyume_referans_gorselle_eslesir() -> None:
    """Referans görsel: Ciro artışı %13,6, Brüt kâr artışı %113,5."""
    result = ipr.extract_price_report_financials(VEYAS_PRICE_REPORT_TEXT)

    revenue_growth = (result.revenue_latest_interim - result.revenue_prior_year_interim) / result.revenue_prior_year_interim * 100
    gross_profit_growth = (
        (result.gross_profit_latest_interim - result.gross_profit_prior_year_interim) / result.gross_profit_prior_year_interim * 100
    )

    assert round(revenue_growth, 1) == Decimal("13.6")
    assert round(gross_profit_growth, 1) == Decimal("113.5")


def test_extract_price_report_financials_anchor_bulunamazsa_tum_alanlar_none() -> None:
    """Kural 3: beklenen etiket/kolon sayısı TAM eşleşmezse uydurma
    YAPILMAZ, tüm alanlar None kalır."""
    result = ipr.extract_price_report_financials("bu metinde ilgili hiçbir tablo yok, tamamen alakasız bir metin.")

    assert result.period_label is None
    assert result.total_assets is None
    assert result.total_equity is None
    assert result.revenue_latest_interim is None
    assert result.gross_profit_latest_interim is None


def test_extract_price_report_financials_kolon_sayisi_eksikse_none_doner() -> None:
    """Beklenen 4 kolon yerine 3 kolon varsa (format sapması) alan None
    kalmalı -- eksik/yanlış sayı asla UYDURULMAZ."""
    eksik_metin = "Varlıklar 31.12.2023 31.12.2024 31.03.2026\nToplam varlıklar 100 200 300\n"
    result = ipr.extract_price_report_financials(eksik_metin)

    assert result.total_assets is None


# --- find_price_report_disclosure_index -- ağ isteği monkeypatch'lenir --------------------------


def test_find_price_report_disclosure_index_bulur(monkeypatch) -> None:
    monkeypatch.setattr(kap, "search_company_by_name", lambda name: [kap.CompanyMatch(member_oid="123", name="HALK YATIRIM MENKUL DEĞERLER A.Ş.", ticker_codes=())])
    monkeypatch.setattr(
        kap,
        "fetch_disclosures_by_oid",
        lambda oid, days=60: [
            kap.Disclosure(
                date=None, title="VEYAS Fiyat Tespit Raporu", category=ipr._IZAHNAME_CATEGORY, summary="", url="",
                importance="dusuk", is_late=False, disclosure_index=42, stock_codes="HALKY", related_stocks="VEYAS",
            ),
        ],
    )

    result = ipr.find_price_report_disclosure_index(_disclosure())

    assert result == 42


def test_find_price_report_disclosure_index_baslikta_gecmezse_none(monkeypatch) -> None:
    monkeypatch.setattr(kap, "search_company_by_name", lambda name: [kap.CompanyMatch(member_oid="123", name="HALK YATIRIM MENKUL DEĞERLER A.Ş.", ticker_codes=())])
    monkeypatch.setattr(
        kap,
        "fetch_disclosures_by_oid",
        lambda oid, days=60: [
            kap.Disclosure(
                date=None, title="VEYAS Onaylı İzahname", category=ipr._IZAHNAME_CATEGORY, summary="", url="",
                importance="dusuk", is_late=False, disclosure_index=1, stock_codes="HALKY", related_stocks="VEYAS",
            ),
        ],
    )

    assert ipr.find_price_report_disclosure_index(_disclosure()) is None


def test_find_price_report_disclosure_index_kurum_bulunamazsa_none(monkeypatch) -> None:
    monkeypatch.setattr(kap, "search_company_by_name", lambda name: [])

    assert ipr.find_price_report_disclosure_index(_disclosure()) is None


# --- fetch_and_parse_price_report -- Kural 9: hata ASLA tüm sonucu çökertmez ---------------------


def test_fetch_and_parse_price_report_bulunamazsa_none_doner(monkeypatch) -> None:
    monkeypatch.setattr(ipr, "find_price_report_disclosure_index", lambda disclosure: None)

    assert ipr.fetch_and_parse_price_report(_disclosure()) is None


def test_fetch_and_parse_price_report_hata_olursa_none_doner_cokmez(monkeypatch) -> None:
    def _boom(disclosure):
        raise RuntimeError("beklenmeyen ağ hatası")

    monkeypatch.setattr(ipr, "find_price_report_disclosure_index", _boom)

    assert ipr.fetch_and_parse_price_report(_disclosure()) is None
