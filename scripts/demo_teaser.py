"""Faz 14 teslim kriteri demo: gerçek pipeline sonucundan X/Twitter teaser
kartı (16:9, en fazla 7 sayı) üretir.

Kullanım:
    python scripts/demo_teaser.py TOASO
    python scripts/demo_teaser.py AAPL --market nasdaq
    python scripts/demo_teaser.py GARAN   (banka -- FAİZ GELİRİ/FAALİYET KÂRI metrikleri)
    python scripts/demo_teaser.py ANSGR   (sigorta -- PRİM ÜRETİMİ/TEKNİK DENGE metrikleri)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402
from src.analysis import calculator  # noqa: E402
from src.bot import pipeline  # noqa: E402
from src.render import card  # noqa: E402

config.setup_logging()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ticker")
    parser.add_argument("--market", choices=["bist", "nasdaq"], default="bist")
    args = parser.parse_args()

    market = args.market.upper()
    print(f"{args.ticker} ({market}) için pipeline çalıştırılıyor...")
    sonuc = pipeline.run_pipeline(args.ticker, market=market)

    if isinstance(sonuc.analysis, calculator.BankAnalysisResult):
        print("Sektör: banka")
        context = card.build_bank_teaser_context(
            sonuc.analysis, sonuc.score, sonuc.commentary, company_name=sonuc.company_name, price=sonuc.price
        )
    elif isinstance(sonuc.analysis, calculator.InsuranceAnalysisResult):
        print("Sektör: sigorta")
        context = card.build_insurance_teaser_context(
            sonuc.analysis, sonuc.score, sonuc.commentary, company_name=sonuc.company_name, price=sonuc.price
        )
    elif market == "NASDAQ":
        print("Sektör: sanayi/US_GAAP")
        context = card.build_teaser_context(
            sonuc.analysis, sonuc.score, sonuc.commentary, company_name=sonuc.company_name, price=sonuc.price,
            market="NASDAQ", currency_symbol="$", data_sources_note="SEC EDGAR (XBRL)",
        )
    else:
        print("Sektör: sanayi")
        context = card.build_teaser_context(
            sonuc.analysis, sonuc.score, sonuc.commentary, company_name=sonuc.company_name, price=sonuc.price
        )

    print(f"Dönem: {context['period_label']} · Skor: {context['score_total_display']}/10 ({context['score_badge']})")
    print(f"Metrikler: {[(m['label'], m['display']) for m in context['metrics']]}")
    print(f"Hüküm: {context['headline']}")

    out_path = config.DATA_DIR / "cards" / f"{args.ticker}_teaser.png"
    result_path = card.render_card(context, str(out_path), template_name="teaser_card.html", screenshot_selector="#teaser-card")
    print(f"\nPNG üretildi (16:9): {result_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
