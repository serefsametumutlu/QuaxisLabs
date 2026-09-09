"""Three Drives doğrulama kuralları.

Kullanıcının verdiği çerçeve (2026-09-08) aynen uygulanıyor:

  *"Bu formasyonu sadece 'üç tepe' ya da 'üç dip' olarak görmek büyük hata
  olur. Three Drives'ın asıl değeri, fiyat hareketinin kendi içinde
  oluşturduğu Fibonacci, fiyat ve zaman simetrisidir."*

Üç doğrulama:
  1. **Fibonacci** — A ve C düzeltmeleri önceki hareketin ~%61.8 veya
     ~%78.6'sını geri almalı; Drive 2 ve Drive 3 ise ~1.272 / ~1.618
     uzantılarında tamamlanmalı.
  2. **Fiyat simetrisi (AB=CD)** — A→Drive2 ile C→Drive3 bacakları yakın
     büyüklükte olmalı.
  3. **Zaman simetrisi** — iki bacağın SÜRESİ yakın olmalı.

Ve kullanıcının vurguladığı kural:

  *"Drive 3 oluştu diye doğrudan ters yönde işlem açmak doğru değildir.
  Three Drives bize kesin dönüş değil, dönüş ihtimalinin yoğunlaştığı bir
  bölge verir."*

Bu yüzden sonuç `AL`/`SAT` DEĞİL, `İZLE` durumudur. `AL`a dönmesi için
fiyatın Drive 3'ten sonra GERÇEKTEN tepki vermesi gerekir.

Hesap yapar, çizmez.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class SymmetryCheck:
    name: str
    value: float
    target: str
    ok: bool


@dataclass(frozen=True)
class ThreeDrivesQuality:
    checks: tuple[SymmetryCheck, ...]
    score: float                 # 0..1
    verdict: str                 # "gecerli" | "zayif" | "gecersiz"
    state: str                   # "izle" | "onaylandi" | "gecersiz"
    reaction_pct: float          # Drive 3 sonrası tepki
    note: str

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c.ok)


def _near(value: float, targets: tuple[float, ...], tol: float) -> bool:
    return any(abs(value - t) <= tol for t in targets)


def assess(
    df: pd.DataFrame,
    *,
    x: tuple[pd.Timestamp, float],
    d1: tuple[pd.Timestamp, float],
    a: tuple[pd.Timestamp, float],
    d2: tuple[pd.Timestamp, float],
    c: tuple[pd.Timestamp, float],
    d3: tuple[pd.Timestamp, float],
    retrace_targets: tuple[float, ...] = (0.618, 0.786),
    extension_targets: tuple[float, ...] = (1.272, 1.618),
    ratio_tol: float = 0.09,
    price_symmetry_tol: float = 0.25,
    time_symmetry_tol: float = 0.40,
    min_reaction_pct: float = 0.03,
) -> ThreeDrivesQuality:
    """Altı noktadan formasyonun kalitesini ölçer."""
    def leg(p0, p1) -> float:
        return abs(p1[1] - p0[1])

    def bars(p0, p1) -> int:
        return int(abs(df.index.get_indexer([p1[0]])[0] - df.index.get_indexer([p0[0]])[0]))

    checks: list[SymmetryCheck] = []

    # 1) Fibonacci — düzeltmeler
    r_a = leg(d1, a) / max(leg(x, d1), 1e-9)
    r_c = leg(d2, c) / max(leg(a, d2), 1e-9)
    checks.append(SymmetryCheck("A düzeltmesi", r_a, "0.618 / 0.786",
                                _near(r_a, retrace_targets, ratio_tol)))
    checks.append(SymmetryCheck("C düzeltmesi", r_c, "0.618 / 0.786",
                                _near(r_c, retrace_targets, ratio_tol)))

    # 1b) Fibonacci — uzantılar
    e_2 = leg(a, d2) / max(leg(d1, a), 1e-9)
    e_3 = leg(c, d3) / max(leg(d2, c), 1e-9)
    checks.append(SymmetryCheck("Drive 2 uzantısı", e_2, "1.272 / 1.618",
                                _near(e_2, extension_targets, ratio_tol * 2)))
    checks.append(SymmetryCheck("Drive 3 uzantısı", e_3, "1.272 / 1.618",
                                _near(e_3, extension_targets, ratio_tol * 2)))

    # 2) FİYAT simetrisi (AB=CD): A→D2 ile C→D3 yakın büyüklükte
    leg_ad2, leg_cd3 = leg(a, d2), leg(c, d3)
    price_sym = abs(leg_ad2 - leg_cd3) / max((leg_ad2 + leg_cd3) / 2, 1e-9)
    checks.append(SymmetryCheck("Fiyat simetrisi", price_sym,
                                f"≤ {price_symmetry_tol:.0%}",
                                price_sym <= price_symmetry_tol))

    # 3) ZAMAN simetrisi: iki bacağın süresi yakın
    t_ad2, t_cd3 = bars(a, d2), bars(c, d3)
    time_sym = abs(t_ad2 - t_cd3) / max((t_ad2 + t_cd3) / 2, 1e-9)
    checks.append(SymmetryCheck("Zaman simetrisi", time_sym,
                                f"≤ {time_symmetry_tol:.0%}",
                                time_sym <= time_symmetry_tol))

    score = sum(1 for ch in checks if ch.ok) / len(checks)
    verdict = "gecerli" if score >= 0.8 else ("zayif" if score >= 0.5 else "gecersiz")

    # Drive 3 SONRASI tepki: formasyon "izle" durumundan ancak fiyat
    # gerçekten tepki verince çıkar.
    after = df.loc[df.index > d3[0], "close"]
    down_drive = d3[1] < c[1]
    if len(after):
        extreme = float(after.max() if down_drive else after.min())
        reaction = (extreme - d3[1]) / max(abs(d3[1]), 1e-9)
        reaction = reaction if down_drive else -reaction
    else:
        reaction = 0.0

    if verdict == "gecersiz":
        state = "gecersiz"
        note = "Simetri şartları sağlanmıyor — Three Drives sayılmaz."
    elif reaction >= min_reaction_pct:
        state = "onaylandi"
        note = f"Drive 3 sonrası %{reaction * 100:.1f} tepki geldi — dönüş teyit edildi."
    else:
        state = "izle"
        note = (
            "Drive 3 oluştu ama TEPKİ HENÜZ YOK. Three Drives kesin dönüş "
            "değil, dönüş ihtimalinin yoğunlaştığı bölgedir — teyit bekleniyor."
        )

    return ThreeDrivesQuality(
        checks=tuple(checks), score=score, verdict=verdict, state=state,
        reaction_pct=float(reaction), note=note,
    )
