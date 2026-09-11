"""Komposer giriş tipleri — göstergeyle grafik arasındaki SÖZLEŞME.

Eski mimaride gösterge, jenerik bir primitif torbası (`Line`/`Box`/
`Marker`) döndürüyordu ve tek bir renderer hepsini aynı biçimde basıyordu.
Buradaki tipler bunun yerine geçer: her arketip için AÇIK alanları olan
bir tip var, komposer o alanları çizer. Eksik/yanlış bir alan sessizce
boş çizilemez — tip tutmaz.

Bkz. `docs/KOMPOSER_HARITASI.md`.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tlab.chart.tokens import Role


@dataclass(frozen=True)
class BoundaryTouch:
    """Sınır çizgisine temas. Referansta numaralı içi boş daire (U1, L3...)."""

    t: pd.Timestamp
    price: float
    label: str
    above: bool


@dataclass(frozen=True)
class BoundaryLine:
    """Formasyon sınırı. `points` en az iki nokta — yatay için iki uç,
    eğimli/kırıklı için daha fazlası. Çizgi YALNIZCA bu noktalar arasında
    uzanır, grafik kenarına kadar uzatılmaz."""

    points: tuple[tuple[pd.Timestamp, float], ...]
    role: Role
    name: str
    touches: tuple[BoundaryTouch, ...] = ()
    dash: str | None = None

    def __post_init__(self) -> None:
        if len(self.points) < 2:
            raise ValueError(f"{self.name}: sınır çizgisi en az 2 nokta ister")


@dataclass(frozen=True)
class ChartSignal:
    """Grafiğe basılacak AL/SAT/İZLE kutusu."""

    t: pd.Timestamp
    price: float
    text: str
    role: Role
    below: bool = True


@dataclass(frozen=True)
class BoundaryPattern:
    """Sınır çizgileriyle tanımlanan her formasyon.

    Kapsadıkları: yatay aralık, yükselen/alçalan kanal, simetrik/yükselen/
    alçalan üçgen, kama, genişleyen formasyon, kırılım seviyeleri.
    Hepsi aynı grafik iskeletini kullanır; fark yalnızca sınırların
    geometrisi ve vurgu rengidir (bkz. referans HRiOTwUbQAA9WKw ile
    HRiPy4qbUAA1bKc — birebir aynı şablon).
    """

    kind: str
    title: str
    state: str
    boundaries: tuple[BoundaryLine, ...]
    facts: tuple[tuple[str, str], ...] = ()
    band: tuple[float, float] | None = None
    band_label: str = ""
    band_role: Role = "accent"
    signal: ChartSignal | None = None
    bars_ago: int | None = None

    def __post_init__(self) -> None:
        if not self.boundaries:
            raise ValueError(f"{self.kind}: en az bir sınır çizgisi gerekli")

    @property
    def touch_count(self) -> int:
        return sum(len(b.touches) for b in self.boundaries)


@dataclass(frozen=True)
class XabcdPoint:
    t: pd.Timestamp
    price: float
    label: str           # "X", "A", "B", "C", "D"


@dataclass(frozen=True)
class XabcdPattern:
    """Harmonik / ABCD formasyonları.

    Kapsadıkları: 8 harmonik okul (`harmonic.*`) ve
    `structure.swing_fib_abcd`. Hepsi aynı çizimi ister: X-A-B-C-D
    poligonu (yarı saydam dolgu + net kenar), köşe etiketleri, PRZ bandı,
    fibo merdiveni, ve D'de sinyal kutusu.

    Referans: `önemli/HRhIeAdbcAAL2_B.png` (dolgulu gövde + sağ kenar fibo
    merdiveni) ve `önemli/HRdEu6qaoAEaHIT.png` (teorik D / gerçek D ayrımı).
    """

    school: str                       # "carney", "gilmore", "abcd", ...
    pattern_name: str                 # "gartley", "bat", ...
    direction: str                    # "bullish" | "bearish"
    points: tuple[XabcdPoint, ...]    # X, A, B, C (+ D varsa)
    state: str                        # "izlemede" | "aktif" | "tamamlandi" | "gecersiz"
    prz: tuple[float, float] | None   # potansiyel dönüş bölgesi (alt, üst)
    theoretical_d: float | None       # hesaplanan hedef D
    actual_d: XabcdPoint | None       # gerçekleşen D
    fib_levels: tuple[tuple[float, float, str], ...] = ()
    ratios: tuple[tuple[str, str], ...] = ()   # ("AB/XA", "0.618") gibi
    bars_ago: int | None = None

    def __post_init__(self) -> None:
        labels = [p.label for p in self.points]
        # İKİ geçerli iskelet:
        #  * X,A,B,C(,D) -- 5 noktalı harmonikler (Gartley/Bat/Crab/...)
        #  * A,B,C(,D)   -- 4 noktalı AB=CD (`structure.swing_fib_abcd`)
        #
        # AB=CD, XABCD'nin eksik hâli DEĞİL; kendi başına bir formasyon.
        # Literatür bunu net ayırıyor: 5 noktalı harmonikler 3/4 noktalı
        # ABCD'yi İÇERİR ("patterns have embedded 3-point (ABC) or
        # four-level (ABCD) patterns"), yani ABCD daha temel bir yapı --
        # Gartley'in özgün formasyonuna Fibonacci oranlarını ilk uygulayan
        # Pesavento'nun AB=CD'si de X'siz. Sözleşme X'i ZORUNLU tutunca
        # `swing_fib_abcd` bağlanamıyordu (uydurma bir X eklemek yanlış
        # geometri üretirdi).
        if labels[:4] != ["X", "A", "B", "C"] and labels[:3] != ["A", "B", "C"]:
            raise ValueError(
                f"noktalar X,A,B,C (harmonik) ya da A,B,C (AB=CD) ile başlamalı — "
                f"alınan: {labels}"
            )
        if self.direction not in ("bullish", "bearish"):
            raise ValueError(f"yön 'bullish' veya 'bearish' olmalı — alınan: {self.direction!r}")
