"""Faz 4 (yapı indikatörleri) testleri için paylaşılan sentetik OHLCV fixture'ları.

Tüm sabitler gerçek kod çalıştırılarak doğrulanmıştır (bkz.
tests/test_harmonics/test_schools.py'deki aynı ilke) — bu dosyadaki sayılar
SONUÇ, türetme süreci değil.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from tlab.core.types import Timeframe
from tlab.testing.fixtures import make_zigzag


def build_abcd_ohlcv() -> pd.DataFrame:
    """İki ardışık AB=CD üçlüsü içeren seri.

    1. üçlü: A=100(low)@idx2, B=130(high)@idx11, C=115(retrace ~.5)@idx15.
    D hedefleri (abcd_ratios=(1.0,1.272,1.618)): ~145.07 / ~153.26 / ~163.68.
    Fiyat idx25'te 146'ya çıkarak ratio=1.0 hedefini "completed" yapar,
    ratio=1.272/1.618 hâlâ "pending/active" iken idx30'da YENİ bir C
    (2. üçlü, A=115@idx15, B=146@idx25, C=122@idx30) doğar ve eskilerini
    "invalidated" yapar."""
    pivots = [
        (0, 100), (5, 100), (10, 130), (15, 115), (25, 146),
        (30, 122), (35, 150), (40, 128), (45, 135),
    ]
    return make_zigzag(pivots, noise=0.02, timeframe=Timeframe.D1, seed=3)


def build_structure_ohlcv() -> pd.DataFrame:
    """Direnç/destek trendlineları, iç içe konsolidasyon kutuları, direnç/
    destek bölgeleri, hacim profili ve MACD için zengin bir sentetik seri
    (59 bar). El ile inşa edilmiştir (make_zigzag'in otomatik ara-değer
    üretimi yeterince kontrollü dokunuşlar vermediği için)."""
    closes: list[float] = []
    closes += list(np.linspace(100, 130, 8))
    closes += list(np.linspace(130, 112, 6))[1:]
    closes += list(np.linspace(112, 129, 6))[1:]
    closes += list(np.linspace(129, 110, 6))[1:]
    closes += list(np.linspace(110, 128, 6))[1:]
    closes += list(np.linspace(128, 118, 6))[1:]
    closes += [119, 120, 119.5, 120.5, 119, 120, 119.5, 120.2, 119.3, 120.1, 119.6, 120.3]
    closes += list(np.linspace(120, 145, 10))[1:]
    closes += [145] * 5

    close = np.array(closes)
    n = len(close)
    index = pd.date_range("2024-01-02", periods=n, freq="1D", tz="Europe/Istanbul")
    open_ = np.empty_like(close)
    open_[0] = close[0]
    open_[1:] = close[:-1]
    high = np.maximum(open_, close) + 0.3
    low = np.minimum(open_, close) - 0.3
    volume = np.full(n, 5000.0)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume}, index=index
    )


def build_registry_smoke_ohlcv() -> pd.DataFrame:
    """Registry kaydı için: kısa bir zigzag "kafa" + uzun, MONOTON (dönüşsüz)
    bir "kuyruk". Kuyrukta yeni pivot/aday OLUŞMAZ (find_pivots katı > şartı
    monoton seride tetiklenmez), böylece varsayılan `repaint_test` penceresi
    (son 60 bar) tamamen "artık hiçbir şeyin yeni doğmadığı" bir bölgeye
    denk gelir — SwingFibABCD için registry.register()'ın gerektirdiği
    varsayılan parametrelerle temiz bir repaint_test PASS'ı sağlar."""
    closes = list(np.linspace(100, 130, 10))
    closes += list(np.linspace(130, 110, 10))[1:]
    closes += list(np.linspace(110, 125, 10))[1:]
    closes += list(np.linspace(125, 300, 110))[1:]
    close = np.array(closes)
    n = len(close)
    index = pd.date_range("2024-01-02", periods=n, freq="1D", tz="Europe/Istanbul")
    open_ = np.empty_like(close)
    open_[0] = close[0]
    open_[1:] = close[:-1]
    high = np.maximum(open_, close) + 0.3
    low = np.minimum(open_, close) - 0.3
    volume = np.full(n, 5000.0)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume}, index=index
    )
