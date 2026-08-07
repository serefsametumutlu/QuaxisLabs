"""src/bot/ipo_pipeline.py testleri -- Faz 20 devamı.

Kural 11: ağ isteği ATILMAZ -- `kap_ipo` fonksiyonları monkeypatch edilir.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from src.bot import ipo_pipeline
from src.fetchers import ipo_broker_page, kap_ipo


def _disclosure(ticker: str = "KARCL") -> kap_ipo.IzahnameDisclosure:
    return kap_ipo.IzahnameDisclosure(
        disclosure_indices=(1,),
        publish_date=date(2026, 7, 17),
        underwriter_name="A1 CAPİTAL YATIRIM MENKUL DEĞERLER A.Ş.",
        target_tickers=(ticker,),
        summary=f"{ticker} Halka Arzına İlişkin Onaylı İzahname",
    )


def _facts() -> kap_ipo.IpoFacts:
    return kap_ipo.IpoFacts(
        offering_price=Decimal("35.00"), capital_increase_amount=Decimal("110000000"),
        offering_size=Decimal("3850000000"), estimated_offering_cost=Decimal("122174720"),
        net_offering_proceeds=Decimal("3727825280"), equity_before=Decimal("11686748615"),
        equity_after=Decimal("15414573895"), paid_capital_before=Decimal("720000000"),
        paid_capital_after=Decimal("830000000"), book_value_per_share_before=Decimal("16.2316"),
        book_value_per_share_after=Decimal("18.5718"), dilution_existing_pct=Decimal("14.42"),
        dilution_new_pct=Decimal("-46.94"), allocation_breakdown={"Yurt İçi Bireysel Yatırımcılara": Decimal("100")},
        use_of_proceeds=None,
    )


def test_compute_ipo_card_data_basarili_akis(monkeypatch) -> None:
    monkeypatch.setattr(kap_ipo, "find_izahname_for_ticker", lambda ticker, days=180: _disclosure(ticker))
    monkeypatch.setattr(kap_ipo, "fetch_and_parse_izahname", lambda disclosure: _facts())

    result = ipo_pipeline.compute_ipo_card_data("karcl")

    assert result.ticker == "KARCL"
    assert result.reason is None
    assert result.disclosure is not None
    assert result.facts is not None
    assert result.assessment is not None
    assert result.assessment.is_pure_capital_increase is True


def test_compute_ipo_card_data_izahname_bulunamazsa_reason_doner(monkeypatch) -> None:
    monkeypatch.setattr(kap_ipo, "find_izahname_for_ticker", lambda ticker, days=180: None)

    result = ipo_pipeline.compute_ipo_card_data("YOKTUR")

    assert result.disclosure is None
    assert result.facts is None
    assert result.assessment is None
    assert "bulunamadı" in result.reason


def test_compute_ipo_card_data_pdf_ayristirilamazsa_reason_doner(monkeypatch) -> None:
    monkeypatch.setattr(kap_ipo, "find_izahname_for_ticker", lambda ticker, days=180: _disclosure(ticker))
    monkeypatch.setattr(kap_ipo, "fetch_and_parse_izahname", lambda disclosure: None)

    result = ipo_pipeline.compute_ipo_card_data("KARCL")

    assert result.disclosure is not None
    assert result.facts is None
    assert result.assessment is None
    assert "ayrıştırılamadı" in result.reason


def test_compute_ipo_card_data_kap_taramasi_cokerse_sessizce_dusmez(monkeypatch) -> None:
    """Kural 9: beklenmeyen bir hata (network vb.) TÜM akışı çökertmez,
    kullanıcıya anlaşılır bir 'reason' ile döner."""

    def _boom(ticker, days=180):
        raise RuntimeError("beklenmedik ağ hatası")

    monkeypatch.setattr(kap_ipo, "find_izahname_for_ticker", _boom)

    result = ipo_pipeline.compute_ipo_card_data("KARCL")

    assert result.assessment is None
    assert "ulaşılamıyor" in result.reason


def test_compute_ipo_card_data_from_disclosure_taramayi_atlar(monkeypatch) -> None:
    """`disclosure` ZATEN biliniyorsa `find_izahname_for_ticker()` (22
    aracı kurum taraması) HİÇ ÇAĞRILMAMALI -- sadece PDF indirme/ayrıştırma
    adımı çalışır."""

    def _bomba(*args, **kwargs):
        raise AssertionError("find_izahname_for_ticker ÇAĞRILMAMALIYDI")

    monkeypatch.setattr(kap_ipo, "find_izahname_for_ticker", _bomba)
    monkeypatch.setattr(kap_ipo, "fetch_and_parse_izahname", lambda disclosure: _facts())

    result = ipo_pipeline.compute_ipo_card_data_from_disclosure(_disclosure("KARCL"))

    assert result.ticker == "KARCL"
    assert result.assessment is not None
    assert result.reason is None


def test_list_available_ipos_kap_ipo_ya_delege_eder(monkeypatch) -> None:
    expected = [_disclosure("KARCL"), _disclosure("QUICK")]
    monkeypatch.setattr(kap_ipo, "find_recent_izahnameler", lambda days=60: expected)

    assert ipo_pipeline.list_available_ipos(days=30) == expected


# --- Fiyat Tespit Raporu wiring (Faz 20.5, 2026-08-07 devamı) -----------------------------------


def _price_report():
    from decimal import Decimal

    from src.fetchers import ipo_price_report

    return ipo_price_report.PriceReportFinancials(
        period_label="31.03.2026", full_year_label="2025",
        revenue_latest_interim=Decimal("5775822"), revenue_prior_year_interim=Decimal("5084478"),
        revenue_full_year=Decimal("26652218"),
        gross_profit_latest_interim=Decimal("2469357"), gross_profit_prior_year_interim=Decimal("1156369"),
        total_assets=Decimal("30121124"), total_equity=Decimal("15590464"),
    )


def test_compute_ipo_card_data_from_disclosure_price_report_assessmente_gecirilir(monkeypatch) -> None:
    from src.fetchers import ipo_price_report

    monkeypatch.setattr(kap_ipo, "fetch_and_parse_izahname", lambda disclosure: _facts())
    monkeypatch.setattr(ipo_price_report, "fetch_and_parse_price_report", lambda disclosure: _price_report())
    monkeypatch.setattr(ipo_broker_page, "fetch_supplementary_ipo_info", lambda ticker: None)

    result = ipo_pipeline.compute_ipo_card_data_from_disclosure(_disclosure("KARCL"))

    assert result.price_report is not None
    assert result.price_report.revenue_full_year == Decimal("26652218")
    assert result.assessment.revenue_yoy_growth_pct is not None


def test_compute_ipo_card_data_from_disclosure_price_report_bulunamazsa_none(monkeypatch) -> None:
    from src.fetchers import ipo_price_report

    monkeypatch.setattr(kap_ipo, "fetch_and_parse_izahname", lambda disclosure: _facts())
    monkeypatch.setattr(ipo_price_report, "fetch_and_parse_price_report", lambda disclosure: None)
    monkeypatch.setattr(ipo_broker_page, "fetch_supplementary_ipo_info", lambda ticker: None)

    result = ipo_pipeline.compute_ipo_card_data_from_disclosure(_disclosure("KARCL"))

    assert result.price_report is None
    assert result.assessment is not None  # Kural 9: ana akış ETKİLENMEZ
    assert result.assessment.revenue_yoy_growth_pct is None
