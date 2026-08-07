"""src/analysis/ipo_assessment.py testleri -- Faz 20 devamı.

Kural 11: ağ isteği ATILMAZ. GERÇEK KARCL izahname metniyle (aynı fixture,
tests/test_kap_ipo.py ile PAYLAŞILIR) uçtan uca doğrulanır -- rakamlar
`extract_ipo_facts()` çıktısından elle hesaplanıp karşılaştırılmıştır.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from src.analysis import ipo_assessment
from src.fetchers import kap_ipo

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
KARCL_IZAHNAME_TEXT = (FIXTURES_DIR / "kap_izahname_karcl_2026_07.txt").read_text(encoding="utf-8")


def _q4(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def test_compute_ipo_assessment_karcl_gercek_veriyle_birebir() -> None:
    """KARCL: sermaye artırımı (110.000.000 x 35,00 = 3.850.000.000) TAM
    olarak arz büyüklüğüne (3.850.000.000) eşit -- yani arzın TAMAMI yeni
    sermaye, hiç ortak satışı yok (%100 saf sermaye artırımı)."""
    facts = kap_ipo.extract_ipo_facts(KARCL_IZAHNAME_TEXT)
    assessment = ipo_assessment.compute_ipo_assessment(facts)

    assert assessment.capital_increase_share_pct == Decimal("100")
    assert assessment.partner_sale_share_pct == Decimal("0")
    assert assessment.is_pure_capital_increase is True

    assert assessment.allocation_retail_pct == Decimal("40.00")
    assert assessment.allocation_domestic_institutional_pct == Decimal("30.00")
    assert assessment.allocation_foreign_institutional_pct == Decimal("20.00")
    # "Yüksek Talepte Bulunacak Yatırımcı Grubu" -- KENDİ grubuna ayrıldı
    # (2026-08-07), artık "diğer"e düşmüyor.
    assert assessment.allocation_high_demand_pct == Decimal("10.00")
    assert assessment.allocation_other_pct == Decimal("0")

    assert _q4(assessment.price_to_book_before) == Decimal("2.1563")
    assert _q4(assessment.equity_growth_pct) == Decimal("31.8979")


def test_compute_ipo_assessment_karcl_lot_sayilari_gercek_veriyle_birebir() -> None:
    """KARCL: toplam lot = 3.850.000.000 ÷ 35,00 = 110.000.000; her tahsisat
    grubunun lot sayısı kendi yüzdesinin toplam lota uygulanmasıyla bulunur."""
    facts = kap_ipo.extract_ipo_facts(KARCL_IZAHNAME_TEXT)
    assessment = ipo_assessment.compute_ipo_assessment(facts)

    assert assessment.total_lot_count == Decimal("110000000")
    assert assessment.allocation_retail_lot_count == Decimal("44000000")
    assert assessment.allocation_domestic_institutional_lot_count == Decimal("33000000")
    assert assessment.allocation_foreign_institutional_lot_count == Decimal("22000000")
    assert assessment.allocation_high_demand_lot_count == Decimal("11000000")
    assert assessment.allocation_other_lot_count == Decimal("0")


def test_compute_ipo_assessment_tahmini_dagitim_esit_bolme_ve_asagi_yuvarlama() -> None:
    """Referans görseldeki senaryoyla AYNI mantık: 44.000.000 bireysel lot,
    500.000 katılımcıya bölününce kişi başı 88 lot (tam bölünüyor); TL
    karşılığı lot × arz fiyatıyla (35,00) hesaplanır."""
    facts = kap_ipo.extract_ipo_facts(KARCL_IZAHNAME_TEXT)
    assessment = ipo_assessment.compute_ipo_assessment(facts)

    rows = dict((p, (lot, tl)) for p, lot, tl in assessment.estimated_retail_distribution)
    assert rows[500_000] == (Decimal("88"), Decimal("3080"))
    assert rows[300_000] == (Decimal("146"), Decimal("5110"))


def test_compute_ipo_assessment_lot_verisi_eksikse_none_doner() -> None:
    """Kural 3: offering_price/offering_size'dan biri eksikse lot alanları
    da (çöküp uydurmak yerine) None kalır."""
    facts = kap_ipo.IpoFacts(
        offering_price=None, capital_increase_amount=None, offering_size=None,
        estimated_offering_cost=None, net_offering_proceeds=None,
        equity_before=None, equity_after=None,
        paid_capital_before=None, paid_capital_after=None,
        book_value_per_share_before=None, book_value_per_share_after=None,
        dilution_existing_pct=None, dilution_new_pct=None,
        allocation_breakdown=None, use_of_proceeds=None,
    )
    assessment = ipo_assessment.compute_ipo_assessment(facts)
    assert assessment.total_lot_count is None
    assert assessment.allocation_retail_lot_count is None
    assert assessment.estimated_retail_distribution is None


def test_compute_ipo_assessment_fon_kullanim_yeri_yoksa_top_use_of_proceeds_none() -> None:
    facts = kap_ipo.extract_ipo_facts(KARCL_IZAHNAME_TEXT)  # use_of_proceeds_text verilmedi
    assessment = ipo_assessment.compute_ipo_assessment(facts)
    assert assessment.top_use_of_proceeds is None


def test_compute_ipo_assessment_use_of_proceeds_buyukten_kucuge_siralanir() -> None:
    facts = kap_ipo.IpoFacts(
        offering_price=None, capital_increase_amount=None, offering_size=None,
        estimated_offering_cost=None, net_offering_proceeds=None,
        equity_before=None, equity_after=None,
        paid_capital_before=None, paid_capital_after=None,
        book_value_per_share_before=None, book_value_per_share_after=None,
        dilution_existing_pct=None, dilution_new_pct=None,
        allocation_breakdown=None,
        use_of_proceeds={"Borç Ödemesi": Decimal("40"), "Yatırım": Decimal("55"), "İşletme Sermayesi": Decimal("5")},
    )
    assessment = ipo_assessment.compute_ipo_assessment(facts)
    assert assessment.top_use_of_proceeds == (
        ("Yatırım", Decimal("55")),
        ("Borç Ödemesi", Decimal("40")),
        ("İşletme Sermayesi", Decimal("5")),
    )


def test_compute_ipo_assessment_kismi_ortak_satisi_dogru_oranlanir() -> None:
    """BEWEN örneğine benzer senaryo: 80mn lotun 56mn'ı sermaye artırımı,
    24mn'ı ortak satışı -- capital_increase_share_pct ~%70 olmalı."""
    facts = kap_ipo.IpoFacts(
        offering_price=Decimal("48.10"),
        capital_increase_amount=Decimal("56000000"),
        offering_size=Decimal("3848000000"),  # 80.000.000 x 48,10
        estimated_offering_cost=None, net_offering_proceeds=None,
        equity_before=None, equity_after=None,
        paid_capital_before=None, paid_capital_after=None,
        book_value_per_share_before=None, book_value_per_share_after=None,
        dilution_existing_pct=None, dilution_new_pct=None,
        allocation_breakdown=None, use_of_proceeds=None,
    )
    assessment = ipo_assessment.compute_ipo_assessment(facts)
    assert _q4(assessment.capital_increase_share_pct) == Decimal("70.0000")
    assert _q4(assessment.partner_sale_share_pct) == Decimal("30.0000")
    assert assessment.is_pure_capital_increase is False


def test_compute_ipo_assessment_eksik_veri_none_doner() -> None:
    """Kural 3: girdi alanları None ise ÇÖKMEZ, ilgili çıktı None kalır."""
    facts = kap_ipo.IpoFacts(
        offering_price=None, capital_increase_amount=None, offering_size=None,
        estimated_offering_cost=None, net_offering_proceeds=None,
        equity_before=None, equity_after=None,
        paid_capital_before=None, paid_capital_after=None,
        book_value_per_share_before=None, book_value_per_share_after=None,
        dilution_existing_pct=None, dilution_new_pct=None,
        allocation_breakdown=None, use_of_proceeds=None,
    )
    assessment = ipo_assessment.compute_ipo_assessment(facts)
    assert assessment.capital_increase_share_pct is None
    assert assessment.partner_sale_share_pct is None
    assert assessment.is_pure_capital_increase is False
    assert assessment.allocation_retail_pct is None
    assert assessment.price_to_book_before is None
    assert assessment.equity_growth_pct is None


# --- YoY büyüme (Faz 20.5, 2026-08-07 devamı) -- GERÇEK VEYAS Fiyat Tespit Raporu verisiyle ------


def _bos_facts() -> kap_ipo.IpoFacts:
    return kap_ipo.IpoFacts(
        offering_price=None, capital_increase_amount=None, offering_size=None,
        estimated_offering_cost=None, net_offering_proceeds=None,
        equity_before=None, equity_after=None,
        paid_capital_before=None, paid_capital_after=None,
        book_value_per_share_before=None, book_value_per_share_after=None,
        dilution_existing_pct=None, dilution_new_pct=None,
        allocation_breakdown=None, use_of_proceeds=None,
    )


def test_compute_ipo_assessment_yoy_buyume_veyas_referans_gorselle_eslesir() -> None:
    """Referans görsel: Ciro artışı %13,6, Brüt kâr artışı %113,5 (bkz.
    tests/test_ipo_price_report.py, aynı Fiyat Tespit Raporu verisi)."""
    from src.fetchers import ipo_price_report

    price_report = ipo_price_report.PriceReportFinancials(
        period_label="31.03.2026", full_year_label="2025",
        revenue_latest_interim=Decimal("5775822"), revenue_prior_year_interim=Decimal("5084478"),
        revenue_full_year=Decimal("26652218"),
        gross_profit_latest_interim=Decimal("2469357"), gross_profit_prior_year_interim=Decimal("1156369"),
        total_assets=Decimal("30121124"), total_equity=Decimal("15590464"),
    )

    assessment = ipo_assessment.compute_ipo_assessment(_bos_facts(), price_report=price_report)

    assert _q4(assessment.revenue_yoy_growth_pct).quantize(Decimal("0.1")) == Decimal("13.6")
    assert _q4(assessment.gross_profit_yoy_growth_pct).quantize(Decimal("0.1")) == Decimal("113.5")


def test_compute_ipo_assessment_price_report_verilmezse_yoy_buyume_none() -> None:
    assessment = ipo_assessment.compute_ipo_assessment(_bos_facts())

    assert assessment.revenue_yoy_growth_pct is None
    assert assessment.gross_profit_yoy_growth_pct is None


def test_compute_ipo_assessment_price_report_kismi_veriyle_ilgili_alan_none() -> None:
    from src.fetchers import ipo_price_report

    price_report = ipo_price_report.PriceReportFinancials(
        period_label=None, full_year_label=None,
        revenue_latest_interim=None, revenue_prior_year_interim=None, revenue_full_year=None,
        gross_profit_latest_interim=Decimal("2469357"), gross_profit_prior_year_interim=Decimal("1156369"),
        total_assets=None, total_equity=None,
    )

    assessment = ipo_assessment.compute_ipo_assessment(_bos_facts(), price_report=price_report)

    assert assessment.revenue_yoy_growth_pct is None
    assert assessment.gross_profit_yoy_growth_pct is not None
