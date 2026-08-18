"""PRZ dogrulanma filtresi -- somut kural + out-of-sample backtest.

`docs/spec/ABCD_XABCD_PRZ_DOGRULANMA_FAKTORLERI.md`nin bulgusunu (tek
univariate+holdout VE multivariate modelde TUTARLI kalan 2 ozellik:
`cd_duration_bars` pozitif, `volume_ratio` negatif) somut, Pine/Telegram'a
tasinabilir bir ESIK KURALINA cevirir ve GERCEK out-of-sample (holdout)
veriyle dogrular -- "bu kural gercekten dogrulanma oranini/PnL'i iyilestiriyor
mu, yoksa train'e mi uyduruldu" sorusuna cevap verir.

## Metodoloji -- neden esikler SADECE train'den turetilir

Esikler (`cd_duration_bars >= train medyani` VE `volume_ratio <= train
medyani`) SADECE kronolojik train (%70, ilk) biriminden hesaplanir, sonra
DEGISTIRILMEDEN holdout'a (%30, son -- GERCEKTEN GORULMEMIS veri) uygulanir.
Butun raporlanan "filtre isliyor mu" iddialari SADECE holdout uzerindendir
-- train uzerinde olculen herhangi bir iyilesme, esikler zaten O verirye
gore secildigi icin ANLAMSIZDIR (dolasik/circular).

Medyan secimi (ROC-optimize edilmis bir esik DEGIL) BILINCLI: (1) basit,
yorumlanabilir, Pine input'una dogrudan tasinabilir bir kural hedefleniyor
(karmasik bir ML modeli DEGIL), (2) az sayida (2) ozellik + medyan-split,
train'e asiri-uyum (overfitting) riskini kucuk n'lerde bile dusuk tutar.

Kullanim:
    python scripts/harmonic_xabcd_prz_filter_backtest.py --limit-symbols 30  # pilot
    python scripts/harmonic_xabcd_prz_filter_backtest.py                     # TAM BIST evreni
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
from src.analysis.harmonic_xabcd import HARMONIC_XABCD_PRESETS, PrzEvent, match_prz_to_confirmed  # noqa: E402
from src.analysis import harmonic_xabcd  # noqa: E402
from src.fetchers.abcd_data import fetch_ohlcv_abcd  # noqa: E402

config.setup_logging()

_DEFAULT_OUT_MD = BASE_DIR / "docs" / "spec" / "ABCD_XABCD_PRZ_FILTRE_BACKTEST.md"
_DEFAULT_OUT_CSV = config.DATA_DIR / "abcd_cache" / "harmonic_xabcd_prz_filter_events.csv"
_BARS_PER_YEAR = {"60": 252 * 7, "120": 252 * 4, "240": 252 * 2, "1D": 252, "1W": 52}


def _bars_for_years(tf: str, years: float) -> int:
    return max(int(_BARS_PER_YEAR[tf] * years) + 50, 200)


def _volume_ratio(df: pd.DataFrame, c_bar: int, d_bar: int) -> float | None:
    """`abcd_factor_analysis.extract_features`in `volume_ratio` formuluyle
    BIREBIR AYNI (hesaplama mantigi IKI YERDE YASAMASIN ilkesi -- burada
    TEK basit bolme oldugu icin tam modulu import etmek yerine ayni formul
    yeniden yazildi, ama TANIM birebir eslesir: mean(volume[c:d+1]) /
    mean(volume[d-20:d]))."""
    volume = df["volume"].to_numpy(dtype=float)
    seg_cd = volume[c_bar : d_bar + 1]
    base_start = max(d_bar - 20, 0)
    seg_base = volume[base_start:d_bar]
    if len(seg_cd) == 0 or len(seg_base) == 0 or seg_base.mean() <= 0:
        return None
    return float(seg_cd.mean() / seg_base.mean())


def collect(
    symbols: list[str], tfs: list[str], years: float
) -> tuple[pd.DataFrame, dict[tuple[str, str], pd.DataFrame]]:
    """Her PRZ olayi icin `cd_duration_bars`/`volume_ratio`/`vindicated` +
    geri-backtest icin gereken TUM `PrzEvent` alanlarini tek bir DataFrame'de
    toplar (satir basina `_event` sutununda orijinal `PrzEvent` nesnesi de
    saklanir -- filtre uygulandiktan SONRA `backtest_symbol`e gecmek icin).

    `(events_df, ohlcv_cache)` doner -- `ohlcv_cache`, her (sembol,tf) icin
    BURADA zaten cekilmis DataFrame'i saklar; `main()` sonradan AYNI veriyi
    (parquet onbellek acik olsa bile ag/IO'ya IKINCI kez gitmeden) backtest
    icin yeniden kullanir."""
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

            for formation_name, base_params in HARMONIC_XABCD_PRESETS.items():
                for direction in ("LONG", "SHORT"):
                    dp = replace(base_params, enable_long=direction == "LONG", enable_short=direction == "SHORT")
                    confirmed = harmonic_xabcd.detect(df, dp)
                    events = harmonic_xabcd.detect_prz(df, dp)
                    if not events:
                        continue
                    vindicated_flags = match_prz_to_confirmed(events, confirmed)

                    for ev, vindicated in zip(events, vindicated_flags):
                        vol_ratio = _volume_ratio(df, ev.c_bar, ev.d_bar)
                        rows.append(
                            {
                                "symbol": symbol,
                                "tf": tf,
                                "formasyon": formation_name,
                                "yon": direction,
                                "entry_time": ev.signal_time,
                                "vindicated": bool(vindicated),
                                "cd_duration_bars": ev.d_bar - ev.c_bar,
                                "volume_ratio": vol_ratio,
                                "_event": ev,
                            }
                        )

    return pd.DataFrame(rows), ohlcv_cache


def _fmt(value: float, fmt: str = "{:.2f}") -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    if isinstance(value, float) and math.isinf(value):
        return "sonsuz" if value > 0 else "-sonsuz"
    return fmt.format(value)


def _backtest_events(events: list[PrzEvent], ohlcv_by_symbol_tf: dict, symbols_tfs: list[tuple[str, str]]) -> tuple[list, list]:
    """Verilen `events` listesini (sembol, tf) basina gruplayip
    `backtest_symbol` uzerinden gecirir -- turn `(trades, drawdowns)`."""
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


def _cell_stats(trades: list, drawdowns: list[float]) -> dict:
    n = len(trades)
    if n == 0:
        return {"n": 0, "win_rate": float("nan"), "profit_factor": float("nan"), "expectancy_r": float("nan"), "avg_dd": float("nan")}
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
        "avg_dd": sum(drawdowns) / len(drawdowns) if drawdowns else float("nan"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PRZ dogrulanma filtresi -- somut kural + out-of-sample backtest.")
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
    events_df, ohlcv_cache = collect(symbols, tfs, args.years)
    print(f"Toplam {len(events_df)} PRZ olayi (volume_ratio hesaplanamayan satirlar cikarilacak).")
    events_df = events_df.dropna(subset=["volume_ratio"]).reset_index(drop=True)
    events_df = events_df.sort_values("entry_time").reset_index(drop=True)
    print(f"volume_ratio hesaplanan: {len(events_df)}")

    split_idx = int(round(len(events_df) * 0.7))
    split_idx = min(max(split_idx, 1), len(events_df) - 1) if len(events_df) > 1 else len(events_df)
    train_df = events_df.iloc[:split_idx]
    holdout_df = events_df.iloc[split_idx:]
    split_time = events_df["entry_time"].iloc[split_idx - 1] if split_idx > 0 else None

    cd_threshold = float(train_df["cd_duration_bars"].median())
    vol_threshold = float(train_df["volume_ratio"].median())
    print(f"Train-turetilmis esikler: cd_duration_bars >= {cd_threshold:.1f} VE volume_ratio <= {vol_threshold:.3f}")

    def _passes(row) -> bool:
        return row["cd_duration_bars"] >= cd_threshold and row["volume_ratio"] <= vol_threshold

    holdout_pass = holdout_df[holdout_df.apply(_passes, axis=1)]
    holdout_fail = holdout_df[~holdout_df.apply(_passes, axis=1)]

    def _run_bt(sub_df: pd.DataFrame) -> dict:
        events = list(sub_df["_event"])
        keys = list(zip(sub_df["symbol"], sub_df["tf"]))
        trades, drawdowns = _backtest_events(events, ohlcv_cache, keys)
        return _cell_stats(trades, drawdowns)

    stats_holdout_all = _run_bt(holdout_df)
    stats_holdout_pass = _run_bt(holdout_pass)
    stats_holdout_fail = _run_bt(holdout_fail)
    stats_train_all = _run_bt(train_df)
    train_pass = train_df[train_df.apply(_passes, axis=1)]
    stats_train_pass = _run_bt(train_pass)

    vind_holdout_all = holdout_df["vindicated"].mean() * 100.0 if len(holdout_df) else float("nan")
    vind_holdout_pass = holdout_pass["vindicated"].mean() * 100.0 if len(holdout_pass) else float("nan")
    vind_holdout_fail = holdout_fail["vindicated"].mean() * 100.0 if len(holdout_fail) else float("nan")
    vind_train_all = train_df["vindicated"].mean() * 100.0 if len(train_df) else float("nan")
    vind_train_pass = train_pass["vindicated"].mean() * 100.0 if len(train_pass) else float("nan")

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    events_df.drop(columns=["_event"]).to_csv(out_csv, index=False)
    print(f"Ham PRZ olay tablosu kaydedildi: {out_csv}")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# PRZ Dogrulanma Filtresi -- Somut Kural + Out-of-Sample Backtest\n",
        f"\nOlusturulma: {now}\n",
        "\n## Kural\n",
        f"\n`cd_duration_bars >= {cd_threshold:.1f}` VE `volume_ratio <= {vol_threshold:.3f}` -- "
        "esikler SADECE kronolojik train'in (%70, ilk) medyanlarindan turetildi, holdout'a "
        "(%30, son -- gercekten gorulmemis veri) DEGISTIRILMEDEN uygulandi.\n",
        f"\n- Toplam PRZ olayi: {len(events_df)} (train={len(train_df)}, holdout={len(holdout_df)})\n",
        f"- Kronolojik split esigi: {split_time}\n",
        "\n## ⚠️ Bu raporun SADECE holdout satirlari out-of-sample gecerlidir\n",
        "\nTrain satirlari SADECE referans/karsilastirma icindir -- esikler train'den turetildigi "
        "icin train uzerindeki herhangi bir 'iyilesme' dolasiktir (circular), kanit DEGERI YOK.\n",
        "\n## Dogrulanma Orani (Vindication Rate)\n",
        "\n| Kume | n | Dogrulanma Orani % |\n|---|---|---|\n",
        f"| HOLDOUT -- tum PRZ (filtresiz) | {len(holdout_df)} | {_fmt(vind_holdout_all)} |\n",
        f"| HOLDOUT -- filtreyi GECEN | {len(holdout_pass)} | {_fmt(vind_holdout_pass)} |\n",
        f"| HOLDOUT -- filtreyi GECEMEYEN | {len(holdout_fail)} | {_fmt(vind_holdout_fail)} |\n",
        f"| (referans, train) tum PRZ | {len(train_df)} | {_fmt(vind_train_all)} |\n",
        f"| (referans, train) filtreyi GECEN | {len(train_pass)} | {_fmt(vind_train_pass)} |\n",
        "\n## Backtest Performansi (R-multiple bazli)\n",
        "\n| Kume | n_trades | Win Rate % | Profit Factor | Beklenti (R) | Ort. Max DD % |\n|---|---|---|---|---|---|\n",
    ]
    for label, stats in (
        ("HOLDOUT -- tum PRZ (filtresiz)", stats_holdout_all),
        ("HOLDOUT -- filtreyi GECEN", stats_holdout_pass),
        ("HOLDOUT -- filtreyi GECEMEYEN", stats_holdout_fail),
        ("(referans, train) tum PRZ", stats_train_all),
        ("(referans, train) filtreyi GECEN", stats_train_pass),
    ):
        lines.append(
            f"| {label} | {stats['n']} | {_fmt(stats['win_rate'])} | {_fmt(stats['profit_factor'])} | "
            f"{_fmt(stats['expectancy_r'], '{:.3f}')} | {_fmt(stats['avg_dd'])} |\n"
        )

    lines.append("\n## Ham Veri\n")
    lines.append(f"\nHam PRZ olay tablosu (ozellikler + vindicated etiketi): `{out_csv}`\n")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"Rapor kaydedildi: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
