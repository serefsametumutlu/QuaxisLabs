"""XABCD (Gartley/Bat/Butterfly/Crab, V2.1 -- X noktali, literatur-dogru CD/BC
+ XD/XA) formasyonlari icin tam-evren backtest + PRZ (erken uyari) kalite
arastirmasi.

Kullanicinin canli TradingView geri bildirimine (2026-08-18: "gercek
sinyaller cok azalmis, PRZ bazen alakasiz noktalarda geliyor") yanit olarak:
bu script HEM onayli (confirmed) sinyallerin yeni (X-noktali) tanimla
performansini HEM DE PRZ erken-uyarilarinin "kalitesini" (bir PRZ olayinin
GERCEKTEN sonradan onayli bir formasyona mi donustugu, yoksa "yanlis alarm"
mi oldugu -- `harmonic_xabcd.match_prz_to_confirmed`) OBJEKTIF, sayisal
olarak olcer.

4 kategori, HER (formasyon x yon x tf) hucresi icin AYRI backtest edilir:
  - CONFIRMED         : sadece onayli D sinyalleri (mevcut, pivot_lookback
                         sonrasi teyitli giris).
  - PRZ_ALL           : erken bolge-girislerinin TAMAMI (vindicated + false-start
                         birlikte) -- "PRZ'yi hic filtrelemeden kullansaydik".
  - PRZ_VINDICATED    : sadece SONRADAN gercekten onayli bir formasyona
                         donusen erken girisler -- "PRZ'nin EN IYI durumu".
  - PRZ_FALSE_START   : sadece hicbir zaman onaylanmayan erken girisler --
                         "PRZ'nin EN KOTU durumu" (kullanicinin "alakasiz
                         noktalar" gozlemi buradaki islemler olmali).

Ayrica her hucre icin `vindication_rate` (n_vindicated / n_prz_events * 100)
raporlanir -- PRZ'nin GENEL guvenilirligi.

quant-uzmani disiplinleri (`docs/spec/spec_abcd_mimari_kararlar.md`,
`scripts/abcd_research.py` ile AYNI): `min_trades_show`/`min_trades_trustworthy`
esikleri, GUVENSIZ hucreler GIZLENMEZ.

Kullanim:
    python scripts/harmonic_xabcd_research.py --limit-symbols 30   # pilot
    python scripts/harmonic_xabcd_research.py                      # TAM BIST evreni
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
from src.analysis.abcd_backtest import BacktestParams, backtest_symbol, compute_metrics  # noqa: E402
from src.analysis.abcd_scanner import get_bist_universe  # noqa: E402
from src.analysis.harmonic_xabcd import HARMONIC_XABCD_PRESETS, match_prz_to_confirmed  # noqa: E402
from src.analysis import harmonic_xabcd  # noqa: E402
from src.fetchers.abcd_data import fetch_ohlcv_abcd  # noqa: E402

config.setup_logging()

_DEFAULT_OUT_MD = BASE_DIR / "docs" / "spec" / "ABCD_XABCD_V2_ARASTIRMASI.md"
_DEFAULT_OUT_CSV = config.DATA_DIR / "abcd_cache" / "harmonic_xabcd_summary.csv"
_BARS_PER_YEAR = {"60": 252 * 7, "120": 252 * 4, "240": 252 * 2, "1D": 252, "1W": 52}
_CATEGORIES = ("CONFIRMED", "PRZ_ALL", "PRZ_VINDICATED", "PRZ_FALSE_START")


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


def run(symbols: list[str], tfs: list[str], years: float, min_trades_show: int, min_trades_trustworthy: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(cell_summary_df, vindication_df) doner."""
    bt_params = BacktestParams()
    cells: dict[tuple[str, str, str, str], list] = {}
    vindication_cells: dict[tuple[str, str, str], dict] = {}

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

            for formation_name, base_params in HARMONIC_XABCD_PRESETS.items():
                for direction in ("LONG", "SHORT"):
                    dp = replace(base_params, enable_long=direction == "LONG", enable_short=direction == "SHORT")

                    confirmed = harmonic_xabcd.detect(df, dp)
                    prz_events = harmonic_xabcd.detect_prz(df, dp)
                    vindicated_flags = match_prz_to_confirmed(prz_events, confirmed)
                    vindicated = [e for e, v in zip(prz_events, vindicated_flags) if v]
                    false_start = [e for e, v in zip(prz_events, vindicated_flags) if not v]

                    vkey = (formation_name, direction, tf)
                    vcell = vindication_cells.setdefault(vkey, {"n_events": 0, "n_vindicated": 0})
                    vcell["n_events"] += len(prz_events)
                    vcell["n_vindicated"] += len(vindicated)

                    for category, sig_list in (
                        ("CONFIRMED", confirmed),
                        ("PRZ_ALL", prz_events),
                        ("PRZ_VINDICATED", vindicated),
                        ("PRZ_FALSE_START", false_start),
                    ):
                        if not sig_list:
                            continue
                        trades, curve = backtest_symbol(df, symbol, sig_list, bt_params)
                        if not trades:
                            continue
                        key = (formation_name, direction, tf, category)
                        cell = cells.setdefault(key, {"trades": [], "drawdowns": [], "total_bars": 0})
                        cell["trades"].extend(trades)
                        metrics = compute_metrics(trades, curve, bt_params.initial_equity, len(df))
                        cell["drawdowns"].append(metrics["max_drawdown_pct"])
                        cell["total_bars"] += len(df)

    rows = []
    for (formation_name, direction, tf, category), cell in cells.items():
        trades = cell["trades"]
        n = len(trades)
        r_values = [t.r_multiple for t in trades if not math.isnan(t.r_multiple)]
        wins = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl <= 0]
        gross_profit = sum(t.pnl for t in wins)
        gross_loss = -sum(t.pnl for t in losses)
        rows.append(
            {
                "formasyon": formation_name,
                "yon": direction,
                "tf": tf,
                "kategori": category,
                "n_trades": n,
                "win_rate": (len(wins) / n * 100.0) if n else float("nan"),
                "profit_factor": (gross_profit / gross_loss) if gross_loss > 0 else float("inf") if gross_profit > 0 else float("nan"),
                "expectancy_r": (sum(r_values) / len(r_values)) if r_values else float("nan"),
                "avg_max_drawdown_pct": sum(cell["drawdowns"]) / len(cell["drawdowns"]) if cell["drawdowns"] else float("nan"),
                "trustworthy": n >= min_trades_trustworthy,
                "guven_etiketi": _guven(n, min_trades_show, min_trades_trustworthy),
            }
        )

    vrows = []
    for (formation_name, direction, tf), vcell in vindication_cells.items():
        n_events = vcell["n_events"]
        n_vind = vcell["n_vindicated"]
        vrows.append(
            {
                "formasyon": formation_name,
                "yon": direction,
                "tf": tf,
                "n_prz_events": n_events,
                "n_vindicated": n_vind,
                "vindication_rate_pct": (n_vind / n_events * 100.0) if n_events else float("nan"),
            }
        )

    cell_df = pd.DataFrame(rows)
    vind_df = pd.DataFrame(vrows)
    return cell_df, vind_df


def _build_report(cell_df: pd.DataFrame, vind_df: pd.DataFrame, symbols: list[str], tfs: list[str], years: float, min_trades_show: int, min_trades_trustworthy: int, out_csv: Path) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = ["# XABCD V2.1 (X-noktali) Arastirmasi -- Confirmed vs PRZ Kalitesi\n", f"\nOlusturulma: {now}\n"]

    lines.append("\n## Kapsam\n")
    lines.append(
        f"\nSembol sayisi: {len(symbols)} · Zaman dilimleri: {', '.join(tfs)} · Backtest derinligi: ~{years} yil · "
        "Para birimi: TRY. Formasyonlar: GARTLEY/BAT/BUTTERFLY/CRAB, X-noktali (V2.1) literatur-dogru CD/BC + "
        "XD/XA tanimiyla -- `pine/harmonic_formations_v1_indicator.pine` (V2.1, XD yon duzeltmesi dahil) ile "
        "Pine-parity.\n"
    )
    lines.append("\n## ⚠️ METODOLOJI UYARISI\n")
    lines.append(
        f"\n`min_trades_show={min_trades_show}` altindaki hucreler ASLA gizlenmez -- \"GUVENSIZ (n=X)\" olarak "
        f"etiketlenip tabloda TUTULUR. \"En iyi\" iddialari SADECE `min_trades_trustworthy={min_trades_trustworthy}` "
        "esigini gecen hucrelerden secilir.\n"
    )

    lines.append("\n## PRZ Dogrulanma (Vindication) Oranlari\n")
    lines.append(
        "\nBir PRZ erken-uyarisi \"dogrulanmis\" sayilir eger AYNI C pivotu icin SONRADAN gercekten onayli bir "
        "D sinyali olustuysa (`harmonic_xabcd.match_prz_to_confirmed`). Dusuk oran = PRZ'nin \"alakasiz\" gorunen "
        "kismi.\n"
    )
    if not vind_df.empty:
        lines.append("\n| Formasyon | Yon | TF | PRZ Olay Sayisi | Dogrulanan | Dogrulanma Orani % |\n")
        lines.append("|---|---|---|---|---|---|\n")
        for _, row in vind_df.sort_values(["formasyon", "yon", "tf"]).iterrows():
            lines.append(
                f"| {row['formasyon']} | {row['yon']} | {row['tf']} | {int(row['n_prz_events'])} | "
                f"{int(row['n_vindicated'])} | {_fmt(row['vindication_rate_pct'])} |\n"
            )
    else:
        lines.append("\n_Hicbir PRZ olayi uretilmedi._\n")

    lines.append("\n## Kategori Karsilastirmasi (CONFIRMED vs PRZ_ALL vs PRZ_VINDICATED vs PRZ_FALSE_START)\n")
    if not cell_df.empty:
        lines.append("\n| Formasyon | Yon | TF | Kategori | n | Win Rate % | Profit Factor | Beklenti (R) | Ort. Max DD % | Guven |\n")
        lines.append("|---|---|---|---|---|---|---|---|---|---|\n")
        cat_order = {c: i for i, c in enumerate(_CATEGORIES)}
        sorted_df = cell_df.assign(_cat_order=cell_df["kategori"].map(cat_order)).sort_values(
            ["formasyon", "yon", "tf", "_cat_order"]
        )
        for _, row in sorted_df.iterrows():
            lines.append(
                f"| {row['formasyon']} | {row['yon']} | {row['tf']} | {row['kategori']} | {int(row['n_trades'])} | "
                f"{_fmt(row['win_rate'])} | {_fmt(row['profit_factor'])} | {_fmt(row['expectancy_r'], '{:.3f}')} | "
                f"{_fmt(row['avg_max_drawdown_pct'])} | {row['guven_etiketi']} |\n"
            )
    else:
        lines.append("\n_Hicbir hucre uretilmedi._\n")

    lines.append("\n## Ham Veri\n")
    lines.append(f"\nHam hucre tablosu: `{out_csv}`\n")
    return "".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="XABCD V2.1 confirmed vs PRZ kalite arastirmasi.")
    parser.add_argument("--symbols", default=None)
    parser.add_argument("--tfs", default="1D,240")
    parser.add_argument("--years", type=float, default=2.0)
    parser.add_argument("--min-trades-show", type=int, default=30)
    parser.add_argument("--min-trades-trustworthy", type=int, default=100)
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

    print(f"Grid: {len(symbols)} sembol x {len(tfs)} tf x 4 formasyon x 2 yon x 4 kategori (~{args.years} yil gecmis).")
    cell_df, vind_df = run(symbols, tfs, args.years, args.min_trades_show, args.min_trades_trustworthy)

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    cell_df.to_csv(out_csv, index=False)
    print(f"Ham CSV kaydedildi: {out_csv}")

    report = _build_report(cell_df, vind_df, symbols, tfs, args.years, args.min_trades_show, args.min_trades_trustworthy, out_csv)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"Rapor kaydedildi: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
