"""Faz 4 teslim kriteri: calculator.py icin elle hesaplanmis beklenen
degerlerle test senaryolari (negatiften pozitife gecis dahil).

Beklenen degerler, uygulamanin kullandigi AYNI Decimal ifadeleriyle
(orn. (current-previous)/abs(previous)*100) yazilir; boylece "elle
hesaplama" gercek matematiksel dogrulugu test eder, kayan nokta/yuvarlama
farkliliklarini degil.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.analysis.calculator import (
    ChangeLabel,
    compute_valuation,
    compute_valuation_bank,
    compute_valuation_insurance,
    ebitda,
    ebitda_cum,
    analyze,
    analyze_bank,
    analyze_insurance,
    classify_change,
    classify_debt_change,
    margin_pct,
    net_debt,
    previous_quarter_period,
    safe_div,
    trailing_12m_from_cumulative,
    year_ago_period,
)


def pct(current, previous) -> Decimal:
    current, previous = Decimal(current), Decimal(previous)
    return (current - previous) / abs(previous) * 100


# --- Donem aritmetigi -----------------------------------------------------


def test_year_ago_period() -> None:
    assert year_ago_period((2026, 3)) == (2025, 3)


def test_previous_quarter_period_yil_ici() -> None:
    assert previous_quarter_period((2026, 6)) == (2026, 3)


def test_previous_quarter_period_yil_basi_geriye_sarar() -> None:
    assert previous_quarter_period((2026, 3)) == (2025, 12)


# --- PUBLIC sarmalayıcılar (Derin Kart, trends.py tarafından kullanılır) -----------------------------------------------------


def test_safe_div_elle_dogrulanir() -> None:
    assert safe_div(Decimal("10"), Decimal("4")) == Decimal("2.5")


def test_safe_div_payda_sifir_veya_none_ise_none() -> None:
    assert safe_div(Decimal("10"), Decimal("0")) is None
    assert safe_div(Decimal("10"), None) is None
    assert safe_div(None, Decimal("10")) is None


def test_margin_pct_elle_dogrulanir() -> None:
    assert margin_pct(Decimal("30"), Decimal("120")) == Decimal("30") / Decimal("120") * 100


def test_net_debt_elle_dogrulanir() -> None:
    assert net_debt(Decimal("300"), Decimal("200"), None) == Decimal("100")
    assert net_debt(Decimal("300"), Decimal("200"), Decimal("50")) == Decimal("50")


def test_trailing_12m_from_cumulative_sample_financials_ile_ayni_sonucu_verir() -> None:
    """test_analyze_net_borc_favok_ttm ile AYNI (zaten dogrulanmis) TTM
    degerini, PUBLIC sarmalayici uzerinden de uretir."""
    result = trailing_12m_from_cumulative(_sample_financials(), _LATEST, ebitda_cum)
    assert result == Decimal("30") + Decimal("36") - Decimal("20")  # 46


# --- classify_change: normal esikler -----------------------------------------------------


def test_classify_change_artis() -> None:
    percent, label, direction = classify_change(Decimal("110"), Decimal("100"))
    assert percent == pct(110, 100) == Decimal("10")
    assert label == ChangeLabel.ARTIS
    assert direction == "artis"


def test_classify_change_guclu_artis() -> None:
    percent, label, direction = classify_change(Decimal("130"), Decimal("100"))
    assert percent == Decimal("30")
    assert label == ChangeLabel.GUCLU_ARTIS
    assert direction == "artis"


def test_classify_change_yatay() -> None:
    percent, label, direction = classify_change(Decimal("103"), Decimal("100"))
    assert percent == Decimal("3")
    assert label == ChangeLabel.YATAY
    assert direction == "yatay"


def test_classify_change_azalis() -> None:
    percent, label, direction = classify_change(Decimal("80"), Decimal("100"))
    assert percent == Decimal("-20")
    assert label == ChangeLabel.AZALIS
    assert direction == "azalis"


def test_classify_change_sert_dusus() -> None:
    percent, label, direction = classify_change(Decimal("60"), Decimal("100"))
    assert percent == Decimal("-40")
    assert label == ChangeLabel.SERT_DUSUS
    assert direction == "azalis"


# --- classify_change: esik sinirlari (dahil/haric davranisi kilitler) -----------------------------------------------------


def test_classify_change_sinir_tam_25_artis_sayilir_guclu_degil() -> None:
    # %25 tam sinirda -- ">%25" degil, bu yuzden ARTIS (GUCLU_ARTIS DEGIL)
    percent, label, _ = classify_change(Decimal("125"), Decimal("100"))
    assert percent == Decimal("25")
    assert label == ChangeLabel.ARTIS


def test_classify_change_sinir_tam_5_yatay_sayilir() -> None:
    percent, label, _ = classify_change(Decimal("105"), Decimal("100"))
    assert percent == Decimal("5")
    assert label == ChangeLabel.YATAY


def test_classify_change_sinir_tam_eksi_5_yatay_sayilir() -> None:
    percent, label, _ = classify_change(Decimal("95"), Decimal("100"))
    assert percent == Decimal("-5")
    assert label == ChangeLabel.YATAY


def test_classify_change_sinir_tam_eksi_25_azalis_sayilir_sert_dusus_degil() -> None:
    percent, label, _ = classify_change(Decimal("75"), Decimal("100"))
    assert percent == Decimal("-25")
    assert label == ChangeLabel.AZALIS


def test_classify_change_sinir_altinda_sert_dusus() -> None:
    percent, label, _ = classify_change(Decimal("74"), Decimal("100"))
    assert percent == Decimal("-26")
    assert label == ChangeLabel.SERT_DUSUS


# --- classify_change: isaret gecisleri (KENAR DURUMU - gorev geregi zorunlu) -----------------------------------------------------


def test_classify_change_zarardan_kara_gecti() -> None:
    percent, label, direction = classify_change(Decimal("30"), Decimal("-50"))
    assert percent is None  # yuzde degisim anlamsiz -> None
    assert label == ChangeLabel.ZARARDAN_KARA_GECTI
    assert direction == "artis"


def test_classify_change_kara_karsin_zarar() -> None:
    percent, label, direction = classify_change(Decimal("-30"), Decimal("50"))
    assert percent is None
    assert label == ChangeLabel.KARA_KARSIN_ZARAR
    assert direction == "azalis"


def test_classify_change_basabas_zarardan_kara_sayilir() -> None:
    # previous negatif, current TAM SIFIR -> "zarardan kara gecti" (kar/zarar olmayan basabas)
    percent, label, _ = classify_change(Decimal("0"), Decimal("-10"))
    assert percent is None
    assert label == ChangeLabel.ZARARDAN_KARA_GECTI


# --- classify_debt_change (net_debt'e ozel, canli TERA hatasinin regresyon testi) -----------------------------------------------------


def test_classify_debt_change_net_nakitten_net_borca_kotulesme() -> None:
    # canli hata: net borc -4,7mn (net nakit) -> 15mn (net borc) KOTULESME idi,
    # ama eski kod "zarardan kara gecti" (IYILESME anlaminda) yaziyordu.
    percent, label, direction = classify_debt_change(Decimal("15"), Decimal("-4.7"))
    assert percent is None
    assert label == ChangeLabel.NET_BORCA_GECTI
    assert label != ChangeLabel.ZARARDAN_KARA_GECTI
    assert direction == "azalis"  # kar/zarar degil, KOTULESME yonunde


def test_classify_debt_change_net_borctan_net_nakde_iyilesme() -> None:
    percent, label, direction = classify_debt_change(Decimal("-30"), Decimal("50"))
    assert percent is None
    assert label == ChangeLabel.NET_NAKDE_GECTI
    assert label != ChangeLabel.KARA_KARSIN_ZARAR
    assert direction == "artis"  # IYILESME yonunde


def test_classify_debt_change_normal_artis_ayni_classify_change_gibi_davranir() -> None:
    # sifir gecisi olmayan durumlarda classify_change ile AYNI (sadece etiketler farkli olabilir)
    percent, label, direction = classify_debt_change(Decimal("120"), Decimal("100"))
    assert percent == pct(120, 100)
    assert direction == "artis"


def test_classify_change_basabas_kara_karsin_zarar_sayilir() -> None:
    percent, label, _ = classify_change(Decimal("0"), Decimal("10"))
    assert percent is None
    assert label == ChangeLabel.KARA_KARSIN_ZARAR


def test_classify_change_negatiften_negatife_iyilesme_guclu_artis() -> None:
    # Zarar daralmasi (-100 -> -20): naif formul (payda=previous) yanlislikla
    # negatif/kotulesme gosterirdi; abs(previous) kullanimi DOGRU yonu verir.
    percent, label, direction = classify_change(Decimal("-20"), Decimal("-100"))
    assert percent == Decimal("80")
    assert label == ChangeLabel.GUCLU_ARTIS
    assert direction == "artis"


def test_classify_change_negatiften_negatife_kotulesme_sert_dusus() -> None:
    percent, label, direction = classify_change(Decimal("-150"), Decimal("-100"))
    assert percent == Decimal("-50")
    assert label == ChangeLabel.SERT_DUSUS
    assert direction == "azalis"


# --- classify_change: sifira bolme / eksik veri (KENAR DURUMU - gorev geregi zorunlu) -----------------------------------------------------


def test_classify_change_onceki_sifir_sifira_bolme_guvenli() -> None:
    percent, label, direction = classify_change(Decimal("100"), Decimal("0"))
    assert percent is None
    assert label == ChangeLabel.VERI_YOK
    assert direction == "belirsiz"


def test_classify_change_guncel_none() -> None:
    percent, label, _ = classify_change(None, Decimal("100"))
    assert percent is None
    assert label == ChangeLabel.VERI_YOK


def test_classify_change_onceki_none() -> None:
    percent, label, _ = classify_change(Decimal("100"), None)
    assert percent is None
    assert label == ChangeLabel.VERI_YOK


def test_classify_change_ikisi_de_none() -> None:
    percent, label, _ = classify_change(None, None)
    assert percent is None
    assert label == ChangeLabel.VERI_YOK


# --- ebitda() (KENAR DURUMU: banka/sigorta -> amortisman verisi yok) -----------------------------------------------------


def test_ebitda_hesaplanir() -> None:
    # ebitda() BILEREK "operating_profit" DEGIL "operating_profit_ebitda_base"
    # okur (bkz. calculator.ebitda() docstring'i -- Fintables'in FAVOK icin
    # kullandigi DAR faaliyet kari kavrami, gelir tablosunda gosterilen
    # "operating_profit" ile AYNI DEGIL).
    assert ebitda({"operating_profit_ebitda_base": Decimal("100"), "depreciation_amortization": Decimal("20")}) == Decimal("120")


def test_ebitda_amortisman_eksikse_none() -> None:
    assert ebitda({"operating_profit_ebitda_base": Decimal("100")}) is None


def test_ebitda_faaliyet_kari_eksikse_none() -> None:
    assert ebitda({"depreciation_amortization": Decimal("20")}) is None


# --- analyze(): tam entegrasyon senaryosu (elle hesaplanmis) -----------------------------------------------------

_LATEST = (2026, 3)
_QOQ_PRIOR = (2025, 12)
_TTM_3 = (2025, 9)
_TTM_4 = (2025, 6)
_YOY_PRIOR = (2025, 3)  # ayni zamanda TTM'in disinda kalir (5. donem)


def _sample_financials() -> dict:
    # NOT: "_cum" alanlari (kumulatif/YTD) bu testlerde KASITLI OLARAK
    # ceyreklik alanla AYNI degeri tasir -- income_statement/findings artik
    # "_cum" alanlarini okuyor (bkz. calculator.analyze() ici not), TTM/rasyo
    # hesaplari ise ceyreklik alanlari okumaya devam ediyor; bu testler ikisi
    # arasindaki FARKI degil, YoY/QoQ/TTM formullerinin kendisini dogruluyor,
    # bu yuzden iki alan kumesini ayni tutmak testleri sadelestirir.
    # "operating_profit_ebitda_base"(_cum) da ayni sebeple KASITLI OLARAK
    # "operating_profit" ile AYNI deger tasir -- bu testler FAVOK'un
    # "operating_profit" ile "operating_profit_ebitda_base" arasindaki
    # (gercek veride var olan, bkz. isyatirim.py ici not) FARKI degil,
    # ebitda()/ebitda_cum()'in formulunu dogruluyor.
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
            "net_income": Decimal("-5"),  # KASITLI: YoY net kar gecisini test eder
            "net_income_cum": Decimal("-5"),
            "cash": Decimal("150"),
            "trade_receivables": Decimal("60"),
            "total_assets": Decimal("800"),
            "financial_debt": Decimal("290"),
            "equity": Decimal("200"),
        },
    }


def test_analyze_gelir_tablosu_yoy_bloklari() -> None:
    result = analyze("TEST", _sample_financials())
    inc = result.income_statement

    assert inc.revenue.percent_change == pct(120, 100)
    assert inc.revenue.change_label == ChangeLabel.ARTIS

    assert inc.gross_profit.percent_change == pct(50, 38)
    assert inc.gross_profit.change_label == ChangeLabel.GUCLU_ARTIS

    assert inc.operating_profit.percent_change == pct(20, 12)
    assert inc.operating_profit.change_label == ChangeLabel.GUCLU_ARTIS


def test_analyze_ebitda_hesabi_ve_yoy_degisimi() -> None:
    result = analyze("TEST", _sample_financials())
    inc = result.income_statement

    assert inc.ebitda is not None
    assert inc.ebitda.current == Decimal("30")  # 20 + 10
    assert inc.ebitda.comparison == Decimal("20")  # 12 + 8
    assert inc.ebitda.percent_change == pct(30, 20) == Decimal("50")
    assert inc.ebitda.change_label == ChangeLabel.GUCLU_ARTIS


def test_analyze_net_kar_zarardan_kara_gecis() -> None:
    result = analyze("TEST", _sample_financials())
    net_income = result.income_statement.net_income

    assert net_income.current == Decimal("15")
    assert net_income.comparison == Decimal("-5")
    assert net_income.percent_change is None
    assert net_income.change_label == ChangeLabel.ZARARDAN_KARA_GECTI


def test_analyze_bilanco_qoq_bloklari() -> None:
    result = analyze("TEST", _sample_financials())
    bal = result.balance_sheet

    assert bal.cash.percent_change == pct(200, 180)
    assert bal.cash.change_label == ChangeLabel.ARTIS

    assert bal.financial_debt.percent_change == pct(300, 310)
    assert bal.financial_debt.change_label == ChangeLabel.YATAY

    assert bal.equity.percent_change == pct(400, 380)


def test_analyze_marjlar_ve_puan_degisimi() -> None:
    result = analyze("TEST", _sample_financials())
    ratios = result.ratios

    assert ratios.gross_margin_current == Decimal("50") / Decimal("120") * 100
    assert ratios.gross_margin_prior_year == Decimal("38") / Decimal("100") * 100
    assert ratios.gross_margin_change_points == ratios.gross_margin_current - ratios.gross_margin_prior_year

    assert ratios.ebitda_margin_current == Decimal("30") / Decimal("120") * 100
    assert ratios.ebitda_margin_change_points == Decimal("5")  # 25% - 20%

    assert ratios.net_margin_current == Decimal("15") / Decimal("120") * 100
    assert ratios.net_margin_prior_year == Decimal("-5")
    assert ratios.net_margin_change_points == Decimal("17.5")


def test_analyze_net_borc_favok_ttm() -> None:
    result = analyze("TEST", _sample_financials())
    # TTM FAVOK = guncel YTD(30=20+10) + gecen yil tam yil(36=25+11, _QOQ_PRIOR
    # ayni zamanda 2025/12) - gecen yil ayni donem YTD(20=12+8, _YOY_PRIOR) = 46
    # net borc = finansal borc(300) - nakit(200) = 100
    assert result.ratios.net_debt_to_ebitda == Decimal("100") / Decimal("46")


def test_analyze_degerleme_girdileri_ratios_uzerinde_disari_acilir() -> None:
    # net_debt, ttm_ebitda, ttm_revenue, ttm_operating_profit, ttm_net_income
    # compute_valuation()'in girdisidir; Ratios uzerinden disari acik olmali.
    # TTM = guncel YTD(_LATEST=2026/3) + gecen yil tam yil(_QOQ_PRIOR=2025/12)
    # - gecen yil ayni donem YTD(_YOY_PRIOR=2025/3) (bkz. _trailing_12m_from_cumulative).
    result = analyze("TEST", _sample_financials())
    r = result.ratios

    assert r.net_debt == Decimal("100")  # finansal borc(300) - nakit(200)
    assert r.ttm_ebitda == Decimal("30") + Decimal("36") - Decimal("20")  # 46
    assert r.ttm_revenue == Decimal("120") + Decimal("140") - Decimal("100")  # 160
    assert r.ttm_operating_profit == Decimal("20") + Decimal("25") - Decimal("12")  # 33
    assert r.ttm_net_income == Decimal("15") + Decimal("18") - Decimal("-5")  # 38


def test_analyze_cari_oran_ve_borc_ozkaynak() -> None:
    result = analyze("TEST", _sample_financials())
    assert result.ratios.current_ratio == Decimal("500") / Decimal("250") == Decimal("2")
    assert result.ratios.debt_to_equity == Decimal("300") / Decimal("400") == Decimal("0.75")


def test_analyze_roe_yillikandirilmis_ttm() -> None:
    result = analyze("TEST", _sample_financials())
    # TTM net kar = 15+18-(-5) = 38; ROE = 38/400*100
    assert result.ratios.roe_annualized == Decimal("38") / Decimal("400") * 100


def test_analyze_ceyreklik_seri_eskiden_yeniye_5_donem() -> None:
    result = analyze("TEST", _sample_financials())
    series = result.quarterly_series

    assert [p.period for p in series] == [_YOY_PRIOR, _TTM_4, _TTM_3, _QOQ_PRIOR, _LATEST]
    assert series[-1].revenue == Decimal("120")  # en yeni donem sirada son
    assert series[0].net_income == Decimal("-5")  # en eski donem sirada ilk


def test_analyze_bulgular_listesi_10_kalem_icerir() -> None:
    result = analyze("TEST", _sample_financials())
    fields = [f.field for f in result.findings]
    assert fields == [
        "revenue",
        "gross_profit",
        "operating_profit",
        "ebitda",
        "net_income",
        "cash",
        "trade_receivables",
        "total_assets",
        "financial_debt",
        "equity",
    ]

    net_income_finding = next(f for f in result.findings if f.field == "net_income")
    assert net_income_finding.comparison == "YoY"
    assert net_income_finding.change_label == ChangeLabel.ZARARDAN_KARA_GECTI

    cash_finding = next(f for f in result.findings if f.field == "cash")
    assert cash_finding.comparison == "QoQ"


# --- analyze(): kenar durumlari -----------------------------------------------------


def test_analyze_banka_sigorta_amortisman_yoksa_favok_gizlenir() -> None:
    financials = _sample_financials()
    for period_data in financials.values():
        period_data.pop("depreciation_amortization", None)
        period_data.pop("depreciation_amortization_cum", None)

    result = analyze("BANKATEST", financials)

    assert result.income_statement.ebitda is None
    assert result.ratios.ebitda_margin_current is None
    assert result.ratios.net_debt_to_ebitda is None
    assert "ebitda" not in [f.field for f in result.findings]


def test_analyze_eksik_yoy_donemi_veri_yok_doner() -> None:
    financials = _sample_financials()
    del financials[_YOY_PRIOR]  # sirket 1 yil once henuz veri saglamamis olabilir

    result = analyze("TEST", financials)

    assert result.income_statement.revenue.comparison is None
    assert result.income_statement.revenue.change_label == ChangeLabel.VERI_YOK


def test_analyze_tek_donemlik_veri_cokmeden_calisir() -> None:
    financials = {_LATEST: _sample_financials()[_LATEST]}

    result = analyze("TEST", financials)

    assert result.latest_period == _LATEST
    assert result.income_statement.revenue.comparison is None
    assert result.ratios.net_debt_to_ebitda is None  # TTM icin 4 donem yok
    assert len(result.quarterly_series) == 1


def test_analyze_bos_sozluk_hata_firlatir() -> None:
    with pytest.raises(ValueError):
        analyze("TEST", {})


# --- compute_valuation() -----------------------------------------------------


def test_compute_valuation_fiyat_ve_sermaye_ile_tam_hesap() -> None:
    result = analyze("TEST", _sample_financials())
    val = compute_valuation(result, price=Decimal("10"), share_capital=Decimal("1000"))

    assert val is not None
    assert val.market_cap == Decimal("10000")  # 10 x 1000
    assert val.net_debt == Decimal("100")
    assert val.enterprise_value == Decimal("10100")  # 10000 + 100
    assert val.pe_ratio == Decimal("10000") / Decimal("38")
    assert val.pb_ratio == Decimal("10000") / Decimal("400")  # guncel ozkaynak
    assert val.ev_ebitda == Decimal("10100") / Decimal("46")
    assert val.ev_revenue == Decimal("10100") / Decimal("160")
    assert val.price_to_operating_profit == Decimal("10000") / Decimal("33")


def test_compute_valuation_fiyat_yoksa_none() -> None:
    result = analyze("TEST", _sample_financials())
    assert compute_valuation(result, price=None, share_capital=Decimal("1000")) is None


def test_compute_valuation_sermaye_yoksa_none() -> None:
    result = analyze("TEST", _sample_financials())
    assert compute_valuation(result, price=Decimal("10"), share_capital=None) is None


def test_compute_valuation_ttm_eksikse_carpanlar_none_ama_market_cap_dolu() -> None:
    # Tek donemlik veri -- TTM toplamlari (4 ceyrek gerektirir) None doner,
    # ama piyasa degeri/net borc/PD-DD icin TTM gerekmedigi icin doludur.
    financials = {_LATEST: _sample_financials()[_LATEST]}
    result = analyze("TEST", financials)
    val = compute_valuation(result, price=Decimal("10"), share_capital=Decimal("1000"))

    assert val is not None
    assert val.market_cap == Decimal("10000")
    assert val.pb_ratio == Decimal("10000") / Decimal("400")
    assert val.pe_ratio is None  # ttm_net_income yok
    assert val.ev_ebitda is None  # ttm_ebitda yok
    assert val.ev_revenue is None  # ttm_revenue yok
    assert val.price_to_operating_profit is None  # ttm_operating_profit yok


# --- analyze_bank() / compute_valuation_bank() (banka/UFRS) -----------------------------------------------------
#
# GARAN canli verisiyle mertebe olarak tutarli, elle hesaplanmis kucuk
# rakamlarla: gercek YoY/QoQ/TTM formullerini dogrular (bkz. dosya ust notu).


def _bank_donem(interest_income, interest_expense, net_fee_income, net_operating_profit, net_income,
                 loans=None, deposits=None, provisions=None, total_assets=None, equity=None) -> dict:
    d = {
        "interest_income": Decimal(interest_income), "interest_income_cum": Decimal(interest_income),
        "interest_expense": Decimal(interest_expense), "interest_expense_cum": Decimal(interest_expense),
        "net_fee_income": Decimal(net_fee_income), "net_fee_income_cum": Decimal(net_fee_income),
        "net_operating_profit": Decimal(net_operating_profit), "net_operating_profit_cum": Decimal(net_operating_profit),
        "net_income": Decimal(net_income), "net_income_cum": Decimal(net_income),
    }
    if loans is not None:
        d["loans"] = Decimal(loans)
    if deposits is not None:
        d["deposits"] = Decimal(deposits)
    if provisions is not None:
        d["provisions"] = Decimal(provisions)
    if total_assets is not None:
        d["total_assets"] = Decimal(total_assets)
    if equity is not None:
        d["equity"] = Decimal(equity)
    return d


_BANK_LATEST = (2026, 6)
_BANK_YOY_PRIOR = (2025, 6)
_BANK_QOQ_PRIOR = (2026, 3)


def _sample_bank_financials() -> dict:
    return {
        _BANK_LATEST: _bank_donem(
            412, -294, 88, 64, 64, loans=2625, deposits=3020, provisions=0, total_assets=4412, equity=487
        ),
        _BANK_QOQ_PRIOR: _bank_donem(200, -140, 44, 30, 31, loans=2437, deposits=2710, total_assets=4017, equity=451),
        _BANK_YOY_PRIOR: _bank_donem(329, -266, 64, 54, 54, loans=2200, deposits=2700, total_assets=3800, equity=400),
    }


def test_analyze_bank_gelir_tablosu_yoy() -> None:
    result = analyze_bank("GARAN", _sample_bank_financials())

    assert result.income_statement.interest_income.current == Decimal("412")
    assert result.income_statement.interest_income.comparison == Decimal("329")
    assert result.income_statement.interest_income.percent_change == pct(412, 329)


def test_analyze_bank_interest_expense_negatif_deger_class() -> None:
    """Faiz Giderleri fetcher katmaninda ZATEN negatiflenmis olarak gelir
    (bkz. isyatirim.standardized_value_ufrs); analyze_bank bunu OLDUGU GIBI
    tasir, tekrar isaret DEGISTIRMEZ."""
    result = analyze_bank("GARAN", _sample_bank_financials())
    assert result.income_statement.interest_expense.current == Decimal("-294")


def test_analyze_bank_bilanco_qoq() -> None:
    result = analyze_bank("GARAN", _sample_bank_financials())
    assert result.balance_sheet.loans.current == Decimal("2625")
    assert result.balance_sheet.loans.comparison == Decimal("2437")


def test_analyze_bank_katilim_varyanti_etiketleri_degistirir() -> None:
    """bank_variant='participation' (katilim bankasi, orn. ALBRK) SADECE
    Faiz Gelirleri/Giderleri ve Mevduat etiketlerini degistirir -- degerler
    ayni sekilde hesaplanir."""
    result = analyze_bank("ALBRK", _sample_bank_financials(), bank_variant="participation")
    assert result.income_statement.interest_income.label_tr == "Kâr Payı Gelirleri"
    assert result.income_statement.interest_expense.label_tr == "Kâr Payı Giderleri"
    assert result.balance_sheet.deposits.label_tr == "Toplanan Fonlar"
    # Deger HESABI degismedi.
    assert result.income_statement.interest_income.current == Decimal("412")


def test_analyze_bank_konvansiyonel_varsayilan_etiketler() -> None:
    result = analyze_bank("GARAN", _sample_bank_financials())
    assert result.income_statement.interest_income.label_tr == "Faiz Gelirleri"
    assert result.balance_sheet.deposits.label_tr == "Mevduatlar"
    assert result.balance_sheet.equity.current == Decimal("487")


def test_analyze_bank_no_gross_profit_veya_ebitda_kavrami_yok() -> None:
    """BankIncomeStatementSummary sanayi alanlarini (gross_profit/ebitda)
    HIC ICERMEZ -- ayri bir veri modeli oldugunu dogrular."""
    result = analyze_bank("GARAN", _sample_bank_financials())
    assert not hasattr(result.income_statement, "gross_profit")
    assert not hasattr(result.income_statement, "ebitda")


def test_analyze_bank_ratios_roe_ve_nim_yaklasik() -> None:
    result = analyze_bank("GARAN", _sample_bank_financials())
    r = result.ratios
    # roe_annualized = TTM net kar / guncel ozkaynak * 100 -- sadece 3 donem
    # var (TTM icin 4 gerekir), bu yuzden None beklenir.
    assert r.ttm_net_income is None
    assert r.roe_annualized is None


def test_analyze_bank_ratios_roa_ve_ozkaynak_aktif_orani() -> None:
    """return_on_assets_annualized = TTM net kar / guncel toplam varlik * 100
    (CAMELS 'Earnings' -- NIM ile birlikte onerilir). equity_to_assets_current
    = guncel ozkaynak / guncel toplam varlik * 100 (regulatuar Sermaye
    Yeterlilik Orani'nin YERINE GECMEYEN, TAMAMEN hesaplanabilir bir
    kaldirac/sermaye gucu yaklasimi -- bkz. scorer.score_bank docstring'i)."""
    financials = {
        _BANK_LATEST: _sample_bank_financials()[_BANK_LATEST],
        (2026, 3): _sample_bank_financials()[_BANK_QOQ_PRIOR],
        (2025, 12): _bank_donem(180, -120, 40, 28, 28, total_assets=4100),
        (2025, 9): _bank_donem(160, -110, 36, 25, 25, total_assets=4000),
        _BANK_YOY_PRIOR: _sample_bank_financials()[_BANK_YOY_PRIOR],
    }
    result = analyze_bank("GARAN", financials)
    r = result.ratios

    # TTM = guncel YTD(2026/6=64) + gecen yil tam yil(2025/12=28) -
    # gecen yil ayni donem YTD(2025/6=54) = 38 (bkz. _trailing_12m_from_cumulative)
    ttm_net_income = Decimal("64") + Decimal("28") - Decimal("54")
    assert r.ttm_net_income == ttm_net_income
    assert r.return_on_assets_annualized == ttm_net_income / Decimal("4412") * 100
    assert r.equity_to_assets_current == Decimal("487") / Decimal("4412") * 100


def test_analyze_bank_bos_sozluk_hata_firlatir() -> None:
    with pytest.raises(ValueError):
        analyze_bank("GARAN", {})


def test_analyze_bank_tek_donem_cokmeden_calisir() -> None:
    financials = {_BANK_LATEST: _sample_bank_financials()[_BANK_LATEST]}
    result = analyze_bank("GARAN", financials)
    assert result.latest_period == _BANK_LATEST
    assert result.income_statement.interest_income.comparison is None
    assert len(result.quarterly_series) == 1


def test_compute_valuation_bank_fk_pddd_hesaplar() -> None:
    financials = {
        _BANK_LATEST: _sample_bank_financials()[_BANK_LATEST],
        (2026, 3): _sample_bank_financials()[_BANK_QOQ_PRIOR],
        (2025, 12): _bank_donem(180, -120, 40, 28, 28, equity=440),
        (2025, 9): _bank_donem(160, -110, 36, 25, 25, equity=420),
        _BANK_YOY_PRIOR: _sample_bank_financials()[_BANK_YOY_PRIOR],
    }
    result = analyze_bank("GARAN", financials)
    val = compute_valuation_bank(result, price=Decimal("126.30"), share_capital=Decimal("4200"))

    assert val is not None
    assert val.market_cap == Decimal("126.30") * Decimal("4200")
    ttm_net_income = Decimal("64") + Decimal("28") - Decimal("54")
    assert val.pe_ratio == val.market_cap / ttm_net_income
    assert val.pb_ratio == val.market_cap / Decimal("487")


def test_compute_valuation_bank_no_ev_carpanlari() -> None:
    """compute_valuation_bank BILEREK FD/FAVOK, FD/Hasilat, PD/EFK
    URETMEZ -- BankValuationMetrics'te bu alanlar HIC YOKTUR (bkz.
    docstring: bankalar EV/EBITDA ile degerlendirilmez)."""
    result = analyze_bank("GARAN", _sample_bank_financials())
    val = compute_valuation_bank(result, price=Decimal("126.30"), share_capital=Decimal("4200"))
    assert not hasattr(val, "ev_ebitda")
    assert not hasattr(val, "net_debt")


def test_compute_valuation_bank_fiyat_yoksa_none() -> None:
    result = analyze_bank("GARAN", _sample_bank_financials())
    assert compute_valuation_bank(result, price=None, share_capital=Decimal("4200")) is None


# --- analyze_insurance() / compute_valuation_insurance() (sigorta/UFRS_K) -----------------------------------------------------
#
# ANSGR canli verisiyle mertebe olarak tutarli, elle hesaplanmis kucuk
# rakamlarla: gercek YoY/QoQ/TTM formullerini dogrular.


def _insurance_donem(gross_written_premiums, net_premiums_earned, technical_income, technical_balance, net_income,
                      cash_and_financial_assets=None, receivables=None, provisions=None, payables=None, equity=None) -> dict:
    d = {
        "gross_written_premiums": Decimal(gross_written_premiums), "gross_written_premiums_cum": Decimal(gross_written_premiums),
        "net_premiums_earned": Decimal(net_premiums_earned), "net_premiums_earned_cum": Decimal(net_premiums_earned),
        "technical_income": Decimal(technical_income), "technical_income_cum": Decimal(technical_income),
        "technical_balance": Decimal(technical_balance), "technical_balance_cum": Decimal(technical_balance),
        "net_income": Decimal(net_income), "net_income_cum": Decimal(net_income),
    }
    if cash_and_financial_assets is not None:
        d["cash_and_financial_assets"] = Decimal(cash_and_financial_assets)
    if receivables is not None:
        d["receivables_from_operations"] = Decimal(receivables)
    if provisions is not None:
        d["technical_provisions"] = Decimal(provisions)
    if payables is not None:
        d["payables_from_operations"] = Decimal(payables)
    if equity is not None:
        d["equity"] = Decimal(equity)
    return d


_INS_LATEST = (2026, 6)
_INS_YOY_PRIOR = (2025, 6)
_INS_QOQ_PRIOR = (2026, 3)


def _sample_insurance_financials() -> dict:
    return {
        _INS_LATEST: _insurance_donem(
            54190, 41664, 54903, 9301, 7397,
            cash_and_financial_assets=99868, receivables=27212, provisions=84812, payables=14703, equity=40046,
        ),
        _INS_QOQ_PRIOR: _insurance_donem(
            25000, 20000, 26000, 4500, 3500,
            cash_and_financial_assets=95000, receivables=25000, payables=14000, equity=37000,
        ),
        _INS_YOY_PRIOR: _insurance_donem(
            44469, 33738, 37827, 6673, 5220,
            cash_and_financial_assets=85000, receivables=22000, payables=12000, equity=32000,
        ),
    }


def test_analyze_insurance_gelir_tablosu_yoy() -> None:
    result = analyze_insurance("ANSGR", _sample_insurance_financials())
    assert result.income_statement.gross_written_premiums.current == Decimal("54190")
    assert result.income_statement.gross_written_premiums.comparison == Decimal("44469")
    assert result.income_statement.gross_written_premiums.percent_change == pct(54190, 44469)


def test_analyze_insurance_bilanco_qoq() -> None:
    result = analyze_insurance("ANSGR", _sample_insurance_financials())
    assert result.balance_sheet.equity.current == Decimal("40046")
    assert result.balance_sheet.equity.comparison == Decimal("37000")


def test_analyze_insurance_no_gross_profit_kavrami_yok() -> None:
    """InsuranceIncomeStatementSummary sanayi/banka alanlarini HIC ICERMEZ."""
    result = analyze_insurance("ANSGR", _sample_insurance_financials())
    assert not hasattr(result.income_statement, "gross_profit")
    assert not hasattr(result.income_statement, "interest_income")


def test_analyze_insurance_teknik_denge_marji() -> None:
    result = analyze_insurance("ANSGR", _sample_insurance_financials())
    # 9301 / 54903 * 100
    assert result.ratios.technical_balance_margin_current == (Decimal("9301") / Decimal("54903")) * 100


def test_analyze_insurance_bos_sozluk_hata_firlatir() -> None:
    with pytest.raises(ValueError):
        analyze_insurance("ANSGR", {})


def test_analyze_insurance_tek_donem_cokmeden_calisir() -> None:
    financials = {_INS_LATEST: _sample_insurance_financials()[_INS_LATEST]}
    result = analyze_insurance("ANSGR", financials)
    assert result.latest_period == _INS_LATEST
    assert result.income_statement.gross_written_premiums.comparison is None
    assert len(result.quarterly_series) == 1


def test_compute_valuation_insurance_fk_pddd_hesaplar() -> None:
    financials = {
        _INS_LATEST: _sample_insurance_financials()[_INS_LATEST],
        (2026, 3): _sample_insurance_financials()[_INS_QOQ_PRIOR],
        (2025, 12): _insurance_donem(24000, 19000, 25000, 4200, 3200),
        (2025, 9): _insurance_donem(23000, 18000, 24000, 4000, 3000),
        _INS_YOY_PRIOR: _sample_insurance_financials()[_INS_YOY_PRIOR],
    }
    result = analyze_insurance("ANSGR", financials)
    val = compute_valuation_insurance(result, price=Decimal("27.18"), share_capital=Decimal("2000"))

    assert val is not None
    assert val.market_cap == Decimal("27.18") * Decimal("2000")
    # TTM = guncel YTD(2026/6=7397) + gecen yil tam yil(2025/12=3200) -
    # gecen yil ayni donem YTD(2025/6=5220) = 5377
    ttm_net_income = Decimal("7397") + Decimal("3200") - Decimal("5220")
    assert val.pe_ratio == val.market_cap / ttm_net_income
    assert val.pb_ratio == val.market_cap / Decimal("40046")


def test_compute_valuation_insurance_no_ev_carpanlari() -> None:
    result = analyze_insurance("ANSGR", _sample_insurance_financials())
    val = compute_valuation_insurance(result, price=Decimal("27.18"), share_capital=Decimal("2000"))
    assert not hasattr(val, "ev_ebitda")
    assert not hasattr(val, "net_debt")


def test_compute_valuation_insurance_fiyat_yoksa_none() -> None:
    result = analyze_insurance("ANSGR", _sample_insurance_financials())
    assert compute_valuation_insurance(result, price=None, share_capital=Decimal("2000")) is None
