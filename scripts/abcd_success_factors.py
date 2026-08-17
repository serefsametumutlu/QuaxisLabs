"""AB=CD basari faktoru analizi CLI (Faz 8) -- `abcd_backtest.collect_trades`
ile TAMAMLANMIS (D onaylanmis, backtest edilmis) islemleri toplar, her
benzersiz (symbol, tf) icin OHLCV'yi (`fetch_ohlcv_abcd` zaten parquet-
onbellekli) BIR KEZ ceker, `abcd_factor_analysis.run_factor_analysis` +
`format_report`'u calistirir, sonucu markdown dosyaya yazar.

Mimari kararlar: `docs/spec/spec_abcd_mimari_kararlar.md`,
`src/analysis/abcd_factor_analysis.py` modul-ust notu (ozellikle "Kapsam
siniri -- TEK para birimi").

**Bu script `scripts/abcd_research.py` ile AYNI ANDA calisabilir** -- ikisi
de sadece `fetch_ohlcv_abcd`in KENDI parquet onbellegini okur/yazar, ortak
bir yazilabilir durum PAYLASMAZLAR (onbellek dosyalari `{symbol}_{tf}.parquet`
anahtariyla es-zamanli okuma/ekleme guvenlidir, `abcd_data._cached_fetch`
zaten dedupe-on-time uygular).

Kullanim:
    python scripts/abcd_success_factors.py --symbols THYAO,ASELS,TUPRS,KCHOL,AKBNK --tfs 1D --currencies TRY --years 2
    python scripts/abcd_success_factors.py                                   # varsayilan: TUM BIST evreni, 240+1D, TRY+USD (BUYUK -- dikkat)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import pandas as pd  # noqa: E402

import config  # noqa: E402
from src.analysis.abcd_backtest import BacktestParams, collect_trades  # noqa: E402
from src.analysis.abcd_factor_analysis import format_report, run_factor_analysis  # noqa: E402
from src.analysis.abcd_pattern import Params  # noqa: E402
from src.analysis.abcd_scanner import get_bist_universe  # noqa: E402
from src.fetchers.abcd_data import fetch_ohlcv_abcd  # noqa: E402

config.setup_logging()

_DEFAULT_OUT = BASE_DIR / "docs" / "spec" / "ABCD_BASARI_FAKTORLERI.md"


def _parse_list(raw: str) -> list[str]:
    return [x.strip() for x in raw.split(",") if x.strip()]


def _build_ohlcv_cache(
    trades_df: pd.DataFrame, years: float
) -> dict[tuple[str, str], pd.DataFrame]:
    """`trades_df`deki her benzersiz (symbol, tf) ciftinin TAM fiyat serisini
    BIR KEZ ceker (`fetch_ohlcv_abcd` zaten parquet-onbellekli -- ayni
    (symbol, tf) `collect_trades` icinde zaten cekilmisti, burada tekrar
    cekmek onbellekten HIZLI okunur, ag cagrisi TEKRARLANMAZ).

    `run_factor_analysis`in "TEK para birimi" sinirlamasi geregi (bkz.
    `abcd_factor_analysis.py` modul-ust notu) bu fonksiyon `trades_df`nin
    TEK bir `currency`ye ait oldugunu varsayar -- cagiran (`main`) bunu
    currency basina AYRI cagirir."""
    from src.analysis.abcd_backtest import _bars_for_years  # ic yardimci, script-ici kullanim

    if trades_df.empty:
        return {}

    cache: dict[tuple[str, str], pd.DataFrame] = {}
    pairs = trades_df[["symbol", "tf"]].drop_duplicates().itertuples(index=False)
    for symbol, tf in pairs:
        n_bars = _bars_for_years(tf, years)
        cache[(symbol, tf)] = fetch_ohlcv_abcd(symbol, tf, n_bars)
    return cache


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "AB=CD tamamlanmis islemlerden kazanan/kaybeden ORTAK faktorlerini "
            "(hacim, RSI, MACD, mum yapisi, trend/ADX/Bollinger) arastirir -- "
            "iliskisel dil, FDR-duzeltmeli, holdout-dogrulamali."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--symbols", default=None, help="Virgullu ticker listesi (varsayilan: get_bist_universe() -- TUM BIST evreni, DB'den).")
    parser.add_argument("--tfs", default="240,1D", help="Virgullu zaman dilimi listesi (varsayilan: 240,1D).")
    parser.add_argument("--currencies", default="TRY", help="Virgullu para birimi listesi -- HER BIRI AYRI analiz edilir (varsayilan: TRY).")
    parser.add_argument("--years", type=float, default=2.0, help="Sembol basina gecmis yil sayisi (varsayilan: 2.0).")
    parser.add_argument("--out", default=str(_DEFAULT_OUT), help=f"Markdown rapor cikti yolu (varsayilan: {_DEFAULT_OUT}).")
    parser.add_argument("--limit-symbols", type=int, default=None, help="TEST/dogrulama amacli: sadece ilk N sembolle calistir.")
    args = parser.parse_args(argv)

    if args.symbols:
        symbols = _parse_list(args.symbols)
    else:
        print("Sembol listesi verilmedi -- get_bist_universe() ile TUM BIST evreni DB'den cekiliyor...")
        symbols = get_bist_universe()
        print(f"  {len(symbols)} sembol bulundu.")

    if args.limit_symbols is not None:
        symbols = symbols[: args.limit_symbols]
        print(f"--limit-symbols {args.limit_symbols}: ilk {len(symbols)} sembolle sinirlandi.")

    if not symbols:
        print("Sembol listesi bos -- islem yapilamaz.")
        return 1

    tfs = _parse_list(args.tfs)
    currencies = _parse_list(args.currencies)

    print(
        f"Grid: {len(symbols)} sembol x {len(tfs)} tf x {len(currencies)} para birimi "
        f"(~{args.years} yil gecmis, detector Params() varsayilan)."
    )

    report_sections: list[str] = []
    for currency in currencies:
        print(f"\n[{currency}] islemler toplaniyor (collect_trades)...")
        trades_df = collect_trades(
            symbols=symbols,
            tfs=tfs,
            params=Params(),
            backtest_params=BacktestParams(),
            denominators=(currency,),
            years=args.years,
        )
        print(f"  {len(trades_df)} tamamlanmis islem bulundu.")

        if trades_df.empty:
            report_sections.append(
                f"\n\n---\n\n# {currency}\n\n_Bu para biriminde hicbir tamamlanmis islem bulunamadi "
                "(veri cekilemedi ya da hic sinyal/islem yok)._\n"
            )
            continue

        print(f"[{currency}] OHLCV onbellegi olusturuluyor ({trades_df[['symbol', 'tf']].drop_duplicates().shape[0]} benzersiz (symbol, tf))...")
        ohlcv_cache = _build_ohlcv_cache(trades_df, args.years)

        print(f"[{currency}] faktor analizi calisiyor (kronolojik split, Mann-Whitney/ki-kare + FDR, lojistik regresyon)...")
        result = run_factor_analysis(trades_df, ohlcv_cache)

        n_total = result.get("n_total", 0)
        n_skipped = result.get("n_skipped", 0)
        print(f"  n_total={n_total}, n_skipped(ozellik hesaplanamadi)={n_skipped}")
        if result.get("error"):
            print(f"  UYARI: {result['error']}")

        section = format_report(result)
        report_sections.append(f"\n\n---\n\n# {currency}\n\n{section}")

    header = (
        "# AB=CD Basari Faktoru Analizi -- Tum Para Birimleri\n\n"
        f"Sembol sayisi: {len(symbols)} | Zaman dilimleri: {', '.join(tfs)} | "
        f"Para birimleri: {', '.join(currencies)} (HER BIRI AYRI analiz edildi -- bkz. "
        "`abcd_factor_analysis.py` 'Kapsam siniri' notu) | Gecmis derinligi: "
        f"~{args.years} yil\n"
    )
    full_report = header + "".join(report_sections)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(full_report, encoding="utf-8")
    print(f"\nRapor kaydedildi: {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
