"""patterns.breakout_fvg'nin konsolidasyon-kutusu genislik/ATR oraninin
(box_atr_max esigi) gercek dagilimini D1 ve 4H icin AYRI AYRI olcer.

Kok neden (docs/KALAN_ISLER.md madde 3): `consolidation_bars` _BAR_FIELDS'te
(D1'den 4H'e x3 olcekleniyor, 10->30) ama `box_atr_max` (bir ORAN, bar sayisi
DEGIL) SABIT kaliyor -- 30-bar bir pencerenin genisligi, atr_period=14'un
(SABIT kalan) ATR'sine gore D1'deki 10-bar pencereden CIDDI olcude daha
buyuk cikiyor, bu yuzden AYNI mutlak esik (1.5) 4H'te MATEMATIKSEL olarak
ulasilamaz hale geliyordu (648 sembollik gercek tlab eod kosusunda
dogrulandi: patterns.breakout_fvg 4H = 0/648 aday)."""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from tlab.features.volatility import atr

random.seed(3)
DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "ohlcv" / "bist"
N_SYMBOLS = 80


def ratios(df: pd.DataFrame, window_bars: int, atr_period: int = 14) -> list[float]:
    a = atr(df, atr_period).to_numpy()
    high, low = df["high"].to_numpy(), df["low"].to_numpy()
    out = []
    for i in range(window_bars - 1, len(df), 5):
        if a[i] > 0 and a[i] == a[i]:  # not NaN
            out.append((high[i - window_bars + 1 : i + 1].max()
                         - low[i - window_bars + 1 : i + 1].min()) / a[i])
    return out


def main() -> None:
    all_syms = sorted(d.name for d in DATA_ROOT.iterdir() if d.is_dir() and "." not in d.name)
    random.shuffle(all_syms)
    d1_ratios: list[float] = []
    h4_ratios: list[float] = []
    used = 0
    for sym in all_syms:
        p1, p4 = DATA_ROOT / sym / "1D.parquet", DATA_ROOT / sym / "4H.parquet"
        if not p1.exists() or not p4.exists():
            continue
        df1, df4 = pd.read_parquet(p1), pd.read_parquet(p4)
        if len(df1) < 100 or len(df4) < 100:
            continue
        used += 1
        d1_ratios.extend(ratios(df1, 10))
        h4_ratios.extend(ratios(df4, 30))
        if used >= N_SYMBOLS:
            break

    d1 = pd.Series(d1_ratios)
    h4 = pd.Series(h4_ratios)
    print(f"sembol: {used}")
    print(f"D1 n={len(d1)} quantiles:\n{d1.quantile([0.001, 0.004, 0.01, 0.02, 0.05])}")
    print(f"\n4H n={len(h4)} quantiles:\n{h4.quantile([0.001, 0.004, 0.01, 0.02, 0.05])}")


if __name__ == "__main__":
    main()
