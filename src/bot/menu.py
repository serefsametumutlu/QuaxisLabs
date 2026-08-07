"""Telegram bot buton menu agaci: InlineKeyboardMarkup insasi + callback_data
semasi + "hisse kodu bekleniyor" durumunun (bekleyen_islem) TTL'li yonetimi.

telegram_bot.py'nin daha da buyumesini onlemek icin menu agaci burada, ayri
bir modulde tutulur. Bu modul Telegram API'sine mesaj GONDERMEZ (sadece
markup/metin/state nesneleri uretir) -- gonderim/edit_message_text cagrilari
telegram_bot.py'de kalir.

State semasi (bkz. PROJE_HAFIZASI/05_BOT_VE_VERITABANI.md SS5):
- Menu NAVIGASYONU tamamen `callback_data` icine gomulur (orn.
  "menu:analiz:nasdaq") -- surec yeniden baslasa bile butonlar calisir.
- SADECE "hisse kodu bekleniyor" durumu `context.user_data["bekleyen_islem"]`
  icinde tutulur (TTL'li) -- bu, bir sonraki SERBEST METIN mesajinin hangi
  market'e ait oldugunu bilmek icin gereklidir ve callback_data'ya sigacak
  kadar kucuk degildir/zaten bir sonraki mesaj bir buton tiki degildir.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# 10 dakika: kullanici "hisse kodu yaz" diyen butona basip gunler sonra
# yarim kalan bir metin yazarsa bu ESKI beklentiye TAKILMAMALI.
_BEKLEYEN_ISLEM_TTL_SECONDS = 600.0


@dataclass
class BekleyenIslem:
    tip: str  # "analiz" (temel) | "teknik" (Faz 15) | "fonanaliz" (Faz 19) | "degerleme" (Faz 21)
    market: str  # "BIST" | "NASDAQ" -- tip="fonanaliz" icin kullanilmaz, "-" sabiti konur
    expires_at: float  # time.monotonic() bazli


def set_bekleyen_islem(user_data: dict, *, tip: str, market: str) -> None:
    user_data["bekleyen_islem"] = BekleyenIslem(
        tip=tip, market=market, expires_at=time.monotonic() + _BEKLEYEN_ISLEM_TTL_SECONDS
    )


def peek_bekleyen_islem(user_data: dict) -> BekleyenIslem | None:
    """Suresi dolmamis bir bekleyen islem varsa SILMEDEN dondurur (kullanici
    gecersiz bir sey yazip TEKRAR denemek isteyebilir). Suresi dolmussa
    ORADA temizler ve None doner."""
    islem = user_data.get("bekleyen_islem")
    if islem is None:
        return None
    if time.monotonic() > islem.expires_at:
        user_data.pop("bekleyen_islem", None)
        return None
    return islem


def clear_bekleyen_islem(user_data: dict) -> None:
    user_data.pop("bekleyen_islem", None)


# --- "Son kullanılan piyasa" hafızası (TTL'siz, §B18) -----------------------------------------------------
#
# CANLI KULLANICI GERİ BİLDİRİMİ (§B18, 06_BILINEN_SORUNLAR.md): her NASDAQ
# hissesi ararken /menu -> Bilanço Analizi -> NASDAQ -> ticker yazma akışını
# HER SEFERİNDE baştan yapmak yorucu bulunuyordu. bekleyen_islem (yukarısı)
# TTL'li ve TEK SEFERLİK -- bir arama SONRASI hemen unutulur. Bu ayrı,
# TTL'siz anahtar en son hangi piyasanın seçildiğini/kullanıldığını KALICI
# tutar (surec/bot yeniden baslasa bile Telegram user_data persistence'i
# ile hayatta kalir) ve handle_ticker_message'in varsayilan piyasa
# secimini ("menusuz dogrudan ticker yazma" akisi) buna gore yapar --
# eskiden HER ZAMAN sabit "BIST" varsayiliyordu.
_SON_MARKET_KEY = "son_market"


def set_son_market(user_data: dict, market: str) -> None:
    user_data[_SON_MARKET_KEY] = market


def get_son_market(user_data: dict) -> str:
    return user_data.get(_SON_MARKET_KEY, "BIST")


# --- Menu ekranlari (InlineKeyboardMarkup) -----------------------------------------------------


def build_root_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📊 Bilanço Analizi", callback_data="menu:analiz")],
            [InlineKeyboardButton("📈 Teknik Görünüm", callback_data="menu:teknikanaliz")],
            [InlineKeyboardButton("🔬 Detaylı Analiz (Derin Kart)", callback_data="menu:derinanaliz")],
            [InlineKeyboardButton("🧮 Değerleme", callback_data="menu:degerleme")],
            [InlineKeyboardButton("💰 Fon Analiz", callback_data="menu:fonanaliz")],
            [InlineKeyboardButton("🆕 Halka Arz İnceleme", callback_data="menu:halkaarz")],
            [InlineKeyboardButton("📅 Yaklaşan Bilanço Tarihleri", callback_data="menu:takvim")],
            [InlineKeyboardButton("🕘 Son Kartlar", callback_data="menu:son")],
            [InlineKeyboardButton("ℹ️ Hakkında", callback_data="menu:hakkinda")],
        ]
    )


def build_analiz_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🇹🇷 BİST", callback_data="menu:analiz:bist")],
            [InlineKeyboardButton("🇺🇸 NASDAQ", callback_data="menu:analiz:nasdaq")],
            [InlineKeyboardButton("⬅️ Geri", callback_data="menu:root")],
        ]
    )


def build_teknik_menu() -> InlineKeyboardMarkup:
    """/teknik komutu -- 'hangi piyasa' ekrani, build_analiz_menu() ile AYNI
    yapida ama callback_data'lar 'menu:teknikanaliz:...' (analiz akisiyla
    KARISMASIN, bekleyen_islem.tip farkli kalsin diye ayri bir screen)."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🇹🇷 BİST", callback_data="menu:teknikanaliz:bist")],
            [InlineKeyboardButton("🇺🇸 NASDAQ", callback_data="menu:teknikanaliz:nasdaq")],
            [InlineKeyboardButton("⬅️ Geri", callback_data="menu:root")],
        ]
    )


def build_derin_menu() -> InlineKeyboardMarkup:
    """/temel komutu -- 'hangi piyasa' ekrani, build_teknik_menu() ile AYNI
    yapida ama callback_data'lar 'menu:derinanaliz:...' (kullanıcı isteği:
    "bilanço bakmadan bu temel analiz kısmına gelemiyorum" -- /teknik'in
    Derin Kart karşılığı, DOĞRUDAN bu karta gider, tek çeyreklik Bilanço
    Analizi kartına HİÇ UĞRAMAZ, bkz. telegram_bot._gonder_derin_analiz_tam())."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🇹🇷 BİST", callback_data="menu:derinanaliz:bist")],
            [InlineKeyboardButton("🇺🇸 NASDAQ", callback_data="menu:derinanaliz:nasdaq")],
            [InlineKeyboardButton("⬅️ Geri", callback_data="menu:root")],
        ]
    )


def build_fonanaliz_menu() -> InlineKeyboardMarkup:
    """'💰 Fon Analiz' -- Faz 19. Üç mod (kullanıcı isteği): tekli fon
    (kod yazılır, detaylı kart), öne çıkan fonlar (sabit 6 fon, özet
    kart), tüm liste (sabit 15 fon, özet kart). Son ikisi metin GİRİŞİ
    GEREKTİRMEZ -- takvim akışıyla AYNI şekilde doğrudan tetiklenir."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔍 Tek Fon Analizi", callback_data="menu:fonanaliz:tekli")],
            [InlineKeyboardButton("⭐ Öne Çıkan Fonlar", callback_data="menu:fonanaliz:onplan")],
            [InlineKeyboardButton("📋 Tüm Liste (15 Fon)", callback_data="menu:fonanaliz:tumliste")],
            [InlineKeyboardButton("⬅️ Geri", callback_data="menu:root")],
        ]
    )


def build_fonanaliz_bekleniyor_menu() -> InlineKeyboardMarkup:
    """Tekli fon icin 'fon kodunu yaz' ekrani -- Geri, menu:fonanaliz'e doner."""
    return _geri_menu("menu:fonanaliz")


def build_halkaarz_menu(disclosures: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    """'🆕 Halka Arz İnceleme' -- Faz 20 devamı. `disclosures`: ÖNCEDEN
    çekilmiş (ticker, buton_etiketi) çiftleri (bkz.
    `src.bot.ipo_pipeline.list_available_ipos()`) -- bu fonksiyon SAF UI,
    hiçbir I/O yapmaz (diğer tüm menu.py builder'larıyla AYNI ilke).
    Fon Analiz'in "tekli"/"tümliste" ikiliğinin AKSİNE tek bir mod var:
    liste ZATEN kısa (haftada birkaç yeni izahname), kod YAZMAYA gerek yok,
    doğrudan butona dokunulur (Kural: keşif odaklı bir özellik, kullanıcı
    ticker'ı önceden BİLMEYEBİLİR)."""
    rows = [[InlineKeyboardButton(f"🏢 {label}", callback_data=f"halkaarz:goster:{ticker}")] for ticker, label in disclosures]
    rows.append([InlineKeyboardButton("⬅️ Geri", callback_data="menu:root")])
    return InlineKeyboardMarkup(rows)


def build_degerleme_bekleniyor_menu() -> InlineKeyboardMarkup:
    """Değerleme icin 'hisse kodunu yaz' ekrani -- Faz 21, `fundamental_screens.py`
    SADECE BIST XI_29 (sanayi/ticaret) icin anlamli oldugundan (bkz. modul
    ust notu) build_teknik_menu/build_derin_menu'nun AKSINE BIST/NASDAQ
    SECIM EKRANI YOK -- dogrudan 'hisse kodunu yaz' ekranina gidilir (Geri,
    menu:root'a doner)."""
    return _geri_menu("menu:root")


def build_takvim_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🇹🇷 BİST", callback_data="menu:takvim:bist")],
            [InlineKeyboardButton("🇺🇸 NASDAQ", callback_data="menu:takvim:nasdaq")],
            [InlineKeyboardButton("⬅️ Geri", callback_data="menu:root")],
        ]
    )


def _geri_menu(hedef_callback_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Geri", callback_data=hedef_callback_data)]])


def build_analiz_bekleniyor_menu() -> InlineKeyboardMarkup:
    """'Hisse kodunu yaz' ekrani -- Geri, bir ust menu olan analiz secimine doner."""
    return _geri_menu("menu:analiz")


def build_teknik_bekleniyor_menu() -> InlineKeyboardMarkup:
    """Teknik icin 'hisse kodunu yaz' ekrani -- Geri, menu:teknikanaliz'e doner."""
    return _geri_menu("menu:teknikanaliz")


def build_derin_bekleniyor_menu() -> InlineKeyboardMarkup:
    """Derin Kart icin 'hisse kodunu yaz' ekrani -- Geri, menu:derinanaliz'e doner."""
    return _geri_menu("menu:derinanaliz")


def build_takvim_iskelet_menu() -> InlineKeyboardMarkup:
    return _geri_menu("menu:takvim")


def build_alt_ekran_menu() -> InlineKeyboardMarkup:
    """Son Kartlar / Hakkında gibi tek seviyeli alt ekranlar icin -- Geri ana menuye doner."""
    return _geri_menu("menu:root")


def build_sonuc_sonrasi_menu(
    ticker: str | None = None, market: str | None = None, show_derin_analiz: bool = False
) -> InlineKeyboardMarkup:
    """Her analiz SONUCUNUN altina eklenir (§B18) -- kullanici /menu ->
    Bilanço Analizi -> piyasa akisini BASTAN gezmeden tek dokunusla yeni
    bir aramaya baslayabilsin diye. Callback_data'lar MEVCUT "menu:analiz:
    bist/nasdaq" ile AYNI (yeni bir handler GEREKMEDI, handle_menu_callback
    zaten herhangi bir bot mesaji uzerinde edit_message_text ile calisir).

    `ticker`/`market` verilirse (Faz 15) en uste "📈 Teknik Görünüm" butonu
    eklenir -- callback_data "teknik:{market}:{ticker}" formatinda, AYRI bir
    handler'a (handle_teknik_callback) gider. Ikisi de None ise (eski
    cagiranlar/testler) buton EKLENMEZ -- geriye uyumlu.

    `show_derin_analiz=True` ise (SADECE sanayi/US_GAAP -- bkz.
    src/analysis/trends.py modul notu, banka/sigortada anlamsiz) AYNI
    satira "🔬 Detaylı Analiz" butonu da eklenir -- callback_data
    "derin:{market}:{ticker}", handle_derin_analiz_callback'e gider (kullanici
    isteği: tek çeyreklik kart YERİNE çok dönemli/farklı bir içerik)."""
    rows = []
    if ticker is not None and market is not None:
        top_row = [InlineKeyboardButton("📈 Teknik Görünüm", callback_data=f"teknik:{market}:{ticker}")]
        if show_derin_analiz:
            top_row.append(InlineKeyboardButton("🔬 Detaylı Analiz", callback_data=f"derin:{market}:{ticker}"))
        rows.append(top_row)
    rows.append(
        [
            InlineKeyboardButton("🇹🇷 BİST'te Ara", callback_data="menu:analiz:bist"),
            InlineKeyboardButton("🇺🇸 NASDAQ'ta Ara", callback_data="menu:analiz:nasdaq"),
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_teknik_sonrasi_menu(ticker: str, market: str) -> InlineKeyboardMarkup:
    """Her Teknik Görünüm kartının ALTINA eklenir -- build_sonuc_sonrasi_menu()'nun
    SİMETRİĞİ (kullanıcı isteği: temel analizden teknik görünüme tek dokunuşla
    geçiş vardı, TERSİ yoktu). Callback_data "derin:{market}:{ticker}"
    formatinda -- build_sonuc_sonrasi_menu'nun "🔬 Detaylı Analiz" butonuyla
    AYNI handler'a (handle_derin_analiz_callback) gider: kullanıcı geri
    bildirimi ("Temel Analiz butonu Bilanço Analizi ile AYNI görseli
    tekrarlıyor") üzerine bu buton artık tek çeyreklik kart YERİNE çok
    dönemli "Derin Kart"ı üretir -- "teknik:..." ile KARIŞMASIN diye farklı
    bir öncelik ismi kullanılır."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📊 Temel Analiz", callback_data=f"derin:{market}:{ticker}")],
            [
                InlineKeyboardButton("🇹🇷 BİST'te Ara", callback_data="menu:teknikanaliz:bist"),
                InlineKeyboardButton("🇺🇸 NASDAQ'ta Ara", callback_data="menu:teknikanaliz:nasdaq"),
            ],
        ]
    )


# --- Sabit metinler -----------------------------------------------------


ROOT_MENU_TEXT = "Bilanço Radar 📊\n\nNe yapmak istersin?"
ANALIZ_MENU_TEXT = "📊 Bilanço Analizi — hangi piyasa?"
TEKNIK_MENU_TEXT = "📈 Teknik Görünüm — hangi piyasa?"
DERIN_MENU_TEXT = "🔬 Detaylı Analiz (Derin Kart) — hangi piyasa?"
TAKVIM_MENU_TEXT = "📅 Yaklaşan Bilanço Tarihleri — hangi piyasa?"
FONANALIZ_MENU_TEXT = "💰 Fon Analiz — ne görmek istersin?"
FONANALIZ_TEKLI_PROMPT = "Fon kodunu yaz (örn: PHE, TLY)"
HALKAARZ_MENU_TEXT = "🆕 Halka Arz İnceleme — SPK onaylı, henüz işlem görmeyen izahnameler:"
HALKAARZ_BOS_TEXT = "🆕 Şu an son 60 günde SPK onaylı, işleme başlamamış bir izahname bulunamadı."
HALKAARZ_YUKLENIYOR_TEXT = "🆕 İzahnameler taranıyor... (~45-60 saniye, ~22 aracı kurumun KAP profili kontrol ediliyor)"
DEGERLEME_PROMPT = "🧮 Değerleme — hisse kodunu yaz (örn: THYAO). Sadece BİST sanayi/ticaret şirketleri desteklenir."

ANALIZ_BIST_PROMPT = "Hisse kodunu yaz (örn: THYAO)"
ANALIZ_NASDAQ_PROMPT = "Sembolü yaz (örn: AAPL)"
TEKNIK_BIST_PROMPT = "Hisse kodunu yaz (örn: THYAO)"
TEKNIK_NASDAQ_PROMPT = "Sembolü yaz (örn: AAPL)"
DERIN_BIST_PROMPT = "Hisse kodunu yaz (örn: THYAO)"
DERIN_NASDAQ_PROMPT = "Sembolü yaz (örn: AAPL)"
