"""src/fetchers/stockanalysis.py testleri: gomulu JS veri blobu ayristirma
mantigi (saf, ag GEREKTIRMEZ) + fetch_quarterly_income() ic HTTP cagrisinin
monkeypatch ile izole edilmis hali (bkz. test_sec_edgar.py/test_kap_financials.py
ile AYNI ilke -- proje testlerinde gercek ag istegi ATILMAZ, Kural 11)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.fetchers import stockanalysis

# Gercek stockanalysis.com sayfasindan (2026-08-03, ASTS) CANLI gozlemlenen
# bicimi taklit eder -- kesif scripti (scripts/explore_stockanalysis.py) ile
# dogrulandi (bkz. data/exploration/STOCKANALYSIS_ozet_*.txt).
_ORNEK_HTML = (
    '<html><body><script>{"props":{"page":{"id":"epsdil",title:"EPS"}],'
    'data:{datekey:["2026-03-31","2025-12-31","2023-12-31"],'
    'fiscalYear:["2026","2025","2023"],fiscalQuarter:["Q1","Q4","Q4"],'
    'revenue:[14735000,54305000,null],gp:[3086000,54305000,null],'
    'opinc:[-149412000,-42864000,-60878000],'
    'netinccmn:[-191012000,-73966000,-31926000],epsdil:[-0.7,-0.3,-0.2]}}'
    "</script></body></html>"
)


def test_parse_quarterly_blob_temel_alanlari_dogru_cikartir() -> None:
    snapshots = stockanalysis._parse_quarterly_blob(_ORNEK_HTML, "ASTS")
    assert len(snapshots) == 3

    q1_2026 = snapshots[0]
    assert q1_2026.period == (2026, 3)
    assert q1_2026.revenue == Decimal("14735000")
    assert q1_2026.gross_profit == Decimal("3086000")
    assert q1_2026.operating_profit == Decimal("-149412000")
    assert q1_2026.net_income == Decimal("-191012000")


def test_parse_quarterly_blob_null_degerler_none_olur() -> None:
    snapshots = stockanalysis._parse_quarterly_blob(_ORNEK_HTML, "ASTS")
    eski_donem = next(s for s in snapshots if s.period == (2023, 12))
    assert eski_donem.revenue is None
    assert eski_donem.gross_profit is None
    assert eski_donem.operating_profit == Decimal("-60878000")  # bu alan doluydu


def test_parse_quarterly_blob_donem_ceyrek_sonu_tarihinden_turetilir() -> None:
    """datekey'in KENDI ay/yilindan (fiscalQuarter ETIKETINE GUVENMEDEN --
    takvim disi mali yili olan sirketlerde etiket YANILTICI olabilir, bkz.
    sec_edgar.py modul notu) period (yil, ceyrek_sonu_ayi) turetilir."""
    snapshots = stockanalysis._parse_quarterly_blob(_ORNEK_HTML, "ASTS")
    assert snapshots[1].period == (2025, 12)


def test_parse_quarterly_blob_veri_blogu_bulunamazsa_hata_firlatir() -> None:
    with pytest.raises(stockanalysis.StockAnalysisParseError):
        stockanalysis._parse_quarterly_blob("<html><body>bos sayfa</body></html>", "ASTS")


def test_parse_quarterly_blob_dizi_uzunluklari_uyusmazsa_hata_firlatir() -> None:
    bozuk_html = (
        "<script>data:{datekey:[\"2026-03-31\",\"2025-12-31\"],"
        "revenue:[14735000],gp:[3086000,54305000],"
        "opinc:[-149412000,-42864000],netinccmn:[-191012000,-73966000]}}</script>"
    )
    with pytest.raises(stockanalysis.StockAnalysisParseError):
        stockanalysis._parse_quarterly_blob(bozuk_html, "ASTS")


def test_extract_array_field_bulunamazsa_none_doner() -> None:
    assert stockanalysis._extract_array_field("data:{datekey:[1,2]}", "gp") is None


# --- fetch_quarterly_income (HTTP katmani monkeypatch ile izole edilir) -----------------------------------------------------


def test_fetch_quarterly_income_html_alip_ayristirir(monkeypatch) -> None:
    monkeypatch.setattr(stockanalysis, "_fetch_page_html", lambda ticker: _ORNEK_HTML)
    snapshots = stockanalysis.fetch_quarterly_income("asts")
    assert snapshots[0].period == (2026, 3)
    assert snapshots[0].revenue == Decimal("14735000")


def test_fetch_quarterly_income_ticker_normalize_edilir(monkeypatch) -> None:
    gonderilen: list[str] = []

    def sahte_fetch(ticker: str) -> str:
        gonderilen.append(ticker)
        return _ORNEK_HTML

    monkeypatch.setattr(stockanalysis, "_fetch_page_html", sahte_fetch)
    stockanalysis.fetch_quarterly_income("  asts  ")
    assert gonderilen == ["ASTS"]


def test_fetch_quarterly_income_ag_hatasi_yukari_firlatilir(monkeypatch) -> None:
    def patlayan_fetch(ticker: str) -> str:
        raise stockanalysis.StockAnalysisNetworkError("baglanti hatasi")

    monkeypatch.setattr(stockanalysis, "_fetch_page_html", patlayan_fetch)
    with pytest.raises(stockanalysis.StockAnalysisNetworkError):
        stockanalysis.fetch_quarterly_income("ASTS")
