"""Faz 12 teslim kriteri demo scripti: onumuzdeki 30 gunun "Yaklasan Bilanco
Tarihleri" takvimini (BIST ve/veya NASDAQ) konsola tablo olarak yazdirir.

Gercek ag isteklerini kullanir (KAP + TradingView tarama + NASDAQ takvim
API'si) -- calismasi BIST tarafinda ticker basina birkac saniye surebilir
(her ticker icin 1-4 KAP istegi + nezaket bekletmesi).

Kullanim:
    python scripts/demo_takvim.py bist                  # piyasa degerine gore ilk 15 BIST hissesi
    python scripts/demo_takvim.py bist --top 30          # ilk 30
    python scripts/demo_takvim.py bist THYAO ASELS TAVHL # sadece belirtilen hisseler
    python scripts/demo_takvim.py nasdaq                 # onumuzdeki 30 gun, TUM NASDAQ/NYSE
    python scripts/demo_takvim.py nasdaq --days 7         # onumuzdeki 7 gun
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402
from src.fetchers import earnings_calendar as ec  # noqa: E402
from src.fetchers import kap  # noqa: E402

config.setup_logging()

_GUVEN_ROZETI = {
    ec.CONFIDENCE_KESIN: "KESİN",
    ec.CONFIDENCE_TAHMINI: "tahmini",
    ec.CONFIDENCE_SON_TARIH: "son tarih",
}


def _print_table(entries: list[ec.EarningsDate]) -> None:
    if not entries:
        print("  (bu aralikta hicbir kayit bulunamadi)")
        return
    for e in entries:
        donem_etiketi = f"{e.period[1] // 3}Ç{e.period[0] % 100:02d}"
        rozet = _GUVEN_ROZETI.get(e.confidence, e.confidence)
        print(f"  {e.expected_date.isoformat()}  {e.ticker:<8} {donem_etiketi:<5} [{rozet:<9}] {e.company_name} ({e.source})")


def run_bist(tickers: list[str] | None, top: int) -> None:
    if tickers:
        ticker_pairs = []
        for t in tickers:
            try:
                company = kap.search_company(t)
                name = company.name
            except kap.KapError:
                name = t
            ticker_pairs.append((t.upper(), name))
    else:
        print(f"Piyasa degerine gore ilk {top} BIST hissesi araniyor (TradingView tarama, RESMİ BIST100 DEĞİL)...")
        symbols = ec.get_bist_top_market_cap_tickers(limit=top)
        ticker_pairs = [(s, s) for s in symbols]

    print(f"\n{len(ticker_pairs)} BIST sirketi taraniyor (bu birkac dakika surebilir)...\n")
    entries = ec.fetch_upcoming_bist(ticker_pairs, days_ahead=30)
    print(f"===== BIST -- onumuzdeki 30 gun ({len(entries)} kayit) =====")
    _print_table(entries)


def run_nasdaq(days: int) -> None:
    print(f"NASDAQ/NYSE takvimi araniyor (onumuzdeki {days} gun)...\n")
    entries = ec.fetch_upcoming_nasdaq(days_ahead=days)
    print(f"===== NASDAQ -- onumuzdeki {days} gun ({len(entries)} kayit) =====")
    _print_table(entries[:50])
    if len(entries) > 50:
        print(f"  ... ve {len(entries) - 50} kayit daha (ilk 50 gosterildi)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("market", choices=["bist", "nasdaq"])
    parser.add_argument("tickers", nargs="*", help="BIST icin belirli ticker'lar (verilmezse piyasa degeri sirasi kullanilir)")
    parser.add_argument("--top", type=int, default=15, help="BIST: piyasa degerine gore ilk N hisse (varsayilan 15)")
    parser.add_argument("--days", type=int, default=30, help="NASDAQ: onumuzdeki kac gun (varsayilan 30)")
    args = parser.parse_args()

    if args.market == "bist":
        run_bist(args.tickers or None, args.top)
    else:
        run_nasdaq(args.days)
    return 0


if __name__ == "__main__":
    sys.exit(main())
