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
    tip: str  # su an icin sadece "analiz"
    market: str  # "BIST" | "NASDAQ"
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


def build_takvim_iskelet_menu() -> InlineKeyboardMarkup:
    return _geri_menu("menu:takvim")


def build_alt_ekran_menu() -> InlineKeyboardMarkup:
    """Son Kartlar / Hakkında gibi tek seviyeli alt ekranlar icin -- Geri ana menuye doner."""
    return _geri_menu("menu:root")


def build_sonuc_sonrasi_menu(ticker: str | None = None, market: str | None = None) -> InlineKeyboardMarkup:
    """Her analiz SONUCUNUN altina eklenir (§B18) -- kullanici /menu ->
    Bilanço Analizi -> piyasa akisini BASTAN gezmeden tek dokunusla yeni
    bir aramaya baslayabilsin diye. Callback_data'lar MEVCUT "menu:analiz:
    bist/nasdaq" ile AYNI (yeni bir handler GEREKMEDI, handle_menu_callback
    zaten herhangi bir bot mesaji uzerinde edit_message_text ile calisir).

    `ticker`/`market` verilirse (Faz 15) en uste "📈 Teknik Görünüm" butonu
    eklenir -- callback_data "teknik:{market}:{ticker}" formatinda, AYRI bir
    handler'a (handle_teknik_callback) gider. Ikisi de None ise (eski
    cagiranlar/testler) buton EKLENMEZ -- geriye uyumlu."""
    rows = []
    if ticker is not None and market is not None:
        rows.append([InlineKeyboardButton("📈 Teknik Görünüm", callback_data=f"teknik:{market}:{ticker}")])
    rows.append(
        [
            InlineKeyboardButton("🇹🇷 BİST'te Ara", callback_data="menu:analiz:bist"),
            InlineKeyboardButton("🇺🇸 NASDAQ'ta Ara", callback_data="menu:analiz:nasdaq"),
        ]
    )
    return InlineKeyboardMarkup(rows)


# --- Sabit metinler -----------------------------------------------------


ROOT_MENU_TEXT = "Bilanço Radar 📊\n\nNe yapmak istersin?"
ANALIZ_MENU_TEXT = "📊 Bilanço Analizi — hangi piyasa?"
TAKVIM_MENU_TEXT = "📅 Yaklaşan Bilanço Tarihleri — hangi piyasa?"

ANALIZ_BIST_PROMPT = "Hisse kodunu yaz (örn: THYAO)"
ANALIZ_NASDAQ_PROMPT = "Sembolü yaz (örn: AAPL)"
