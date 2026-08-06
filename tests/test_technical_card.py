"""src/render/technical_card.py testleri (Faz 15 - Teknik Analiz kartı).

build_technical_context() saf bir fonksiyondur -- src.analysis.technical'e
hiçbir AĞ isteği atmaz, elle kurulmuş bir TechnicalSnapshot kullanılır
(Kural 11). SADECE test_render_technical_card_* GERÇEK Playwright render'i
doğrular (card.py/calendar_card.py'deki AYNI desen).
"""

from __future__ import annotations

import struct
from datetime import date
from decimal import Decimal

from src.analysis.technical import TechnicalSnapshot
from src.render import card, technical_card


def _png_dimensions(path) -> tuple[int, int]:
    """PNG'nin IHDR parçasından genişlik/yükseklik okur -- test_deep_card.py/
    test_calendar_card.py ile AYNI teknik (Pillow'a bağımlı OLMADAN)."""
    with open(path, "rb") as f:
        header = f.read(24)
    width, height = struct.unpack(">II", header[16:24])
    return width, height


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
        chart_rsi=(None, Decimal("48"), Decimal("52"), Decimal("55"), Decimal("55.5")),
        chart_macd_line=(None, None, Decimal("-0.5"), Decimal("1.0"), Decimal("2.3")),
        chart_macd_signal=(None, None, None, Decimal("0.5"), Decimal("1.1")),
        chart_macd_histogram=(None, None, None, Decimal("0.5"), Decimal("1.2")),
        chart_volumes=tuple(Decimal(str(1_000_000 + i * 100_000)) for i in range(5)),
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


# --- MACD/RSI/Hacim mini grafikleri (Faz 15.1) ------------------------------------


def test_macd_chart_veriyle_dolu_doner():
    context = technical_card.build_technical_context(_snapshot(), "THYAO", "BIST")
    macd_chart = context["macd_chart"]

    assert macd_chart["has_data"] is True
    assert macd_chart["line_points"] is not None
    assert macd_chart["signal_points"] is not None
    assert len(macd_chart["histogram_bars"]) == 2  # sadece son 2 eleman None degil (bkz. _snapshot fixture)
    assert all(bar["positive"] for bar in macd_chart["histogram_bars"])  # ikisi de pozitif (0.5, 1.2)


def test_macd_chart_sifir_cizgisi_tum_deger_ayni_isaretteyken_bile_araliga_dahil():
    """Tüm MACD/histogram değerleri POZİTİFSE bile sıfır çizgisi görünür
    aralıkta kalmalı (`include_zero=True`) -- aksi halde histogram
    çubuklarının hangi yöne (pozitif/negatif) baktığı görsel olarak
    ANLAMSIZLAŞIR."""
    snap = _snapshot(
        chart_macd_line=(Decimal("5"), Decimal("6"), Decimal("7"), Decimal("8"), Decimal("9")),
        chart_macd_signal=(Decimal("4"), Decimal("4.5"), Decimal("5"), Decimal("5.5"), Decimal("6")),
        chart_macd_histogram=(Decimal("1"), Decimal("1.5"), Decimal("2"), Decimal("2.5"), Decimal("3")),
    )
    context = technical_card.build_technical_context(snap, "THYAO", "BIST")
    macd_chart = context["macd_chart"]

    zero_y = float(macd_chart["zero_line_y"])
    assert 0 <= zero_y <= technical_card._MINI_CHART_VIEWBOX_HEIGHT


def test_macd_chart_veri_yoksa_has_data_false():
    n = 5
    snap = _snapshot(
        chart_macd_line=tuple([None] * n),
        chart_macd_signal=tuple([None] * n),
        chart_macd_histogram=tuple([None] * n),
    )
    context = technical_card.build_technical_context(snap, "THYAO", "BIST")
    assert context["macd_chart"]["has_data"] is False


def test_rsi_chart_sabit_0_100_olcek_kullanir():
    """RSI grafiği dinamik min/max DEĞİL, tanım gereği sabit 0-100
    ölçeğini kullanır (bkz. modül üst notu K2) -- bu yüzden 70/30
    referans çizgilerinin y konumu HER ZAMAN aynı olmalı, veri
    aralığından BAĞIMSIZ."""
    snap_low = _snapshot(chart_rsi=(Decimal("10"), Decimal("15"), Decimal("20"), Decimal("22"), Decimal("25")))
    snap_high = _snapshot(chart_rsi=(Decimal("80"), Decimal("85"), Decimal("88"), Decimal("90"), Decimal("92")))

    ctx_low = technical_card.build_technical_context(snap_low, "THYAO", "BIST")["rsi_chart"]
    ctx_high = technical_card.build_technical_context(snap_high, "THYAO", "BIST")["rsi_chart"]

    assert ctx_low["overbought_y"] == ctx_high["overbought_y"]
    assert ctx_low["oversold_y"] == ctx_high["oversold_y"]


def test_rsi_chart_veri_yoksa_has_data_false():
    snap = _snapshot(chart_rsi=(None, None, None, None, None))
    context = technical_card.build_technical_context(snap, "THYAO", "BIST")
    assert context["rsi_chart"]["has_data"] is False


def test_volume_history_chart_bar_sayisi_seri_uzunluguyla_esit():
    context = technical_card.build_technical_context(_snapshot(), "THYAO", "BIST")
    volume_chart = context["volume_history_chart"]

    assert volume_chart["has_data"] is True
    assert len(volume_chart["bars"]) == 5
    assert volume_chart["avg_line_y"] is not None


def test_volume_history_chart_ortalama_yoksa_avg_line_none():
    snap = _snapshot(avg_volume_20=None)
    context = technical_card.build_technical_context(snap, "THYAO", "BIST")
    assert context["volume_history_chart"]["avg_line_y"] is None


# --- Teknik değerlendirme metni (Gemini/fallback, Faz 15.1) -----------------------


class _FakeCommentary:
    def __init__(self):
        self.headline = "GÖRÜNÜM NÖTR"
        self.summary = "Fiyat SMA200 üzerinde, RSI nötr bölgede."
        self.positives = ["Fiyat SMA200'ün %16,3 üzerinde"]
        self.negatives = ["Hacim ortalamanın altında"]
        self.source = "llm"


def test_build_technical_context_commentary_verilmezse_none_doner():
    context = technical_card.build_technical_context(_snapshot(), "THYAO", "BIST")
    assert context["commentary"] is None


def test_build_technical_context_commentary_verilirse_sozluge_cevrilir():
    context = technical_card.build_technical_context(_snapshot(), "THYAO", "BIST", commentary=_FakeCommentary())
    assert context["commentary"]["headline"] == "GÖRÜNÜM NÖTR"
    assert context["commentary"]["positives"] == ["Fiyat SMA200'ün %16,3 üzerinde"]


# --- build_commentary_inputs (Faz 15.1) -----------------------------------------


def test_build_commentary_inputs_gerekli_alanlari_dondurur():
    inputs = technical_card.build_commentary_inputs(_snapshot(), "THYAO", "BIST")

    assert inputs["ticker"] == "THYAO"
    assert inputs["price_display"] is not None
    assert len(inputs["indicator_groups"]) == 3  # Trend/Momentum/Volatilite
    assert inputs["week52_bar"]["has_data"] is True
    assert inputs["volume_strip"]["has_data"] is True


# --- Gercek Playwright render -----------------------------------------------------


def test_render_technical_card_gercek_png_uretir(tmp_path):
    context = technical_card.build_technical_context(_snapshot(), "THYAO", "BIST", company_name="Türk Hava Yolları A.O.")

    out_path = tmp_path / "test_teknik.png"
    result = card.render_card(context, str(out_path), template_name="technical_card.html", screenshot_selector="#technical-card")

    assert result == str(out_path)
    assert out_path.exists()
    assert out_path.stat().st_size > 1000
    assert out_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


class _FakeCommentaryWorstCase:
    headline = "YUKARI EĞİLİMLİ, MOMENTUM GÜÇLENİYOR AMA AŞIRI ISINMA RİSKİ VAR"
    summary = (
        "Fiyat SMA200'ün belirgin şekilde üzerinde seyrediyor ve kısa vadeli hareketli ortalamalar "
        "yukarı eğilimini sürdürüyor. RSI aşırı alım bölgesine yaklaşırken MACD histogramı pozitif "
        "bölgede genişlemeye devam ediyor; bu iki gösterge arasında kısmi bir uyumsuzluk dikkat "
        "çekiyor. Hacim son günlerde 20 günlük ortalamanın belirgin üzerinde seyrediyor, bu da "
        "fiyat hareketinin katılımla desteklendiğini gösteriyor. 52 haftalık aralığın üst "
        "sınırına yakın bir konumda bulunuluyor."
    )
    positives = ["Fiyat SMA200 üzerinde", "MACD sinyal çizgisinin üzerinde", "Hacim ortalamanın üzerinde", "Golden Cross yakın zamanda oluştu"]
    negatives = ["RSI aşırı alım bölgesinde", "Fiyat 52 hafta tepesine yakın", "ADX aşırı güçlü trend gösteriyor", "Bollinger üst bandının üzerinde"]
    source = "llm"


def test_render_technical_card_en_kotu_durumda_telegram_boyut_sinirini_asmaz(tmp_path):
    """Faz 15.1 (2026-08-06): MACD/RSI/Hacim grafik panelleri + Teknik
    Değerlendirme metni EKLENDİKTEN SONRA kart büyüdü -- bu test, TÜM
    bölümlerin dolu olduğu (260 günlük tam veri + 4/4 maddelik en uzun
    yorum) EN KÖTÜ durumda bile Telegram'ın fotoğraf sınırını (genişlik+
    yükseklik <= 10000) AŞMADIĞINI kanıtlar (bkz. test_deep_card.py'deki
    AYNI sınıf regresyon, CIMSA canlı hatası)."""
    import datetime as _dt

    n = 260
    dates = [date(2025, 1, 1) + _dt.timedelta(days=i) for i in range(n)]
    closes = tuple(Decimal(str(300 + i * 0.2)) for i in range(n))
    snap = _snapshot(
        chart_dates=tuple(dates[-184:]),
        chart_closes=closes[-184:],
        chart_sma50=tuple(Decimal(str(295 + i * 0.15)) for i in range(184)),
        chart_sma200=tuple(Decimal(str(290 + i * 0.1)) for i in range(184)),
        chart_rsi=tuple(Decimal(str(40 + (i % 50))) for i in range(184)),
        chart_macd_line=tuple(Decimal(str(-2 + (i % 8))) for i in range(184)),
        chart_macd_signal=tuple(Decimal(str(-1.5 + (i % 8))) for i in range(184)),
        chart_macd_histogram=tuple(Decimal(str(-0.5 + (i % 3))) for i in range(184)),
        chart_volumes=tuple(Decimal(str(1_000_000 + i * 5000)) for i in range(184)),
        week52_high=Decimal("340.0"),
        week52_low=Decimal("230.0"),
        week52_position_pct=Decimal("94.2"),
    )
    context = technical_card.build_technical_context(
        snap, "THYAO", "BIST", company_name="Türk Hava Yolları A.O.", commentary=_FakeCommentaryWorstCase()
    )

    out_path = tmp_path / "test_teknik_en_kotu.png"
    card.render_card(context, str(out_path), template_name="technical_card.html", screenshot_selector="#technical-card")

    width, height = _png_dimensions(out_path)
    assert width + height <= 10000, f"Telegram fotoğraf sınırı aşıldı: {width}x{height} (toplam {width + height})"


def test_render_technical_card_veri_yokken_de_cokmez(tmp_path):
    context = technical_card.build_technical_context(None, "YENIHISSE", "BIST")

    out_path = tmp_path / "test_teknik_bos.png"
    card.render_card(context, str(out_path), template_name="technical_card.html", screenshot_selector="#technical-card")

    assert out_path.exists()
    assert out_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
