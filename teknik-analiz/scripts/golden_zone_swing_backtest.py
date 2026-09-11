"""golden_zone.py'nin 'hangi swing guncel bolgeyi tanimlar' kararini
(madde 2.2) BACKTEST ile cozer: swing BUYUKLUGU (|fiyat acikligi|/ATR)
ile o swing'in altin bolgesinin GERCEK SONUCU (reaction+success vs fail)
arasinda iliski var mi? Varsa 'baskin' (buyuk swing) daha iyi -- yoksa
'en yeni' (kodun mevcut varsayilani, basit) kalabilir."""
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\Samet\Desktop\Teknik Analiz")

import random
import pandas as pd
import numpy as np

from tlab.core.types import Timeframe
from tlab.indicators.bootstrap import scaled_factory
from tlab.features.volatility import atr

random.seed(11)
DATA_ROOT = Path(r"C:\Users\Samet\Desktop\Teknik Analiz\data\ohlcv\bist")
N_SYMBOLS = 150
MIN_BARS = 300

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
print(f"{len(symbols)} sembol yuklendi.")

ind = scaled_factory("structure.golden_zone", Timeframe.D1)
rows = []
for sym in symbols:
    df = dfs[sym]
    try:
        result = ind(df)
    except Exception:
        continue
    a = atr(df, 14)
    lines_by_swing = {}
    for ln in result.lines:
        if ln.label.startswith("swing_"):
            sid = int(ln.label.split("_")[1])
            (t0, p0), (t1, p1) = ln.points[0], ln.points[-1]
            lines_by_swing[sid] = (t0, p0, t1, p1)

    # her swing_id icin: son (en ileri) olay -> nihai sonuc
    outcomes: dict[int, str] = {}
    for sig in result.signals:
        sid = sig.payload.get("swing_id")
        ev = sig.payload.get("event")
        if sid is None or ev is None:
            continue
        if ev.endswith("_success"):
            outcomes[sid] = "success"
        elif ev.endswith("_fail"):
            outcomes[sid] = "fail"
        elif ev.endswith("_reaction") and outcomes.get(sid) != "success":
            outcomes[sid] = "reaction_no_confirm"
        elif ev.endswith("_touch") and sid not in outcomes:
            outcomes[sid] = "touched_no_reaction"

    for sid, (t0, p0, t1, p1) in lines_by_swing.items():
        outcome = outcomes.get(sid, "no_touch")
        try:
            atr_at = a.loc[t1]
        except KeyError:
            continue
        if pd.isna(atr_at) or atr_at <= 0:
            continue
        span_pct = abs(p1 - p0) / p0 if p0 else np.nan
        span_atr = abs(p1 - p0) / atr_at
        rows.append({
            "sembol": sym, "swing_id": sid, "span_pct": span_pct,
            "span_atr": span_atr, "outcome": outcome,
        })

rec = pd.DataFrame(rows)
print(f"toplam swing: {len(rec)}")
print(rec["outcome"].value_counts())

# basari/basarisizlik oranini swing buyuklugu (span_atr) yuzdelik dilimine gore incele
rec = rec[rec["outcome"].isin(["success", "fail", "reaction_no_confirm", "touched_no_reaction"])]
rec["good"] = rec["outcome"].isin(["success", "reaction_no_confirm"]).astype(int)
rec["dilim"] = pd.qcut(rec["span_atr"], 5, duplicates="drop")
summary = rec.groupby("dilim", observed=True).agg(
    n=("good", "size"), basari_orani=("good", "mean"),
    span_atr_araligi=("span_atr", lambda x: (round(x.min(), 2), round(x.max(), 2))),
)
print(summary.to_string())

from scipy import stats as sps
rho, p = sps.spearmanr(rec["span_atr"], rec["good"])
print(f"\nSpearman(span_atr, basari) rho={rho:.4f} p={p:.4f}")

# ayrica: EN BASKIN (sembol icindeki en buyuk span_atr'li) swing'lerin
# basari orani vs DIGER (baskin olmayan) swing'lerin basari orani
rec["is_dominant"] = rec.groupby("sembol")["span_atr"].transform(lambda x: x == x.max())
print("\nEn baskin swing basari orani:", rec[rec["is_dominant"]]["good"].mean(),
      "n=", rec["is_dominant"].sum())
print("Baskin OLMAYAN swing basari orani:", rec[~rec["is_dominant"]]["good"].mean(),
      "n=", (~rec["is_dominant"]).sum())

# en yeni (sembol icinde en son/en yuksek swing_id) swing'lerin basari orani
rec["is_latest"] = rec.groupby("sembol")["swing_id"].transform(lambda x: x == x.max())
print("\nEn yeni swing basari orani:", rec[rec["is_latest"]]["good"].mean(),
      "n=", rec["is_latest"].sum())
print("Yeni OLMAYAN swing basari orani:", rec[~rec["is_latest"]]["good"].mean(),
      "n=", (~rec["is_latest"]).sum())

out = Path(r"C:\Users\Samet\AppData\Local\Temp\claude\C--Users-Samet-Desktop-Teknik-Analiz\2a31625f-8b80-4c7a-93e5-386961cc98c1\scratchpad\golden_zone_swing_backtest.csv")
rec.to_csv(out, index=False)
print(f"\nkaydedildi: {out}")
