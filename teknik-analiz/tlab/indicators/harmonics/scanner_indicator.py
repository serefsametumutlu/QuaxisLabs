"""Harmonik formasyon tarayıcı indikatörü — 8 ekolün ortak sarmalayıcısı.

BİLİNEN SINIRLAMA (Line/Polygon repaint_test diffing, bkz. trendlines.py/
zones.py'deki aynı not): bir adayın Polygon/Line'ı ancak candidate.born_idx
(C kesinleştiği bar) barında doğar, ama repaint_test'in genel diffing'i
"var olma" kanıtı olarak points[0][0]'ı (ör. X'in bar_time'ı, C'den çok
daha ERKEN) kullanır. Bu GERÇEK bir repaint hatası değil — testlerde
cut_points yalnızca tüm adayların zaten doğduğu bardan itibaren seçilir
(bkz. tests/test_harmonics/). Signal nesneleri bu sorundan ETKİLENMEZ
(detected_at zaten doğru bar'ı taşır).

D noktası HENÜZ oluşmadan (PENDING) bile PRZ merkezi sabittir (yalnızca
X,A,B,C'den hesaplanır) — bu yüzden "D (hedef)" çizgisi/level'ı candidate
doğar doğmaz, gerçek D barı beklenmeden çizilebilir.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from tlab.core.indicator import BaseIndicator
from tlab.core.params import BaseParams, params_hash
from tlab.core.types import (
    IndicatorMeta,
    IndicatorResult,
    Level,
    Line,
    Marker,
    Polygon,
    Timeframe,
)
from tlab.features.fibonacci import retracement as fib_retracement
from tlab.features.swings import Pivot, alternate_pivots, atr_zigzag, find_pivots
from tlab.indicators.harmonics.geometry import generate_candidates
from tlab.indicators.harmonics.prz import project_ratio
from tlab.indicators.harmonics.schools.base import HarmonicSchool
from tlab.indicators.harmonics.schools.beck_navarro200 import Navarro200School
from tlab.indicators.harmonics.schools.carney import CarneySchool
from tlab.indicators.harmonics.schools.five_zero import FiveZeroSchool
from tlab.indicators.harmonics.schools.gilmore import GilmoreSchool
from tlab.indicators.harmonics.schools.kerkez_nenstar import NenStarSchool
from tlab.indicators.harmonics.schools.oglesbee_cypher import CypherSchool
from tlab.indicators.harmonics.schools.pesavento import PesaventoSchool
from tlab.indicators.harmonics.schools.three_drives import ThreeDrivesSchool
from tlab.indicators.harmonics.state import ConfirmationPolicy, TrackingConfig, track_pattern

ZigzagMethod = Literal["fixed", "atr"]

# 2026-08-30: kullanıcı geri bildirimi — harmonik grafiklerde "fibo çizgileri
# yok" ve "D noktası için olası hedef neresi" görülemiyordu. D'nin klasik
# tanımı ZATEN XA bacağının bir geri çekilmesidir (Gartley 0.786, Bat 0.886,
# Butterfly/Crab 0.618-1.0 vb.) — PRZ (`prz.py`) bunu ekol-özel oranlarla
# birden fazla bacağın KESİŞİMİ olarak hesaplıyor, ama görsel olarak TEK bir
# bant (PRZ Üst/Alt) dışında hangi standart oranın nereye denk geldiği hiç
# gösterilmiyordu. Bu ladder (`swing_fib_abcd.py::_fibonacci_levels` ile AYNI
# desen — zaten var olan `fibonacci.retracement()`'ın sarmalanması, YENİ bir
# hesap yöntemi DEĞİL) XA bacağının standart basamaklarını çizer; PRZ bandı
# tipik olarak bu basamaklardan biri/birkaçıyla çakışır, kullanıcı NEDEN o
# bantta olduğunu görebilir.
_XA_FIB_LEVELS: tuple[float, ...] = (0.382, 0.5, 0.618, 0.786)

# PRZ/fib Level'larının `end`i olmadan (None) `renderer.py::_draw_levels`
# bunları HER ZAMAN veri setinin GERÇEK son barına kadar çizerdi — bir aday
# eskiyse (ondan sonra yeni bir aday doğmadıysa) bu, etiketin (`renderer.py::
# _harmonic_auto_window_start`ın artık ADAYIN KENDİ ufkuna göre kısıtladığı,
# bkz. `_HARMONIC_END_PAD_BARS`) yakınlaştırılmış görünür pencerenin ÇOK
# DIŞINDA, görünmez bir noktada kalmasına yol açıyordu (kullanıcı geri
# bildirimiyle bulunan bir davranış: "fibo/PRZ değerleri desenin üzerinde
# olmalı, dokundukları noktada hiçbir şey yazmıyor"). Bu pay, renderer'daki
# `_HARMONIC_END_PAD_BARS` ile AYNI (iki katman birbirini import ETMEZ, ama
# görsel sonucun tutarlı olması için aynı ufku hedefler).
_LEVEL_END_PAD_BARS = 60

_SCHOOLS: dict[str, type[HarmonicSchool]] = {
    "carney": CarneySchool,
    "pesavento": PesaventoSchool,
    "gilmore": GilmoreSchool,
    "cypher": CypherSchool,
    "nenstar": NenStarSchool,
    "navarro200": Navarro200School,
    "five_zero": FiveZeroSchool,
    "three_drives": ThreeDrivesSchool,
}

_STATE_LABEL_TR = {
    "pending": "BEKLEMEDE",
    "active": "AKTİF",
    "confirmed": "TAMAMLANDI",
    "invalidated": "GEÇERSİZ",
    "expired": "SÜRESİ DOLDU",
}


@dataclass(frozen=True)
class HarmonicParams(BaseParams):
    left: int = 3
    right: int = 3
    zigzag_method: ZigzagMethod = "fixed"
    atr_mult: float = 2.0
    atr_period: int = 14
    confirmation_policy: ConfirmationPolicy = "close_reversal"
    reversal_bars: int = 1
    require_extra_bar_on_warning: bool = False
    lookback_bars: int | None = None
    allow_overlapping: bool = True


def _build_pivots(df: pd.DataFrame, params: HarmonicParams) -> list[Pivot]:
    if params.zigzag_method == "atr":
        return atr_zigzag(df, params.atr_mult, params.atr_period)
    return find_pivots(df, params.left, params.right)


class HarmonicIndicator(BaseIndicator):
    """Tek bir ekolü (school) tüm formasyonlarıyla tarayan indikatör."""

    def __init__(self, school: str, params: HarmonicParams | None = None) -> None:
        if school not in _SCHOOLS:
            raise ValueError(f"bilinmeyen ekol: {school} (beklenen: {sorted(_SCHOOLS)})")
        self._school_name = school
        self._school = _SCHOOLS[school]()
        self.params: HarmonicParams = params or HarmonicParams()
        self.meta = IndicatorMeta(  # type: ignore[misc]  # her ekol örneği kendi meta.name'ini taşır
            name=f"harmonic.{school}",
            version="0.1.0",
            category="harmonics",
            description=f"{school} ekolü — çoklu-ekol harmonik formasyon tarayıcı (Faz 3).",
            supported_timeframes=(Timeframe.D1, Timeframe.H4),
        )

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        n = len(df)
        raw_pivots = _build_pivots(df, self.params)
        zigzag = alternate_pivots(raw_pivots)
        candidates = generate_candidates(df, zigzag)

        if self.params.lookback_bars is not None:
            cutoff = n - self.params.lookback_bars
            candidates = [c for c in candidates if c.born_idx >= cutoff]

        signals = []
        levels: list[Level] = []
        lines: list[Line] = []
        polygons: list[Polygon] = []
        markers: list[Marker] = []
        last_state: dict[str, dict] = {}

        for candidate in candidates:
            horizon_time = df.index[min(n - 1, candidate.born_idx + _LEVEL_END_PAD_BARS)]
            for pmatch in self._school.match(candidate):
                spec, prz = pmatch.spec, pmatch.prz
                pid = f"{self._school_name}_{spec.name}_{candidate.pattern_id}"

                invalidation_price = (
                    project_ratio(candidate, spec.invalidation[0], spec.invalidation[1])
                    if spec.invalidation is not None
                    else None
                )
                time_window = self._school.time_window(candidate, spec)
                xb_line = None
                if self.params.confirmation_policy == "xb_break":
                    x, b = candidate.x, candidate.b
                    slope = (b.price - x.price) / (b.bar_idx - x.bar_idx)
                    xb_line = (slope, x.price - slope * x.bar_idx)

                cfg = TrackingConfig(
                    pattern_name=spec.name,
                    confirmation_policy=self.params.confirmation_policy,
                    reversal_bars=self.params.reversal_bars,
                    require_extra_bar_on_warning=self.params.require_extra_bar_on_warning,
                    invalidation_price=invalidation_price,
                    time_window=time_window,
                    xb_line=xb_line,
                    extra_confirmation_fn=(
                        self._school.extra_confirmation
                        if self.params.confirmation_policy == "school"
                        else None
                    ),
                    score=pmatch.score,
                    suggested_levels=self._school.suggested_levels(candidate, spec, prz),
                )
                pattern_signals = track_pattern(df, candidate, prz, cfg, raw_pivots)
                signals.extend(pattern_signals)

                x, a, b, c = candidate.x, candidate.a, candidate.b, candidate.c
                bearish = candidate.direction == "bearish"
                style = "bearish" if bearish else "bullish"

                polygons.append(
                    Polygon(
                        points=(
                            (x.bar_time, x.price), (a.bar_time, a.price), (b.bar_time, b.price),
                        ),
                        label=f"{pid}_xab", style=style,
                    )
                )
                polygons.append(
                    Polygon(
                        points=(
                            (b.bar_time, b.price), (c.bar_time, c.price),
                            (candidate.born_time, prz.center),
                        ),
                        label=f"{pid}_bcd", style=style,
                    )
                )
                lines.append(
                    Line(
                        points=((x.bar_time, x.price), (b.bar_time, b.price)),
                        label=f"{pid}_xb", style="dashed", extend_right=True,
                    )
                )
                lines.append(
                    Line(
                        points=((x.bar_time, x.price), (candidate.born_time, prz.center)),
                        label=f"{pid}_xd_envelope", style="dotted", extend_right=False,
                    )
                )
                levels.append(
                    Level(
                        price=prz.low, label=f"{pid}_prz_low", style="dotted",
                        start=candidate.born_time, end=horizon_time,
                    )
                )
                levels.append(
                    Level(
                        price=prz.high, label=f"{pid}_prz_high", style="dotted",
                        start=candidate.born_time, end=horizon_time,
                    )
                )
                for lv, price in fib_retracement(x.price, a.price, _XA_FIB_LEVELS).items():
                    levels.append(
                        Level(
                            price=price, label=f"{pid}_fib_{lv}", style="fib_retracement",
                            start=candidate.born_time, end=horizon_time,
                        )
                    )

                last_sig = pattern_signals[-1]
                state_label = _STATE_LABEL_TR[last_sig.state]
                d_price = last_sig.payload.get("d_price", prz.center)
                markers.append(
                    Marker(
                        t=last_sig.detected_at, price=d_price,
                        text=f"D: {d_price:.4f} [{state_label}]", kind=f"harmonic_{last_sig.state}",
                    )
                )

                last_state[pid] = {
                    "school": self._school_name, "pattern": spec.name,
                    "direction": last_sig.direction, "state": last_sig.state,
                    "score": pmatch.score,
                }

        return IndicatorResult(
            indicator=self.meta.name, version=self.meta.version,
            params_hash=params_hash(self.params), symbol="", timeframe=Timeframe.D1,
            signals=signals, levels=levels, lines=lines, polygons=polygons, markers=markers,
            last_state=last_state,
        )
