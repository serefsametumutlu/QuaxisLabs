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
