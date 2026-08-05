"""Fon günlük getiri TAHMİNİ kartı için orkestrasyon katmanı (Faz 19).

`src.bot.pipeline` (şirket bilanço analizi) ile AYNI ilke: bu modül SADECE
fetcher'ları (`tefas`/`kap_fund_portfolio`/`isyatirim`) ve saf hesaplayıcıyı
(`src.analysis.fund_estimator`) birbirine bağlar -- kendi başına HİÇBİR
sayı hesaplamaz.

🚨 GERÇEK ZAMANLI/CANLI FİYAT KAYNAĞI YOK (Kural 8 -- açıkça belgelenir,
gizlenmez): `isyatirim.fetch_price_history()` SADECE günlük (EOD) kapanış
serisi döner, 'açılış'/anlık fiyat alanı hiçbir zaman yok (bkz. o modülün
docstring'i). Bu yüzden BİST hisseleri için "günlük getiri", GÜN İÇİNDE
"bugünün açılışına göre şu ana kadarki getiri" DEĞİL, EN SON İKİ KAPANMIŞ
işlem gününün kapanış-kapanışa getirisidir -- piyasa açıkken bu pratikte
DÜNKÜ getiridir (bugünün kapanışı henüz oluşmadığı için), kapanıştan sonra
BUGÜNKÜ getiridir. Kart bu farkı SESSİZCE gizlemez, "en son kapanışa göre"
ifadesiyle açıkça belirtir (bkz. `src.render.fund_card`).

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
import time
from dataclasses import dataclass
from decimal import Decimal

from src.analysis import fund_estimator
from src.fetchers import isyatirim, kap_fund_portfolio as kfp, tefas

logger = logging.getLogger(__name__)

_COURTESY_DELAY_SECONDS = 0.3

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
    rows = isyatirim.fetch_price_history(ticker, days=10)
    closes = sorted(((r["date"], r["close"]) for r in rows if r.get("close")), key=lambda t: t[0])
    if len(closes) < 2:
        return None
    prev_price = closes[-2][1]
    last_price = closes[-1][1]
    if not prev_price:
        return None
    return (last_price / prev_price - 1) * Decimal(100)


def _fon_daily_return(ticker: str) -> Decimal | None:
    try:
        returns = tefas.fetch_fund_returns(ticker)
    except tefas.TefasError as exc:
        logger.info("Alt fon %s için TEFAS getirisi çekilemedi: %s", ticker, exc)
        return None
    return returns.d1


def _price_changes_for_portfolio(portfolio: "kfp.FundPortfolio") -> dict[str, Decimal]:
    """Portföydeki HER BENZERSİZ (tür, ticker) için günlük getiriyi çeker
    -- aynı ticker birden fazla kalemde tekrarlanıyorsa (nadiren olur) TEK
    seferde çekilir. Bir ticker'ın getirisi çekilemezse (Kural 9) o kalem
    `fund_estimator`'da otomatik "fiyatlandırılamadı" sayılır -- burada
    hata FIRLATILMAZ, sadece o anahtar sözlükte YOK olur."""
    price_changes: dict[str, Decimal] = {}
    seen: set[tuple[str, str]] = set()
    for holding in portfolio.holdings:
        if not holding.ticker or holding.instrument_type not in ("hisse", "fon"):
            continue
        key = (holding.instrument_type, holding.ticker)
        if key in seen:
            continue
        seen.add(key)

        try:
            if holding.instrument_type == "hisse":
                ret = _hisse_daily_return(holding.ticker)
            else:
                ret = _fon_daily_return(holding.ticker)
        except Exception:  # noqa: BLE001 -- ikincil veri, TEK bir kalemdeki hata TÜM tahmini ÇÖKERTMEMELİ
            logger.warning("%s (%s) için günlük getiri çekilemedi", holding.ticker, holding.instrument_type, exc_info=True)
            ret = None

        time.sleep(_COURTESY_DELAY_SECONDS)
        if ret is not None:
            price_changes[holding.ticker] = ret

    return price_changes


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

    portfolio = kfp.fetch_latest_portfolio(fund_code)
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


def compute_fund_estimates(fund_codes: list[str]) -> list[FundEstimateResult]:
    """Birden fazla fon için `compute_fund_estimate()`'i sırayla çağırır
    (grup kartları -- 'öne çıkan fonlar'/'tüm liste' -- için). Fonlar
    ARASINDA da nezaket gecikmesi uygulanır; TEK bir fondaki hata
    (Kural 9) diğerlerini ETKİLEMEZ."""
    results: list[FundEstimateResult] = []
    for code in fund_codes:
        try:
            results.append(compute_fund_estimate(code))
        except Exception:  # noqa: BLE001 -- bir fondaki beklenmeyen hata TUM grubu COKERTMEMELI
            logger.warning("%s için tahmin hesaplanamadı (beklenmeyen hata)", code, exc_info=True)
            results.append(FundEstimateResult(code, None, None, "Beklenmeyen bir hata oluştu.", None))
        time.sleep(_COURTESY_DELAY_SECONDS)
    return results
