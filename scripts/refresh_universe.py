"""YOL_HARİTASI.md Faz 2, adım 3: BİST + NASDAQ sektör/evren verisini
(Company.ust_sektor, sirket_turu, sic_code, exchange, cik, sector_updated_at)
doldurur/tazeler -- bkz. docs/spec/spec_sektor_evren.md "Tazelik ve
checkpoint tasarımı" bölümü. `refresh_sector_cache.py`/`refresh_takvim_cache.py`
ile AYNI ilke: ayrı, zamanlanmış bir süreçte çalışır, ana `run_pipeline`'ı
BLOKE ETMEZ.

BİST kolu (basit -- tek istek, rate-limit riski yok):
    `kap.fetch_sector_map()` (TEK istek, ~640 şirket) TÜM evreni proaktif
    doldurur/günceller -- checkpoint GEREKMEZ (spec: tek-istek doğası).
    `sirket_turu` KAP ince sektöründen ÖN-TAHMİN olarak yazılır (bkz.
    kap.sirket_turu_on_tahmin_from_kap() -- financial_group dolduğunda bu
    ön-tahminin KESİN değerle üzerine yazılması Faz 3'ün pipeline
    entegrasyonu konusudur, bu script'in kapsamı DIŞINDA).

NASDAQ kolu (büyük evren -- checkpoint ZORUNLU):
    Adım 1 (ucuz bulk keşif, tek istek, rate-limit riski YOK):
        `sec_edgar.fetch_exchange_listings()` ile TÜM SEC filer'ları çekilir,
        `exchange == "Nasdaq"` filtrelenir, bare Company satırları (cik +
        exchange, sic_code=None) DB'ye yazılır.
    Adım 2 (pahalı per-company zenginleştirme, rate-limit'e tabi, checkpoint
        ZORUNLU): `_next_batch()` sorgusuyla ("sic_code IS NULL VEYA
        sector_updated_at SECTOR_STALE_AFTER_DAYS'ten eski") bir PARTİ
        (--limit) işlenir; DB'nin KENDİSİ checkpoint'tir -- SIGINT/crash
        durumunda işlenen satırlar ZATEN commit edilmiş olduğundan bir
        SONRAKİ çalıştırma KALDIĞI YERDEN devam eder.

Kullanım:
    python scripts/refresh_universe.py                     # BİST + NASDAQ (Adım 1+2, limit=500)
    python scripts/refresh_universe.py --market bist
    python scripts/refresh_universe.py --market bist --dry-run   # sadece cek, DB'ye YAZMA
    python scripts/refresh_universe.py --market nasdaq --limit 200
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402
from sqlalchemy import and_, or_, select  # noqa: E402

from src.db import repository  # noqa: E402
from src.db.models import Company, utcnow_naive  # noqa: E402
from src.fetchers import fintables_sektor, kap, sec_edgar  # noqa: E402

config.setup_logging()
logger = logging.getLogger(__name__)

# Sektör/SIC nadiren değişir, günlük yenileme GEREKSİZ -- spec "Tazelik ve
# checkpoint tasarımı" bölümündeki SECTOR_STALE_AFTER_DAYS BİREBİR.
SECTOR_STALE_AFTER_DAYS = 90
# SEC 10 istek/sn/IP limitine saygı için istekler arasında bekleme (spec:
# HTTP_RATE_LIMIT_DELAY_SECONDS=1.0 retry-backoff İÇİNDİR, bu AYRI bir
# sabit -- sadece toplu tarama script'lerinde kullanılır).
SEC_BULK_PACING_SECONDS = 0.12
DEFAULT_NASDAQ_LIMIT = 500


def _refresh_bist(session) -> int:
    """BİST evrenini doldurur/günceller -- kullanıcı isteği (2026-08-13):
    Fintables'ın elle doğrulanmış 44-sektörlük sınıflandırması (`src/
    fetchers/fintables_sektor.py`, `bist-sektorler-ve-hisseler.md`'den
    üretildi) ARTIK BİRİNCİL kaynak (KAP'ın canlı-kazınan ince sektörü
    bazen eksik/hatalı çıkıyordu, örn. alakasız iş modellerini AYNI kovaya
    koyuyordu). KAP'ın `fetch_sector_map()`'i İKİNCİL/YEDEK olarak KALIR
    (persona kural 8: genişlet ama çöpe atma) -- SADECE Fintables listesinde
    OLMAYAN ticker'lar (yeni IPO, henüz Fintables'a düşmemiş) için devreye
    girer, aksi halde Fintables'IN KENDİSİ atlanır (tekrar YAZILMAZ)."""
    print(f"{kap.SEKTORLER_URL} çekiliyor (KAP yedek kaynağı, TÜM BİST şirketleri, tek istek)...")
    kap_sector_map = kap.fetch_sector_map()
    print(f"KAP'tan {len(kap_sector_map)} benzersiz ticker için ince sektör bulundu (yedek).")
    print(f"Fintables birincil kaynağı: {len(fintables_sektor.FINTABLES_TICKER_TO_SEKTOR)} ticker.")

    all_tickers = set(fintables_sektor.FINTABLES_TICKER_TO_SEKTOR) | set(kap_sector_map)
    updated = 0
    fintables_kaynakli = 0
    kap_yedek_kaynakli = 0
    for ticker in all_tickers:
        fine_sector = fintables_sektor.fine_sector_for_ticker(ticker)
        if fine_sector is not None:
            ust_sektor = fintables_sektor.ust_sektor_for_fintables(ticker, fine_sector)
            sirket_turu = fintables_sektor.sirket_turu_on_tahmin_from_fintables(fine_sector)
            fintables_kaynakli += 1
        else:
            fine_sector = kap_sector_map[ticker]
            ust_sektor = kap.ust_sektor_for_kap(ticker, fine_sector)
            sirket_turu = kap.sirket_turu_on_tahmin_from_kap(fine_sector)
            kap_yedek_kaynakli += 1
        repository.upsert_sector_taxonomy(
            session,
            ticker,
            market="BIST",
            sector=fine_sector,
            ust_sektor=ust_sektor,
            sirket_turu=sirket_turu,
        )
        updated += 1
    session.commit()
    print(f"Kaynak dağılımı: {fintables_kaynakli} Fintables, {kap_yedek_kaynakli} KAP yedek.")
    return updated


def _refresh_nasdaq_step1(session) -> tuple[int, int, list[str]]:
    """SEC'in company_tickers_exchange.json'undan TÜM NASDAQ-listeli
    ticker'ları bare Company satırı olarak yazar -- spec "NASDAQ kolu Adım 1"
    BİREBİR: bu adım checkpoint GEREKMEZ (tek bulk dosya).

    Spec "Kenar durumlar": BİST/NASDAQ sembol çakışması (TickerMarketConflictError)
    SESSİZCE EZİLMEZ -- ama tek bir çakışmanın 4000+ satırlık toplu adımı
    komple durdurması da yanlış; hata satır bazında yakalanır, loglanır ve
    SADECE o satır atlanır. `_get_or_create_company` bu hatayı `session.add()`
    ÇAĞRILMADAN ÖNCE fırlatır (bkz. repository.py), bu yüzden session.rollback()
    GEREKMEZ/YAPILMAMALI -- rollback() o ana kadar eklenmiş TÜM commit'lenmemiş
    satırları da geri alır (bu, ilk denemede fark edilen bir hataydı: rollback
    4347 satırdan sadece ~900'ünün kalıcı olmasına yol açmıştı)."""
    print(f"{sec_edgar.TICKERS_EXCHANGE_ENDPOINT} çekiliyor (TÜM SEC filer'ları, tek istek)...")
    listings = sec_edgar.fetch_exchange_listings()
    nasdaq_listings = [row for row in listings if sec_edgar.is_nasdaq_exchange(row.exchange)]
    print(f"{len(listings)} toplam SEC filer'ı arasından {len(nasdaq_listings)} NASDAQ-listeli ticker bulundu.")

    conflicts: list[str] = []
    for row in nasdaq_listings:
        try:
            repository.upsert_sector_taxonomy(
                session,
                row.ticker,
                market="NASDAQ",
                exchange=row.exchange,
                cik=row.cik10,
                touch_sector_updated_at=False,
            )
        except repository.TickerMarketConflictError:
            logger.warning(
                "%s BIST/NASDAQ sembol cakismasi -- NASDAQ evrenine EKLENMEDI (mevcut BIST kaydi korunuyor).",
                row.ticker,
            )
            conflicts.append(row.ticker)
    session.commit()
    return len(listings), len(nasdaq_listings), conflicts


def _next_batch(session, limit: int) -> list[Company]:
    """Sektör/SIC zenginleştirme kuyruğu -- spec "NASDAQ kolu Adım 2"
    kod bloğu BİREBİR: `sic_code IS NULL VEYA sector_updated_at
    SECTOR_STALE_AFTER_DAYS'ten eski VEYA (filer_category IS NULL VE
    sic_code IS NOT NULL)` olan NASDAQ satırları, en eski/hiç işlenmemiş
    ÖNCE olacak şekilde, en fazla `limit` tanesi.

    Üçüncü koşul (docs/spec/spec_dashboard.md §NASDAQ "tam evren" kapsamı,
    "Tek seferlik backfill"): Faz 2'de ZATEN zenginleştirilmiş (sic_code
    dolu) ama `filer_category` alanı HENÜZ YOKKEN işlenmiş satırlar --
    90 günlük tazelik penceresinden BAĞIMSIZ, sadece BU alan boşsa
    yeniden-dene (sic_code'a TEKRAR dokunmaz, sadece filer_category
    eksikse kuyruğa alır)."""
    cutoff = utcnow_naive() - timedelta(days=SECTOR_STALE_AFTER_DAYS)
    return (
        session.execute(
            select(Company)
            .where(
                Company.market == "NASDAQ",
                or_(
                    Company.sic_code.is_(None),
                    Company.sector_updated_at < cutoff,
                    and_(Company.filer_category.is_(None), Company.sic_code.is_not(None)),
                ),
            )
            .order_by(Company.sector_updated_at.asc().nullsfirst())
            .limit(limit)
        )
        .scalars()
        .all()
    )


def _refresh_nasdaq_step2(session, limit: int) -> tuple[int, int]:
    """Kuyruktaki bir PARTİ NASDAQ satırı için SEC submissions'tan SIC kodu
    çeker, ust_sektor/sirket_turu türetir -- spec "NASDAQ kolu Adım 2"
    madde 3-4 BİREBİR (404 -> satır atlanır AMA sector_updated_at YİNE DE
    güncellenir, aksi halde kuyruk SONSUZ döngüye girer)."""
    batch = _next_batch(session, limit)
    print(f"NASDAQ zenginleştirme kuyruğunda işlenecek {len(batch)} satır (limit={limit}).")

    enriched = 0
    skipped_404 = 0
    for company in batch:
        if not company.cik:
            logger.warning("%s icin cik yok (Adim 1 hic calismamis olabilir), atlaniyor.", company.ticker)
            continue

        try:
            sic_info = sec_edgar.fetch_sic_info(company.cik)
        except sec_edgar.CompanyNotFoundError:
            logger.info("%s (CIK%s) icin SEC submissions bulunamadi (404) -- kalici olarak isaretleniyor.", company.ticker, company.cik)
            repository.upsert_sector_taxonomy(session, company.ticker, market="NASDAQ", touch_sector_updated_at=True)
            skipped_404 += 1
            time.sleep(SEC_BULK_PACING_SECONDS)
            continue

        ust_sektor = sec_edgar.ust_sektor_for_sic(company.ticker, sic_info.sic)
        sirket_turu = sec_edgar.sirket_turu_for_sic(sic_info.sic)
        repository.upsert_sector_taxonomy(
            session,
            company.ticker,
            market="NASDAQ",
            sector=sic_info.sic_description,
            ust_sektor=ust_sektor,
            sirket_turu=sirket_turu,
            sic_code=sic_info.sic,
            filer_category=sic_info.category,
            touch_sector_updated_at=True,
        )
        enriched += 1
        time.sleep(SEC_BULK_PACING_SECONDS)

    session.commit()
    return enriched, skipped_404


def main() -> int:
    parser = argparse.ArgumentParser(
        description="BİST + NASDAQ sektör/evren verisini KAP/SEC EDGAR'dan doldurur/tazeler (bkz. docs/spec/spec_sektor_evren.md)."
    )
    parser.add_argument(
        "--market", choices=("bist", "nasdaq"), default=None,
        help="Sadece belirtilen piyasayı işle (varsayılan: ikisi de).",
    )
    parser.add_argument(
        "--limit", type=int, default=DEFAULT_NASDAQ_LIMIT,
        help=f"NASDAQ zenginleştirme adımında (Adım 2) işlenecek MAKS satır sayısı (varsayılan: {DEFAULT_NASDAQ_LIMIT}).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Veriyi kaynaktan çek ve say ama DB'ye YAZMA (doğrulama amaçlı).",
    )
    args = parser.parse_args()

    markets = [args.market] if args.market else ["bist", "nasdaq"]

    if args.dry_run:
        if "bist" in markets:
            sector_map = kap.fetch_sector_map()
            print(f"[--dry-run] BİST: {len(sector_map)} şirket için ince sektör çekildi (DB'ye YAZILMADI).")
        if "nasdaq" in markets:
            listings = sec_edgar.fetch_exchange_listings()
            nasdaq_count = sum(1 for row in listings if sec_edgar.is_nasdaq_exchange(row.exchange))
            print(f"[--dry-run] NASDAQ: {len(listings)} toplam SEC filer'ı arasından {nasdaq_count} NASDAQ-listeli ticker bulundu (DB'ye YAZILMADI).")
        return 0

    with repository.get_session() as session:
        if "bist" in markets:
            updated = _refresh_bist(session)
            print(f"BİST: {updated} şirketin sektör/evren bilgisi güncellendi.")

        if "nasdaq" in markets:
            total, nasdaq_count, conflicts = _refresh_nasdaq_step1(session)
            print(f"NASDAQ Adım 1: {total} toplam SEC filer'ı arasından {nasdaq_count} NASDAQ-listeli satır oluşturuldu/dokunuldu.")
            if conflicts:
                print(f"NASDAQ Adım 1: {len(conflicts)} ticker BIST/NASDAQ sembol çakışması nedeniyle atlandı: {', '.join(conflicts)}")
            enriched, skipped = _refresh_nasdaq_step2(session, args.limit)
            print(f"NASDAQ Adım 2: {enriched} şirket zenginleştirildi, {skipped} şirket 404 ile atlandı (kalıcı işaretlendi).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
