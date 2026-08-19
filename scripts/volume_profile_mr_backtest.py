"""Hacim Profili Ortalamaya Donus (volume_profile_mr.py) -- tam BIST
backtesti + Hurst-filtreli/filtresiz karsilastirma.

Kullanici istegi (2026-08-19): "yeni strateji uret ve backtest yap" --
bu YENI stratejinin (MMR-esintili, `ULTIMATE_5_STRATEGIES.md §4`ten
uyarlandi) ilk gercek-veri dogrulamasi. `abcd_backtest.backtest_symbol`
DOGRUDAN reuse edilir (volume_profile_mr.Signal duck-typing uyumlu).

Kullanim:
    python scripts/volume_profile_mr_backtest.py --limit-symbols 30  # pilot
    python scripts/volume_profile_mr_backtest.py                     # TAM BIST
"""

from __future__ import annotations

import argparse
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402
from src.analysis import volume_profile_mr as vpmr  # noqa: E402
from src.analysis.abcd_backtest import BacktestParams, backtest_symbol, compute_metrics  # noqa: E402
from src.analysis.abcd_scanner import get_bist_universe  # noqa: E402
from src.fetchers.abcd_data import fetch_ohlcv_abcd  # noqa: E402

config.setup_logging()

_DEFAULT_OUT_MD = BASE_DIR / "docs" / "spec" / "VOLUME_PROFILE_MR_BACKTEST.md"
_BARS_PER_YEAR = {"240": 252 * 2, "1D": 252}
_MIN_TRADES_TRUSTWORTHY = 100
_MIN_TRADES_SHOW = 10


def _bars_for_years(tf: str, years: float) -> int:
    return max(int(_BARS_PER_YEAR[tf] * years) + 50, 200)


def _fmt(value, fmt: str = "{:.2f}") -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    if isinstance(value, float) and math.isinf(value):
        return "sonsuz" if value > 0 else "-sonsuz"
    return fmt.format(value)


def _guven(n: int) -> str:
    if n < _MIN_TRADES_SHOW:
        return "orneklem COK kucuk"
    if n < _MIN_TRADES_TRUSTWORTHY:
        return "orneklem kucuk"
    return "guvenilir n"


def _cell_stats(trades: list) -> dict:
    n = len(trades)
    if n == 0:
        return {"n": 0, "win_rate": float("nan"), "profit_factor": float("nan"), "expectancy_r": float("nan"), "max_dd": float("nan")}
    r_values = [t.r_multiple for t in trades if not math.isnan(t.r_multiple)]
    wins = [t for t in trades if t.pnl > 0]
    losses = [t for t in trades if t.pnl <= 0]
    gross_profit = sum(t.pnl for t in wins)
    gross_loss = -sum(t.pnl for t in losses)
    return {
        "n": n,
        "win_rate": len(wins) / n * 100.0,
        "profit_factor": (gross_profit / gross_loss) if gross_loss > 0 else float("inf") if gross_profit > 0 else float("nan"),
        "expectancy_r": (sum(r_values) / len(r_values)) if r_values else float("nan"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tfs", default="1D,240")
    parser.add_argument("--years", type=float, default=2.0)
    parser.add_argument("--limit-symbols", type=int, default=None)
    parser.add_argument("--out", default=str(_DEFAULT_OUT_MD))
    args = parser.parse_args(argv)

    print("get_bist_universe() ile TUM BIST evreni DB'den cekiliyor...")
    symbols = get_bist_universe()
    print(f"  {len(symbols)} sembol bulundu.")
    if args.limit_symbols is not None:
        symbols = symbols[: args.limit_symbols]
        print(f"--limit-symbols {args.limit_symbols}: ilk {len(symbols)} sembolle sinirlandi.")

    tfs = [t.strip() for t in args.tfs.split(",") if t.strip()]

    variants = {
        "BASELINE (Hurst filtresiz)": vpmr.Params(),
        "+Hurst(MR<0.45)": vpmr.Params(require_hurst_mr=True),
    }

    bt_params = BacktestParams()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Hacim Profili Ortalamaya Donus -- Tam BIST Backtest (YENI STRATEJI)\n",
        f"\nOlusturulma: {now}\n",
        "\n## Strateji\n",
        "\nD -20 barlik hacim profilinden POC/VAH/VAL turetilir. Fiyat VAL altina inip RSI(5)<30 "
        "aşırı satima duserse VE donus mumu (kapanis>acilis) olusursa LONG: TP1=POC, TP2=VAH, "
        "SL=VAL-1.0xATR. `ULTIMATE_5_STRATEGIES.md §4 Microstructure Mean-Reverter`den OHLCV-only "
        "uyarlama (gercek LOB verisi yok).\n",
        f"\n## Kapsam\n\nSembol: {len(symbols)} · TF: {', '.join(tfs)} · Derinlik: {args.years:.1f} yil\n",
        "\n## Sonuclar (TF bazinda, iki varyant)\n",
        "\n| TF | Varyant | n_trades | Win Rate % | Profit Factor | Beklenti (R) | Guven |\n|---|---|---|---|---|---|---|\n",
    ]

    for tf in tfs:
        n_bars = _bars_for_years(tf, args.years)
        for vname, params in variants.items():
            all_trades = []
            for symbol in symbols:
                df = fetch_ohlcv_abcd(symbol, tf, n_bars)
                if df.empty:
                    continue
                signals = vpmr.detect(df, params)
                if not signals:
                    continue
                trades, _curve = backtest_symbol(df, symbol, signals, bt_params)
                all_trades.extend(trades)
            stats = _cell_stats(all_trades)
            lines.append(
                f"| {tf} | {vname} | {stats['n']} | {_fmt(stats['win_rate'])} | "
                f"{_fmt(stats['profit_factor'])} | {_fmt(stats['expectancy_r'], '{:.3f}')} | {_guven(stats['n'])} |\n"
            )
            print(f"{tf} / {vname}: n={stats['n']} win_rate={_fmt(stats['win_rate'])} pf={_fmt(stats['profit_factor'])}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"Rapor kaydedildi: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
