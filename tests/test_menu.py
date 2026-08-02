"""src/bot/menu.py testleri: buton yapisi (callback_data semasi) + bekleyen_islem
TTL mantigi. Bu modul Telegram API'sine hic dokunmadigi icin tamamen senkron
ve saf mantik testleridir (bkz. test_telegram_bot.py modul docstring'i --
gercek Update/Application gerektiren akislar orada da ayni prensiple
sinirlidir)."""

from __future__ import annotations

import time

import pytest

from src.bot import menu


# --- Menu yapisi (callback_data semasi) -----------------------------------------------------


def _callback_data_grid(markup) -> list[list[str]]:
    return [[button.callback_data for button in row] for row in markup.inline_keyboard]


def test_build_root_menu_dort_dal_icerir() -> None:
    grid = _callback_data_grid(menu.build_root_menu())
    assert grid == [["menu:analiz"], ["menu:takvim"], ["menu:son"], ["menu:hakkinda"]]


def test_build_analiz_menu_bist_nasdaq_ve_geri_icerir() -> None:
    grid = _callback_data_grid(menu.build_analiz_menu())
    assert grid == [["menu:analiz:bist"], ["menu:analiz:nasdaq"], ["menu:root"]]


def test_build_takvim_menu_bist_nasdaq_ve_geri_icerir() -> None:
    grid = _callback_data_grid(menu.build_takvim_menu())
    assert grid == [["menu:takvim:bist"], ["menu:takvim:nasdaq"], ["menu:root"]]


def test_build_analiz_bekleniyor_menu_geri_analiz_menusune_doner() -> None:
    grid = _callback_data_grid(menu.build_analiz_bekleniyor_menu())
    assert grid == [["menu:analiz"]]


def test_build_takvim_iskelet_menu_geri_takvim_menusune_doner() -> None:
    grid = _callback_data_grid(menu.build_takvim_iskelet_menu())
    assert grid == [["menu:takvim"]]


def test_build_alt_ekran_menu_geri_ana_menuye_doner() -> None:
    grid = _callback_data_grid(menu.build_alt_ekran_menu())
    assert grid == [["menu:root"]]


@pytest.mark.parametrize(
    "callback_data",
    [
        "menu:analiz",
        "menu:analiz:bist",
        "menu:analiz:nasdaq",
        "menu:takvim",
        "menu:takvim:bist",
        "menu:takvim:nasdaq",
        "menu:son",
        "menu:hakkinda",
        "menu:root",
    ],
)
def test_tum_callback_data_degerleri_64_byte_siniri_altinda(callback_data: str) -> None:
    assert len(callback_data.encode("utf-8")) <= 64


# --- bekleyen_islem TTL -----------------------------------------------------


def test_set_ve_peek_bekleyen_islem_market_bilgisini_korur() -> None:
    user_data: dict = {}
    menu.set_bekleyen_islem(user_data, tip="analiz", market="NASDAQ")
    islem = menu.peek_bekleyen_islem(user_data)
    assert islem is not None
    assert islem.tip == "analiz"
    assert islem.market == "NASDAQ"


def test_peek_bekleyen_islem_yokken_none_doner() -> None:
    assert menu.peek_bekleyen_islem({}) is None


def test_peek_bekleyen_islem_silmez_tekrar_okunabilir() -> None:
    """Kullanici gecersiz bir sey yazip TEKRAR deneyebilmeli -- peek, tuketmeden
    (silmeden) okur; sadece handle_ticker_message basarili bir ticker
    ALDIKTAN SONRA clear_bekleyen_islem ile tuketir."""
    user_data: dict = {}
    menu.set_bekleyen_islem(user_data, tip="analiz", market="BIST")
    assert menu.peek_bekleyen_islem(user_data) is not None
    assert menu.peek_bekleyen_islem(user_data) is not None
    assert "bekleyen_islem" in user_data


def test_clear_bekleyen_islem_kaldirir() -> None:
    user_data: dict = {}
    menu.set_bekleyen_islem(user_data, tip="analiz", market="BIST")
    menu.clear_bekleyen_islem(user_data)
    assert menu.peek_bekleyen_islem(user_data) is None


def test_clear_bekleyen_islem_yokken_hata_vermez() -> None:
    menu.clear_bekleyen_islem({})  # patlamamali


def test_peek_bekleyen_islem_suresi_dolmussa_none_doner_ve_temizler(monkeypatch) -> None:
    user_data: dict = {}
    menu.set_bekleyen_islem(user_data, tip="analiz", market="BIST")

    # TTL'i (10 dk) asan bir zaman noktasina "isinlan".
    gercek_expires_at = user_data["bekleyen_islem"].expires_at
    monkeypatch.setattr(time, "monotonic", lambda: gercek_expires_at + 1.0)

    assert menu.peek_bekleyen_islem(user_data) is None
    assert "bekleyen_islem" not in user_data


def test_set_bekleyen_islem_eskisinin_uzerine_yazar() -> None:
    user_data: dict = {}
    menu.set_bekleyen_islem(user_data, tip="analiz", market="BIST")
    menu.set_bekleyen_islem(user_data, tip="analiz", market="NASDAQ")
    islem = menu.peek_bekleyen_islem(user_data)
    assert islem.market == "NASDAQ"
