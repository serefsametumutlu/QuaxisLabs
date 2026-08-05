"""Faz 3 teslim kriteri: upsert'un mukerrer kayit olusturmadigini ve
onbellek (is_data_fresh) mantigini dogrulayan testler.

Her test kendi izole SQLite dosyasini kullanir (tmp_path) -- gercek
data/bilanco_radar.db dosyasina asla dokunulmaz.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from src.db import models, repository
from src.db.models import Company, Disclosure, EarningsCalendar, FinancialPeriod, Fund, FundHolding


@pytest.fixture()
def session(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'test.db'}"
    engine, session_factory = models.create_engine_and_session(db_url)
    models.init_db(engine)
    db_session = session_factory()
    yield db_session
    db_session.close()


# --- upsert_financials -----------------------------------------------------


def test_upsert_financials_ilk_cagrida_satirlari_ekler(session) -> None:
    records = [
        (2026, 3, "3C", "Satis Gelirleri", Decimal("100")),
        (2026, 3, "1BL", "Toplam Varliklar", Decimal("1000")),
    ]
    inserted = repository.upsert_financials(session, "THYAO", records)

    assert inserted == 2
    rows = session.execute(select(FinancialPeriod).where(FinancialPeriod.ticker == "THYAO")).scalars().all()
    assert len(rows) == 2


def test_upsert_financials_ayni_kayitla_tekrar_cagrilinca_mukerrer_olusturmaz(session) -> None:
    records = [(2026, 3, "3C", "Satis Gelirleri", Decimal("100"))]

    repository.upsert_financials(session, "THYAO", records)
    inserted_second = repository.upsert_financials(session, "THYAO", records)

    rows = session.execute(select(FinancialPeriod).where(FinancialPeriod.ticker == "THYAO")).scalars().all()
    assert len(rows) == 1  # mukerrer satir OLUSMADI
    assert inserted_second == 0  # ikinci cagrida yeni satir eklenmedi


def test_upsert_financials_ayni_anahtarda_degeri_gunceller(session) -> None:
    repository.upsert_financials(session, "THYAO", [(2026, 3, "3C", "Satis Gelirleri", Decimal("100"))])
    repository.upsert_financials(session, "THYAO", [(2026, 3, "3C", "Satis Gelirleri", Decimal("250"))])

    rows = session.execute(select(FinancialPeriod).where(FinancialPeriod.ticker == "THYAO")).scalars().all()
    assert len(rows) == 1
    assert rows[0].value == Decimal("250")


def test_upsert_financials_company_satirini_otomatik_olusturur(session) -> None:
    repository.upsert_financials(session, "THYAO", [(2026, 3, "3C", "Satis Gelirleri", Decimal("100"))])

    company = session.get(Company, "THYAO")
    assert company is not None
    assert company.last_updated is not None


def test_upsert_financials_farkli_donem_ayri_satir_olarak_eklenir(session) -> None:
    repository.upsert_financials(session, "THYAO", [(2026, 3, "3C", "Satis Gelirleri", Decimal("100"))])
    inserted = repository.upsert_financials(session, "THYAO", [(2025, 12, "3C", "Satis Gelirleri", Decimal("90"))])

    assert inserted == 1
    rows = session.execute(select(FinancialPeriod).where(FinancialPeriod.ticker == "THYAO")).scalars().all()
    assert len(rows) == 2


# --- get_financials -----------------------------------------------------


def test_get_financials_donemleri_yeniden_eskiye_sinirla(session) -> None:
    repository.upsert_financials(
        session,
        "THYAO",
        [
            (2026, 3, "3C", "Satis Gelirleri", Decimal("300")),
            (2025, 12, "3C", "Satis Gelirleri", Decimal("200")),
            (2025, 9, "3C", "Satis Gelirleri", Decimal("100")),
        ],
    )

    result = repository.get_financials(session, "THYAO", n_periods=2)

    assert list(result.keys()) == [(2026, 3), (2025, 12)]
    assert result[(2026, 3)]["3C"] == Decimal("300")


# --- save_disclosures / get_recent_disclosures -----------------------------------------------------


def test_save_disclosures_mukerrer_url_atlar(session) -> None:
    records = [(datetime(2026, 7, 1), "Baslik", "Kategori", "yuksek", "https://kap.org.tr/x")]

    first = repository.save_disclosures(session, "THYAO", records)
    second = repository.save_disclosures(session, "THYAO", records)

    rows = session.execute(select(Disclosure).where(Disclosure.ticker == "THYAO")).scalars().all()
    assert first == 1
    assert second == 0
    assert len(rows) == 1


def test_get_recent_disclosures_gun_penceresine_gore_filtreler(session) -> None:
    now = repository.utcnow_naive()
    records = [
        (now - timedelta(days=5), "Yeni", "Kategori", "yuksek", "https://kap.org.tr/yeni"),
        (now - timedelta(days=200), "Eski", "Kategori", "dusuk", "https://kap.org.tr/eski"),
    ]
    repository.save_disclosures(session, "THYAO", records)

    recent = repository.get_recent_disclosures(session, "THYAO", days=90)

    assert len(recent) == 1
    assert recent[0].title == "Yeni"


# --- is_data_fresh -----------------------------------------------------


def test_is_data_fresh_hic_gorulmeyen_ticker_icin_false(session) -> None:
    assert repository.is_data_fresh(session, "BILINMEYEN") is False


def test_is_data_fresh_yeni_upsert_sonrasi_true(session) -> None:
    repository.upsert_financials(session, "THYAO", [(2026, 3, "3C", "Satis Gelirleri", Decimal("100"))])

    assert repository.is_data_fresh(session, "THYAO", max_age_hours=12) is True


def test_is_data_fresh_eski_veri_icin_false(session) -> None:
    repository.upsert_financials(session, "THYAO", [(2026, 3, "3C", "Satis Gelirleri", Decimal("100"))])

    company = session.get(Company, "THYAO")
    company.last_updated = repository.utcnow_naive() - timedelta(hours=13)
    session.commit()

    assert repository.is_data_fresh(session, "THYAO", max_age_hours=12) is False


def test_is_data_fresh_sinir_degerinde_true(session) -> None:
    repository.upsert_financials(session, "THYAO", [(2026, 3, "3C", "Satis Gelirleri", Decimal("100"))])

    company = session.get(Company, "THYAO")
    company.last_updated = repository.utcnow_naive() - timedelta(hours=11, minutes=59)
    session.commit()

    assert repository.is_data_fresh(session, "THYAO", max_age_hours=12) is True


# --- save_generated_card -----------------------------------------------------


def test_save_generated_card_her_cagrida_yeni_satir_ekler(session) -> None:
    repository.save_generated_card(session, "THYAO", "data/cards/thyao_1.png", 7.5)
    repository.save_generated_card(session, "THYAO", "data/cards/thyao_2.png", 8.0)

    from src.db.models import GeneratedCard

    rows = session.execute(select(GeneratedCard).where(GeneratedCard.ticker == "THYAO")).scalars().all()
    assert len(rows) == 2


# --- get_score_history (Derin Kart, skor geçmişi) -----------------------------------------------------


def test_get_score_history_eskiden_yeniye_sirali_doner(session) -> None:
    repository.save_generated_card(session, "THYAO", "data/cards/1.png", 5.0)
    repository.save_generated_card(session, "THYAO", "data/cards/2.png", 7.5)
    repository.save_generated_card(session, "THYAO", "data/cards/3.png", 6.0)

    history = repository.get_score_history(session, "THYAO")

    assert [score for _, score in history] == [5.0, 7.5, 6.0]
    # created_at artan sirada olmali (grafik/cizgi icin dogal sira)
    assert history[0][0] <= history[1][0] <= history[2][0]


def test_get_score_history_baska_sirketi_karistirmaz(session) -> None:
    repository.save_generated_card(session, "THYAO", "data/cards/1.png", 5.0)
    repository.save_generated_card(session, "ASELS", "data/cards/2.png", 9.0)

    history = repository.get_score_history(session, "THYAO")

    assert [score for _, score in history] == [5.0]


def test_get_score_history_kayit_yoksa_bos_liste_doner(session) -> None:
    assert repository.get_score_history(session, "YOKTUR") == []


def test_get_score_history_limit_en_yeni_n_kaydi_tutar(session) -> None:
    for i, score in enumerate([1.0, 2.0, 3.0, 4.0, 5.0]):
        repository.save_generated_card(session, "THYAO", f"data/cards/{i}.png", score)

    history = repository.get_score_history(session, "THYAO", limit=2)

    # limit=2 -> en YENI 2 kayit, ama yine ESKIDEN YENIYE sirali donmeli
    assert [score for _, score in history] == [4.0, 5.0]


# --- update_company_sectors / get_sector_peer_tickers (Faz 16, Derin Kart) -----------------------------------------------------


def test_update_company_sectors_eslesen_sirketleri_gunceller(session) -> None:
    repository.upsert_financials(session, "THYAO", [(2026, 3, "revenue", "Satislar", Decimal("100"))])
    repository.upsert_financials(session, "TUPRS", [(2026, 3, "revenue", "Satislar", Decimal("100"))])

    updated = repository.update_company_sectors(session, {"THYAO": "ULAŞTIRMA VE DEPOLAMA", "TUPRS": "KİMYA"})

    assert updated == 2
    assert session.get(Company, "THYAO").sector == "ULAŞTIRMA VE DEPOLAMA"
    assert session.get(Company, "TUPRS").sector == "KİMYA"


def test_update_company_sectors_haritada_olmayan_sirket_degismez(session) -> None:
    repository.upsert_financials(session, "THYAO", [(2026, 3, "revenue", "Satislar", Decimal("100"))])
    updated = repository.update_company_sectors(session, {"BASKA": "X"})
    assert updated == 0
    assert session.get(Company, "THYAO").sector is None


def test_update_company_sectors_zaten_ayni_sektorse_sayilmaz(session) -> None:
    repository.upsert_financials(session, "THYAO", [(2026, 3, "revenue", "Satislar", Decimal("100"))])
    repository.update_company_sectors(session, {"THYAO": "ULAŞTIRMA"})
    updated_again = repository.update_company_sectors(session, {"THYAO": "ULAŞTIRMA"})
    assert updated_again == 0


def test_get_sector_peer_tickers_ayni_sektor_ve_grubu_bulur(session) -> None:
    for ticker in ("THYAO", "PGSUS", "TUPRS"):
        repository.upsert_financials(session, ticker, [(2026, 3, "revenue", "Satislar", Decimal("100"))])
    repository.set_company_info(session, "THYAO", financial_group="XI_29")
    repository.set_company_info(session, "PGSUS", financial_group="XI_29")
    repository.set_company_info(session, "TUPRS", financial_group="XI_29")
    repository.update_company_sectors(
        session, {"THYAO": "ULAŞTIRMA", "PGSUS": "ULAŞTIRMA", "TUPRS": "KİMYA"}
    )

    peers = repository.get_sector_peer_tickers(session, "ULAŞTIRMA", "XI_29", exclude_ticker="THYAO")

    assert peers == ["PGSUS"]


def test_get_sector_peer_tickers_farkli_financial_group_haric_tutulur(session) -> None:
    for ticker in ("THYAO", "FAKEBANK"):
        repository.upsert_financials(session, ticker, [(2026, 3, "revenue", "Satislar", Decimal("100"))])
    repository.set_company_info(session, "THYAO", financial_group="XI_29")
    repository.set_company_info(session, "FAKEBANK", financial_group="UFRS")
    repository.update_company_sectors(session, {"THYAO": "ULAŞTIRMA", "FAKEBANK": "ULAŞTIRMA"})

    peers = repository.get_sector_peer_tickers(session, "ULAŞTIRMA", "XI_29", exclude_ticker="THYAO")

    assert peers == []


def test_get_sector_peer_tickers_sektor_bossa_bos_liste(session) -> None:
    repository.upsert_financials(session, "THYAO", [(2026, 3, "revenue", "Satislar", Decimal("100"))])
    repository.set_company_info(session, "THYAO", financial_group="XI_29")
    peers = repository.get_sector_peer_tickers(session, "ULAŞTIRMA", "XI_29", exclude_ticker="THYAO")
    assert peers == []


# --- market / Faz 9 (NASDAQ) -----------------------------------------------------


def test_yeni_sirket_varsayilan_olarak_bist_piyasasinda_olusturulur(session) -> None:
    repository.upsert_financials(session, "THYAO", [(2026, 6, "revenue", "Satislar", Decimal("100"))])

    company = session.get(Company, "THYAO")
    assert company.market == "BIST"


def test_set_company_info_market_nasdaq_olarak_ayarlanabilir(session) -> None:
    repository.set_company_info(session, "AAPL", name="Apple Inc.", financial_group="US_GAAP", market="NASDAQ")

    company = session.get(Company, "AAPL")
    assert company.market == "NASDAQ"
    assert company.financial_group == "US_GAAP"


def test_set_company_info_farkli_market_ile_tekrar_cagrilinca_hata_firlatir(session) -> None:
    repository.set_company_info(session, "AAPL", market="NASDAQ")

    with pytest.raises(repository.TickerMarketConflictError):
        repository.set_company_info(session, "AAPL", market="BIST")


def test_set_company_info_market_verilmezse_mevcut_deger_korunur(session) -> None:
    repository.set_company_info(session, "AAPL", market="NASDAQ")

    # market=None (varsayilan) ile cagirmak MEVCUT degeri DEGISTIRMEMELI ve
    # TickerMarketConflictError FIRLATMAMALI (bkz. _get_or_create_company:
    # kontrol sadece market ACIKCA verildiginde yapilir).
    repository.set_company_info(session, "AAPL", name="Apple Inc.")

    company = session.get(Company, "AAPL")
    assert company.market == "NASDAQ"
    assert company.name == "Apple Inc."


def test_migrate_add_market_column_eski_semaya_sutun_ekler_ve_bist_ile_doldurur(tmp_path) -> None:
    """Faz 9 ONCESI olusturulmus (market sutunu OLMAYAN) bir 'company' tablosunu
    simule eder -- init_db() bunu ALTER TABLE ile GUVENLI sekilde migrate
    etmeli (bkz. models._migrate_add_market_column)."""
    from sqlalchemy import text

    db_url = f"sqlite:///{tmp_path / 'legacy.db'}"
    engine, _ = models.create_engine_and_session(db_url)

    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE company ("
                "ticker VARCHAR(20) PRIMARY KEY, name VARCHAR(255), sector VARCHAR(100), "
                "financial_group VARCHAR(20), kap_member_id VARCHAR(64), last_updated DATETIME)"
            )
        )
        connection.execute(text("INSERT INTO company (ticker, financial_group) VALUES ('THYAO', 'XI_29')"))

    models.init_db(engine)

    with engine.connect() as connection:
        row = connection.execute(text("SELECT ticker, market FROM company WHERE ticker = 'THYAO'")).fetchone()
    assert row == ("THYAO", "BIST")

    # idempotentlik: tekrar cagirmak hata FIRLATMAMALI.
    models.init_db(engine)


# --- Faz 12: earnings_calendar (upsert_earnings_calendar / get_upcoming_earnings / is_earnings_calendar_fresh) -----------------------------------------------------


def _fake_earnings_record(ticker="TESTAS", market="BIST", expected_date=date(2026, 8, 10), confidence="tahmini"):
    return (ticker, market, f"{ticker} A.Ş.", 2026, 6, expected_date, confidence, "geçmiş yayın medyanı")


def test_upsert_earnings_calendar_ilk_cagrida_satir_ekler(session) -> None:
    inserted = repository.upsert_earnings_calendar(session, [_fake_earnings_record()])
    assert inserted == 1
    rows = session.execute(select(EarningsCalendar).where(EarningsCalendar.ticker == "TESTAS")).scalars().all()
    assert len(rows) == 1
    assert rows[0].expected_date == date(2026, 8, 10)


def test_upsert_earnings_calendar_ayni_donem_icin_mukerrer_satir_olusturmaz_gunceller(session) -> None:
    repository.upsert_earnings_calendar(session, [_fake_earnings_record(confidence="son_tarih", expected_date=date(2026, 8, 20))])
    repository.upsert_earnings_calendar(session, [_fake_earnings_record(confidence="kesin", expected_date=date(2026, 8, 10))])

    rows = session.execute(select(EarningsCalendar).where(EarningsCalendar.ticker == "TESTAS")).scalars().all()
    assert len(rows) == 1
    assert rows[0].confidence == "kesin"
    assert rows[0].expected_date == date(2026, 8, 10)


def test_get_upcoming_earnings_tarih_araligina_gore_filtreler(session) -> None:
    repository.upsert_earnings_calendar(
        session,
        [
            _fake_earnings_record("ICERIDE", expected_date=date(2026, 8, 15)),
            _fake_earnings_record("ONCESI", expected_date=date(2026, 7, 1)),
            _fake_earnings_record("SONRASI", expected_date=date(2026, 12, 1)),
        ],
    )

    results = repository.get_upcoming_earnings(session, market="BIST", days_ahead=30, today=date(2026, 8, 1))

    assert [r.ticker for r in results] == ["ICERIDE"]


def test_get_upcoming_earnings_market_filtreler(session) -> None:
    repository.upsert_earnings_calendar(
        session,
        [
            _fake_earnings_record("BIST_HISSE", market="BIST", expected_date=date(2026, 8, 10)),
            _fake_earnings_record("NASDAQ_HISSE", market="NASDAQ", expected_date=date(2026, 8, 10)),
        ],
    )

    results = repository.get_upcoming_earnings(session, market="NASDAQ", days_ahead=30, today=date(2026, 8, 1))

    assert [r.ticker for r in results] == ["NASDAQ_HISSE"]


def test_get_upcoming_earnings_tarihe_gore_siralanir(session) -> None:
    repository.upsert_earnings_calendar(
        session,
        [
            _fake_earnings_record("GEC", expected_date=date(2026, 8, 20)),
            _fake_earnings_record("ERKEN", expected_date=date(2026, 8, 5)),
        ],
    )

    results = repository.get_upcoming_earnings(session, market="BIST", days_ahead=30, today=date(2026, 8, 1))

    assert [r.ticker for r in results] == ["ERKEN", "GEC"]


def test_is_earnings_calendar_fresh_hic_kayit_yoksa_false(session) -> None:
    assert repository.is_earnings_calendar_fresh(session, market="BIST") is False


def test_is_earnings_calendar_fresh_yeni_guncellenmisse_true(session) -> None:
    repository.upsert_earnings_calendar(session, [_fake_earnings_record()])
    assert repository.is_earnings_calendar_fresh(session, market="BIST", max_age_hours=24) is True


def test_is_earnings_calendar_fresh_eskiyse_false(session) -> None:
    repository.upsert_earnings_calendar(session, [_fake_earnings_record()])
    row = session.execute(select(EarningsCalendar).where(EarningsCalendar.ticker == "TESTAS")).scalar_one()
    row.updated_at = models.utcnow_naive() - timedelta(hours=48)
    session.commit()

    assert repository.is_earnings_calendar_fresh(session, market="BIST", max_age_hours=24) is False


def test_is_earnings_calendar_fresh_farkli_market_etkilemez(session) -> None:
    repository.upsert_earnings_calendar(session, [_fake_earnings_record(market="BIST")])
    assert repository.is_earnings_calendar_fresh(session, market="NASDAQ") is False


# --- Fon (Faz 17) -----------------------------------------------------


def test_save_fund_info_ilk_cagrida_ekler_ikinci_cagrida_gunceller(session) -> None:
    repository.save_fund_info(session, "AFA", "AK PORTFÖY AMERİKA", "AK PORTFÖY YÖNETİMİ A.Ş.", "Hisse Senedi Fonu", Decimal("1.259391"), None)

    fund = repository.get_fund(session, "AFA")
    assert fund is not None
    assert fund.name == "AK PORTFÖY AMERİKA"
    assert fund.last_price == Decimal("1.259391")

    repository.save_fund_info(session, "AFA", "AK PORTFÖY AMERİKA", "AK PORTFÖY YÖNETİMİ A.Ş.", "Hisse Senedi Fonu", Decimal("1.3"), None)

    rows = session.execute(select(Fund).where(Fund.code == "AFA")).scalars().all()
    assert len(rows) == 1
    assert rows[0].last_price == Decimal("1.3")


def test_get_fund_bulunamayan_kod_none_doner(session) -> None:
    assert repository.get_fund(session, "YOKTUR") is None


def test_save_fund_holdings_ekler_ve_mukerrer_atlanir(session) -> None:
    holdings = [
        ("hisse", "AAPL", "Apple Inc.", Decimal("5.5")),
        ("repo", None, "Ters-Repo", Decimal("3.09")),
    ]
    inserted = repository.save_fund_holdings(session, "AFA", date(2026, 7, 31), holdings)
    assert inserted == 2

    inserted_again = repository.save_fund_holdings(session, "AFA", date(2026, 7, 31), holdings)
    assert inserted_again == 0

    rows = session.execute(select(FundHolding).where(FundHolding.fund_code == "AFA")).scalars().all()
    assert len(rows) == 2


def test_save_fund_holdings_farkli_rapor_tarihi_ayri_satir_olur(session) -> None:
    repository.save_fund_holdings(session, "AFA", date(2026, 6, 30), [("hisse", "AAPL", "Apple Inc.", Decimal("5.0"))])
    repository.save_fund_holdings(session, "AFA", date(2026, 7, 31), [("hisse", "AAPL", "Apple Inc.", Decimal("5.5"))])

    rows = session.execute(select(FundHolding).where(FundHolding.fund_code == "AFA")).scalars().all()
    assert len(rows) == 2


def test_get_latest_fund_holdings_en_guncel_tarihi_doner(session) -> None:
    repository.save_fund_holdings(session, "AFA", date(2026, 6, 30), [("hisse", "AAPL", "Apple Inc.", Decimal("4.0"))])
    repository.save_fund_holdings(
        session,
        "AFA",
        date(2026, 7, 31),
        [("hisse", "AAPL", "Apple Inc.", Decimal("5.5")), ("hisse", "MSFT", "Microsoft Corp.", Decimal("6.5"))],
    )

    latest = repository.get_latest_fund_holdings(session, "AFA")

    assert [h.report_date for h in latest] == [date(2026, 7, 31), date(2026, 7, 31)]
    assert [h.name for h in latest] == ["Microsoft Corp.", "Apple Inc."]  # agirliga gore buyukten kucuge


def test_get_latest_fund_holdings_hic_veri_yoksa_bos_liste_doner(session) -> None:
    assert repository.get_latest_fund_holdings(session, "YOKTUR") == []
