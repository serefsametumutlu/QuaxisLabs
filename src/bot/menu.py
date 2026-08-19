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
    tip: str  # "analiz" (temel) | "teknik" (Faz 15) | "fonanaliz" (Faz 19) | "degerleme" (Faz 21) | "abcd" (Faz 6)
    market: str  # "BIST" | "NASDAQ" -- tip="fonanaliz" icin kullanilmaz, "-" sabiti konur
    expires_at: float  # time.monotonic() bazli
    extra: str | None = None  # tip="abcd" icin secilen zaman dilimini tasir (geriye-uyumlu, varsayilan None)


def set_bekleyen_islem(user_data: dict, *, tip: str, market: str, extra: str | None = None) -> None:
    user_data["bekleyen_islem"] = BekleyenIslem(
        tip=tip, market=market, expires_at=time.monotonic() + _BEKLEYEN_ISLEM_TTL_SECONDS, extra=extra
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
    """Kullanıcı kararı (2026-08-19): '💰 Fon Analiz' ve '🕘 Son Kartlar' dalları
    ana menüden kaldırıldı (sadece menü/komut erişimi -- alttaki fund_pipeline/
    _son_kartlar_metni kodu ve testleri DOKUNULMADAN kalır, kolay geri
    dönüşe izin vermek için bkz. telegram_bot.py CommandHandler kaydı notu).
    Yerine '📶 İndikatörler' eklendi (Momentum Confluence V1/V2 taraması)."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📊 Bilanço Analizi", callback_data="menu:analiz")],
            [InlineKeyboardButton("📈 Teknik Görünüm", callback_data="menu:teknikanaliz")],
            [InlineKeyboardButton("🔬 Detaylı Analiz (Derin Kart)", callback_data="menu:derinanaliz")],
            [InlineKeyboardButton("🧮 Değerleme", callback_data="menu:degerleme")],
            [InlineKeyboardButton("🆕 Halka Arz İnceleme", callback_data="menu:halkaarz")],
            [InlineKeyboardButton("📅 Yaklaşan Bilanço Tarihleri", callback_data="menu:takvim")],
            [InlineKeyboardButton("🔺 Formasyonlar", callback_data="menu:formasyonlar")],
            [InlineKeyboardButton("📶 İndikatörler", callback_data="menu:indikator")],
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


def build_formasyonlar_menu() -> InlineKeyboardMarkup:
    """'🔺 Formasyonlar' -- Faz 6, deneysel formasyon özelliklerinin kök
    ekranı. Şu an tek dal var (ABCD), ama diğer menu ekranlarıyla (Fon
    Analiz, Halka Arz) AYNI iki-seviyeli desen için ayrı bir alt-menu
    olarak tutulur -- ileride yeni formasyon türleri EKLENEBİLİR diye."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔍 ABCD Formasyonu (onaylı)", callback_data="abcd:menu")],
            [InlineKeyboardButton("🌀 Harmonik Tarama (Anlık D)", callback_data="harm:menu")],
            [InlineKeyboardButton("⬅️ Geri", callback_data="menu:root")],
        ]
    )


# --- ABCD formasyon akışı (Faz 6) -----------------------------------------------------
#
# `abcd:...` callback_data ailesi, kalanının `menu:...` aile şemasıyla
# KARIŞMASIN diye BİLİNÇLİ olarak ayrı bir önek kullanır (bkz.
# telegram_bot.py::handle_abcd_callback, `pattern=r"^abcd:"` ile ayrı bir
# CallbackQueryHandler'a bağlanır). Kaynak referans (kullanıcının BEĞENDİĞİ
# UX akışı): `abcd-project/abcd/bot.py::_tf_keyboard` -- tek satırda tüm
# zaman dilimi butonları.

# src.fetchers.abcd_data.TIMEFRAMES ile AYNI sırada/değerlerde tutulmalıdır
# -- menu.py katman disiplini gereği (SAF UI, I/O/fetcher importu YAPMAZ)
# burada bağımsız bir kopya olarak tutulur, o modülün KENDİSİ import EDİLMEZ.
_ABCD_TIMEFRAMES: tuple[str, ...] = ("60", "120", "240", "1D", "1W")


def abcd_mode_keyboard() -> InlineKeyboardMarkup:
    """'abcd:menu' ekranı -- Tek Hisse mi, Tüm BİST Taraması mı?"""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔍 Tek Hisse", callback_data="abcd:mode:tekli")],
            [InlineKeyboardButton("📡 Tüm BİST Taraması", callback_data="abcd:mode:tarama")],
            [InlineKeyboardButton("⬅️ Geri", callback_data="menu:formasyonlar")],
        ]
    )


def abcd_tf_keyboard(mode: str) -> InlineKeyboardMarkup:
    """'abcd:mode:{mode}' ekranı -- zaman dilimi seçimi, abcd-project
    `_tf_keyboard()` ile AYNI düzen (tek satırda 5 buton). `mode` callback_data
    içine gömülür ('abcd:tf:{mode}:{tf}') ki bir sonraki adım (handle_abcd_callback)
    hem modu hem zaman dilimini AYNI tıklamadan bilsin -- ayrı bir state
    GEREKMEZ (bkz. menu.py modül notu: navigasyon callback_data'ya gömülür)."""
    tf_row = [InlineKeyboardButton(tf, callback_data=f"abcd:tf:{mode}:{tf}") for tf in _ABCD_TIMEFRAMES]
    return InlineKeyboardMarkup([tf_row, [InlineKeyboardButton("⬅️ Geri", callback_data="abcd:menu")]])


def build_abcd_bekleniyor_menu(mode: str) -> InlineKeyboardMarkup:
    """Tekli mod için 'hisse kodunu yaz' ekranı -- Geri, AYNI modun zaman
    dilimi seçim ekranına döner (kullanıcı zaman dilimini değiştirmek
    isterse baştan mod seçmesine gerek kalmaz)."""
    return _geri_menu(f"abcd:mode:{mode}")


def _geri_menu(hedef_callback_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Geri", callback_data=hedef_callback_data)]])


# --- Harmonik (Anlık D / V2.2) tarama akışı (Faz 6 uzantısı, 2026-08-19) ----------
#
# `harm:...` callback_data ailesi -- `harm:menu` (formasyon seçimi) ->
# `harm:tf:{FORMASYON}:{tf}` (zaman dilimi seçimi + doğrudan tarama başlar,
# `abcd:tf:tarama:{tf}` ile AYNI desen: metin istemeden başlar). `FORMASYON`
# `src.analysis.harmonic_scanner.FORMATION_NAMES`teki 5 isimden biri VEYA
# "HEPSI" (tümü, tek taramada 5 formasyonun hepsi). Kullanıcı talebi
# (2026-08-19): "abcd gartley grab gibi tüm formasyonları seçebileyim ...
# birde hepsi seçeneği olsun". `menu.py` katman disiplini gereği
# `harmonic_scanner.FORMATION_NAMES` BURAYA import EDİLMEZ (SAF UI) --
# aynı 5 isim bağımsız bir kopya olarak tutulur (abcd_tf_keyboard'daki
# `_ABCD_TIMEFRAMES` ile AYNI gerekçe).
_HARM_FORMATIONS: tuple[str, ...] = ("ABCD", "GARTLEY", "BAT", "BUTTERFLY", "CRAB")
_HARM_TIMEFRAMES: tuple[str, ...] = ("240", "1D")  # sadece bu ikisi backtest edildi (bkz. harmonic_scanner._PF_TABLE)

HARM_MENU_TEXT = (
    "🌀 Harmonik Tarama (Anlık D) — hangi formasyonu taratayım?\n"
    "⚠️ D, kendi pivot onayını BEKLEMEDEN anlık üretilir (repaint edebilir)."
)
HARM_TF_TEXT = "Zaman dilimini seç:"


def build_harm_formation_menu() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f, callback_data=f"harm:tfmenu:{f}")] for f in _HARM_FORMATIONS]
    rows.append([InlineKeyboardButton("🌐 HEPSİ (5 formasyon)", callback_data="harm:tfmenu:HEPSI")])
    rows.append([InlineKeyboardButton("⬅️ Geri", callback_data="menu:formasyonlar")])
    return InlineKeyboardMarkup(rows)


def build_harm_tf_menu(formation: str) -> InlineKeyboardMarkup:
    tf_row = [InlineKeyboardButton(tf, callback_data=f"harm:tf:{formation}:{tf}") for tf in _HARM_TIMEFRAMES]
    return InlineKeyboardMarkup([tf_row, [InlineKeyboardButton("⬅️ Geri", callback_data="harm:menu")]])


# --- İndikatörler (Momentum Confluence V1/V2 tarama, 2026-08-19) -----------------------------------------------------
#
# `ind:...` callback_data ailesi -- `harm:...` ile AYNI 3-adimli desen
# (`ind:menu` varyant secimi -> `ind:tfmenu:{variant}` zaman dilimi secimi ->
# `ind:tf:{variant}:{tf}` DOGRUDAN tum BIST taramasi baslar, tekli hisse
# modu YOK -- kullanici karari: Harmonik Tarama'nin basit akisi model alindi).
# `variant` "v1" | "v2" (`src.analysis.momentum_confluence.detect`in
# `variant` parametresiyle AYNI degerler). Sadece 240/1D backtest edildi
# (bkz. `docs/spec/MOMENTUM_CONFLUENCE_OPTIMIZASYON.md`), `_HARM_TIMEFRAMES`
# ile AYNI iki zaman dilimi kullanilir.
_IND_VARIANTS: tuple[tuple[str, str], ...] = (("v1", "🌊 Momentum Confluence V1"), ("v2", "🌊 Momentum Confluence V2"))
_IND_TIMEFRAMES: tuple[str, ...] = ("240", "1D")

IND_MENU_TEXT = "📶 İndikatörler — hangi göstergeyi taratayım?"
IND_TF_TEXT = "Zaman dilimini seç:"


def build_indikator_menu() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(label, callback_data=f"ind:tfmenu:{variant}")] for variant, label in _IND_VARIANTS]
    rows.append([InlineKeyboardButton("⬅️ Geri", callback_data="menu:root")])
    return InlineKeyboardMarkup(rows)


def build_indikator_tf_menu(variant: str) -> InlineKeyboardMarkup:
    tf_row = [InlineKeyboardButton(tf, callback_data=f"ind:tf:{variant}:{tf}") for tf in _IND_TIMEFRAMES]
    return InlineKeyboardMarkup([tf_row, [InlineKeyboardButton("⬅️ Geri", callback_data="ind:menu")]])


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
FORMASYONLAR_MENU_TEXT = "🔺 Formasyonlar — deneysel formasyon tespiti, temel/teknik skorlardan bağımsızdır:"
ABCD_MODE_TEXT = "🔍 ABCD Formasyonu — tek hisse mi bakmak istersin, yoksa tüm BİST'i mi taratayım?"
ABCD_TF_TEXT = "Zaman dilimini seç:"
ABCD_TEKLI_PROMPT = "Hisse kodunu yaz (örn: THYAO)"

ANALIZ_BIST_PROMPT = "Hisse kodunu yaz (örn: THYAO)"
ANALIZ_NASDAQ_PROMPT = "Sembolü yaz (örn: AAPL)"
TEKNIK_BIST_PROMPT = "Hisse kodunu yaz (örn: THYAO)"
TEKNIK_NASDAQ_PROMPT = "Sembolü yaz (örn: AAPL)"
DERIN_BIST_PROMPT = "Hisse kodunu yaz (örn: THYAO)"
DERIN_NASDAQ_PROMPT = "Sembolü yaz (örn: AAPL)"
