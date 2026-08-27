"""tlab.indicators.harmonics.geometry için birim testleri."""

from __future__ import annotations

from zoneinfo import ZoneInfo

import pandas as pd

from tlab.features.swings import Pivot
from tlab.indicators.harmonics.geometry import generate_candidates

TZ = ZoneInfo("Europe/Istanbul")


def _zigzag_df_and_pivots() -> tuple[pd.DataFrame, list[Pivot]]:
    """0(low)->X(low,100)->A(high,120)->B(low,107.64)->C(high,116.64) zigzag'i.

    (0 noktası shark/five_zero testleri için eklendi.) Her bacak arasında
    doğrusal ilerleyen basit bir seri; bar_idx'ler pivot listesine elle verildiği
    için OHLCV'nin kendisi yalnızca finalized_idx'in df sınırları içinde
    kalması için yeterli uzunlukta olmalı.
    """
    n = 30
    idx = pd.date_range("2024-01-02 00:00", periods=n, freq="4h", tz=TZ)
    close = [100.0] * n
    df = pd.DataFrame(
        {"open": close, "high": [c + 0.5 for c in close], "low": [c - 0.5 for c in close],
         "close": close, "volume": [1000.0] * n},
        index=idx,
    )

    zero = Pivot(0, idx[0], 90.0, "low", 1, idx[1], finalized_idx=5, finalized_time=idx[5])
    x = Pivot(5, idx[5], 100.0, "low", 6, idx[6], finalized_idx=10, finalized_time=idx[10])
    a = Pivot(10, idx[10], 120.0, "high", 11, idx[11], finalized_idx=15, finalized_time=idx[15])
    b = Pivot(15, idx[15], 107.64, "low", 16, idx[16], finalized_idx=20, finalized_time=idx[20])
    c = Pivot(20, idx[20], 116.64, "high", 21, idx[21], finalized_idx=25, finalized_time=idx[25])
    return df, [zero, x, a, b, c]


def test_generate_candidates_computes_correct_ratios() -> None:
    df, zigzag = _zigzag_df_and_pivots()
    candidates = generate_candidates(df, zigzag)

    # zigzag uzunluğu 5 -> tam olarak iki 4'lü pencere: (zero,x,a,b) ve (x,a,b,c)
    assert len(candidates) == 2

    cand = candidates[-1]  # (x,a,b,c) penceresi
    assert cand.x.price == 100.0 and cand.a.price == 120.0
    assert cand.b.price == 107.64 and cand.c.price == 116.64
    assert abs(cand.ab_xa - 0.618) < 1e-9
    assert cand.direction == "bullish"
    assert cand.zero is not None and cand.zero.price == 90.0
    assert cand.born_idx == 25 and cand.born_time == df.index[25]
    assert cand.c_beyond_a is False
    assert cand.b_beyond_x is False
    assert cand.bars_xa == 5 and cand.bars_ab == 5 and cand.bars_bc == 5


def test_generate_candidates_skips_when_c_not_finalized_within_df() -> None:
    df, zigzag = _zigzag_df_and_pivots()
    short_df = df.iloc[:22]  # (x,a,b,c) penceresinin c.finalized_idx=25 >= 22 -> üretilmez
    candidates = generate_candidates(short_df, zigzag)
    # yalnızca (zero,x,a,b) penceresi kalır (onun "c"si = b, finalized_idx=20 < 22)
    assert len(candidates) == 1
    assert candidates[0].c.price == 107.64


def test_generate_candidates_first_window_has_no_zero() -> None:
    df, zigzag = _zigzag_df_and_pivots()
    candidates = generate_candidates(df, zigzag)
    first = candidates[0]  # (zero,x,a,b) penceresi -> zero'dan ÖNCE başka pivot yok
    assert first.zero is None
