"""Faz 14 teslim kriteri: X/Twitter teaser kartı (16:9) context oluşturma
testleri + gerçek bir PNG üreten tek uçtan uca entegrasyon testi.

Fixture'lar test_card.py'dekiyle AYNI ilkeyi (calculator.analyze() ailesini
GERÇEKTEN çağırıp doğrulanmış türetme mantığını kullan, elle sahte
AnalysisResult kurma) izler ama test dosyaları arası import YAPILMAZ
(her modül tek başına test edilebilir olmalı, Kural 11) -- bu yüzden
minimal fixture'lar burada KENDİ başına tanımlanır.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.ai.commentary import Commentary
from src.analysis import calculator, scorer
from src.render import card

_LATEST = (2026, 3)
_YOY_PRIOR = (2025, 3)
_QOQ_PRIOR = (2025, 12)


def _donem(revenue, gross, op, dep, net, cash, tr, assets, debt, equity, ca, stl) -> dict:
    d = {
        "revenue": Decimal(revenue), "revenue_cum": Decimal(revenue),
        "gross_profit": Decimal(gross), "gross_profit_cum": Decimal(gross),
        "operating_profit": Decimal(op), "operating_profit_cum": Decimal(op),
        "operating_profit_ebitda_base": Decimal(op), "operating_profit_ebitda_base_cum": Decimal(op),
        "net_income": Decimal(net), "net_income_cum": Decimal(net), "cash": Decimal(cash),
        "trade_receivables": Decimal(tr),
        "total_assets": Decimal(assets), "financial_debt": Decimal(debt), "equity": Decimal(equity),
        "current_assets": Decimal(ca), "short_term_liabilities": Decimal(stl),
    }
    if dep is not None:
        d["depreciation_amortization"] = Decimal(dep)
        d["depreciation_amortization_cum"] = Decimal(dep)
    return d


def _saglikli_finansallar() -> calculator.FinancialsByPeriod:
    return {
        _LATEST: _donem(1200, 500, 350, 60, 260, 400, 150, 5000, 600, 3000, 1800, 900),
        _QOQ_PRIOR: _donem(1100, 460, 320, 58, 230, 380, 140, 4800, 620, 2850, 1700, 880),
        _YOY_PRIOR: _donem(1000, 400, 260, 55, -80, 300, 130, 4500, 700, 2600, 1600, 850),
    }


def _ornek_commentary(headline: str = "TESTAS satışlarını artırırken kârlılıkta baskı yaşadı") -> Commentary:
    return Commentary(
        headline=headline, hook="Kanca cümlesi.", summary="Özet.", positives=["artış maddesi"], negatives=["azalış maddesi"],
        kap_note="KAP notu.", disclaimer_context=None, source="llm",
    )


# --- _truncate_headline --------------------------------------------


def test_truncate_headline_kisa_metin_degismez():
    assert card._truncate_headline("Kısa bir başlık.") == "Kısa bir başlık."


def test_truncate_headline_uzun_metin_kelime_sinirinda_kesilir():
    uzun = "Bu " + "çok " * 30 + "uzun bir başlık"
    sonuc = card._truncate_headline(uzun, max_chars=40)
    assert len(sonuc) <= 41  # "…" dahil
    assert sonuc.endswith("…")
    assert not sonuc[:-1].endswith(" ")  # kelime sinirinda kesildi, yarim kelime/bosluk kalmadi


# --- _teaser_metric --------------------------------------------


def test_teaser_metric_none_item_na_doner():
    m = card._teaser_metric(None, "SATIŞLAR")
    assert m == {"label": "SATIŞLAR", "display": "N/A", "color_class": "neutral"}


def test_teaser_metric_pozitif_yuzde_yesil():
    item = calculator.LineItemChange(
        label_tr="Hasılat", current=Decimal("1200"), comparison=Decimal("1000"),
        percent_change=Decimal("20"), change_label=calculator.ChangeLabel.ARTIS,
    )
    m = card._teaser_metric(item, "SATIŞLAR")
    assert m["display"] == "%20,0"
    assert m["color_class"] == "positive"


def test_teaser_metric_negatif_yuzde_kirmizi():
    item = calculator.LineItemChange(
        label_tr="FAVÖK", current=Decimal("80"), comparison=Decimal("100"),
        percent_change=Decimal("-20"), change_label=calculator.ChangeLabel.AZALIS,
    )
    m = card._teaser_metric(item, "FAVÖK")
    assert m["display"] == "%-20,0"
    assert m["color_class"] == "negative"


def test_teaser_metric_gecis_etiketi_yuzdesiz_gosterir():
    item = calculator.LineItemChange(
        label_tr="Net Dönem Kârı", current=Decimal("260"), comparison=Decimal("-80"),
        percent_change=None, change_label=calculator.ChangeLabel.ZARARDAN_KARA_GECTI,
    )
    m = card._teaser_metric(item, "NET KÂR")
    assert m["display"] == calculator.ChangeLabel.ZARARDAN_KARA_GECTI
    assert m["color_class"] == "positive"


# --- build_teaser_context (sanayi + US_GAAP paylasimli) --------------------------------------------


def test_build_teaser_context_temel_alanlar():
    analiz = calculator.analyze("TESTAS", _saglikli_finansallar())
    skor = scorer.score_industrial(analiz)
    context = card.build_teaser_context(analiz, skor, _ornek_commentary(), company_name="Test A.Ş.", price=Decimal("142.5"))

    assert context["ticker"] == "TESTAS"
    assert context["company_name"] == "Test A.Ş."
    assert context["period_label"] == "1Ç26"
    assert context["price_display"] == "142,50 ₺"
    assert len(context["metrics"]) == 3
    assert {m["label"] for m in context["metrics"]} == {"SATIŞLAR", "FAVÖK", "NET KÂR"}
    assert context["headline"] == _ornek_commentary().headline
    assert "yatırım tavsiyesi değildir" in context["disclaimer"]


def test_build_teaser_context_fiyatsiz_none_gosterir():
    analiz = calculator.analyze("TESTAS", _saglikli_finansallar())
    skor = scorer.score_industrial(analiz)
    context = card.build_teaser_context(analiz, skor, _ornek_commentary())

    assert context["price_display"] is None


def test_build_teaser_context_nasdaq_mali_yil_etiketi_kullanir():
    # market="NASDAQ" -- CANLI kod yolu _fiscal_quarter_label() kullanmali
    # (build_us_card_context ile AYNI ilke), "1Ç26" DEGIL "FY26 Ç1" gibi
    # bir bicim beklenir (analysis.is_annual_only False oldugu icin).
    analiz = calculator.analyze("TESTUS", _saglikli_finansallar())
    skor = scorer.score_industrial(analiz)
    context = card.build_teaser_context(
        analiz, skor, _ornek_commentary(), market="NASDAQ", currency_symbol="$", price=Decimal("100")
    )

    assert context["period_label"] == card._fiscal_quarter_label(_LATEST, annual_only=False)
    assert context["price_display"] == "$100,00"


def test_build_teaser_context_veri_yetersizse_skor_gosterilmez():
    # score.data_sufficient=False durumunda (§B17 ile AYNI ilke) numerik
    # skor DEGIL rozet gosterilmeli -- context bunu _score_display_context
    # ile ZATEN saglar, burada SADECE teaser'in bu alani DOGRU ILETTIGI
    # dogrulanir.
    analiz = calculator.analyze("TESTAS", _saglikli_finansallar())
    skor = scorer.score_industrial(analiz)
    context = card.build_teaser_context(analiz, skor, _ornek_commentary())
    assert "score_data_sufficient" in context
    assert "score_badge_class" in context


# --- render_html (Playwright'siz, sadece Jinja2) --------------------------------------------


def test_render_html_teaser_yedi_sayi_kuralina_uyar():
    """Roadmap kurali: kartta EN FAZLA 7 SAYI. Metrics(3) + skor(1) +
    fiyat(1) = 5 -- kurala uyar (dönem etiketi 'sayı' sayılmaz, tarih/
    rozet metnidir)."""
    analiz = calculator.analyze("TESTAS", _saglikli_finansallar())
    skor = scorer.score_industrial(analiz)
    context = card.build_teaser_context(analiz, skor, _ornek_commentary(), price=Decimal("142.5"))
    assert len(context["metrics"]) == 3  # + skor + fiyat = 5 numerik alan, 7 siniri asilmiyor


def test_render_html_teaser_none_sizdirmaz():
    analiz = calculator.analyze("TESTAS", _saglikli_finansallar())
    skor = scorer.score_industrial(analiz)
    context = card.build_teaser_context(analiz, skor, _ornek_commentary())
    html = card.render_html(context, "teaser_card.html")
    assert "None" not in html
    assert "TESTAS" in html


# --- render_card: gercek Playwright ile PNG uretimi (uctan uca) --------------------------------------------


def test_render_card_teaser_gercek_png_uretir(tmp_path) -> None:
    analiz = calculator.analyze("TESTAS", _saglikli_finansallar())
    skor = scorer.score_industrial(analiz)
    context = card.build_teaser_context(analiz, skor, _ornek_commentary(), company_name="Test A.Ş.", price=Decimal("142.5"))

    out_path = tmp_path / "test_teaser.png"
    result = card.render_card(context, str(out_path), "teaser_card.html", "#teaser-card")

    assert result == str(out_path)
    assert out_path.exists()
    assert out_path.stat().st_size > 1000
    assert out_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
