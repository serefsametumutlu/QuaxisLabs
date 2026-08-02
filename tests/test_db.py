"""Faz 3 teslim kriteri: upsert'un mukerrer kayit olusturmadigini ve
onbellek (is_data_fresh) mantigini dogrulayan testler.

Her test kendi izole SQLite dosyasini kullanir (tmp_path) -- gercek
data/bilanco_radar.db dosyasina asla dokunulmaz.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from src.db import models, repository
from src.db.models import Company, Disclosure, FinancialPeriod


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
