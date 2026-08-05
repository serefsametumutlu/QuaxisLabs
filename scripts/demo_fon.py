"""Faz 17 (Türk yatırım fonları veri katmanı) teslim kriteri demo scripti.

TEFAS'tan (tefas.py) fon bilgisi + KAP'tan (kap_fund_portfolio.py) portföy
dağılım raporu arar, hepsini konsola döker.

Kullanım:
    python scripts/demo_fon.py AFA
    python scripts/demo_fon.py AFA --search
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402
from src.fetchers import kap_fund_portfolio, tefas  # noqa: E402


def main() -> int:
    config.setup_logging()

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("fon_kodu", help="TEFAS fon kodu (örn. AFA) veya --search ile arama kelimesi")
    parser.add_argument("--search", action="store_true", help="Fon kodu yerine ad/kod ile arama yap")
    args = parser.parse_args(sys.argv[1:])

    if args.search:
        print(f"=== TEFAS fon arama: {args.fon_kodu!r} ===")
        matches = tefas.search_fund(args.fon_kodu)
        if not matches:
            print("Eşleşme bulunamadı.")
            return 1
        for match in matches[:20]:
            print(f"  {match.code:8s} | {match.name} | kurucu={match.founder} | durum={match.status}")
        print(f"\nToplam {len(matches)} eşleşme (ilk 20 gösterildi).")
        return 0

    fon_kodu = args.fon_kodu.strip().upper()

    print(f"=== TEFAS Fon Bilgisi: {fon_kodu} ===")
    try:
        info = tefas.fetch_fund_info(fon_kodu)
    except tefas.TefasFundNotFoundError as exc:
        print(f"HATA: {exc}")
        return 1
    except tefas.TefasError as exc:
        print(f"HATA: {exc}")
        return 1

    print(f"Kod          : {info.code}")
    print(f"Ad           : {info.name}")
    print(f"Kurucu       : {info.founder or 'N/A'}")
    print(f"Tür/Kategori : {info.type or 'N/A'}")
    print(f"Son Fiyat    : {info.price if info.price is not None else 'N/A'}")
    print(f"Fiyat Tarihi : {info.price_date if info.price_date is not None else 'N/A (bkz. tefas.py modül notu)'}")
    print(f"Toplam Değer : {info.total_value if info.total_value is not None else 'N/A'}")
    print(f"Yatırımcı    : {info.investor_count if info.investor_count is not None else 'N/A'}")
    print(
        f"Varlık Dağ.  : {info.allocation if info.allocation else 'N/A (bkz. tefas.py modül notu)'}"
    )

    print(f"\n=== TEFAS Getiri Bilgisi: {fon_kodu} ===")
    returns = tefas.fetch_fund_returns(fon_kodu)
    print(f"1G={returns.d1} 1H={returns.w1} 1A={returns.m1} 3A={returns.m3} "
          f"6A={returns.m6} YB={returns.ytd} 1Y={returns.y1} 3Y={returns.y3} 5Y={returns.y5}")

    print(f"\n=== TEFAS Fiyat Geçmişi (3 ay): {fon_kodu} ===")
    history = tefas.fetch_price_history(fon_kodu, months=3)
    if history:
        for trade_date, price in history[:10]:
            print(f"  {trade_date} | {price}")
    else:
        print("  (boş -- bkz. tefas.py modül notu)")

    print(f"\n=== KAP Portföy Dağılım Raporu: {fon_kodu} ===")
    portfolio = kap_fund_portfolio.fetch_latest_portfolio(fon_kodu)
    if portfolio is None:
        print("  Bulunamadı (bkz. kap_fund_portfolio.py modül notu -- bilinen bir kapsam sınırı).")
    else:
        print(f"  Rapor tarihi : {portfolio.report_date}")
        print(f"  Yayın tarihi : {portfolio.publish_date}")
        print(f"  Bayatlık     : {portfolio.staleness_days} gün")
        for holding in portfolio.holdings:
            print(f"    {holding.instrument_type:10s} {holding.ticker or '-':8s} {holding.name:40s} %{holding.weight_pct}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
