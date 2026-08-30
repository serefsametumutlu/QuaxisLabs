"""Görsel temalar — tüm renkler TEK yerden (`renderer.py`/`table.py`/`report.py`
kendi renk sabitini taşımaz). İki tema: `dark_terminal` (pair paneli, Görsel 1/4)
ve `light_analysis` (yapı/harmonik panelleri, Görsel 2/3/5).

**2026-08-29 palet revizyonu (aracı kurum raporu tasarım geçişi):** Eskiden
`_FIB_NEAREST`/`_LINE_STYLE_COLOR`/`_FILL_STYLE_COLOR` gri/kırmızı/sarı/yeşil/
mavi/mor'u oldukça keyfi dağıtıyordu ("varsayılan grafik kütüphanesi gökkuşağı"
hissi veriyordu). Artık bilinçli bir hiyerarşi var: `accent` (TEK bir marka
rengi, altın/hardal tonu — hem karanlık hem aydınlık temada "en karara-değer"
öğeler için ayrılmış: POC, fib altın bölgesi [%61.8/%78.6], başlık/kart
vurgusu), yön anlamı taşıyan `green`/`red` (`up`/`down` mumlarla AYNI — bu
LOAD-BEARING, değişmedi), yapısal-nötr `blue` (destek/MA gibi "önemli ama
marka rengi değil" öğeler) ve gerisi (`gray`/`muted`) — eski sarı/mor/turuncu
serpiştirmesi kalktı. `page_bg`/`border`/`accent` YENİ alanlar (kart/sayfa
çerçevesi ve başlık/dipnot şeridi için, bkz. `renderer.py::_apply_layout`).

**2026-08-30 kısmi geri dönüş (`_FIB_NEAREST` YALNIZCA):** kullanıcı gerçek
referans ekran görüntüleriyle (images/) kıyaslayınca fib merdiveninin tek-gri
minimalizmini "aracı kurum raporu"na göre fakir buldu — her basamak artık
yine ayrı bir Theme rengi taşıyor (bkz. `_FIB_NEAREST` docstring'i). Bu
DEĞİŞİKLİK yalnızca fib seviyelerini kapsar; yukarıdaki hiyerarşinin geri
kalanı (accent kıtlığı, resistance/support kırmızı/mavi eşleşmesi, vb.)
AYNEN korunuyor."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    bg: str
    grid: str
    text: str
    muted: str
    up: str
    down: str
    green: str
    red: str
    orange: str
    blue: str
    yellow: str
    purple: str
    gray: str
    # Sayfa/kart çerçevesi (bkz. modül docstring'i, `renderer.py::_apply_layout`):
    # `page_bg` dış "sayfa" zemini, `bg` iç "kart" (plot) zemini, `border` ikisi
    # arasındaki ince çerçeve/legend kenarlığı.
    page_bg: str = "#f2f3f5"
    border: str = "#d8dce1"
    # Tek marka/vurgu rengi — "en karara-değer" öğeler İÇİN AYRILMIŞ (POC, fib
    # altın bölgesi, başlık vurgusu); her yerde kullanılmaz, bilinçli kıtlık.
    accent: str = "#b8860b"
    font: str = "Consolas, 'Courier New', monospace"


DARK_TERMINAL = Theme(
    name="dark_terminal",
    # 2026-08-29 pair-modu düzeltmesi (bkz. renderer.py `_render_pair` +
    # CLAUDE.md kaydı): kullanıcı paylaşılan "aracı kurum raporu" tasarım
    # geçişini bu TEK grafik için reddetti, referans ekran görüntüsündeki
    # (images/Ekran görüntüsü 2026-08-26 203751.png) neredeyse SAF SİYAH
    # zemine geri dönüldü — eskiden `bg="#0e1116"` (page_bg'den belirgin
    # şekilde daha açık bir "kart" hissi veriyordu, referansta öyle bir
    # ayrım yok). `grid` de aynı gerekçeyle biraz karartıldı. Bu tema
    # YALNIZCA pair modunda kullanılıyor (bkz. modül docstring'i) + Görsel 4
    # metrik tablosunda (`table.py`) — ikisi de bu revizyondan aynı yönde
    # (daha koyu/sade) etkilenmesi istenen yerler.
    bg="#000000",
    grid="#161a1f",
    text="#d7dde3",
    muted="#8b98a5",
    up="#2ecc71",
    down="#e74c3c",
    green="#2ecc71",
    red="#e74c3c",
    orange="#e08b2f",
    blue="#4c8ef7",
    yellow="#e0c72f",
    purple="#9b6fe0",
    gray="#5a6773",
    page_bg="#000000",
    border="#2a323c",
    accent="#d4af37",
)

LIGHT_ANALYSIS = Theme(
    name="light_analysis",
    bg="#ffffff",
    grid="#e6e9ec",
    text="#1c2530",
    muted="#6b7684",
    up="#1f9d55",
    down="#d64545",
    green="#1f9d55",
    red="#d64545",
    orange="#d98a1f",
    blue="#2f6fd6",
    yellow="#c9a416",
    purple="#7b4fc9",
    gray="#8b95a1",
    page_bg="#eef0f3",
    border="#d8dce1",
    accent="#9c6b0b",
    font="Segoe UI, Arial, sans-serif",
)

_THEMES: dict[str, Theme] = {"dark_terminal": DARK_TERMINAL, "light_analysis": LIGHT_ANALYSIS}

_FIB_NEAREST: dict[float, str] = {
    # 2026-08-30 geri dönüş: kullanıcı, referans ekran görüntülerindeki
    # ("aracı kurum raporu" mockup'ları — images/) her basamağı AYRI renkte
    # gösteren "gökkuşağı" fib merdivenini, 2026-08-29'un tek-marka-rengi
    # minimalist paletine TERCİH ETTİ (o palet BİLİNÇLİ bir tasarım kararıydı,
    # ama kullanıcı gerçek örneklerle kıyaslayınca daha zengin/ayırt edici
    # görünümü istedi — bkz. CLAUDE.md 2026-08-30 kaydı). Klasik "altın bölge"
    # (%61.8/%78.6) hâlâ marka rengini (`accent`) taşır — bu ikisi hâlâ "en
    # karara-değer" seviye; geri kalanı artık Theme'in mevcut alanlarından
    # (yeni renk EKLENMEDİ) birbirinden ayırt edilebilir bir sıra oluşturur.
    0.236: "purple",
    0.382: "blue",
    0.5: "yellow",
    0.618: "accent",
    0.786: "accent",
    1.0: "text",
    1.272: "orange",
    1.618: "red",
    2.0: "purple",
}

_LINE_STYLE_COLOR: dict[str, str] = {
    # Direnç/destek YÖN-anlamlı çift (kırmızı/mavi) olarak kalır (indikatörün
    # kendi çekirdek çıktısı — decision-relevant); jenerik dashed/dotted/swing
    # (bağlamsal yardımcı çizgiler) artık `muted`/`gray`'e çekiliyor (eskiden
    # mavi/mor/turuncu). POC artık marka rengini (`accent`) alıyor — hacim
    # profilindeki TEK en karara-değer seviye.
    "resistance": "red",
    "support": "blue",
    "dashed": "muted",
    "dotted": "gray",
    "swing": "muted",
    "bullish": "green",
    "bearish": "red",
    "poc": "accent",
    "value_area": "gray",
    # Faz 8C: pivot kanalı (weekly_channel) — extend-only, tek çizgi ailesi.
    "channel": "blue",
    # Regresyon kanalının "şu an" görünümü (her barda değişir, bkz.
    # weekly_channel.py docstring'i) -> marka rengi, belirgin.
    "channel_current": "accent",
    # Geçmiş bir sinyal barında DONDURULMUŞ kanal -> soluk/bağlamsal.
    "channel_frozen": "muted",
}

_FILL_STYLE_COLOR: dict[str, str] = {
    # `resistance_zone`/`support_zone` artık KENDİ trendline eşdeğeriyle
    # (`_LINE_STYLE_COLOR`'daki resistance/support) AYNI aile — eskiden
    # direnç ÇİZGİSİ kırmızı ama direnç BÖLGESİ sarıydı (tutarsız, "hangi
    # ikisi eşleşiyor" belirsizdi). `y_holding`/`x_holding` BİLİNÇLİ OLARAK
    # kendi çizgi renkleriyle (Y=mavi, X=gri) HİZALI DEĞİL — 2026-08-29 pair
    # düzeltmesinde kullanıcının referans ekran görüntüsü (images/Ekran
    # görüntüsü 2026-08-26 203751.png) Y-tutulan-dönem için doygun bir yeşil,
    # X-tutulan-dönem için koyu mavi/gri-mavi kullanıyordu — bu ikisi çizgi
    # kimliğinden (hangi sembol) değil, referansın kendi gölgeleme
    # sözleşmesinden geliyor, bilerek KORUNDU.
    "resistance_zone": "red",
    "support_zone": "blue",
    "range_box": "gray",
    "bullish": "green",
    "bearish": "red",
    "y_holding": "green",
    "x_holding": "blue",
    # Faz 8C golden_zone.py — "altın gölgeli bant" spec'i: TEK marka rengi.
    "golden_zone": "accent",
    "golden_zone_alt": "yellow",
    # Faz 8C supply_demand.py — klasik yeşil (talep) / kırmızı (arz);
    # kırılan bölgeler soluk (gray) kalır (spec: "broken bölgeler soluk").
    "demand": "green",
    "supply": "red",
    "demand_broken": "gray",
    "supply_broken": "gray",
}


def resolve_theme(theme: Theme | str | None, *, default: Theme) -> Theme:
    if theme is None or theme == "auto":
        return default
    if isinstance(theme, Theme):
        return theme
    key = theme if theme in _THEMES else f"{theme}_terminal" if theme == "dark" else theme
    key = "light_analysis" if theme == "light" else key
    key = "dark_terminal" if theme == "dark" else key
    if key not in _THEMES:
        raise ValueError(f"Bilinmeyen tema: {theme} (bekleniyor: dark|light|{sorted(_THEMES)})")
    return _THEMES[key]


def fib_color(theme: Theme, level: float) -> str:
    nearest = min(_FIB_NEAREST, key=lambda k: abs(k - level))
    return getattr(theme, _FIB_NEAREST[nearest])


def line_color(theme: Theme, style: str) -> str:
    name = _LINE_STYLE_COLOR.get(style)
    if name is not None:
        return getattr(theme, name)
    if style.startswith("fib_"):
        return theme.gray
    return theme.gray


def fill_color(theme: Theme, style: str, opacity: float = 0.15) -> str:
    name = _FILL_STYLE_COLOR.get(style, "gray")
    return with_alpha(getattr(theme, name), opacity)


def with_alpha(hex_color: str, alpha: float) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"
