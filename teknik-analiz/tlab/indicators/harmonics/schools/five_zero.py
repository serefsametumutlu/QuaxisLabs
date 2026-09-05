"""5-0 Formasyonu (6 noktalı: 0-X-A-B-C, D projeksiyonu). A, 0X bacağının
1.13-1.618 uzantısıdır; B ise XA'nın 1.618-2.24 uzantısı (candidate.ab_xa
ile aynı formül, standart xab alanı üzerinden kontrol edilir). D = BC'nin
tam %50 geri çekilmesi. Ek: CD ≈ AB (post-prz). Yapısal trend dönüş teyidi
(label_structure kırılımı) bilinçli olarak KAPSAM DIŞI bırakıldı — bu,
scanner_indicator.py seviyesinde ayrı bir zigzag etiketleme geçişi
gerektirir; ilk sürümde yalnızca oran kuralları uygulanır.

**GERÇEK bir hata bulunup düzeltildi (Faz 5, 2026-09-05):** CLAUDE.md'de
belgelenen "harmonic.five_zero 622 sembollük TAM BIST evreninde HİÇBİR
aday bulamadı" bulgusunun kök nedeni — `c_beyond_a_required` VARSAYILAN
(`False`) bırakılmıştı. Bu, D = C + 0.5*(B-C) (bc_ret, B'ye doğru %50
geri çekilme) formülüyle BİRLİKTE MATEMATİKSEL OLARAK İMKANSIZ bir
kombinasyon üretiyordu: C, A ile B arasında (A'yı AŞMADAN) kalmaya
zorlanınca BC <= AB olmak ZORUNDA kalıyor, bu yüzden CD = 0.5*BC HER
ZAMAN AB'nin en fazla YARISI kadar olabiliyordu — ama `_post_prz_match`
CD ≈ AB (±%5) istiyordu. Yani `c_beyond_a_required=False` iken CD=AB
şartı HİÇBİR fiyat serisinde sağlanamazdı (kanıt: elle kurulmuş bir
sentetik 5-0 adayıyla doğrulandı — `c_beyond_a_required=True` yapılınca
AYNI aday eşleşti, `False` iken asla eşleşmedi). Düzeltme:
`c_beyond_a_required=True` — C, A'yı AŞAR (BC yeterince büyüyebilir,
CD=0.5*BC artık AB'ye ulaşabilir)."""

from __future__ import annotations

from tlab.features.fibonacci import ratio, within
from tlab.indicators.harmonics.geometry import Candidate
from tlab.indicators.harmonics.prz import PRZ
from tlab.indicators.harmonics.schools.base import HarmonicSchool, PatternSpec

_TOL = 0.05


class FiveZeroSchool(HarmonicSchool):
    name = "five_zero"
    tolerance = _TOL

    def __init__(self) -> None:
        self.patterns = {
            "five_zero": PatternSpec(
                name="five_zero", xab=(1.618, 2.24), abc=None,
                d_components=(("bc_ret", 0.5 - _TOL, 0.5 + _TOL),),
                prz_method="single_pm_tol", requires_zero=True, b_beyond_x_required=True,
                c_beyond_a_required=True,
                invalidation=("bc_ret", 1.0),
            ),
        }

    def _extra_match(self, candidate: Candidate, spec: PatternSpec) -> bool:
        if candidate.zero is None:
            return False
        a_ratio = ratio(candidate.zero.price, candidate.x.price, candidate.a.price)
        return within(a_ratio, 1.13, 1.618)

    def _post_prz_match(self, candidate: Candidate, spec: PatternSpec, prz: PRZ) -> bool:
        ab = abs(candidate.b.price - candidate.a.price)
        if ab == 0:
            return False
        cd_ab = abs(prz.center - candidate.c.price) / ab
        return within(cd_ab, 1.0 - self.tolerance, 1.0 + self.tolerance)
