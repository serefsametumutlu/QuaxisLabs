"""src/render/technical_card.py testleri (Faz 15 - Teknik Analiz kartı).

build_technical_context() saf bir fonksiyondur -- src.analysis.technical'e
hiçbir AĞ isteği atmaz, elle kurulmuş bir TechnicalSnapshot kullanılır
(Kural 11). SADECE test_render_technical_card_* GERÇEK Playwright render'i
doğrular (card.py/calendar_card.py'deki AYNI desen).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from src.analysis.technical import TechnicalSnapshot
from src.render import card, technical_card


def _snapshot(**overrides) -> TechnicalSnapshot:
    defaults = dict(
        as_of_date=date(2026, 8, 3),
        price=Decimal("314.0"),
        sma_20=Decimal("300.0"),
        sma_50=Decimal("290.0"),
        sma_200=Decimal("270.0"),
        ema_12=Decimal("305.0"),
        ema_26=Decimal("295.0"),
        rsi_14=Decimal("55.5"),
        macd_line=Decimal("2.3"),
        macd_signal=Decimal("1.1"),
        macd_histogram=Decimal("1.2"),
        bb_upper=Decimal("320.0"),
        bb_middle=Decimal("300.0"),
        bb_lower=Decimal("280.0"),
        atr_14=Decimal("5.5"),
        adx_14=Decimal("30.0"),
        sma_cross_state="golden",
        sma_cross_recent=False,
        week52_high=Decimal("340.0"),
        week52_low=Decimal("230.0"),
        week52_position_pct=Decimal("76.4"),
        avg_volume_20=Decimal("15000000000"),
        last_volume=Decimal("18000000000"),
        volume_ratio_pct=Decimal("120.0"),
        price_vs_sma200_pct=Decimal("16.3"),
        chart_dates=tuple(date(2026, 2, 1 + i) for i in range(5)),
        chart_closes=tuple(Decimal(str(280 + i)) for i in range(5)),
        chart_sma50=(None, None, Decimal("282"), Decimal("283"), Decimal("284")),
        chart_sma200=(None, None, None, None, None),
    )
    defaults.update(overrides)
    return TechnicalSnapshot(**defaults)


def _all_rows(context: dict) -> list[dict]:
    """indicator_groups (Trend/Momentum/Volatilite) icindeki TUM satirlari
    tek bir duz listede toplar -- eski flat indicator_rows'u ARAYAN testler
    icin kolaylik."""
    return [row for group in context["indicator_groups"] for row in group["rows"]]


# --- Bolge etiketleri (K2: sinyal degil, sadece olgu) -----------------------


def test_rsi_zone_asiri_alim():
    label, css_class = technical_card._rsi_zone(Decimal("75"))
    assert label == "Aşırı Alım Bölgesi"
    assert css_class == "extreme"


def test_rsi_zone_asiri_satim():
    label, _ = technical_card._rsi_zone(Decimal("25"))
    assert label == "Aşırı Satım Bölgesi"


def test_rsi_zone_notr():
    label, css_class = technical_card._rsi_zone(Decimal("50"))
    assert label == "Nötr Bölge"
    assert css_class == "neutral"


def test_rsi_zone_esik_sinirinda_asiri_sayilir():
    """70 ve 30 DAHIL (>= / <=) -- Wilder'in kendi esikleri."""
    assert technical_card._rsi_zone(Decimal("70"))[0] == "Aşırı Alım Bölgesi"
    assert technical_card._rsi_zone(Decimal("30"))[0] == "Aşırı Satım Bölgesi"


def test_bollinger_zone_ust_bandin_uzerinde():
    label, css_class = technical_card._bollinger_zone(Decimal("325"), Decimal("320"), Decimal("280"))
    assert label == "Üst Bandın Üzerinde"
    assert css_class == "extreme"


def test_bollinger_zone_bantlar_icinde():
    label, _ = technical_card._bollinger_zone(Decimal("300"), Decimal("320"), Decimal("280"))
    assert label == "Bantlar İçinde"


def test_adx_zone_guclu_trend():
    label, css_class = technical_card._adx_zone(Decimal("30"))
    assert label == "Güçlü Trend"
    assert css_class == "extreme"


def test_adx_zone_gelisen_trend():
    label, css_class = technical_card._adx_zone(Decimal("22"))
    assert label == "Gelişen Trend"
    assert css_class == "neutral"


def test_adx_zone_zayif_yatay():
    label, _ = technical_card._adx_zone(Decimal("15"))
    assert label == "Zayıf / Yatay Piyasa"


def test_adx_zone_none_ise_na():
    assert technical_card._adx_zone(None) == ("N/A", "neutral")


def test_cross_display_golden():
    value, note, css_class = technical_card._cross_display("golden", recent=False)
    assert value == "Altın Kesişim (Golden Cross)"
    assert note is None
    assert css_class == "positive"


def test_cross_display_golden_yakin_zamanda():
    _, note, _ = technical_card._cross_display("golden", recent=True)
    assert note == "Yakın Zamanda Oluştu"


def test_cross_display_death():
    value, note, css_class = technical_card._cross_display("death", recent=False)
    assert value == "Ölüm Kesişimi (Death Cross)"
    assert css_class == "negative"


def test_cross_display_none_ise_na():
    assert technical_card._cross_display(None, recent=False) == ("N/A", None, "neutral")


# --- build_technical_context ------------------------------------------------------


def test_build_technical_context_veri_yoksa_has_data_false():
    context = technical_card.build_technical_context(None, "ASTS", "NASDAQ")

    assert context["has_data"] is False
    assert context["ticker"] == "ASTS"
    assert context["market_label"] == "NASDAQ"
    assert "disclaimer" in context
    assert "past_performance_warning" in context


def test_build_technical_context_veriyle_tum_bolumleri_doldurur():
    context = technical_card.build_technical_context(_snapshot(), "THYAO", "BIST", company_name="Türk Hava Yolları A.O.")

    assert context["has_data"] is True
    assert context["ticker"] == "THYAO"
    assert context["company_name"] == "Türk Hava Yolları A.O."
    assert context["price_display"] == "314,00 ₺"
    assert [g["title"] for g in context["indicator_groups"]] == ["Trend", "Momentum", "Volatilite"]
    assert len(_all_rows(context)) == 16
    assert context["price_chart"]["has_data"] is True
    assert context["week52_bar"]["has_data"] is True
    assert context["volume_strip"]["has_data"] is True


def test_build_technical_context_nasdaq_dolar_isaretiyle_gosterir():
    context = technical_card.build_technical_context(_snapshot(), "AAPL", "NASDAQ")
    assert context["price_display"] == "$314,00"
    # SMA gibi fiyat-birimli gostergeler de dolar ile gosterilmeli
    sma20_row = next(r for r in _all_rows(context) if r["label"] == "SMA 20")
    assert sma20_row["value_display"].startswith("$")


def test_build_technical_context_rsi_notu_dogru_gecer():
    context = technical_card.build_technical_context(_snapshot(rsi_14=Decimal("80")), "THYAO", "BIST")
    rsi_row = next(r for r in _all_rows(context) if r["label"] == "RSI (14)")
    assert rsi_row["note_display"] == "Aşırı Alım Bölgesi"
    assert rsi_row["note_class"] == "extreme"


def test_build_technical_context_adx_ve_cross_satirlari_trend_grubunda():
    context = technical_card.build_technical_context(_snapshot(), "THYAO", "BIST")
    trend_group = next(g for g in context["indicator_groups"] if g["title"] == "Trend")
    labels = [r["label"] for r in trend_group["rows"]]
    assert "ADX (14) — Trend Gücü" in labels
    assert "SMA50/200 Kesişimi" in labels

    cross_row = next(r for r in trend_group["rows"] if r["label"] == "SMA50/200 Kesişimi")
    assert cross_row["value_display"] == "Altın Kesişim (Golden Cross)"
    assert cross_row["note_class"] == "positive"


def test_build_technical_context_haftaci_52_verisi_yoksa_bolum_bos():
    context = technical_card.build_technical_context(_snapshot(week52_high=None, week52_low=None, week52_position_pct=None), "THYAO", "BIST")
    assert context["week52_bar"]["has_data"] is False


def test_build_technical_context_hacim_verisi_yoksa_bolum_bos():
    context = technical_card.build_technical_context(_snapshot(avg_volume_20=None, volume_ratio_pct=None), "THYAO", "BIST")
    assert context["volume_strip"]["has_data"] is False


def test_price_chart_sma_hicbiri_dolu_degilse_none_doner():
    snap = _snapshot(chart_sma200=(None, None, None, None, None))
    context = technical_card.build_technical_context(snap, "THYAO", "BIST")
    assert context["price_chart"]["sma200_points"] is None
    assert context["price_chart"]["sma50_points"] is not None  # kismen dolu


def test_price_chart_tek_bar_ile_has_data_false():
    snap = _snapshot(chart_dates=(date(2026, 2, 1),), chart_closes=(Decimal("280"),), chart_sma50=(None,), chart_sma200=(None,))
    context = technical_card.build_technical_context(snap, "THYAO", "BIST")
    assert context["price_chart"]["has_data"] is False


# --- Gercek Playwright render -----------------------------------------------------


def test_render_technical_card_gercek_png_uretir(tmp_path):
    context = technical_card.build_technical_context(_snapshot(), "THYAO", "BIST", company_name="Türk Hava Yolları A.O.")

    out_path = tmp_path / "test_teknik.png"
    result = card.render_card(context, str(out_path), template_name="technical_card.html", screenshot_selector="#technical-card")

    assert result == str(out_path)
    assert out_path.exists()
    assert out_path.stat().st_size > 1000
    assert out_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_technical_card_veri_yokken_de_cokmez(tmp_path):
    context = technical_card.build_technical_context(None, "YENIHISSE", "BIST")

    out_path = tmp_path / "test_teknik_bos.png"
    card.render_card(context, str(out_path), template_name="technical_card.html", screenshot_selector="#technical-card")

    assert out_path.exists()
    assert out_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
