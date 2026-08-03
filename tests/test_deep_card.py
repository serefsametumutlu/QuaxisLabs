"""src/render/deep_card.py testleri (Derin Kart -- çok dönemli temel analiz).

build_deep_card_context() saf bir fonksiyondur -- src.analysis.trends'e
hiçbir AĞ isteği atmaz, elle kurulmuş bir MultiPeriodTrend/score_history
kullanılır (Kural 11). SADECE test_render_deep_card_* GERÇEK Playwright
render'i doğrular (card.py/technical_card.py'deki AYNI desen).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from src.analysis.trends import MultiPeriodTrend, PeriodTrendPoint, SeasonalityGroup
from src.render import card, deep_card


def _point(period, revenue=Decimal("120"), ebitda=Decimal("30"), net_income=Decimal("15"),
           equity=Decimal("400"), gross_margin_pct=Decimal("40"), ebitda_margin_pct=Decimal("25"),
           net_margin_pct=Decimal("12"), net_debt_to_ebitda=Decimal("2"), roe_pct=Decimal("9")) -> PeriodTrendPoint:
    return PeriodTrendPoint(
        period=period,
        revenue=revenue,
        ebitda=ebitda,
        net_income=net_income,
        equity=equity,
        gross_margin_pct=gross_margin_pct,
        ebitda_margin_pct=ebitda_margin_pct,
        net_margin_pct=net_margin_pct,
        net_debt_to_ebitda=net_debt_to_ebitda,
        roe_pct=roe_pct,
    )


def _trend(points=None, seasonality=()) -> MultiPeriodTrend:
    if points is None:
        points = (_point((2025, 12), revenue=Decimal("100")), _point((2026, 3), revenue=Decimal("120")))
    return MultiPeriodTrend(points=tuple(points), seasonality=tuple(seasonality))


# --- build_deep_card_context ------------------------------------------------------


def test_build_deep_card_context_veri_yoksa_has_data_false():
    context = deep_card.build_deep_card_context(None, [], "ASTS", "NASDAQ")

    assert context["has_data"] is False
    assert context["ticker"] == "ASTS"
    assert context["market_label"] == "NASDAQ"
    assert "disclaimer" in context


def test_build_deep_card_context_bos_puan_listesinde_has_data_false():
    context = deep_card.build_deep_card_context(MultiPeriodTrend(points=(), seasonality=()), [], "ASTS", "NASDAQ")
    assert context["has_data"] is False


def test_build_deep_card_context_veriyle_tum_bolumleri_doldurur():
    context = deep_card.build_deep_card_context(_trend(), [], "THYAO", "BIST", company_name="Türk Hava Yolları A.O.")

    assert context["has_data"] is True
    assert context["ticker"] == "THYAO"
    assert context["company_name"] == "Türk Hava Yolları A.O."
    assert context["period_count"] == 2
    assert context["period_range_display"] == "4Ç25 — 1Ç26"
    assert len(context["overview_charts"]) == 4
    assert {c["title"] for c in context["overview_charts"]} == {"Hasılat", "FAVÖK", "Net Kâr", "Özkaynak"}
    assert context["margin_chart"]["has_data"] is True
    assert context["leverage_chart"]["has_data"] is True
    assert context["roe_chart"]["has_data"] is True


def test_build_deep_card_context_overview_grafik_dogru_olcekleniyor():
    context = deep_card.build_deep_card_context(_trend(), [], "THYAO", "BIST")
    revenue_chart = next(c for c in context["overview_charts"] if c["title"] == "Hasılat")["chart"]

    assert revenue_chart["has_data"] is True
    assert revenue_chart["min_display"] == "100 ₺"
    assert revenue_chart["max_display"] == "120 ₺"
    assert revenue_chart["x_start_label"] == "4Ç25"
    assert revenue_chart["x_end_label"] == "1Ç26"


def test_build_deep_card_context_nasdaq_dolar_isaretiyle_gosterir():
    context = deep_card.build_deep_card_context(_trend(), [], "AAPL", "NASDAQ")
    revenue_chart = next(c for c in context["overview_charts"] if c["title"] == "Hasılat")["chart"]
    assert revenue_chart["min_display"] == "100 $"
    assert revenue_chart["max_display"] == "120 $"


def test_build_deep_card_context_tek_donemde_grafikler_yeterli_veri_yok():
    """Sadece 1 donem varsa (K4: tek nokta trend SAYILMAZ) TUM grafikler
    has_data=False olmali."""
    context = deep_card.build_deep_card_context(_trend(points=[_point((2026, 3))]), [], "THYAO", "BIST")

    assert context["has_data"] is True  # kart yine uretilir (bkz. K4)
    assert context["overview_charts"][0]["chart"]["has_data"] is False
    assert context["margin_chart"]["has_data"] is False
    assert context["leverage_chart"]["has_data"] is False
    assert context["roe_chart"]["has_data"] is False


def test_build_deep_card_context_marj_grafigi_uc_seri_icerir():
    context = deep_card.build_deep_card_context(_trend(), [], "THYAO", "BIST")
    keys = {line["key"] for line in context["margin_chart"]["lines"]}
    assert keys == {"gross", "ebitda", "net"}


def test_build_deep_card_context_kismi_eksik_veri_None_atlanir_grafik_yine_uretilir():
    """Bir donemde kaldirac/ROE None olsa bile (K4) diger donem yeterliyse
    grafik yine has_data=True olmali; polyline SADECE gercek noktalari icerir."""
    points = [
        _point((2025, 12), net_debt_to_ebitda=None, roe_pct=None),
        _point((2026, 3), net_debt_to_ebitda=Decimal("2"), roe_pct=Decimal("9")),
    ]
    context = deep_card.build_deep_card_context(_trend(points=points), [], "THYAO", "BIST")
    assert context["leverage_chart"]["has_data"] is True
    assert context["roe_chart"]["has_data"] is True


# --- Skor gecmisi -----------------------------------------------------


def test_build_deep_card_context_skor_gecmisi_yeterliyse_grafik_uretir():
    history = [(datetime(2026, 1, 1), 5.0), (datetime(2026, 4, 1), 7.5)]
    context = deep_card.build_deep_card_context(_trend(), history, "THYAO", "BIST")

    chart = context["score_history_chart"]
    assert chart["has_data"] is True
    assert chart["x_start_label"] == "01.01.26"
    assert chart["min_display"] == "5,00/10"
    assert chart["max_display"] == "7,50/10"


def test_build_deep_card_context_skor_gecmisi_tek_kayitla_yeterli_degil():
    context = deep_card.build_deep_card_context(_trend(), [(datetime(2026, 1, 1), 5.0)], "THYAO", "BIST")
    assert context["score_history_chart"]["has_data"] is False


def test_build_deep_card_context_skor_gecmisi_bossa_yeterli_degil():
    context = deep_card.build_deep_card_context(_trend(), [], "THYAO", "BIST")
    assert context["score_history_chart"]["has_data"] is False


# --- Mevsimsellik -----------------------------------------------------


def test_build_deep_card_context_mevsimsellik_gruplari_grafik_uretir():
    seasonality = (SeasonalityGroup(quarter_number=3, years=(2025, 2026), revenues=(Decimal("100"), Decimal("120"))),)
    context = deep_card.build_deep_card_context(_trend(seasonality=seasonality), [], "THYAO", "BIST")

    assert len(context["seasonality_charts"]) == 1
    item = context["seasonality_charts"][0]
    assert item["title"] == "1. Çeyrek — Yıllar Arası Hasılat"
    assert item["chart"]["has_data"] is True
    assert item["chart"]["x_start_label"] == "2025"
    assert item["chart"]["x_end_label"] == "2026"


def test_build_deep_card_context_mevsimsellik_bossa_bos_liste():
    context = deep_card.build_deep_card_context(_trend(), [], "THYAO", "BIST")
    assert context["seasonality_charts"] == []


# --- Gercek Playwright render -----------------------------------------------------


def test_render_deep_card_gercek_png_uretir(tmp_path):
    seasonality = (SeasonalityGroup(quarter_number=3, years=(2025, 2026), revenues=(Decimal("100"), Decimal("120"))),)
    history = [(datetime(2026, 1, 1), 5.0), (datetime(2026, 4, 1), 7.5)]
    context = deep_card.build_deep_card_context(
        _trend(seasonality=seasonality), history, "THYAO", "BIST", company_name="Türk Hava Yolları A.O."
    )

    out_path = tmp_path / "test_derin.png"
    result = card.render_card(context, str(out_path), template_name="deep_card.html", screenshot_selector="#deep-card")

    assert result == str(out_path)
    assert out_path.exists()
    assert out_path.stat().st_size > 1000
    assert out_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_deep_card_veri_yokken_de_cokmez(tmp_path):
    context = deep_card.build_deep_card_context(None, [], "YENIHISSE", "BIST")

    out_path = tmp_path / "test_derin_bos.png"
    card.render_card(context, str(out_path), template_name="deep_card.html", screenshot_selector="#deep-card")

    assert out_path.exists()
    assert out_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
