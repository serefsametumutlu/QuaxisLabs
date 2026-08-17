"""KAP'ta son `--days` gunde yayinlanmis 'Finansal Rapor' bildirimlerini
proaktif tespit edip, o bildirimi yayinlayan BIST sirketlerini
`tarama_toplu.py` ile AYNI v2 cok-mercekli motorla HEDEFLI olarak
yeniden tarar (MarketScanResult upsert).

NEDEN AYRI BIR SCRIPT: `src/bot/pipeline.py::_patch_with_kap_if_fresher`
HER ticker taranirken KENDI KAP kontrolunu zaten yapiyor (bkz. o modulun
ust notu) -- ama bu SADECE o ticker `tarama_toplu.py --universe tam` ile
(DB'deki tazelik kuyruguna gore, `SCAN_STALE_AFTER_DAYS=7` esigiyle)
zaten taranmaya SIRA GELDIGINDE tetiklenir. Bu script TERSINE calisir:
KAP'i PROAKTIF tarayip "bugun/son N gunde kim yeni bilanco yayinladi"
sorusuna cevap verir, SADECE o sirketleri HEMEN, tazelik kuyrugunu
BEKLEMEDEN hedefli olarak yeniden tarar -- tum evreni (--universe tam,
657 BIST sirketi) yeniden taramaya GEREK KALMAZ.

Kategori filtresi (`Disclosure.category == "Finansal Rapor"`, yani KAP
API'sinin `subject` alani): `src/fetchers/kap_financials.py::
find_latest_financial_report_disclosure` docstring'indeki CANLI dogrulanmis
notla AYNI ayrimi kullanir -- "disclosureCategory=='FR' (subject='Finansal
Rapor')" gercek XBRL veri iceren bildirimdir, ayni pakette gelen "Faaliyet
Raporu"/"Sorumluluk Beyani" gibi companion bildirimler FARKLI bir subject
tasir (disclosureClass="FR" ile KARISTIRILMAMALI, o alan cok daha genis).

`kap.fetch_all_disclosures()` guvenli pencere sinirina (gunluk deger:
`_MAX_SAFE_ALL_DISCLOSURES_DAYS=10`, KAP yaniti 2000 satirda kesiliyor)
tabidir -- `--days` bu sinirin USTUNE CIKARSA ValueError ile ACIKCA durur
(sessizce eksik sonuc URETMEZ).

Kullanim:
    python scripts/kap_yeni_bilanco_tara.py                # bugun + dun (varsayilan --days 1)
    python scripts/kap_yeni_bilanco_tara.py --days 3        # son 3 gun
    python scripts/kap_yeni_bilanco_tara.py --dry-run       # sadece tespit et, TARAMA YAPMA
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))  # ayni dizindeki tarama_toplu.py icin

import config  # noqa: E402
from sqlalchemy import select  # noqa: E402

from src.db import repository  # noqa: E402
from src.db.models import Company  # noqa: E402
from src.fetchers import kap  # noqa: E402
from tarama_toplu import _run_batch  # noqa: E402 -- ayni dizin, mevcut tarama motorunu TEKRAR YAZMAMAK icin

config.setup_logging()

_FR_CATEGORY = "Finansal Rapor"


def _detect_bist_tickers_with_fresh_fr(days: int) -> dict[str, list[kap.Disclosure]]:
    """Son `days` gunde 'Finansal Rapor' kategorisinde bildirim yayinlayan,
    VE DB'de zaten tanidigimiz (`Company.market=='BIST'`) sirketleri
    `{ticker: [o tickera ait bildirimler]}` seklinde doner. Tanimadigimiz/
    fon-KAP-uyesi gibi eslesmeler (Company tablosunda yoksa) SESSIZCE elenir
    -- bu script SADECE mevcut BIST evrenini gunceller, yeni sirket EKLEMEZ."""
    disclosures = kap.fetch_all_disclosures(days=days)
    fr_disclosures = [d for d in disclosures if d.category == _FR_CATEGORY]

    with repository.get_session() as session:
        known_tickers = set(session.execute(select(Company.ticker).where(Company.market == "BIST")).scalars().all())

    hits: dict[str, list[kap.Disclosure]] = {}
    for d in fr_disclosures:
        for raw_code in d.stock_codes.split(","):
            ticker = raw_code.strip().upper()
            if ticker in known_tickers:
                hits.setdefault(ticker, []).append(d)
    return hits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="KAP'ta yeni yayinlanmis 'Finansal Rapor' bildirimi olan BIST sirketlerini tespit edip hedefli yeniden tarar."
    )
    parser.add_argument("--days", type=int, default=1, help="Son kac gunun KAP bildirimleri taransin (varsayilan: 1 -- bugun).")
    parser.add_argument("--dry-run", action="store_true", help="Sadece tespit edilen ticker listesini raporla, TARAMA YAPMA.")
    args = parser.parse_args(argv)

    print(f"KAP'ta son {args.days} gunde '{_FR_CATEGORY}' bildirimi taraniyor (tum uyeler, tek istek)...")
    hits = _detect_bist_tickers_with_fresh_fr(args.days)

    if not hits:
        print("Yeni Finansal Rapor bulunamadi -- hedefli tarama yapilacak sirket yok.")
        return 0

    tickers = sorted(hits)
    print(f"{len(tickers)} BIST sirketinde yeni Finansal Rapor tespit edildi:")
    for ticker in tickers:
        en_yeni = max(hits[ticker], key=lambda d: d.date)
        print(f"  {ticker}: {en_yeni.date:%d.%m.%Y %H:%M} -- {en_yeni.title[:80]}")

    if args.dry_run:
        print("\n[--dry-run] Yukaridaki sirketler taranacakti, DB'ye YAZILMADI.")
        return 0

    print(f"\n{len(tickers)} sirket hedefli olarak yeniden taraniyor (v2 cok-mercekli motor, MarketScanResult upsert)...")
    counts = _run_batch(tickers, "BIST", dry_run=False)
    print(f"\nBitti: {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
