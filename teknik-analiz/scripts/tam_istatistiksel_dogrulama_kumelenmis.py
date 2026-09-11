"""docs/KALAN_ISLER.md madde 1.7 devami -- SEMBOL DUZEYINDE KUMELENMIS
tekrar. `tam_istatistiksel_dogrulama.py`nin bulgusu: ham (sinyal-duzeyi)
permutasyon testi pseudo-replication'a acikti -- ayni sembolde CAKISAN/
tekrarlayan adaylar (ayni alttaki fiyat hareketi) bagimsiz gozlem gibi
sayiliyordu (wedge: 10 "sinyal" = 2 sembol; broadening: 57 "sinyal" = 10
sembol). Bu surum HER SEMBOL icin TEK bir ozet getiri (o sembolun OOS/IS
sinyallerinin ORTALAMASI) hesaplayip permutasyon testini SEMBOL sayisi
uzerinde kurar -- birim-analiz artik "sinyal" degil "sembol".

Ayrica ham sinyal-duzeyi veriyi de (gosterge, sembol, tarih, yon, getiri,
is_oos) uzun formatta CSV'ye yazar -- gelecekte yeniden hesaplamadan
farkli kumeleme/analiz denenebilsin diye."""
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
    print(f"{len(targets)} gosterge test edilecek (SEMBOL-duzeyi kumelenmis).")

    rows = []
    raw_records = []  # uzun format: gosterge, sembol, tarih, yon, getiri, is_oos
    for name in targets:
        indicator = scaled_factory(name, Timeframe.D1)
        # sembol -> [getiri, ...] (IS ve OOS ayri)
        is_by_sym: dict[str, list[float]] = {}
        oos_by_sym: dict[str, list[float]] = {}
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
                raw_records.append({
                    "gosterge": name, "sembol": sym, "tarih": sig.detected_at,
                    "yon": sig.direction, "getiri": r, "is_oos": "OOS" if is_oos else "IS",
                })
                if is_oos:
                    oos_by_sym.setdefault(sym, []).append(r)
                    oos_total += 1
                    oos_long += sig.direction == "long"
                else:
                    is_by_sym.setdefault(sym, []).append(r)
                    is_total += 1
                    is_long += sig.direction == "long"
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

        # KUMELEME: her sembol icin TEK ortalama getiri (birim artik sembol)
        is_clustered = [float(np.mean(v)) for v in is_by_sym.values()]
        oos_clustered = [float(np.mean(v)) for v in oos_by_sym.values()]

        is_long_frac = is_long / is_total if is_total else 0.5
        oos_long_frac = oos_long / oos_total if oos_total else 0.5
        oos_diff, oos_p = permutation_p_value(
            oos_clustered, oos_base_long, oos_base_short, oos_long_frac,
        )
        is_diff, is_p = permutation_p_value(
            is_clustered, is_base_long, is_base_short, is_long_frac,
        )
        rows.append({
            "gosterge": name,
            "n_is_sinyal": is_total, "n_is_sembol": len(is_clustered),
            "n_oos_sinyal": oos_total, "n_oos_sembol": len(oos_clustered),
            "is_fark_20b": is_diff, "is_p": is_p,
            "oos_fark_20b": oos_diff, "oos_p": oos_p,
            "oos_medyan_sembol_getiri": (
                float(np.median(oos_clustered)) if oos_clustered else float("nan")
            ),
            "n_hata": n_err,
        })
        print(f"{name:30s} n_oos_sinyal={oos_total:6d} n_oos_sembol={len(oos_clustered):4d} "
              f"oos_fark={oos_diff} oos_p={oos_p}")

    df_out = pd.DataFrame(rows)
    oos_pvals = dict(zip(df_out["gosterge"], df_out["oos_p"], strict=True))
    sig_map = benjamini_hochberg(oos_pvals, q=0.05)
    df_out["oos_bh_anlamli_q05"] = df_out["gosterge"].map(sig_map)

    print(f"\ntoplam sure: {time.time()-t0:.1f}s")
    out_dir = Path(__file__).resolve().parents[1] / "outputs" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    df_out.sort_values("oos_p").to_csv(
        out_dir / "tam_istatistiksel_dogrulama_kumelenmis_2026-09-12.csv", index=False,
    )
    pd.DataFrame(raw_records).to_csv(
        out_dir / "tam_istatistiksel_dogrulama_ham_sinyaller_2026-09-12.csv", index=False,
    )
    print(f"kaydedildi: {out_dir}")
    print("\n=== Benjamini-Hochberg q=0.05 SONRASI ANLAMLI KALANLAR (SEMBOL-kumeleme) ===")
    sig_rows = df_out[df_out["oos_bh_anlamli_q05"]].sort_values("oos_p")
    print(sig_rows[
        ["gosterge", "n_oos_sembol", "oos_fark_20b", "oos_medyan_sembol_getiri", "oos_p"]
    ].to_string(index=False))


if __name__ == "__main__":
    main()
