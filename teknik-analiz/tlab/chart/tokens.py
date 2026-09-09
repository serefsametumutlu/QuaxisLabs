"""Grafik tasarım token'ları — TEK renk/ölçü kaynağı.

`tlab/viz/themes.py`'nin yerini alır. Oradaki hata, stil adlarının
(`demand`, `supply`, ...) bir sözlükte AYRI AYRI tanımlanması ve eksik
kalan adın SESSİZCE griye düşmesiydi (bkz. docs/GORSEL_HATA_TESHISI.md).
Burada renk, ANLAMDAN türetilir: bir çizimin rolü (`bullish`, `bearish`,
`neutral`, `accent`) + yoğunluğu (`line`, `fill`, `muted`) verilir; eksik
ad diye bir şey YOKTUR, rol kümesi kapalıdır.

Üç tema, kullanıcının seçtiği üç yön (docs/design/grafik_stil_vitrini.html):
  light     — "Klasik Beyaz Rapor"
  dark      — "Terminal Koyu"
  paper     — "Kağıt Rapor"
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Role = Literal["bullish", "bearish", "neutral", "accent", "warn"]
ThemeName = Literal["light", "dark", "paper"]


@dataclass(frozen=True)
class Palette:
    bg: str
    panel_bg: str
    grid: str
    axis: str
    text: str
    text_muted: str
    # rol -> çizgi rengi
    bullish: str
    bearish: str
    neutral: str
    accent: str
    warn: str
    # mum gövdesi
    candle_up: str
    candle_down: str
    candle_up_line: str
    candle_down_line: str
    # hover kutusu
    hover_bg: str
    hover_border: str


_LIGHT = Palette(
    bg="#ffffff", panel_bg="#ffffff",
    grid="#eef1f4", axis="#c9d1d9", text="#1c2128", text_muted="#6b7480",
    bullish="#1a9850", bearish="#d6455d", neutral="#7a8794",
    accent="#2f6fb0", warn="#d98b1f",
    candle_up="#26a37a", candle_down="#e05563",
    candle_up_line="#1e7f60", candle_down_line="#c0414e",
    hover_bg="#ffffff", hover_border="#c9d1d9",
)

_DARK = Palette(
    bg="#0d1117", panel_bg="#0d1117",
    grid="#1c2430", axis="#2b3440", text="#e2e8ef", text_muted="#8b95a3",
    bullish="#3ddc97", bearish="#ff6b81", neutral="#8b95a3",
    accent="#6aa9ff", warn="#f5b342",
    candle_up="#26a37a", candle_down="#e05563",
    candle_up_line="#3ddc97", candle_down_line="#ff6b81",
    hover_bg="#161b22", hover_border="#2b3440",
)

_PAPER = Palette(
    bg="#faf8f3", panel_bg="#faf8f3",
    grid="#e8e2d6", axis="#c4bba8", text="#2b2823", text_muted="#7a7364",
    bullish="#3f7d4e", bearish="#a8434f", neutral="#8a8172",
    accent="#3a6280", warn="#b8842c",
    candle_up="#4a8c5e", candle_down="#b35461",
    candle_up_line="#356b46", candle_down_line="#8f4049",
    hover_bg="#faf8f3", hover_border="#c4bba8",
)

PALETTES: dict[str, Palette] = {"light": _LIGHT, "dark": _DARK, "paper": _PAPER}


@dataclass(frozen=True)
class Metrics:
    """Ölçüler — referans görsellerden ölçülerek alındı."""

    # panel yükseklik oranları (fiyat her zaman ilk)
    panel_ratio_price: float = 0.56
    panel_ratio_sub: float = 0.147
    panel_gap: float = 0.035

    line_pattern: float = 2.0       # formasyon sınır çizgisi
    line_level: float = 1.4         # yatay seviye
    line_series: float = 1.3        # MA/gösterge serisi
    line_guide: float = 1.0         # RSI 30/70 gibi kılavuz

    marker_touch: float = 8.0       # temas dairesi
    marker_signal: float = 13.0     # AL/SAT üçgeni
    marker_pivot: float = 7.0       # HH/LH/HL/LL üçgeni

    font_family: str = "Inter, -apple-system, Segoe UI, Roboto, sans-serif"
    font_mono: str = "JetBrains Mono, SFMono-Regular, Menlo, monospace"
    font_title: int = 15
    font_sub: int = 11
    font_label: int = 10
    font_axis: int = 11

    fill_alpha_zone: float = 0.055  # arz/talep, aralık bandı
    fill_alpha_shape: float = 0.13  # harmonik gövde

    margin_l: int = 12
    margin_r: int = 132             # sağ eksen + sağ kenar etiketleri için
    margin_t: int = 64
    margin_b: int = 36


METRICS = Metrics()


def rgba(hex_color: str, alpha: float) -> str:
    """'#rrggbb' -> 'rgba(r,g,b,alpha)'. Plotly fillcolor için."""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        raise ValueError(f"6 haneli hex bekleniyor, alındı: {hex_color!r}")
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha:g})"


def palette(theme: ThemeName) -> Palette:
    try:
        return PALETTES[theme]
    except KeyError:
        raise ValueError(
            f"bilinmeyen tema {theme!r} — geçerli: {sorted(PALETTES)}"
        ) from None


def role_color(theme: ThemeName, role: Role) -> str:
    """Rol -> renk. Rol kümesi KAPALI: yanlış ad sessizce griye düşmez, patlar."""
    p = palette(theme)
    table = {
        "bullish": p.bullish, "bearish": p.bearish,
        "neutral": p.neutral, "accent": p.accent, "warn": p.warn,
    }
    try:
        return table[role]
    except KeyError:
        raise ValueError(
            f"bilinmeyen rol {role!r} — geçerli: {sorted(table)}"
        ) from None
