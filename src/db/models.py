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
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, Engine, ForeignKey, JSON, Numeric, String, UniqueConstraint, create_engine, inspect, text
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
    # Faz 16.4: X/Twitter thread'inin ilk gonderisi icin tek cumlelik "kanca"
    # (bkz. src/ai/commentary.py::Commentary.hook). Nullable -- bu sutun
    # eklenmeden ONCE onbelleklenmis kayitlarda hic yok (bkz.
    # _migrate_add_commentary_hook_column); cagiran taraf (pipeline.py)
    # None ise positives'ten yeniden kurar, YENI bir Gemini cagrisi GEREKMEZ.
    hook: Mapped[str | None] = mapped_column(String(300), nullable=True)
    summary: Mapped[str] = mapped_column(String(2000))
    positives: Mapped[list] = mapped_column(JSON)
    negatives: Mapped[list] = mapped_column(JSON)
    kap_note: Mapped[str | None] = mapped_column(String(500))
    source: Mapped[str] = mapped_column(String(20))  # "llm" | "fallback"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)


class TechnicalCommentaryCache(Base):
    """Faz 15.1: `/teknik` kartının Gemini teknik yorumu için `CommentaryCache`
    ile AYNI amaçlı (Gemini günlük kota sınırı) ama AYRI bir önbellek --
    tazelik anahtarı ÇEYREK (year/period) değil `as_of_date` (o günün
    işlem kapanışı, bkz. TechnicalSnapshot.as_of_date): teknik görünüm her
    işlem gününde değişebilir, fundamental veri gibi çeyreklik durağan
    DEĞİLDİR. Aynı (ticker, market, as_of_date) için tekrar sorgulanınca
    (örn. aynı gün birden fazla kullanıcı) Gemini TEKRAR ÇAĞRILMAZ."""

    __tablename__ = "technical_commentary_cache"
    __table_args__ = (UniqueConstraint("ticker", "market", "as_of_date", name="uq_technical_commentary_cache_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    market: Mapped[str] = mapped_column(String(10))
    as_of_date: Mapped[date] = mapped_column(Date)
    headline: Mapped[str] = mapped_column(String(255))
    hook: Mapped[str] = mapped_column(String(300))
    summary: Mapped[str] = mapped_column(String(2000))
    positives: Mapped[list] = mapped_column(JSON)
    negatives: Mapped[list] = mapped_column(JSON)
    source: Mapped[str] = mapped_column(String(20))  # "llm" | "fallback"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)


class EarningsCalendar(Base):
    """Faz 12: "Yaklaşan Bilanço Tarihleri" onbellek tablosu -- her (ticker,
    year, period) icin EN SON hesaplanan tahmini/kesin tarihi tutar (bkz.
    src/fetchers/earnings_calendar.py). `ticker` KASITLI OLARAK Company'ye
    FK DEGIL -- takvim, kullanicinin henuz hic sormadigi (Company tablosunda
    kaydi olmayan) BIST100/NASDAQ evrenindeki sirketleri de icerebilir."""

    __tablename__ = "earnings_calendar"
    __table_args__ = (UniqueConstraint("ticker", "year", "period", name="uq_earnings_calendar_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    market: Mapped[str] = mapped_column(String(10))  # "BIST" | "NASDAQ"
    company_name: Mapped[str] = mapped_column(String(255))
    year: Mapped[int]
    period: Mapped[int]  # 3, 6, 9 veya 12
    expected_date: Mapped[date] = mapped_column(Date)
    confidence: Mapped[str] = mapped_column(String(20))  # "kesin" | "tahmini" | "son_tarih"
    source: Mapped[str] = mapped_column(String(100))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)


class Fund(Base):
    """Faz 17: Türk yatırım fonları (TEFAS) veri katmanı -- bkz.
    src/fetchers/tefas.py. `code` TEFAS fon kodudur (örn. "AFA").
    `last_price_date` HER ZAMAN None kalabilir -- tefas.py'nin
    fonBilgiGetir yanıtında bu tarih YOK (bkz. tefas.py modül üst notu,
    fiyat açıklanma zamanlaması bu fazda doğrulanamadı)."""

    __tablename__ = "fund"

    code: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255))
    founder: Mapped[str | None] = mapped_column(String(255))
    fund_type: Mapped[str | None] = mapped_column(String(100))
    last_price: Mapped[Decimal | None] = mapped_column(Numeric(24, 6))
    last_price_date: Mapped[date | None] = mapped_column(Date)
    last_updated: Mapped[datetime | None] = mapped_column(DateTime)


class FundHolding(Base):
    """Faz 17: bir fonun belirli bir rapor tarihindeki hisse/varlık bazlı
    içeriği -- bkz. src/fetchers/kap_fund_portfolio.py. ⚠️ Bu fazda
    kap_fund_portfolio.fetch_latest_portfolio() CANLI hiçbir "Portföy
    Dağılım Raporu" örneğine ulaşamadığı için (bkz. o modülün üst notu)
    bu tablo şu an İÇİ BOŞ kalır -- şema, gelecekte gerçek bir kaynak
    bulunduğunda kullanılmak üzere hazırlandı (Kural: DB katmanı kur,
    tahmin/kart YAPMA)."""

    __tablename__ = "fund_holding"
    # 🚨 CANLI HATA + DÜZELTME (Faz 19, 2026-08-05): eskiden kısıt
    # (fund_code, report_date, name) idi -- 'name' fon-içinde-fon
    # holding'lerinde YÖNETİCİ ŞİRKET adı (örn. "PUSULA PORTFÖY
    # YÖNETİMİ A.Ş.") olduğu için BİRDEN FAZLA farklı ticker (PCS/PDG/
    # PKZ/PRY gibi) AYNI ismi paylaşabiliyor -- IntegrityError'a yol
    # açıyordu (kullanıcı raporu: PHE sorgusu 6-7 dakika "asılı kaldı",
    # kök neden bu hatanın sessizce hiçbir yanıt gönderilmeden
    # patlamasıydı). `ticker` (nakit residual'da None olsa bile rapor
    # başına TEK bir residual satırı olur) doğru doğal anahtardır --
    # bkz. `src.db.models._migrate_fix_fund_holding_unique_constraint`
    # (eski kısıtlı tabloları otomatik düzeltir).
    __table_args__ = (UniqueConstraint("fund_code", "report_date", "ticker", "name", name="uq_fund_holding_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fund_code: Mapped[str] = mapped_column(ForeignKey("fund.code"), index=True)
    report_date: Mapped[date] = mapped_column(Date)
    instrument_type: Mapped[str] = mapped_column(String(50))  # "hisse" | "tahvil" | "repo" | ...
    ticker: Mapped[str | None] = mapped_column(String(20))  # hisse ise BIST kodu
    name: Mapped[str] = mapped_column(String(255))
    weight_pct: Mapped[Decimal] = mapped_column(Numeric(9, 4))


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


def _migrate_add_commentary_hook_column(engine: Engine) -> None:
    """Faz 16.4 (X/Twitter thread formatı) öncesi oluşturulmuş veritabanlarında
    'commentary_cache' tablosu zaten var ama 'hook' sütunu YOK --
    _migrate_add_market_column ile AYNI ilke: idempotent ALTER TABLE, sütun
    zaten varsa hiçbir şey yapılmaz. Eski satırlar NULL kalır (pipeline.py
    bunu positives'ten yeniden kurar, veri kaybı/hata OLUŞTURMAZ)."""
    inspector = inspect(engine)
    if "commentary_cache" not in inspector.get_table_names():
        return  # create_all() zaten dogru sekilde (hook DAHIL) olusturacak
    existing_columns = {col["name"] for col in inspector.get_columns("commentary_cache")}
    if "hook" in existing_columns:
        return
    logger.info("Migration: 'commentary_cache' tablosuna 'hook' sutunu ekleniyor.")
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE commentary_cache ADD COLUMN hook VARCHAR(300)"))


def _migrate_fix_fund_holding_unique_constraint(engine: Engine) -> None:
    """Faz 19 CANLI hata (bkz. `FundHolding.__table_args__` üst notu):
    ESKİ kısıtla (fund_code, report_date, name) oluşturulmuş bir
    'fund_holding' tablosu varsa DÜŞÜRÜLÜR -- hemen ardından çağrılan
    `create_all()` DOĞRU kısıtla (ticker DAHİL) yeniden oluşturur.

    Veri kaybı riski YOK: bu tablo Faz 17'den beri hep BOŞ kalmıştı (Faz
    19'un DB önbellek katmanı ilk gerçek yazıcısıydı, bkz. o modülün üst
    notu) -- ne varsa zaten sadece birkaç saatlik bir önbellek, KAP'tan
    HER ZAMAN yeniden türetilebilir. `create_all()`'DAN ÖNCE çağrılmalı
    (SQLAlchemy var olan bir tabloya DOKUNMAZ, bu yüzden ESKİ şema
    ÖNCE düşürülmeli ki create_all() onu YENİDEN, doğru şemayla kursun).
    """
    inspector = inspect(engine)
    if "fund_holding" not in inspector.get_table_names():
        return
    for constraint in inspector.get_unique_constraints("fund_holding"):
        if set(constraint.get("column_names", [])) == {"fund_code", "report_date", "name"}:
            logger.info("Migration: eski kısıtlı 'fund_holding' tablosu düşürülüyor (doğru şemayla yeniden kurulacak).")
            with engine.begin() as connection:
                connection.execute(text("DROP TABLE fund_holding"))
            return


def init_db(engine: Engine | None = None) -> None:
    """Tablolari olusturur (varsa dokunmaz -- create_all idempotenttir) VE
    var olan tablolarda eksik sutunlari migrate eder (bkz. _migrate_add_market_column,
    _migrate_add_commentary_hook_column).

    `engine` verilmezse varsayilan (config.DATABASE_URL'e bagli) engine
    kullanilir. Uygulama ilk calistiginda repository.get_session() bunu
    otomatik tetikler; testler kendi izole engine'leriyle acikca cagirir.
    """
    target_engine = engine if engine is not None else default_engine
    _migrate_fix_fund_holding_unique_constraint(target_engine)  # create_all() ONCESI -- eski semali tabloyu dusurebilir
    Base.metadata.create_all(bind=target_engine)
    _migrate_add_market_column(target_engine)
    _migrate_add_commentary_hook_column(target_engine)


# Uygulamanin varsayilan (production) baglantisi. Testler bunu KULLANMAZ;
# create_engine_and_session() ile kendi izole engine'lerini olustururlar.
default_engine, DefaultSessionLocal = create_engine_and_session(config.DATABASE_URL)
