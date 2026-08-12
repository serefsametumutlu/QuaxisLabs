"""SPEC: `docs/spec/spec_bilesik_skor.md` testleri -- Bileşik Skor (4
merceğin birleşimi, v2)."""

from __future__ import annotations

from decimal import Decimal

from src.analysis.lens_bilesik_skor import hesapla_bilesik_skor, hesapla_veri_kapsam_ozeti
from src.analysis.lens_common import ComponentScore, ScoreResult, YETERSIZ_VERI_ROZETI


def _lens_sonucu(skor: Decimal, template: str, veri_yeterli: bool = True, coverage_pct: Decimal = Decimal(100)) -> ScoreResult:
    return ScoreResult(
        ticker="TEST", period=(2026, 3), template=template, total_score=skor,
        badge="DENGELİ", data_coverage_pct=coverage_pct, data_sufficient=veri_yeterli,
        components=[ComponentScore(name="X", score=skor, weight_nominal=Decimal(100), weight_effective=Decimal(100), contribution=skor, reasoning_tr="x")],
    )


def test_bilesik_skor_dort_mercek_de_yeterliyse_agirlikli_ortalama() -> None:
    deger = _lens_sonucu(Decimal(8), "değer")
    kalite = _lens_sonucu(Decimal(6), "kalite")
    buyume = _lens_sonucu(Decimal(4), "büyüme")
    guvenlik = _lens_sonucu(Decimal(7), "güvenlik")
    sonuc = hesapla_bilesik_skor("TEST", (2026, 3), deger, kalite, buyume, guvenlik)
    beklenen = (Decimal(8) * 30 + Decimal(6) * 30 + Decimal(7) * 25 + Decimal(4) * 15) / 100
    assert sonuc.total_score == beklenen
    assert sonuc.data_sufficient
    assert set(sonuc.dahil_edilen_mercekler) == {"değer", "kalite", "büyüme", "güvenlik"}


def test_bilesik_skor_bir_mercek_eksikse_agirlik_orantisal_dagitilir() -> None:
    # Buyume merceği TAMAMEN eksik (None) -- agirlik (%15) diger 3'e dagitilir.
    deger = _lens_sonucu(Decimal(8), "değer")
    kalite = _lens_sonucu(Decimal(6), "kalite")
    guvenlik = _lens_sonucu(Decimal(7), "güvenlik")
    sonuc = hesapla_bilesik_skor("TEST", (2026, 3), deger, kalite, None, guvenlik)
    toplam_agirlik = Decimal(30 + 30 + 25)
    beklenen = (Decimal(8) * 30 + Decimal(6) * 30 + Decimal(7) * 25) / toplam_agirlik
    assert abs(sonuc.total_score - beklenen) < Decimal("0.0000001")
    assert "büyüme" not in sonuc.dahil_edilen_mercekler


def test_bilesik_skor_data_sufficient_false_olan_mercek_disarida_birakilir() -> None:
    deger = _lens_sonucu(Decimal(8), "değer")
    kalite = _lens_sonucu(Decimal(2), "kalite", veri_yeterli=False)  # YETERSIZ VERI -- disarida
    sonuc = hesapla_bilesik_skor("TEST", (2026, 3), deger, kalite, None, None)
    assert sonuc.total_score == Decimal(8)
    assert sonuc.dahil_edilen_mercekler == ["değer"]


def test_bilesik_skor_tum_mercekler_yetersizse_yetersiz_veri_rozeti_sifira_bolme_yok() -> None:
    sonuc = hesapla_bilesik_skor("TEST", (2026, 3), None, None, None, None)
    assert sonuc.badge == YETERSIZ_VERI_ROZETI
    assert sonuc.data_sufficient is False
    assert sonuc.total_score == Decimal(0)
    assert sonuc.dahil_edilen_mercekler == []


def test_bilesik_skor_rozet_esikleri_v1_ile_tutarli() -> None:
    deger = _lens_sonucu(Decimal(9), "değer")
    kalite = _lens_sonucu(Decimal(9), "kalite")
    buyume = _lens_sonucu(Decimal(9), "büyüme")
    guvenlik = _lens_sonucu(Decimal(9), "güvenlik")
    sonuc = hesapla_bilesik_skor("TEST", (2026, 3), deger, kalite, buyume, guvenlik)
    assert sonuc.badge == "SAĞLAM"


def test_bilesik_skor_banka_sigorta_finansman_ust_agirliklar_sabit_kalir() -> None:
    """spec_bilesik_skor.md §Kenar durumlar: "banka/sigorta/finansman
    şirketleri: mercek İÇ bileşen kümesi KÜÇÜLÜR ama 4-mercek ÜST
    ağırlıkları AYNI KALIR" -- hesapla_bilesik_skor() bu turda banka/
    sigorta/finansman için AYRI bir dallanma İÇERMEZ (ince orkestrasyon
    katmanı, kendi hesap mantığı taşımaz -- spec §Amaç), bu yüzden
    template etiketi "kalite_banka"/"güvenlik_finans" gibi olsa bile
    ağırlıklandırma (%30/%30/%25/%15) DEĞİŞMEZ."""
    deger = _lens_sonucu(Decimal(8), "değer")
    kalite = _lens_sonucu(Decimal(6), "kalite_banka")  # sadece ROE+ROA'dan olusan mercek
    guvenlik = _lens_sonucu(Decimal(7), "güvenlik_finans")  # sadece ozkaynak/aktif oranindan olusan mercek
    buyume = None  # banka Buyume merceği bazen "YETERSİZ VERİ" (spec'in kabul ettiği geçiş durumu)
    sonuc = hesapla_bilesik_skor("AKBNK", (2026, 3), deger, kalite, buyume, guvenlik)
    toplam_agirlik = Decimal(30 + 30 + 25)
    beklenen = (Decimal(8) * 30 + Decimal(6) * 30 + Decimal(7) * 25) / toplam_agirlik
    assert abs(sonuc.total_score - beklenen) < Decimal("0.0000001")
    assert set(sonuc.dahil_edilen_mercekler) == {"değer", "kalite", "güvenlik"}


# --- hesapla_veri_kapsam_ozeti (docs/spec/spec_dashboard.md §Formüller-0) -----------------------------------------------------


def test_hesapla_veri_kapsam_ozeti_dort_mercek_agirlikli_ortalama() -> None:
    """Spec "Test senaryoları" #3: THYAO benzeri, coverage'lar 88/100/62/100."""
    deger = _lens_sonucu(Decimal(8), "değer", coverage_pct=Decimal(88))
    kalite = _lens_sonucu(Decimal(6), "kalite", coverage_pct=Decimal(100))
    buyume = _lens_sonucu(Decimal(5), "büyüme", coverage_pct=Decimal(62))
    guvenlik = _lens_sonucu(Decimal(7), "güvenlik", coverage_pct=Decimal(100))
    bilesik = hesapla_bilesik_skor("THYAO", (2026, 3), deger, kalite, buyume, guvenlik)

    sonuc = hesapla_veri_kapsam_ozeti(bilesik)

    beklenen = (Decimal(88) * 30 + Decimal(100) * 30 + Decimal(100) * 25 + Decimal(62) * 15) / 100
    assert abs(sonuc - beklenen) < Decimal("0.01")


def test_hesapla_veri_kapsam_ozeti_eksik_mercek_paydaya_girmez() -> None:
    """Spec "Test senaryoları" #3: Banka (AKBNK, Büyüme=None) -- Büyüme
    ne payda NE payda GİRER, SADECE 3 mercek üzerinden hesaplanır (bileşik
    skorun efektif-ağırlık dağıtımından KASITLI olarak FARKLI: burada
    NOMİNAL ağırlıklar kullanılır, ama var-olmayan mercek hâlâ tamamen
    dışlanır)."""
    deger = _lens_sonucu(Decimal(8), "değer", coverage_pct=Decimal(90))
    kalite = _lens_sonucu(Decimal(6), "kalite_banka", coverage_pct=Decimal(100))
    guvenlik = _lens_sonucu(Decimal(7), "güvenlik_finans", coverage_pct=Decimal(80))
    bilesik = hesapla_bilesik_skor("AKBNK", (2026, 3), deger, kalite, None, guvenlik)

    sonuc = hesapla_veri_kapsam_ozeti(bilesik)

    toplam_agirlik = Decimal(30 + 30 + 25)
    beklenen = (Decimal(90) * 30 + Decimal(100) * 30 + Decimal(80) * 25) / toplam_agirlik
    assert abs(sonuc - beklenen) < Decimal("0.01")


def test_hesapla_veri_kapsam_ozeti_veri_yetersiz_mercek_de_dahil_edilir() -> None:
    """`hesapla_veri_kapsam_ozeti` bilesik_skor'un `dahil_edilen_mercekler`
    (data_sufficient eşiğiyle filtrelenmiş) listesini DEĞİL, mercek
    KAVRAMSAL OLARAK var mı (None mu değil mi) sorusunu sorar -- bir mercek
    data_sufficient=False olsa bile (bilesik skora KATILMASA bile) coverage
    özetine KATILIR (spec: "genel olarak ne kadar veriye dayanıyoruz")."""
    deger = _lens_sonucu(Decimal(8), "değer", coverage_pct=Decimal(90))
    kalite = _lens_sonucu(Decimal(2), "kalite", veri_yeterli=False, coverage_pct=Decimal(20))
    bilesik = hesapla_bilesik_skor("TEST", (2026, 3), deger, kalite, None, None)
    assert "kalite" not in bilesik.dahil_edilen_mercekler  # bilesik skora KATILMADI

    sonuc = hesapla_veri_kapsam_ozeti(bilesik)

    toplam_agirlik = Decimal(30 + 30)
    beklenen = (Decimal(90) * 30 + Decimal(20) * 30) / toplam_agirlik
    assert abs(sonuc - beklenen) < Decimal("0.01")


def test_hesapla_veri_kapsam_ozeti_tum_mercekler_none_ise_none_doner() -> None:
    bilesik = hesapla_bilesik_skor("TEST", (2026, 3), None, None, None, None)
    assert hesapla_veri_kapsam_ozeti(bilesik) is None
