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


def test_build_root_menu_yedi_dal_icerir() -> None:
    grid = _callback_data_grid(menu.build_root_menu())
    assert grid == [
        ["menu:analiz"],
        ["menu:teknikanaliz"],
        ["menu:derinanaliz"],
        ["menu:fonanaliz"],
        ["menu:takvim"],
        ["menu:son"],
        ["menu:hakkinda"],
    ]


def test_build_analiz_menu_bist_nasdaq_ve_geri_icerir() -> None:
    grid = _callback_data_grid(menu.build_analiz_menu())
    assert grid == [["menu:analiz:bist"], ["menu:analiz:nasdaq"], ["menu:root"]]


def test_build_teknik_menu_bist_nasdaq_ve_geri_icerir() -> None:
    grid = _callback_data_grid(menu.build_teknik_menu())
    assert grid == [["menu:teknikanaliz:bist"], ["menu:teknikanaliz:nasdaq"], ["menu:root"]]


def test_build_teknik_bekleniyor_menu_teknikanaliz_ekranina_doner() -> None:
    grid = _callback_data_grid(menu.build_teknik_bekleniyor_menu())
    assert grid == [["menu:teknikanaliz"]]


def test_build_derin_menu_bist_nasdaq_ve_geri_icerir() -> None:
    grid = _callback_data_grid(menu.build_derin_menu())
    assert grid == [["menu:derinanaliz:bist"], ["menu:derinanaliz:nasdaq"], ["menu:root"]]


def test_build_derin_bekleniyor_menu_derinanaliz_ekranina_doner() -> None:
    grid = _callback_data_grid(menu.build_derin_bekleniyor_menu())
    assert grid == [["menu:derinanaliz"]]


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
        "menu:teknikanaliz",
        "menu:teknikanaliz:bist",
        "menu:teknikanaliz:nasdaq",
        "menu:derinanaliz",
        "menu:derinanaliz:bist",
        "menu:derinanaliz:nasdaq",
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


# --- "son kullanılan piyasa" hafızası (§B18) -----------------------------------------------------


def test_get_son_market_hic_secilmemisse_bist_varsayilan() -> None:
    assert menu.get_son_market({}) == "BIST"


def test_set_ve_get_son_market_degeri_korur() -> None:
    user_data: dict = {}
    menu.set_son_market(user_data, "NASDAQ")
    assert menu.get_son_market(user_data) == "NASDAQ"


def test_set_son_market_ttlsiz_zaman_gecmesiyle_silinmez(monkeypatch) -> None:
    """bekleyen_islem'in AKSINE (10 dk TTL) son_market KALICIDIR -- zaman
    ilerlese de degeri korumali."""
    user_data: dict = {}
    menu.set_son_market(user_data, "NASDAQ")
    monkeypatch.setattr(time, "monotonic", lambda: time.monotonic() + 10_000.0)
    assert menu.get_son_market(user_data) == "NASDAQ"


# --- "sonuc sonrasi" hizli arama menusu (§B18) -----------------------------------------------------


def test_build_sonuc_sonrasi_menu_bist_ve_nasdaq_butonlari_icerir() -> None:
    grid = _callback_data_grid(menu.build_sonuc_sonrasi_menu())
    assert grid == [["menu:analiz:bist", "menu:analiz:nasdaq"]]


def test_build_sonuc_sonrasi_menu_ticker_market_verilirse_teknik_butonu_ekler() -> None:
    """Faz 15: ticker/market verildiginde en uste 'teknik:{market}:{ticker}'
    callback_data'li bir buton eklenir, mevcut BIST/NASDAQ butonlari korunur."""
    grid = _callback_data_grid(menu.build_sonuc_sonrasi_menu(ticker="THYAO", market="BIST"))
    assert grid == [["teknik:BIST:THYAO"], ["menu:analiz:bist", "menu:analiz:nasdaq"]]


def test_build_sonuc_sonrasi_menu_show_derin_analiz_ikinci_buton_ekler() -> None:
    """Derin Kart: SADECE show_derin_analiz=True iken teknik butonunun
    YANINA (ayni satirda) 'derin:{market}:{ticker}' callback'li buton eklenir."""
    grid = _callback_data_grid(
        menu.build_sonuc_sonrasi_menu(ticker="THYAO", market="BIST", show_derin_analiz=True)
    )
    assert grid == [["teknik:BIST:THYAO", "derin:BIST:THYAO"], ["menu:analiz:bist", "menu:analiz:nasdaq"]]


def test_build_sonuc_sonrasi_menu_show_derin_analiz_varsayilan_false() -> None:
    grid = _callback_data_grid(menu.build_sonuc_sonrasi_menu(ticker="THYAO", market="BIST"))
    assert grid[0] == ["teknik:BIST:THYAO"]


# --- "teknik sonrasi" temel analiz butonu (build_sonuc_sonrasi_menu'nun simetrigi) -----------------------------------------------------


def test_build_teknik_sonrasi_menu_derin_analiz_butonu_ve_teknikanaliz_arama_butonlarini_icerir() -> None:
    """'📊 Temel Analiz' butonu artik 'derin:...' callback'ine gider --
    Bilanço kartindaki '🔬 Detaylı Analiz' butonuyla AYNI hedef (kullanici
    sikayeti: eskiden tek ceyreklik karti tekrarliyordu)."""
    grid = _callback_data_grid(menu.build_teknik_sonrasi_menu(ticker="THYAO", market="BIST"))
    assert grid == [["derin:BIST:THYAO"], ["menu:teknikanaliz:bist", "menu:teknikanaliz:nasdaq"]]


def test_build_teknik_sonrasi_menu_nasdaq_ticker_ile_dogru_callback_uretir() -> None:
    grid = _callback_data_grid(menu.build_teknik_sonrasi_menu(ticker="AAPL", market="NASDAQ"))
    assert grid[0] == ["derin:NASDAQ:AAPL"]


@pytest.mark.parametrize("ticker,market", [("THYAO", "BIST"), ("AAPL", "NASDAQ"), ("BRK.B", "NASDAQ")])
def test_build_teknik_sonrasi_menu_callback_data_64_byte_siniri_altinda(ticker: str, market: str) -> None:
    grid = _callback_data_grid(menu.build_teknik_sonrasi_menu(ticker=ticker, market=market))
    for row in grid:
        for callback_data in row:
            assert len(callback_data.encode("utf-8")) <= 64
