"""BOS (Break of Structure) / CHoCH (Change of Character) tespiti — Faz 4d
(`ornek1.png` standardı, `docs/GORSEL_HATA_TESHISI.md` bölüm 4).

Bu bir SMC/ICT ("Smart Money Concepts") kavramı: HH/HL (yükselen) ya da
LH/LL (düşen) dizisiyle tanımlanan bir "yapısal karakter" (trend), fiyatın
dizinin bir sonraki üyesini KAPANIŞLA aşmasıyla ya devam eder (BOS) ya da
tersine döner (CHoCH):

- **BOS** (devam): mevcut trend yönünde bir önceki yapısal zirvenin/dibin
  kapanışla aşılması. Yükselen trendde (son iz HH) son HH'nin üstüne kapanış
  → BOS↑; düşen trendde (son iz LH) son LL'nin altına kapanış → BOS↓.
- **CHoCH** (dönüş): trend yönünün TERSİNE İLK yapısal kırılım. Yükselen
  trendde son HL'nin (pullback dibi) kapanışla altına inilmesi → CHoCH↓;
  düşen trendde son LH'nin (pullback tepesi) kapanışla üstüne çıkılması
  → CHoCH↑.

Mimari: `tlab/features/swings.py::significant_pivots` + `label_structure`
zaten HH/HL/LH/LL etiketlerini üretiyor — bu modül YENİ bir pivot/zigzag
algoritması YAZMAZ, yalnızca o zigzag'in üstünde bar-bar bir "hangi seviye
hâlâ kırılmadı" durum makinesi işletir.

NON-REPAINT: `detect_market_structure` saf, tek geçişli bir taramadır —
her olay YALNIZCA `[0, bar_idx]` aralığına bakılarak, kapanışın o seviyeyi
AŞTIĞI barda üretilir; bir kez üretilen bir olay (kind/bar_idx/level) bir
daha değişmez/kaybolmaz (yalnızca AYNI pivotun kırdığı seviye "tüketilir",
her sonraki bar için yeniden değerlendirilmez — pivots argümanının kendisi
zaten prefix-tutarlı/non-repaint olduğu sürece bu fonksiyon da öyledir)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from tlab.features.swings import Pivot

MSEventKind = Literal["bos_up", "bos_down", "choch_up", "choch_down"]


@dataclass(frozen=True)
class StructureEvent:
    """Bir BOS/CHoCH olayı.

    bar_idx/bar_time: kırılımın KAPANIŞLA onaylandığı bar (bu bar sonradan
    DEĞİŞMEZ). level: kırılan yapısal seviyenin fiyatı (kırılan pivotun
    price'ı). source_pivot: kırılan seviyeyi oluşturan pivot (HH/HL/LH/LL
    etiketi/bar_time'ı için)."""

    kind: MSEventKind
    bar_idx: int
    bar_time: pd.Timestamp
    level: float
    source_pivot: Pivot

    @property
    def direction(self) -> Literal["up", "down"]:
        return "up" if self.kind in ("bos_up", "choch_up") else "down"

    @property
    def is_bos(self) -> bool:
        return self.kind in ("bos_up", "bos_down")


def detect_market_structure(df: pd.DataFrame, pivots: list[Pivot]) -> list[StructureEvent]:
    """Etiketlenmiş (`label_structure`'dan geçmiş, `bar_idx` artan) bir
    zigzag üzerinden BOS/CHoCH taraması.

    Durum: `bull_pivot` = henüz kırılmamış en son HIGH pivot (bull/CHoCH-up
    hedefi), `bear_pivot` = henüz kırılmamış en son LOW pivot. Her ikisi de
    kendi türünden YENİ bir pivot `finalized_idx`'inde (yoksa `confirmed_
    idx`'inde) güncellenir — böylece bir seviye, KENDİSİNDEN DAHA YENİ bir
    aynı-türden pivot oluşana kadar "izlemede" kalır.

    `trend`, ilk olaya kadar "neutral"dır — henüz bir "karakter" tesis
    edilmeden gelen İLK kırılım kavramsal olarak bir "değişim" değildir, bu
    yüzden BOS sayılır (trend'i o yöne başlatır); sonraki her kırılım o an
    ki `trend`e göre BOS (aynı yön) ya da CHoCH (ters yön) olarak sınıflanır.
    """
    n = len(df)
    close = df["close"].to_numpy()

    events: list[StructureEvent] = []
    trend: Literal["up", "down", "neutral"] = "neutral"
    bull_pivot: Pivot | None = None
    bear_pivot: Pivot | None = None

    def ready_idx(p: Pivot) -> int:
        return p.finalized_idx if p.finalized_idx is not None else p.confirmed_idx

    ordered = sorted(pivots, key=lambda p: (ready_idx(p), p.bar_idx))
    pi = 0

    for i in range(n):
        while pi < len(ordered) and ready_idx(ordered[pi]) <= i:
            p = ordered[pi]
            if p.kind == "high":
                bull_pivot = p
            else:
                bear_pivot = p
            pi += 1

        if bull_pivot is not None and close[i] > bull_pivot.price:
            kind: MSEventKind = "choch_up" if trend == "down" else "bos_up"
            events.append(StructureEvent(kind, i, df.index[i], bull_pivot.price, bull_pivot))
            trend = "up"
            bull_pivot = None

        if bear_pivot is not None and close[i] < bear_pivot.price:
            kind = "choch_down" if trend == "up" else "bos_down"
            events.append(StructureEvent(kind, i, df.index[i], bear_pivot.price, bear_pivot))
            trend = "down"
            bear_pivot = None

    return events
