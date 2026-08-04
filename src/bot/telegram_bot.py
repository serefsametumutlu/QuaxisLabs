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
from telegram.error import Conflict, NetworkError
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.request import HTTPXRequest

import config
from src.analysis import calculator, technical, trends
from src.bot import menu, pipeline
from src.db import models, repository
from src.fetchers import price_history
from src.formatting import format_number_tr
from src.render import calendar_card, card, deep_card, technical_card

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
    if isinstance(context.error, NetworkError):
        # Gecici DNS/baglanti kesintisi (orn. httpx.ConnectError: getaddrinfo
        # failed) -- PTB'nin kendi network_retry_loop'u bunu zaten otomatik
        # tekrar dener (canli dogrulandi: birkac saniye sonra getUpdates
        # yeniden 200 donuyor), bu yuzden FATAL degil. Once tam traceback
        # "Beklenmeyen hata" olarak loglaniyordu -- her gecici internet
        # kesintisinde terminali dev bir stack trace ile dolduruyordu.
        logger.warning("Telegram'a gecici olarak ulasilamadi (otomatik tekrar denenecek): %s", context.error)
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


async def cmd_teknik(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/teknik -- Faz 15 teknik görünüm için BİST/NASDAQ seçim ekranını açar.
    Öncesinde teknik kart SADECE bir analiz sonucunun altındaki butondan
    erişilebiliyordu (bkz. handle_teknik_callback); bu komut hiç fundamental
    analiz yapmadan doğrudan teknik karta gidilmesini sağlar."""
    await update.message.reply_text(menu.TEKNIK_MENU_TEXT, reply_markup=menu.build_teknik_menu())


async def cmd_temel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/temel -- Faz 16 Derin Kart için BİST/NASDAQ seçim ekranını açar.
    CANLI KULLANICI GERİ BİLDİRİMİ (2026-08-03): Derin Kart'a eskiden SADECE
    bir Bilanço Analizi/Teknik Görünüm sonucunun altındaki butondan
    erişilebiliyordu ("bilanço bakmadan bu temel analiz kısmına
    gelemiyorum") -- bu komut önce Bilanço Analizi'ne HİÇ uğramadan
    doğrudan (gerekirse önce fetch tetikleyerek) Derin Kart'a gider."""
    await update.message.reply_text(menu.DERIN_MENU_TEXT, reply_markup=menu.build_derin_menu())


async def _send_card_photo(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    png_path: str,
    caption: str,
    reply_markup=None,
) -> None:
    """Karti HEM send_photo (sohbet-ici hizli onizleme) HEM send_document
    (orijinal PNG, sikistirmadan) ile gonderir.

    Kok neden (kullanici raporu + kod incelemesi, 2026-08-03, bkz.
    PROJE_HAFIZASI/06_BILINEN_SORUNLAR.md §B25): Telegram `sendPhoto`
    gonderilen gorseli sunucu tarafinda otomatik JPEG'e cevirip sikistirir
    (orijinal byte'lar KORUNMAZ). Kullanici bu ZATEN sikistirilmis gorseli
    telefonuna kaydedip X'e (Twitter) yukleyince X kendi sikistirmasini da
    UZERINE ekliyordu -- cift kayipli sikistirma, ince izgara cizgileri/
    monospace font kenarlarinda gozle gorulur bulanikliga yol aciyordu.
    `sendDocument` dosyayi ORIJINAL BAYT BAZINDA iletir; kullanici oradan
    kaydedip paylasinca sadece TEK (X'in kendi) sikistirmasi uygulanir.

    CANLI hata (kullanici raporu, 2026-08-04): send_photo VE send_document
    ONCEDEN TEK try/except altinda ardisik cagriliyordu -- send_photo
    (kotu/yavas baglantida, bkz. terminal loglari: WriteTimeout/ReadTimeout)
    PATLAYINCA fonksiyon orada KESILIYOR, send_document (X'te paylasmadan
    once kaydedilecek ORIJINAL kalite dosya) HIC calismadan cagiran tarafin
    disaridaki try/except'ine dusuyordu -- kullanici "X'e atarken bozulmasin
    diye gelen ikinci gorsel gelmedi" diye bildirdi. Artik ikisi BIRBIRINDEN
    BAGIMSIZ denenir (ayri try/except) -- biri (agdan dolayi) basarisiz olsa
    bile digeri yine de gonderilmeye calisilir."""
    try:
        with open(png_path, "rb") as photo_file:
            await context.bot.send_photo(chat_id=chat_id, photo=photo_file, caption=caption, reply_markup=reply_markup)
    except Exception:
        logger.exception("Kart fotografi (onizleme) gonderilemedi, orijinal kalite dosya yine de denenecek.")

    try:
        with open(png_path, "rb") as document_file:
            await context.bot.send_document(
                chat_id=chat_id,
                document=document_file,
                caption="🖼️ Orijinal kalite (X/Twitter'da paylaşmadan önce bunu kaydet)",
            )
    except Exception:
        logger.exception("Kart orijinal kalite dosyasi (X icin) gonderilemedi.")


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
        caption = f"📅 Yaklaşan Bilanço Tarihleri · {takvim_context['market_label']}"
        await _send_card_photo(context, chat_id, png_path, caption)
    except Exception:
        logger.exception("%s takvim görseli gönderilemedi (metin yine de denenecek)", market)

    try:
        await context.bot.send_message(chat_id=chat_id, text=calendar_card.build_calendar_share_text(takvim_context))
    except Exception:
        logger.exception("%s takvim metni gönderilemedi", market)


# --- Teknik Görünüm (Faz 15) -----------------------------------------------------


async def _gonder_teknik(chat_id: int, context: ContextTypes.DEFAULT_TYPE, ticker: str, market: str) -> None:
    """'📈 Teknik Görünüm' butonuna basılınca AYNI ticker/market için Faz 15
    teknik analiz kartını üretir ve gönderir. Bu kart temel analiz kartından
    TAMAMEN BAĞIMSIZ bir veri kaynağı (price_history) ve hesap zinciri
    (src/analysis/technical.py) kullanır (bkz. K1: skor/puan İÇERMEZ) --
    burada bir hata olsa bile temel analiz akışını ETKİLEMEZ."""
    bars = await asyncio.to_thread(price_history.fetch_ohlcv, ticker, market, 400)
    price_bars = [
        technical.PriceBar(trade_date=bar.trade_date, high=bar.high, low=bar.low, close=bar.close, volume=bar.volume)
        for bar in bars
    ]
    snapshot = technical.compute_snapshot(price_bars)
    teknik_context = technical_card.build_technical_context(snapshot, ticker, market)

    if not teknik_context["has_data"]:
        await context.bot.send_message(
            chat_id,
            f"⚠️ {ticker} için yeterli fiyat geçmişi bulamadım, teknik görünüm üretilemedi.",
        )
        return

    out_path = config.DATA_DIR / "cards" / f"{ticker}_teknik.png"
    try:
        png_path = await asyncio.to_thread(
            card.render_card, teknik_context, str(out_path), "technical_card.html", "#technical-card"
        )
    except card.CardRenderError:
        logger.exception("%s teknik kartı render edilemedi", ticker)
        await context.bot.send_message(chat_id, "⚠️ Teknik görünüm görseli üretilemedi, birkaç dakika sonra tekrar dene.")
        return

    try:
        caption = (
            f"📈 #{ticker} Teknik Görünüm\n\n"
            "Bu içerik yatırım tavsiyesi değildir; geçmiş performans gelecekteki "
            "getirinin göstergesi değildir."
        )
        await _send_card_photo(
            context, chat_id, png_path, caption, reply_markup=menu.build_teknik_sonrasi_menu(ticker=ticker, market=market)
        )
    except Exception:
        logger.exception("%s teknik görünüm görseli gönderilemedi", ticker)


async def handle_teknik_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """callback_data: 'teknik:{market}:{ticker}' (bkz. menu.build_sonuc_sonrasi_menu)."""
    query = update.callback_query
    await query.answer()

    parts = (query.data or "").split(":")
    if len(parts) < 3:
        return
    market, ticker = parts[1], parts[2]

    chat_id = query.message.chat_id
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)
    await _gonder_teknik(chat_id, context, ticker, market)


# --- Derin Kart (çok dönemli temel analiz) -----------------------------------------------------

# SADECE bu iki financial_group icin anlamli -- calculator.analyze()/analyze_us()
# (ikisi de AYNI AnalysisResult tipini doner) sanayi/ticaret alan adlarini
# (revenue/gross_profit/... ) kullanir; banka/sigorta (UFRS/UFRS_K/UFRS_KATILIM)
# TAMAMEN farkli alan semasina sahiptir (bkz. trends.py modul notu).
_DERIN_ANALIZ_DESTEKLENEN_GRUPLAR = ("XI_29", "US_GAAP")


async def _gonder_derin_analiz(chat_id: int, context: ContextTypes.DEFAULT_TYPE, ticker: str, market: str) -> None:
    """'🔬 Detaylı Analiz' (Bilanço kartı altı) VEYA '📊 Temel Analiz' (Teknik
    kartı altı, handle_teknik_callback'in simetriği) butonuna basılınca AYNI
    ticker/market için çok dönemli "Derin Kart"ı üretir ve gönderir.

    Bu kart DB'de ZATEN biriken (repository.get_financials -- bkz.
    src/analysis/trends.py modül notu) geçmiş dönemleri kullanır, YENİ bir
    ağ isteği ATMAZ -- bu yüzden ticker DAHA ÖNCE bir Bilanço Analizi ile
    en az bir kez sorgulanmış OLMALIDIR (yoksa DB'de veri yoktur)."""
    with repository.get_session() as session:
        company = session.get(models.Company, ticker)
        if company is None or company.financial_group not in _DERIN_ANALIZ_DESTEKLENEN_GRUPLAR:
            await context.bot.send_message(
                chat_id,
                f"⚠️ {ticker} için detaylı (çok dönemli) analiz üretilemedi -- önce bir Bilanço Analizi "
                "çalıştırılmış olmalı ve şirket sanayi/ticaret (banka/sigorta desteklenmiyor) sınıfında olmalı.",
            )
            return
        financials_by_period = repository.get_financials(session, ticker, n_periods=trends.SEASONALITY_FETCH_PERIODS)
        score_history = repository.get_score_history(session, ticker)
        company_name = company.name or ticker
        financial_group = company.financial_group

        # Sektör ortalaması (2. çizgi) -- SADECE Company.sector DOLU ise (bkz.
        # scripts/refresh_sector_cache.py) mümkündür. Boşsa (henüz cache
        # çalıştırılmamışsa) sector_average boş kalır, kart otomatik olarak
        # TEK çizgiye düşer (bkz. deep_card.py K4 mantığı) -- YENİ bir ağ
        # isteği ATILMAZ, sadece DB'de zaten var olan peer'ler okunur.
        sector_average: dict = {}
        sector_name = company.sector
        peer_count = 0
        peer_tickers: list[str] = []
        peer_financials_list: list[dict] = []
        if sector_name:
            peer_tickers = repository.get_sector_peer_tickers(
                session, sector_name, company.financial_group, exclude_ticker=ticker
            )
            peer_count = len(peer_tickers)
            peer_financials_list = [
                repository.get_financials(session, peer, n_periods=trends.SEASONALITY_FETCH_PERIODS) for peer in peer_tickers
            ]
            if peer_financials_list:
                sector_average = trends.compute_sector_average(peer_financials_list)

    trend = trends.compute_multi_period_trend(financials_by_period)

    # Değerleme Analizi paneli (2026-08-04, kullanıcı isteği; Faz 16.6'da
    # genişletildi) -- Faz 16.6'dan İTİBAREN `peer_tickers` BOŞ olsa bile
    # HER ZAMAN çağrılır: Benjamin Graham/Peter Lynch ölçütleri SEKTÖR
    # PEER'İ GEREKTİRMEZ (bkz. valuation.py modül notu), sadece own F/K-
    # PD/DD + fiyat geçmişinden hesaplanır; sektöre-göreli kısım (peer
    # varsa) bunun İÇİNDE ayrıca dolar. Fiyat/eş şirket verisi İKİNCİL
    # olduğu için (Kural 9) herhangi bir hata bu bloğu SESSİZCE atlar,
    # Derin Kart'ın geri kalanı (zaten üretilmiş trend/sektör verisi) bundan
    # ETKİLENMEZ.
    valuation_assessment = None
    try:
        valuation_assessment = pipeline.compute_valuation_assessment_for_ticker(
            ticker, market, financial_group, financials_by_period, peer_tickers, peer_financials_list
        )
    except Exception:
        logger.warning("%s için Değerleme Analizi paneli hesaplanamadı, panel gizlenecek.", ticker, exc_info=True)

    deep_context = deep_card.build_deep_card_context(
        trend,
        score_history,
        ticker,
        market,
        company_name=company_name,
        sector_average=sector_average,
        sector_name=sector_name,
        peer_count=peer_count,
        valuation_assessment=valuation_assessment,
    )

    if not deep_context["has_data"]:
        await context.bot.send_message(chat_id, f"⚠️ {ticker} için çok dönemli trend analizi için yeterli veri yok.")
        return

    out_path = config.DATA_DIR / "cards" / f"{ticker}_derin.png"
    try:
        png_path = await asyncio.to_thread(
            card.render_card, deep_context, str(out_path), "deep_card.html", "#deep-card"
        )
    except card.CardRenderError:
        logger.exception("%s derin kart render edilemedi", ticker)
        await context.bot.send_message(chat_id, "⚠️ Detaylı analiz görseli üretilemedi, birkaç dakika sonra tekrar dene.")
        return

    try:
        caption = (
            f"🔬 #{ticker} Detaylı Analiz — {deep_context['period_count']} çeyrek\n\n"
            "Bu içerik yatırım tavsiyesi değildir; yatırım kararı için profesyonel danışmanlık alınmalıdır."
        )
        await _send_card_photo(
            context, chat_id, png_path, caption, reply_markup=menu.build_sonuc_sonrasi_menu(ticker=ticker, market=market)
        )
    except Exception:
        logger.exception("%s derin kart gönderilemedi", ticker)


async def handle_derin_analiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """callback_data: 'derin:{market}:{ticker}' (bkz. menu.build_sonuc_sonrasi_menu
    '🔬 Detaylı Analiz' butonu VE menu.build_teknik_sonrasi_menu '📊 Temel
    Analiz' butonu -- İKİSİ DE aynı hedefe gider, bkz. _gonder_derin_analiz)."""
    query = update.callback_query
    await query.answer()

    parts = (query.data or "").split(":")
    if len(parts) < 3:
        return
    market, ticker = parts[1], parts[2]

    chat_id = query.message.chat_id
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)
    await _gonder_derin_analiz(chat_id, context, ticker, market)


# --- Analiz akisi -----------------------------------------------------


def _period_label_for(sonuc: pipeline.PipelineResult) -> str:
    """pipeline.quarter_label()'i çağırır -- `is_annual_only` SADECE
    `calculator.AnalysisResult`'ta (sanayi/US_GAAP) var, `BankAnalysisResult`/
    `InsuranceAnalysisResult`'ta YOK (bkz. calculator.py). CANLI HATA
    (kullanıcı raporu, 2026-08-03, ISCTR): eski kod bu alana KOŞULSUZ erişiyordu
    -- her banka/sigorta analizinde `AttributeError` ile hem kart fotoğrafı
    HEM özet metni gönderimi ÇÖKÜYORDU (try/except sadece logluyordu,
    kullanıcıya HİÇBİR ŞEY ulaşmıyordu). `getattr(..., False)` ile
    bankalar/sigortalar için güvenli varsayılan (asla "sadece yıllık" değil,
    zaten çeyreklik veri) kullanılır."""
    is_annual_only = getattr(sonuc.analysis, "is_annual_only", False)
    return pipeline.quarter_label(sonuc.analysis.latest_period, annual_only=is_annual_only)


# --- X/Twitter thread formatı (Faz 16.4, kullanıcı isteği 2026-08-04) -------------------------------
#
# Kullanıcı, kartla birlikte gelen tek bloklu özet metni yerine DOĞRUDAN bir
# X/Twitter thread'ine (4 ayrı gönderi) kopyalanabilecek bir format istedi --
# her biri kendi başına bir "post" olacak şekilde, Telegram'da AYRI mesajlar
# olarak art arda gönderilir (bkz. _gonder_thread_gonderileri). Sıra:
#   1) Kanca (fotoğraf altyazısı) -- skor + tek cümlelik çarpıcı özet + CTA
#   2) Artışlar & Azalışlar
#   3) Bilanço Özeti (detaylı anlatı)
#   4) Radar Skoru Detayı (bileşen kırılımı) + "yorumlara yazın" CTA'sı


def _thread_post_1_kanca(sonuc: pipeline.PipelineResult) -> str:
    """Fotoğrafla BİRLİKTE giden altyazı VE thread'in ilk gönderisi -- kısa,
    çarpıcı, "detaylar thread'de" ile devam eden gönderilere yönlendirir."""
    period_label = _period_label_for(sonuc)
    skor = format_number_tr(sonuc.score.total_score, decimals=2)
    return (
        f"#{sonuc.ticker} {period_label} Bilanço Özeti 🧵\n\n"
        f"🎯 Radar Skoru: {skor}/10 ({sonuc.score.badge})\n\n"
        f"{sonuc.commentary.hook}\n\n"
        "Detaylar thread'de 👇\n\n"
        "Bu içerik yatırım tavsiyesi değildir."
    )


def _thread_post_2_artis_azalis(sonuc: pipeline.PipelineResult) -> str | None:
    """İKİSİ de boşsa None döner (bu gönderi hiç yollanmaz -- boş bir "post"
    paylaşıma hazır olmaz)."""
    yorum = sonuc.commentary
    if not yorum.positives and not yorum.negatives:
        return None

    lines = [f"#{sonuc.ticker} · Artışlar & Azalışlar", ""]
    if yorum.positives:
        lines.append("📈 Artışlar:")
        lines.extend(f"• {p}" for p in yorum.positives)
    if yorum.negatives:
        if yorum.positives:
            lines.append("")
        lines.append("📉 Azalışlar:")
        lines.extend(f"• {n}" for n in yorum.negatives)
    return "\n".join(lines)


def _thread_post_3_bilanco_ozeti(sonuc: pipeline.PipelineResult) -> str:
    """Kullanıcı isteği: bu bölüm eski tek-satırlık özetten DAHA DETAYLI
    olmalı -- bkz. src/ai/commentary.py `summary` alanı istem talimatı
    (5-7 cümle, ÖNCEDEN 3-5 cümleydi). Metnin KENDİSİ hâlâ SADECE Gemini'nin
    (veya LLM'siz yedek modun) ürettiği, önceden hesaplanmış sayılardan
    kurulan `summary` -- burada YENİDEN metin ÜRETİLMEZ, sadece başlıklanır."""
    return f"#{sonuc.ticker} · Bilanço Özeti\n\n{sonuc.commentary.summary}"


def _thread_post_4_skor_detay(sonuc: pipeline.PipelineResult) -> str:
    """Skorun kompakt bileşen kırılımı -- kartta/karttaki gerekçe metninin
    AKSİNE burada her bileşen için tam `reasoning_tr` cümlesi YOK (bir X
    gönderisi için fazla uzun olurdu); SADECE "Değerleme" bileşeninde
    (kullanıcının örneği: "F/K 5,3 – PD/DD 2,1") kısa parantez notu
    eklenir -- bu da scorer.py'nin ZATEN ürettiği reasoning_tr'nin ta
    kendisi, YENİDEN hesaplanmaz."""
    skor = sonuc.score
    baslik_skor = format_number_tr(skor.total_score, decimals=2)
    lines = [f"#{sonuc.ticker} · Radar Skoru Detayı ({baslik_skor}/10 {skor.badge})", ""]
    for c in skor.components:
        skor_metni = f"{format_number_tr(c.score, decimals=1)}/10" if c.score is not None else "N/A"
        agirlik = format_number_tr(c.weight_nominal, decimals=0)
        parantez = f" ({c.reasoning_tr.rstrip('.')})" if c.name == "Değerleme" and c.score is not None else ""
        lines.append(f"• {c.name} (%{agirlik}) → {skor_metni}{parantez}")
    lines.append("")
    lines.append("Sizce bu skor adil mi?")
    lines.append("Hangi hisseyi analiz edeyim? Yorumlara yazın 👇")
    return "\n".join(lines)


async def _gonder_thread_gonderileri(
    chat_id: int, context: ContextTypes.DEFAULT_TYPE, sonuc: pipeline.PipelineResult, market: str
) -> None:
    """Kart fotoğrafının (thread'in 1. gönderisi, ayrı gönderilir) ARDINDAN
    2-3-4. gönderileri AYRI Telegram mesajları olarak yollar -- kullanıcı
    bunları X/Twitter'a kopyalayıp doğrudan bir thread haline getirebilsin
    diye HER BİRİ kendi başına bir mesaj (bkz. modül üst notu). "Tek
    dokunuşla yeni arama" menüsü (§B18) SON gönderiye (4.) eklenir --
    thread'in doğal bitişi orası."""
    ticker = sonuc.ticker

    try:
        post2 = _thread_post_2_artis_azalis(sonuc)
        if post2 is not None:
            await context.bot.send_message(chat_id=chat_id, text=post2)
    except Exception:
        logger.exception("istek ticker=%s: thread 2. gönderisi (artış/azalış) gönderilemedi", ticker)

    try:
        await context.bot.send_message(chat_id=chat_id, text=_thread_post_3_bilanco_ozeti(sonuc))
    except Exception:
        logger.exception("istek ticker=%s: thread 3. gönderisi (bilanço özeti) gönderilemedi", ticker)

    try:
        # show_derin_analiz: SADECE sanayi/US_GAAP (analyze()/analyze_us()
        # AYNI AnalysisResult tipini doner) -- banka/sigorta farkli alan
        # semasina sahip oldugu icin Derin Kart onlarda ANLAMSIZ olurdu
        # (bkz. trends.py modul notu).
        await context.bot.send_message(
            chat_id=chat_id,
            text=_thread_post_4_skor_detay(sonuc),
            reply_markup=menu.build_sonuc_sonrasi_menu(
                ticker=ticker,
                market=market,
                show_derin_analiz=isinstance(sonuc.analysis, calculator.AnalysisResult),
            ),
        )
    except Exception:
        logger.exception("istek ticker=%s: thread 4. gönderisi (skor detayı) gönderilemedi", ticker)


async def _execute_and_send(
    ticker: str,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    periods=None,
    market: str = "BIST",
    allow_market_fallback: bool = False,
    output_mode: str = "temel",
) -> None:
    """`output_mode="derin"` (bkz. cmd_temel/menu:derinanaliz -- kullanıcı
    isteği: "bilanço bakmadan bu temel analiz kısmına gelemiyorum"): pipeline
    YİNE çalışır (DB'de veri YOKSA/eskiyse tam fetch tetiklenir -- Derin
    Kart'ın "ticker daha önce analiz edilmiş olmalı" ön koşulu BURADA
    otomatik sağlanır) ama BAŞARI durumunda tek çeyreklik kart/özet metin
    YERİNE doğrudan _gonder_derin_analiz() çağrılır (aynı fonksiyon "🔬
    Detaylı Analiz" butonuyla da kullanılır, DB'yi ZATEN taze haliyle
    tekrar okur)."""
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
        # §B18: en son basarili aramanin piyasasi (fallback ile degismis
        # olabilir, orn. BIST->NASDAQ) kalici hafizaya yazilir -- bir
        # sonraki menusuz/dogrudan ticker yazma varsayilani bunu kullanir.
        menu.set_son_market(context.user_data, market)

        if output_mode == "derin":
            # cmd_temel/menu:derinanaliz akışı: pipeline BAŞARIYLA çalıştı
            # (DB artık taze) -- tek çeyreklik kart/özet metin YERİNE
            # doğrudan Derin Kart'a geç (bkz. _execute_and_send docstring'i).
            await _gonder_derin_analiz(chat_id, context, sonuc.ticker, market)
            logger.info(
                "istek user=%s ticker=%s sure=%.1fs sonuc=basarili (derin kart)",
                user_id, ticker, time.monotonic() - started,
            )
            return

        # CANLI hata (kullanici raporu, OTKAR): "gorsel geldi ama metin
        # gelmedi" -- eskiden send_photo/send_message TEK bir try/except
        # ALTINDA DEGILDI (hic try/except yoktu), send_photo bir
        # httpx.ReadTimeout ile patlarsa (bkz. build_application timeout
        # notu) send_message'a HIC ULASILMIYORDU. Artik HER gonderi KENDI
        # try/except'i icinde -- biri basarisiz olsa bile digerleri yine de
        # denenir (bkz. _gonder_thread_gonderileri, Faz 16.4).
        try:
            await _send_card_photo(context, chat_id, sonuc.png_path, _thread_post_1_kanca(sonuc))
        except Exception:
            logger.exception("istek user=%s ticker=%s: kart fotoğrafı gönderilemedi (thread gönderileri yine de denenecek)", user_id, ticker)

        await _gonder_thread_gonderileri(chat_id, context, sonuc, market)

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

    teknik_istegi = islem is not None and islem.tip == "teknik"
    derin_istegi = islem is not None and islem.tip == "derin"

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
        if teknik_istegi:
            # /teknik komutuyla (veya menu:teknikanaliz butonuyla) baslatilan
            # akis -- fundamental pipeline'a HIC UGRAMAZ, dogrudan
            # _gonder_teknik cagirilir (bkz. handle_teknik_callback ile AYNI
            # hedef fonksiyon, sadece giris noktasi farkli).
            await update.message.reply_text(f"📈 {ticker} teknik görünümü hazırlanıyor...")
            chat_id = update.effective_chat.id
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)
            await _gonder_teknik(chat_id, context, ticker, market)
            return

        if derin_istegi:
            # /temel komutuyla (veya menu:derinanaliz butonuyla) baslatilan
            # akis -- teknik'in AKSINE pipeline'a UGRAR (Derin Kart'in "DB'de
            # veri olmali" on kosulunu burada otomatik saglamak icin, bkz.
            # _execute_and_send docstring'i) ama basari durumunda tek
            # ceyreklik kart YERINE dogrudan Derin Kart gonderilir.
            await update.message.reply_text(f"🔬 {ticker} için detaylı analiz hazırlanıyor... (~20 sn)")
            await _execute_and_send(ticker, update, context, market=market, output_mode="derin")
            return

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

    if screen == "teknikanaliz":
        if sub == "bist":
            menu.set_bekleyen_islem(context.user_data, tip="teknik", market="BIST")
            menu.set_son_market(context.user_data, "BIST")
            await query.edit_message_text(menu.TEKNIK_BIST_PROMPT, reply_markup=menu.build_teknik_bekleniyor_menu())
        elif sub == "nasdaq":
            menu.set_bekleyen_islem(context.user_data, tip="teknik", market="NASDAQ")
            menu.set_son_market(context.user_data, "NASDAQ")
            await query.edit_message_text(menu.TEKNIK_NASDAQ_PROMPT, reply_markup=menu.build_teknik_bekleniyor_menu())
        else:
            menu.clear_bekleyen_islem(context.user_data)
            await query.edit_message_text(menu.TEKNIK_MENU_TEXT, reply_markup=menu.build_teknik_menu())
        return

    if screen == "derinanaliz":
        if sub == "bist":
            menu.set_bekleyen_islem(context.user_data, tip="derin", market="BIST")
            menu.set_son_market(context.user_data, "BIST")
            await query.edit_message_text(menu.DERIN_BIST_PROMPT, reply_markup=menu.build_derin_bekleniyor_menu())
        elif sub == "nasdaq":
            menu.set_bekleyen_islem(context.user_data, tip="derin", market="NASDAQ")
            menu.set_son_market(context.user_data, "NASDAQ")
            await query.edit_message_text(menu.DERIN_NASDAQ_PROMPT, reply_markup=menu.build_derin_bekleniyor_menu())
        else:
            menu.clear_bekleyen_islem(context.user_data)
            await query.edit_message_text(menu.DERIN_MENU_TEXT, reply_markup=menu.build_derin_menu())
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
    BotCommand("teknik", "Teknik görünüm kartı için piyasa seç"),
    BotCommand("temel", "Detaylı (çok dönemli) analiz için piyasa seç"),
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
    application.add_handler(CommandHandler("teknik", cmd_teknik))
    application.add_handler(CommandHandler("temel", cmd_temel))
    application.add_handler(CommandHandler("son", cmd_son))
    application.add_handler(CommandHandler("takvim", cmd_takvim))
    application.add_handler(CommandHandler("hakkinda", cmd_hakkinda))
    application.add_handler(CallbackQueryHandler(handle_period_callback, pattern=r"^oncekidonem:"))
    application.add_handler(CallbackQueryHandler(handle_teknik_callback, pattern=r"^teknik:"))
    application.add_handler(CallbackQueryHandler(handle_derin_analiz_callback, pattern=r"^derin:"))
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
    # CANLI hata (kullanici raporu, 2026-08-04): PTB'nin varsayilani
    # bootstrap_retries=0 -- baslangicta (get_me() cagrisi sirasinda) internet
    # o an kesikse (getaddrinfo failed vb.) TEK denemede pes edip run_polling'i
    # yakalanmamis bir NetworkError ile PATLATIYORDU (terminalde cift
    # traceback, bot tamamen COKUYORDU, manuel yeniden baslatma gerekiyordu).
    # bootstrap_retries=-1 SINIRSIZ tekrar dener (PTB kendi ic-backoff'uyla,
    # bkz. network_retry_loop) -- internet gelince bot kendiliginden acilir.
    application.run_polling(allowed_updates=Update.ALL_TYPES, bootstrap_retries=-1)
