"""docs/spec/spec_dashboard.md Faz 5 adım 2: BİST + NASDAQ evrenindeki HER
şirket için mevcut v2 çok-mercekli motoru (`src.bot.pipeline.
compute_multi_lens_score_for_ticker()`, DEĞİŞTİRİLMEZ) çağırıp sonucu
kalıcı, sorgulanabilir bir DB tablosunda (`MarketScanResult`) biriktirir.

`scripts/refresh_universe.py` (Faz 2) ile BİREBİR AYNI ilkeler -- checkpoint
DB'nin KENDİSİDİR, ayrı bir dosya/kuyruk tablosu YOK; rate-limit'e saygı
mevcut fetcher içi mekanizmalardan (config.HTTP_RATE_LIMIT_DELAY_SECONDS,
retry-backoff) BAĞIMSIZ, ek bir PARTİLER-ARASI bekleme sabitiyle sağlanır
(spec §Eşikler ve ağırlıklar: SCAN_PACING_SECONDS_BIST/_NASDAQ).

**Kritik fark (refresh_universe.py'den, bkz. spec §Mimari karar 1):** bu
script HER ticker için TAM bir `compute_multi_lens_score_for_ticker()`
çağrısı yapar -- İÇİNDE potansiyel olarak tam mali tablo fetch'i VE 400
günlük OHLCV fiyat geçmişi (DB önbelleği YOK, HER çağrıda ağa gider) İÇERİR.
Bu yüzden per-company maliyeti refresh_universe.py'den KATBEKAT yüksektir.

Kullanım (spec §Orkestrasyon adımları + §çekirdek ticker kümesi -- BİREBİR):
    python scripts/tarama_toplu.py --universe bist30              # küçük doğrulama, BİST (32 ticker, statik liste)
    python scripts/tarama_toplu.py --universe nasdaq30             # küçük doğrulama, NASDAQ (30 ticker, statik liste)
    python scripts/tarama_toplu.py --universe pilot                # BİST30 + NASDAQ30 pilot listeleri BİRLİKTE (--market ile daraltılabilir)
    python scripts/tarama_toplu.py --market bist                   # tam BİST evreni, 1 parti (limit=200), DB kuyruğu (get_scan_queue)
    python scripts/tarama_toplu.py --market nasdaq --limit 300      # NASDAQ, kademeli, filer_category filtreli
    python scripts/tarama_toplu.py --market bist --dry-run          # sadece kuyruk boyutunu raporla, hesaplama YAPMA
    python scripts/tarama_toplu.py --market nasdaq --dry-run        # filtrelenmiş "kaliteli" NASDAQ evreninin GERÇEK boyutunu ölç

`--universe pilot` VE `--universe full` spec'in BİREBİR `tam|bist30|nasdaq30`
seçeneklerine (kodlama fazına bırakılan CLI ayrıntısı) eklenmiş KULLANIŞLI
takma adlardır -- `full`, `tam`'ın birebir eş anlamlısıdır; `pilot`,
`bist30`+`nasdaq30`'u --market seçimine göre BİRLİKTE çalıştırır (ikisi de
spec'in zorunlu kıldığı DAVRANIŞI DEĞİŞTİRMEZ, sadece iş akışını kolaylaştırır).
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402
from sqlalchemy import select  # noqa: E402

from src.analysis import lens_bilesik_skor  # noqa: E402
from src.analysis.lens_common import LensSonucu  # noqa: E402
from src.bot import pipeline  # noqa: E402
from src.db import repository  # noqa: E402
from src.db.models import Company, EarningsCalendar, utcnow_naive  # noqa: E402
from src.db.repository import TickerMarketConflictError  # noqa: E402

config.setup_logging()
logger = logging.getLogger(__name__)

# spec §Eşikler ve ağırlıklar (docs/spec/spec_dashboard.md) -- BİREBİR.
SCAN_STALE_AFTER_DAYS = 7
SCAN_PACING_SECONDS_BIST = 0.3
SCAN_PACING_SECONDS_NASDAQ = 0.15
DEFAULT_LIMIT_BIST = 200
DEFAULT_LIMIT_NASDAQ = 150

# spec §"--universe bist30/nasdaq30 -- ÇEKİRDEK ticker kümesi" -- BİREBİR
# (kaynak+tarih spec'in dipnotlarında[^bist30][^ndx] belgelendi, burada
# TEKRAR uydurma YAPILMADI, sadece spec'ten kopyalandı).
BIST_DOGRULANMIŞ_CEKIRDEK = [
    "THYAO", "ASELS", "TUPRS", "KCHOL", "AKBNK",  # AKBNK=banka (UFRS)
    "SISE", "BIMAS", "EREGL", "FROTO", "ENKAI",
    "ANSGR",  # sigorta (UFRS_K)
    "KTLEV",  # finansman (XI_29K)
]
NASDAQ_DOGRULANMIŞ_CEKIRDEK = [
    "AAPL", "TSLA", "NVDA", "MSFT", "GOOGL",
    "AMZN", "META", "NFLX", "AMD", "PYPL",
]
BIST30_EK_20 = [
    "AEFES", "ASTOR", "DSTKF", "EKGYO", "GARAN", "GUBRF", "ISCTR", "KRDMD",
    "MGROS", "PETKM", "PGSUS", "SAHOL", "SASA", "TAVHL", "TCELL", "TOASO",
    "TRALT", "TTKOM", "VAKBN", "YKBNK",
]
BIST30_PILOT = BIST_DOGRULANMIŞ_CEKIRDEK + BIST30_EK_20  # toplam 32
NASDAQ30_EK_20 = [
    "ADBE", "ADI", "ADP", "ADSK", "AMAT", "AMGN", "ASML", "AVGO", "BKNG",
    "CHTR", "CMCSA", "COST", "CRWD", "CSCO", "CSX", "DASH", "EA", "EXC",
    "FTNT", "GILD",
]
NASDAQ30_PILOT = NASDAQ_DOGRULANMIŞ_CEKIRDEK + NASDAQ30_EK_20  # toplam 30

_PACING_BY_MARKET = {"BIST": SCAN_PACING_SECONDS_BIST, "NASDAQ": SCAN_PACING_SECONDS_NASDAQ}
_DEFAULT_LIMIT_BY_MARKET = {"BIST": DEFAULT_LIMIT_BIST, "NASDAQ": DEFAULT_LIMIT_NASDAQ}
_CURRENCY_BY_MARKET = {"BIST": "TRY", "NASDAQ": "USD"}
# get_scan_queue()/--dry-run'da "toplam kuyruk boyutu"nu ölçmek için pratik
# bir üst sınır (gerçek evren -- BİST 643, NASDAQ filtrelenmiş alt küme --
# bu rakamın ÇOK altında, bkz. spec §Girdiler).
_QUEUE_SIZE_PROBE_LIMIT = 100_000


def _priority_tickers(session, market: str) -> set[str]:
    """spec §Formüller-2 (Öncelik kümesi) -- BİREBİR: bilanço tarihi ±3 gün
    penceresindeki şirketler için 7 günlük standart pencereyi BEKLEMEDEN
    zorla yeniden tara."""
    cutoff_gecmis = utcnow_naive() - timedelta(days=3)
    cutoff_gelecek = utcnow_naive() + timedelta(days=3)
    rows = session.execute(
        select(EarningsCalendar.ticker).where(
            EarningsCalendar.market == market,
            EarningsCalendar.expected_date.between(cutoff_gecmis.date(), cutoff_gelecek.date()),
        )
    ).scalars().all()
    return set(rows)


def _mercek_alanlari(mercek: LensSonucu | None) -> tuple[Decimal | None, str | None, Decimal | None]:
    if mercek is None:
        return None, None, None
    return mercek.total_score, mercek.badge, mercek.data_coverage_pct


def _component_to_dict(bilesen) -> dict:
    """JSON sütununa yazılabilir (Decimal İÇERMEYEN) sözlük -- SQLAlchemy'nin
    varsayılan JSON serileştiricisi (Python `json` modülü) Decimal'i
    SERİLEŞTİREMEZ, bu yüzden sayısal alanlar `str()` ile metne çevrilir
    (hassasiyet KAYBOLMAZ, float'a YUVARLANMAZ -- "Decimal her yerde" ilkesi
    JSON-on-SQLite katmanında BÖYLE korunur)."""
    return {
        "name": bilesen.name,
        "score": str(bilesen.score) if bilesen.score is not None else None,
        "weight_nominal": str(bilesen.weight_nominal),
        "weight_effective": str(bilesen.weight_effective),
        "contribution": str(bilesen.contribution),
        "reasoning_tr": bilesen.reasoning_tr,
    }


def _mercekler_detay(profil: lens_bilesik_skor.MercekProfili) -> dict:
    detay = {}
    for isim, mercek in (("değer", profil.deger), ("kalite", profil.kalite), ("büyüme", profil.buyume), ("güvenlik", profil.guvenlik)):
        if mercek is not None:
            detay[isim] = [_component_to_dict(b) for b in mercek.components]
    return detay


def _scan_one(ticker: str, market: str) -> str:
    """Tek bir ticker'ı tarar + `MarketScanResult`'a upsert eder -- spec
    §Orkestrasyon adımları madde 3 BİREBİR. Döndürdüğü `scan_status`
    özet raporlama içindir; hiçbir hata script'i ÇÖKERTMEZ (mevcut
    `_refresh_nasdaq_step1`'in "tek satır hatası tüm batch'i durdurmaz"
    ilkesiyle AYNI).

    🚨 CANLI HATA + DÜZELTME (bu turda pilot doğrulamasında bulundu):
    `pipeline.compute_multi_lens_score_for_ticker()` KENDİ İÇİNDE (İş
    Yatırım/KAP/SEC fetch'lerinin ardından) BİRDEN FAZLA AYRI `repository.
    get_session()` açıp COMMIT edip kapatıyor (bkz. `_fetch_and_store()`).
    İlk sürümde bu fonksiyon dışarıdan TEK bir (tüm parti boyunca AÇIK
    kalan) `session` parametresi alıyordu -- o DIŞ session'ın (salt-okuma
    bile olsa) SQLite'ta açık bıraktığı transaction, pipeline'ın İÇ
    session'larının COMMIT'te EXCLUSIVE kilit almasını ENGELLEYİP CANLI
    olarak `sqlite3.OperationalError: database is locked` ÜRETTİ (pilot
    çalıştırmasında THYAO/ASELS DIŞINDA NEREDEYSE HER ticker'da GÖZLENDİ).
    Çözüm: bu fonksiyon ARTIK session'ı KENDİSİ, SADECE pipeline çağrısı
    TAMAMEN BİTTİKTEN SONRA (kısa ömürlü, tek-ticker'lık) açar -- pipeline
    kendi iç session'larını AÇARKEN dışarıda HİÇBİR session açık
    TUTULMAZ, kilit çakışması KÖKTEN ortadan kalkar."""
    try:
        sonuc = pipeline.compute_multi_lens_score_for_ticker(ticker, market=market)
    except pipeline.TickerNotFoundError:
        with repository.get_session() as session:
            repository.upsert_market_scan_result(session, ticker, market, scan_status="veri_yok")
            session.commit()
        return "veri_yok"
    except pipeline.UnsupportedCompanyTypeError as exc:
        with repository.get_session() as session:
            repository.upsert_market_scan_result(session, ticker, market, scan_status="desteklenmiyor", error_detail=str(exc)[:500])
            session.commit()
        return "desteklenmiyor"
    except TickerMarketConflictError as exc:
        logger.warning("%s (%s) BIST/NASDAQ sembol cakismasi -- atlaniyor: %s", ticker, market, exc)
        return "hata"
    except Exception as exc:  # noqa: BLE001 -- transient/beklenmeyen ag hatasi, script COKMEMELI (spec madde 3d)
        logger.warning("%s (%s) taranirken hata (bir SONRAKI ticker'a geciliyor): %s", ticker, market, exc)
        with repository.get_session() as session:
            repository.upsert_market_scan_result(session, ticker, market, scan_status="hata", error_detail=str(exc)[:500])
            session.commit()
        return "hata"

    profil = sonuc.bilesik.mercekler
    deger_score, deger_badge, deger_cov = _mercek_alanlari(profil.deger)
    kalite_score, kalite_badge, kalite_cov = _mercek_alanlari(profil.kalite)
    buyume_score, buyume_badge, buyume_cov = _mercek_alanlari(profil.buyume)
    guvenlik_score, guvenlik_badge, guvenlik_cov = _mercek_alanlari(profil.guvenlik)
    bilesik_cov = lens_bilesik_skor.hesapla_veri_kapsam_ozeti(sonuc.bilesik)

    vm = sonuc.valuation_metrics

    with repository.get_session() as session:
        company_row = session.get(Company, ticker)
        repository.upsert_market_scan_result(
            session,
            ticker,
            market,
            scan_status="ok",
            company_name=sonuc.company_name,
            ust_sektor=company_row.ust_sektor if company_row else None,
            sirket_turu=company_row.sirket_turu if company_row else None,
            template=sonuc.template,
            year=sonuc.period[0],
            period=sonuc.period[1],
            deger_score=deger_score, deger_badge=deger_badge, deger_coverage_pct=deger_cov,
            kalite_score=kalite_score, kalite_badge=kalite_badge, kalite_coverage_pct=kalite_cov,
            buyume_score=buyume_score, buyume_badge=buyume_badge, buyume_coverage_pct=buyume_cov,
            guvenlik_score=guvenlik_score, guvenlik_badge=guvenlik_badge, guvenlik_coverage_pct=guvenlik_cov,
            bilesik_score=sonuc.bilesik.total_score if sonuc.bilesik.data_sufficient else None,
            bilesik_badge=sonuc.bilesik.badge,
            bilesik_data_coverage_pct=bilesik_cov,
            dahil_edilen_mercekler=sonuc.bilesik.dahil_edilen_mercekler,
            current_price=getattr(vm, "price", None),
            market_cap=getattr(vm, "market_cap", None),
            pe_ratio=getattr(vm, "pe_ratio", None),
            pb_ratio=getattr(vm, "pb_ratio", None),
            ev_ebitda=getattr(vm, "ev_ebitda", None),
            currency=_CURRENCY_BY_MARKET.get(market),
            mercekler_detay=_mercekler_detay(profil),
            financial_data_as_of=company_row.last_updated if company_row else None,
            computed_at=utcnow_naive(),
        )
        session.commit()
    return "ok"


def _run_batch(tickers: list[str], market: str, dry_run: bool) -> dict[str, int]:
    """Her ticker KENDİ kısa ömürlü session'ında upsert + commit edilir
    (bkz. `_scan_one` "CANLI HATA + DÜZELTME" notu) -- DB YİNE DE
    checkpoint'tir (spec §Orkestrasyon adımları madde 4'ün RUHU KORUNUR:
    SIGINT/crash durumunda o ana kadar işlenen HER ticker ZATEN kalıcı,
    hatta parti-sonu commit'ten DAHA GRANÜLER/GÜVENLİ bir haliyle)."""
    counts = {"ok": 0, "hata": 0, "desteklenmiyor": 0, "veri_yok": 0}
    if dry_run:
        print(f"[--dry-run] {market}: {len(tickers)} ticker taranacaktı (DB'ye YAZILMADI, hesaplama YAPILMADI).")
        return counts

    pacing = _PACING_BY_MARKET.get(market, SCAN_PACING_SECONDS_BIST)
    for i, ticker in enumerate(tickers, start=1):
        status = _scan_one(ticker, market)
        counts[status] += 1
        print(f"  [{i}/{len(tickers)}] {ticker} ({market}) -> {status}", flush=True)
        time.sleep(pacing)
    return counts


def _resolve_targets(market_arg: str | None, universe: str) -> list[tuple[str, list[str] | None]]:
    """(market, statik_ticker_listesi_veya_None) çiftlerini döner -- liste
    `None` ise `--universe tam` (DB kuyruğu, `get_scan_queue`) demektir.
    spec §Orkestrasyon adımları madde 2 BİREBİR."""
    if universe == "bist30":
        return [("BIST", BIST30_PILOT)]
    if universe == "nasdaq30":
        return [("NASDAQ", NASDAQ30_PILOT)]

    markets = ["BIST", "NASDAQ"] if market_arg in (None, "all") else [market_arg.upper()]

    if universe == "pilot":
        pilot_by_market = {"BIST": BIST30_PILOT, "NASDAQ": NASDAQ30_PILOT}
        return [(m, pilot_by_market[m]) for m in markets]

    # universe in ("tam", "full") -- DB kuyruğu
    return [(m, None) for m in markets]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="BİST + NASDAQ evrenindeki HER şirket için v2 çok-mercekli skorlamayı toplu çalıştırır ve MarketScanResult'a yazar (bkz. docs/spec/spec_dashboard.md)."
    )
    parser.add_argument("--market", choices=("bist", "nasdaq", "all"), default=None, help="Sadece belirtilen piyasayı işle (varsayılan: ikisi de).")
    parser.add_argument(
        "--universe", choices=("tam", "bist30", "nasdaq30", "pilot", "full"), default="tam",
        help="'tam'/'full': DB kuyruğu (get_scan_queue). 'bist30'/'nasdaq30': statik pilot liste (tek piyasa). "
        "'pilot': bist30+nasdaq30'u --market seçimine göre BİRLİKTE çalıştırır.",
    )
    parser.add_argument("--limit", type=int, default=None, help=f"'tam' evrende işlenecek MAKS satır sayısı (varsayılan: BİST {DEFAULT_LIMIT_BIST}, NASDAQ {DEFAULT_LIMIT_NASDAQ}).")
    parser.add_argument("--dry-run", action="store_true", help="Sadece kuyruk/liste boyutunu raporla, hesaplama YAPMA.")
    args = parser.parse_args()

    universe = "tam" if args.universe == "full" else args.universe
    targets = _resolve_targets(args.market, universe)

    toplam_counts = {"ok": 0, "hata": 0, "desteklenmiyor": 0, "veri_yok": 0}
    kalan_kuyruk_notlari: list[str] = []

    for market, static_list in targets:
        if static_list is not None:
            print(f"=== {market} ({universe}): {len(static_list)} ticker (statik liste) ===")
            counts = _run_batch(static_list, market, args.dry_run)
        else:
            limit = args.limit if args.limit is not None else _DEFAULT_LIMIT_BY_MARKET[market]
            with repository.get_session() as session:
                priority = _priority_tickers(session, market)
                queue = repository.get_scan_queue(session, market, SCAN_STALE_AFTER_DAYS, limit, priority_tickers=priority)
                tickers = [c.ticker for c in queue]
            print(f"=== {market} (tam evren, DB kuyruğu): işlenecek {len(tickers)} ticker (limit={limit}) ===")
            counts = _run_batch(tickers, market, args.dry_run)
            if not args.dry_run:
                with repository.get_session() as session:
                    kalan = repository.get_scan_queue(session, market, SCAN_STALE_AFTER_DAYS, _QUEUE_SIZE_PROBE_LIMIT)
                kalan_kuyruk_notlari.append(f"{market}: {len(kalan)}")

        for key in toplam_counts:
            toplam_counts[key] += counts[key]

    toplam = sum(toplam_counts.values())
    if args.dry_run:
        print("[--dry-run] Hiçbir hesaplama YAPILMADI, DB'ye YAZILMADI.")
        return 0

    ozet = (
        f"{toplam} şirket tarandı ({toplam_counts['ok']} başarılı, {toplam_counts['hata']} hata, "
        f"{toplam_counts['desteklenmiyor']} desteklenmiyor, {toplam_counts['veri_yok']} veri_yok)"
    )
    if kalan_kuyruk_notlari:
        ozet += f", kuyrukta kaldı ({', '.join(kalan_kuyruk_notlari)}) (sonraki çalıştırmaya)."
    else:
        ozet += "."
    print(ozet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
