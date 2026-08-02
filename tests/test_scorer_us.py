"""Faz 10 teslim kriteri: scorer.score_industrial_us() testleri.

score_industrial_us(), score_industrial(..., template="abd_sanayi") icin
ince bir sarmalayicidir (bkz. scorer.py modul ici not) -- bilesen
YAPISI/agirlik dagitim mekanigi zaten test_scorer.py'de (44 test)
dogrulandi, burada TEKRAR edilmez. Bu dosya SADECE:
  1. CONFIG['abd_sanayi'] agirlik toplaminin %100 oldugunu,
  2. score_industrial_us()'in dogru sablonu ("sanayi_holding_abd") VE
     dogru esik SETINI (CONFIG['abd_sanayi'], CONFIG['sanayi'] DEGIL)
     kullandigini dogrular.
"""

from __future__ import annotations

from decimal import Decimal

from src.analysis import calculator, scorer

_LATEST = (2026, 9)
_YOY_PRIOR = (2025, 9)
_QOQ_PRIOR = (2026, 6)
_TTM_3 = (2026, 3)
_TTM_4 = (2025, 12)


def _donem(revenue, gross, op, dep, net, cash, tr, assets, debt, equity, ca, stl) -> dict:
    return {
        "revenue": Decimal(revenue),
        "revenue_cum": Decimal(revenue),
        "gross_profit": Decimal(gross),
        "gross_profit_cum": Decimal(gross),
        "operating_profit": Decimal(op),
        "operating_profit_cum": Decimal(op),
        "operating_profit_ebitda_base": Decimal(op),
        "operating_profit_ebitda_base_cum": Decimal(op),
        "depreciation_amortization": Decimal(dep),
        "depreciation_amortization_cum": Decimal(dep),
        "net_income": Decimal(net),
        "net_income_cum": Decimal(net),
        "cash": Decimal(cash),
        "trade_receivables": Decimal(tr),
        "total_assets": Decimal(assets),
        "financial_debt": Decimal(debt),
        "equity": Decimal(equity),
        "current_assets": Decimal(ca),
        "short_term_liabilities": Decimal(stl),
    }


def test_config_abd_sanayi_agirlik_toplami_100() -> None:
    toplam = sum(v["agirlik"] for v in scorer.CONFIG["abd_sanayi"].values())
    assert toplam == Decimal("100")


def test_score_industrial_us_sablon_ve_bilesen_sayisi() -> None:
    financials = {
        _LATEST: _donem(1200, 500, 350, 60, 260, 400, 150, 5000, 600, 3000, 1800, 900),
        _QOQ_PRIOR: _donem(1100, 460, 320, 58, 230, 380, 140, 4800, 620, 2850, 1700, 880),
        _YOY_PRIOR: _donem(1000, 400, 260, 55, 180, 300, 130, 4500, 700, 2600, 1600, 850),
        _TTM_3: _donem(1050, 430, 280, 56, 200, 320, 135, 4600, 680, 2700, 1650, 860),
        _TTM_4: _donem(980, 390, 250, 54, 175, 290, 125, 4400, 690, 2550, 1580, 840),
    }
    analysis = calculator.analyze_us("AAPL", financials)

    sonuc = scorer.score_industrial_us(analysis)
    assert sonuc.template == "sanayi_holding_abd"
    assert len(sonuc.components) == 7
    assert Decimal("0") <= sonuc.total_score <= Decimal("10")


def test_score_industrial_us_degerleme_esikleri_sanayiden_farkli_uygulanir() -> None:
    """CANLI KANIT: BIST 'sanayi' sablonunda F/K 15 'makul' ust sinirinin
    (fk_makul) TAM UZERINDEDIR (dusuk puan bolgesi), ama 'abd_sanayi'
    sablonunda F/K 15 HALA 'ucuz' bolgesinde (fk_ucuz=12 < 15 < fk_makul=20)
    -- bu yuzden AYNI F/K degeri IKI sablonda FARKLI (ve abd_sanayi'de
    DAHA YUKSEK) bir Degerleme puani uretmelidir."""
    financials = {
        _LATEST: _donem(1200, 500, 350, 60, 260, 400, 150, 5000, 600, 3000, 1800, 900),
        _QOQ_PRIOR: _donem(1100, 460, 320, 58, 230, 380, 140, 4800, 620, 2850, 1700, 880),
        _YOY_PRIOR: _donem(1000, 400, 260, 55, 180, 300, 130, 4500, 700, 2600, 1600, 850),
        _TTM_3: _donem(1050, 430, 280, 56, 200, 320, 135, 4600, 680, 2700, 1650, 860),
        _TTM_4: _donem(980, 390, 250, 54, 175, 290, 125, 4400, 690, 2550, 1580, 840),
    }
    analysis_bist = calculator.analyze("TESTAS", financials)
    analysis_us = calculator.analyze_us("TESTUS", financials)
    valuation = scorer.ValuationInput(pe_ratio=Decimal("15"))

    skor_bist = scorer.score_industrial(analysis_bist, valuation=valuation)
    skor_us = scorer.score_industrial_us(analysis_us, valuation=valuation)

    degerleme_bist = next(c for c in skor_bist.components if c.name == "Değerleme")
    degerleme_us = next(c for c in skor_us.components if c.name == "Değerleme")
    assert degerleme_us.score > degerleme_bist.score


def test_score_industrial_us_buyume_esigi_sanayiden_dusuk() -> None:
    """CANLI KANIT: %12 hasilat buyumesi BIST 'sanayi' sablonunda (guclu
    esik %15) HENUZ 'guclu' degil (orta bolgede), ama 'abd_sanayi'
    sablonunda (guclu esik %10) ZATEN 'guclu' bolgesindedir -- bu yuzden
    AYNI buyume orani abd_sanayi'de DAHA YUKSEK puanlanmalidir."""
    assert scorer.CONFIG["sanayi"]["buyume"]["guclu_esik"] == Decimal("15")
    assert scorer.CONFIG["abd_sanayi"]["buyume"]["guclu_esik"] == Decimal("10")

    financials = {
        _LATEST: _donem(1120, 500, 350, 60, 260, 400, 150, 5000, 600, 3000, 1800, 900),  # %12 YoY
        _QOQ_PRIOR: _donem(1050, 460, 320, 58, 230, 380, 140, 4800, 620, 2850, 1700, 880),
        _YOY_PRIOR: _donem(1000, 400, 260, 55, 180, 300, 130, 4500, 700, 2600, 1600, 850),
        _TTM_3: _donem(1030, 430, 280, 56, 200, 320, 135, 4600, 680, 2700, 1650, 860),
        _TTM_4: _donem(980, 390, 250, 54, 175, 290, 125, 4400, 690, 2550, 1580, 840),
    }
    analysis_bist = calculator.analyze("TESTAS", financials)
    analysis_us = calculator.analyze_us("TESTUS", financials)

    skor_bist = scorer.score_industrial(analysis_bist)
    skor_us = scorer.score_industrial_us(analysis_us)

    buyume_bist = next(c for c in skor_bist.components if c.name == "Büyüme")
    buyume_us = next(c for c in skor_us.components if c.name == "Büyüme")
    assert buyume_us.score > buyume_bist.score


def test_score_industrial_us_kaldirac_esikleri_sanayiyle_ayni() -> None:
    # Gorev talimati: kredi derecelendirme pratigine dayandigi icin AYNI kalmali.
    assert scorer.CONFIG["abd_sanayi"]["kaldirac"] == scorer.CONFIG["sanayi"]["kaldirac"]
