"""Fon günlük getiri TAHMİNİ kartı için orkestrasyon katmanı (Faz 19).

`src.bot.pipeline` (şirket bilanço analizi) ile AYNI ilke: bu modül SADECE
fetcher'ları (`tefas`/`kap_fund_portfolio`/`yahoo_quote`) ve saf
hesaplayıcıyı (`src.analysis.fund_estimator`) birbirine bağlar -- kendi
başına HİÇBİR sayı hesaplamaz.

🚨 KULLANICI KARARI #7 (2026-08-05, CANLI hata + düzeltme): BİST hisse
günlük getirisi ESKİDEN `isyatirim.fetch_price_history()` ile
çekiliyordu -- CANLI kullanıcı raporuyla YAKALANDI: bu uç nokta BUGÜNÜN
kapanışını YAYINLAMIYOR, en güncel satırı HER ZAMAN bir tam gün gecikmeli
(OZATD örneği: kart %2,55 [aslında dünkü getiri] gösterirken gerçek
bugünkü kapanış %8,41 idi). `src.fetchers.yahoo_quote` (Yahoo'nun public
chart uç noktası, NASDAQ için `sec_edgar.py`'nin de kullandığı AYNI API,
".IS" uzantılı BİST sembolleriyle) CANLI test edildi ve kullanıcının
bildirdiği rakamla BİREBİR eşleşti -- artık BİST günlük getirisi BURADAN
alınır (bkz. `_hisse_daily_return`). `isyatirim.py` projenin DİĞER
akışlarında (teknik analiz, 400 günlük seri) DEĞİŞTİRİLMEDİ.

Fon-içinde-fon (`instrument_type="fon"`) alt fonlarının getirisi
`tefas.fetch_fund_returns(alt_kod).d1` ile -- yani TEFAS'ın kendi
yayınladığı EN SON günlük getiri -- alınır (kullanıcı isteği: alt fonun
NAV'ı zaten günde bir kez yayınlanır, "önceki güne göre" mantığı buraya
zaten UYGUNDUR, hisse gibi bir "gün içi" beklentisi YOKTUR).

Yönetim ücreti (`fund_expense_ratio_annual_pct`) bu fazda HİÇBİR kaynaktan
ÇEKİLMİYOR -- `fund_estimator.estimate_daily_return()`'a `None` geçilir
(Decimal(0) varsayılır, sistematik iyimser bir sapma kaynağıdır, bkz. o
modülün docstring'i).
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from src.analysis import fund_estimator
from src.db import repository
from src.fetchers import kap_fund_portfolio as kfp, tefas, yahoo_quote

logger = logging.getLogger(__name__)

_PRICE_FETCH_MAX_WORKERS = 6  # CANLI hata (kullanici raporu): 24 kalemli TLY tek tek/gecikmeli cekilince 4 DAKIKA suruyordu
_PORTFOLIO_CACHE_TTL_DAYS = 3  # KAP raporu ayda bir yayinlanir -- bu TTL "yeni rapor kacirma" riskini pratikte SIFIRLAR

# Kullanıcının Telegram "Fon Analiz" özelliği için verdiği hedef fon
# listesi (2026-08-05) -- bkz. PROJE_HAFIZASI/08_DEGISIKLIK_GUNLUGU.md.
# TÜMÜ KAP'ta ayrıştırılabilir/uygulanabilir OLMAYABİLİR (bkz.
# `compute_fund_estimate()`'in `reason` alanı) -- liste OLDUĞU GİBİ
# tutulur, ayrıştırılamayan fonlar grup kartlarında "tahmin üretilemeyen
# fonlar" bölümünde AÇIKÇA gösterilir (Kural 3), listeden SESSİZCE
# ÇIKARILMAZ.
TARGET_FUND_CODES: list[str] = [
    "TLY", "TMV", "PHE", "PBR", "DFI", "DKR", "LTL", "RIH", "PUK", "SNY", "BMU", "RSK", "KHA", "YIT", "IJC",
]
# Kullanıcının "ön planda olan fonlar" dediği alt küme.
FEATURED_FUND_CODES: list[str] = ["TLY", "TMV", "PHE", "PBR", "PUK", "DFI"]


@dataclass(frozen=True)
class FundEstimateResult:
    """`compute_fund_estimate()`'in döndüğü, kart katmanının ihtiyaç
    duyduğu her şeyi taşıyan tek paket. `estimate` None ise `reason`
    KULLANICIYA gösterilecek Türkçe bir açıklama içerir (Kural 3/9: hata
    fırlatılmaz, sebep her zaman anlaşılır bir metindir)."""

    fund_code: str
    fund_name: str | None
    estimate: fund_estimator.FundEstimate | None
    reason: str | None
    portfolio: "kfp.FundPortfolio | None"


def _hisse_daily_return(ticker: str) -> Decimal | None:
    """🚨 KULLANICI KARARI #7 (2026-08-05, CANLI hata): eskiden
    `isyatirim.fetch_price_history()` kullanılıyordu -- bu uç nokta
    BUGÜNÜN kapanışını YAYINLAMIYOR (bir tam gün gecikmeli, CANLI
    doğrulandı: OZATD örneğinde kart %2,55 [dünkü getiri] gösterirken
    gerçek bugünkü kapanış %8,41 idi). `yahoo_quote.fetch_daily_return()`
    (Yahoo'nun ".IS" uzantılı BİST sembolleri) CANLI test edildi ve
    kullanıcının bildirdiği rakamla BİREBİR eşleşti -- bkz. o modülün
    üst notu. `isyatirim.py` diğer akışlarda (teknik analiz vb.)
    DEĞİŞTİRİLMEDİ, sadece BURADA (bugünün getirisi kritik) değişti."""
    return yahoo_quote.fetch_daily_return(ticker, suffix=".IS")


def _fon_daily_return(ticker: str) -> Decimal | None:
    try:
        returns = tefas.fetch_fund_returns(ticker)
    except tefas.TefasError as exc:
        logger.info("Alt fon %s için TEFAS getirisi çekilemedi: %s", ticker, exc)
        return None
    return returns.d1


def _fetch_one_return(instrument_type: str, ticker: str) -> Decimal | None:
    try:
        return _hisse_daily_return(ticker) if instrument_type == "hisse" else _fon_daily_return(ticker)
    except Exception:  # noqa: BLE001 -- ikincil veri, TEK bir kalemdeki hata TÜM tahmini ÇÖKERTMEMELİ
        logger.warning("%s (%s) için günlük getiri çekilemedi", ticker, instrument_type, exc_info=True)
        return None


def _price_changes_for_portfolio(portfolio: "kfp.FundPortfolio") -> dict[str, Decimal]:
    """Portföydeki HER BENZERSİZ (tür, ticker) için günlük getiriyi çeker
    -- aynı ticker birden fazla kalemde tekrarlanıyorsa (nadiren olur) TEK
    seferde çekilir. Bir ticker'ın getirisi çekilemezse (Kural 9) o kalem
    `fund_estimator`'da otomatik "fiyatlandırılamadı" sayılır -- burada
    hata FIRLATILMAZ, sadece o anahtar sözlükte YOK olur.

    CANLI KULLANICI RAPORU (2026-08-05): 24 kalemli TLY için bu adım
    (TEK TEK, aralarında nezaket gecikmesiyle) ~4 DAKİKA sürüyordu --
    Telegram'da "hiç sonuç gelmiyor" izlenimi veriyordu. Artık
    `_PRICE_FETCH_MAX_WORKERS` kadar İSTEK PARALEL atılıyor (ağ G/Ç
    ağırlıklı iş, `isyatirim`/`tefas` kendi timeout/retry mantığını
    KORUYOR, sadece ARALARINDAKİ sıralı bekleme kaldırıldı)."""
    unique_items = list({(h.instrument_type, h.ticker) for h in portfolio.holdings if h.ticker and h.instrument_type in ("hisse", "fon")})
    if not unique_items:
        return {}

    price_changes: dict[str, Decimal] = {}
    with ThreadPoolExecutor(max_workers=_PRICE_FETCH_MAX_WORKERS) as executor:
        futures = {executor.submit(_fetch_one_return, itype, ticker): ticker for itype, ticker in unique_items}
        for future in as_completed(futures):
            ticker = futures[future]
            ret = future.result()
            if ret is not None:
                price_changes[ticker] = ret

    return price_changes


def _portfolio_from_cached_holdings(fund_code: str, rows: list) -> "kfp.FundPortfolio":
    holdings = [
        kfp.Holding(instrument_type=r.instrument_type, ticker=r.ticker, name=r.name, weight_pct=r.weight_pct) for r in rows
    ]
    report_date = rows[0].report_date
    return kfp.FundPortfolio(
        fund_code=fund_code,
        report_date=report_date,
        publish_date=report_date,
        holdings=holdings,
        staleness_days=(date.today() - report_date).days,
    )


def _cached_or_fresh_portfolio(fund_code: str) -> "kfp.FundPortfolio | None":
    """KAP portföyünü ÖNCE veritabanı önbelleğinden okumayı dener --
    `Fund.last_updated` `_PORTFOLIO_CACHE_TTL_DAYS` içindeyse KAP'a HİÇ
    gidilmez (CANLI kullanıcı raporu: KAP PDF indirme+ayrıştırma tek
    başına onlarca saniye sürebiliyordu, HER sorguda tekrarlanması
    gereksizdi -- portföy zaten ayda bir güncelleniyor). Önbellek
    YOKSA/BAYATSA KAP'tan taze çekilir VE sonraki sorgular için
    kaydedilir."""
    with repository.get_session() as session:
        fund = repository.get_fund(session, fund_code)
        if fund is not None and fund.last_updated is not None:
            if datetime.utcnow() - fund.last_updated < timedelta(days=_PORTFOLIO_CACHE_TTL_DAYS):
                rows = repository.get_latest_fund_holdings(session, fund_code)
                if rows:
                    return _portfolio_from_cached_holdings(fund_code, rows)

    portfolio = kfp.fetch_latest_portfolio(fund_code)
    if portfolio is not None and portfolio.holdings:
        with repository.get_session() as session:
            repository.save_fund_info(session, fund_code, None, None, None, None, None)
            repository.save_fund_holdings(
                session,
                fund_code,
                portfolio.report_date,
                [(h.instrument_type, h.ticker, h.name, h.weight_pct) for h in portfolio.holdings],
            )
    return portfolio


def compute_fund_estimate(fund_code: str) -> FundEstimateResult:
    """Bir fon kodu için uçtan uca tahmin üretir: TEFAS kategori/isim →
    KAP güncel portföy → portföydeki her kalem için güncel fiyat değişimi
    → `fund_estimator.estimate_daily_return()`.

    Her adımda başarısızlık `reason` ile AÇIKÇA raporlanır (Kural 3/9) --
    hiçbir zaman istisna fırlatmaz, çağıran taraf (bot) SADECE
    `result.estimate is None` kontrolü yapıp `result.reason`'ı
    gösterebilir."""
    fund_code = fund_code.strip().upper()

    try:
        info = tefas.fetch_fund_info(fund_code)
    except tefas.TefasFundNotFoundError:
        return FundEstimateResult(fund_code, None, None, f"'{fund_code}' TEFAS'ta bulunamadı.", None)
    except tefas.TefasError as exc:
        logger.warning("%s için TEFAS bilgisi çekilemedi: %s", fund_code, exc)
        return FundEstimateResult(fund_code, None, None, "TEFAS'a şu an ulaşılamıyor, birkaç dakika sonra tekrar dene.", None)

    applicable, reason = fund_estimator.is_estimable_fund_type(info.type)
    if not applicable:
        return FundEstimateResult(fund_code, info.name, None, reason, None)

    portfolio = _cached_or_fresh_portfolio(fund_code)
    if portfolio is None or not portfolio.holdings:
        return FundEstimateResult(
            fund_code,
            info.name,
            None,
            "KAP'ta bu fon için güncel bir 'Portföy Dağılım Raporu' bulunamadı ya da güvenilir "
            "şekilde ayrıştırılamadı -- bu fon için şu an tahmin üretilemiyor.",
            None,
        )

    price_changes = _price_changes_for_portfolio(portfolio)

    estimate = fund_estimator.estimate_daily_return(
        portfolio,
        price_changes,
        fund_expense_ratio_annual_pct=None,
        fund_category=info.type,
    )
    if estimate is None:
        return FundEstimateResult(fund_code, info.name, None, "Tahmin üretilemedi.", portfolio)

    return FundEstimateResult(fund_code, info.name, estimate, None, portfolio)


_FUND_GROUP_MAX_WORKERS = 4  # her fon kendi icinde de PRICE_FETCH_MAX_WORKERS kadar is parcacigi acabildigi icin dusuk tutulur


def compute_fund_estimates(fund_codes: list[str]) -> list[FundEstimateResult]:
    """Birden fazla fon için `compute_fund_estimate()`'i PARALEL çağırır
    (grup kartları -- 'öne çıkan fonlar'/'tüm liste' -- için, CANLI
    kullanıcı raporu: sıralı+nezaket-gecikmeli akış 15 fon için dakikalar
    sürüyordu). Sonuç sırası `fund_codes` ile AYNI kalır (paralel
    tamamlanma sırası KARIŞSA bile) -- grup kartındaki sıralama tutarlı
    olsun diye. TEK bir fondaki hata (Kural 9) diğerlerini ETKİLEMEZ."""
    results: dict[str, FundEstimateResult] = {}
    with ThreadPoolExecutor(max_workers=_FUND_GROUP_MAX_WORKERS) as executor:
        futures = {executor.submit(compute_fund_estimate, code): code for code in fund_codes}
        for future in as_completed(futures):
            code = futures[future]
            try:
                results[code] = future.result()
            except Exception:  # noqa: BLE001 -- bir fondaki beklenmeyen hata TUM grubu COKERTMEMELI
                logger.warning("%s için tahmin hesaplanamadı (beklenmeyen hata)", code, exc_info=True)
                results[code] = FundEstimateResult(code, None, None, "Beklenmeyen bir hata oluştu.", None)
    return [results[code] for code in fund_codes]
