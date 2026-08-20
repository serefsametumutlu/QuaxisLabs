"""Wavelet Trend Rider -- "KOTU SINYAL" ELEME ablasyonu, tam BIST backtesti.

Kullanici geri bildirimi (2026-08-20, canli TradingView testi): "cok fazla
sinyal var, cogu hissenin tepesinde geliyor, SL'ye gidiyor -- bunlari
eleyecek bir formul bulmamiz gerekiyor". Bu script `wavelet_trend_rider_
variants.VARIANTS` sozlugundeki HER varyanti (baseline + 8 tekil filtre +
5 kombinasyon = 14 varyant) tam BIST evreninde, tf=240 (SADECE bu zaman
dilimi validasyonlu, bkz. docs/spec/YENI_10_STRATEJI_BACKTEST.md) + 1D MTF
onayla backtest eder.

Mimari: `abcd_backtest.backtest_symbol`/`compute_metrics` DOGRUDAN reuse
edilir (wavelet_trend_rider_variants.Signal zaten uyumlu, bkz. o modulun
ust notu) -- YENI bir backtest motoru YAZILMAZ.

Kullanim:
    python scripts/wavelet_trend_rider_optimizasyon.py --limit-symbols 30  # pilot
    python scripts/wavelet_trend_rider_optimizasyon.py                     # TAM BIST
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
from src.analysis import wavelet_trend_rider_variants as wtrv  # noqa: E402
from src.analysis.abcd_backtest import BacktestParams, backtest_symbol, compute_metrics  # noqa: E402
from src.analysis.abcd_scanner import get_bist_universe  # noqa: E402
from src.analysis.wavelet_trend_rider import Params  # noqa: E402
from src.fetchers.abcd_data import fetch_ohlcv_abcd  # noqa: E402

config.setup_logging()

_DEFAULT_OUT_MD = BASE_DIR / "docs" / "spec" / "WAVELET_TREND_RIDER_OPTIMIZASYON.md"
_DEFAULT_OUT_CSV = config.DATA_DIR / "abcd_cache" / "wavelet_trend_rider_optimizasyon_summary.csv"
_N_BARS_240 = 1200
_N_BARS_1D = 700
_MIN_TRADES_SHOW = 20
_MIN_TRADES_TRUSTWORTHY = 50


def _fmt(value, fmt: str = "{:.2f}") -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    if isinstance(value, float) and math.isinf(value):
        return "sonsuz" if value > 0 else "-sonsuz"
    return fmt.format(value)


def _guven(n: int) -> str:
    if n < _MIN_TRADES_SHOW:
        return "cok kucuk"
    if n < _MIN_TRADES_TRUSTWORTHY:
        return "kucuk"
    return "guvenilir (n>=50)"


def _cell_stats(trades: list) -> dict:
    n = len(trades)
    if n == 0:
        return {"n": 0, "win_rate": float("nan"), "profit_factor": float("nan"), "expectancy_r": float("nan"), "max_dd": float("nan")}
    wins = [t for t in trades if t.pnl > 0]
    losses = [t for t in trades if t.pnl <= 0]
    gross_profit = sum(t.pnl for t in wins)
    gross_loss = -sum(t.pnl for t in losses)
    r_values = [t.r_multiple for t in trades if not math.isnan(t.r_multiple)]
    return {
        "n": n,
        "win_rate": len(wins) / n * 100.0,
        "profit_factor": (gross_profit / gross_loss) if gross_loss > 0 else float("inf") if gross_profit > 0 else float("nan"),
        "expectancy_r": (sum(r_values) / len(r_values)) if r_values else float("nan"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit-symbols", type=int, default=None)
    parser.add_argument("--out", default=str(_DEFAULT_OUT_MD))
    parser.add_argument("--out-csv", default=str(_DEFAULT_OUT_CSV))
    args = parser.parse_args(argv)

    symbols = get_bist_universe()
    if args.limit_symbols is not None:
        symbols = symbols[: args.limit_symbols]
    total = len(symbols)
    print(f"{total} sembol -- {len(wtrv.VARIANTS)} varyant, tf=240+1D MTF...")

    bt_params = BacktestParams()
    wtr_params = Params()

    # Her sembol icin veri TEK SEFER cekilir, TUM varyantlar ayni veri
    # uzerinde calisir (performans -- diger ablasyon scriptleriyle AYNI ilke).
    trades_by_variant: dict[str, list] = {name: [] for name in wtrv.VARIANTS}
    raw_signal_rows: list[dict] = []

    for done, symbol in enumerate(symbols, start=1):
        if done % 50 == 0:
            print(f"  ... {done}/{total} sembol islendi")
        df240 = fetch_ohlcv_abcd(symbol, "240", _N_BARS_240)
        if df240.empty or len(df240) < 300:
            continue
        df1d = fetch_ohlcv_abcd(symbol, "1D", _N_BARS_1D)

        for variant_name, flags in wtrv.VARIANTS.items():
            try:
                signals = wtrv.detect_variant(df240, df1d, wtr_params, flags)
            except Exception:
                continue
            if not signals:
                continue
            trades, _curve = backtest_symbol(df240, symbol, signals, bt_params)
            trades_by_variant[variant_name].extend(trades)
            if variant_name == "BASELINE":
                for sig in signals:
                    raw_signal_rows.append(
                        {
                            "symbol": symbol,
                            "signal_time": sig.signal_time,
                            "entry_ref": sig.entry_ref,
                            "dist_from_denoised_atr": sig.dist_from_denoised_atr,
                            "is_new_high_20": sig.is_new_high_20,
                            "pullback_bars": sig.pullback_bars,
                            "adx": sig.adx,
                        }
                    )

    print("Backtest tamamlandi, rapor yaziliyor...")

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(raw_signal_rows).to_csv(out_csv, index=False)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Wavelet Trend Rider -- Kotu Sinyal Eleme Ablasyonu (Tam BIST)\n",
        f"\nOlusturulma: {now}\n",
        "\n## Kapsam\n",
        f"\nSembol: {total} · TF: 240 (4H) + 1D MTF onay · Derinlik: ~{_N_BARS_240} bar · "
        f"Varyant sayisi: {len(wtrv.VARIANTS)}\n",
        "\n## Motivasyon\n",
        "\nKullanici canli TradingView testinde 'sinyallerin cogu hissenin tepesinde geliyor, SL'ye gidiyor' "
        "geri bildirimi verdi. Bu ablasyon 6 hipotezi (asiri-uzama, pullback-sartsizligi, yeni-tepe, ADX tavani, "
        "yesil mum, hacim onayi) BASELINE'a TEK TEK ve kombinasyon halinde ekleyip PF/WR/n uzerindeki etkisini olcer.\n",
        "\n## Sonuclar\n",
        "\n| Varyant | n | Win Rate % | Profit Factor | Beklenti (R) | Guven |\n|---|---|---|---|---|---|\n",
    ]

    baseline_stats = _cell_stats(trades_by_variant.get("BASELINE", []))
    results_for_summary = []
    for variant_name in wtrv.VARIANTS:
        stats = _cell_stats(trades_by_variant[variant_name])
        results_for_summary.append((variant_name, stats))
        lines.append(
            f"| {variant_name} | {stats['n']} | {_fmt(stats['win_rate'])} | {_fmt(stats['profit_factor'])} | "
            f"{_fmt(stats['expectancy_r'], '{:.3f}')} | {_guven(stats['n'])} |\n"
        )

    lines.append("\n## Ozet -- BASELINE'a gore PF degisimi (n>=20 varyantlar arasindan)\n")
    lines.append(f"\nBASELINE: n={baseline_stats['n']}, PF={_fmt(baseline_stats['profit_factor'])}, Win%={_fmt(baseline_stats['win_rate'])}\n")
    lines.append("\n| Varyant | n | PF | BASELINE'a gore PF farki | Win Rate % |\n|---|---|---|---|---|\n")
    comparable = [
        (name, stats) for name, stats in results_for_summary
        if name != "BASELINE" and stats["n"] >= _MIN_TRADES_SHOW and not math.isnan(stats["profit_factor"])
    ]
    baseline_pf = baseline_stats["profit_factor"] if not math.isnan(baseline_stats["profit_factor"]) else 0.0
    comparable.sort(key=lambda x: x[1]["profit_factor"], reverse=True)
    for name, stats in comparable:
        pf_diff = stats["profit_factor"] - baseline_pf
        lines.append(f"| {name} | {stats['n']} | {stats['profit_factor']:.2f} | {pf_diff:+.2f} | {_fmt(stats['win_rate'])} |\n")

    lines.append("\n## Ham Veri (BASELINE sinyallerinin teshis alanlari)\n")
    lines.append(f"\n`{out_csv}`\n")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"Rapor: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
