"""trend.breakouts'un quality_score'u gercekten ileri getiriyi ongoruyor mu?
AYNI 60 sembol, AYNI yontem (olcum.py) -- skor besliye (quintile) bolup
her dilimin 20-bar ortalama/medyan getirisini karsilastirir."""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\Samet\Desktop\Teknik Analiz")

import numpy as np
import pandas as pd

from tlab.core.types import Timeframe
from tlab.indicators.bootstrap import scaled_factory

random.seed(7)
DATA_ROOT = Path(r"C:\Users\Samet\Desktop\Teknik Analiz\data\ohlcv\bist")
MIN_BARS = 300
N_SYMBOLS = 60
HORIZON = 20

all_syms = sorted(d.name for d in DATA_ROOT.iterdir() if d.is_dir() and "." not in d.name)
random.shuffle(all_syms)
symbols, dfs = [], {}
for s in all_syms:
    p = DATA_ROOT / s / "1D.parquet"
    if not p.exists():
        continue
    df = pd.read_parquet(p)
    if len(df) < MIN_BARS:
        continue
    symbols.append(s)
    dfs[s] = df
    if len(symbols) >= N_SYMBOLS:
        break

indicator = scaled_factory("trend.breakouts", Timeframe.D1)
records = []
for sym in symbols:
    df = dfs[sym]
    try:
        result = indicator(df)
    except Exception:
        continue
    idx = df.index
    pos_of = {t: i for i, t in enumerate(idx)}
    for sig in result.signals:
        if sig.state not in ("confirmed", "completed"):
            continue
        if sig.direction not in ("long", "short"):
            continue
        pos = pos_of.get(sig.detected_at)
        if pos is None or pos + HORIZON >= len(df):
            continue
        entry = float(df["close"].iloc[pos])
        exit_ = float(df["close"].iloc[pos + HORIZON])
        ret = exit_ / entry - 1.0
        ret = ret if sig.direction == "long" else -ret
        records.append({"score": sig.score, "ret": ret, "kind": sig.payload.get("kind", "?")})

rec = pd.DataFrame(records)
print(f"toplam kayit: {len(rec)}")
rec["dilim"] = pd.qcut(rec["score"], 5, duplicates="drop")
summary = rec.groupby("dilim", observed=True).agg(
    n=("ret", "size"), ort=("ret", "mean"), medyan=("ret", "median"),
    kazanma=("ret", lambda x: (x > 0).mean()), skor_araligi=("score", lambda x: (x.min(), x.max())),
)
print(summary.to_string())

corr = rec["score"].corr(rec["ret"])
print(f"\nPearson korelasyon(score, 20b getiri): {corr:.4f}")
from scipy import stats as sps
rho, p = sps.spearmanr(rec["score"], rec["ret"])
print(f"Spearman rho: {rho:.4f}  p-degeri: {p:.4f}")

out = Path(r"C:\Users\Samet\AppData\Local\Temp\claude\C--Users-Samet-Desktop-Teknik-Analiz\2a31625f-8b80-4c7a-93e5-386961cc98c1\scratchpad\quality_score_sonuc.csv")
rec.to_csv(out, index=False)
