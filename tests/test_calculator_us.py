"""Faz 10 teslim kriteri: calculator.analyze_us() testleri.

analyze_us(), analyze() ile AYNI _build_analysis_result() cekirdegini
kullanir (bkz. calculator.py modul ici not) -- YoY/QoQ/TTM formullerinin
KENDISI zaten test_calculator.py'de (70 test) dogrulandi, burada TEKRAR
edilmez. Bu dosya SADECE analyze_us()'e OZGU davranisi test eder:
  1. currency='USD' doner (analyze() 'TRY' doner -- regresyon kilidi).
  2. GELIR TABLOSU/bulgu listesi KUMULATIF (YTD) DEGIL, TEK CEYREKLIK
     rakam gosterir (analyze()'nin TERSI -- bkz. asagidaki kritik test).
  3. US GAAP alan adlarindan (pipeline._standardize_to_records_us_gaap ile
     AYNI sekil) dogru bir AnalysisResult uretilir.

Asagidaki rakamlar UYDURULMADI -- AAPL'in GERCEK SEC EDGAR verisinden
(2026-08-02 canli cekildi, bkz. src/fetchers/sec_edgar.py) alindi VE
kullanicinin paylastigi bagimsiz bir "earnings highlights" kaynagiyla
CAPRAZ dogrulandi: Hasilat $109,42 mr (bizim $109,417 mr), Net Kar $29,79 mr
(bizim $29,789 mr), Brut Kar $54,77 mr (bizim $54,770 mr) -- ucu de
BIREBIR/kurus farkiyla eslesti.
"""

from __future__ import annotations

from decimal import Decimal

from src.analysis.calculator import analyze, analyze_us

_LATEST = (2026, 9)  # AAPL mali yil 2026, Ç3 (fiscal Ç3 = takvim Mart 29 - Haz 27, 2026)
_YOY_PRIOR = (2025, 9)
_QOQ_PRIOR = (2026, 6)


def _sample_us_financials() -> dict:
    return {
        _LATEST: {
            # KUMULATIF (9 aylik, YTD) ve TEK CEYREKLIK degerler KASITLI
            # olarak FARKLI -- gercek AAPL Ç3 FY2026 verisi (canli SEC EDGAR
            # dogrulamasi): ceyreklik $109,417 mr, kumulatif $364,357 mr.
            "revenue": Decimal("109417000000"),
            "revenue_cum": Decimal("364357000000"),
            "gross_profit": Decimal("54770000000"),
            "gross_profit_cum": Decimal("178782000000"),
            "operating_profit": Decimal("35695000000"),
            "operating_profit_cum": Decimal("122432000000"),
            # Faz 10 (bkz. pipeline._standardize_to_records_us_gaap): US_GAAP'te
            # dar/genis ayrimi YOK, "ebitda_base" operating_profit ile AYNI yazilir.
            "operating_profit_ebitda_base": Decimal("35695000000"),
            "operating_profit_ebitda_base_cum": Decimal("122432000000"),
            "depreciation_amortization": Decimal("3320000000"),
            "depreciation_amortization_cum": Decimal("9973000000"),
            "net_income": Decimal("29789000000"),
            "net_income_cum": Decimal("101464000000"),
            "cash": Decimal("39544000000"),
            "trade_receivables": Decimal("31398000000"),
            "total_assets": Decimal("383266000000"),
            "financial_debt": Decimal("82347000000"),
            "equity": Decimal("107520000000"),
            "current_assets": Decimal("149818000000"),
            "short_term_liabilities": Decimal("149294000000"),
            "shares_outstanding": Decimal("14594180000"),
        },
        _YOY_PRIOR: {
            "revenue": Decimal("94036000000"),
            "revenue_cum": Decimal("313695000000"),
            "gross_profit": Decimal("43718000000"),
            "gross_profit_cum": Decimal("146860000000"),
            "operating_profit": Decimal("28202000000"),
            "operating_profit_cum": Decimal("100623000000"),
            "operating_profit_ebitda_base": Decimal("28202000000"),
            "operating_profit_ebitda_base_cum": Decimal("100623000000"),
            "depreciation_amortization": Decimal("2830000000"),
            "depreciation_amortization_cum": Decimal("8571000000"),
            "net_income": Decimal("23434000000"),
            "net_income_cum": Decimal("84544000000"),
            "cash": Decimal("35934000000"),
            "trade_receivables": Decimal("29508000000"),
            "total_assets": Decimal("359241000000"),
            "financial_debt": Decimal("90678000000"),
            "equity": Decimal("73733000000"),
        },
        _QOQ_PRIOR: {
            "cash": Decimal("45572000000"),
            "trade_receivables": Decimal("30300000000"),
            "total_assets": Decimal("371082000000"),
            "financial_debt": Decimal("82714000000"),
            "equity": Decimal("106491000000"),
            "current_assets": Decimal("144114000000"),
        },
    }


def test_analyze_us_currency_usd_doner() -> None:
    result = analyze_us("AAPL", _sample_us_financials())
    assert result.currency == "USD"


def test_analyze_currency_try_varsayilan_kalir() -> None:
    # Regresyon kilidi: currency alani eklenmeden ONCEKI BIST analyze()
    # cagrilari (399 test) davranisi DEGISMEMELI.
    result = analyze("THYAO", {_LATEST: {"revenue": Decimal("100"), "revenue_cum": Decimal("100")}})
    assert result.currency == "TRY"


# --- §B21: is_annual_only (NVO/TSM/SHEL/BABA tipi ADR/20-F sirketleri) -----------------------------------------------------


def test_analyze_us_is_annual_only_normal_ceyreklik_sirkette_false() -> None:
    """AAPL tipi normal 10-Q/10-K sirketi -- periyotlar fiscal_period=9/6
    icerdigi icin is_annual_only False kalmali (regresyon kilidi)."""
    result = analyze_us("AAPL", _sample_us_financials())
    assert result.is_annual_only is False


def test_analyze_us_is_annual_only_tum_donemler_fy_ise_true() -> None:
    """NVO/TSM tipi: financials_by_period'daki TUM donemler (fy, 12) ise
    (bkz. pipeline._standardize_to_records_us_gaap annual-only yazma mantigi)
    is_annual_only True olmali."""
    financials = {
        (2025, 12): {"revenue": Decimal("309064000000"), "revenue_cum": Decimal("309064000000")},
        (2024, 12): {"revenue": Decimal("290403000000"), "revenue_cum": Decimal("290403000000")},
        (2023, 12): {"revenue": Decimal("270000000000"), "revenue_cum": Decimal("270000000000")},
        (2022, 12): {"revenue": Decimal("260000000000"), "revenue_cum": Decimal("260000000000")},
    }
    result = analyze_us("NVO", financials)
    assert result.is_annual_only is True


def test_analyze_us_is_annual_only_eski_izole_donem_tespiti_bozmaz() -> None:
    """B21 -- SADECE en yakin 4 donem penceresine bakilir (bkz. pipeline.py
    ile AYNI ilke): eski/izole bir fp=6 donemi annual-only tespitini
    BOZMAMALI."""
    financials = {
        (2025, 12): {"revenue": Decimal("100")},
        (2024, 12): {"revenue": Decimal("90")},
        (2023, 12): {"revenue": Decimal("80")},
        (2022, 12): {"revenue": Decimal("70")},
        (2020, 6): {"revenue": Decimal("40")},
    }
    result = analyze_us("NVO", financials)
    assert result.is_annual_only is True


def test_analyze_bist_is_annual_only_her_zaman_false() -> None:
    """BIST (XI_29) sirketleri her zaman ceyreklik raporlar -- is_annual_only
    hicbir zaman True OLMAMALI (regresyon kilidi)."""
    result = analyze("THYAO", {_LATEST: {"revenue": Decimal("100"), "revenue_cum": Decimal("100")}})
    assert result.is_annual_only is False


def test_analyze_us_gelir_tablosu_kumulatif_DEGIL_tek_ceyreklik_gosterir() -> None:
    """KRITIK regresyon testi (kullanici raporu, 2026-08-02): analyze_us()
    ONCEDEN BIST gibi KUMULATIF (9 aylik, $364,4 mr) rakam gosteriyordu --
    bu, sosyal medyadaki "tek ceyreklik" earnings-highlight paylasimlariyla
    karsilastirildiginda "yanlis veri" izlenimi yaratti (kullanici $109,42
    mr'lik gercek ceyreklik rakami bekliyordu). Simdi analyze_us() TEK
    CEYREKLIK rakam gosterir -- analyze() (BIST) ise KUMULATIF gostermeye
    devam eder (bkz. test_analyze_bist_gelir_tablosu_kumulatif_gosterir)."""
    result = analyze_us("AAPL", _sample_us_financials())
    assert result.income_statement.revenue.current == Decimal("109417000000")
    assert result.income_statement.revenue.comparison == Decimal("94036000000")
    assert result.income_statement.net_income.current == Decimal("29789000000")
    assert result.income_statement.net_income.comparison == Decimal("23434000000")
    assert result.income_statement.gross_profit.current == Decimal("54770000000")
    assert result.income_statement.operating_profit.current == Decimal("35695000000")


def test_analyze_bist_gelir_tablosu_kumulatif_gosterir() -> None:
    # analyze() (BIST) DAVRANIŞI DEĞİŞMEMELİ -- Fintables/Matriks konvansiyonu
    # geregi KUMULATIF (YTD) gosterir (bkz. test_calculator.py ile AYNI ilke).
    financials = {
        _LATEST: {"revenue": Decimal("100"), "revenue_cum": Decimal("300")},
        _YOY_PRIOR: {"revenue": Decimal("90"), "revenue_cum": Decimal("250")},
    }
    result = analyze("THYAO", financials)
    assert result.income_statement.revenue.current == Decimal("300")


def test_analyze_us_bulgu_listesi_de_tek_ceyreklik_kullanir() -> None:
    result = analyze_us("AAPL", _sample_us_financials())
    revenue_finding = next(f for f in result.findings if f.field == "revenue")
    assert revenue_finding.current == Decimal("109417000000")


def test_analyze_us_ratios_ve_ttm_ceyreklik_alanlari_KULLANMAYA_DEVAM_EDER() -> None:
    # use_cumulative_display bayragi SADECE gorunum tablosunu etkiler --
    # ratios/TTM her zaman ceyreklik alanlari okur (degismedi).
    result = analyze_us("AAPL", _sample_us_financials())
    assert result.ratios.net_margin_current is not None
    beklenen_net_marj = Decimal("29789000000") / Decimal("109417000000") * 100
    assert result.ratios.net_margin_current == beklenen_net_marj


def test_analyze_us_favok_ebitda_base_ile_ayni_deger_uzerinden_hesaplanir() -> None:
    # bkz. pipeline._standardize_to_records_us_gaap ust notu: US GAAP'te
    # operating_profit_ebitda_base == operating_profit (dar/genis ayrimi yok).
    result = analyze_us("AAPL", _sample_us_financials())
    assert result.income_statement.ebitda is not None
    assert result.income_statement.ebitda.current == Decimal("35695000000") + Decimal("3320000000")


def test_analyze_us_ticker_ve_latest_period_dogru() -> None:
    result = analyze_us("AAPL", _sample_us_financials())
    assert result.ticker == "AAPL"
    assert result.latest_period == _LATEST


# --- ttm_depreciation_amortization_override (§B20 -- AMD/TSLA FAVOK N/A duzeltmesi) --------


def _amd_tipi_financials_eksik_da_ile() -> dict:
    """AMD gibi bir sirketi TAKLIT eder: esas faaliyet kari (operating_profit)
    HER donemde eksiksiz, ama 'depreciation_amortization_cum' guncel (kismi
    yil) donemde EKSIK -- bu, standart _trailing_12m_from_cumulative'in
    (ebitda_cum uzerinden) TTM FAVOK'u hesaplayamamasina sebep olur, oysa
    TTM esas faaliyet kari (ttm_operating_profit) SORUNSUZ hesaplanir."""
    latest = (2026, 3)
    prior_year_full = (2025, 12)
    prior_year_same = (2025, 3)
    return {
        latest: {
            "revenue": Decimal("10000000000"),
            "revenue_cum": Decimal("10000000000"),
            "operating_profit": Decimal("1000000000"),
            "operating_profit_cum": Decimal("1000000000"),
            "operating_profit_ebitda_base": Decimal("1000000000"),
            "operating_profit_ebitda_base_cum": Decimal("1000000000"),
            # KASITLI olarak YOK -- AMD'nin Depreciation'inin ceyreklik/YTD
            # kirilimi olmamasiyla AYNI durum.
            "net_income": Decimal("700000000"),
            "net_income_cum": Decimal("700000000"),
            "cash": Decimal("1000000000"),
            "equity": Decimal("5000000000"),
            "current_assets": Decimal("2000000000"),
            "short_term_liabilities": Decimal("1000000000"),
        },
        prior_year_full: {
            "operating_profit_cum": Decimal("3800000000"),
            "operating_profit_ebitda_base_cum": Decimal("3800000000"),
            "depreciation_amortization_cum": Decimal("2700000000"),
            "net_income_cum": Decimal("2600000000"),
        },
        prior_year_same: {
            "operating_profit_cum": Decimal("900000000"),
            "operating_profit_ebitda_base_cum": Decimal("900000000"),
            "depreciation_amortization_cum": Decimal("650000000"),
            "net_income_cum": Decimal("600000000"),
        },
    }


def test_analyze_us_ttm_ebitda_standart_yontemle_basarisiz_olursa_none_doner() -> None:
    """Override VERILMEDEN -- eski davranis KORUNUR (regresyon kilidi):
    D&A'nin guncel donemde eksik olmasi TTM FAVOK'u None birakir."""
    result = analyze_us("AMD", _amd_tipi_financials_eksik_da_ile())
    assert result.ratios.ttm_operating_profit is not None  # bu ETKILENMEDI
    assert result.ratios.ttm_ebitda is None


def test_analyze_us_ttm_ebitda_override_ile_ttm_esas_faaliyet_kariyla_birlestirilir() -> None:
    """§B20 duzeltmesi: standart yontem basarisiz olunca, TTM esas faaliyet
    kari + cagiran tarafin (pipeline.py, sec_edgar.
    trailing_12m_depreciation_amortization_us_gaap) ayrica hesapladigi TTM
    D&A YEDEGI toplanarak TTM FAVOK YINE DE elde edilir."""
    override = Decimal("2800000000")
    result = analyze_us("AMD", _amd_tipi_financials_eksik_da_ile(), ttm_depreciation_amortization_override=override)
    assert result.ratios.ttm_ebitda == result.ratios.ttm_operating_profit + override


def test_analyze_us_ttm_ebitda_override_ttm_operating_profit_yoksa_kullanilmaz() -> None:
    """TTM esas faaliyet kari da hesaplanamiyorsa (orn. onceki yil verisi
    hic yoksa) override tek basina TTM FAVOK URETMEZ -- Kural 8: iki
    taraftan biri eksikken yarim bir TTM uydurulmaz."""
    financials = {(2026, 3): _amd_tipi_financials_eksik_da_ile()[(2026, 3)]}
    result = analyze_us("AMD", financials, ttm_depreciation_amortization_override=Decimal("2800000000"))
    assert result.ratios.ttm_operating_profit is None
    assert result.ratios.ttm_ebitda is None
