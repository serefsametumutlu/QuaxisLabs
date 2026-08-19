"""10 YENI teknik strateji -- tam BIST backtest + ornek sinyal grafikleri.

Kullanici istegi (2026-08-19): "yeni 10 tane daha strateji uret, PF ve WR
orani yuksek olacak, n sayisi 50-100 uzeri yeterli, backtest yap, sinyallerin
geldigi mum icin birer ikiser ornek goster, WR/PF/n tablo halinde ver."

Mimari: her sembol icin 1D (+ gerekliyse 240) verisi TEK SEFER cekilir, TUM
10 detektor ayni veri uzerinde calisir (performans -- `harmonic_confirmation_
optimizasyon.py` ile AYNI ilke). `abcd_backtest.backtest_symbol`/
`compute_metrics` DOGRUDAN reuse edilir (her modul zaten duck-typing
uyumlu). Her strateji icin ILK 2 GECERLI sinyalin +-25 barlik penceresi
mplfinance ile PNG olarak kaydedilir (giris/SL/TP1/TP2 yatay cizgilerle).

Kullanim:
    python scripts/strateji_arastirma_backtest.py --limit-symbols 30  # pilot
    python scripts/strateji_arastirma_backtest.py                     # TAM BIST
"""

from __future__ import annotations

import argparse
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import mplfinance as mpf  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402
from src.analysis import (  # noqa: E402
    cpr_regime_router, double_rsi_mtf, extreme_close_fade, failed_breakout_reversal,
    halflife_mean_reversion, momentum_ladder, rsi_mw_pattern, vcp_breakout,
    vol_breakout_kestner, wavelet_trend_rider,
)
from src.analysis.abcd_backtest import BacktestParams, backtest_symbol, compute_metrics  # noqa: E402
from src.analysis.abcd_scanner import get_bist_universe  # noqa: E402
from src.fetchers.abcd_data import fetch_ohlcv_abcd  # noqa: E402

config.setup_logging()

_OUT_DIR = BASE_DIR / "docs" / "spec"
_CHART_DIR = BASE_DIR / "docs" / "spec" / "strateji_ornek_grafikler"
_DEFAULT_OUT_MD = _OUT_DIR / "YENI_10_STRATEJI_BACKTEST.md"
_DEFAULT_OUT_CSV = config.DATA_DIR / "abcd_cache" / "yeni_10_strateji_sinyaller.csv"
_N_BARS_1D = 1200
_N_BARS_240 = 1200
_MIN_TRADES_SHOW = 20
_MIN_TRADES_TRUSTWORTHY = 50  # kullanici karari (2026-08-19): "n 50-100 uzeri yeterli"
_MAX_CHART_EXAMPLES = 2
_CHART_WINDOW = 25  # sinyal barinin +-N bari

# (strateji_adi, tf_gerektirir) -- "1D" ya da "1D+240" (double_rsi/wavelet MTF ister)
_STRATEGIES = [
    "WAVELET_TREND_RIDER",
    "VCP_BREAKOUT",
    "VOL_BREAKOUT_KESTNER",
    "MOMENTUM_LADDER",
    "FAILED_BREAKOUT_REVERSAL",
    "EXTREME_CLOSE_FADE",
    "DOUBLE_RSI_MTF",
    "RSI_MW_PATTERN",
    "CPR_REGIME_ROUTER",
    "HALFLIFE_MEAN_REVERSION",
]


def _detect_all(symbol: str, df1d: pd.DataFrame, df240: pd.DataFrame | None) -> dict[str, list]:
    out: dict[str, list] = {}
    try:
        out["VCP_BREAKOUT"] = vcp_breakout.detect(df1d)
    except Exception:
        out["VCP_BREAKOUT"] = []
    try:
        out["VOL_BREAKOUT_KESTNER"] = vol_breakout_kestner.detect(df1d)
    except Exception:
        out["VOL_BREAKOUT_KESTNER"] = []
    try:
        out["MOMENTUM_LADDER"] = momentum_ladder.detect(df1d)
    except Exception:
        out["MOMENTUM_LADDER"] = []
    try:
        out["FAILED_BREAKOUT_REVERSAL"] = failed_breakout_reversal.detect(df1d)
    except Exception:
        out["FAILED_BREAKOUT_REVERSAL"] = []
    try:
        out["EXTREME_CLOSE_FADE"] = extreme_close_fade.detect(df1d)
    except Exception:
        out["EXTREME_CLOSE_FADE"] = []
    try:
        out["RSI_MW_PATTERN"] = rsi_mw_pattern.detect(df1d)
    except Exception:
        out["RSI_MW_PATTERN"] = []
    try:
        out["CPR_REGIME_ROUTER"] = cpr_regime_router.detect(df1d)
    except Exception:
        out["CPR_REGIME_ROUTER"] = []
    try:
        out["HALFLIFE_MEAN_REVERSION"] = halflife_mean_reversion.detect(df1d)
    except Exception:
        out["HALFLIFE_MEAN_REVERSION"] = []

    if df240 is not None and not df240.empty:
        try:
            out["WAVELET_TREND_RIDER"] = wavelet_trend_rider.detect(df240, df1d)
        except Exception:
            out["WAVELET_TREND_RIDER"] = []
        try:
            out["DOUBLE_RSI_MTF"] = double_rsi_mtf.detect(df240, df1d)
        except Exception:
            out["DOUBLE_RSI_MTF"] = []
    else:
        out["WAVELET_TREND_RIDER"] = []
        out["DOUBLE_RSI_MTF"] = []
    return out


def _save_chart(df: pd.DataFrame, signal, symbol: str, strategy: str, idx: int) -> str | None:
    bar = signal.signal_bar
    lo = max(0, bar - _CHART_WINDOW)
    hi = min(len(df), bar + _CHART_WINDOW)
    if hi - lo < 10:
        return None
    window = df.iloc[lo:hi].copy()
    window_idx = pd.DatetimeIndex(pd.to_datetime(window["time"]))
    plot_df = pd.DataFrame(
        {
            "Open": window["open"].to_numpy(dtype=float),
            "High": window["high"].to_numpy(dtype=float),
            "Low": window["low"].to_numpy(dtype=float),
            "Close": window["close"].to_numpy(dtype=float),
            "Volume": window["volume"].to_numpy(dtype=float),
        },
        index=window_idx,
    )
    direction = "LONG" if signal.direction > 0 else "SHORT"
    hlines = dict(
        hlines=[signal.entry_ref, signal.sl, signal.tp1, signal.tp2],
        colors=["yellow", "red", "cyan", "lime"],
        linestyle="--", linewidths=2.0,
    )
    _CHART_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"{strategy}_{symbol}_{idx}.png"
    out_path = _CHART_DIR / fname
    try:
        mpf.plot(
            plot_df, type="candle", style="nightclouds",
            title=f"{strategy} | {symbol} {direction} | {signal.signal_time}",
            hlines=hlines, volume=True, figsize=(8, 5), savefig=str(out_path),
        )
    except Exception:
        return None
    return f"strateji_ornek_grafikler/{fname}"


def _cell_stats(trades: list) -> dict:
    n = len(trades)
    if n == 0:
        return {"n": 0, "win_rate": float("nan"), "profit_factor": float("nan"), "expectancy_r": float("nan")}
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
    print(f"{total} sembol -- 10 strateji tek gecişte taranacak (1D + 240)...")

    bt_params = BacktestParams()
    trades_by_strategy: dict[str, list] = {s: [] for s in _STRATEGIES}
    n_signals_by_strategy: dict[str, int] = {s: 0 for s in _STRATEGIES}
    chart_examples: dict[str, list[str]] = {s: [] for s in _STRATEGIES}
    csv_rows: list[dict] = []

    for done, symbol in enumerate(symbols, start=1):
        if done % 50 == 0:
            print(f"  ... {done}/{total} sembol islendi")
        df1d = fetch_ohlcv_abcd(symbol, "1D", _N_BARS_1D)
        if df1d.empty or len(df1d) < 300:
            continue
        df240 = fetch_ohlcv_abcd(symbol, "240", _N_BARS_240)

        per_strategy = _detect_all(symbol, df1d, df240)
        for strategy, signals in per_strategy.items():
            if not signals:
                continue
            n_signals_by_strategy[strategy] += len(signals)
            df_for_bt = df240 if strategy in ("WAVELET_TREND_RIDER", "DOUBLE_RSI_MTF") else df1d
            trades, _curve = backtest_symbol(df_for_bt, symbol, signals, bt_params)
            trades_by_strategy[strategy].extend(trades)

            for sig in signals:
                csv_rows.append(
                    {
                        "strateji": strategy, "symbol": symbol, "signal_time": sig.signal_time,
                        "direction": sig.direction, "entry_ref": sig.entry_ref, "sl": sig.sl,
                        "tp1": sig.tp1, "tp2": sig.tp2,
                    }
                )

            if len(chart_examples[strategy]) < _MAX_CHART_EXAMPLES:
                mid_signals = signals[len(signals) // 3 : len(signals) // 3 + 1] or signals[:1]
                for sig in mid_signals:
                    if len(chart_examples[strategy]) >= _MAX_CHART_EXAMPLES:
                        break
                    rel_path = _save_chart(df_for_bt, sig, symbol, strategy, len(chart_examples[strategy]) + 1)
                    if rel_path:
                        chart_examples[strategy].append(rel_path)

    print("Backtest tamamlandi, rapor yaziliyor...")

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(csv_rows).to_csv(out_csv, index=False)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# 10 Yeni Strateji -- Tam BIST Backtest + Ornek Sinyaller\n",
        f"\nOlusturulma: {now}\n",
        f"\n## Kapsam\n",
        f"\nSembol: {total} · TF: 1D (+240 sadece Wavelet Trend Rider icin) · Derinlik: ~{_N_BARS_1D} bar\n",
        "\n## Ozet Tablo\n",
        "\n| Strateji | n_sinyal (ham) | n_islem (backtest) | Win Rate % | Profit Factor | Beklenti (R) | Guven |\n"
        "|---|---|---|---|---|---|---|\n",
    ]
    summary_rows = []
    for strategy in _STRATEGIES:
        stats = _cell_stats(trades_by_strategy[strategy])
        summary_rows.append((strategy, stats))
        lines.append(
            f"| {strategy} | {n_signals_by_strategy[strategy]} | {stats['n']} | {_fmt(stats['win_rate'])} | "
            f"{_fmt(stats['profit_factor'])} | {_fmt(stats['expectancy_r'], '{:.3f}')} | {_guven(stats['n'])} |\n"
        )

    lines.append("\n## Strateji Detaylari + Ornek Sinyaller\n")
    for strategy, stats in summary_rows:
        lines.append(f"\n### {strategy}\n")
        lines.append(
            f"\n- n_islem: {stats['n']} · Win Rate: {_fmt(stats['win_rate'])}% · "
            f"Profit Factor: {_fmt(stats['profit_factor'])} · Beklenti: {_fmt(stats['expectancy_r'], '{:.3f}')}R · "
            f"Guven: {_guven(stats['n'])}\n"
        )
        if chart_examples[strategy]:
            for rel_path in chart_examples[strategy]:
                lines.append(f"\n![{strategy} ornek]({rel_path})\n")
        else:
            lines.append("\n(Bu calistirmada ornek grafik icin yeterli sinyal bulunamadi.)\n")

    lines.append(f"\n## Ham Veri\n\nTum sinyaller: `{out_csv}`\n")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"Rapor: {out_path}")
    print(f"Grafikler: {_CHART_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
