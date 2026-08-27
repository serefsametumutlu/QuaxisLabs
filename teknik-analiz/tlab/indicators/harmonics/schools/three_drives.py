"""Three Drives (Ch.7) — X=drive1, A=düzeltme1, B=drive2, C=düzeltme2,
D=drive3 (projeksiyon). Standart XABCD adayı yeniden kullanılır ama
retracement değil İMPULSİF DEVAM istenir: B, X'i aşmalı (b_beyond_x=True).

Oran eşlemesi:
- ab_xa (candidate.ab_xa) = drive2'nin (X->A) bacağına göre uzantısı,
  hedef {1.272, 1.618} — AB=CD zincirindeki ilk bacağın kendisi.
- bc_ab (candidate.abc) = düzeltme2'nin drive2 bacağını geri çekilmesi,
  hedef 0.618-0.786.
- D (drive3): klasik AB=CD projeksiyonu (D = C + ratio*(B-A)), "abcd"
  bacak koduyla — ratio, xab'daki İLE AYNI aile (1.272 ya da 1.618) olacak
  şekilde iki ayrı PatternSpec varyantı ("three_drives_1272"/"_1618").

İki oran ailesi arasından hangisinin geçerli olacağına dair kitapta kesin
bir "ikisi aynı olmalı" şartı yoktu — sembolik yakınlık (near-perfect
symmetry) vurgusu vardı; burada basitleştirilerek AYNI aile şartı konuldu
(varsayım, dokümante edildi)."""

from __future__ import annotations

from tlab.indicators.harmonics.schools.base import HarmonicSchool, PatternSpec

_TOL = 0.08


def _pt(v: float, tol: float = _TOL) -> tuple[float, float]:
    return (v - tol, v + tol)


class ThreeDrivesSchool(HarmonicSchool):
    name = "three_drives"
    tolerance = _TOL

    def __init__(self) -> None:
        self.patterns = {
            "three_drives_1272": PatternSpec(
                name="three_drives_1272", xab=_pt(1.272), abc=(0.618 - _TOL, 0.786 + _TOL),
                d_components=(("abcd", 1.272 - _TOL, 1.272 + _TOL),),
                prz_method="single_pm_tol", b_beyond_x_required=True,
                invalidation=("abcd", 1.618),
            ),
            "three_drives_1618": PatternSpec(
                name="three_drives_1618", xab=_pt(1.618), abc=(0.618 - _TOL, 0.786 + _TOL),
                d_components=(("abcd", 1.618 - _TOL, 1.618 + _TOL),),
                prz_method="single_pm_tol", b_beyond_x_required=True,
                invalidation=("abcd", 2.0),
            ),
        }
