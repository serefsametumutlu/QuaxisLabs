"""Zigzag yontemine gore pivot yogunlugu olcumu.

Sistemdeki HER formasyon tek bir zigzag uzerine kurulu:
find_pivots(df, left=3, right=3) -> alternate_pivots(...). Bu betik o
varsayilanin ne kadar gurultulu oldugunu, alternatiflerle yan yana olcer.

Bkz. docs/STRATEJI_DENETIM_TAM.md bolum A1.

2026-09-03 sonuclari (sentetik 4H serisi, n=1000, seed=7):
    find_pivots(3,3)  [VARSAYILAN] : 100 barda 14.5 pivot, ort. bacak  6.9 bar
    find_pivots(5,5)               : 100 barda  9.1 pivot, ort. bacak 10.8 bar
    find_pivots(10,10)             : 100 barda  4.8 pivot, ort. bacak 19.7 bar
    atr_zigzag(mult=2.0)           : 100 barda  9.2 pivot, ort. bacak 10.7 bar
    atr_zigzag(mult=3.0)           : 100 barda  4.3 pivot, ort. bacak 23.0 bar

4H'te 7 barlik bir bacak BIR GUNDEN KISA -- sistemin "swing" dedigi sey bir
gunluk dalgalanma. Formasyonlarin gurultulu gorunmesinin kok nedeni bu.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tlab.features.swings import alternate_pivots, atr_zigzag, find_pivots  # noqa: E402


def synth_ohlcv(n: int, seed: int = 7, vol: float = 0.018) -> pd.DataFrame:
    """Sentetik ama gercekci 4H OHLCV -- olcum tekrarlanabilir olsun diye
    sabit tohumlu (gercek veriye bagimlilik YOK)."""
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0.0003, vol, n)))
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, vol * 0.4, n)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, vol * 0.4, n)))
    index = pd.date_range("2024-01-01", periods=n, freq="4h", tz="Europe/Istanbul")
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": np.full(n, 1e6)},
        index=index,
    )


def main() -> int:
    header = (
        f"{'yontem':36s} {'ham':>6s} {'zigzag':>7s} {'100 barda':>10s} "
        f"{'ort.bacak(bar)':>15s} {'ort.bacak(%)':>13s}"
    )
    for n in (500, 1000):
        df = synth_ohlcv(n)
        print(f"\n--- n={n} bar (4H) ---")
        print(header)
        print("-" * len(header))
        methods = [
            ("find_pivots(3,3)  [VARSAYILAN]", find_pivots(df, 3, 3)),
            ("find_pivots(5,5)", find_pivots(df, 5, 5)),
            ("find_pivots(10,10)", find_pivots(df, 10, 10)),
            ("atr_zigzag(mult=2.0)", atr_zigzag(df, 2.0, 14)),
            ("atr_zigzag(mult=3.0)", atr_zigzag(df, 3.0, 14)),
        ]
        for name, pivots in methods:
            zz = alternate_pivots(pivots)
            if len(zz) < 2:
                continue
            legs_bar = [zz[i + 1].bar_idx - zz[i].bar_idx for i in range(len(zz) - 1)]
            legs_pct = [
                abs(zz[i + 1].price - zz[i].price) / zz[i].price * 100 for i in range(len(zz) - 1)
            ]
            print(
                f"{name:36s} {len(pivots):6d} {len(zz):7d} {len(zz) / n * 100:10.1f} "
                f"{np.mean(legs_bar):15.1f} {np.mean(legs_pct):12.2f}%"
            )
    print(
        "\nNOT: atr_zigzag OLCEK BAGIMSIZDIR (ATR kati kadar ters donus ister) --"
        "\n     4H'te ve 1D'de ayni ekonomik anlami tasir. find_pivots(left,right)"
        "\n     ise ham bar sayar, bu yuzden zaman dilimine gore anlami degisir."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
