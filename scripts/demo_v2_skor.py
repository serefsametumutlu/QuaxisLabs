"""Faz 3c/3.1: v2 çok-mercekli (Değer/Kalite/Büyüme/Güvenlik) skorlamanın
uçtan uca demo scripti -- `src.bot.pipeline.compute_multi_lens_score_for_ticker()`
BAĞIMSIZ giriş noktasını çalıştırır (v1'in `run_pipeline()`/kart üretimi
akışına HİÇ DOKUNMAZ, bkz. pipeline.py modül notu).

Gerçek ağ isteklerini kullanır (İş Yatırım/SEC EDGAR/KAP) -- internet
bağlantısı gerektirir, ~10-30 saniye sürebilir.

Kullanım:
    python scripts/demo_v2_skor.py                # varsayılan sepet (asağı bkz.)
    python scripts/demo_v2_skor.py THYAO BIST      # tek ticker/piyasa
    python scripts/demo_v2_skor.py AAPL NASDAQ

Varsayılan sepet (Faz 3.1 -- banka/sigorta/finansman v2 desteği eklendi):
THYAO (BIST sanayi), AAPL (NASDAQ abd_sanayi), AKBNK (BIST banka/UFRS),
ANSGR (BIST sigorta/UFRS_K), KTLEV (BIST finansman/XI_29K) -- bu 3 yeni
ticker DB'de `repository.get_financials()` ile 8 dönem TAM veri
içerdiği DOĞRULANARAK seçildi (`financial_group` sırasıyla UFRS/UFRS_K/
XI_29K, bkz. compute_multi_lens_score_for_ticker() docstring'i).
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from src.bot import pipeline
from src.analysis.lens_common import ScoreResult

config.setup_logging()


def _fmt_skor(score: Decimal | None) -> str:
    if score is None:
        return "N/A"
    return f"{score.quantize(Decimal('0.1'))}".replace(".", ",")


def _mercek_raporu(baslik: str, sonuc: ScoreResult | None) -> None:
    print(f"\n--- {baslik} ---")
    if sonuc is None:
        print("  Bu şirket türünde uygulanamaz veya hesaplanamadı.")
        return
    print(f"  Skor: {_fmt_skor(sonuc.total_score)} / 10  ({sonuc.badge})  -- veri kapsamı %{sonuc.data_coverage_pct.quantize(Decimal('0.1'))}")
    for bilesen in sonuc.components:
        skor_str = _fmt_skor(bilesen.score)
        agirlik_str = f"nominal %{bilesen.weight_nominal}, efektif %{bilesen.weight_effective.quantize(Decimal('0.1'))}"
        print(f"    * {bilesen.name}: {skor_str}  ({agirlik_str})")
        print(f"      -> {bilesen.reasoning_tr}")


def demo_ticker(ticker: str, market: str) -> int:
    print("=" * 78)
    print(f"'{ticker}' ({market}) için v2 çok-mercekli skorlama çalıştırılıyor...")
    try:
        sonuc = pipeline.compute_multi_lens_score_for_ticker(ticker, market=market)
    except pipeline.TickerNotFoundError:
        print(f"❌ {ticker} diye bir hisse bulamadım. Kodu kontrol eder misin?")
        return 1
    except pipeline.UnsupportedCompanyTypeError as exc:
        print(f"⚠️ {exc}")
        return 1
    except pipeline.DataSourceUnavailableError as exc:
        print(f"Veri kaynağına ulaşılamadı: {exc}")
        return 1

    print(f"Şirket   : {sonuc.company_name or sonuc.ticker} ({sonuc.ticker}, {sonuc.market})")
    print(f"Dönem    : {pipeline.quarter_label(sonuc.period)}")
    print(f"Fiyat    : {sonuc.price if sonuc.price is not None else 'N/A'}")

    profil = sonuc.bilesik.mercekler
    _mercek_raporu("DEĞER MERCEĞİ", profil.deger)
    _mercek_raporu("KALİTE MERCEĞİ", profil.kalite)
    _mercek_raporu("BÜYÜME MERCEĞİ", profil.buyume)
    _mercek_raporu("GÜVENLİK MERCEĞİ", profil.guvenlik)

    print("\n=== BİLEŞİK SKOR ===")
    parcalar = []
    for isim, mercek_sonuc in (("Değer", profil.deger), ("Kalite", profil.kalite), ("Büyüme", profil.buyume), ("Güvenlik", profil.guvenlik)):
        if mercek_sonuc is not None:
            parcalar.append(f"{isim}: {_fmt_skor(mercek_sonuc.total_score)}")
    print(" · ".join(parcalar) + f" -> Bileşik: {_fmt_skor(sonuc.bilesik.total_score)} {sonuc.bilesik.badge}")
    print(f"(bileşik skora dahil edilen mercekler: {', '.join(sonuc.bilesik.dahil_edilen_mercekler) or 'YOK'})")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args:
        hedefler = [
            ("THYAO", "BIST"),
            ("AAPL", "NASDAQ"),
            ("AKBNK", "BIST"),  # banka (UFRS)
            ("ANSGR", "BIST"),  # sigorta (UFRS_K)
            ("KTLEV", "BIST"),  # finansman (XI_29K)
        ]
    elif len(args) == 2:
        hedefler = [(args[0], args[1])]
    else:
        print("Kullanım: python scripts/demo_v2_skor.py [TICKER] [BIST|NASDAQ]")
        return 1

    exit_code = 0
    for ticker, market in hedefler:
        exit_code = demo_ticker(ticker, market) or exit_code
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
