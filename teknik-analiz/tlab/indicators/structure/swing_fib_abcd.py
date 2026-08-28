"""SwingFibABCD — swing yapısı, AB=CD projeksiyonu ve Fibonacci seviyeleri.

Harmonik motordan (Faz 3) farkı: burada X YOKTUR — bu, kitaptaki (bilgi-bankasi/
teknik/10/FORMASYON-01, AB=CD) 3 noktalı yapıyla birebir örtüşür: A, B, C üç
ardışık zigzag pivotu, D ise C'den itibaren projekte edilen bir fiyat hedefidir.

Durum makinesi harmonik motordan daha basittir (5 değil 3+1 durum):
- PENDING: C finalize olduğu bar, D hedefi(leri) hesaplanır ve damgalanır.
- ACTIVE ("yaklaşıyor"): fiyat D'ye kalan mesafenin near_pct'i içine girer.
- COMPLETED: fiyat D'ye target_tol_atr*ATR içinde ulaşır ("[TAMAM]").
- INVALIDATED: bir SONRAKİ (A,B,C) üçlüsü doğduğunda, hâlâ açık olan eski hedef.
  (Fiyatın hedefi AŞMASI ayrıca bir geçersizlik koşulu DEĞİLDİR — bu basitleştirilmiş
  indikatörde tek geçersizlik nedeni "yeni üçlünün doğması"dır; harmonik motordaki
  overshoot/max_overshoot mantığı burada YOK, kapsam dışı bırakıldı.)

Her (A,B,C) üçlüsü için `abcd_ratios`'taki HER oran (max_active_targets'a kadar)
ayrı bir D hedefi ve dolayısıyla ayrı bir sinyal zinciri üretir — `harmonic_unit`
(|A-B|) payload'a yazılır (başlıkta "Harmonik sayı: X TL" olarak gösterilecek).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from tlab.core.indicator import BaseIndicator
from tlab.core.params import BaseParams, params_hash
from tlab.core.types import (
    Direction,
    IndicatorMeta,
    IndicatorResult,
    Level,
    Line,
    Marker,
    Signal,
    Timeframe,
)
from tlab.features.fibonacci import extension as fib_extension
from tlab.features.fibonacci import projection_abcd, ratio, retracement, within
from tlab.features.swings import Pivot, alternate_pivots, atr_zigzag, find_pivots, label_structure
from tlab.features.volatility import atr

ZigzagMethod = Literal["fixed", "atr"]


@dataclass(frozen=True)
class SwingFibABCDParams(BaseParams):
    left: int = 3
    right: int = 3
    zigzag_method: ZigzagMethod = "fixed"
    atr_mult: float = 2.0
    atr_period: int = 14
    abcd_ratios: tuple[float, ...] = (1.0, 1.272, 1.618)
    bc_retrace: tuple[float, float] = (0.382, 0.886)
    target_tol_atr: float = 0.3
    fib_retracement_levels: tuple[float, ...] = (0.382, 0.5, 0.618, 0.786)
    fib_extension_levels: tuple[float, ...] = (1.272, 1.618)
    fib_touch_levels: tuple[float, ...] = (0.618, 0.786)
    max_active_targets: int = 3
    near_pct: float = 0.15


def _build_pivots(df: pd.DataFrame, params: SwingFibABCDParams) -> list[Pivot]:
    if params.zigzag_method == "atr":
        return atr_zigzag(df, params.atr_mult, params.atr_period)
    return find_pivots(df, params.left, params.right)


class SwingFibABCD(BaseIndicator):
    """Swing yapısı + AB=CD projeksiyonu + Fibonacci retracement/extension."""

    meta = IndicatorMeta(
        name="structure.swing_fib_abcd",
        version="0.1.0",
        category="structure",
        description="Swing yapısı (HH/HL/LH/LL), AB=CD hedef projeksiyonu ve Fibonacci seviyeleri.",
        supported_timeframes=(Timeframe.D1, Timeframe.H4),
    )

    def __init__(self, params: SwingFibABCDParams | None = None) -> None:
        self.params: SwingFibABCDParams = params or SwingFibABCDParams()

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        p = self.params
        raw_pivots = _build_pivots(df, p)
        zigzag = label_structure(alternate_pivots(raw_pivots))
        atr_series = atr(df, p.atr_period)

        lines, markers = _swing_lines_and_markers(zigzag)
        fib_levels = _fibonacci_levels(zigzag, p)
        signals, target_levels, fib_touch_signals = _abcd_targets(df, zigzag, atr_series, p)

        abcd_only = [s for s in signals if "triple_id" in s.payload]
        last_triple_id = abcd_only[-1].payload["triple_id"] if abcd_only else None
        by_ratio: dict[float, str] = {}
        for s in abcd_only:
            if s.payload["triple_id"] == last_triple_id:
                by_ratio[s.payload["ratio"]] = s.state
        active_targets = sum(
            1 for state in by_ratio.values() if state not in ("completed", "invalidated")
        )
        last_state: dict = {
            "swing_points": len(zigzag),
            "last_label": zigzag[-1].label if zigzag else None,
            "active_targets": active_targets,
        }

        return IndicatorResult(
            indicator=self.meta.name,
            version=self.meta.version,
            params_hash=params_hash(p),
            symbol="",
            timeframe=Timeframe.D1,
            signals=signals + fib_touch_signals,
            levels=target_levels + fib_levels,
            lines=lines,
            markers=markers,
            last_state=last_state,
        )


def _swing_lines_and_markers(zigzag: list[Pivot]) -> tuple[list[Line], list[Marker]]:
    lines: list[Line] = []
    markers: list[Marker] = []
    for i in range(1, len(zigzag)):
        p0, p1 = zigzag[i - 1], zigzag[i]
        lines.append(
            Line(
                points=((p0.bar_time, p0.price), (p1.bar_time, p1.price)),
                label=f"swing_{i}",
                style="swing",
            )
        )
    for p in zigzag:
        if p.label is None:
            continue
        markers.append(Marker(t=p.bar_time, price=p.price, text=p.label, kind="structure_label"))
    return lines, markers


def _fibonacci_levels(zigzag: list[Pivot], p: SwingFibABCDParams) -> list[Level]:
    """Her ardışık zigzag bacağı için ayrı bir Fibonacci seti — extend-only:
    en yeni bacak hariç hepsinin `end`'i bir SONRAKİ bacağın başlangıç barına
    sabitlenir (bkz. modül docstring'i); en yeni bacağın `end`'i None kalır."""
    levels: list[Level] = []
    for i in range(1, len(zigzag)):
        leg_start, leg_end = zigzag[i - 1], zigzag[i]
        is_last_leg = i == len(zigzag) - 1
        end_time = None if is_last_leg else zigzag[i + 1].bar_time
        ret = retracement(leg_start.price, leg_end.price, p.fib_retracement_levels)
        ext = fib_extension(leg_start.price, leg_end.price, p.fib_extension_levels)
        for lv, price in {**ret, **ext}.items():
            style = "fib_retracement" if lv in ret else "fib_extension"
            levels.append(
                Level(
                    price=price, label=f"fib_{lv}", style=style,
                    start=leg_end.bar_time, end=end_time,
                )
            )
    return levels


def _direction_for(a: Pivot) -> tuple[Direction, str]:
    """A'nın türüne göre yapı yönü: A düşükse (AB yukarı) bullish/yeşil, A
    yüksekse (AB aşağı) bearish/kırmızı."""
    if a.kind == "low":
        return "long", "bullish"
    return "short", "bearish"


def _abcd_targets(
    df: pd.DataFrame, zigzag: list[Pivot], atr_series: pd.Series, p: SwingFibABCDParams
) -> tuple[list[Signal], list[Level], list[Signal]]:
    n = len(df)
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()

    triples = [
        (zigzag[i], zigzag[i + 1], zigzag[i + 2])
        for i in range(len(zigzag) - 2)
        if within(ratio(zigzag[i].price, zigzag[i + 1].price, zigzag[i + 2].price), *p.bc_retrace)
    ]

    signals: list[Signal] = []
    levels: list[Level] = []

    for idx, (a, b, c) in enumerate(triples):
        born_idx = c.finalized_idx
        if born_idx is None or born_idx >= n:
            continue
        end_idx = (
            triples[idx + 1][2].finalized_idx
            if idx + 1 < len(triples) and triples[idx + 1][2].finalized_idx is not None
            else n
        )
        end_idx = min(end_idx, n) if end_idx is not None else n

        direction, style = _direction_for(a)
        harmonic_unit = abs(a.price - b.price)
        bc_ratio = ratio(a.price, b.price, c.price)
        mid = (p.bc_retrace[0] + p.bc_retrace[1]) / 2.0
        span = max(p.bc_retrace[1] - p.bc_retrace[0], 1e-9) / 2.0
        score = max(0.0, min(1.0, 1.0 - abs(bc_ratio - mid) / span))

        triple_id = f"abcd_{a.bar_idx}_{b.bar_idx}_{c.bar_idx}"
        targets = projection_abcd(a.price, b.price, c.price, p.abcd_ratios)

        for ratio_key in p.abcd_ratios[: p.max_active_targets]:
            d_price = targets[ratio_key]
            initial_distance = abs(d_price - c.price)
            levels.append(
                Level(
                    price=d_price, label=f"D (hedef): {d_price:.2f}",
                    style=style, start=c.bar_time,
                )
            )
            base_payload = {
                "triple_id": triple_id, "ratio": ratio_key, "target_price": d_price,
                "harmonic_unit": harmonic_unit,
            }
            signals.append(
                Signal(
                    bar_time=c.bar_time, detected_at=c.bar_time, direction=direction,
                    state="pending", score=score, payload=base_payload,
                )
            )

            state: Literal["pending", "active", "completed"] = "pending"
            for t in range(born_idx, end_idx):
                extreme = high[t] if direction == "long" else low[t]
                distance = abs(extreme - d_price)
                atr_t = atr_series.iloc[t]
                tol_price = p.target_tol_atr * atr_t if not pd.isna(atr_t) else 0.0

                if distance <= tol_price:
                    signals.append(
                        Signal(
                            bar_time=df.index[t], detected_at=df.index[t], direction=direction,
                            state="completed", score=score,
                            payload={**base_payload, "event": "abcd_target_reached"},
                        )
                    )
                    state = "completed"
                    break
                if state == "pending" and distance <= p.near_pct * initial_distance:
                    signals.append(
                        Signal(
                            bar_time=df.index[t], detected_at=df.index[t], direction=direction,
                            state="active", score=score,
                            payload={**base_payload, "event": "abcd_pending_near"},
                        )
                    )
                    state = "active"

            if state != "completed" and end_idx < n:
                signals.append(
                    Signal(
                        bar_time=df.index[end_idx], detected_at=df.index[end_idx],
                        direction=direction, state="invalidated", score=score,
                        payload={**base_payload, "reason": "superseded_by_new_triple"},
                    )
                )

    fib_touch_signals = _fib_touch_signals(df, zigzag, p)
    return signals, levels, fib_touch_signals


def _fib_touch_signals(
    df: pd.DataFrame, zigzag: list[Pivot], p: SwingFibABCDParams
) -> list[Signal]:
    """Her bacağın seçili Fibonacci seviyelerine İLK temas barı — bacağın
    kendisi zaten kesinleşmiş (start barından itibaren) olduğu için bu temas
    tespiti başka bir onay gerektirmez, anlık bilinir (non-repaint doğal)."""
    n = len(df)
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    signals: list[Signal] = []

    for i in range(1, len(zigzag)):
        leg_start, leg_end = zigzag[i - 1], zigzag[i]
        start_idx = leg_end.finalized_idx
        if start_idx is None or start_idx >= n:
            continue
        direction: Direction = "long" if leg_start.kind == "low" else "short"
        ret = retracement(leg_start.price, leg_end.price, p.fib_touch_levels)
        for lv, price in ret.items():
            for t in range(start_idx, n):
                if low[t] <= price <= high[t]:
                    signals.append(
                        Signal(
                            bar_time=df.index[t], detected_at=df.index[t], direction=direction,
                            state="completed", score=1.0,
                            payload={
                                "event": "fib_touch", "level": lv, "price": price,
                                "leg": f"{leg_start.bar_idx}_{leg_end.bar_idx}",
                            },
                        )
                    )
                    break
    return signals
