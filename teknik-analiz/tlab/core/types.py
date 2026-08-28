"""Çekirdek veri tipleri: OHLCV şeması, sinyal ve görsel primitifler.

Tüm indikatörler bu modüldeki tiplerle konuşur. Görselleştirme katmanı yalnızca
bu primitifleri (Level, Line, Box, Polygon, Marker) çizer; kendi hesap yapmaz.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal

import numpy as np
import pandas as pd

from tlab.core.errors import OHLCVError


class Timeframe(str, Enum):
    """Desteklenen zaman dilimleri (ileride W1 eklenebilir).

    H1 yalnızca veri katmanının (store/resample) iç kullanımı içindir;
    indikatörler yalnızca H4/D1 kabul eder.
    """

    H1 = "1H"
    H4 = "4H"
    D1 = "1D"


class Market(str, Enum):
    """Desteklenen piyasalar."""

    BIST = "bist"
    NASDAQ = "nasdaq"


Direction = Literal["long", "short", "neutral"]
SignalState = Literal["pending", "active", "confirmed", "invalidated", "completed", "expired"]


@dataclass(frozen=True)
class Level:
    """Yatay bir fiyat seviyesi (ör. POC, destek/direnç, Fibonacci seviyesi)."""

    price: float
    label: str
    style: str
    start: datetime | None = None
    end: datetime | None = None


@dataclass(frozen=True)
class Line:
    """İki veya daha fazla noktadan geçen çizgi (ör. trend çizgisi)."""

    points: tuple[tuple[datetime, float], ...]
    label: str
    style: str
    extend_right: bool = False


@dataclass(frozen=True)
class Box:
    """Bir zaman-fiyat dikdörtgeni (ör. konsolidasyon kutusu)."""

    t0: datetime
    t1: datetime
    low: float
    high: float
    label: str
    style: str


@dataclass(frozen=True)
class Polygon:
    """Gölgeli çokgen (ör. harmonik XAB/BCD üçgenleri)."""

    points: tuple[tuple[datetime, float], ...]
    label: str
    style: str


@dataclass(frozen=True)
class Marker:
    """Tek noktalı etiket/işaret (ör. pivot, sinyal oku)."""

    t: datetime
    price: float
    text: str
    kind: str


@dataclass(frozen=True)
class Signal:
    """Bir indikatörün ürettiği sinyal.

    bar_time: sinyalin ait olduğu bar. detected_at: bilginin fiilen elde
    edildiği bar (pivot onaylı sinyallerde bar_time'dan sonra olabilir).
    """

    bar_time: datetime
    detected_at: datetime
    direction: Direction
    state: SignalState
    score: float
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.detected_at < self.bar_time:
            raise OHLCVError(
                f"detected_at ({self.detected_at}) bar_time'dan ({self.bar_time}) önce olamaz"
            )
        if not 0.0 <= self.score <= 1.0:
            raise OHLCVError(f"score 0..1 aralığında olmalı, alınan: {self.score}")


@dataclass(frozen=True)
class IndicatorMeta:
    """Bir indikatör sınıfının sabit tanıtım bilgisi."""

    name: str
    version: str
    category: str
    description: str
    supported_timeframes: tuple[Timeframe, ...]


def _series_from_json(values: dict[str, float | None]) -> pd.Series:
    """`to_json()`'ın ürettiği {str(key): value} sözlüğünü geri bir Series'e
    çevirir. Series'ler İKİ türde index taşıyabilir: ÇOĞU zaman-indeksli
    (`str(pd.Timestamp)`), ama bazı indikatörler (ör. `PriceStructure`'ın
    `vp_bins`/`vp_volumes`/`vp_gauss`'ı — bkz. o modülün docstring'i)
    BİLEREK FİYAT-indekslidir. Anahtarları önce Timestamp olarak ayrıştırmayı
    dener; başarısız olursa (fiyat gibi salt sayısal bir anahtarsa) float
    index'e düşer. Bir Series'in TÜMÜ aynı index türünü paylaşır, bu yüzden
    karar tek bir anahtara bakarak verilir."""
    if not values:
        return pd.Series(dtype=float)
    first_key = next(iter(values))
    try:
        pd.Timestamp(first_key)
    except (ValueError, TypeError):
        return pd.Series({float(k): v for k, v in values.items()})
    return pd.Series({pd.Timestamp(k): v for k, v in values.items()})


@dataclass
class IndicatorResult:
    """Bir indikatörün tek bir (symbol, timeframe) koşusunun tam çıktısı.

    `series_layout` (Faz 7, viz): `series` sözlüğündeki hangi serilerin aynı
    alt panelde gruplanacağını belirtir — {panel_adı: [seri_adı, ...]}.
    Boş bırakılırsa (varsayılan) renderer alt panel çizmez (yalnızca ana
    mum grafiği + primitifler). "vp_" önekli seriler bu mekanizmaya DAHİL
    DEĞİLDİR — onlar fiyat-indeksli oldukları için renderer'da ayrı, özel
    bir yatay hacim profili paneline gider (bkz. `structure/price_structure.py`
    docstring'i)."""

    indicator: str
    version: str
    params_hash: str
    symbol: str
    timeframe: Timeframe
    signals: list[Signal] = field(default_factory=list)
    levels: list[Level] = field(default_factory=list)
    lines: list[Line] = field(default_factory=list)
    boxes: list[Box] = field(default_factory=list)
    polygons: list[Polygon] = field(default_factory=list)
    markers: list[Marker] = field(default_factory=list)
    series: dict[str, pd.Series] = field(default_factory=dict)
    series_layout: dict[str, list[str]] = field(default_factory=dict)
    last_state: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Seriler {timestamp_iso: value} sözlüğüne çevrilerek JSON string döner."""

        def _default(obj: Any) -> Any:
            if isinstance(obj, pd.Series):
                return {str(k): (None if pd.isna(v) else float(v)) for k, v in obj.items()}
            if isinstance(obj, (datetime, pd.Timestamp)):
                return obj.isoformat()
            if isinstance(obj, Timeframe):
                return obj.value
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            raise TypeError(f"JSON'a çevrilemeyen tip: {type(obj)}")

        payload = {
            "indicator": self.indicator,
            "version": self.version,
            "params_hash": self.params_hash,
            "symbol": self.symbol,
            "timeframe": self.timeframe.value,
            "signals": [asdict(s) for s in self.signals],
            "levels": [asdict(x) for x in self.levels],
            "lines": [asdict(x) for x in self.lines],
            "boxes": [asdict(x) for x in self.boxes],
            "polygons": [asdict(x) for x in self.polygons],
            "markers": [asdict(x) for x in self.markers],
            "series": self.series,
            "series_layout": self.series_layout,
            "last_state": self.last_state,
        }
        return json.dumps(payload, default=_default, ensure_ascii=False)

    @classmethod
    def from_json(cls, data: str) -> IndicatorResult:
        raw = json.loads(data)

        def _dt(value: str) -> datetime:
            return datetime.fromisoformat(value)

        def _points(raw_points: list[list[Any]]) -> tuple[tuple[datetime, float], ...]:
            return tuple((_dt(t), float(p)) for t, p in raw_points)

        signals = [
            Signal(
                bar_time=_dt(s["bar_time"]),
                detected_at=_dt(s["detected_at"]),
                direction=s["direction"],
                state=s["state"],
                score=s["score"],
                payload=s["payload"],
            )
            for s in raw["signals"]
        ]
        levels = [
            Level(
                price=x["price"],
                label=x["label"],
                style=x["style"],
                start=_dt(x["start"]) if x.get("start") else None,
                end=_dt(x["end"]) if x.get("end") else None,
            )
            for x in raw["levels"]
        ]
        lines = [
            Line(points=_points(x["points"]), label=x["label"], style=x["style"],
                 extend_right=x["extend_right"])
            for x in raw["lines"]
        ]
        boxes = [
            Box(t0=_dt(x["t0"]), t1=_dt(x["t1"]), low=x["low"], high=x["high"],
                label=x["label"], style=x["style"])
            for x in raw["boxes"]
        ]
        polygons = [
            Polygon(points=_points(x["points"]), label=x["label"], style=x["style"])
            for x in raw["polygons"]
        ]
        markers = [
            Marker(t=_dt(x["t"]), price=x["price"], text=x["text"], kind=x["kind"])
            for x in raw["markers"]
        ]
        series = {name: _series_from_json(values) for name, values in raw["series"].items()}

        return cls(
            indicator=raw["indicator"],
            version=raw["version"],
            params_hash=raw["params_hash"],
            symbol=raw["symbol"],
            timeframe=Timeframe(raw["timeframe"]),
            signals=signals,
            levels=levels,
            lines=lines,
            boxes=boxes,
            polygons=polygons,
            markers=markers,
            series=series,
            series_layout=raw.get("series_layout", {}),
            last_state=raw["last_state"],
        )


def validate_ohlcv(df: pd.DataFrame) -> None:
    """OHLCV DataFrame'inin şema ve tutarlılık kurallarını doğrular.

    Kurallar: tz-aware DatetimeIndex, monoton artan, tekrarsız; kolonlar
    open/high/low/close/volume; high >= max(open,close); low <= min(open,close);
    NaN yok. İhlalde OHLCVError fırlatır.
    """
    required_cols = {"open", "high", "low", "close", "volume"}
    missing = required_cols - set(df.columns)
    if missing:
        raise OHLCVError(f"Eksik kolonlar: {sorted(missing)}")

    if not isinstance(df.index, pd.DatetimeIndex):
        raise OHLCVError("Index DatetimeIndex olmalı")
    if df.index.tz is None:
        raise OHLCVError("Index tz-aware olmalı")
    if not df.index.is_monotonic_increasing:
        raise OHLCVError("Index monoton artan olmalı")
    if df.index.has_duplicates:
        raise OHLCVError("Index tekrarlayan zaman damgaları içeriyor")

    if df[list(required_cols)].isna().any().any():
        raise OHLCVError("OHLCV verisinde NaN değer var")

    high_ok = df["high"] >= df[["open", "close"]].max(axis=1)
    low_ok = df["low"] <= df[["open", "close"]].min(axis=1)
    if not bool(high_ok.all()):
        bad = df.index[~high_ok].tolist()
        raise OHLCVError(f"high >= max(open, close) ihlali: {bad[:5]}")
    if not bool(low_ok.all()):
        bad = df.index[~low_ok].tolist()
        raise OHLCVError(f"low <= min(open, close) ihlali: {bad[:5]}")
