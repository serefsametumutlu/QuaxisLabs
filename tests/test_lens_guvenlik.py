"""SPEC: `docs/spec/spec_mercek_guvenlik.md` testleri -- Güvenlik Merceği (v2)."""

from __future__ import annotations

from decimal import Decimal

from src.analysis import calculator
from src.analysis.fundamental_screens import PiotroskiResult
from src.analysis.lens_guvenlik import (
    GuvenlikGirdisi,
    _skor_faiz_karsilama,
    _skor_merton,
    _skor_ozkaynak_aktif_orani,
    _skor_piotroski,
    _skor_toplam_yukumluluk_ozkaynak,
    hesapla_guvenlik_mercegi,
    hesapla_guvenlik_mercegi_finans,
)
from src.analysis.merton import MertonResult

_LATEST = (2026, 3)
_QOQ_PRIOR = (2025, 12)
_TTM_3 = (2025, 9)
_TTM_4 = (2025, 6)
_YOY_PRIOR = (2025, 3)


def _sample_financials(equity_current=Decimal("400"), stl=Decimal("250"), ltl=Decimal("150")) -> dict:
    return {
        _LATEST: {
            "revenue": Decimal("120"), "revenue_cum": Decimal("120"),
            "operating_profit_ebitda_base": Decimal("20"), "operating_profit_ebitda_base_cum": Decimal("20"),
            "depreciation_amortization": Decimal("10"), "depreciation_amortization_cum": Decimal("10"),
            "net_income": Decimal("15"), "net_income_cum": Decimal("15"),
            "cash": Decimal("200"), "total_assets": Decimal("1000"),
            "financial_debt": Decimal("300"), "equity": equity_current,
            "current_assets": Decimal("500"), "short_term_liabilities": stl, "long_term_liabilities": ltl,
        },
        _QOQ_PRIOR: {
            "operating_profit_ebitda_base": Decimal("22"), "operating_profit_ebitda_base_cum": Decimal("22"),
            "depreciation_amortization": Decimal("10"), "depreciation_amortization_cum": Decimal("10"),
        },
        _TTM_3: {
            "operating_profit_ebitda_base": Decimal("22"), "operating_profit_ebitda_base_cum": Decimal("22"),
            "depreciation_amortization": Decimal("10"), "depreciation_amortization_cum": Decimal("10"),
        },
        _TTM_4: {
            "operating_profit_ebitda_base": Decimal("15"), "operating_profit_ebitda_base_cum": Decimal("15"),
            "depreciation_amortization": Decimal("9"), "depreciation_amortization_cum": Decimal("9"),
        },
        _YOY_PRIOR: {
            "operating_profit_ebitda_base": Decimal("12"), "operating_profit_ebitda_base_cum": Decimal("12"),
            "depreciation_amortization": Decimal("8"), "depreciation_amortization_cum": Decimal("8"),
        },
    }


def _analysis(equity_current=Decimal("400"), stl=Decimal("250"), ltl=Decimal("150")):
    return calculator.analyze("TEST", _sample_financials(equity_current, stl, ltl))


def test_guvenlik_mercegi_tum_veriyle_calisir() -> None:
    analysis = _analysis()
    fbp = _sample_financials()
    piotroski = PiotroskiResult(score=7, criteria_evaluated=9, band="Güçlü", details=[])
    merton = MertonResult(
        asset_value=Decimal("1000"), asset_volatility_pct=Decimal("30"), debt_face_value=Decimal("300"),
        distance_to_default=Decimal("3"), default_probability_pct=Decimal("1.5"), converged=True,
    )
    girdi = GuvenlikGirdisi(analysis=analysis, financials_by_period=fbp, piotroski=piotroski, merton=merton)
    sonuc = hesapla_guvenlik_mercegi(girdi)
    assert sonuc.data_sufficient
    isimler = {c.name for c in sonuc.components}
    assert isimler == {
        "Kaldıraç (Net Borç/FAVÖK)", "Bilanço Kalitesi (Cari Oran + Özkaynak/Varlık)", "Piotroski F-Skoru",
        "Toplam Yükümlülük/Özkaynak (geniş tanım)", "Merton Temerrüt Olasılığı (EDF)", "Finansman Gideri Karşılama Oranı",
    }


def test_guvenlik_mercegi_piotroski_merton_yoksa_atlanir_toplam_uretilir() -> None:
    analysis = _analysis()
    fbp = _sample_financials()
    girdi = GuvenlikGirdisi(analysis=analysis, financials_by_period=fbp, piotroski=None, merton=None)
    sonuc = hesapla_guvenlik_mercegi(girdi)
    isimler = {c.name: c for c in sonuc.components}
    assert isimler["Piotroski F-Skoru"].score is None
    assert isimler["Merton Temerrüt Olasılığı (EDF)"].score is None
    assert sonuc.total_score > Decimal("0")


# --- _skor_toplam_yukumluluk_ozkaynak (K3a duzeltmesi) -----------------------------------------------------


def test_toplam_yukumluluk_ozkaynak_negatif_ozkaynakta_none() -> None:
    analysis = _analysis(equity_current=Decimal("-50"))
    fbp = _sample_financials(equity_current=Decimal("-50"))
    skor, gerekce = _skor_toplam_yukumluluk_ozkaynak(analysis, fbp)
    assert skor is None
    assert "negatif" in gerekce


def test_toplam_yukumluluk_ozkaynak_dusuk_oranda_yuksek_skor() -> None:
    analysis = _analysis(equity_current=Decimal("1000"), stl=Decimal("100"), ltl=Decimal("100"))
    fbp = _sample_financials(equity_current=Decimal("1000"), stl=Decimal("100"), ltl=Decimal("100"))
    skor, gerekce = _skor_toplam_yukumluluk_ozkaynak(analysis, fbp)
    assert skor is not None
    assert skor > Decimal("8")
    assert "x" in gerekce  # oran_str biciminde x-kati gosterilir
    assert "%" not in gerekce.split("--")[0]  # K4: yuzde DEGIL


def test_toplam_yukumluluk_ozkaynak_veri_eksikse_none() -> None:
    analysis = _analysis()
    fbp = {analysis.latest_period: {"equity": Decimal("400")}}  # stl/ltl yok
    skor, gerekce = _skor_toplam_yukumluluk_ozkaynak(analysis, fbp)
    assert skor is None
    assert "eksik" in gerekce


# --- _skor_piotroski -----------------------------------------------------


def test_skor_piotroski_none_ise_atlanir() -> None:
    skor, gerekce = _skor_piotroski(None)
    assert skor is None
    assert "atlandı" in gerekce


def test_skor_piotroski_yuksek_oranda_yuksek_puan() -> None:
    piotroski = PiotroskiResult(score=8, criteria_evaluated=9, band="Güçlü", details=[])
    skor, _ = _skor_piotroski(piotroski)
    assert skor is not None
    assert skor > Decimal("7")


# --- _skor_merton -----------------------------------------------------


def test_skor_merton_none_ise_atlanir() -> None:
    skor, gerekce = _skor_merton(None)
    assert skor is None
    assert "atlandı" in gerekce


def test_skor_merton_dusuk_edf_yuksek_puan() -> None:
    merton = MertonResult(
        asset_value=Decimal("1000"), asset_volatility_pct=Decimal("20"), debt_face_value=Decimal("100"),
        distance_to_default=Decimal("5"), default_probability_pct=Decimal("0.5"), converged=True,
    )
    skor, gerekce = _skor_merton(merton)
    assert skor is not None
    assert skor > Decimal("7")
    assert "Merton" in gerekce


def test_skor_merton_yuksek_edf_dusuk_puan() -> None:
    merton = MertonResult(
        asset_value=Decimal("1000"), asset_volatility_pct=Decimal("80"), debt_face_value=Decimal("900"),
        distance_to_default=Decimal("0.2"), default_probability_pct=Decimal("35"), converged=True,
    )
    skor, _ = _skor_merton(merton)
    assert skor is not None
    assert skor < Decimal("3")


# --- hesapla_guvenlik_mercegi_finans (banka/sigorta/finansman -- spec §Sektör ayarlaması madde 1) -----------------------------------------------------


def test_skor_ozkaynak_aktif_orani_veri_yoksa_atlanir() -> None:
    skor, gerekce = _skor_ozkaynak_aktif_orani(None)
    assert skor is None
    assert "atlandı" in gerekce


def test_skor_ozkaynak_aktif_orani_guclu_oranda_yuksek_puan() -> None:
    skor, gerekce = _skor_ozkaynak_aktif_orani(Decimal("15"))
    assert skor is not None
    assert skor > Decimal("6")
    assert "sermaye yeterliliği" in gerekce


def test_guvenlik_mercegi_finans_banka_ozkaynak_aktif_orani_ile_calisir() -> None:
    """Banka/finansman: ozkaynak_aktif_orani MEVCUT (BankRatios/
    FinancingRatios'ta zaten var), Piotroski YAPISAL OLARAK YOK -- bu tur
    (fundamental_screens.py SADECE XI_29 sanayi icin hesaplar) Piotroski
    bileseni bilesen LISTESINDEN TAMAMEN CIKARILIR (None-skorlu bir satir
    olarak DEGIL) ki nominal agirlik %100 tek bilesende toplanip
    data_sufficient DOGRU calissin (bkz. modul notu -- 44,44/55,56 split
    Piotroski HICBIR ZAMAN dolmadigi surece merceği surekli 'yetersiz'
    birakirdi)."""
    sonuc = hesapla_guvenlik_mercegi_finans("AKBNK", (2026, 3), ozkaynak_aktif_orani_pct=Decimal("14"), piotroski=None)
    isimler = {c.name: c for c in sonuc.components}
    assert isimler["Özkaynak/Aktif Oranı (sermaye yeterliliği proxy'si)"].score is not None
    assert isimler["Özkaynak/Aktif Oranı (sermaye yeterliliği proxy'si)"].weight_effective == Decimal(100)
    assert "Piotroski Benzeri Finansal Sağlık Taraması" not in isimler
    assert sonuc.data_sufficient
    assert sonuc.total_score > Decimal("0")


def test_guvenlik_mercegi_finans_sigorta_veri_yoksa_yetersiz_veri() -> None:
    """Sigorta (UFRS_K) semasinda total_assets HIC YOK -- ozkaynak_aktif_
    orani_pct de None gelir, Piotroski de None -- HICBIR bilesen veri
    uretmez, mercek durustce 'YETERSIZ VERI' doner (Kural 3, uydurma yok)."""
    sonuc = hesapla_guvenlik_mercegi_finans("XSIGORTA", (2026, 3), ozkaynak_aktif_orani_pct=None, piotroski=None)
    assert not sonuc.data_sufficient
    assert sonuc.total_score == Decimal("0")


# --- Finansman Gideri Karşılama Oranı (docs/spec/spec_yeni_bilesenler_agirliklandirma.md §2) -----------------------------------------------------


def test_guvenlik_mercegi_agirlik_toplami_her_zaman_yuz() -> None:
    """Nominal ağırlıklar (veri durumundan BAĞIMSIZ, statik) HER ZAMAN
    %100'e tamamlanmalı -- 5 eski + 1 yeni bileşen (29+18+24+12+7+10)."""
    analysis = _analysis()
    fbp = _sample_financials()
    girdi = GuvenlikGirdisi(analysis=analysis, financials_by_period=fbp)
    sonuc = hesapla_guvenlik_mercegi(girdi)
    toplam_nominal = sum((c.weight_nominal for c in sonuc.components), Decimal(0))
    assert toplam_nominal == Decimal(100)


def test_guvenlik_mercegi_bist_faiz_karsilama_none_agirlik_dagitilir() -> None:
    """BİST sanayi haritasında interest_expense hiç çekilmiyor -- Finansman
    Gideri Karşılama Oranı HER ZAMAN None döner, ağırlığı diğer 5 bileşene
    ORANTISAL dağıtılır."""
    analysis = _analysis()  # interest_expense fixture'da YOK
    fbp = _sample_financials()
    girdi = GuvenlikGirdisi(analysis=analysis, financials_by_period=fbp)
    sonuc = hesapla_guvenlik_mercegi(girdi)
    isimler = {c.name: c for c in sonuc.components}
    assert isimler["Finansman Gideri Karşılama Oranı"].score is None
    assert sonuc.data_sufficient
    assert sonuc.total_score > Decimal("0")


def test_guvenlik_mercegi_nasdaq_benzeri_veriyle_faiz_karsilama_hesaplanir() -> None:
    finansallar = _sample_financials()
    finansallar[_LATEST]["operating_profit"] = Decimal("20")
    finansallar[_LATEST]["interest_expense"] = Decimal("1")  # oran = 1/20*100 = %5 -- coverage = 100/5 = 20x (AAA)
    analysis = calculator.analyze("TESTUS", finansallar)
    girdi = GuvenlikGirdisi(analysis=analysis, financials_by_period=finansallar)
    sonuc = hesapla_guvenlik_mercegi(girdi)
    isimler = {c.name: c for c in sonuc.components}
    assert isimler["Finansman Gideri Karşılama Oranı"].score == Decimal("10.0")
    assert "AAA" in isimler["Finansman Gideri Karşılama Oranı"].reasoning_tr


def test_skor_faiz_karsilama_none_veya_sifir_faiz_giderinde_atlanir() -> None:
    skor, gerekce = _skor_faiz_karsilama(None)
    assert skor is None
    assert "atlandı" in gerekce
    skor2, _ = _skor_faiz_karsilama(Decimal("0"))
    assert skor2 is None


def test_skor_faiz_karsilama_dusuk_kaldirac_dusuk_puan_damodaran_bandi() -> None:
    """oran = 100/faiz_gideri_orani -- faiz_gideri_orani=%80 -> coverage=1,25x
    -- Damodaran Tablo 2.4 sınırında (CC/CCC), düşük puan."""
    skor, gerekce = _skor_faiz_karsilama(Decimal("80"))
    assert skor is not None
    assert skor < Decimal("2")
    assert "Damodaran" in gerekce


def test_skor_faiz_karsilama_guclu_kaldirac_yuksek_puan() -> None:
    """faiz_gideri_orani=%5 -> coverage=20x -- Damodaran'ın AAA (>12,5x)
    tavanının üstünde, sabit 10,0."""
    skor, gerekce = _skor_faiz_karsilama(Decimal("5"))
    assert skor == Decimal("10.0")
    assert "AAA" in gerekce
