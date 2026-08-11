"""SPEC: `docs/spec/spec_bilesik_skor.md` testleri -- Bileşik Skor (4
merceğin birleşimi, v2)."""

from __future__ import annotations

from decimal import Decimal

from src.analysis.lens_bilesik_skor import hesapla_bilesik_skor
from src.analysis.lens_common import ComponentScore, ScoreResult, YETERSIZ_VERI_ROZETI


def _lens_sonucu(skor: Decimal, template: str, veri_yeterli: bool = True) -> ScoreResult:
    return ScoreResult(
        ticker="TEST", period=(2026, 3), template=template, total_score=skor,
        badge="DENGELİ", data_coverage_pct=Decimal(100), data_sufficient=veri_yeterli,
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
