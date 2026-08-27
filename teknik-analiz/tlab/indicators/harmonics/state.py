"""Durum makinesi: PENDING -> ACTIVE -> CONFIRMED / INVALIDATED / EXPIRED.

Her geçiş kendi barında damgalanır (bar_time=detected_at=o bar), geriye
yazım yok. Bir pattern_id için üretilen TÜM geçmiş durumlar Signal listesi
olarak döner (repaint_test bunların hepsini detected_at<=cut_time ile
karşılaştırır). schools/base.py'ye bağımlılık YOK (döngüsel import'tan
kaçınmak için) — çağıran taraf (scanner_indicator.py) ekole özel her şeyi
(confirmation_policy, invalidation_price, time_window, extra_confirmation_fn,
xb_line) zaten hesaplanmış primitifler olarak verir.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import pandas as pd

from tlab.core.types import Direction, Signal
from tlab.features.swings import Pivot
from tlab.indicators.harmonics.geometry import Candidate
from tlab.indicators.harmonics.prz import PRZ

ConfirmationPolicy = Literal["close_reversal", "xb_break", "pivot", "school"]


@dataclass(frozen=True)
class TrackingConfig:
    pattern_name: str  # payload'a yazılır — aynı candidate birden fazla PatternSpec'e uyabilir
    confirmation_policy: ConfirmationPolicy
    reversal_bars: int
    require_extra_bar_on_warning: bool
    invalidation_price: float | None
    time_window: tuple[int, int] | None  # (min_bars, max_bars) c.bar_idx'ten itibaren
    xb_line: tuple[float, float] | None  # (slope, intercept), index-tabanlı
    extra_confirmation_fn: Callable[[pd.DataFrame, Candidate, int], bool] | None
    score: float


def _overlaps(direction: Direction, prz: PRZ, bar_high: float, bar_low: float) -> bool:
    return bar_high >= prz.low and bar_low <= prz.high


def _overshoot(
    direction: Direction, invalidation_price: float | None, bar_high: float, bar_low: float
) -> bool:
    if invalidation_price is None:
        return False
    if direction == "long":
        return bar_low < invalidation_price
    return bar_high > invalidation_price


def track_pattern(
    df: pd.DataFrame,
    candidate: Candidate,
    prz: PRZ,
    cfg: TrackingConfig,
    pivots: list[Pivot],
) -> list[Signal]:
    direction: Direction = "long" if candidate.direction == "bullish" else "short"
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    close = df["close"].to_numpy()
    n = len(df)

    signals: list[Signal] = []
    pending_signal = Signal(
        bar_time=candidate.born_time,
        detected_at=candidate.born_time,
        direction=direction,
        state="pending",
        score=cfg.score,
        payload={
            "pattern_id": candidate.pattern_id,
            "pattern_name": cfg.pattern_name,
            "prz_low": prz.low,
            "prz_high": prz.high,
            "prz_center": prz.center,
        },
    )
    signals.append(pending_signal)

    state: Literal["pending", "active", "confirmed", "invalidated", "expired"] = "pending"
    active_idx: int | None = None
    d_price: float | None = None
    reversal_streak = 0
    warning_bundle = candidate.gap_after_c or candidate.wide_bar_at_c
    effective_reversal_bars = cfg.reversal_bars + (
        1 if cfg.require_extra_bar_on_warning and warning_bundle else 0
    )

    for t in range(candidate.born_idx, n):
        if state in ("confirmed", "invalidated", "expired"):
            break

        bars_since_c = t - candidate.c.bar_idx

        if state == "pending":
            if cfg.time_window is not None and bars_since_c > cfg.time_window[1]:
                signals.append(
                    Signal(
                        bar_time=df.index[t], detected_at=df.index[t], direction=direction,
                        state="expired", score=cfg.score,
                        payload={
                            "pattern_id": candidate.pattern_id, "pattern_name": cfg.pattern_name,
                            "reason": "time_window_closed",
                        },
                    )
                )
                state = "expired"
                break

            if _overshoot(direction, cfg.invalidation_price, high[t], low[t]):
                signals.append(
                    Signal(
                        bar_time=df.index[t], detected_at=df.index[t], direction=direction,
                        state="invalidated", score=cfg.score,
                        payload={
                            "pattern_id": candidate.pattern_id, "pattern_name": cfg.pattern_name,
                            "reason": "overshoot_before_active",
                        },
                    )
                )
                state = "invalidated"
                break

            if _overlaps(direction, prz, high[t], low[t]):
                in_window = cfg.time_window is None or (
                    cfg.time_window[0] <= bars_since_c <= cfg.time_window[1]
                )
                if not in_window:
                    continue  # PENDING'de kal, "erken/geç temas" görmezden gelinir
                active_idx = t
                d_price = low[t] if direction == "long" else high[t]
                signals.append(
                    Signal(
                        bar_time=df.index[t], detected_at=df.index[t], direction=direction,
                        state="active", score=cfg.score,
                        payload={
                            "pattern_id": candidate.pattern_id, "pattern_name": cfg.pattern_name,
                            "d_price": d_price,
                        },
                    )
                )
                state = "active"
            continue

        # state == "active"
        if _overshoot(direction, cfg.invalidation_price, high[t], low[t]):
            signals.append(
                Signal(
                    bar_time=df.index[t], detected_at=df.index[t], direction=direction,
                    state="invalidated", score=cfg.score,
                    payload={
                        "pattern_id": candidate.pattern_id, "pattern_name": cfg.pattern_name,
                        "reason": "overshoot_after_active",
                    },
                )
            )
            state = "invalidated"
            break

        confirmed_now = False
        confirm_payload: dict = {
            "pattern_id": candidate.pattern_id, "pattern_name": cfg.pattern_name,
            "d_price": d_price,
        }

        if cfg.confirmation_policy == "close_reversal":
            beyond = close[t] > prz.high if direction == "long" else close[t] < prz.low
            reversal_streak = reversal_streak + 1 if beyond else 0
            if reversal_streak >= effective_reversal_bars:
                confirmed_now = True

        elif cfg.confirmation_policy == "xb_break":
            if cfg.xb_line is not None:
                slope, intercept = cfg.xb_line
                line_val = slope * t + intercept
                beyond = close[t] > line_val if direction == "long" else close[t] < line_val
                if beyond:
                    confirmed_now = True
                    confirm_payload["xb_break_at"] = str(df.index[t])

        elif cfg.confirmation_policy == "pivot":
            want_kind = "low" if direction == "long" else "high"
            match = next(
                (
                    p for p in pivots
                    if p.kind == want_kind and p.bar_idx == active_idx and p.confirmed_idx <= t
                ),
                None,
            )
            if match is not None:
                confirmed_now = True

        elif cfg.confirmation_policy == "school":
            if cfg.extra_confirmation_fn is None:
                confirmed_now = True
            else:
                confirmed_now = cfg.extra_confirmation_fn(df, candidate, t)

        if confirmed_now:
            signals.append(
                Signal(
                    bar_time=df.index[t], detected_at=df.index[t], direction=direction,
                    state="confirmed", score=cfg.score, payload=confirm_payload,
                )
            )
            state = "confirmed"

    return signals
