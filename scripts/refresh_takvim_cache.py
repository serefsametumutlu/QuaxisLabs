"""Faz 13 teslim kriteri: "Yaklaşan Bilanço Tarihleri" DB önbelleğini
(earnings_calendar tablosu) canlı verilerle doldurur/günceller.

Bu script GÜNDE 1-2 KEZ bir zamanlayıcıyla (Windows Görev Zamanlayıcı /
cron) çalıştırılmak üzere tasarlandı -- Telegram botu (/takvim,
menu:takvim:*) BU işlemi KENDİSİ TETİKLEMEZ (bkz.
src/bot/pipeline.py::refresh_earnings_calendar docstring'i: BIST100
yaklaşımı ticker başına 1-4 KAP isteği gerektirdiği için birkaç dakika
sürer, bu bir Telegram etkileşimini BLOKE ETMEMELİDİR).

⚠️ BIST taraması KÜÇÜK PARÇALAR (varsayılan 20 şirket) halinde, parçalar
arasında bekleyerek (varsayılan 15 sn) yapılır -- CANLI keşfedildi: 100
şirketi tek seferde taramak KAP'ın bağlantılarımızı geçici olarak
düşürmesine sebep oldu (bkz. PROJE_HAFIZASI/06_BILINEN_SORUNLAR.md §B16).
Bu yüzden --top 100 ile tam bir tarama ~25-30 dakika sürebilir.

Kullanım:
    python scripts/refresh_takvim_cache.py bist                # ilk 100 BIST hissesi
    python scripts/refresh_takvim_cache.py bist --top 30       # ilk 30
    python scripts/refresh_takvim_cache.py bist --batch-size 10 --batch-pause 20  # daha da nazik
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
    parser.add_argument("--batch-size", type=int, default=20, help="BIST: bir seferde kaç şirket taransın (varsayılan 20)")
    parser.add_argument("--batch-pause", type=float, default=15.0, help="BIST: parçalar arası bekleme saniyesi (varsayılan 15)")
    args = parser.parse_args()

    for market in args.markets:
        market_upper = market.upper()
        print(f"\n===== {market_upper} takvim önbelleği güncelleniyor (bu {'~25-30 dakika' if market_upper == 'BIST' else 'birkaç dakika'} sürebilir) =====")
        count = pipeline.refresh_earnings_calendar(
            market_upper, bist_limit=args.top, days_ahead=args.days,
            batch_size=args.batch_size, batch_pause_seconds=args.batch_pause,
        )
        print(f"{market_upper}: {count} kayıt upsert edildi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
