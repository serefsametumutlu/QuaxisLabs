"""docs/KALAN_ISLER.md madde 3 -- gercek BIST evreninde gosterge basina
aday (pattern_id / son durum) sayisi. Sifira yakin olanlar ya cok dar
parametreli ya da bozuk bir tespit edicidir; bu script sadece SAYAR,
kok neden arastirmasi ayrica yapilir."""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from tlab.core.types import Timeframe
from tlab.indicators.bootstrap import CATALOG, scaled_factory

DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "ohlcv" / "bist"
MIN_BARS = 300
N_SYMBOLS = 200


def main() -> None:
    all_syms = sorted(d.name for d in DATA_ROOT.iterdir() if d.is_dir() and "." not in d.name)
    symbols: list[str] = []
    dfs: dict[str, pd.DataFrame] = {}
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

    targets = [
        name for name, spec in CATALOG.items()
        if not spec.needs_context and not spec.needs_universe
    ]
    rows = []
    t0 = time.time()
    for name in sorted(targets):
        indicator = scaled_factory(name, Timeframe.D1)
        n_candidates = 0
        n_symbols_with_any = 0
        n_confirmed_completed = 0
        n_err = 0
        for sym in symbols:
            df = dfs[sym]
            try:
                result = indicator(df)
            except Exception:
                n_err += 1
                continue
            if not result.last_state:
                continue
            # structure.golden_zone/supply_demand vb. bazi gostergeler
            # last_state'i pattern_id basina bir sozluk DEGIL, TEK bir DUZ
            # sozluk (band_low/in_band gibi skaler alanlar) olarak tutuyor --
            # deger tipine bakarak ayirt edilir.
            is_per_pattern = all(isinstance(v, dict) for v in result.last_state.values())
            if is_per_pattern:
                n_candidates += len(result.last_state)
                n_symbols_with_any += 1
                n_confirmed_completed += sum(
                    1 for st in result.last_state.values()
                    if st.get("state") in ("confirmed", "completed")
                )
        rows.append({
            "gosterge": name, "n_aday_toplam": n_candidates,
            "n_sembol_en_az_1_aday": n_symbols_with_any,
            "n_confirmed_completed": n_confirmed_completed,
            "n_sembol": len(symbols), "n_hata": n_err,
        })
        print(f"{name:30s} aday={n_candidates:6d}  sembol_kapsayan={n_symbols_with_any:4d}/"
              f"{len(symbols)}  confirmed/completed={n_confirmed_completed:6d}  hata={n_err}")

    print(f"\nsure: {time.time()-t0:.1f}s")
    out = pd.DataFrame(rows).sort_values("n_aday_toplam")
    out_path = Path(__file__).resolve().parents[1] / "outputs" / "reports" / (
        "aday_sayisi_sayimi_2026-09-11.csv"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    print(f"kaydedildi: {out_path}")
    print("\n=== EN DAR (aday sayisina gore) 10 gosterge ===")
    print(out.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
