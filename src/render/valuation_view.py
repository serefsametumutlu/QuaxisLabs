"""`src.analysis.valuation.ValuationAssessment`'ı Türkçe biçimlendirilmiş bir
context dict'ine çevirir -- HEM Derin Kart (`deep_card.py`, geniş panel) HEM
tek çeyreklik Bilanço kartı (`card.py`, kompakt panel) tarafından paylaşılır
(Kural 4: render katmanı hiçbir oran HESAPLAMAZ, formatlama mantığının
KOPYALANMAMASI için tek bir yerde tutulur).

Bu modül SADECE biçimlendirme yapar -- hesaplamanın kendisi tamamen
`src/analysis/valuation.py`'de (saf matematik, I/O yok) yapılmıştır.
"""

from __future__ import annotations

from decimal import Decimal

from src.analysis.valuation import ValuationAssessment
from src.formatting import format_currency_short, format_number_tr, format_percent_tr

_MARKET_CURRENCY: dict[str, str] = {"BIST": "₺", "NASDAQ": "$"}

_SECTOR_VERDICT_CLASS: dict[str, str] = {
    "Sektöre Göre Ucuz": "verdict-ucuz",
    "Sektöre Göre Makul": "verdict-makul",
    "Sektöre Göre Pahalı": "verdict-pahali",
}

# Graham/PEG rozetleri İKİ-durumlu (Ucuz/Pahalı, "Makul" SADECE PEG'de var) --
# sektör rozetiyle AYNI 3'lü CSS sınıfı ailesini (verdict-ucuz/makul/pahali)
# yeniden kullanır ki kartta GÖRSEL OLARAK tutarlı kalsın.
_GRAHAM_VERDICT_CLASS: dict[str, str] = {
    "Graham Ölçütüne Göre Ucuz": "verdict-ucuz",
    "Graham Ölçütüne Göre Pahalı": "verdict-pahali",
}
_PEG_VERDICT_CLASS: dict[str, str] = {
    "Büyümeye Göre Ucuz (PEG)": "verdict-ucuz",
    "Büyümeye Göre Makul (PEG)": "verdict-makul",
    "Büyümeye Göre Pahalı (PEG)": "verdict-pahali",
}
# Damodaran rozeti de Graham gibi İKİ-durumlu (Ucuz/Pahalı) -- AYNI 3'lü CSS
# ailesini yeniden kullanır (bkz. yukarıdaki not).
_DAMODARAN_VERDICT_CLASS: dict[str, str] = {
    "Damodaran Modeline Göre Ucuz": "verdict-ucuz",
    "Damodaran Modeline Göre Pahalı": "verdict-pahali",
}


def _currency_symbol(market: str) -> str:
    return _MARKET_CURRENCY.get(market, "₺")


def _fmt_currency(value: Decimal | None, market: str) -> str:
    return format_currency_short(value, symbol=_currency_symbol(market)) if value is not None else "N/A"


def _fmt_pct(value: Decimal | None, decimals: int = 1) -> str:
    return format_percent_tr(value, decimals) if value is not None else "N/A"


def _fmt_ratio(value: Decimal | None) -> str:
    # CANLI KULLANICI GERI BILDIRIMI (2026-08-04): "x" ibaresi (orn. "5,30x")
    # gereksiz/kalabalik bulundu -- SADECE sayi gosterilsin istendi.
    return format_number_tr(value, 2) if value is not None else "N/A"


def _pct_class(value: Decimal | None) -> str:
    if value is None:
        return "neutral"
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "neutral"


def build_valuation_view(assessment: ValuationAssessment | None, market: str) -> dict:
    """"Değerleme Analizi" paneli için TEK, paylaşılan context -- hem Derin
    Kart'ın geniş versiyonu hem Bilanço kartının kompakt versiyonu AYNI
    dict'i kullanır (bazı alanları göstermeyip bazılarını göstermek şablonun
    kendi tercihidir, veri KAYNAĞI tektir)."""
    if assessment is None or not assessment.has_data:
        return {"has_data": False}

    return {
        "has_data": True,
        "peer_count": assessment.peer_count,
        # Sektöre göreli (peer varsa dolu, yoksa None/verdict=None)
        "verdict": assessment.verdict,
        "verdict_class": _SECTOR_VERDICT_CLASS.get(assessment.verdict or "", "verdict-makul"),
        "verdict_reasoning": assessment.verdict_reasoning,
        "own_pe_display": _fmt_ratio(assessment.own_pe),
        "own_pb_display": _fmt_ratio(assessment.own_pb),
        "sector_avg_pe_display": _fmt_ratio(assessment.sector_avg_pe),
        "sector_avg_pb_display": _fmt_ratio(assessment.sector_avg_pb),
        "sector_implied_target_display": _fmt_currency(assessment.implied_target_price, market),
        "sector_implied_target_basis": assessment.implied_target_basis,
        "sector_implied_upside_display": _fmt_pct(assessment.implied_upside_pct),
        "sector_implied_upside_class": _pct_class(assessment.implied_upside_pct),
        # Momentum (peer'den BAĞIMSIZ)
        "price_change_1m_display": _fmt_pct(assessment.price_change_1m_pct),
        "price_change_1m_class": _pct_class(assessment.price_change_1m_pct),
        "price_change_3m_display": _fmt_pct(assessment.price_change_3m_pct),
        "price_change_3m_class": _pct_class(assessment.price_change_3m_pct),
        "momentum_note": assessment.momentum_note,
        # Benjamin Graham (peer'den BAĞIMSIZ)
        "graham_multiple_display": _fmt_ratio(assessment.graham_multiple),
        "graham_verdict": assessment.graham_verdict,
        "graham_verdict_class": _GRAHAM_VERDICT_CLASS.get(assessment.graham_verdict or "", "verdict-makul"),
        "graham_target_display": _fmt_currency(assessment.graham_fair_value_price, market),
        "graham_upside_display": _fmt_pct(assessment.graham_upside_pct),
        "graham_upside_class": _pct_class(assessment.graham_upside_pct),
        # Peter Lynch PEG (peer'den BAĞIMSIZ, büyüme verisi gerekir)
        "peg_ratio_display": _fmt_ratio(assessment.peg_ratio),
        "peg_verdict": assessment.peg_verdict,
        "peg_verdict_class": _PEG_VERDICT_CLASS.get(assessment.peg_verdict or "", "verdict-makul"),
        # Aswath Damodaran istikrarlı büyüme FCFE modeli (peer'den BAĞIMSIZ,
        # TTM net kâr + ROE + büyüme verisi gerekir)
        "damodaran_cost_of_equity_display": _fmt_pct(assessment.damodaran_cost_of_equity_pct),
        "damodaran_growth_used_display": _fmt_pct(assessment.damodaran_growth_used_pct),
        "damodaran_verdict": assessment.damodaran_verdict,
        "damodaran_verdict_class": _DAMODARAN_VERDICT_CLASS.get(assessment.damodaran_verdict or "", "verdict-makul"),
        "damodaran_target_display": _fmt_currency(assessment.damodaran_fair_value_price, market),
        "damodaran_upside_display": _fmt_pct(assessment.damodaran_upside_pct),
        "damodaran_upside_class": _pct_class(assessment.damodaran_upside_pct),
    }
