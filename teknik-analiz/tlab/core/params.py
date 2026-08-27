"""Parametre taban sınıfı ve deterministik hash yardımcıları."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass


@dataclass(frozen=True)
class BaseParams:
    """Tüm indikatör/özellik parametre sınıflarının türediği taban sınıf.

    Alt sınıflar frozen dataclass olmalı; parametreler değişmez ve hash'lenebilir olmalı.
    """


def params_hash(params: BaseParams) -> str:
    """Parametrelerin sıralı anahtarlı JSON gösteriminin SHA1 özeti.

    Aynı parametre değerleri her zaman aynı hash'i üretir (deterministik).
    """
    if not is_dataclass(params):
        raise TypeError("params_hash yalnızca dataclass örnekleri kabul eder")
    payload = json.dumps(asdict(params), sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()
