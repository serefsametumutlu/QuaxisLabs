"""Görsel temalar — tüm renkler TEK yerden (`renderer.py`/`table.py`/`report.py`
kendi renk sabitini taşımaz). İki tema: `dark_terminal` (pair paneli, Görsel 1/4)
ve `light_analysis` (yapı/harmonik panelleri, Görsel 2/3/5)."""

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
    font: str = "Consolas, 'Courier New', monospace"


DARK_TERMINAL = Theme(
    name="dark_terminal",
    bg="#0b0e11",
    grid="#20262e",
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
    font="Segoe UI, Arial, sans-serif",
)

_THEMES: dict[str, Theme] = {"dark_terminal": DARK_TERMINAL, "light_analysis": LIGHT_ANALYSIS}

_FIB_NEAREST: dict[float, str] = {
    0.236: "gray",
    0.382: "red",
    0.5: "yellow",
    0.618: "green",
    0.786: "blue",
    1.0: "gray",
    1.272: "purple",
    1.618: "red",
    2.0: "gray",
}

_LINE_STYLE_COLOR: dict[str, str] = {
    "resistance": "red",
    "support": "blue",
    "dashed": "blue",
    "dotted": "purple",
    "swing": "orange",
    "bullish": "green",
    "bearish": "red",
    "poc": "orange",
    "value_area": "gray",
}

_FILL_STYLE_COLOR: dict[str, str] = {
    "resistance_zone": "yellow",
    "support_zone": "blue",
    "range_box": "gray",
    "bullish": "green",
    "bearish": "red",
    "y_holding": "green",
    "x_holding": "blue",
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
