"""src/render/deep_card.py testleri (Derin Kart -- çok dönemli temel analiz).

build_deep_card_context() saf bir fonksiyondur -- src.analysis.trends'e
hiçbir AĞ isteği atmaz, elle kurulmuş bir MultiPeriodTrend/score_history/
sector_average kullanılır (Kural 11). SADECE test_render_deep_card_*
GERÇEK Playwright render'i doğrular (card.py/technical_card.py'deki AYNI
desen).
"""

from __future__ import annotations

import struct
from datetime import datetime
from decimal import Decimal

from src.analysis.trends import MultiPeriodTrend, PeriodTrendPoint, SeasonalityGroup, SectorAveragePoint
from src.render import card, deep_card


def _png_dimensions(path) -> tuple[int, int]:
    """PNG'nin IHDR parçasından genişlik/yükseklik okur -- test_calendar_card.py
    ile AYNI teknik (Pillow gibi bir DIŞ BAĞIMLILIK gerekmeden)."""
    with open(path, "rb") as f:
        header = f.read(24)
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def _point(period, revenue=Decimal("120"), ebitda=Decimal("30"), net_income=Decimal("15"),
           equity=Decimal("400"), gross_margin_pct=Decimal("40"), ebitda_margin_pct=Decimal("25"),
           net_margin_pct=Decimal("12"), current_ratio=Decimal("1.5"), net_debt_to_ebitda=Decimal("2"),
           roe_pct=Decimal("9")) -> PeriodTrendPoint:
    return PeriodTrendPoint(
        period=period,
        revenue=revenue,
        ebitda=ebitda,
        net_income=net_income,
        equity=equity,
        gross_margin_pct=gross_margin_pct,
        ebitda_margin_pct=ebitda_margin_pct,
        net_margin_pct=net_margin_pct,
        current_ratio=current_ratio,
        net_debt_to_ebitda=net_debt_to_ebitda,
        roe_pct=roe_pct,
    )


def _trend(points=None, seasonality=()) -> MultiPeriodTrend:
    if points is None:
        points = (_point((2025, 12), revenue=Decimal("100")), _point((2026, 3), revenue=Decimal("120")))
    return MultiPeriodTrend(points=tuple(points), seasonality=tuple(seasonality))


def _metric_chart(context: dict, title: str) -> dict:
    return next(c for c in context["metric_charts"] if c["title"] == title)


# --- build_deep_card_context: genel iskelet ------------------------------------------------------


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

    titles = {c["title"] for c in context["metric_charts"]}
    assert titles == {
        "Çeyreklik Satışlar",
        "Brüt Kâr Marjı (Çeyreklik)",
        "FAVÖK Marjı (Çeyreklik)",
        "Net Kâr Marjı (Çeyreklik)",
        "Cari Oran",
        "Kaldıraç Oranı",
        "Özkaynak Kârlılığı (ROE)",
    }
    assert all(c["chart"]["has_data"] for c in context["metric_charts"])


def test_build_deep_card_context_tek_donemde_grafikler_yeterli_veri_yok():
    """Sadece 1 donem varsa (K4: tek nokta trend SAYILMAZ) TUM grafikler
    has_data=False olmali."""
    context = deep_card.build_deep_card_context(_trend(points=[_point((2026, 3))]), [], "THYAO", "BIST")

    assert context["has_data"] is True  # kart yine uretilir (bkz. K4)
    assert all(not c["chart"]["has_data"] for c in context["metric_charts"])


def test_build_deep_card_context_kismi_eksik_veri_none_atlanir_grafik_yine_uretilir():
    """Bir donemde kaldirac/ROE None olsa bile (K4) diger donem yeterliyse
    grafik yine has_data=True olmali; polyline SADECE gercek noktalari icerir."""
    points = [
        _point((2025, 12), net_debt_to_ebitda=None, roe_pct=None),
        _point((2026, 3), net_debt_to_ebitda=Decimal("2"), roe_pct=Decimal("9")),
    ]
    context = deep_card.build_deep_card_context(_trend(points=points), [], "THYAO", "BIST")
    assert _metric_chart(context, "Kaldıraç Oranı")["chart"]["has_data"] is True
    assert _metric_chart(context, "Özkaynak Kârlılığı (ROE)")["chart"]["has_data"] is True


# --- Çeyreklik Satışlar: her zaman tek çizgi (mutlak deger) -----------------------------------------------------


def test_build_deep_card_context_satislar_grafigi_dogru_olcekleniyor():
    context = deep_card.build_deep_card_context(_trend(), [], "THYAO", "BIST")
    chart = _metric_chart(context, "Çeyreklik Satışlar")["chart"]

    assert chart["has_data"] is True
    assert len(chart["lines"]) == 1
    assert chart["lines"][0]["key"] == "self"
    assert chart["lines"][0]["label"] == "THYAO"


def test_build_deep_card_context_satislar_sektor_ortalamasi_verilse_bile_tek_cizgi():
    """Mutlak (para birimi) değerler farklı büyüklükteki şirketler arasında
    karşılaştırılamaz -- bkz. trends.compute_sector_average() modül notu.
    Sektör ortalaması verilse BİLE Çeyreklik Satışlar grafiği TEK çizgi kalmalı."""
    sector_average = {(2026, 3): SectorAveragePoint(
        period=(2026, 3), peer_count=2, gross_margin_pct=Decimal("30"), ebitda_margin_pct=None,
        net_margin_pct=None, current_ratio=None, net_debt_to_ebitda=None, roe_pct=None,
    )}
    context = deep_card.build_deep_card_context(
        _trend(), [], "THYAO", "BIST", sector_average=sector_average, sector_name="Ulaştırma"
    )
    chart = _metric_chart(context, "Çeyreklik Satışlar")["chart"]
    assert len(chart["lines"]) == 1


def test_build_deep_card_context_nasdaq_dolar_isaretiyle_gosterir():
    context = deep_card.build_deep_card_context(_trend(), [], "AAPL", "NASDAQ")
    chart = _metric_chart(context, "Çeyreklik Satışlar")["chart"]
    # gridline degerleri dolar isaretiyle formatlanmis olmali
    assert any("$" in gl["display"] for gl in chart["gridlines"])


# --- Sektör ortalaması (2. çizgi) -- oran/marj grafikleri -----------------------------------------------------


def test_build_deep_card_context_sektor_ortalamasi_yoksa_tek_cizgi():
    context = deep_card.build_deep_card_context(_trend(), [], "THYAO", "BIST")
    chart = _metric_chart(context, "Brüt Kâr Marjı (Çeyreklik)")["chart"]
    assert len(chart["lines"]) == 1
    assert chart["lines"][0]["key"] == "self"


def test_build_deep_card_context_sektor_ortalamasi_varsa_iki_cizgi():
    sector_average = {
        (2025, 12): SectorAveragePoint(
            period=(2025, 12), peer_count=2, gross_margin_pct=Decimal("35"), ebitda_margin_pct=Decimal("20"),
            net_margin_pct=Decimal("10"), current_ratio=Decimal("1.2"), net_debt_to_ebitda=Decimal("2.5"),
            roe_pct=Decimal("8"),
        ),
        (2026, 3): SectorAveragePoint(
            period=(2026, 3), peer_count=2, gross_margin_pct=Decimal("38"), ebitda_margin_pct=Decimal("22"),
            net_margin_pct=Decimal("11"), current_ratio=Decimal("1.3"), net_debt_to_ebitda=Decimal("2.2"),
            roe_pct=Decimal("9"),
        ),
    }
    context = deep_card.build_deep_card_context(
        _trend(), [], "THYAO", "BIST",
        sector_average=sector_average, sector_name="Ulaştırma ve Depolama", peer_count=2,
    )

    chart = _metric_chart(context, "Brüt Kâr Marjı (Çeyreklik)")["chart"]
    keys = {line["key"] for line in chart["lines"]}
    assert keys == {"self", "sector"}
    sector_line = next(line for line in chart["lines"] if line["key"] == "sector")
    assert sector_line["label"] == "Sektör Ort. (Ulaştırma ve Depolama)"
    assert context["sector_name"] == "Ulaştırma ve Depolama"
    assert context["peer_count"] == 2


def test_build_deep_card_context_peer_count_varsayilan_sifir():
    """CANLI GÖZLEM (TATGD, 2 gerçek peer -- EFOR/BORSK): SectorAveragePoint.
    peer_count dönem-bazlı olduğu için (bir peer bir çeyreği kaçırabilir)
    eskiden buradan max() ile türetilen peer_count YANILTICI şekilde 1
    çıkıyordu. Artık peer_count AYRI, açık bir parametre -- verilmezse
    (eski çağıranlar/testler) varsayılan 0 kalır, sector_average'ın kendi
    içeriğinden TÜRETİLMEZ."""
    sector_average = {
        (2026, 3): SectorAveragePoint(
            period=(2026, 3), peer_count=5, gross_margin_pct=Decimal("38"), ebitda_margin_pct=None,
            net_margin_pct=None, current_ratio=None, net_debt_to_ebitda=None, roe_pct=None,
        ),
    }
    context = deep_card.build_deep_card_context(
        _trend(), [], "THYAO", "BIST", sector_average=sector_average, sector_name="X"
    )
    assert context["peer_count"] == 0


def test_build_deep_card_context_sektor_ortalamasi_kismi_donem_eslesir():
    """Sektör ortalaması SADECE eşleşen dönemler için None-olmayan deger
    tasimali -- eslesmeyen donemde None (grafik o noktada polyline'i keser,
    cokme YOK)."""
    sector_average = {
        (2026, 3): SectorAveragePoint(
            period=(2026, 3), peer_count=1, gross_margin_pct=Decimal("38"), ebitda_margin_pct=None,
            net_margin_pct=None, current_ratio=None, net_debt_to_ebitda=None, roe_pct=None,
        ),
    }
    context = deep_card.build_deep_card_context(
        _trend(), [], "THYAO", "BIST", sector_average=sector_average, sector_name="X"
    )
    chart = _metric_chart(context, "Brüt Kâr Marjı (Çeyreklik)")["chart"]
    sector_line = next(line for line in chart["lines"] if line["key"] == "sector")
    # 2 donemden SADECE 1'i (2026,3) sektor ortalamasinda var -- polyline'da TEK nokta.
    assert len(sector_line["markers"]) == 1


def test_build_deep_card_context_sektor_verisi_hicbir_alanda_yoksa_ikinci_cizgi_eklenmez():
    """SectorAveragePoint var ama o METRIK icin TUM degerler None ise
    (peer'lerde o alan hesaplanamamis) ikinci cizgi EKLENMEMELI."""
    sector_average = {
        (2025, 12): SectorAveragePoint(
            period=(2025, 12), peer_count=1, gross_margin_pct=Decimal("35"), ebitda_margin_pct=None,
            net_margin_pct=None, current_ratio=None, net_debt_to_ebitda=None, roe_pct=None,
        ),
        (2026, 3): SectorAveragePoint(
            period=(2026, 3), peer_count=1, gross_margin_pct=Decimal("38"), ebitda_margin_pct=None,
            net_margin_pct=None, current_ratio=None, net_debt_to_ebitda=None, roe_pct=None,
        ),
    }
    context = deep_card.build_deep_card_context(
        _trend(), [], "THYAO", "BIST", sector_average=sector_average, sector_name="X"
    )
    # ebitda_margin_pct sektorde HICBIR donem icin yok -> FAVOK Marji grafiginde TEK cizgi kalmali.
    chart = _metric_chart(context, "FAVÖK Marjı (Çeyreklik)")["chart"]
    assert len(chart["lines"]) == 1


# --- Cari Oran (yeni metrik) -----------------------------------------------------


def test_build_deep_card_context_cari_oran_dogru_formatlanir():
    context = deep_card.build_deep_card_context(_trend(), [], "THYAO", "BIST")
    chart = _metric_chart(context, "Cari Oran")["chart"]
    assert chart["has_data"] is True
    assert any("x" in gl["display"] for gl in chart["gridlines"])


# --- Skor gecmisi -----------------------------------------------------


def test_build_deep_card_context_skor_gecmisi_yeterliyse_grafik_uretir():
    history = [(datetime(2026, 1, 1), 5.0), (datetime(2026, 4, 1), 7.5)]
    context = deep_card.build_deep_card_context(_trend(), history, "THYAO", "BIST")

    chart = context["score_history_chart"]
    assert chart["has_data"] is True
    assert chart["x_ticks"][0]["label"] == "01.01.26"
    assert len(chart["lines"][0]["markers"]) == 2


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
    assert [t["label"] for t in item["chart"]["x_ticks"]] == ["2025", "2026"]


def test_build_deep_card_context_mevsimsellik_bossa_bos_liste():
    context = deep_card.build_deep_card_context(_trend(), [], "THYAO", "BIST")
    assert context["seasonality_charts"] == []


# --- Gercek Playwright render -----------------------------------------------------


def test_render_deep_card_gercek_png_uretir(tmp_path):
    seasonality = (SeasonalityGroup(quarter_number=3, years=(2025, 2026), revenues=(Decimal("100"), Decimal("120"))),)
    history = [(datetime(2026, 1, 1), 5.0), (datetime(2026, 4, 1), 7.5)]
    sector_average = {
        (2025, 12): SectorAveragePoint(
            period=(2025, 12), peer_count=2, gross_margin_pct=Decimal("35"), ebitda_margin_pct=Decimal("20"),
            net_margin_pct=Decimal("10"), current_ratio=Decimal("1.2"), net_debt_to_ebitda=Decimal("2.5"),
            roe_pct=Decimal("8"),
        ),
        (2026, 3): SectorAveragePoint(
            period=(2026, 3), peer_count=2, gross_margin_pct=Decimal("38"), ebitda_margin_pct=Decimal("22"),
            net_margin_pct=Decimal("11"), current_ratio=Decimal("1.3"), net_debt_to_ebitda=Decimal("2.2"),
            roe_pct=Decimal("9"),
        ),
    }
    context = deep_card.build_deep_card_context(
        _trend(seasonality=seasonality), history, "THYAO", "BIST",
        company_name="Türk Hava Yolları A.O.", sector_average=sector_average, sector_name="Ulaştırma ve Depolama",
    )

    out_path = tmp_path / "test_derin.png"
    result = card.render_card(context, str(out_path), template_name="deep_card.html", screenshot_selector="#deep-card")

    assert result == str(out_path)
    assert out_path.exists()
    assert out_path.stat().st_size > 1000
    assert out_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_deep_card_en_kotu_durumda_telegram_boyut_sinirini_asmaz(tmp_path):
    """CANLI HATA (kullanıcı raporu, 2026-08-03, CIMSA): 7 sabit metrik
    grafiği + skor geçmişi + 4 mevsimsellik grafiği (bu TAVAN -- sadece 4
    çeyrek numarası olduğu için daha fazlası MÜMKÜN DEĞİL) içeren bir kart
    2400x8760'a ulaşıp `telegram.error.BadRequest: Photo_invalid_dimensions`
    ile çöküyordu (Telegram sınırı: genişlik+yükseklik <= 10000). Bu test
    TAM olarak bu en-kötü-durumu (12 blok: sektör ortalamalı 7 metrik + skor
    geçmişi + 4/4 mevsimsellik grubu) kurup GERÇEK Playwright render'iyle
    doğrular -- test_calendar_card.py'deki AYNI teknik (Pillow'a bağımlı
    OLMADAN IHDR'dan boyut okuma, bkz. _png_dimensions)."""
    seasonality = tuple(
        SeasonalityGroup(quarter_number=q, years=(2024, 2025, 2026), revenues=(Decimal("100"), Decimal("110"), Decimal("120")))
        for q in (3, 6, 9, 12)
    )
    history = [(datetime(2026, 1, 1), 5.0), (datetime(2026, 4, 1), 7.5), (datetime(2026, 7, 1), 6.0)]
    # 9 çeyreklik ardışık dönem serisi (CIMSA ile aynı büyüklükte pencere).
    points = [
        _point((2024, 6)), _point((2024, 9)), _point((2024, 12)),
        _point((2025, 3)), _point((2025, 6)), _point((2025, 9)), _point((2025, 12)),
        _point((2026, 3)), _point((2026, 6)),
    ]
    sector_average = {
        p.period: SectorAveragePoint(
            period=p.period, peer_count=2, gross_margin_pct=Decimal("35"), ebitda_margin_pct=Decimal("20"),
            net_margin_pct=Decimal("10"), current_ratio=Decimal("1.2"), net_debt_to_ebitda=Decimal("2.5"),
            roe_pct=Decimal("8"),
        )
        for p in points
    }
    context = deep_card.build_deep_card_context(
        _trend(points=points, seasonality=seasonality), history, "CIMSA", "BIST",
        company_name="ÇİMSA ÇİMENTO SANAYİ VE TİCARET A.Ş.",
        sector_average=sector_average, sector_name="TAŞ VE TOPRAĞA DAYALI SANAYİ",
    )
    assert len(context["metric_charts"]) == 7
    assert len(context["seasonality_charts"]) == 4

    out_path = tmp_path / "test_derin_en_kotu.png"
    card.render_card(context, str(out_path), template_name="deep_card.html", screenshot_selector="#deep-card")

    width, height = _png_dimensions(out_path)
    assert width + height <= 10000, f"Telegram foto sınırı aşıldı: {width}x{height} (toplam {width + height})"


def test_render_deep_card_veri_yokken_de_cokmez(tmp_path):
    context = deep_card.build_deep_card_context(None, [], "YENIHISSE", "BIST")

    out_path = tmp_path / "test_derin_bos.png"
    card.render_card(context, str(out_path), template_name="deep_card.html", screenshot_selector="#deep-card")

    assert out_path.exists()
    assert out_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
