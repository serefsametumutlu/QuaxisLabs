"""Veritabani CRUD/upsert islemleri.

Tasarim notu: Fonksiyonlar kendi session'larini ACMAZ; cagiran taraf bir
`Session` verir (bagimlilik enjeksiyonu). Bu sayede hem uretim kodunda
(get_session() ile) hem de testlerde (izole bir SQLite dosyasina bagli
session ile) ayni fonksiyonlar degismeden kullanilabilir.

Bu modul kasitli olarak src.fetchers.* modullerini import ETMEZ (temiz
katman ayrimi): upsert_financials/save_disclosures duz tuple'lar alir,
fetcher -> repository donusumu ileride bir orkestrasyon/servis katmaninda
yapilacaktir.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Iterator

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.db.models import (
    CommentaryCache,
    Company,
    Disclosure,
    EarningsCalendar,
    FinancialPeriod,
    Fund,
    FundHolding,
    GeneratedCard,
    MarketScanResult,
    SectorMetricCache,
    TechnicalCommentaryCache,
    DefaultSessionLocal,
    utcnow_naive,
    init_db,
)

logger = logging.getLogger(__name__)

# (year, period, item_code, item_name, value)
FinancialRecord = tuple[int, int, str, str, Decimal]

# (date, title, category, importance, url)
DisclosureRecord = tuple[datetime, str, str, str, str]

# (ticker, market, company_name, year, period, expected_date, confidence, source)
EarningsCalendarRecord = tuple[str, str, str, int, int, date, str, str]

_default_db_initialized = False


class TickerMarketConflictError(Exception):
    """Bir ticker, veritabaninda ZATEN FARKLI bir 'market' (BIST/NASDAQ)
    ile kayitliyken TEKRAR farkli bir market ile yazilmaya calisildi.

    Neden var: `Company.ticker` HALA TEK BASINA birincil anahtar (bkz.
    models.Company) -- (market, ticker) bilesik anahtarina GECILMEDI, cunku
    bu, olgun/376-test-kapsamli BIST kod yolunun (fetchers/pipeline/repository
    HER YERINDE ticker'in TEK BASINA bir str oldugunu varsayan onlarca
    cagri) BASTAN AsAGI degistirilmesini gerektirirdi -- Faz 9 kapsaminin
    ("SADECE veri katmani") COK disinda, riskli bir refactor olurdu. Bugun
    icin BIST (THYAO, ASELS, ...) ile NASDAQ (AAPL, NVDA, JPM, ...) evrenleri
    arasinda GERCEK bir sembol cakismasi YOK (canli dogrulandi, proje
    evreninin 10+10 hisse listesi). Ama bu TEORIK bir risktir (orn. ileride
    3-6 harfli bir NASDAQ sembolu bir BIST koduyla CAKISABILIR).

    Bu yuzden "sessizce coz" (orn. bir market'i otomatik 'kazanan' sec) YERINE
    "algilay ve REDDET" secildi (Kural: yanlis/belirsiz veriden ISE None/hata
    iyidir) -- boyle bir cakisma GERCEKTEN olursa sistem SESSIZCE bir
    borsanin verisini digeriyle EZMEK yerine GURULTULU sekilde patlar, bir
    insan (orn. sembollerden birine ayirt edici bir onek/sonek ekleyerek)
    cozer.
    """


def _get_or_create_company(session: Session, ticker: str, market: str | None = None) -> Company:
    company = session.get(Company, ticker)
    if company is None:
        company = Company(ticker=ticker, market=market or "BIST")
        session.add(company)
    elif market is not None and company.market is not None and company.market != market:
        raise TickerMarketConflictError(
            f"'{ticker}' zaten '{company.market}' piyasasinda kayitli, '{market}' olarak "
            "TEKRAR yazilmaya calisildi -- muhtemelen BIST/NASDAQ sembol cakismasi (bkz. "
            "TickerMarketConflictError docstring'i). Otomatik cozulmedi, elle mudahale gerekir."
        )
    return company


@contextmanager
def get_session() -> Iterator[Session]:
    """Uretim kodu icin: veritabanini (ilk cagrida) hazirlar ve varsayilan
    (config.DATABASE_URL'e bagli) bir Session doner.

    Kullanim: `with get_session() as session: repository.upsert_financials(session, ...)`
    """
    global _default_db_initialized
    if not _default_db_initialized:
        init_db()
        _default_db_initialized = True

    session = DefaultSessionLocal()
    try:
        yield session
    finally:
        session.close()


def upsert_financials(session: Session, ticker: str, records: Iterable[FinancialRecord], market: str | None = None) -> int:
    """FinancialPeriod satirlarini (ticker, year, period, item_code) anahtarina
    gore upsert eder: anahtar zaten varsa deger/kalem adi GUNCELLENIR, YENI
    SATIR EKLENMEZ; yoksa yeni satir eklenir. Ayrica Company.last_updated'i
    simdiki UTC zamanina gunceller (is_data_fresh() bu alana bakar).

    CANLI HATA (Faz 10, NASDAQ ile bulundu): `market` verilmezse (varsayilan
    cagirim) brand-new bir ticker icin BURADA olusturulan Company satiri
    HER ZAMAN varsayilan "BIST" market'iyle yaratiliyordu -- pipeline.py
    _fetch_and_store_us_gaap() hemen ARDINDAN set_company_info(market="NASDAQ")
    cagirdiginda bu, henuz "BIST" olarak olusturulmus satirla CAKISIYOR
    (TickerMarketConflictError) ve HER TEK yeni NASDAQ ticker'i icin sabit
    sekilde patliyordu. Bu yuzden `pipeline._fetch_and_store_us_gaap()`
    `market="NASDAQ"` ACIKCA gecirir -- boylece satir BASTAN dogru market'le
    olusur, set_company_info()'nun sonraki cagrisi CAKISMAZ.

    Donen deger: yeni EKLENEN satir sayisi (guncellenenler dahil degil).
    """
    records = list(records)

    company = _get_or_create_company(session, ticker, market=market)

    existing_rows = session.execute(
        select(FinancialPeriod).where(FinancialPeriod.ticker == ticker)
    ).scalars().all()
    existing_by_key = {(row.year, row.period, row.item_code): row for row in existing_rows}

    inserted = 0
    for year, period, item_code, item_name, value in records:
        key = (year, period, item_code)
        existing = existing_by_key.get(key)
        if existing is not None:
            existing.item_name = item_name
            existing.value = value
        else:
            session.add(
                FinancialPeriod(
                    ticker=ticker,
                    year=year,
                    period=period,
                    item_code=item_code,
                    item_name=item_name,
                    value=value,
                )
            )
            inserted += 1

    company.last_updated = utcnow_naive()
    session.commit()
    return inserted


def set_company_info(
    session: Session,
    ticker: str,
    name: str | None = None,
    sector: str | None = None,
    financial_group: str | None = None,
    market: str | None = None,
) -> None:
    """Sirket adi/sektor/financial_group/market bilgisini gunceller (bos/None
    verilen alanlar DEGISTIRILMEZ, mevcut deger korunur). Orkestrasyon katmani
    (src/bot/pipeline.py) KAP arama sonucundan gelen sirket adini VE Is Yatirim'dan
    cozulen financial_group'u (XI_29/UFRS/UFRS_K) buraya yazar -- run_pipeline
    hangi analiz/kart yolunu (sanayi vs banka) kullanacagina bunu okuyarak karar verir.
    NASDAQ tarafi (src/fetchers/sec_edgar.py) icin `market="NASDAQ"`,
    `financial_group="US_GAAP"` ile cagrilir.

    `market` verilip ticker ZATEN FARKLI bir market ile kayitliysa
    TickerMarketConflictError firlatir (bkz. sinif docstring'i) -- BIST/NASDAQ
    sembol cakismasini SESSIZCE EZMEK yerine GURULTULU sekilde reddeder.
    """
    company = _get_or_create_company(session, ticker, market=market)
    if name:
        company.name = name
    if sector:
        company.sector = sector
    if financial_group:
        company.financial_group = financial_group
    if market:
        company.market = market
    session.commit()


def get_financials(session: Session, ticker: str, n_periods: int = 8) -> dict[tuple[int, int], dict[str, Decimal]]:
    """Bir sirketin en yeni `n_periods` donemine ait tum kalemlerini
    {(year, period): {item_code: value}} seklinde doner (yeniden eskiye).
    """
    rows = session.execute(
        select(FinancialPeriod)
        .where(FinancialPeriod.ticker == ticker)
        .order_by(FinancialPeriod.year.desc(), FinancialPeriod.period.desc())
    ).scalars().all()

    result: dict[tuple[int, int], dict[str, Decimal]] = {}
    for row in rows:
        period_key = (row.year, row.period)
        if period_key not in result and len(result) >= n_periods:
            continue
        result.setdefault(period_key, {})[row.item_code] = row.value
    return result


def save_disclosures(session: Session, ticker: str, records: Iterable[DisclosureRecord]) -> int:
    """Disclosure satirlarini `url` benzersizligine gore kaydeder; ayni url
    zaten varsa o kayit ATLANIR (guncellenmez -- bir bildirim yayinlandiktan
    sonra icerigi degismez, sadece tekrar cekilmis olabilir).

    Donen deger: yeni EKLENEN satir sayisi.
    """
    records = list(records)
    if not records:
        return 0

    _get_or_create_company(session, ticker)

    existing_urls = set(
        session.execute(select(Disclosure.url).where(Disclosure.ticker == ticker)).scalars().all()
    )

    inserted = 0
    for disclosure_date, title, category, importance, url in records:
        if url in existing_urls:
            continue
        session.add(
            Disclosure(
                ticker=ticker,
                date=disclosure_date,
                title=title,
                category=category,
                importance=importance,
                url=url,
            )
        )
        existing_urls.add(url)
        inserted += 1

    try:
        session.commit()
    except IntegrityError:
        # CANLI hata (kullanici raporu icin arastirilirken bulundu, EREGL):
        # UNIQUE(ticker, url) yine de ihlal edilebilir (orn. ayni ticker+url
        # icin es zamanli iki fetch, ya da bu fonksiyon disinda baska bir
        # yoldan zaten eklenmis bir satir) -- bildirimler karta SADECE
        # kozmetik zenginlestirme katar, TEMEL finansal veri DEGILDIR, bu
        # yuzden bu asla run_pipeline'i COKERTMEMELI (bkz. modul geneli
        # "tazelik yamasi" ilkesi, src/fetchers/kap_financials.py).
        logger.warning("%s icin bildirimler kaydedilirken UNIQUE catismasi (atlaniyor): %s kayittan bazilari", ticker, len(records))
        session.rollback()
        return 0
    return inserted


def get_recent_disclosures(session: Session, ticker: str, days: int = 90) -> list[Disclosure]:
    """Son `days` gunun bildirimlerini tarihe gore (yeniden eskiye) doner."""
    cutoff = utcnow_naive() - timedelta(days=days)
    rows = session.execute(
        select(Disclosure)
        .where(Disclosure.ticker == ticker, Disclosure.date >= cutoff)
        .order_by(Disclosure.date.desc())
    ).scalars().all()
    return list(rows)


def get_cached_commentary(session: Session, ticker: str, period: tuple[int, int]) -> CommentaryCache | None:
    """(ticker, period) icin en son onbelleklenmis yorumu doner (yoksa None).
    run_pipeline, finansal veri TAZEYSE (is_data_fresh) bunu kullanip
    Gemini'yi TEKRAR cagirmaz -- bkz. CommentaryCache modeli (Gemini
    ucretsiz katmaninin gunluk kota siniri var, canli dogrulandi: 20
    istek/gun/model; ayni donem icin tekrar sorgu bu kotayi gereksiz tuketir)."""
    year, period_no = period
    return session.execute(
        select(CommentaryCache).where(
            CommentaryCache.ticker == ticker, CommentaryCache.year == year, CommentaryCache.period == period_no
        )
    ).scalar_one_or_none()


def save_commentary(
    session: Session,
    ticker: str,
    period: tuple[int, int],
    headline: str,
    hook: str,
    summary: str,
    positives: list[str],
    negatives: list[str],
    kap_note: str | None,
    source: str,
) -> None:
    """(ticker, period) icin yorumu upsert eder (ayni donem icin TEKRAR
    cagrilirsa GUNCELLENIR, yeni satir EKLENMEZ)."""
    year, period_no = period
    existing = session.execute(
        select(CommentaryCache).where(
            CommentaryCache.ticker == ticker, CommentaryCache.year == year, CommentaryCache.period == period_no
        )
    ).scalar_one_or_none()

    if existing is not None:
        existing.headline = headline
        existing.hook = hook
        existing.summary = summary
        existing.positives = positives
        existing.negatives = negatives
        existing.kap_note = kap_note
        existing.source = source
        existing.created_at = utcnow_naive()
    else:
        _get_or_create_company(session, ticker)
        session.add(
            CommentaryCache(
                ticker=ticker, year=year, period=period_no, headline=headline, hook=hook, summary=summary,
                positives=positives, negatives=negatives, kap_note=kap_note, source=source,
            )
        )
    session.commit()


# --- Teknik Görünüm yorumu önbelleği (Faz 15.1) -----------------------------------


def get_technical_commentary(session: Session, ticker: str, market: str, as_of_date: date) -> TechnicalCommentaryCache | None:
    """(ticker, market, as_of_date) için önceden üretilmiş bir yorum var
    mı kontrol eder -- `get_commentary()` (fundamental) ile AYNI amaç,
    tazelik anahtarı ÇEYREK değil işlem günü (bkz. modül üst notu)."""
    return session.execute(
        select(TechnicalCommentaryCache).where(
            TechnicalCommentaryCache.ticker == ticker,
            TechnicalCommentaryCache.market == market,
            TechnicalCommentaryCache.as_of_date == as_of_date,
        )
    ).scalar_one_or_none()


def save_technical_commentary(
    session: Session,
    ticker: str,
    market: str,
    as_of_date: date,
    headline: str,
    hook: str,
    summary: str,
    positives: list[str],
    negatives: list[str],
    source: str,
) -> None:
    """(ticker, market, as_of_date) için yorumu upsert eder -- `save_commentary()`
    ile AYNI ilke. `Company`'ye FK OLMADIĞI için (EarningsCalendar ile AYNI
    gerekçe: `/teknik` komutu bir Bilanço Analizi ÖN KOŞULU GEREKTİRMEZ,
    ticker Company tablosunda hiç KAYITLI olmayabilir) `_get_or_create_company`
    ÇAĞRILMAZ."""
    existing = session.execute(
        select(TechnicalCommentaryCache).where(
            TechnicalCommentaryCache.ticker == ticker,
            TechnicalCommentaryCache.market == market,
            TechnicalCommentaryCache.as_of_date == as_of_date,
        )
    ).scalar_one_or_none()

    if existing is not None:
        existing.headline = headline
        existing.hook = hook
        existing.summary = summary
        existing.positives = positives
        existing.negatives = negatives
        existing.source = source
        existing.created_at = utcnow_naive()
    else:
        session.add(
            TechnicalCommentaryCache(
                ticker=ticker, market=market, as_of_date=as_of_date, headline=headline, hook=hook,
                summary=summary, positives=positives, negatives=negatives, source=source,
            )
        )
    session.commit()


def is_data_fresh(session: Session, ticker: str, max_age_hours: int = 12) -> bool:
    """Company.last_updated `max_age_hours` icindeyse True doner (yeniden
    internetten cekmeye gerek yok demektir). Sirket hic gorulmemisse veya
    henuz finansal veri cekilmemisse False doner.
    """
    company = session.get(Company, ticker)
    if company is None or company.last_updated is None:
        return False
    return (utcnow_naive() - company.last_updated) <= timedelta(hours=max_age_hours)


# --- Fon (Faz 17, TEFAS/KAP) -----------------------------------------------------


def save_fund_info(
    session: Session,
    code: str,
    name: str | None,
    founder: str | None,
    fund_type: str | None,
    last_price: Decimal | None,
    last_price_date: date | None,
) -> None:
    """Fund satirini (code anahtarina gore) upsert eder -- ayni ticker/company
    deseninde (bkz. _get_or_create_company), tekrar cagrilirsa GUNCELLENIR."""
    fund = session.get(Fund, code)
    if fund is None:
        fund = Fund(code=code)
        session.add(fund)
    fund.name = name
    fund.founder = founder
    fund.fund_type = fund_type
    fund.last_price = last_price
    fund.last_price_date = last_price_date
    fund.last_updated = utcnow_naive()
    session.commit()


def get_fund(session: Session, code: str) -> Fund | None:
    return session.get(Fund, code)


def save_fund_holdings(
    session: Session,
    fund_code: str,
    report_date: date,
    holdings: Iterable[tuple[str, str | None, str, Decimal]],
) -> int:
    """FundHolding satirlarini (fund_code, report_date, ticker, name)
    anahtarina gore kaydeder -- ayni anahtar zaten varsa ATLANIR (bir rapor
    yayinlandiktan sonra icerigi degismez, bkz. save_disclosures ile AYNI
    ilke). `holdings`: (instrument_type, ticker, name, weight_pct) tuple'lari.

    🚨 CANLI HATA + DÜZELTME (Faz 19, 2026-08-05): eskiden SADECE `name`
    anahtar olarak kullanılıyordu -- fon-içinde-fon holding'lerinde `name`
    YÖNETİCİ ŞİRKET adı olduğu için (bkz. `FundHolding.__table_args__`
    üst notu) BİRDEN FAZLA farklı ticker AYNI ismi paylaşabiliyordu, bu da
    `session.commit()` anında `IntegrityError` fırlatıp TÜM tahmin akışını
    (kullanıcıya HİÇBİR yanıt gitmeden) sessizce çökertiyordu (kullanıcı
    raporu: PHE sorgusu). Artık `ticker` de anahtara DAHİL -- hem Python
    tarafındaki bu ön-kontrol HEM DB'nin kendi kısıtı (bkz. models.py)
    AYNI (fund_code, report_date, ticker, name) anahtarını kullanıyor.

    Donen deger: yeni EKLENEN satir sayisi.
    """
    holdings = list(holdings)
    if not holdings:
        return 0

    if session.get(Fund, fund_code) is None:
        session.add(Fund(code=fund_code))

    existing_keys = set(
        session.execute(
            select(FundHolding.ticker, FundHolding.name).where(
                FundHolding.fund_code == fund_code, FundHolding.report_date == report_date
            )
        ).all()
    )

    inserted = 0
    for instrument_type, ticker, name, weight_pct in holdings:
        key = (ticker, name)
        if key in existing_keys:
            continue
        session.add(
            FundHolding(
                fund_code=fund_code,
                report_date=report_date,
                instrument_type=instrument_type,
                ticker=ticker,
                name=name,
                weight_pct=weight_pct,
            )
        )
        existing_keys.add(key)  # AYNI parti icinde tekrar edebilecek anahtarlari da yakalar
        inserted += 1
    session.commit()
    return inserted


def get_latest_fund_holdings(session: Session, fund_code: str) -> list[FundHolding]:
    """Bir fonun EN GUNCEL rapor tarihine ait holding satirlarini doner
    (agirliga gore buyukten kucuge siralanmis). Hic holding yoksa bos
    liste doner."""
    latest_date = session.execute(
        select(FundHolding.report_date)
        .where(FundHolding.fund_code == fund_code)
        .order_by(FundHolding.report_date.desc())
        .limit(1)
    ).scalar_one_or_none()
    if latest_date is None:
        return []
    rows = session.execute(
        select(FundHolding)
        .where(FundHolding.fund_code == fund_code, FundHolding.report_date == latest_date)
        .order_by(FundHolding.weight_pct.desc())
    ).scalars().all()
    return list(rows)


def get_recent_cards(session: Session, limit: int = 5) -> list[GeneratedCard]:
    """Bot genelinde en son URETILEN (herhangi bir sirket icin) en fazla
    `limit` karti tarihe gore (yeniden eskiye) doner.

    NOT: kullanici/chat bazinda DEGIL -- GeneratedCard semasinda (Faz 3'te
    tasarlandigi sekliyle) bir chat_id sutunu yoktur, bu yuzden /son komutu
    botun genelinde son uretilenleri gosterir.
    """
    rows = session.execute(
        select(GeneratedCard).order_by(GeneratedCard.created_at.desc()).limit(limit)
    ).scalars().all()
    return list(rows)


def save_generated_card(session: Session, ticker: str, png_path: str, score: float) -> GeneratedCard:
    """Uretilen bir kartin kaydini olusturur (her cagrida YENI satir - kart
    gecmisini tutmak icin upsert yapilmaz)."""
    _get_or_create_company(session, ticker)
    card = GeneratedCard(ticker=ticker, png_path=png_path, score=score, created_at=utcnow_naive())
    session.add(card)
    session.commit()
    return card


def get_score_history(session: Session, ticker: str, limit: int = 20) -> list[tuple[datetime, float]]:
    """Derin Kart'in "Skor Geçmişi" bölümü için: bir şirketin ZATEN
    `save_generated_card()` ile kaydedilmiş geçmiş skorlarını (created_at,
    score) çiftleri olarak ESKIDEN YENIYE döner (grafik/çizgi için doğal
    sıra). YENİ bir hesaplama YAPILMAZ -- sadece var olan `generated_card`
    tablosunu okur (bkz. models.GeneratedCard, Faz 3'ten beri her analizde
    doldurulur)."""
    rows = (
        session.execute(
            select(GeneratedCard.created_at, GeneratedCard.score)
            .where(GeneratedCard.ticker == ticker)
            .order_by(GeneratedCard.created_at.desc())
            .limit(limit)
        )
        .all()
    )
    return [(created_at, score) for created_at, score in reversed(rows)]


# --- Faz 16: Derin Kart -- sektör ortalaması -----------------------------------------------------


def update_company_sectors(session: Session, sector_map: dict[str, str]) -> int:
    """DB'de ZATEN kayıtlı (BIST) şirketlerin `sector` alanını toplu
    günceller -- bkz. src/fetchers/kap.py::fetch_sector_map(),
    scripts/refresh_sector_cache.py (refresh_takvim_cache.py ile AYNI ilke:
    ayrı/zamanlanmış bir süreçte çalışır, ana pipeline'ı BLOKLAMAZ). YENİ
    bir Company satırı OLUŞTURULMAZ -- sadece daha önce en az bir kez
    analiz edilmiş (dolayısıyla DB'de zaten var olan) şirketler için
    anlamlıdır. Güncellenen satır sayısını döner."""
    rows = session.execute(select(Company).where(Company.market == "BIST")).scalars().all()
    updated = 0
    for company in rows:
        sector = sector_map.get(company.ticker)
        if sector and company.sector != sector:
            company.sector = sector
            updated += 1
    session.commit()
    return updated


def upsert_sector_taxonomy(
    session: Session,
    ticker: str,
    market: str,
    sector: str | None = None,
    ust_sektor: str | None = None,
    sirket_turu: str | None = None,
    sic_code: str | None = None,
    exchange: str | None = None,
    cik: str | None = None,
    filer_category: str | None = None,
    touch_sector_updated_at: bool = True,
) -> Company:
    """Faz 2 (docs/spec/spec_sektor_evren.md): scripts/refresh_universe.py için
    bir Company satırını (yoksa OLUŞTURARAK) sektör/evren alanlarıyla günceller
    -- `set_company_info()` ile AYNI ilke (None verilen alan DEĞİŞTİRİLMEZ),
    SADECE bu spec'in yeni alanlarına (ust_sektor, sirket_turu, sic_code,
    exchange, cik) ve `sector`'a (KAP ince sektör / SEC sicDescription --
    Company'nin ZATEN var olan alanı, spec ile İSMİ DEĞİŞTİRİLMEDİ, kullanım
    alanı NASDAQ'ı da kapsayacak şekilde GENİŞLETİLDİ) odaklanır.

    `filer_category` (Faz 5, docs/spec/spec_dashboard.md §NASDAQ "tam evren"
    kapsamı, KESİN karar): SEC submissions'ın AYNI yanıtından (sic_code ile
    BİRLİKTE, SIFIR EK AĞ İSTEĞİ) gelen resmi filer-durumu etiketi -- SADECE
    NASDAQ satırlarında dolar.

    `market` HER ZAMAN açıkça verilir -- evren-doldurma script'i yeni bir
    Company satırı OLUŞTURABİLİR. TickerMarketConflictError (bkz. sınıf
    docstring'i) burada SESSİZCE YUTULMAZ, `_get_or_create_company` yolu
    üzerinden çağırana FIRLATILIR (spec "Kenar durumlar" bölümü: BIST/NASDAQ
    sembol çakışması sessizce ezilmemeli).

    `touch_sector_updated_at=False`: NASDAQ Adım 1'in (bkz. spec "Tazelik ve
    checkpoint tasarımı") ucuz bulk-keşif satırları için -- bu satırlar HENÜZ
    zenginleştirilmedi (sic_code=None kalır), bu yüzden "sektör verisi
    şimdi tazelendi" damgası VURULMAMALI; `_next_batch()` sorgusu zaten
    `sic_code IS NULL` koşuluyla bu satırları YİNE DE kuyruğa alır.

    `session.commit()` BURADA YAPILMAZ -- çağıran taraf (refresh_universe.py)
    toplu işi TEK commit ile bitirir (binlerce satırlık NASDAQ evreninde her
    satırda ayrı commit performans kaybı yaratır).
    """
    company = _get_or_create_company(session, ticker, market=market)
    if sector:
        company.sector = sector
    if ust_sektor is not None:
        company.ust_sektor = ust_sektor
    if sirket_turu is not None:
        company.sirket_turu = sirket_turu
    if sic_code is not None:
        company.sic_code = sic_code
    if exchange is not None:
        company.exchange = exchange
    if cik is not None:
        company.cik = cik
    if filer_category is not None:
        company.filer_category = filer_category
    if touch_sector_updated_at:
        company.sector_updated_at = utcnow_naive()
    return company


def get_sector_peer_tickers(session: Session, sector: str, financial_group: str, exclude_ticker: str) -> list[str]:
    """Derin Kart'ın "Karşılaştırma Ortalaması" çizgisi için: AYNI sektör +
    AYNI financial_group'taki DİĞER (kendisi hariç) şirketlerin ticker
    listesini döner. SADECE `update_company_sectors()` ile sektörü DOLDURULMUŞ
    satırlar dahil olur -- sektör hiç doldurulmamışsa (henüz
    `refresh_sector_cache.py` çalıştırılmamışsa) boş liste döner (K4:
    yeterli veri yoksa uydurma yapılmaz, ikinci çizgi gösterilmez)."""
    rows = session.execute(
        select(Company.ticker).where(
            Company.sector == sector,
            Company.financial_group == financial_group,
            Company.ticker != exclude_ticker,
        )
    ).scalars().all()
    return list(rows)


def get_sector_peer_tickers_v2(
    session: Session, ust_sektor: str, sirket_turu: str, exclude_ticker: str | None = None, market: str | None = None
) -> list[str]:
    """`get_sector_peer_tickers()`'ın Faz 3c YÜKSELTMESİ -- gruplama anahtarı
    `(sector, financial_group)` YERİNE `(ust_sektor, sirket_turu)` (spec_
    sektor_evren.md "Mevcut sınırlama tespiti": eski fonksiyon BİST-ince-
    sektör bazlıydı ve NASDAQ'ı hiç KAPSAMIYORDU) -- bu fonksiyon İKİ
    piyasayı BİRLİKTE gören ortak eksende çalışır (`market` verilirse TEK
    piyasaya daraltılabilir, verilmezse BİST+NASDAQ BİRLİKTE taranır).

    Eski `get_sector_peer_tickers()` DEĞİŞTİRİLMEDİ (v1/Derin Kart hâlâ onu
    kullanır, persona kural 8) -- bu YENİ, AYRI bir fonksiyondur."""
    conditions = [Company.ust_sektor == ust_sektor, Company.sirket_turu == sirket_turu]
    if exclude_ticker is not None:
        conditions.append(Company.ticker != exclude_ticker)
    if market is not None:
        conditions.append(Company.market == market)
    rows = session.execute(select(Company.ticker).where(*conditions)).scalars().all()
    return list(rows)


def get_sector_metric_cache(
    session: Session, ust_sektor: str, sirket_turu: str, metric: str, period: tuple[int, int], max_age_hours: int = 12
) -> SectorMetricCache | None:
    """Faz 3c -- `(ust_sektor, sirket_turu, metric, year, period)` için
    DÖNEM BAZLI önbelleklenmiş robust istatistiği (n, medyan, mad) döner.
    Kayıt yoksa VEYA `max_age_hours`'tan eskiyse `None` döner (çağıran
    taraf -- pipeline.py -- bu durumda `src.analysis.lens_common.
    robust_istatistik()`'i YENİDEN çalıştırıp `save_sector_metric_cache()`
    ile üzerine yazmalıdır; bu fonksiyon hesaplama YAPMAZ, SADECE okur).

    `max_age_hours=12`: mevcut `is_data_fresh()` ile AYNI muhafazakar
    pencere (bu tabloda DB'nin İÇİNE her yeni analiz edilen şirketle
    büyüyen bir örneklem var -- taksonomi önbelleğinin (90 gün) AKSİNE bu
    dağılım günlük ölçekte anlamlı değişebilir)."""
    year, period_no = period
    row = session.execute(
        select(SectorMetricCache).where(
            SectorMetricCache.ust_sektor == ust_sektor,
            SectorMetricCache.sirket_turu == sirket_turu,
            SectorMetricCache.metric == metric,
            SectorMetricCache.year == year,
            SectorMetricCache.period == period_no,
        )
    ).scalar_one_or_none()
    if row is None:
        return None
    if utcnow_naive() - row.updated_at > timedelta(hours=max_age_hours):
        return None
    return row


def save_sector_metric_cache(
    session: Session,
    ust_sektor: str,
    sirket_turu: str,
    metric: str,
    period: tuple[int, int],
    n: int,
    medyan: Decimal,
    mad: Decimal,
) -> SectorMetricCache:
    """`get_sector_metric_cache()`'in yazma tarafı -- upsert (aynı anahtar
    zaten varsa GÜNCELLENİR, yeni satır oluşturulmaz)."""
    year, period_no = period
    row = session.execute(
        select(SectorMetricCache).where(
            SectorMetricCache.ust_sektor == ust_sektor,
            SectorMetricCache.sirket_turu == sirket_turu,
            SectorMetricCache.metric == metric,
            SectorMetricCache.year == year,
            SectorMetricCache.period == period_no,
        )
    ).scalar_one_or_none()
    if row is None:
        row = SectorMetricCache(
            ust_sektor=ust_sektor, sirket_turu=sirket_turu, metric=metric, year=year, period=period_no,
            n=n, medyan=medyan, mad=mad,
        )
        session.add(row)
    else:
        row.n = n
        row.medyan = medyan
        row.mad = mad
        row.updated_at = utcnow_naive()
    session.commit()
    return row


_SECTOR_METRIC_DISTRIBUTION_COLUMNS = {"pe_ratio": MarketScanResult.pe_ratio, "pb_ratio": MarketScanResult.pb_ratio}


def get_sector_metric_distribution(
    session: Session,
    ust_sektor: str,
    sirket_turu: str,
    metric: str,
    market: str | None = None,
    exclude_ticker: str | None = None,
) -> list[Decimal]:
    """DÜZELTME (kod-geliştirici turu, 2026-08-12): `get_sector_metric_cache`/
    `save_sector_metric_cache` şimdiye kadar hiçbir yerden BESLENMİYORDU --
    `lens_common.SektorIstatistigi` docstring'inin vaat ettiği
    `get_sector_metric_distribution` HİÇ YAZILMAMIŞTI, bu yüzden Değer
    merceğinin "Sektöre Göreli Konum" bileşeni `pipeline.py`'de HER ZAMAN
    `sektor_pe=None, sektor_pb=None` ile çağrılıyor, kaç peer taranmış
    olursa olsun bileşen DAİMA atlanıyordu. Bu fonksiyon o eksik halkadır:
    `MarketScanResult` (scripts/tarama_toplu.py'nin ZATEN doldurduğu, ticker
    başına TEK güncel satır tutan tablo) üzerinden `(ust_sektor,
    sirket_turu)` grubundaki `scan_status="ok"` satırların ham
    `pe_ratio`/`pb_ratio` değerlerini döner -- HESAPLAMA YAPMAZ (medyan/MAD
    çağıran tarafın `lens_common.robust_istatistik()`'idir, quaxis-mimari
    anayasa: repository SADECE CRUD/okuma).

    `MarketScanResult` ticker başına TEK (en güncel) satır tuttuğu için
    (bkz. o modelin docstring'i) peer'lerin KENDİ raporlama dönemi burada
    AYRICA süzülmez -- süzülseydi n neredeyse HER ZAMAN sıfıra düşerdi
    (farklı şirketler farklı tarihlerde bilanço açıklar); F/K ve PD/DD
    zaten GÜNCEL fiyata dayalı çapraz-kesit karşılaştırmalardır (dönem
    hizalaması KALİTE/BÜYÜME gibi büyüme-oranı bazlı metriklerde daha
    kritiktir, bu fonksiyon SADECE `pe_ratio`/`pb_ratio` içindir).

    `None` değerler (hesaplanamamış) DIŞLANIR -- pozitif/negatif filtresi
    BURADA YAPILMAZ (çağıran taraf -- `pipeline.py` -- own_pe>0 ile AYNI
    ilkeyle F/K ve PD/DD için sadece pozitif değerleri robust_istatistik'e
    verir, bkz. `lens_deger._skor_sektore_goreli`)."""
    column = _SECTOR_METRIC_DISTRIBUTION_COLUMNS.get(metric)
    if column is None:
        raise ValueError(f"desteklenmeyen metric: '{metric}' (beklenen: {sorted(_SECTOR_METRIC_DISTRIBUTION_COLUMNS)})")

    conditions = [
        MarketScanResult.ust_sektor == ust_sektor,
        MarketScanResult.sirket_turu == sirket_turu,
        MarketScanResult.scan_status == "ok",
        column.is_not(None),
    ]
    if market is not None:
        conditions.append(MarketScanResult.market == market)
    if exclude_ticker is not None:
        conditions.append(MarketScanResult.ticker != exclude_ticker)
    rows = session.execute(select(column).where(*conditions)).scalars().all()
    return list(rows)


# --- Faz 12: Yaklaşan Bilanço Tarihleri (earnings_calendar) -----------------------------------------------------


def upsert_earnings_calendar(session: Session, records: Iterable[EarningsCalendarRecord]) -> int:
    """(ticker, year, period) benzersizligine gore kaydeder/gunceller --
    ayni donem icin daha once (orn. dusuk guvenli 'son_tarih') bir tahmin
    varsa, YENI (orn. KAP'in kendisinin acikladigi 'kesin') deger bunun
    UZERINE YAZILIR (bkz. src/fetchers/earnings_calendar.py -- caller
    ONCELIK sirasina gore [kesin > tahmini > son_tarih] SADECE bir tanesini
    gonderir, bu fonksiyon sirf var olan satiri gunceller).

    Donen deger: eklenen/guncellenen satir sayisi.
    """
    records = list(records)
    if not records:
        return 0

    existing_by_key: dict[tuple[str, int, int], EarningsCalendar] = {
        (row.ticker, row.year, row.period): row
        for row in session.execute(select(EarningsCalendar)).scalars().all()
    }

    count = 0
    for ticker, market, company_name, year, period, expected_date, confidence, source in records:
        key = (ticker, year, period)
        row = existing_by_key.get(key)
        if row is None:
            row = EarningsCalendar(ticker=ticker, year=year, period=period)
            session.add(row)
            existing_by_key[key] = row
        row.market = market
        row.company_name = company_name
        row.expected_date = expected_date
        row.confidence = confidence
        row.source = source
        row.updated_at = utcnow_naive()
        count += 1

    session.commit()
    return count


def get_upcoming_earnings(
    session: Session, market: str, days_ahead: int = 30, today: date | None = None
) -> list[EarningsCalendar]:
    """`today` (varsayilan: bugun) ile `today + days_ahead` arasindaki
    (dahil) tarihe sahip kayitlari, tarihe gore (en yakin once) doner.
    `today` parametresi TEST EDILEBILIRLIK icin acik birakildi (date.today()
    dogrudan cagrilmaz -- bkz. Faz 12 gorev talimati)."""
    reference_day = today if today is not None else date.today()
    end_day = reference_day + timedelta(days=days_ahead)
    rows = session.execute(
        select(EarningsCalendar)
        .where(
            EarningsCalendar.market == market,
            EarningsCalendar.expected_date >= reference_day,
            EarningsCalendar.expected_date <= end_day,
        )
        .order_by(EarningsCalendar.expected_date.asc())
    ).scalars().all()
    return list(rows)


def is_earnings_calendar_fresh(session: Session, market: str, max_age_hours: int = 24) -> bool:
    """O market icin herhangi bir kayit YOKSA VEYA en son guncellenen kayit
    `max_age_hours`'tan eskiyse False doner -- gunde 1 kez yenileme
    stratejisi icin (bkz. Faz 12 gorev talimati)."""
    latest_updated_at = session.execute(
        select(EarningsCalendar.updated_at).where(EarningsCalendar.market == market).order_by(EarningsCalendar.updated_at.desc()).limit(1)
    ).scalar_one_or_none()
    if latest_updated_at is None:
        return False
    return (utcnow_naive() - latest_updated_at) <= timedelta(hours=max_age_hours)


# --- Faz 5 (docs/spec/spec_dashboard.md): Piyasa Dashboard'u -- toplu tarama sonuç önbelleği (market_scan_result) -----------------------------------------------------

SCAN_STALE_AFTER_DAYS_UNSUPPORTED = 90
# spec "Eşikler ve ağırlıklar" tablosu: `scan_status in ("desteklenmiyor",
# "veri_yok")` satırlar için SABİT bir taban -- bir şirketin financial_group'u/
# veri kaynağı HAFTADA BİR yeniden denense bile SONUÇ DEĞİŞMEZ (kod desteği
# eklenmeden), bu yüzden `get_scan_queue()` bu iki durumda çağıranın verdiği
# `stale_after_days` (haftalık kadans) PARAMETRESİNİ DEĞİL, bu SABİTİ
# kullanır -- kuyruk gereksiz yere ISRARLA aynı başarısız ticker'ları
# DENEMEZ (refresh_universe.py'nin 404 kalıcı-işaretleme ilkesiyle AYNI).
_SCAN_UNSUPPORTED_STATUSES = ("desteklenmiyor", "veri_yok")


def upsert_market_scan_result(
    session: Session,
    ticker: str,
    market: str,
    scan_status: str,
    *,
    company_name: str | None = None,
    ust_sektor: str | None = None,
    sirket_turu: str | None = None,
    template: str | None = None,
    year: int | None = None,
    period: int | None = None,
    error_detail: str | None = None,
    deger_score: Decimal | None = None,
    deger_badge: str | None = None,
    deger_coverage_pct: Decimal | None = None,
    kalite_score: Decimal | None = None,
    kalite_badge: str | None = None,
    kalite_coverage_pct: Decimal | None = None,
    buyume_score: Decimal | None = None,
    buyume_badge: str | None = None,
    buyume_coverage_pct: Decimal | None = None,
    guvenlik_score: Decimal | None = None,
    guvenlik_badge: str | None = None,
    guvenlik_coverage_pct: Decimal | None = None,
    bilesik_score: Decimal | None = None,
    bilesik_badge: str | None = None,
    bilesik_data_coverage_pct: Decimal | None = None,
    dahil_edilen_mercekler: list[str] | None = None,
    current_price: Decimal | None = None,
    market_cap: Decimal | None = None,
    pe_ratio: Decimal | None = None,
    pb_ratio: Decimal | None = None,
    ev_ebitda: Decimal | None = None,
    currency: str | None = None,
    mercekler_detay: dict | None = None,
    financial_data_as_of: datetime | None = None,
    computed_at: datetime | None = None,
) -> MarketScanResult:
    """docs/spec/spec_dashboard.md §Mimari karar 1 (adım 3e) + §Kenar
    durumlar: `ticker` başına TEK GÜNCEL satırı upsert eder -- `GeneratedCard`
    ile KASITLI OLARAK FARKLI erişim deseni (bkz. `MarketScanResult`
    docstring'i, models.py).

    `scan_status="hata"` (transient ağ hatası) İÇİN ÖZEL davranış (spec
    "Kenar durumlar"): satır ZATEN varsa (önceki BAŞARILI/başka bir tarama)
    SADECE `scan_status`/`error_detail` güncellenir -- `deger_score` vb.
    SKOR ALANLARI ve `computed_at` EZİLMEZ (dashboard "eski ama gerçek" bir
    skor göstermeye devam eder, sessizce boş satır GÖSTERMEZ, "henüz gerçek
    bir yeniden-hesaplama OLMADI"). Satır İLK KEZ oluşturuluyorsa (önceki
    başarılı kayıt YOK) tüm skor alanları doğal olarak NULL kalır (hiçbiri
    kwarg olarak verilmemiştir).

    Diğer TÜM durumlarda ("ok", "desteklenmiyor", "veri_yok") satır TAMAMEN
    üzerine yazılır (verilmeyen alanlar NULL'a döner) -- "desteklenmiyor"/
    "veri_yok" gibi DETERMİNİSTİK sonuçların ESKİ (artık geçersiz) bir
    başarılı skorun kalıntısını TAŞIMAMASI için KASITLIDIR (bkz. spec
    Dashboard JSON şeması: "hatalı/desteklenmeyen satır örneği",
    `mercekler: null` vb.).

    `session.commit()` BURADA YAPILMAZ -- `upsert_sector_taxonomy()` ile
    AYNI ilke: çağıran taraf (`scripts/tarama_toplu.py`) TEK bir partiyi
    (`--limit` kadar ticker) TEK commit ile bitirir (spec §Orkestrasyon
    adımları madde 4: "session.commit() HER PARTİ SONUNDA")."""
    row = session.get(MarketScanResult, ticker)
    is_new = row is None
    if row is None:
        _get_or_create_company(session, ticker, market=market)
        row = MarketScanResult(ticker=ticker, market=market, scan_status=scan_status)
        session.add(row)

    if scan_status == "hata" and not is_new:
        row.scan_status = scan_status
        row.error_detail = error_detail
        return row

    row.market = market
    row.scan_status = scan_status
    row.error_detail = error_detail
    row.company_name = company_name
    row.ust_sektor = ust_sektor
    row.sirket_turu = sirket_turu
    row.template = template
    row.year = year
    row.period = period
    row.deger_score = deger_score
    row.deger_badge = deger_badge
    row.deger_coverage_pct = deger_coverage_pct
    row.kalite_score = kalite_score
    row.kalite_badge = kalite_badge
    row.kalite_coverage_pct = kalite_coverage_pct
    row.buyume_score = buyume_score
    row.buyume_badge = buyume_badge
    row.buyume_coverage_pct = buyume_coverage_pct
    row.guvenlik_score = guvenlik_score
    row.guvenlik_badge = guvenlik_badge
    row.guvenlik_coverage_pct = guvenlik_coverage_pct
    row.bilesik_score = bilesik_score
    row.bilesik_badge = bilesik_badge
    row.bilesik_data_coverage_pct = bilesik_data_coverage_pct
    row.dahil_edilen_mercekler = dahil_edilen_mercekler
    row.current_price = current_price
    row.market_cap = market_cap
    row.pe_ratio = pe_ratio
    row.pb_ratio = pb_ratio
    row.ev_ebitda = ev_ebitda
    row.currency = currency
    row.mercekler_detay = mercekler_detay
    row.financial_data_as_of = financial_data_as_of
    row.computed_at = computed_at if computed_at is not None else utcnow_naive()
    return row


def update_faaliyet_raporu_bulgulari(
    session: Session, ticker: str, market: str, bulgular: dict | None
) -> MarketScanResult | None:
    """docs/spec/spec_veri_tamlik_yol_haritasi.md §Faaliyet Raporu -- SADECE
    `faaliyet_raporu_bulgulari` sütununu günceller, `upsert_market_scan_result()`
    ile KASITLI OLARAK FARKLI davranır: o fonksiyon verilMEYEN alanları NULL'a
    döndürür (bkz. kendi docstring'i) -- bu, `scripts/kar_kaynagi_toplu.py`
    (sıcak/ağır, AYRI bir pilot script) çalıştığında ana v2 skor/mercek
    verisini SİLMEMESİ için özellikle GEREKLİDİR.

    Satır (ticker+market) DB'de YOKSA (henüz `tarama_toplu.py` ile taranmamış
    bir şirket) `None` döner -- bu script YENİ bir `MarketScanResult` satırı
    OLUŞTURMAZ (Kural 3: faaliyet raporu bulgusu, o şirketin ZATEN var olan
    bir tarama sonucunu ZENGİNLEŞTİRİR, kendi başına bir satır kaynağı DEĞİLDİR).

    `session.commit()` BURADA YAPILMAZ (diğer upsert/güncelleme fonksiyonlarıyla
    AYNI ilke -- çağıran taraf commit eder)."""
    row = session.get(MarketScanResult, ticker)
    if row is None or row.market != market:
        return None
    row.faaliyet_raporu_bulgulari = bulgular
    return row


def get_ok_scanned_tickers(session: Session, market: str) -> list[str]:
    """`scripts/kar_kaynagi_toplu.py`'nin `--universe full` (tüm evren)
    modu için TAM evren tanımı -- kullanıcının 2026-08-12'de onayladığı
    "önce `tarama_toplu.py` ile TARANMIŞ (`scan_status='ok'`) HER BİST
    şirketini işle" kuralı BİREBİR.

    `get_scan_queue()`'dan (Company tablosunu -- HENÜZ taranmamışlar dahil
    -- kaynak alır, `pipeline`'ın v2 skorlama motorunu tetikleyecek bir
    "taranacaklar" kuyruğu üretir) KASITLI OLARAK FARKLI: bu fonksiyon
    `MarketScanResult`'IN KENDİSİNİ kaynak alır, SADECE `scan_status='ok'`
    (yani zaten başarıyla taranmış, `mercekler_detay` dolu) satırların
    ticker'larını döner -- `update_faaliyet_raporu_bulgulari()`'nin
    docstring'inde belirtilen ilkeyle AYNI: faaliyet raporu bulgusu ZATEN
    var olan bir tarama sonucunu ZENGİNLEŞTİRİR, kendi başına bir satır
    kaynağı DEĞİLDİR -- bu yüzden burada `Company`'ye değil `MarketScanResult`'a
    bakılır (henüz hiç taranmamış bir ticker `update_faaliyet_raporu_
    bulgulari()`'de zaten `None` ile atlanır, bu fonksiyon o boşa gidecek
    çağrıyı EN BAŞTAN elemiş olur).

    Deterministik sıralama (ticker alfabetik) -- `--limit` ile kademeli
    çalıştırmanın (kod-geliştirici turdan tura) AYNI alt-kümeyi vermesi
    için (get_scan_queue'nun computed_at sıralamasının AKSİNE, bu kuyrukta
    "en eski/en yeni" önceliği YOK -- hepsi zaten "ok")."""
    rows = session.execute(
        select(MarketScanResult.ticker)
        .where(MarketScanResult.market == market, MarketScanResult.scan_status == "ok")
        .order_by(MarketScanResult.ticker.asc())
    ).scalars().all()
    return list(rows)


def get_market_scan_results(session: Session, market: str | None = None) -> list[MarketScanResult]:
    """docs/spec/spec_dashboard.md §Dashboard'a gömülecek JSON şeması:
    `src/render/dashboard.py::build_dashboard_data()` (Faz 5 adım 3) için
    TOPLU okuma kaynağı -- HESAPLAMA yapmaz, saf CRUD/okuma (quaxis-mimari
    anayasa)."""
    query = select(MarketScanResult)
    if market is not None:
        query = query.where(MarketScanResult.market == market)
    rows = session.execute(query).scalars().all()
    return list(rows)


def is_scan_fresh(session: Session, ticker: str, max_age_days: int = 7) -> bool:
    """docs/spec/spec_dashboard.md §Tazelik ve freshness politikası "Katman 3":
    `is_data_fresh()`/`is_earnings_calendar_fresh()` ile AYNI ilke -- SADECE
    `scan_status="ok"` bir satır varsa VE `computed_at` `max_age_days`
    içindeyse True döner. Hiç taranmamış VEYA son deneme başarısız
    ("hata"/"desteklenmiyor"/"veri_yok") ise False döner -- bir önceki
    BAŞARISIZ deneme "taze" sayılamaz, sadece gerçek bir başarılı tarama
    tazelik sağlar."""
    row = session.get(MarketScanResult, ticker)
    if row is None or row.scan_status != "ok":
        return False
    return (utcnow_naive() - row.computed_at) <= timedelta(days=max_age_days)


def get_scan_queue(
    session: Session,
    market: str,
    stale_after_days: int,
    limit: int,
    priority_tickers: set[str] | None = None,
) -> list[Company]:
    """docs/spec/spec_dashboard.md §Formüller-1: `scripts/tarama_toplu.py`'nin
    `--universe tam` kuyruk sorgusu -- `MarketScanResult`'ı `Company`'ye
    LEFT JOIN eder, aday satırlar:
      (a) `MarketScanResult` HİÇ YOK (hiç taranmamış) VEYA
      (b) `MarketScanResult.computed_at` şimdiden `stale_after_days` günden
          eski (scan_status "desteklenmiyor"/"veri_yok" İSE bu genel
          parametre YERİNE SABİT `SCAN_STALE_AFTER_DAYS_UNSUPPORTED` (90
          gün) kullanılır -- bkz. spec "Eşikler ve ağırlıklar" tablosu,
          "kuyruk gereksiz yere ISRARLA aynı başarısız ticker'ları
          DENEMEZ") VEYA
      (c) ticker `priority_tickers` içinde (bilanço-tarihi yaklaşan/geçmiş
          şirketler için FORCE-check, bkz. spec §Formüller-2)

    ÖNKOŞUL: `Company.market == market AND Company.ust_sektor IS NOT NULL`
    (Faz 2 tamamlanmamış satırlar ATLANIR, bkz. spec "Kenar durumlar").
    `market="NASDAQ"` ise EK ÖNKOŞUL: §NASDAQ kalite filtresi (`filer_category`
    tabanlı, bkz. spec "NASDAQ 'tam evren' kapsamı" bölümü) -- alt-dizgi
    tuzağı ("non-accelerated filer" de "accelerated filer" İÇERİR) `not_like`
    ile ÖNCE elenir. `--universe bist30/nasdaq30` (statik pilot liste) bu
    fonksiyonu HİÇ ÇAĞIRMAZ (spec "Orkestrasyon adımları" madde 2a).

    Sıralama: hiç taranmamış (`computed_at IS NULL`) ÖNCE, sonra en eski
    `computed_at` -- `_next_batch` (refresh_universe.py) ile AYNI ilke.
    `limit` uygulanır."""
    priority_tickers = priority_tickers or set()
    cutoff_standard = utcnow_naive() - timedelta(days=stale_after_days)
    cutoff_unsupported = utcnow_naive() - timedelta(days=SCAN_STALE_AFTER_DAYS_UNSUPPORTED)

    conditions = [Company.market == market, Company.ust_sektor.is_not(None)]
    if market == "NASDAQ":
        kategori = func.lower(Company.filer_category)
        conditions.append(
            and_(
                Company.filer_category.is_not(None),
                kategori.like("%accelerated filer%"),
                kategori.not_like("%non-accelerated%"),  # alt-dizgi tuzagi (bkz. spec NASDAQ kalite filtresi)
            )
        )

    standard_stale = and_(
        or_(MarketScanResult.scan_status.is_(None), MarketScanResult.scan_status.not_in(_SCAN_UNSUPPORTED_STATUSES)),
        or_(MarketScanResult.computed_at.is_(None), MarketScanResult.computed_at < cutoff_standard),
    )
    unsupported_stale = and_(
        MarketScanResult.scan_status.in_(_SCAN_UNSUPPORTED_STATUSES),
        MarketScanResult.computed_at < cutoff_unsupported,
    )
    eligibility = or_(standard_stale, unsupported_stale)
    if priority_tickers:
        eligibility = or_(eligibility, Company.ticker.in_(priority_tickers))

    rows = (
        session.execute(
            select(Company)
            .outerjoin(MarketScanResult, MarketScanResult.ticker == Company.ticker)
            .where(*conditions, eligibility)
            .order_by(MarketScanResult.computed_at.asc().nullsfirst())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return list(rows)
