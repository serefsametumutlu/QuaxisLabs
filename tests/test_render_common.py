"""SPEC: docs/spec/spec_kapsam_cezali_skor.md -- `src/render/render_common.py`
paylaşılan yardımcılarının (dashboard.py/company_detail.py'nin ORTAK
kullandığı `mercek_score_display`/`mercek_bilesen_sayimi`) izole testleri.
"""

from __future__ import annotations

from decimal import Decimal

from src.render import render_common as rc


# --- mercek_bilesen_sayimi ------------------------------------------------


def test_mercek_bilesen_sayimi_bos_detayda_sifir_sifir_doner() -> None:
    assert rc.mercek_bilesen_sayimi(None, "kalite") == (0, 0)
    assert rc.mercek_bilesen_sayimi({}, "kalite") == (0, 0)


def test_mercek_bilesen_sayimi_ayes_ornegi() -> None:
    detay = {
        "kalite": [
            {"name": "ROE", "score": "9.3"},
            {"name": "ROA", "score": "8.8"},
            {"name": "FAVÖK Marjı", "score": None},
            {"name": "Net Marj", "score": None},
            {"name": "Brüt Kâr Marjı", "score": None},
            {"name": "Greenblatt ROC", "score": None},
            {"name": "OCF/Net Kâr", "score": None},
        ],
    }
    assert rc.mercek_bilesen_sayimi(detay, "kalite") == (2, 7)


# --- mercek_score_display -------------------------------------------------


def test_mercek_score_display_yeterli_kapsamda_degisiklik_yok() -> None:
    """badge != YETERSİZ VERİ (kapsam>=%50 ile TANIM gereği aynı) -> mevcut
    S AYNEN gösterilir, kapsam_notu None."""
    score_value, display, notu = rc.mercek_score_display(
        Decimal("7.5"), "SAĞLAM", Decimal("100"),
    )
    assert score_value == Decimal("7.5")
    assert display == "7,5"
    assert notu is None


def test_mercek_score_display_kapsam_sifirda_na_doner() -> None:
    """spec §3: kapsam=%0 -> score_display N/A AYNEN kalır, RİSKLİ'ye ASLA
    düşürülmez (kapsam_notu None -- gösterilecek bir S′ yok)."""
    score_value, display, notu = rc.mercek_score_display(
        Decimal("0"), "YETERSİZ VERİ", Decimal("0"),
    )
    assert score_value is None
    assert display == "N/A"
    assert notu is None


def test_mercek_score_display_score_veya_coverage_none_ise_na_doner() -> None:
    score_value, display, notu = rc.mercek_score_display(None, "YETERSİZ VERİ", None)
    assert (score_value, display, notu) == (None, "N/A", None)


def test_mercek_score_display_dusuk_kapsamda_kapsam_cezali_skor_doner() -> None:
    """spec §4 tam cümle -- AYES örneği: "Kalite: 2,3/10 (YETERSİZ VERİ —
    kapsam %25 — sadece 2/7 bileşen ölçülebildi)"."""
    score_value, display, notu = rc.mercek_score_display(
        Decimal("9.21"), "YETERSİZ VERİ", Decimal("25"),
        mercek_label="Kalite", n_mevcut=2, n_toplam=7,
    )
    assert score_value == Decimal("2.3025")
    assert display == "2,3"
    assert notu == "Kalite: 2,3/10 (YETERSİZ VERİ — kapsam %25 — sadece 2/7 bileşen ölçülebildi)"


def test_mercek_score_display_bilesen_sayisi_verilmezse_kisa_notu_uretir() -> None:
    """mercek_label/n_mevcut/n_toplam verilmezse (veya n_toplam=0 ise) tam
    cümle ÜRETİLEMEZ -- yine de S′ ve kısa, dürüst bir kapsam notu döner
    (sessizce boş BIRAKILMAZ)."""
    score_value, display, notu = rc.mercek_score_display(
        Decimal("9.21"), "YETERSİZ VERİ", Decimal("25"),
    )
    assert score_value == Decimal("2.3025")
    assert display == "2,3"
    assert notu is not None
    assert "kapsam %25" in notu
