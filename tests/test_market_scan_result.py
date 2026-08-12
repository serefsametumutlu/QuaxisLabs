"""SPEC: docs/spec/spec_dashboard.md -- `MarketScanResult` modeli,
`repository.upsert_market_scan_result()`/`get_scan_queue()`/`is_scan_fresh()`/
`get_market_scan_results()` testleri (spec "Test senaryoları" #1, #2, #5,
#9, #10 BİREBİR + ek CRUD/migration testleri).

Gerçek ağ isteği ATILMAZ -- bu modül SADECE DB katmanını test eder.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import inspect, text

from src.db import models, repository
from src.db.models import Company, EarningsCalendar, MarketScanResult


@pytest.fixture()
def session(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'test_market_scan_result.db'}"
    engine, session_factory = models.create_engine_and_session(db_url)
    models.init_db(engine)
    db_session = session_factory()
    yield db_session
    db_session.close()


def _make_company(session, ticker: str, market: str = "BIST", ust_sektor: str = "Sanayi", **kwargs) -> Company:
    repository.upsert_sector_taxonomy(session, ticker, market=market, ust_sektor=ust_sektor, sirket_turu=kwargs.pop("sirket_turu", "sanayi"), **kwargs)
    session.commit()
    return session.get(Company, ticker)


# --- Migration: yeni tablo (create_all yeterli, ALTER TABLE gerekmez) -----------------------------------------------------


def test_market_scan_result_tablosu_init_db_ile_olusur(session) -> None:
    inspector = inspect(session.get_bind())
    assert "market_scan_result" in inspector.get_table_names()


def test_company_filer_category_sutunu_migration_ile_eklenir(tmp_path) -> None:
    """Faz 5 ÖNCESİ oluşturulmuş (filer_category YOK) bir 'company' tablosunu
    simüle eder -- init_db() bunu GÜVENLİ şekilde migrate etmeli (bkz.
    test_sector_universe.py'nin aynı desenli testiyle TUTARLI)."""
    db_url = f"sqlite:///{tmp_path / 'legacy_filer_category.db'}"
    engine, _ = models.create_engine_and_session(db_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE company (ticker VARCHAR(20) PRIMARY KEY, name VARCHAR(255), sector VARCHAR(100), "
                "financial_group VARCHAR(20), kap_member_id VARCHAR(64), last_updated DATETIME, market VARCHAR(10), "
                "ust_sektor VARCHAR(40), sirket_turu VARCHAR(20), sic_code VARCHAR(10), exchange VARCHAR(20), "
                "cik VARCHAR(10), index_memberships JSON, sector_updated_at DATETIME)"
            )
        )
        connection.execute(text("INSERT INTO company (ticker, market) VALUES ('AAPL', 'NASDAQ')"))

    models.init_db(engine)

    columns = {col["name"] for col in inspect(engine).get_columns("company")}
    assert "filer_category" in columns
    models.init_db(engine)  # idempotentlik


# --- upsert_market_scan_result -----------------------------------------------------


def test_faaliyet_raporu_bulgulari_sutunu_migration_ile_eklenir(tmp_path) -> None:
    """docs/spec/spec_veri_tamlik_yol_haritasi.md §Faaliyet Raporu (2026-08-12)
    ÖNCESİ oluşturulmuş (faaliyet_raporu_bulgulari YOK) bir 'market_scan_result'
    tablosunu simüle eder -- init_db() bunu GÜVENLİ şekilde migrate etmeli."""
    db_url = f"sqlite:///{tmp_path / 'legacy_faaliyet_raporu.db'}"
    engine, _ = models.create_engine_and_session(db_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE market_scan_result (ticker VARCHAR(20) PRIMARY KEY, market VARCHAR(10), "
                "scan_status VARCHAR(20))"
            )
        )
        connection.execute(text("INSERT INTO market_scan_result (ticker, market, scan_status) VALUES ('THYAO', 'BIST', 'ok')"))

    models.init_db(engine)

    inspector = inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("market_scan_result")}
    assert "faaliyet_raporu_bulgulari" in columns


# --- update_faaliyet_raporu_bulgulari (docs/spec/spec_veri_tamlik_yol_
# haritasi.md §Faaliyet Raporu) --------------------------------------------------


def test_update_faaliyet_raporu_bulgulari_diger_alanlari_ezmez(session) -> None:
    _make_company(session, "THYAO")
    repository.upsert_market_scan_result(
        session, "THYAO", "BIST", scan_status="ok",
        deger_score=Decimal("7.2"), bilesik_score=Decimal("6.9"), bilesik_badge="DENGELİ",
    )
    session.commit()

    bulgular = {"kaynak_baslik": "2025 Faaliyet Raporu", "source": "llm", "kar_kaynagi_ozeti": "test"}
    row = repository.update_faaliyet_raporu_bulgulari(session, "THYAO", "BIST", bulgular)
    session.commit()

    assert row is not None
    fetched = session.get(MarketScanResult, "THYAO")
    assert fetched.faaliyet_raporu_bulgulari == bulgular
    # ana skor alanları DOKUNULMADAN kalmalı (bkz. upsert_market_scan_result'ın
    # AKSİNE -- bu fonksiyon SADECE tek bir sütunu günceller)
    assert fetched.deger_score == Decimal("7.20")
    assert fetched.bilesik_score == Decimal("6.90")
    assert fetched.bilesik_badge == "DENGELİ"


def test_update_faaliyet_raporu_bulgulari_satir_yoksa_none_doner(session) -> None:
    assert repository.update_faaliyet_raporu_bulgulari(session, "YOKSAT", "BIST", {"a": 1}) is None


def test_update_faaliyet_raporu_bulgulari_piyasa_uyusmuyorsa_none_doner(session) -> None:
    _make_company(session, "THYAO")
    repository.upsert_market_scan_result(session, "THYAO", "BIST", scan_status="ok")
    session.commit()
    assert repository.update_faaliyet_raporu_bulgulari(session, "THYAO", "NASDAQ", {"a": 1}) is None


def test_upsert_market_scan_result_basarili_tarama_tum_alanlari_yazar(session) -> None:
    _make_company(session, "THYAO")
    row = repository.upsert_market_scan_result(
        session, "THYAO", "BIST", scan_status="ok",
        company_name="Türk Hava Yolları A.O.", ust_sektor="Sanayi", sirket_turu="sanayi", template="sanayi",
        year=2026, period=6,
        deger_score=Decimal("7.2"), deger_badge="SAĞLAM", deger_coverage_pct=Decimal("88.0"),
        bilesik_score=Decimal("6.9"), bilesik_badge="DENGELİ", bilesik_data_coverage_pct=Decimal("87.5"),
        dahil_edilen_mercekler=["değer", "kalite", "güvenlik", "büyüme"],
        current_price=Decimal("305.50"), market_cap=Decimal("428500000000"),
        pe_ratio=Decimal("6.8"), pb_ratio=Decimal("2.1"), ev_ebitda=Decimal("4.3"), currency="TRY",
    )
    session.commit()

    fetched = session.get(MarketScanResult, "THYAO")
    assert fetched.scan_status == "ok"
    assert fetched.deger_score == Decimal("7.20")
    assert fetched.bilesik_score == Decimal("6.90")
    assert fetched.dahil_edilen_mercekler == ["değer", "kalite", "güvenlik", "büyüme"]
    assert fetched.pe_ratio == Decimal("6.8000")
    assert fetched.computed_at is not None


def test_upsert_market_scan_result_ticker_basina_tek_satir_upsert(session) -> None:
    """`GeneratedCard`'ın AKSİNE -- her çağrı YENİ satır EKLEMEZ, aynı
    ticker'ın satırı GÜNCELLENİR (spec §Mimari karar 2)."""
    _make_company(session, "THYAO")
    repository.upsert_market_scan_result(session, "THYAO", "BIST", scan_status="ok", bilesik_score=Decimal("5.0"))
    session.commit()
    repository.upsert_market_scan_result(session, "THYAO", "BIST", scan_status="ok", bilesik_score=Decimal("7.5"))
    session.commit()

    rows = session.query(MarketScanResult).filter_by(ticker="THYAO").all()
    assert len(rows) == 1
    assert rows[0].bilesik_score == Decimal("7.50")


def test_upsert_market_scan_result_hata_sonrasi_eski_skor_korunur(session) -> None:
    """Spec "Test senaryoları" #5 BİREBİR: ÖNCE başarılı bir tarama (deger_score=7.2),
    sonra 'hata' -- deger_score EZİLMEZ, computed_at DEĞİŞMEZ."""
    _make_company(session, "THYAO")
    repository.upsert_market_scan_result(
        session, "THYAO", "BIST", scan_status="ok", deger_score=Decimal("7.2"), bilesik_score=Decimal("6.5"),
    )
    session.commit()
    ilk_computed_at = session.get(MarketScanResult, "THYAO").computed_at

    repository.upsert_market_scan_result(session, "THYAO", "BIST", scan_status="hata", error_detail="Ağ hatası")
    session.commit()

    row = session.get(MarketScanResult, "THYAO")
    assert row.scan_status == "hata"
    assert row.error_detail == "Ağ hatası"
    assert row.deger_score == Decimal("7.20")  # EZİLMEDİ
    assert row.bilesik_score == Decimal("6.50")  # EZİLMEDİ
    assert row.computed_at == ilk_computed_at  # GÜNCELLENMEDİ


def test_upsert_market_scan_result_ilk_taramada_hata_tum_skorlar_null(session) -> None:
    """Spec "Kenar durumlar" netleştirmesi: önceki BAŞARILI kayıt YOKSA
    ilk 'hata' tüm skor alanlarını NULL bırakır."""
    _make_company(session, "YENI")
    repository.upsert_market_scan_result(session, "YENI", "BIST", scan_status="hata", error_detail="ilk deneme başarısız")
    session.commit()

    row = session.get(MarketScanResult, "YENI")
    assert row.scan_status == "hata"
    assert row.deger_score is None
    assert row.bilesik_score is None


def test_upsert_market_scan_result_veri_yok_eski_basarili_skoru_ezer(session) -> None:
    """"veri_yok"/"desteklenmiyor" DETERMİNİSTİK sonuçlardır -- "hata"nın
    AKSİNE eski skoru KORUMAZ, tamamen üzerine yazar (dashboard JSON
    şemasındaki `mercekler: null` örneğiyle TUTARLI)."""
    _make_company(session, "ESKISIRKET")
    repository.upsert_market_scan_result(session, "ESKISIRKET", "BIST", scan_status="ok", deger_score=Decimal("7.2"))
    session.commit()

    repository.upsert_market_scan_result(session, "ESKISIRKET", "BIST", scan_status="veri_yok")
    session.commit()

    row = session.get(MarketScanResult, "ESKISIRKET")
    assert row.scan_status == "veri_yok"
    assert row.deger_score is None


# --- get_market_scan_results / is_scan_fresh -----------------------------------------------------


def test_get_market_scan_results_market_filtresi(session) -> None:
    _make_company(session, "THYAO", market="BIST")
    _make_company(session, "AAPL", market="NASDAQ", ust_sektor="Teknoloji")
    repository.upsert_market_scan_result(session, "THYAO", "BIST", scan_status="ok")
    repository.upsert_market_scan_result(session, "AAPL", "NASDAQ", scan_status="ok")
    session.commit()

    assert {r.ticker for r in repository.get_market_scan_results(session)} == {"THYAO", "AAPL"}
    assert {r.ticker for r in repository.get_market_scan_results(session, market="BIST")} == {"THYAO"}


def test_is_scan_fresh_basarili_ve_taze_ise_true(session) -> None:
    _make_company(session, "THYAO")
    repository.upsert_market_scan_result(session, "THYAO", "BIST", scan_status="ok")
    session.commit()
    assert repository.is_scan_fresh(session, "THYAO", max_age_days=7) is True


def test_is_scan_fresh_bayat_ise_false(session) -> None:
    _make_company(session, "THYAO")
    repository.upsert_market_scan_result(session, "THYAO", "BIST", scan_status="ok")
    session.commit()
    row = session.get(MarketScanResult, "THYAO")
    row.computed_at = models.utcnow_naive() - timedelta(days=8)
    session.commit()
    assert repository.is_scan_fresh(session, "THYAO", max_age_days=7) is False


def test_is_scan_fresh_hic_taranmamis_ise_false(session) -> None:
    assert repository.is_scan_fresh(session, "YOKYOK", max_age_days=7) is False


def test_is_scan_fresh_son_deneme_basarisizsa_false(session) -> None:
    _make_company(session, "THYAO")
    repository.upsert_market_scan_result(session, "THYAO", "BIST", scan_status="hata")
    session.commit()
    assert repository.is_scan_fresh(session, "THYAO", max_age_days=7) is False


# --- get_ok_scanned_tickers (scripts/kar_kaynagi_toplu.py --universe full) -----------------------------------------------------


def test_get_ok_scanned_tickers_sadece_ok_ve_dogru_market_doner(session) -> None:
    _make_company(session, "THYAO", market="BIST")
    _make_company(session, "ASELS", market="BIST")
    _make_company(session, "SAHOL", market="BIST")
    _make_company(session, "AAPL", market="NASDAQ", ust_sektor="Teknoloji")
    repository.upsert_market_scan_result(session, "THYAO", "BIST", scan_status="ok")
    repository.upsert_market_scan_result(session, "ASELS", "BIST", scan_status="hata")
    repository.upsert_market_scan_result(session, "SAHOL", "BIST", scan_status="veri_yok")
    repository.upsert_market_scan_result(session, "AAPL", "NASDAQ", scan_status="ok")
    session.commit()

    assert repository.get_ok_scanned_tickers(session, "BIST") == ["THYAO"]


def test_get_ok_scanned_tickers_alfabetik_siralidir(session) -> None:
    for ticker in ("ZORLU", "AKBNK", "MGROS"):
        _make_company(session, ticker, market="BIST")
        repository.upsert_market_scan_result(session, ticker, "BIST", scan_status="ok")
    session.commit()

    assert repository.get_ok_scanned_tickers(session, "BIST") == ["AKBNK", "MGROS", "ZORLU"]


def test_get_ok_scanned_tickers_hic_taranmamis_bos_liste(session) -> None:
    assert repository.get_ok_scanned_tickers(session, "BIST") == []


# --- get_scan_queue -- Spec "Test senaryoları" #1: sıralama/filtreleme -----------------------------------------------------


def test_get_scan_queue_ust_sektor_null_satirlar_haric_tutulur(session) -> None:
    repository.upsert_sector_taxonomy(session, "SINIFSIZ", market="BIST", ust_sektor=None)
    session.commit()
    _make_company(session, "THYAO")

    queue = repository.get_scan_queue(session, "BIST", stale_after_days=7, limit=10)

    assert [c.ticker for c in queue] == ["THYAO"]


def test_get_scan_queue_hic_taranmamis_taze_taramadan_once_gelir(session) -> None:
    _make_company(session, "YENI")
    _make_company(session, "ESKI")
    repository.upsert_market_scan_result(session, "ESKI", "BIST", scan_status="ok")
    session.commit()
    row = session.get(MarketScanResult, "ESKI")
    row.computed_at = models.utcnow_naive() - timedelta(days=8)
    session.commit()

    queue = repository.get_scan_queue(session, "BIST", stale_after_days=7, limit=10)

    assert [c.ticker for c in queue] == ["YENI", "ESKI"]


def test_get_scan_queue_taze_tarama_kuyruga_girmez(session) -> None:
    _make_company(session, "TAZE")
    repository.upsert_market_scan_result(session, "TAZE", "BIST", scan_status="ok")
    session.commit()  # computed_at = simdi (3 gun degil ama "taze" varsayimini test etmek icin asagida ayarlanacak)
    row = session.get(MarketScanResult, "TAZE")
    row.computed_at = models.utcnow_naive() - timedelta(days=3)
    session.commit()

    queue = repository.get_scan_queue(session, "BIST", stale_after_days=7, limit=10)

    assert queue == []


def test_get_scan_queue_limit_parametresine_uyar(session) -> None:
    for i in range(5):
        _make_company(session, f"T{i}")
    session.commit()

    queue = repository.get_scan_queue(session, "BIST", stale_after_days=7, limit=2)

    assert len(queue) == 2


# --- get_scan_queue -- Spec "Test senaryoları" #2: priority_tickers -----------------------------------------------------


def test_get_scan_queue_priority_ticker_taze_olsa_bile_kuyruga_girer(session) -> None:
    _make_company(session, "FORCE")
    repository.upsert_market_scan_result(session, "FORCE", "BIST", scan_status="ok")
    session.commit()
    row = session.get(MarketScanResult, "FORCE")
    row.computed_at = models.utcnow_naive() - timedelta(days=2)  # 7 GUNDEN TAZE
    session.commit()

    kuyruksuz = repository.get_scan_queue(session, "BIST", stale_after_days=7, limit=10)
    assert kuyruksuz == []

    zorlanan = repository.get_scan_queue(session, "BIST", stale_after_days=7, limit=10, priority_tickers={"FORCE"})
    assert [c.ticker for c in zorlanan] == ["FORCE"]


# --- get_scan_queue -- Spec "Test senaryoları" #9: SCAN_STALE_AFTER_DAYS_UNSUPPORTED ayrımı -----------------------------------------------------


def test_get_scan_queue_desteklenmiyor_10_gunde_standart_cagride_girmez_100_gunde_girer(session) -> None:
    _make_company(session, "DESTEKSIZ")
    repository.upsert_market_scan_result(session, "DESTEKSIZ", "BIST", scan_status="desteklenmiyor")
    session.commit()
    row = session.get(MarketScanResult, "DESTEKSIZ")
    row.computed_at = models.utcnow_naive() - timedelta(days=10)  # 7'den eski AMA 90'dan taze
    session.commit()

    standart = repository.get_scan_queue(session, "BIST", stale_after_days=7, limit=10)
    assert standart == []

    row.computed_at = models.utcnow_naive() - timedelta(days=100)  # 90'dan da eski
    session.commit()

    doksan_gunluk = repository.get_scan_queue(session, "BIST", stale_after_days=7, limit=10)
    assert [c.ticker for c in doksan_gunluk] == ["DESTEKSIZ"]


# --- get_scan_queue -- Spec "Test senaryoları" #10: NASDAQ filer_category kalite filtresi -----------------------------------------------------


def test_get_scan_queue_nasdaq_non_accelerated_filer_alt_dizgi_tuzagi(session) -> None:
    _make_company(session, "NONACC", market="NASDAQ", ust_sektor="Teknoloji", filer_category="Non-accelerated filer")
    _make_company(session, "LARGEACC", market="NASDAQ", ust_sektor="Teknoloji", filer_category="Large accelerated filer")
    _make_company(session, "BOSKATEGORI", market="NASDAQ", ust_sektor="Teknoloji", filer_category=None)
    session.commit()

    queue = repository.get_scan_queue(session, "NASDAQ", stale_after_days=7, limit=10)

    assert {c.ticker for c in queue} == {"LARGEACC"}


def test_get_scan_queue_nasdaq30_pilot_filer_category_filtresine_tabi_degil(session) -> None:
    """`--universe nasdaq30` (statik pilot liste) `get_scan_queue()`'u HİÇ
    ÇAĞIRMAZ -- bu test SADECE `get_scan_queue()`'un `market="NASDAQ"`
    çağrıldığında filtreyi UYGULADIĞINI doğrular (pilot akışı script
    seviyesinde ZATEN farklı bir kod yolu, bkz. tarama_toplu.py)."""
    _make_company(session, "NONACC", market="NASDAQ", ust_sektor="Teknoloji", filer_category="Non-accelerated filer")
    session.commit()
    assert repository.get_scan_queue(session, "NASDAQ", stale_after_days=7, limit=10) == []


# --- Formüller-2: priority_tickers kaynağı (EarningsCalendar) -- ek entegrasyon testi -----------------------------------------------------


def test_earnings_calendar_yaklasan_tarih_priority_kaynagidir(session) -> None:
    """`scripts/tarama_toplu.py::_priority_tickers()`'ın dayandığı sorgunun
    (EarningsCalendar, ±3 gün) DOĞRU satırları döndürdüğünü doğrular."""
    bugun = date.today()
    repository.upsert_earnings_calendar(
        session,
        [
            ("YAKINDA", "BIST", "Yakında A.Ş.", 2026, 6, bugun + timedelta(days=2), "tahmini", "test"),
            ("UZAK", "BIST", "Uzak A.Ş.", 2026, 6, bugun + timedelta(days=30), "tahmini", "test"),
        ],
    )
    from sqlalchemy import select

    cutoff_gecmis = models.utcnow_naive() - timedelta(days=3)
    cutoff_gelecek = models.utcnow_naive() + timedelta(days=3)
    rows = session.execute(
        select(EarningsCalendar.ticker).where(
            EarningsCalendar.market == "BIST",
            EarningsCalendar.expected_date.between(cutoff_gecmis.date(), cutoff_gelecek.date()),
        )
    ).scalars().all()
    assert set(rows) == {"YAKINDA"}
