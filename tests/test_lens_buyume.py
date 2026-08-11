"""SPEC: `docs/spec/spec_mercek_buyume.md` testleri -- Büyüme Merceği (v2)."""

from __future__ import annotations

from decimal import Decimal

from src.analysis import calculator
from src.analysis.lens_buyume import BuyumeGirdisi, hesapla_buyume_mercegi, _skor_marjinal_roe_ve_verimlilik, _skor_peg

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
    assert isimler == {"Hasılat Büyümesi (reel, seviye+trend)", "PEG Oranı (Lynch)", "Marjinal ROE + Verimlilik Kaynaklı Büyüme"}


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
