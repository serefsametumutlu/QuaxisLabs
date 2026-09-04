"""`config/pairs.yaml`'ı sıfırdan yeniden üretir -- `scripts/pair_denetim.py`
(CLI) VE `web/backend/routes/pairs_refresh.py` (web butonu) AYNI
`refresh_pairs_yaml()`'ı çağırır, mantık iki yerde ayrı yazılmaz.

2026-09-04 kullanıcı isteği: `config/pairs.yaml`nin kendi notu zaten "KALICI
BİR ONAY DEĞİL, periyodik olarak yeniden koşulmalı" diyor -- ama bu yeniden
koşma elle (`python scripts/pair_denetim.py`) yapılıyordu. Kullanıcı bunun
yerine web arayüzünde, her tarama öncesi basabileceği bir buton istedi --
böylece yeni cointegre olan bir çift (ör. GARAN/AKBNK) bir sonraki
yenilemede otomatik listeye girer, elle tetiklemek zorunda kalmaz."""

from __future__ import annotations

from pathlib import Path

import yaml

from tlab.core.types import Market, Timeframe
from tlab.data.providers.yfinance_provider import YFinanceProvider
from tlab.data.store import Store
from tlab.data.universe import load_universe
from tlab.indicators.pairs.discovery import (
    PairCandidate,
    discover_pairs,
    load_economic_link_map,
    load_sector_map,
)

LOOKBACK_BARS = 600
MIN_BARS = 200
SECTOR_MAP_PATH = "config/sectors_bist.yaml"
ECONOMIC_LINKS_PATH = "config/economic_links.yaml"
# 2026-09-04 kullanıcı kararı (bkz. docs/spec/ARBITRAJ_DENETIM_v2.md) --
# scripts/pair_denetim.py'nin varsayılanıyla AYNI.
FDR_Q = 0.05
OOS_SPLIT: float | None = None


def load_all_close_prices(
    symbols: list[str], *, lookback_bars: int = LOOKBACK_BARS, min_bars: int = MIN_BARS,
) -> dict[str, object]:
    store = Store(YFinanceProvider())
    prices = {}
    for sym in symbols:
        try:
            df = store.get(sym, Timeframe.D1, Market.BIST, last_n=lookback_bars)
        except FileNotFoundError:
            continue
        if len(df) >= min_bars:
            prices[sym] = df["close"].astype(float)
    return prices


def write_pairs_yaml(
    path: str, candidates: list[PairCandidate], fdr_q: float | None, oos_split: float | None,
) -> None:
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
    oos_desc = f"oos_split={oos_split}" if oos_split is not None else "oos_split=None (KAPALI)"
    fdr_desc = f"fdr_q={fdr_q}" if fdr_q is not None else "fdr_q=None (KAPALI)"
    header = (
        "# Faz 2, 2D (docs/TANI_VE_YOL_HARITASI_v2.md ## FAZ 2) ile YENIDEN uretildi --\n"
        f"# Engle-Granger (coint) + Sidak duzeltmesi + Benjamini-Hochberg FDR ({fdr_desc}) +\n"
        f"# out-of-sample dogrulama ({oos_desc}). Detay + elenme sebebi dagilimi:\n"
        "# docs/spec/ARBITRAJ_DENETIM_v2.md.\n"
        "#\n"
        "# y/x: RelativeMomentumPair/VolHarvestPair'in 'Y hissesi'/'X hissesi' sozlesmesiyle\n"
        "# AYNI (spread = log(Y) - beta*log(X)). adf_p: Sidak-duzeltilmis p (adf_pvalue ile\n"
        "# ayni). p_raw: Sidak ONCESI. n_tests: bu taramada denenen TOPLAM kombinasyon sayisi\n"
        "# (FDR'nin M'si). adf_p_is/adf_p_oos: oos_split kullanilmadiysa HER ZAMAN null.\n"
        "# DISIPLIN-06/08 (discovery.py docstring'i): bu liste KALICI BIR ONAY DEGIL, anlik\n"
        "# bir tarama -- periyodik olarak yeniden kosulmali (tlab/indicators/pairs/refresh.py\n"
        "# ::refresh_pairs_yaml -- web arayuzunde 'Cift Listesini Yenile' butonu ya da\n"
        "# `python scripts/pair_denetim.py`).\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(header)
        yaml.safe_dump(payload, f, allow_unicode=True, sort_keys=False)


def refresh_pairs_yaml(
    path: str = "config/pairs.yaml",
    *,
    fdr_q: float | None = FDR_Q,
    oos_split: float | None = OOS_SPLIT,
    sector_map_path: str = SECTOR_MAP_PATH,
    economic_links_path: str = ECONOMIC_LINKS_PATH,
) -> dict:
    """`discover_pairs`i BIST evreninin tamamı üzerinde sıfırdan koşup
    `path`i (varsayılan `config/pairs.yaml`) yeniden yazar. Dönen sözlük web
    tarafının iş durumuna (`_JOBS[job_id]["result"]`) koyabileceği kısa bir
    özet -- tam aday listesi için `path`i oku."""
    symbols = load_universe(Market.BIST)
    prices = load_all_close_prices(symbols)
    sector_map = load_sector_map(sector_map_path)
    economic_link_map = load_economic_link_map(economic_links_path)
    candidates = discover_pairs(
        prices, sector_map=sector_map, same_sector_only=True,
        economic_link_map=economic_link_map, fdr_q=fdr_q, oos_split=oos_split,
    )
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    write_pairs_yaml(path, candidates, fdr_q, oos_split)
    return {
        "n_symbols_priced": len(prices),
        "n_pairs": len(candidates),
        "pairs": [f"{c.symbol_y}/{c.symbol_x}" for c in candidates],
    }
