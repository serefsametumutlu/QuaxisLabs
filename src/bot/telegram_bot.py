"""Telegram bot komutlarini ve kullanici akisini yonetir (python-telegram-bot
v21+, async). Butun agir/senkron is (Is Yatirim/KAP fetch, Playwright
render) src.bot.pipeline.run_pipeline() icinde SENKRON calisir; burada
asyncio.to_thread() ile sarilir ki event loop bloklanmasin.

Bu modul sayi HESAPLAMAZ; sadece pipeline'in urettigi hazir sonuclari
Telegram mesajlarina/dosyalarina cevirir.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import time
from typing import IO

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.error import Conflict
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.request import HTTPXRequest

import config
from src.bot import menu, pipeline
from src.db import repository
from src.formatting import format_number_tr
from src.render import calendar_card, card

logger = logging.getLogger(__name__)

_LOCK_PATH = config.DATA_DIR / "bilanco_radar.lock"
_lock_file_handle: IO[str] | None = None  # process omru boyunca acik tutulur, GC ile kilit erken serbest kalmasin diye


def _acquire_single_instance_lock() -> None:
    """`main.py`'nin AYNI ANDA iki kez calistirilmasini engeller.

    Canli hata (bkz. kullanici raporu): iki `python main.py` sureci ayni
    Telegram token'iyla ayni anda polling yapinca Telegram API'si "409
    Conflict: terminated by other getUpdates request" donuyor VE guncellemeler
    (kullanici mesajlari) iki surec arasinda RASTGELE paylasiliyor -- bu da
    "ikinci hisseyi sorunca bot cevap vermiyor" belirtisine yol aciyordu
    (mesaj bazen OTEKI surece gidiyordu). Isletim sistemi seviyesinde
    ozel (exclusive) dosya kilidi kullanilir (Windows: msvcrt, POSIX: fcntl)
    -- surec cokse/ oldurulse bile OS kilidi otomatik serbest kalir, bu
    yuzden "eski PID dosyasi kaldi mi" turu manuel temizlik GEREKMEZ.
    """
    global _lock_file_handle
    _LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    handle = open(_LOCK_PATH, "w", encoding="utf-8")
    try:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        handle.close()
        raise RuntimeError(
            "Bilanço Radar botu zaten başka bir süreçte çalışıyor (lock dosyası: "
            f"{_LOCK_PATH}). Önce o süreci kapatın (görev yöneticisinden ilgili "
            "python.exe sürecini sonlandırın), sonra tekrar deneyin."
        ) from exc

    handle.write(str(os.getpid()))
    handle.flush()
    _lock_file_handle = handle  # referansi canli tut


async def _on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Application genel hata yakalayicisi. Conflict hatasi (bkz.
    _acquire_single_instance_lock docstring'i) artik kilit sayesinde normal
    kosullarda OLUSMAMALI; yine de gecici bir ag/Telegram taraflı çakışma
    olursa tam traceback yerine kisa bir uyari loglanir ki terminal spam
    olmasin."""
    if isinstance(context.error, Conflict):
        logger.warning(
            "Telegram getUpdates Conflict alindi (baska bir bot sureci mi calisiyor?): %s", context.error
        )
        return
    logger.exception("Beklenmeyen hata:", exc_info=context.error)

# BIST: 3-6 harf. NASDAQ: 1-5 harf, opsiyonel tek harfli ".X" sinif eki (orn.
# BRK.B, BF.B) -- Google'in GOOGL/GOOG'u gibi cift sembolluler zaten taban
# desenle (nokta olmadan) eslesir, sinif eki SADECE BRK.B turu semboller icin
# gerekir.
_TICKER_RE_BIST = re.compile(r"^[A-Z]{3,6}$")
_TICKER_RE_NASDAQ = re.compile(r"^[A-Z]{1,5}(\.[A-Z])?$")

# --- Es zamanlilik / hiz siniri (bellek-ici, tek surec varsayimiyla) -----------------------------------------------------

_active_users: set[int] = set()
_rate_limit_history: dict[int, list[float]] = {}
_RATE_LIMIT_MAX_REQUESTS = 3
_RATE_LIMIT_WINDOW_SECONDS = 60.0

_RETRY_PERIODS_KEY_PREFIX = "retry_periods:"


def normalize_ticker_input(text: str, market: str = "BIST") -> str | None:
    """'$thyao', '#THYAO ', 'thyao' -> 'THYAO'. Market'e gore beklenen
    desene (BIST: 3-6 harf, NASDAQ: 1-5 harf + opsiyonel .X sinif eki)
    uymuyorsa None doner. Varsayilan market="BIST" -- menu ONCESI mevcut
    kullanicilarin serbest metin ticker aliskanligi (bkz. handle_ticker_message)
    AYNEN korunur."""
    cleaned = text.strip().lstrip("$#").strip().upper()
    ticker_re = _TICKER_RE_NASDAQ if market == "NASDAQ" else _TICKER_RE_BIST
    return cleaned if ticker_re.fullmatch(cleaned) else None


def _check_rate_limit(user_id: int) -> bool:
    """True: istege izin var (ve bu istek sayaca eklendi). False: limit asildi."""
    now = time.monotonic()
    history = _rate_limit_history.setdefault(user_id, [])
    history[:] = [t for t in history if now - t < _RATE_LIMIT_WINDOW_SECONDS]
    if len(history) >= _RATE_LIMIT_MAX_REQUESTS:
        return False
    history.append(now)
    return True


# --- Komutlar -----------------------------------------------------


_HAKKINDA_TEXT = (
    "Bilanço Radar; çeyreklik finansal verileri İş Yatırım'dan, önemli "
    "şirket duyurularını KAP'tan çeker. Tüm sayısal hesaplamalar "
    "(yüzde değişim, oran, puan) kural tabanlı Python koduyla yapılır; "
    "yapay zeka SADECE bu hazır sayılara kısa sözel yorum ekler, hiçbir "
    "sayı üretmez.\n\n"
    "Kaynaklar: İş Yatırım, KAP (kap.org.tr)\n\n"
    "Bu içerik yatırım tavsiyesi değildir; yatırım kararı için "
    "profesyonel danışmanlık alınmalıdır."
)


async def _son_kartlar_metni() -> str:
    """cmd_son (/son) ve menu:son buton ekrani AYNI metni kullanir --
    orkestrasyon farkli (biri yeni mesaj, digeri edit_message_text) ama
    icerik TEK kaynaktan gelir."""
    with repository.get_session() as session:
        cards = repository.get_recent_cards(session, limit=5)

    if not cards:
        return "Henüz üretilmiş bir kart yok. Bir hisse kodu yazarak başlayabilirsin."

    lines = ["Son üretilen kartlar:"]
    for c in cards:
        skor = format_number_tr(c.score, decimals=2)
        lines.append(f"• #{c.ticker} — {c.created_at.strftime('%d.%m.%Y %H:%M')} — {skor}/10")
    return "\n".join(lines)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Merhaba! Ben Bilanço Radar 📊\n\n"
        "Bir BIST hisse kodu yazarsan (örn: THYAO), son çeyrek bilançosunu "
        "analiz edip kart olarak sana gönderirim: yıllık/çeyreklik değişimler, "
        "kural tabanlı puanlama ve önemli KAP bildirimleri dahil.\n\n"
        "Denemek için yaz: THYAO\n\n"
        "Ya da aşağıdaki menüden BİST/NASDAQ seçip ilerleyebilirsin "
        "(bu menü her zaman /menu ile tekrar açılır).\n\n"
        "Not: Bu içerik yatırım tavsiyesi değildir.",
        reply_markup=menu.build_root_menu(),
    )


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(menu.ROOT_MENU_TEXT, reply_markup=menu.build_root_menu())


async def cmd_hakkinda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(_HAKKINDA_TEXT)


async def cmd_son(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(await _son_kartlar_metni())


async def cmd_takvim(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/takvim -- menu:takvim ekranıyla AYNI (BİST/NASDAQ seçim) ekranını açar."""
    await update.message.reply_text(menu.TAKVIM_MENU_TEXT, reply_markup=menu.build_takvim_menu())


# --- Takvim (Faz 13) -----------------------------------------------------


async def _gonder_takvim(chat_id: int, context: ContextTypes.DEFAULT_TYPE, market: str) -> None:
    """DB önbelleğinden (pipeline.get_cached_earnings_calendar -- CANLI KAP/NASDAQ
    isteği ATMAZ, bkz. pipeline.py modül notu) okur, takvim kartını render eder
    ve görsel + kopyala-yapıştır metnini AYRI try/except'lerle gönderir (bkz.
    _execute_and_send'deki OTKAR dersi: biri başarısız olsa bile diğeri denenir)."""
    entries = await asyncio.to_thread(pipeline.get_cached_earnings_calendar, market, 30)
    takvim_context = calendar_card.build_calendar_context(entries, market)

    if takvim_context["is_empty"]:
        await context.bot.send_message(
            chat_id,
            f"📅 {takvim_context['market_label']} için şu an kesin/tahmini bir bilanço tarihi kaydı yok. "
            "Önbellek henüz oluşturulmamış ya da yakın zamanda kesin/tahmini bir açıklama yok olabilir, "
            "daha sonra tekrar dener misin?",
        )
        return

    out_path = config.DATA_DIR / "cards" / f"takvim_{market}.png"
    try:
        png_path = await asyncio.to_thread(
            card.render_card,
            takvim_context,
            str(out_path),
            "calendar_card.html",
            "#calendar-card",
        )
    except card.CardRenderError:
        logger.exception("%s takvim kartı render edilemedi", market)
        await context.bot.send_message(chat_id, "⚠️ Takvim görseli üretilemedi, birkaç dakika sonra tekrar dene.")
        return

    try:
        with open(png_path, "rb") as png_file:
            caption = f"📅 Yaklaşan Bilanço Tarihleri · {takvim_context['market_label']}"
            await context.bot.send_photo(chat_id=chat_id, photo=png_file, caption=caption)
    except Exception:
        logger.exception("%s takvim görseli gönderilemedi (metin yine de denenecek)", market)

    try:
        await context.bot.send_message(chat_id=chat_id, text=calendar_card.build_calendar_share_text(takvim_context))
    except Exception:
        logger.exception("%s takvim metni gönderilemedi", market)


# --- Analiz akisi -----------------------------------------------------


def _score_caption(sonuc: pipeline.PipelineResult) -> str:
    period_label = pipeline.quarter_label(sonuc.analysis.latest_period)
    skor = format_number_tr(sonuc.score.total_score, decimals=2)
    return f"#{sonuc.ticker} · {period_label}\nRadar Skoru: {skor}/10\n\nBu içerik yatırım tavsiyesi değildir."


def _skor_aciklama_satirlari(sonuc: pipeline.PipelineResult) -> list[str]:
    """Skorun ALT SATIRDAKI gerekcesi -- scorer.py'nin zaten her bilesen icin
    urettigi Turkce reasoning_tr metnini kullanir (kartta gosterilenle AYNI
    kaynak); boylece Telegram metni de "neden bu skor" sorusunu kendi
    icinde, goruntuye bakmadan cevaplar (kullanici istegi: tek basina
    paylasima hazir bir gonderi metni)."""
    skor = sonuc.score
    lines = [f"🎯 Radar Skoru: {format_number_tr(skor.total_score, decimals=2)}/10 ({skor.badge})", "", "Neden bu skor:"]
    for c in skor.components:
        skor_metni = f"{format_number_tr(c.score, decimals=1)}/10" if c.score is not None else "N/A"
        agirlik = format_number_tr(c.weight_nominal, decimals=0)
        lines.append(f"• {c.name} (%{agirlik} ağırlık) — {skor_metni}: {c.reasoning_tr}")
    return lines


def _bilanco_ozeti_metni(sonuc: pipeline.PipelineResult) -> str:
    """Karttaki ARTIŞLAR/AZALIŞLAR + BİLANÇO ÖZETİ + SKOR GEREKÇESİ ile AYNI
    icerigi duz metin olarak Telegram mesajina cevirir -- kullanici bunu
    goruntuyle BIRLIKTE, tek basina paylasima hazir (kopyala-yapistir) bir
    gonderi metni olarak kullanmak istedi."""
    period_label = pipeline.quarter_label(sonuc.analysis.latest_period)
    yorum = sonuc.commentary

    lines = [f"#{sonuc.ticker} · {period_label} Bilanço Özeti", ""]

    if yorum.positives:
        lines.append("📈 Artışlar:")
        lines.extend(f"• {p}" for p in yorum.positives)
        lines.append("")

    if yorum.negatives:
        lines.append("📉 Azalışlar:")
        lines.extend(f"• {n}" for n in yorum.negatives)
        lines.append("")

    lines.append("📋 Bilanço Özeti:")
    lines.append(yorum.summary)
    lines.append("")
    lines.extend(_skor_aciklama_satirlari(sonuc))
    return "\n".join(lines).strip()


async def _execute_and_send(
    ticker: str,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    periods=None,
    market: str = "BIST",
    allow_market_fallback: bool = False,
) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    started = time.monotonic()

    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)
        try:
            sonuc = await asyncio.to_thread(pipeline.run_pipeline, ticker, periods=periods, market=market)
        except pipeline.TickerNotFoundError:
            # CANLI kullanici raporu (2026-08-02): kullanici menuden 🇺🇸 NASDAQ
            # SECMEDEN dogrudan "AMD" yazdi -- varsayilan (menusuz) davranis
            # BIST'te aradigi icin "bulamadim" mesaji aldi, oysa AMD GERCEK ve
            # BUYUK bir NASDAQ sirketi (canli dogrulandi: sec_edgar.resolve_cik
            # aninda CIK donuyor). BIST ile NASDAQ evrenleri arasinda GERCEK bir
            # sembol cakismasi OLMADIGI canli dogrulandigindan (bkz.
            # 06_BILINEN_SORUNLAR.md B12), SADECE menusuz/varsayilan aramalarda
            # (allow_market_fallback=True, bkz. handle_ticker_message) BIST'te
            # bulunamayan bir ticker SESSIZCE NASDAQ'ta da denenir -- kullanici
            # ACIKCA 🇹🇷 BIST'i secmisse (menu uzerinden) bu fallback DEVREYE
            # GIRMEZ, kullanicinin acik tercihi ezilmez.
            if not (allow_market_fallback and market == "BIST"):
                raise
            logger.info("%s BIST'te bulunamadı, varsayılan aramada NASDAQ'ta da deneniyor", ticker)
            sonuc = await asyncio.to_thread(pipeline.run_pipeline, ticker, periods=periods, market="NASDAQ")
            market = "NASDAQ"

    except pipeline.TickerNotFoundError:
        if allow_market_fallback and market == "BIST":
            # Buraya gelindiyse hem BIST HEM NASDAQ denenmis (yukarida) ikisi de basarisiz olmus demektir.
            mesaj = f"❌ {ticker} diye bir hisse ne BİST'te ne NASDAQ'ta bulamadım. Kodu kontrol eder misin?"
        else:
            mesaj = f"❌ {ticker} diye bir hisse bulamadım. Kodu kontrol eder misin?"
        await context.bot.send_message(chat_id, mesaj)
        logger.info("istek user=%s ticker=%s sure=%.1fs sonuc=bulunamadi", user_id, ticker, time.monotonic() - started)

    except pipeline.FinancialDataNotFoundError:
        # CANLI hata (kullanici raporu, 2026-08-02): "SKHY" (SK hynix) SEC'te
        # KAYITLI ama hicbir finansal tablo (XBRL) verisi yok -- yabanci ozel
        # ihracci ABD standardinda raporlamiyor. "bulamadim" (yazim hatasi
        # izlenimi) yerine SEBEBI acikca belirten AYRI bir mesaj (bkz.
        # pipeline.FinancialDataNotFoundError docstring'i).
        await context.bot.send_message(
            chat_id,
            f"⚠️ {ticker} sembolünü SEC'te buldum ama hiçbir finansal tablo verisi yok. "
            "Bu genelde yabancı bir şirketin (ABD SEC standardında XBRL raporlamayan) "
            "sembolü olduğunda görülür. Farklı bir NASDAQ sembolü dener misin?",
        )
        logger.info("istek user=%s ticker=%s sure=%.1fs sonuc=veri_yok", user_id, ticker, time.monotonic() - started)

    except pipeline.PeriodNotAvailableError as exc:
        if exc.available_label is None:
            await context.bot.send_message(
                chat_id, f"⏳ {ticker} için {exc.requested_label} bilançosu henüz açıklanmamış görünüyor."
            )
        else:
            context.user_data[f"{_RETRY_PERIODS_KEY_PREFIX}{ticker}"] = exc.retry_periods
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Evet", callback_data=f"oncekidonem:evet:{ticker}"),
                        InlineKeyboardButton("Hayır", callback_data="oncekidonem:hayir"),
                    ]
                ]
            )
            await context.bot.send_message(
                chat_id,
                f"⏳ Bu şirketin {exc.requested_label} bilançosu henüz açıklanmamış görünüyor. "
                f"Son açıklanan: {exc.available_label} — ister misin onu analiz edeyim?",
                reply_markup=keyboard,
            )
        logger.info("istek user=%s ticker=%s sure=%.1fs sonuc=donem_yok", user_id, ticker, time.monotonic() - started)

    except pipeline.UnsupportedCompanyTypeError:
        await context.bot.send_message(
            chat_id,
            f"⚠️ {ticker} için finansal tablo formatı (banka/sigorta/aracı kurum) şu an desteklenmiyor.",
        )
        logger.info("istek user=%s ticker=%s sure=%.1fs sonuc=desteklenmiyor", user_id, ticker, time.monotonic() - started)

    except pipeline.DataSourceUnavailableError:
        await context.bot.send_message(chat_id, "Veri kaynağına şu an ulaşamıyorum, birkaç dakika sonra tekrar dene.")
        logger.info("istek user=%s ticker=%s sure=%.1fs sonuc=ag_hatasi", user_id, ticker, time.monotonic() - started)

    except Exception:
        logger.exception("istek user=%s ticker=%s beklenmeyen hata", user_id, ticker)
        await context.bot.send_message(chat_id, "Beklenmeyen bir hata oluştu, birkaç dakika sonra tekrar dener misin?")

    else:
        # CANLI hata (kullanici raporu, OTKAR): "gorsel geldi ama metin
        # gelmedi" -- eskiden send_photo/send_message TEK bir try/except
        # ALTINDA DEGILDI (hic try/except yoktu), send_photo bir
        # httpx.ReadTimeout ile patlarsa (bkz. build_application timeout
        # notu) send_message'a HIC ULASILMIYORDU. Artik IKISI AYRI
        # try/except ile korunur: biri basarisiz olsa bile digeri yine de
        # denenir, kullanici EN AZINDAN birini alir.
        try:
            with open(sonuc.png_path, "rb") as png_file:
                await context.bot.send_photo(chat_id=chat_id, photo=png_file, caption=_score_caption(sonuc))
        except Exception:
            logger.exception("istek user=%s ticker=%s: kart fotoğrafı gönderilemedi (özet metni yine de denenecek)", user_id, ticker)

        # §B18: en son basarili aramanin piyasasi (fallback ile degismis
        # olabilir, orn. BIST->NASDAQ) kalici hafizaya yazilir -- bir
        # sonraki menusuz/dogrudan ticker yazma varsayilani bunu kullanir.
        menu.set_son_market(context.user_data, market)

        try:
            # §B18: ozet mesajina "tek dokunusla yeni arama" butonlari
            # eklenir -- kullanici /menu -> Bilanço Analizi akisini BASTAN
            # gezmeden hemen baska bir piyasada/hissede arama baslatabilsin.
            await context.bot.send_message(
                chat_id=chat_id, text=_bilanco_ozeti_metni(sonuc), reply_markup=menu.build_sonuc_sonrasi_menu()
            )
        except Exception:
            logger.exception("istek user=%s ticker=%s: özet metni gönderilemedi", user_id, ticker)

        logger.info(
            "istek user=%s ticker=%s sure=%.1fs sonuc=basarili skor=%s",
            user_id, ticker, time.monotonic() - started, sonuc.score.total_score,
        )


async def handle_ticker_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Serbest metin ticker akisi. Menu uzerinden "Hisse kodunu yaz" butonuna
    basilmissa `context.user_data["bekleyen_islem"]` o market'i (TTL'li)
    belirtir; YOKSA (kullanici menuye HIC girmeden dogrudan "THYAO" yazdi)
    varsayilan market="BIST" ile ESKI davranis AYNEN calisir -- menu EK bir
    yol, yerine gecen degil (bkz. menu.py modul docstring'i)."""
    user = update.effective_user
    raw_text = update.message.text or ""

    islem = menu.peek_bekleyen_islem(context.user_data)
    # CANLI KULLANICI GERİ BİLDİRİMİ (§B18): menüsüz dogrudan ticker yazan
    # kullanicilar icin varsayilan piyasa ARTIK sabit "BIST" DEGIL -- en son
    # kullanilan/secilen piyasa (menu.get_son_market, TTL'siz) kullanilir.
    # Hic hicbir sey secilmemisse (ilk kullanim) "BIST" varsayilanina duser
    # (eski davranisla GERIYE UYUMLU).
    market = islem.market if islem is not None else menu.get_son_market(context.user_data)

    ticker = normalize_ticker_input(raw_text, market=market)
    if ticker is None:
        if market == "NASDAQ":
            await update.message.reply_text(
                "Anlayamadım. Lütfen 1-5 harfli bir NASDAQ sembolü yaz (örn: AAPL, BRK.B)."
            )
        else:
            await update.message.reply_text("Anlayamadım. Lütfen 3-6 harfli bir BIST hisse kodu yaz (örn: THYAO).")
        return

    if islem is not None:
        menu.clear_bekleyen_islem(context.user_data)

    if user.id in _active_users:
        await update.message.reply_text("⏳ Önceki isteğin hâlâ işleniyor, lütfen onu bekle.")
        return

    if not _check_rate_limit(user.id):
        await update.message.reply_text("🐢 Çok hızlı istek gönderiyorsun. Dakikada en fazla 3 analiz yapabilirim, biraz bekle.")
        return

    _active_users.add(user.id)
    try:
        await update.message.reply_text(f"🔍 {ticker} analiz ediliyor... (~20 sn)")
        # allow_market_fallback: SADECE menuden ACIKCA bir piyasa SECILMEDIYSE
        # (islem is None -- kullanici direkt "AMD" yazdi) True -- kullanici
        # menuden 🇹🇷 BIST'i ACIKCA secmisse bu fallback devreye GIRMEZ.
        await _execute_and_send(ticker, update, context, market=market, allow_market_fallback=islem is None)
    finally:
        _active_users.discard(user.id)


async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tum 'menu:...' callback_data'lari icin tek giris noktasi. Menu mesaji
    HER TIKLAMADA edit_message_text ile GUNCELLENIR -- yeni mesaj atilmaz
    (sohbet kirlenmesin diye, gorev talimati)."""
    query = update.callback_query
    await query.answer()

    parts = (query.data or "").split(":")
    screen = parts[1] if len(parts) > 1 else "root"
    sub = parts[2] if len(parts) > 2 else None

    if screen == "root":
        menu.clear_bekleyen_islem(context.user_data)
        await query.edit_message_text(menu.ROOT_MENU_TEXT, reply_markup=menu.build_root_menu())
        return

    if screen == "analiz":
        if sub == "bist":
            menu.set_bekleyen_islem(context.user_data, tip="analiz", market="BIST")
            menu.set_son_market(context.user_data, "BIST")
            await query.edit_message_text(menu.ANALIZ_BIST_PROMPT, reply_markup=menu.build_analiz_bekleniyor_menu())
        elif sub == "nasdaq":
            menu.set_bekleyen_islem(context.user_data, tip="analiz", market="NASDAQ")
            menu.set_son_market(context.user_data, "NASDAQ")
            await query.edit_message_text(menu.ANALIZ_NASDAQ_PROMPT, reply_markup=menu.build_analiz_bekleniyor_menu())
        else:
            menu.clear_bekleyen_islem(context.user_data)
            await query.edit_message_text(menu.ANALIZ_MENU_TEXT, reply_markup=menu.build_analiz_menu())
        return

    if screen == "takvim":
        if sub in ("bist", "nasdaq"):
            market = "BIST" if sub == "bist" else "NASDAQ"
            await query.edit_message_text(
                f"📅 {market} takvimi hazırlanıyor... (~birkaç saniye)", reply_markup=menu.build_takvim_iskelet_menu()
            )
            await _gonder_takvim(query.message.chat_id, context, market)
        else:
            await query.edit_message_text(menu.TAKVIM_MENU_TEXT, reply_markup=menu.build_takvim_menu())
        return

    if screen == "son":
        await query.edit_message_text(await _son_kartlar_metni(), reply_markup=menu.build_alt_ekran_menu())
        return

    if screen == "hakkinda":
        await query.edit_message_text(_HAKKINDA_TEXT, reply_markup=menu.build_alt_ekran_menu())
        return


async def handle_period_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    parts = (query.data or "").split(":")
    if len(parts) < 2 or parts[1] == "hayir":
        await query.edit_message_text("Tamam, iptal ettim.")
        return

    ticker = parts[2]
    retry_periods = context.user_data.pop(f"{_RETRY_PERIODS_KEY_PREFIX}{ticker}", None)

    user_id = update.effective_user.id
    if user_id in _active_users:
        await query.edit_message_text("⏳ Önceki isteğin hâlâ işleniyor, lütfen onu bekle.")
        return

    _active_users.add(user_id)
    try:
        await query.edit_message_text(f"🔍 {ticker} (önceki dönem) analiz ediliyor... (~20 sn)")
        await _execute_and_send(ticker, update, context, periods=retry_periods)
    finally:
        _active_users.discard(user_id)


# --- Uygulama kurulumu -----------------------------------------------------

_BOT_COMMANDS = [
    BotCommand("start", "Botu tanıt, menüyü aç"),
    BotCommand("menu", "Buton menüsünü aç"),
    BotCommand("son", "Son üretilen 5 kartı listele"),
    BotCommand("takvim", "Yaklaşan bilanço tarihleri (BİST/NASDAQ)"),
    BotCommand("hakkinda", "Veri kaynakları ve sorumluluk reddi"),
]


async def _post_init(application: Application) -> None:
    """Telegram'in komut menusune (sohbette '/' yazinca cikan liste)
    Turkce aciklamalari kaydeder. run_polling baslamadan once, uygulama
    hazir olur olmaz bir kez calisir."""
    await application.bot.set_my_commands(_BOT_COMMANDS)


def build_application() -> Application:
    if not config.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN tanımlı değil (.env dosyasını kontrol edin).")

    # CANLI hata (kullanici raporu, OTKAR): kart PNG'leri ~2-2,5 MB -- PTB'nin
    # VARSAYILAN read_timeout'u (5sn) bu boyuttaki bir fotograf icin bazen
    # YETERSIZ kaliyordu. Telegram sunucu tarafinda yuklemeyi/isleme genelde
    # TAMAMLIYORDU ama istemci yanit beklerken httpx.ReadTimeout ile
    # PATLIYORDU -- bu da _execute_and_send'i (send_photo SONRASINDAKI
    # send_message'a hic ULASMADAN) yariminda kesiyordu: kullanici goreli
    # (Telegram sunucusu zaten almisti) ama ozet METIN hic gitmiyordu (bkz.
    # _execute_and_send, gonderim artik ayri try/except'lerle korunuyor).
    request = HTTPXRequest(connect_timeout=20.0, read_timeout=60.0, write_timeout=60.0, pool_timeout=20.0)
    application = (
        Application.builder().token(config.TELEGRAM_BOT_TOKEN).request(request).post_init(_post_init).build()
    )
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("menu", cmd_menu))
    application.add_handler(CommandHandler("son", cmd_son))
    application.add_handler(CommandHandler("takvim", cmd_takvim))
    application.add_handler(CommandHandler("hakkinda", cmd_hakkinda))
    application.add_handler(CallbackQueryHandler(handle_period_callback, pattern=r"^oncekidonem:"))
    application.add_handler(CallbackQueryHandler(handle_menu_callback, pattern=r"^menu:"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ticker_message))
    application.add_error_handler(_on_error)
    return application


def run_bot() -> None:
    config.setup_logging()
    errors = config.validate_config()
    if errors:
        for error in errors:
            logger.error(error)
        raise RuntimeError("Konfigürasyon eksik: " + "; ".join(errors))

    _acquire_single_instance_lock()
    application = build_application()
    logger.info("Bilanço Radar botu başlatılıyor (polling)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
