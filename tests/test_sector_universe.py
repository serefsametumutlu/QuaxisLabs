"""Faz 2 (docs/spec/spec_sektor_evren.md) teslim kriteri: KAP/SIC -> ortak
üst-sektör eşleme tablolarını, sirket_turu türetmesini, Company migration'ını
ve scripts/refresh_universe.py'nin NASDAQ zenginleştirme kuyruğu sorgusunu
doğrulayan testler -- spec "Test senaryoları" bölümündeki 8 madde BİREBİR.

Gerçek SEC/KAP API'sine BURADA ÇIKILMAZ -- SIC değerleri spec'te CANLI
doğrulanmış 10 resmi NASDAQ hissesinin sabit tablosundan (regresyon verisi
olarak) kullanılır; KAP tablosu tamamen statik/elle denetlenebilir bir
sözlüktür.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import inspect, text

from src.db import models, repository
from src.db.models import Company
from src.fetchers import kap, sec_edgar

import scripts.refresh_universe as refresh_universe


# --- 1. KAP_SEKTOR_TO_UST_SEKTOR: her 48 anahtarın değeri geçerli üst-sektör -----------------------------------------------------


def test_kap_sektor_to_ust_sektor_48_anahtar_icerir() -> None:
    assert len(kap.KAP_SEKTOR_TO_UST_SEKTOR) == 48


def test_kap_sektor_to_ust_sektor_her_deger_gecerli_ust_sektor() -> None:
    for fine_sector, ust_sektor in kap.KAP_SEKTOR_TO_UST_SEKTOR.items():
        assert ust_sektor in kap.UST_SEKTOR_DEGERLERI, f"'{fine_sector}' -> '{ust_sektor}' gecersiz üst-sektör"


def test_ust_sektor_degerleri_11_grup() -> None:
    assert len(kap.UST_SEKTOR_DEGERLERI) == 11


# --- 2. SIC_RANGE_TO_UST_SEKTOR: aralıklar ÇAKIŞMIYOR (en dar aralık önce) -----------------------------------------------------


def test_sic_range_tablosu_kismi_cakisma_icermez() -> None:
    """Herhangi iki aralık ÇAKIŞIYORSA (kesişim boş değilse) biri diğerinin
    TAMAMEN İÇİNDE (kasıtlı iç içe aralık, örn. 2830-2836 içinde 2800-2899)
    olmalı -- KISMİ çakışma (ne tam iç içe ne ayrık) BUG'dır."""
    ranges = sec_edgar.SIC_RANGE_TO_UST_SEKTOR
    for i, (lo1, hi1, _) in enumerate(ranges):
        for j in range(i + 1, len(ranges)):
            lo2, hi2, _ = ranges[j]
            disjoint = hi1 < lo2 or hi2 < lo1
            if disjoint:
                continue
            fully_nested = (lo1 <= lo2 and hi2 <= hi1) or (lo2 <= lo1 and hi1 <= hi2)
            assert fully_nested, (
                f"Kısmi çakışma tespit edildi: ({lo1},{hi1}) ile ({lo2},{hi2}) -- "
                "aralıklar ya tamamen AYRIK ya da biri diğerinin TAMAMEN İÇİNDE olmalı."
            )


def test_sic_range_tablosu_dar_aralik_genis_olandan_once_gelir() -> None:
    """Bir aralık başka bir aralığı TAMAMEN içeriyorsa (kasıtlı iç içe çift),
    DAR (içteki) aralık listede daha ÖNCE (küçük index) yer almalı -- "ilk
    eşleşen kullanılır" kuralı geregi (bkz. ust_sektor_for_sic())."""
    ranges = sec_edgar.SIC_RANGE_TO_UST_SEKTOR
    for i, (lo1, hi1, _) in enumerate(ranges):
        for j in range(i + 1, len(ranges)):
            lo2, hi2, _ = ranges[j]
            if (lo1, hi1) == (lo2, hi2):
                continue
            wide_contains_narrow_but_wide_first = lo1 <= lo2 and hi2 <= hi1
            assert not wide_contains_narrow_but_wide_first, (
                f"Geniş aralık ({lo1},{hi1}) dar aralıktan ({lo2},{hi2}) ÖNCE geliyor "
                f"(index {i} < {j}) -- dar aralık önce sıralanmalı."
            )


def test_sic_3674_teknoloji_3300_ana_metaller_3300_3200_arasina_dusmez() -> None:
    """Spec'teki somut örnek (Test senaryosu #2) BİREBİR."""
    assert sec_edgar.ust_sektor_for_sic("TEST", "3674") == "Teknoloji"  # [3660-3679]
    assert sec_edgar.ust_sektor_for_sic("TEST", "3300") == "Ana Metaller ve Madencilik"  # [3300-3399]
    # 3300, [3200-3299]'un İÇİNDE DEĞİL (üst sınır 3299 < 3300).
    lo, hi, _ = next(r for r in sec_edgar.SIC_RANGE_TO_UST_SEKTOR if r[:2] == (3200, 3299))
    assert not (lo <= 3300 <= hi)


# --- 3. 10 resmi NASDAQ ticker'ının SIC koduyla doğru ust_sektor'a eşlendiği (regresyon) -----------------------------------------------------


_CANLI_DOGRULANMIS_NASDAQ_SIC = [
    ("AAPL", "3571", "Teknoloji"),
    ("NVDA", "3674", "Teknoloji"),
    ("AMD", "3674", "Teknoloji"),
    ("MSFT", "7372", "Teknoloji"),
    ("GOOGL", "7370", "İletişim"),
    ("META", "7370", "İletişim"),
    ("AMZN", "5961", "Tüketici (Döngüsel)"),
    ("TSLA", "3711", "Tüketici (Döngüsel)"),
    ("NFLX", "7841", "İletişim"),
    ("PYPL", "7389", "Finans"),
]


@pytest.mark.parametrize("ticker, sic, expected_ust_sektor", _CANLI_DOGRULANMIS_NASDAQ_SIC)
def test_10_resmi_nasdaq_ticker_canli_sic_ile_dogru_ust_sektore_eslenir(ticker, sic, expected_ust_sektor) -> None:
    assert sec_edgar.ust_sektor_for_sic(ticker, sic) == expected_ust_sektor


@pytest.mark.parametrize("ticker, sic, expected_ust_sektor", _CANLI_DOGRULANMIS_NASDAQ_SIC)
def test_10_resmi_nasdaq_ticker_sirket_turu_sanayi_veya_finans_disi_bekleniyor(ticker, sic, expected_ust_sektor) -> None:
    # Bu 10 hisse hiçbiri Finans/GYO (SIC 6000-6999) aralığında değil --
    # hepsinin sirket_turu 'sanayi' olmalı (spec NASDAQ kolonu: "6000-6999
    # ve 6798 DIŞINDA HER ŞEY -> sanayi").
    assert sec_edgar.sirket_turu_for_sic(sic) == "sanayi"


# --- 4. SIC_TICKER_SECTOR_OVERRIDES aralık tablosundan HER ZAMAN önce uygulanır -----------------------------------------------------


def test_sic_override_googl_meta_pypl_aralik_tablosunu_ezer() -> None:
    # GOOGL/META gerçek SIC'i (7370) aralık tablosunda "Teknoloji" verirdi --
    # override bunu "İletişim"e ÇEVİRİR.
    assert sec_edgar.SIC_RANGE_TO_UST_SEKTOR  # tabloyu kullanmadan da dogrulayalim
    naive_range_result = sec_edgar.ust_sektor_for_sic("BASKA_TICKER_OVERRIDE_YOK", "7370")
    assert naive_range_result == "Teknoloji"  # override YOKKEN aralık tablosunun verdiği deger

    assert sec_edgar.ust_sektor_for_sic("GOOGL", "7370") == "İletişim"
    assert sec_edgar.ust_sektor_for_sic("META", "7370") == "İletişim"
    assert sec_edgar.ust_sektor_for_sic("PYPL", "7389") == "Finans"


def test_sic_override_sic_kodu_uyusmasa_da_uygulanir() -> None:
    """Override, SIC kodu ne olursa olsun (hatta None/bilinmeyen bir kod
    olsa da) HER ZAMAN önce uygulanır -- 'kural sırası' testi."""
    assert sec_edgar.ust_sektor_for_sic("GOOGL", "9999") == "İletişim"
    assert sec_edgar.ust_sektor_for_sic("PYPL", None) == "Finans"


# --- 5. _next_batch(): sic_code IS NULL / eski / taze / limit -----------------------------------------------------


@pytest.fixture()
def session(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'test.db'}"
    engine, session_factory = models.create_engine_and_session(db_url)
    models.init_db(engine)
    db_session = session_factory()
    yield db_session
    db_session.close()


def test_next_batch_sic_code_null_satirlari_doner(session) -> None:
    repository.upsert_sector_taxonomy(session, "AAAA", market="NASDAQ", cik="0000000001", touch_sector_updated_at=False)
    session.commit()

    batch = refresh_universe._next_batch(session, limit=10)

    assert [c.ticker for c in batch] == ["AAAA"]


def test_next_batch_90_gunden_eski_satirlari_da_doner(session) -> None:
    company = repository.upsert_sector_taxonomy(
        session, "ESKI", market="NASDAQ", sic_code="3571", ust_sektor="Teknoloji", sirket_turu="sanayi",
    )
    session.commit()
    company.sector_updated_at = models.utcnow_naive() - timedelta(days=91)
    session.commit()

    batch = refresh_universe._next_batch(session, limit=10)

    assert [c.ticker for c in batch] == ["ESKI"]


def test_next_batch_taze_satirlari_dondurmez(session) -> None:
    # Faz 5 (docs/spec/spec_dashboard.md §NASDAQ "tam evren" kapsamı, "Tek
    # seferlik backfill"): _next_batch artık filer_category BOŞ olan
    # satırları da (sic_code dolu olsa bile) kuyruğa alır -- bu yüzden
    # "gerçekten tamamen taze/tam işlenmiş" bir satır filer_category'yi de
    # DOLU taşımalı, aksi halde backfill koşulu satırı YENİDEN kuyruğa alır
    # (bu KASITLI, spec'in istediği davranış).
    repository.upsert_sector_taxonomy(
        session, "TAZE", market="NASDAQ", sic_code="3571", ust_sektor="Teknoloji", sirket_turu="sanayi",
        filer_category="Large accelerated filer",
    )
    session.commit()

    batch = refresh_universe._next_batch(session, limit=10)

    assert batch == []


def test_next_batch_filer_category_bos_satirlari_backfill_icin_doner(session) -> None:
    """Faz 5 §NASDAQ "tam evren" kapsamı, "Tek seferlik backfill": Faz 2'de
    ZATEN zenginleştirilmiş (sic_code dolu) ama filer_category HENÜZ
    YOKKEN işlenmiş bir satır -- 90 günlük tazelik penceresinden BAĞIMSIZ
    olarak yeniden kuyruğa girer."""
    repository.upsert_sector_taxonomy(
        session, "ESKIBACKFILL", market="NASDAQ", sic_code="3571", ust_sektor="Teknoloji", sirket_turu="sanayi",
    )
    session.commit()

    batch = refresh_universe._next_batch(session, limit=10)

    assert [c.ticker for c in batch] == ["ESKIBACKFILL"]


def test_next_batch_limit_parametresine_uyar(session) -> None:
    for i in range(5):
        repository.upsert_sector_taxonomy(session, f"T{i}", market="NASDAQ", cik=f"{i:010d}", touch_sector_updated_at=False)
    session.commit()

    batch = refresh_universe._next_batch(session, limit=2)

    assert len(batch) == 2


def test_next_batch_bist_satirlarini_karistirmaz(session) -> None:
    repository.upsert_sector_taxonomy(session, "THYAO", market="BIST", sector="ULAŞTIRMA")
    session.commit()

    batch = refresh_universe._next_batch(session, limit=10)

    assert batch == []


# --- 6. Migration idempotentliği -----------------------------------------------------


def test_migrate_add_sector_taxonomy_columns_eski_semaya_sutunlari_ekler(tmp_path) -> None:
    """Faz 2 ÖNCESİ oluşturulmuş (yeni sütunlar YOK) bir 'company' tablosunu
    simüle eder -- init_db() bunu GÜVENLİ şekilde migrate etmeli."""
    db_url = f"sqlite:///{tmp_path / 'legacy.db'}"
    engine, _ = models.create_engine_and_session(db_url)

    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE company ("
                "ticker VARCHAR(20) PRIMARY KEY, name VARCHAR(255), sector VARCHAR(100), "
                "financial_group VARCHAR(20), kap_member_id VARCHAR(64), last_updated DATETIME, "
                "market VARCHAR(10))"
            )
        )
        connection.execute(text("INSERT INTO company (ticker, market) VALUES ('THYAO', 'BIST')"))

    models.init_db(engine)

    inspector_columns = {col["name"] for col in inspect(engine).get_columns("company")}
    for expected_column in (
        "ust_sektor", "sirket_turu", "sic_code", "exchange", "cik", "index_memberships", "sector_updated_at",
    ):
        assert expected_column in inspector_columns

    with engine.connect() as connection:
        row = connection.execute(text("SELECT ticker, ust_sektor FROM company WHERE ticker = 'THYAO'")).fetchone()
    assert row == ("THYAO", None)

    # idempotentlik: tekrar cagirmak hata FIRLATMAMALI.
    models.init_db(engine)
    models._migrate_add_sector_taxonomy_columns(engine)


# --- 7. TickerMarketConflictError evren-doldurma yolunda da fırlatılır -----------------------------------------------------


def test_upsert_sector_taxonomy_farkli_market_ile_cakisirsa_hata_firlatir(session) -> None:
    repository.upsert_sector_taxonomy(session, "AAPL", market="NASDAQ", sic_code="3571")
    session.commit()

    with pytest.raises(repository.TickerMarketConflictError):
        repository.upsert_sector_taxonomy(session, "AAPL", market="BIST", sector="ULAŞTIRMA")


# --- 8. KAP'ın 48 kategorisinde OLMAYAN uydurma sektör -> ust_sektor=None, hata YOK -----------------------------------------------------


def test_ust_sektor_for_kap_bilinmeyen_sektor_none_doner_exception_firlatmaz() -> None:
    result = kap.ust_sektor_for_kap("UYDURMA_TICKER", "UYDURMA BİR SEKTÖR ADI")
    assert result is None


def test_sirket_turu_on_tahmin_from_kap_bilinmeyen_sektor_none_doner() -> None:
    assert kap.sirket_turu_on_tahmin_from_kap("UYDURMA BİR SEKTÖR ADI") is None


# --- Ek: KAP ticker override + sirket_turu ön-tahmini davranışı -----------------------------------------------------


def test_ust_sektor_for_kap_tuprs_override_enerji_doner() -> None:
    # TUPRS ince sektörde "KİMYA İLAÇ PETROL LASTİK VE PLASTİK ÜRÜNLER" olsa
    # bile (varsayılan eşleme Ana Metaller ve Madencilik) override Enerji verir.
    assert kap.ust_sektor_for_kap("TUPRS", "KİMYA İLAÇ PETROL LASTİK VE PLASTİK ÜRÜNLER") == "Enerji"
    # override YOKKEN varsayılan eşleme:
    assert kap.ust_sektor_for_kap("BASKA", "KİMYA İLAÇ PETROL LASTİK VE PLASTİK ÜRÜNLER") == "Ana Metaller ve Madencilik"


def test_sirket_turu_on_tahmin_from_kap_kesin_kategoriler() -> None:
    assert kap.sirket_turu_on_tahmin_from_kap("BANKALAR") == "banka"
    assert kap.sirket_turu_on_tahmin_from_kap("SİGORTA ŞİRKETLERİ") == "sigorta"
    assert kap.sirket_turu_on_tahmin_from_kap("FİNANSMAN ŞİRKETLERİ") == "finansman"
    assert kap.sirket_turu_on_tahmin_from_kap("GAYRİMENKUL YATIRIM ORTAKLIKLARI") == "gyo"


def test_sirket_turu_on_tahmin_from_kap_sanayi_ust_sektorde_sanayi_doner() -> None:
    assert kap.sirket_turu_on_tahmin_from_kap("ULAŞTIRMA VE DEPOLAMA") == "sanayi"


def test_sirket_turu_on_tahmin_from_kap_belirsiz_finans_alt_kategori_none_doner() -> None:
    # "ARACI KURUMLAR" Finans üst-sektöründe ama BANKALAR/SİGORTA/FİNANSMAN/GYO
    # DEĞİL -- KAP ince sektöründen banka/sigorta/finansman ayrımı YAPILAMAZ.
    assert kap.sirket_turu_on_tahmin_from_kap("ARACI KURUMLAR") is None


# --- Ek: sirket_turu_for_sic (NASDAQ) sınır davranışı -----------------------------------------------------


def test_sirket_turu_for_sic_banka_finansman_sigorta_gyo_araliklari() -> None:
    assert sec_edgar.sirket_turu_for_sic("6021") == "banka"  # JPM benzeri
    assert sec_edgar.sirket_turu_for_sic("6199") == "finansman"
    assert sec_edgar.sirket_turu_for_sic("6411") == "sigorta"
    assert sec_edgar.sirket_turu_for_sic("6500") == "gyo"
    assert sec_edgar.sirket_turu_for_sic("6798") == "gyo"


def test_sirket_turu_for_sic_bilinmeyen_finans_alt_araligi_none_doner() -> None:
    # 6700-6797 (6798 haric) -- spec'te acik bir sirket_turu tanimlanmadi.
    assert sec_edgar.sirket_turu_for_sic("6726") is None


def test_sirket_turu_for_sic_sic_kodu_yoksa_none_doner() -> None:
    assert sec_edgar.sirket_turu_for_sic(None) is None
