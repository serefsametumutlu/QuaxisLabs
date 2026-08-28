"""Faz 8A (`trend.breakouts`) testleri için paylaşılan sentetik OHLCV fixture'ları."""

from __future__ import annotations

import numpy as np
import pandas as pd

_TZ = "Europe/Istanbul"


def ohlcv_from_close(
    close: np.ndarray, wick: float = 0.05, volume: float | np.ndarray = 1000.0
) -> pd.DataFrame:
    n = len(close)
    index = pd.date_range("2024-01-02", periods=n, freq="1D", tz=_TZ)
    open_ = np.empty_like(close)
    open_[0] = close[0]
    open_[1:] = close[:-1]
    high = np.maximum(open_, close) + wick
    low = np.minimum(open_, close) - wick
    vol = np.full(n, volume) if np.isscalar(volume) else volume
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": vol}, index=index
    )


def build_noisy_uptrend(n: int = 400, seed: int = 3) -> pd.DataFrame:
    """Genel duman testi için: yeterince gürültülü ki pivot/trendline/zone/
    range/HH-LL/MA/Donchian/Bollinger/kanal kırılımlarının ÇOĞU en az bir
    kez tetiklensin."""
    rng = np.random.default_rng(seed)
    trend = 100.0 + 0.12 * np.arange(n)
    close = trend + rng.normal(0, 1.4, n)
    return ohlcv_from_close(close)


def build_donchian_lookahead_case(period: int = 5) -> pd.DataFrame:
    """İlk `period` bar sabit 100 (Donchian penceresi bunlarla dolar);
    `period`. barda (0-indeksli) ANİ bir sıçrama (200) — `.shift(1)`
    UYGULANMAZSA bu barın kendi high'ı KENDİ penceresine girer ve kırılımı
    (yanlışlıkla) BASTIRIR/geciktirir; doğru (shift(1)'li) davranışta bu
    barın kendisi tam olarak kırılım barıdır (kırılan seviye, SADECE önceki
    barlardan hesaplanmış olmalı)."""
    close = np.concatenate([np.full(period, 100.0), [200.0], np.full(30, 200.0)])
    return ohlcv_from_close(close, wick=0.01)


def build_confirm_bars_case() -> pd.DataFrame:
    """EMA50 kırılımını `confirm_bars=2` ile test etmek için: uzun düz bir
    taban (EMA'yı ~sabitler), sonra kapanışın EMA üzerine çıkıp bir bar
    İÇERİDE geri düşüp sonra tekrar üstte kalıcı olarak kapandığı bir seri —
    confirm_bars=1 ile İLK yukarı kapanışta tetiklenir, confirm_bars=2 ile
    yalnızca gerçekten 2 ardışık bar üstte kapananında tetiklenir."""
    base = np.full(120, 100.0)
    # EMA50 baz'a yakın ~100 iken: 1 bar üstte (101), 1 bar içeride (99.5),
    # sonra kalıcı olarak üstte (103, 104, ...).
    tail = np.array([101.0, 99.5, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0])
    close = np.concatenate([base, tail])
    return ohlcv_from_close(close, wick=0.01)


def build_false_break_case() -> pd.DataFrame:
    """Bir Donchian(5) kırılımı, hemen ardından (false_break_bars içinde)
    kapanışın seviyenin GERİSİNE dönmesi."""
    close = np.concatenate(
        [np.full(6, 100.0), [110.0], [95.0, 94.0], np.full(20, 96.0)]
    )
    return ohlcv_from_close(close, wick=0.01)


def build_retest_hold_case() -> pd.DataFrame:
    """Bir Donchian(5) kırılımı (seviye ≈ 100.01, önceki barların high'ı),
    ardından fiyatın KIRILAN SEVİYEYE geri YAKLAŞIP (low seviyenin biraz
    altına iner) kapanışın seviye ÜSTÜNDE kalması. `low` doğrudan seviyenin
    altına indiği için `tol_atr*ATR`'den (erken barlarda NaN/küçük olabilir)
    BAĞIMSIZ, sağlam bir test."""
    close = np.concatenate(
        [np.full(6, 100.0), [110.0], [101.0, 100.5, 105.0], np.full(20, 108.0)]
    )
    df = ohlcv_from_close(close, wick=0.01)
    # Retest barında (index 8) low'u kırılan seviyenin (≈100.01) ALTINA indir,
    # kapanış (100.5) seviyenin ÜSTÜNDE kalsın.
    df.iloc[8, df.columns.get_loc("low")] = 99.9
    return df
