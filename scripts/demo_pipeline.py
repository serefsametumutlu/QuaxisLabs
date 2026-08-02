"""Botun cekirdek akisini Telegram OLMADAN test eder: ticker -> PNG yolu.

Gercek ag isteklerini (Is Yatirim, KAP, Gemini) kullanir -- demo_card.py'nin
aksine burada sahte veri YOKTUR, bu yuzden calismasi ~20-40 saniye surebilir
ve internet baglantisi + .env icinde GEMINI_API_KEY gerektirir (yoksa
commentary katmani otomatik LLM'siz yedek moda duser, yine de calisir).

Kullanim: python scripts/demo_pipeline.py THYAO
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from src.bot import pipeline

config.setup_logging()


def main() -> int:
    ticker = sys.argv[1] if len(sys.argv) > 1 else "THYAO"

    print(f"'{ticker}' için boru hattı çalıştırılıyor...")
    try:
        sonuc = pipeline.run_pipeline(ticker)
    except pipeline.TickerNotFoundError:
        print(f"❌ {ticker} diye bir hisse bulamadım. Kodu kontrol eder misin?")
        return 1
    except pipeline.PeriodNotAvailableError as exc:
        if exc.available_label:
            print(f"⏳ {ticker}: {exc.requested_label} yok, son açıklanan: {exc.available_label}")
        else:
            print(f"⏳ {ticker}: {exc.requested_label} henüz açıklanmamış.")
        return 1
    except pipeline.UnsupportedCompanyTypeError as exc:
        print(f"⚠️ {exc}")
        return 1
    except pipeline.DataSourceUnavailableError as exc:
        print(f"Veri kaynağına ulaşılamadı: {exc}")
        return 1

    print(f"Şirket   : {sonuc.company_name} ({sonuc.ticker})")
    print(f"Dönem    : {pipeline.quarter_label(sonuc.analysis.latest_period)}")
    print(f"Skor     : {sonuc.score.total_score} / 10 (kaynak: {sonuc.commentary.source})")
    print(f"PNG yolu : {sonuc.png_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
