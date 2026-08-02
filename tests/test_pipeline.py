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
from src.fetchers import isyatirim, kap, kap_financials, sec_edgar


# --- Izole DB fixture (repository.get_session()'i tmp_path'e yonlendirir) -----------------------------------------------------


@pytest.fixture()
def izole_db(monkeypatch, tmp_path):
    engine, session_factory = models.create_engine_and_session(f"sqlite:///{tmp_path / 'test_pipeline.db'}")
    models.init_db(engine)
    monkeypatch.setattr(repository, "DefaultSessionLocal", session_factory)
    monkeypatch.setattr(repository, "_default_db_initialized", True)
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")  # commentary'yi deterministik yedek moda zorla
    monkeypatch.setattr(isyatirim, "fetch_latest_price", lambda ticker, lookback_days=10: None)  # ag istegi atma
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
