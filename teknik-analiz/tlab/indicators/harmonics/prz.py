"""PRZ (Potential Reversal Zone) hesaplama — D noktası HENÜZ gerçekleşmeden
bile X,A,B,C fiyatlarından tamamen deterministik olarak hesaplanabilir.

Bacak kodları tek bir `fibonacci.extension(p0, p1, levels)` çağrısıyla
ifade edilir: her kod bir (p0,p1) çifti seçer, r=1.0 tam p1'i verir, r<1
p1'e doğru bir geri çekilme, r>1 p1'in ötesine bir uzantıdır (bkz.
_leg_price docstring'i). "_ret" / "_ext" isimlendirmesi yalnızca OKUNURLUK
içindir — hangisi çağrılacağı çağıranın verdiği r aralığına bağlıdır, iki
isim aynı bacağı paylaşabilir.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from tlab.features.fibonacci import extension, projection_abcd
from tlab.indicators.harmonics.geometry import Candidate

PRZMethod = Literal["intersection", "single_pm_tol"]

# (bacak_kodu, lo, hi) — D'nin bu bacağa göre projeksiyon aralığı.
DComponent = tuple[str, float, float]


@dataclass(frozen=True)
class PRZ:
    low: float
    high: float
    center: float
    components: dict[str, float]
    method: str


def _leg_price(c: Candidate, code: str) -> tuple[float, float]:
    """D projeksiyonu HER ZAMAN 'hedef bacağın SONUNA doğru, oradan öteye'
    biçiminde tek bir extension() çağrısıyla ifade edilir: r=1.0 tam hedef
    noktasını verir, r<1 ona doğru bir GERİ ÇEKİLME, r>1 onun ÖTESİNE bir
    UZANTI olur. Bu yüzden "xa_ret" (D, X'e doğru geri çeker) ile "xa_ext"
    (D, X'in ötesine uzanır — Butterfly/Crab) AYNI (A,X) bacağını kullanır;
    tek fark çağıranın verdiği r aralığıdır (<1 ya da >1). Aynı mantık
    "bc_ext" (D, B'nin ötesine — Gartley/Bat/Crab/Butterfly'nin BC-tabanlı
    bileşeni) ile "bc_ret" (D, B'ye doğru geri çekilir — five_zero) için de
    geçerli: ikisi de (C,B) bacağını kullanır.
    """
    x, a, b, cc = c.x.price, c.a.price, c.b.price, c.c.price
    if code in ("xa_ret", "xa_ext"):
        return (a, x)
    if code in ("bc_ext", "bc_ret"):
        return (cc, b)
    if code == "xc_ret":
        return (cc, x)
    if code == "0x_proj":
        if c.zero is None:
            raise ValueError("'0x_proj' bacağı için candidate.zero gerekli (shark/five_zero)")
        return (c.zero.price, x)
    raise ValueError(f"bilinmeyen bacak kodu: {code}")


def project_ratio(candidate: Candidate, code: str, ratio_: float) -> float:
    """Tek bir bacak kodu + oran için fiyat projeksiyonu (PRZ dışı kullanım
    için, ör. INVALIDATED eşiği) — compute_prz ile aynı bacak sözlüğünü kullanır."""
    if code == "abcd":
        a, b, c = candidate.a.price, candidate.b.price, candidate.c.price
        return projection_abcd(a, b, c, (ratio_,))[ratio_]
    p0, p1 = _leg_price(candidate, code)
    return extension(p0, p1, (ratio_,))[ratio_]


def compute_prz(
    candidate: Candidate, d_components: tuple[DComponent, ...], method: PRZMethod
) -> PRZ | None:
    """d_components boşsa None döner. intersection: tüm bileşen bantlarının
    kesişimi (kesişmiyorsa None). single_pm_tol: TEK bileşenin kendi
    (lo,hi) bandı doğrudan PRZ olur (birden fazla bileşen verilirse ilk
    kullanılır — çağıran taraf tek bileşen vermeli)."""
    if not d_components:
        return None

    bands: dict[str, tuple[float, float]] = {}
    for code, lo, hi in d_components:
        price_lo = project_ratio(candidate, code, lo)
        price_hi = project_ratio(candidate, code, hi)
        band_lo, band_hi = (price_lo, price_hi) if price_lo <= price_hi else (price_hi, price_lo)
        bands[f"{code}_{lo}_{hi}"] = (band_lo, band_hi)

    components = {k: (v[0] + v[1]) / 2.0 for k, v in bands.items()}

    if method == "single_pm_tol":
        band_lo, band_hi = next(iter(bands.values()))
        return PRZ(low=band_lo, high=band_hi, center=(band_lo + band_hi) / 2.0,
                   components=components, method=method)

    # intersection
    low = max(v[0] for v in bands.values())
    high = min(v[1] for v in bands.values())
    if low > high:
        return None
    return PRZ(low=low, high=high, center=(low + high) / 2.0, components=components, method=method)
