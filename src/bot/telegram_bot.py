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
from src.bot import pipeline
from src.db import repository
from src.formatting import format_number_tr

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

_TICKER_RE = re.compile(r"^[A-Z]{3,6}$")

# --- Es zamanlilik / hiz siniri (bellek-ici, tek surec varsayimiyla) -----------------------------------------------------

_active_users: set[int] = set()
_rate_limit_history: dict[int, list[float]] = {}
_RATE_LIMIT_MAX_REQUESTS = 3
_RATE_LIMIT_WINDOW_SECONDS = 60.0

_RETRY_PERIODS_KEY_PREFIX = "retry_periods:"


def normalize_ticker_input(text: str) -> str | None:
    """'$thyao', '#THYAO ', 'thyao' -> 'THYAO'. 3-6 harf disinda bir sey
    girilirse (ya da bos/cok uzunsa) None doner."""
    cleaned = text.strip().lstrip("$#").strip().upper()
    return cleaned if _TICKER_RE.fullmatch(cleaned) else None


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


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Merhaba! Ben Bilanço Radar 📊\n\n"
        "Bir BIST hisse kodu yazarsan (örn: THYAO), son çeyrek bilançosunu "
        "analiz edip kart olarak sana gönderirim: yıllık/çeyreklik değişimler, "
        "kural tabanlı puanlama ve önemli KAP bildirimleri dahil.\n\n"
        "Denemek için yaz: THYAO\n\n"
        "Diğer komutlar: /son (son üretilen kartlar), /hakkinda\n\n"
        "Not: Bu içerik yatırım tavsiyesi değildir."
    )


async def cmd_hakkinda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Bilanço Radar; çeyreklik finansal verileri İş Yatırım'dan, önemli "
        "şirket duyurularını KAP'tan çeker. Tüm sayısal hesaplamalar "
        "(yüzde değişim, oran, puan) kural tabanlı Python koduyla yapılır; "
        "yapay zeka SADECE bu hazır sayılara kısa sözel yorum ekler, hiçbir "
        "sayı üretmez.\n\n"
        "Kaynaklar: İş Yatırım, KAP (kap.org.tr)\n\n"
        "Bu içerik yatırım tavsiyesi değildir; yatırım kararı için "
        "profesyonel danışmanlık alınmalıdır."
    )


async def cmd_son(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    with repository.get_session() as session:
        cards = repository.get_recent_cards(session, limit=5)

    if not cards:
        await update.message.reply_text("Henüz üretilmiş bir kart yok. Bir hisse kodu yazarak başlayabilirsin.")
        return

    lines = ["Son üretilen kartlar:"]
    for c in cards:
        skor = format_number_tr(c.score, decimals=2)
        lines.append(f"• #{c.ticker} — {c.created_at.strftime('%d.%m.%Y %H:%M')} — {skor}/10")
    await update.message.reply_text("\n".join(lines))


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


async def _execute_and_send(ticker: str, update: Update, context: ContextTypes.DEFAULT_TYPE, periods=None) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    started = time.monotonic()

    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)
        sonuc = await asyncio.to_thread(pipeline.run_pipeline, ticker, periods=periods)

    except pipeline.TickerNotFoundError:
        await context.bot.send_message(chat_id, f"❌ {ticker} diye bir hisse bulamadım. Kodu kontrol eder misin?")
        logger.info("istek user=%s ticker=%s sure=%.1fs sonuc=bulunamadi", user_id, ticker, time.monotonic() - started)

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

        try:
            await context.bot.send_message(chat_id=chat_id, text=_bilanco_ozeti_metni(sonuc))
        except Exception:
            logger.exception("istek user=%s ticker=%s: özet metni gönderilemedi", user_id, ticker)

        logger.info(
            "istek user=%s ticker=%s sure=%.1fs sonuc=basarili skor=%s",
            user_id, ticker, time.monotonic() - started, sonuc.score.total_score,
        )


async def handle_ticker_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    raw_text = update.message.text or ""

    ticker = normalize_ticker_input(raw_text)
    if ticker is None:
        await update.message.reply_text("Anlayamadım. Lütfen 3-6 harfli bir BIST hisse kodu yaz (örn: THYAO).")
        return

    if user.id in _active_users:
        await update.message.reply_text("⏳ Önceki isteğin hâlâ işleniyor, lütfen onu bekle.")
        return

    if not _check_rate_limit(user.id):
        await update.message.reply_text("🐢 Çok hızlı istek gönderiyorsun. Dakikada en fazla 3 analiz yapabilirim, biraz bekle.")
        return

    _active_users.add(user.id)
    try:
        await update.message.reply_text(f"🔍 {ticker} analiz ediliyor... (~20 sn)")
        await _execute_and_send(ticker, update, context)
    finally:
        _active_users.discard(user.id)


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
    BotCommand("start", "Botu tanıt, örnek kullanım göster"),
    BotCommand("son", "Son üretilen 5 kartı listele"),
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
    application.add_handler(CommandHandler("son", cmd_son))
    application.add_handler(CommandHandler("hakkinda", cmd_hakkinda))
    application.add_handler(CallbackQueryHandler(handle_period_callback, pattern=r"^oncekidonem:"))
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
