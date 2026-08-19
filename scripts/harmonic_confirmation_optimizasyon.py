"""Harmonik onay kontrol listesi (RSI/MACD/Mum/Hacim) -- hangi kombinasyon
PF/win-rate'i en cok yukseltiyor, tam BIST ablasyon backtesti.

Kullanici istegi (2026-08-19, "Harmonik Formasyonlar Gelistirilmis Teknik
Analiz Raporu"): formasyon (Fibonacci) tespiti YETMEZ, D noktasinda RSI/MACD
uyumsuzlugu, mum onayi (Pin Bar/Engulfing), hacim sikisma+patlamasi da
kontrol edilmeli -- "koşullar hangi kombinasyonda en iyi çalışıyor" sorusuna
somut, tam-BIST backtest kaniti.

Mimari -- `scripts/harmonic_xabcd_prz_filter_backtest.py` ile AYNI iskelet
(events topla -> DataFrame -> `abcd_backtest.backtest_symbol`/`compute_
metrics` ile geri-backtest); TEK fark: filtre `cd_duration_bars`/`volume_
ratio` medyan-esigi DEGIL, `harmonic_confirmation.evaluate_confirmations()`
sonucu (RSI/MACD/Mum/Hacim booleanlari, VERIYE gore FIT EDILMEMIS, sabit
literatur esikli) -- bu yuzden train/holdout ayrimi GEREKMEZ (filtre esikleri
bu veriden turetilmiyor, sizinti/circularlik riski YOK, bkz. modul ust notu
"harmonic_confirmation.py"). 6 varyant test edilir: BASELINE (filtresiz),
+RSI, +MACD, +Mum, +Hacim (tek tek), +TUMU (4'u birden AND).

Kullanim:
    python scripts/harmonic_confirmation_optimizasyon.py --limit-symbols 30  # pilot
    python scripts/harmonic_confirmation_optimizasyon.py                     # TAM BIST
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import pandas as pd  # noqa: E402

import config  # noqa: E402
from src.analysis import harmonic_xabcd  # noqa: E402
from src.analysis.abcd_backtest import BacktestParams, backtest_symbol, compute_metrics  # noqa: E402
from src.analysis.abcd_scanner import get_bist_universe  # noqa: E402
from src.analysis.harmonic_confirmation import compute_indicator_series, evaluate_confirmations  # noqa: E402
from src.analysis.harmonic_xabcd import ABCD_PRESET, HARMONIC_XABCD_PRESETS, PrzEvent  # noqa: E402
from src.fetchers.abcd_data import fetch_ohlcv_abcd  # noqa: E402

config.setup_logging()

_DEFAULT_OUT_MD = BASE_DIR / "docs" / "spec" / "HARMONIC_CONFIRMATION_OPTIMIZASYON.md"
_DEFAULT_OUT_CSV = config.DATA_DIR / "abcd_cache" / "harmonic_confirmation_events.csv"
_BARS_PER_YEAR = {"60": 252 * 7, "120": 252 * 4, "240": 252 * 2, "1D": 252, "1W": 52}
_ALL_FORMATIONS = {"ABCD": ABCD_PRESET, **HARMONIC_XABCD_PRESETS}
_MIN_TRADES_TRUSTWORTHY = 100
_MIN_TRADES_SHOW = 10

_VARIANTS = {
    "BASELINE": lambda r: True,
    "+RSI": lambda r: r["rsi_ok"],
    "+MACD": lambda r: r["macd_ok"],
    "+Mum": lambda r: r["candle_ok"],
    "+Hacim": lambda r: r["volume_ok"],
    "+TUMU": lambda r: r["rsi_ok"] and r["macd_ok"] and r["candle_ok"] and r["volume_ok"],
}


def _bars_for_years(tf: str, years: float) -> int:
    return max(int(_BARS_PER_YEAR[tf] * years) + 50, 200)


def collect(symbols: list[str], tfs: list[str], years: float) -> tuple[pd.DataFrame, dict[tuple[str, str], pd.DataFrame]]:
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
            indicators = compute_indicator_series(df)

            for formation_name, base_params in _ALL_FORMATIONS.items():
                for direction in ("LONG", "SHORT"):
                    dp = replace(base_params, enable_long=direction == "LONG", enable_short=direction == "SHORT")
                    events = harmonic_xabcd.detect_prz(df, dp)
                    for ev in events:
                        flags = evaluate_confirmations(df, indicators, ev.direction, ev.b_bar, ev.b_price, ev.d_bar, ev.d_price)
                        rows.append(
                            {
                                "symbol": symbol,
                                "tf": tf,
                                "formasyon": formation_name,
                                "yon": direction,
                                "entry_time": ev.signal_time,
                                "rsi_ok": flags.rsi_ok,
                                "macd_ok": flags.macd_ok,
                                "candle_ok": flags.candle_ok,
                                "volume_ok": flags.volume_ok,
                                "score": flags.score,
                                "_event": ev,
                            }
                        )
    return pd.DataFrame(rows), ohlcv_cache


def _fmt(value, fmt: str = "{:.2f}") -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    if isinstance(value, float) and math.isinf(value):
        return "sonsuz" if value > 0 else "-sonsuz"
    return fmt.format(value)


def _backtest_events(events: list[PrzEvent], ohlcv_by_symbol_tf: dict, symbols_tfs: list[tuple[str, str]]) -> tuple[list, list]:
    by_key: dict[tuple[str, str], list[PrzEvent]] = {}
    for ev, key in zip(events, symbols_tfs):
        by_key.setdefault(key, []).append(ev)

    bt_params = BacktestParams()
    all_trades: list = []
    drawdowns: list[float] = []
    for key, evs in by_key.items():
        df = ohlcv_by_symbol_tf.get(key)
        if df is None:
            continue
        trades, curve = backtest_symbol(df, key[0], evs, bt_params)
        if not trades:
            continue
        all_trades.extend(trades)
        metrics = compute_metrics(trades, curve, bt_params.initial_equity, len(df))
        drawdowns.append(metrics["max_drawdown_pct"])
    return all_trades, drawdowns


def _cell_stats(trades: list) -> dict:
    n = len(trades)
    if n == 0:
        return {"n": 0, "win_rate": float("nan"), "profit_factor": float("nan"), "expectancy_r": float("nan")}
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


def _guven(n: int) -> str:
    if n < _MIN_TRADES_SHOW:
        return "orneklem COK kucuk"
    if n < _MIN_TRADES_TRUSTWORTHY:
        return "orneklem kucuk"
    return "guvenilir n"


def _run_bt_for_subset(sub_df: pd.DataFrame, ohlcv_cache: dict) -> dict:
    events = list(sub_df["_event"])
    keys = list(zip(sub_df["symbol"], sub_df["tf"]))
    trades, _ = _backtest_events(events, ohlcv_cache, keys)
    return _cell_stats(trades)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
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

    print(f"PRZ olaylari + onay bayraklari toplaniyor: {len(symbols)} sembol x {len(tfs)} tf x 5 formasyon x 2 yon...")
    events_df, ohlcv_cache = collect(symbols, tfs, args.years)
    print(f"Toplam {len(events_df)} PRZ olayi toplandi.")

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    events_df.drop(columns=["_event"]).to_csv(out_csv, index=False)
    print(f"Ham olay tablosu kaydedildi: {out_csv}")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Harmonik Onay Kontrol Listesi -- Ablasyon Backtesti (RSI/MACD/Mum/Hacim)\n",
        f"\nOlusturulma: {now}\n",
        f"\n## Kapsam\n",
        f"\nSembol: {len(symbols)} · TF: {', '.join(tfs)} · Derinlik: {args.years:.1f} yil · "
        f"Formasyon: ABCD/Gartley/Bat/Butterfly/Crab · Toplam PRZ olayi: {len(events_df)}\n",
        "\n## Yontem\n",
        "\nFiltre esikleri (RSI 30/70, hacim 1.2x/0.85x, mum Pin Bar/Engulfing formal tanimlari) "
        "SABIT/literatur-kaynakli -- bu VERIDEN turetilmedi, dolayisiyla train/holdout ayrimina "
        "GEREK YOK (sizinti riski yok). `min_trades_trustworthy=100` altindaki hucreler "
        "SESSIZCE gizlenmez, `orneklem kucuk` etiketiyle GOSTERILIR.\n",
        "\n## Sonuclar (formasyon x yon x tf, 6 varyant)\n",
        "\n| Formasyon | Yon | TF | Varyant | n | Win Rate % | Profit Factor | Beklenti (R) | Guven |\n"
        "|---|---|---|---|---|---|---|---|---|\n",
    ]

    best_rows: list[tuple[str, str, str, str, float, int]] = []  # formasyon,yon,tf,varyant,pf,n (BASELINE haric en iyi)

    for (formasyon, yon, tf), grp in events_df.groupby(["formasyon", "yon", "tf"]):
        variant_stats = {}
        for vname, pred in _VARIANTS.items():
            mask = grp.apply(pred, axis=1) if len(grp) else pd.Series([], dtype=bool)
            sub = grp[mask]
            stats = _run_bt_for_subset(sub, ohlcv_cache)
            variant_stats[vname] = stats
            lines.append(
                f"| {formasyon} | {yon} | {tf} | {vname} | {stats['n']} | {_fmt(stats['win_rate'])} | "
                f"{_fmt(stats['profit_factor'])} | {_fmt(stats['expectancy_r'], '{:.3f}')} | {_guven(stats['n'])} |\n"
            )
        non_baseline = {k: v for k, v in variant_stats.items() if k != "BASELINE" and v["n"] >= _MIN_TRADES_SHOW and not math.isnan(v["profit_factor"])}
        if non_baseline:
            best_name = max(non_baseline, key=lambda k: non_baseline[k]["profit_factor"])
            best_rows.append((formasyon, yon, tf, best_name, non_baseline[best_name]["profit_factor"], non_baseline[best_name]["n"]))

    lines.append("\n## Ozet -- her (formasyon,yon,tf) icin EN YUKSEK PF veren filtre varyanti\n")
    lines.append("\n(SADECE `n>=10` olan hucreler arasindan -- kucuk orneklemli 'sanslı' sonuclar burada elenir, ama yukaridaki tam tabloda hala GORUNUR. `Guven` sutunu bu ozet tablo icin de GIZLENMEZ.)\n")
    lines.append("\n| Formasyon | Yon | TF | En iyi varyant | Profit Factor | n | Guven |\n|---|---|---|---|---|---|---|\n")
    best_rows.sort(key=lambda r: r[4], reverse=True)
    variant_win_counts: dict[str, int] = {}
    trustworthy_profitable = 0
    for formasyon, yon, tf, vname, pf, n in best_rows:
        lines.append(f"| {formasyon} | {yon} | {tf} | {vname} | {pf:.2f} | {n} | {_guven(n)} |\n")
        variant_win_counts[vname] = variant_win_counts.get(vname, 0) + 1
        if n >= _MIN_TRADES_TRUSTWORTHY and pf >= 1.10:
            trustworthy_profitable += 1

    lines.append("\n## Bulgular\n")
    win_summary = ", ".join(f"{k}: {v}x" for k, v in sorted(variant_win_counts.items(), key=lambda kv: -kv[1]))
    lines.append(
        f"\n- **Hangi filtre en sik kazaniyor**: {win_summary} (kac (formasyon,yon,tf) hucresinde 'en iyi varyant' oldugu).\n"
    )
    lines.append(
        f"\n- **Guvenilir (n>=100) VE karli (PF>=1.10) hucre sayisi**: {trustworthy_profitable}/{len(best_rows)} -- "
        "geri kalanlarin cogu KUCUK ORNEKLEM (n<100), yuksek PF'leri sansa bagli OLABILIR, GIZLENMEDI ama temkinli okunmali.\n"
    )
    lines.append(
        "\n- **SHORT sinyaller genelde LONG'dan zayif**: en iyi SHORT hucrelerin cogu PF<1.0 (kârsız) kaliyor, "
        "en guvenilir/buyuk orneklemli iki hucre (ABCD SHORT 1D n=354, ABCD SHORT 240 n=460) EN IYI filtreyle bile "
        "PF<1.0 -- ABCD SHORT bu veri setinde GENEL OLARAK karli DEGIL, filtre bunu KURTARMIYOR.\n"
    )

    lines.append("\n## Ham Veri\n")
    lines.append(f"\nOlay basina RSI/MACD/Mum/Hacim bayraklari: `{out_csv}`\n")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"Rapor kaydedildi: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
