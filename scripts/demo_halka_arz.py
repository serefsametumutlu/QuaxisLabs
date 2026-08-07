"""Faz 20 devamı teslim kriteri demo: GERÇEK KAP verisiyle uçtan uca halka arz
izahname kartı (PNG) + paylaşıma hazır düz metin üretir.

İki mod:
    python scripts/demo_halka_arz.py --liste                # son 7 günde onaylı TÜM izahnameler
    python scripts/demo_halka_arz.py CITAS                   # tek bir ticker için detaylı kart

--liste artık TÜM KAP üyelerini TEK istekte tarayan `kap.fetch_all_disclosures()`
kullanır (~1-2 saniye, ESKİ ~22-aracı-kurum sıralı taramasının (~45-60 sn)
YERİNİ aldı, bkz. `src/fetchers/kap_ipo.py` modül üst notu, 2026-08-07).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402
from src.bot import ipo_pipeline  # noqa: E402
from src.render import card, ipo_card  # noqa: E402

config.setup_logging()


def _liste_modu() -> int:
    print("Son 7 günde SPK onaylı izahnameler taranıyor (canlı, ~1-2 saniye)...")
    disclosures = ipo_pipeline.list_available_ipos()
    if not disclosures:
        print("Şu an listelenecek bir izahname bulunamadı.")
        return 0

    print(f"\n{len(disclosures)} izahname bulundu:\n")
    for d in disclosures:
        company = ipo_card._derive_company_name(d.summary)
        tickers = ", ".join(d.target_tickers)
        print(f"  - {company} ({tickers}) · {d.underwriter_name} · {d.publish_date}")
    return 0


def _detay_modu(ticker: str) -> int:
    print(f"{ticker} için izahname aranıyor + PDF indirilip ayrıştırılıyor (canlı, biraz sürebilir)...")
    result = ipo_pipeline.compute_ipo_card_data(ticker)

    if result.assessment is None or result.disclosure is None or result.facts is None:
        print(f"⚠️  {ticker} için kart üretilemedi: {result.reason}")
        return 1

    context = ipo_card.build_ipo_card_context(
        result.disclosure, result.facts, result.assessment, supplementary=result.supplementary, price_report=result.price_report
    )

    print(f"\nŞirket             : {context['company_name']} (#{context['primary_ticker']})")
    print(f"Konsorsiyum Lideri : {context['underwriter_name']}")
    print(f"Halka Arz          : {context['offering_price_display']} · Büyüklük {context['offering_size_display']} · Toplam {context['total_lot_display'] or '-'} Lot")
    sermaye_kaynak = " (kaynak: halkarz.com)" if context["capital_split_is_fallback"] else ""
    print(f"Sermaye/Ortak      : {context['capital_increase_pct_display']} / {context['partner_sale_pct_display']}{sermaye_kaynak}")
    if context["has_quick_info"]:
        print(f"Talep Toplama      : {context['demand_period_display'] or '-'} ({context['demand_period_hours'] or '-'})")
        durum = "Uygun" if context["participation_compliant"] else "Uygun Değil" if context["participation_compliant"] is not None else "-"
        print(f"Katılım Endeksi    : {durum} (kaynak: halkarz.com, ikincil)")
    else:
        print("Talep Toplama/Katılım Endeksi: ikincil kaynaktan (halkarz.com) bulunamadı, kartta gösterilmiyor.")

    print("\nDağıtım Yapısı:")
    if context["allocation_rows"]:
        for row in context["allocation_rows"]:
            print(f"  - {row['label']}: {row['pct_display']} ({row['lot_display'] or '-'} Lot)")
    elif context["allocation_fallback_lines"]:
        print("  (izahnameden ayrıştırılamadı -- kaynak: halkarz.com)")
        for line in context["allocation_fallback_lines"]:
            print(f"  - {line}")

    if not context["is_estimated_distribution_empty"]:
        kaynak = " (kaynak: halkarz.com)" if context["estimated_distribution_is_fallback"] else ""
        print(f"\nTahmini Dağıtım (Yurt İçi Bireysel, örnek satırlar){kaynak}:")
        for row in context["estimated_distribution_rows"][:3]:
            print(f"  - {row['participants_display']} kişi -> kişi başı {row['lot_display']} Lot ({row['tl_display']})")

    if not context["is_operational_financial_empty"]:
        print("\nOperasyonel ve Finansal Veriler (Fiyat Tespit Raporu):")
        for row in context["operational_financial_rows"]:
            yoy = f" (YoY {row['yoy_display']})" if row["yoy_display"] else ""
            print(f"  - {row['label']}: {row['value_display']}{yoy}")

    out_path = config.DATA_DIR / "cards" / f"halkaarz_{ticker}.png"
    result_path = card.render_card(context, str(out_path), template_name="ipo_card.html", screenshot_selector="#ipo-card")
    print(f"\nPNG üretildi: {result_path}")
    print(f"Debug HTML  : {card._debug_html_path('ipo_card.html')}")

    print("\n----- Paylaşıma hazır inceleme metni -----\n")
    print(ipo_card.build_ipo_analysis_text(context))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ticker", nargs="?", help="Detaylı kart için hedef ticker (örn. KARCL)")
    parser.add_argument("--liste", action="store_true", help="Sadece son 60 günün izahname listesini göster")
    args = parser.parse_args()

    if args.liste or not args.ticker:
        return _liste_modu()
    return _detay_modu(args.ticker.strip().upper())


if __name__ == "__main__":
    sys.exit(main())
