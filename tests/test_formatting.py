"""src/formatting.py -- Turkce sayi/yuzde/para birimi bicimlendirme
yardimcilarinin testleri. Bu modul projede sayi gosterimi icin TEK kaynak
oldugu icin (bkz. modul docstring'i) burada bulunan her hata butun projeye
(kart, LLM istemi, skor gerekceleri) yayilir.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.formatting import format_currency_short, format_number_tr, format_percent_tr


# --- format_number_tr -----------------------------------------------------


def test_format_number_tr_none_tire_doner() -> None:
    assert format_number_tr(None) == "-"


def test_format_number_tr_binlik_ayiraci_nokta() -> None:
    assert format_number_tr(Decimal("54189705323")) == "54.189.705.323"


def test_format_number_tr_ondalik_ayiraci_virgul() -> None:
    assert format_number_tr(Decimal("1234.5"), decimals=2) == "1.234,50"


def test_format_number_tr_negatif_deger_basina_eksi_koyar() -> None:
    assert format_number_tr(Decimal("-1234.5"), decimals=1) == "-1.234,5"


def test_format_number_tr_yuvarlama_yarim_yukari() -> None:
    assert format_number_tr(Decimal("1.25"), decimals=1) == "1,3"


def test_format_number_tr_sifir() -> None:
    assert format_number_tr(Decimal("0"), decimals=1) == "0,0"


# --- format_percent_tr -----------------------------------------------------


def test_format_percent_tr_none_tire_doner() -> None:
    assert format_percent_tr(None) == "-"


def test_format_percent_tr_pozitif_yuzde_isareti_basta() -> None:
    assert format_percent_tr(Decimal("20")) == "%20,0"


def test_format_percent_tr_negatif_deger_yuzde_onekinden_sonra_eksi() -> None:
    assert format_percent_tr(Decimal("-3.2")) == "%-3,2"


def test_format_percent_tr_sifir_eksi_isareti_almaz() -> None:
    assert format_percent_tr(Decimal("0")) == "%0,0"


def test_format_percent_tr_decimals_parametresi() -> None:
    assert format_percent_tr(Decimal("20.456"), decimals=2) == "%20,46"


def test_format_percent_tr_int_ve_float_da_kabul_eder() -> None:
    assert format_percent_tr(20) == "%20,0"
    assert format_percent_tr(-3.2) == "%-3,2"


# --- format_currency_short -----------------------------------------------------


def test_format_currency_short_none_tire_doner() -> None:
    assert format_currency_short(None) == "-"


def test_format_currency_short_milyar_kisaltir() -> None:
    assert format_currency_short(Decimal("5420000000")) == "5,4 mr ₺"


def test_format_currency_short_milyon_kisaltir() -> None:
    assert format_currency_short(Decimal("3500000")) == "3,5 mn ₺"


def test_format_currency_short_kucuk_tutar_tam_sayi_binlik_ayiracli() -> None:
    assert format_currency_short(Decimal("125000")) == "125.000 ₺"


def test_format_currency_short_negatif_tutar_basa_eksi_koyar() -> None:
    assert format_currency_short(Decimal("-5420000000")) == "-5,4 mr ₺"


def test_format_currency_short_ozel_sembol() -> None:
    assert format_currency_short(Decimal("1000000"), symbol="$") == "1,0 mn $"


@pytest.mark.parametrize("deger", [Decimal("999999999"), Decimal("999999"), Decimal("0")])
def test_format_currency_short_sinir_degerlerinde_cokmez(deger) -> None:
    # Sadece cokmedigini dogrula; esik siniri tam olcum degil.
    assert format_currency_short(deger)
