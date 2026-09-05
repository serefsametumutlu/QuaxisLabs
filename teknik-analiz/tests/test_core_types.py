"""IndicatorResult.to_json()/from_json() round-trip.

Faz 6'da bulunan gerçek bir hata için regresyon: hiçbir Faz 0-5 testi bu
round-trip'i EGZERSİZ ETMEMİŞTİ (repaint_test doğrudan Python nesnelerini
karşılaştırır, JSON'a hiç uğramaz) — `structure.price_structure`'ın
FİYAT-indeksli `vp_bins`/`vp_volumes`/`vp_gauss` serileri, `from_json()`'ın
"her series zaman-indekslidir" varsayımını kırana kadar bu sessizce
kalmıştı (bkz. `tlab/scanner/engine.py`'nin worker'ları — sonuçları
süreçler arası JSON string olarak taşıyor, ilk gerçek round-trip BUYDU)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tlab.core.types import (
    Box,
    IndicatorResult,
    Level,
    Line,
    Marker,
    Polygon,
    Signal,
    Timeframe,
)

_TZ = "Europe/Istanbul"


def _sample_result() -> IndicatorResult:
    t1 = pd.Timestamp("2024-01-01", tz=_TZ)
    t2 = pd.Timestamp("2024-01-02", tz=_TZ)
    time_index = pd.date_range("2024-01-01", periods=3, freq="D", tz=_TZ)

    return IndicatorResult(
        indicator="test.roundtrip", version="0.1.0", params_hash="h1",
        symbol="TCELL", timeframe=Timeframe.D1,
        signals=[
            Signal(bar_time=t1, detected_at=t2, direction="long", state="confirmed",
                   score=0.75, payload={"a": 1, "b": "x", "c": None, "vol_ok": np.bool_(True)}),
        ],
        levels=[Level(price=100.5, label="POC", style="poc", start=t1, end=None)],
        lines=[
            Line(
                points=((t1, 1.0), (t2, 2.0)), label="l1", style="resistance", extend_right=True,
                touches=3, direction="rising", broken=False,
            )
        ],
        boxes=[Box(t0=t1, t1=t2, low=1.0, high=2.0, label="b1", style="range_box")],
        polygons=[
            Polygon(points=((t1, 1.0), (t2, 2.0), (t1, 3.0)), label="p1", style="bullish")
        ],
        markers=[Marker(t=t1, price=1.5, text="AL", kind="signal")],
        series={
            "close": pd.Series([1.0, 2.0, 3.0], index=time_index),
            "vp_bins": pd.Series(
                [10.5, 11.93666632970174, 13.2], index=[10.5, 11.93666632970174, 13.2]
            ),
        },
        last_state={"x": 1, "y": "text"},
    )


def test_roundtrip_preserves_signals_and_levels() -> None:
    result = _sample_result()
    restored = IndicatorResult.from_json(result.to_json())

    assert restored.indicator == result.indicator
    assert restored.signals[0].bar_time == result.signals[0].bar_time
    assert restored.signals[0].detected_at == result.signals[0].detected_at
    assert restored.signals[0].payload == result.signals[0].payload
    assert restored.levels[0].price == pytest.approx(result.levels[0].price)
    assert restored.levels[0].start == result.levels[0].start


def test_roundtrip_numpy_bool_payload_does_not_crash() -> None:
    """Faz 8A bulgusu: `payload`'da `numpy.bool_` (ör. `vol_ratio >= k`
    karşılaştırmasından) varsa `to_json()` eskiden `TypeError: JSON'a
    çevrilemeyen tip: <class 'numpy.bool'>` fırlatırdı — `trend.breakouts`
    scanner üzerinden (süreçler arası JSON) çalıştırılana kadar hiçbir test
    bunu yakalamamıştı."""
    result = _sample_result()
    restored = IndicatorResult.from_json(result.to_json())
    assert restored.signals[0].payload["vol_ok"] is True


def test_roundtrip_preserves_lines_boxes_polygons_markers() -> None:
    result = _sample_result()
    restored = IndicatorResult.from_json(result.to_json())

    assert restored.lines[0].points == result.lines[0].points
    assert restored.lines[0].touches == 3
    assert restored.lines[0].direction == "rising"
    assert restored.lines[0].broken is False
    assert restored.lines[0].extend_right is True
    assert restored.boxes[0].low == pytest.approx(result.boxes[0].low)
    assert restored.polygons[0].points == result.polygons[0].points
    assert restored.markers[0].text == "AL"


def test_roundtrip_time_indexed_series() -> None:
    result = _sample_result()
    restored = IndicatorResult.from_json(result.to_json())

    close = restored.series["close"]
    assert isinstance(close.index, pd.DatetimeIndex)
    assert list(close.to_numpy()) == pytest.approx([1.0, 2.0, 3.0])


def test_roundtrip_price_indexed_series_does_not_crash() -> None:
    """Faz 6 bulgusu: fiyat-indeksli seriler (vp_bins vb.) Timestamp OLARAK
    ayrıştırılmaya ÇALIŞILIRSA ValueError fırlatırdı — artık float index'e
    düşüyor."""
    result = _sample_result()
    restored = IndicatorResult.from_json(result.to_json())

    vp = restored.series["vp_bins"]
    assert not isinstance(vp.index, pd.DatetimeIndex)
    assert all(isinstance(x, float) for x in vp.index)
    assert sorted(vp.index) == pytest.approx([10.5, 11.93666632970174, 13.2])


def test_roundtrip_price_indexed_series_with_date_like_key_does_not_crash() -> None:
    """GERÇEK hata (Faz 8B sonrası, gerçek bir çoklu-süreç BIST taramasında
    ilk kez tetiklendi): eski `_series_from_json` yalnızca serinin İLK
    anahtarına bakıp karar veriyordu ("Timestamp olarak ayrıştırılamazsa
    float'a düş") — ama `pd.Timestamp` çok esnek: `"2026.5"` RASTLANTISAL
    olarak geçerli bir tarihe ("2026-05-01") ayrıştırılıyor, `"4749.375"`
    (aynı fiyat-indeksli serideki BAŞKA bir anahtar) ise ayrıştırılamıyor —
    ilk anahtar "yanlışlıkla" geçtiği için fonksiyon TÜM anahtarları
    Timestamp sanıp ikincisinde yakalanmamış bir `DateParseError`le
    çöküyordu. Düzeltme: karar artık içerik sezgisi değil, serinin adının
    `vp_` önekini taşıyıp taşımadığına bakıyor (`series_layout`
    docstring'indeki ZATEN var olan sözleşme)."""
    result = IndicatorResult(
        indicator="test.roundtrip", version="0.1.0", params_hash="h1",
        symbol="TEST", timeframe=Timeframe.D1,
        series={"vp_bins": pd.Series([1.0, 2.0], index=[2026.5, 4749.375])},
    )
    restored = IndicatorResult.from_json(result.to_json())
    vp = restored.series["vp_bins"]
    assert not isinstance(vp.index, pd.DatetimeIndex)
    assert sorted(vp.index) == pytest.approx([2026.5, 4749.375])


def test_roundtrip_empty_series_does_not_crash() -> None:
    result = _sample_result()
    result.series["empty"] = pd.Series(dtype=float)
    restored = IndicatorResult.from_json(result.to_json())
    assert restored.series["empty"].empty
