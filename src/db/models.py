"""SQLAlchemy ORM modelleri: sirket, ceyreklik finansal kalem, KAP
bildirimi ve uretilen kart kaydi.

Tasarim notu: Bu modul sadece SQLite'a degil (config.DATABASE_URL
uzerinden) herhangi bir SQLAlchemy destekli veritabanina baglanabilecek
sekilde yazildi (ileride PostgreSQL'e gecis icin `create_engine_and_session()`
farkli bir DATABASE_URL ile tekrar cagrilabilir). Tum datetime alanlari
UTC'dir ve timezone bilgisi olmadan (naive) saklanir -- karsilastirmalarin
tutarli olmasi icin projede baska hicbir yerde yerel saat kullanilmamalidir.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Engine, ForeignKey, JSON, Numeric, String, UniqueConstraint, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

import config

logger = logging.getLogger(__name__)


def utcnow_naive() -> datetime:
    """Timezone-naive UTC zaman damgasi (datetime.utcnow() kullanmiyoruz,
    Python 3.12+ bunu deprecated sayiyor). repository.py tarafindan da
    kullanildigi icin ortak/public bir yardimci fonksiyondur."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "company"

    ticker: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255))
    sector: Mapped[str | None] = mapped_column(String(100))
    financial_group: Mapped[str | None] = mapped_column(String(20))  # XI_29 / UFRS / UFRS_K / UFRS_KATILIM / US_GAAP
    kap_member_id: Mapped[str | None] = mapped_column(String(64))  # kap.py'daki mkkMemberOid
    last_updated: Mapped[datetime | None] = mapped_column(DateTime)  # is_data_fresh() bu alana bakar
    # Faz 9 (NASDAQ/ABD): "BIST" | "NASDAQ" -- hangi fetcher/borsanin kullanilacagini
    # belirler (bkz. src/fetchers/sec_edgar.py). server_default="BIST" SAYESINDE
    # mevcut (Faz 9 ONCESI olusturulmus) satirlar ALTER TABLE sirasinda BIST
    # olarak isaretlenir -- hepsi zaten BIST hisseleridir, bu GUVENLI bir
    # varsayimdir (bkz. _migrate_add_market_column ve modul ust notu).
    market: Mapped[str] = mapped_column(String(10), default="BIST", server_default="BIST")


class FinancialPeriod(Base):
    __tablename__ = "financial_period"
    __table_args__ = (
        UniqueConstraint("ticker", "year", "period", "item_code", name="uq_financial_period_key"),
        CheckConstraint("period IN (3, 6, 9, 12)", name="ck_financial_period_donem"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(ForeignKey("company.ticker"), index=True)
    year: Mapped[int]
    period: Mapped[int]  # 3, 6, 9 veya 12
    item_code: Mapped[str] = mapped_column(String(20))  # isyatirim.py itemCode'u, orn. '3C'
    item_name: Mapped[str] = mapped_column(String(255))
    value: Mapped[Decimal] = mapped_column(Numeric(24, 4))


class Disclosure(Base):
    __tablename__ = "disclosure"
    # CANLI hata (kullanici raporu icin arastirilirken bulundu, EREGL): ayni
    # KAP bildirim URL'si BIRDEN FAZLA sirketin bildirim feed'inde
    # gorunebilir (orn. ortak/grup duyurulari) -- `url` TEK BASINA global
    # benzersiz DEGILDIR. Eskiden UNIQUE(url) idi; bu, boyle bir URL'nin
    # IKINCI sirket icin kaydedilmeye calisilmasinda IntegrityError
    # firlatip TUM run_pipeline'i (sadece "ek bilgi" olan bildirimler
    # yuzunden) COKERTIYORDU. Benzersizlik artik (ticker, url) ikilisine
    # gore -- ayni bildirim birden fazla sirket altinda ayri satir olarak
    # saklanabilir, dedup yine SADECE ayni sirket+url tekrarini engeller
    # (bkz. repository.save_disclosures).
    __table_args__ = (UniqueConstraint("ticker", "url", name="uq_disclosure_ticker_url"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(ForeignKey("company.ticker"), index=True)
    date: Mapped[datetime] = mapped_column(DateTime)
    title: Mapped[str] = mapped_column(String(500))
    category: Mapped[str] = mapped_column(String(255))
    importance: Mapped[str] = mapped_column(String(20))  # kap.py: IMPORTANCE_HIGH ("yuksek") / IMPORTANCE_LOW ("dusuk")
    url: Mapped[str] = mapped_column(String(500))


class CommentaryCache(Base):
    """(ticker, year, period) basina en son uretilen Gemini/yedek yorumu
    saklar. AMAC: Gemini ucretsiz katmaninin GUNLUK kota siniri var (canli
    dogrulandi: 20 istek/gun, model basina) -- ayni donem icin TEKRAR
    sorgulanan (orn. /son, ayni kullanicinin tekrar yazmasi, farkli
    kullanicilarin ayni hisseyi sorması) her istek Gemini'yi TEKRAR
    cagirirsa kota gereksiz yere tuketilir. run_pipeline, finansal veri
    tazeyse (is_data_fresh) bu onbellegi de kullanip Gemini'yi TEKRAR
    cagirmaz -- veri degismedigi surece yorum da degismemelidir."""

    __tablename__ = "commentary_cache"
    __table_args__ = (UniqueConstraint("ticker", "year", "period", name="uq_commentary_cache_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(ForeignKey("company.ticker"), index=True)
    year: Mapped[int]
    period: Mapped[int]
    headline: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(String(2000))
    positives: Mapped[list] = mapped_column(JSON)
    negatives: Mapped[list] = mapped_column(JSON)
    kap_note: Mapped[str | None] = mapped_column(String(500))
    source: Mapped[str] = mapped_column(String(20))  # "llm" | "fallback"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)


class GeneratedCard(Base):
    __tablename__ = "generated_card"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(ForeignKey("company.ticker"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)
    png_path: Mapped[str] = mapped_column(String(500))
    score: Mapped[float]


def create_engine_and_session(database_url: str) -> tuple[Engine, sessionmaker[Session]]:
    """Verilen DATABASE_URL icin bagimsiz bir engine + session factory olusturur.

    Testlerin gercek veritabani dosyasina dokunmadan izole bir SQLite
    dosyasi kullanabilmesi icin ayri bir engine uretebilmek gerekir; bu
    yuzden modul-seviyesi tek bir engine'e sabitlenmek yerine bu factory
    fonksiyonu disariya acilir.
    """
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, echo=False, future=True, connect_args=connect_args)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    return engine, session_factory


def _migrate_add_market_column(engine: Engine) -> None:
    """Faz 9 (NASDAQ) oncesi olusturulmus veritabanlarinda 'company' tablosu
    zaten var ama 'market' sutunu YOK -- `Base.metadata.create_all()` SADECE
    eksik TABLOLARI olusturur, VAR OLAN bir tabloya eksik SUTUN eklemez
    (SQLAlchemy'nin belgelenmis davranisi). Bu yuzden basit, idempotent bir
    ALTER TABLE burada elle uygulanir: sutun zaten varsa (yeni kurulum VEYA
    daha once migrate edilmis DB) HICBIR SEY yapilmaz.

    SQLite VE PostgreSQL ikisi de 'ALTER TABLE ... ADD COLUMN ... DEFAULT ...'
    sozdizimini destekler; mevcut satirlar server_default ('BIST') ile
    doldurulur -- bu GUVENLIDIR cunku Faz 9 ONCESI eklenen HER sirket zaten
    BIST hissesidir (NASDAQ fetcher'i bu fazdan once HIC yoktu).
    """
    inspector = inspect(engine)
    if "company" not in inspector.get_table_names():
        return  # create_all() zaten dogru sekilde (market DAHIL) olusturacak
    existing_columns = {col["name"] for col in inspector.get_columns("company")}
    if "market" in existing_columns:
        return
    logger.info("Migration: 'company' tablosuna 'market' sutunu ekleniyor (varsayilan 'BIST').")
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE company ADD COLUMN market VARCHAR(10) DEFAULT 'BIST'"))
        connection.execute(text("UPDATE company SET market = 'BIST' WHERE market IS NULL"))


def init_db(engine: Engine | None = None) -> None:
    """Tablolari olusturur (varsa dokunmaz -- create_all idempotenttir) VE
    var olan tablolarda eksik sutunlari migrate eder (bkz. _migrate_add_market_column).

    `engine` verilmezse varsayilan (config.DATABASE_URL'e bagli) engine
    kullanilir. Uygulama ilk calistiginda repository.get_session() bunu
    otomatik tetikler; testler kendi izole engine'leriyle acikca cagirir.
    """
    target_engine = engine if engine is not None else default_engine
    Base.metadata.create_all(bind=target_engine)
    _migrate_add_market_column(target_engine)


# Uygulamanin varsayilan (production) baglantisi. Testler bunu KULLANMAZ;
# create_engine_and_session() ile kendi izole engine'lerini olustururlar.
default_engine, DefaultSessionLocal = create_engine_and_session(config.DATABASE_URL)
