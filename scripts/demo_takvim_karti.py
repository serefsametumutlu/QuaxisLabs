"""Faz 13 teslim kriteri demo: gerçek "Yaklaşan Bilanço Tarihleri" verisiyle
uçtan uca takvim kartı (PNG) + paylaşıma hazır düz metin üretir.

DB önbelleği boşsa/bayatsa (bkz. pipeline.is_earnings_calendar_fresh) ÖNCE
canlı bir refresh_earnings_calendar() koşumu yapar (demo'nun kendisi bunu
göze alabilir, ama Telegram bot ASLA yapmaz -- bkz.
scripts/refresh_takvim_cache.py ve pipeline.py modül notu).

Kullanım:
    python scripts/demo_takvim_karti.py bist
    python scripts/demo_takvim_karti.py bist --top 20 --zorla-yenile
    python scripts/demo_takvim_karti.py nasdaq
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402
from src.bot import pipeline  # noqa: E402
from src.render import calendar_card, card  # noqa: E402

config.setup_logging()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("market", choices=["bist", "nasdaq"])
    parser.add_argument("--top", type=int, default=30, help="BIST: piyasa değerine göre ilk N hisse (varsayılan 30, hızlı demo için)")
    parser.add_argument("--days", type=int, default=45, help="Refresh ufku (varsayılan 45)")
    parser.add_argument("--zorla-yenile", action="store_true", help="Önbellek taze olsa bile canlı refresh yap")
    args = parser.parse_args()

    market = args.market.upper()

    fresh = pipeline.is_earnings_calendar_fresh(market)
    if fresh and not args.zorla_yenile:
        print(f"{market} önbelleği zaten taze (<24 saat) -- canlı refresh ATLANIYOR, DB'den okunuyor.")
    else:
        print(f"{market} takvim önbelleği güncelleniyor (canlı istekler, birkaç dakika sürebilir)...")
        count = pipeline.refresh_earnings_calendar(market, bist_limit=args.top, days_ahead=args.days)
        print(f"{count} kayıt upsert edildi.")

    entries = pipeline.get_cached_earnings_calendar(market, days_ahead=30)
    print(f"\nGösterim penceresi (30 gün) içinde {len(entries)} ham kayıt bulundu (kesin+tahmini+son_tarih dahil).")

    context = calendar_card.build_calendar_context(entries, market)
    kesin_sayisi = sum(len(g["rows"]) for g in context["kesin_day_groups"])
    tahmini_sayisi = sum(len(g["rows"]) for g in context["tahmini_day_groups"])
    print(f"Kartta gösterilecek: {kesin_sayisi} kesin + {tahmini_sayisi} tahmini şirket")
    if context["kesin_truncated_count"]:
        print(f"⚠️  {context['kesin_truncated_count']} KESİN kayıt kart okunabilirliği için KISALTILDI.")
    if context["tahmini_truncated_count"]:
        print(f"⚠️  {context['tahmini_truncated_count']} TAHMİNİ kayıt kart okunabilirliği için KISALTILDI.")

    out_path = config.DATA_DIR / "cards" / f"takvim_{market}.png"
    result_path = card.render_card(
        context, str(out_path), template_name="calendar_card.html", screenshot_selector="#calendar-card"
    )
    print(f"\nPNG üretildi: {result_path}")
    print(f"Debug HTML  : {card._debug_html_path('calendar_card.html')}")

    print("\n----- Paylaşıma hazır metin -----\n")
    print(calendar_card.build_calendar_share_text(context))
    return 0


if __name__ == "__main__":
    sys.exit(main())
