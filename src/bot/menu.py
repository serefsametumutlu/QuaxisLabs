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


# --- Sabit metinler -----------------------------------------------------


ROOT_MENU_TEXT = "Bilanço Radar 📊\n\nNe yapmak istersin?"
ANALIZ_MENU_TEXT = "📊 Bilanço Analizi — hangi piyasa?"
TAKVIM_MENU_TEXT = "📅 Yaklaşan Bilanço Tarihleri — hangi piyasa?"

ANALIZ_BIST_PROMPT = "Hisse kodunu yaz (örn: THYAO)"
ANALIZ_NASDAQ_PROMPT = "Sembolü yaz (örn: AAPL)"

TAKVIM_ISKELET_TEXT_BIST = "📅 Yaklaşan Bilanço Tarihleri (BİST)\n\nBu özellik yakında eklenecek."
TAKVIM_ISKELET_TEXT_NASDAQ = "📅 Yaklaşan Bilanço Tarihleri (NASDAQ)\n\nBu özellik yakında eklenecek."
