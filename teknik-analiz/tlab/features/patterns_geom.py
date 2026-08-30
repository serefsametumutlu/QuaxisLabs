"""İki trend çizgisinin göreli geometrisi: yakınsama testi, apex, sınıflama.

Bu modül `Trendline` nesnelerinin (zaten `trendlines.build_trendlines`'dan
non-repaint olarak üretilmiş — slope/intercept p1/p2 pivotları KESİNLEŞTİĞİ
anda sabitlenir, bir daha değişmez) SAF geometrisiyle ilgilenir; df'ye hiç
dokunmaz. Bu yüzden `converging_lines`/`classify` doğası gereği non-repaint'tir
— girdi Trendline'lar zaten repaint-safe olduğu sürece (bkz. trendlines.py
docstring'i, "aday havuzu" istisnası) çıktı da öyledir.

`classify()`, spec'teki 7 türü döner: 'falling_wedge', 'rising_wedge',
'sym_triangle', 'asc_triangle', 'desc_triangle', 'flag', 'pennant' (veya
tanınan bir şekil yoksa None). "Sınıflandırma, ilgili son pivotun ONAY
barında verilir" kuralı burada `ConvergingLines.created_idx` ile taşınır —
çağıran (ör. Faz 8B wedge.py) bunu Signal.detected_at olarak kullanmalı.

TASARIM KARARI (spec'te belirtilmeyen bir ayrım): 'flag'/'pennant', saf
geometriden (upper/lower slope işaretleri + yakınsama) TÜRETİLEMEZ — ikisi
de klasik TA tanımında "önceki keskin harekete (direk/pole) göre KÜÇÜK bir
konsolidasyon" gerektirir. Bu yüzden `classify()` opsiyonel bir `pole_range`
parametresi alır (direk büyüklüğü, fiyat cinsinden): yalnızca verilirse VE
desen created_idx'teki yüksekliği pole_range'in `small_pattern_ratio`
oranından küçükse simetrik yakınsama 'pennant', neredeyse paralel/aynı
yönlü yakınsamayan çizgiler 'flag' olarak raporlanır; aksi halde (pole_range
verilmemişse) bu iki tür hiç dönmez ('sym_triangle' ya da None döner) —
pole bilgisi olmadan flag/pennant iddiası temelsiz olurdu.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from tlab.core.params import BaseParams
from tlab.features.trendlines import Trendline

PatternShape = Literal[
    "falling_wedge", "rising_wedge", "sym_triangle", "asc_triangle", "desc_triangle",
    "flag", "pennant",
]

_SlopeSign = Literal["up", "down", "flat"]


@dataclass(frozen=True)
class ConvergingLines:
    """`upper`/`lower` iki trend çizgisinin (aynı df üzerinde, upper tipik
    olarak resistance/lower support Trendline'ı) göreli geometrisi.

    created_idx: iki çizginin İKİSİNİN de var olduğu ilk bar
    (max(upper.created_idx, lower.created_idx)) — sınıflandırma bu barda
    "onaylanmış" sayılır. slope_ratio: |upper.slope| / |lower.slope|
    (payda sıfırsa `math.inf`, ikisi de sıfırsa 1.0). apex_idx/apex_price:
    iki çizginin (uzatıldığında) kesiştiği nokta — çizgiler paralelse
    (slope eşit) None. is_converging: created_idx'te upper gerçekten
    lower'ın üstünde VE apex created_idx'ten SONRA (ileride) VE gap
    created_idx'ten itibaren daralıyor.
    """

    upper: Trendline
    lower: Trendline
    created_idx: int
    slope_ratio: float
    is_converging: bool
    apex_idx: float | None
    apex_price: float | None


def _safe_ratio(a: float, b: float) -> float:
    if b == 0:
        return math.inf if a != 0 else 1.0
    return abs(a) / abs(b)


def converging_lines(upper: Trendline, lower: Trendline) -> ConvergingLines:
    """İki çizginin eğim oranını, apex'ini ve yakınsama durumunu hesaplar.

    Yalnızca `Trendline.slope`/`intercept`/`created_idx` kullanır — df'ye
    erişmez, bu yüzden sonuç girdi çizgiler sabit kaldığı sürece (ki
    Trendline zaten frozen) DAİMA aynıdır."""
    created_idx = max(upper.created_idx, lower.created_idx)
    gap_at_created = upper.value_at(created_idx) - lower.value_at(created_idx)
    gap_slope = upper.slope - lower.slope

    if gap_slope == 0:
        apex_idx: float | None = None
        apex_price: float | None = None
        is_converging = False
    else:
        apex_idx = (lower.intercept - upper.intercept) / (upper.slope - lower.slope)
        apex_price = upper.value_at(apex_idx)
        is_converging = gap_at_created > 0 and gap_slope < 0 and apex_idx > created_idx

    return ConvergingLines(
        upper=upper,
        lower=lower,
        created_idx=created_idx,
        slope_ratio=_safe_ratio(upper.slope, lower.slope),
        is_converging=is_converging,
        apex_idx=apex_idx,
        apex_price=apex_price,
    )


@dataclass(frozen=True)
class ClassifyParams(BaseParams):
    """`classify()`'ın eşik tablosu.

    flat_ratio: bir çizgi, diğerinin |slope|'unun bu oranından azsa "düz"
    (yatay) sayılır -> asc/desc üçgen adaylığı.
    parallel_tol: aynı yönlü (ikisi de up/ikisi de down) VE yakınsamayan
    çizgilerde slope_ratio 1'e bu tolerans içinde yakınsa "neredeyse
    paralel kanal" (flag adayı, yalnızca pole_range ile raporlanır).
    small_pattern_ratio: created_idx'teki desen yüksekliği pole_range'in
    bu oranından küçükse "küçük/sıkı konsolidasyon" (flag/pennant adaylığı).
    """

    flat_ratio: float = 0.15
    parallel_tol: float = 0.20
    small_pattern_ratio: float = 0.5


@dataclass(frozen=True)
class DivergingLines:
    """`upper`/`lower`'ın created_idx'ten itibaren birbirinden UZAKLAŞTIĞI
    (genişleyen üçgen/megafon — 'broadening') geometrisi. `converging_lines`'ın
    tersi: apex YOKTUR (ileride hiç kesişmezler), bu yüzden apex/slope_ratio
    hesaplanmaz — yalnızca created_idx'te gap pozitif VE gap_slope pozitifse
    (mesafe zamanla büyüyorsa) `is_diverging=True`. Formasyonun 'top' mu
    'bottom' mu (Faz 8B `patterns/broadening.py`) son pivotların pozisyonuna
    göre çağıran tarafından ayrıca belirlenir — bu fonksiyon yalnızca SAF
    iki-çizgi geometrisiyle ilgilenir."""

    upper: Trendline
    lower: Trendline
    created_idx: int
    is_diverging: bool


def diverging_lines(upper: Trendline, lower: Trendline) -> DivergingLines:
    """İki çizginin created_idx'ten itibaren birbirinden uzaklaşıp
    uzaklaşmadığını hesaplar — yalnızca `Trendline.slope`/`intercept`/
    `created_idx` kullanır, df'ye erişmez (girdi çizgiler sabit kaldığı
    sürece sonuç DAİMA aynıdır, non-repaint)."""
    created_idx = max(upper.created_idx, lower.created_idx)
    gap_at_created = upper.value_at(created_idx) - lower.value_at(created_idx)
    gap_slope = upper.slope - lower.slope
    is_diverging = gap_at_created > 0 and gap_slope > 0
    return DivergingLines(
        upper=upper, lower=lower, created_idx=created_idx, is_diverging=is_diverging,
    )


def _slope_sign(this_slope: float, other_slope: float, flat_ratio: float) -> _SlopeSign:
    if abs(this_slope) <= flat_ratio * max(abs(other_slope), 1e-12):
        return "flat"
    return "up" if this_slope > 0 else "down"


def classify(
    conv: ConvergingLines,
    params: ClassifyParams | None = None,
    pole_range: float | None = None,
) -> PatternShape | None:
    """`conv`'un geometrisini 7 türden birine (veya None'a) sınıflar.

    pole_range: opsiyonel, desenden HEMEN ÖNCEKİ keskin hareketin büyüklüğü
    (fiyat cinsinden) — yalnızca verilirse flag/pennant değerlendirilir
    (bkz. modül docstring'i, tasarım kararı)."""
    p = params or ClassifyParams()
    up_sign = _slope_sign(conv.upper.slope, conv.lower.slope, p.flat_ratio)
    low_sign = _slope_sign(conv.lower.slope, conv.upper.slope, p.flat_ratio)
    near_parallel = abs(conv.slope_ratio - 1.0) <= p.parallel_tol

    base: str | None
    if up_sign == "flat" and low_sign == "up":
        base = "asc_triangle"
    elif low_sign == "flat" and up_sign == "down":
        base = "desc_triangle"
    elif up_sign == "down" and low_sign == "up" and conv.is_converging:
        base = "sym_triangle"
    elif up_sign == "down" and low_sign == "down" and conv.is_converging:
        base = "falling_wedge"
    elif up_sign == "up" and low_sign == "up" and conv.is_converging:
        base = "rising_wedge"
    elif up_sign == low_sign and up_sign != "flat" and not conv.is_converging and near_parallel:
        base = "_channel"
    else:
        return None

    height = abs(conv.upper.value_at(conv.created_idx) - conv.lower.value_at(conv.created_idx))
    is_small = (
        pole_range is not None and pole_range > 0 and height <= p.small_pattern_ratio * pole_range
    )

    if base == "sym_triangle":
        return "pennant" if is_small else "sym_triangle"
    if base == "_channel":
        return "flag" if is_small else None
    return base  # type: ignore[return-value]
