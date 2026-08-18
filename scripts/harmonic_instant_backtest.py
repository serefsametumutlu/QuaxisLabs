"""'Anlik D' (V2.2, `pine/harmonic_formations_v1_indicator.pine`) mekanizmasinin
TAM BIST backtesti -- 5 formasyonun (ABCD + Gartley/Bat/Butterfly/Crab) HER
BIRI icin, `detect_prz()`'in urettigi (D'nin kendi pivot onayini BEKLEMEDEN,
fiyat istatistiksel D bolgesine CANLI girdigi an tetiklenen) sinyalleri
BIREBIR BUY/SELL islem sinyali olarak kullanir.

Kullanici talebi (2026-08-18): "bu kodu bu haliyle, yani XABC olusunca
orana gore belirlenen D noktasini buy/sell sinyali olarak baz aldigimiz
zaman nasil sonuclar ortaya cikiyor" -- bu script TAM OLARAK bunu yapar.

Mimari -- HICBIR hesaplama mantigi TEKRAR YAZILMADI:
  - Tespit: `src/analysis/harmonic_xabcd.py::detect_prz()` (ayni gun icinde
    2 kritik hata duzeltildi: XD yon formulu + "sadece 3 pivot yeterli"
    minimum-nokta hatasi, bkz. o modulun ust notlari).
  - Backtest: `abcd_backtest.backtest_symbol`/`compute_metrics`/
    `BacktestParams` DOGRUDAN REUSE edilir (PrzEvent'in Signal-uyumlu alan
    adlari sayesinde, `harmonic_xabcd_research.py` ile AYNI duck-typing).

quant-uzmani disiplinleri (`min_trades_show`/`min_trades_trustworthy`,
hicbir hucre sessizce gizlenmez) korunur.

Kullanim:
    python scripts/harmonic_instant_backtest.py --limit-symbols 30  # pilot
    python scripts/harmonic_instant_backtest.py                     # TAM BIST evreni
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
from src.analysis import harmonic_xabcd  # noqa: E402
from src.analysis.abcd_backtest import BacktestParams, backtest_symbol, compute_metrics  # noqa: E402
from src.analysis.abcd_scanner import get_bist_universe  # noqa: E402
from src.fetchers.abcd_data import fetch_ohlcv_abcd  # noqa: E402

config.setup_logging()

_DEFAULT_OUT_MD = BASE_DIR / "docs" / "spec" / "HARMONIC_INSTANT_D_BACKTEST.md"
_DEFAULT_OUT_CSV = config.DATA_DIR / "abcd_cache" / "harmonic_instant_summary.csv"
_BARS_PER_YEAR = {"60": 252 * 7, "120": 252 * 4, "240": 252 * 2, "1D": 252, "1W": 52}

_ALL_FORMATIONS: dict[str, harmonic_xabcd.Params] = {"ABCD": harmonic_xabcd.ABCD_PRESET, **harmonic_xabcd.HARMONIC_XABCD_PRESETS}


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


def run(symbols: list[str], tfs: list[str], years: float) -> dict[tuple[str, str, str], list]:
    """(formasyon, yon, tf) -> [Trade] doner."""
    bt_params = BacktestParams()
    cells: dict[tuple[str, str, str], list] = {}

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

            for formasyon_adi, params in _ALL_FORMATIONS.items():
                events = harmonic_xabcd.detect_prz(df, params)
                if not events:
                    continue
                long_events = [e for e in events if e.direction > 0]
                short_events = [e for e in events if e.direction < 0]
                for yon, evs in (("LONG", long_events), ("SHORT", short_events)):
                    if not evs:
                        continue
                    trades, curve = backtest_symbol(df, symbol, evs, bt_params)
                    if not trades:
                        continue
                    key = (formasyon_adi, yon, tf)
                    cell = cells.setdefault(key, {"trades": [], "drawdowns": []})
                    cell["trades"].extend(trades)
                    metrics = compute_metrics(trades, curve, bt_params.initial_equity, len(df))
                    cell["drawdowns"].append(metrics["max_drawdown_pct"])

    return cells


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Anlik-D (V2.2) mekanizmasi -- tam BIST backtest, 5 formasyon.")
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
    print(f"Grid: {len(symbols)} sembol x {len(tfs)} tf x 5 formasyon x 2 yon (~{args.years} yil gecmis).")

    cells = run(symbols, tfs, args.years)

    rows = []
    for (formasyon, yon, tf), cell in cells.items():
        trades = cell["trades"]
        n = len(trades)
        r_values = [t.r_multiple for t in trades if not math.isnan(t.r_multiple)]
        wins = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl <= 0]
        gross_profit = sum(t.pnl for t in wins)
        gross_loss = -sum(t.pnl for t in losses)
        rows.append(
            {
                "formasyon": formasyon,
                "yon": yon,
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
        "# Harmonic \"Anlik D\" (V2.2) Backtest -- 5 Formasyon\n",
        f"\nOlusturulma: {now}\n",
        "\n## Kapsam\n",
        f"\nSembol sayisi: {len(symbols)} · Zaman dilimleri: {', '.join(tfs)} · Backtest derinligi: ~{args.years} yil · "
        "Para birimi: TRY. Formasyonlar: ABCD (klasik, X yok) + Gartley/Bat/Butterfly/Crab (X-noktali). HER BIRI "
        "`detect_prz()`nin (D pivot onayi BEKLEMEDEN, fiyat istatistiksel D bolgesine CANLI girdigi an) urettigi "
        "sinyalleri DOGRUDAN BUY/SELL islemi olarak kullanir -- `pine/harmonic_formations_v1_indicator.pine` V2.2 "
        "ile Pine-parity.\n",
        "\n## ⚠️ Bu sinyaller REPAINT EDEBILIR\n",
        "\nD, klasik `detect()`teki gibi kendi pivot onayini gecirmis bir nokta DEGIL -- sadece fiyatin istatistiksel "
        "hedefe ulastigi andir; formasyon sonradan tamamlanmayabilir. Asagidaki sonuclar bu OLDUGU gibi -- "
        "onaylanmis/onaylanmamis ayrimi YAPMADAN -- backtest edilmistir (kullanicinin acik talebi).\n",
        f"\n- `min_trades_show={args.min_trades_show}` altindaki hucreler ASLA gizlenmez.\n",
        "\n## Sonuclar (R-multiple bazli, PF'ye gore siralı)\n",
        "\n| Formasyon | Yon | TF | n_trades | Win Rate % | Profit Factor | Beklenti (R) | Ort. Max DD % | Guven |\n",
        "|---|---|---|---|---|---|---|---|---|\n",
    ]
    for _, row in df.iterrows():
        lines.append(
            f"| {row['formasyon']} | {row['yon']} | {row['tf']} | {int(row['n_trades'])} | {_fmt(row['win_rate'])} | "
            f"{_fmt(row['profit_factor'])} | {_fmt(row['expectancy_r'], '{:.3f}')} | {_fmt(row['avg_max_drawdown_pct'])} | "
            f"{row['guven_etiketi']} |\n"
        )
    if df.empty:
        lines.append("\n_Hicbir hucre uretilmedi._\n")

    lines.append("\n## Ham Veri\n")
    lines.append(f"\n`{out_csv}`\n")

    out_path = _DEFAULT_OUT_MD
    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"Rapor kaydedildi: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
