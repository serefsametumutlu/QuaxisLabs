"""tlab.indicators.harmonics.state için birim testleri (durum makinesi)."""

from __future__ import annotations

from zoneinfo import ZoneInfo

import pandas as pd

from tests.test_harmonics.fixtures import make_candidate
from tlab.indicators.harmonics.prz import PRZ
from tlab.indicators.harmonics.state import TrackingConfig, track_pattern

TZ = ZoneInfo("Europe/Istanbul")


def _df(n: int = 25) -> pd.DataFrame:
    idx = pd.date_range("2024-01-02 00:00", periods=n, freq="4h", tz=TZ)
    # Varsayılan: fiyat 200 civarında, PRZ'den (100-102) uzak — testler
    # ilgili barlarda high/low'u elle üzerine yazar.
    close = [200.0] * n
    df = pd.DataFrame(
        {"open": close, "high": [c + 1.0 for c in close], "low": [c - 1.0 for c in close],
         "close": close, "volume": [1000.0] * n},
        index=idx,
    )
    return df


def _cfg(**overrides) -> TrackingConfig:
    defaults = dict(
        pattern_name="test", confirmation_policy="close_reversal", reversal_bars=1,
        require_extra_bar_on_warning=False, invalidation_price=None, time_window=None,
        xb_line=None, extra_confirmation_fn=None, score=0.8,
    )
    defaults.update(overrides)
    return TrackingConfig(**defaults)


def _bullish_candidate_and_prz(born_idx: int = 10) -> tuple:
    cand = make_candidate(100.0, 120.0, 107.64, 116.64)
    born_time = pd.Timestamp("2024-01-04 08:00", tz=TZ)
    cand = cand.__class__(**{**cand.__dict__, "born_idx": born_idx, "born_time": born_time})
    prz = PRZ(low=100.0, high=102.0, center=101.0, components={}, method="single_pm_tol")
    return cand, prz


def test_pending_to_active_to_confirmed_close_reversal() -> None:
    df = _df()
    cand, prz = _bullish_candidate_and_prz(born_idx=10)
    df.loc[df.index[13], ["high", "low", "close"]] = [102.5, 99.5, 101.0]  # PRZ'ye temas
    df.loc[df.index[14], ["high", "low", "close"]] = [103.5, 102.5, 103.0]  # kapanış PRZ üstünde

    cfg = _cfg()
    signals = track_pattern(df, cand, prz, cfg, pivots=[])

    states = [s.state for s in signals]
    assert states == ["pending", "active", "confirmed"]
    assert signals[0].detected_at == cand.born_time
    assert signals[1].detected_at == df.index[13]
    assert signals[1].payload["d_price"] == 99.5
    assert signals[2].detected_at == df.index[14]
    assert all(s.direction == "long" for s in signals)


def test_close_reversal_requires_n_consecutive_bars() -> None:
    df = _df()
    cand, prz = _bullish_candidate_and_prz(born_idx=10)
    df.loc[df.index[13], ["high", "low", "close"]] = [102.5, 99.5, 101.0]
    df.loc[df.index[14], ["high", "low", "close"]] = [103.5, 102.5, 103.0]  # 1. onay barı
    df.loc[df.index[15], ["high", "low", "close"]] = [102.0, 96.0, 97.0]  # streak sıfırlanır
    df.loc[df.index[16], ["high", "low", "close"]] = [103.5, 102.5, 103.0]
    df.loc[df.index[17], ["high", "low", "close"]] = [104.0, 103.0, 103.5]  # 2. ardışık onay

    cfg = _cfg(reversal_bars=2)
    signals = track_pattern(df, cand, prz, cfg, pivots=[])
    states = [s.state for s in signals]
    assert states == ["pending", "active", "confirmed"]
    assert signals[-1].detected_at == df.index[17]


def test_overshoot_invalidates_before_confirmation() -> None:
    df = _df()
    cand, prz = _bullish_candidate_and_prz(born_idx=10)
    df.loc[df.index[13], ["high", "low", "close"]] = [102.5, 99.5, 101.0]  # active
    df.loc[df.index[14], ["high", "low", "close"]] = [100.0, 90.0, 91.0]  # eşiğin altına

    cfg = _cfg(invalidation_price=95.0)
    signals = track_pattern(df, cand, prz, cfg, pivots=[])
    states = [s.state for s in signals]
    assert states == ["pending", "active", "invalidated"]
    assert signals[-1].payload["reason"] == "overshoot_after_active"


def test_require_extra_bar_on_warning_delays_confirmation() -> None:
    df = _df()
    cand, prz = _bullish_candidate_and_prz(born_idx=10)
    cand = cand.__class__(**{**cand.__dict__, "gap_after_c": True})
    df.loc[df.index[13], ["high", "low", "close"]] = [102.5, 99.5, 101.0]
    df.loc[df.index[14], ["high", "low", "close"]] = [103.5, 102.5, 103.0]  # tek başına yetmez
    df.loc[df.index[15], ["high", "low", "close"]] = [104.0, 103.0, 103.5]  # 2. ardışık -> onay

    cfg = _cfg(require_extra_bar_on_warning=True)
    signals = track_pattern(df, cand, prz, cfg, pivots=[])
    states = [s.state for s in signals]
    assert states == ["pending", "active", "confirmed"]
    assert signals[-1].detected_at == df.index[15]


def test_school_policy_uses_extra_confirmation_fn() -> None:
    df = _df()
    cand, prz = _bullish_candidate_and_prz(born_idx=10)
    df.loc[df.index[13], ["high", "low", "close"]] = [102.5, 99.5, 101.0]

    calls: list[int] = []

    def extra_fn(df_: pd.DataFrame, c, t: int) -> bool:
        calls.append(t)
        return t == 14

    df.loc[df.index[14], ["high", "low", "close"]] = [103.0, 101.0, 102.5]

    cfg = _cfg(confirmation_policy="school", extra_confirmation_fn=extra_fn)
    signals = track_pattern(df, cand, prz, cfg, pivots=[])
    states = [s.state for s in signals]
    assert states == ["pending", "active", "confirmed"]
    # confirmation kontrolü ACTIVE'in KENDİ barında değil, bir SONRAKİ bardan
    # itibaren çalışır (ACTIVE geçişi zaten o barın sonunda gerçekleşiyor).
    assert calls == [14]
    assert signals[-1].detected_at == df.index[14]


def test_time_window_defers_active_until_inside_window() -> None:
    df = _df()
    cand, prz = _bullish_candidate_and_prz(born_idx=10)
    # cand.c.bar_idx = 15 (fixtures.make_candidate ile: bar_gap=5 -> c_idx=15)
    # bar 13: bars_since_c negatif -> pencere dışı (henüz erken); bar 20: pencere içinde
    df.loc[df.index[13], ["high", "low", "close"]] = [102.5, 99.5, 101.0]
    df.loc[df.index[20], ["high", "low", "close"]] = [102.5, 99.5, 101.0]

    cfg = _cfg(time_window=(4, 6))
    signals = track_pattern(df, cand, prz, cfg, pivots=[])
    active_signals = [s for s in signals if s.state == "active"]
    assert len(active_signals) == 1
    assert active_signals[0].detected_at == df.index[20]


def test_time_window_expires_when_closed_without_touch() -> None:
    df = _df(n=25)
    cand, prz = _bullish_candidate_and_prz(born_idx=10)
    # PRZ'ye hiç dokunulmuyor (fiyat 200'de kalıyor); pencere c.bar_idx+3 barında kapanır.
    cfg = _cfg(time_window=(1, 3))
    signals = track_pattern(df, cand, prz, cfg, pivots=[])
    assert signals[-1].state == "expired"
