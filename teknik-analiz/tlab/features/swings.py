"""Non-repainting swing pivot tespiti ve zigzag.

Bir bar pivot high/low olarak ANCAK confirmed_idx (=i+right ya da ATR
zigzag'de dönüşün onaylandığı bar) barında bilinir; bu bardan önce
hiçbir sonuçta görünmemelidir (walk-forward: df[:cut] üzerinde hesaplanan
sonuç, tam df'nin cut'a kadarki kısmıyla birebir aynı olmalı).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

import pandas as pd

from tlab.features.volatility import atr

PivotKind = Literal["high", "low"]
PivotLabel = Literal["HH", "HL", "LH", "LL"] | None
EqPolicy = Literal["strict", "nonstrict"]


@dataclass(frozen=True)
class Pivot:
    """Bir swing pivot noktası.

    bar_idx/bar_time: pivotun oluştuğu (ekstrem) bar.
    confirmed_idx/confirmed_time: pivotun komşularına göre bir aday olarak
    DOĞRULANDIĞI bar (bar_idx'ten sonra veya eşit).
    finalized_idx/finalized_time: alternate_pivots'tan geçtikten sonra,
    pivotun artık aynı-türden daha ekstrem bir pivot tarafından İPTAL
    EDİLEMEYECEĞİNİN kesinleştiği bar (find_pivots ham çıktısında None'dır).
    label: yalnızca label_structure'dan geçtikten sonra doldurulur.
    """

    bar_idx: int
    bar_time: pd.Timestamp
    price: float
    kind: PivotKind
    confirmed_idx: int
    confirmed_time: pd.Timestamp
    label: PivotLabel = None
    finalized_idx: int | None = None
    finalized_time: pd.Timestamp | None = None


def find_pivots(
    df: pd.DataFrame, left: int, right: int, eq_policy: EqPolicy = "nonstrict"
) -> list[Pivot]:
    """Sabit sol/sağ pencereli pivot high/low tespiti.

    nonstrict (varsayılan): high[i] > high[i-left:i] (katı) VE
    high[i] >= high[i+1:i+right+1] (gevşek) — sağ tarafta eşitliğe izin
    verir (henüz kesin olarak daha yükseği gelmediği sürece aday kabul
    edilir). strict: her iki tarafta da katı (>). low için işaretler ters
    çevrilir.

    Kural: bar i, ancak i+right barında ONAYLANIR (confirmed_idx=i+right).
    Serinin son `right` barında (henüz onaylanamayacakları için) pivot
    ARANMAZ.
    """
    if left < 1 or right < 1:
        raise ValueError("left ve right >= 1 olmalı")

    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    n = len(df)
    pivots: list[Pivot] = []

    for i in range(left, n - right):
        left_high = high[i - left : i]
        right_high = high[i + 1 : i + right + 1]
        if eq_policy == "nonstrict":
            is_high = bool((high[i] > left_high).all() and (high[i] >= right_high).all())
        else:
            is_high = bool((high[i] > left_high).all() and (high[i] > right_high).all())
        if is_high:
            pivots.append(
                Pivot(
                    bar_idx=i,
                    bar_time=df.index[i],
                    price=float(high[i]),
                    kind="high",
                    confirmed_idx=i + right,
                    confirmed_time=df.index[i + right],
                )
            )

        left_low = low[i - left : i]
        right_low = low[i + 1 : i + right + 1]
        if eq_policy == "nonstrict":
            is_low = bool((low[i] < left_low).all() and (low[i] <= right_low).all())
        else:
            is_low = bool((low[i] < left_low).all() and (low[i] < right_low).all())
        if is_low:
            pivots.append(
                Pivot(
                    bar_idx=i,
                    bar_time=df.index[i],
                    price=float(low[i]),
                    kind="low",
                    confirmed_idx=i + right,
                    confirmed_time=df.index[i + right],
                )
            )

    pivots.sort(key=lambda p: (p.confirmed_idx, p.bar_idx, p.kind))
    return pivots


def alternate_pivots(pivots: list[Pivot], include_pending: bool = False) -> list[Pivot]:
    """Ham pivot listesini gerçek bir zigzag'e indirger.

    Ardışık aynı-türden pivotlardan yalnızca en ekstrem olan (en yüksek
    high / en düşük low) zigzag'da kalır. Kesinleşme kuralı: bir pivot
    ancak kendisinden SONRA zıt türde bir pivot ONAYLANDIĞINDA
    finalized_idx alır — o ana kadar aynı türden daha ekstrem bir pivot
    onu iptal edebilir, ve bu iptal NON-REPAINT gereği yeni (iptal eden)
    pivotun onay barında gerçekleşir, eski pivotun kendi barında değil.

    Serinin en sonundaki, henüz zıt türde bir pivotla "kapatılmamış" pivot
    varsayılan olarak DIŞLANIR (resample.py'deki drop_open deseniyle
    paralel: dönen her şey gerçekten kesinleşmiştir). include_pending=True
    verilirse bu uç pivot da finalized_idx=None ile eklenir — yalnızca
    görselleştirme/hata ayıklama amaçlı, indikatör sonucuna ASLA gitmemeli.

    pivots, confirmed_idx'e göre artan sırada olmalı (find_pivots/atr_zigzag
    zaten bu sırayla döner).
    """
    ordered = sorted(pivots, key=lambda p: (p.confirmed_idx, p.bar_idx, p.kind))

    zigzag: list[Pivot] = []
    pending: Pivot | None = None

    for p in ordered:
        if pending is None:
            pending = p
            continue
        if p.kind == pending.kind:
            is_more_extreme = (p.kind == "high" and p.price > pending.price) or (
                p.kind == "low" and p.price < pending.price
            )
            if is_more_extreme:
                pending = p
            continue
        zigzag.append(
            replace(pending, finalized_idx=p.confirmed_idx, finalized_time=p.confirmed_time)
        )
        pending = p

    if pending is not None and include_pending:
        zigzag.append(pending)

    return zigzag


def label_structure(zigzag: list[Pivot]) -> list[Pivot]:
    """HH/HL/LH/LL etiketlerini atar.

    Etiket, önceki AYNI türden pivotla (zigzag'daki bir önceki high<->high,
    low<->low) kıyaslanarak verilir. zigzag zaten kesinleşmiş pivotlardan
    oluştuğu için (alternate_pivots'tan geçmiş), etiketleme anı ek bir
    gecikme gerektirmez — pivotun kendi finalized_idx'inde bilinir.
    Eşitlik durumunda "daha yüksek/düşük" SAYILMAZ (katı karşılaştırma):
    eşit high -> LH, eşit low -> HL.

    İlk high ve ilk low etiketlenemez (kıyaslanacak önceki aynı-türden
    pivot yok) -> label=None kalır.
    """
    labeled: list[Pivot] = []
    last_high: Pivot | None = None
    last_low: Pivot | None = None

    for p in zigzag:
        if p.kind == "high":
            label: PivotLabel = None
            if last_high is not None:
                label = "HH" if p.price > last_high.price else "LH"
            last_high = p
        else:
            label = None
            if last_low is not None:
                label = "HL" if p.price > last_low.price else "LL"
            last_low = p
        labeled.append(replace(p, label=label))

    return labeled


def atr_zigzag(df: pd.DataFrame, atr_mult: float = 2.0, atr_period: int = 14) -> list[Pivot]:
    """ATR tabanlı ters dönüş eşiğiyle zigzag.

    Fiyat, mevcut uçtan (son pivot ya da seri başlangıcı) atr_mult * ATR
    kadar ters yöne gittiği BARDA dönüş onaylanır: yeni pivot bar_idx'i
    o ana kadarki en ekstrem (uç) bar, confirmed_idx dönüşün fiilen
    gerçekleştiği (mevcut) bardır. ATR, dönüş anındaki (o bara kadar
    hesaplanmış, yalnızca geçmişe bakan) değeriyle kullanılır.

    find_pivots ile aynı Pivot arayüzünü döner (finalized_idx boş kalır;
    zaten doğası gereği tek yönlü/alternatiflenmiş bir zigzag ürettiği
    için gerekirse alternate_pivots'a da verilebilir).
    """
    n = len(df)
    pivots: list[Pivot] = []
    if n == 0:
        return pivots

    atr_series = atr(df, atr_period)
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()

    ext_high_idx, ext_high_val = 0, high[0]
    ext_low_idx, ext_low_val = 0, low[0]
    direction: Literal["up", "down"] | None = None

    for i in range(1, n):
        a = atr_series.iloc[i]
        if pd.isna(a):
            if high[i] > ext_high_val:
                ext_high_idx, ext_high_val = i, high[i]
            if low[i] < ext_low_val:
                ext_low_idx, ext_low_val = i, low[i]
            continue

        # Dönüş kontrolü DAİMA önceki (bu barda henüz güncellenmemiş) uç
        # değere göre yapılır — aksi halde aynı bar hem yeni uç olur hem de
        # kendi barında "onaylanmış" sayılır (bar_idx==confirmed_idx, barlar
        # arası sıralama garantisini bozar; intrabar high/low sırası zaten
        # bilinmez).
        if direction != "down" and ext_high_val - low[i] >= atr_mult * a:
            pivots.append(
                Pivot(
                    bar_idx=ext_high_idx,
                    bar_time=df.index[ext_high_idx],
                    price=float(ext_high_val),
                    kind="high",
                    confirmed_idx=i,
                    confirmed_time=df.index[i],
                )
            )
            direction = "down"
            ext_low_idx, ext_low_val = i, low[i]
            continue

        if direction != "up" and high[i] - ext_low_val >= atr_mult * a:
            pivots.append(
                Pivot(
                    bar_idx=ext_low_idx,
                    bar_time=df.index[ext_low_idx],
                    price=float(ext_low_val),
                    kind="low",
                    confirmed_idx=i,
                    confirmed_time=df.index[i],
                )
            )
            direction = "up"
            ext_high_idx, ext_high_val = i, high[i]
            continue

        if direction != "down" and high[i] > ext_high_val:
            ext_high_idx, ext_high_val = i, high[i]
        if direction != "up" and low[i] < ext_low_val:
            ext_low_idx, ext_low_val = i, low[i]

    return pivots
