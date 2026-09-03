"""Monte Carlo: tlab discover_pairs boru hattinin sahte-kesif orani.

Iki BAGIMSIZ rastgele yuruyus (gercek kointegrasyon YOK) uretilir;
tlab'in yontemi (ham adfuller + iki yon dene, dusugu al) ile dogru
yontem (statsmodels coint = Engle-Granger, MacKinnon kritik degerleri)
karsilastirilir.
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, coint

rng = np.random.default_rng(20260903)

def tlab_beta(y_log, x_log):
    # tlab/features/stats.py::rolling_beta (tum pencere) -> cov/var, INTERCEPT YOK
    cov = np.cov(y_log, x_log, ddof=1)[0, 1]
    var = np.var(x_log, ddof=1)
    return cov / var

def tlab_pipeline(y, x, corr_min=0.7, adf_max=0.05, hl_range=(5.0, 60.0)):
    """discover_pairs'in tam mantigi: corr filtresi -> her iki yon -> min adf_p."""
    best = None
    for yy, xx in ((y, x), (x, y)):
        y_log, x_log = np.log(yy), np.log(xx)
        corr = np.corrcoef(y_log, x_log)[0, 1]
        if corr < corr_min:
            continue
        b = tlab_beta(y_log, x_log)
        spread = y_log - b * x_log
        p = adfuller(spread)[1]
        if p >= adf_max:
            continue
        # halflife
        lag, d = spread[:-1], np.diff(spread)
        lam = np.polyfit(lag, d, 1)[0]
        if lam >= 0:
            continue
        hl = -np.log(2) / lam
        if not (hl_range[0] <= hl <= hl_range[1]):
            continue
        if best is None or p < best:
            best = p
    return best is not None

def correct_pipeline(y, x, corr_min=0.7, p_max=0.05, hl_range=(5.0, 60.0)):
    best = None
    for yy, xx in ((y, x), (x, y)):
        y_log, x_log = np.log(yy), np.log(xx)
        corr = np.corrcoef(y_log, x_log)[0, 1]
        if corr < corr_min:
            continue
        p = coint(y_log, x_log, trend="c")[1]   # Engle-Granger, MacKinnon
        if p >= p_max:
            continue
        b = tlab_beta(y_log, x_log)
        spread = y_log - b * x_log
        lag, d = spread[:-1], np.diff(spread)
        lam = np.polyfit(lag, d, 1)[0]
        if lam >= 0:
            continue
        hl = -np.log(2) / lam
        if not (hl_range[0] <= hl <= hl_range[1]):
            continue
        if best is None or p < best:
            best = p
    return best is not None

for n in (250, 500, 750):
    trials = 400
    tlab_hits = corr_hits = adf_only = coint_only = correct_hits = 0
    for _ in range(trials):
        # bagimsiz rastgele yuruyusler, hafif pozitif drift (BIST gibi)
        y = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.02, n)))
        x = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.02, n)))
        y_log, x_log = np.log(y), np.log(x)
        if np.corrcoef(y_log, x_log)[0, 1] >= 0.7:
            corr_hits += 1
        b = tlab_beta(y_log, x_log)
        if adfuller(y_log - b * x_log)[1] < 0.05:
            adf_only += 1
        if coint(y_log, x_log, trend="c")[1] < 0.05:
            coint_only += 1
        if tlab_pipeline(y, x):
            tlab_hits += 1
        if correct_pipeline(y, x):
            correct_hits += 1
    print(f"n={n:4d} | corr>=0.7: {corr_hits/trials:6.1%} | "
          f"ham adfuller p<.05: {adf_only/trials:6.1%} | "
          f"coint (EG) p<.05: {coint_only/trials:6.1%} | "
          f"TLAB tam boru hatti: {tlab_hits/trials:6.1%} | "
          f"DUZELTILMIS boru hatti: {correct_hits/trials:6.1%}")


# ---------------------------------------------------------------------------
# 2026-09-03 sonuclari (400 deneme x 3 orneklem boyu, bagimsiz rastgele
# yuruyusler -- yani GERCEK kointegrasyon YOK, tum bulgular sahte-kesif):
#
#   n= 250 | corr>=0.7:  9.5% | ham adfuller: 16.8% | coint(EG): 8.8%
#           | TLAB boru hatti: 3.2% | duzeltilmis: 1.8%
#   n= 500 | corr>=0.7: 12.5% | ham adfuller: 18.5% | coint(EG): 7.0%
#           | TLAB boru hatti: 4.0% | duzeltilmis: 2.2%
#   n= 750 | corr>=0.7: 13.5% | ham adfuller: 13.8% | coint(EG): 5.5%
#           | TLAB boru hatti: 3.5% | duzeltilmis: 1.2%
#
# Nominal seviye %5 iken ham adfuller %14-18 reddediyor: ~3 kat asiri-reddetme.
# Capraz kontrol: config/pairs.yaml'daki 606 cift, 8754 sektor-ici
# kombinasyondan bulunmus = %6.9. Saf gurultunun kendi orani %3.2-4.0.
# Yani mevcut listenin kabaca YARISI, hicbir gercek kointegrasyon olmasa
# bile beklenen sayida.
#
# Bkz. docs/TANI_VE_YOL_HARITASI_v2.md bolum 1.4.
# ---------------------------------------------------------------------------
