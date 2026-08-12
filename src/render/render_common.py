"""`src/render/dashboard.py` ve `src/render/company_detail.py` arasında
PAYLAŞILAN küçük render yardımcıları -- docs/spec/spec_kapsam_cezali_skor.md
§9 madde 4'ün "iki dosyada kod tekrarı varsa ORTAK bir yardımcıya çıkarılması
ÖNERİLİR" tavsiyesi: her iki dosya da AYNI mantığı (kapsam-cezalı skor
gösterimi + bileşen sayımı) TEKRAR TEKRAR yazmak yerine burayı kullanır.

Bu modül -- `dashboard.py`/`company_detail.py` ile AYNI ilke (quaxis-mimari
anayasa) -- HİÇBİR skor HESAPLAMAZ: `src.analysis.lens_common.
kapsam_cezali_skor()` (SAF matematik) çağrılır, burada SADECE eşik kararı
(spec §3) + Türkçe biçimlendirme (spec §4) yapılır.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from src.analysis.lens_common import YETERSIZ_VERI_ROZETI, kapsam_cezali_skor
from src.formatting import format_number_tr


def mercek_bilesen_sayimi(mercekler_detay: dict[str, Any] | None, detay_key: str) -> tuple[int, int]:
    """`mercekler_detay[detay_key]` (bkz. `scripts/tarama_toplu.py::
    _component_to_dict`) listesinden (n_mevcut, n_toplam) çıkarır -- skoru
    `None` OLMAYAN bileşen sayısı / toplam tanımlı bileşen sayısı
    (spec_kapsam_cezali_skor.md §4: "YENİ bir alan İCAT EDİLMEZ, mevcut
    `components` listesinden türetilir")."""
    bilesenler = (mercekler_detay or {}).get(detay_key, [])
    n_toplam = len(bilesenler)
    n_mevcut = sum(1 for b in bilesenler if b.get("score") is not None)
    return n_mevcut, n_toplam


def mercek_score_display(
    score: Decimal | None,
    badge: str | None,
    coverage: Decimal | None,
    *,
    mercek_label: str | None = None,
    n_mevcut: int | None = None,
    n_toplam: int | None = None,
) -> tuple[Decimal | None, str, str | None]:
    """docs/spec/spec_kapsam_cezali_skor.md §3/§4 -- bir merceğin EKRANA
    basılacak `(score_value, score_display, kapsam_notu)` üçlüsünü üretir.

    Kural (spec §3, somut eşik):
      - `badge != YETERSİZ VERİ` (kapsam>=%50 ile TANIM gereği AYNI) ->
        mevcut S AYNEN gösterilir (DEĞİŞİKLİK YOK), kapsam_notu=None.
      - `badge == YETERSİZ VERİ` VE (`score`/`coverage` None veya
        `coverage == 0`) -> "N/A" (mevcut c5c8499 davranışı AYNEN korunur
        -- §3'ün "kapsam=%0" özel durumu: "veri yok" ile "şirket kötü"
        KARIŞTIRILMASIN).
      - `badge == YETERSİZ VERİ` VE `0 < coverage < 50` -> S′ = S×kapsam/100
        (kapsam-cezalı skor, nominal ağırlık × skor, eksik bileşen SIFIR
        katkı) gösterilir + (mercek_label/n_mevcut/n_toplam verildiyse)
        §4'teki tam açıklama cümlesi `kapsam_notu`'ya yazılır.
    """
    if badge != YETERSIZ_VERI_ROZETI:
        return score, (format_number_tr(score, decimals=1) if score is not None else "N/A"), None

    if score is None or coverage is None or coverage == 0:
        return None, "N/A", None

    s_prime = kapsam_cezali_skor(score, coverage)
    display = format_number_tr(s_prime, decimals=1)
    kapsam_str = format_number_tr(coverage, decimals=0)

    if mercek_label is not None and n_mevcut is not None and n_toplam is not None and n_toplam > 0:
        notu = (
            f"{mercek_label}: {display}/10 (YETERSİZ VERİ — kapsam %{kapsam_str} — "
            f"sadece {n_mevcut}/{n_toplam} bileşen ölçülebildi)"
        )
    else:
        notu = f"Kapsam-cezalı skor (nominal ağırlık × skor, eksik bileşen sıfır sayılır) -- kapsam %{kapsam_str}."
    return s_prime, display, notu


__all__ = ["mercek_bilesen_sayimi", "mercek_score_display"]
