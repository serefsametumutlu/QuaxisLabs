"""Faz 10 teslim kriteri: card.build_us_card_context() testleri.

build_us_card_context(), build_card_context()'in ozel yardimcilarini
(_line_item_row/_build_chart/_valuation_context/_score_row) `currency_symbol="$"`
ile CAGIRIR (bkz. card.py modul ici not) -- satir/renk/grafik MANTIGININ
kendisi zaten test_card.py'de (58 test) dogrulandi, burada TEKRAR edilmez.
Bu dosya SADECE US_GAAP'e OZGU farkllari test eder: para birimi sembolu,
mali donem etiketi ("FYyy Çn"), sector_template="abd", kaynak notu, VE
gercek bir PNG ureten uctan uca entegrasyon testi.
"""

from __future__ import annotations

from decimal import Decimal

from src.ai.commentary import Commentary
from src.analysis import calculator, scorer
from src.render import card

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
        "shares_outstanding": Decimal("14594180000"),
    }


def _saglikli_us_finansallar() -> calculator.FinancialsByPeriod:
    return {
        _LATEST: _donem(1200, 500, 350, 60, 260, 400, 150, 5000, 600, 3000, 1800, 900),
        _QOQ_PRIOR: _donem(1100, 460, 320, 58, 230, 380, 140, 4800, 620, 2850, 1700, 880),
        _YOY_PRIOR: _donem(1000, 400, 260, 55, 180, 300, 130, 4500, 700, 2600, 1600, 850),
        _TTM_3: _donem(1050, 430, 280, 56, 200, 320, 135, 4600, 680, 2700, 1650, 860),
        _TTM_4: _donem(980, 390, 250, 54, 175, 290, 125, 4400, 690, 2550, 1580, 840),
    }


def _ornek_commentary() -> Commentary:
    return Commentary(
        headline="BAŞLIK", summary="Özet.", positives=["artış maddesi"], negatives=["azalış maddesi"],
        kap_note=None, disclaimer_context=None, source="llm",
    )


# --- _fiscal_quarter_label -----------------------------------------------------


def test_fiscal_quarter_label_takvim_etiketinden_farklidir() -> None:
    # NVDA gibi takvim disi mali yili olan sirketlerde "1Ç27" (takvim
    # ceyregi izlenimi verir, YANLIS) yerine "FY27 Ç1" (acikca mali yil).
    assert card._fiscal_quarter_label((2027, 3)) == "FY27 Ç1"
    assert card._fiscal_quarter_label((2027, 3)) != card._quarter_label((2027, 3))


# --- build_us_card_context -----------------------------------------------------


def test_build_us_card_context_sector_template_abd() -> None:
    analiz = calculator.analyze_us("AAPL", _saglikli_us_finansallar())
    skor = scorer.score_industrial_us(analiz)
    context = card.build_us_card_context(analiz, skor, _ornek_commentary())
    assert context["sector_template"] == "abd"


def test_build_us_card_context_para_birimi_dolar() -> None:
    analiz = calculator.analyze_us("AAPL", _saglikli_us_finansallar())
    skor = scorer.score_industrial_us(analiz)
    context = card.build_us_card_context(analiz, skor, _ornek_commentary(), price=Decimal("308.91"))

    assert context["price_display"] == "$308,91"
    assert "$" in context["income_rows"]["revenue"]["current"]
    assert "₺" not in context["income_rows"]["revenue"]["current"]


def test_build_us_card_context_valuation_dolar_formatli() -> None:
    analiz = calculator.analyze_us("AAPL", _saglikli_us_finansallar())
    skor = scorer.score_industrial_us(analiz)
    valuation = calculator.compute_valuation(analiz, Decimal("308.91"), Decimal("14594180000"))
    context = card.build_us_card_context(analiz, skor, _ornek_commentary(), price=Decimal("308.91"), valuation=valuation)

    assert "$" in context["valuation"]["piyasa_degeri"]
    assert "₺" not in context["valuation"]["piyasa_degeri"]


def test_build_us_card_context_donem_etiketi_mali_yil_formatinda() -> None:
    analiz = calculator.analyze_us("AAPL", _saglikli_us_finansallar())
    skor = scorer.score_industrial_us(analiz)
    context = card.build_us_card_context(analiz, skor, _ornek_commentary())

    assert context["period_label"] == "FY26 Ç3"
    assert context["table_periods"]["current"] == "FY26 Ç3"


def test_build_us_card_context_kaynak_notu_sec_edgar() -> None:
    analiz = calculator.analyze_us("AAPL", _saglikli_us_finansallar())
    skor = scorer.score_industrial_us(analiz)
    context = card.build_us_card_context(analiz, skor, _ornek_commentary())
    assert context["data_sources_note"] == "SEC EDGAR (XBRL)"


def test_build_us_card_context_disclosure_rows_her_zaman_bos() -> None:
    # Gorev talimati: KAP/8-K bu fazin kapsami disinda.
    analiz = calculator.analyze_us("AAPL", _saglikli_us_finansallar())
    skor = scorer.score_industrial_us(analiz)
    context = card.build_us_card_context(analiz, skor, _ornek_commentary())
    assert context["disclosure_rows"] == []
    assert context["kap_note"] is None


def test_build_us_card_context_show_ebitda_true() -> None:
    analiz = calculator.analyze_us("AAPL", _saglikli_us_finansallar())
    skor = scorer.score_industrial_us(analiz)
    context = card.build_us_card_context(analiz, skor, _ornek_commentary())
    assert context["show_ebitda"] is True
    assert context["charts"]["ebitda"] is not None
    assert "$" in context["charts"]["ebitda"]["current_value_display"]


# --- FAVOK (TTM) yedegi -- §B20, AMD/TSLA gibi tek ceyreklik D&A turetilemeyen sirketler -----------------------------------------------------


def _amd_tipi_eksik_da_ile() -> calculator.FinancialsByPeriod:
    """_saglikli_us_finansallar() ile AYNI ama guncel donemde
    depreciation_amortization(_cum) KASITLI olarak EKSIK -- AMD'nin
    Depreciation'inin ceyreklik/YTD kirilimi olmamasiyla AYNI durumu
    taklit eder (income_statement.ebitda None kalir, ttm_operating_profit
    ise SORUNSUZ hesaplanir)."""
    financials = _saglikli_us_finansallar()
    del financials[_LATEST]["depreciation_amortization"]
    del financials[_LATEST]["depreciation_amortization_cum"]
    return financials


def test_build_us_card_context_ebitda_yoksa_ama_ttm_varsa_ttm_etiketli_satir_gosterir() -> None:
    override = Decimal("500")
    analiz = calculator.analyze_us("AMD", _amd_tipi_eksik_da_ile(), ttm_depreciation_amortization_override=override)
    assert analiz.income_statement.ebitda is None  # on kosul: standart ceyreklik FAVOK gercekten None
    assert analiz.ratios.ttm_ebitda is not None  # on kosul: override sayesinde TTM calisti

    skor = scorer.score_industrial_us(analiz)
    context = card.build_us_card_context(analiz, skor, _ornek_commentary())

    ebitda_row = context["income_rows"]["ebitda"]
    assert "TTM" in ebitda_row["label"]
    assert ebitda_row["current"] != "N/A"
    assert "$" in ebitda_row["current"]
    assert ebitda_row["comparison"] == "—"
    # Mini grafik (ceyreklik trend) HALA gizli kalmali -- TTM tek nokta,
    # ceyreklik bar grafigiyle KARISTIRILMAMALI.
    assert context["show_ebitda"] is False
    assert context["charts"]["ebitda"] is None


def test_build_us_card_context_ebitda_de_ttm_de_yoksa_veri_yok_gosterir() -> None:
    """Regresyon kilidi: override VERILMEZSE eski davranis (§B17) korunur --
    FAVOK satiri HER ZAMAN gorunur ama "veri yok" der, kart cokmez."""
    analiz = calculator.analyze_us("AMD", _amd_tipi_eksik_da_ile())
    assert analiz.income_statement.ebitda is None
    assert analiz.ratios.ttm_ebitda is None

    skor = scorer.score_industrial_us(analiz)
    context = card.build_us_card_context(analiz, skor, _ornek_commentary())

    ebitda_row = context["income_rows"]["ebitda"]
    assert ebitda_row["current"] == "—"
    assert ebitda_row["change_display"] == "veri yok"


# --- render_card: gercek Playwright ile PNG uretimi (uctan uca) -----------------------------------------------------


def test_render_card_us_gercek_png_uretir(tmp_path) -> None:
    analiz = calculator.analyze_us("AAPL", _saglikli_us_finansallar())
    valuation = calculator.compute_valuation(analiz, Decimal("308.91"), Decimal("14594180000"))
    valuation_input = scorer.ValuationInput(pe_ratio=valuation.pe_ratio, pb_ratio=valuation.pb_ratio)
    skor = scorer.score_industrial_us(analiz, valuation=valuation_input)
    context = card.build_us_card_context(analiz, skor, _ornek_commentary(), price=Decimal("308.91"), valuation=valuation)

    out_path = tmp_path / "test_card_us.png"
    result = card.render_card(context, str(out_path))

    assert result == str(out_path)
    assert out_path.exists()
    assert out_path.stat().st_size > 1000
    assert out_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
