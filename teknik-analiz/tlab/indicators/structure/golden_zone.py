"""GoldenZoneIndicator — en güncel onaylı swing'in Fibonacci "altın bölge"
geri çekilme bandı (0.618-0.786) + izleme.

Zigzag `swings.alternate_pivots` (varsayılan `include_pending=False`) ile
elde edilir — bu yüzden zigzag'deki HER pivot ZATEN kesinleşmiştir
(`finalized_idx` hiçbir zaman None değildir), `structure.swing_fib_abcd`
ile AYNI mimari. Bu, `structure.price_structure`/`trend.breakouts`'un
aksine bu indikatörün generic `Registry.register()`'a (repaint_test'ten
geçerek) TEMİZ kaydolabileceği anlamına gelir — "aday havuzu" istisnasına
ihtiyaç YOK.

TASARIM KARARI (spec'in "A onay barında" ifadesi belirsizdi): "A" burada
harmonik jargondaki gibi EN GÜNCEL zigzag pivotunu ifade eder (bir önceki
pivot "X"); bant, A'nın kendi RAW pivot onayında (`confirmed_idx`) değil
`finalized_idx`'inde doğar — aksi halde A, daha sonra aynı türden daha
ekstrem bir pivotla İPTAL EDİLEBİLECEĞİ için (bkz. `alternate_pivots`
docstring'i) bant sınırları SONRADAN değişirdi (gerçek bir repaint). Bu
seçim, projenin `SwingFibABCD`'de zaten kullandığı `born_idx = c.finalized_idx`
deseniyle birebir tutarlıdır.

"Yeni swing onayı → eski bant end alır" kuralı: bir sonraki zigzag pivotu
finalize olduğunda ÖNCEKİ bandın Box/Level `end`'i o bara SABİTLENİR; en
güncel (henüz süperseded olmamış) bant `t1`/`end`'i `df.index[-1]`'e uzanır
(extend-only, her `compute()` çağrısında büyür).

FAZ 0.5 (A1) NOTU: pivot girişi artık `tlab/features/swings.py::
significant_pivots`'tan geliyor (`zigzag_method`/`atr_mult`/`min_swing_atr`
parametreleri buna bağlanır) — bu modülün ÖNCEDEN kendi içinde uyguladığı
swing-büyüklüğü filtresi (`swing_range < min_swing_atr * ATR`) artık
`significant_pivots(method="fixed", min_swing_atr=...)`'in İÇİNDE yaşıyor
(tekrar yok); varsayılan `zigzag_method="atr"` iken bu filtre YOK SAYILIR,
`atr_mult` zaten aynı işi görür.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from tlab.core.indicator import BaseIndicator
from tlab.core.params import BaseParams, params_hash
from tlab.core.types import (
    Box,
    Direction,
    IndicatorMeta,
    IndicatorResult,
    Level,
    Line,
    Marker,
    Signal,
    Timeframe,
)
from tlab.features.fibonacci import retracement
from tlab.features.swings import ZigzagMethod, label_structure, significant_pivots
from tlab.features.volatility import atr
from tlab.features.zones_sd import golden_zone


@dataclass(frozen=True)
class GoldenZoneParams(BaseParams):
    left: int = 3
    right: int = 3
    band: tuple[float, float] = (0.618, 0.786)
    alt_band: tuple[float, float] | None = (0.5, 0.618)
    reaction_body_ratio: float = 0.5
    min_swing_atr: float = 3.0
    atr_period: int = 14
    # Faz 0.5, A1: ortak pivot girişi (tlab/features/swings.py::significant_
    # pivots) -- bu modül A1 denetiminde "doğru davranan tek modül" olarak
    # işaretlenmişti (kendi min_swing_atr filtresini ZATEN uyguluyordu); o
    # filtre artık significant_pivots(method="fixed", min_swing_atr=...)
    # içine TAŞINDI (tekrar yok). Sistem-geneli varsayılan zigzag_method="atr"
    # olduğunda min_swing_atr YOK SAYILIR (atr_mult zaten aynı işi görür) --
    # min_swing_atr yalnızca zigzag_method="fixed" iken devrede.
    zigzag_method: ZigzagMethod = "atr"
    atr_mult: float = 3.0


class GoldenZoneIndicator(BaseIndicator):
    """En güncel onaylı swing'in altın bölge bandı + dokunuş/reaksiyon/
    başarısızlık/başarı izlemesi."""

    meta = IndicatorMeta(
        name="structure.golden_zone",
        version="0.1.0",
        category="structure",
        description="Fibonacci altın bölge (0.618-0.786) geri çekilme bandı ve izlemesi.",
        supported_timeframes=(Timeframe.D1, Timeframe.H4),
    )

    def __init__(self, params: GoldenZoneParams | None = None) -> None:
        self.params: GoldenZoneParams = params or GoldenZoneParams()

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        p = self.params
        zigzag = label_structure(
            significant_pivots(
                df, method=p.zigzag_method, left=p.left, right=p.right,
                atr_mult=p.atr_mult, atr_period=p.atr_period, min_swing_atr=p.min_swing_atr,
            )
        )
        atr_series = atr(df, p.atr_period)
        n = len(df)
        low = df["low"].to_numpy()
        high = df["high"].to_numpy()
        close = df["close"].to_numpy()
        open_ = df["open"].to_numpy()

        signals: list[Signal] = []
        levels: list[Level] = []
        boxes: list[Box] = []
        lines: list[Line] = []
        markers: list[Marker] = []
        last_state: dict = {
            "band_low": None, "band_high": None, "in_band": False,
            "distance_atr": None, "last_reaction_at": None,
        }

        for i in range(1, len(zigzag)):
            x_pivot, a_pivot = zigzag[i - 1], zigzag[i]

            lines.append(
                Line(
                    points=((x_pivot.bar_time, x_pivot.price), (a_pivot.bar_time, a_pivot.price)),
                    label=f"swing_{i}", style="swing",
                )
            )

            born = a_pivot.finalized_idx
            if born is None or born >= n:
                continue

            next_finalized = None
            if i + 1 < len(zigzag) and zigzag[i + 1].finalized_idx is not None:
                candidate = zigzag[i + 1].finalized_idx
                if candidate is not None and candidate < n:
                    next_finalized = candidate
            is_open = next_finalized is None
            scan_end = next_finalized if next_finalized is not None else n
            edge_time = df.index[next_finalized] if next_finalized is not None else df.index[-1]

            # swing-büyüklüğü/min_swing_atr filtresi artık `significant_
            # pivots`'un içinde (zigzag_method="fixed" iken) — burada TEKRAR
            # uygulanmıyor.
            is_uptrend = x_pivot.kind == "low"
            direction: Direction = "long" if is_uptrend else "short"

            lo_price, hi_price = golden_zone(
                x_pivot.price, a_pivot.price, lo=p.band[0], hi=p.band[1]
            )
            boxes.append(
                Box(
                    t0=a_pivot.bar_time, t1=edge_time, low=lo_price, high=hi_price,
                    label=f"GOLDEN ZONE {p.band[0]}={hi_price:.2f} / {p.band[1]}={lo_price:.2f}",
                    style="golden_zone",
                )
            )
            half_price = retracement(x_pivot.price, a_pivot.price, (0.5,))[0.5]
            levels.append(
                Level(
                    price=half_price, label="fib_0.5", style="fib_retracement",
                    start=a_pivot.bar_time, end=(edge_time if not is_open else None),
                )
            )
            if p.alt_band is not None:
                alt_lo, alt_hi = golden_zone(
                    x_pivot.price, a_pivot.price, lo=p.alt_band[0], hi=p.alt_band[1]
                )
                boxes.append(
                    Box(
                        t0=a_pivot.bar_time, t1=edge_time, low=alt_lo, high=alt_hi,
                        label=f"ALT BÖLGE {p.alt_band[0]}-{p.alt_band[1]}",
                        style="golden_zone_alt",
                    )
                )

            touched = False
            reaction_bar: int | None = None
            done = False

            for t in range(born, scan_end):
                if done:
                    break
                fail_cond = close[t] < lo_price if is_uptrend else close[t] > hi_price
                success_cond = close[t] > a_pivot.price if is_uptrend else close[t] < a_pivot.price

                if not touched:
                    in_band = low[t] <= hi_price and high[t] >= lo_price
                    if in_band:
                        touched = True
                        signals.append(
                            Signal(
                                bar_time=df.index[t], detected_at=df.index[t], direction=direction,
                                state="active", score=0.6,
                                payload={"event": "golden_zone_touch", "swing_id": i},
                            )
                        )

                if touched and reaction_bar is None and not fail_cond and not success_cond:
                    bar_range = high[t] - low[t]
                    body_ratio = abs(close[t] - open_[t]) / bar_range if bar_range > 0 else 0.0
                    favorable_close = close[t] > hi_price if is_uptrend else close[t] < lo_price
                    favorable_body = (close[t] > open_[t]) if is_uptrend else (close[t] < open_[t])
                    if favorable_close and favorable_body and body_ratio >= p.reaction_body_ratio:
                        reaction_bar = t
                        signals.append(
                            Signal(
                                bar_time=df.index[t], detected_at=df.index[t], direction=direction,
                                state="confirmed", score=0.8,
                                payload={"event": "golden_zone_reaction", "swing_id": i},
                            )
                        )
                        markers.append(
                            Marker(df.index[t], close[t], "REAKSİYON", "golden_zone_reaction")
                        )

                if fail_cond:
                    signals.append(
                        Signal(
                            bar_time=df.index[t], detected_at=df.index[t],
                            direction=("short" if is_uptrend else "long"), state="invalidated",
                            score=0.5, payload={"event": "golden_zone_fail", "swing_id": i},
                        )
                    )
                    markers.append(Marker(df.index[t], close[t], "BAŞARISIZ", "golden_zone_fail"))
                    done = True
                elif success_cond:
                    signals.append(
                        Signal(
                            bar_time=df.index[t], detected_at=df.index[t], direction=direction,
                            state="completed", score=1.0,
                            payload={"event": "golden_zone_success", "swing_id": i},
                        )
                    )
                    markers.append(Marker(df.index[t], close[t], "BAŞARILI", "golden_zone_success"))
                    done = True

            if is_open:
                last_price = close[-1]
                distance_atr = 0.0
                last_atr = atr_series.iloc[-1]
                if not pd.isna(last_atr) and last_atr > 0:
                    if last_price > hi_price:
                        distance_atr = (last_price - hi_price) / last_atr
                    elif last_price < lo_price:
                        distance_atr = (lo_price - last_price) / last_atr
                last_state = {
                    "band_low": lo_price, "band_high": hi_price,
                    "in_band": lo_price <= last_price <= hi_price,
                    "distance_atr": distance_atr,
                    "last_reaction_at": (
                        df.index[reaction_bar].isoformat() if reaction_bar is not None else None
                    ),
                }

        return IndicatorResult(
            indicator=self.meta.name, version=self.meta.version, params_hash=params_hash(p),
            symbol="", timeframe=Timeframe.D1,
            signals=signals, levels=levels, lines=lines, boxes=boxes, markers=markers,
            last_state=last_state,
        )
