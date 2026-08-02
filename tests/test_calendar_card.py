"""src/render/calendar_card.py testleri (Faz 13).

build_calendar_context()/build_calendar_share_text() saf fonksiyonlardir --
src.fetchers.earnings_calendar'a hicbir AG istegi atmaz, elle kurulmus
EarningsDate listeleri kullanilir (bkz. Kural 11: testlerde ag istegi
atilmaz). Sadece test_render_calendar_card_gercek_png_uretir GERCEK
Playwright render'i dogrular (card.py'deki AYNI desen, bkz. test_card.py
test_render_card_gercek_png_uretir).
"""

from __future__ import annotations

from datetime import date, datetime

from src.fetchers.earnings_calendar import CONFIDENCE_KESIN, CONFIDENCE_SON_TARIH, CONFIDENCE_TAHMINI, EarningsDate
from src.render import calendar_card, card

_NOW = datetime(2026, 8, 2, 10, 0)


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


# --- build_calendar_context -----------------------------------------------------


def test_build_calendar_context_son_tarih_dislanir() -> None:
    context = calendar_card.build_calendar_context(_ornek_entries(), "BIST", now=_NOW)

    all_tickers = {row["ticker"] for group in context["day_groups"] for row in group["rows"]}
    assert all_tickers == {"THYAO", "ASELS", "TUPRS"}
    assert "KCHOL" not in all_tickers


def test_build_calendar_context_tarihe_gore_gruplar() -> None:
    context = calendar_card.build_calendar_context(_ornek_entries(), "BIST", now=_NOW)

    assert len(context["day_groups"]) == 2  # 2 ve 5 agustos
    ilk_gun = context["day_groups"][0]
    assert {row["ticker"] for row in ilk_gun["rows"]} == {"THYAO", "ASELS"}
    ikinci_gun = context["day_groups"][1]
    assert {row["ticker"] for row in ikinci_gun["rows"]} == {"TUPRS"}


def test_build_calendar_context_bugun_isaretlenir() -> None:
    context = calendar_card.build_calendar_context(_ornek_entries(), "BIST", now=_NOW)

    assert context["day_groups"][0]["is_today"] is True
    assert context["day_groups"][1]["is_today"] is False


def test_build_calendar_context_badge_eslemesi() -> None:
    context = calendar_card.build_calendar_context(_ornek_entries(), "BIST", now=_NOW)
    rows_by_ticker = {row["ticker"]: row for group in context["day_groups"] for row in group["rows"]}

    assert rows_by_ticker["THYAO"]["badge_class"] == "kesin"
    assert rows_by_ticker["THYAO"]["badge_label"] == "KESİN"
    assert rows_by_ticker["ASELS"]["badge_class"] == "tahmini"
    assert rows_by_ticker["ASELS"]["badge_label"] == "TAHMİNİ"


def test_build_calendar_context_bos_liste_is_empty() -> None:
    context = calendar_card.build_calendar_context([], "BIST", now=_NOW)
    assert context["is_empty"] is True
    assert context["day_groups"] == []


def test_build_calendar_context_sadece_son_tarih_varsa_is_empty() -> None:
    entries = [_entry("KCHOL", "Koç Holding", date(2026, 8, 20), CONFIDENCE_SON_TARIH)]
    context = calendar_card.build_calendar_context(entries, "BIST", now=_NOW)
    assert context["is_empty"] is True


def test_build_calendar_context_max_rows_kirpar() -> None:
    """CANLI hata (2026-08-02): NASDAQ 10 gunluk pencerede 2287 kayit dondurdu,
    Chromium bu kadar satirli bir #calendar-card'in ekran goruntusunu ALAMADI.
    max_rows bu yuzden ZORUNLU bir tavan -- asan kisim kesilir, truncated_count
    ile raporlanir."""
    entries = [_entry(f"T{i}", f"Şirket {i}", date(2026, 8, 2), CONFIDENCE_KESIN) for i in range(5)]
    context = calendar_card.build_calendar_context(entries, "BIST", now=_NOW, max_rows=3)

    shown = sum(len(g["rows"]) for g in context["day_groups"])
    assert shown == 3
    assert context["is_truncated"] is True
    assert context["truncated_count"] == 2
    assert context["is_empty"] is False


def test_build_calendar_context_max_rows_gun_sinirinda_keser() -> None:
    """Tavan bir gunun ORTASINA denk gelirse o gun KISMEN gosterilir, bir
    SONRAKI gunun TAMAMI hic eklenmez (bkz. build_calendar_context docstring'i)."""
    entries = [
        _entry("A", "A Şirketi", date(2026, 8, 2), CONFIDENCE_KESIN),
        _entry("B", "B Şirketi", date(2026, 8, 2), CONFIDENCE_KESIN),
        _entry("C", "C Şirketi", date(2026, 8, 3), CONFIDENCE_KESIN),
    ]
    context = calendar_card.build_calendar_context(entries, "BIST", now=_NOW, max_rows=1)

    assert len(context["day_groups"]) == 1
    assert len(context["day_groups"][0]["rows"]) == 1
    assert context["truncated_count"] == 2


def test_build_calendar_context_max_rows_asilmazsa_kirpma_yok() -> None:
    context = calendar_card.build_calendar_context(_ornek_entries(), "BIST", now=_NOW, max_rows=60)
    assert context["is_truncated"] is False
    assert context["truncated_count"] == 0


def test_build_calendar_context_lejant_iki_madde_icerir() -> None:
    """Kullanici karari: son_tarih hic gosterilmedigi icin lejant da SADECE
    kesin/tahmini aciklar (ucuncu, hic gorunmeyen bir rozet icin madde YOK)."""
    context = calendar_card.build_calendar_context(_ornek_entries(), "BIST", now=_NOW)
    assert [item["css_class"] for item in context["legend_items"]] == ["kesin", "tahmini"]


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


# --- build_calendar_share_text -----------------------------------------------------


def test_build_calendar_share_text_ticker_ve_tarihleri_icerir() -> None:
    context = calendar_card.build_calendar_context(_ornek_entries(), "BIST", now=_NOW)
    text = calendar_card.build_calendar_share_text(context)

    assert "$THYAO" in text
    assert "$ASELS" in text
    assert "$TUPRS" in text
    assert "$KCHOL" not in text
    assert "(BUGÜN)" in text
    assert "yatırım tavsiyesi değildir" in text


def test_build_calendar_share_text_bos_liste_mesaji() -> None:
    context = calendar_card.build_calendar_context([], "BIST", now=_NOW)
    text = calendar_card.build_calendar_share_text(context)
    assert "bulunamadı" in text


def test_build_calendar_share_text_kirpilmissa_not_ekler() -> None:
    entries = [_entry(f"T{i}", f"Şirket {i}", date(2026, 8, 2), CONFIDENCE_KESIN) for i in range(5)]
    context = calendar_card.build_calendar_context(entries, "BIST", now=_NOW, max_rows=3)
    text = calendar_card.build_calendar_share_text(context)
    assert "+2 kayıt daha" in text


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
