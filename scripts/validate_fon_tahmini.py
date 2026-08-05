"""Faz 18 ZORUNLU geriye dönük doğrulama: `src/analysis/fund_estimator.py`
GERÇEK verilerle ne kadar isabetli?

⚠️ BU RAPOR OKUNMADAN tahmin motoru hiçbir yere (bot, kart) BAĞLANMAMALIDIR.
Görev tanımı: "Bu fazın EN ÖNEMLİ çıktısı tahmin değil, TAHMİNİN HATA
PAYIDIR." Bu script MAE > 0,5 puan gibi kabul edilemez bir sonuç
bulursa açıkça YAYINLAMAMAYI önerir (bkz. rapor sonu).

── METODOLOJİ (look-ahead bias'tan KAÇINMA) ──
Her test günü `d` için tahmin, SADECE `d`'den ÖNCE yayınlanmış bir KAP
"Portföy Dağılım Raporu"nu kullanır -- `kap_fund_portfolio.
find_portfolio_disclosures()` bir fonun TÜM geçmiş rapor bildirimlerini
döner, bu script her test günü için "o gün itibarıyla EN GÜNCEL olan"
raporu seçer (`publish_date < d`). Bu, gerçek bir kullanıcının o gün
elinde OLABİLECEK bilgiyle sınırlıdır -- gelecekteki bir raporu
"kullanmak" (geriye dönük testte sık yapılan bir hata) KESİNLİKLE
YAPILMAZ.

"Gerçekleşen getiri" `tefas.fetch_price_history()`'nin döndürdüğü GERÇEK
günlük fon fiyatından hesaplanır (tahmin motorunun KULLANDIĞI hisse/fon
fiyatlarından TAMAMEN BAĞIMSIZ bir kaynak -- ground truth).

── KAPSAM ──
`FUND_CANDIDATES` listesi CANLI olarak taranıp (bkz. bu dosyanın git
geçmişindeki tarama scripti) hem TEFAS kategorisi ("Hisse Senedi Fonu"/
"Endeks Fonu") hem KAP'ta GERÇEKTEN ayrıştırılabilir bir portföy raporu
olan fonlarla sınırlandı -- bkz. `fund_estimator.is_estimable_fund_type()`.

Kullanım:
    python scripts/validate_fon_tahmini.py
"""

from __future__ import annotations

import statistics
import sys
import time
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402
from src.analysis import fund_estimator  # noqa: E402
from src.fetchers import isyatirim, kap_fund_portfolio as kfp, tefas  # noqa: E402

# CANLI tarandı (2026-08-05): TEFAS fonKategori="Hisse Senedi Fonu"/
# "Endeks Fonu" OLAN VE KAP'ta gerçekten ayrıştırılabilir (öz-doğrulaması
# geçen) bir "Portföy Dağılım Raporu"na sahip fonlar. Bkz. rapor çıktısı
# için hangi adayların ELENDİĞİ (kategori uygun değil VEYA KAP parser'ı
# güvenilir sonuç veremedi) ayrı ayrı loglanır.
FUND_CANDIDATES: list[str] = []  # main() basinda doldurulur (bkz. _DISCOVERED_FUNDS)

TEST_WINDOW_DAYS = 35  # ~30 islem gunu hedeflenir, hafta sonlari icin pay birakildi
COURTESY_DELAY_SECONDS = 0.5


@dataclass(frozen=True)
class _PortfolioSnapshot:
    """`fund_estimator.PortfolioLike` protokolüne uyan, GERİYE DÖNÜK bir
    tarihe göre `staleness_days`'i YENİDEN hesaplanmış hafif bir taşıyıcı
    (kap_fund_portfolio.FundPortfolio ile AYNI alanlar)."""

    fund_code: str
    report_date: date
    staleness_days: int
    holdings: list = field(default_factory=list)


@dataclass
class _TestResult:
    fund_code: str
    test_date: date
    estimated_return_pct: Decimal
    realized_return_pct: Decimal
    error: Decimal
    confidence: str
    covered_weight_pct: Decimal
    staleness_days: int


def _daily_returns_from_price_series(prices: list[tuple[date, Decimal]]) -> dict[date, Decimal]:
    """(tarih, fiyat) listesinden {tarih: gunluk_yuzde_getiri} sozlugu
    uretir (bir onceki GERCEK islem gunune gore, takvim gunune GORE
    DEGIL)."""
    prices = sorted(prices, key=lambda t: t[0])
    returns: dict[date, Decimal] = {}
    for i in range(1, len(prices)):
        prev_date, prev_price = prices[i - 1]
        cur_date, cur_price = prices[i]
        if prev_price and prev_price != 0:
            returns[cur_date] = (cur_price / prev_price - 1) * 100
    return returns


def _select_disclosure_as_of(disclosures: list[dict], as_of: date) -> dict | None:
    """`as_of` tarihinden ÖNCE yayınlanmış (look-ahead bias YOK) en
    GÜNCEL bildirimi döner -- yoksa None (o gün için henüz hiçbir KAP
    raporu yayınlanmamıştı, test dışı bırakılır)."""
    eligible = [d for d in disclosures if d["publish_date"] < as_of]
    if not eligible:
        return None
    return max(eligible, key=lambda d: d["publish_date"])


def _validate_fund(fund_code: str, fund_category: str | None) -> list[_TestResult]:
    print(f"\n=== {fund_code} ===")
    oid = kfp.resolve_fund_oid(fund_code)
    if oid is None:
        print("  KAP oid çözülemedi, atlanıyor.")
        return []
    time.sleep(COURTESY_DELAY_SECONDS)

    disclosures = kfp.find_portfolio_disclosures(oid)
    if not disclosures:
        print("  Hiç 'Portföy Dağılım Raporu' bulunamadı, atlanıyor.")
        return []
    print(f"  {len(disclosures)} portföy raporu bulundu: {[d['publish_date'].isoformat() for d in disclosures]}")

    # Her bildirimi BİR KEZ indirip ayrıştır (disclosure_index -> holdings).
    holdings_by_disclosure: dict[int, list] = {}
    for disc in disclosures:
        portfolio = kfp.fetch_portfolio_by_disclosure(fund_code, disc, as_of=disc["publish_date"])
        time.sleep(COURTESY_DELAY_SECONDS)
        if portfolio is None or not portfolio.holdings:
            continue
        holdings_by_disclosure[disc["disclosure_index"]] = portfolio.holdings
    if not holdings_by_disclosure:
        print("  Hiçbir rapor güvenilir şekilde ayrıştırılamadı, atlanıyor.")
        return []

    # Fonun KENDİ gerçekleşen günlük fiyat serisi -- ground truth.
    fund_prices = tefas.fetch_price_history(fund_code, months=2)
    fund_returns = _daily_returns_from_price_series(fund_prices)
    if not fund_returns:
        print("  TEFAS fiyat geçmişi alınamadı, atlanıyor.")
        return []

    cutoff = date.today() - timedelta(days=TEST_WINDOW_DAYS)
    test_dates = sorted(d for d in fund_returns if d >= cutoff)
    if not test_dates:
        print("  Test penceresinde işlem günü yok, atlanıyor.")
        return []

    # Portfoydeki TUM benzersiz (tur, ticker) ciftleri icin fiyat serisi
    # (TEK seferde cekilir, gun basina TEKRAR TEKRAR cekilmez).
    all_tickers: set[tuple[str, str]] = set()
    for holdings in holdings_by_disclosure.values():
        for h in holdings:
            if h.ticker and h.instrument_type in ("hisse", "fon"):
                all_tickers.add((h.instrument_type, h.ticker))

    ticker_returns: dict[str, dict[date, Decimal]] = {}
    for instrument_type, ticker in sorted(all_tickers):
        try:
            if instrument_type == "hisse":
                rows = isyatirim.fetch_price_history(ticker, days=TEST_WINDOW_DAYS + 45)
                series = [(r["date"], r["close"]) for r in rows if r.get("close")]
            else:  # "fon" -- alt fon kendi TEFAS kodudur
                series = tefas.fetch_price_history(ticker, months=3)
        except Exception as exc:  # noqa: BLE001 -- bu ikincil/yardimci bir veri, tum testi COKERTMEMELI
            print(f"    [{ticker}] fiyat geçmişi çekilemedi: {exc}")
            time.sleep(COURTESY_DELAY_SECONDS)
            continue
        ticker_returns[ticker] = _daily_returns_from_price_series(series)
        time.sleep(COURTESY_DELAY_SECONDS)

    results: list[_TestResult] = []
    for test_date in test_dates:
        disclosure = _select_disclosure_as_of(disclosures, test_date)
        if disclosure is None:
            continue
        holdings = holdings_by_disclosure.get(disclosure["disclosure_index"])
        if not holdings:
            continue

        report_date = kfp.report_period_end(disclosure["year"], disclosure["period"])
        staleness_days = (test_date - report_date).days
        snapshot = _PortfolioSnapshot(fund_code=fund_code, report_date=report_date, staleness_days=staleness_days, holdings=holdings)

        price_changes = {
            ticker: ticker_returns[ticker][test_date]
            for (_itype, ticker) in all_tickers
            if ticker in ticker_returns and test_date in ticker_returns[ticker]
        }

        estimate = fund_estimator.estimate_daily_return(
            snapshot, price_changes, fund_category=fund_category, estimate_date=test_date
        )
        if estimate is None:
            continue

        realized = fund_returns[test_date]
        error = abs(estimate.estimated_return_pct - realized)
        results.append(
            _TestResult(
                fund_code=fund_code,
                test_date=test_date,
                estimated_return_pct=estimate.estimated_return_pct,
                realized_return_pct=realized,
                error=error,
                confidence=estimate.confidence,
                covered_weight_pct=estimate.covered_weight_pct,
                staleness_days=staleness_days,
            )
        )

    print(f"  {len(results)} gün test edildi.")
    return results


def _print_report(results: list[_TestResult]) -> None:
    print("\n" + "=" * 70)
    print("GERİYE DÖNÜK DOĞRULAMA RAPORU")
    print("=" * 70)

    if not results:
        print("\n🚨 HİÇ TEST SONUCU ÜRETİLEMEDİ -- tahmin motoru bu veriyle "
              "DOĞRULANAMADI. YAYINLANMASI ÖNERİLMEZ.")
        return

    errors = [r.error for r in results]
    mae = sum(errors) / len(errors)
    median_error = Decimal(str(statistics.median([float(e) for e in errors])))

    print(f"\nToplam test noktası: {len(results)} ({len(set(r.fund_code for r in results))} fon)")
    print(f"Ortalama Mutlak Hata (MAE): {mae:.4f} puan")
    print(f"Medyan Hata: {median_error:.4f} puan")
    print(f"En kötü hata: {max(errors):.4f} puan")
    print(f"En iyi hata: {min(errors):.4f} puan")

    # Hata dagilimi (basit histogram)
    buckets = {"<0.15": 0, "0.15-0.30": 0, "0.30-0.50": 0, "0.50-1.00": 0, ">1.00": 0}
    for e in errors:
        if e < Decimal("0.15"):
            buckets["<0.15"] += 1
        elif e < Decimal("0.30"):
            buckets["0.15-0.30"] += 1
        elif e < Decimal("0.50"):
            buckets["0.30-0.50"] += 1
        elif e < Decimal("1.00"):
            buckets["0.50-1.00"] += 1
        else:
            buckets[">1.00"] += 1
    print("\nHata dağılımı:")
    for label, count in buckets.items():
        pct = count / len(errors) * 100
        print(f"  {label:12s}: {count:4d} ({pct:5.1f}%)")

    # Tazelikle iliski
    print("\nHata / portföy tazeliği ilişkisi:")
    staleness_buckets: dict[str, list[Decimal]] = {"0-7 gün": [], "8-15 gün": [], "16-30 gün": [], "30+ gün": []}
    for r in results:
        if r.staleness_days <= 7:
            staleness_buckets["0-7 gün"].append(r.error)
        elif r.staleness_days <= 15:
            staleness_buckets["8-15 gün"].append(r.error)
        elif r.staleness_days <= 30:
            staleness_buckets["16-30 gün"].append(r.error)
        else:
            staleness_buckets["30+ gün"].append(r.error)
    for label, errs in staleness_buckets.items():
        if errs:
            print(f"  {label:10s}: MAE={sum(errs)/len(errs):.4f} puan (n={len(errs)})")
        else:
            print(f"  {label:10s}: veri yok")

    # Guven seviyesine gore
    print("\nHata / bildirilen güven seviyesi ilişkisi (güven kalibrasyonu):")
    for level in ("yüksek", "orta", "düşük"):
        errs = [r.error for r in results if r.confidence == level]
        if errs:
            print(f"  {level:8s}: MAE={sum(errs)/len(errs):.4f} puan (n={len(errs)})")
        else:
            print(f"  {level:8s}: veri yok")

    # Fon bazinda
    print("\nFon bazında MAE:")
    by_fund: dict[str, list[Decimal]] = {}
    for r in results:
        by_fund.setdefault(r.fund_code, []).append(r.error)
    for fund_code, errs in sorted(by_fund.items(), key=lambda kv: -sum(kv[1]) / len(kv[1])):
        print(f"  {fund_code:6s}: MAE={sum(errs)/len(errs):.4f} puan (n={len(errs)})")

    # Sonuc / oneri
    print("\n" + "-" * 70)
    target = Decimal("0.15")
    unacceptable = Decimal("0.50")
    if mae > unacceptable:
        print(f"🚨 SONUÇ: MAE ({mae:.4f}) kabul edilemez eşiği ({unacceptable}) AŞIYOR.")
        print("ÖNERİ: Bu özellik ŞU HALİYLE YAYINLANMAMALI. Hata payı kaynakları")
        print("(kapsam/tazelik/varlık sınıfı) yukarıdaki kırılımlardan araştırılmalı.")
    elif mae > target:
        print(f"⚠️  SONUÇ: MAE ({mae:.4f}) hedefi ({target}) aşıyor ama kabul edilemez")
        print(f"    eşiğin ({unacceptable}) altında -- SINIRLI/UYARILI yayın düşünülebilir")
        print("    (örn. sadece 'yüksek' güven seviyesindeki tahminler gösterilerek).")
    else:
        print(f"✅ SONUÇ: MAE ({mae:.4f}) hedefin ({target}) altında.")


# CANLI tarama ile bulunan, TEFAS kategorisi uygun VE KAP'ta gerçekten
# ayrıştırılabilir fonlar (bkz. modül üst notu).
_DISCOVERED_FUNDS: list[tuple[str, str]] = []  # main() içinde doldurulur


def _discover_funds(candidates: list[str], min_count: int = 10) -> list[tuple[str, str]]:
    """Aday listesini tarar, (kod, kategori) olarak UYGULANABİLİR VE
    KAP'ta ayrıştırılabilir olanları döner. `min_count`'a ulaşınca DAHİ
    TÜM listeyi tarar (rapordaki "elenenler" bilgisi de değerlidir)."""
    found: list[tuple[str, str]] = []
    for code in candidates:
        try:
            info = tefas.fetch_fund_info(code)
        except tefas.TefasError as exc:
            print(f"  {code}: fetch_fund_info hatası ({exc}), atlanıyor.")
            continue
        applicable, reason = fund_estimator.is_estimable_fund_type(info.type)
        if not applicable:
            print(f"  {code}: UYGULANAMAZ -- {reason}")
            continue
        time.sleep(COURTESY_DELAY_SECONDS)
        portfolio = kfp.fetch_latest_portfolio(code)
        if portfolio is None or not portfolio.holdings:
            print(f"  {code}: kategori uygun ({info.type}) ama KAP portföyü ayrıştırılamadı, atlanıyor.")
            continue
        hisse_pct = sum(h.weight_pct for h in portfolio.holdings if h.instrument_type == "hisse")
        if hisse_pct < 50:
            print(f"  {code}: KAP portföyü ayrıştırıldı ama hisse ağırlığı çok düşük ({hisse_pct}%), atlanıyor.")
            time.sleep(COURTESY_DELAY_SECONDS)
            continue
        print(f"  {code}: OK ({info.type}, hisse ağırlığı %{hisse_pct}, {len(portfolio.holdings)} kalem)")
        found.append((code, info.type))
        time.sleep(COURTESY_DELAY_SECONDS)
    return found


def main() -> int:
    config.setup_logging()

    # CANLI tarandı (2026-08-05): "hisse senedi" adı geçen ~36 TEFAS fonu
    # arasından TEFAS kategorisi uygun ("Hisse Senedi Fonu"), KAP'ta
    # GERÇEKTEN ayrıştırılabilir VE hisse ağırlığı anlamlı (≥%50) olan 10
    # fon. Elenenler (Serbest Fon kategorisi VEYA KAP parser'ı güvenilir
    # sonuç veremedi) bu dosyanın geliştirme sürecinde ayrı ayrı loglandı
    # (bkz. PROJE_HAFIZASI/08_DEGISIKLIK_GUNLUGU.md) -- burada TEKRAR
    # taranmaları gereksiz zaman/istek harcar, bu yüzden sabitlendi.
    candidates = ["PHE", "ACC", "AEV", "AK3", "AKU", "ALC", "BDY", "BHA", "BID", "ADP"]

    print("=== Faz 18 doğrulama: uygulanabilir fon taraması ===")
    discovered = _discover_funds(candidates)
    print(f"\n{len(discovered)} / {len(candidates)} aday uygulanabilir bulundu.")

    if len(discovered) < 3:
        print("\n🚨 Yeterli sayıda uygulanabilir/ayrıştırılabilir fon bulunamadı -- doğrulama YAPILAMIYOR.")
        return 1

    all_results: list[_TestResult] = []
    for fund_code, category in discovered:
        try:
            all_results.extend(_validate_fund(fund_code, category))
        except Exception as exc:  # noqa: BLE001 -- bir fondaki hata TUM doğrulamayı COKERTMEMELI
            print(f"  {fund_code}: beklenmeyen hata, atlanıyor: {exc}")

    _print_report(all_results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
