"""config/pairs.yaml'daki cift listesine Benjamini-Hochberg FDR uygular.

Mevcut liste (606 cift) `p < 0.05` esigiyle, HICBIR coklu-test duzeltmesi
olmadan uretildi. 8754 sektor-ici kombinasyon test edildigi icin bu esik
tek basina anlamsizdir.

Bkz. docs/TANI_VE_YOL_HARITASI_v2.md bolum 1.4(d).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import yaml


def sector_pair_count(path: Path) -> int:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return sum(
        len(v or []) * (len(v or []) - 1) // 2
        for v in raw.get("sectors", {}).values()
    )


def benjamini_hochberg(pvalues: np.ndarray, q: float, m: int) -> int:
    """m testten kac tanesi FDR q seviyesinde hayatta kalir."""
    srt = np.sort(pvalues)
    survivors = 0
    for i, p in enumerate(srt, start=1):
        if p <= (i / m) * q:
            survivors = i
    return survivors


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    pairs_path = root / "config" / "pairs.yaml"
    sectors_path = root / "config" / "sectors_bist.yaml"

    pairs = (yaml.safe_load(pairs_path.read_text(encoding="utf-8")) or {}).get("pairs", [])
    adf = np.array([p["adf_p"] for p in pairs if "adf_p" in p])
    m = sector_pair_count(sectors_path)

    print(f"Kayitli cift            : {len(pairs)}")
    print(f"adf_p tasiyan           : {len(adf)}")
    print(f"Test edilen kombinasyon : {m} (sektor-ici, tum ikili)")
    print(f"Ham kesif orani         : {len(adf) / m:.1%}")
    print()
    print("Coklu-test duzeltmesi sonrasi hayatta kalan cift:")
    for q in (0.20, 0.10, 0.05):
        print(f"  BH-FDR q={q:<5.2f} -> {benjamini_hochberg(adf, q, m):>4d}")
    print(f"  Bonferroni      -> {int((adf < 0.05 / m).sum()):>4d}  (alpha=0.05/{m})")
    print()
    print("NOT: bu p-degerleri hala ham adfuller'dan geliyor (~3 kat sisirilmis).")
    print("     statsmodels.tsa.stattools.coint ile yeniden hesaplaninca daha da dusecek.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
