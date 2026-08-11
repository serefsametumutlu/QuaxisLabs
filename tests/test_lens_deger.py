"""SPEC: `docs/spec/spec_mercek_deger.md` testleri -- Değer Merceği (v2).

Fixture deseni `tests/test_calculator.py::_sample_financials()` ile AYNI
ilkeyi izler (bkz. o dosyanın üst notu): "_cum" alanları kasıtlı olarak
çeyreklik alanla aynı değeri taşır, bu testler YoY/QoQ/TTM formüllerinin
KENDİSİNİ değil mercek-seviyesi ağırlıklandırma/birleştirmeyi doğrular.
"""

from __future__ import annotations

from decimal import Decimal

from src.analysis import calculator
from src.analysis.fundamental_screens import AcquirersMultipleResult, FundamentalScreens, GrahamResult, GreenblattResult
from src.analysis.lens_deger import DegerGirdisi, hesapla_deger_mercegi
from src.analysis.lens_common import SektorIstatistigi

_LATEST = (2026, 3)
_QOQ_PRIOR = (2025, 12)
_YOY_PRIOR = (2025, 3)


def _sample_financials() -> dict:
    return {
        _LATEST: {
            "revenue": Decimal("120"), "revenue_cum": Decimal("120"),
            "gross_profit": Decimal("50"), "gross_profit_cum": Decimal("50"),
            "operating_profit": Decimal("20"), "operating_profit_cum": Decimal("20"),
            "operating_profit_ebitda_base": Decimal("20"), "operating_profit_ebitda_base_cum": Decimal("20"),
            "depreciation_amortization": Decimal("10"), "depreciation_amortization_cum": Decimal("10"),
            "net_income": Decimal("15"), "net_income_cum": Decimal("15"),
            "cash": Decimal("200"), "trade_receivables": Decimal("80"),
            "total_assets": Decimal("1000"), "financial_debt": Decimal("300"),
            "equity": Decimal("400"), "current_assets": Decimal("500"),
            "short_term_liabilities": Decimal("250"), "long_term_liabilities": Decimal("150"),
            "share_capital": Decimal("100"),
        },
        _QOQ_PRIOR: {
            "revenue": Decimal("140"), "revenue_cum": Decimal("140"),
            "gross_profit": Decimal("55"), "gross_profit_cum": Decimal("55"),
            "operating_profit": Decimal("25"), "operating_profit_cum": Decimal("25"),
            "operating_profit_ebitda_base": Decimal("25"), "operating_profit_ebitda_base_cum": Decimal("25"),
            "depreciation_amortization": Decimal("11"), "depreciation_amortization_cum": Decimal("11"),
            "net_income": Decimal("18"), "net_income_cum": Decimal("18"),
            "cash": Decimal("180"), "total_assets": Decimal("950"),
            "financial_debt": Decimal("310"), "equity": Decimal("380"),
        },
        _YOY_PRIOR: {
            "revenue": Decimal("100"), "revenue_cum": Decimal("100"),
            "gross_profit": Decimal("38"), "gross_profit_cum": Decimal("38"),
            "operating_profit": Decimal("12"), "operating_profit_cum": Decimal("12"),
            "operating_profit_ebitda_base": Decimal("12"), "operating_profit_ebitda_base_cum": Decimal("12"),
            "depreciation_amortization": Decimal("8"), "depreciation_amortization_cum": Decimal("8"),
            "net_income": Decimal("10"), "net_income_cum": Decimal("10"),
            "cash": Decimal("150"), "total_assets": Decimal("800"),
            "financial_debt": Decimal("290"), "equity": Decimal("200"),
        },
    }


def _analysis():
    return calculator.analyze("TEST", _sample_financials())


def _valuation(pe=Decimal("6"), pb=Decimal("1.5")):
    analysis = _analysis()
    price = pe * (analysis.ratios.ttm_net_income / Decimal("100")) if pe else Decimal("10")
    return calculator.compute_valuation(analysis, price=price, share_capital=Decimal("100"))


# --- hesapla_deger_mercegi: temel akış -----------------------------------------------------


def test_deger_mercegi_valuation_yoksa_mutlak_ucuzluk_atlanir_ama_diger_bilesenler_calisir() -> None:
    analysis = _analysis()
    girdi = DegerGirdisi(analysis=analysis, valuation=None)
    sonuc = hesapla_deger_mercegi(girdi)
    isimler = {c.name: c for c in sonuc.components}
    assert isimler["Mutlak Ucuzluk (F/K + PD/DD)"].score is None
    # NCAV bonusu fiyattan BAGIMSIZ calismaz (market_cap gerekir) -- valuation
    # None oldugunda o da atlanmis olmali.
    assert isimler["NCAV / Net-Net Bonus"].score is None
    assert sonuc.total_score == Decimal("0")  # hicbir bilesen veri uretmedi


def test_deger_mercegi_ucuz_carpanlarla_yuksek_skor_uretir() -> None:
    analysis = _analysis()
    valuation = calculator.compute_valuation(analysis, price=Decimal("3"), share_capital=Decimal("100"))
    girdi = DegerGirdisi(analysis=analysis, valuation=valuation, risk_free_rate_pct=Decimal("32"))
    sonuc = hesapla_deger_mercegi(girdi)
    assert sonuc.total_score > Decimal("5")
    assert sonuc.data_sufficient


def test_deger_mercegi_fundamental_yoksa_greenblatt_carlisle_graham_atlanir() -> None:
    analysis = _analysis()
    valuation = calculator.compute_valuation(analysis, price=Decimal("3"), share_capital=Decimal("100"))
    girdi = DegerGirdisi(analysis=analysis, valuation=valuation, fundamental=None)
    sonuc = hesapla_deger_mercegi(girdi)
    isimler = {c.name: c for c in sonuc.components}
    assert isimler["Graham Çarpanı (F/K×PD/DD)"].score is None
    assert isimler["Greenblatt Kazanç Getirisi (EBIT/FD)"].score is None
    assert isimler["Carlisle Acquirer's Multiple (FD/EBIT)"].score is None
    assert "sadece BİST XI_29 sanayi" in isimler["Greenblatt Kazanç Getirisi (EBIT/FD)"].reasoning_tr


def test_deger_mercegi_fundamental_ile_graham_greenblatt_carlisle_calisir() -> None:
    analysis = _analysis()
    valuation = calculator.compute_valuation(analysis, price=Decimal("3"), share_capital=Decimal("100"))
    fundamental = FundamentalScreens(
        has_data=True,
        graham=GrahamResult(graham_multiple=Decimal("10"), fair_value_price=None, upside_pct=None, verdict="Ucuz"),
        greenblatt=GreenblattResult(
            ebit=Decimal("20"), enterprise_value=Decimal("100"), earnings_yield_pct=Decimal("20"),
            earnings_yield_band="Yüksek", net_working_capital=Decimal("250"), net_fixed_assets=Decimal("300"),
            return_on_capital_pct=Decimal("30"), return_on_capital_band="Yüksek",
        ),
        acquirers_multiple=AcquirersMultipleResult(acquirers_multiple=Decimal("5"), band="Ucuz"),
        piotroski=None,
    )
    girdi = DegerGirdisi(analysis=analysis, valuation=valuation, fundamental=fundamental)
    sonuc = hesapla_deger_mercegi(girdi)
    isimler = {c.name: c for c in sonuc.components}
    # graham_multiple=10 <= 22.5 esigi -> _lerp_score(10, 0, 22.5, 10, 6) = 10 - (10/22.5)*4 = 8,2(2)
    assert isimler["Graham Çarpanı (F/K×PD/DD)"].score == Decimal(10) - (Decimal(10) / Decimal("22.5")) * Decimal(4)
    assert isimler["Greenblatt Kazanç Getirisi (EBIT/FD)"].score is not None
    assert isimler["Carlisle Acquirer's Multiple (FD/EBIT)"].score is not None


# --- _skor_sektore_goreli (n>=5 kurali, robust z-skoru) -----------------------------------------------------


def test_sektore_goreli_n_yetersizse_atlanir() -> None:
    from src.analysis.lens_deger import _skor_sektore_goreli

    sektor_pe = SektorIstatistigi(n=3, medyan=Decimal("10"), mad=Decimal("2"))
    skor, gerekce = _skor_sektore_goreli(Decimal("8"), None, sektor_pe, None)
    assert skor is None
    assert "yetersiz örneklem" in gerekce
    assert "n≥5" in gerekce


def test_sektore_goreli_n_yeterliyse_ucuz_pozitif_z_yuksek_skor() -> None:
    from src.analysis.lens_deger import _skor_sektore_goreli

    sektor_pe = SektorIstatistigi(n=8, medyan=Decimal("15"), mad=Decimal("2"))
    # own_pe sektor medyanindan COK DUSUK (ucuz) -> negatif z -> yuksek skor.
    skor, gerekce = _skor_sektore_goreli(Decimal("9"), None, sektor_pe, None)
    assert skor is not None
    assert skor > Decimal("6")
    assert "z=" in gerekce


# --- _skor_ncav_bonus (K2 duzeltmesi: net_isletme_sermayesi<=0 -> None, ceza yok) -----------------------------------------------------


def test_ncav_bonus_negatif_net_isletme_sermayesinde_none_ceza_yok() -> None:
    from src.analysis.lens_deger import _skor_ncav_bonus

    financials = _sample_financials()
    financials[_LATEST]["current_assets"] = Decimal("100")  # kucuk donen varlik -> negatif NIS
    analysis = calculator.analyze("TEST", financials)
    valuation = calculator.compute_valuation(analysis, price=Decimal("3"), share_capital=Decimal("100"))
    skor, gerekce = _skor_ncav_bonus(analysis, valuation)
    assert skor is None
    assert "ceza" in gerekce


def test_ncav_bonus_piyasa_degeri_ncav_altindaysa_yuksek_skor() -> None:
    from src.analysis.lens_deger import _skor_ncav_bonus

    analysis = _analysis()  # current_assets=500, total_liabilities=1000-400=600 -> NIS=-100 (negatif ornek DEGIL burada dikkat)
    # NIS pozitif olsun diye current_assets'i yukselten ayri bir fixture kur:
    financials = _sample_financials()
    financials[_LATEST]["current_assets"] = Decimal("900")  # NIS = 900-600=300
    analysis2 = calculator.analyze("TEST", financials)
    valuation = calculator.compute_valuation(analysis2, price=Decimal("1"), share_capital=Decimal("100"))  # market_cap=100 < 300
    skor, gerekce = _skor_ncav_bonus(analysis2, valuation)
    assert skor is not None
    assert skor > Decimal("7")
    assert "ALTINDA" in gerekce
