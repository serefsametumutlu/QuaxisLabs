"""Faz 10 teslim kriteri: calculator.analyze_us() testleri.

analyze_us(), analyze() ile AYNI _build_analysis_result() cekirdegini
kullanir (bkz. calculator.py modul ici not) -- YoY/QoQ/TTM formullerinin
KENDISI zaten test_calculator.py'de (70 test) dogrulandi, burada TEKRAR
edilmez. Bu dosya SADECE analyze_us()'e OZGU davranisi test eder:
  1. currency='USD' doner (analyze() 'TRY' doner -- regresyon kilidi).
  2. US GAAP alan adlarindan (pipeline._standardize_to_records_us_gaap ile
     AYNI sekil) dogru bir AnalysisResult uretilir.
"""

from __future__ import annotations

from decimal import Decimal

from src.analysis.calculator import analyze, analyze_us

_LATEST = (2026, 9)
_YOY_PRIOR = (2025, 9)
_QOQ_PRIOR = (2026, 6)


def _sample_us_financials() -> dict:
    return {
        _LATEST: {
            "revenue": Decimal("364357000000"),
            "revenue_cum": Decimal("364357000000"),
            "gross_profit": Decimal("178782000000"),
            "gross_profit_cum": Decimal("178782000000"),
            "operating_profit": Decimal("122356000000"),
            "operating_profit_cum": Decimal("122356000000"),
            # Faz 10 (bkz. pipeline._standardize_to_records_us_gaap): US_GAAP'te
            # dar/genis ayrimi YOK, "ebitda_base" operating_profit ile AYNI yazilir.
            "operating_profit_ebitda_base": Decimal("122356000000"),
            "operating_profit_ebitda_base_cum": Decimal("122356000000"),
            "depreciation_amortization": Decimal("10049000000"),
            "depreciation_amortization_cum": Decimal("10049000000"),
            "net_income": Decimal("101453000000"),
            "net_income_cum": Decimal("101453000000"),
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
            "revenue": Decimal("313695000000"),
            "revenue_cum": Decimal("313695000000"),
            "gross_profit": Decimal("146860000000"),
            "gross_profit_cum": Decimal("146860000000"),
            "operating_profit": Decimal("100600000000"),
            "operating_profit_cum": Decimal("100600000000"),
            "operating_profit_ebitda_base": Decimal("100600000000"),
            "operating_profit_ebitda_base_cum": Decimal("100600000000"),
            "depreciation_amortization": Decimal("8594000000"),
            "depreciation_amortization_cum": Decimal("8594000000"),
            "net_income": Decimal("84509000000"),
            "net_income_cum": Decimal("84509000000"),
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


def test_analyze_us_gelir_tablosu_dogru_hesaplanir() -> None:
    result = analyze_us("AAPL", _sample_us_financials())
    assert result.income_statement.revenue.current == Decimal("364357000000")
    assert result.income_statement.revenue.comparison == Decimal("313695000000")
    assert result.income_statement.net_income.current == Decimal("101453000000")


def test_analyze_us_favok_ebitda_base_ile_ayni_deger_uzerinden_hesaplanir() -> None:
    # bkz. pipeline._standardize_to_records_us_gaap ust notu: US GAAP'te
    # operating_profit_ebitda_base == operating_profit (dar/genis ayrimi yok).
    result = analyze_us("AAPL", _sample_us_financials())
    assert result.income_statement.ebitda is not None
    assert result.income_statement.ebitda.current == Decimal("122356000000") + Decimal("10049000000")


def test_analyze_us_ticker_ve_latest_period_dogru() -> None:
    result = analyze_us("AAPL", _sample_us_financials())
    assert result.ticker == "AAPL"
    assert result.latest_period == _LATEST
