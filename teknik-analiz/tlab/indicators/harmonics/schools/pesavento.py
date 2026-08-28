"""Larry Pesavento ekolü — PRZ tek-seviye±tolerans (single_pm_tol), ±0.05.

Carney'den ayrılan iki nokta: (1) daha geniş tolerans, (2) her formasyonda
AB=CD simetrisi zorunlu (D tahmini, CD/AB oranının 1.0/1.27/1.618/2.0'e yakın
olmasını da sağlamalı — bkz. _post_prz_match). Ek teyit (extra_confirmation)
X→B trend çizgisi kırılımıdır; asıl kırılım tespiti confirmation_policy=
"xb_break" ile scanner_indicator.py'de yapılır, burada yalnızca extra
teyit için de aynı yönü ister (school policy seçilirse).

Oran/eşik değerleri `bilgi-bankasi/teknik/10_pesavento_twys.md` (Trade What
You See — Pesavento & Jouflas) birincil kaynağıyla hizalanmıştır — K1-D
görevi, bkz. dosyanın sonundaki "Faz 3 karşılaştırma tablosu". Kitapta
sayısal olarak verilmeyen (B/C oranları gibi) alanlar `extra["assumed"]`
notuyla işaretlenir; bunlar kitapla ÇELİŞMEZ ama kitaptan da DOĞRULANMAZ.
"""

from __future__ import annotations

import pandas as pd

from tlab.indicators.harmonics.geometry import Candidate
from tlab.indicators.harmonics.prz import PRZ, project_ratio
from tlab.indicators.harmonics.schools.base import HarmonicSchool, PatternSpec

_TOL = 0.05
_AB_CD_RATIOS = (1.0, 1.27, 1.618, 2.0)  # bilgi-bankasi/teknik/10/ORAN-02


def _pt(v: float, tol: float = _TOL) -> tuple[float, float]:
    return (v - tol, v + tol)


class PesaventoSchool(HarmonicSchool):
    name = "pesavento"
    tolerance = _TOL

    def __init__(self) -> None:
        self.patterns = {
            "gartley": PatternSpec(
                name="gartley", xab=_pt(0.618), abc=(0.382, 0.886),
                # bilgi-bankasi/teknik/10/ORAN-04: kitaptaki TÜM Gartley
                # örnekleri D'yi XA'nın .786 geri çekilmesi olarak kullanır.
                d_components=(("xa_ret", 0.786 - _TOL, 0.786 + _TOL),),
                prz_method="single_pm_tol",
                # bilgi-bankasi/teknik/10/FORMASYON-02 geçersizlik 1: D, X'i aşamaz.
                invalidation=("xa_ret", 1.0),
                extra={
                    "assumed": "xab (B oranı) ve abc (C oranı) kitapta (ORAN-03/PSK-02) "
                    "B'ye/C'ye özel bir sayı olarak verilmiyor — kitap yalnızca genel "
                    ".382/.50/.618/.786 listesini veriyor, hangi oranın hangi bacağa "
                    "ait olduğunu ayırmıyor. Mevcut sabit .618±tol / .382-.886 aralığı "
                    "genel harmonik konvansiyondan (Carney) ödünç alındı.",
                },
            ),
            "butterfly": PatternSpec(
                name="butterfly",
                # bilgi-bankasi/teknik/10/ORAN-05: kabul edilen küme fiilen
                # {.382, .50, .618, .786} — tek geniş bant olarak ifade edildi
                # (PatternSpec.xab tek (lo,hi) aralığı destekliyor, ayrı 4
                # merkezli bant desteği bu görevin kapsamı dışında).
                xab=(0.382 - _TOL, 0.886 + _TOL),
                abc=(0.382, 0.886),
                # bilgi-bankasi/teknik/10/ORAN-06: D, XA'nın 1.272/1.618/2.00/2.618
                # uzantılarından birinde tamamlanır — eskiden (1.27,1.618) idi,
                # kitap 2.00 ve 2.618'i de GEÇERLİ D hedefi sayıyor.
                d_components=(("xa_ext", 1.27, 2.618),),
                prz_method="single_pm_tol",
                # bilgi-bankasi/teknik/10/FORMASYON-03 geçersizlik 2: yalnızca
                # 2.618'İN ÖTESİ patern negatif sayılır (eskiden 1.618'de
                # kesiliyordu — 1.618 kitapta "azami risk" seviyesi, geçersizlik
                # SINIRI değil).
                invalidation=("xa_ext", 2.618),
                extra={
                    "assumed": "abc (BC oranı) kitapta özel bir sayı olarak verilmiyor, "
                    "Carney'den ödünç alındı (ORAN-06 yalnızca D/XA hedefini verir).",
                    "note": "xab üst sınırı .886+tol'de tutuldu; kitap teknik olarak "
                    ".786 ötesinde X'e (1.0) kadar izin veriyor ama bu, paterni ayırt "
                    "edici olmaktan çıkarır — ORAN-05'in pragmatik/dar yorumu.",
                },
            ),
        }

    def _post_prz_match(self, candidate: Candidate, spec: PatternSpec, prz: PRZ) -> bool:
        ab = abs(candidate.b.price - candidate.a.price)
        if ab == 0:
            return False
        cd_ab = abs(prz.center - candidate.c.price) / ab
        return any(abs(cd_ab - r) <= self.tolerance for r in _AB_CD_RATIOS)

    def extra_confirmation(self, df: pd.DataFrame, candidate: Candidate, t: int) -> bool:
        x, b = candidate.x, candidate.b
        slope = (b.price - x.price) / (b.bar_idx - x.bar_idx)
        intercept = x.price - slope * x.bar_idx
        line_val = slope * t + intercept
        close_t = float(df["close"].iloc[t])
        return close_t > line_val if candidate.direction == "bullish" else close_t < line_val

    def suggested_levels(
        self, candidate: Candidate, spec: PatternSpec, prz: PRZ
    ) -> dict[str, float | str] | None:
        """TWYS giriş/stop önerileri — yalnızca hesaplanabilir (fiyat/oran
        bazlı) kısım. "Shaded" limit ince ayarı ve sabit dolar/yüzde stop
        enstrümana ve trader risk toleransına bırakılmıştır (kitapta
        genellenebilir bir sayı verilmiyor) — bu kısımlar suggested_* alanlarına
        TAŞINMADI, yalnızca *_note metninde belirtildi (PSK niteliğinde)."""
        if spec.name == "gartley":
            return {
                # bilgi-bankasi/teknik/10/ORAN-04: D = .786 XA geri çekilmesi.
                "suggested_entry": prz.center,
                # bilgi-bankasi/teknik/10/FORMASYON-02: stop, X seviyesinin
                # (XA'nın %100'ü) hemen ötesi — xa_ret oranı 1.0 == X fiyatı.
                "suggested_stop": candidate.x.price,
                "entry_note": ".786 tamamlanma seviyesinin hemen ötesine 'shaded' "
                "limit emir; kesin ofset enstrümana göre değişir (PSK notu).",
            }
        if spec.name == "butterfly":
            return {
                # bilgi-bankasi/teknik/10/ORAN-06: 1.272-2.618 XA bandının ortası.
                "suggested_entry": prz.center,
                # bilgi-bankasi/teknik/10/FORMASYON-03: pratikte azami risk
                # çoğunlukla 1.618 XA uzantısı seviyesinde konumlandırılır
                # (formel geçersizlik 2.618'de olsa da, bu DAHA SIKI bir
                # pratik stop seviyesidir — kitaptaki ayrım korunuyor).
                "suggested_stop": project_ratio(candidate, "xa_ext", 1.618),
                "entry_note": "1.272/1.618 tamamlanma bölgesine 'shaded' limit emir; "
                "1.272 mi 1.618 mi daha olası olduğu C'den çıkışın hızına bağlıdır "
                "(bkz. KURAL-06), otomatik hesaplanamaz.",
            }
        return None
