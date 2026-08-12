"""docs/spec/spec_veri_tamlik_yol_haritasi.md §Faaliyet Raporu / Dipnot
Araştırması, "Önerilen somut ilk adım": `src/ai/kar_kaynagi.py::
analyze_kar_kaynagi()`'i BİST evrenindeki şirketler için toplu çalıştırıp
sonucu `MarketScanResult.faaliyet_raporu_bulgulari`'a yazan AYRI bir script.

**Neden `scripts/tarama_toplu.py`'ye BAĞLANMADI (görev talimatı gereği):**
bu, HER taramada çalıştırılamayacak kadar SICAK/AĞIR bir işlem -- ticker
başına: 1 KAP bildirim listesi isteği + 1 KAP bildirim detay sayfası + 1
PDF indirme (birkaç MB) + 1 Gemini API çağrısı. `tarama_toplu.py`'nin
`--universe tam` modu GÜNDE binlerce şirketi tarayabilir; bu script AYNI
pacing'le çalıştırılırsa hem KAP'ı hem Gemini kotasını riske atar.

**Kapsam BAŞTA BİLİNÇLİ OLARAK dar tutulmuştu, kullanıcı 2026-08-12'de TAM
evrene açılmasını ONAYLADI:** script başlangıçta SADECE bir statik pilot
liste (`--tickers` veya `--universe pilot` -- `scripts/tarama_toplu.py::
BIST30_PILOT`, 32 ticker) kabul ediyordu; TAM BİST evrenine açan bir mod
BİLEREK YOKTU ("tam evrene AÇMA, kullanıcı onayı GEREKİR" görev talimatıyla).
Kullanıcı onayının ARDINDAN `--universe full` eklendi: `MarketScanResult`
tablosunda `market='BIST' AND scan_status='ok'` olan (yani `tarama_toplu.py`
ile ZATEN başarıyla taranmış) TÜM ticker'ları işler (bkz. `repository.
get_ok_scanned_tickers()` -- `tarama_toplu.py::get_scan_queue()`'dan
KASITLI OLARAK FARKLI kaynak: `Company` değil `MarketScanResult`, çünkü bu
script HENÜZ taranmamış bir şirkete YENİ bir satır AÇMAZ, bkz. aşağıdaki
"Satır (...) HENÜZ YOKSA" notu). Kademeli çalıştırma için `--limit` bu modda da GEÇERLİDİR (ticker
listesi alfabetik sıralı olduğundan ardışık çalıştırmalar TUTARLI bir
alt-küme üzerinde ilerler).

Satır (ticker+market) `MarketScanResult`'ta HENÜZ YOKSA (yani `tarama_toplu.py`
ile hiç taranmamış bir şirket) bu script o ticker'ı ATLAR -- faaliyet raporu
bulgusu, ZATEN var olan bir tarama sonucunu ZENGİNLEŞTİRİR, kendi başına
bir satır kaynağı DEĞİLDİR (bkz. `repository.update_faaliyet_raporu_
bulgulari()` docstring'i).

Kullanım:
    python scripts/kar_kaynagi_toplu.py --tickers THYAO SAHOL
    python scripts/kar_kaynagi_toplu.py --universe pilot --limit 5
    python scripts/kar_kaynagi_toplu.py --universe pilot --dry-run
    python scripts/kar_kaynagi_toplu.py --universe full --dry-run     # TAM evrenin GERÇEK boyutunu ölç, ağa GİTME
    python scripts/kar_kaynagi_toplu.py --universe full --limit 50    # kademeli, TAM evrenden alfabetik ilk 50
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402

from scripts import tarama_toplu  # noqa: E402
from src.ai import kar_kaynagi  # noqa: E402
from src.db import repository  # noqa: E402
from src.db.models import MarketScanResult  # noqa: E402

config.setup_logging()
logger = logging.getLogger(__name__)

# Ticker başına KAP (bildirim listesi + detay sayfası + PDF indirme) VE
# Gemini çağrısı İÇEREN, `tarama_toplu.py::SCAN_PACING_SECONDS_BIST`'ten
# (0.3sn) KASITLI OLARAK DAHA UZUN bir bekleme -- bu script'in HER ticker'ı
# en az 3 ayrı KAP isteği + 1 Gemini isteği yapıyor (bkz. modül üst notu).
PACING_SECONDS = 2.0

_MARKET = "BIST"  # spec kapsamı: bu turda SADECE BİST (NASDAQ ayrı/sonraki tur)


def _run_one(ticker: str) -> str:
    """Tek bir ticker'ı işler + `MarketScanResult.faaliyet_raporu_bulgulari`'a
    yazar. Döndürdüğü durum özet raporlama içindir; hiçbir hata script'i
    ÇÖKERTMEZ (tarama_toplu.py::_scan_one İLE AYNI ilke)."""
    try:
        bulgular = kar_kaynagi.analyze_kar_kaynagi(ticker)
    except Exception as exc:  # noqa: BLE001 -- Kural 9: bir ticker'ın hatası TÜM partiyi durdurmamalı
        logger.warning("%s icin kar kaynagi analizi beklenmeyen sekilde basarisiz: %s", ticker, exc)
        return "hata"

    if bulgular is None:
        return "bildirim_bulunamadi"

    with repository.get_session() as session:
        row = repository.update_faaliyet_raporu_bulgulari(session, ticker, _MARKET, bulgular.to_dict())
        if row is None:
            return "taranmamis_sirket"
        session.commit()
    return bulgular.source  # "llm" | "fallback"


def _resolve_tickers(args: argparse.Namespace) -> list[str]:
    if args.tickers:
        return [t.strip().upper() for t in args.tickers]
    if args.universe == "pilot":
        return list(tarama_toplu.BIST30_PILOT)
    if args.universe == "full":
        with repository.get_session() as session:
            return repository.get_ok_scanned_tickers(session, _MARKET)
    raise ValueError("--tickers veya --universe pilot/full belirtilmeli.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="BİST şirketleri için KAP faaliyet raporundan nitel 'kâr kaynağı' bulgularını çıkarır ve MarketScanResult.faaliyet_raporu_bulgulari'a yazar."
    )
    parser.add_argument("--tickers", nargs="+", help="İşlenecek BİST ticker'ları (örn. THYAO SAHOL).")
    parser.add_argument(
        "--universe", choices=("pilot", "full"), default=None,
        help="'pilot': tarama_toplu.BIST30_PILOT (32 ticker). 'full': MarketScanResult'ta market='BIST' AND scan_status='ok' olan TÜM ticker'lar (kullanıcı onayıyla, 2026-08-12).",
    )
    parser.add_argument("--limit", type=int, default=None, help="İşlenecek MAKS ticker sayısı (pilot/full listeyi kısaltmak için, kademeli çalıştırma).")
    parser.add_argument("--dry-run", action="store_true", help="Sadece işlenecek listeyi raporla, ağa GİTME.")
    args = parser.parse_args()

    if not args.tickers and args.universe is None:
        parser.error("--tickers VEYA --universe pilot/full belirtilmeli.")

    tickers = _resolve_tickers(args)
    if args.limit is not None:
        tickers = tickers[: args.limit]

    print(f"=== BİST faaliyet raporu / kâr kaynağı ({args.universe or 'tickers'}): {len(tickers)} ticker ===")
    if args.dry_run:
        if args.universe == "full":
            tahmini_saniye = len(tickers) * PACING_SECONDS
            print(
                f"[--dry-run] TAM evren (scan_status='ok', BİST): {len(tickers)} şirket "
                f"-- işlenecekti (HİÇBİR ağ isteği ATILMADI). Kaba süre tahmini: "
                f"{len(tickers)} şirket × ~{PACING_SECONDS:.0f}sn/şirket (sabit bekleme) "
                f"+ KAP/Gemini yanıt süreleri ≈ en az {tahmini_saniye / 3600:.1f} saat "
                f"(gerçek KAP/Gemini gecikmeleri EKLENMEMİŞTİR, bu SADECE PACING_SECONDS tabanlı bir ALT SINIR)."
            )
        else:
            print(f"[--dry-run] İşlenecekti: {', '.join(tickers)} -- HİÇBİR ağ isteği ATILMADI.")
        return 0

    counts: dict[str, int] = {}
    for i, ticker in enumerate(tickers, start=1):
        status = _run_one(ticker)
        counts[status] = counts.get(status, 0) + 1
        print(f"  [{i}/{len(tickers)}] {ticker} -> {status}", flush=True)
        time.sleep(PACING_SECONDS)

    ozet = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
    print(f"Tamamlandı: {len(tickers)} ticker işlendi ({ozet}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
