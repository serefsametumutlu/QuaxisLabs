"""Derin Kart (çok dönemli temel analiz) teslim kriteri demo: gerçek DB
verisiyle uçtan uca "Derin Kart" PNG'si üretir. Telegram'a BAĞIMLI DEĞİLDİR --
sadece repository (mevcut veri) + trends + deep_card zincirini uçtan uca
doğrular.

⚠️ Bu script YENİ bir ağ isteği ATMAZ -- ticker'ın DAHA ÖNCE en az bir kez
`scripts/demo_pipeline.py TICKER` (veya botta bir Bilanço Analizi) ile
sorgulanmış olması, DB'de finansal veri BULUNMASI gerekir (bkz.
src/analysis/trends.py modül notu).

Kullanım:
    python scripts/demo_derin_kart.py THYAO
    python scripts/demo_derin_kart.py THYAO --market BIST --company-name "Türk Hava Yolları A.O."
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402
from src.analysis import trends  # noqa: E402
from src.db import models, repository  # noqa: E402
from src.render import card, deep_card  # noqa: E402

config.setup_logging()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ticker", help="Hisse kodu (BIST: THYAO / NASDAQ: AAPL)")
    parser.add_argument("--market", choices=["BIST", "NASDAQ"], default="BIST")
    parser.add_argument("--company-name", default=None, help="Kart başlığında gösterilecek şirket adı (opsiyonel)")
    args = parser.parse_args()

    ticker = args.ticker.strip().upper()

    with repository.get_session() as session:
        company = session.get(models.Company, ticker)
        if company is None:
            print(f"UYARI: '{ticker}' için DB'de kayıt yok -- önce scripts/demo_pipeline.py {ticker} çalıştır.")
            return 1
        print(f"Şirket: {company.name or ticker} ({company.financial_group}, {company.market})")

        financials_by_period = repository.get_financials(session, ticker, n_periods=trends.MAX_TREND_PERIODS)
        score_history = repository.get_score_history(session, ticker)
        company_name = args.company_name or company.name or ticker

    print(f"{len(financials_by_period)} dönem finansal veri bulundu: {sorted(financials_by_period.keys())}")
    print(f"{len(score_history)} skor geçmişi kaydı bulundu.")

    trend = trends.compute_multi_period_trend(financials_by_period)
    if trend:
        print(f"\nTrend noktaları ({len(trend.points)} çeyrek):")
        for point in trend.points:
            print(
                f"  {point.period}: Hasılat={point.revenue} FAVÖK={point.ebitda} "
                f"NetKâr={point.net_income} Özkaynak={point.equity} "
                f"BrütMarj=%{point.gross_margin_pct} FAVÖKMarj=%{point.ebitda_margin_pct} "
                f"NetMarj=%{point.net_margin_pct} Kaldıraç={point.net_debt_to_ebitda} ROE=%{point.roe_pct}"
            )
        print(f"\nMevsimsellik grupları: {len(trend.seasonality)}")
        for group in trend.seasonality:
            print(f"  {group.quarter_number}. çeyrek -- yıllar: {group.years}, hasılat: {group.revenues}")
    else:
        print("\nTrend üretilemedi (yeterli veri yok).")

    context = deep_card.build_deep_card_context(trend, score_history, ticker, args.market, company_name=company_name)

    out_path = config.DATA_DIR / "cards" / f"{ticker}_derin.png"
    result_path = card.render_card(context, str(out_path), template_name="deep_card.html", screenshot_selector="#deep-card")
    print(f"\nPNG üretildi: {result_path}")
    print(f"Debug HTML  : {card._debug_html_path('deep_card.html')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
