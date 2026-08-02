"""Faz 2 teslim kriteri demo scripti.

fetch_financials() ile cekilen son 8 ceyregin hasilat / net kar / ozkaynak
degerlerini konsola duzgun formatli bir tablo olarak basar.

Kullanim:
    python scripts/demo_fetch.py THYAO
"""

from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402
from src.fetchers.isyatirim import (  # noqa: E402
    CompanyNotFoundError,
    FinancialDataNotAvailableError,
    IsYatirimError,
    UnsupportedFinancialGroupError,
    fetch_financials,
    quarterly_standardized_value,
    standardized_value,
)
from src.formatting import format_number_tr  # noqa: E402


def _period_label(period: tuple[int, int]) -> str:
    """ASCII-guvenli donem etiketi (konsol/terminal encoding sorunlarindan kacinmak icin)."""
    year, quarter_end_month = period
    return f"{year} Q{quarter_end_month // 3}"


def main() -> int:
    config.setup_logging()

    if len(sys.argv) != 2:
        print("Kullanim: python scripts/demo_fetch.py <HISSE_KODU>")
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
    except UnsupportedFinancialGroupError as exc:
        print(f"HATA: {exc}")
        return 1
    except IsYatirimError as exc:
        print(f"HATA: {exc}")
        return 1

    print(f"{ticker} | financialGroup={raw.financial_group} | {len(raw.periods)} donem cekildi")
    print()

    col_period, col_value = 10, 24
    header = (
        f"{'Donem':<{col_period}} | "
        f"{'Hasilat (ceyreklik)':>{col_value}} | "
        f"{'Net Kar (ceyreklik)':>{col_value}} | "
        f"{'Ozkaynak (donem sonu)':>{col_value}}"
    )
    print(header)
    print("-" * len(header))

    for period in raw.periods:
        revenue_q = quarterly_standardized_value(raw, "revenue", period)
        net_income_q = quarterly_standardized_value(raw, "net_income", period)
        equity = standardized_value(raw, "equity", period)

        print(
            f"{_period_label(period):<{col_period}} | "
            f"{format_number_tr(revenue_q):>{col_value}} | "
            f"{format_number_tr(net_income_q):>{col_value}} | "
            f"{format_number_tr(equity):>{col_value}}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
