"""isyatirim.py icindeki saf mantik fonksiyonlarinin birim testleri.

Ag erisimi gerektiren fetch_financials() bu dosyada test EDILMEZ (bkz.
scripts/demo_fetch.py -- canli veriyle calisan Faz 2 teslim kriteri
scripti). Burada sadece disariya bagimliligi olmayan hesaplamalar
dogrulanir.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.fetchers.isyatirim import (
    FinancialItem,
    STANDARD_ITEM_MAP_FINANSMAN,
    STANDARD_ITEM_MAP_UFRS,
    STANDARD_ITEM_MAP_UFRS_K,
    STANDARD_ITEM_MAP_UFRS_KATILIM,
    UnsupportedFinancialGroupError,
    _merge_items,
    _parse_decimal,
    _resolve_actual_group,
    _rows_to_items,
    cash_and_financial_assets_ufrs_k,
    guess_last_periods,
    normalize_company_code,
    previous_period,
    quarterly_standardized_value_ufrs,
    quarterly_standardized_value_ufrs_k,
    quarterly_standardized_value_ufrs_katilim,
    quarterly_technical_balance_ufrs_k,
    quarterly_value_from_cumulative,
    standardized_value_ufrs,
    standardized_value_ufrs_k,
    standardized_value_ufrs_katilim,
    standardized_value_financing,
    quarterly_standardized_value_financing,
    technical_balance_ufrs_k,
    technical_provisions_ufrs_k,
    total_debt,
    total_revenue,
    quarterly_total_revenue,
    sga_expense,
    quarterly_sga_expense,
    standardized_value,
    quarterly_standardized_value,
    RawFinancials,
    STANDARD_ITEM_MAP_XI_29,
)


# --- STANDARD_ITEM_MAP_XI_29: THYAO canli kesif yanitiyla dogrulanan kodlar -----------------------------------------------------
# (bkz. data/exploration/thyao_items_readable.txt) -- bu alanlar onceden
# haritada YOKTU (kart "Ticari Alacaklar" satiri her zaman "veri yok"
# gosteriyordu); regresyonu kilitler.


def test_standard_item_map_trade_receivables_dogru_kod() -> None:
    assert STANDARD_ITEM_MAP_XI_29["trade_receivables"] == "1AC"


def test_standard_item_map_current_assets_dogru_kod() -> None:
    assert STANDARD_ITEM_MAP_XI_29["current_assets"] == "1A"


def test_standard_item_map_share_capital_dogru_kod() -> None:
    assert STANDARD_ITEM_MAP_XI_29["share_capital"] == "2OA"


# --- CANLI hata duzeltmesi (kullanici raporu, SAHOL PD/DD Fintables/Matriks'e
# gore YANLIS cikiyordu): "equity" TOPLAM ozkaynak (azinlik dahil, "2N")
# yerine ARTIK ana ortaklik-only ("2O") doner (bkz. data/exploration/
# SAHOL_XI_29_get_20260812_190310.json ve thyao_items_readable.txt satir
# 58-69 canli dogrulamasi: 2N = 2O + 2ODA ozdesligi) -----------------------------------------------------


def test_standard_item_map_equity_artik_ana_ortaklik_only() -> None:
    assert STANDARD_ITEM_MAP_XI_29["equity"] == "2O"


def test_standard_item_map_equity_total_toplam_ozkaynagi_korur() -> None:
    """Eski "equity" degeri (TOPLAM, azinlik dahil) bilgi kaybi olmasin diye
    "equity_total" adiyla AYRICA saklanir (Kural 8)."""
    assert STANDARD_ITEM_MAP_XI_29["equity_total"] == "2N"


def test_standard_item_map_minority_interest_dogru_kod() -> None:
    assert STANDARD_ITEM_MAP_XI_29["minority_interest"] == "2ODA"


def test_standardized_value_xi_29_equity_sahol_canli_degerleriyle_dogrulanir() -> None:
    """CANLI dogrulandi (2026-08-12, data/exploration/SAHOL_XI_29_get_20260812_190310.json):
    2N (Ozkaynaklar TOPLAM) = 625.852.441.000, 2O (Ana Ortakliga Ait
    Ozkaynaklar) = 382.411.470.000, 2ODA (Azinlik Paylari) = 243.440.971.000
    -- 2O + 2ODA == 2N ozdesligi TL'ye kadar dogrulandi. Bu, kullanicinin
    raporladigi PD/DD hatasinin (eski "equity"=2N ile PD/DD=0,294 iken
    duzeltilmis "equity"=2O ile PD/DD=0,481 -- Fintables/Matriks'e daha
    YAKIN) kok nedenidir."""
    period = (2026, 3)
    items = {
        "2N": FinancialItem("2N", "Özkaynaklar", {period: Decimal("625852441000")}),
        "2O": FinancialItem("2O", "Ana Ortaklığa Ait Özkaynaklar", {period: Decimal("382411470000")}),
        "2ODA": FinancialItem("2ODA", "Azınlık Payları", {period: Decimal("243440971000")}),
    }
    raw = RawFinancials(ticker="SAHOL", company_code="SAHOL", financial_group="XI_29", periods=[period], items=items)
    from src.fetchers.isyatirim import standardized_value

    assert standardized_value(raw, "equity", period) == Decimal("382411470000")
    assert standardized_value(raw, "equity_total", period) == Decimal("625852441000")
    assert standardized_value(raw, "minority_interest", period) == Decimal("243440971000")
    # Ozdeslik: equity + minority_interest == equity_total
    assert standardized_value(raw, "equity", period) + standardized_value(raw, "minority_interest", period) == standardized_value(
        raw, "equity_total", period
    )


def test_standard_item_map_pretax_profit_dogru_kod() -> None:
    """V-07 (docs/spec/spec_veri_tamlik_yol_haritasi.md) -- "3I" ("SÜRDÜRÜLEN
    FAALİYETLER VERGİ ÖNCESİ KARI (ZARARI)"), THYAO VE BIMAS (İKİ BAĞIMSIZ
    XI_29 şirketi) canlı kesif yanitiyla dogrulandi (bkz.
    data/exploration/thyao_items_readable.txt satir 98, BIMAS_XI_29_get_*.json)."""
    assert STANDARD_ITEM_MAP_XI_29["pretax_profit"] == "3I"


def test_standard_item_map_tax_provision_dogru_kod() -> None:
    assert STANDARD_ITEM_MAP_XI_29["tax_provision"] == "3IA"


def test_pretax_profit_xi_29_ceyreklestirme_diger_alanlarla_ayni_ilkeyi_kullanir() -> None:
    """V-07 -- "3I" digerleri (Satislar/Brut Kar) gibi KUMULATIF (YTD)
    -- quarterly_standardized_value() ile AYNI cikarma ilkesiyle
    ceyreklestirilebilmeli (regresyon: CUMULATIVE_FIELDS'e eklenmedi ise
    bu test HAM kumulatif degeri yanlislikla doner)."""
    items = {
        STANDARD_ITEM_MAP_XI_29["pretax_profit"]: FinancialItem(
            item_code=STANDARD_ITEM_MAP_XI_29["pretax_profit"], description_tr="Vergi Öncesi Kâr",
            values_by_period={(2026, 6): Decimal("300"), (2026, 3): Decimal("120")},
        ),
    }
    raw = RawFinancials(ticker="THYAO", company_code="THYAO", financial_group="XI_29", periods=[(2026, 6), (2026, 3)], items=items)
    from src.fetchers.isyatirim import quarterly_standardized_value, standardized_value

    assert standardized_value(raw, "pretax_profit", (2026, 6)) == Decimal("300")
    assert quarterly_standardized_value(raw, "pretax_profit", (2026, 6)) == Decimal("300") - Decimal("120")


# --- V-10/V-11/V-12 (docs/spec/spec_veri_tamlik_yol_haritasi.md) -- BIST
# Capex/Temettu/Finansman Faaliyetleri, thyao_items_readable.txt (satir
# 132/136/137) ile CANLI dogrulanan itemCode'lar -----------------------------------------------------


def test_standard_item_map_capex_dogru_kod() -> None:
    assert STANDARD_ITEM_MAP_XI_29["capex"] == "4CAI"


def test_standard_item_map_dividends_paid_dogru_kod() -> None:
    assert STANDARD_ITEM_MAP_XI_29["dividends_paid"] == "4CBB"


def test_standard_item_map_net_financing_debt_change_dogru_kod() -> None:
    assert STANDARD_ITEM_MAP_XI_29["net_financing_debt_change"] == "4CBA"


def test_standardized_value_capex_negatiften_pozitife_cevrilir() -> None:
    """Is Yatirim capex'i nakit CIKISI icin NEGATIF isaretle raporlar
    (THYAO CANLI: -20.125.000.000) -- NASDAQ'taki "us-gaap:PaymentsTo
    AcquirePropertyPlantAndEquipment" POZITIF buyukluk kullandigi icin
    (calculator.py'nin PIYASA-BAGIMSIZ capex_to_net_income_pct rasyosunun
    TUTARLI calismasi icin) BURADA pozitife cevrilir."""
    period = (2026, 6)
    item_code = STANDARD_ITEM_MAP_XI_29["capex"]
    raw = RawFinancials(
        ticker="THYAO", company_code="THYAO", financial_group="XI_29", periods=[period],
        items={item_code: FinancialItem(item_code, "Sabit Sermaye Yatırımları", {period: Decimal("-20125000000")})},
    )
    from src.fetchers.isyatirim import standardized_value

    assert standardized_value(raw, "capex", period) == Decimal("20125000000")


def test_standardized_value_dividends_paid_negatiften_pozitife_cevrilir() -> None:
    period = (2026, 6)
    item_code = STANDARD_ITEM_MAP_XI_29["dividends_paid"]
    raw = RawFinancials(
        ticker="TUPRS", company_code="TUPRS", financial_group="XI_29", periods=[period],
        items={item_code: FinancialItem(item_code, "Temettü Ödemeleri", {period: Decimal("-21402951")})},
    )
    from src.fetchers.isyatirim import standardized_value

    assert standardized_value(raw, "dividends_paid", period) == Decimal("21402951")


def test_standardized_value_net_financing_debt_change_isareti_korunur() -> None:
    """"4CBA" ZATEN NET (ihrac - geri odeme) bir rakamdir, isareti
    ANLAMLIDIR -- capex/dividends_paid'in AKSINE negatife/pozitife
    CEVRILMEMELI (Kural 8: emin olunmayan bir isaret varsayimi UYDURULMAZ)."""
    period = (2026, 6)
    item_code = STANDARD_ITEM_MAP_XI_29["net_financing_debt_change"]
    raw = RawFinancials(
        ticker="THYAO", company_code="THYAO", financial_group="XI_29", periods=[period],
        items={item_code: FinancialItem(item_code, "Finansal Borçlardaki Değişim", {period: Decimal("-9558000000")})},
    )
    from src.fetchers.isyatirim import standardized_value

    assert standardized_value(raw, "net_financing_debt_change", period) == Decimal("-9558000000")


def test_quarterly_standardized_value_capex_kumulatiften_ceyreklik_ve_pozitif() -> None:
    """Kumulatiften ceyreklik turetilirken de pozitif isaret korunmali
    (negatiflemeyle cikarma islemi degismez, bkz. quarterly_standardized_value
    docstring'i)."""
    q1, q2 = (2026, 3), (2026, 6)
    item_code = STANDARD_ITEM_MAP_XI_29["capex"]
    raw = RawFinancials(
        ticker="THYAO", company_code="THYAO", financial_group="XI_29", periods=[q1, q2],
        items={item_code: FinancialItem(item_code, "Sabit Sermaye Yatırımları", {q1: Decimal("-35408000000"), q2: Decimal("-51663000000")})},
    )
    from src.fetchers.isyatirim import quarterly_standardized_value

    # Ceyreklik (ham) = -51.663mn - (-35.408mn) = -16.255mn, pozitife cevrilmis hali +16.255mn
    assert quarterly_standardized_value(raw, "capex", q2) == Decimal("16255000000")


def test_normalize_company_code_strips_suffix_and_uppercases() -> None:
    assert normalize_company_code("THYAO.IS") == "THYAO"
    assert normalize_company_code("thyao") == "THYAO"
    assert normalize_company_code("  akbnk.is  ") == "AKBNK"


def test_previous_period_yil_basinda_none_doner() -> None:
    assert previous_period((2026, 3)) is None


def test_previous_period_yil_ici_dogru_hesaplar() -> None:
    assert previous_period((2026, 6)) == (2026, 3)
    assert previous_period((2026, 9)) == (2026, 6)
    assert previous_period((2026, 12)) == (2026, 9)


def test_previous_period_yil_donusu_dogru_hesaplar() -> None:
    assert previous_period((2026, 3)) is None
    assert previous_period((2025, 12)) == (2025, 9)


def test_previous_period_gecersiz_donem_hata_firlatir() -> None:
    with pytest.raises(ValueError):
        previous_period((2026, 5))


def test_quarterly_value_yil_basinda_cikarma_yapmaz() -> None:
    values = {(2026, 3): Decimal("100")}
    assert quarterly_value_from_cumulative(values, (2026, 3)) == Decimal("100")


def test_quarterly_value_onceki_donemden_cikarir() -> None:
    values = {(2026, 3): Decimal("100"), (2026, 6): Decimal("250")}
    assert quarterly_value_from_cumulative(values, (2026, 6)) == Decimal("150")


def test_quarterly_value_onceki_donem_yoksa_none_doner() -> None:
    values = {(2026, 6): Decimal("250")}
    assert quarterly_value_from_cumulative(values, (2026, 6)) is None


def test_quarterly_value_mevcut_donem_yoksa_none_doner() -> None:
    values = {(2026, 3): Decimal("100")}
    assert quarterly_value_from_cumulative(values, (2026, 6)) is None


def test_guess_last_periods_dogru_sayida_ve_sirada() -> None:
    periods = guess_last_periods(count=8)
    assert len(periods) == 8
    for year, period in periods:
        assert period in (3, 6, 9, 12)
    # Yeniden eskiye siralanmis olmali
    for i in range(len(periods) - 1):
        current_year, current_period = periods[i]
        next_year, next_period = periods[i + 1]
        assert (current_year, current_period) > (next_year, next_period)


def test_parse_decimal_bos_ve_none_degerler() -> None:
    assert _parse_decimal(None) is None
    assert _parse_decimal("") is None
    assert _parse_decimal("   ") is None


def test_parse_decimal_gecerli_sayi() -> None:
    assert _parse_decimal("485646000000") == Decimal("485646000000")
    assert _parse_decimal("-1818000000") == Decimal("-1818000000")


def test_parse_decimal_sayisal_olmayan_deger_none_doner() -> None:
    assert _parse_decimal("N/A") is None


def test_rows_to_items_deger_donem_eslemesi() -> None:
    rows = [
        {"itemCode": "3C", "itemDescTr": "Satis Gelirleri", "value1": "100", "value2": "80", "value3": "", "value4": None},
    ]
    periods = [(2026, 3), (2025, 12), (2025, 9), (2025, 6)]
    items = _rows_to_items(rows, periods)
    assert items["3C"].values_by_period == {(2026, 3): Decimal("100"), (2025, 12): Decimal("80")}


def test_merge_items_farkli_donemleri_birlestirir() -> None:
    base = {
        "3C": FinancialItem("3C", "Satis Gelirleri", {(2026, 3): Decimal("100")}),
    }
    extra = {
        "3C": FinancialItem("3C", "Satis Gelirleri", {(2025, 3): Decimal("50")}),
        "1BL": FinancialItem("1BL", "Toplam Varliklar", {(2025, 3): Decimal("1000")}),
    }
    merged = _merge_items(base, extra)
    assert merged["3C"].values_by_period == {(2026, 3): Decimal("100"), (2025, 3): Decimal("50")}
    assert merged["1BL"].values_by_period == {(2025, 3): Decimal("1000")}


def test_total_debt_iki_kalemi_toplar() -> None:
    period = (2026, 3)
    items = {
        STANDARD_ITEM_MAP_XI_29["short_term_financial_debt"]: FinancialItem(
            "2AA", "Kisa Vadeli Finansal Borclar", {period: Decimal("100")}
        ),
        STANDARD_ITEM_MAP_XI_29["long_term_financial_debt"]: FinancialItem(
            "2BA", "Uzun Vadeli Finansal Borclar", {period: Decimal("400")}
        ),
    }
    raw = RawFinancials(
        ticker="TEST", company_code="TEST", financial_group="XI_29", periods=[period], items=items
    )
    assert total_debt(raw, period) == Decimal("500")


def test_total_debt_hicbiri_yoksa_none_doner() -> None:
    period = (2026, 3)
    raw = RawFinancials(
        ticker="TEST", company_code="TEST", financial_group="XI_29", periods=[period], items={}
    )
    assert total_debt(raw, period) is None


# --- total_revenue / quarterly_total_revenue: finans segmentli sirketler (TOASO canli hatasi) -----------------------------------------------------


def test_total_revenue_finans_segmenti_varsa_3cac_ile_toplar() -> None:
    """Canli dogrulanan TOASO hatasi: '3C' (Satis Gelirleri) tek basina,
    bunyesinde finansman/leasing kolu olan sirketlerde Fintables'in
    "Satislar" kaleminden dusuk kaliyordu -- '3CAC' (Finans Sektoru
    Faaliyetlerinden Gelirler) DAHIL edilince TL'ye kadar eslesti."""
    h1 = (2026, 6)
    q1 = (2026, 3)
    items = {
        STANDARD_ITEM_MAP_XI_29["revenue"]: FinancialItem(
            item_code=STANDARD_ITEM_MAP_XI_29["revenue"], description_tr="Satis Gelirleri",
            values_by_period={h1: Decimal("201797108000"), q1: Decimal("95109919000")},
        ),
        "3CAC": FinancialItem(
            item_code="3CAC", description_tr="Faiz, Ucret, Prim, Komisyon ve Diger Gelirler",
            values_by_period={h1: Decimal("11346872000"), q1: Decimal("5000000000")},
        ),
    }
    raw = RawFinancials(ticker="TOASO", company_code="TOASO", financial_group="XI_29", periods=[h1, q1], items=items)

    assert total_revenue(raw, h1) == Decimal("213143980000")
    assert quarterly_total_revenue(raw, h1) == Decimal("213143980000") - Decimal("100109919000")


def test_total_revenue_finans_segmenti_yoksa_sadece_3c_doner() -> None:
    """Cogunluk sirketlerde '3CAC' hic raporlanmaz -- davranis eskisiyle AYNI kalmali."""
    period = (2026, 3)
    items = {
        STANDARD_ITEM_MAP_XI_29["revenue"]: FinancialItem(
            item_code=STANDARD_ITEM_MAP_XI_29["revenue"], description_tr="Satis Gelirleri",
            values_by_period={period: Decimal("1000")},
        ),
    }
    raw = RawFinancials(ticker="TEST", company_code="TEST", financial_group="XI_29", periods=[period], items=items)

    assert total_revenue(raw, period) == Decimal("1000")
    assert quarterly_total_revenue(raw, period) == Decimal("1000")


def test_total_revenue_hicbiri_yoksa_none_doner() -> None:
    period = (2026, 3)
    raw = RawFinancials(ticker="TEST", company_code="TEST", financial_group="XI_29", periods=[period], items={})
    assert total_revenue(raw, period) is None
    assert quarterly_total_revenue(raw, period) is None


# --- Kullanıcı isteği (2026-08-14): "N/A olan veri kalmasın" -- BİST XI_29'da
# hiç çekilmeyen SG&A/Ar-Ge/Faiz Gideri (bkz. STANDARD_ITEM_MAP_XI_29
# "3DC"/"4BB" ve sga_expense() "3DA"+"3DB" yorumları) ---------------------


def test_research_development_expense_negatiflenir() -> None:
    """Ham veride Ar-Ge Gideri "gider (-)" isaretiyle NEGATIF gelir (THYAO
    canli yaniti: v1=0, sanayi sirketlerinde dolu -- CANLI dogrulama
    referansi data/exploration/thyao_items_readable.txt satir 84) --
    standardized_value POZITIFE cevirmeli (capex/dividends_paid ILE AYNI teknik)."""
    period = (2026, 6)
    item_code = STANDARD_ITEM_MAP_XI_29["research_development_expense"]
    raw = RawFinancials(
        ticker="TEST", company_code="TEST", financial_group="XI_29", periods=[period],
        items={item_code: FinancialItem(item_code, "Arastirma ve Gelistirme Giderleri (-)", {period: Decimal("-500000")})},
    )
    assert standardized_value(raw, "research_development_expense", period) == Decimal("500000")


def test_interest_expense_xi29_negatiflenir() -> None:
    """Ham veride Finansman Giderleri (4BB) NEGATIF gelir (THYAO canli yaniti:
    v1=-14.407.000.000, bkz. data/exploration/thyao_items_readable.txt satir
    116) -- standardized_value POZITIFE cevirmeli."""
    period = (2026, 6)
    item_code = STANDARD_ITEM_MAP_XI_29["interest_expense"]
    raw = RawFinancials(
        ticker="TEST", company_code="TEST", financial_group="XI_29", periods=[period],
        items={item_code: FinancialItem(item_code, "Finansman Giderleri", {period: Decimal("-14407000000")})},
    )
    assert standardized_value(raw, "interest_expense", period) == Decimal("14407000000")


def test_sga_expense_iki_alt_kalemi_toplar_ve_pozitife_cevirir() -> None:
    """sga_expense() = "3DA" (Pazarlama/Satis/Dagitim) + "3DB" (Genel
    Yonetim) -- total_revenue()'nun "3C"+"3CAC" deseniyle AYNI teknik, ama
    her iki alt kalem de NEGATIF gelir (gider (-) isareti), toplam POZITIFE
    cevrilir."""
    h1, q1 = (2026, 6), (2026, 3)
    items = {
        "3DA": FinancialItem("3DA", "Pazarlama, Satis ve Dagitim Giderleri (-)", {h1: Decimal("-21121000000"), q1: Decimal("-10000000000")}),
        "3DB": FinancialItem("3DB", "Genel Yonetim Giderleri (-)", {h1: Decimal("-7544000000"), q1: Decimal("-3500000000")}),
    }
    raw = RawFinancials(ticker="THYAO", company_code="THYAO", financial_group="XI_29", periods=[h1, q1], items=items)

    assert sga_expense(raw, h1) == Decimal("28665000000")
    assert quarterly_sga_expense(raw, h1) == Decimal("28665000000") - Decimal("13500000000")


def test_sga_expense_sadece_bir_alt_kalem_varsa_onunla_calisir() -> None:
    period = (2026, 3)
    items = {"3DB": FinancialItem("3DB", "Genel Yonetim Giderleri (-)", {period: Decimal("-1000")})}
    raw = RawFinancials(ticker="TEST", company_code="TEST", financial_group="XI_29", periods=[period], items=items)
    assert sga_expense(raw, period) == Decimal("1000")
    assert quarterly_sga_expense(raw, period) == Decimal("1000")


def test_sga_expense_hicbiri_yoksa_none_doner() -> None:
    period = (2026, 3)
    raw = RawFinancials(ticker="TEST", company_code="TEST", financial_group="XI_29", periods=[period], items={})
    assert sga_expense(raw, period) is None
    assert quarterly_sga_expense(raw, period) is None


# --- STANDARD_ITEM_MAP_UFRS (banka): GARAN + AKBNK canli kesif yanitlariyla
# dogrulanan kodlar (bkz. data/exploration/GARAN_UFRS_get_*.json,
# akbnk_ufrs_items_readable.txt) -----------------------------------------------------


def _raw_ufrs(items: dict) -> RawFinancials:
    return RawFinancials(ticker="GARAN", company_code="GARAN", financial_group="UFRS", periods=list(items), items=items)


def test_standardized_value_ufrs_interest_expense_negatiflenir() -> None:
    """Ham veride Faiz Giderleri POZITIF buyukluk olarak gelir (GARAN canli
    yaniti: value1=293769000000); kart/rapor geleneginde gider satiri EKSI
    gosterilir (bkz. GARAN referans karti) -- standardized_value_ufrs bunu
    NEGATIFE cevirmeli."""
    period = (2026, 6)
    item_code = STANDARD_ITEM_MAP_UFRS["interest_expense"]
    raw = _raw_ufrs({item_code: FinancialItem(item_code, "FAIZ GIDERLERI", {period: Decimal("293769000000")})})
    assert standardized_value_ufrs(raw, "interest_expense", period) == Decimal("-293769000000")


def test_standardized_value_ufrs_diger_alanlar_negatiflenmez() -> None:
    period = (2026, 6)
    item_code = STANDARD_ITEM_MAP_UFRS["loans"]
    raw = _raw_ufrs({item_code: FinancialItem(item_code, "KREDILER", {period: Decimal("2624664000000")})})
    assert standardized_value_ufrs(raw, "loans", period) == Decimal("2624664000000")


def test_quarterly_standardized_value_ufrs_interest_expense_ceyreklik_ve_negatif() -> None:
    """Kumulatif (YTD) Faiz Giderleri'nden ceyreklik turetilirken de negatif
    isaret korunmali."""
    q1, q2 = (2026, 3), (2026, 6)
    item_code = STANDARD_ITEM_MAP_UFRS["interest_expense"]
    raw = _raw_ufrs(
        {item_code: FinancialItem(item_code, "FAIZ GIDERLERI", {q1: Decimal("150000000000"), q2: Decimal("293769000000")})}
    )
    # Ceyreklik = 2Ç kumulatif - 1Ç kumulatif = 293.769mn - 150.000mn = 143.769mn, negatiflenmis hali -143.769mn
    assert quarterly_standardized_value_ufrs(raw, "interest_expense", q2) == Decimal("-143769000000")


def test_quarterly_standardized_value_ufrs_bilanco_kalemi_ceyreklestirilmez() -> None:
    """loans (STOK deger) kumulatif -> ceyreklik donusumune TABI DEGILDIR --
    standardized_value_ufrs ile ayni sonucu dondurmeli."""
    period = (2026, 6)
    item_code = STANDARD_ITEM_MAP_UFRS["loans"]
    raw = _raw_ufrs({item_code: FinancialItem(item_code, "KREDILER", {period: Decimal("2624664000000")})})
    assert quarterly_standardized_value_ufrs(raw, "loans", period) == Decimal("2624664000000")


def test_standardized_value_ufrs_xi_29_semasinda_hata_firlatir() -> None:
    raw = RawFinancials(ticker="THYAO", company_code="THYAO", financial_group="XI_29", periods=[], items={})
    with pytest.raises(UnsupportedFinancialGroupError):
        standardized_value_ufrs(raw, "loans", (2026, 6))


# --- CANLI hata duzeltmesi (kullanici raporu, SAHOL PD/DD -- bkz.
# STANDARD_ITEM_MAP_UFRS["equity_total"] yorumu): bankada "2O" (XVI.
# OZKAYNAKLAR) TOPLAMdir, "16.5 Azinlik Paylari" (2OVA) onun ALT kalemidir
# -- "equity" bu yuzden equity_total - minority_interest olarak HESAPLANIR -----------------------------------------------------


def test_standard_item_map_ufrs_equity_total_dogru_kod() -> None:
    assert STANDARD_ITEM_MAP_UFRS["equity_total"] == "2O"


def test_standard_item_map_ufrs_minority_interest_dogru_kod() -> None:
    assert STANDARD_ITEM_MAP_UFRS["minority_interest"] == "2OVA"


def test_standardized_value_ufrs_equity_azinlik_payini_dusurur() -> None:
    period = (2026, 6)
    total_code = STANDARD_ITEM_MAP_UFRS["equity_total"]
    minority_code = STANDARD_ITEM_MAP_UFRS["minority_interest"]
    raw = _raw_ufrs(
        {
            total_code: FinancialItem(total_code, "XVI. ÖZKAYNAKLAR", {period: Decimal("487168000000")}),
            minority_code: FinancialItem(minority_code, "16.5 Azınlık Payları", {period: Decimal("5000000000")}),
        }
    )
    assert standardized_value_ufrs(raw, "equity", period) == Decimal("482168000000")


def test_standardized_value_ufrs_equity_azinlik_yoksa_toplama_esittir() -> None:
    """AKBNK/GARAN canli veride azinlik payi (2OVA) 0 -- minority_interest
    item'i hic raporlanmamissa (None/eksik) equity == equity_total olmali."""
    period = (2026, 6)
    total_code = STANDARD_ITEM_MAP_UFRS["equity_total"]
    raw = _raw_ufrs({total_code: FinancialItem(total_code, "XVI. ÖZKAYNAKLAR", {period: Decimal("302597564000")})})
    assert standardized_value_ufrs(raw, "equity", period) == Decimal("302597564000")


def test_standardized_value_ufrs_equity_toplam_yoksa_none_doner() -> None:
    """Kural 3: eksik veri = None yayilimi, 0 varsayilmaz."""
    period = (2026, 6)
    raw = _raw_ufrs({})
    assert standardized_value_ufrs(raw, "equity", period) is None


def test_quarterly_standardized_value_ufrs_equity_ceyreklestirilmez() -> None:
    """'equity' STOK bir hesaplamadir -- quarterly_standardized_value_ufrs
    ile standardized_value_ufrs AYNI sonucu dondurmeli (ceyreklik turetme
    UYGULANMAZ)."""
    period = (2026, 6)
    total_code = STANDARD_ITEM_MAP_UFRS["equity_total"]
    minority_code = STANDARD_ITEM_MAP_UFRS["minority_interest"]
    raw = _raw_ufrs(
        {
            total_code: FinancialItem(total_code, "XVI. ÖZKAYNAKLAR", {period: Decimal("487168000000")}),
            minority_code: FinancialItem(minority_code, "16.5 Azınlık Payları", {period: Decimal("5000000000")}),
        }
    )
    assert quarterly_standardized_value_ufrs(raw, "equity", period) == Decimal("482168000000")


# --- STANDARD_ITEM_MAP_FINANSMAN (Tasarruf Finansman Sirketi/XI_29K): KTLEV
# canli kesif yanitiyla dogrulanan kodlar (bkz. data/exploration/
# KTLEV_XI_29K_raw_2026Q1.json, KAP disclosure_index=1605385 ile net kar
# 3.361.411.828 birebir dogrulandi) -----------------------------------------------------


def _raw_financing(items: dict) -> RawFinancials:
    return RawFinancials(ticker="KTLEV", company_code="KTLEV", financial_group="XI_29K", periods=list(items), items=items)


def test_standardized_value_financing_net_income_gercek_ktlev_degeri() -> None:
    period = (2026, 3)
    item_code = STANDARD_ITEM_MAP_FINANSMAN["net_income"]
    raw = _raw_financing({item_code: FinancialItem(item_code, "NET DONEM KARI (ZARARI)", {period: Decimal("3361411828")})})
    assert standardized_value_financing(raw, "net_income", period) == Decimal("3361411828")


def test_standardized_value_financing_operating_expenses_isaret_degistirilmez() -> None:
    """Esas Faaliyet Giderleri ham veride ZATEN NEGATIF gelir (KTLEV canli
    yaniti: -1725631994) -- bankadaki 'interest_expense'in AKSINE burada
    isaret DONUSUMU yapilmaz, oldugu gibi tasinir."""
    period = (2026, 3)
    item_code = STANDARD_ITEM_MAP_FINANSMAN["operating_expenses"]
    raw = _raw_financing(
        {item_code: FinancialItem(item_code, "ESAS FAALIYET GIDERLERI (-)", {period: Decimal("-1725631994")})}
    )
    assert standardized_value_financing(raw, "operating_expenses", period) == Decimal("-1725631994")


def test_standard_item_map_financing_equity_artik_ana_ortaklik_only() -> None:
    """CANLI dogrulandi (data/exploration/KTLEV_XI_29K_raw_2026Q1.json):
    2N (Ozkaynaklar, TOPLAM) = 15.819.301.983, 2O (Ana Ortaklığa Ait
    Özkaynaklar) = 14.753.674.798, A2OE (13.5 Azinlik Paylari) =
    1.065.627.185 -- 2O + A2OE == 2N ozdesligi TL'ye kadar dogrulandi."""
    assert STANDARD_ITEM_MAP_FINANSMAN["equity"] == "2O"
    assert STANDARD_ITEM_MAP_FINANSMAN["equity_total"] == "2N"
    assert STANDARD_ITEM_MAP_FINANSMAN["minority_interest"] == "A2OE"


def test_standardized_value_financing_equity_ktlev_canli_degerleriyle_dogrulanir() -> None:
    period = (2026, 3)
    raw = _raw_financing(
        {
            "2N": FinancialItem("2N", "Özkaynaklar", {period: Decimal("15819301983")}),
            "2O": FinancialItem("2O", "Ana Ortaklığa Ait Özkaynaklar", {period: Decimal("14753674798")}),
            "A2OE": FinancialItem("A2OE", "13.5 Azınlık Payları", {period: Decimal("1065627185")}),
        }
    )
    assert standardized_value_financing(raw, "equity", period) == Decimal("14753674798")
    assert standardized_value_financing(raw, "equity_total", period) == Decimal("15819301983")
    assert standardized_value_financing(raw, "minority_interest", period) == Decimal("1065627185")


def test_quarterly_standardized_value_financing_bilanco_kalemi_ceyreklestirilmez() -> None:
    """total_assets (STOK deger) kumulatif -> ceyreklik donusumune TABI
    DEGILDIR -- standardized_value_financing ile ayni sonucu dondurmeli."""
    period = (2026, 3)
    item_code = STANDARD_ITEM_MAP_FINANSMAN["total_assets"]
    raw = _raw_financing({item_code: FinancialItem(item_code, "AKTIF TOPLAMI", {period: Decimal("56679474844")})})
    assert quarterly_standardized_value_financing(raw, "total_assets", period) == Decimal("56679474844")


def test_standardized_value_financing_bilinmeyen_alan_hata_firlatir() -> None:
    raw = _raw_financing({})
    with pytest.raises(KeyError):
        standardized_value_financing(raw, "loans", (2026, 3))


def test_standardized_value_financing_xi_29_semasinda_hata_firlatir() -> None:
    raw = RawFinancials(ticker="THYAO", company_code="THYAO", financial_group="XI_29", periods=[], items={})
    with pytest.raises(UnsupportedFinancialGroupError):
        standardized_value_financing(raw, "total_assets", (2026, 3))


# --- STANDARD_ITEM_MAP_UFRS_K (sigorta): ANSGR canli kesif yanitiyla
# dogrulanan kodlar (bkz. data/exploration/ANSGR_UFRS_K_get_*.json) --
# TUM degerler PROGRAMATIK olarak canli veriyle son haneye kadar dogrulandi. -----------------------------------------------------


def _raw_ufrs_k(items: dict) -> RawFinancials:
    return RawFinancials(ticker="ANSGR", company_code="ANSGR", financial_group="UFRS_K", periods=list(items), items=items)


def test_standardized_value_ufrs_k_prim_uretimi() -> None:
    period = (2026, 6)
    item_code = STANDARD_ITEM_MAP_UFRS_K["gross_written_premiums"]
    raw = _raw_ufrs_k({item_code: FinancialItem(item_code, "BRUT YAZILAN PRIMLER", {period: Decimal("54189705323")})})
    assert standardized_value_ufrs_k(raw, "gross_written_premiums", period) == Decimal("54189705323")


def test_technical_balance_ufrs_k_gelir_artı_gider_toplanir() -> None:
    """Teknik Denge = Teknik Gelir + Teknik Gider (Teknik Gider ham veride
    ZATEN negatif isaretle gelir, dogrudan toplanir). ANSGR ile canli
    dogrulandi: 54.903.467.315 + (-45.602.915.467) = 9.300.551.848."""
    period = (2026, 6)
    income_code = STANDARD_ITEM_MAP_UFRS_K["technical_income"]
    expense_code = STANDARD_ITEM_MAP_UFRS_K["technical_expense"]
    raw = _raw_ufrs_k(
        {
            income_code: FinancialItem(income_code, "TEKNIK GELIR", {period: Decimal("54903467315")}),
            expense_code: FinancialItem(expense_code, "TEKNIK GIDER", {period: Decimal("-45602915467")}),
        }
    )
    assert technical_balance_ufrs_k(raw, period) == Decimal("9300551848")


def test_cash_and_financial_assets_ufrs_k_iki_kalemi_toplar() -> None:
    """Nakit Benzeri Finansal Varliklar = Nakit (1A) + Finansal Varliklar (1B)
    -- ANSGR ile canli dogrulandi: 38.872.587.231 + 60.995.842.343 = 99.868.429.574."""
    period = (2026, 6)
    cash_code = STANDARD_ITEM_MAP_UFRS_K["cash_and_equivalents"]
    financial_code = STANDARD_ITEM_MAP_UFRS_K["financial_assets"]
    raw = _raw_ufrs_k(
        {
            cash_code: FinancialItem(cash_code, "NAKIT", {period: Decimal("38872587231")}),
            financial_code: FinancialItem(financial_code, "FINANSAL VARLIKLAR", {period: Decimal("60995842343")}),
        }
    )
    assert cash_and_financial_assets_ufrs_k(raw, period) == Decimal("99868429574")


def test_technical_provisions_ufrs_k_iki_kalemi_toplar() -> None:
    """Teknik Karsiliklar = kisa vadeli (2E) + uzun vadeli (2MD) -- ANSGR ile
    canli dogrulandi: 82.395.051.067 + 2.416.774.566 = 84.811.825.633."""
    period = (2026, 6)
    current_code = STANDARD_ITEM_MAP_UFRS_K["technical_provisions_current"]
    noncurrent_code = STANDARD_ITEM_MAP_UFRS_K["technical_provisions_noncurrent"]
    raw = _raw_ufrs_k(
        {
            current_code: FinancialItem(current_code, "TEKNIK KARSILIK KV", {period: Decimal("82395051067")}),
            noncurrent_code: FinancialItem(noncurrent_code, "TEKNIK KARSILIK UV", {period: Decimal("2416774566")}),
        }
    )
    assert technical_provisions_ufrs_k(raw, period) == Decimal("84811825633")


def test_quarterly_technical_balance_ufrs_k_ceyreklestirir() -> None:
    q1, q2 = (2026, 3), (2026, 6)
    income_code = STANDARD_ITEM_MAP_UFRS_K["technical_income"]
    expense_code = STANDARD_ITEM_MAP_UFRS_K["technical_expense"]
    raw = _raw_ufrs_k(
        {
            income_code: FinancialItem(
                income_code, "TEKNIK GELIR", {q1: Decimal("20000000000"), q2: Decimal("54903467315")}
            ),
            expense_code: FinancialItem(
                expense_code, "TEKNIK GIDER", {q1: Decimal("-15000000000"), q2: Decimal("-45602915467")}
            ),
        }
    )
    # Ceyreklik gelir = 54.903.467.315 - 20.000.000.000 = 34.903.467.315
    # Ceyreklik gider = -45.602.915.467 - (-15.000.000.000) = -30.602.915.467
    # Toplam = 34.903.467.315 + (-30.602.915.467) = 4.300.551.848
    assert quarterly_technical_balance_ufrs_k(raw, q2) == Decimal("4300551848")


def test_standardized_value_ufrs_k_yanlis_semada_hata_firlatir() -> None:
    raw = RawFinancials(ticker="GARAN", company_code="GARAN", financial_group="UFRS", periods=[], items={})
    with pytest.raises(UnsupportedFinancialGroupError):
        standardized_value_ufrs_k(raw, "gross_written_premiums", (2026, 6))


# --- CANLI hata duzeltmesi (kullanici raporu, SAHOL PD/DD -- bkz.
# STANDARD_ITEM_MAP_UFRS_K["equity_total"] yorumu): sigortada "2O" (Ozsermaye
# Toplami) TOPLAMdir, "G-Azinlik Paylari" (2MEZD) onun ALT kalemidir -----------------------------------------------------


def test_standard_item_map_ufrs_k_equity_total_dogru_kod() -> None:
    assert STANDARD_ITEM_MAP_UFRS_K["equity_total"] == "2O"


def test_standard_item_map_ufrs_k_minority_interest_dogru_kod() -> None:
    assert STANDARD_ITEM_MAP_UFRS_K["minority_interest"] == "2MEZD"


def test_standardized_value_ufrs_k_equity_ansgr_canli_degerleriyle_dogrulanir() -> None:
    """CANLI dogrulandi (data/exploration/ANSGR_UFRS_K_get_20260730_195513.json):
    2O (Ozsermaye Toplami) = 40.045.701.921, azinlik payi (2MEZD) ANSGR'de
    0 -- bu yuzden equity == equity_total olmali."""
    period = (2026, 6)
    total_code = STANDARD_ITEM_MAP_UFRS_K["equity_total"]
    raw = _raw_ufrs_k({total_code: FinancialItem(total_code, "Özsermaye Toplamı", {period: Decimal("40045701921")})})
    assert standardized_value_ufrs_k(raw, "equity", period) == Decimal("40045701921")
    assert standardized_value_ufrs_k(raw, "equity_total", period) == Decimal("40045701921")


def test_standardized_value_ufrs_k_equity_azinlik_payini_dusurur() -> None:
    period = (2026, 6)
    total_code = STANDARD_ITEM_MAP_UFRS_K["equity_total"]
    minority_code = STANDARD_ITEM_MAP_UFRS_K["minority_interest"]
    raw = _raw_ufrs_k(
        {
            total_code: FinancialItem(total_code, "Özsermaye Toplamı", {period: Decimal("40045701921")}),
            minority_code: FinancialItem(minority_code, "G-Azınlık Payları", {period: Decimal("1000000000")}),
        }
    )
    assert standardized_value_ufrs_k(raw, "equity", period) == Decimal("39045701921")


# --- STANDARD_ITEM_MAP_UFRS_KATILIM (katilim bankasi): ALBRK canli kesif
# yanitiyla dogrulanan kodlar (bkz. data/exploration/ALBRK_UFRS_get_*.json) -----------------------------------------------------


def _raw_ufrs_katilim(items: dict) -> RawFinancials:
    return RawFinancials(ticker="ALBRK", company_code="ALBRK", financial_group="UFRS_KATILIM", periods=list(items), items=items)


def test_standardized_value_ufrs_katilim_kar_payi_geliri() -> None:
    period = (2026, 3)
    item_code = STANDARD_ITEM_MAP_UFRS_KATILIM["interest_income"]
    raw = _raw_ufrs_katilim({item_code: FinancialItem(item_code, "KAR PAYI GELIRLERI", {period: Decimal("19514464000")})})
    assert standardized_value_ufrs_katilim(raw, "interest_income", period) == Decimal("19514464000")


def test_standardized_value_ufrs_katilim_kar_payi_gideri_negatiflenir() -> None:
    """Kar Payi Giderleri ham veride POZITIF buyukluk olarak gelir
    (konvansiyonel bankadaki Faiz Giderleri gibi); NEGATIFE cevrilmeli."""
    period = (2026, 3)
    item_code = STANDARD_ITEM_MAP_UFRS_KATILIM["interest_expense"]
    raw = _raw_ufrs_katilim({item_code: FinancialItem(item_code, "KAR PAYI GIDERLERI", {period: Decimal("16316515000")})})
    assert standardized_value_ufrs_katilim(raw, "interest_expense", period) == Decimal("-16316515000")


def test_quarterly_standardized_value_ufrs_katilim_ceyreklestirir() -> None:
    q1, q2 = (2025, 12), (2026, 3)
    item_code = STANDARD_ITEM_MAP_UFRS_KATILIM["interest_income"]
    raw = _raw_ufrs_katilim(
        {item_code: FinancialItem(item_code, "KAR PAYI GELIRLERI", {q1: Decimal("66678784000"), q2: Decimal("19514464000")})}
    )
    # q2 kumulatif zaten yil basi (period=3) oldugu icin CIKARMA YAPILMAZ,
    # kendisi doner (bkz. quarterly_value_from_cumulative).
    assert quarterly_standardized_value_ufrs_katilim(raw, "interest_income", q2) == Decimal("19514464000")


def test_standardized_value_ufrs_katilim_yanlis_semada_hata_firlatir() -> None:
    raw = RawFinancials(ticker="GARAN", company_code="GARAN", financial_group="UFRS", periods=[], items={})
    with pytest.raises(UnsupportedFinancialGroupError):
        standardized_value_ufrs_katilim(raw, "interest_income", (2026, 6))


# --- CANLI hata duzeltmesi (kullanici raporu, SAHOL PD/DD -- bkz.
# STANDARD_ITEM_MAP_UFRS_KATILIM["equity_total"] yorumu): katilim bankasinda
# "2O" (OZKAYNAK) TOPLAMdir, "14.5 Azinlik Paylari" (2NAU) onun ALT
# kalemidir (CANLI ALBRK verisiyle -- fetch_financials('ALBRK') -- dogrulandi,
# TUM tarihsel donemlerinde 2NAU=0) -----------------------------------------------------


def test_standard_item_map_ufrs_katilim_equity_total_dogru_kod() -> None:
    assert STANDARD_ITEM_MAP_UFRS_KATILIM["equity_total"] == "2O"


def test_standard_item_map_ufrs_katilim_minority_interest_dogru_kod() -> None:
    assert STANDARD_ITEM_MAP_UFRS_KATILIM["minority_interest"] == "2NAU"


def test_standardized_value_ufrs_katilim_equity_azinlik_payini_dusurur() -> None:
    period = (2026, 3)
    total_code = STANDARD_ITEM_MAP_UFRS_KATILIM["equity_total"]
    minority_code = STANDARD_ITEM_MAP_UFRS_KATILIM["minority_interest"]
    raw = _raw_ufrs_katilim(
        {
            total_code: FinancialItem(total_code, "ÖZKAYNAK", {period: Decimal("25578285000")}),
            minority_code: FinancialItem(minority_code, "14.5 Azınlık Payları", {period: Decimal("1000000000")}),
        }
    )
    assert standardized_value_ufrs_katilim(raw, "equity", period) == Decimal("24578285000")


def test_standardized_value_ufrs_katilim_equity_albrk_canli_degeriyle_dogrulanir() -> None:
    """CANLI dogrulandi (fetch_financials('ALBRK'), 2026Ç1): 2O (ÖZKAYNAK) =
    25.578.285.000, 2NAU (14.5 Azınlık Payları) = 0 -- equity == equity_total."""
    period = (2026, 3)
    total_code = STANDARD_ITEM_MAP_UFRS_KATILIM["equity_total"]
    raw = _raw_ufrs_katilim({total_code: FinancialItem(total_code, "ÖZKAYNAK", {period: Decimal("25578285000")})})
    assert standardized_value_ufrs_katilim(raw, "equity", period) == Decimal("25578285000")


# --- _resolve_actual_group: katilim bankasi tespiti (canli ALBRK yanitiyla
# dogrulanan '3A' aciklama metni: "I. KAR PAYI GELİRLERİ") -----------------------------------------------------


def test_resolve_actual_group_kar_payi_katilim_bankasi_olarak_tespit_eder() -> None:
    rows = [{"itemCode": "3A", "itemDescTr": "I. KAR PAYI GELİRLERİ"}]
    assert _resolve_actual_group("UFRS", rows, "ALBRK") == "UFRS_KATILIM"


def test_resolve_actual_group_faiz_konvansiyonel_banka_olarak_tespit_eder() -> None:
    rows = [{"itemCode": "3A", "itemDescTr": "I. FAİZ GELİRLERİ"}]
    assert _resolve_actual_group("UFRS", rows, "GARAN") == "UFRS"


def test_resolve_actual_group_teknik_sigorta_olarak_tespit_eder() -> None:
    rows = [{"itemCode": "3A", "itemDescTr": "A- Hayat Dışı Teknik Gelir"}]
    assert _resolve_actual_group("UFRS", rows, "ANSGR") == "UFRS_K"


def test_resolve_actual_group_xi_29_dokunulmaz() -> None:
    assert _resolve_actual_group("XI_29", [{"itemCode": "3A", "itemDescTr": "her ne olursa"}], "THYAO") == "XI_29"
