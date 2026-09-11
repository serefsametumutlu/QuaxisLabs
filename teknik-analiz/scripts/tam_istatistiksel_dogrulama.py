"""docs/KALAN_ISLER.md madde 1.2/1.3 -- TAM istatistiksel dogrulama.

olcum_forward_return.py'nin (60 sembol, tek pencere, coklu test duzeltmesi
YOK) devami: TAM 648-sembol BIST evreni + IS/OOS zaman ayrimi (sinyal
tarihine gore, ayni veri iki kez KULLANILMAZ) + permutasyon testiyle
p-degeri + Benjamini-Hochberg FDR duzeltmesi (23 gosterge = 23 test).

Yontem:
  1. Her sembol icin df TAM (indicator non-repaint sozlesmesi geregi TEK
     kez hesaplanir, walk-forward gerek yok -- bkz. olcum_forward_return.py
     docstring'i).
  2. IS/OOS ayrimi ZAMANA gore: her sembolun kendi tarih araliginin ilk
     %70'i IS, son %30'u OOS (bar pozisyonuna gore DEGIL, boylece farkli
     sembollerin farkli IS/OOS tarih araliklari olabilir -- ama HER
     sembolun KENDI ic ayrimi tutarli).
  3. state in {confirmed, completed} sinyaller, giris detected_at kapanisi,
     20 bar ileri getiri (yon-duzeltilmis), yon-agirlikli adil baz (AYNI
     yontem, olcum_forward_return.py).
  4. OOS icin: permutasyon testi (B=3000) ile p-degeri (sinyal getirileri
     havuzu vs baz getiri havuzu, iki grubun ortalama farki HANGI siklikla
     rastgele yeniden gruplamadan buyuk cikiyor).
  5. Benjamini-Hochberg FDR (q=0.05), 23 gosterge uzerinde.
"""
from __future__ import annotations

import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from tlab.core.types import Timeframe
from tlab.indicators.bootstrap import CATALOG, scaled_factory

random.seed(7)
np.random.seed(7)

DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "ohlcv" / "bist"
HORIZON = 20
MIN_BARS = 300
IS_FRACTION = 0.70
N_PERM = 3000


def load_universe() -> dict[str, pd.DataFrame]:
    all_syms = sorted(d.name for d in DATA_ROOT.iterdir() if d.is_dir() and "." not in d.name)
    dfs: dict[str, pd.DataFrame] = {}
    for s in all_syms:
        p = DATA_ROOT / s / "1D.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        if len(df) < MIN_BARS:
            continue
        dfs[s] = df
    return dfs


def fwd_return(df: pd.DataFrame, entry_pos: int, horizon: int, direction: str) -> float | None:
    exit_pos = entry_pos + horizon
    if exit_pos >= len(df):
        return None
    entry_px = float(df["close"].iloc[entry_pos])
    exit_px = float(df["close"].iloc[exit_pos])
    ret = exit_px / entry_px - 1.0
    return ret if direction == "long" else -ret


def permutation_p_value(
    sig_returns: list[float], base_long: list[float], base_short: list[float],
    long_frac: float, n_perm: int = N_PERM,
) -> tuple[float, float]:
    """H0: sinyal getirileri, yon-agirlikli adil baz havuzuyla AYNI
    dagilimdan geliyor. Gozlenen fark = mean(sinyal) - adil_baz_ortalamasi.
    Baz havuzu (long+short karisimi, HER cekilis yon-agirlikli) permute
    edilerek null dagilim kurulur, iki-yonlu p-degeri doner."""
    if not sig_returns or (not base_long and not base_short):
        return float("nan"), float("nan")
    obs_mean = float(np.mean(sig_returns))
    fair_base = long_frac * np.mean(base_long) + (1 - long_frac) * np.mean(base_short) \
        if base_long and base_short else (np.mean(base_long) if base_long else np.mean(base_short))
    observed_diff = obs_mean - fair_base

    pool = np.array(sig_returns + base_long + base_short)
    n_sig = len(sig_returns)
    diffs = np.empty(n_perm)
    for b in range(n_perm):
        idx = np.random.permutation(len(pool))
        resampled_sig = pool[idx[:n_sig]]
        diffs[b] = resampled_sig.mean() - fair_base
    p = float((np.abs(diffs) >= abs(observed_diff)).mean())
    return observed_diff, p


def benjamini_hochberg(pvalues: dict[str, float], q: float = 0.05) -> dict[str, bool]:
    items = [(k, v) for k, v in pvalues.items() if not np.isnan(v)]
    items.sort(key=lambda kv: kv[1])
    m = len(items)
    significant: dict[str, bool] = dict.fromkeys(pvalues, False)
    max_rank_ok = 0
    for rank, (name, p) in enumerate(items, start=1):
        if p <= (rank / m) * q:
            max_rank_ok = rank
    for rank, (name, p) in enumerate(items, start=1):
        significant[name] = rank <= max_rank_ok
    return significant


def main() -> None:
    t0 = time.time()
    dfs = load_universe()
    print(f"{len(dfs)} sembol yuklendi (tam evren, >= {MIN_BARS} bar).")

    targets = sorted(
        name for name, spec in CATALOG.items()
        if not spec.needs_context and not spec.needs_universe
    )
    print(f"{len(targets)} gosterge test edilecek.")

    rows = []
    for name in targets:
        indicator = scaled_factory(name, Timeframe.D1)
        is_sig, oos_sig = [], []
        is_base_long, is_base_short = [], []
        oos_base_long, oos_base_short = [], []
        is_long = oos_long = is_total = oos_total = 0
        n_err = 0
        for sym, df in dfs.items():
            n = len(df)
            split_pos = int(n * IS_FRACTION)
            split_time = df.index[split_pos]
            try:
                result = indicator(df)
            except Exception:
                n_err += 1
                continue
            idx = df.index
            for sig in result.signals:
                if sig.state not in ("confirmed", "completed"):
                    continue
                if sig.direction not in ("long", "short"):
                    continue
                pos = idx.get_indexer([sig.detected_at])[0]
                if pos < 0:
                    continue
                r = fwd_return(df, pos, HORIZON, sig.direction)
                if r is None:
                    continue
                is_oos = sig.detected_at >= split_time
                if is_oos:
                    oos_sig.append(r)
                    oos_total += 1
                    oos_long += sig.direction == "long"
                else:
                    is_sig.append(r)
                    is_total += 1
                    is_long += sig.direction == "long"
            # baz: sembol basina rastgele barlar, IS/OOS ayni sekilde bolunur
            n_base = min(30, n - HORIZON - 1)
            if n_base > 0:
                positions = random.sample(range(0, n - HORIZON - 1), n_base)
                for p in positions:
                    r = fwd_return(df, p, HORIZON, "long")
                    if r is None:
                        continue
                    if idx[p] >= split_time:
                        oos_base_long.append(r)
                        oos_base_short.append(-r)
                    else:
                        is_base_long.append(r)
                        is_base_short.append(-r)

        is_long_frac = is_long / is_total if is_total else 0.5
        oos_long_frac = oos_long / oos_total if oos_total else 0.5
        oos_diff, oos_p = permutation_p_value(
            oos_sig, oos_base_long, oos_base_short, oos_long_frac,
        )
        is_diff, is_p = permutation_p_value(
            is_sig, is_base_long, is_base_short, is_long_frac,
        )
        rows.append({
            "gosterge": name,
            "n_is": is_total, "n_oos": oos_total,
            "is_fark_20b": is_diff, "is_p": is_p,
            "oos_fark_20b": oos_diff, "oos_p": oos_p,
            "n_hata": n_err,
        })
        print(f"{name:30s} n_is={is_total:6d} n_oos={oos_total:6d} "
              f"is_fark={is_diff} oos_fark={oos_diff} oos_p={oos_p}")

    df_out = pd.DataFrame(rows)
    oos_pvals = dict(zip(df_out["gosterge"], df_out["oos_p"], strict=True))
    sig_map = benjamini_hochberg(oos_pvals, q=0.05)
    df_out["oos_bh_anlamli_q05"] = df_out["gosterge"].map(sig_map)

    print(f"\ntoplam sure: {time.time()-t0:.1f}s")
    out_path = Path(__file__).resolve().parents[1] / "outputs" / "reports" / (
        "tam_istatistiksel_dogrulama_2026-09-11.csv"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_out.sort_values("oos_p").to_csv(out_path, index=False)
    print(f"kaydedildi: {out_path}")
    print("\n=== Benjamini-Hochberg q=0.05 SONRASI ANLAMLI KALANLAR ===")
    sig_rows = df_out[df_out["oos_bh_anlamli_q05"]].sort_values("oos_p")
    print(sig_rows[["gosterge", "n_oos", "oos_fark_20b", "oos_p"]].to_string(index=False))


if __name__ == "__main__":
    main()
