"""src/render/fundamental_screens_card.py testleri (Faz 21 - Değerleme kartı).

build_fundamental_screens_context() saf bir fonksiyondur -- HİÇBİR AĞ isteği
atmaz, elle kurulmuş bir FundamentalScreens kullanılır (test_technical_card.py
ile AYNI ilke). SADECE test_render_* GERÇEK Playwright render'i doğrular."""

from __future__ import annotations

from decimal import Decimal

from src.analysis.fundamental_screens import (
    AcquirersMultipleResult,
    FundamentalScreens,
    GrahamResult,
    GreenblattResult,
    PiotroskiResult,
)
from src.render import card, fundamental_screens_card


def _screens(**overrides) -> FundamentalScreens:
    defaults = dict(
        has_data=True,
        graham=GrahamResult(
            graham_multiple=Decimal(10), fair_value_price=Decimal(150), upside_pct=Decimal(50), verdict="Graham Ölçütüne Göre Ucuz"
        ),
        greenblatt=GreenblattResult(
            ebit=Decimal(26000),
            enterprise_value=Decimal(130000),
            earnings_yield_pct=Decimal(20),
            earnings_yield_band="Yüksek",
            net_working_capital=Decimal(15000),
            net_fixed_assets=Decimal(25000),
            return_on_capital_pct=Decimal(65),
            return_on_capital_band="Yüksek",
        ),
        acquirers_multiple=AcquirersMultipleResult(acquirers_multiple=Decimal(5), band="Ucuz"),
        piotroski=PiotroskiResult(
            score=8,
            criteria_evaluated=9,
            band="Güçlü",
            details=[("Aktif Kârlılığı (ROA) Pozitif", True), ("Aktif Devir Hızı Arttı (Verimlilik)", False), ("Bilinmeyen Kriter", None)],
        ),
    )
    defaults.update(overrides)
    return FundamentalScreens(**defaults)


# --- build_fundamental_screens_context -----------------------------------------------------


def test_uygulanabilir_ve_veri_varsa_tum_bolumler_dolar() -> None:
    ctx = fundamental_screens_card.build_fundamental_screens_context(
        _screens(), "THYAO", applicable=True, company_name="Türk Hava Yolları A.O.", price=Decimal(314)
    )
    assert ctx["has_data"] is True
    assert ctx["applicable"] is True
    assert ctx["graham"]["verdict_class"] == "positive"
    assert ctx["graham"]["multiple_display"] == "10,00"
    assert ctx["greenblatt"]["earnings_yield_class"] == "positive"
    assert ctx["acquirers_multiple"]["band_class"] == "positive"
    assert ctx["piotroski"]["score_display"] == "8"
    assert ctx["piotroski"]["details"][0]["icon"] == "✓"
    assert ctx["piotroski"]["details"][0]["icon_class"] == "positive"
    assert ctx["piotroski"]["details"][1]["icon"] == "✗"
    assert ctx["piotroski"]["details"][1]["icon_class"] == "negative"
    assert ctx["piotroski"]["details"][2]["icon"] == "—"
    assert ctx["piotroski"]["details"][2]["icon_class"] == "neutral"


def test_uygulanamaz_sirket_turu_has_data_false() -> None:
    ctx = fundamental_screens_card.build_fundamental_screens_context(None, "AKBNK", applicable=False)
    assert ctx["applicable"] is False
    assert ctx["has_data"] is False


def test_veri_yoksa_has_data_false() -> None:
    bos = FundamentalScreens(has_data=False, graham=None, greenblatt=None, acquirers_multiple=None, piotroski=None)
    ctx = fundamental_screens_card.build_fundamental_screens_context(bos, "YENIHISSE", applicable=True)
    assert ctx["has_data"] is False
    assert ctx["graham"]["has_data"] is False


def test_pahali_ve_zayif_bantlar_negative_sinifina_esler() -> None:
    ctx = fundamental_screens_card.build_fundamental_screens_context(
        _screens(
            graham=GrahamResult(
                graham_multiple=Decimal(30), fair_value_price=Decimal(80), upside_pct=Decimal(-20), verdict="Graham Ölçütüne Göre Pahalı"
            ),
            acquirers_multiple=AcquirersMultipleResult(acquirers_multiple=Decimal(20), band="Pahalı"),
            piotroski=PiotroskiResult(score=2, criteria_evaluated=9, band="Zayıf", details=[("X", False)]),
        ),
        "TEST",
        applicable=True,
    )
    assert ctx["graham"]["verdict_class"] == "negative"
    assert ctx["graham"]["upside_class"] == "negative"
    assert ctx["acquirers_multiple"]["band_class"] == "negative"
    assert ctx["piotroski"]["band_class"] == "negative"


# --- Gercek Playwright render -----------------------------------------------------


def test_render_fundamental_screens_card_gercek_png_uretir(tmp_path):
    ctx = fundamental_screens_card.build_fundamental_screens_context(
        _screens(), "THYAO", applicable=True, company_name="Türk Hava Yolları A.O.", price=Decimal(314)
    )

    out_path = tmp_path / "test_degerleme.png"
    result = card.render_card(
        ctx, str(out_path), template_name="fundamental_screens_card.html", screenshot_selector="#fundamental-screens-card"
    )

    assert result == str(out_path)
    assert out_path.exists()
    assert out_path.stat().st_size > 1000
    assert out_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_fundamental_screens_card_uygulanamaz_durumda_da_cokmez(tmp_path):
    ctx = fundamental_screens_card.build_fundamental_screens_context(None, "AKBNK", applicable=False)

    out_path = tmp_path / "test_degerleme_uygulanamaz.png"
    card.render_card(ctx, str(out_path), template_name="fundamental_screens_card.html", screenshot_selector="#fundamental-screens-card")

    assert out_path.exists()
    assert out_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
