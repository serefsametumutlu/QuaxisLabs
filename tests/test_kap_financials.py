"""kap_financials.py icindeki saf mantik fonksiyonlarinin birim testleri.

Ag erisimi gerektiren find_latest_financial_report()/fetch_latest_xi29_financials()
bu dosyada test EDILMEZ. Burada sadece _infer_period_from_publish_date()
dogrulanir -- KAP'in kendi (year, kap_period) alanlarina GUVENMEDEN, bir
bildirimin publish_date'inden takvim ceyregini cikaran fonksiyon (bkz.
FinancialReportRef.period docstring'i).

Asagidaki (publish_date -> beklenen period) ciftleri UYDURULMADI -- canli
KAP API'sinden (POST /tr/api/disclosure/members/byCriteria, disclosureCategory
"FR") gercek BORSK ve TATGD bildirimleri cekilip elle dogrulandi:
  - BORSK (Bor Şeker) icin kap_period numaralandirmasi TATGD'den KAYMIŞ --
    kap_period=1, 30.07.2026'da yayinlanan rapor GERCEKTE 2Ç26 (Haziran)
    donemine ait (disclosure_index=1639748: XBRL context tarihleri
    "01.04.2026-30.06.2026", PDF eki "BORŞEKER 30.06.2026.pdf" ile
    dogrulandi) -- eski `kap_period * 3` formulu bunu YANLISLIKLA (2026,3)
    hesapliyordu (bkz. kap_financials.py FinancialReportRef.period docstring'i).
  - TATGD icin ayni gun (30.07.2026) yayinlanan rapor da 2Ç26 (disclosure_index=1639813,
    kodun modul docstring'inde referans verilen ayni bildirim).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from src.fetchers.kap_financials import (
    _extract_presentation_currency_scale,
    _infer_period_from_publish_date,
    parse_financial_report,
)


def test_borsk_30_temmuz_yayini_haziran_donemi_olarak_cikarilir() -> None:
    # disclosure_index=1639748, kap_period=1 (TATGD'den FARKLI anlam tasiyor) --
    # eski formul (kap_period*3) bunu yanlislikla (2026,3) hesapliyordu.
    publish_date = datetime(2026, 7, 30, 18, 15, 54)
    assert _infer_period_from_publish_date(publish_date) == (2026, 6)


def test_tatgd_30_temmuz_yayini_haziran_donemi_olarak_cikarilir() -> None:
    # disclosure_index=1639813, kap_period=2 -- bu sirket icin eski formul
    # zaten dogruydu (2*3=6); yeni fonksiyon da ayni sonucu vermeli.
    publish_date = datetime(2026, 7, 30, 19, 0, 51)
    assert _infer_period_from_publish_date(publish_date) == (2026, 6)


def test_tatgd_mayis_yayini_mart_donemi_olarak_cikarilir() -> None:
    publish_date = datetime(2026, 5, 5, 18, 18, 42)
    assert _infer_period_from_publish_date(publish_date) == (2026, 3)


def test_borsk_mayis_yayini_mart_donemi_olarak_cikarilir() -> None:
    publish_date = datetime(2026, 5, 22, 18, 27, 14)
    assert _infer_period_from_publish_date(publish_date) == (2026, 3)


def test_borsk_ocak_yayini_bir_onceki_yilin_aralik_donemi_olarak_cikarilir() -> None:
    # Yil siniri gecisi: Ocak'ta yayinlanan rapor bir ONCEKI yilin Aralik
    # (yillik) donemine ait olmali.
    publish_date = datetime(2026, 1, 30, 18, 14, 29)
    assert _infer_period_from_publish_date(publish_date) == (2025, 12)


def test_cok_erken_yayin_min_lag_esigini_gecemiyorsa_bir_onceki_ceyrege_duser() -> None:
    # Ceyrek sonundan hemen sonra (min_lag_days=14 esiginin ALTINDA) yayinlanmis
    # gibi imkansiz bir durum -- bir onceki ceyrege duşmeli, gelecege sarkmamali.
    publish_date = datetime(2026, 7, 5, 12, 0, 0)  # 30 Haziran'dan sadece 5 gun sonra
    assert _infer_period_from_publish_date(publish_date) == (2026, 3)


# --- _extract_presentation_currency_scale / parse_financial_report olcekleme -----------------------------------------------------
#
# Canli hata (kullanici raporu): OTKAR icin sermaye 120.000.000 yerine
# 120.000 olarak kaydedildi -- KAP sayfasi "Sunum Para Birimi" alaninda
# sirkete gore "TL", "1.000 TL" veya "1.000.000 TL" bildirebiliyor, eski
# parser bunu hic OKUMUYORDU. Asagidaki 3 deger CANLI dogrulandi: TATGD=TL,
# OTKAR=1.000 TL, YKBNK(konsolide)=1.000.000 TL.


def _header_html(unit: str, *, js_escaped: bool = False) -> str:
    if js_escaped:
        return f"...Sunum Para Birimi\\u003c/td\\u003e\\r\\n\\u003ctd\\u003e{unit}\\u003c/td\\u003e..."
    return f"...<td>Sunum Para Birimi</td><td>{unit}</td>..."


def test_extract_presentation_currency_scale_tl_ise_bir_doner() -> None:
    assert _extract_presentation_currency_scale(_header_html("TL")) == Decimal(1)


def test_extract_presentation_currency_scale_bin_tl_ise_bin_doner() -> None:
    # canli OTKAR degeri
    assert _extract_presentation_currency_scale(_header_html("1.000 TL")) == Decimal(1000)


def test_extract_presentation_currency_scale_milyon_tl_ise_milyon_doner() -> None:
    # canli YKBNK (konsolide) degeri
    assert _extract_presentation_currency_scale(_header_html("1.000.000 TL")) == Decimal(1_000_000)


def test_extract_presentation_currency_scale_js_escaped_bicimde_de_calisir() -> None:
    # gercek KAP sayfasindaki bicim: bilgi DOM'da degil, </> kacisli
    # bir JS/JSON metin blogunda yer aliyor (canli 3 sirkette dogrulandi).
    assert _extract_presentation_currency_scale(_header_html("1.000 TL", js_escaped=True)) == Decimal(1000)


def test_extract_presentation_currency_scale_bulunamazsa_guvenli_varsayilana_duser() -> None:
    assert _extract_presentation_currency_scale("<html>sunum para birimi bilgisi yok</html>") == Decimal(1)


def _sample_row_html(tag: str, values: list[str], unit: str) -> str:
    cells = "".join(
        f'<td class="taxonomy-context-value"><span class="taxonomy-label-field" title="{v}"></span></td>'
        for v in values
    )
    return f"""
    <html>
    {_header_html(unit)}
    <table>
      <tr class="data-input-row">
        <td class="taxonomy-field-name">{tag}|Aciklama</td>
        {cells}
      </tr>
    </table>
    </html>
    """


def test_parse_financial_report_bin_tl_olcegini_degerlere_uygular() -> None:
    # canli OTKAR hatasinin regresyon testi: sermaye 120000 (ham) -> 120000000 (olceklenmis)
    html = _sample_row_html("ifrs-full_IssuedCapital", ["120000", "120000"], "1.000 TL")
    raw = parse_financial_report(html, "OTKAR", 1, (2026, 6))
    assert raw.balance_value("ifrs-full_IssuedCapital") == Decimal("120000000")


def test_parse_financial_report_tl_biriminde_olcek_uygulanmaz() -> None:
    html = _sample_row_html("ifrs-full_IssuedCapital", ["500000", "500000"], "TL")
    raw = parse_financial_report(html, "TATGD", 1, (2026, 6))
    assert raw.balance_value("ifrs-full_IssuedCapital") == Decimal("500000")


# --- Banka (UFRS) destegi: 6 kolonlu bilanco duzeni + Konsolide/Solo ayrimi -----------------------------------------------------
#
# Asagidaki degerler CANLI YKBNK konsolide raporuyla (disclosure_index=1639924,
# 31.07.2026) dogrulandi -- Fintables'in gosterdigi konsolide rakamlarla
# (Krediler, Mevduatlar, Ozkaynaklar, Beklenen Zarar Karsiliklari, Faiz
# Gelirleri/Giderleri, Net Ucret Komisyon Geliri, Net Faaliyet Kari, Net
# Donem Kari) TL'ye kadar birebir eslesti.


def test_raw_kap_financials_balance_value_6_kolonda_indeks_2yi_kullanir() -> None:
    # 6 kolon: [TP_cari, YP_cari, TOPLAM_cari, TP_onceki, YP_onceki, TOPLAM_onceki]
    from src.fetchers.kap_financials import RawKapFinancials

    raw = RawKapFinancials(
        ticker="YKBNK", disclosure_index=1, period=(2026, 6),
        balance_sheet_items={"kap-fr_Loans": [Decimal(1453759), Decimal(728602), Decimal(2182361), Decimal(1255138), Decimal(642167), Decimal(1897305)]},
        income_statement_items={},
    )
    assert raw.balance_value("kap-fr_Loans") == Decimal(2182361)


def test_raw_kap_financials_balance_value_2_kolonda_indeks_0i_kullanir_geriye_donuk_uyumlu() -> None:
    from src.fetchers.kap_financials import RawKapFinancials

    raw = RawKapFinancials(
        ticker="TATGD", disclosure_index=1, period=(2026, 6),
        balance_sheet_items={"ifrs-full_Assets": [Decimal(500000), Decimal(400000)]},
        income_statement_items={},
    )
    assert raw.balance_value("ifrs-full_Assets") == Decimal(500000)


def _variant_header_html(variant: str) -> str:
    return f"...<td>Finansal Tablo Niteliği</td><td>{variant}</td>..."


def test_report_variant_konsolideyi_dogru_okur() -> None:
    from src.fetchers.kap_financials import _report_variant

    assert _report_variant(_variant_header_html("Konsolide")) == "Konsolide"


def test_report_variant_konsolide_olmayani_karistirmaz() -> None:
    # "Konsolide" alternatifi listede ONCE gelse bile "Konsolide Olmayan"in
    # bir ONEKI olarak yanlislikla eslesmemeli (alternation sirasi onemli).
    from src.fetchers.kap_financials import _report_variant

    assert _report_variant(_variant_header_html("Konsolide Olmayan")) == "Konsolide Olmayan"


def test_report_variant_bulunamazsa_none_doner() -> None:
    from src.fetchers.kap_financials import _report_variant

    assert _report_variant("<html>bilgi yok</html>") is None


def _bank_income_row_html(tag: str, cur_cum: str, prior_cum: str, cur_q: str, prior_q: str) -> str:
    values = [cur_cum, prior_cum, cur_q, prior_q]
    cells = "".join(
        f'<td class="taxonomy-context-value"><span class="taxonomy-label-field" title="{v}"></span></td>'
        for v in values
    )
    return f"""
    <html>
    {_header_html("1.000.000 TL")}
    <table>
      <tr class="data-input-row">
        <td class="taxonomy-field-name">{tag}|Aciklama</td>
        {cells}
      </tr>
    </table>
    </html>
    """


def test_parse_financial_report_banka_gelir_tablosu_kumulatif_ve_ceyreklik_dogru_okunur() -> None:
    # canli YKBNK degerleri (milyon TL): Faiz Gelirleri 2Ç26 kumulatif=360009, 2Ç25 kumulatif=281230
    html = _bank_income_row_html("kap-fr_InterestIncome", "360009", "281230", "186459", "146147")
    raw = parse_financial_report(html, "YKBNK", 1, (2026, 6), balance_column_count=6)
    assert raw.income_cum_value("kap-fr_InterestIncome") == Decimal(360009) * Decimal(1_000_000)
    assert raw.income_quarterly_value("kap-fr_InterestIncome") == Decimal(186459) * Decimal(1_000_000)


def _bank_balance_row_html(tag: str, values: list[str]) -> str:
    cells = "".join(
        f'<td class="taxonomy-context-value"><span class="taxonomy-label-field" title="{v}"></span></td>'
        for v in values
    )
    return f"""
    <html>
    {_header_html("1.000.000 TL")}
    <table>
      <tr class="data-input-row">
        <td class="taxonomy-field-name">{tag}|Aciklama</td>
        {cells}
      </tr>
    </table>
    </html>
    """


def test_parse_financial_report_banka_bilancosu_6_kolon_cari_toplami_dogru_okur() -> None:
    # canli YKBNK Krediler (milyon TL): [TP,YP,TOPLAM_cari,TP,YP,TOPLAM_onceki]
    html = _bank_balance_row_html("kap-fr_Loans", ["1453759", "728602", "2182361", "1255138", "642167", "1897305"])
    raw = parse_financial_report(html, "YKBNK", 1, (2026, 6), balance_column_count=6)
    assert raw.balance_value("kap-fr_Loans") == Decimal(2182361) * Decimal(1_000_000)


def test_standardized_record_values_ufrs_tum_alanlari_uretir() -> None:
    from src.fetchers.kap_financials import STANDARD_ITEM_MAP_KAP_UFRS_BALANCE, STANDARD_ITEM_MAP_KAP_UFRS_INCOME, standardized_record_values_ufrs
    from src.fetchers.kap_financials import RawKapFinancials

    balance_items = {tag: [Decimal(1), Decimal(1), Decimal(100), Decimal(1), Decimal(1), Decimal(90)] for tag in STANDARD_ITEM_MAP_KAP_UFRS_BALANCE.values()}
    income_items = {tag: [Decimal(400), Decimal(300), Decimal(200), Decimal(150)] for tag in STANDARD_ITEM_MAP_KAP_UFRS_INCOME.values()}
    raw = RawKapFinancials(ticker="YKBNK", disclosure_index=1, period=(2026, 6), balance_sheet_items=balance_items, income_statement_items=income_items)

    values = standardized_record_values_ufrs(raw)
    for field in STANDARD_ITEM_MAP_KAP_UFRS_BALANCE:
        assert values[field] == Decimal(100)
    for field in STANDARD_ITEM_MAP_KAP_UFRS_INCOME:
        assert values[f"{field}_cum"] == Decimal(400)
        assert values[field] == Decimal(200)


# --- CANLI hata duzeltmesi (kullanici raporu, SAHOL PD/DD -- bkz.
# STANDARD_ITEM_MAP_KAP_XI_29_BALANCE["equity"] yorumu): IFRS taksonomisinde
# "ifrs-full_Equity" TOPLAM (azinlik dahil) ozkaynak tag'idir --
# "ifrs-full_EquityAttributableToOwnersOfParent" (ana ortaklik-only) VE
# "ifrs-full_NoncontrollingInterests" (azinlik payi) AYRI tag'lerdir (CANLI
# dogrulandi: TUPRS_kap_1643116.html'de UCU de MEVCUT) -----------------------------------------------------


def test_standard_item_map_kap_xi_29_equity_artik_ana_ortaklik_only_tagi() -> None:
    from src.fetchers.kap_financials import STANDARD_ITEM_MAP_KAP_XI_29_BALANCE

    assert STANDARD_ITEM_MAP_KAP_XI_29_BALANCE["equity"] == "ifrs-full_EquityAttributableToOwnersOfParent"
    assert STANDARD_ITEM_MAP_KAP_XI_29_BALANCE["equity_total"] == "ifrs-full_Equity"
    assert STANDARD_ITEM_MAP_KAP_XI_29_BALANCE["minority_interest"] == "ifrs-full_NoncontrollingInterests"


def test_standardized_record_values_equity_parent_only_ve_total_ayri_okunur() -> None:
    """SAHOL benzeri (buyuk azinlik payli) bir sirket senaryosu: parent-only
    ve TOPLAM ozkaynak tag'leri FARKLI degerler tasidiginda birbirine
    KARISMAMALI."""
    from src.fetchers.kap_financials import STANDARD_ITEM_MAP_KAP_XI_29_BALANCE, RawKapFinancials, standardized_record_values

    balance_items = {
        "ifrs-full_EquityAttributableToOwnersOfParent": [Decimal(382411470000), Decimal(0)],
        "ifrs-full_Equity": [Decimal(625852441000), Decimal(0)],
        "ifrs-full_NoncontrollingInterests": [Decimal(243440971000), Decimal(0)],
    }
    raw = RawKapFinancials(ticker="SAHOL", disclosure_index=1, period=(2026, 3), balance_sheet_items=balance_items, income_statement_items={})

    values = standardized_record_values(raw)
    assert values["equity"] == Decimal(382411470000)
    assert values["equity_total"] == Decimal(625852441000)
    assert values["minority_interest"] == Decimal(243440971000)


# --- operating_profit_ebitda_base (FAVOK'un dar-kavram girdisi, canli OTKAR/TERA hatasinin regresyon testi) -----------------------------------------------------
#
# Degerler CANLI TOASO 2026/6 Finansal Rapor'undan (disclosure_index=1639026)
# alindi -- Is Yatirim'in kendi bildirdigi "3H" (Net Faaliyet Kar/Zarari)
# degeriyle (1.850.359.000) TAM eslesti.


def test_standardized_record_values_favok_dar_kavrami_3_tagden_turetir() -> None:
    from src.fetchers.kap_financials import RawKapFinancials, standardized_record_values

    income_items = {
        "ifrs-full_ProfitLossFromOperatingActivities": [Decimal(2884353000), Decimal(0), Decimal(2884353000), Decimal(0)],
        "ifrs-full_OtherIncome": [Decimal(5118124000), Decimal(0), Decimal(5118124000), Decimal(0)],
        "ifrs-full_OtherExpenseByFunction": [Decimal(-4084130000), Decimal(0), Decimal(-4084130000), Decimal(0)],
    }
    raw = RawKapFinancials(ticker="TOASO", disclosure_index=1, period=(2026, 6), balance_sheet_items={}, income_statement_items=income_items)

    values = standardized_record_values(raw)
    assert values["operating_profit_ebitda_base_cum"] == Decimal(1850359000)
    assert values["operating_profit_ebitda_base"] == Decimal(1850359000)


def test_standardized_record_values_favok_bilesenlerden_biri_eksikse_none_doner() -> None:
    """Kural 8: GENIS kavrama (3DF) sessizce dusmek YANLIS (ama makul
    gorunen) bir FAVOK rakami uretir -- bilesenlerden biri eksikse None
    donmeli, GENIS deger DEGIL."""
    from src.fetchers.kap_financials import RawKapFinancials, standardized_record_values

    income_items = {
        "ifrs-full_ProfitLossFromOperatingActivities": [Decimal(2884353000), Decimal(0), Decimal(2884353000), Decimal(0)],
        # ifrs-full_OtherIncome / OtherExpenseByFunction bu sirkette hic raporlanmamis.
    }
    raw = RawKapFinancials(ticker="TEST", disclosure_index=1, period=(2026, 6), balance_sheet_items={}, income_statement_items=income_items)

    values = standardized_record_values(raw)
    assert values["operating_profit_ebitda_base_cum"] is None
    assert values["operating_profit_ebitda_base"] is None
