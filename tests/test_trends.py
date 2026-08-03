"""src/analysis/trends.py testleri (Derin Kart -- çok dönemli trend serileri).

Fikstür test_calculator.py::_sample_financials() ile AYNI (isteyerek
kopyalandı) -- bu sayede beklenen değerler test_calculator.py'de ZATEN elle
doğrulanmış TTM/marj/net borç rakamlarıyla ÇAPRAZ tutarlı kalır (orn.
test_analyze_net_borc_favok_ttm: TTM FAVÖK=46, test_analyze_roe_yillikandirilmis_ttm:
ROE=38/400*100).
"""

from __future__ import annotations

from decimal import Decimal

from src.analysis.trends import compute_multi_period_trend

_LATEST = (2026, 3)
_QOQ_PRIOR = (2025, 12)
_TTM_3 = (2025, 9)
_TTM_4 = (2025, 6)
_YOY_PRIOR = (2025, 3)


def _sample_financials() -> dict:
    return {
        _LATEST: {
            "revenue": Decimal("120"),
            "revenue_cum": Decimal("120"),
            "gross_profit": Decimal("50"),
            "gross_profit_cum": Decimal("50"),
            "operating_profit": Decimal("20"),
            "operating_profit_cum": Decimal("20"),
            "operating_profit_ebitda_base": Decimal("20"),
            "operating_profit_ebitda_base_cum": Decimal("20"),
            "depreciation_amortization": Decimal("10"),
            "depreciation_amortization_cum": Decimal("10"),
            "net_income": Decimal("15"),
            "net_income_cum": Decimal("15"),
            "cash": Decimal("200"),
            "trade_receivables": Decimal("80"),
            "total_assets": Decimal("1000"),
            "financial_debt": Decimal("300"),
            "equity": Decimal("400"),
            "current_assets": Decimal("500"),
            "short_term_liabilities": Decimal("250"),
        },
        _QOQ_PRIOR: {
            "revenue": Decimal("140"),
            "revenue_cum": Decimal("140"),
            "gross_profit": Decimal("55"),
            "gross_profit_cum": Decimal("55"),
            "operating_profit": Decimal("25"),
            "operating_profit_cum": Decimal("25"),
            "operating_profit_ebitda_base": Decimal("25"),
            "operating_profit_ebitda_base_cum": Decimal("25"),
            "depreciation_amortization": Decimal("11"),
            "depreciation_amortization_cum": Decimal("11"),
            "net_income": Decimal("18"),
            "net_income_cum": Decimal("18"),
            "cash": Decimal("180"),
            "trade_receivables": Decimal("75"),
            "total_assets": Decimal("950"),
            "financial_debt": Decimal("310"),
            "equity": Decimal("380"),
        },
        _TTM_3: {
            "revenue": Decimal("130"),
            "revenue_cum": Decimal("130"),
            "gross_profit": Decimal("52"),
            "gross_profit_cum": Decimal("52"),
            "operating_profit": Decimal("22"),
            "operating_profit_cum": Decimal("22"),
            "operating_profit_ebitda_base": Decimal("22"),
            "operating_profit_ebitda_base_cum": Decimal("22"),
            "depreciation_amortization": Decimal("10"),
            "depreciation_amortization_cum": Decimal("10"),
            "net_income": Decimal("16"),
            "net_income_cum": Decimal("16"),
        },
        _TTM_4: {
            "revenue": Decimal("110"),
            "revenue_cum": Decimal("110"),
            "gross_profit": Decimal("44"),
            "gross_profit_cum": Decimal("44"),
            "operating_profit": Decimal("15"),
            "operating_profit_cum": Decimal("15"),
            "operating_profit_ebitda_base": Decimal("15"),
            "operating_profit_ebitda_base_cum": Decimal("15"),
            "depreciation_amortization": Decimal("9"),
            "depreciation_amortization_cum": Decimal("9"),
            "net_income": Decimal("10"),
            "net_income_cum": Decimal("10"),
        },
        _YOY_PRIOR: {
            "revenue": Decimal("100"),
            "revenue_cum": Decimal("100"),
            "gross_profit": Decimal("38"),
            "gross_profit_cum": Decimal("38"),
            "operating_profit": Decimal("12"),
            "operating_profit_cum": Decimal("12"),
            "operating_profit_ebitda_base": Decimal("12"),
            "operating_profit_ebitda_base_cum": Decimal("12"),
            "depreciation_amortization": Decimal("8"),
            "depreciation_amortization_cum": Decimal("8"),
            "net_income": Decimal("-5"),
            "net_income_cum": Decimal("-5"),
            "cash": Decimal("150"),
            "trade_receivables": Decimal("60"),
            "total_assets": Decimal("800"),
            "financial_debt": Decimal("290"),
            "equity": Decimal("200"),
        },
    }


def test_compute_multi_period_trend_bos_girdide_none_doner():
    assert compute_multi_period_trend({}) is None


def test_compute_multi_period_trend_noktalar_artan_donem_sirasinda():
    trend = compute_multi_period_trend(_sample_financials())
    assert trend is not None
    assert [p.period for p in trend.points] == [_YOY_PRIOR, _TTM_4, _TTM_3, _QOQ_PRIOR, _LATEST]


def test_compute_multi_period_trend_guncel_donem_ham_degerler():
    trend = compute_multi_period_trend(_sample_financials())
    latest_point = trend.points[-1]

    assert latest_point.period == _LATEST
    assert latest_point.revenue == Decimal("120")
    assert latest_point.ebitda == Decimal("30")  # 20 + 10 (operating_profit_ebitda_base + D&A)
    assert latest_point.net_income == Decimal("15")
    assert latest_point.equity == Decimal("400")


def test_compute_multi_period_trend_guncel_donem_marjlar():
    trend = compute_multi_period_trend(_sample_financials())
    latest_point = trend.points[-1]

    assert latest_point.gross_margin_pct == Decimal("50") / Decimal("120") * 100
    assert latest_point.ebitda_margin_pct == Decimal("30") / Decimal("120") * 100
    assert latest_point.net_margin_pct == Decimal("15") / Decimal("120") * 100


def test_compute_multi_period_trend_guncel_donem_kaldirac_ve_roe():
    """test_calculator.py::test_analyze_net_borc_favok_ttm/test_analyze_roe_yillikandirilmis_ttm
    ile AYNI (zaten elle doğrulanmış) TTM FAVÖK=46, net borç=100, TTM net
    kâr=38 rakamlarıyla ÇAPRAZ tutarlı olmalı."""
    trend = compute_multi_period_trend(_sample_financials())
    latest_point = trend.points[-1]

    assert latest_point.net_debt_to_ebitda == Decimal("100") / Decimal("46")
    assert latest_point.roe_pct == Decimal("38") / Decimal("400") * 100


def test_compute_multi_period_trend_eksik_bilanco_alanlarinda_kaldirac_roe_none():
    """_TTM_3/_TTM_4 donemlerinde bilanco (cash/financial_debt/equity) HİÇ
    yok -- kaldıraç/ROE bu donemler icin None kalmali (K4), ama marj/hasilat
    gibi gelir-tablosu-bazli alanlar YİNE DE dolu olmali."""
    trend = compute_multi_period_trend(_sample_financials())
    ttm3_point = next(p for p in trend.points if p.period == _TTM_3)

    assert ttm3_point.revenue == Decimal("130")
    assert ttm3_point.gross_margin_pct is not None
    assert ttm3_point.net_debt_to_ebitda is None
    assert ttm3_point.roe_pct is None


def test_compute_multi_period_trend_mevsimsellik_en_az_iki_yil_gerekir():
    """Fikstürde SADECE 1. çeyrek (period numarası 3) iki farklı yılda
    (2025, 2026) var -- diğer çeyrek numaraları (6/9/12) tek yıl, gruba
    DAHİL EDİLMEMELİ (K4: tek nokta karşılaştırma sayılmaz)."""
    trend = compute_multi_period_trend(_sample_financials())

    assert len(trend.seasonality) == 1
    group = trend.seasonality[0]
    assert group.quarter_number == 3
    assert group.years == (2025, 2026)
    assert group.revenues == (Decimal("100"), Decimal("120"))


def test_compute_multi_period_trend_tek_donemde_mevsimsellik_bos():
    trend = compute_multi_period_trend({_LATEST: _sample_financials()[_LATEST]})
    assert trend is not None
    assert trend.seasonality == ()


def test_compute_multi_period_trend_mevsimsellik_biri_none_ise_grup_disi_kalir():
    """CANLI keşfedilen kenar durum (THYAO demo karti): iki farkli yilda
    AYNI ceyrek numarasi VAR ama birinin hasilati None (o donem kismi/eksik
    veri) -- bu tek GERCEK nokta bir 'karsilastirma' SAYILMAZ, grup
    OLUSTURULMAMALI (K4), aksi halde duz/anlamsiz bir cizgi cikardi."""
    financials = _sample_financials()
    financials[(2024, 3)] = {"revenue": None}  # ayni ceyrek (3) ama hasilat None

    trend = compute_multi_period_trend(financials)

    # quarter_number=3 icin artik UC yil var (2024 None, 2025=100, 2026=120)
    # ama SADECE IKI gercek (non-None) deger -- grup YINE DE olusmali (2 gercek yeterli).
    group = next(g for g in trend.seasonality if g.quarter_number == 3)
    assert group.years == (2024, 2025, 2026)
    assert group.revenues == (None, Decimal("100"), Decimal("120"))


def test_compute_multi_period_trend_mevsimsellik_sadece_bir_gercek_deger_varsa_disarida_kalir():
    financials = {
        _LATEST: _sample_financials()[_LATEST],
        (2024, 3): {"revenue": None},
    }
    trend = compute_multi_period_trend(financials)
    assert trend.seasonality == ()
