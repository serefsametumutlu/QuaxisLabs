"""Piyasa REJIMI siniflandirmasi -- Hurst ustu (R/S-benzeri, lag-varyansi
yontemi). SAF MATEMATIK, I/O YOK (`abcd_pattern.py`/`harmonic_xabcd.py` ile
AYNI katman ilkesi -- `src.fetchers.*`/`src.db.*` HICBIR modulu import ETMEZ).

Kaynak/motivasyon (2026-08-19, kullanicinin masaustundeki harici arastirma
notlari -- "gecikme_direncli_stratejiler.md" / "HURST REGIME SWITCHER"):
Hurst ustu (H) piyasanin "hafizasini" olcer -- H>0.55 TREND (momentum
stratejileri daha guvenilir), H<0.45 MEAN-REVERSION (ortalamaya donus daha
guvenilir), 0.45<=H<=0.55 RANDOM WALK (hicbir yon-bagimli strateji guvenilir
DEGIL). Bu modul, `momentum_confluence_variants.py` (trend-takip) ve
`scripts/harmonic_confirmation_optimizasyon.py` (harmonik donus) icin
opsiyonel bir REJIM FILTRESI olarak kullanilir -- kullanici sorusu "farkli
kosullar altinda en iyi kombinasyonu bul" dogrultusunda.

Yontem notu -- neden klasik R/S DEGIL: kaynak dokumandaki formul (ve bu
port) klasik Hurst/R/S rescaled-range ISTATISTIGI DEGIL, "genellestirilmis
Hurst" olarak bilinen, lag'e gore GETIRI FARKI STANDART SAPMASININ
olcek-degisimini kullanan basitlestirilmis bir tahmincidir:
  tau(lag) = std(x[lag:] - x[:-lag])
  H = log-log egim: polyfit(log(lags), log(tau), 1)[0]
Bu, literatur genelinde (özellikle pratik/quant blog kaynaklarinda) yaygin
kullanilan bir yaklasimdir -- klasik R/S kadar teorik olarak temiz olmasa
da, HESAPLAMA HIZI (tam BIST taramasinda pratik) ve KAYNAK DOKUMANLA
BIREBIR AYNI TANIM (sonuclarin karsilastirilabilir olmasi) icin BILINCLI
tercih edildi. `pandas`/`numpy` disinda bagimlilik YOK.

## KRITIK matematiksel uyari -- ne "TREND" olarak algilanir

`np.std()` ORTALAMA-MERKEZLIDIR: `tau(lag)=std(x[lag:]-x[:-lag])` sabit bir
SÜRÜKLENMEYİ (deterministic drift -- örn. duz bir dogru) OTOMATIK ELER,
çünkü std() önce o farkin KENDI ortalamasini çikarir. Bu yontem TREND'i
"fiyat sürekli artiyor" olarak DEGIL, "getiriler ARDIŞIK OLARAK AYNI YÖNDE
KÜMELENİYOR" (pozitif öz-korelasyon/momentum -- fraksiyonel Brown hareketi
anlaminda KALICILIK) olarak algilar. Yani gercek piyasa trendleri (kendisi
de gürültülü bir momentum sürecidir) bu tanima uyar, ama saf/deterministik
bir egim UYMAZ -- bkz. `tests/test_regime_filters.py` bu ayrimi ACIKCA
test eder.
"""

from __future__ import annotations

import numpy as np

TREND_THRESHOLD = 0.55
MEAN_REVERSION_THRESHOLD = 0.45
_MIN_LAG = 2


def hurst_exponent(series: np.ndarray, max_lag: int = 50) -> float:
    """Tek bir pencere icin Hurst ustu tahmini (kaynak dokumanin R/S-benzeri
    lag-varyansi yontemi). Yetersiz veri (< 2*max_lag) veya dejenere seride
    (sabit fiyat, sifir varyans) NOTR deger 0.5 (RANDOM_WALK sinirinda,
    hicbir rejime YANLISLIKLA atanmaz) doner -- FIRLATMAZ."""
    x = np.asarray(series, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) < max_lag * 2:
        return 0.5

    lags = range(_MIN_LAG, min(max_lag, len(x) // 2))
    taus = []
    for lag in lags:
        val = float(np.std(x[lag:] - x[:-lag]))
        taus.append(max(val, 1e-10))
    if len(taus) < 2:
        return 0.5

    log_lags = np.log(list(lags)[: len(taus)])
    log_taus = np.log(taus)
    if not np.all(np.isfinite(log_taus)):
        return 0.5

    slope = float(np.polyfit(log_lags, log_taus, 1)[0])
    return slope


def rolling_hurst(closes: np.ndarray, window: int = 100, max_lag: int = 50) -> np.ndarray:
    """`hurst_exponent`in TUM seri uzerinde kayan-pencere hali -- her bar
    icin SADECE `closes[i-window:i]` (gecmis, kendisi HARIC) kullanilir,
    look-ahead YOK. Ilk `window` bar icin 0.5 (RANDOM_WALK notr degeri,
    "henuz hesaplanamadi" anlaminda -- filtre bu barlarda devre disi kalir,
    hicbir rejime yanlislikla dahil ETMEZ)."""
    x = np.asarray(closes, dtype=float)
    n = len(x)
    out = np.full(n, 0.5)
    for i in range(window, n):
        out[i] = hurst_exponent(x[i - window : i], max_lag=max_lag)
    return out


def classify_regime(h: float) -> str:
    """`h` (Hurst ustu) -> "TREND" / "MEAN_REVERSION" / "RANDOM_WALK"."""
    if h > TREND_THRESHOLD:
        return "TREND"
    if h < MEAN_REVERSION_THRESHOLD:
        return "MEAN_REVERSION"
    return "RANDOM_WALK"
