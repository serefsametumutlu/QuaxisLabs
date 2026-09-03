"""Formasyon göstergelerinin PAYLAŞTIĞI üç bağlam kontrolü (Faz 1, 1A —
`docs/TANI_VE_YOL_HARITASI_v2.md`). Hepsi saf fonksiyon, non-repaint
(yalnızca `[0, start_idx]`/`[0, idx]` aralığına bakar, gelecek veriye
erişmez).

Kaynak: Bulkowski'nin çift dip/OBO tanımlarındaki "önce düşen/yükselen bir
trend" şartı + minimum derinlik + kırılım hacmi onayı — bu üç kontrol
şimdiye kadar HER formasyon modülünde (varsa) ayrı ayrı ve TUTARSIZ
yazılmıştı (bkz. `docs/STRATEJI_DENETIM_TAM.md` Bölüm B); burada TEK
kaynağa toplandı."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from tlab.core.types import Direction


def rolling_trend_tstat(series: pd.Series, window: int) -> tuple[pd.Series, pd.Series]:
    """`series`nin (zamana karşı) rolling OLS eğimi + t-istatistiği.

    Kapalı-form basit doğrusal regresyon (y=series, x=0..window-1 bar
    indeksi), yalnızca `[t-window+1, t]` penceresini kullanır (non-repaint).
    `tlab/indicators/momentum/momentum_rank.py`'nin RS eğimi için ZATEN
    kullandığı formülün TAŞINMIŞ hâli (Faz 1, 1A — "kod TEKRARLAMA")."""
    values = series.to_numpy(dtype=float)
    n = len(values)
    slope = np.full(n, np.nan)
    tstat = np.full(n, np.nan)
    x = np.arange(window, dtype=float)
    x_mean = x.mean()
    x_var = float(((x - x_mean) ** 2).sum())
    dof = window - 2
    if window >= 2 and dof > 0 and x_var > 0:
        for t in range(window - 1, n):
            y = values[t - window + 1 : t + 1]
            if np.isnan(y).any():
                continue
            y_mean = y.mean()
            b = float(((x - x_mean) * (y - y_mean)).sum() / x_var)
            a = y_mean - b * x_mean
            resid = y - (a + b * x)
            resid_var = float((resid**2).sum() / dof)
            se_b = math.sqrt(resid_var / x_var) if resid_var > 0 else 0.0
            slope[t] = b
            tstat[t] = (b / se_b) if se_b > 0 else np.nan
    return pd.Series(slope, index=series.index), pd.Series(tstat, index=series.index)


def prior_trend(
    df: pd.DataFrame,
    start_idx: int,
    lookback: int,
    direction: Direction,
    min_tstat: float = 1.5,
) -> tuple[bool, float]:
    """Formasyonun BAŞLADIĞI (`start_idx`) bardan geriye `lookback` bar
    bakıp, o pencerede log-fiyatın `direction` yönünde ANLAMLI bir trend
    (`|t-istatistiği| >= min_tstat`) taşıyıp taşımadığını döner.

    `direction="long"` (çift dip/TOBO gibi DİPTEN dönüş formasyonları) ->
    DÜŞEN bir ön trend beklenir (eğim negatif). `direction="short"` (çift
    tepe/OBO gibi TEPEDEN dönüş) -> YÜKSELEN bir ön trend beklenir (eğim
    pozitif). Kaynak: Bulkowski — çift dip DÜŞEN bir trendden sonra gelmeli,
    OBO/TOBO için de AYNI ön-trend şartı.

    Non-repaint: yalnızca `df.iloc[start_idx-lookback+1 : start_idx+1]`'e
    bakar (`start_idx`'ten SONRAKİ hiçbir veriye erişmez). Pencere sığmıyorsa
    (`start_idx < lookback-1`) ya da fiyat serisinde negatif/sıfır değer
    varsa (log tanımsız) `(False, 0.0)` döner."""
    window_start = start_idx - lookback + 1
    if window_start < 0:
        return False, 0.0
    close = df["close"].to_numpy(dtype=float)[window_start : start_idx + 1]
    if len(close) < lookback or np.any(close <= 0):
        return False, 0.0
    log_close = pd.Series(np.log(close))
    slope, tstat = rolling_trend_tstat(log_close, lookback)
    s, t = slope.iloc[-1], tstat.iloc[-1]
    if pd.isna(s) or pd.isna(t):
        return False, 0.0
    if direction == "long":
        ok = s < 0 and abs(t) >= min_tstat
    elif direction == "short":
        ok = s > 0 and abs(t) >= min_tstat
    else:
        ok = False
    return bool(ok), float(t)


def pattern_depth_ok(
    depth: float, price: float, atr_at_birth: float, min_pct: float, min_atr: float
) -> bool:
    """Formasyon derinliği (`depth`, fiyat biriminde) HEM `price`'ın
    `min_pct` kadarından HEM `atr_at_birth`'ün `min_atr` katından BÜYÜK
    olmalı — ikisi birden, çünkü yalnızca yüzde ölçütü düşük volatiliteli
    hisselerde çok gevşek, yalnızca ATR ölçütü yüksek volatilitede çok
    gevşek kalırdı (bkz. STRATEJI_DENETIM_TAM.md — ZOREN örneğinde
    formasyon derinliği fiyatın ~%3'ü, 4H gürültüsünden ayırt edilemezdi)."""
    if price <= 0 or pd.isna(atr_at_birth) or atr_at_birth <= 0:
        return False
    return depth >= min_pct * price and depth >= min_atr * atr_at_birth


def breakout_volume_ok(volume: np.ndarray, idx: int, ma_window: int, k: float) -> bool:
    """Kırılım barının (`idx`) hacmi, KENDİSİ DAHİL geriye `ma_window`
    barlık ortalamanın `k` katından büyük mü. `min_periods=5` ile (tam
    pencere dolmasa bile en az 5 bar varsa hesaplanır) — formasyon
    modüllerinin ÖNCEDEN ayrı ayrı yazdığı `df["volume"].rolling(vol_ma_
    window, min_periods=5).mean()` deseninin TEK kaynağa toplanmış hâli.
    Non-repaint: yalnızca `volume[:idx+1]`'e bakar."""
    if idx < 0 or idx >= len(volume):
        return False
    vma = pd.Series(volume[: idx + 1]).rolling(ma_window, min_periods=5).mean().iloc[-1]
    if pd.isna(vma) or vma <= 0:
        return False
    return bool(volume[idx] >= k * vma)
