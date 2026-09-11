import sys
sys.path.insert(0, r"C:\Users\Samet\Desktop\Teknik Analiz")
import pandas as pd
from pathlib import Path
from tlab.core.types import Timeframe
from tlab.indicators.bootstrap import scaled_factory

DATA_ROOT = Path(r"C:\Users\Samet\Desktop\Teknik Analiz\data\ohlcv\bist")
HORIZON = 20
MIN_BARS = 300
IS_FRACTION = 0.70

all_syms = sorted(d.name for d in DATA_ROOT.iterdir() if d.is_dir() and "." not in d.name)
dfs = {}
for s in all_syms:
    p = DATA_ROOT / s / "1D.parquet"
    if not p.exists():
        continue
    df = pd.read_parquet(p)
    if len(df) < MIN_BARS:
        continue
    dfs[s] = df

def fwd_return(df, entry_pos, horizon, direction):
    exit_pos = entry_pos + horizon
    if exit_pos >= len(df):
        return None
    entry_px = float(df["close"].iloc[entry_pos])
    exit_px = float(df["close"].iloc[exit_pos])
    ret = exit_px / entry_px - 1.0
    return ret if direction == "long" else -ret

for name in ["patterns.wedge", "patterns.broadening", "harmonic.five_zero"]:
    indicator = scaled_factory(name, Timeframe.D1)
    records = []
    for sym, df in dfs.items():
        n = len(df)
        split_pos = int(n * IS_FRACTION)
        split_time = df.index[split_pos]
        try:
            result = indicator(df)
        except Exception:
            continue
        idx = df.index
        for sig in result.signals:
            if sig.state not in ("confirmed", "completed"):
                continue
            if sig.direction not in ("long", "short"):
                continue
            if sig.detected_at < split_time:
                continue
            pos = idx.get_indexer([sig.detected_at])[0]
            if pos < 0:
                continue
            r = fwd_return(df, pos, HORIZON, sig.direction)
            if r is None:
                continue
            records.append({"sembol": sym, "tarih": sig.detected_at, "yon": sig.direction, "getiri": r})
    rec = pd.DataFrame(records)
    print(f"=== {name} (n={len(rec)}) ===")
    print(rec.sort_values("getiri", ascending=False).to_string(index=False))
    print(f"ortalama: {rec['getiri'].mean():.4f}  medyan: {rec['getiri'].median():.4f}")
    print()
