"""coint_monitor.py: rolling Engle-Granger kointegrasyon çürüme izleyicisi
(Faz 2, 2C)."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import pytest

from tests.test_pairs.fixtures import build_cointegrated_pair
from tlab.indicators.pairs.coint_monitor import cointegration_broken, rolling_coint_pvalue


def test_rolling_coint_pvalue_nan_before_window() -> None:
    df_y, df_x = build_cointegrated_pair(n=200)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        p = rolling_coint_pvalue(df_y["close"], df_x["close"], window=90)
    assert p.iloc[:89].isna().all()
    assert not p.iloc[89:].isna().any()


def _noisy_cointegrated_series(n: int, seed: int = 5) -> tuple[pd.Series, pd.Series]:
    """`build_cointegrated_pair`'in aksine (deterministik sinüs şoku, kısa
    pencerelerde neredeyse tam ortak-doğrusallığa yol açabiliyor -- rolling
    testler için uygun değil) burada X bağımsız bir random walk, Y ise
    GÜRÜLTÜLÜ bir katı -- `tests/test_stats.py`'nin engle_granger testleriyle
    AYNI desen."""
    rng = np.random.default_rng(seed)
    x = np.cumsum(rng.normal(0, 1, n)) + 50
    y = 2.0 * x + rng.normal(0, 0.5, n)
    idx = pd.date_range("2024-01-01", periods=n, freq="D", tz="Europe/Istanbul")
    return pd.Series(y, index=idx), pd.Series(x, index=idx)


def test_rolling_coint_pvalue_low_for_genuinely_cointegrated_pair() -> None:
    """GERÇEK kointegre bir çiftin (Y = 2X + gürültü) her 90 barlık
    penceresinde de p düşük kalmalı."""
    y, x = _noisy_cointegrated_series(300)
    p = rolling_coint_pvalue(y, x, window=90)
    assert (p.dropna() < 0.05).all()


def test_cointegration_broken_true_after_structural_break() -> None:
    """İlk yarı GERÇEKTEN kointegre (ortak base), ikinci yarı Y'nin KENDİ
    BAĞIMSIZ rastgele yürüyüşüne geçmesiyle KOPUYOR (yapısal kırılma
    simülasyonu). Tek bir barın True/False'una GÜVENMEK yerine (Engle-
    Granger'ın 90-barlık pencerelerde her zaman %100 güçle reddetmediği,
    ampirik olarak ölçüldü) -- ÖNCESİ tamamen sessiz, SONRASI belirgin
    şekilde daha sık işaretlenmeli olmalı (istatistiksel bir testin
    beklenen davranışı, deterministik bir eşik değil)."""
    rng = np.random.default_rng(7)
    n = 300
    break_at = 150
    base = np.cumsum(rng.normal(0, 0.01, n))
    x_log = base.copy()
    y_log = base.copy()
    # break_at'ten SONRA Y, base'den KOPUP kendi bağımsız yürüyüşüne geçiyor.
    y_log[break_at:] = base[break_at] + np.cumsum(rng.normal(0, 0.03, n - break_at))
    idx = pd.date_range("2024-01-01", periods=n, freq="D", tz="Europe/Istanbul")
    y = pd.Series(100 * np.exp(y_log), index=idx)
    x = pd.Series(50 * np.exp(x_log), index=idx)

    window = 90
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        broken = cointegration_broken(y, x, window=window, p_threshold=0.10)
    # Penceresi TAMAMEN kırılma-öncesi veriyle dolu barlar: HİÇ işaretlenmemeli.
    pre_break_fraction = broken.iloc[window - 1 : break_at].mean()
    # Penceresi TAMAMEN kırılma-sonrası veriyle dolu barlar (t >= break_at+window):
    post_break_fraction = broken.iloc[break_at + window :].mean()
    assert pre_break_fraction == 0.0
    assert post_break_fraction > pre_break_fraction
    assert post_break_fraction > 0.15  # ampirik olarak ~%21 ölçüldü


def test_cointegration_broken_all_false_when_no_break() -> None:
    y, x = _noisy_cointegrated_series(300)
    broken = cointegration_broken(y, x, window=90, p_threshold=0.10)
    assert not broken.any()


def test_cointegration_broken_false_during_nan_warmup() -> None:
    df_y, df_x = build_cointegrated_pair(n=200)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        broken = cointegration_broken(df_y["close"], df_x["close"], window=90)
    assert not broken.iloc[:89].any()


def test_rolling_coint_pvalue_non_repaint_prefix_consistent() -> None:
    """`t`'deki değer yalnızca `[0,t]`'e bakar -- kesik bir serinin son
    değeri, tam serinin AYNI bardaki değeriyle BİREBİR eşleşmeli."""
    df_y, df_x = build_cointegrated_pair(n=200)
    y, x = df_y["close"], df_x["close"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        full = rolling_coint_pvalue(y, x, window=90)
        cut = 150
        partial = rolling_coint_pvalue(y.iloc[:cut], x.iloc[:cut], window=90)
    assert partial.iloc[-1] == pytest.approx(full.iloc[cut - 1])
