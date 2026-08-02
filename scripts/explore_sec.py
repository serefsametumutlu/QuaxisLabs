"""SEC EDGAR companyfacts uc noktasinin GERCEK yanit seklini kesfetmek icin script.

sec_edgar.py fetcher'ini varsayima dayali yazmamak icin once bu script
calistirilir, donen ham JSON incelenir, standart alan haritasi (STANDARD_ITEM_MAP_US_GAAP)
GERCEK yanita gore yazilir (bkz. CLAUDE.md Kural 3 -- emin olunmayan XBRL tag'i
"muhtemelen budur" diye haritaya eklenmez).

Kullanim ornekleri:
    python scripts/explore_sec.py AAPL
    python scripts/explore_sec.py NVDA
    python scripts/explore_sec.py JPM
    python scripts/explore_sec.py AAPL --tags us-gaap:Revenues us-gaap:GrossProfit

Cikti:
    - Konsola: CIK cozumu, aday US GAAP tag'lerinin VAR/YOK durumu, her tag icin
      son birkac veri noktasi (start/end/val/form/fp/fy/frame) VE start-end
      arasindaki gun farkina gore "ceyreklik mi kumulatif mi gorunuyor" tahmini.
    - Diske: data/exploration/<TICKER>_companyfacts_<zaman damgasi>.json (tam ham yanit)
      + data/exploration/<TICKER>_ozet_<zaman damgasi>.txt (insan-okunur ozet)

Hiz limiti (SEC: 10 istek/sn/IP, asilirsa ~10 dk IP blogu) icin istekler
arasinda config.HTTP_RATE_LIMIT_DELAY_SECONDS kadar nezaket beklemesi vardir.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date, datetime
from pathlib import Path

import httpx

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402  (sys.path ayarlandiktan sonra import edilmeli)

TICKERS_ENDPOINT = "https://www.sec.gov/files/company_tickers.json"
COMPANYFACTS_ENDPOINT = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik10}.json"

EXPLORATION_DIR = BASE_DIR / "data" / "exploration"

# CLAUDE.md kullanici e-postasi (serefsamet2021@gmail.com) -- SEC User-Agent
# ZORUNLU ve aciklayici olmali, aksi halde 403 doner (canli dogrulandi).
USER_AGENT = "QuaxisLabs Bilanco Radar serefsamet2021@gmail.com"

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
}

# Faz gorev tanimindaki aday tag'ler -- KESIFTE dogrulanacak, korulukorune
# fetcher'a tasınmayacak (bkz. modul docstring'i).
CANDIDATE_TAGS: dict[str, list[str]] = {
    "revenue": [
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
        "us-gaap:Revenues",
        "us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax",
        "us-gaap:InterestAndDividendIncomeOperating",  # banka adayi (JPM)
        "us-gaap:InterestIncomeExpenseNet",  # banka adayi (JPM)
    ],
    "gross_profit": ["us-gaap:GrossProfit"],
    "operating_profit": ["us-gaap:OperatingIncomeLoss"],
    "net_income": [
        "us-gaap:NetIncomeLoss",
        "us-gaap:ProfitLoss",
        "us-gaap:NetIncomeLossAvailableToCommonStockholdersBasic",
    ],
    "depreciation_amortization": [
        "us-gaap:DepreciationDepletionAndAmortization",
        "us-gaap:DepreciationAmortizationAndAccretionNet",
        "us-gaap:DepreciationAndAmortization",
        "us-gaap:Depreciation",
    ],
    "total_assets": ["us-gaap:Assets"],
    "current_assets": ["us-gaap:AssetsCurrent"],
    "equity": [
        "us-gaap:StockholdersEquity",
        "us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    "cash": [
        "us-gaap:CashAndCashEquivalentsAtCarryingValue",
        "us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    ],
    "short_term_debt": [
        "us-gaap:LongTermDebtCurrent",
        "us-gaap:DebtCurrent",
        "us-gaap:ShortTermBorrowings",
        "us-gaap:CommercialPaper",
    ],
    "long_term_debt": [
        "us-gaap:LongTermDebtNoncurrent",
        "us-gaap:LongTermDebt",
    ],
    "shares_outstanding": [
        "dei:EntityCommonStockSharesOutstanding",
        "us-gaap:CommonStockSharesOutstanding",
    ],
}


def normalize_ticker(raw: str) -> str:
    return raw.strip().upper()


def fetch_ticker_map() -> dict[str, dict]:
    """https://www.sec.gov/files/company_tickers.json -> {TICKER: {cik_str, title, ticker}}."""
    response = httpx.get(TICKERS_ENDPOINT, headers=HEADERS, timeout=config.HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()
    payload = response.json()
    # Yanit {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, "1": {...}, ...} seklinde.
    by_ticker: dict[str, dict] = {}
    for row in payload.values():
        ticker = str(row.get("ticker", "")).upper()
        if ticker:
            by_ticker[ticker] = row
    return by_ticker


def resolve_cik(ticker: str, ticker_map: dict[str, dict]) -> str | None:
    row = ticker_map.get(ticker)
    if row is None:
        return None
    return f"{int(row['cik_str']):010d}"


def fetch_companyfacts(cik10: str) -> dict:
    url = COMPANYFACTS_ENDPOINT.format(cik10=cik10)
    response = httpx.get(url, headers=HEADERS, timeout=config.HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def _facts_for_tag(payload: dict, tag: str) -> list[dict]:
    """'us-gaap:Assets' -> payload['facts']['us-gaap']['Assets']['units']['USD'] (veya sehpa/adet icin uygun birim)."""
    taxonomy, concept = tag.split(":", 1)
    node = payload.get("facts", {}).get(taxonomy, {}).get(concept)
    if node is None:
        return []
    units = node.get("units", {})
    # Cogu parasal kalem USD; pay adedi 'shares' biriminde.
    for unit_key in ("USD", "shares", "USD/shares"):
        if unit_key in units:
            return units[unit_key]
    # bilinmeyen birim -- ilk bulunani dondur.
    for values in units.values():
        return values
    return []


def _days_between(start: str | None, end: str | None) -> int | None:
    if not start or not end:
        return None
    try:
        d1 = date.fromisoformat(start)
        d2 = date.fromisoformat(end)
    except ValueError:
        return None
    return (d2 - d1).days


def _pattern_guess(days: int | None) -> str:
    if days is None:
        return "?"
    if days <= 100:
        return "CEYREKLIK-gorunumlu (~3 ay)"
    if 150 <= days <= 200:
        return "YTD-2C-gorunumlu (~6 ay)"
    if 250 <= days <= 290:
        return "YTD-3C-gorunumlu (~9 ay)"
    if 300 <= days <= 380:
        return "YTD-YILLIK-gorunumlu (~12 ay)"
    return f"belirsiz ({days} gun)"


def summarize_tag(field: str, tag: str, entries: list[dict], lines: list[str], max_rows: int = 10) -> None:
    if not entries:
        lines.append(f"    [{tag}] -> YOK (bu sirkette raporlanmamis)")
        return

    # form=10-Q VE form=10-K olanlari ayri goster; en yeniden eskiye sirala.
    entries_sorted = sorted(entries, key=lambda e: (e.get("end") or "", e.get("filed") or ""), reverse=True)
    lines.append(f"    [{tag}] -> VAR, {len(entries)} veri noktasi (ilk {max_rows} en yeniden eskiye):")
    for e in entries_sorted[:max_rows]:
        start = e.get("start")
        end = e.get("end")
        days = _days_between(start, end)
        pattern = _pattern_guess(days)
        lines.append(
            f"      start={start!s:<12} end={end!s:<12} val={e.get('val')!s:<18} "
            f"form={e.get('form')!s:<8} fp={e.get('fp')!s:<4} fy={e.get('fy')!s:<6} "
            f"frame={e.get('frame')!s:<12} gun={days!s:<5} tahmin={pattern}"
        )


def run_ticker(ticker: str, ticker_map: dict[str, dict], tag_filter: list[str] | None) -> int:
    lines: list[str] = []
    ticker = normalize_ticker(ticker)
    lines.append(f"===== {ticker} =====")

    cik10 = resolve_cik(ticker, ticker_map)
    if cik10 is None:
        lines.append(f"HATA: '{ticker}' company_tickers.json icinde bulunamadi.")
        print("\n".join(lines))
        return 1
    lines.append(f"CIK: {cik10}")

    try:
        payload = fetch_companyfacts(cik10)
    except httpx.HTTPStatusError as exc:
        lines.append(f"HATA: companyfacts istegi basarisiz: HTTP {exc.response.status_code}")
        print("\n".join(lines))
        return 1
    except httpx.RequestError as exc:
        lines.append(f"HATA: Ag hatasi: {exc}")
        print("\n".join(lines))
        return 1

    lines.append(f"entityName: {payload.get('entityName')}")
    lines.append(f"Toplam us-gaap kavram sayisi: {len(payload.get('facts', {}).get('us-gaap', {}))}")
    lines.append(f"Toplam dei kavram sayisi: {len(payload.get('facts', {}).get('dei', {}))}")

    EXPLORATION_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_path = EXPLORATION_DIR / f"{ticker}_companyfacts_{timestamp}.json"
    raw_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    lines.append(f"Ham yanit kaydedildi: {raw_path}")
    lines.append("")

    fields_to_check = CANDIDATE_TAGS
    if tag_filter:
        # --tags acikca verilmisse sadece o tag'leri dogrudan sorgula (field'a bakmaksizin).
        lines.append("--- Elle belirtilen tag'ler ---")
        for tag in tag_filter:
            entries = _facts_for_tag(payload, tag)
            summarize_tag("(elle)", tag, entries, lines)
        print("\n".join(lines))
        _save_summary(ticker, timestamp, lines)
        return 0

    for field, candidates in fields_to_check.items():
        lines.append(f"--- alan: {field} ---")
        for tag in candidates:
            entries = _facts_for_tag(payload, tag)
            summarize_tag(field, tag, entries, lines)
        lines.append("")

    print("\n".join(lines))
    _save_summary(ticker, timestamp, lines)
    return 0


def _save_summary(ticker: str, timestamp: str, lines: list[str]) -> Path:
    out_path = EXPLORATION_DIR / f"{ticker}_ozet_{timestamp}.txt"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("tickers", nargs="+", help="ABD hisse kodlari (orn. AAPL NVDA JPM)")
    parser.add_argument(
        "--tags", nargs="+", default=None,
        help="Sadece bu XBRL tag'lerini sorgula (orn. us-gaap:Revenues us-gaap:GrossProfit)",
    )
    return parser.parse_args(argv)


def main() -> int:
    config.setup_logging()
    args = parse_args(sys.argv[1:])

    print("Ticker haritasi (company_tickers.json) cekiliyor...")
    ticker_map = fetch_ticker_map()
    print(f"  {len(ticker_map)} ticker yuklendi.\n")

    exit_code = 0
    for i, ticker in enumerate(args.tickers):
        result = run_ticker(ticker, ticker_map, args.tags)
        exit_code = exit_code or result
        if i < len(args.tickers) - 1:
            time.sleep(config.HTTP_RATE_LIMIT_DELAY_SECONDS)
            print()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
