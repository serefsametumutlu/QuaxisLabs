"""Kointegrasyon çürüme (decay) izleyicisi — Faz 2, 2C (CLAUDE.md backlog
madde 4, kullanıcının takip ettiği bir kantçının notundan, 2026-08-29).

`discovery.py::discover_pairs` kointegrasyonu yalnızca KEŞİF anında (tek
seferlik, `oos_split` ile en fazla iki pencerede) test eder — bir çift
seçilip pozisyon açıldıktan SONRA spread'in kointegre KALDIĞI hiç
YENİDEN doğrulanmıyordu. Bu modül, AKTİF tutulan bir çift için spread
üzerinde ROLLING Engle-Granger p-değerini izler: p eşiği GERİ aşarsa
(yapısal kırılma — M&A, mevzuat değişikliği, endeks yeniden dengeleme vb.)
z henüz dönmemiş olsa bile bir "kırılma" bayrağı üretir —
`RelativeMomentumPair(mode="mean_reversion")` bunu (opsiyonel,
`coint_monitor_window` verilirse) pozisyonu düzleştirme sinyali olarak
kullanır (bkz. o modülün `_compute_mean_reversion`'ı).

AYNI istatistiksel makineyi (`tlab/features/stats.py::engle_granger_pvalue`,
Faz 2, 2A) tekrar kullanır — YENİ bir yöntem GEREKTİRMEZ, `discover_pairs`'in
KEŞİF testinin sürekli/kayan (rolling) bir versiyonudur."""

from __future__ import annotations

import numpy as np
import pandas as pd

from tlab.features.stats import engle_granger_pvalue


def rolling_coint_pvalue(y: pd.Series, x: pd.Series, window: int = 90) -> pd.Series:
    """`[t-window+1, t]` penceresinde Engle-Granger p-değeri — yalnızca
    GEÇMİŞE bakar (non-repaint: `t`'deki değer yalnızca `t` ve öncesi
    veriyle hesaplanır, `t`'den SONRA asla değişmez). İlk `window-1` bar
    `NaN`. `window` varsayılanı 90 (CLAUDE.md backlog notundaki öneri —
    günlük veride ~4.5 ay, `coint`'in asimptotik güvenilirliği ile "yeterince
    güncel" olma arasında makul bir denge).

    `y`/`x` HER ZAMAN inner-join ile hizalanır (index'leri farklı olabilir);
    pencere içinde `engle_granger_pvalue` başarısız olursa (yetersiz gözlem,
    negatif/sıfır fiyat vb.) o bar `NaN` kalır (aday elenmiş SAYILMAZ,
    yalnızca ölçülemez)."""
    common = y.index.intersection(x.index)
    y_aligned = y.loc[common].astype(float)
    x_aligned = x.loc[common].astype(float)
    n = len(common)
    values = np.full(n, np.nan)
    for t in range(window - 1, n):
        y_win = y_aligned.iloc[t - window + 1 : t + 1]
        x_win = x_aligned.iloc[t - window + 1 : t + 1]
        try:
            values[t] = engle_granger_pvalue(y_win, x_win)
        except ValueError:
            continue
    return pd.Series(values, index=common)


def cointegration_broken(
    y: pd.Series, x: pd.Series, window: int = 90, p_threshold: float = 0.10,
) -> pd.Series:
    """`rolling_coint_pvalue(y, x, window) >= p_threshold` — `True` olan
    barlarda yapısal kırılma ŞÜPHESİ (spread ARTIK kointegre GÖRÜNMÜYOR).

    `p_threshold` (varsayılan 0.10), `discover_pairs`'in tipik KEŞİF eşiğinden
    (`adf_max`, genelde 0.05) BİLİNÇLİ OLARAK daha GEVŞEK — buradaki amaç
    yeni bir çift KEŞFETMEK değil, zaten kabul edilmiş bir ilişkinin GERÇEKTEN
    kırıldığını yakalamak; `adf_max` kadar sıkı bir eşik, ROLLING bir pencerede
    normal istatistiksel gürültüyü bile sürekli "kırılma" olarak işaretlerdi
    (yalancı-pozitif alarm oranı çok yüksek olurdu). `NaN` (pencere henüz
    dolmadı ya da test başarısız oldu) barlarda `False` döner — belirsizlik
    "kırılma yok" olarak ele alınır, aksi hâlde ısınma penceresindeki HER
    bar yanlışlıkla kırılma sayılırdı."""
    p = rolling_coint_pvalue(y, x, window)
    return (p >= p_threshold).fillna(False)
