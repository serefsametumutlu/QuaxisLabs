"""Faz 3c: v2 çok-mercekli skorlama ortak altyapısı (`src/analysis/lens_common.py`)
için testler -- özellikle K1 (cliff) düzeltmesinin gerçekten SÜREKLİ
olduğunu doğrular (quant_denetim_01.md K1)."""

from __future__ import annotations

from decimal import Decimal

from src.analysis import lens_common as lc


# --- robust_istatistik / z_skoru -----------------------------------------------------


def test_robust_istatistik_bos_listede_none_doner() -> None:
    assert lc.robust_istatistik([]) is None


def test_robust_istatistik_medyan_ve_mad_dogru_hesaplanir() -> None:
    # winsorizasyonun ETKİSİZ kaldığı küçük bir örneklem (n=5, %5 kırpma ~0 eleman).
    degerler = [Decimal(v) for v in [10, 12, 14, 16, 18]]
    sonuc = lc.robust_istatistik(degerler, winsor_pct=Decimal(0))
    assert sonuc is not None
    medyan, mad, n = sonuc
    assert medyan == Decimal(14)
    assert n == 5
    # sapmalar: |10-14|=4,|12-14|=2,|14-14|=0,|16-14|=2,|18-14|=4 -> sirali [0,2,2,4,4] -> medyan=2
    assert mad == Decimal(2)


def test_z_skoru_mad_sifirsa_none_doner() -> None:
    assert lc.z_skoru(Decimal(10), Decimal(10), Decimal(0)) is None


def test_z_skoru_pozitif_sapma_pozitif_z_uretir() -> None:
    z = lc.z_skoru(Decimal(20), Decimal(10), Decimal(2))
    assert z is not None
    assert z > 0


# --- oran_str -----------------------------------------------------


def test_oran_str_x_eki_ile_bicimlenir_yuzde_degil() -> None:
    # K4 duzeltmesi: x-katı oranlar "%" DEĞİL "x" son ekiyle gösterilmeli.
    assert lc.oran_str(Decimal("1.0")) == "1,00x"
    assert lc.oran_str(None) == "-"


# --- seviye_trend_skoru_v2: K1 (cliff) düzeltmesi -----------------------------------------------------


def test_seviye_trend_skoru_v2_veri_yoksa_none() -> None:
    skor, gerekce = lc.seviye_trend_skoru_v2("X", None, None, Decimal(20), Decimal(10), Decimal(30))
    assert skor is None
    assert "veri yok" in gerekce


def test_seviye_trend_skoru_v2_trend_sifir_civarinda_SUREKLI() -> None:
    # K1 KANIT SENARYOSU (quant_denetim_01.md): FAVOK marji %40 (guclu_esik=20
    # UZERINDE) iken v1'de trend_puan -0,01 -> +0,00 arasinda skor 4,00 -> 9,33
    # SICRIYORDU (~5,3 puanlik ucurum). v2'de bu iki komsu deger ARASINDAKI
    # fark COK KUCUK (surekli) olmali.
    skor_hafif_negatif, _ = lc.seviye_trend_skoru_v2(
        "FAVÖK marjı", Decimal("40"), Decimal("-0.01"), Decimal(20), Decimal(10), Decimal(30)
    )
    skor_sifir, _ = lc.seviye_trend_skoru_v2(
        "FAVÖK marjı", Decimal("40"), Decimal("0.00"), Decimal(20), Decimal(10), Decimal(30)
    )
    assert skor_hafif_negatif is not None and skor_sifir is not None
    fark = abs(skor_sifir - skor_hafif_negatif)
    assert fark < Decimal("0.05"), f"beklenen sureklilik, ama fark={fark} (cliff hala var)"


def test_seviye_trend_skoru_v2_bant_sinirlarinda_UCLAR_CAKISIR() -> None:
    # K1 ikincil bulgu: v1'de orta_esik/guclu_esik sinirlarinda [0,4]-[5,7]-[8,10]
    # arasinda bosluk (1 puanlik sicrama) vardi. v2'de UCLAR CAKISMALI.
    skor_orta_altinda, _ = lc.seviye_trend_skoru_v2(
        "X", Decimal("9.999"), None, Decimal(20), Decimal(10), Decimal(30)
    )
    skor_orta_tam, _ = lc.seviye_trend_skoru_v2("X", Decimal(10), None, Decimal(20), Decimal(10), Decimal(30))
    assert abs(skor_orta_tam - skor_orta_altinda) < Decimal("0.01")

    skor_guclu_altinda, _ = lc.seviye_trend_skoru_v2(
        "X", Decimal("19.999"), None, Decimal(20), Decimal(10), Decimal(30)
    )
    skor_guclu_tam, _ = lc.seviye_trend_skoru_v2("X", Decimal(20), None, Decimal(20), Decimal(10), Decimal(30))
    assert abs(skor_guclu_tam - skor_guclu_altinda) < Decimal("0.01")


def test_seviye_trend_skoru_v2_bozulan_trend_hala_dusuk_puan_uretir() -> None:
    # Surekli hale getirilse bile "belirgin" bir bozulma (buyuk negatif trend)
    # yine dusuk bir puana YAKINSAMALI (ceza carpani 0,5'e dogru gider).
    skor, gerekce = lc.seviye_trend_skoru_v2(
        "FAVÖK marjı", Decimal("40"), Decimal("-10"), Decimal(20), Decimal(10), Decimal(30)
    )
    assert skor is not None
    assert skor < Decimal(6)  # ~9,33'un yarisina yakin bir bolgede
    assert "bozuluyor" in gerekce


def test_seviye_trend_skoru_v2_seviye_yukseldikce_skor_monoton_artar() -> None:
    skor_dusuk, _ = lc.seviye_trend_skoru_v2("X", Decimal(5), None, Decimal(20), Decimal(10), Decimal(30))
    skor_orta, _ = lc.seviye_trend_skoru_v2("X", Decimal(15), None, Decimal(20), Decimal(10), Decimal(30))
    skor_yuksek, _ = lc.seviye_trend_skoru_v2("X", Decimal(25), None, Decimal(20), Decimal(10), Decimal(30))
    assert skor_dusuk < skor_orta < skor_yuksek
