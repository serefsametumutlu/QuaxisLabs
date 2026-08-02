"""Faz 13 teslim kriteri: "Yaklaşan Bilanço Tarihleri" DB önbelleğini
(earnings_calendar tablosu) canlı verilerle doldurur/günceller.

Bu script GÜNDE 1-2 KEZ bir zamanlayıcıyla (Windows Görev Zamanlayıcı /
cron) çalıştırılmak üzere tasarlandı -- Telegram botu (/takvim,
menu:takvim:*) BU işlemi KENDİSİ TETİKLEMEZ (bkz.
src/bot/pipeline.py::refresh_earnings_calendar docstring'i: BIST100
yaklaşımı ticker başına 1-4 KAP isteği gerektirdiği için birkaç dakika
sürer, bu bir Telegram etkileşimini BLOKE ETMEMELİDİR).

Kullanım:
    python scripts/refresh_takvim_cache.py bist                # ilk 100 BIST hissesi
    python scripts/refresh_takvim_cache.py bist --top 30       # ilk 30
    python scripts/refresh_takvim_cache.py nasdaq               # NASDAQ/NYSE takvimi
    python scripts/refresh_takvim_cache.py bist nasdaq          # ikisi birden
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402
from src.bot import pipeline  # noqa: E402

config.setup_logging()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markets", nargs="+", choices=["bist", "nasdaq"], help="Güncellenecek piyasa(lar)")
    parser.add_argument("--top", type=int, default=100, help="BIST: piyasa değerine göre ilk N hisse (varsayılan 100)")
    parser.add_argument("--days", type=int, default=45, help="Kaç günlük ufuk taransın (varsayılan 45)")
    args = parser.parse_args()

    for market in args.markets:
        market_upper = market.upper()
        print(f"\n===== {market_upper} takvim önbelleği güncelleniyor (bu birkaç dakika sürebilir) =====")
        count = pipeline.refresh_earnings_calendar(market_upper, bist_limit=args.top, days_ahead=args.days)
        print(f"{market_upper}: {count} kayıt upsert edildi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
