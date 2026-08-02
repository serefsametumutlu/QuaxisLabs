"""Faz 2 (KAP) teslim kriteri demo scripti.

fetch_disclosures() + get_top_disclosures() ile cekilen son 90 gunun
onemli KAP bildirimlerini tarih + etiket + baslik formatinda listeler.

Kullanim:
    python scripts/demo_kap.py TAVHL
    python scripts/demo_kap.py TAVHL --days 30 --limit 10
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402
from src.fetchers.kap import (  # noqa: E402
    IMPORTANCE_HIGH,
    KapCompanyNotFoundError,
    KapError,
    fetch_disclosures,
    get_top_disclosures,
)


def main() -> int:
    config.setup_logging()

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ticker", help="BIST hisse kodu (orn. TAVHL)")
    parser.add_argument("--days", type=int, default=90, help="Kac gun geriye gidilecek (varsayilan: 90)")
    parser.add_argument("--limit", type=int, default=5, help="En fazla kac bildirim gosterilecek (varsayilan: 5)")
    args = parser.parse_args(sys.argv[1:])

    try:
        disclosures = fetch_disclosures(args.ticker, days=args.days)
    except KapCompanyNotFoundError as exc:
        print(f"HATA: {exc}")
        return 1
    except KapError as exc:
        print(f"HATA: {exc}")
        return 1

    print(f"{args.ticker} | son {args.days} gunde toplam {len(disclosures)} bildirim")
    print()

    top = get_top_disclosures(disclosures, limit=args.limit)
    if not top:
        print("Gosterilecek bildirim yok.")
        return 0

    for disclosure in top:
        etiket = "[ONEMLI]" if disclosure.importance == IMPORTANCE_HIGH else "[rutin] "
        print(f"{disclosure.date:%Y-%m-%d %H:%M} | {etiket} | {disclosure.category} | {disclosure.title}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
