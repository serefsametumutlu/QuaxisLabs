"""Faz 9 teslim kriteri demo scripti.

sec_edgar.fetch_financials() ile cekilen son 8 mali ceyregin hasilat / net
kar / toplam varlik / ozkaynak degerlerini konsola duzgun formatli bir
tablo olarak basar.

Kullanim:
    python scripts/demo_fetch_us.py AAPL
    python scripts/demo_fetch_us.py NVDA
    python scripts/demo_fetch_us.py JPM
"""

from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402
from src.fetchers.sec_edgar import (  # noqa: E402
    CompanyNotFoundError,
    FinancialDataNotAvailableError,
    SecEdgarError,
    fetch_financials,
    fetch_latest_price,
    quarterly_standardized_value_us_gaap,
    standardized_value_us_gaap,
    total_debt_us_gaap,
)
from src.formatting import format_number_tr  # noqa: E402


def _period_label(period: tuple[int, int]) -> str:
    """ASCII-guvenli mali donem etiketi. NOT: 'year' burada TAKVIM yili
    DEGIL, sirketin KENDI mali yilidir (bkz. sec_edgar.py modul notu)."""
    fiscal_year, fiscal_period = period
    return f"FY{fiscal_year} Q{fiscal_period // 3}"


def main() -> int:
    config.setup_logging()

    if len(sys.argv) != 2:
        print("Kullanim: python scripts/demo_fetch_us.py <TICKER>")
        return 1

    ticker = sys.argv[1]

    try:
        raw = fetch_financials(ticker)
    except CompanyNotFoundError as exc:
        print(f"HATA: {exc}")
        return 1
    except FinancialDataNotAvailableError as exc:
        print(f"UYARI: {exc}")
        return 1
    except SecEdgarError as exc:
        print(f"HATA: {exc}")
        return 1

    print(f"{ticker} | {raw.company_name} | CIK{raw.cik10} | {len(raw.periods)} mali ceyrek cekildi")
    price = fetch_latest_price(ticker)
    print(f"Son fiyat (Yahoo Finance, ikincil veri): {format_number_tr(price, decimals=2) if price else 'N/A'}")
    print()

    col_period, col_value = 12, 24
    header = (
        f"{'Mali Donem':<{col_period}} | "
        f"{'Hasilat (ceyreklik)':>{col_value}} | "
        f"{'Net Kar (ceyreklik)':>{col_value}} | "
        f"{'Toplam Varlik':>{col_value}} | "
        f"{'Ozkaynak':>{col_value}} | "
        f"{'Toplam Fin. Borc':>{col_value}}"
    )
    print(header)
    print("-" * len(header))

    for period in raw.periods:
        revenue_q = quarterly_standardized_value_us_gaap(raw, "revenue", period)
        net_income_q = quarterly_standardized_value_us_gaap(raw, "net_income", period)
        total_assets = standardized_value_us_gaap(raw, "total_assets", period)
        equity = standardized_value_us_gaap(raw, "equity", period)
        debt = total_debt_us_gaap(raw, period)

        print(
            f"{_period_label(period):<{col_period}} | "
            f"{format_number_tr(revenue_q):>{col_value}} | "
            f"{format_number_tr(net_income_q):>{col_value}} | "
            f"{format_number_tr(total_assets):>{col_value}} | "
            f"{format_number_tr(equity):>{col_value}} | "
            f"{format_number_tr(debt):>{col_value}}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
