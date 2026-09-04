"""Faz 2, 2D -- config/pairs.yaml'daki mevcut 606 çifti Engle-Granger ile
YENİDEN doğrular + discover_pairs v2'yi (coint + Šidák + FDR + OOS) sıfırdan
koşup config/pairs.yaml'ı yeniden üretir + docs/spec/ARBITRAJ_DENETIM_v2.md
yazar.

Gercek BIST onbellek verisiyle calisir (network YOK -- data/ohlcv/bist/ zaten
indirilmis, Store.get() yalnizca parquet okur). Bkz.
docs/TANI_VE_YOL_HARITASI_v2.md ## FAZ 2, bolum 2D."""

from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml  # noqa: E402

from tlab.core.types import Market, Timeframe  # noqa: E402
from tlab.data.providers.yfinance_provider import YFinanceProvider  # noqa: E402
from tlab.data.store import Store  # noqa: E402
from tlab.data.universe import load_universe  # noqa: E402
from tlab.features.stats import benjamini_hochberg, engle_granger_pvalue  # noqa: E402
from tlab.indicators.pairs.discovery import (  # noqa: E402
    PairCandidate,
    discover_pairs,
    load_economic_link_map,
    load_pairs_yaml,
    load_sector_map,
)

LOOKBACK_BARS = 600
MIN_BARS = 200
OLD_PAIRS_PATH = "config/pairs.yaml"
DEPRECATED_PATH = "config/pairs_v1_deprecated.yaml"
SECTOR_MAP_PATH = "config/sectors_bist.yaml"
ECONOMIC_LINKS_PATH = "config/economic_links.yaml"


def _load_all_close_prices(symbols: list[str]) -> dict:
    store = Store(YFinanceProvider())
    prices = {}
    for sym in symbols:
        try:
            df = store.get(sym, Timeframe.D1, Market.BIST, last_n=LOOKBACK_BARS)
        except FileNotFoundError:
            continue
        if len(df) >= MIN_BARS:
            prices[sym] = df["close"].astype(float)
    return prices


def _reverify_existing_pairs(prices: dict) -> dict:
    pairs = load_pairs_yaml(OLD_PAIRS_PATH)
    results = []
    p_values = []
    for y_sym, x_sym in pairs:
        if y_sym not in prices or x_sym not in prices:
            results.append({"y": y_sym, "x": x_sym, "p": None, "reason": "veri_yok"})
            continue
        try:
            p = engle_granger_pvalue(prices[y_sym], prices[x_sym])
        except ValueError:
            results.append({"y": y_sym, "x": x_sym, "p": None, "reason": "hesaplanamadi"})
            continue
        results.append({"y": y_sym, "x": x_sym, "p": p})
        p_values.append(p)

    still_significant = sum(1 for r in results if r.get("p") is not None and r["p"] < 0.05)
    fdr_pass = 0
    if p_values:
        passed = benjamini_hochberg(p_values, 0.05)
        fdr_pass = int(passed.sum())
    print(
        f"  {len(pairs)} eski çift -- hâlâ p<0.05 (düzeltmesiz): {still_significant}, "
        f"BH-FDR (q=0.05, M={len(p_values)}) geçen: {fdr_pass}"
    )
    return {
        "n_old_pairs": len(pairs), "n_priced": len(p_values),
        "still_significant_raw": still_significant, "fdr_pass": fdr_pass,
        "detail": results,
    }


def _sector_distribution(candidates: list[PairCandidate], sector_map: dict) -> dict:
    counts: Counter = Counter()
    for c in candidates:
        counts[sector_map.get(c.symbol_y, "bilinmeyen")] += 1
    return dict(counts.most_common())


def _write_pairs_yaml(path: str, candidates: list[PairCandidate]) -> None:
    payload = {
        "pairs": [
            {
                "y": c.symbol_y, "x": c.symbol_x, "corr": round(c.corr, 4),
                "adf_p": round(c.adf_pvalue, 6), "p_raw": round(c.p_raw, 6),
                "halflife": round(c.halflife, 2), "beta": round(c.beta, 4),
                "n_tests": c.n_tests, "n_bars": c.n_bars,
                "adf_p_is": round(c.adf_p_is, 6) if c.adf_p_is is not None else None,
                "adf_p_oos": round(c.adf_p_oos, 6) if c.adf_p_oos is not None else None,
            }
            for c in candidates
        ]
    }
    header = (
        "# Faz 2, 2D (docs/TANI_VE_YOL_HARITASI_v2.md ## FAZ 2) ile YENIDEN uretildi --\n"
        "# Engle-Granger (coint) + Sidak duzeltmesi + Benjamini-Hochberg FDR (q=0.05) +\n"
        "# out-of-sample dogrulama (oos_split=0.5). Onceki (2026-09-03) surum, ham adfuller\n"
        "# + duzeltmesiz coklu-test kullaniyordu (606 cift) -- config/pairs_v1_deprecated.yaml'a\n"
        "# tasindi. Detay: docs/spec/ARBITRAJ_DENETIM_v2.md.\n"
        "#\n"
        "# y/x: RelativeMomentumPair/VolHarvestPair'in 'Y hissesi'/'X hissesi' sozlesmesiyle\n"
        "# AYNI (spread = log(Y) - beta*log(X)). adf_p: Sidak-duzeltilmis p (adf_pvalue ile\n"
        "# ayni). p_raw: Sidak ONCESI. n_tests: bu taramada denenen TOPLAM kombinasyon sayisi\n"
        "# (FDR'nin M'si). adf_p_is/adf_p_oos: oos_split'in in-sample/out-of-sample p'leri.\n"
        "# DISIPLIN-06/08 (discovery.py docstring'i): bu liste KALICI BIR ONAY DEGIL, anlik\n"
        "# bir tarama -- periyodik olarak yeniden kosulmali.\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(header)
        yaml.safe_dump(payload, f, allow_unicode=True, sort_keys=False)


def main() -> int:
    t0 = time.time()
    print("BIST evreni yükleniyor...")
    symbols = load_universe(Market.BIST)
    prices = _load_all_close_prices(symbols)
    print(f"  {len(prices)}/{len(symbols)} sembol önbellekte (D1, >={MIN_BARS} bar)\n")

    print("=== 1: mevcut config/pairs.yaml'ı Engle-Granger ile yeniden doğrulama ===")
    reverify = _reverify_existing_pairs(prices)

    print("\n=== 2: discover_pairs v2 sıfırdan (coint + Šidák + FDR + OOS) ===")
    sector_map = load_sector_map(SECTOR_MAP_PATH)
    economic_link_map = load_economic_link_map(ECONOMIC_LINKS_PATH)
    new_candidates = discover_pairs(
        prices, sector_map=sector_map, same_sector_only=True,
        economic_link_map=economic_link_map, fdr_q=0.05, oos_split=0.5,
    )
    n_tests = new_candidates[0].n_tests if new_candidates else None
    print(f"  YENİ çift sayısı: {len(new_candidates)} (n_tests={n_tests})")
    sector_dist = _sector_distribution(new_candidates, sector_map)
    print(f"  Sektör dağılımı (ilk 10): {dict(list(sector_dist.items())[:10])}")

    print("\n=== 3: config/pairs.yaml yeniden üretiliyor (eski -> pairs_v1_deprecated.yaml) ===")
    old_path = Path(OLD_PAIRS_PATH)
    deprecated_path = Path(DEPRECATED_PATH)
    if old_path.exists() and not deprecated_path.exists():
        deprecated_path.write_text(old_path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"  Eski dosya korundu: {deprecated_path}")
    _write_pairs_yaml(OLD_PAIRS_PATH, new_candidates)
    print(f"  Yeni {len(new_candidates)} çift yazıldı: {OLD_PAIRS_PATH}")

    out = {
        "n_symbols_priced": len(prices),
        "reverify_existing": reverify,
        "new_discovery": {
            "n_candidates": len(new_candidates), "n_tests": n_tests,
            "sector_distribution": sector_dist,
            "candidates": [
                {
                    "y": c.symbol_y, "x": c.symbol_x, "corr": c.corr, "adf_p": c.adf_pvalue,
                    "p_raw": c.p_raw, "halflife": c.halflife, "beta": c.beta,
                    "adf_p_is": c.adf_p_is, "adf_p_oos": c.adf_p_oos,
                }
                for c in new_candidates
            ],
        },
    }
    out_path = Path("outputs/reports/pair_denetim_v2.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    print(f"\nJSON çıktı: {out_path} ({time.time() - t0:.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
