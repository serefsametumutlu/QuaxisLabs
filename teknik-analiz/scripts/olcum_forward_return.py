"""27 gostergeden context/universe istemeyen 23'unun, gercek 1D BIST verisinde
ureteceği TUM tarihi sinyallerin ileri-donuk (forward) getirisini olcer.

Yontem: her (sembol, gosterge) icin indicator(df) TAM gecmis uzerinde BIR KEZ
cagrilir (non-repaint sozlesmesi geregi result.signals zaten TAM ve GECERLI
bir tarihi liste -- ayrica walk-forward tekrar hesaplamaya gerek yok).
state in {confirmed, completed} VE direction in {long, short} olan sinyaller
"aksiyon alinabilir" sayilir. Giris: detected_at barinin kapanisi. Getiri:
[5, 10, 20] bar sonraki kapanis / giris kapanisi - 1, short icin isaret ters
cevrilir. Baz cizgi: AYNI sembol/ufuk icin RASTGELE (sinyalsiz) barlarin
ortalama ileri getirisi -- gostergenin "piyasa suruklenmesini" mi yoksa
GERCEK bir kenar mi yakaladigini ayirt etmek icin.
"""
from __future__ import annotations

import random
import sys
import time
from pathlib import Path

sys.path.insert(0, r"C:\Users\Samet\Desktop\Teknik Analiz")

import numpy as np
import pandas as pd

from tlab.core.types import Market, Timeframe
from tlab.indicators.bootstrap import CATALOG, scaled_factory

random.seed(7)

DATA_ROOT = Path(r"C:\Users\Samet\Desktop\Teknik Analiz\data\ohlcv\bist")
HORIZONS = [5, 10, 20]
MIN_BARS = 300
N_SYMBOLS = 60

def load_1d(symbol: str) -> pd.DataFrame | None:
    p = DATA_ROOT / symbol / "1D.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    if len(df) < MIN_BARS:
        return None
    return df

all_syms = sorted(d.name for d in DATA_ROOT.iterdir() if d.is_dir() and "." not in d.name)
random.shuffle(all_syms)
symbols: list[str] = []
dfs: dict[str, pd.DataFrame] = {}
for s in all_syms:
    df = load_1d(s)
    if df is not None:
        symbols.append(s)
        dfs[s] = df
    if len(symbols) >= N_SYMBOLS:
        break

print(f"{len(symbols)} sembol yuklendi (min {MIN_BARS} bar sarti).")

targets = [
    name for name, spec in CATALOG.items()
    if not spec.needs_context and not spec.needs_universe
]
print(f"{len(targets)} gosterge olculecek (context/universe haric).")

def fwd_return(df: pd.DataFrame, entry_pos: int, horizon: int, direction: str) -> float | None:
    exit_pos = entry_pos + horizon
    if exit_pos >= len(df):
        return None
    entry_px = float(df["close"].iloc[entry_pos])
    exit_px = float(df["close"].iloc[exit_pos])
    ret = exit_px / entry_px - 1.0
    return ret if direction == "long" else -ret

rows = []
t_start = time.time()
for name in sorted(targets):
    indicator = scaled_factory(name, Timeframe.D1)
    n_sig = 0
    n_long = 0
    n_short = 0
    sig_returns: dict[int, list[float]] = {h: [] for h in HORIZONS}
    base_long: dict[int, list[float]] = {h: [] for h in HORIZONS}
    base_short: dict[int, list[float]] = {h: [] for h in HORIZONS}
    n_err = 0
    for sym in symbols:
        df = dfs[sym]
        try:
            result = indicator(df)
        except Exception:
            n_err += 1
            continue
        idx = df.index
        pos_of = {t: i for i, t in enumerate(idx)}
        for sig in result.signals:
            if sig.state not in ("confirmed", "completed"):
                continue
            if sig.direction not in ("long", "short"):
                continue
            pos = pos_of.get(sig.detected_at)
            if pos is None:
                continue
            n_sig += 1
            n_long += sig.direction == "long"
            n_short += sig.direction == "short"
            for h in HORIZONS:
                r = fwd_return(df, pos, h, sig.direction)
                if r is not None:
                    sig_returns[h].append(r)
        # baz cizgi: bu sembolde 40 rastgele bar -- HEM long HEM short yonunde
        # (yon-eslestirilmis karsilastirma icin, piyasanin genel suruklenmesi
        # tek basina "kenar" gibi gorunmesin diye)
        n_base = min(40, len(idx) - max(HORIZONS) - 1)
        if n_base > 0:
            base_positions = random.sample(range(0, len(idx) - max(HORIZONS) - 1), n_base)
            for p in base_positions:
                for h in HORIZONS:
                    r = fwd_return(df, p, h, "long")
                    if r is not None:
                        base_long[h].append(r)
                        base_short[h].append(-r)

    long_frac = n_long / n_sig if n_sig else None
    row = {"gosterge": name, "n_sinyal": n_sig, "n_long": n_long, "n_short": n_short, "n_hata": n_err}
    for h in HORIZONS:
        rs = sig_returns[h]
        bl, bs_ = base_long[h], base_short[h]
        if rs:
            row[f"ort_{h}b"] = float(np.mean(rs))
            row[f"medyan_{h}b"] = float(np.median(rs))
            row[f"kazanma_{h}b"] = float(np.mean([1.0 if x > 0 else 0.0 for x in rs]))
            row[f"n_{h}b"] = len(rs)
        else:
            row[f"ort_{h}b"] = row[f"medyan_{h}b"] = row[f"kazanma_{h}b"] = None
            row[f"n_{h}b"] = 0
        row[f"baz_long_{h}b"] = float(np.mean(bl)) if bl else None
        row[f"baz_short_{h}b"] = float(np.mean(bs_)) if bs_ else None
        # yon-agirlikli adil baz: sinyallerin long/short karisimiyla AYNI oranda
        if long_frac is not None and bl and bs_:
            fair = long_frac * np.mean(bl) + (1 - long_frac) * np.mean(bs_)
            row[f"baz_adil_{h}b"] = float(fair)
            row[f"fark_{h}b"] = (row[f"ort_{h}b"] - fair) if row[f"ort_{h}b"] is not None else None
        else:
            row[f"baz_adil_{h}b"] = row[f"fark_{h}b"] = None
    rows.append(row)
    print(f"{name:30s} n={n_sig:5d}(L{n_long}/S{n_short}) hata={n_err:3d} "
          f"ort_20b={row['ort_20b']} baz_adil_20b={row['baz_adil_20b']} fark_20b={row['fark_20b']}")

print(f"\nToplam sure: {time.time()-t_start:.1f}s")

out = pd.DataFrame(rows)
out_path = Path(r"C:\Users\Samet\AppData\Local\Temp\claude\C--Users-Samet-Desktop-Teknik-Analiz\2a31625f-8b80-4c7a-93e5-386961cc98c1\scratchpad\olcum_sonuc.csv")
out.to_csv(out_path, index=False)
print(f"Kaydedildi: {out_path}")
