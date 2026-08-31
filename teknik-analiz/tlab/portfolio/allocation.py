"""Handcrafting: portföy/forecast ağırlıklandırma (Faz 10, K3/Carver
çıkarımı).

Kaynak: `bilgi-bankasi/teknik/11/{KURAL-05,ORAN-06,ORAN-07,DISIPLIN-05,
DISIPLIN-06,DISIPLIN-07,DISIPLIN-08}`. Markowitz optimizasyonunun küçük
tahmin hatalarına aşırı duyarlılığından (DISIPLIN-06) kaçınmak için,
korelasyona göre GRUPLANMIŞ varlıklara Tablo 8'in (ORAN-07) grup-ağırlık
kurallarını uygulayan, performans/Sharpe verisi KULLANMAYAN (varsayılan)
bir ağırlıklandırma yöntemi."""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from tlab.core.params import BaseParams

# Bir "Group", ya tek bir sembol adı (yaprak) ya da iç içe Group'lardan oluşan
# bir liste (KURAL-05 adım 1-4'ün "hisse->sektör->ülke->varlık sınıfı" gibi
# çok seviyeli gruplamasını temsil eder).
Group = str | list["Group"]


@dataclass(frozen=True)
class HandcraftParams(BaseParams):
    # TASARIM KARARI — K3 kitabı bir "her ne kadar sık isterseniz" notu
    # dışında kesin bir frekans vermiyor; üç aylık, korelasyonun "zamanla çok
    # değişmediği" gözlemiyle (11/DISIPLIN-08) tutarlı makul bir varsayılan.
    recompute_frequency: str = "quarterly"
    correlation_source: str = "rolling_backtest"  # "rolling_backtest" | "rule_of_thumb"
    sharpe_adjustment: bool = False  # 11/DISIPLIN-07 — varsayılan KAPALI


# 11/ORAN-07 (Tablo 8, s.?) — DOĞRULANMIŞ SABİT. Anahtar: (corr_AB, corr_AC,
# corr_BC); "A/B/C" rolleri tablonun KENDİ örneklerindeki isimlendirmedir
# (B her zaman diğer ikisi arasındaki "ortak" varlık) — `_lookup_3asset_
# weights` bu rolleri GERÇEK sembol sırasından bağımsız (permütasyon
# araması ile) doğru eşler.
_TABLE_3ASSET: dict[tuple[float, float, float], tuple[float, float, float]] = {
    (0.0, 0.5, 0.0): (0.30, 0.40, 0.30),
    (0.0, 0.9, 0.0): (0.27, 0.46, 0.27),
    (0.5, 0.0, 0.5): (0.37, 0.26, 0.37),
    (0.0, 0.5, 0.9): (0.45, 0.45, 0.10),
    (0.9, 0.0, 0.9): (0.39, 0.22, 0.39),
    (0.5, 0.9, 0.5): (0.29, 0.42, 0.29),
    (0.9, 0.5, 0.9): (0.42, 0.16, 0.42),
}


def _lookup_3asset_weights(corr: np.ndarray) -> np.ndarray:
    """`corr`: 3x3 korelasyon matrisi (herhangi bir sembol sırasıyla).
    Tabloya (11/ORAN-07) EN YAKIN satırı, üç varlığın olası TÜM 6
    eşleşmesini (hangi varlık A/B/C rolünde) deneyerek bulur — tablo A/B/C
    rollerine göre ASİMETRİK olduğu için (B her zaman "ortadaki" varlık)
    sembol SIRASINDAN bağımsız doğru sonucu garantiler. **TASARIM KARARI**:
    tablo yalnızca 7 somut korelasyon üçlüsünü kapsıyor (kitabın kendi
    çalışılmış örnekleri) — bunların dışındaki üçlüler EN YAKIN (L2
    mesafesi) satıra yuvarlanır ("Tam eşleşmeyen korelasyon değerleri EN
    YAKIN satıra yuvarlanır" — 11/ORAN-07 notu)."""
    corr = np.clip(corr, 0.0, None)  # negatif korelasyon -> taban sıfır (11/KURAL-05 adım 5)
    best_dist = math.inf
    best_i, best_j, best_k = 0, 1, 2
    best_row: tuple[float, float, float] = (1.0, 1.0, 1.0)
    for i, j, k in itertools.permutations(range(3)):
        ab, ac, bc = corr[i, j], corr[i, k], corr[j, k]
        for row, weights in _TABLE_3ASSET.items():
            dist = (row[0] - ab) ** 2 + (row[1] - ac) ** 2 + (row[2] - bc) ** 2
            if dist < best_dist:
                best_dist, best_row = dist, weights
                best_i, best_j, best_k = i, j, k
    result = np.empty(3)
    result[best_i], result[best_j], result[best_k] = best_row
    return result


def _base_group_weights(corr: np.ndarray) -> np.ndarray:
    """11/ORAN-07 (Tablo 8) — tek grup İÇİNDEKİ N varlık için taban ağırlık.
    N=1: %100. N=2: %50/%50 (korelasyondan BAĞIMSIZ). N=3: tabloya en yakın
    satır. N>=4: eşit korelasyonluysa eşit ağırlık; aksi halde otomatik
    gruplama YOK (KURAL-05 adım 4 — kitap N>=4 farklı-korelasyonlu bir
    algoritma vermiyor, "alt gruplara böl, tabloya tekrar uy" diyor) —
    çağıran `groups` parametresiyle elle alt-gruplamalı."""
    n = corr.shape[0]
    if n == 1:
        return np.array([1.0])
    if n == 2:
        return np.array([0.5, 0.5])
    if n == 3:
        return _lookup_3asset_weights(corr)
    off_diag = corr[~np.eye(n, dtype=bool)]
    if np.allclose(off_diag, off_diag[0], atol=1e-9):
        return np.full(n, 1.0 / n)
    raise ValueError(
        "4+ farklı-korelasyonlu varlık için otomatik gruplama YOK (11/KURAL-05 adım 4) "
        "— `groups` parametresiyle elle alt-gruplayın"
    )


def _group_leaves(group: Group) -> list[str]:
    if isinstance(group, str):
        return [group]
    leaves: list[str] = []
    for item in group:
        leaves.extend(_group_leaves(item))
    return leaves


def _group_correlation(
    leaves_a: list[str], leaves_b: list[str], corr_matrix: pd.DataFrame
) -> float:
    """İki grup ARASINDAKİ korelasyon, gruplar arasındaki TÜM varlık
    çiftlerinin ORTALAMASI olarak tahmin edilir. **TASARIM KARARI**: kitap
    grup-arası korelasyonun KESİN hesaplanma yöntemini belirtmiyor — basit
    ortalama, tek-elemanlı gruplar için TAM olarak ham korelasyona indirgenir
    (bu yüzden flat/tek-seviyeli çağrılarda `handcraft_weights(groups=None)`
    ile BİREBİR aynı sonucu üretir)."""
    pairs = [corr_matrix.loc[a, b] for a in leaves_a for b in leaves_b]
    return float(np.mean(pairs))


def _weights_for_group(group: Group, corr_matrix: pd.DataFrame) -> dict[str, float]:
    if isinstance(group, str):
        return {group: 1.0}
    items = list(group)
    if len(items) == 1:
        return _weights_for_group(items[0], corr_matrix)

    leaves_per_item = [_group_leaves(item) for item in items]
    n = len(items)
    corr = np.array(
        [
            [
                1.0 if i == j
                else _group_correlation(leaves_per_item[i], leaves_per_item[j], corr_matrix)
                for j in range(n)
            ]
            for i in range(n)
        ]
    )
    top_weights = _base_group_weights(corr)

    final: dict[str, float] = {}
    for item, group_w in zip(items, top_weights, strict=True):
        for asset, w in _weights_for_group(item, corr_matrix).items():
            final[asset] = final.get(asset, 0.0) + group_w * w
    return final


def handcraft_weights(corr_matrix: pd.DataFrame, groups: Group | None = None) -> dict[str, float]:
    """11/KURAL-05 — flat (`groups=None`, her sembol kendi düz grubu) ya da
    iç içe gruplu (`groups`) handcrafting. `groups` örneği:
    `[["BOND"], ["SP500", "NASDAQ"]]` — 2 üst-grup (Bond tek başına,
    SP500+NASDAQ birlikte); daha derin iç içe yapılar (3+ seviye) da
    desteklenir. Grup içi/arası ağırlıkların ÇARPIMI nihai ağırlığı verir
    (KURAL-05 adım 3)."""
    if groups is None:
        groups = list(corr_matrix.columns)
    return _weights_for_group(groups, corr_matrix)


def apply_sharpe_adjustment(
    weights: dict[str, float], multipliers: dict[str, float]
) -> dict[str, float]:
    """11/DISIPLIN-07 — Tablo 12 (s.86) çarpanlarıyla ağırlıkları yeniden
    ölçekleyip normalize eder. **DÜRÜST NOT**: Tablo 12'nin kendi sayısal
    değerleri K3'ün hedefli çıkarım kapsamına DAHİL EDİLMEDİ — bu fonksiyon
    çarpanları PARAMETRE olarak alır, içinde SABİT/uydurma bir tablo
    TAŞIMAZ. `HandcraftParams.sharpe_adjustment` varsayılan olarak KAPALI
    (11/DISIPLIN-07: "<10 yıl veriyle Sharpe farkına göre AYARLAMA YAPMA")."""
    adjusted = {k: w * multipliers.get(k, 1.0) for k, w in weights.items()}
    total = sum(adjusted.values())
    if total <= 0:
        raise ValueError("sharpe_adjustment sonrası toplam ağırlık <= 0")
    return {k: v / total for k, v in adjusted.items()}


def periodic_handcraft_schedule(
    returns: pd.DataFrame,
    recompute_dates: list[pd.Timestamp],
    correlation_window: int,
    groups: Group | None = None,
) -> dict[pd.Timestamp, dict[str, float]]:
    """Her `recompute_dates` noktasında YALNIZCA o tarihe kadarki (dahil)
    trailing `correlation_window` barlık getiriyle `handcraft_weights()`
    çalıştırır — piecewise-constant, non-repaint (bkz. spec "Durum
    makinesi": ağırlıklar iki recompute ARASINDA sabit kalan bir adım
    fonksiyonudur). Yetersiz geçmişte (`correlation_window` kadar veri
    yoksa) o recompute tarihi ATLANIR (hata fırlatılmaz — Faz 8D'nin
    `min_history_bars` guard deseniyle tutarlı)."""
    schedule: dict[pd.Timestamp, dict[str, float]] = {}
    for dt in sorted(recompute_dates):
        window = returns.loc[:dt].tail(correlation_window)
        if len(window) < correlation_window:
            continue
        schedule[dt] = handcraft_weights(window.corr(), groups)
    return schedule


def weights_at(
    schedule: dict[pd.Timestamp, dict[str, float]], t: pd.Timestamp
) -> dict[str, float] | None:
    """`t` barındaki GEÇERLİ ağırlık — en son GEÇMİŞ (t'de veya öncesinde)
    recompute noktasının ağırlığı ("extend-only sabit değer", `structure.
    golden_zone`'un bant deseniyle AYNI ilke, Faz 8C). Hiçbir recompute
    noktası `t`'den önce/eşit değilse `None` döner."""
    valid = [dt for dt in schedule if dt <= t]
    if not valid:
        return None
    return schedule[max(valid)]
