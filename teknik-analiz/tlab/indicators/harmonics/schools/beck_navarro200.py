"""Ross Beck — Navarro 200. C, AB'nin uzantısıdır (B'yi de A'yı da aşar);
D = XA'nın tam %200 uzantısı (dar PRZ).

NOT (uygulama sırasında düzeltilen tasarım kararı): spesifikasyonda ek bir
"CD, AB'nin 1.27/1.618 uzantısı olmalı" şartı da öngörülmüştü, ancak D
yalnızca X,A'dan (200% XA) hesaplandığı ve C, B'nin ötesine (A'yı aşarak)
gittiği için, bu iki şart birlikte GEOMETRİK OLARAK TUTARSIZ çıkıyor: D,
C'den A boyunun birkaç katı uzaklıkta kalıyor, CD/AB oranı gerçekçi xab
(0.382-0.618) değerleriyle asla 1.27-1.618 aralığına düşmüyor (brüt-kuvvet
doğrulamayla saptandı). Bu yüzden ek şart kaldırıldı — B ve D oranları
formasyonu zaten tam belirliyor."""

from __future__ import annotations

from tlab.indicators.harmonics.schools.base import HarmonicSchool, PatternSpec

_TOL = 0.03


class Navarro200School(HarmonicSchool):
    name = "navarro200"
    tolerance = _TOL

    def __init__(self) -> None:
        self.patterns = {
            "navarro200": PatternSpec(
                name="navarro200", xab=(0.382, 0.618), abc=(1.272, 1.618),
                d_components=(("xa_ext", 2.0 - _TOL / 2, 2.0 + _TOL / 2),),
                prz_method="single_pm_tol", c_beyond_a_required=True,
                invalidation=("xa_ext", 2.24),
            ),
        }
