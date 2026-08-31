"""MASystems — çoklu periyotlu hareketli ortalama sistemi: kesişimler,
sıralama (stack) durumu, bant genişliği sıkışma/genişleme.

Periyotlar `mas_type`'a göre (ema/sma/kama/hull — hepsi `tlab/features/ma.py`)
hesaplanır, ardışık her (hızlı,yavaş) çifti için kesişim taranır. "Sıralama
durumu" (`stack_state`) her barda close + tüm MA'ların göreli konumuna göre
`bull_stack` (close > en hızlı > ... > en yavaş), `bear_stack` (ters sıra)
veya `mixed` olarak sınıflanır — klasik "MA ribbon" okuması. Bant genişliği
= (en yüksek MA - en düşük MA) / close; kendi `squeeze_window`'luk rolling
`squeeze_quantile`'ının ALTINA düştüğünde "sıkışma" (`is_squeeze`), bu
durumdan ÇIKIŞ (bandın yeniden genişlemesi) `squeeze_expansion` sinyalini
üretir. Tüm hesaplar yalnızca `rolling()`/`ewm()`/pozitif `shift()` kullanır
(non-repaint) — aday havuzu/zamanlama sorunu YOK.

**Kayıt istisnası** (bkz. `tlab/indicators/bootstrap.py` docstring'i):
her MA'nın TAM (büyüyen) serisi tek bir `Line` overlay'i olarak taşınır
(`weekly_channel.py`'nin `channel_current`'ıyla AYNI desen) — bu, generic
`repaint_test`'in `(points, label)` tam-eşitlik karşılaştırmasını YANLIŞ
ALARM olarak tetikler (gerçek bir repaint DEĞİL, yalnızca "aynı overlay her
barda bir nokta daha uzun"). `register_verified_elsewhere` kullanılır;
sinyallerin (kesişim/stack/squeeze) gerçek non-repaint'liği `tests/
test_trend/test_ma_systems.py`'de hedefli testlerle doğrulanır."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from tlab.core.indicator import BaseIndicator
from tlab.core.params import BaseParams, params_hash
from tlab.core.types import Direction, IndicatorMeta, IndicatorResult, Line, Signal, Timeframe
from tlab.features.ma import crossovers, ema, hull, kama, sma

MAType = Literal["ema", "sma", "kama", "hull"]
StackState = Literal["bull_stack", "bear_stack", "mixed"]


@dataclass(frozen=True)
class MASystemsParams(BaseParams):
    periods: tuple[int, ...] = (8, 21, 55, 200)
    ma_type: MAType = "ema"
    kama_er_window: int = 10
    kama_fast: int = 2
    kama_slow: int = 30
    squeeze_window: int = 100
    squeeze_quantile: float = 0.2


def _ma_series(close: pd.Series, period: int, p: MASystemsParams) -> pd.Series:
    if p.ma_type == "ema":
        return ema(close, period)
    if p.ma_type == "sma":
        return sma(close, period)
    if p.ma_type == "kama":
        return kama(close, er_window=p.kama_er_window, fast=p.kama_fast, slow=p.kama_slow)
    return hull(close, period)


def _stack_state(close: float, ma_vals_fast_to_slow: list[float]) -> StackState:
    values = [close, *ma_vals_fast_to_slow]
    pairs = list(zip(values, values[1:], strict=False))
    if all(a > b for a, b in pairs):
        return "bull_stack"
    if all(a < b for a, b in pairs):
        return "bear_stack"
    return "mixed"


class MASystems(BaseIndicator):
    """Çoklu MA sistemi — kesişim, ribbon-sıralama ve bant sıkışma/genişleme."""

    meta = IndicatorMeta(
        name="trend.ma_systems",
        version="0.1.0",
        category="trend",
        description="Çoklu hareketli ortalama: kesişim, sıralama durumu, bant sıkışma/genişleme.",
        supported_timeframes=(Timeframe.H4, Timeframe.D1),
    )

    def __init__(self, params: MASystemsParams | None = None) -> None:
        self.params: MASystemsParams = params or MASystemsParams()

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        p = self.params
        close = df["close"].astype(float)
        periods = sorted(p.periods)
        mas = {period: _ma_series(close, period, p) for period in periods}

        stacked = pd.concat(mas.values(), axis=1)
        band_width = (stacked.max(axis=1) - stacked.min(axis=1)) / close
        squeeze_threshold = band_width.rolling(
            p.squeeze_window, min_periods=p.squeeze_window
        ).quantile(p.squeeze_quantile)
        is_squeeze = band_width <= squeeze_threshold

        n = len(df)
        stack_states: list[StackState | None] = [None] * n
        for t in range(n):
            row = [mas[period].iloc[t] for period in periods]
            if any(pd.isna(v) for v in row) or pd.isna(close.iloc[t]):
                continue
            stack_states[t] = _stack_state(float(close.iloc[t]), row)

        signals: list[Signal] = []
        lines: list[Line] = []
        for period in periods:
            series = mas[period]
            points = tuple(
                (idx, float(v)) for idx, v in series.items() if not pd.isna(v)
            )
            if points:
                lines.append(
                    Line(points=points, label=f"{p.ma_type.upper()}{period}", style=f"ma_{period}")
                )

        n_pairs = max(1, len(periods) - 1)
        for i in range(len(periods) - 1):
            fast_period, slow_period = periods[i], periods[i + 1]
            cross = crossovers(mas[fast_period], mas[slow_period])
            importance = 0.4 + 0.6 * (i / (n_pairs - 1) if n_pairs > 1 else 1.0)
            for t in range(n):
                direction_str = cross.iloc[t]
                if pd.isna(direction_str):
                    continue
                event = f"ma_cross_{fast_period}_{slow_period}_" + (
                    "bull" if direction_str == "up" else "bear"
                )
                direction: Direction = "long" if direction_str == "up" else "short"
                signals.append(
                    Signal(
                        bar_time=df.index[t], detected_at=df.index[t], direction=direction,
                        state="confirmed", score=importance,
                        payload={"event": event, "fast": fast_period, "slow": slow_period},
                    )
                )

        for t in range(1, n):
            prev_state, now_state = stack_states[t - 1], stack_states[t]
            if now_state is None or now_state == prev_state:
                continue
            direction2: Direction
            if now_state == "bull_stack":
                event, direction2 = "bull_stack_entry", "long"
            elif now_state == "bear_stack":
                event, direction2 = "bear_stack_entry", "short"
            else:
                continue
            signals.append(
                Signal(
                    bar_time=df.index[t], detected_at=df.index[t], direction=direction2,
                    state="confirmed", score=0.6,
                    payload={"event": event, "stack_state": now_state},
                )
            )

        for t in range(1, n):
            prev_sq, now_sq = is_squeeze.iloc[t - 1], is_squeeze.iloc[t]
            if pd.isna(prev_sq) or pd.isna(now_sq):
                continue
            if bool(prev_sq) and not bool(now_sq):
                roc = close.iloc[t] / close.iloc[max(0, t - 5)] - 1.0
                direction3: Direction = "long" if roc >= 0 else "short"
                signals.append(
                    Signal(
                        bar_time=df.index[t], detected_at=df.index[t], direction=direction3,
                        state="confirmed", score=0.5,
                        payload={
                            "event": "squeeze_expansion",
                            "band_width": float(band_width.iloc[t]),
                        },
                    )
                )

        series_out = {"band_width": band_width, "squeeze_threshold": squeeze_threshold}

        last_state = {
            "stack_state": stack_states[-1],
            "is_squeeze": bool(is_squeeze.iloc[-1]) if not pd.isna(is_squeeze.iloc[-1]) else None,
            "band_width": float(band_width.iloc[-1]) if not pd.isna(band_width.iloc[-1]) else None,
            "ma_values": {
                str(period): (
                    None if pd.isna(mas[period].iloc[-1]) else float(mas[period].iloc[-1])
                )
                for period in periods
            },
        }

        return IndicatorResult(
            indicator=self.meta.name, version=self.meta.version,
            params_hash=params_hash(p), symbol="", timeframe=Timeframe.D1,
            signals=signals, lines=lines, series=series_out,
            series_layout={"bant_genisligi": ["band_width", "squeeze_threshold"]},
            last_state=last_state,
        )
