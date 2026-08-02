"""Kesif scripti: stockanalysis.com'un gomulu ceyreklik veri blobunu ceker
ve konsola/ozet dosyasina yazar -- SEC EDGAR'da eksik kalan Brut Kar/Esas
Faaliyet Kari icin YEDEK kaynak arastirmasi (bkz. 06_BILINEN_SORUNLAR.md §B17,
src/fetchers/stockanalysis.py modul notu).

Kullanim:
    python scripts/explore_stockanalysis.py ASTS
    python scripts/explore_stockanalysis.py ASTS GOOGL AAPL
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402  (sys.path ayarlandiktan sonra import edilmeli)
from src.fetchers import stockanalysis  # noqa: E402


def main() -> None:
    config.setup_logging()
    tickers = [t.upper() for t in sys.argv[1:]] or ["ASTS"]

    lines: list[str] = []
    for ticker in tickers:
        lines.append(f"===== {ticker} =====")
        try:
            snapshots = stockanalysis.fetch_quarterly_income(ticker)
        except stockanalysis.StockAnalysisError as exc:
            lines.append(f"  HATA: {exc}")
            continue

        if not snapshots:
            lines.append("  (hic donem bulunamadi)")
            continue

        for snap in snapshots:
            yil, ay = snap.period
            lines.append(
                f"  {yil}/{ay:02d}  revenue={snap.revenue}  gross_profit={snap.gross_profit}  "
                f"operating_profit={snap.operating_profit}  net_income={snap.net_income}"
            )

    ozet = "\n".join(lines)
    print(ozet)

    exploration_dir = BASE_DIR / "data" / "exploration"
    exploration_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = exploration_dir / f"STOCKANALYSIS_ozet_{ts}.txt"
    out_path.write_text(ozet, encoding="utf-8")
    print(f"\nKaydedildi: {out_path}")


if __name__ == "__main__":
    main()
