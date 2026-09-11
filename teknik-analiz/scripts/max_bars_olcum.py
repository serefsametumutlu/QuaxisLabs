"""wedge/triangle/broadening'in confirmed/completed adaylarinin span'ini
(baslangic pivotundan olusum barina kadar bar sayisi) gercek 60-sembol
orneklemde olcer -- max_bars varsayilani icin karar verisi."""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\Samet\Desktop\Teknik Analiz")

import pandas as pd

from tlab.core.types import Timeframe
from tlab.indicators.bootstrap import scaled_factory

random.seed(7)
DATA_ROOT = Path(r"C:\Users\Samet\Desktop\Teknik Analiz\data\ohlcv\bist")
MIN_BARS = 300
N_SYMBOLS = 60

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

def pos_of(df, t):
    ts = pd.Timestamp(t)
    try:
        return int(df.index.get_loc(ts))
    except KeyError:
        return None

spans = []
for indicator_name in ["patterns.wedge", "patterns.triangle", "patterns.broadening"]:
    indicator = scaled_factory(indicator_name, Timeframe.D1)
    for sym in symbols:
        df = dfs[sym]
        try:
            result = indicator(df)
        except Exception:
            continue
        for pid, st in result.last_state.items():
            if st.get("state") not in ("confirmed", "completed"):
                continue
            key = pid.rsplit("_", 1)[0]
            line_spans = []
            for side in ("upper", "lower"):
                line = next((ln for ln in result.lines if ln.label == f"{key}_{side}"), None)
                if line is None:
                    continue
                i0 = pos_of(df, line.points[0][0])
                i1 = pos_of(df, line.points[-1][0])
                if i0 is not None and i1 is not None:
                    line_spans.append(abs(i1 - i0))
            if line_spans:
                spans.append({
                    "gosterge": indicator_name, "sembol": sym, "pattern_id": pid,
                    "span_bar": max(line_spans),
                })

sp = pd.DataFrame(spans)
print(f"toplam confirmed/completed aday: {len(sp)}")
print(sp.groupby("gosterge")["span_bar"].describe())
print()
for th in [60, 90, 120, 150, 180, 220, 250, 300, 0]:
    if th == 0:
        n = len(sp)
        label = "sinirsiz"
    else:
        n = (sp["span_bar"] <= th).sum()
        label = str(th)
    print(f"max_bars={label:10s} -> kalan aday: {n} / {len(sp)} (%{100*n/len(sp):.1f})")

out = Path(r"C:\Users\Samet\AppData\Local\Temp\claude\C--Users-Samet-Desktop-Teknik-Analiz\2a31625f-8b80-4c7a-93e5-386961cc98c1\scratchpad\max_bars_sonuc.csv")
sp.to_csv(out, index=False)
print(f"\nkaydedildi: {out}")
