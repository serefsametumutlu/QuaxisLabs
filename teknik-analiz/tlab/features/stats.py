"""İstatistiksel yardımcılar — çift (pair) ticareti ve rejim analizi için.

Rolling fonksiyonlar pandas .rolling() kullanır (asla center=True — bu,
tlab/testing/lint_lookahead.py tarafından da sert hata olarak yakalanır),
bu yüzden doğaları gereği yalnızca geçmişe bakar. halflife/adf_pvalue ise
fibonacci.py/volume_profile.py ile aynı felsefede: verilen SERİNİN
tamamını kullanan saf fonksiyonlardır — hangi pencerenin (geriye dönük)
verileceği çağıranın sorumluluğundadır.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, coint


def zscore(series: pd.Series, window: int) -> pd.Series:
    """(x - rolling_mean) / rolling_std. std=0 olan barlarda NaN döner."""
    mean = series.rolling(window).mean()
    std = series.rolling(window).std()
    return (series - mean) / std.replace(0.0, np.nan)


def log_spread(y: pd.Series, x: pd.Series, beta: float | pd.Series) -> pd.Series:
    """log(y) - beta*log(x). beta sabit ya da (ör. rolling_beta'dan) bir
    Series olabilir — Series ise index'e göre hizalanır."""
    return np.log(y) - beta * np.log(x)


def rolling_beta(y: pd.Series, x: pd.Series, window: int) -> pd.Series:
    """y = alpha + beta*x OLS regresyonunun rolling beta katsayısı.

    beta[t] = cov(y,x)[t-window+1:t+1] / var(x)[t-window+1:t+1].
    """
    cov = y.rolling(window).cov(x)
    var = x.rolling(window).var()
    return cov / var.replace(0.0, np.nan)


def rolling_corr(a: pd.Series, b: pd.Series, window: int) -> pd.Series:
    """Rolling Pearson korelasyonu."""
    return a.rolling(window).corr(b)


def halflife(spread: pd.Series) -> float:
    """Ornstein-Uhlenbeck yarı ömrü: delta_spread[t] ~ lambda*spread[t-1]
    OLS regresyonundan -ln(2)/lambda. lambda>=0 (ıraksak/rastgele yürüyüş)
    ise math.inf döner (yarı ömür tanımsız/sonsuz)."""
    lagged = spread.shift(1)
    delta = spread.diff()
    valid = pd.concat([lagged, delta], axis=1).dropna()
    if len(valid) < 2:
        raise ValueError("halflife için en az 2 geçerli (lag'lenmiş) gözlem gerekli")

    x = valid.iloc[:, 0].to_numpy()
    y = valid.iloc[:, 1].to_numpy()
    x_mean, y_mean = x.mean(), y.mean()
    denom = float(((x - x_mean) ** 2).sum())
    if denom == 0:
        raise ValueError("spread sabit — regresyon tanımsız")
    lam = float(((x - x_mean) * (y - y_mean)).sum() / denom)

    if lam >= 0:
        return math.inf
    return -math.log(2) / lam


def adf_pvalue(spread: pd.Series) -> float:
    """Augmented Dickey-Fuller birim kök testi p-değeri (statsmodels).

    Düşük p-değeri -> durağanlık (mean-reversion) lehine kanıt.

    **UYARI (Faz 2, 2A — docs/TANI_VE_YOL_HARITASI_v2.md bölüm 1.4b):** Bu
    fonksiyonu TAHMİN EDİLMİŞ bir regresyon kalıntısına (ör. `y - beta*x`,
    beta ayrı bir OLS'ten geldiyse) UYGULAMA — o durumda `engle_granger_
    pvalue` kullan. Neden: OLS kalıntısı kareler toplamını MİNİMİZE edecek
    şekilde seçildiği için durağan GÖRÜNMEYE eğilimlidir; standart ADF
    kritik değerleri bu durumda GEÇERSİZDİR (400 denemelik Monte Carlo
    ölçümü: iki BAĞIMSIZ rastgele yürüyüşte bile ham `adfuller` nominal
    %5 yerine %14-18 reddediyor — ~3 kat aşırı-reddetme). `adf_pvalue`
    yalnızca zaten SABİT bir β ile (ör. discovery dışında, tek bir seri
    üzerinde) doğrudan durağanlık test edilirken güvenlidir; iki serinin
    KENDİSİ arasındaki kointegrasyonu test etmek için HER ZAMAN
    `engle_granger_pvalue` kullanılmalı."""
    clean = spread.dropna()
    result = adfuller(clean.to_numpy())
    return float(result[1])


def engle_granger_pvalue(y: pd.Series, x: pd.Series, trend: str = "c") -> float:
    """İki serinin kointegrasyonu için Engle-Granger p-değeri (statsmodels
    `coint`, MacKinnon kritik değerleriyle) — `adf_pvalue`'nun TAHMİN
    EDİLMİŞ bir OLS kalıntısı üzerinde YANLIŞ olan kullanımının doğru
    yerine geçer (bkz. `adf_pvalue`'nun UYARI bölümü).

    `coint` kendi içinde bir OLS regresyonu (β) tahmin edip kalıntının ADF
    testini MacKinnon'ın kointegrasyon-özel kritik değerleriyle yapar --
    bu, `ols_spread`/`adf_pvalue` ikilisinin AYRI AYRI yapmaya çalıştığı ama
    yanlış kritik değerlerle yaptığı şeyin İSTATİSTİKSEL OLARAK doğru
    hâlidir. `y`/`x` inner-join ile hizalanır, NaN/negatif (log tanımsız
    olmasa da tutarlılık için) satırlar atılır."""
    common = y.index.intersection(x.index)
    y_clean = y.loc[common].astype(float)
    x_clean = x.loc[common].astype(float)
    valid = pd.concat([y_clean, x_clean], axis=1).dropna()
    if len(valid) < 3:
        raise ValueError("engle_granger_pvalue için en az 3 hizalı gözlem gerekli")
    result = coint(valid.iloc[:, 0].to_numpy(), valid.iloc[:, 1].to_numpy(), trend=trend)
    return float(result.pvalue)


def ols_spread(y: pd.Series, x: pd.Series) -> tuple[pd.Series, float, float]:
    """Sabit terimli (intercept'li) TEK OLS regresyonu: `log(y) = alpha +
    beta*log(x) + spread`. `(spread, alpha, beta)` döner.

    `log_spread(y, x, beta)`'nın (intercept'siz, geriye dönük uyumluluk
    için hâlâ duruyor) aksine burada alpha da AYRICA tahmin edilir --
    Faz 2 tanısının (e) bulgusu: `rolling_beta`'nın cov/var'ı sabitli
    OLS'in EĞİMİDİR ama `log_spread` alpha'yı hiç çıkarmıyordu, test edilen
    seri gerçek bir OLS kalıntısı DEĞİLDİ (adfuller'ın varsayılan
    `regression='c'`'si ortalamayı soğurduğu için felakete dönüşmüyordu
    ama tutarsızdı). `discover_pairs` artık BUNU kullanıyor."""
    y_log = np.log(y.astype(float))
    x_log = np.log(x.astype(float))
    x_mean, y_mean = float(x_log.mean()), float(y_log.mean())
    var = float(((x_log - x_mean) ** 2).sum())
    if var == 0:
        raise ValueError("x sabit -- regresyon tanımsız")
    cov = float(((x_log - x_mean) * (y_log - y_mean)).sum())
    beta = cov / var
    alpha = y_mean - beta * x_mean
    spread = y_log - alpha - beta * x_log
    return spread, alpha, beta


def benjamini_hochberg(pvalues: np.ndarray | list[float], q: float) -> np.ndarray:
    """Standart Benjamini-Hochberg FDR (false discovery rate) prosedürü.

    `pvalues`'taki p-değerleri artan sırada sıralanır (p_(1)<=...<=p_(m));
    `p_(k) <= (k/m)*q` şartını sağlayan EN BÜYÜK k bulunur, p_(1)..p_(k)
    (orijinal sırayla) `True` (reddedilir/hayatta kalır) olarak işaretlenir.
    Hiçbir k şartı sağlamazsa tamamı `False` döner. Saf fonksiyon, girdi
    sırasıyla AYNI uzunlukta bir bool dizisi döner (orijinal sıraya göre)."""
    p = np.asarray(pvalues, dtype=float)
    m = len(p)
    result = np.zeros(m, dtype=bool)
    if m == 0:
        return result
    order = np.argsort(p, kind="stable")
    sorted_p = p[order]
    ranks = np.arange(1, m + 1, dtype=float)
    thresholds = (ranks / m) * q
    passed = sorted_p <= thresholds
    if not passed.any():
        return result
    max_k = int(np.max(np.nonzero(passed)[0]))
    reject_sorted = np.zeros(m, dtype=bool)
    reject_sorted[: max_k + 1] = True
    result[order] = reject_sorted
    return result
