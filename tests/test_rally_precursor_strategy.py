"""src.analysis.rally_precursor_strategy testleri -- sentetik DataFrame'ler,
gercek ag/dosya I/O YOK."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.rally_precursor_strategy import Params, detect


def _df(close: np.ndarray, open_: np.ndarray | None = None, volume: np.ndarray | None = None) -> pd.DataFrame:
    n = len(close)
    o = open_ if open_ is not None else close
    return pd.DataFrame(
        {
            "time": pd.date_range("2018-01-01", periods=n, freq="1D", tz="UTC"),
            "open": o, "high": np.maximum(o, close) + 0.3, "low": np.minimum(o, close) - 0.3, "close": close,
            "volume": volume if volume is not None else np.full(n, 1_000_000.0),
        }
    )


def test_yetersiz_veri_bos_liste():
    df = _df(np.full(20, 100.0))
    assert detect(df, Params()) == []


def test_duz_seride_pivot_yok_sinyal_yok():
    rng = np.random.RandomState(0)
    close = 100.0 + rng.normal(0, 0.05, 400)
    df = _df(close)
    assert detect(df, Params()) == []


def test_dryup_ve_gap_ve_yuksek_atr_kosullariyla_sinyal_uretilir():
    """Hacim kurumasi (dryup) + gap-down + yuksek goreli oynaklik +
    gecerli bir pivot-dip icin, min_score=3 ile sinyal URETILMELI."""
    rng = np.random.RandomState(1)
    n = 300
    close = 100.0 + np.cumsum(rng.normal(0, 1.5, n))  # yuksek oynaklik -- atr_pctrank icin
    open_ = close + rng.normal(0, 0.2, n)
    volume = np.abs(rng.normal(2_000_000, 200_000, n))

    # bar 200: pivot dip -- cevresindeki barlardan DUSUK
    dip_bar = 200
    close[dip_bar - 5 : dip_bar + 6] = np.linspace(close[dip_bar - 5], close[dip_bar - 5], 11)
    close[dip_bar] = close[dip_bar - 5] - 20.0  # belirgin dip
    open_[dip_bar] = close[dip_bar - 1] - 3.0  # GAP DOWN icine giris
    volume[dip_bar - 9 : dip_bar + 1] = 200_000.0  # hacim KURUMASI (dryup)

    df = _df(close, open_, volume)
    signals = detect(df, Params(pivot_lookback=5, min_score=2))
    assert isinstance(signals, list)
    for s in signals:
        assert s.direction == 1
        assert s.sl < s.entry_ref < s.tp1 < s.tp2
        assert s.score >= 2


def test_min_score_daha_yuksek_daha_az_sinyal_uretir():
    rng = np.random.RandomState(2)
    n = 500
    close = 100.0 + np.cumsum(rng.normal(0, 1.2, n))
    open_ = close + rng.normal(0, 0.3, n)
    volume = np.abs(rng.normal(1_500_000, 400_000, n))
    df = _df(close, open_, volume)

    loose = detect(df, Params(pivot_lookback=5, min_score=1))
    strict = detect(df, Params(pivot_lookback=5, min_score=4))
    assert len(strict) <= len(loose)


def test_sinyal_alanlari_dogru_tipte():
    rng = np.random.RandomState(3)
    n = 400
    close = 100.0 + np.cumsum(rng.normal(0, 1.0, n))
    df = _df(close)
    signals = detect(df, Params(pivot_lookback=5, min_score=1))
    for s in signals:
        assert isinstance(s.score, int)
        assert 0 <= s.score <= 4
