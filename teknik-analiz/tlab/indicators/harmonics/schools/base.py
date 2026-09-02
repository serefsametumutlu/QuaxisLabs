"""Her harmonik ekolün uyduğu ortak sözleşme. Ekoller birbirini import ETMEZ."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field

import pandas as pd

from tlab.indicators.harmonics.geometry import Candidate
from tlab.indicators.harmonics.prz import PRZ, DComponent, PRZMethod, compute_prz

_DEFAULT_MAX_WAIT_MULT = 2.0


@dataclass(frozen=True)
class PatternSpec:
    """Tek bir formasyonun (ör. "gartley") oran/kabul kuralları.

    xab: ab_xa (B'nin XA'ya oranı) için (lo,hi) — None ise kontrol edilmez.
    abc: bc_ab (C'nin AB'ye oranı) için (lo,hi) — None ise kontrol edilmez.
    C'nin A'yı aşıp aşmaması (klasik retracement vs shark/cypher/nenstar
    tarzı uzantı) ayrı bir "mod" değil, doğrudan c_beyond_a_required ile
    belirlenir — ratio() formülü her iki durumda da aynıdır, yalnızca
    coğrafi yorum (retracement/extension) c_beyond_a'ya bağlıdır.
    d_components: PRZ hesaplaması için bacak listesi (bkz. prz.py).
    invalidation: (bacak_kodu, oran) — bu bacakta bu oranın ötesi INVALIDATED
    sayılır (ör. butterfly için ("xa_ext", 1.618) — kendi D hedefinden bir
    sonraki standart oran).
    """

    name: str
    xab: tuple[float, float] | None
    abc: tuple[float, float] | None
    d_components: tuple[DComponent, ...]
    prz_method: PRZMethod
    c_beyond_a_required: bool = False
    b_beyond_x_required: bool = False
    requires_zero: bool = False
    invalidation: tuple[str, float] | None = None
    extra: dict = field(default_factory=dict)


@dataclass(frozen=True)
class PatternMatch:
    candidate: Candidate
    spec: PatternSpec
    prz: PRZ
    score: float


class HarmonicSchool(ABC):
    """Bir harmonik ekolün (Carney, Pesavento, ...) kural kümesi."""

    name: str
    patterns: dict[str, PatternSpec]
    tolerance: float

    def match(self, candidate: Candidate) -> list[PatternMatch]:
        """candidate'ı bu ekolün TÜM formasyonlarına karşı dener; eşleşenleri döner."""
        matches: list[PatternMatch] = []
        for spec in self.patterns.values():
            if candidate.c_beyond_a != spec.c_beyond_a_required:
                continue
            if candidate.b_beyond_x != spec.b_beyond_x_required:
                continue
            if spec.requires_zero and candidate.zero is None:
                continue
            if spec.xab is not None and not (spec.xab[0] <= candidate.ab_xa <= spec.xab[1]):
                continue
            abc_value = candidate.bc_ab
            if spec.abc is not None and not (spec.abc[0] <= abc_value <= spec.abc[1]):
                continue
            if not self._extra_match(candidate, spec):
                continue

            prz = compute_prz(candidate, spec.d_components, spec.prz_method)
            if prz is None:
                continue
            if not self._post_prz_match(candidate, spec, prz):
                continue

            matches.append(
                PatternMatch(
                    candidate=candidate, spec=spec, prz=prz,
                    score=self._score(candidate, spec, prz),
                )
            )
        return matches

    def _extra_match(self, candidate: Candidate, spec: PatternSpec) -> bool:
        """Alt sınıflar (ör. Gilmore zaman oranı) buraya PRZ hesaplanmadan
        ÖNCE değerlendirilebilecek ek kabul kuralı ekleyebilir. Varsayılan:
        her zaman kabul."""
        return True

    def _post_prz_match(self, candidate: Candidate, spec: PatternSpec, prz: PRZ) -> bool:
        """PRZ hesaplandıktan SONRA (D tahminine ihtiyaç duyan kurallar için,
        ör. Pesavento'nun AB=CD simetrisi) değerlendirilir. Varsayılan: kabul."""
        return True

    def _score(self, candidate: Candidate, spec: PatternSpec, prz: PRZ) -> float:
        """0..1 skor: oran sapmalarının tersi (1=mükemmel oran uyumu)."""
        deviations: list[float] = []
        if spec.xab is not None:
            mid = (spec.xab[0] + spec.xab[1]) / 2.0
            span = max(spec.xab[1] - spec.xab[0], 1e-9) / 2.0 + self.tolerance
            deviations.append(min(1.0, abs(candidate.ab_xa - mid) / span))
        if spec.abc is not None:
            mid = (spec.abc[0] + spec.abc[1]) / 2.0
            span = max(spec.abc[1] - spec.abc[0], 1e-9) / 2.0 + self.tolerance
            deviations.append(min(1.0, abs(candidate.bc_ab - mid) / span))
        if not deviations:
            return 0.5
        avg_dev = sum(deviations) / len(deviations)
        return max(0.0, 1.0 - avg_dev)

    def prz(self, candidate: Candidate, spec: PatternSpec) -> PRZ | None:
        return compute_prz(candidate, spec.d_components, spec.prz_method)

    def extra_confirmation(self, df: pd.DataFrame, candidate: Candidate, t: int) -> bool:
        """confirmation_policy="school" seçildiğinde çağrılır. Varsayılan: True
        (ilk ACTIVE barında hemen onaylanır) — alt sınıflar override edebilir."""
        return True

    def suggested_levels(
        self, candidate: Candidate, spec: PatternSpec, prz: PRZ
    ) -> dict[str, float | str] | None:
        """Ekol/kaynak kitaptan gelen giriş-stop önerisi (varsa). Değerler
        yalnızca X,A,B,C ve PRZ'den DETERMİNİSTİK hesaplanabilir olmalı —
        lookahead yok, D henüz gerçekleşmemiş olsa bile candidate doğar
        doğmaz hesaplanabilir. Varsayılan: None (öneri yok); alt sınıflar
        override edebilir (bkz. PesaventoSchool — TWYS kaynaklı)."""
        return None

    def time_window(self, candidate: Candidate, spec: PatternSpec) -> tuple[int, int] | None:
        """2026-09-03 ÖNCESİ: yalnızca Gilmore override ediyordu, diğer 7
        ekol None (SÜRESİZ bekleme) dönüyordu. Gerçek veride (648 sembol,
        BIST) bu, C'den D'ye 650 GÜNE kadar süren zincirlerin `confirmed`
        olarak (yani "AL sinyali" gibi) görünmesine yol açtığını ortaya
        çıkardı — kullanıcının bildirdiği "ABC oluşup uzun süre yatay
        gidince/başka yöne gidip geri gelince bile eninde sonunda D'ye
        değindi diye sinyal veriyor" sorunuydu (median bekleme 29 gün ama
        kuyruk 650 güne kadar çıkıyordu — 2 yıla yakın "beklemiş" bir yapı
        artık trade edilebilir bir harmonik DEĞİL).

        Bu varsayılan, Gilmore'un KENDİ kitabından (Time Bars) gelen kesin
        oran tablosu DEĞİL — genel bir SAĞLIK SINIRI: D, XABC yapısının
        kendi oluşum süresinin (X'ten C'ye kadar geçen bar sayısı) makul
        bir katı içinde gelmeli, aksi halde EXPIRED olur (bkz. `state.py::
        track_pattern`'daki `time_window[1]` kontrolü). Alt sınıflar (ör.
        Gilmore) kendi kitap-kaynaklı kuralıyla override etmeye devam eder."""
        structure_bars = max(candidate.c.bar_idx - candidate.x.bar_idx, 1)
        max_wait = max(candidate.bars_ab, round(_DEFAULT_MAX_WAIT_MULT * structure_bars))
        return (0, max_wait)
