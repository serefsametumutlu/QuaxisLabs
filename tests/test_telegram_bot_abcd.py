"""src/bot/telegram_bot.py -- ABCD formasyon akışı testleri (Faz 6).

test_telegram_bot.py'nin modül notuyla AYNI ilke: gerçek bir asyncio event
loop KULLANILMAZ (Windows + Playwright + pytest-asyncio çakışması, bkz. o
dosyanın üst notu) -- handler'lar `_run_coro` ile elle sürülür, gerçek I/O
`asyncio.to_thread` monkeypatch'iyle senkrona indirgenir. Telegram API'sine
gerçek istek ATILMAZ (context.bot / update.callback_query TAMAMEN sahte).
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.bot import menu, telegram_bot


def _run_coro(coro):
    try:
        coro.send(None)
    except StopIteration as exc:
        return exc.value
    raise AssertionError(
        "coroutine gercek bir event loop'a ihtiyac duydu (bir await noktasinda askida kaldi) -- "
        "bu test yardimcisi sadece AsyncMock/trivial async fonksiyonlar icin calisir"
    )


async def _fake_to_thread(func, *args, **kwargs):
    return func(*args, **kwargs)


@pytest.fixture(autouse=True)
def _temiz_active_users_durumu():
    telegram_bot._active_users.clear()
    yield
    telegram_bot._active_users.clear()


def _fake_callback_update(data: str, chat_id: int = 12345, user_id: int = 1, *, edit_return=None):
    query = SimpleNamespace(
        data=data,
        answer=AsyncMock(),
        edit_message_text=AsyncMock(return_value=edit_return),
        message=SimpleNamespace(chat_id=chat_id),
    )
    update = SimpleNamespace(
        callback_query=query,
        effective_chat=SimpleNamespace(id=chat_id),
        effective_user=SimpleNamespace(id=user_id),
    )
    return update, query


def _fake_context(user_data: dict | None = None):
    return SimpleNamespace(user_data=user_data if user_data is not None else {})


# --- handle_abcd_callback: 'abcd:menu' -> mod secim klavyesi -----------------------------------------------------


def test_handle_abcd_callback_menu_mod_klavyesini_gosterir() -> None:
    update, query = _fake_callback_update("abcd:menu")
    _run_coro(telegram_bot.handle_abcd_callback(update, _fake_context()))

    query.answer.assert_awaited_once()
    query.edit_message_text.assert_awaited_once()
    (text,), kwargs = query.edit_message_text.await_args
    assert text == menu.ABCD_MODE_TEXT
    grid = [[b.callback_data for b in row] for row in kwargs["reply_markup"].inline_keyboard]
    assert grid == [["abcd:mode:tekli"], ["abcd:mode:tarama"], ["menu:formasyonlar"]]


# --- handle_abcd_callback: 'abcd:mode:{mode}' -> zaman dilimi klavyesi -----------------------------------------------------


@pytest.mark.parametrize("mode", ["tekli", "tarama"])
def test_handle_abcd_callback_mode_tf_klavyesini_gosterir(mode: str) -> None:
    update, query = _fake_callback_update(f"abcd:mode:{mode}")
    _run_coro(telegram_bot.handle_abcd_callback(update, _fake_context()))

    (text,), kwargs = query.edit_message_text.await_args
    assert text == menu.ABCD_TF_TEXT
    grid = [[b.callback_data for b in row] for row in kwargs["reply_markup"].inline_keyboard]
    assert grid[0] == [f"abcd:tf:{mode}:60", f"abcd:tf:{mode}:120", f"abcd:tf:{mode}:240", f"abcd:tf:{mode}:1D", f"abcd:tf:{mode}:1W"]
    assert grid[1] == ["abcd:menu"]


# --- handle_abcd_callback: 'abcd:tf:tekli:{tf}' -> bekleyen_islem kurar + ticker sorar -----------------------------------------------------


def test_handle_abcd_callback_tf_tekli_bekleyen_islem_kurar_ve_prompt_gosterir() -> None:
    user_data: dict = {}
    update, query = _fake_callback_update("abcd:tf:tekli:240")

    _run_coro(telegram_bot.handle_abcd_callback(update, _fake_context(user_data)))

    islem = menu.peek_bekleyen_islem(user_data)
    assert islem is not None
    assert islem.tip == "abcd"
    assert islem.market == "BIST"
    assert islem.extra == "240"

    (text,), kwargs = query.edit_message_text.await_args
    assert text == menu.ABCD_TEKLI_PROMPT
    grid = [[b.callback_data for b in row] for row in kwargs["reply_markup"].inline_keyboard]
    assert grid == [["abcd:mode:tekli"]]


# --- handle_abcd_callback: 'abcd:tf:tarama:{tf}' -> metin istemeden DOGRUDAN tarama baslar -----------------------------------------------------


def test_handle_abcd_callback_tf_tarama_metin_istemeden_dogrudan_baslar(monkeypatch) -> None:
    monkeypatch.setattr(telegram_bot.asyncio, "to_thread", _fake_to_thread)
    monkeypatch.setattr(telegram_bot.abcd_scanner, "get_bist_universe", lambda: ["THYAO", "TUPRS"])

    scan_calls: list[tuple] = []

    def _fake_scan(symbols, tf, params, lookback_bars, n_bars, workers, on_progress):
        scan_calls.append((symbols, tf, lookback_bars, n_bars, workers))
        return SimpleNamespace(
            tf=tf, scanned_at=datetime.now(timezone.utc), lookback_bars=lookback_bars, buys=[], sells=[], errors={}
        )

    monkeypatch.setattr(telegram_bot.abcd_scanner, "scan", _fake_scan)

    status = SimpleNamespace(edit_text=AsyncMock())
    user_data: dict = {}
    update, query = _fake_callback_update("abcd:tf:tarama:1D", edit_return=status)

    _run_coro(telegram_bot.handle_abcd_callback(update, _fake_context(user_data)))

    # Metin istenmedi -- bekleyen_islem HIC kurulmadi (tekli modun aksine).
    assert menu.peek_bekleyen_islem(user_data) is None

    # Ilk edit_message_text "basliyor" mesaji -- Geri butonu/prompt YOK.
    query.edit_message_text.assert_awaited_once()

    # Tarama gercekten cagirildi (abcd_scanner.get_bist_universe'dan gelen sembollerle).
    assert len(scan_calls) == 1
    symbols, tf, lookback_bars, n_bars, workers = scan_calls[0]
    assert symbols == ["THYAO", "TUPRS"]
    assert tf == "1D"
    assert lookback_bars == telegram_bot._ABCD_LOOKBACK_BARS
    assert n_bars == telegram_bot._ABCD_SCAN_N_BARS
    assert workers == telegram_bot._ABCD_SCAN_WORKERS

    # Sonuc raporu status.edit_text ile GONDERILDI (en az bir kez -- ilk ilerleme
    # + son rapor edit'i).
    assert status.edit_text.await_count >= 1
    son_metin = status.edit_text.await_args_list[-1].args[0]
    # Baslik MarkdownV2 icin kacislanir (orn. "AB\=CD"), bu yuzden kacislanmamis
    # kalan parcalar kontrol edilir (bkz. abcd_scanner.format_report/_escape_mdv2).
    assert "Tarama" in son_metin
    assert "BUY:" in son_metin


def test_handle_abcd_callback_tf_tarama_hata_durumunda_kullaniciya_bilgi_verir(monkeypatch) -> None:
    monkeypatch.setattr(telegram_bot.asyncio, "to_thread", _fake_to_thread)
    monkeypatch.setattr(telegram_bot.abcd_scanner, "get_bist_universe", lambda: ["THYAO"])

    def _patlar(*args, **kwargs):
        raise RuntimeError("scan patladi")

    monkeypatch.setattr(telegram_bot.abcd_scanner, "scan", _patlar)

    status = SimpleNamespace(edit_text=AsyncMock())
    update, query = _fake_callback_update("abcd:tf:tarama:240", edit_return=status)

    _run_coro(telegram_bot.handle_abcd_callback(update, _fake_context()))

    son_metin = status.edit_text.await_args_list[-1].args[0]
    assert "başarısız" in son_metin


# --- handle_ticker_message: tip='abcd' dogrudan _gonder_abcd_sinyal'e delege eder -----------------------------------------------------


def test_handle_ticker_message_abcd_bekleyen_islem_gonder_abcd_sinyal_cagirir(monkeypatch) -> None:
    calls = AsyncMock()
    monkeypatch.setattr(telegram_bot, "_gonder_abcd_sinyal", calls)
    execute_calls = AsyncMock()
    monkeypatch.setattr(telegram_bot, "_execute_and_send", execute_calls)

    user_data: dict = {}
    menu.set_bekleyen_islem(user_data, tip="abcd", market="BIST", extra="240")

    message = SimpleNamespace(text="THYAO", reply_text=AsyncMock())
    update = SimpleNamespace(
        message=message,
        effective_user=SimpleNamespace(id=9101),
        effective_chat=SimpleNamespace(id=4242),
    )
    context = SimpleNamespace(user_data=user_data, bot=SimpleNamespace(send_chat_action=AsyncMock()))

    _run_coro(telegram_bot.handle_ticker_message(update, context))

    calls.assert_awaited_once_with(4242, context, "THYAO", "BIST", "240")
    execute_calls.assert_not_awaited()
    assert "bekleyen_islem" not in user_data  # basarili girdiden sonra TUKETILDI
