"""Momentum Confluence -- KOŞUL ABLASYONU tam BIST backtesti.

Kullanici sorusu (2026-08-19): "en iyi kombinasyonlari bulmamiz gerekiyor
hangi zaman diliminde en iyisi kosullara ne ekleyip ne cikarsak daha saglam
win rate orani ve profit orani yuksek sinyaller yakalayabiliriz". Bu script
`src/analysis/momentum_confluence_variants.py::VARIANTS` sozlugundeki HER
varyanti (V1/V2 baseline + hacim/WT/yesil-mum/EMA aciklik ablasyonlari) tam
BIST evreninde, 1D ve 240 zaman dilimlerinde backtest eder.

Mimari: `abcd_backtest.backtest_symbol`/`compute_metrics`/`BacktestParams`
DOGRUDAN REUSE edilir (momentum_confluence.Signal zaten bu motorla uyumlu
alan sozlesmesine sahip, bkz. o modulun ust notu) -- YENI bir backtest
motoru YAZILMAZ.

Kullanim:
    python scripts/momentum_confluence_optimizasyon.py --limit-symbols 30  # pilot
    python scripts/momentum_confluence_optimizasyon.py                     # TAM BIST
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
from src.analysis import momentum_confluence as mc  # noqa: E402
from src.analysis import momentum_confluence_variants as mcv  # noqa: E402
from src.analysis.abcd_backtest import BacktestParams, backtest_symbol, compute_metrics  # noqa: E402
from src.analysis.abcd_scanner import get_bist_universe  # noqa: E402
from src.fetchers.abcd_data import fetch_ohlcv_abcd  # noqa: E402

config.setup_logging()

_DEFAULT_OUT_MD = BASE_DIR / "docs" / "spec" / "MOMENTUM_CONFLUENCE_OPTIMIZASYON.md"
_DEFAULT_OUT_CSV = config.DATA_DIR / "abcd_cache" / "momentum_confluence_optimizasyon_summary.csv"
_BARS_PER_YEAR = {"240": 252 * 2, "1D": 252}


def _bars_for_years(tf: str, years: float) -> int:
    return max(int(_BARS_PER_YEAR[tf] * years) + 50, 200)


def _fmt(value, fmt: str = "{:.2f}") -> str:
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


def run(symbols: list[str], tfs: list[str], years: float) -> dict[tuple[str, str], list]:
    """(varyant_adi, tf) -> Trade listesi doner."""
    bt_params = BacktestParams()
    mc_params = mc.Params()
    cells: dict[tuple[str, str], list] = {}

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

            for variant_name, flags in mcv.VARIANTS.items():
                signals = mcv.detect_variant(df, mc_params, flags)
                if not signals:
                    continue
                trades, curve = backtest_symbol(df, symbol, signals, bt_params)
                if not trades:
                    continue
                key = (variant_name, tf)
                cell = cells.setdefault(key, {"trades": [], "drawdowns": []})
                cell["trades"].extend(trades)
                metrics = compute_metrics(trades, curve, bt_params.initial_equity, len(df))
                cell["drawdowns"].append(metrics["max_drawdown_pct"])

    return cells


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Momentum Confluence kosul ablasyonu -- tam BIST backtest.")
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
    print(f"Grid: {len(symbols)} sembol x {len(tfs)} tf x {len(mcv.VARIANTS)} varyant (~{args.years} yil gecmis).")

    cells = run(symbols, tfs, args.years)

    rows = []
    for (variant, tf), cell in cells.items():
        trades = cell["trades"]
        n = len(trades)
        r_values = [t.r_multiple for t in trades if not math.isnan(t.r_multiple)]
        wins = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl <= 0]
        gross_profit = sum(t.pnl for t in wins)
        gross_loss = -sum(t.pnl for t in losses)
        rows.append(
            {
                "varyant": variant,
                "tf": tf,
                "n_trades": n,
                "win_rate": (len(wins) / n * 100.0) if n else float("nan"),
                "profit_factor": (gross_profit / gross_loss) if gross_loss > 0 else float("inf") if gross_profit > 0 else float("nan"),
                "expectancy_r": (sum(r_values) / len(r_values)) if r_values else float("nan"),
                "avg_max_drawdown_pct": sum(cell["drawdowns"]) / len(cell["drawdowns"]) if cell["drawdowns"] else float("nan"),
                "trustworthy": n >= args.min_trades_trustworthy,
                "guven_etiketi": _guven(n, args.min_trades_show, args.min_trades_trustworthy),
            }
        )

    df = pd.DataFrame(rows).sort_values(["trustworthy", "profit_factor"], ascending=[False, False]) if rows else pd.DataFrame()

    out_csv = _DEFAULT_OUT_CSV
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    print(f"Ham CSV kaydedildi: {out_csv}")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Momentum Confluence -- Koşul Ablasyonu Optimizasyon Backtesti\n",
        f"\nOluşturulma: {now}\n",
        "\n## Kapsam\n",
        f"\nSembol sayısı: {len(symbols)} · Zaman dilimleri: {', '.join(tfs)} · Backtest derinliği: ~{args.years} yıl · "
        f"Varyant sayısı: {len(mcv.VARIANTS)} (bkz. `src/analysis/momentum_confluence_variants.py::VARIANTS`). "
        "V1_BASELINE/V2_BASELINE, `MOMENTUM_CONFLUENCE_BACKTEST.md`deki orijinal V1/V2 sonuçlarıyla PARITY "
        "doğrulanmıştır (bkz. commit notu) -- aradaki KÜÇÜK sayısal farklar (varsa) SADECE bu koşunun farklı "
        "n_bars/tarih penceresinden kaynaklanabilir, mantık AYNIDIR.\n",
        f"\n- `min_trades_show={args.min_trades_show}` altındaki hücreler ASLA gizlenmez.\n",
        "\n## Sonuçlar (R-multiple bazlı, PF'ye göre sıralı)\n",
        "\n| Varyant | TF | n_trades | Win Rate % | Profit Factor | Beklenti (R) | Ort. Max DD % | Güven |\n",
        "|---|---|---|---|---|---|---|---|\n",
    ]
    for _, row in df.iterrows():
        lines.append(
            f"| {row['varyant']} | {row['tf']} | {int(row['n_trades'])} | {_fmt(row['win_rate'])} | "
            f"{_fmt(row['profit_factor'])} | {_fmt(row['expectancy_r'], '{:.3f}')} | {_fmt(row['avg_max_drawdown_pct'])} | "
            f"{row['guven_etiketi']} |\n"
        )
    if df.empty:
        lines.append("\n_Hiçbir hücre üretilmedi._\n")

    lines.append("\n## Ham Veri\n")
    lines.append(f"\n`{out_csv}`\n")

    out_path = _DEFAULT_OUT_MD
    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"Rapor kaydedildi: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
