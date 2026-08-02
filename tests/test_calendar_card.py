"""src/render/calendar_card.py testleri (Faz 13, v2 -- iki katmanlı/chip tasarımı).

build_calendar_context()/build_calendar_share_text() saf fonksiyonlardir --
src.fetchers.earnings_calendar'a hicbir AG istegi atmaz, elle kurulmus
EarningsDate listeleri kullanilir (bkz. Kural 11: testlerde ag istegi
atilmaz). Sadece test_render_calendar_card_* GERCEK Playwright render'i
dogrular (card.py'deki AYNI desen, bkz. test_card.py
test_render_card_gercek_png_uretir).
"""

from __future__ import annotations

import struct
from datetime import date, datetime

from src.fetchers.earnings_calendar import CONFIDENCE_KESIN, CONFIDENCE_SON_TARIH, CONFIDENCE_TAHMINI, EarningsDate
from src.render import calendar_card, card

_NOW = datetime(2026, 8, 2, 10, 0)


def _png_dimensions(path) -> tuple[int, int]:
    """PNG'nin IHDR parcasindan genislik/yukseklik okur (buyuk-endian uint32,
    dosyanin ilk 24 baytinda) -- Pillow gibi bir DIS BAGIMLILIK GEREKMEDEN
    (requirements.txt'te yok) Telegram boyut siniri testini dogrulamak icin."""
    with open(path, "rb") as f:
        header = f.read(24)
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def _entry(
    ticker: str, company_name: str, expected_date: date, confidence: str, period=(2026, 6), market: str = "BIST"
) -> EarningsDate:
    source = {
        CONFIDENCE_KESIN: "KAP Finansal Takvim bildirimi",
        CONFIDENCE_TAHMINI: "geçmiş yayın medyanı",
        CONFIDENCE_SON_TARIH: "SPK II-14.1 Tebliği",
    }[confidence]
    return EarningsDate(
        ticker=ticker, company_name=company_name, market=market, period=period,
        expected_date=expected_date, confidence=confidence, source=source,
    )


def _ornek_entries() -> list[EarningsDate]:
    return [
        _entry("THYAO", "Türk Hava Yolları A.O.", date(2026, 8, 2), CONFIDENCE_KESIN),
        _entry("ASELS", "Aselsan A.Ş.", date(2026, 8, 2), CONFIDENCE_TAHMINI),
        _entry("TUPRS", "Tüpraş", date(2026, 8, 5), CONFIDENCE_KESIN),
        # son_tarih DISLANMALI (kullanici karari, bkz. modul ust notu):
        _entry("KCHOL", "Koç Holding", date(2026, 8, 20), CONFIDENCE_SON_TARIH),
    ]


# --- _wrap_line_count (saf yardimci) -----------------------------------------------------


def test_wrap_line_count_tam_bolunen() -> None:
    assert calendar_card._wrap_line_count(10, 10) == 1
    assert calendar_card._wrap_line_count(20, 10) == 2


def test_wrap_line_count_yukari_yuvarlar() -> None:
    assert calendar_card._wrap_line_count(11, 10) == 2
    assert calendar_card._wrap_line_count(1, 10) == 1


def test_wrap_line_count_sifir() -> None:
    assert calendar_card._wrap_line_count(0, 10) == 0


# --- build_calendar_context: katmanlara ayirma -----------------------------------------------------


def test_build_calendar_context_iki_katmana_ayirir() -> None:
    context = calendar_card.build_calendar_context(_ornek_entries(), "BIST", now=_NOW)

    kesin_tickers = {row["ticker"] for group in context["kesin_day_groups"] for row in group["rows"]}
    tahmini_tickers = {row["ticker"] for group in context["tahmini_day_groups"] for row in group["rows"]}

    assert kesin_tickers == {"THYAO", "TUPRS"}
    assert tahmini_tickers == {"ASELS"}


def test_build_calendar_context_son_tarih_hicbir_katmanda_yok() -> None:
    context = calendar_card.build_calendar_context(_ornek_entries(), "BIST", now=_NOW)
    all_tickers = {row["ticker"] for group in context["kesin_day_groups"] + context["tahmini_day_groups"] for row in group["rows"]}
    assert "KCHOL" not in all_tickers


def test_build_calendar_context_tarihe_gore_gruplar() -> None:
    context = calendar_card.build_calendar_context(_ornek_entries(), "BIST", now=_NOW)
    assert len(context["kesin_day_groups"]) == 2  # 2 ve 5 agustos
    assert context["kesin_day_groups"][0]["date_short"] == "02.08.2026"
    assert context["kesin_day_groups"][1]["date_short"] == "05.08.2026"


def test_build_calendar_context_bugun_isaretlenir() -> None:
    context = calendar_card.build_calendar_context(_ornek_entries(), "BIST", now=_NOW)
    assert context["kesin_day_groups"][0]["is_today"] is True
    assert context["kesin_day_groups"][1]["is_today"] is False


def test_build_calendar_context_bos_liste_is_empty() -> None:
    context = calendar_card.build_calendar_context([], "BIST", now=_NOW)
    assert context["is_empty"] is True
    assert context["is_kesin_empty"] is True
    assert context["is_tahmini_empty"] is True


def test_build_calendar_context_sadece_kesin_varsa_tahmini_bos() -> None:
    entries = [_entry("THYAO", "Türk Hava Yolları", date(2026, 8, 2), CONFIDENCE_KESIN)]
    context = calendar_card.build_calendar_context(entries, "BIST", now=_NOW)
    assert context["is_empty"] is False
    assert context["is_kesin_empty"] is False
    assert context["is_tahmini_empty"] is True


def test_build_calendar_context_sadece_son_tarih_varsa_is_empty() -> None:
    entries = [_entry("KCHOL", "Koç Holding", date(2026, 8, 20), CONFIDENCE_SON_TARIH)]
    context = calendar_card.build_calendar_context(entries, "BIST", now=_NOW)
    assert context["is_empty"] is True


def test_build_calendar_context_market_label_ve_kaynak_notu() -> None:
    bist_context = calendar_card.build_calendar_context(_ornek_entries(), "BIST", now=_NOW)
    assert bist_context["market_label"] == "BİST"
    assert "KAP" in bist_context["data_sources_note"]

    nasdaq_entries = [_entry("AAPL", "Apple Inc.", date(2026, 8, 3), CONFIDENCE_TAHMINI, market="NASDAQ")]
    nasdaq_context = calendar_card.build_calendar_context(nasdaq_entries, "NASDAQ", now=_NOW)
    assert nasdaq_context["market_label"] == "NASDAQ"
    assert nasdaq_context["data_sources_note"] == "NASDAQ takvim API"


def test_build_calendar_context_disclaimer_zorunlu() -> None:
    context = calendar_card.build_calendar_context(_ornek_entries(), "BIST", now=_NOW)
    assert "yatırım tavsiyesi değildir" in context["disclaimer"]


# --- build_calendar_context: piksel butcesi / kirpma -----------------------------------------------------


def test_build_calendar_context_max_rows_kesin_katmani_kirpar() -> None:
    entries = [_entry(f"T{i}", f"Şirket {i}", date(2026, 8, 2), CONFIDENCE_KESIN) for i in range(5)]
    context = calendar_card.build_calendar_context(entries, "BIST", now=_NOW, max_rows=3)

    shown = sum(len(g["rows"]) for g in context["kesin_day_groups"])
    assert shown == 3
    assert context["kesin_truncated_count"] == 2


def test_build_calendar_context_kesin_katmani_asla_kirpilmaz_tahmini_kirpilir() -> None:
    """Kesin katmani ONCE doldurulur, kalan butce tahmini katmanina aktarilir
    -- kullanici karari: kesin tarihler ONCELIKLI, kesilecekse ONCE tahmini
    kesilmeli."""
    kesin = [_entry(f"K{i}", f"Kesin {i}", date(2026, 8, 2), CONFIDENCE_KESIN) for i in range(3)]
    tahmini = [_entry(f"T{i}", f"Tahmini {i}", date(2026, 8, 3), CONFIDENCE_TAHMINI) for i in range(500)]
    context = calendar_card.build_calendar_context(kesin + tahmini, "BIST", now=_NOW)

    assert context["kesin_truncated_count"] == 0
    kesin_shown = sum(len(g["rows"]) for g in context["kesin_day_groups"])
    assert kesin_shown == 3
    assert context["tahmini_truncated_count"] > 0  # 500 tahmini kesinlikle butceyi asar


# --- build_calendar_share_text -----------------------------------------------------


def test_build_calendar_share_text_hashtag_formati() -> None:
    context = calendar_card.build_calendar_context(_ornek_entries(), "BIST", now=_NOW)
    text = calendar_card.build_calendar_share_text(context)

    assert "#THYAO" in text
    assert "#TUPRS" in text
    assert "#ASELS" in text
    assert "$THYAO" not in text  # eski "$" formati ARTIK kullanilmiyor
    assert "#KCHOL" not in text  # son_tarih dislanmali
    assert "02.08.2026" in text
    assert "(BUGÜN)" in text
    assert "yatırım tavsiyesi değildir" in text


def test_build_calendar_share_text_iki_bolum_basligi_icerir() -> None:
    context = calendar_card.build_calendar_context(_ornek_entries(), "BIST", now=_NOW)
    text = calendar_card.build_calendar_share_text(context)
    assert "KESİNLEŞEN" in text
    assert "TAHMİNİ" in text
    assert text.index("KESİNLEŞEN") < text.index("TAHMİNİ")  # kesin ONCE gelir


def test_build_calendar_share_text_bos_liste_mesaji() -> None:
    context = calendar_card.build_calendar_context([], "BIST", now=_NOW)
    text = calendar_card.build_calendar_share_text(context)
    assert "bulunamadı" in text


def test_build_calendar_share_text_sadece_kesin_varsa_tahmini_basligi_yok() -> None:
    entries = [_entry("THYAO", "Türk Hava Yolları", date(2026, 8, 2), CONFIDENCE_KESIN)]
    context = calendar_card.build_calendar_context(entries, "BIST", now=_NOW)
    text = calendar_card.build_calendar_share_text(context)
    assert "KESİNLEŞEN" in text
    assert "TAHMİNİ" not in text


# --- render_card: gercek Playwright ile PNG uretimi (uctan uca) -----------------------------------------------------


def test_render_calendar_card_gercek_png_uretir(tmp_path) -> None:
    context = calendar_card.build_calendar_context(_ornek_entries(), "BIST", now=_NOW)

    out_path = tmp_path / "test_takvim.png"
    result = card.render_card(
        context, str(out_path), template_name="calendar_card.html", screenshot_selector="#calendar-card"
    )

    assert result == str(out_path)
    assert out_path.exists()
    assert out_path.stat().st_size > 1000
    assert out_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_calendar_card_telegram_boyut_sinirini_asmaz(tmp_path, monkeypatch) -> None:
    """CANLI hata (kullanıcı raporu, 2026-08-02): eski "bir şirket bir satır"
    tasarımında 57 satır/16 gün grubu 2400x8924 piksele ulaşmıştı, Telegram
    send_photo bunu `Photo_invalid_dimensions` ile REDDETMİŞTİ (Telegram
    sınırı: genişlik+yükseklik <= 10000). Bu test, çok sayıda kesin/tahmini
    kayıt içeren GERÇEK bir Playwright render'ın (yeni "yan yana chip"
    tasarımıyla) Telegram sınırının İÇİNDE kaldığını doğrular.

    `company_logo.fetch_logo_data_uri` monkeypatch'lenir -- 100 UYDURMA
    ticker (T0, K0, ...) için gerçek TradingView aramaları hem AĞ İSTEĞİ
    ATMAMA kuralını (Kural 11) ihlal eder hem de testi YAVAŞLATIR (canlı
    ölçüldü: ~165 saniye, monkeypatch'siz)."""
    monkeypatch.setattr(calendar_card.company_logo, "fetch_logo_data_uri", lambda ticker, market="BIST": None)

    kesin = [_entry(f"K{i}", f"Kesin Şirket {i}", date(2026, 8, 1 + (i % 15)), CONFIDENCE_KESIN) for i in range(20)]
    tahmini = [_entry(f"T{i}", f"Tahmini Şirket {i}", date(2026, 8, 1 + (i % 25)), CONFIDENCE_TAHMINI) for i in range(80)]
    context = calendar_card.build_calendar_context(kesin + tahmini, "BIST", now=_NOW)

    out_path = tmp_path / "test_takvim_buyuk.png"
    card.render_card(context, str(out_path), template_name="calendar_card.html", screenshot_selector="#calendar-card")

    width, height = _png_dimensions(out_path)
    assert width + height <= 10_000
