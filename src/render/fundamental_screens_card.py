"""Faz 21: "Değerleme" kartı context builder'ı.

src/render/technical_card.py ile AYNI ilke: bu modül HİÇBİR sayı
HESAPLAMAZ -- src.analysis.fundamental_screens.compute_fundamental_screens()
zaten hesaplanmış bir `FundamentalScreens` verir, burada SADECE Türkçe
biçimlendirme + renk/rozet eşleme yapılır.

Kullanıcı isteği (2026-08-05/06): eski "Değerleme Analizi" panelinin
(card.html/deep_card.html içinde, sektör karşılaştırması + Damodaran)
YERİNE -- doğrudan bilançoya EKLENMEDEN, AYRI bir "Değerleme" ekranı/kartı.
Burada SEKTÖR/PEER karşılaştırması HİÇ YOKTUR (kullanıcı: "sektörel...
gelmesin bi değer bu değerleme için") -- sadece şirketin kendi verisinden
hesaplanan 4 bağımsız yöntem: Benjamin Graham, Joel Greenblatt Sihirli
Formül, Tobias Carlisle Acquirer's Multiple, Joseph Piotroski F-Skoru.

GÖRSEL KİMLİK BİLEREK temel analiz kartından (card.html) VE teknik
görünümden (technical_card.html) AYRI: yeşil/zümrüt aksan + "DEĞERLEME"
başlığı.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from src.analysis.fundamental_screens import FundamentalScreens
from src.formatting import format_currency_short, format_number_tr, format_percent_tr

_DISCLAIMER = "Bu içerik yatırım tavsiyesi değildir; yatırım kararı için profesyonel danışmanlık alınmalıdır."
_DATA_SOURCE_NOTE = "İş Yatırım (XI_29 finansal tablolar), KAP"

# Turkce bant/rozet kelimelerinin renk sinifina eslenmesi -- 4 yontemin
# HEPSI (Graham/Greenblatt/Carlisle/Piotroski) "iyi/notr/kotu" ucunu AYNI
# 3 kelimeden birine (bkz. fundamental_screens.py sabitleri) yazdigi icin
# TEK bir esleme tablosu yeterli, her yontem icin ayri fonksiyon GEREKMEZ.
_BAND_CLASS: dict[str, str] = {
    "Ucuz": "positive",
    "Yüksek": "positive",
    "Güçlü": "positive",
    "Graham Ölçütüne Göre Ucuz": "positive",
    "Makul": "neutral",
    "Orta": "neutral",
    "Pahalı": "negative",
    "Düşük": "negative",
    "Zayıf": "negative",
    "Graham Ölçütüne Göre Pahalı": "negative",
}


def _band_class(band: str | None) -> str:
    if band is None:
        return "neutral"
    return _BAND_CLASS.get(band, "neutral")


def _num(value: Decimal | None, decimals: int = 2) -> str:
    return format_number_tr(value, decimals) if value is not None else "N/A"


def _pct(value: Decimal | None, decimals: int = 1) -> str:
    return format_percent_tr(value, decimals) if value is not None else "N/A"


def _try(value: Decimal | None) -> str:
    return f"{format_number_tr(value, 2)} ₺" if value is not None else "N/A"


def _short_try(value: Decimal | None) -> str:
    return format_currency_short(value) if value is not None else "N/A"


def _build_graham(screens: FundamentalScreens) -> dict:
    g = screens.graham
    if g is None:
        return {"has_data": False}
    return {
        "has_data": True,
        "verdict": g.verdict,
        "verdict_class": _band_class(g.verdict),
        "multiple_display": _num(g.graham_multiple),
        "fair_value_display": _try(g.fair_value_price),
        "upside_display": _pct(g.upside_pct),
        "upside_class": "positive" if (g.upside_pct is not None and g.upside_pct >= 0) else "negative",
    }


def _build_greenblatt(screens: FundamentalScreens) -> dict:
    gb = screens.greenblatt
    if gb is None:
        return {"has_data": False}
    return {
        "has_data": True,
        "earnings_yield_display": _pct(gb.earnings_yield_pct),
        "earnings_yield_band": gb.earnings_yield_band,
        "earnings_yield_class": _band_class(gb.earnings_yield_band),
        "return_on_capital_display": _pct(gb.return_on_capital_pct),
        "return_on_capital_band": gb.return_on_capital_band,
        "return_on_capital_class": _band_class(gb.return_on_capital_band),
        "ebit_display": _short_try(gb.ebit),
        "enterprise_value_display": _short_try(gb.enterprise_value),
    }


def _build_acquirers_multiple(screens: FundamentalScreens) -> dict:
    am = screens.acquirers_multiple
    if am is None:
        return {"has_data": False}
    return {
        "has_data": True,
        "multiple_display": _num(am.acquirers_multiple),
        "band": am.band,
        "band_class": _band_class(am.band),
    }


def _build_piotroski(screens: FundamentalScreens) -> dict:
    p = screens.piotroski
    if p is None:
        return {"has_data": False}
    details = [
        {
            "label": label,
            # Kural 3: eksik veri (None) "basarisiz" DEGIL, ayri bir "veri yok"
            # durumu -- ✓/✗ yerine "—" gosterilir (bkz. fundamental_screens.py
            # modul notu).
            "icon": "✓" if passed else ("✗" if passed is False else "—"),
            "icon_class": "positive" if passed else ("negative" if passed is False else "neutral"),
        }
        for label, passed in p.details
    ]
    return {
        "has_data": True,
        "score_display": str(p.score),
        "criteria_evaluated_display": str(p.criteria_evaluated),
        "band": p.band,
        "band_class": _band_class(p.band),
        "details": details,
    }


def build_fundamental_screens_context(
    screens: FundamentalScreens | None,
    ticker: str,
    applicable: bool,
    company_name: str | None = None,
    price: Decimal | None = None,
    now: datetime | None = None,
) -> dict:
    """`screens`: `src.analysis.fundamental_screens.compute_fundamental_screens()`
    çıktısı (uygulanamaz bir şirket türüyse `None`). `applicable=False`
    (banka/sigorta/katılım bankası/NASDAQ) ise kart "bu değerleme yöntemleri
    bu şirket türüne uygulanamaz" der (Kural 3: uydurma yapmak yerine
    dürüstçe eksikliği bildirir) -- `screens.has_data=False` (veri
    bulunamadı) durumundan AYRI, farklı bir metinle gösterilir."""
    now = now or datetime.now()

    base = {
        "ticker": ticker,
        "company_name": company_name,
        "price_display": _try(price) if price is not None else None,
        "report_timestamp": now.strftime("%d.%m.%Y %H:%M"),
        "data_sources_note": _DATA_SOURCE_NOTE,
        "disclaimer": _DISCLAIMER,
        "applicable": applicable,
    }

    if not applicable or screens is None:
        return {**base, "has_data": False}

    return {
        **base,
        "has_data": screens.has_data,
        "graham": _build_graham(screens),
        "greenblatt": _build_greenblatt(screens),
        "acquirers_multiple": _build_acquirers_multiple(screens),
        "piotroski": _build_piotroski(screens),
    }
