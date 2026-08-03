"""B21 kesif scripti: NVO/TSM/SHEL/BABA gibi ADR'lerin SEC companyfacts
yanitindaki GERCEK tag adlarini (ifrs-full VEYA us-gaap ad alani) ve
raporlama periyodu deseni (SADECE FY mi, yoksa Q1-Q3 de var mi) tespit eder.

Kural 3 geregi: STANDARD_ITEM_MAP_IFRS_FULL yazilmadan ONCE bu script ile
GERCEK tag isimleri dogrulanir, tahmin/varsayim YAPILMAZ.

Kullanim:
    python scripts/explore_ifrs.py NVO
    python scripts/explore_ifrs.py TSM SHEL BABA
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.fetchers import sec_edgar  # noqa: E402

# Aradigimiz temel kavramlar -- bu anahtar kelimelerden herhangi biri tag
# adinda GECIYORSA aday olarak listelenir (kesif amacli, kesin esleme
# DEGIL -- kesin esleme STANDARD_ITEM_MAP_IFRS_FULL'a insan gozuyle
# yazilacak).
_KEYWORDS = [
    "revenue", "grossprofit", "costofsales", "costofgoodssold",
    "operatingincome", "profitfromoperations", "profitloss", "netincome",
    "assets", "liabilities", "equity", "cashandcashequivalent",
    "borrowing", "debt", "depreciation", "amortization",
]


def main() -> int:
    tickers = sys.argv[1:] or ["NVO", "TSM", "SHEL", "BABA"]

    for ticker in tickers:
        print(f"\n{'=' * 70}\n{ticker}\n{'=' * 70}")
        try:
            cik10 = sec_edgar.resolve_cik(ticker)
            payload = sec_edgar._request_companyfacts(cik10)
        except sec_edgar.SecEdgarError as exc:
            print(f"HATA: {exc}")
            continue

        facts = payload.get("facts", {})
        namespaces = sorted(facts.keys())
        print(f"Ad alanlari (namespace): {namespaces}")

        for ns in namespaces:
            if ns not in ("us-gaap", "ifrs-full"):
                continue
            tags = facts[ns]
            print(f"\n  [{ns}] {len(tags)} tag")

            matches = sorted(
                tag for tag in tags if any(kw in tag.lower() for kw in _KEYWORDS)
            )
            for tag in matches:
                units = tags[tag].get("units", {})
                unit_key = next(iter(units), None)
                n_points = len(units.get(unit_key, [])) if unit_key else 0
                fps = Counter(pt.get("fp") for pt in units.get(unit_key, []))
                print(f"    {tag}  (n={n_points}, fp dagilimi={dict(fps)})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
