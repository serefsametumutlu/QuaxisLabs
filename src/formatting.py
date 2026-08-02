"""Turkce sayi/para birimi formatlama yardimcilari.

Kural: binlik ayraci nokta, ondalik ayraci virgul (orn. 54.189.705.323).
Bu modul tum projede sayi gosterimi icin TEK kaynak olmali; baska hicbir
yerde manuel string formatlama yapilmamali.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

_BILLION = Decimal("1000000000")
_MILLION = Decimal("1000000")


def format_number_tr(value: Decimal | int | float | None, decimals: int = 0) -> str:
    """Sayiyi Turkce formatta yazdirir: binlik ayrac nokta, ondalik ayrac virgul.

    Ornek: format_number_tr(Decimal("54189705323")) -> '54.189.705.323'
           format_number_tr(Decimal("1234.5"), decimals=2) -> '1.234,50'
    """
    if value is None:
        return "-"

    quant = Decimal(1).scaleb(-decimals) if decimals else Decimal(1)
    quantized = Decimal(value).quantize(quant, rounding=ROUND_HALF_UP)

    negative = quantized < 0
    quantized = abs(quantized)

    # Once ingilizce bicimde formatla (1,234,567.89), sonra ayiraclari
    # takas et; bu locale modulune bagimli olmadigi icin platform bagimsizdir.
    english = f"{quantized:,.{decimals}f}"
    turkish = english.replace(",", "_").replace(".", ",").replace("_", ".")
    return f"-{turkish}" if negative else turkish


def format_percent_tr(value: Decimal | int | float | None, decimals: int = 1) -> str:
    """Yuzde degerini '%' onekiyle yazdirir; eksi isareti format_number_tr'nin
    kendi kuralina gore rakamin basina gelir (orn. '%-3,2').

    Ornek: format_percent_tr(Decimal("20")) -> '%20,0'
           format_percent_tr(Decimal("-3.2")) -> '%-3,2'
    """
    if value is None:
        return "-"
    return f"%{format_number_tr(value, decimals=decimals)}"


def format_currency_short(value: Decimal | int | float | None, symbol: str = "₺") -> str:
    """Buyuk TL tutarlarini milyar/milyon olarak kisaltir. Orn: 54,2 mr ₺.

    1 milyar TL ve uzeri -> 'mr' (milyar), 1 milyon TL ve uzeri -> 'mn' (milyon),
    daha kucuk tutarlar -> tam sayi olarak binlik ayracli gosterilir.
    """
    if value is None:
        return "-"

    amount = Decimal(value)
    negative = amount < 0
    magnitude = abs(amount)

    if magnitude >= _BILLION:
        scaled = magnitude / _BILLION
        text = f"{format_number_tr(scaled, decimals=1)} mr {symbol}"
    elif magnitude >= _MILLION:
        scaled = magnitude / _MILLION
        text = f"{format_number_tr(scaled, decimals=1)} mn {symbol}"
    else:
        text = f"{format_number_tr(magnitude, decimals=0)} {symbol}"

    return f"-{text}" if negative else text
