"""Derin Kart (çok dönemli temel analiz) teslim kriteri demo: gerçek DB
verisiyle uçtan uca "Derin Kart" PNG'si üretir. Telegram'a BAĞIMLI DEĞİLDİR --
sadece repository (mevcut veri) + trends + deep_card zincirini uçtan uca
doğrular.

⚠️ Bu script VARSAYILAN olarak YENİ bir ağ isteği ATMAZ -- ticker'ın DAHA
ÖNCE en az bir kez `scripts/demo_pipeline.py TICKER` (veya botta bir Bilanço
Analizi) ile sorgulanmış olması, DB'de finansal veri BULUNMASI gerekir (bkz.
src/analysis/trends.py modül notu).

`--with-valuation` bayrağı (OPSİYONEL, HAFİF ama CANLI fiyat istekleri
gerektirir -- kendisi + her sektör peer'i için 1 kapanış fiyatı sorgusu):
"Değerleme Analizi" panelini de (sektöre göre ucuz/pahalı + 1/3 ay fiyat
momentumu + ima edilen hedef fiyat) hesaplayıp gösterir -- bkz.
src/analysis/valuation.py, src/bot/pipeline.py::compute_valuation_assessment_for_ticker
(AYNI orkestrasyon burada TEKRAR KULLANILIR, kopyalanmaz -- Derin Kart VE
tek çeyreklik Bilanço kartı da AYNI fonksiyonu paylaşır).

Kullanım:
    python scripts/demo_derin_kart.py THYAO
    python scripts/demo_derin_kart.py THYAO --market BIST --company-name "Türk Hava Yolları A.O."
    python scripts/demo_derin_kart.py THYAO --with-valuation
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402
from src.analysis import trends  # noqa: E402
from src.bot.pipeline import compute_valuation_assessment_for_ticker  # noqa: E402
from src.db import models, repository  # noqa: E402
from src.render import card, deep_card  # noqa: E402

config.setup_logging()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ticker", help="Hisse kodu (BIST: THYAO / NASDAQ: AAPL)")
    parser.add_argument("--market", choices=["BIST", "NASDAQ"], default="BIST")
    parser.add_argument("--company-name", default=None, help="Kart başlığında gösterilecek şirket adı (opsiyonel)")
    parser.add_argument(
        "--with-valuation", action="store_true",
        help="Değerleme Analizi panelini de hesapla (CANLI fiyat istekleri gerektirir, bkz. modül üst notu)",
    )
    args = parser.parse_args()

    ticker = args.ticker.strip().upper()
    financial_group = None
    peer_tickers: list[str] = []
    peer_financials_list: list[dict] = []

    with repository.get_session() as session:
        company = session.get(models.Company, ticker)
        if company is None:
            print(f"UYARI: '{ticker}' için DB'de kayıt yok -- önce scripts/demo_pipeline.py {ticker} çalıştır.")
            return 1
        print(f"Şirket: {company.name or ticker} ({company.financial_group}, {company.market})")
        financial_group = company.financial_group

        financials_by_period = repository.get_financials(session, ticker, n_periods=trends.SEASONALITY_FETCH_PERIODS)
        score_history = repository.get_score_history(session, ticker)
        company_name = args.company_name or company.name or ticker

        sector_average = {}
        sector_name = company.sector
        peer_count = 0
        if sector_name:
            peer_tickers = repository.get_sector_peer_tickers(
                session, sector_name, company.financial_group, exclude_ticker=ticker
            )
            peer_count = len(peer_tickers)
            print(f"Sektör: {sector_name} -- {peer_count} karşılaştırma şirketi: {peer_tickers}")
            peer_financials_list = [
                repository.get_financials(session, peer, n_periods=trends.SEASONALITY_FETCH_PERIODS) for peer in peer_tickers
            ]
            if peer_financials_list:
                sector_average = trends.compute_sector_average(peer_financials_list)
        else:
            print("Sektör bilgisi yok (scripts/refresh_sector_cache.py çalıştırılmamış olabilir) -- tek çizgi.")

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

    valuation_assessment = None
    if args.with_valuation:
        # Faz 16.6: peer_tickers BOŞ olsa bile çağrılır -- Graham/PEG
        # ölçütleri sektör peer'i GEREKTİRMEZ (bkz. valuation.py modül notu).
        valuation_assessment = compute_valuation_assessment_for_ticker(
            ticker, args.market, financial_group, financials_by_period, peer_tickers, peer_financials_list
        )
        if valuation_assessment and valuation_assessment.has_data:
            print(
                f"\nDeğerleme Analizi: verdict={valuation_assessment.verdict}, "
                f"F/K={valuation_assessment.own_pe} (sektör {valuation_assessment.sector_avg_pe}), "
                f"1 ay={valuation_assessment.price_change_1m_pct}, "
                f"sektöre göre ima edilen değer={valuation_assessment.implied_target_price} ({valuation_assessment.implied_target_basis}), "
                f"Graham={valuation_assessment.graham_fair_value_price} ({valuation_assessment.graham_verdict}), "
                f"PEG={valuation_assessment.peg_ratio} ({valuation_assessment.peg_verdict})"
            )
        else:
            print("\nDeğerleme Analizi için yeterli veri yok (fiyat/F-K-PD-DD bulunamadı).")

    context = deep_card.build_deep_card_context(
        trend, score_history, ticker, args.market, company_name=company_name,
        sector_average=sector_average, sector_name=sector_name, peer_count=peer_count,
        valuation_assessment=valuation_assessment,
    )

    out_path = config.DATA_DIR / "cards" / f"{ticker}_derin.png"
    result_path = card.render_card(context, str(out_path), template_name="deep_card.html", screenshot_selector="#deep-card")
    print(f"\nPNG üretildi: {result_path}")
    print(f"Debug HTML  : {card._debug_html_path('deep_card.html')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
