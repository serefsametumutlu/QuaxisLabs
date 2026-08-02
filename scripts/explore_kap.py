"""KAP (kap.org.tr) sirket arama + bildirim listesi uc noktalarini
kesfetmek/dogrulamak icin script.

KAP sitesi Next.js ile yeniden yazilmis; eski "memberDisclosureQuery" tarzi
uc nokta artik yok. Gercek uc noktalar, sitenin derlenmis JS bundle'lari
icindeki rota tablosu (`_next/static/chunks/...`) taranarak bulundu:

    POST /tr/api/search/combined   {"keyword": "<hisse kodu>"}
        -> [{"category":"companyOrFunds","results":[{... memberOrFundOid,
             searchType:"C"|"F", cmpOrFundCode:"thyao" ...}]}, ...]
        Hisse kodu -> KAP'in ic uye kimligi (mkkMemberOid) eslemesi icin
        kullanilir. searchType == "C" (company) olanlari, cmpOrFundCode
        virgulle ayrilmis liste (coklu pay sinifi olan sirketlerde, orn.
        "krdma,krdmb,krdmd") icinde arananlari filtrele.

    POST /tr/api/disclosure/members/byCriteria
        {"fromDate":"YYYY-MM-DD","toDate":"YYYY-MM-DD","mkkMemberOidList":[oid]}
        -> [{"publishDate":"DD.MM.YYYY HH:MM:SS","subject":"...",
             "summary":"...","disclosureClass":"ODA|FR|DKB|DG",
             "disclosureIndex": 1234567, "stockCodes":"THYAO", ...}, ...]
        ONEMLI: fromDate/toDate ISO formatinda (YYYY-MM-DD) OLMALI;
        DD.MM.YYYY formati veya bu alanlarin hic gonderilmemesi HTTP 500
        donduruyor (canli olarak dogrulandi).

    Bildirim detay sayfasi: https://www.kap.org.tr/tr/Bildirim/{disclosureIndex}

Bu script bu bulgulari canli olarak tekrar dogrulamak / farkli bir hisse
icin gozlemlemek istediginizde kullanilir.

Kullanim:
    python scripts/explore_kap.py TAVHL
    python scripts/explore_kap.py THYAO --days 30
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import httpx

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402

KAP_BASE = "https://www.kap.org.tr/tr"
SEARCH_ENDPOINT = f"{KAP_BASE}/api/search/combined"
DISCLOSURES_ENDPOINT = f"{KAP_BASE}/api/disclosure/members/byCriteria"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Referer": f"{KAP_BASE}/",
}

EXPLORATION_DIR = BASE_DIR / "data" / "exploration"


def search_company(client: httpx.Client, ticker: str) -> dict | None:
    normalized = ticker.strip().lower().removesuffix(".is")
    response = client.post(SEARCH_ENDPOINT, json={"keyword": normalized}, timeout=config.HTTP_TIMEOUT_SECONDS)
    print(f"  [POST search/combined] HTTP {response.status_code}")
    payload = response.json()

    companies = next((c["results"] for c in payload if c.get("category") == "companyOrFunds"), [])
    print(f"  companyOrFunds sonuc sayisi: {len(companies)}")
    for row in companies:
        print(f"    - {row['searchValue']} | code={row['cmpOrFundCode']} | type={row['searchType']} | oid={row['memberOrFundOid']}")

    for row in companies:
        if row.get("searchType") != "C":
            continue
        codes = (row.get("cmpOrFundCode") or "").split(",")
        if normalized in codes:
            return row
    return None


def fetch_disclosures(client: httpx.Client, member_oid: str, days: int) -> list[dict]:
    to_date = date.today()
    from_date = to_date - timedelta(days=days)
    body = {
        "fromDate": from_date.isoformat(),
        "toDate": to_date.isoformat(),
        "mkkMemberOidList": [member_oid],
    }
    response = client.post(DISCLOSURES_ENDPOINT, json=body, timeout=config.HTTP_TIMEOUT_SECONDS)
    print(f"  [POST disclosure/members/byCriteria] HTTP {response.status_code}")
    payload = response.json()
    if isinstance(payload, dict):
        print(f"  BEKLENMEYEN yanit (dict): {payload}")
        return []
    return payload


def run(ticker: str, days: int) -> int:
    EXPLORATION_DIR.mkdir(parents=True, exist_ok=True)
    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        print(f"--- '{ticker}' icin KAP uye kimligi araniyor ---")
        company = search_company(client, ticker)
        if company is None:
            print(f"\n'{ticker}' icin companyOrFunds sonuclarinda tam eslesme bulunamadi.")
            return 1

        print(f"\nEslesen sirket: {company['searchValue']} (oid={company['memberOrFundOid']})")

        print(f"\n--- son {days} gunun bildirimleri cekiliyor ---")
        rows = fetch_disclosures(client, company["memberOrFundOid"], days)
        print(f"  Toplam bildirim: {len(rows)}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = EXPLORATION_DIR / f"{ticker.upper()}_disclosures_{timestamp}.json"
        out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  Ham yanit kaydedildi: {out_path}")

        print("\n  Ilk 10 bildirim (tarih | disclosureClass | subject | summary):")
        for row in rows[:10]:
            print(
                f"    {row['publishDate']} | {row['disclosureClass']:5s} | "
                f"{row['subject']} | {row.get('summary')}"
            )

    return 0


def main() -> int:
    config.setup_logging()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ticker", help="BIST hisse kodu (orn. TAVHL)")
    parser.add_argument("--days", type=int, default=90, help="Kac gun geriye gidilecek (varsayilan: 90)")
    args = parser.parse_args(sys.argv[1:])
    return run(args.ticker, args.days)


if __name__ == "__main__":
    sys.exit(main())
