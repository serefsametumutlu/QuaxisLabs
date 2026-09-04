"""Parametre taban sınıfı ve deterministik hash yardımcıları."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass, replace
from typing import TYPE_CHECKING, ClassVar, TypeVar

if TYPE_CHECKING:
    from tlab.core.types import Timeframe

_P = TypeVar("_P", bound="BaseParams")

# Faz 0.5, A2 (docs/TANI_VE_YOL_HARITASI_v2.md): 1D TABAN kabul edilir.
# Bar-cinsi her eşik, aynı TAKVİMSEL süreyi temsil etsin diye bu katsayıyla
# çarpılır -- 4H'te 1D'lik bir eşik 6 kat daha AZ bar demekti (kalibre edilen
# her şey 6 KAT SIKI olurdu), bu satır o sistemik hatayı kapatıyor.
#
# Faz 1, 1D DÜZELTMESİ (2026-09-04, docs/spec/FORMASYON_DENETIM_v2.md):
# yukarıdaki 24.0/6.0 değerleri "gün 24 saat sürekli işlem görür" varsayımına
# dayanıyordu (24h/1h=24, 24h/4h=6) -- ama BIST seansı 10:00-18:00 (8 saat)
# ve GERÇEK bar sayısı (data/resample.py'nin 09:00/13:00/17:00 hizalamasıyla,
# gerçek ISCTR verisinde ÖLÇÜLDÜ) günde ORTALAMA 9 (1H) / 3 (4H) -- yani
# eski katsayılar 1H'de ~2.7x, 4H'de TAM 2x FAZLA SIKI ölçekliyordu. GERÇEK
# BULGU: bu, `patterns.double_top_bottom`'un min_bars_between=22'sinin 4H'te
# 132 bara (22 gün yerine 44 gün) ölçeklenmesine, ve dolayısıyla 120 gerçek
# BIST sembolünde SIFIR sinyale (125->0) yol açmıştı. Düzeltilmiş katsayılar
# BIST'in GERÇEK seans yapısına göre kalibre edildi (NASDAQ/kripto gibi farklı
# seans uzunluğuna sahip piyasalar için bu tablo Market-farkında DEĞİL --
# bilinçli bir basitleştirme, tlab'ın birincil evreni BIST).
_TF_BAR_SCALE: dict[str, float] = {
    "1H": 9.0,
    "4H": 3.0,
    "1D": 1.0,
    "1W": 1.0 / 5.0,
}


@dataclass(frozen=True)
class BaseParams:
    """Tüm indikatör/özellik parametre sınıflarının türediği taban sınıf.

    Alt sınıflar frozen dataclass olmalı; parametreler değişmez ve hash'lenebilir olmalı.

    `_BAR_FIELDS` (Faz 0.5, A2): TAKVİMSEL bir süreyi temsil eden bar-cinsi
    alan adları (ör. "min_bars_between", "range_min_bars"). `ClassVar` olduğu
    için dataclass alanı SAYILMAZ (constructor/asdict/params_hash'e girmez).
    KASITLI OLARAK bar-cinsi olup DA _BAR_FIELDS'e girmeyen alanlar var:
    pivot `left`/`right` (A1'in `atr_mult` ile çözdüğü ayrı bir sorun —
    "fixed" moduna manuel geçilmedikçe zaten devrede değil), `confirm_bars`/
    `*_confirm` (sinyal MEKANİĞİ, takvimsel bir süre değil — "N bar bekle"
    kuralı tasarım gereği ham bar'da kalır), `atr_period`/`vol_ma_window`/
    `macd_*`/`rsi_period` (TA'nın evrensel kısaltmaları — RSI(14)/MACD(12,26,9)
    HER zaman dilimde AYNI ham bar sayısıyla anılır, kaynak literatür bunu
    böyle tanımlar)."""

    _BAR_FIELDS: ClassVar[frozenset[str]] = frozenset()

    def for_timeframe(self: _P, tf: Timeframe) -> _P:
        """`_BAR_FIELDS`'teki her alanı `tf`'ye göre ölçekler (1D taban).

        round() + max(1, ...) ile -- 0'a yuvarlanan bir eşik (ör. min_bars=0)
        anlamsız/etkisiz bir parametreye dönüşürdü. `_BAR_FIELDS` boşsa ya da
        `tf` zaten 1D'yse (çarpan 1.0) hiçbir kopya oluşturmadan `self`
        döner (gereksiz alloc yok)."""
        if not self._BAR_FIELDS:
            return self
        scale = _TF_BAR_SCALE.get(tf.value, 1.0)
        if scale == 1.0:
            return self
        updates = {
            name: max(1, round(getattr(self, name) * scale)) for name in self._BAR_FIELDS
        }
        return replace(self, **updates)


def params_hash(params: BaseParams) -> str:
    """Parametrelerin sıralı anahtarlı JSON gösteriminin SHA1 özeti.

    Aynı parametre değerleri her zaman aynı hash'i üretir (deterministik).
    """
    if not is_dataclass(params):
        raise TypeError("params_hash yalnızca dataclass örnekleri kabul eder")
    payload = json.dumps(asdict(params), sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()
