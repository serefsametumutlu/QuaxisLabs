"""Momentum Confluence (V1: TRF+EMA Squeeze+Hacim, V2: V1 + WaveTrend + yesil
mum + siki EMA) icin tam-BIST backtest + kazanan/kaybeden faktor analizi.

Kullanici isteği (2026-08-18): "detayli backtest calismasi yap, duzgun ve
dogru TP/SL noktalari ekle, pozitif sinyalleri negatiflerden ayirabilecek
bir kosul var mi arastir, V2'nin V1'den daha az sinyal verdigini de goster."

Mimari -- HICBIR hesaplama mantigi TEKRAR YAZILMADI:
  - Tespit: `src/analysis/momentum_confluence.py::detect()` (Pine-parity,
    TP/SL bu modulde EKLENDI -- bkz. o modulun ust notu).
  - Backtest: `abcd_backtest.backtest_symbol`/`compute_metrics`/
    `BacktestParams` DOGRUDAN REUSE edilir (Signal alan-adi uyumlulugu,
    `harmonic_xabcd.py` ile AYNI duck-typing hilesi).
  - Faktor analizi: `abcd_factor_analysis.run_factor_analysis` (Faz 8'in
    kronolojik split/FDR/holdout/lojistik regresyon motoru) `momentum_
    confluence_factors.py`nin KENDI ozellik kumesiyle CAGRILIR
    (`feature_names`/`extract_features_fn` parametreleri).

quant-uzmani disiplinleri (`abcd_backtest.py`/diger scriptlerle AYNI):
`min_trades_show`/`min_trades_trustworthy` esikleri, hicbir hucre
sessizce gizlenmez.

Kullanim:
    python scripts/momentum_confluence_arastirma.py --limit-symbols 30  # pilot
    python scripts/momentum_confluence_arastirma.py                     # TAM BIST evreni
"""

from __future__ import annotations

import argparse
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import pandas as pd  # noqa: E402

import config  # noqa: E402
from src.analysis import momentum_confluence, momentum_confluence_factors  # noqa: E402
from src.analysis.abcd_backtest import BacktestParams, backtest_symbol, compute_metrics  # noqa: E402
from src.analysis.abcd_factor_analysis import format_report, run_factor_analysis  # noqa: E402
from src.analysis.abcd_scanner import get_bist_universe  # noqa: E402
from src.fetchers.abcd_data import fetch_ohlcv_abcd  # noqa: E402

config.setup_logging()

_DEFAULT_OUT_MD = BASE_DIR / "docs" / "spec" / "MOMENTUM_CONFLUENCE_BACKTEST.md"
_DEFAULT_OUT_FACTOR_MD_TMPL = str(BASE_DIR / "docs" / "spec" / "MOMENTUM_CONFLUENCE_FAKTOR_{variant}.md")
_DEFAULT_OUT_CSV = config.DATA_DIR / "abcd_cache" / "momentum_confluence_summary.csv"
_BARS_PER_YEAR = {"60": 252 * 7, "120": 252 * 4, "240": 252 * 2, "1D": 252, "1W": 52}
_SIG_DIAG_FIELDS = ("ema_spread_pct", "volume_ratio", "downward_streak_before_flip", "wt1_at_signal")


def _bars_for_years(tf: str, years: float) -> int:
    return max(int(_BARS_PER_YEAR[tf] * years) + 50, 200)


def _fmt(value: float, fmt: str = "{:.2f}") -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    if isinstance(value, float) and math.isinf(value):
        return "sonsuz" if value > 0 else "-sonsuz"
    return fmt.format(value)


def _guven(n: int, show: int, trust: int) -> str:
    if n < show:
        return f"GUVENSIZ (n={n})"
    if n < trust:
        return f"DUSUK GUVEN (n={n})"
    return "GUVENILIR"


def run(symbols: list[str], tfs: list[str], years: float, min_trades_show: int, min_trades_trustworthy: int):
    bt_params = BacktestParams()
    cells: dict[tuple[str, str], list] = {}  # (variant, tf) -> [Trade]
    drawdowns: dict[tuple[str, str], list[float]] = {}
    factor_rows: dict[str, list[dict]] = {"v1": [], "v2": []}
    ohlcv_cache: dict[tuple[str, str], pd.DataFrame] = {}

    total = len(symbols) * len(tfs)
    done = 0
    for tf in tfs:
        n_bars = _bars_for_years(tf, years)
        for symbol in symbols:
            done += 1
            if done % 50 == 0:
                print(f"  ... {done}/{total} (sembol x tf) islendi")
            df = fetch_ohlcv_abcd(symbol, tf, n_bars)
            if df.empty:
                continue
            ohlcv_cache[(symbol, tf)] = df

            for variant in ("v1", "v2"):
                signals = momentum_confluence.detect(df, momentum_confluence.Params(), variant=variant)
                if not signals:
                    continue
                trades, curve = backtest_symbol(df, symbol, signals, bt_params)
                sig_by_bar = {s.signal_bar: s for s in signals}

                key = (variant, tf)
                cells.setdefault(key, []).extend(trades)
                if trades:
                    metrics = compute_metrics(trades, curve, bt_params.initial_equity, len(df))
                    drawdowns.setdefault(key, []).append(metrics["max_drawdown_pct"])

                for trade in trades:
                    sig = sig_by_bar.get(trade.signal_bar)
                    row = {
                        "symbol": symbol,
                        "tf": tf,
                        "currency": "TRY",
                        "entry_time": trade.entry_time,
                        "pnl": trade.pnl,
                        "sig_signal_bar": trade.signal_bar,
                    }
                    for f in _SIG_DIAG_FIELDS:
                        row[f"sig_{f}"] = getattr(sig, f) if sig is not None else None
                    factor_rows[variant].append(row)

    return cells, drawdowns, factor_rows, ohlcv_cache


def _cell_row(variant: str, tf: str, trades: list, drawdowns: list[float], min_trades_show: int, min_trades_trustworthy: int) -> dict:
    n = len(trades)
    r_values = [t.r_multiple for t in trades if not math.isnan(t.r_multiple)]
    wins = [t for t in trades if t.pnl > 0]
    losses = [t for t in trades if t.pnl <= 0]
    gross_profit = sum(t.pnl for t in wins)
    gross_loss = -sum(t.pnl for t in losses)
    return {
        "variant": variant,
        "tf": tf,
        "n_trades": n,
        "win_rate": (len(wins) / n * 100.0) if n else float("nan"),
        "profit_factor": (gross_profit / gross_loss) if gross_loss > 0 else float("inf") if gross_profit > 0 else float("nan"),
        "expectancy_r": (sum(r_values) / len(r_values)) if r_values else float("nan"),
        "avg_max_drawdown_pct": sum(drawdowns) / len(drawdowns) if drawdowns else float("nan"),
        "trustworthy": n >= min_trades_trustworthy,
        "guven_etiketi": _guven(n, min_trades_show, min_trades_trustworthy),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Momentum Confluence V1/V2 tam-BIST backtest + faktor analizi.")
    parser.add_argument("--symbols", default=None)
    parser.add_argument("--tfs", default="1D,240")
    parser.add_argument("--years", type=float, default=2.0)
    parser.add_argument("--min-trades-show", type=int, default=30)
    parser.add_argument("--min-trades-trustworthy", type=int, default=100)
    parser.add_argument("--limit-symbols", type=int, default=None)
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
    print(f"Grid: {len(symbols)} sembol x {len(tfs)} tf x 2 varyant (V1/V2) (~{args.years} yil gecmis).")

    cells, drawdowns, factor_rows, ohlcv_cache = run(symbols, tfs, args.years, args.min_trades_show, args.min_trades_trustworthy)

    rows = [
        _cell_row(variant, tf, trades, drawdowns.get((variant, tf), []), args.min_trades_show, args.min_trades_trustworthy)
        for (variant, tf), trades in cells.items()
    ]
    cell_df = pd.DataFrame(rows).sort_values(["variant", "tf"]) if rows else pd.DataFrame()

    out_csv = _DEFAULT_OUT_CSV
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    cell_df.to_csv(out_csv, index=False)
    print(f"Ham CSV kaydedildi: {out_csv}")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Momentum Confluence V1/V2 -- Tam BIST Backtest\n",
        f"\nOlusturulma: {now}\n",
        "\n## Kapsam\n",
        f"\nSembol sayisi: {len(symbols)} · Zaman dilimleri: {', '.join(tfs)} · Backtest derinligi: ~{args.years} yil · "
        "Para birimi: TRY. V1 = TRF flip + EMA Squeeze + Hacim patlamasi. V2 = V1'in TUMU + WaveTrend kesisim onayi + "
        "yesil mum + daha siki EMA sirali/mesafe kosulu.\n",
        "\n## ⚠️ TP/SL -- kaynak Pine dosyalarinda YOKTU, bu arastirma icin EKLENDI\n",
        "\nSL = entry - atr_mult(1.5) * ATR14(Wilder) · risk = entry-SL · TP1 = entry + 1R · TP2 = entry + 2R "
        "(abcd_backtest.py'nin AYNI 1R/2R kismi-cikis motoru reuse edildi -- bkz. src/analysis/momentum_confluence.py "
        "modul ust notu).\n",
        f"\n- `min_trades_show={args.min_trades_show}` altindaki hucreler ASLA gizlenmez.\n",
        "\n## Backtest Sonuclari (R-multiple bazli)\n",
        "\n| Varyant | TF | n_trades | Win Rate % | Profit Factor | Beklenti (R) | Ort. Max DD % | Guven |\n",
        "|---|---|---|---|---|---|---|---|\n",
    ]
    for _, row in cell_df.iterrows():
        lines.append(
            f"| {row['variant'].upper()} | {row['tf']} | {int(row['n_trades'])} | {_fmt(row['win_rate'])} | "
            f"{_fmt(row['profit_factor'])} | {_fmt(row['expectancy_r'], '{:.3f}')} | {_fmt(row['avg_max_drawdown_pct'])} | "
            f"{row['guven_etiketi']} |\n"
        )
    if cell_df.empty:
        lines.append("\n_Hicbir hucre uretilmedi._\n")

    v1_n = int(cell_df[cell_df["variant"] == "v1"]["n_trades"].sum()) if not cell_df.empty else 0
    v2_n = int(cell_df[cell_df["variant"] == "v2"]["n_trades"].sum()) if not cell_df.empty else 0
    lines.append(f"\n## V1 vs V2 Sinyal Sikligi\n\n- V1 toplam işlem: {v1_n}\n- V2 toplam işlem: {v2_n}\n")
    if v1_n:
        lines.append(f"- V2/V1 orani: %{v2_n / v1_n * 100:.1f} (V2, V1'in kosullarinin USTUNE ek filtre ekliyor -- bu oranin <100 olmasi BEKLENIR)\n")

    lines.append("\n## Ham Veri\n")
    lines.append(f"\nHucre bazli ozet: `{out_csv}`\n")

    out_path = _DEFAULT_OUT_MD
    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"Backtest raporu kaydedildi: {out_path}")

    for variant in ("v1", "v2"):
        trades_df = pd.DataFrame(factor_rows[variant])
        print(f"\n[{variant.upper()}] Faktor analizi calisiyor (n={len(trades_df)})...")
        if trades_df.empty:
            print(f"  [{variant.upper()}] Hic islem yok, faktor analizi atlaniyor.")
            continue
        result = run_factor_analysis(
            trades_df,
            ohlcv_cache,
            feature_names=momentum_confluence_factors.ALL_FEATURES,
            categorical_features=momentum_confluence_factors.CATEGORICAL_FEATURES,
            extract_features_fn=momentum_confluence_factors.extract_features,
            methodology_note=(
                f"Momentum Confluence {variant.upper()} -- kazanan/kaybeden ILISKISEL analizi. "
                "'X ozelligi kazandirir' turu ifadeler YASAKTIR; sadece 'kazananlarda X ile birlikte "
                "gorulur, n=.., p=.., FDR q=.., holdout: dogrulandi/dogrulanmadi' turu ifadeler kullanilir."
            ),
        )
        report = format_report(result)
        out_factor_path = Path(_DEFAULT_OUT_FACTOR_MD_TMPL.format(variant=variant))
        out_factor_path.write_text(report, encoding="utf-8")
        print(f"  [{variant.upper()}] Faktor raporu kaydedildi: {out_factor_path} (n_total={result['n_total']})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
