"""SPEC: `docs/spec/spec_mercek_buyume.md` testleri -- Büyüme Merceği (v2)."""

from __future__ import annotations

from decimal import Decimal

from src.analysis import calculator
from src.analysis.lens_buyume import (
    BuyumeGirdisi,
    BuyumeGirdisiFinans,
    hesapla_buyume_mercegi,
    hesapla_buyume_mercegi_finans,
    _skor_capex_orani,
    _skor_marjinal_roe_ve_verimlilik,
    _skor_payout_orani,
    _skor_peg,
)

_LATEST = (2026, 3)
_QOQ_PRIOR = (2025, 12)
_YOY_PRIOR = (2025, 3)  # = year_ago_period(_LATEST), ayrica TTM(_YOY_PRIOR) icin (2024,12)/(2024,3) gerekir
_PRIOR_YEAR_FULL = (2024, 12)
_PRIOR_YEAR_SAME_Q = (2024, 3)


def _sample_financials(equity_yoy=Decimal("200")) -> dict:
    return {
        _LATEST: {
            "revenue": Decimal("120"), "revenue_cum": Decimal("120"),
            "net_income": Decimal("15"), "net_income_cum": Decimal("15"),
            "equity": Decimal("400"),
        },
        _QOQ_PRIOR: {
            "revenue": Decimal("140"), "revenue_cum": Decimal("140"),
            "net_income": Decimal("18"), "net_income_cum": Decimal("18"),
            "equity": Decimal("380"),
        },
        _YOY_PRIOR: {
            "revenue": Decimal("100"), "revenue_cum": Decimal("100"),
            "net_income": Decimal("10"), "net_income_cum": Decimal("10"),
            "equity": equity_yoy,
        },
        _PRIOR_YEAR_FULL: {
            "net_income_cum": Decimal("35"),
        },
        _PRIOR_YEAR_SAME_Q: {
            "net_income_cum": Decimal("8"),
        },
    }


def _analysis(equity_yoy=Decimal("200")):
    return calculator.analyze("TEST", _sample_financials(equity_yoy))


def test_buyume_mercegi_tum_veriyle_calisir() -> None:
    analysis = _analysis()
    fbp = _sample_financials()
    girdi = BuyumeGirdisi(analysis=analysis, financials_by_period=fbp, own_pe=Decimal("8"), enflasyon_yoy_pct=Decimal("10"))
    sonuc = hesapla_buyume_mercegi(girdi)
    assert sonuc.data_sufficient
    isimler = {c.name for c in sonuc.components}
    assert isimler == {
        "Hasılat Büyümesi (reel, seviye+trend)", "PEG Oranı (Lynch)", "Marjinal ROE + Verimlilik Kaynaklı Büyüme",
        "Capex/Net Kâr (Yeniden Yatırım Kalitesi)", "Payout Oranı (Temettü Disiplini)",
    }


def test_buyume_mercegi_own_pe_yoksa_peg_atlanir() -> None:
    analysis = _analysis()
    fbp = _sample_financials()
    girdi = BuyumeGirdisi(analysis=analysis, financials_by_period=fbp, own_pe=None)
    sonuc = hesapla_buyume_mercegi(girdi)
    isimler = {c.name: c for c in sonuc.components}
    assert isimler["PEG Oranı (Lynch)"].score is None
    assert sonuc.total_score > Decimal("0")


def test_hasilat_buyumesi_enflasyon_reel_buyumeyi_dusurur() -> None:
    analysis = _analysis()
    fbp = _sample_financials()
    yuksek_enflasyon = hesapla_buyume_mercegi(
        BuyumeGirdisi(analysis=analysis, financials_by_period=fbp, own_pe=None, enflasyon_yoy_pct=Decimal("19"))
    )
    dusuk_enflasyon = hesapla_buyume_mercegi(
        BuyumeGirdisi(analysis=analysis, financials_by_period=fbp, own_pe=None, enflasyon_yoy_pct=Decimal("0"))
    )
    isimler_yuksek = {c.name: c for c in yuksek_enflasyon.components}
    isimler_dusuk = {c.name: c for c in dusuk_enflasyon.components}
    assert isimler_yuksek["Hasılat Büyümesi (reel, seviye+trend)"].score < isimler_dusuk["Hasılat Büyümesi (reel, seviye+trend)"].score


# --- _skor_peg (U-sekli notu) -----------------------------------------------------


def test_skor_peg_negatif_buyumede_none() -> None:
    skor, gerekce = _skor_peg(Decimal("10"), Decimal("-5"))
    assert skor is None
    assert "atlandı" in gerekce


def test_skor_peg_dusuk_buyumede_u_sekli_notu_eklenir() -> None:
    skor, gerekce = _skor_peg(Decimal("10"), Decimal("2"))  # PEG=5, dusuk buyume
    assert skor is not None
    assert "yapısal olarak yüksek" in gerekce


# --- _skor_marjinal_roe_ve_verimlilik (K5a guard) -----------------------------------------------------


def test_marjinal_roe_negatif_ozkaynakta_none() -> None:
    analysis = _analysis(equity_yoy=Decimal("-10"))
    fbp = _sample_financials(equity_yoy=Decimal("-10"))
    skor, gerekce = _skor_marjinal_roe_ve_verimlilik(analysis, fbp)
    assert skor is None
    assert "atlandı" in gerekce


def test_marjinal_roe_pozitif_ozkaynakta_hesaplanir() -> None:
    analysis = _analysis()
    fbp = _sample_financials()
    skor, gerekce = _skor_marjinal_roe_ve_verimlilik(analysis, fbp)
    assert skor is not None
    assert Decimal("0") <= skor <= Decimal("10")
    assert "marjinal ROE" in gerekce


# --- hesapla_buyume_mercegi_finans (banka/sigorta/finansman -- spec §Sektör ayarlaması madde 3) -----------------------------------------------------

_SIG_LATEST = (2026, 3)
_SIG_QOQ = (2025, 12)
_SIG_YOY = (2025, 3)


_SIG_PRIOR_YEAR_FULL = (2024, 12)
_SIG_PRIOR_YEAR_SAME_Q = (2024, 3)


def _sigorta_fbp() -> dict:
    return {
        _SIG_LATEST: {
            "gross_written_premiums_cum": Decimal("500"), "gross_written_premiums": Decimal("500"),
            "net_premiums_earned_cum": Decimal("400"),
            "technical_income_cum": Decimal("300"), "technical_expense_cum": Decimal("-250"),
            "net_income_cum": Decimal("40"),
            "receivables_from_operations": Decimal("100"), "payables_from_operations": Decimal("80"),
            "equity": Decimal("600"), "share_capital": Decimal("200"),
        },
        _SIG_QOQ: {"net_income_cum": Decimal("140"), "equity": Decimal("560")},
        _SIG_YOY: {"gross_written_premiums": Decimal("400"), "net_income_cum": Decimal("30"), "equity": Decimal("480")},
        _SIG_PRIOR_YEAR_FULL: {"net_income_cum": Decimal("110")},
        _SIG_PRIOR_YEAR_SAME_Q: {"net_income_cum": Decimal("25")},
    }


def _sigorta_analysis():
    return calculator.analyze_insurance("TESTSIG", _sigorta_fbp())


def _banka_fbp() -> dict:
    return {
        _SIG_LATEST: {
            "interest_income_cum": Decimal("500"), "interest_expense_cum": Decimal("-200"),
            "net_income_cum": Decimal("120"),
            "loans": Decimal("4000"), "deposits": Decimal("4500"), "total_assets": Decimal("10000"),
            "equity": Decimal("1200"), "share_capital": Decimal("500"),
        },
        _SIG_QOQ: {"interest_income_cum": Decimal("1600"), "net_income_cum": Decimal("380"), "loans": Decimal("3800"), "equity": Decimal("1100")},
        _SIG_YOY: {"interest_income_cum": Decimal("420"), "net_income_cum": Decimal("95"), "loans": Decimal("3200"), "equity": Decimal("950")},
        _SIG_PRIOR_YEAR_FULL: {"net_income_cum": Decimal("340")},
        _SIG_PRIOR_YEAR_SAME_Q: {"net_income_cum": Decimal("80")},
    }


def _banka_analysis():
    return calculator.analyze_bank("TESTBANK", _banka_fbp())


def test_buyume_mercegi_finans_sigorta_prim_buyumesi_bileseni_uretir() -> None:
    analysis = _sigorta_analysis()
    fbp = _sigorta_fbp()
    girdi = BuyumeGirdisiFinans(
        analysis=analysis, financials_by_period=fbp, template="sigorta",
        buyume_orani_pct=analysis.ratios.premium_growth_yoy_pct, buyume_metrik_adi="prim",
        own_pe=Decimal("8"),
    )
    sonuc = hesapla_buyume_mercegi_finans(girdi)
    isimler = {c.name: c for c in sonuc.components}
    assert "Prim Büyümesi (reel, seviye+trend)" in isimler
    assert isimler["Prim Büyümesi (reel, seviye+trend)"].score is not None
    assert isimler["PEG Oranı (Lynch)"].score is not None
    assert sonuc.total_score > Decimal("0")


def test_buyume_mercegi_finans_banka_kredi_buyumesi_bileseni_uretir() -> None:
    analysis = _banka_analysis()
    fbp = _banka_fbp()
    kredi_buyume_pct, _label, _direction = calculator.classify_change(
        fbp[_SIG_LATEST]["loans"], fbp[_SIG_YOY]["loans"]
    )
    girdi = BuyumeGirdisiFinans(
        analysis=analysis, financials_by_period=fbp, template="banka",
        buyume_orani_pct=kredi_buyume_pct, buyume_metrik_adi="kredi",
    )
    sonuc = hesapla_buyume_mercegi_finans(girdi)
    isimler = {c.name: c for c in sonuc.components}
    assert "Kredi Büyümesi (reel, seviye+trend)" in isimler
    assert isimler["Kredi Büyümesi (reel, seviye+trend)"].score is not None
    assert isimler["Marjinal ROE + Verimlilik Kaynaklı Büyüme"].score is not None


# --- YENİ bileşenler (docs/spec/spec_yeni_bilesenler_agirliklandirma.md §3) -----------------------------------------------------


def test_buyume_mercegi_agirlik_toplami_her_zaman_yuz() -> None:
    """Nominal ağırlıklar (veri durumundan BAĞIMSIZ, statik) HER ZAMAN
    %100'e tamamlanmalı -- 3 eski + 2 yeni bileşen (55+15+17+8+5)."""
    analysis = _analysis()
    fbp = _sample_financials()
    girdi = BuyumeGirdisi(analysis=analysis, financials_by_period=fbp, own_pe=Decimal("8"))
    sonuc = hesapla_buyume_mercegi(girdi)
    toplam_nominal = sum((c.weight_nominal for c in sonuc.components), Decimal(0))
    assert toplam_nominal == Decimal(100)


def test_buyume_mercegi_capex_payout_veri_eksikse_none_agirlik_dagitilir() -> None:
    """Fixture'da capex_cum/dividends_paid_cum YOK -- iki yeni bileşen de
    None döner, ağırlığı diğer 3 bileşene ORANTISAL dağıtılır, mercek YİNE
    'YETERSİZ VERİ' düşmez."""
    analysis = _analysis()
    fbp = _sample_financials()
    girdi = BuyumeGirdisi(analysis=analysis, financials_by_period=fbp, own_pe=Decimal("8"))
    sonuc = hesapla_buyume_mercegi(girdi)
    isimler = {c.name: c for c in sonuc.components}
    assert isimler["Capex/Net Kâr (Yeniden Yatırım Kalitesi)"].score is None
    assert isimler["Payout Oranı (Temettü Disiplini)"].score is None
    assert sonuc.data_sufficient
    assert sonuc.total_score > Decimal("0")


def test_buyume_mercegi_capex_payout_verilerle_hesaplanir_bist_nasdaq_simetrik() -> None:
    """Capex/Net Kâr ve Payout Oranı, mercek çoğunluğundan (KALİTE §1/
    GÜVENLİK §2, SADECE NASDAQ) FARKLI olarak BİST'te de dolu olur --
    isyatirim.py '4CAI'/'4CBB' itemCode'ları PİYASA-BAĞIMSIZ."""
    finansallar = _sample_financials()
    # ttm_net_income = net_income_cum(_LATEST) + net_income_cum(_QOQ_PRIOR) - net_income_cum(_YOY_PRIOR)
    # = 15 + 18 - 10 = 23 (calculator._trailing_12m_from_cumulative -- year_ago(latest)=_YOY_PRIOR,
    # latest yilin bir onceki tam yili=_QOQ_PRIOR (2025,12)).
    finansallar[_LATEST]["capex_cum"] = Decimal("2")
    finansallar[_QOQ_PRIOR]["capex_cum"] = Decimal("6")
    finansallar[_YOY_PRIOR]["capex_cum"] = Decimal("3")
    finansallar[_LATEST]["dividends_paid_cum"] = Decimal("4")
    finansallar[_QOQ_PRIOR]["dividends_paid_cum"] = Decimal("18")
    finansallar[_YOY_PRIOR]["dividends_paid_cum"] = Decimal("6")
    analysis = calculator.analyze("TESTBIST", finansallar)
    girdi = BuyumeGirdisi(analysis=analysis, financials_by_period=finansallar, own_pe=Decimal("8"))
    sonuc = hesapla_buyume_mercegi(girdi)
    isimler = {c.name: c for c in sonuc.components}
    # ttm_net_income=23 -- ttm_capex=5 (2+6-3) -> %21,7 (mukemmel bandi)
    assert isimler["Capex/Net Kâr (Yeniden Yatırım Kalitesi)"].score is not None
    assert isimler["Capex/Net Kâr (Yeniden Yatırım Kalitesi)"].score > Decimal("8")
    # ttm_dividends_paid=16 (4+18-6) -> %69,57 (60-75 bandı ortasına yakın, yuksek puan)
    assert isimler["Payout Oranı (Temettü Disiplini)"].score is not None
    assert isimler["Payout Oranı (Temettü Disiplini)"].score > Decimal("8")
    assert sonuc.data_sufficient


def test_skor_capex_orani_dusuk_oranda_yuksek_puan_yuksek_oranda_dusuk_puan() -> None:
    dusuk_skor, _ = _skor_capex_orani(Decimal("10"))
    yuksek_skor, _ = _skor_capex_orani(Decimal("90"))
    assert dusuk_skor > yuksek_skor


def test_skor_capex_orani_none_ise_atlanir() -> None:
    skor, gerekce = _skor_capex_orani(None)
    assert skor is None
    assert "atlandı" in gerekce


def test_skor_payout_orani_bant_ortasinda_yuksek_puan() -> None:
    skor, gerekce = _skor_payout_orani(Decimal("67.5"))
    assert skor is not None
    assert skor >= Decimal("9")
    assert "%60-75" in gerekce


def test_skor_payout_orani_dusuk_payoutta_hafif_ceza() -> None:
    dusuk_skor, _ = _skor_payout_orani(Decimal("10"))
    bant_skor, _ = _skor_payout_orani(Decimal("67.5"))
    assert dusuk_skor < bant_skor
    assert dusuk_skor > Decimal("0")  # İLKE-180 hafif ceza, SIFIRA vurmaz


def test_skor_payout_orani_asiri_yuksekte_dusuk_puan() -> None:
    skor, _ = _skor_payout_orani(Decimal("95"))
    bant_skor, _ = _skor_payout_orani(Decimal("67.5"))
    assert skor is not None
    assert skor < bant_skor


def test_skor_payout_orani_none_ise_atlanir() -> None:
    skor, gerekce = _skor_payout_orani(None)
    assert skor is None
    assert "atlandı" in gerekce


def test_buyume_mercegi_finans_buyume_verisi_yoksa_atlanir_diger_bilesenler_calisir() -> None:
    analysis = _sigorta_analysis()
    fbp = _sigorta_fbp()
    girdi = BuyumeGirdisiFinans(
        analysis=analysis, financials_by_period=fbp, template="sigorta",
        buyume_orani_pct=None, buyume_metrik_adi="prim", own_pe=Decimal("8"),
    )
    sonuc = hesapla_buyume_mercegi_finans(girdi)
    isimler = {c.name: c for c in sonuc.components}
    assert isimler["Prim Büyümesi (reel, seviye+trend)"].score is None
    # PEG de buyume_orani_pct'e bagli oldugu icin (payda) o da None olmali.
    assert isimler["PEG Oranı (Lynch)"].score is None
    # Marjinal ROE buyume oranindan BAGIMSIZ -- HALA calisir.
    assert isimler["Marjinal ROE + Verimlilik Kaynaklı Büyüme"].score is not None
    assert sonuc.total_score > Decimal("0")
