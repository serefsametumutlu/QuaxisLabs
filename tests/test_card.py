"""Faz 6 teslim kriteri: context olusturma/bicimlendirme mantiginin (hizli,
Playwright'siz) testleri + gercek bir PNG ureten TEK uctan uca entegrasyon
testi (bu, chromium baslatir, digerlerinden yavastir).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from src.ai.commentary import Commentary
from src.analysis import calculator, scorer
from src.fetchers import kap
from src.render import card


# --- _quarter_label -----------------------------------------------------


@pytest.mark.parametrize(
    "period,beklenen",
    [((2026, 3), "1Ç26"), ((2026, 6), "2Ç26"), ((2026, 9), "3Ç26"), ((2026, 12), "4Ç26"), ((2025, 3), "1Ç25")],
)
def test_quarter_label(period, beklenen) -> None:
    assert card._quarter_label(period) == beklenen


# --- _line_item_row -----------------------------------------------------


def test_line_item_row_artis_pozitif_renk_ve_yuzde() -> None:
    item = calculator.LineItemChange(
        label_tr="Hasılat", current=Decimal("1200"), comparison=Decimal("1000"),
        percent_change=Decimal("20"), change_label=calculator.ChangeLabel.ARTIS,
    )
    row = card._line_item_row(item)
    assert row["color_class"] == "positive"
    assert row["change_display"] == "%20,0"
    assert "1.200" in row["current"] or "mn" in row["current"] or "₺" in row["current"]


def test_line_item_row_negatif_yuzde_yatay_etiketle_bile_kirmizidir() -> None:
    """Kullanici geri bildirimi: yuzdenin ISARETI belirleyicidir -- YATAY
    (|degisim|<%5) etiketi olsa bile yuzde EKSI ise kirmizi gosterilmeli,
    aksi halde "bazi negatifler kirmizi bazilari gri" gorunumu ortaya cikar."""
    item = calculator.LineItemChange(
        label_tr="Finansal Borçlar", current=Decimal("600"), comparison=Decimal("620"),
        percent_change=Decimal("-3.2"), change_label=calculator.ChangeLabel.YATAY,
    )
    row = card._line_item_row(item)
    assert row["change_display"] == "%-3,2"
    assert row["color_class"] == "negative"


def test_line_item_row_net_borc_azalis_lower_is_better_ile_yesildir() -> None:
    # Canli hata (kullanici raporu, Fintables karsilastirmasi): Net Borc
    # icin AZALIS (daha az borc/daha fazla net nakit) IYI haberdir, ama
    # lower_is_better olmadan yuzde EKSI oldugu icin KIRMIZI gosteriliyordu
    # -- Fintables ayni durumu (net borc %-103, daha da negatife/net nakde
    # gitmis) DOGRU sekilde YESIL gosteriyordu. card.render_card_context
    # net_debt satirini lower_is_better=True ile cagirir (bkz. cagiran yer).
    item = calculator.LineItemChange(
        label_tr="Net Borç", current=Decimal("-146336672263"), comparison=Decimal("-72087836879"),
        percent_change=Decimal("-102.99"), change_label=calculator.ChangeLabel.SERT_DUSUS,
    )
    row = card._line_item_row(item, lower_is_better=True)
    assert row["color_class"] == "positive"
    # lower_is_better OLMADAN (varsayilan) ayni veri hala eski (yanlis) gibi kirmizi cikar --
    # bu da parametrenin GERCEKTEN isareti ters cevirdigini kanitlar.
    assert card._line_item_row(item)["color_class"] == "negative"


def test_line_item_row_zarardan_kara_gecti_sadece_etiket_gosterir() -> None:
    # Canli TERA hatasi: gecis durumlarinda ek bir yuzde ((guncel-onceki)/
    # |onceki|*100) daha once gosteriliyordu, ama guncel deger onceki
    # DEGERE GORE cok kucuk kaldiginda bu formul buyuklukten BAGIMSIZ olarak
    # neredeyse HER ZAMAN ~%100 uretiyordu (bkz. calculator.py TERA notu) --
    # bilgi degeri yok, hatta yanlis bir "yaklasik %100 degisim" izlenimi
    # veriyordu. Artik SADECE etiket gosterilir, ek yuzde YOKTUR.
    item = calculator.LineItemChange(
        label_tr="Net Dönem Kârı", current=Decimal("260"), comparison=Decimal("-80"),
        percent_change=None, change_label=calculator.ChangeLabel.ZARARDAN_KARA_GECTI,
    )
    row = card._line_item_row(item)
    assert row["change_display"] == calculator.ChangeLabel.ZARARDAN_KARA_GECTI
    assert row["color_class"] == "positive"


def test_line_item_row_kara_karsin_zarar_sadece_etiket_gosterir() -> None:
    item = calculator.LineItemChange(
        label_tr="Esas Faaliyet Kârı", current=Decimal("-8.6"), comparison=Decimal("92.2"),
        percent_change=None, change_label=calculator.ChangeLabel.KARA_KARSIN_ZARAR,
    )
    row = card._line_item_row(item)
    assert row["change_display"] == calculator.ChangeLabel.KARA_KARSIN_ZARAR
    assert row["color_class"] == "negative"


def test_line_item_row_none_deger_tire_gosterir() -> None:
    item = calculator.LineItemChange(
        label_tr="FAVÖK", current=None, comparison=None,
        percent_change=None, change_label=calculator.ChangeLabel.VERI_YOK,
    )
    row = card._line_item_row(item)
    assert row["current"] == "—"
    assert row["comparison"] == "—"
    assert "None" not in row["current"]
    assert "None" not in row["change_display"]


def test_line_item_row_zarar_devam_ederse_degisim_kirmizi_deger_notr() -> None:
    # DEGISIM sutunu (color_class) icin: zarar hala suruyorsa (YATAY =
    # degisim kucuk) notr/gri degil, kirmizi gosterilmeli. GUNCEL DEGER
    # (value_class) icin ise CANLI hata (kullanici raporu, Net Borc/TERA):
    # guncel donem HER ZAMAN duz/beyaz olmali, isaretine gore kirmiziya
    # boyanmamali -- eskiden "zarar varsa kirmizi olmali" idi, bu kural artik
    # SADECE Degisim sutununa (color_class) uygulanir.
    item = calculator.LineItemChange(
        label_tr="Net Dönem Kârı", current=Decimal("-84"), comparison=Decimal("-80"),
        percent_change=Decimal("-5"), change_label=calculator.ChangeLabel.YATAY,
    )
    row = card._line_item_row(item)
    assert row["color_class"] == "negative"
    assert row["value_class"] == ""


def test_line_item_row_kar_yatay_pozitif_yuzde_yesildir() -> None:
    item = calculator.LineItemChange(
        label_tr="Net Dönem Kârı", current=Decimal("84"), comparison=Decimal("80"),
        percent_change=Decimal("5"), change_label=calculator.ChangeLabel.YATAY,
    )
    row = card._line_item_row(item)
    assert row["color_class"] == "positive"
    assert row["value_class"] == ""


def test_line_item_row_yatay_tam_sifir_yuzde_notrdur() -> None:
    item = calculator.LineItemChange(
        label_tr="Net Dönem Kârı", current=Decimal("80"), comparison=Decimal("80"),
        percent_change=Decimal("0"), change_label=calculator.ChangeLabel.YATAY,
    )
    row = card._line_item_row(item)
    assert row["color_class"] == "neutral"


def test_line_item_row_pozitif_deger_value_class_bos() -> None:
    item = calculator.LineItemChange(
        label_tr="Hasılat", current=Decimal("1200"), comparison=Decimal("1000"),
        percent_change=Decimal("20"), change_label=calculator.ChangeLabel.ARTIS,
    )
    row = card._line_item_row(item)
    assert row["value_class"] == ""


# --- _valuation_context -----------------------------------------------------


def test_valuation_context_none_ise_none_doner() -> None:
    assert card._valuation_context(None) is None


def test_valuation_context_degerler_bicimlenir() -> None:
    val = calculator.ValuationMetrics(
        price=Decimal("10"),
        share_capital=Decimal("1000"),
        market_cap=Decimal("10000"),
        net_debt=Decimal("100"),
        enterprise_value=Decimal("10100"),
        pe_ratio=Decimal("14.2"),
        pb_ratio=Decimal("1.9"),
        ev_ebitda=Decimal("8.3"),
        ev_revenue=Decimal("2.1"),
        price_to_operating_profit=Decimal("12.5"),
    )
    ctx = card._valuation_context(val)
    assert ctx["fk"] == "14,20"
    assert ctx["pd_dd"] == "1,90"
    assert ctx["fd_favok"] == "8,30"
    assert ctx["fd_hasilat"] == "2,10"
    assert ctx["pd_efk"] == "12,50"
    assert "None" not in ctx["piyasa_degeri"]


def test_valuation_context_ttm_carpanlari_none_ise_na_gosterir() -> None:
    # Fintables konvansiyonuyla tutarlilik: hesaplanamayan degerleme
    # carpanlari "—" degil "N/A" gostermeli (bkz. card._money_or_na/_ratio_or_na).
    val = calculator.ValuationMetrics(
        price=Decimal("10"), share_capital=Decimal("1000"), market_cap=Decimal("10000"),
        net_debt=None, enterprise_value=None, pe_ratio=None, pb_ratio=Decimal("2"),
        ev_ebitda=None, ev_revenue=None, price_to_operating_profit=None,
    )
    ctx = card._valuation_context(val)
    assert ctx["fk"] == "N/A"
    assert ctx["fd_favok"] == "N/A"


# --- _score_row -----------------------------------------------------


def test_score_row_none_skorda_na_gosterir() -> None:
    c = scorer.ComponentScore(
        name="Değerleme", score=None, weight_nominal=Decimal("20"), weight_effective=Decimal("0"),
        contribution=Decimal("0"), reasoning_tr="fiyat verisi girilmedi, bileşen atlandı.",
    )
    row = card._score_row(c)
    assert row["score"] == "N/A"
    assert row["contribution"] == "N/A"


def test_score_row_dolu_skorda_deger_ve_katki_gosterir() -> None:
    c = scorer.ComponentScore(
        name="Kaldıraç", score=Decimal("9.86"), weight_nominal=Decimal("20"), weight_effective=Decimal("20"),
        contribution=Decimal("1.972"), reasoning_tr="net borç/FAVÖK 0,1x, çok düşük kaldıraç.",
    )
    row = card._score_row(c)
    assert "9,9" in row["score"]
    assert row["contribution"] == "1,97"


# --- _score_display_context -----------------------------------------------------


def test_score_display_context_yeterli_veride_sayisal_skor_gosterilir() -> None:
    sonuc = scorer.ScoreResult(
        ticker="TESTAS", period=(2026, 3), template="sanayi_holding",
        total_score=Decimal("7.5"), badge="DENGELİ",
        data_coverage_pct=Decimal("80"), data_sufficient=True,
    )
    ctx = card._score_display_context(sonuc)
    assert ctx["score_data_sufficient"] is True
    assert ctx["score_total_display"] == "7,50"
    assert ctx["score_badge"] == "DENGELİ"
    assert ctx["score_badge_class"] == "dengeli"


def test_score_display_context_yetersiz_veride_sayisal_skor_GIZLENIR() -> None:
    """CANLI HATA (kullanici raporu, ASTS, §B17 -- ACİL): bilesenlerin
    buyuk cogunlugu "veri yok" iken bile sayisal bir skor ("10,00/10
    SAĞLAM") gosteriliyordu. data_sufficient=False oldugunda context
    ARTIK score_data_sufficient=False dondurur -- card.html bu bayrakla
    buyuk sayiyi TAMAMEN gizleyip sadece "YETERSİZ VERİ" rozetini gosterir."""
    sonuc = scorer.ScoreResult(
        ticker="ASTS", period=(2026, 3), template="sanayi_holding",
        total_score=Decimal("10"), badge=scorer.YETERSIZ_VERI_ROZETI,
        data_coverage_pct=Decimal("4"), data_sufficient=False,
    )
    ctx = card._score_display_context(sonuc)
    assert ctx["score_data_sufficient"] is False
    assert ctx["score_badge"] == scorer.YETERSIZ_VERI_ROZETI
    assert ctx["score_badge_class"] == "yetersiz"


def test_render_html_yetersiz_veride_sayisal_skor_html_disinda_kalir() -> None:
    sonuc = scorer.ScoreResult(
        ticker="ASTS", period=(2026, 3), template="sanayi_holding",
        total_score=Decimal("10"), badge=scorer.YETERSIZ_VERI_ROZETI,
        data_coverage_pct=Decimal("4"), data_sufficient=False,
    )
    analiz = calculator.analyze("TESTAS", _saglikli_finansallar())
    context = card.build_card_context(analiz, sonuc, _ornek_commentary())
    html = card.render_html(context)
    assert "YETERSİZ VERİ" in html
    assert "10,00" not in html


# --- _build_chart -----------------------------------------------------


def test_build_chart_pozitif_deger_ustte_negatif_altta() -> None:
    chart = card._build_chart("Net Kâr", [Decimal("-80"), Decimal("260")], ["1Ç25", "1Ç26"])
    assert chart["points"][0]["neg_pct"] > 0
    assert chart["points"][0]["pos_pct"] == 0
    assert chart["points"][1]["pos_pct"] > 0
    assert chart["points"][1]["neg_pct"] == 0


def test_build_chart_en_buyuk_mutlak_deger_100_yuzdeye_yakin() -> None:
    chart = card._build_chart("Hasılat", [Decimal("500"), Decimal("1000")], ["a", "b"])
    assert chart["points"][1]["pos_pct"] == 100


def test_build_chart_taban_bar_yuksekligi_uygulanir() -> None:
    # Cok kucuk bir deger bile min bar yuksekliginin altina dusmemeli.
    chart = card._build_chart("Hasılat", [Decimal("1"), Decimal("1000")], ["a", "b"])
    assert chart["points"][0]["pos_pct"] >= card._MIN_BAR_PCT


def test_build_chart_none_deger_tire_gosterir_cokmez() -> None:
    chart = card._build_chart("Hasılat", [None, Decimal("1000")], ["a", "b"])
    assert chart["points"][0]["display"] == "—"
    assert chart["points"][0]["pos_pct"] == 0


def test_build_chart_tum_degerler_none_cokmez() -> None:
    chart = card._build_chart("Hasılat", [None, None], ["a", "b"])
    assert all(p["display"] == "—" for p in chart["points"])


# --- _build_chart: y_axis_ticks (deger artik bar uzerine degil, SOL eksende,
# position:absolute + onceden hesaplanmis top_pct ile hizali) -----------------------------------------------------


def test_build_chart_y_axis_ticks_guzel_yuvarlak_araliklarla_uretilir() -> None:
    # max_abs=1000 icin 'guzel' adim 500 (bkz. card._nice_axis_step) -- 3 cizgi:
    # 1.000 / 500 / 0,0. Tik sayisi artik SABIT 4 degil, veriye gore degisir.
    chart = card._build_chart("Hasılat", [Decimal("500"), Decimal("1000")], ["a", "b"])
    assert len(chart["y_axis_ticks"]) == 3
    assert [t["label"] for t in chart["y_axis_ticks"]] == ["1.000", "500", "0,0"]


def test_build_chart_y_axis_ticks_en_ustte_max_en_altta_sifir() -> None:
    chart = card._build_chart("Hasılat", [Decimal("500"), Decimal("1000")], ["a", "b"])
    ticks = chart["y_axis_ticks"]
    assert ticks[0]["label"] == card._axis_tick_label(Decimal("1000"))
    assert ticks[0]["top_pct"] == 0
    assert ticks[-1]["label"] == "0,0"
    assert ticks[-1]["top_pct"] == 100


def test_build_chart_y_axis_ticks_veri_yoksa_bos_liste() -> None:
    chart = card._build_chart("Hasılat", [None, None], ["a", "b"])
    assert chart["y_axis_ticks"] == []


# --- _nice_axis_step (kullanici geri bildirimi: eksen etiketleri Fintables'daki
# gibi YUVARLAK sayilar olmali, ham max_abs'in kesirleri degil) -----------------------------------------------------


def test_nice_axis_step_1000_icin_500_adim_2_tik_uretir() -> None:
    step, tick_count = card._nice_axis_step(Decimal("1000"))
    assert step == Decimal("500")
    assert tick_count == 2


def test_nice_axis_step_260_icin_100_adim_3_tik_uretir() -> None:
    step, tick_count = card._nice_axis_step(Decimal("260"))
    assert step == Decimal("100")
    assert tick_count == 3


def test_nice_axis_step_sifir_veya_negatif_icin_sifir_doner() -> None:
    assert card._nice_axis_step(Decimal("0")) == (Decimal(0), 0)


def test_build_chart_current_value_en_son_noktayi_yansitir() -> None:
    chart = card._build_chart("Net Kâr", [Decimal("100"), Decimal("-50")], ["1Ç25", "1Ç26"])
    assert chart["current_value_display"] == chart["points"][-1]["display"]
    assert chart["current_value_class"] == "negative"


def test_build_chart_current_value_pozitifse_positive_sinifi() -> None:
    chart = card._build_chart("Net Kâr", [Decimal("-50"), Decimal("100")], ["1Ç25", "1Ç26"])
    assert chart["current_value_class"] == "positive"


def test_build_chart_current_value_veri_yoksa_notr() -> None:
    chart = card._build_chart("Net Kâr", [Decimal("100"), None], ["1Ç25", "1Ç26"])
    assert chart["current_value_class"] == "neutral"
    assert chart["current_value_display"] == "—"


def test_build_chart_y_axis_ticks_negatif_seride_axis_pxlerine_gore_hizali() -> None:
    """has_negative=True iken eksen (_AXIS_UPPER_PX + zero + _AXIS_LOWER_PX)
    uzerinden olceklenir -- sifir cizgisi tam UPPER/(UPPER+ZERO+LOWER)'da,
    en alttaki negatif tepe tam %100'de olmali (bkz. card.py
    _AXIS_UPPER_PX/_AXIS_LOWER_PX). Zero tick'i sabit bir indeksle DEGIL
    (tick sayisi artik veriye gore degisir, bkz. _nice_axis_step) etiketinden
    bulunur."""
    chart = card._build_chart("Net Kâr", [Decimal("1000"), Decimal("-1000")], ["a", "b"])
    ticks = chart["y_axis_ticks"]
    assert chart["has_negative"] is True
    zero_tick = next(t for t in ticks if t["label"] == "0,0")
    expected_zero_pct = card._AXIS_UPPER_PX / (card._AXIS_UPPER_PX + card._AXIS_ZERO_PX + card._AXIS_LOWER_PX) * 100
    assert round(zero_tick["top_pct"], 2) == round(expected_zero_pct, 2)
    assert round(ticks[-1]["top_pct"], 2) == 100.0


def test_axis_tick_label_sifir_virgul_sifir_doner() -> None:
    assert card._axis_tick_label(Decimal("0")) == "0,0"


def test_axis_tick_label_para_birimi_sembolu_icermez() -> None:
    label = card._axis_tick_label(Decimal("25000000000"))
    assert "₺" not in label
    assert "mr" in label


# --- build_card_context -----------------------------------------------------

_LATEST = (2026, 3)
_YOY_PRIOR = (2025, 3)
_QOQ_PRIOR = (2025, 12)
_TTM_3 = (2025, 9)
_TTM_4 = (2025, 6)


def _donem(revenue, gross, op, dep, net, cash, tr, assets, debt, equity, ca, stl) -> dict:
    # "_cum" (kumulatif/YTD) alanlari bu testlerde KASITLI OLARAK ceyreklik
    # alanla ayni deger tasir -- bkz. test_calculator.py::_sample_financials notu.
    d = {
        "revenue": Decimal(revenue), "revenue_cum": Decimal(revenue),
        "gross_profit": Decimal(gross), "gross_profit_cum": Decimal(gross),
        "operating_profit": Decimal(op), "operating_profit_cum": Decimal(op),
        # "operating_profit_ebitda_base"(_cum) KASITLI OLARAK "operating_profit"
        # ile AYNI deger tasir -- bkz. test_calculator.py::_sample_financials notu
        # (bu testler FAVOK formulunu dogruluyor, iki alan arasindaki gercek-veri
        # farkini degil).
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
        _TTM_3: _donem(1050, 430, 280, 56, 200, 320, 135, 4600, 680, 2700, 1650, 860),
        _TTM_4: _donem(980, 390, 250, 54, 175, 290, 125, 4400, 690, 2550, 1580, 840),
    }


def _banka_finansallari() -> calculator.FinancialsByPeriod:
    # depreciation_amortization YOK -- FAVOK hesaplanamaz (banka/sigorta senaryosu).
    return {
        _LATEST: _donem(1200, 500, 350, None, 260, 400, 150, 5000, 600, 3000, 1800, 900),
        _YOY_PRIOR: _donem(1000, 400, 260, None, 180, 300, 130, 4500, 700, 2600, 1600, 850),
    }


def _ornek_commentary() -> Commentary:
    return Commentary(
        headline="BAŞLIK", summary="Özet.", positives=["artış maddesi"], negatives=["azalış maddesi"],
        kap_note="KAP notu metni.", disclaimer_context=None, source="llm",
    )


def _ornek_disclosures() -> list[kap.Disclosure]:
    return [
        kap.Disclosure(
            date=datetime(2026, 7, 15), title="Önemli Bildirim", category="Özel Durum",
            summary="Önemli Bildirim", url="https://kap.org.tr/x", importance=kap.IMPORTANCE_HIGH,
            is_late=False, disclosure_index=1, stock_codes="TESTAS",
        ),
        kap.Disclosure(
            date=datetime(2026, 7, 10), title="Rutin Bildirim", category="Yatırımcı Bülteni",
            summary="Rutin Bildirim", url="https://kap.org.tr/y", importance=kap.IMPORTANCE_LOW,
            is_late=False, disclosure_index=2, stock_codes="TESTAS",
        ),
    ]


def test_build_card_context_sanayi_show_ebitda_true() -> None:
    analiz = calculator.analyze("TESTAS", _saglikli_finansallar())
    skor = scorer.score_industrial(analiz)
    context = card.build_card_context(analiz, skor, _ornek_commentary(), _ornek_disclosures())

    assert context["show_ebitda"] is True
    assert context["income_rows"]["ebitda"] is not None
    assert context["charts"]["ebitda"] is not None


def test_build_card_context_ebitda_yoksa_satir_na_ile_gorunur_grafik_gizlenir() -> None:
    """CANLI HATA (kullanici raporu, MSFT/ASTS, bkz. 06_BILINEN_SORUNLAR.md
    §A29/§B17): FAVOK hesaplanamadiginda (eksik amortisman verisi vb.) gelir
    tablosu satiri TAMAMEN GIZLENIYORDU (5 yerine 4 satir, kart eksik/dengesiz
    gorunuyordu). Artik satir HER ZAMAN gorunur ("—"/"veri yok" ile) --
    SADECE bos bir cubuk grafigi anlamsiz oldugu icin mini-grafik gizli kalir."""
    analiz = calculator.analyze("BANKAS", _banka_finansallari())
    skor = scorer.score_industrial(analiz)
    context = card.build_card_context(analiz, skor, _ornek_commentary())

    assert context["show_ebitda"] is False
    assert context["income_rows"]["ebitda"] is not None
    assert context["income_rows"]["ebitda"]["label"] == "FAVÖK"
    assert context["income_rows"]["ebitda"]["change_display"] == "veri yok"
    assert context["charts"]["ebitda"] is None


def test_build_card_context_sadece_onemli_bildirimler_ve_en_fazla_5() -> None:
    analiz = calculator.analyze("TESTAS", _saglikli_finansallar())
    skor = scorer.score_industrial(analiz)
    context = card.build_card_context(analiz, skor, _ornek_commentary(), _ornek_disclosures())

    assert len(context["disclosure_rows"]) == 1  # sadece IMPORTANCE_HIGH olan
    assert context["disclosure_rows"][0]["title"] == "Önemli Bildirim"


def test_build_card_context_fiyat_verilmezse_none() -> None:
    analiz = calculator.analyze("TESTAS", _saglikli_finansallar())
    skor = scorer.score_industrial(analiz)
    context = card.build_card_context(analiz, skor, _ornek_commentary())
    assert context["price_display"] is None


def test_build_card_context_fiyat_verilirse_iki_ondalikli_formatlanir() -> None:
    analiz = calculator.analyze("TESTAS", _saglikli_finansallar())
    skor = scorer.score_industrial(analiz)
    context = card.build_card_context(analiz, skor, _ornek_commentary(), price=Decimal("142.5"))
    assert context["price_display"] == "142,50 ₺"


def test_build_card_context_badge_class_eslemesi() -> None:
    analiz = calculator.analyze("TESTAS", _saglikli_finansallar())
    skor = scorer.score_industrial(analiz)
    context = card.build_card_context(analiz, skor, _ornek_commentary())
    assert context["score_badge_class"] == card._BADGE_CLASS[skor.badge]


def test_build_card_context_sector_template_sanayi() -> None:
    analiz = calculator.analyze("TESTAS", _saglikli_finansallar())
    skor = scorer.score_industrial(analiz)
    context = card.build_card_context(analiz, skor, _ornek_commentary())
    assert context["sector_template"] == "sanayi"


# --- build_bank_card_context (banka/UFRS) -----------------------------------------------------

_BANK_LATEST = (2026, 6)
_BANK_YOY_PRIOR = (2025, 6)


def _bank_donem(interest_income, interest_expense, net_fee_income, net_operating_profit, net_income,
                 loans, deposits, provisions, total_assets, equity) -> dict:
    return {
        "interest_income": Decimal(interest_income), "interest_income_cum": Decimal(interest_income),
        "interest_expense": Decimal(interest_expense), "interest_expense_cum": Decimal(interest_expense),
        "net_fee_income": Decimal(net_fee_income), "net_fee_income_cum": Decimal(net_fee_income),
        "net_operating_profit": Decimal(net_operating_profit), "net_operating_profit_cum": Decimal(net_operating_profit),
        "net_income": Decimal(net_income), "net_income_cum": Decimal(net_income),
        "loans": Decimal(loans), "deposits": Decimal(deposits),
        "provisions": Decimal(provisions),
        "total_assets": Decimal(total_assets), "equity": Decimal(equity),
    }


def _gercek_banka_finansallari() -> calculator.FinancialsByPeriod:
    return {
        _BANK_LATEST: _bank_donem(412, -294, 88, 64, 64, 2625, 3020, 0, 4412, 487),
        _BANK_YOY_PRIOR: _bank_donem(329, -266, 64, 54, 54, 2200, 2700, 0, 3800, 400),
    }


def test_build_bank_card_context_sector_template_banka() -> None:
    analiz = calculator.analyze_bank("GARAN", _gercek_banka_finansallari())
    skor = scorer.score_bank(analiz)
    context = card.build_bank_card_context(analiz, skor, _ornek_commentary())
    assert context["sector_template"] == "banka"
    assert context["show_ebitda"] is False


def test_build_bank_card_context_income_rows_banka_alanlarini_icerir() -> None:
    analiz = calculator.analyze_bank("GARAN", _gercek_banka_finansallari())
    skor = scorer.score_bank(analiz)
    context = card.build_bank_card_context(analiz, skor, _ornek_commentary())

    for key in ("interest_income", "interest_expense", "net_fee_income", "net_operating_profit", "net_income"):
        assert context["income_rows"][key] is not None
    # bkz. test_line_item_row_zarar_devam_ederse_degisim_kirmizi_deger_notr:
    # guncel donem degeri artik isaretine gore boyanmiyor.
    assert context["income_rows"]["interest_expense"]["value_class"] == ""


def test_build_bank_card_context_balance_rows_banka_alanlarini_icerir() -> None:
    analiz = calculator.analyze_bank("GARAN", _gercek_banka_finansallari())
    skor = scorer.score_bank(analiz)
    context = card.build_bank_card_context(analiz, skor, _ornek_commentary())

    for key in ("loans", "deposits", "provisions", "total_assets", "equity"):
        assert context["balance_rows"][key] is not None


def test_build_bank_card_context_charts_uc_seri_icerir() -> None:
    analiz = calculator.analyze_bank("GARAN", _gercek_banka_finansallari())
    skor = scorer.score_bank(analiz)
    context = card.build_bank_card_context(analiz, skor, _ornek_commentary())

    assert set(context["charts"]) == {"net_interest_income", "net_income", "loans"}
    assert context["charts"]["net_interest_income"]["title"] == "Net Faiz Geliri"
    assert context["charts"]["loans"]["title"] == "Krediler"


def test_build_bank_card_context_valuation_sadece_fk_pddd() -> None:
    analiz = calculator.analyze_bank("GARAN", _gercek_banka_finansallari())
    skor = scorer.score_bank(analiz)
    valuation = calculator.compute_valuation_bank(analiz, price=Decimal("126.30"), share_capital=Decimal("4200"))
    context = card.build_bank_card_context(analiz, skor, _ornek_commentary(), valuation=valuation)

    assert set(context["valuation"]) == {"piyasa_degeri", "fk", "pd_dd"}


# --- build_insurance_card_context (sigorta/UFRS_K) -----------------------------------------------------

_INS_LATEST = (2026, 6)
_INS_YOY_PRIOR = (2025, 6)


def _insurance_donem(gross_written_premiums, net_premiums_earned, technical_income, technical_balance, net_income,
                      cash_and_financial_assets, receivables, provisions, payables, equity) -> dict:
    return {
        "gross_written_premiums": Decimal(gross_written_premiums), "gross_written_premiums_cum": Decimal(gross_written_premiums),
        "net_premiums_earned": Decimal(net_premiums_earned), "net_premiums_earned_cum": Decimal(net_premiums_earned),
        "technical_income": Decimal(technical_income), "technical_income_cum": Decimal(technical_income),
        "technical_balance": Decimal(technical_balance), "technical_balance_cum": Decimal(technical_balance),
        "net_income": Decimal(net_income), "net_income_cum": Decimal(net_income),
        "cash_and_financial_assets": Decimal(cash_and_financial_assets),
        "receivables_from_operations": Decimal(receivables),
        "technical_provisions": Decimal(provisions),
        "payables_from_operations": Decimal(payables),
        "equity": Decimal(equity),
    }


def _gercek_sigorta_finansallari() -> calculator.FinancialsByPeriod:
    return {
        _INS_LATEST: _insurance_donem(54190, 41664, 54903, 9301, 7397, 99868, 27212, 84812, 14703, 40046),
        _INS_YOY_PRIOR: _insurance_donem(44469, 33738, 37827, 6673, 5220, 85000, 22000, 75000, 12000, 32000),
    }


def test_build_insurance_card_context_sector_template_sigorta() -> None:
    analiz = calculator.analyze_insurance("ANSGR", _gercek_sigorta_finansallari())
    skor = scorer.score_insurance(analiz)
    context = card.build_insurance_card_context(analiz, skor, _ornek_commentary())
    assert context["sector_template"] == "sigorta"
    assert context["show_ebitda"] is False


def test_build_insurance_card_context_income_rows_sigorta_alanlarini_icerir() -> None:
    analiz = calculator.analyze_insurance("ANSGR", _gercek_sigorta_finansallari())
    skor = scorer.score_insurance(analiz)
    context = card.build_insurance_card_context(analiz, skor, _ornek_commentary())

    for key in ("gross_written_premiums", "net_premiums_earned", "technical_income", "technical_balance", "net_income"):
        assert context["income_rows"][key] is not None


def test_build_insurance_card_context_balance_rows_sigorta_alanlarini_icerir() -> None:
    analiz = calculator.analyze_insurance("ANSGR", _gercek_sigorta_finansallari())
    skor = scorer.score_insurance(analiz)
    context = card.build_insurance_card_context(analiz, skor, _ornek_commentary())

    for key in ("cash_and_financial_assets", "receivables_from_operations", "technical_provisions", "payables_from_operations", "equity"):
        assert context["balance_rows"][key] is not None


def test_build_insurance_card_context_charts_uc_seri_icerir() -> None:
    analiz = calculator.analyze_insurance("ANSGR", _gercek_sigorta_finansallari())
    skor = scorer.score_insurance(analiz)
    context = card.build_insurance_card_context(analiz, skor, _ornek_commentary())

    assert set(context["charts"]) == {"gross_written_premiums", "technical_balance", "net_income"}
    assert context["charts"]["gross_written_premiums"]["title"] == "Prim Üretimi"
    assert context["charts"]["technical_balance"]["title"] == "Teknik Denge"


def test_build_insurance_card_context_valuation_sadece_fk_pddd() -> None:
    analiz = calculator.analyze_insurance("ANSGR", _gercek_sigorta_finansallari())
    skor = scorer.score_insurance(analiz)
    valuation = calculator.compute_valuation_insurance(analiz, price=Decimal("27.18"), share_capital=Decimal("2000"))
    context = card.build_insurance_card_context(analiz, skor, _ornek_commentary(), valuation=valuation)

    assert set(context["valuation"]) == {"piyasa_degeri", "fk", "pd_dd"}


# --- render_html (Playwright'siz, sadece Jinja2) -----------------------------------------------------


def test_render_html_sanayi_favok_metnini_icerir() -> None:
    analiz = calculator.analyze("TESTAS", _saglikli_finansallar())
    skor = scorer.score_industrial(analiz)
    context = card.build_card_context(analiz, skor, _ornek_commentary())
    html = card.render_html(context)
    assert "FAVÖK" in html
    assert "TESTAS" in html
    assert "None" not in html


def test_render_html_ebitda_yoksa_satir_na_ile_gorunur_grafik_gizlenir() -> None:
    # NOT: scorer'in "Nakit Üretimi (FAVÖK)" bilesen ADI skor tablosunda her
    # zaman gorunur (skoru "—" olsa bile) -- bu beklenen davranis. Burada
    # ozel olarak dogrulanan: FAVOK hesaplanamadiginda (§B17) GELIR TABLOSU
    # satiri "N/A" ile HER ZAMAN render edilir, SADECE mini grafik
    # (show_ebitda=False oldugunda) hic render EDILMEZ.
    analiz = calculator.analyze("BANKAS", _banka_finansallari())
    skor = scorer.score_industrial(analiz)
    context = card.build_card_context(analiz, skor, _ornek_commentary())
    html = card.render_html(context)
    assert '<td class="label-cell">FAVÖK</td>' in html  # gelir tablosu satiri HER ZAMAN gorunur
    assert '<span class="mini-chart-title">FAVÖK</span>' not in html  # mini grafik basligi gizli


def test_render_html_kap_notu_yoksa_bolumu_gizler() -> None:
    analiz = calculator.analyze("TESTAS", _saglikli_finansallar())
    skor = scorer.score_industrial(analiz)
    commentary_kapsiz = Commentary(
        headline="BAŞLIK", summary="Özet.", positives=[], negatives=[],
        kap_note=None, disclaimer_context=None, source="llm",
    )
    context = card.build_card_context(analiz, skor, commentary_kapsiz)
    html = card.render_html(context)
    assert "KAP NOTU" not in html


# --- render_card: gercek Playwright ile PNG uretimi (uctan uca) -----------------------------------------------------


def test_render_card_gercek_png_uretir(tmp_path) -> None:
    analiz = calculator.analyze("TESTAS", _saglikli_finansallar())
    skor = scorer.score_industrial(analiz, valuation=scorer.ValuationInput(pe_ratio=Decimal("14.2"), pb_ratio=Decimal("1.9")))
    context = card.build_card_context(analiz, skor, _ornek_commentary(), _ornek_disclosures(), price=Decimal("142.5"))

    out_path = tmp_path / "test_card.png"
    result = card.render_card(context, str(out_path))

    assert result == str(out_path)
    assert out_path.exists()
    assert out_path.stat().st_size > 1000  # bos/kirik bir dosya degil
    assert out_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"  # gecerli PNG imzasi
