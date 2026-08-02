"""sec_edgar.py icindeki saf mantik fonksiyonlarinin birim testleri.

Ag erisimi gerektiren fetch_financials()/resolve_cik()/fetch_latest_price()
BU DOSYADA test EDILMEZ (bkz. scripts/demo_fetch_us.py -- canli veriyle
calisan Faz 9 teslim kriteri scripti). Burada SADECE disariya bagimliligi
olmayan ayristirma/turetme fonksiyonlari VE data/exploration/ altinda
SAKLANMIS gercek SEC yanitlari (canli kesifte kaydedildi, bkz.
scripts/explore_sec.py) fixture olarak kullanilir -- hicbir ag istegi
ATILMAZ.
"""

from __future__ import annotations

import glob
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from src.fetchers.sec_edgar import (
    STANDARD_ITEM_MAP_US_GAAP,
    ConceptFact,
    RawUsFinancials,
    _discover_available_periods,
    _extract_relevant_facts,
    _select_best_fact,
    depreciation_amortization_us_gaap,
    gross_profit_us_gaap,
    normalize_ticker,
    quarterly_depreciation_amortization_us_gaap,
    quarterly_gross_profit_us_gaap,
    quarterly_standardized_value_us_gaap,
    quarterly_value_from_cumulative_us_gaap,
    standardized_value_us_gaap,
    total_debt_us_gaap,
)

BASE_DIR = Path(__file__).resolve().parent.parent
EXPLORATION_DIR = BASE_DIR / "data" / "exploration"


def _load_fixture(ticker: str) -> dict:
    matches = sorted(glob.glob(str(EXPLORATION_DIR / f"{ticker}_companyfacts_*.json")))
    if not matches:
        pytest.skip(f"data/exploration/{ticker}_companyfacts_*.json bulunamadi (kesif scripti calistirilmamis olabilir).")
    return json.loads(Path(matches[-1]).read_text(encoding="utf-8"))


def _build_raw(ticker: str) -> RawUsFinancials:
    payload = _load_fixture(ticker)
    facts_by_tag = _extract_relevant_facts(payload)
    periods = _discover_available_periods(facts_by_tag)
    return RawUsFinancials(
        ticker=ticker, cik10="", company_name=payload.get("entityName"), periods=periods, facts_by_tag=facts_by_tag
    )


# --- normalize_ticker -----------------------------------------------------


def test_normalize_ticker_bosluk_ve_kucuk_harfi_temizler() -> None:
    assert normalize_ticker("  aapl ") == "AAPL"


# --- quarterly_value_from_cumulative_us_gaap (isyatirim.quarterly_value_from_cumulative ile AYNI ilke) -----------------------------------------------------


def _fact(start: str | None, end: str, val: str, fp: str, fy: int, filed: str = "2026-01-01") -> ConceptFact:
    return ConceptFact(
        start=date.fromisoformat(start) if start else None,
        end=date.fromisoformat(end),
        val=Decimal(val),
        form="10-Q",
        fp=fp,
        fy=fy,
        frame=None,
        filed=filed,
    )


def test_quarterly_value_ilk_ceyrekte_cikarma_yapilmaz() -> None:
    facts = [_fact("2025-09-28", "2025-12-27", "100", "Q1", 2026)]
    assert quarterly_value_from_cumulative_us_gaap(facts, 2026, 3) == Decimal("100")


def test_quarterly_value_ikinci_ceyrekte_onceki_kumulatiften_cikarilir() -> None:
    facts = [
        _fact("2025-09-28", "2025-12-27", "100", "Q1", 2026),
        _fact("2025-09-28", "2026-03-28", "250", "Q2", 2026),
    ]
    assert quarterly_value_from_cumulative_us_gaap(facts, 2026, 6) == Decimal("150")


def test_quarterly_value_dorduncu_ceyrek_fp_fy_yillik_eksi_3_ceyrek() -> None:
    # fiscal_period=12 -> fp="FY" (yillik 10-K), Q4-only = FY - Q3 kumulatif.
    facts = [
        _fact("2025-09-28", "2026-06-27", "270", "Q3", 2026),
        _fact("2025-09-28", "2026-09-26", "400", "FY", 2026),
    ]
    assert quarterly_value_from_cumulative_us_gaap(facts, 2026, 12) == Decimal("130")


def test_quarterly_value_onceki_donem_eksikse_none_doner() -> None:
    facts = [_fact("2025-09-28", "2026-03-28", "250", "Q2", 2026)]
    assert quarterly_value_from_cumulative_us_gaap(facts, 2026, 6) is None


def test_quarterly_standardized_value_sirket_ceyrekler_arasi_tag_degistirse_bile_calisir() -> None:
    """CANLI HATA (kullanici raporu -- GOOGL kartinda 'Satislar (karsilastirma)'
    satiri sessizce 'veri yok' gosteriyordu): GOOGL 2025 Ç1 10-Q'sunda
    'RevenueFromContractWithCustomerExcludingAssessedTax' tag'ini kullanirken
    2025 Ç2 10-Q'sunda (taksonomi degisikligiyle) 'Revenues' tag'ine GECTI --
    HER IKI donem de kendi TEK tag'i icinde TAM/dogru veriye sahip, ama ESKI
    (tek-tag icinde cikarma yapan) uygulama iki donemi AYNI tag'de ARADIGI
    icin basarisiz oluyordu. quarterly_standardized_value_us_gaap() artik
    HER DONEMI standardized_value_us_gaap() ile AYRI AYRI (TUM aday
    tag'leri deneyerek) cozup SONRA cikarir -- tag degisikligine DAYANIKLI."""
    facts_by_tag = {
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax": [
            _fact("2025-01-01", "2025-03-31", "90234000000", "Q1", 2025),
        ],
        "us-gaap:Revenues": [
            _fact("2025-01-01", "2025-06-30", "186662000000", "Q2", 2025),
        ],
    }
    raw = RawUsFinancials(
        ticker="GOOGL", cik10="0001652044", company_name="Alphabet Inc.",
        periods=[(2025, 6), (2025, 3)], facts_by_tag=facts_by_tag,
    )
    # standardized_value_us_gaap HER DONEMI ayri ayri (kendi tag'inden) bulur.
    assert standardized_value_us_gaap(raw, "revenue", (2025, 3)) == Decimal("90234000000")
    assert standardized_value_us_gaap(raw, "revenue", (2025, 6)) == Decimal("186662000000")
    # ceyreklik turetme ARTIK basarili: 186.662.000.000 - 90.234.000.000
    assert quarterly_standardized_value_us_gaap(raw, "revenue", (2025, 6)) == Decimal("96428000000")


def test_standardized_value_asts_ucuncu_revenue_tag_ile_bulunur() -> None:
    """CANLI HATA (kullanici raporu, §B17): ASTS (AST SpaceMobile) kartinda
    Satislar/Brut Kar/Esas Faaliyet Kari 'veri yok' gosteriyordu. Kok neden:
    ASTS 2025 Ç1'den itibaren "ExcludingAssessedTax" VE "Revenues" tag'lerini
    birakip SADECE "RevenueFromContractWithCustomerIncludingAssessedTax"
    kullanmaya basladi (CANLI dogrulandi: data/exploration/ASTS_companyfacts_
    *.json -- ilk iki tag FY2024'te kesiliyor). Bu tag adaya EKLENENE kadar
    quarterly_standardized_value_us_gaap None donuyordu."""
    facts_by_tag = {
        "us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax": [
            _fact("2026-01-01", "2026-03-31", "14735000", "Q1", 2026),
        ],
    }
    raw = RawUsFinancials(
        ticker="ASTS", cik10="0001780312", company_name="AST SpaceMobile, Inc.",
        periods=[(2026, 3)], facts_by_tag=facts_by_tag,
    )
    assert standardized_value_us_gaap(raw, "revenue", (2026, 3)) == Decimal("14735000")
    assert quarterly_standardized_value_us_gaap(raw, "revenue", (2026, 3)) == Decimal("14735000")


# --- _select_best_fact: CANLI HATA regresyonu (AAPL, bkz. sec_edgar.py modul notu) -----------------------------------------------------


def test_select_best_fact_onceki_mali_yil_sonu_karsilastirma_kolonunu_ELEMELI() -> None:
    """CANLI HATA (AAPL companyfacts ile kesifte bulundu): SEC ayni (fy, fp)
    etiketini HEM gercek ceyrek-sonu bakiyeye HEM O CEYREGIN 10-Q'sundaki
    "bir onceki mali yil sonu" karsilastirma koluna yapistiriyor. Ikisi de
    AYNI 'filed' tarihini tasidigi icin (ayni dosyalamadan geldikleri icin)
    'filed' ile AYIRT EDILEMEZ -- dogru secim EN BUYUK (en yeni) 'end'
    tarihli olandir (karsilastirma kolonu HER ZAMAN daha eskidir)."""
    facts = [
        # Onceki mali yil sonu (YANLIS) -- ayni filed tarihi.
        ConceptFact(start=None, end=date(2025, 9, 27), val=Decimal("359241000000"), form="10-Q", fp="Q1", fy=2026, frame=None, filed="2026-01-30"),
        # Gercek Ç1 FY26 bakiyesi (DOGRU) -- ayni filed tarihi.
        ConceptFact(start=None, end=date(2025, 12, 27), val=Decimal("379297000000"), form="10-Q", fp="Q1", fy=2026, frame="CY2025Q4I", filed="2026-01-30"),
    ]
    best = _select_best_fact(facts, 2026, "Q1")
    assert best is not None
    assert best.val == Decimal("379297000000")


# --- AAPL: gercek kayitli SEC yanitiyla uctan uca dogrulama -----------------------------------------------------
# Asagidaki degerler CANLI SEC EDGAR yanitindan (2026-08-02, bkz.
# data/exploration/AAPL_companyfacts_*.json) VE kamuya acik Apple mali
# raporlarindan (10-Q/10-K) alinmistir -- UYDURULMADI:
#   - FY2025 Q1 (Ekim-Aralik 2024 ceyregi) hasilati $124.300 milyar --
#     Apple'in Ocak 2025'te acikladigi TATIL SEZONU ceyregi rakamiyla
#     BIREBIR eslesiyor (kamuya acik/iyi bilinen rakam).
#   - FY2024 Q4 (mali yil sonu, Eylul 2024) toplam varlik $364.980 milyar --
#     Apple'in FY2024 10-K'sindeki TAM rakamla BIREBIR eslesiyor.
#   - FY2024 Q4 net kar $14.736 milyar -- AB'nin tek seferlik vergi
#     cezasi nedeniyle DUSUK cikan, kamuya acik/iyi bilinen ceyrek.


def test_aapl_fy2025_q1_hasilat_canli_degerle_eslesir() -> None:
    raw = _build_raw("AAPL")
    value = quarterly_standardized_value_us_gaap(raw, "revenue", (2025, 3))
    assert value == Decimal("124300000000")


def test_aapl_fy2024_q4_toplam_varlik_canli_degerle_eslesir() -> None:
    raw = _build_raw("AAPL")
    value = standardized_value_us_gaap(raw, "total_assets", (2024, 12))
    assert value == Decimal("364980000000")


def test_aapl_fy2024_q4_net_kar_canli_degerle_eslesir() -> None:
    raw = _build_raw("AAPL")
    value = quarterly_standardized_value_us_gaap(raw, "net_income", (2024, 12))
    assert value == Decimal("14736000000")


def test_aapl_ardisik_ceyreklerde_bilanco_degeri_TEKRARLANMAZ() -> None:
    """Duzeltilen CANLI HATANIN regresyon kilidi: FY2026 Q1/Q2/Q3 toplam
    varlik degerleri BIRBIRINDEN FARKLI olmali (once hepsi ayni -- yanlislikla
    'onceki mali yil sonu' degerine sabitleniyordu)."""
    raw = _build_raw("AAPL")
    q1 = standardized_value_us_gaap(raw, "total_assets", (2026, 3))
    q2 = standardized_value_us_gaap(raw, "total_assets", (2026, 6))
    q3 = standardized_value_us_gaap(raw, "total_assets", (2026, 9))
    assert len({q1, q2, q3}) == 3


# --- NVDA: takvim yiliyla ORTUSMEYEN mali yil -----------------------------------------------------


def test_nvda_fy2026_q1_hasilat_canli_degerle_eslesir() -> None:
    # NVIDIA'nin Ocak sonu biten mali yili -- FY2026 Q1 = Subat-Nisan 2025
    # ceyregi, kamuya acik hasilat rakami $44.062 milyar.
    raw = _build_raw("NVDA")
    value = quarterly_standardized_value_us_gaap(raw, "revenue", (2026, 3))
    assert value == Decimal("44062000000")


# --- JPM: banka semasi -- BIST UFRS ile AYNI bilinen sinirlamalar -----------------------------------------------------


def test_jpm_ceyreklik_hasilat_alani_none_doner() -> None:
    """Bankalarda "revenue" (tek satirlik toplam hasilat) kavramı YOK --
    JPM'nin "Revenues" tag'i SADECE yillik (10-K, fp='FY') raporlaniyor,
    ceyreklik (10-Q, fp='Q1'/'Q2'/'Q3') hicbir donemde YOK (CANLI dogrulandi).
    BIST UFRS semasinda da 'revenue' alani YOKTUR (bkz. isyatirim.py) --
    bu, o durumla TUTARLI bir N/A, hata DEGIL."""
    raw = _build_raw("JPM")
    latest = raw.periods[0]
    assert quarterly_standardized_value_us_gaap(raw, "revenue", latest) is None


def test_jpm_gross_profit_ve_current_assets_none_doner() -> None:
    raw = _build_raw("JPM")
    latest = raw.periods[0]
    assert standardized_value_us_gaap(raw, "gross_profit", latest) is None
    assert standardized_value_us_gaap(raw, "operating_profit", latest) is None
    assert standardized_value_us_gaap(raw, "current_assets", latest) is None


def test_jpm_net_kar_dogru_tag_ile_bulunur() -> None:
    raw = _build_raw("JPM")
    latest = raw.periods[0]
    value = quarterly_standardized_value_us_gaap(raw, "net_income", latest)
    assert value is not None
    assert value > 0


def test_total_debt_us_gaap_iki_bileseni_toplar() -> None:
    raw = _build_raw("AAPL")
    period = raw.periods[0]
    short_debt = standardized_value_us_gaap(raw, "short_term_financial_debt", period)
    long_debt = standardized_value_us_gaap(raw, "long_term_financial_debt", period)
    assert total_debt_us_gaap(raw, period) == short_debt + long_debt


# --- gross_profit_us_gaap: dogrudan tag varsa oncelikli, yoksa turetme -----------------------------------------------------


def test_gross_profit_us_gaap_dogrudan_tag_varsa_onceliklidir() -> None:
    # AAPL'de "GrossProfit" tag'i dogrudan mevcut -- turetme YAPILMAMALI.
    raw = _build_raw("AAPL")
    period = raw.periods[0]
    direct = standardized_value_us_gaap(raw, "gross_profit", period)
    assert direct is not None
    assert gross_profit_us_gaap(raw, period) == direct


def test_gross_profit_us_gaap_dogrudan_tag_yoksa_maliyetten_turetir() -> None:
    """CANLI DOGRULANDI (kullanici raporu -- 10 resmi NASDAQ hissesi taramasi
    sirasinda GOOGL/AMZN/META/NFLX'te 'GrossProfit' tag'inin GUNCEL donemde
    HIC olmadigi bulundu): Hasilat - Satislarin Maliyeti = stockanalysis.com'un
    raporladigi Brut Kar ile BIREBIR eslesti (GOOGL 2026 Ç2: $119,796mr -
    $45,943mr = $73,853mr)."""
    facts_by_tag = {
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax": [
            _fact("2026-01-01", "2026-06-30", "119796000000", "Q2", 2026),
        ],
        "us-gaap:CostOfRevenue": [
            _fact("2026-04-01", "2026-06-30", "45943000000", "Q2", 2026),
        ],
    }
    raw = RawUsFinancials(
        ticker="GOOGL", cik10="0001652044", company_name="Alphabet Inc.",
        periods=[(2026, 6)], facts_by_tag=facts_by_tag,
    )
    assert standardized_value_us_gaap(raw, "gross_profit", (2026, 6)) is None  # dogrudan tag YOK
    assert gross_profit_us_gaap(raw, (2026, 6)) == Decimal("73853000000")


def test_gross_profit_us_gaap_maliyet_verisi_de_yoksa_none_doner() -> None:
    # PYPL senaryosu: ne GrossProfit ne CostOfRevenue/CostOfGoodsAndServicesSold var.
    facts_by_tag = {
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax": [
            _fact("2026-01-01", "2026-03-31", "8353000000", "Q1", 2026),
        ],
    }
    raw = RawUsFinancials(
        ticker="PYPL", cik10="0001633917", company_name="PayPal Holdings, Inc.",
        periods=[(2026, 3)], facts_by_tag=facts_by_tag,
    )
    assert gross_profit_us_gaap(raw, (2026, 3)) is None
    assert quarterly_gross_profit_us_gaap(raw, (2026, 3)) is None


def test_quarterly_gross_profit_us_gaap_kumulatiften_ceyreklik_turetir() -> None:
    # Sentetik ama TUTARLI kumulatif degerler: Ç2 (6 aylik) kumulatif -
    # Ç1 (3 aylik) kumulatif = TEK CEYREKLIK deger -- hem hasilat hem
    # maliyet icin AYRI AYRI turetilip SONRA cikarilmali (quarterly_value_
    # from_cumulative_us_gaap ile AYNI ilke, bkz. NFLX gercek 2026 Ç2
    # dogrulamasi: test_gross_profit_us_gaap_dogrudan_tag_yoksa_maliyetten_turetir).
    facts_by_tag = {
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax": [
            _fact("2026-01-01", "2026-03-31", "6000000000", "Q1", 2026),
            _fact("2026-01-01", "2026-06-30", "12559938000", "Q2", 2026),
        ],
        "us-gaap:CostOfRevenue": [
            _fact("2026-01-01", "2026-03-31", "5000000000", "Q1", 2026),
            _fact("2026-01-01", "2026-06-30", "11925203000", "Q2", 2026),
        ],
    }
    raw = RawUsFinancials(
        ticker="NFLX", cik10="0001065280", company_name="NETFLIX INC",
        periods=[(2026, 6), (2026, 3)], facts_by_tag=facts_by_tag,
    )
    # ceyreklik hasilat = 12.559.938.000 - 6.000.000.000 = 6.559.938.000
    # ceyreklik maliyet = 11.925.203.000 - 5.000.000.000 = 6.925.203.000
    beklenen = Decimal("6559938000") - Decimal("6925203000")
    assert quarterly_gross_profit_us_gaap(raw, (2026, 6)) == beklenen


# --- depreciation_amortization_us_gaap: dogrudan tag varsa oncelikli, yoksa Depreciation+Amortization toplami -----------------------------------------------------


def test_depreciation_amortization_us_gaap_dogrudan_tag_varsa_onceliklidir() -> None:
    # AAPL'de "DepreciationDepletionAndAmortization" tag'i dogrudan mevcut.
    raw = _build_raw("AAPL")
    period = raw.periods[0]
    direct = standardized_value_us_gaap(raw, "depreciation_amortization", period)
    assert direct is not None
    assert depreciation_amortization_us_gaap(raw, period) == direct


def test_depreciation_amortization_us_gaap_birlesik_tag_yoksa_depreciation_ve_amortizasyonu_toplar() -> None:
    """CANLI DOGRULANDI (kullanici raporu, 2026-08-02: MSFT kartinda FAVOK
    satiri eksikti -- 5 yerine 4 gelir tablosu metrigi gorunuyordu). MSFT
    "DepreciationDepletionAndAmortization"/"DepreciationAmortizationAndAccretionNet"
    tag'lerinin HICBIRINI kullanmiyor, D&A'yi "Depreciation" (maddi duran
    varlik) + "AmortizationOfIntangibleAssets" (maddi olmayan duran varlik)
    olarak IKI AYRI satirda raporluyor. Web aramasiyla (gurufocus.com)
    dogrulandi: MSFT FY2026 Ç3 (Ocak-Mart 2026) birlesik D&A = $10.167mr;
    bu testteki $9,0mr + $1,1mr = $10,1mr, %1'in ALTINDA farkla eslesiyor."""
    raw = _build_raw("MSFT")
    period = (2026, 9)  # FY2026 Q3 (fp="Q3") -- Ocak-Mart 2026 takvim ceyregi
    assert standardized_value_us_gaap(raw, "depreciation_amortization", period) is None  # birlesik tag YOK
    beklenen = Decimal("24000000000") - Decimal("15000000000") + (Decimal("3700000000") - Decimal("2600000000"))
    assert quarterly_depreciation_amortization_us_gaap(raw, period) == beklenen
    assert beklenen == Decimal("10100000000")  # $10,1mr -- gurufocus'un $10,167mr'iyle %1 altinda fark


def test_depreciation_amortization_us_gaap_sadece_bir_bilesen_varsa_none_doner() -> None:
    # Sadece "Depreciation" var, "AmortizationOfIntangibleAssets" yok --
    # yanlislikla eksik bir D&A rakami uretmemek icin None donmeli (Kural 8).
    facts_by_tag = {
        "us-gaap:Depreciation": [_fact("2026-01-01", "2026-03-31", "9000000000", "Q3", 2026)],
    }
    raw = RawUsFinancials(
        ticker="TEST", cik10="0000000000", company_name="Test Corp",
        periods=[(2026, 9)], facts_by_tag=facts_by_tag,
    )
    assert depreciation_amortization_us_gaap(raw, (2026, 9)) is None
    assert quarterly_depreciation_amortization_us_gaap(raw, (2026, 9)) is None


def test_shares_outstanding_donem_ortalamasi_fallback_uzerinden_dogru_secilir() -> None:
    """CANLI HATA (kullanici raporu -- 10 resmi NASDAQ hissesi taramasi
    sirasinda bulundu): META'da dei:EntityCommonStockSharesOutstanding VE
    us-gaap:CommonStockSharesOutstanding HIC YOK (dei namespace'i SADECE
    'EntityPublicFloat' iceriyor) -- shares_outstanding HER ZAMAN None
    donuyordu, Piyasa Degeri/F-K/PD-DD hesaplanamiyordu. Ucuncul yedek
    (WeightedAverageNumberOfDilutedSharesOutstanding, bir DURATION/donem
    ortalamasi fact'i) eklendi -- _select_best_fact bunu ~90 gunluk ceyrek
    uzunluguna otomatik filtreler (ekstra kod GEREKMEDI). CANLI DOGRULANDI:
    macrotrends.net'in bagimsiz raporladigi '2.564B (Mart 2026 ceyregi)'
    ile BIREBIR eslesti."""
    facts = [
        # ANLIK (point-in-time) tag'ler HIC YOK -- META senaryosu.
        ConceptFact(start=date(2026, 1, 1), end=date(2026, 3, 31), val=Decimal("2564000000"), form="10-Q", fp="Q1", fy=2026, frame="CY2026Q1", filed="2026-04-30"),
        # 9 aylik (YTD) donem ortalamasi -- YANLISLIKLA secilmemeli (~90 gunluk degil).
        ConceptFact(start=date(2026, 1, 1), end=date(2026, 9, 30), val=Decimal("2550000000"), form="10-Q", fp="Q3", fy=2026, frame=None, filed="2026-10-30"),
    ]
    raw = RawUsFinancials(
        ticker="META", cik10="0001326801", company_name="Meta Platforms, Inc.",
        periods=[(2026, 3)],
        facts_by_tag={"us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding": facts},
    )
    assert standardized_value_us_gaap(raw, "shares_outstanding", (2026, 3)) == Decimal("2564000000")


# --- STANDARD_ITEM_MAP_US_GAAP butunluk kontrolu -----------------------------------------------------


def test_standard_item_map_her_alan_en_az_bir_aday_tag_icerir() -> None:
    for field, candidates in STANDARD_ITEM_MAP_US_GAAP.items():
        assert candidates, f"'{field}' icin aday tag listesi bos olamaz"
        for tag in candidates:
            assert ":" in tag, f"'{tag}' 'taxonomy:concept' biciminde degil"
