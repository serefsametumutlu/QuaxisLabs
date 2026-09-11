"""patterns.flag_pennant'in direklerinin (`pole_pct`) gercek BIST evrenindeki
dagilimini olcer -- `FlagPennantParams.htf_pct` (High and Tight Flag esigi)
icin karar verisi. `find_impulses`in SABIT `pole_bars` (varsayilan 5)
penceresi yuzunden Bulkowski'nin ham %90'i bu sistemde fiilen imkansiza
yakin -- esik bu dagilimin ust yuzdelik dilimine gore empirik kalibre
edilmeli. docs/KALAN_ISLER.md madde 2.3."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from tlab.core.types import Timeframe
from tlab.indicators.bootstrap import scaled_factory

DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "ohlcv" / "bist"
MIN_BARS = 300


def main() -> None:
    all_syms = sorted(d.name for d in DATA_ROOT.iterdir() if d.is_dir() and "." not in d.name)
    indicator = scaled_factory("patterns.flag_pennant", Timeframe.D1)
    pcts: list[float] = []
    htf_found: list[tuple[str, str, str, str]] = []

    for sym in all_syms:
        p = DATA_ROOT / sym / "1D.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        if len(df) < MIN_BARS:
            continue
        try:
            result = indicator(df)
        except Exception:
            continue
        seen: set[str] = set()
        for sig in result.signals:
            pid = sig.payload.get("pattern_id")
            if pid is None or pid in seen:
                continue
            seen.add(pid)
            pct = sig.payload.get("pole_pct")
            if pct is not None:
                pcts.append(pct)
        for pid, st in result.last_state.items():
            if st.get("is_htf"):
                htf_found.append((sym, pid, st.get("state", ""), st.get("direction", "")))

    s = pd.Series(pcts)
    print(f"toplam direk: {len(s)}")
    print(s.describe())
    print("yuzdelik dilimler:")
    print(s.quantile([0.5, 0.75, 0.9, 0.95, 0.99, 0.999]))
    print(f"\nis_htf=True aday sayisi (mevcut htf_pct ile): {len(htf_found)}")
    for row in htf_found[:20]:
        print(row)


if __name__ == "__main__":
    main()
