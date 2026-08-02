"""Botun NASDAQ/ABD (US_GAAP) akisini Telegram OLMADAN test eder: ticker -> PNG yolu.

Gercek ag isteklerini (SEC EDGAR, Yahoo Finance fiyat, Gemini) kullanir --
demo_card.py'nin aksine sahte veri YOKTUR, bu yuzden calismasi ~10-30 saniye
surebilir ve internet baglantisi gerektirir (GEMINI_API_KEY yoksa commentary
katmani otomatik LLM'siz yedek moda duser, yine de calisir).

Kullanim:
    python scripts/demo_pipeline_us.py AAPL
    python scripts/demo_pipeline_us.py NVDA
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from src.bot import pipeline
from src.fetchers import sec_edgar

config.setup_logging()


def main() -> int:
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"

    print(f"'{ticker}' (NASDAQ) için boru hattı çalıştırılıyor...")
    try:
        sonuc = pipeline.run_pipeline(ticker, market="NASDAQ")
    except pipeline.TickerNotFoundError:
        print(f"❌ {ticker} diye bir sembol bulamadım (SEC EDGAR). Kodu kontrol eder misin?")
        return 1
    except pipeline.DataSourceUnavailableError as exc:
        print(f"Veri kaynağına ulaşılamadı: {exc}")
        return 1
    except sec_edgar.SecEdgarError as exc:
        print(f"SEC EDGAR hatası: {exc}")
        return 1

    fiscal_year, fiscal_period = sonuc.analysis.latest_period
    print(f"Şirket   : {sonuc.company_name} ({sonuc.ticker})")
    print(f"Mali Dönem: FY{fiscal_year} Ç{fiscal_period // 3}")
    print(f"Para Birimi: {sonuc.analysis.currency}")
    print(f"Skor     : {sonuc.score.total_score} / 10 ({sonuc.score.badge}, kaynak: {sonuc.commentary.source})")
    print(f"PNG yolu : {sonuc.png_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
