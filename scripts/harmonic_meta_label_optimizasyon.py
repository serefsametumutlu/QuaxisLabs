"""Harmonik sinyaller icin ILERI ablasyon + META-ETIKETLEME (AEGIS-tarzi)
backtesti -- `scripts/harmonic_confirmation_optimizasyon.py`nin devami.

Kullanici istegi (2026-08-19): "farkli kosullar altinda... cok detayli bir
backtest yap" + kullanicinin masaustundeki harici arastirma kaynagi
(`strateji_3_aegis_meta_filter.py`, `ULTIMATE_5_STRATEGIES.md §Hurst Regime
Switcher`) -- bu script IKI YENI boyut ekler:

  1. HUCUM sayisi (skor) esikli varyantlar (+2/4, +3/4 -- onceki script
     sadece TEK TEK filtreleri ve HEPSI'ni (4/4) test etmisti, arasindaki
     kombinasyonlari DEGIL) + Hurst rejim filtresi (+Hurst, TREND rejiminde
     mi daha guvenilir).
  2. META-ETIKETLEME: `src/analysis/triple_barrier.py` ile HER olayin
     BAGIMSIZ (portfoy kisitlamasi OLMADAN) kazanc/kayip etiketini hesaplar,
     RandomForest (AEGIS'in AYNI hiperparametreleri: n_estimators=100,
     max_depth=5, min_samples_leaf=3) egitir -- "onay bayraklarindan/
     Hurst'ten/formasyon geometrisinden bu sinyalin kazanacagini ONCEDEN
     tahmin edebilir miyiz" sorusuna KRONOLOJIK train(%70)/holdout(%30)
     ile (sizinti YOK, `scripts/harmonic_xabcd_prz_filter_backtest.py` ile
     AYNI disiplin) cevap verir.

Mimari: `harmonic_confirmation_optimizasyon.py`nin `collect()` iskeletini
GENISLETIR (ayni veriyi IKI KEZ CEKMEMEK icin ayri script, kod TEKRARI
BILINCLI -- ustteki script hala BAGIMSIZ calisir/gecerlidir).

Kullanim:
    python scripts/harmonic_meta_label_optimizasyon.py --limit-symbols 30  # pilot
    python scripts/harmonic_meta_label_optimizasyon.py                     # TAM BIST
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

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.ensemble import RandomForestClassifier  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402

import config  # noqa: E402
from src.analysis import harmonic_xabcd  # noqa: E402
from src.analysis.abcd_scanner import get_bist_universe  # noqa: E402
from src.analysis.harmonic_confirmation import compute_indicator_series, evaluate_confirmations  # noqa: E402
from src.analysis.harmonic_xabcd import ABCD_PRESET, HARMONIC_XABCD_PRESETS  # noqa: E402
from src.analysis.regime_filters import TREND_THRESHOLD, rolling_hurst  # noqa: E402
from src.analysis.triple_barrier import label_outcome  # noqa: E402
from src.fetchers.abcd_data import fetch_ohlcv_abcd  # noqa: E402

config.setup_logging()

_DEFAULT_OUT_MD = BASE_DIR / "docs" / "spec" / "HARMONIC_META_LABEL_OPTIMIZASYON.md"
_DEFAULT_OUT_CSV = config.DATA_DIR / "abcd_cache" / "harmonic_meta_label_events.csv"
_BARS_PER_YEAR = {"60": 252 * 7, "120": 252 * 4, "240": 252 * 2, "1D": 252, "1W": 52}
_ALL_FORMATIONS = {"ABCD": ABCD_PRESET, **HARMONIC_XABCD_PRESETS}
_MAX_HOLD_BARS = 15  # triple-barrier dikey bariyer (bkz. modul ust notu)
_HURST_WINDOW = 50
_HURST_MAX_LAG = 15
_MIN_TRADES_TRUSTWORTHY = 100
_MIN_TRADES_SHOW = 10

_SCORE_VARIANTS = {
    "BASELINE": lambda r: True,
    "+RSI": lambda r: r["rsi_ok"],
    "+MACD": lambda r: r["macd_ok"],
    "+Mum": lambda r: r["candle_ok"],
    "+Hacim": lambda r: r["volume_ok"],
    "+Hurst(TREND)": lambda r: r["hurst"] > TREND_THRESHOLD,
    "+2/4onay": lambda r: r["score"] >= 2,
    "+3/4onay": lambda r: r["score"] >= 3,
    "+TUMU(4/4)": lambda r: r["score"] >= 4,
}


def _bars_for_years(tf: str, years: float) -> int:
    return max(int(_BARS_PER_YEAR[tf] * years) + 50, 200)


def collect(symbols: list[str], tfs: list[str], years: float) -> pd.DataFrame:
    rows: list[dict] = []
    total = len(symbols) * len(tfs)
    done = 0
    for tf in tfs:
        n_bars = _bars_for_years(tf, years)
        for symbol in symbols:
            done += 1
            if done % 50 == 0:
                print(f"  ... {done}/{total} (sembol x tf) islendi, su ana kadar {len(rows)} olay")
            df = fetch_ohlcv_abcd(symbol, tf, n_bars)
            if df.empty:
                continue
            indicators = compute_indicator_series(df)
            close = df["close"].to_numpy(dtype=float)
            high = df["high"].to_numpy(dtype=float)
            low = df["low"].to_numpy(dtype=float)
            hurst_series = rolling_hurst(close, window=_HURST_WINDOW, max_lag=_HURST_MAX_LAG)

            for formation_name, base_params in _ALL_FORMATIONS.items():
                for direction in ("LONG", "SHORT"):
                    dp = replace(base_params, enable_long=direction == "LONG", enable_short=direction == "SHORT")
                    events = harmonic_xabcd.detect_prz(df, dp)
                    for ev in events:
                        flags = evaluate_confirmations(df, indicators, ev.direction, ev.b_bar, ev.b_price, ev.d_bar, ev.d_price)
                        outcome = label_outcome(
                            high, low, close, entry_bar=ev.signal_bar, entry_price=ev.entry_ref,
                            tp=ev.tp1, sl=ev.sl, direction=ev.direction, max_hold_bars=_MAX_HOLD_BARS,
                        )
                        if outcome.hit == "INSUFFICIENT_DATA":
                            continue
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
                                "hurst": float(hurst_series[ev.d_bar]) if ev.d_bar < len(hurst_series) else 0.5,
                                "bc_ratio": ev.bc_ratio,
                                "win": outcome.win,
                                "r_multiple": outcome.r_multiple,
                                "hit": outcome.hit,
                            }
                        )
    return pd.DataFrame(rows)


def _fmt(value, fmt: str = "{:.2f}") -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    if isinstance(value, float) and math.isinf(value):
        return "sonsuz" if value > 0 else "-sonsuz"
    return fmt.format(value)


def _r_stats(r_values: pd.Series) -> dict:
    n = len(r_values)
    if n == 0:
        return {"n": 0, "win_rate": float("nan"), "profit_factor": float("nan"), "expectancy_r": float("nan")}
    wins = r_values[r_values > 0]
    losses = r_values[r_values <= 0]
    gross_profit = float(wins.sum())
    gross_loss = float(-losses.sum())
    return {
        "n": n,
        "win_rate": float((r_values > 0).mean() * 100.0),
        "profit_factor": (gross_profit / gross_loss) if gross_loss > 0 else float("inf") if gross_profit > 0 else float("nan"),
        "expectancy_r": float(r_values.mean()),
    }


def _guven(n: int) -> str:
    if n < _MIN_TRADES_SHOW:
        return "orneklem COK kucuk"
    if n < _MIN_TRADES_TRUSTWORTHY:
        return "orneklem kucuk"
    return "guvenilir n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tfs", default="1D,240")
    parser.add_argument("--years", type=float, default=2.0)
    parser.add_argument("--limit-symbols", type=int, default=None)
    parser.add_argument("--out", default=str(_DEFAULT_OUT_MD))
    parser.add_argument("--out-csv", default=str(_DEFAULT_OUT_CSV))
    args = parser.parse_args(argv)

    print("get_bist_universe() ile TUM BIST evreni DB'den cekiliyor...")
    symbols = get_bist_universe()
    print(f"  {len(symbols)} sembol bulundu.")
    if args.limit_symbols is not None:
        symbols = symbols[: args.limit_symbols]
        print(f"--limit-symbols {args.limit_symbols}: ilk {len(symbols)} sembolle sinirlandi.")

    tfs = [t.strip() for t in args.tfs.split(",") if t.strip()]

    print(f"Olaylar + onay bayraklari + Hurst + triple-barrier etiketleri toplaniyor: {len(symbols)} sembol x {len(tfs)} tf...")
    events_df = collect(symbols, tfs, args.years)
    print(f"Toplam {len(events_df)} etiketlenebilir olay toplandi.")

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    events_df.to_csv(out_csv, index=False)
    print(f"Ham olay tablosu kaydedildi: {out_csv}")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Harmonik Ileri Ablasyon + Meta-Etiketleme (AEGIS-tarzi RandomForest)\n",
        f"\nOlusturulma: {now}\n",
        "\n## Kapsam\n",
        f"\nSembol: {len(symbols)} · TF: {', '.join(tfs)} · Derinlik: {args.years:.1f} yil · "
        f"Toplam etiketlenebilir olay: {len(events_df)} · Triple-barrier dikey sinir: {_MAX_HOLD_BARS} bar\n",
        "\n## Yontem -- iki ayri deney\n",
        "\n**(A) Skor-esikli ablasyon**: `harmonic_confirmation_optimizasyon.py`nin tek-tek filtre "
        "testinin OTESINDE, `score>=2`/`score>=3` (kombinasyon) ve `+Hurst(TREND)` varyantlari eklendi. "
        "Sonuc her (formasyon,yon,tf) hucresi icin TAM BIST uzerinde, r-multiple bazli.\n",
        "\n**(B) Meta-etiketleme**: her olay `src/analysis/triple_barrier.py` ile BAGIMSIZ (portfoy "
        "kisitlamasi olmadan) kazanc/kayip etiketlenir; `RandomForestClassifier(n_estimators=100, "
        "max_depth=5, min_samples_leaf=3)` KRONOLOJIK ilk %70 (train) uzerinde egitilir, SON %30 "
        "(holdout, gercekten gorulmemis) uzerinde test edilir. Ozellikler: rsi_ok/macd_ok/candle_ok/"
        "volume_ok/score/hurst/bc_ratio + formasyon/yon/tf (one-hot). SADECE holdout sonuclari "
        "out-of-sample gecerlidir.\n",
    ]

    # ── (A) Skor-esikli ablasyon ──
    lines.append("\n## (A) Skor-esikli + Hurst ablasyonu (tam BIST, r-multiple bazli)\n")
    lines.append("\n| Formasyon | Yon | TF | Varyant | n | Win Rate % | Profit Factor | Beklenti (R) | Guven |\n|---|---|---|---|---|---|---|---|---|\n")
    for (formasyon, yon, tf), grp in events_df.groupby(["formasyon", "yon", "tf"]):
        for vname, pred in _SCORE_VARIANTS.items():
            mask = grp.apply(pred, axis=1) if len(grp) else pd.Series([], dtype=bool)
            sub = grp[mask]
            stats = _r_stats(sub["r_multiple"])
            lines.append(
                f"| {formasyon} | {yon} | {tf} | {vname} | {stats['n']} | {_fmt(stats['win_rate'])} | "
                f"{_fmt(stats['profit_factor'])} | {_fmt(stats['expectancy_r'], '{:.3f}')} | {_guven(stats['n'])} |\n"
            )

    # ── (B) Meta-etiketleme ──
    lines.append("\n## (B) Meta-Etiketleme -- RandomForest Kapisi (kronolojik train/holdout)\n")

    events_df = events_df.sort_values("entry_time").reset_index(drop=True)
    feature_cols_base = ["rsi_ok", "macd_ok", "candle_ok", "volume_ok", "score", "hurst", "bc_ratio"]
    cat_cols = ["formasyon", "yon", "tf"]

    model_df = events_df.dropna(subset=feature_cols_base + ["win"]).copy()
    for c in ["rsi_ok", "macd_ok", "candle_ok", "volume_ok"]:
        model_df[c] = model_df[c].astype(int)

    dummies = pd.get_dummies(model_df[cat_cols], prefix=cat_cols)
    X_full = pd.concat([model_df[feature_cols_base], dummies], axis=1)
    y_full = model_df["win"].astype(int)

    split_idx = int(round(len(model_df) * 0.7))
    split_idx = min(max(split_idx, 1), len(model_df) - 1) if len(model_df) > 1 else len(model_df)

    if len(model_df) < 200 or split_idx <= 0 or split_idx >= len(model_df):
        lines.append("\n⚠️ Yetersiz veri -- meta-etiketleme egitimi ATLANDI (n<200 veya split gecersiz).\n")
    else:
        X_train, X_hold = X_full.iloc[:split_idx], X_full.iloc[split_idx:]
        y_train, y_hold = y_full.iloc[:split_idx], y_full.iloc[split_idx:]
        r_hold = model_df["r_multiple"].iloc[split_idx:]
        split_time = model_df["entry_time"].iloc[split_idx - 1]

        rf = RandomForestClassifier(n_estimators=100, max_depth=5, min_samples_leaf=3, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)

        proba_hold = rf.predict_proba(X_hold)[:, 1] if len(np.unique(y_train)) > 1 else np.full(len(X_hold), y_train.mean())
        auc = roc_auc_score(y_hold, proba_hold) if len(np.unique(y_hold)) > 1 else float("nan")

        lines.append(f"\n- Toplam etiketlenebilir olay: {len(model_df)} (train={len(X_train)}, holdout={len(X_hold)})\n")
        lines.append(f"- Kronolojik split tarihi: {split_time}\n")
        lines.append(f"- Holdout AUC (RF'nin ayirt etme gucu, 0.5=rastgele): {_fmt(auc, '{:.3f}')}\n")

        lines.append("\n### Holdout: filtre esigine gore PF/win-rate\n")
        lines.append("\n| Esik | n | Win Rate % | Profit Factor | Beklenti (R) | Guven |\n|---|---|---|---|---|---|\n")
        baseline_stats = _r_stats(r_hold)
        lines.append(
            f"| (filtresiz, TUM holdout) | {baseline_stats['n']} | {_fmt(baseline_stats['win_rate'])} | "
            f"{_fmt(baseline_stats['profit_factor'])} | {_fmt(baseline_stats['expectancy_r'], '{:.3f}')} | {_guven(baseline_stats['n'])} |\n"
        )
        for thresh in (0.50, 0.55, 0.60, 0.65):
            pass_mask = proba_hold >= thresh
            sub_r = r_hold[pass_mask]
            stats = _r_stats(sub_r)
            lines.append(
                f"| RF prob >= {thresh:.2f} | {stats['n']} | {_fmt(stats['win_rate'])} | "
                f"{_fmt(stats['profit_factor'])} | {_fmt(stats['expectancy_r'], '{:.3f}')} | {_guven(stats['n'])} |\n"
            )

        importances = pd.Series(rf.feature_importances_, index=X_full.columns).sort_values(ascending=False)
        lines.append("\n### Ozellik onemleri (RandomForest, egitim uzerinden)\n")
        lines.append("\n| Ozellik | Onem |\n|---|---|\n")
        for feat, imp in importances.head(12).items():
            lines.append(f"| {feat} | {imp:.4f} |\n")

    lines.append("\n## Ham Veri\n")
    lines.append(f"\nOlay basina TUM ozellikler + win/r_multiple etiketleri: `{out_csv}`\n")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"Rapor kaydedildi: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
