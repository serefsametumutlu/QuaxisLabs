"""Faz 15 teslim kriteri demo: gerçek fiyat geçmişiyle uçtan uca Teknik
Analiz kartı (PNG) üretir. Telegram/DB'ye bağımlı DEĞİLDİR -- sadece
price_history + technical + technical_card zincirini uçtan uca doğrular.

Kullanım:
    python scripts/demo_teknik.py THYAO
    python scripts/demo_teknik.py THYAO --market BIST --days 400
    python scripts/demo_teknik.py AAPL --market NASDAQ --company-name "Apple Inc."
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402
from src.ai import commentary  # noqa: E402
from src.analysis import technical  # noqa: E402
from src.fetchers import price_history  # noqa: E402
from src.render import card, technical_card  # noqa: E402

config.setup_logging()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ticker", help="Hisse kodu (BIST: THYAO / NASDAQ: AAPL)")
    parser.add_argument("--market", choices=["BIST", "NASDAQ"], default="BIST")
    parser.add_argument("--days", type=int, default=400, help="Kaç günlük fiyat geçmişi çekilecek (varsayılan 400)")
    parser.add_argument("--company-name", default=None, help="Kart başlığında gösterilecek şirket adı (opsiyonel)")
    args = parser.parse_args()

    ticker = args.ticker.strip().upper()

    print(f"{ticker} ({args.market}) için son {args.days} günlük fiyat geçmişi çekiliyor...")
    bars = price_history.fetch_ohlcv(ticker, args.market, days=args.days)
    print(f"{len(bars)} günlük bar çekildi.")
    if not bars:
        print("UYARI: hiç fiyat verisi bulunamadı -- kart 'yeterli veri yok' durumuyla üretilecek.")

    price_bars = [
        technical.PriceBar(trade_date=bar.trade_date, high=bar.high, low=bar.low, close=bar.close, volume=bar.volume)
        for bar in bars
    ]
    snapshot = technical.compute_snapshot(price_bars)

    if snapshot:
        print(f"\nSon kapanış ({snapshot.as_of_date}): {snapshot.price}")
        print(f"SMA20/50/200 : {snapshot.sma_20} / {snapshot.sma_50} / {snapshot.sma_200}")
        print(f"RSI(14)      : {snapshot.rsi_14}")
        print(f"MACD (çizgi/sinyal/hist): {snapshot.macd_line} / {snapshot.macd_signal} / {snapshot.macd_histogram}")
        print(f"Bollinger (üst/orta/alt): {snapshot.bb_upper} / {snapshot.bb_middle} / {snapshot.bb_lower}")
        print(f"ATR(14)      : {snapshot.atr_14}")
        print(f"ADX(14)      : {snapshot.adx_14}")
        print(f"SMA50/200 kesişimi: {snapshot.sma_cross_state} (yakın zamanda: {snapshot.sma_cross_recent})")
        print(f"52 hafta     : {snapshot.week52_low} - {snapshot.week52_high} (konum: %{snapshot.week52_position_pct})")
        print(f"Hacim oranı  : %{snapshot.volume_ratio_pct} (20g ort: {snapshot.avg_volume_20})")
    else:
        print("\nSnapshot üretilemedi (yeterli fiyat verisi yok).")

    yorum = None
    if snapshot:
        print("\nTeknik değerlendirme üretiliyor (Gemini varsa, yoksa şablon yedeği)...")
        commentary_inputs = technical_card.build_commentary_inputs(snapshot, ticker, args.market)
        yorum = commentary.generate_commentary_technical(commentary_inputs)
        print(f"[{yorum.source}] {yorum.headline}")
        print(yorum.summary)
        for p in yorum.positives:
            print(f"  + {p}")
        for n in yorum.negatives:
            print(f"  - {n}")

    context = technical_card.build_technical_context(
        snapshot, ticker, args.market, company_name=args.company_name, commentary=yorum
    )

    out_path = config.DATA_DIR / "cards" / f"{ticker}_teknik.png"
    result_path = card.render_card(
        context, str(out_path), template_name="technical_card.html", screenshot_selector="#technical-card"
    )
    print(f"\nPNG üretildi: {result_path}")
    print(f"Debug HTML  : {card._debug_html_path('technical_card.html')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
