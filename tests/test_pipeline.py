"""Faz 7 teslim kriteri (cekirdek akis): src/bot/pipeline.py'nin ham
Is Yatirim verisini standart alanlara cevirme, donem-kaydirma/onerme ve
hata esleme mantiginin testleri.

Gercek ag istegi ATILMAZ -- isyatirim.fetch_financials / kap.search_company /
kap.fetch_disclosures monkeypatch ile sahtelenir. Sahte fetch_financials
GERCEK sozlesmeyi taklit eder (istenen en yeni donem fixture'da yoksa
FinancialDataNotAvailableError firlatir) -- boylece _resolve_raw_financials'in
ILERI DOGRU probe mantigi (bkz. modul docstring'i, TAVHL canli hatasi) gercekci
sekilde test edilir. GEMINI_API_KEY bos birakilarak commentary katmani
deterministik LLM'siz yedek moda zorlanir. Veritabani izole bir tmp_path
SQLite dosyasina yonlendirilir -- gercek data/bilanco_radar.db'ye ASLA
dokunulmaz.
"""

from __future__ import annotations

from pathlib import Path
from decimal import Decimal

import pytest

import config
from src.bot import pipeline
from src.db import models, repository
from src.fetchers import isyatirim, kap, kap_financials, sec_edgar, stockanalysis


# --- Izole DB fixture (repository.get_session()'i tmp_path'e yonlendirir) -----------------------------------------------------


@pytest.fixture()
def izole_db(monkeypatch, tmp_path):
    engine, session_factory = models.create_engine_and_session(f"sqlite:///{tmp_path / 'test_pipeline.db'}")
    models.init_db(engine)
    monkeypatch.setattr(repository, "DefaultSessionLocal", session_factory)
    monkeypatch.setattr(repository, "_default_db_initialized", True)
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")  # commentary'yi deterministik yedek moda zorla
    monkeypatch.setattr(isyatirim, "fetch_latest_price", lambda ticker, lookback_days=10: None)  # ag istegi atma
    # Faz 16.5: _ensure_sector_populated() yeni (sector=None) XI_29 sirketlerinde
    # kap.fetch_sector_map()'i CAGIRIR -- gercek ag istegi atilmasin diye BOS
    # bir harita ile sahtelenir (davranisi ACIKCA test etmek isteyen testler
    # kendi monkeypatch'leriyle EZEBILIR).
    monkeypatch.setattr(kap, "fetch_sector_map", lambda: {})
    return engine


# --- Sahte RawFinancials uretici + gercekci fetch_financials simulatoru -----------------------------------------------------


def _build_fake_raw(ticker: str, values_by_period: dict[tuple[int, int], dict[str, Decimal]]) -> isyatirim.RawFinancials:
    values_by_item_code: dict[str, dict[tuple[int, int], Decimal]] = {}
    for period, field_values in values_by_period.items():
        for field, value in field_values.items():
            std_field = "short_term_financial_debt" if field == "financial_debt" else field
            item_code = isyatirim.STANDARD_ITEM_MAP_XI_29[std_field]
            values_by_item_code.setdefault(item_code, {})[period] = value

    items = {
        code: isyatirim.FinancialItem(item_code=code, description_tr="", values_by_period=vals)
        for code, vals in values_by_item_code.items()
    }
    periods = sorted(values_by_period.keys(), reverse=True)
    return isyatirim.RawFinancials(ticker=ticker, company_code=ticker, financial_group="XI_29", periods=periods, items=items)


def _donem(revenue, gross, op, dep, net, cash, assets, debt, equity, stl) -> dict:
    return {
        "revenue": Decimal(revenue), "gross_profit": Decimal(gross), "operating_profit": Decimal(op),
        "depreciation_amortization": Decimal(dep), "net_income": Decimal(net), "cash": Decimal(cash),
        "total_assets": Decimal(assets), "financial_debt": Decimal(debt), "equity": Decimal(equity),
        "short_term_liabilities": Decimal(stl),
    }


def _fake_raw_saglikli(ticker: str = "TESTAS") -> isyatirim.RawFinancials:
    # Sadece 1. ceyrekler (period=3) kullanilir ki kumulatif->ceyreklik
    # turetme (onceki ceyrek gerektirmez) basit ve dogru kalsin.
    values = {
        (2026, 3): _donem(1200, 500, 350, 60, 260, 400, 5000, 600, 3000, 900),
        (2025, 3): _donem(1000, 400, 260, 55, -80, 300, 4500, 700, 2600, 850),
        (2024, 3): _donem(900, 360, 230, 50, 150, 280, 4200, 650, 2400, 820),
        (2023, 3): _donem(800, 320, 200, 45, 120, 260, 4000, 600, 2200, 800),
    }
    return _build_fake_raw(ticker, values)


def _fixture_has_period(fixture: isyatirim.RawFinancials, period: tuple[int, int]) -> bool:
    return any(period in item.values_by_period for item in fixture.items.values())


def _make_fake_fetch(fixture: isyatirim.RawFinancials, call_log: list | None = None):
    """GERCEK isyatirim.fetch_financials sozlesmesini taklit eder: istenen
    (verilmemisse tahmin edilen) EN YENI donem fixture'da yoksa
    FinancialDataNotAvailableError firlatir; basariliysa sadece istenen VE
    fixture'da GERCEKTEN bulunan donemleri iceren bir RawFinancials doner.
    Bu, _resolve_raw_financials'in ileri-probe mantiginin (bir sonraki
    ceyrek gercekten yoksa basarisiz olmasi gerektigi icin) dogru test
    edilmesi icin sarttir."""

    def fake_fetch(ticker, periods=None, financial_group=None):
        if call_log is not None:
            call_log.append(periods)
        target_periods = periods if periods is not None else isyatirim.guess_last_periods(count=8)
        newest = target_periods[0]
        if not _fixture_has_period(fixture, newest):
            raise isyatirim.FinancialDataNotAvailableError(f"{ticker}: {newest} yok")

        achieved = [p for p in target_periods if _fixture_has_period(fixture, p)]
        items = {
            code: isyatirim.FinancialItem(
                item_code=code,
                description_tr=item.description_tr,
                values_by_period={p: v for p, v in item.values_by_period.items() if p in achieved},
            )
            for code, item in fixture.items.items()
        }
        return isyatirim.RawFinancials(ticker=ticker, company_code=ticker, financial_group=fixture.financial_group, periods=achieved, items=items)

    return fake_fetch


# --- _standardize_to_records -----------------------------------------------------


def test_standardize_to_records_alanlari_dogru_cevirir() -> None:
    raw = _fake_raw_saglikli()
    records = pipeline._standardize_to_records(raw)
    by_key = {(y, p, code): value for (y, p, code, _name, value) in records}

    assert by_key[(2026, 3, "revenue")] == Decimal("1200")
    assert by_key[(2026, 3, "net_income")] == Decimal("260")
    assert by_key[(2026, 3, "total_assets")] == Decimal("5000")
    assert by_key[(2026, 3, "financial_debt")] == Decimal("600")  # short+long (long=0) toplami


def test_standardize_to_records_trade_receivables_uretmez() -> None:
    # STANDARD_ITEM_MAP_XI_29'da yok -- bilinen, kasitli bir bosluk.
    raw = _fake_raw_saglikli()
    records = pipeline._standardize_to_records(raw)
    assert not any(code == "trade_receivables" for (_y, _p, code, _n, _v) in records)


# --- _standardize_to_records_us_gaap (Faz 9 -- NASDAQ) -----------------------------------------------------


def _us_fact(start, end, val, fp, fy) -> sec_edgar.ConceptFact:
    from datetime import date

    return sec_edgar.ConceptFact(
        start=date.fromisoformat(start) if start else None,
        end=date.fromisoformat(end),
        val=Decimal(val),
        form="10-Q",
        fp=fp,
        fy=fy,
        frame=None,
        filed="2026-01-01",
    )


def _fake_raw_us_gaap(ticker: str = "TESTUS") -> sec_edgar.RawUsFinancials:
    # Sadece mali Q1 (fp='Q1') kullanilir ki kumulatif->ceyreklik turetme
    # (onceki ceyrek gerektirmez) basit ve dogru kalsin -- isyatirim
    # testlerindeki _fake_raw_saglikli ile AYNI ilke.
    facts_by_tag = {
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax": [_us_fact("2025-09-28", "2025-12-27", "1200", "Q1", 2026)],
        "us-gaap:GrossProfit": [_us_fact("2025-09-28", "2025-12-27", "500", "Q1", 2026)],
        "us-gaap:OperatingIncomeLoss": [_us_fact("2025-09-28", "2025-12-27", "350", "Q1", 2026)],
        "us-gaap:NetIncomeLoss": [_us_fact("2025-09-28", "2025-12-27", "260", "Q1", 2026)],
        "us-gaap:DepreciationDepletionAndAmortization": [_us_fact("2025-09-28", "2025-12-27", "60", "Q1", 2026)],
        "us-gaap:Assets": [_us_fact(None, "2025-12-27", "5000", "Q1", 2026)],
        "us-gaap:AssetsCurrent": [_us_fact(None, "2025-12-27", "2000", "Q1", 2026)],
        "us-gaap:StockholdersEquity": [_us_fact(None, "2025-12-27", "3000", "Q1", 2026)],
        "us-gaap:CashAndCashEquivalentsAtCarryingValue": [_us_fact(None, "2025-12-27", "400", "Q1", 2026)],
        "us-gaap:LongTermDebtCurrent": [_us_fact(None, "2025-12-27", "200", "Q1", 2026)],
        "us-gaap:LongTermDebtNoncurrent": [_us_fact(None, "2025-12-27", "400", "Q1", 2026)],
        "dei:EntityCommonStockSharesOutstanding": [_us_fact(None, "2025-12-27", "1000000", "Q1", 2026)],
    }
    return sec_edgar.RawUsFinancials(
        ticker=ticker, cik10="0000000000", company_name="Test Inc.", periods=[(2026, 3)], facts_by_tag=facts_by_tag
    )


def test_standardize_to_records_us_gaap_alanlari_dogru_cevirir() -> None:
    raw = _fake_raw_us_gaap()
    records = pipeline._standardize_to_records_us_gaap(raw)
    by_key = {(y, p, code): value for (y, p, code, _name, value) in records}

    assert by_key[(2026, 3, "revenue")] == Decimal("1200")
    assert by_key[(2026, 3, "net_income")] == Decimal("260")
    assert by_key[(2026, 3, "total_assets")] == Decimal("5000")
    assert by_key[(2026, 3, "shares_outstanding")] == Decimal("1000000")
    assert by_key[(2026, 3, "financial_debt")] == Decimal("600")  # kisa (200) + uzun (400) toplami


def test_standardize_to_records_us_gaap_kisa_uzun_borc_bileseni_ayrica_yazilmaz() -> None:
    # BIST XI_29 ile AYNI davranis: sadece bilesik "financial_debt" yazilir.
    raw = _fake_raw_us_gaap()
    records = pipeline._standardize_to_records_us_gaap(raw)
    codes = {code for (_y, _p, code, _n, _v) in records}
    assert "short_term_financial_debt" not in codes
    assert "long_term_financial_debt" not in codes


# --- §B21: annual-only ADR/20-F sirketleri (NVO/TSM/SHEL/BABA tipi) -----------------------------------------------------


def _period_fact(year: int, fiscal_period: int, val: str) -> sec_edgar.ConceptFact:
    from datetime import date

    end_month_day = {3: (3, 31), 6: (6, 30), 9: (9, 30), 12: (12, 31)}[fiscal_period]
    fp_label = {3: "Q1", 6: "Q2", 9: "Q3", 12: "FY"}[fiscal_period]
    return sec_edgar.ConceptFact(
        start=date(year, 1, 1), end=date(year, *end_month_day), val=Decimal(val),
        form="20-F", fp=fp_label, fy=year, frame=None, filed=f"{year}-12-31",
    )


def _fake_raw_annual_only(ticker: str = "NVOTEST", periods=None) -> sec_edgar.RawUsFinancials:
    """NVO/TSM tipi sirket: varsayilan olarak TUM donemler fp='FY' (fiscal_period=12),
    hicbir Q1-Q3 YOK. Her (yil, fiscal_period) icin `year*100+fiscal_period`
    biciminde BENZERSIZ/kolay dogrulanir bir deger uretilir (orn. (2025,12) -> 202512)."""
    periods = periods or [(2025, 12), (2024, 12), (2023, 12), (2022, 12)]
    facts_by_tag: dict[str, list[sec_edgar.ConceptFact]] = {
        "ifrs-full:Revenue": [], "ifrs-full:ProfitLoss": [], "ifrs-full:Assets": [],
    }
    for year, fiscal_period in periods:
        val_base = year * 100 + fiscal_period
        facts_by_tag["ifrs-full:Revenue"].append(_period_fact(year, fiscal_period, str(val_base)))
        facts_by_tag["ifrs-full:ProfitLoss"].append(_period_fact(year, fiscal_period, str(val_base + 1)))
        facts_by_tag["ifrs-full:Assets"].append(_period_fact(year, fiscal_period, str(val_base + 2)))
    return sec_edgar.RawUsFinancials(
        ticker=ticker, cik10="0", company_name="Test ADR A/S", periods=periods, facts_by_tag=facts_by_tag
    )


def test_standardize_to_records_annual_only_guncel_alan_tam_yil_kumulatif_deger_alir() -> None:
    """B21 -- CANLI HATA (BABA ile kesifte bulundu): eskiden annual-only
    sirketlerde ceyreklik turetme (FY - Q3) HER ZAMAN basarisiz oluyordu
    (Q3 hic yok), "guncel" alan surekli None kaliyordu. Artik annual-only
    tespit edilince tam yil kumulatif deger DOGRUDAN "guncel" alana yazilir."""
    raw = _fake_raw_annual_only()
    records = pipeline._standardize_to_records_us_gaap(raw)
    by_key = {(y, p, code): value for (y, p, code, _name, value) in records}

    assert by_key[(2025, 12, "revenue")] == Decimal("202512")
    assert by_key[(2025, 12, "revenue")] == by_key[(2025, 12, "revenue_cum")]
    assert by_key[(2025, 12, "net_income")] == Decimal("202513")
    assert by_key[(2024, 12, "revenue")] == Decimal("202412")  # onceki yil da DOGRU deger tasimali (YoY icin)


def test_standardize_to_records_annual_only_stockanalysis_yedek_hic_cagirilmaz(monkeypatch) -> None:
    """B21 -- CANLI HATA (BABA): stockanalysis.com'un TAKVIM CEYREGI bazli
    verisi, annual-only bir sirketin mali YIL bazli (fy,fp) anahtariyla
    YANLIS eslesip TAMAMEN ILGISIZ bir rakami "guncel" gibi gosteriyordu.
    Bu yuzden annual-only sirketlerde yedek yolu HIC DENENMEMELI -- ceri
    (revenue tag'i EKSIK birakilarak yedek_gerekli tetiklenmeye CALISILIR,
    yine de _stockanalysis_yedek_veri cagrilmamali)."""
    raw = _fake_raw_annual_only()
    del raw.facts_by_tag["ifrs-full:Revenue"]  # yedek_gerekli tetiklenmeye calisilsin diye

    def patlayan_yedek(ticker):
        raise AssertionError("annual-only sirkette stockanalysis yedegi COK cagirilmamaliydi")

    monkeypatch.setattr(pipeline, "_stockanalysis_yedek_veri", patlayan_yedek)
    records = pipeline._standardize_to_records_us_gaap(raw)  # patlamamali
    by_key = {(y, p, code) for (y, p, code, _name, _v) in records}
    assert (2025, 12, "revenue") not in by_key  # veri gercekten yok, uydurulmadi


def test_standardize_to_records_annual_only_eski_izole_ceyreklik_fact_yanlissiz_saymaz() -> None:
    """B21 -- CANLI HATA (BABA): 2020'den kalma TEK bir izole fp='Q2' fact'i
    (SEC fy/fp etiketleme tuhafligi/eski bir gecis donemi dosyalamasi
    olabilir) annual-only tespitini BOZUYORDU (tum donem GECMISINE bakildigi
    icin). Artik SADECE en yakin 4 donem penceresine bakildigindan bu eski
    anomali annual-only siniflandirmasini ETKILEMEMELI."""
    periods = [(2025, 12), (2024, 12), (2023, 12), (2022, 12), (2020, 6)]
    raw = _fake_raw_annual_only(periods=periods)
    records = pipeline._standardize_to_records_us_gaap(raw)
    by_key = {(y, p, code): value for (y, p, code, _name, value) in records}
    assert by_key[(2025, 12, "revenue")] == Decimal("202512")  # annual-only davranisi HALA uygulanmali


def test_standardize_to_records_yari_yillik_sirket_annual_only_sayilmaz() -> None:
    """B21 -- SHEL tipi (H1+FY karma raporlama, bkz. 06_BILINEN_SORUNLAR.md):
    SON DONEM penceresinde GERCEK bir fp=6 (H1) donemi varsa annual_only=False
    kalmali -- bu daha karmasik yari-yillik turetme AYRI/cozulmemis bir konu,
    annual-only'nin (tam yil dogrudan kullanim) YANLISLIKLA uygulanmasi
    (Q2 verisini "tam yil" sanmak) BURADA ONLENIR."""
    periods = [(2025, 12), (2025, 6), (2024, 12), (2024, 6)]
    raw = _fake_raw_annual_only(periods=periods)
    # annual_only=False oldugundan eski (quarterly-derivation) davranis
    # devam eder -- fp=6 (H1) icin onceki ceyrek (fy,3) hic yok, bu yuzden
    # ceyreklik turetme None doner (uydurulmuyor, dogru/beklenen davranis).
    records = pipeline._standardize_to_records_us_gaap(raw)
    by_key = {(y, p, code): value for (y, p, code, _name, value) in records}
    assert (2025, 6, "revenue") not in by_key
    assert by_key[(2025, 6, "revenue_cum")] == Decimal("202506")


# --- §B17: stockanalysis.com YEDEK veri (SEC'te eksik revenue/gross_profit/operating_profit) -----------------------------------------------------


def _fake_raw_us_gaap_eksik_gp_opinc(ticker: str = "ASTSTEST") -> sec_edgar.RawUsFinancials:
    """ASTS'de CANLI gozlemlenen durumu taklit eder: GrossProfit/
    OperatingIncomeLoss tag'leri SEC'te bu donem icin HIC YOK (revenue/
    net_income VAR) -- bkz. _fake_raw_us_gaap() ile AYNI ilke, SADECE
    "us-gaap:GrossProfit"/"us-gaap:OperatingIncomeLoss" anahtarlari EKSIK."""
    facts_by_tag = {
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax": [_us_fact("2025-09-28", "2025-12-27", "1200", "Q1", 2026)],
        "us-gaap:NetIncomeLoss": [_us_fact("2025-09-28", "2025-12-27", "260", "Q1", 2026)],
        "us-gaap:DepreciationDepletionAndAmortization": [_us_fact("2025-09-28", "2025-12-27", "60", "Q1", 2026)],
        "us-gaap:Assets": [_us_fact(None, "2025-12-27", "5000", "Q1", 2026)],
        "us-gaap:AssetsCurrent": [_us_fact(None, "2025-12-27", "2000", "Q1", 2026)],
        "us-gaap:StockholdersEquity": [_us_fact(None, "2025-12-27", "3000", "Q1", 2026)],
        "us-gaap:CashAndCashEquivalentsAtCarryingValue": [_us_fact(None, "2025-12-27", "400", "Q1", 2026)],
        "us-gaap:LongTermDebtCurrent": [_us_fact(None, "2025-12-27", "200", "Q1", 2026)],
        "us-gaap:LongTermDebtNoncurrent": [_us_fact(None, "2025-12-27", "400", "Q1", 2026)],
        "dei:EntityCommonStockSharesOutstanding": [_us_fact(None, "2025-12-27", "1000000", "Q1", 2026)],
    }
    return sec_edgar.RawUsFinancials(
        ticker=ticker, cik10="0000000000", company_name="Test Inc.", periods=[(2026, 3)], facts_by_tag=facts_by_tag
    )


def test_standardize_to_records_us_gaap_sec_eksikse_stockanalysis_yedek_kullanir(monkeypatch) -> None:
    """CANLI HATA (kullanici raporu, ASTS, §B17): SEC'te GrossProfit/
    OperatingIncomeLoss tag'leri yoksa bu alanlar N/A kaliyordu. Artik
    stockanalysis.com'dan (yedek kaynak) doldurulur -- VE FAVOK'un ic
    tabani (operating_profit_ebitda_base) da otomatik olarak bu yedek
    degeri kullanir (SIFIR ek kod -- calculator.ebitda() zaten bu alani
    okuyor)."""
    raw = _fake_raw_us_gaap_eksik_gp_opinc()
    yedek = {
        (2026, 3): stockanalysis.QuarterlyIncomeSnapshot(
            period=(2026, 3), revenue=Decimal("1200"), gross_profit=Decimal("480"),
            operating_profit=Decimal("300"), net_income=Decimal("260"),
        )
    }
    monkeypatch.setattr(pipeline.stockanalysis, "fetch_quarterly_income", lambda ticker: list(yedek.values()))

    records = pipeline._standardize_to_records_us_gaap(raw)
    by_key = {(y, p, code): value for (y, p, code, _name, value) in records}

    assert by_key[(2026, 3, "gross_profit")] == Decimal("480")
    assert by_key[(2026, 3, "operating_profit")] == Decimal("300")
    assert by_key[(2026, 3, "operating_profit_ebitda_base")] == Decimal("300")
    # kumulatif ("_cum") alani stockanalysis'ten DOLDURULMAZ (SADECE ceyreklik
    # veri saglar) -- bkz. _standardize_to_records_us_gaap docstring'i.
    assert (2026, 3, "gross_profit_cum") not in by_key
    assert (2026, 3, "operating_profit_cum") not in by_key


def test_standardize_to_records_us_gaap_sec_tamsa_stockanalysis_cagrilmaz(monkeypatch) -> None:
    """Performans/nezaket: SEC verisi ZATEN eksiksizse (AAPL/NVDA/MSFT gibi
    buyuk cogunluk durum) stockanalysis.com'a GEREKSIZ bir istek ATILMAZ."""
    raw = _fake_raw_us_gaap()  # TUM alanlar dolu

    def patlarsa_hata_ver(ticker: str) -> list:
        raise AssertionError("SEC verisi eksiksizken stockanalysis.com CAGRILMAMALIYDI")

    monkeypatch.setattr(pipeline.stockanalysis, "fetch_quarterly_income", patlarsa_hata_ver)
    pipeline._standardize_to_records_us_gaap(raw)  # patlamamali


def test_standardize_to_records_us_gaap_stockanalysis_hata_verirse_alan_none_kalir(monkeypatch) -> None:
    """Kural 9: yardimci/ikincil veri kaynagi HATA verirse ana boru hatti
    ASLA bloklanmaz -- eksik alanlar SESSIZCE N/A kalmaya devam eder."""
    raw = _fake_raw_us_gaap_eksik_gp_opinc()

    def patlayan_fetch(ticker: str) -> list:
        raise stockanalysis.StockAnalysisNetworkError("baglanti hatasi")

    monkeypatch.setattr(pipeline.stockanalysis, "fetch_quarterly_income", patlayan_fetch)

    records = pipeline._standardize_to_records_us_gaap(raw)  # patlamamali
    codes = {code for (_y, _p, code, _n, _v) in records}
    assert "gross_profit" not in codes
    assert "operating_profit" not in codes


# --- _resolve_raw_financials: temel akis -----------------------------------------------------


def test_resolve_raw_financials_basarili_ise_dogru_donemi_doner(monkeypatch) -> None:
    fixture = _fake_raw_saglikli()
    monkeypatch.setattr(isyatirim, "fetch_financials", _make_fake_fetch(fixture))

    result = pipeline._resolve_raw_financials("TESTAS", None)
    assert max(result.periods) == (2026, 3)  # fixture'daki en yeni donem, ileri probe bulamadigi icin degismedi


def test_resolve_raw_financials_periods_none_iken_bir_kez_kaydirip_dener(monkeypatch) -> None:
    call_periods: list = []

    def fake_fetch(ticker, periods=None, financial_group=None):
        call_periods.append(periods)
        if periods is None:
            raise isyatirim.FinancialDataNotAvailableError("henuz yok")
        return _fake_raw_saglikli(ticker)

    monkeypatch.setattr(isyatirim, "fetch_financials", fake_fetch)

    result = pipeline._resolve_raw_financials("TESTAS", None)
    assert result.ticker == "TESTAS"
    assert len(call_periods) == 2
    assert call_periods[0] is None
    assert call_periods[1] is not None  # kaydirilmis donem listesiyle ikinci deneme


def test_resolve_raw_financials_periods_verilmisse_kaydirma_yapmaz(monkeypatch) -> None:
    call_count = {"n": 0}

    def fake_fetch(ticker, periods=None, financial_group=None):
        call_count["n"] += 1
        raise isyatirim.FinancialDataNotAvailableError("henuz yok")

    monkeypatch.setattr(isyatirim, "fetch_financials", fake_fetch)

    with pytest.raises(isyatirim.FinancialDataNotAvailableError):
        pipeline._resolve_raw_financials("TESTAS", [(2026, 3)])
    assert call_count["n"] == 1  # kaydirma denenmedi


# --- _resolve_raw_financials: ILERI probe (TAVHL canli hatasinin regresyon testi) -----------------------------------------------------


def test_resolve_raw_financials_tahminden_daha_yeni_donemi_bulur(monkeypatch) -> None:
    """Canli hata: TAVHL, guess_last_periods'in tahmininden (1Ç26) daha
    erken raporlayip 2Ç26'yi ZATEN acikladigi halde bot hala 1Ç26'yi
    gosteriyordu. Bu test, sirket fixture'da 2Ç26 verisi de bulununca
    _resolve_raw_financials'in onu bulup dogru donemi dondugunu kilitler."""
    genis_fixture = _build_fake_raw(
        "TAVHL",
        {
            (2026, 6): _donem(1300, 550, 380, 65, 300, 420, 5200, 590, 3100, 910),
            (2026, 3): _donem(1200, 500, 350, 60, 260, 400, 5000, 600, 3000, 900),
            (2025, 12): _donem(1150, 470, 330, 57, 240, 390, 4900, 610, 2950, 890),
            (2025, 6): _donem(1100, 460, 320, 58, 230, 380, 4800, 620, 2850, 880),
            (2025, 3): _donem(1000, 400, 260, 55, -80, 300, 4500, 700, 2600, 850),
            (2024, 3): _donem(900, 360, 230, 50, 150, 280, 4200, 650, 2400, 820),
        },
    )
    monkeypatch.setattr(isyatirim, "fetch_financials", _make_fake_fetch(genis_fixture))

    result = pipeline._resolve_raw_financials("TAVHL", None)

    assert max(result.periods) == (2026, 6)
    assert _fixture_has_period(result, (2026, 6))


def test_resolve_raw_financials_gelecekteki_ceyregi_asla_probe_etmez(monkeypatch) -> None:
    # Guncel ceyregin (henuz bitmemis) bir SONRAKI ceyregi -- kesin olarak
    # gelecekte, mantiken hicbir zaman veri OLAMAZ -- asla probe edilmemeli,
    # veri "varmis gibi" davransa bile (fake_fetch hicbir zaman basarisiz olmaz).
    guncel_ceyrek = isyatirim.guess_last_periods(count=1)[0]
    kesin_gelecek_ceyrek = pipeline._next_quarter_period(pipeline._next_quarter_period(guncel_ceyrek))
    assert not pipeline._quarter_has_ended(kesin_gelecek_ceyrek)  # varsayim dogrulamasi

    probed: list = []

    def fake_fetch(ticker, periods=None, financial_group=None):
        if periods is not None:
            probed.append(periods[0])
        return _fake_raw_saglikli(ticker)  # her zaman "basarili" -- probe siniri sadece tarihle korunmali

    monkeypatch.setattr(isyatirim, "fetch_financials", fake_fetch)
    pipeline._resolve_raw_financials("TESTAS", None)

    assert kesin_gelecek_ceyrek not in probed


# --- _fetch_and_store: hata esleme -----------------------------------------------------


def test_fetch_and_store_sirket_bulunamazsa_ticker_not_found(izole_db, monkeypatch) -> None:
    monkeypatch.setattr(
        isyatirim, "fetch_financials",
        lambda ticker, periods=None, financial_group=None: (_ for _ in ()).throw(isyatirim.CompanyNotFoundError("yok")),
    )
    with pytest.raises(pipeline.TickerNotFoundError):
        pipeline._fetch_and_store("ZZZZZ", None)


def test_fetch_and_store_ag_hatasi_data_source_unavailable(izole_db, monkeypatch) -> None:
    monkeypatch.setattr(
        isyatirim, "fetch_financials",
        lambda ticker, periods=None, financial_group=None: (_ for _ in ()).throw(isyatirim.IsYatirimNetworkError("ag hatasi")),
    )
    with pytest.raises(pipeline.DataSourceUnavailableError):
        pipeline._fetch_and_store("TESTAS", None)


def test_fetch_and_store_bilinmeyen_sema_unsupported_company_type(izole_db, monkeypatch) -> None:
    """XI_29/UFRS/UFRS_K disinda (hic beklenmeyen) bir financialGroup gelirse
    hala UnsupportedCompanyTypeError firlatilmali."""
    bilinmeyen_raw = isyatirim.RawFinancials(
        ticker="TESTAS", company_code="TESTAS", financial_group="BILINMEYEN", periods=[(2026, 3)], items={}
    )
    monkeypatch.setattr(isyatirim, "fetch_financials", lambda ticker, periods=None, financial_group=None: bilinmeyen_raw)

    with pytest.raises(pipeline.UnsupportedCompanyTypeError):
        pipeline._fetch_and_store("TESTAS", None)


# --- _fetch_and_store_us_gaap: hata esleme -----------------------------------------------------


def test_fetch_and_store_us_gaap_sirket_bulunamazsa_ticker_not_found(izole_db, monkeypatch) -> None:
    monkeypatch.setattr(
        sec_edgar, "fetch_financials",
        lambda ticker, periods=None: (_ for _ in ()).throw(sec_edgar.CompanyNotFoundError("yok")),
    )
    with pytest.raises(pipeline.TickerNotFoundError):
        pipeline._fetch_and_store_us_gaap("ZZZZZ", None)


def test_fetch_and_store_us_gaap_veri_yoksa_financial_data_not_found(izole_db, monkeypatch) -> None:
    """CANLI hata (kullanici raporu, 2026-08-02): 'SKHY' (SK hynix) SEC'te
    KAYITLI (CIK cozuluyor) ama companyfacts'te hicbir donemde net_income
    turetilemiyor (yabanci ozel ihracci, ABD GAAP/XBRL raporlamiyor).
    TickerNotFoundError'dan AYRI bir hata (FinancialDataNotFoundError)
    firlatilmali ki bot kullaniciya dogru sebebi soyleyebilsin."""
    monkeypatch.setattr(
        sec_edgar, "fetch_financials",
        lambda ticker, periods=None: (_ for _ in ()).throw(
            sec_edgar.FinancialDataNotAvailableError("'SKHY' (CIK0002120882) icin hicbir donemde net_income turetilemedi.")
        ),
    )
    with pytest.raises(pipeline.FinancialDataNotFoundError):
        pipeline._fetch_and_store_us_gaap("SKHY", None)


def test_fetch_and_store_us_gaap_ag_hatasi_data_source_unavailable(izole_db, monkeypatch) -> None:
    monkeypatch.setattr(
        sec_edgar, "fetch_financials",
        lambda ticker, periods=None: (_ for _ in ()).throw(sec_edgar.SecEdgarNetworkError("ag hatasi")),
    )
    with pytest.raises(pipeline.DataSourceUnavailableError):
        pipeline._fetch_and_store_us_gaap("AAPL", None)


def test_fetch_and_store_ufrs_k_semasi_sigorta_olarak_desteklenir(izole_db, monkeypatch) -> None:
    """UFRS_K (sigorta) semasi artik desteklenir -- _standardize_to_records_ufrs_k
    ile DB'ye yazilir ve Company.financial_group='UFRS_K' olarak kaydedilir."""
    item = isyatirim.FinancialItem(
        item_code="3AAAA", description_tr="BRUT YAZILAN PRIMLER", values_by_period={(2026, 3): Decimal("1000")}
    )
    ufrs_k_raw = isyatirim.RawFinancials(
        ticker="ANSGR", company_code="ANSGR", financial_group="UFRS_K", periods=[(2026, 3)], items={"3AAAA": item}
    )
    monkeypatch.setattr(isyatirim, "fetch_financials", lambda ticker, periods=None, financial_group=None: ufrs_k_raw)
    monkeypatch.setattr(kap, "search_company", lambda ticker: (_ for _ in ()).throw(kap.KapError("yok")))
    monkeypatch.setattr(kap, "fetch_disclosures", lambda ticker, days=90: [])

    pipeline._fetch_and_store("ANSGR", None)

    with repository.get_session() as session:
        company = session.get(models.Company, "ANSGR")
        assert company is not None
        assert company.financial_group == "UFRS_K"


def test_fetch_and_store_ufrs_semasi_banka_olarak_desteklenir(izole_db, monkeypatch) -> None:
    """UFRS (banka) semasi artik desteklenir -- _standardize_to_records_ufrs
    ile DB'ye yazilir ve Company.financial_group='UFRS' olarak kaydedilir."""
    item = isyatirim.FinancialItem(
        item_code="3A", description_tr="FAIZ GELIRLERI", values_by_period={(2026, 3): Decimal("1000")}
    )
    ufrs_raw = isyatirim.RawFinancials(
        ticker="GARAN", company_code="GARAN", financial_group="UFRS", periods=[(2026, 3)], items={"3A": item}
    )
    monkeypatch.setattr(isyatirim, "fetch_financials", lambda ticker, periods=None, financial_group=None: ufrs_raw)
    monkeypatch.setattr(kap, "search_company", lambda ticker: (_ for _ in ()).throw(kap.KapError("yok")))
    monkeypatch.setattr(kap, "fetch_disclosures", lambda ticker, days=90: [])

    pipeline._fetch_and_store("GARAN", None)

    with repository.get_session() as session:
        company = session.get(models.Company, "GARAN")
        assert company is not None
        assert company.financial_group == "UFRS"


def test_fetch_and_store_donem_henuz_yoksa_onceki_donemi_onerir(izole_db, monkeypatch) -> None:
    guessed = isyatirim.guess_last_periods(count=1)[0]

    def fake_fetch(ticker, periods=None, financial_group=None):
        if periods is None:
            raise isyatirim.FinancialDataNotAvailableError("henuz yok")
        # Kaydirilmis (bir ceyrek eski) donemle basarili -- ama en yenisi
        # yine de guessed'ten eski olmali ki "oner" mantigi tetiklensin.
        eski_donem = periods[0]
        return _build_fake_raw(ticker, {eski_donem: _donem(1000, 400, 260, 55, 180, 300, 4500, 700, 2600, 850)})

    monkeypatch.setattr(isyatirim, "fetch_financials", fake_fetch)

    with pytest.raises(pipeline.PeriodNotAvailableError) as exc_info:
        pipeline._fetch_and_store("TESTAS", None)

    hata = exc_info.value
    assert hata.available_label is not None
    assert hata.retry_periods is not None
    assert hata.requested_label == pipeline.quarter_label(guessed)


def test_fetch_and_store_hicbir_donem_yoksa_available_label_none(izole_db, monkeypatch) -> None:
    def fake_fetch(ticker, periods=None, financial_group=None):
        raise isyatirim.FinancialDataNotAvailableError("henuz yok")

    monkeypatch.setattr(isyatirim, "fetch_financials", fake_fetch)

    with pytest.raises(pipeline.PeriodNotAvailableError) as exc_info:
        pipeline._fetch_and_store("TESTAS", None)
    assert exc_info.value.available_label is None
    assert exc_info.value.retry_periods is None


def test_fetch_and_store_kap_hatasi_pipeline_i_dusurmez(izole_db, monkeypatch) -> None:
    # KAP tamamen basarisiz olsa bile finansal veri yazilmis olmali (zarif bozulma).
    monkeypatch.setattr(isyatirim, "fetch_financials", _make_fake_fetch(_fake_raw_saglikli("TESTAS")))
    monkeypatch.setattr(kap, "search_company", lambda ticker: (_ for _ in ()).throw(kap.KapCompanyNotFoundError("yok")))
    monkeypatch.setattr(kap, "fetch_disclosures", lambda ticker, days=90: (_ for _ in ()).throw(kap.KapNetworkError("ag hatasi")))

    pipeline._fetch_and_store("TESTAS", None)  # exception firlatmamali

    with repository.get_session() as session:
        financials = repository.get_financials(session, "TESTAS")
    assert financials  # finansal veri yine de yazilmis


# --- _ensure_sector_populated (Faz 16.5, kullanici raporu: yeni sirketlerin sektoru hic dolmuyordu) -----------------------------------------------------


def test_fetch_and_store_yeni_sirkette_sektor_otomatik_doldurulur(izole_db, monkeypatch) -> None:
    monkeypatch.setattr(isyatirim, "fetch_financials", _make_fake_fetch(_fake_raw_saglikli("TESTAS")))
    monkeypatch.setattr(kap, "search_company", lambda ticker: kap.CompanyMatch(member_oid="1", name="Test A.Ş.", ticker_codes=(ticker.lower(),)))
    monkeypatch.setattr(kap, "fetch_disclosures", lambda ticker, days=90: [])
    monkeypatch.setattr(kap, "fetch_sector_map", lambda: {"TESTAS": "TEST SEKTORU"})

    pipeline._fetch_and_store("TESTAS", None)

    with repository.get_session() as session:
        company = session.get(models.Company, "TESTAS")
    assert company.sector == "TEST SEKTORU"


def test_fetch_and_store_sektor_doluysa_fetch_sector_map_tekrar_cagrilmaz(izole_db, monkeypatch) -> None:
    """Rutin/tekrarlanan sorgularda GEREKSIZ KAP istegi atilmasin -- sektor
    ZATEN varsa fetch_sector_map() HIC CAGRILMAZ."""
    monkeypatch.setattr(isyatirim, "fetch_financials", _make_fake_fetch(_fake_raw_saglikli("TESTAS")))
    monkeypatch.setattr(kap, "search_company", lambda ticker: kap.CompanyMatch(member_oid="1", name="Test A.Ş.", ticker_codes=(ticker.lower(),)))
    monkeypatch.setattr(kap, "fetch_disclosures", lambda ticker, days=90: [])

    with repository.get_session() as session:
        repository.set_company_info(session, "TESTAS", name="Test A.Ş.", financial_group="XI_29", sector="ZATEN VAR")

    call_count = {"n": 0}

    def sahte_fetch_sector_map():
        call_count["n"] += 1
        return {}

    monkeypatch.setattr(kap, "fetch_sector_map", sahte_fetch_sector_map)
    pipeline._fetch_and_store("TESTAS", None)

    assert call_count["n"] == 0
    with repository.get_session() as session:
        company = session.get(models.Company, "TESTAS")
    assert company.sector == "ZATEN VAR"


def test_fetch_and_store_sektor_hatasi_pipeline_i_dusurmez(izole_db, monkeypatch) -> None:
    """Kural 9: sektor (ikincil veri) cekilemezse pipeline'in geri kalani
    ETKİLENMEMELİ."""
    monkeypatch.setattr(isyatirim, "fetch_financials", _make_fake_fetch(_fake_raw_saglikli("TESTAS")))
    monkeypatch.setattr(kap, "search_company", lambda ticker: kap.CompanyMatch(member_oid="1", name="Test A.Ş.", ticker_codes=(ticker.lower(),)))
    monkeypatch.setattr(kap, "fetch_disclosures", lambda ticker, days=90: [])
    monkeypatch.setattr(kap, "fetch_sector_map", lambda: (_ for _ in ()).throw(kap.KapNetworkError("ag hatasi")))

    pipeline._fetch_and_store("TESTAS", None)  # exception firlatmamali

    with repository.get_session() as session:
        financials = repository.get_financials(session, "TESTAS")
        company = session.get(models.Company, "TESTAS")
    assert financials  # finansal veri yine de yazilmis
    assert company.sector is None  # sektor bos kaldi ama pipeline cokmedi


# --- _kap_patch_records_for_xi29: FAVOK/amortisman turetmesi (canli OTKAR hatasi) -----------------------------------------------------


def test_kap_patch_records_for_xi29_ceyreklik_amortismani_onceki_ceyrekten_turetir(monkeypatch) -> None:
    """Canli hata (kullanici raporu, OTKAR): KAP SADECE kumulatif amortisman
    doner, bu yuzden FAVOK hesaplanamiyor ("N/A" gosteriliyordu). Is Yatirim'in
    ZATEN cektigi onceki ceyregin (1Ç26) kumulatif D&A'siyla fark alinarak
    ceyreklik deger turetilmeli."""
    from datetime import datetime as dt

    ref = kap_financials.FinancialReportRef(
        disclosure_index=1641767, year=2026, kap_period=2, publish_date=dt(2026, 7, 31, 22, 6)
    )
    raw_kap = kap_financials.RawKapFinancials(
        ticker="OTKAR", disclosure_index=1641767, period=(2026, 6),
        balance_sheet_items={}, income_statement_items={},
    )
    monkeypatch.setattr(kap_financials, "find_latest_financial_report", lambda ticker, days=365: ref)
    monkeypatch.setattr(kap_financials, "fetch_latest_xi29_financials", lambda ticker: raw_kap)
    monkeypatch.setattr(
        kap_financials, "standardized_record_values",
        lambda raw: {"depreciation_amortization": None, "depreciation_amortization_cum": Decimal("150")},
    )

    # onceki ceyrek (2026,3) icin Is Yatirim'dan ZATEN cekilmis D&A = 60 (bkz. _fake_raw_saglikli)
    raw_isyatirim = _fake_raw_saglikli("OTKAR")

    records, patch_period = pipeline._kap_patch_records_for_xi29("OTKAR", (2026, 3), raw_isyatirim)

    assert patch_period == (2026, 6)
    by_field = {code: value for (_y, _p, code, _n, value) in records}
    assert by_field["depreciation_amortization"] == Decimal("90")  # 150 (kumulatif) - 60 (onceki ceyrek kumulatif)
    assert by_field["depreciation_amortization_cum"] == Decimal("150")


def test_kap_patch_records_for_xi29_onceki_ceyrek_verisi_yoksa_turetmez(monkeypatch) -> None:
    from datetime import datetime as dt

    ref = kap_financials.FinancialReportRef(
        disclosure_index=1, year=2026, kap_period=2, publish_date=dt(2026, 7, 31, 22, 6)
    )
    raw_kap = kap_financials.RawKapFinancials(
        ticker="OTKAR", disclosure_index=1, period=(2026, 6), balance_sheet_items={}, income_statement_items={},
    )
    monkeypatch.setattr(kap_financials, "find_latest_financial_report", lambda ticker, days=365: ref)
    monkeypatch.setattr(kap_financials, "fetch_latest_xi29_financials", lambda ticker: raw_kap)
    monkeypatch.setattr(
        kap_financials, "standardized_record_values",
        lambda raw: {"depreciation_amortization": None, "depreciation_amortization_cum": Decimal("150")},
    )

    bos_raw = isyatirim.RawFinancials(ticker="OTKAR", company_code="OTKAR", financial_group="XI_29", periods=[], items={})
    records, _patch_period = pipeline._kap_patch_records_for_xi29("OTKAR", (2026, 3), bos_raw)

    by_field = {code: value for (_y, _p, code, _n, value) in records}
    assert "depreciation_amortization" not in by_field  # turetilemedi, sessizce atlandi
    assert by_field["depreciation_amortization_cum"] == Decimal("150")


# --- _kap_patch_records_for_ufrs (banka) -----------------------------------------------------


def test_kap_patch_records_for_ufrs_daha_yeni_donem_bulunca_yamalar(monkeypatch) -> None:
    from datetime import datetime as dt

    ref = kap_financials.FinancialReportRef(
        disclosure_index=1639924, year=2026, kap_period=2, publish_date=dt(2026, 7, 31, 8, 1)
    )
    raw_kap = kap_financials.RawKapFinancials(
        ticker="YKBNK", disclosure_index=1639924, period=(2026, 6),
        balance_sheet_items={}, income_statement_items={},
    )
    monkeypatch.setattr(kap_financials, "find_latest_financial_report", lambda ticker, days=365: ref)
    monkeypatch.setattr(kap_financials, "fetch_latest_ufrs_financials", lambda ticker: raw_kap)
    monkeypatch.setattr(
        kap_financials, "standardized_record_values_ufrs",
        lambda raw: {"loans": Decimal("2182361000000"), "interest_income": None},
    )

    records, patch_period = pipeline._kap_patch_records_for_ufrs("YKBNK", (2026, 3))

    assert patch_period == (2026, 6)
    assert records == [(2026, 6, "loans", pipeline.calculator.FIELD_LABELS_TR["loans"], Decimal("2182361000000"))]


def test_kap_patch_records_for_ufrs_daha_yeni_donem_yoksa_bos_doner(monkeypatch) -> None:
    monkeypatch.setattr(kap_financials, "find_latest_financial_report", lambda ticker, days=365: None)

    records, patch_period = pipeline._kap_patch_records_for_ufrs("YKBNK", (2026, 3))

    assert records == []
    assert patch_period is None


def test_kap_patch_records_for_ufrs_hata_pipeline_i_dusurmez(monkeypatch) -> None:
    def raise_error(ticker, days=365):
        raise RuntimeError("KAP erisilemedi")

    monkeypatch.setattr(kap_financials, "find_latest_financial_report", raise_error)

    records, patch_period = pipeline._kap_patch_records_for_ufrs("YKBNK", (2026, 3))

    assert records == []
    assert patch_period is None


# --- run_pipeline: uctan uca (Playwright GERCEK calisir, sadece ag katmani sahte) -----------------------------------------------------


def test_run_pipeline_basucdan_uca_basarili(izole_db, monkeypatch) -> None:
    monkeypatch.setattr(isyatirim, "fetch_financials", _make_fake_fetch(_fake_raw_saglikli("TESTAS")))
    monkeypatch.setattr(kap, "search_company", lambda ticker: kap.CompanyMatch(member_oid="1", name="Test Sanayi A.Ş.", ticker_codes=(ticker.lower(),)))
    monkeypatch.setattr(kap, "fetch_disclosures", lambda ticker, days=90: [])

    sonuc = pipeline.run_pipeline("testas")

    assert sonuc.ticker == "TESTAS"
    assert sonuc.company_name == "Test Sanayi A.Ş."
    assert sonuc.commentary.source == "fallback"  # GEMINI_API_KEY bos
    assert sonuc.score.total_score >= Decimal("0")

    png_path = Path(sonuc.png_path)
    assert png_path.exists()
    assert png_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_run_pipeline_veri_tazeyse_yorum_onbellekten_gelir_gemini_tekrar_cagrilmaz(izole_db, monkeypatch) -> None:
    """CommentaryCache: Gemini'nin GUNLUK kota siniri var (bkz. repository.py
    CommentaryCache docstring'i) -- ayni donem icin ikinci bir run_pipeline
    cagrisi (veri hala TAZEYKEN) yorum uretici fonksiyonu TEKRAR CAGIRMAMALI,
    onbellekten okumali."""
    monkeypatch.setattr(isyatirim, "fetch_financials", _make_fake_fetch(_fake_raw_saglikli("TESTAS")))
    monkeypatch.setattr(kap, "search_company", lambda ticker: kap.CompanyMatch(member_oid="1", name="Test Sanayi A.Ş.", ticker_codes=(ticker.lower(),)))
    monkeypatch.setattr(kap, "fetch_disclosures", lambda ticker, days=90: [])
    monkeypatch.setattr(kap_financials, "find_latest_financial_report", lambda ticker, days=365: None)

    call_count = {"n": 0}
    from src.ai import commentary as commentary_module

    original_fallback = commentary_module._fallback_commentary

    def counting_fallback(*args, **kwargs):
        call_count["n"] += 1
        return original_fallback(*args, **kwargs)

    monkeypatch.setattr(commentary_module, "_fallback_commentary", counting_fallback)

    ilk = pipeline.run_pipeline("TESTAS")
    assert call_count["n"] == 1

    ikinci = pipeline.run_pipeline("TESTAS")  # veri hala TAZE (12 saat penceresi icinde)
    assert call_count["n"] == 1  # TEKRAR cagrilmadi -- onbellekten geldi
    assert ikinci.commentary.headline == ilk.commentary.headline
    assert ikinci.commentary.summary == ilk.commentary.summary


def test_run_pipeline_fiyat_varsa_karta_gecer(izole_db, monkeypatch) -> None:
    monkeypatch.setattr(isyatirim, "fetch_financials", _make_fake_fetch(_fake_raw_saglikli("TESTAS")))
    monkeypatch.setattr(isyatirim, "fetch_latest_price", lambda ticker, lookback_days=10: Decimal("142.5"))
    monkeypatch.setattr(kap, "search_company", lambda ticker: kap.CompanyMatch(member_oid="1", name="Test A.Ş.", ticker_codes=(ticker.lower(),)))
    monkeypatch.setattr(kap, "fetch_disclosures", lambda ticker, days=90: [])

    from src.render import card as card_module
    context_holder = {}
    orijinal_build = card_module.build_card_context

    def sarmalayici(*args, **kwargs):
        ctx = orijinal_build(*args, **kwargs)
        context_holder["context"] = ctx
        return ctx

    monkeypatch.setattr(card_module, "build_card_context", sarmalayici)

    pipeline.run_pipeline("TESTAS")
    assert context_holder["context"]["price_display"] == "142,50 ₺"


def test_run_pipeline_fiyat_cekilemezse_kart_yine_de_uretilir(izole_db, monkeypatch) -> None:
    monkeypatch.setattr(isyatirim, "fetch_financials", _make_fake_fetch(_fake_raw_saglikli("TESTAS")))
    monkeypatch.setattr(
        isyatirim, "fetch_latest_price",
        lambda ticker, lookback_days=10: (_ for _ in ()).throw(isyatirim.IsYatirimNetworkError("ag hatasi")),
    )
    monkeypatch.setattr(kap, "search_company", lambda ticker: kap.CompanyMatch(member_oid="1", name="Test A.Ş.", ticker_codes=(ticker.lower(),)))
    monkeypatch.setattr(kap, "fetch_disclosures", lambda ticker, days=90: [])

    sonuc = pipeline.run_pipeline("TESTAS")  # exception firlatmamali
    assert Path(sonuc.png_path).exists()


def test_run_pipeline_ikinci_cagri_onbellekten_okur_yeniden_fetch_yapmaz(izole_db, monkeypatch) -> None:
    """Onbellek YAS bakimindan taze oldugunda bile _has_newer_period_available
    TEK ucuz bir probe cagrisi yapar (bkz. pipeline.py, canli YKBNK hatasinin
    regresyon korumasi) -- fixture'da bir sonraki ceyrek olmadigi icin bu
    probe basarisiz olur ve TAM fetch (agir KAP/disclosure adimlariyla)
    TEKRARLANMAZ; sadece o TEK ucuz probe call_log'a eklenir."""
    call_log: list = []
    monkeypatch.setattr(isyatirim, "fetch_financials", _make_fake_fetch(_fake_raw_saglikli("TESTAS"), call_log))
    monkeypatch.setattr(kap, "search_company", lambda ticker: kap.CompanyMatch(member_oid="1", name="Test A.Ş.", ticker_codes=(ticker.lower(),)))
    monkeypatch.setattr(kap, "fetch_disclosures", lambda ticker, days=90: [])
    monkeypatch.setattr(kap_financials, "find_latest_financial_report", lambda ticker, days=365: None)

    pipeline.run_pipeline("TESTAS")
    ilk_cagri_sayisi = len(call_log)
    assert ilk_cagri_sayisi >= 1

    pipeline.run_pipeline("TESTAS")
    assert len(call_log) == ilk_cagri_sayisi + 1  # sadece ucuz "yeni donem var mi" probe'u eklendi
    assert call_log[-1][0] == pipeline._next_quarter_period((2026, 3))  # probe TESTAS'in bir sonraki ceyregini kontrol etti


def test_run_pipeline_onbellek_tazeyken_bile_yeni_donem_varsa_yakalar(izole_db, monkeypatch) -> None:
    """Canli hata (kullanici raporu, YKBNK): onbellek YAS bakimindan taze
    (12 saatlik pencere icinde) olsa bile, bu sure icinde YENI bir ceyrek
    yayinlanmissa bot bunu bir sonraki sorguda ANINDA yakalamali -- 12 saat
    dolana kadar eski donemi gostermeye DEVAM ETMEMELI (bkz. pipeline.py
    _has_newer_period_available)."""
    fixture_state = {"raw": _fake_raw_saglikli("TESTAS")}

    def fake_fetch(ticker, periods=None, financial_group=None):
        return _make_fake_fetch(fixture_state["raw"])(ticker, periods=periods, financial_group=financial_group)

    monkeypatch.setattr(isyatirim, "fetch_financials", fake_fetch)
    monkeypatch.setattr(kap, "search_company", lambda ticker: kap.CompanyMatch(member_oid="1", name="Test A.Ş.", ticker_codes=(ticker.lower(),)))
    monkeypatch.setattr(kap, "fetch_disclosures", lambda ticker, days=90: [])
    monkeypatch.setattr(kap_financials, "find_latest_financial_report", lambda ticker, days=365: None)

    ilk = pipeline.run_pipeline("TESTAS")
    assert ilk.analysis.latest_period == (2026, 3)

    # 2026/6 bilancosu simdi yayinlandi -- ama onbellek suresi (12 saat) HENUZ DOLMADI.
    fixture_state["raw"] = _build_fake_raw(
        "TESTAS",
        {
            (2026, 6): _donem(1300, 550, 380, 65, 300, 420, 5200, 590, 3100, 910),
            (2026, 3): _donem(1200, 500, 350, 60, 260, 400, 5000, 600, 3000, 900),
            (2025, 3): _donem(1000, 400, 260, 55, -80, 300, 4500, 700, 2600, 850),
            (2024, 3): _donem(900, 360, 230, 50, 150, 280, 4200, 650, 2400, 820),
            (2023, 3): _donem(800, 320, 200, 45, 120, 260, 4000, 600, 2200, 800),
        },
    )

    ikinci = pipeline.run_pipeline("TESTAS")
    assert ikinci.analysis.latest_period == (2026, 6)  # 12 saatlik pencere icinde bile yeni donem yakalandi


def test_run_pipeline_ticker_kucuk_harfle_de_calisir(izole_db, monkeypatch) -> None:
    monkeypatch.setattr(isyatirim, "fetch_financials", _make_fake_fetch(_fake_raw_saglikli("TESTAS")))
    monkeypatch.setattr(kap, "search_company", lambda ticker: kap.CompanyMatch(member_oid="1", name="Test A.Ş.", ticker_codes=(ticker.lower(),)))
    monkeypatch.setattr(kap, "fetch_disclosures", lambda ticker, days=90: [])

    sonuc = pipeline.run_pipeline("testas")
    assert sonuc.ticker == "TESTAS"


# --- §B19: market uyusmazliginda onbellek GECERSIZ sayilmali (KRITIK, kullanici raporu) -----------------------------------------------------


def test_run_pipeline_nasdaq_ucdan_uca_basarili(izole_db, monkeypatch) -> None:
    """Coverage bosluğu: run_pipeline(market='NASDAQ') icin HICBIR uctan
    uca test YOKTU -- §B19'un asagidaki regresyonu icin once bu temel
    "basarili NASDAQ akisi" saglamlastirilir."""
    monkeypatch.setattr(sec_edgar, "fetch_financials", lambda ticker, periods=None: _fake_raw_us_gaap(ticker))
    monkeypatch.setattr(sec_edgar, "fetch_latest_price", lambda ticker: None)

    sonuc = pipeline.run_pipeline("TESTUS", market="NASDAQ")

    assert sonuc.ticker == "TESTUS"
    company_row = None
    with repository.get_session() as session:
        company_row = session.get(models.Company, "TESTUS")
    assert company_row.market == "NASDAQ"


def test_run_pipeline_bist_ile_onbellege_alinan_ticker_nasdaqta_tekrar_sorulursa_dogru_render_edilir(
    izole_db, monkeypatch
) -> None:
    """CANLI HATA (kullanici raporu, 2026-08-03, ACİL): 'AMD'/'ASTS' gibi HEM
    BIST regex'ine (3-6 harf) UYAN HEM DE daha once NASDAQ olarak analiz
    edilmis bir ticker, menusuz/varsayilan bir aramada (market='BIST'
    varsayilaniyla) sorulunca -- is_data_fresh() market'i KONTROL ETMEDIGI
    icin -- yanlislikla "taze" sayiliyor VE BIST sablonuyla (₺, "İş Yatırım,
    KAP" kaynagi, fiyat/degerleme basligi TAMAMEN kayip) render ediliyordu.
    Bu test TAM olarak bu senaryoyu tekrar uretir: once NASDAQ olarak
    onbellege alinir, SONRA market='BIST' ile (BIST'te GERCEKTEN yok)
    sorulur -- artik TickerNotFoundError firlatmali (allow_market_fallback
    mekanizmasinin dogru market'i denemesini saglamak icin), SESSIZCE
    yanlis sablonla 'basarili' DONMEMELI."""
    monkeypatch.setattr(sec_edgar, "fetch_financials", lambda ticker, periods=None: _fake_raw_us_gaap(ticker))
    monkeypatch.setattr(sec_edgar, "fetch_latest_price", lambda ticker: None)
    pipeline.run_pipeline("TESTUS", market="NASDAQ")  # onbellege NASDAQ olarak yazilir

    def bist_te_bulunamaz(ticker, periods=None, financial_group=None):
        raise isyatirim.CompanyNotFoundError(f"'{ticker}' BIST'te bulunamadi (test).")

    monkeypatch.setattr(isyatirim, "fetch_financials", bist_te_bulunamaz)

    with pytest.raises(pipeline.TickerNotFoundError):
        pipeline.run_pipeline("TESTUS", market="BIST")


def test_run_pipeline_ayni_market_ile_tekrar_sorulursa_onbellekten_okur(izole_db, monkeypatch) -> None:
    """Regresyon KORUMASI: market uyusmazligi kontrolu SADECE gercek bir
    uyusmazlik varken devreye girer -- AYNI market ile ikinci cagri hala
    onbellekten okumali (gereksiz tam fetch TETIKLENMEMELI)."""
    call_count = {"n": 0}

    def sayan_fetch(ticker, periods=None):
        call_count["n"] += 1
        return _fake_raw_us_gaap(ticker)

    monkeypatch.setattr(sec_edgar, "fetch_financials", sayan_fetch)
    monkeypatch.setattr(sec_edgar, "fetch_latest_price", lambda ticker: None)

    pipeline.run_pipeline("TESTUS", market="NASDAQ")
    assert call_count["n"] == 1

    pipeline.run_pipeline("TESTUS", market="NASDAQ")  # ayni market, veri hala taze
    assert call_count["n"] == 1  # TEKRAR fetch edilmedi
