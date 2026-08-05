"""src/analysis/fundamental_screens.py testleri -- Graham + Greenblatt Sihirli
Formül + Carlisle Acquirer's Multiple + Piotroski F-Skoru (SAF matematik,
I/O yok). Beklenen değerler ELLE hesaplanmıştır (bkz. test_valuation.py ile
AYNI ilke, 07_BAKIM_KURALLARI.md §3.3)."""

from __future__ import annotations

from decimal import Decimal

from src.analysis.fundamental_screens import compute_fundamental_screens

# --- Tam veri senaryosu (tüm 4 yöntem + Piotroski'nin 9 kriteri de
# değerlendirilebilir) -- rakamlar EBIT/FD/NWC/tangible bölümlerinin TAM
# SAYIYA bölünmesi için özenle seçildi (bkz. asagidaki elle hesap notlari).

_LATEST = (2026, 12)  # period=12 -> TTM'i dogrudan (prior yil verisine gerek olmadan)
_PRIOR = (2025, 12)

_FINANCIALS = {
    _LATEST: {
        "operating_profit_cum": Decimal(26000),  # EBIT (TTM, period=12 -> dogrudan)
        "financial_debt": Decimal(50000),
        "cash": Decimal(20000),
        "financial_investments": Decimal(0),
        # net_debt = 50000 - (20000+0) = 30000 -> EV = market_cap(100*1000=100000) + 30000 = 130000
        "current_assets": Decimal(40000),
        "short_term_liabilities": Decimal(25000),  # NWC = 15000
        "tangible_fixed_assets": Decimal(25000),  # invested_capital = 15000+25000 = 40000
        "net_income_cum": Decimal(15000),
        "operating_cash_flow_cum": Decimal(20000),
        "revenue_cum": Decimal(200000),
        "gross_profit_cum": Decimal(50000),
        "total_assets": Decimal(100000),
        "long_term_financial_debt": Decimal(20000),
        "share_capital": Decimal(1000),
    },
    _PRIOR: {
        "total_assets": Decimal(90000),
        "net_income_cum": Decimal(9000),
        "long_term_financial_debt": Decimal(30000),
        "current_assets": Decimal(30000),
        "short_term_liabilities": Decimal(20000),
        "share_capital": Decimal(1000),
        "gross_profit_cum": Decimal(40000),
        "revenue_cum": Decimal(180000),
    },
}

_PRICE = Decimal(100)
_SHARE_CAPITAL = Decimal(1000)
_OWN_PE = Decimal(10)
_OWN_PB = Decimal(1)


def test_tum_yontemler_dogru_hesaplanir() -> None:
    result = compute_fundamental_screens(_FINANCIALS, _PRICE, _SHARE_CAPITAL, own_pe=_OWN_PE, own_pb=_OWN_PB)
    assert result.has_data is True

    # Graham: multiple = 10*1 = 10 (<=22.5 -> Ucuz); adil deger = 100*sqrt(22.5/10) = 150
    g = result.graham
    assert g.graham_multiple == Decimal(10)
    assert g.verdict == "Graham Ölçütüne Göre Ucuz"
    assert g.fair_value_price == Decimal(150)
    assert g.upside_pct == Decimal(50)

    # Greenblatt: EV = 130000, EBIT = 26000 -> kazanc getirisi = %20 (Yuksek, >=12)
    # NWC=15000, tangible=25000 -> yatirilan sermaye=40000 -> ROC = 26000/40000*100 = %65 (Yuksek, >=25)
    gb = result.greenblatt
    assert gb.ebit == Decimal(26000)
    assert gb.enterprise_value == Decimal(130000)
    assert gb.earnings_yield_pct == Decimal(20)
    assert gb.earnings_yield_band == "Yüksek"
    assert gb.net_working_capital == Decimal(15000)
    assert gb.net_fixed_assets == Decimal(25000)
    assert gb.return_on_capital_pct == Decimal(65)
    assert gb.return_on_capital_band == "Yüksek"

    # Acquirer's Multiple = FD/EBIT = 130000/26000 = 5.0 (<=8 -> Ucuz)
    am = result.acquirers_multiple
    assert am.acquirers_multiple == Decimal(5)
    assert am.band == "Ucuz"

    # Piotroski: 8/9 kriter basarili (asset devir hizi artmadi, 2.0 = 2.0)
    p = result.piotroski
    assert p.score == 8
    assert p.criteria_evaluated == 9
    assert p.band == "Güçlü"
    basarisiz = [label for label, passed in p.details if passed is False]
    assert basarisiz == ["Aktif Devir Hızı Arttı (Verimlilik)"]


def test_own_pe_pb_yoksa_graham_none_digerleri_calisir() -> None:
    result = compute_fundamental_screens(_FINANCIALS, _PRICE, _SHARE_CAPITAL, own_pe=None, own_pb=None)
    assert result.graham is None
    assert result.greenblatt is not None
    assert result.has_data is True


def test_negatif_own_pe_graham_hesaplanmaz() -> None:
    # Zarar eden bir sirkette F/K negatiftir -- Graham Sayisi TANIMSIZDIR
    # (karekokun icine negatif deger duserdi), Kural 3 geregi None kalir.
    result = compute_fundamental_screens(_FINANCIALS, _PRICE, _SHARE_CAPITAL, own_pe=Decimal(-5), own_pb=_OWN_PB)
    assert result.graham is None


def test_fiyat_sermaye_yoksa_ev_hesaplanamaz_ama_piotroski_calisir() -> None:
    # EV (dolayisiyla Greenblatt kazanc getirisi/Acquirer's Multiple) fiyat/
    # sermaye GEREKTIRIR -- ikisi de None ise bu ikisi calismaz, ama
    # Piotroski (sadece bilanco/gelir tablosu kalemlerinden) ETKILENMEZ.
    result = compute_fundamental_screens(_FINANCIALS, price=None, share_capital=None, own_pe=None, own_pb=None)
    assert result.greenblatt is not None
    assert result.greenblatt.enterprise_value is None
    assert result.greenblatt.earnings_yield_pct is None
    # ROC sektor/fiyat GEREKTIRMEZ (sadece NWC+tangible+EBIT) -- yine de dolu olmali.
    assert result.greenblatt.return_on_capital_pct == Decimal(65)
    assert result.acquirers_multiple is None  # EV None oldugu icin hesaplanamaz
    assert result.piotroski is not None
    assert result.piotroski.score == 8


def test_bos_financials_has_data_false() -> None:
    result = compute_fundamental_screens({}, _PRICE, _SHARE_CAPITAL, own_pe=_OWN_PE, own_pb=_OWN_PB)
    assert result.has_data is False
    assert result.graham is None
    assert result.greenblatt is None
    assert result.acquirers_multiple is None
    assert result.piotroski is None


# --- Carlisle Acquirer's Multiple bant esikleri -----------------------------------------------------


_PRICE_EV150K = Decimal(120)  # market_cap=120*1000=120000 + net_debt(30000) = EV 150000 (tam bolunsun diye)


def test_acquirers_multiple_pahali_esik_15_ve_uzeri() -> None:
    financials = {_LATEST: {**_FINANCIALS[_LATEST], "operating_profit_cum": Decimal(10000)}}  # 150000/10000 = 15
    result = compute_fundamental_screens(financials, _PRICE_EV150K, _SHARE_CAPITAL, own_pe=None, own_pb=None)
    assert result.acquirers_multiple.acquirers_multiple == Decimal(15)
    assert result.acquirers_multiple.band == "Pahalı"


def test_acquirers_multiple_makul_araliktaki_deger() -> None:
    financials = {_LATEST: {**_FINANCIALS[_LATEST], "operating_profit_cum": Decimal(15000)}}  # 150000/15000 = 10
    result = compute_fundamental_screens(financials, _PRICE_EV150K, _SHARE_CAPITAL, own_pe=None, own_pb=None)
    assert result.acquirers_multiple.acquirers_multiple == Decimal(10)
    assert result.acquirers_multiple.band == "Makul"


# --- Piotroski eksik veri davranışı -----------------------------------------------------


def test_piotroski_eksik_onceki_donem_kriterleri_disinda_birakir() -> None:
    # Onceki donem HIC yoksa YoY kriterlerin (3,5,6,7,8,9) HICBIRI
    # degerlendirilemez -- SADECE 1,2,4 (guncel doneme ait) kalir, 6/9
    # DEGIL 2/9 (veya benzeri) uzerinden dogru bir oran gosterilir.
    financials = {_LATEST: _FINANCIALS[_LATEST]}
    result = compute_fundamental_screens(financials, _PRICE, _SHARE_CAPITAL, own_pe=None, own_pb=None)
    p = result.piotroski
    assert p.criteria_evaluated == 3
    assert p.score == 3  # ROA pozitif, OCF pozitif, OCF>NetKar -- ucu de guncel donem verisiyle True
    # criteria_evaluated < 5 oldugu icin (Kural 3) bir "guclu/zayif" yorumu YAPILMAZ
    assert p.band is None
