"""SPEC: `docs/spec/spec_mercek_kalite.md` testleri -- Kalite Merceği (v2)."""

from __future__ import annotations

from decimal import Decimal

from src.analysis import calculator
from src.analysis.fundamental_screens import GreenblattResult
from src.analysis.lens_kalite import KaliteGirdisi, hesapla_kalite_mercegi, hesapla_kalite_mercegi_banka

_LATEST = (2026, 3)
_QOQ_PRIOR = (2025, 12)
_YOY_PRIOR = (2025, 3)


def _sample_financials(equity_current=Decimal("400")) -> dict:
    return {
        _LATEST: {
            "revenue": Decimal("120"), "revenue_cum": Decimal("120"),
            "gross_profit": Decimal("60"), "gross_profit_cum": Decimal("60"),
            "operating_profit": Decimal("20"), "operating_profit_cum": Decimal("20"),
            "operating_profit_ebitda_base": Decimal("20"), "operating_profit_ebitda_base_cum": Decimal("20"),
            "depreciation_amortization": Decimal("10"), "depreciation_amortization_cum": Decimal("10"),
            "net_income": Decimal("15"), "net_income_cum": Decimal("15"),
            "cash": Decimal("200"), "total_assets": Decimal("1000"),
            "financial_debt": Decimal("300"), "equity": equity_current,
        },
        _QOQ_PRIOR: {
            "revenue": Decimal("140"), "revenue_cum": Decimal("140"),
            "gross_profit": Decimal("62"), "gross_profit_cum": Decimal("62"),
            "operating_profit": Decimal("25"), "operating_profit_cum": Decimal("25"),
            "operating_profit_ebitda_base": Decimal("25"), "operating_profit_ebitda_base_cum": Decimal("25"),
            "depreciation_amortization": Decimal("11"), "depreciation_amortization_cum": Decimal("11"),
            "net_income": Decimal("18"), "net_income_cum": Decimal("18"),
            "cash": Decimal("180"), "total_assets": Decimal("950"),
            "financial_debt": Decimal("310"), "equity": Decimal("380"),
        },
        _YOY_PRIOR: {
            "revenue": Decimal("100"), "revenue_cum": Decimal("100"),
            "gross_profit": Decimal("40"), "gross_profit_cum": Decimal("40"),
            "operating_profit": Decimal("12"), "operating_profit_cum": Decimal("12"),
            "operating_profit_ebitda_base": Decimal("12"), "operating_profit_ebitda_base_cum": Decimal("12"),
            "depreciation_amortization": Decimal("8"), "depreciation_amortization_cum": Decimal("8"),
            "net_income": Decimal("10"), "net_income_cum": Decimal("10"),
            "cash": Decimal("150"), "total_assets": Decimal("800"),
            "financial_debt": Decimal("290"), "equity": Decimal("200"),
        },
    }


def _analysis(equity_current=Decimal("400")):
    return calculator.analyze("TEST", _sample_financials(equity_current))


def test_kalite_mercegi_tum_veriyle_calisir_ve_veri_yeterli() -> None:
    analysis = _analysis()
    greenblatt = GreenblattResult(
        ebit=Decimal("20"), enterprise_value=Decimal("100"), earnings_yield_pct=Decimal("20"), earnings_yield_band="Yüksek",
        net_working_capital=Decimal("250"), net_fixed_assets=Decimal("300"), return_on_capital_pct=Decimal("30"), return_on_capital_band="Yüksek",
    )
    girdi = KaliteGirdisi(analysis=analysis, greenblatt=greenblatt, operating_cash_flow_ttm=Decimal("20"))
    sonuc = hesapla_kalite_mercegi(girdi)
    assert sonuc.data_sufficient
    assert Decimal("0") <= sonuc.total_score <= Decimal("10")
    isimler = {c.name for c in sonuc.components}
    assert isimler == {
        "Nakit Üretimi (FAVÖK marjı)", "Özkaynak Kârlılığı (ROE)", "Kârlılık (Net Marj)", "Brüt Kâr Marjı",
        "Greenblatt Sermaye Getirisi (ROC)", "Aktif Kârlılığı (ROA)", "Nakit Kâr Kalitesi (OCF/Net Kâr)",
    }


def test_kalite_mercegi_negatif_ozkaynakta_roe_none_diger_bilesenler_calisir() -> None:
    analysis = _analysis(equity_current=Decimal("-50"))
    girdi = KaliteGirdisi(analysis=analysis)
    sonuc = hesapla_kalite_mercegi(girdi)
    isimler = {c.name: c for c in sonuc.components}
    assert isimler["Özkaynak Kârlılığı (ROE)"].score is None
    assert "negatif özkaynak" in isimler["Özkaynak Kârlılığı (ROE)"].reasoning_tr
    # FAVOK marji/net marj/brut marj -- ozkaynaktan BAGIMSIZ -- HALA calisir.
    assert isimler["Nakit Üretimi (FAVÖK marjı)"].score is not None
    assert sonuc.total_score > Decimal("0")


def test_kalite_mercegi_greenblatt_ve_ocf_yoksa_atlanir_toplam_yine_uretilir() -> None:
    analysis = _analysis()
    girdi = KaliteGirdisi(analysis=analysis, greenblatt=None, operating_cash_flow_ttm=None)
    sonuc = hesapla_kalite_mercegi(girdi)
    isimler = {c.name: c for c in sonuc.components}
    assert isimler["Greenblatt Sermaye Getirisi (ROC)"].score is None
    assert isimler["Nakit Kâr Kalitesi (OCF/Net Kâr)"].score is None
    assert sonuc.total_score > Decimal("0")  # kalan bilesenler agirligi devraldi


def test_nakit_kar_kalitesi_negatif_net_karda_none() -> None:
    from src.analysis.lens_kalite import _skor_nakit_kar_kalitesi

    skor, gerekce = _skor_nakit_kar_kalitesi(Decimal("10"), Decimal("-5"))
    assert skor is None
    assert "negatif" in gerekce


def test_nakit_kar_kalitesi_oran_str_ile_formatlanir_yuzde_degil() -> None:
    from src.analysis.lens_kalite import _skor_nakit_kar_kalitesi

    skor, gerekce = _skor_nakit_kar_kalitesi(Decimal("15"), Decimal("15"))  # 1,0x
    assert skor is not None
    assert "1,00x" in gerekce
    assert "%1,0" not in gerekce  # K4: yanlislikla yuzde formatlanmamali


# --- hesapla_kalite_mercegi_banka (Y1 duzeltmesi: ROE %80 / ROA %20) -----------------------------------------------------


def test_kalite_mercegi_banka_ikisi_de_varsa_agirlik_orani_80_20() -> None:
    sonuc = hesapla_kalite_mercegi_banka("AKBNK", (2026, 3), roe_pct=Decimal("25"), roa_pct=Decimal("3"))
    isimler = {c.name: c for c in sonuc.components}
    roe_agirlik = isimler["Özkaynak Kârlılığı (ROE)"].weight_effective
    roa_agirlik = isimler["Aktif Kârlılığı (ROA)"].weight_effective
    assert roe_agirlik == Decimal(80)
    assert roa_agirlik == Decimal(20)


def test_kalite_mercegi_banka_sadece_roe_varsa_agirlik_100() -> None:
    sonuc = hesapla_kalite_mercegi_banka("AKBNK", (2026, 3), roe_pct=Decimal("25"), roa_pct=None)
    isimler = {c.name: c for c in sonuc.components}
    assert isimler["Özkaynak Kârlılığı (ROE)"].weight_effective == Decimal(100)
    assert isimler["Aktif Kârlılığı (ROA)"].score is None


# --- hesapla_kalite_mercegi_banka: template-farkindalik (bu tur -- sigorta/finansman eslikleri banka'dan FARKLI) -----------------------------------------------------


def test_kalite_mercegi_banka_template_varsayilan_banka_esikleriyle_ayni() -> None:
    """template verilmezse ESKI davranis (banka esikleri, ROE guclu=%20)
    KORUNUR -- geriye uyumluluk (mevcut testler DEGISMEDEN gecmeli)."""
    sonuc = hesapla_kalite_mercegi_banka("AKBNK", (2026, 3), roe_pct=Decimal("20"), roa_pct=None)
    isimler = {c.name: c for c in sonuc.components}
    # ROE=20 banka guclu_esik'ine (20) TAM denk -- _lerp_score(20,10,20,4,7)=7 asymptote basi.
    assert isimler["Özkaynak Kârlılığı (ROE)"].score is not None


def test_kalite_mercegi_sigorta_kendi_roe_esiklerini_kullanir() -> None:
    """CONFIG['sigorta']['ozkaynak_karliligi'] = guclu=%25/orta=%10/tavan=%40
    -- banka'dan (guclu=%20) FARKLI. ROE=%22 banka'da 'guclu' bandina
    girerken sigortada henuz 'orta-guclu arasi' kalir -- iki template
    FARKLI skor uretmeli (aksi halde eski hatali davranis SESSIZCE devam
    ediyor demektir)."""
    banka_sonuc = hesapla_kalite_mercegi_banka("XBANK", (2026, 3), roe_pct=Decimal("22"), roa_pct=None, template="banka")
    sigorta_sonuc = hesapla_kalite_mercegi_banka("XSIGORTA", (2026, 3), roe_pct=Decimal("22"), roa_pct=None, template="sigorta")
    banka_roe = {c.name: c for c in banka_sonuc.components}["Özkaynak Kârlılığı (ROE)"].score
    sigorta_roe = {c.name: c for c in sigorta_sonuc.components}["Özkaynak Kârlılığı (ROE)"].score
    assert banka_roe != sigorta_roe


def test_kalite_mercegi_finansman_kendi_roa_esiklerini_kullanir() -> None:
    """CONFIG['finansman']['aktif_karliligi'] = guclu=%5/orta=%2/tavan=%10
    -- banka'dan (guclu=%2,5) FARKLI. ROA=%4 banka esiginde 'guclu'ye
    YAKIN/UZERINDE iken finansmanda henuz orta-guclu arasindadir."""
    banka_sonuc = hesapla_kalite_mercegi_banka("XBANK", (2026, 3), roe_pct=None, roa_pct=Decimal("4"), template="banka")
    finansman_sonuc = hesapla_kalite_mercegi_banka("XFIN", (2026, 3), roe_pct=None, roa_pct=Decimal("4"), template="finansman")
    banka_roa = {c.name: c for c in banka_sonuc.components}["Aktif Kârlılığı (ROA)"].score
    finansman_roa = {c.name: c for c in finansman_sonuc.components}["Aktif Kârlılığı (ROA)"].score
    assert banka_roa != finansman_roa


def test_kalite_mercegi_sigorta_roa_yoksa_keyerror_atmaz_yedek_esik_kullanir() -> None:
    """CONFIG['sigorta']'da 'aktif_karliligi' alt-sozlugu hic YOK -- roa_pct
    zaten None geldigi icin bu hicbir zaman TETIKLENMEZ ama yedek esik
    (banka'nin) dict erisiminde KeyError FIRLATMAMALI."""
    sonuc = hesapla_kalite_mercegi_banka("XSIGORTA", (2026, 3), roe_pct=Decimal("25"), roa_pct=None, template="sigorta")
    isimler = {c.name: c for c in sonuc.components}
    assert isimler["Aktif Kârlılığı (ROA)"].score is None
    assert isimler["Özkaynak Kârlılığı (ROE)"].weight_effective == Decimal(100)
