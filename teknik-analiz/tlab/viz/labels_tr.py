"""Türkçe etiket sözlükleri — `renderer.py`/`table.py`/`report.py` bunları
kullanır, kendi metin sabitlerini taşımaz (tek doğru kaynak burası)."""

from __future__ import annotations

STATE_TR: dict[str, str] = {
    "pending": "BEKLEMEDE",
    "active": "AKTİF",
    "confirmed": "TAMAMLANDI",
    "invalidated": "GEÇERSİZ",
    "completed": "TAMAM",
    "expired": "SÜRESİ DOLDU",
}

STYLE_TR: dict[str, str] = {
    "resistance": "Direnç",
    "support": "Destek",
    "resistance_zone": "Direnç Bölgesi",
    "support_zone": "Destek Bölgesi",
    "range_box": "Konsolidasyon",
    "poc": "POC",
    "value_area": "Değer Alanı",
    "fib_retracement": "Fib Geri Çekilme",
    "fib_extension": "Fib Uzatma",
    "bullish": "Boğa",
    "bearish": "Ayı",
    "y_holding": "Tutulan Dönem",
    "x_holding": "Tutulan Dönem",
}

DIRECTION_TR: dict[str, str] = {"long": "AL", "short": "SAT", "neutral": "NÖTR"}

INDICATOR_CATEGORY_TR: dict[str, str] = {
    "harmonics": "Harmonik Formasyon",
    "structure": "Fiyat Yapısı",
    "pair": "Pair (Rölatif Momentum)",
}


def tr_state(state: str) -> str:
    return STATE_TR.get(state, state.upper())


def tr_style(style: str) -> str:
    return STYLE_TR.get(style, style)


def tr_direction(direction: str) -> str:
    return DIRECTION_TR.get(direction, direction.upper())
