"""Ortak istisna sınıfları."""

from __future__ import annotations


class OHLCVError(Exception):
    """OHLCV veri şeması veya tutarlılık ihlali."""


class RegistryError(Exception):
    """İndikatör registry kaydı sırasında oluşan hata (örn. repaint testi FAIL)."""


class RepaintError(Exception):
    """Bir indikatörün repaint/lookahead ihlali tespit edildiğinde kullanılabilir."""
