"""Omuz-Baş-Omuz (OBO, tepe) / Ters Omuz-Baş-Omuz (TOBO, dip) tespiti.

Girdi, ZATEN alternatif bir zigzag olmalı (bkz. `swings.alternate_pivots` +
opsiyonel `label_structure`) — bu modül kendi pivot tespiti yapmaz, saf
geometri uygular. 5 ardışık pivotluk her pencere ('l1, h1, head, h2, l3')
incelenir; pattern SAĞ OMUZ (l3) ONAYLANDIĞI barda (`l3.confirmed_idx`)
var sayılır — bu ana kadar hiçbir HSPattern üretilemez (non-repaint: yalnızca
zaten kesinleşmiş/onaylı Pivot'lar kullanılır, hepsi frozen).

Alan adlandırması ('l1'/'h1'/'head'/'h2'/'l3') TOBO (dip) yönelimlidir:
l1/head/l3 LOW, h1/h2 HIGH. OBO (tepe) için AYNI pozisyonel alanlar TERS
kind taşır (l1/head/l3 HIGH, h1/h2 LOW) — isimler değişmez, yalnızca hangi
ekstremin "omuz/baş" rolünü oynadığı `kind` parametresine göre değişir.
Boyun çizgisi HER İKİ türde de h1->h2 arasından geçer (omuz ile baş
arasındaki "geri çekilme" noktaları).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from tlab.features.swings import Pivot

HSKind = Literal["tobo", "obo"]


@dataclass(frozen=True)
class HSPattern:
    """created_idx = l3.confirmed_idx (sağ omuz onay barı).

    target: klasik "ölçülü hareket" hedefi — boyun çizgisinin l3 barındaki
    değeri, baş derinliği (depth) kadar TOBO'da yukarı, OBO'da aşağı
    öteklenmiş hâli."""

    kind: HSKind
    l1: Pivot
    h1: Pivot
    head: Pivot
    h2: Pivot
    l3: Pivot
    neckline_slope: float
    neckline_intercept: float
    depth: float
    target: float
    created_idx: int


def neckline_value_at(pattern: HSPattern, idx: int) -> float:
    """Boyun çizgisinin (h1->h2) idx barındaki değeri (extend, iki yöne)."""
    return pattern.neckline_slope * idx + pattern.neckline_intercept


def find_hs(
    pivots: list[Pivot],
    kind: HSKind = "tobo",
    sym_tol: float = 0.5,
    neck_slope_max: float = 0.01,
    neck_total_slope_max: float = 0.15,
) -> list[HSPattern]:
    """pivots'taki (bar_idx sırasına göre) her ardışık 5'li pencereyi dener.

    Geçerlilik: (1) kind dizisi tobo için low,high,low,high,low, obo için
    high,low,high,low,high olmalı; (2) head, l1/l3'ten daha EKSTREM olmalı
    (tobo: daha düşük low; obo: daha yüksek high); (3) boyun çizgisinin
    TOPLAM eğimi (bkz. `neck_total_slope_max` altındaki not) makul bir
    aralıkta kalmalı (~yatay/hafif eğimli boyun kuralı); (4) omuz
    simetrisi: |l1.price - l3.price| <= sym_tol * depth (depth =
    |head.price - boyun(head.bar_idx)|).

    `neck_slope_max` (DEPRECATED, artık KULLANILMIYOR — yalnızca geriye
    dönük API uyumluluğu için imzada duruyor): eskiden `(h2.price-h1.price)/
    (h2.bar_idx-h1.bar_idx)` (BAR BAŞINA eğim) `avg_price`'a normalize
    edilip SABİT bir eşikle (varsayılan 0.01) karşılaştırılıyordu. Bu YANLIŞ
    normalizeydi: 40 barlık bir formasyonda boyun çizgisinin TOPLAMDA
    %40 (0.01×40) eğilmesine izin veriyordu — "yaklaşık yatay boyun" kuralı
    fiilen hiçbir şeyi elemiyordu (bkz. STRATEJI_DENETIM_TAM.md). Faz 1, 1C
    DÜZELTMESİ: `neck_total_slope_max` — formasyon SÜRESİNE göre
    normalize edilmiş TOPLAM eğim (`|h2.price-h1.price|/avg_price`,
    varsayılan 0.15 = boyun formasyon boyunca en fazla %15 eğilebilir).

    Aynı pivot dizisinde üst üste binen pencereler (ör. i ve i+2) BAĞIMSIZ
    aday olarak değerlendirilir — eleme/öncelik sırası bu fonksiyonun
    sorumluluğunda değildir (trendlines/channels'daki max_lines/max_channels
    gibi bir seçim kriteri burada YOK, çağıran filtreleyebilir)."""
    del neck_slope_max  # DEPRECATED, bkz. docstring — yalnızca API uyumluluğu
    if kind == "tobo":
        expected_kinds = ("low", "high", "low", "high", "low")
    elif kind == "obo":
        expected_kinds = ("high", "low", "high", "low", "high")
    else:
        raise ValueError("kind 'tobo' ya da 'obo' olmalı")

    ordered = sorted(pivots, key=lambda p: p.bar_idx)
    results: list[HSPattern] = []

    for i in range(len(ordered) - 4):
        window = ordered[i : i + 5]
        if tuple(p.kind for p in window) != expected_kinds:
            continue
        l1, h1, head, h2, l3 = window

        if kind == "tobo":
            if not (head.price < l1.price and head.price < l3.price):
                continue
        else:
            if not (head.price > l1.price and head.price > l3.price):
                continue

        if h2.bar_idx == h1.bar_idx:
            continue
        neck_slope = (h2.price - h1.price) / (h2.bar_idx - h1.bar_idx)
        neck_intercept = h1.price - neck_slope * h1.bar_idx
        avg_price = (h1.price + h2.price) / 2.0
        if avg_price == 0:
            continue
        # Faz 1, 1C — TOPLAM eğim (bkz. docstring'deki `neck_slope_max`
        # DEPRECATED notu), bar başına DEĞİL.
        total_rise = abs(h2.price - h1.price) / abs(avg_price)
        if total_rise > neck_total_slope_max:
            continue

        neck_at_head = neck_slope * head.bar_idx + neck_intercept
        depth = abs(head.price - neck_at_head)
        if depth == 0:
            continue
        if abs(l1.price - l3.price) > sym_tol * depth:
            continue

        neck_at_l3 = neck_slope * l3.bar_idx + neck_intercept
        target = neck_at_l3 + depth if kind == "tobo" else neck_at_l3 - depth

        results.append(
            HSPattern(
                kind=kind, l1=l1, h1=h1, head=head, h2=h2, l3=l3,
                neckline_slope=neck_slope, neckline_intercept=neck_intercept,
                depth=depth, target=target, created_idx=l3.confirmed_idx,
            )
        )

    return results
