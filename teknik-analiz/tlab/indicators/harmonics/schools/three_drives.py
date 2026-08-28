"""Three Drives (Ch.7) — X=drive1, A=düzeltme1, B=drive2, C=düzeltme2,
D=drive3 (projeksiyon). Standart XABCD adayı yeniden kullanılır ama
retracement değil İMPULSİF DEVAM istenir: B, X'i aşmalı (b_beyond_x=True).

Oran eşlemesi:
- ab_xa (candidate.ab_xa) = drive2'nin (X->A) bacağına göre uzantısı,
  hedef {1.272, 1.618} — AB=CD zincirindeki ilk bacağın kendisi.
- bc_ab (candidate.abc) = düzeltme2'nin drive2 bacağını geri çekilmesi,
  hedef .382/.618/.786 (bilgi-bankasi/teknik/10/ORAN-08).
- D (drive3): klasik AB=CD projeksiyonu (D = C + ratio*(B-A)), "abcd"
  bacak koduyla — ratio, xab'daki İLE AYNI aile (1.272 ya da 1.618) olacak
  şekilde iki ayrı PatternSpec varyantı ("three_drives_1272"/"_1618").

İki oran ailesi arasından hangisinin geçerli olacağına dair kitapta kesin
bir "ikisi aynı olmalı" şartı yoktu — sembolik yakınlık (near-perfect
symmetry) vurgusu vardı; burada basitleştirilerek AYNI aile şartı konuldu
(varsayım, dokümante edildi).

EK-A (2026-08-28): bilgi-bankasi/teknik/10_pesavento_twys.md (FORMASYON-04)
birincil kaynağıyla karşılaştırıldı — bu dosyanın K1 çıkarımındaki notuna göre
(bkz. dosyanın FORMASYON-04 "Non-repaint çevirisi" altındaki not) bu patern
Pesavento'ya özgü olsa da BİLİNÇLİ OLARAK ayrı/izole bir ekol (bu dosya) olarak
tutuluyor — `schools/pesavento.py`'nin kendi `patterns` sözlüğüne YİNELENMEDİ
(iki farklı "three_drives" implementasyonu aynı ekol içinde çelişki yaratırdı;
"ekoller birbirini import etmez" ilkesiyle tutarlı tek değişiklik, MEVCUT bu
dosyanın kitap değerleriyle hizalanmasıdır). Tek FARKLI bulunan alan `abc`
(ORAN-08) — aşağıda düzeltildi. `xab`/`d_components`/`invalidation` zaten
kitapla uyumluydu (ORAN-07, geçersizlik madde 4 — bkz. yorum satırları).
KURAL-09 (zaman simetrisi) betimleyici bir karakteristiktir, kitapta sert bir
geçersizlik kriteri olarak verilmiyor; bu yüzden Gilmore'daki gibi bir
`time_window()` zorunluluğu OLARAK eklenmedi — istenirse ayrı bir görev
olarak eklenebilir (TODO)."""

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
                name="three_drives_1272",
                # bilgi-bankasi/teknik/10/ORAN-07: Drive1->Drive2 uzantısı 1.272 veya 1.618.
                xab=_pt(1.272),
                # bilgi-bankasi/teknik/10/ORAN-08: A/C geri çekilmesi ideal .618/.786,
                # .382'ye gerileme de GEÇERLİ (güçlü trend işareti) — eskiden yalnızca
                # (0.618,0.786) kabul ediliyordu, .382'yi hatalı biçimde dışlıyordu.
                abc=(0.382 - _TOL, 0.786 + _TOL),
                d_components=(("abcd", 1.272 - _TOL, 1.272 + _TOL),),
                prz_method="single_pm_tol", b_beyond_x_required=True,
                # bilgi-bankasi/teknik/10/FORMASYON-04 geçersizlik 4: 1.618 uzantısının
                # ötesi genelde başarısız patern sonucu verir — 1272 ailesi için bir
                # sonraki standart oran zaten 1.618, kitapla uyumlu (değişmedi).
                invalidation=("abcd", 1.618),
            ),
            "three_drives_1618": PatternSpec(
                name="three_drives_1618",
                xab=_pt(1.618),
                abc=(0.382 - _TOL, 0.786 + _TOL),
                d_components=(("abcd", 1.618 - _TOL, 1.618 + _TOL),),
                prz_method="single_pm_tol", b_beyond_x_required=True,
                # 1618 ailesi için bir sonraki standart oran 2.0 — kitapta bu aile için
                # ayrı bir sayı verilmiyor (madde 4 yalnızca "1.618 ötesi" diyor, hangi
                # aile için net değil); PatternSpec sözleşmesindeki "kendi D hedefinden
                # bir sonraki standart oran" kuralına göre mühendislik varsayımı olarak
                # korundu (kaynaksız, çelişki değil).
                invalidation=("abcd", 2.0),
            ),
        }
