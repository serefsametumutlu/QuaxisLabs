"""src/analysis/fund_estimator.py testleri -- SAF matematik, ağ isteği
gerektirmez, elle hesaplanmış senaryolarla doğrulanır."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from src.analysis import fund_estimator as fe


# --- Test yardımcıları (kap_fund_portfolio'ya bağımlı OLMADAN, Protocol şeklini taklit eder) --------


@dataclass(frozen=True)
class _Holding:
    instrument_type: str
    ticker: str | None
    name: str
    weight_pct: Decimal


@dataclass(frozen=True)
class _Portfolio:
    fund_code: str
    report_date: date
    staleness_days: int
    holdings: list[_Holding] = field(default_factory=list)


def _portfolio(holdings: list[_Holding], staleness_days: int = 5, fund_code: str = "PHE") -> _Portfolio:
    return _Portfolio(fund_code=fund_code, report_date=date(2026, 7, 31), staleness_days=staleness_days, holdings=holdings)


# --- is_estimable_fund_type --------------------------------------------


def test_is_estimable_hisse_senedi_fonu_uygulanabilir():
    ok, reason = fe.is_estimable_fund_type("Hisse Senedi Fonu")
    assert ok is True
    assert reason == ""


def test_is_estimable_serbest_fon_uygulanamaz():
    ok, reason = fe.is_estimable_fund_type("Serbest Fon")
    assert ok is False
    assert "Serbest Fon" in reason


def test_is_estimable_none_uygulanamaz():
    ok, reason = fe.is_estimable_fund_type(None)
    assert ok is False


def test_is_estimable_bilinmeyen_kategori_temkinli_uygulanamaz():
    """Kural 3: hiç görülmemiş bir kategori için TEMKİNLİ davranılır."""
    ok, reason = fe.is_estimable_fund_type("Uzay Madenciliği Fonu")
    assert ok is False
    assert "bilinmeyen" in reason.lower()


# --- estimate_daily_return: temel hesap (elle doğrulanmış) --------------------------------------------


def test_estimate_daily_return_iki_hisseli_basit_hesap():
    """Elle hesap: %60 hisse A (+%2), %40 hisse B (-%1), gider yok.
    Beklenen: 0.60*2 + 0.40*(-1) = 1.20 - 0.40 = 0.80"""
    holdings = [
        _Holding("hisse", "AAA", "A A.Ş.", Decimal("60")),
        _Holding("hisse", "BBB", "B A.Ş.", Decimal("40")),
    ]
    portfolio = _portfolio(holdings, staleness_days=3)
    price_changes = {"AAA": Decimal("2"), "BBB": Decimal("-1")}

    result = fe.estimate_daily_return(portfolio, price_changes, fund_category="Hisse Senedi Fonu")

    assert result is not None
    assert result.estimated_return_pct == Decimal("0.80")
    assert result.covered_weight_pct == Decimal("100")
    assert result.confidence == "yüksek"  # taze (3 gün) + tam kapsam + belirsizlik yok


def test_estimate_daily_return_gider_orani_dusulur():
    """Elle hesap: %100 hisse (+%1), yıllık gider %3.65 -> günlük 3.65/365=0.01.
    Beklenen: 1.00 - 0.01 = 0.99"""
    holdings = [_Holding("hisse", "AAA", "A A.Ş.", Decimal("100"))]
    portfolio = _portfolio(holdings)
    price_changes = {"AAA": Decimal("1")}

    result = fe.estimate_daily_return(
        portfolio, price_changes, fund_expense_ratio_annual_pct=Decimal("3.65"), fund_category="Hisse Senedi Fonu"
    )

    assert result.estimated_return_pct == Decimal("0.99")


def test_estimate_daily_return_fon_icinde_fon_ayni_sozlukten_fiyatlanir():
    """'fon' tipi holding'ler de price_changes sözlüğünde AYNI ticker
    anahtarıyla aranır (alt fonun kendi TEFAS kodu)."""
    holdings = [
        _Holding("hisse", "AAA", "A A.Ş.", Decimal("70")),
        _Holding("fon", "PCS", "Alt Fon", Decimal("30")),
    ]
    portfolio = _portfolio(holdings)
    price_changes = {"AAA": Decimal("2"), "PCS": Decimal("1")}

    result = fe.estimate_daily_return(portfolio, price_changes, fund_category="Hisse Senedi Fonu")

    # 0.70*2 + 0.30*1 = 1.40 + 0.30 = 1.70
    assert result.estimated_return_pct == Decimal("1.70")
    assert result.covered_weight_pct == Decimal("100")


# --- kenar durumlar --------------------------------------------


def test_estimate_daily_return_eksik_fiyatli_holding_kapsam_disi_kalir():
    """Fiyatı olmayan bir hisse: contribution=0, covered_weight'e
    KATILMAZ, uncovered_note doldurulur."""
    holdings = [
        _Holding("hisse", "AAA", "A A.Ş.", Decimal("50")),
        _Holding("hisse", "CCC", "C A.Ş. (fiyatsız)", Decimal("50")),
    ]
    portfolio = _portfolio(holdings)
    price_changes = {"AAA": Decimal("4")}  # CCC eksik

    result = fe.estimate_daily_return(portfolio, price_changes, fund_category="Hisse Senedi Fonu")

    assert result.estimated_return_pct == Decimal("2.00")  # 0.50*4 + 0.50*0(kapsam disi)
    assert result.covered_weight_pct == Decimal("50")
    assert result.uncovered_note is not None
    assert "50" in result.uncovered_note

    by_ticker = {c.ticker: c for c in result.contributions}
    assert by_ticker["CCC"].daily_return_pct is None
    assert by_ticker["CCC"].contribution_pct == Decimal("0")


def test_estimate_daily_return_bos_portfoy_none_doner():
    portfolio = _portfolio([])

    assert fe.estimate_daily_return(portfolio, {}, fund_category="Hisse Senedi Fonu") is None


def test_estimate_daily_return_yuzde_100_nakit_fon_sifir_getiri():
    """%100 nakit -- getiri 0, ama covered_weight de 0 (nakit
    'fiyatlandirilmis' sayilmaz, ticker'i yok) ve confidence dusuk olmali."""
    holdings = [_Holding("nakit", None, "Nakit ve Diğer Varlıklar", Decimal("100"))]
    portfolio = _portfolio(holdings, staleness_days=20)

    result = fe.estimate_daily_return(portfolio, {}, fund_category="Hisse Senedi Fonu")

    assert result is not None
    assert result.estimated_return_pct == Decimal("0")
    assert result.covered_weight_pct == Decimal("0")
    assert result.confidence == "düşük"


def test_estimate_daily_return_negatif_getiri_dogru_hesaplanir():
    holdings = [_Holding("hisse", "AAA", "A A.Ş.", Decimal("100"))]
    portfolio = _portfolio(holdings)
    price_changes = {"AAA": Decimal("-5.5")}

    result = fe.estimate_daily_return(portfolio, price_changes, fund_category="Hisse Senedi Fonu")

    assert result.estimated_return_pct == Decimal("-5.50")
    assert result.confidence_interval[0] < result.estimated_return_pct < result.confidence_interval[1]


def test_estimate_daily_return_uygulanamaz_fon_tipi_none_doner():
    holdings = [_Holding("hisse", "AAA", "A A.Ş.", Decimal("100"))]
    portfolio = _portfolio(holdings)

    result = fe.estimate_daily_return(portfolio, {"AAA": Decimal("1")}, fund_category="Serbest Fon")

    assert result is None


def test_estimate_daily_return_fon_kategorisi_verilmezse_uygulanamaz():
    """`fund_category` argümanı verilmezse (varsayılan None) Kural 3
    gereği temkinli davranılıp None döner -- çağıran taraf kategoriyi
    AÇIKÇA geçmek ZORUNDADIR."""
    holdings = [_Holding("hisse", "AAA", "A A.Ş.", Decimal("100"))]
    portfolio = _portfolio(holdings)

    assert fe.estimate_daily_return(portfolio, {"AAA": Decimal("1")}) is None


# --- güven seviyesi --------------------------------------------


def test_estimate_daily_return_bayat_portfoyde_dusuk_guven():
    holdings = [_Holding("hisse", "AAA", "A A.Ş.", Decimal("100"))]
    portfolio = _portfolio(holdings, staleness_days=45)  # 30 gunun uzerinde -- en kotu tazelik puani

    result = fe.estimate_daily_return(portfolio, {"AAA": Decimal("1")}, fund_category="Hisse Senedi Fonu")

    assert result.confidence in ("orta", "düşük")


def test_estimate_daily_return_dusuk_kapsam_ve_bayat_portfoyde_dusuk_guven():
    """Tazelik İYİ tek başına puanı 'orta'ya taşıyabilir (görev tanımının
    "tazelik en yüksek ağırlık" talimatına göre) -- 'düşük' güveni
    görmek için tazelik de KÖTÜ olmalı, sadece düşük kapsam yetmez."""
    holdings = [
        _Holding("hisse", "AAA", "A A.Ş.", Decimal("20")),
        _Holding("hisse", "BBB", "B A.Ş. (fiyatsiz)", Decimal("80")),
    ]
    portfolio = _portfolio(holdings, staleness_days=45)
    result = fe.estimate_daily_return(portfolio, {"AAA": Decimal("1")}, fund_category="Hisse Senedi Fonu")

    assert result.confidence == "düşük"
    width = result.confidence_interval[1] - result.confidence_interval[0]
    assert width == Decimal("4.0")  # dusuk guven: +-2.0 puan


def test_estimate_daily_return_contributions_katkiya_gore_siralanir():
    holdings = [
        _Holding("hisse", "AAA", "Küçük katkı", Decimal("10")),
        _Holding("hisse", "BBB", "Büyük katkı", Decimal("90")),
    ]
    portfolio = _portfolio(holdings)
    price_changes = {"AAA": Decimal("1"), "BBB": Decimal("1")}

    result = fe.estimate_daily_return(portfolio, price_changes, fund_category="Hisse Senedi Fonu")

    assert result.contributions[0].ticker == "BBB"  # 0.90*1=0.90 > 0.10*1=0.10
    assert result.contributions[1].ticker == "AAA"


def test_estimate_daily_return_turev_fiyatlandirilsa_bile_belirsiz_sayilir():
    """'türev'/'nakit' türleri fiyatlandırılsa BİLE (price_changes'te
    varsa) doğaları gereği belirsizlik puanına girer (bkz. modül üst
    notu)."""
    holdings = [
        _Holding("hisse", "AAA", "A A.Ş.", Decimal("90")),
        _Holding("türev", None, "VIOP Nakit Teminatı", Decimal("10")),
    ]
    portfolio = _portfolio(holdings, staleness_days=2)
    # turev'i ticker'i olmadigi icin fiyatlandiramayiz zaten (None), ama
    # yine de coverage disi kalmasi ve belirsizlige girmesi test ediliyor
    result = fe.estimate_daily_return(portfolio, {"AAA": Decimal("1")}, fund_category="Hisse Senedi Fonu")

    assert result.covered_weight_pct == Decimal("90")
