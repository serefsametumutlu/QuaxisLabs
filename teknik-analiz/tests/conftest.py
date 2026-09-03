"""Proje-geneli pytest seçenekleri.

`--update-golden`: `tests/test_viz/test_golden.py`'nin (Faz 0, İş 3 — görsel
gerileme testi) onaylı referans çıktılarını YENİDEN ÜRETMEK için. Bayrak
OLMADAN hiçbir test golden dosyayı yazmaz -- yalnızca karşılaştırır."""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-golden",
        action="store_true",
        default=False,
        help=(
            "tests/test_viz/golden/ altındaki onaylı referans çıktılarını "
            "mevcut renderer çıktısıyla YENİDEN ÜRETİR (üzerine yazar). "
            "Yalnızca KASITLI bir tasarım değişikliğinden sonra kullan."
        ),
    )
