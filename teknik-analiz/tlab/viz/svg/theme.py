"""SVG motorunun kullandığı tema tanımları.

`tlab/viz/themes.py::Theme`'i (Plotly dönemi) SVG'nin ihtiyaç duyduğu ek
alanlarla (accent2, demand/supply/neckline/pole, card_bg/card_border, radius,
candle_w, glow, font_display/font_body/mono) genişletir. Değerler
`docs/design/grafik_stil_vitrini.html::THEMES` sabitindeki `classic`/`dark`/
`editorial`den BİREBİR alındı -- Faz 3'ün "bitti" kriteri bu üç temanın
referansla piksel düzeyinde ayırt edilemez olmasını istiyor
(TANI_VE_YOL_HARITASI_v2.md, Faz 3/3A).

**Tespit edilen fark** (spec'in istediği "farkları tespit et" adımı):
`themes.py::Theme.muted` `neckline` ile YALNIZCA editorial'da tam eşleşiyor
(`#8c7d5f`) -- classic'te `muted=#c7cdd6` ama artifact `neckline=#8b93a1`,
dark'ta `muted=#2a303c` ama artifact `neckline=#565d6a`. Bu yüzden mevcut
Theme'in yaklaşık eşlemesi yerine artifact'in kendi hex değerleri temel
alındı (artifact doğru kabul edildi, spec'in açık talimatı)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SVGTheme:
    key: str
    name: str
    page_bg: str
    card_bg: str
    card_border: str
    text: str
    text_muted: str
    text_faint: str
    grid: str
    axis: str
    up: str
    down: str
    accent: str
    accent2: str
    support: str
    resistance: str
    demand: str
    supply: str
    target: str
    muted: str
    pole: str
    neckline: str
    font_display: str
    font_body: str
    mono: str
    radius: float
    candle_w: float
    wick_opacity: float
    glow: bool


CLASSIC = SVGTheme(
    key="classic", name="Klasik Beyaz Rapor",
    page_bg="#eef0f3", card_bg="#ffffff", card_border="#e3e6ea",
    text="#161a20", text_muted="#838b98", text_faint="#aeb4bf",
    grid="#eef1f4", axis="#c7cdd6",
    up="#1f9d5c", down="#cf4a3e",
    accent="#b8892f", accent2="#35618c",
    support="#35618c", resistance="#c0554a", demand="#1f9d5c", supply="#c0554a",
    target="#8b93a1", muted="#c7cdd6", pole="#1f9d5c", neckline="#8b93a1",
    font_display="'Source Serif 4', Georgia, serif",
    font_body="'Inter', -apple-system, 'Segoe UI', sans-serif",
    mono="'IBM Plex Mono', ui-monospace, monospace",
    radius=8, candle_w=0.58, wick_opacity=0.9, glow=False,
)

DARK = SVGTheme(
    key="dark", name="Terminal Koyu",
    page_bg="#090b0f", card_bg="#0d1015", card_border="#1b2028",
    text="#e7eaf0", text_muted="#6d7480", text_faint="#454b56",
    grid="#161a21", axis="#232935",
    up="#22d67f", down="#ff5c5c",
    accent="#f5b400", accent2="#35b8ff",
    support="#35b8ff", resistance="#ff5c5c", demand="#22d67f", supply="#ff5c5c",
    target="#7d8494", muted="#2a303c", pole="#22d67f", neckline="#565d6a",
    font_display="'JetBrains Mono', ui-monospace, monospace",
    font_body="'Inter', -apple-system, sans-serif",
    mono="'JetBrains Mono', ui-monospace, monospace",
    radius=6, candle_w=0.56, wick_opacity=0.95, glow=True,
)

EDITORIAL = SVGTheme(
    key="editorial", name="Kağıt Rapor",
    page_bg="#efe7d4", card_bg="#faf6ec", card_border="#e1d5b7",
    text="#2c2418", text_muted="#8c7d5f", text_faint="#c3b696",
    grid="#eadfc4", axis="#d8c9a3",
    up="#3c6b4c", down="#a3402c",
    accent="#b8802a", accent2="#4d5c73",
    support="#4d5c73", resistance="#a3402c", demand="#3c6b4c", supply="#a3402c",
    target="#8c7d5f", muted="#d8c9a3", pole="#3c6b4c", neckline="#8c7d5f",
    font_display="'Playfair Display', Georgia, serif",
    font_body="'Source Serif 4', Georgia, serif",
    mono="'IBM Plex Mono', ui-monospace, monospace",
    radius=3, candle_w=0.56, wick_opacity=0.85, glow=False,
)

_THEMES: dict[str, SVGTheme] = {"classic": CLASSIC, "dark": DARK, "editorial": EDITORIAL}
_ALIASES = {"light": "classic", "paper": "editorial"}


def resolve_svg_theme(theme: str | SVGTheme | None) -> SVGTheme:
    if theme is None:
        return CLASSIC
    if isinstance(theme, SVGTheme):
        return theme
    key = _ALIASES.get(theme, theme)
    if key not in _THEMES:
        raise ValueError(f"Bilinmeyen SVG teması: {theme} (bekleniyor: {sorted(_THEMES)})")
    return _THEMES[key]
