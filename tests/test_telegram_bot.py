"""src/bot/telegram_bot.py -- saf mantik testleri (ticker normalizasyonu,
hiz siniri) + handle_ticker_message/handle_menu_callback icin SimpleNamespace
tabanli sahte Update/Context nesneleriyle davranis testleri (gercek Telegram
API'sine BAGLANMAZ -- context.bot.send_photo/send_message gibi gercek
Application gerektiren _execute_and_send AsyncMock ile degistirilir).
Uctan uca akis (gercek pipeline.run_pipeline cagrisi) tests/test_pipeline.py,
scripts/demo_pipeline.py ve canli Telegram testiyle dogrulanir.
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.ai.commentary import Commentary
from src.bot import menu, telegram_bot


# --- normalize_ticker_input (BIST, varsayilan market) -----------------------------------------------------


@pytest.mark.parametrize(
    "girdi,beklenen",
    [
        ("THYAO", "THYAO"),
        ("thyao", "THYAO"),
        ("$thyao", "THYAO"),
        ("#THYAO", "THYAO"),
        ("  thyao  ", "THYAO"),
        ("#$thyao", "THYAO"),
        ("bim", "BIM"),
    ],
)
def test_normalize_ticker_input_gecerli_kodlar(girdi, beklenen) -> None:
    assert telegram_bot.normalize_ticker_input(girdi) == beklenen


@pytest.mark.parametrize("girdi", ["ab", "abcdefg", "thy4o", "", "   ", "thy ao", "12345"])
def test_normalize_ticker_input_gecersiz_girdi_none_doner(girdi) -> None:
    assert telegram_bot.normalize_ticker_input(girdi) is None


# --- normalize_ticker_input (NASDAQ, market="NASDAQ") -----------------------------------------------------


@pytest.mark.parametrize(
    "girdi,beklenen",
    [
        ("AAPL", "AAPL"),
        ("aapl", "AAPL"),
        ("A", "A"),
        ("GOOGL", "GOOGL"),
        ("$aapl", "AAPL"),
        ("brk.b", "BRK.B"),
        ("BRK.B", "BRK.B"),
        ("  aapl  ", "AAPL"),
    ],
)
def test_normalize_ticker_input_nasdaq_gecerli_kodlar(girdi, beklenen) -> None:
    assert telegram_bot.normalize_ticker_input(girdi, market="NASDAQ") == beklenen


@pytest.mark.parametrize("girdi", ["", "123", "abcdef", "BRK.BB", "THYAOX", "brk..b", "brk-b"])
def test_normalize_ticker_input_nasdaq_gecersiz_girdi_none_doner(girdi) -> None:
    assert telegram_bot.normalize_ticker_input(girdi, market="NASDAQ") is None


def test_normalize_ticker_input_market_ayrimi_capraz_gecersiz() -> None:
    """6 harfli bir kod BIST icin gecerliyken (3-6 harf) NASDAQ icin GECERSIZ
    (azami 5 harf); tek harfli bir kod NASDAQ icin gecerliyken BIST icin
    GECERSIZ (asgari 3 harf) -- iki market'in dogrulamasi birbirinden
    BAGIMSIZ."""
    assert telegram_bot.normalize_ticker_input("ABCDEF", market="BIST") == "ABCDEF"
    assert telegram_bot.normalize_ticker_input("ABCDEF", market="NASDAQ") is None
    assert telegram_bot.normalize_ticker_input("A", market="NASDAQ") == "A"
    assert telegram_bot.normalize_ticker_input("A", market="BIST") is None


# --- _check_rate_limit -----------------------------------------------------


@pytest.fixture(autouse=True)
def _temiz_rate_limit_durumu():
    telegram_bot._rate_limit_history.clear()
    yield
    telegram_bot._rate_limit_history.clear()


def test_check_rate_limit_ilk_uc_istek_izinli() -> None:
    user_id = 111
    assert telegram_bot._check_rate_limit(user_id) is True
    assert telegram_bot._check_rate_limit(user_id) is True
    assert telegram_bot._check_rate_limit(user_id) is True


def test_check_rate_limit_dorduncu_istek_reddedilir() -> None:
    user_id = 222
    for _ in range(3):
        telegram_bot._check_rate_limit(user_id)
    assert telegram_bot._check_rate_limit(user_id) is False


def test_check_rate_limit_kullanicilar_birbirinden_bagimsiz() -> None:
    for _ in range(3):
        telegram_bot._check_rate_limit(111)
    assert telegram_bot._check_rate_limit(222) is True


def test_check_rate_limit_pencere_disina_cikan_istekler_sayilmaz() -> None:
    user_id = 333
    # Gecmis, pencerenin (60s) disinda kalacak sekilde elle dolduruluyor.
    telegram_bot._rate_limit_history[user_id] = [0.0, 0.0, 0.0]
    assert telegram_bot._check_rate_limit(user_id) is True


# --- _bilanco_ozeti_metni -----------------------------------------------------


def _sahte_bilesen(name: str, score: Decimal | None, weight: str, reasoning: str) -> SimpleNamespace:
    return SimpleNamespace(name=name, score=score, weight_nominal=Decimal(weight), reasoning_tr=reasoning)


def _sahte_sonuc(positives: list[str], negatives: list[str], summary: str = "Genel değerlendirme metni.") -> SimpleNamespace:
    yorum = Commentary(
        headline="BAŞLIK", summary=summary, positives=positives, negatives=negatives,
        kap_note=None, disclaimer_context=None, source="llm",
    )
    skor = SimpleNamespace(
        total_score=Decimal("8.5"),
        badge="SAĞLAM",
        components=[
            _sahte_bilesen("Kârlılık", Decimal("7.0"), "20", "Net marj güçlü."),
            _sahte_bilesen("Nakit Üretimi", None, "21", "FAVÖK hesaplanamadı."),
        ],
    )
    return SimpleNamespace(
        ticker="TESTAS",
        analysis=SimpleNamespace(latest_period=(2026, 3), is_annual_only=False),
        score=skor,
        commentary=yorum,
    )


def test_bilanco_ozeti_metni_basligi_ve_donemi_icerir() -> None:
    text = telegram_bot._bilanco_ozeti_metni(_sahte_sonuc(["artış"], ["azalış"]))
    assert "#TESTAS · 1Ç26 Bilanço Özeti" in text


def test_bilanco_ozeti_metni_artislari_madde_isaretiyle_listeler() -> None:
    text = telegram_bot._bilanco_ozeti_metni(_sahte_sonuc(["Hasılat arttı.", "Kâr arttı."], []))
    assert "📈 Artışlar:" in text
    assert "• Hasılat arttı." in text
    assert "• Kâr arttı." in text


def test_bilanco_ozeti_metni_azalislari_madde_isaretiyle_listeler() -> None:
    text = telegram_bot._bilanco_ozeti_metni(_sahte_sonuc([], ["Nakit azaldı."]))
    assert "📉 Azalışlar:" in text
    assert "• Nakit azaldı." in text


def test_bilanco_ozeti_metni_genel_degerlendirmeyi_icerir() -> None:
    text = telegram_bot._bilanco_ozeti_metni(_sahte_sonuc([], [], summary="Şirket sağlam görünüyor."))
    assert "Şirket sağlam görünüyor." in text


def test_bilanco_ozeti_metni_bos_listelerde_baslik_gostermez() -> None:
    text = telegram_bot._bilanco_ozeti_metni(_sahte_sonuc([], []))
    assert "📈 Artışlar:" not in text
    assert "📉 Azalışlar:" not in text


def test_bilanco_ozeti_metni_skor_ve_gerekceyi_icerir() -> None:
    """Kullanici istegi: gonderi metni (goruntuyle BIRLIKTE tek basina
    paylasilabilir olsun diye) skoru VE "neden bu skor" gerekcesini de
    icermeli -- kartta zaten gosterilen scorer.py bilesen gerekceleriyle
    AYNI kaynaktan."""
    text = telegram_bot._bilanco_ozeti_metni(_sahte_sonuc(["artış"], []))
    assert "🎯 Radar Skoru: 8,50/10 (SAĞLAM)" in text
    assert "Neden bu skor:" in text
    assert "• Kârlılık (%20 ağırlık) — 7,0/10: Net marj güçlü." in text
    assert "• Nakit Üretimi (%21 ağırlık) — N/A: FAVÖK hesaplanamadı." in text


# --- handle_ticker_message / handle_menu_callback: menu bekleyen_islem entegrasyonu + geriye uyumluluk -----------------------------------------------------
#
# NOT: pytest.mark.asyncio / gercek bir asyncio event loop KULLANILMIYOR.
# CANLI hata (bu oturumda gozlemlendi): tests/test_card.py'deki GERCEK
# Playwright PNG render testi calistiktan SONRA, ayni pytest surecinde
# calisan HERHANGI bir asyncio.Runner/pytest-asyncio cagrisi "Cannot run
# the event loop while another loop is running" ile PATLIYOR (Windows +
# Python 3.14 + Playwright sync API'nin ProactorEventLoop'u process
# genelinde bozmasi -- src/render/card.py'nin thread-local Playwright
# singleton'iyla ilgili, bu FAZIN kapsami DISINDA bir ortam sorunu).
# Test edilen handler'lar (asagida) hicbir GERCEK I/O/timer/thread
# beklemiyor -- hepsi AsyncMock veya trivial async fonksiyon cagiriyor --
# bu yuzden coroutine'ler gercek bir event loop OLMADAN elle "surulur"
# (_run_coro), boylece test_card.py'nin bozdugu global asyncio durumuna
# hic dokunulmaz.


def _run_coro(coro):
    try:
        coro.send(None)
    except StopIteration as exc:
        return exc.value
    raise AssertionError(
        "coroutine gercek bir event loop'a ihtiyac duydu (bir await noktasinda askida kaldi) -- "
        "bu test yardimcisi sadece AsyncMock/trivial async fonksiyonlar icin calisir"
    )


@pytest.fixture(autouse=True)
def _temiz_active_users_durumu():
    telegram_bot._active_users.clear()
    yield
    telegram_bot._active_users.clear()


def _fake_update(text: str, user_id: int):
    message = SimpleNamespace(text=text, reply_text=AsyncMock())
    return SimpleNamespace(message=message, effective_user=SimpleNamespace(id=user_id))


def _fake_context(user_data: dict | None = None):
    return SimpleNamespace(user_data=user_data if user_data is not None else {})


def test_handle_ticker_message_bekleyen_islem_yokken_varsayilan_bist(monkeypatch) -> None:
    """Kullanici menuye HIC girmeden dogrudan 'THYAO' yazarsa bu YINE
    calismali (varsayilan market: BIST) -- gorev talimati, mevcut kullanici
    aliskanligi korunmali."""
    calls = AsyncMock()
    monkeypatch.setattr(telegram_bot, "_execute_and_send", calls)

    update = _fake_update("THYAO", user_id=9001)
    context = _fake_context()
    _run_coro(telegram_bot.handle_ticker_message(update, context))

    calls.assert_awaited_once()
    _, kwargs = calls.await_args
    assert calls.await_args.args[0] == "THYAO"
    assert kwargs["market"] == "BIST"
    assert kwargs["allow_market_fallback"] is True  # menu SECILMEDI -> NASDAQ fallback'e izinli


def test_handle_ticker_message_nasdaq_bekleyen_islem_market_nasdaq_kullanir(monkeypatch) -> None:
    calls = AsyncMock()
    monkeypatch.setattr(telegram_bot, "_execute_and_send", calls)

    user_data: dict = {}
    menu.set_bekleyen_islem(user_data, tip="analiz", market="NASDAQ")

    update = _fake_update("AAPL", user_id=9002)
    context = _fake_context(user_data)
    _run_coro(telegram_bot.handle_ticker_message(update, context))

    calls.assert_awaited_once()
    assert calls.await_args.args[0] == "AAPL"
    assert calls.await_args.kwargs["market"] == "NASDAQ"
    assert calls.await_args.kwargs["allow_market_fallback"] is False  # menuden ACIKCA secildi -> fallback YOK
    assert "bekleyen_islem" not in user_data  # basarili girdiden sonra TUKETILIR


def test_handle_ticker_message_bekleyen_islem_yokken_son_market_kullanilir(monkeypatch) -> None:
    """CANLI KULLANICI GERİ BİLDİRİMİ (§B18): kullanıcı önceki aramasında
    NASDAQ seçmişse (son_market kalıcı hafızası), bekleyen_islem OLMADAN
    (menüsüz) yazdığı bir sonraki ticker de varsayılan olarak NASDAQ'ta
    aranmalı -- artık HER ZAMAN sabit "BIST" değil."""
    calls = AsyncMock()
    monkeypatch.setattr(telegram_bot, "_execute_and_send", calls)

    user_data: dict = {}
    menu.set_son_market(user_data, "NASDAQ")

    update = _fake_update("AAPL", user_id=9010)
    context = _fake_context(user_data)
    _run_coro(telegram_bot.handle_ticker_message(update, context))

    calls.assert_awaited_once()
    assert calls.await_args.kwargs["market"] == "NASDAQ"
    assert calls.await_args.kwargs["allow_market_fallback"] is True  # menuden ACIKCA secilmedi (bekleyen_islem yok)


def test_handle_ticker_message_nasdaq_noktali_sembolu_dogru_normalize_eder(monkeypatch) -> None:
    calls = AsyncMock()
    monkeypatch.setattr(telegram_bot, "_execute_and_send", calls)

    user_data: dict = {}
    menu.set_bekleyen_islem(user_data, tip="analiz", market="NASDAQ")

    update = _fake_update("brk.b", user_id=9003)
    context = _fake_context(user_data)
    _run_coro(telegram_bot.handle_ticker_message(update, context))

    assert calls.await_args.args[0] == "BRK.B"


def test_handle_ticker_message_nasdaq_bekleyen_islemken_gecersiz_girdi_state_korunur(monkeypatch) -> None:
    """NASDAQ icin gecersiz bir kod (BIST kalibinda 6 harf) yazilirsa bekleyen
    islem SILINMEMELI ki kullanici tekrar deneyebilsin."""
    calls = AsyncMock()
    monkeypatch.setattr(telegram_bot, "_execute_and_send", calls)

    user_data: dict = {}
    menu.set_bekleyen_islem(user_data, tip="analiz", market="NASDAQ")

    update = _fake_update("THYAOX", user_id=9004)
    context = _fake_context(user_data)
    _run_coro(telegram_bot.handle_ticker_message(update, context))

    calls.assert_not_awaited()
    update.message.reply_text.assert_awaited_once()
    (msg,), _ = update.message.reply_text.await_args
    assert "NASDAQ" in msg
    assert "bekleyen_islem" in user_data  # state KORUNDU


def test_handle_ticker_message_bist_gecersiz_girdi_orijinal_mesaji_korur(monkeypatch) -> None:
    calls = AsyncMock()
    monkeypatch.setattr(telegram_bot, "_execute_and_send", calls)

    update = _fake_update("AB", user_id=9005)
    context = _fake_context()
    _run_coro(telegram_bot.handle_ticker_message(update, context))

    calls.assert_not_awaited()
    update.message.reply_text.assert_awaited_once_with(
        "Anlayamadım. Lütfen 3-6 harfli bir BIST hisse kodu yaz (örn: THYAO)."
    )


def test_handle_ticker_message_suresi_dolmus_bekleyen_islem_bist_varsayilanina_doner(monkeypatch) -> None:
    import time as time_module

    calls = AsyncMock()
    monkeypatch.setattr(telegram_bot, "_execute_and_send", calls)

    user_data: dict = {}
    menu.set_bekleyen_islem(user_data, tip="analiz", market="NASDAQ")
    expires_at = user_data["bekleyen_islem"].expires_at
    monkeypatch.setattr(time_module, "monotonic", lambda: expires_at + 1.0)

    update = _fake_update("THYAO", user_id=9006)
    context = _fake_context(user_data)
    _run_coro(telegram_bot.handle_ticker_message(update, context))

    assert calls.await_args.kwargs["market"] == "BIST"


# --- handle_menu_callback: her menu dali + geri butonu -----------------------------------------------------


def _fake_callback_update(data: str, chat_id: int = 12345, user_id: int = 1):
    query = SimpleNamespace(
        data=data,
        answer=AsyncMock(),
        edit_message_text=AsyncMock(),
        message=SimpleNamespace(chat_id=chat_id),
    )
    # effective_chat/effective_user: gercek telegram.Update bunlari
    # callback_query'den OTOMATIK turetir (handle_temel_callback gibi
    # _execute_and_send'e delege eden handler'lar bunlara ihtiyac duyar).
    update = SimpleNamespace(
        callback_query=query,
        effective_chat=SimpleNamespace(id=chat_id),
        effective_user=SimpleNamespace(id=user_id),
    )
    return update, query


def test_handle_menu_callback_root_ana_menuyu_gosterir_ve_bekleyeni_temizler() -> None:
    user_data: dict = {}
    menu.set_bekleyen_islem(user_data, tip="analiz", market="NASDAQ")
    update, query = _fake_callback_update("menu:root")

    _run_coro(telegram_bot.handle_menu_callback(update, _fake_context(user_data)))

    query.answer.assert_awaited_once()
    query.edit_message_text.assert_awaited_once()
    (text,), kwargs = query.edit_message_text.await_args
    assert text == menu.ROOT_MENU_TEXT
    assert kwargs["reply_markup"].inline_keyboard[0][0].callback_data == "menu:analiz"
    assert "bekleyen_islem" not in user_data


def test_handle_ticker_message_teknik_bekleyen_islem_dogrudan_teknik_gonderir(monkeypatch) -> None:
    """/teknik -> BİST seçildikten sonra ticker yazılınca fundamental
    pipeline'a HİÇ UĞRAMADAN doğrudan _gonder_teknik çağrılır (bkz.
    cmd_teknik/menu:teknikanaliz -- BekleyenIslem.tip="teknik")."""
    teknik_calls = AsyncMock()
    monkeypatch.setattr(telegram_bot, "_gonder_teknik", teknik_calls)
    execute_calls = AsyncMock()
    monkeypatch.setattr(telegram_bot, "_execute_and_send", execute_calls)

    user_data: dict = {}
    menu.set_bekleyen_islem(user_data, tip="teknik", market="BIST")

    message = SimpleNamespace(text="THYAO", reply_text=AsyncMock())
    update = SimpleNamespace(
        message=message,
        effective_user=SimpleNamespace(id=9101),
        effective_chat=SimpleNamespace(id=4242),
    )
    context = SimpleNamespace(user_data=user_data, bot=SimpleNamespace(send_chat_action=AsyncMock()))

    _run_coro(telegram_bot.handle_ticker_message(update, context))

    teknik_calls.assert_awaited_once_with(4242, context, "THYAO", "BIST")
    execute_calls.assert_not_awaited()
    assert "bekleyen_islem" not in user_data


def test_handle_menu_callback_analiz_ust_menu_secenekleri_gosterir() -> None:
    update, query = _fake_callback_update("menu:analiz")
    _run_coro(telegram_bot.handle_menu_callback(update, _fake_context()))

    (text,), kwargs = query.edit_message_text.await_args
    assert text == menu.ANALIZ_MENU_TEXT
    grid = [[b.callback_data for b in row] for row in kwargs["reply_markup"].inline_keyboard]
    assert grid == [["menu:analiz:bist"], ["menu:analiz:nasdaq"], ["menu:root"]]


def test_handle_menu_callback_analiz_bist_bekleyen_islem_ayarlar_ve_prompt_gosterir() -> None:
    user_data: dict = {}
    update, query = _fake_callback_update("menu:analiz:bist")
    _run_coro(telegram_bot.handle_menu_callback(update, _fake_context(user_data)))

    (text,), _ = query.edit_message_text.await_args
    assert text == menu.ANALIZ_BIST_PROMPT
    assert user_data["bekleyen_islem"].market == "BIST"
    assert menu.get_son_market(user_data) == "BIST"  # §B18: bir sonraki menusuz aramanin varsayilani


def test_handle_menu_callback_analiz_nasdaq_bekleyen_islem_ayarlar_ve_prompt_gosterir() -> None:
    user_data: dict = {}
    update, query = _fake_callback_update("menu:analiz:nasdaq")
    _run_coro(telegram_bot.handle_menu_callback(update, _fake_context(user_data)))

    (text,), _ = query.edit_message_text.await_args
    assert text == menu.ANALIZ_NASDAQ_PROMPT
    assert user_data["bekleyen_islem"].market == "NASDAQ"
    assert menu.get_son_market(user_data) == "NASDAQ"  # §B18: bir sonraki menusuz aramanin varsayilani


def test_handle_menu_callback_teknikanaliz_ust_menu_secenekleri_gosterir() -> None:
    update, query = _fake_callback_update("menu:teknikanaliz")
    _run_coro(telegram_bot.handle_menu_callback(update, _fake_context()))

    (text,), kwargs = query.edit_message_text.await_args
    assert text == menu.TEKNIK_MENU_TEXT
    grid = [[b.callback_data for b in row] for row in kwargs["reply_markup"].inline_keyboard]
    assert grid == [["menu:teknikanaliz:bist"], ["menu:teknikanaliz:nasdaq"], ["menu:root"]]


def test_handle_menu_callback_teknikanaliz_bist_bekleyen_islem_ayarlar_ve_prompt_gosterir() -> None:
    user_data: dict = {}
    update, query = _fake_callback_update("menu:teknikanaliz:bist")
    _run_coro(telegram_bot.handle_menu_callback(update, _fake_context(user_data)))

    (text,), _ = query.edit_message_text.await_args
    assert text == menu.TEKNIK_BIST_PROMPT
    assert user_data["bekleyen_islem"].tip == "teknik"
    assert user_data["bekleyen_islem"].market == "BIST"


def test_handle_menu_callback_teknikanaliz_nasdaq_bekleyen_islem_ayarlar_ve_prompt_gosterir() -> None:
    user_data: dict = {}
    update, query = _fake_callback_update("menu:teknikanaliz:nasdaq")
    _run_coro(telegram_bot.handle_menu_callback(update, _fake_context(user_data)))

    (text,), _ = query.edit_message_text.await_args
    assert text == menu.TEKNIK_NASDAQ_PROMPT
    assert user_data["bekleyen_islem"].tip == "teknik"
    assert user_data["bekleyen_islem"].market == "NASDAQ"


def test_handle_menu_callback_takvim_ust_menu_secenekleri_gosterir() -> None:
    update, query = _fake_callback_update("menu:takvim")
    _run_coro(telegram_bot.handle_menu_callback(update, _fake_context()))

    (text,), kwargs = query.edit_message_text.await_args
    assert text == menu.TAKVIM_MENU_TEXT
    grid = [[b.callback_data for b in row] for row in kwargs["reply_markup"].inline_keyboard]
    assert grid == [["menu:takvim:bist"], ["menu:takvim:nasdaq"], ["menu:root"]]


def test_handle_menu_callback_takvim_bist_hazirlaniyor_gosterir_ve_gonderir(monkeypatch) -> None:
    """Faz 13: skeleton 'yakında eklenecek' metni yerine artık gerçek
    _gonder_takvim() çağrılır (bkz. src/bot/pipeline.py::get_cached_earnings_calendar
    -- DB önbelleğinden okur, canlı KAP isteği atmaz)."""
    calls = AsyncMock()
    monkeypatch.setattr(telegram_bot, "_gonder_takvim", calls)
    update, query = _fake_callback_update("menu:takvim:bist", chat_id=555)

    _run_coro(telegram_bot.handle_menu_callback(update, _fake_context()))

    (text,), _ = query.edit_message_text.await_args
    assert "BIST" in text
    calls.assert_awaited_once()
    assert calls.await_args.args[0] == 555
    assert calls.await_args.args[2] == "BIST"


def test_handle_menu_callback_takvim_nasdaq_hazirlaniyor_gosterir_ve_gonderir(monkeypatch) -> None:
    calls = AsyncMock()
    monkeypatch.setattr(telegram_bot, "_gonder_takvim", calls)
    update, query = _fake_callback_update("menu:takvim:nasdaq", chat_id=777)

    _run_coro(telegram_bot.handle_menu_callback(update, _fake_context()))

    (text,), _ = query.edit_message_text.await_args
    assert "NASDAQ" in text
    calls.assert_awaited_once()
    assert calls.await_args.args[0] == 777
    assert calls.await_args.args[2] == "NASDAQ"


# --- Teknik Görünüm callback (Faz 15) -----------------------------------------------------


def _fake_context_with_bot():
    return SimpleNamespace(bot=SimpleNamespace(send_chat_action=AsyncMock()), user_data={})


def test_handle_teknik_callback_market_ve_ticker_ayristirir_ve_gonderir(monkeypatch) -> None:
    calls = AsyncMock()
    monkeypatch.setattr(telegram_bot, "_gonder_teknik", calls)
    update, query = _fake_callback_update("teknik:BIST:THYAO", chat_id=999)
    context = _fake_context_with_bot()

    _run_coro(telegram_bot.handle_teknik_callback(update, context))

    query.answer.assert_awaited_once()
    calls.assert_awaited_once_with(999, context, "THYAO", "BIST")


def test_handle_teknik_callback_eksik_veri_sessizce_gecer(monkeypatch) -> None:
    """callback_data beklenen 3 parcadan azsa (bozuk/eski veri) handler
    sessizce cikar -- _gonder_teknik cagirilmaz."""
    calls = AsyncMock()
    monkeypatch.setattr(telegram_bot, "_gonder_teknik", calls)
    update, query = _fake_callback_update("teknik:BIST")

    _run_coro(telegram_bot.handle_teknik_callback(update, _fake_context_with_bot()))

    calls.assert_not_awaited()


# --- Temel Analiz callback (handle_teknik_callback'in simetrigi) -----------------------------------------------------


def test_handle_temel_callback_market_ve_ticker_ayristirir_ve_execute_and_send_cagirir(monkeypatch) -> None:
    calls = AsyncMock()
    monkeypatch.setattr(telegram_bot, "_execute_and_send", calls)
    update, query = _fake_callback_update("temel:NASDAQ:AAPL", chat_id=999, user_id=42)
    context = _fake_context_with_bot()

    _run_coro(telegram_bot.handle_temel_callback(update, context))

    query.answer.assert_awaited_once()
    calls.assert_awaited_once_with("AAPL", update, context, market="NASDAQ")


def test_handle_temel_callback_eksik_veri_sessizce_gecer(monkeypatch) -> None:
    calls = AsyncMock()
    monkeypatch.setattr(telegram_bot, "_execute_and_send", calls)
    update, query = _fake_callback_update("temel:BIST")

    _run_coro(telegram_bot.handle_temel_callback(update, _fake_context_with_bot()))

    calls.assert_not_awaited()


def test_handle_menu_callback_son_kartlar_metnini_gosterir(monkeypatch) -> None:
    monkeypatch.setattr(telegram_bot, "_son_kartlar_metni", AsyncMock(return_value="sahte kart listesi"))
    update, query = _fake_callback_update("menu:son")
    _run_coro(telegram_bot.handle_menu_callback(update, _fake_context()))

    (text,), kwargs = query.edit_message_text.await_args
    assert text == "sahte kart listesi"
    grid = [[b.callback_data for b in row] for row in kwargs["reply_markup"].inline_keyboard]
    assert grid == [["menu:root"]]


def test_handle_menu_callback_hakkinda_metnini_gosterir() -> None:
    update, query = _fake_callback_update("menu:hakkinda")
    _run_coro(telegram_bot.handle_menu_callback(update, _fake_context()))

    (text,), kwargs = query.edit_message_text.await_args
    assert text == telegram_bot._HAKKINDA_TEXT
    assert kwargs["reply_markup"].inline_keyboard[0][0].callback_data == "menu:root"


# --- _execute_and_send: NASDAQ fallback (menusuz arama) -----------------------------------------------------
#
# _execute_and_send() ic. asyncio.to_thread(pipeline.run_pipeline, ...) cagirir --
# bu GERCEK bir thread/event-loop iso gerektirir, _run_coro'nun "trivial
# async/AsyncMock" varsayimini BOZAR. Bu yuzden asyncio.to_thread BURADA
# senkron bir sahteyle degistirilir (fonksiyonu dogrudan cagirir) -- geri
# kalan (context.bot.* cagrilari) zaten AsyncMock.


async def _fake_to_thread(func, *args, **kwargs):
    return func(*args, **kwargs)


def _fake_pipeline_result(ticker: str, png_path) -> SimpleNamespace:
    return SimpleNamespace(
        ticker=ticker,
        analysis=SimpleNamespace(latest_period=(2026, 6), is_annual_only=False),
        score=SimpleNamespace(total_score=Decimal("5.0"), badge="DENGELİ", components=[]),
        commentary=SimpleNamespace(positives=[], negatives=[], summary="Özet."),
        png_path=str(png_path),
    )


def _fake_bot_context_for_execute(chat_id=555, user_id=9100):
    bot = SimpleNamespace(send_chat_action=AsyncMock(), send_photo=AsyncMock(), send_message=AsyncMock())
    # user_data={} -- gercek telegram.ext Context'te HER ZAMAN vardir (bkz.
    # menu.set_son_market cagrisi, §B18); bos dict basari yolunun bunu
    # yazabilmesi icin yeterli.
    context = SimpleNamespace(bot=bot, user_data={})
    update = SimpleNamespace(effective_chat=SimpleNamespace(id=chat_id), effective_user=SimpleNamespace(id=user_id))
    return update, context


def test_execute_and_send_basarida_son_market_yazar_ve_hizli_menu_ekler(tmp_path, monkeypatch) -> None:
    """§B18: basarili bir analiz sonrasi (a) son_market kalici hafizaya
    yazilir (bir sonraki menusuz aramanin varsayilanini belirler) ve (b)
    ozet mesajina "tek dokunusla yeni arama" butonlari (build_sonuc_sonrasi_
    menu) eklenir -- kullanici /menu akisini bastan gezmek ZORUNDA kalmaz."""
    monkeypatch.setattr(telegram_bot.asyncio, "to_thread", _fake_to_thread)

    png_path = tmp_path / "thyao.png"
    png_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 20)
    sonuc = _fake_pipeline_result("THYAO", png_path)
    monkeypatch.setattr(telegram_bot.pipeline, "run_pipeline", lambda ticker, periods=None, market="BIST": sonuc)

    update, context = _fake_bot_context_for_execute()
    _run_coro(telegram_bot._execute_and_send("THYAO", update, context, market="BIST"))

    assert menu.get_son_market(context.user_data) == "BIST"
    _, kwargs = context.bot.send_message.await_args
    assert kwargs["reply_markup"] == menu.build_sonuc_sonrasi_menu(ticker="THYAO", market="BIST")


def test_execute_and_send_bist_basarisizsa_nasdaqta_dener(tmp_path, monkeypatch) -> None:
    """CANLI kullanıcı raporu (2026-08-02): 'AMD' menüden 🇺🇸 NASDAQ seçilmeden
    yazıldığında varsayılan BİST'te aranıp bulunamıyordu -- oysa AMD gerçek
    (ve büyük) bir NASDAQ şirketi. allow_market_fallback=True iken BİST
    başarısız olursa NASDAQ OTOMATİK denenmeli."""
    monkeypatch.setattr(telegram_bot.asyncio, "to_thread", _fake_to_thread)

    png_path = tmp_path / "amd.png"
    png_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 20)
    sonuc = _fake_pipeline_result("AMD", png_path)

    calls: list[str] = []

    def sahte_run_pipeline(ticker, periods=None, market="BIST"):
        calls.append(market)
        if market == "BIST":
            raise telegram_bot.pipeline.TickerNotFoundError(f"{ticker} bulunamadı")
        return sonuc

    monkeypatch.setattr(telegram_bot.pipeline, "run_pipeline", sahte_run_pipeline)

    update, context = _fake_bot_context_for_execute()
    _run_coro(telegram_bot._execute_and_send("AMD", update, context, market="BIST", allow_market_fallback=True))

    assert calls == ["BIST", "NASDAQ"]
    context.bot.send_photo.assert_awaited_once()
    context.bot.send_message.assert_awaited_once()  # basari (ozet) mesaji -- "bulamadim" DEGIL


def test_execute_and_send_acikca_bist_secilmisse_nasdaq_denenmez(monkeypatch) -> None:
    """Kullanıcı menüden AÇIKÇA 🇹🇷 BİST'i seçmişse (allow_market_fallback=False),
    BİST'te bulunamayan bir ticker için NASDAQ fallback DEVREYE GİRMEMELİ --
    kullanıcının açık tercihi sessizce ezilmemeli."""
    monkeypatch.setattr(telegram_bot.asyncio, "to_thread", _fake_to_thread)

    calls: list[str] = []

    def sahte_run_pipeline(ticker, periods=None, market="BIST"):
        calls.append(market)
        raise telegram_bot.pipeline.TickerNotFoundError(f"{ticker} bulunamadı")

    monkeypatch.setattr(telegram_bot.pipeline, "run_pipeline", sahte_run_pipeline)

    update, context = _fake_bot_context_for_execute()
    _run_coro(telegram_bot._execute_and_send("XXXXXX", update, context, market="BIST", allow_market_fallback=False))

    assert calls == ["BIST"]  # NASDAQ HIC denenmedi
    (_, text), _ = context.bot.send_message.await_args
    assert "bulamadım" in text


def test_execute_and_send_her_ikisi_de_basarisizsa_iki_piyasayi_da_belirtir(monkeypatch) -> None:
    monkeypatch.setattr(telegram_bot.asyncio, "to_thread", _fake_to_thread)

    def sahte_run_pipeline(ticker, periods=None, market="BIST"):
        raise telegram_bot.pipeline.TickerNotFoundError(f"{ticker} bulunamadı")

    monkeypatch.setattr(telegram_bot.pipeline, "run_pipeline", sahte_run_pipeline)

    update, context = _fake_bot_context_for_execute()
    _run_coro(telegram_bot._execute_and_send("ZZZZZZ", update, context, market="BIST", allow_market_fallback=True))

    (_, text), _ = context.bot.send_message.await_args
    assert "BİST" in text and "NASDAQ" in text
