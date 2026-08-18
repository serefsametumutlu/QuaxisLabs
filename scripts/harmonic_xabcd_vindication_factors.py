"""PRZ "dogrulanma" (vindication) tahmin-faktoru analizi.

Kullanicinin 2026-08-18 gecesi/gunduzu taleplerinin son adimi: tam-evren
arastirmasi (`docs/spec/ABCD_XABCD_V2_ARASTIRMASI.md`) PRZ erken uyarilarinin
sadece %7-25'inin sonradan gercek onayli formasyona donustugunu (vindicated)
gosterdi -- ama vindicated alt kumesi CONFIRMED'i bile sistematik olarak
geciyordu (orn. CRAB LONG 1D: PF 19.04 vs 3.16). Bu script asil soruyu
sorar: "PRZ bolgesine DEGDIGI ANDA, bu dokunusun sonradan vindicated mi
false-start mi olacagini ONCEDEN tahmin eden bir piyasa-durumu ozelligi var
mi?" (RSI/MACD/hacim/ADX/Bollinger -- Faz 8'deki AYNI 11 aday ozellik).

Hesaplama motoru `src/analysis/abcd_factor_analysis.py`nin (Faz 8, kazanan/
kaybeden analizi) AYNI istatistik cekirdegini (`run_factor_analysis` --
kronolojik split, Benjamini-Hochberg FDR, holdout dogrulama, VIF-budanmis
lojistik regresyon) YENIDEN KULLANIR -- `label_fn`/`methodology_note`
parametreleriyle (bu script icin eklendi, bkz. o fonksiyonun docstring'i)
"kazanan/kaybeden" yerine "vindicated/false-start" ikili sonucuna baglanir.
Hesaplama mantigi IKI YERDE YASAMAZ ilkesi (`abcd_backtest.py`/diger
scriptlerle AYNI disiplin).

`extract_features()` RSI/MACD/hacim/ADX/Bollinger'i `sig_signal_bar`de
(bu script icin: PRZ dokunma bari) hesaplar -- yani "dokunma anindaki
piyasa durumu" tam olarak sorulan soru budur.

Kullanim:
    python scripts/harmonic_xabcd_vindication_factors.py --limit-symbols 30  # pilot
    python scripts/harmonic_xabcd_vindication_factors.py                     # TAM BIST evreni
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import pandas as pd  # noqa: E402

import config  # noqa: E402
from dataclasses import replace  # noqa: E402
from src.analysis import harmonic_xabcd  # noqa: E402
from src.analysis.abcd_factor_analysis import HARMONIC_XABCD_METHODOLOGY_NOTE, format_report, run_factor_analysis  # noqa: E402
from src.analysis.abcd_scanner import get_bist_universe  # noqa: E402
from src.fetchers.abcd_data import fetch_ohlcv_abcd  # noqa: E402

config.setup_logging()

_DEFAULT_OUT_MD = BASE_DIR / "docs" / "spec" / "ABCD_XABCD_PRZ_DOGRULANMA_FAKTORLERI.md"
_DEFAULT_OUT_CSV = config.DATA_DIR / "abcd_cache" / "harmonic_xabcd_vindication_features.csv"
_BARS_PER_YEAR = {"60": 252 * 7, "120": 252 * 4, "240": 252 * 2, "1D": 252, "1W": 52}


def _bars_for_years(tf: str, years: float) -> int:
    return max(int(_BARS_PER_YEAR[tf] * years) + 50, 200)


def build_prz_trades_df(
    symbols: list[str], tfs: list[str], years: float
) -> tuple[pd.DataFrame, dict[tuple[str, str], pd.DataFrame]]:
    """Her (sembol x tf x formasyon x yon) icin PRZ olaylarini + vindicated
    etiketini toplar, `run_factor_analysis` bekledigi `sig_*` alan
    sozlesmesine cevirir. `(trades_df, ohlcv_cache)` doner."""
    rows: list[dict] = []
    ohlcv_cache: dict[tuple[str, str], pd.DataFrame] = {}

    total = len(symbols) * len(tfs)
    done = 0
    for tf in tfs:
        n_bars = _bars_for_years(tf, years)
        for symbol in symbols:
            done += 1
            if done % 50 == 0:
                print(f"  ... {done}/{total} (sembol x tf) islendi, su ana kadar {len(rows)} PRZ olayi")
            df = fetch_ohlcv_abcd(symbol, tf, n_bars)
            if df.empty:
                continue
            ohlcv_cache[(symbol, tf)] = df

            for formation_name, base_params in harmonic_xabcd.HARMONIC_XABCD_PRESETS.items():
                for direction in ("LONG", "SHORT"):
                    dp = replace(base_params, enable_long=direction == "LONG", enable_short=direction == "SHORT")
                    confirmed = harmonic_xabcd.detect(df, dp)
                    events = harmonic_xabcd.detect_prz(df, dp)
                    if not events:
                        continue
                    vindicated_flags = harmonic_xabcd.match_prz_to_confirmed(events, confirmed)

                    for ev, vindicated in zip(events, vindicated_flags):
                        rows.append(
                            {
                                "symbol": symbol,
                                "tf": tf,
                                "currency": "TRY",
                                "formasyon": formation_name,
                                "yon": direction,
                                "entry_time": ev.signal_time,
                                "vindicated": bool(vindicated),
                                "sig_signal_bar": ev.signal_bar,
                                "sig_c_bar": ev.c_bar,
                                "sig_d_bar": ev.d_bar,
                                "sig_c_price": ev.c_price,
                                "sig_d_price": ev.d_price,
                                "sig_cd_ratio": None,  # D henuz onayli degil -- bu ozellik PRZ'de anlamsiz
                            }
                        )

    return pd.DataFrame(rows), ohlcv_cache


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PRZ dogrulanma (vindication) tahmin-faktoru analizi.")
    parser.add_argument("--symbols", default=None)
    parser.add_argument("--tfs", default="1D,240")
    parser.add_argument("--years", type=float, default=2.0)
    parser.add_argument("--limit-symbols", type=int, default=None)
    parser.add_argument("--out", default=str(_DEFAULT_OUT_MD))
    parser.add_argument("--out-csv", default=str(_DEFAULT_OUT_CSV))
    args = parser.parse_args(argv)

    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    else:
        print("Sembol listesi verilmedi -- get_bist_universe() ile TUM BIST evreni DB'den cekiliyor...")
        symbols = get_bist_universe()
        print(f"  {len(symbols)} sembol bulundu.")

    if args.limit_symbols is not None:
        symbols = symbols[: args.limit_symbols]
        print(f"--limit-symbols {args.limit_symbols}: ilk {len(symbols)} sembolle sinirlandi.")

    tfs = [t.strip() for t in args.tfs.split(",") if t.strip()]

    print(f"PRZ olaylari toplaniyor: {len(symbols)} sembol x {len(tfs)} tf x 4 formasyon x 2 yon...")
    trades_df, ohlcv_cache = build_prz_trades_df(symbols, tfs, args.years)
    print(f"Toplam {len(trades_df)} PRZ olayi toplandi (vindicated={int(trades_df['vindicated'].sum()) if len(trades_df) else 0}).")

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    trades_df.to_csv(out_csv, index=False)
    print(f"Ham PRZ olay tablosu kaydedildi: {out_csv}")

    print("Faktor analizi calisiyor (kronolojik split + FDR + holdout + lojistik regresyon)...")
    result = run_factor_analysis(
        trades_df,
        ohlcv_cache,
        label_fn=lambda row: int(row["vindicated"]),
        methodology_note=HARMONIC_XABCD_METHODOLOGY_NOTE,
    )

    report = format_report(result)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"Rapor kaydedildi: {out_path}")
    print(f"Ozet: n_total={result['n_total']}, n_train={result.get('n_train')}, n_holdout={result.get('n_holdout')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
