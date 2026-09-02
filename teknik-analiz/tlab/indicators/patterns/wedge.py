"""Takoz (wedge) ve üçgen (triangle) formasyon tarayıcı — Faz 8B.

`tlab/features/patterns_geom.py::converging_lines`/`classify`'ın SAF
geometrisini, `tlab/features/trendlines.py::build_trendlines`'ın ürettiği
resistance/support çizgi ADAY HAVUZUYLA birleştirir: her (upper, lower) çift
denenir, `classify()` 5 (kanal/flag/pennant hariç) türden birini
döndürüyorsa aday olur. Bu, `structure.price_structure`/`trend.breakouts`
ile AYNI "aday havuzu" mimarisidir (bkz. o modüllerin docstring'i) — hangi
trendline'ların `build_trendlines`'ın `max_lines` kesmesinden geçtiği df
büyüdükçe değişebilir, bu yüzden bu indikatör generic `Registry.register()`'a
DEĞİL `register_verified_elsewhere()`'e kaydolur (bkz. bootstrap.py); non-
repaint sözleşmesi `tests/test_patterns/test_wedge.py`'de hedefli testlerle
(pattern sınırlarının created_idx'te SABİTLENDİĞİ, sinyal zincirinin
created_idx'ten itibaren extend-only olduğu) doğrulanır.

İki katalog girdisi TEK sınıftan üretilir (`HarmonicIndicator`'daki
instance-level `meta` deseniyle aynı): `mode="wedge"` yalnızca
falling_wedge/rising_wedge'i, `mode="triangle"` yalnızca sym/asc/desc
triangle'ı raporlar — 'flag'/'pennant' `classify()`'ten dönse bile HİÇ
işlenmez (o formasyonlar `pole_range` gerektirir, bkz. `patterns/
flag_pennant.py`, saf trendline geometrisiyle sorumlu şekilde ayırt
edilemezler).

Yön: falling_wedge/asc_triangle -> kırılım YUKARI beklenir (long, break_line
= üst/direnç çizgisi); rising_wedge/desc_triangle -> kırılım AŞAĞI beklenir
(short, break_line = alt/destek çizgisi). sym_triangle YÖNSÜZDÜR — HER İKİ
yön de bağımsız birer aday olarak izlenir (hangisi önce kırılırsa o
onaylanır; ikisi ayrı pattern_id taşır, birbirini etkilemez).

Geçersizlik: kırılımdan ÖNCE fiyat KARŞI çizgiyi kapanışla kırarsa (ör.
falling_wedge beklerken destek/alt çizgi aşağı kırılırsa) aday geçersizdir
— "yanlış yönde erken kırılım" klasik teknik analiz kuralı. Süre aşımı:
apex'e (iki çizginin kesişim noktası) olan mesafenin %80'i kadar bar
içinde kırılım gelmezse EXPIRED (klasik "takoz apex'e çok yaklaşınca
güvenilirliğini kaybeder" kuralı)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from tlab.core.indicator import BaseIndicator
from tlab.core.params import BaseParams, params_hash
from tlab.core.pattern_state import (
    PatternTrackingConfig,
    level_end_from_signals,
    marker_text,
    track_breakout_pattern,
)
from tlab.core.types import (
    Direction,
    IndicatorMeta,
    IndicatorResult,
    Level,
    Line,
    Marker,
    Polygon,
    Signal,
    Timeframe,
)
from tlab.features.patterns_geom import ClassifyParams, PatternShape, classify, converging_lines
from tlab.features.swings import find_pivots
from tlab.features.trendlines import Trendline, build_trendlines
from tlab.features.volatility import atr

WedgeMode = Literal["wedge", "triangle"]

_WEDGE_SHAPES: frozenset[str] = frozenset({"falling_wedge", "rising_wedge"})
_TRIANGLE_SHAPES: frozenset[str] = frozenset({"sym_triangle", "asc_triangle", "desc_triangle"})
_BULLISH_SHAPES: frozenset[str] = frozenset({"falling_wedge", "asc_triangle"})
_BEARISH_SHAPES: frozenset[str] = frozenset({"rising_wedge", "desc_triangle"})

_LABEL_TR: dict[str, str] = {
    "falling_wedge": "ALÇALAN TAKOZ", "rising_wedge": "YÜKSELEN TAKOZ",
    "sym_triangle": "SİMETRİK ÜÇGEN", "asc_triangle": "YÜKSELEN ÜÇGEN",
    "desc_triangle": "ALÇALAN ÜÇGEN",
}


@dataclass(frozen=True)
class WedgeParams(BaseParams):
    left: int = 3
    right: int = 3
    min_pivots: int = 4
    min_bars: int = 15
    max_apex_bars: int = 120
    slope_ratio_range: tuple[float, float] = (0.3, 1.0)
    tol_atr: float = 0.3
    confirm_bars: int = 1
    vol_k: float = 1.2
    max_lines_per_side: int = 6
    retest_tol_atr: float = 0.3
    atr_period: int = 14
    vol_ma_window: int = 20


def _normalized_ratio(slope_a: float, slope_b: float) -> float:
    """min(|a|,|b|)/max(|a|,|b|) -> (0,1] (0 yön içerir ama sıfıra bölme
    korumalı); `patterns_geom._safe_ratio`'nun tersine HER ZAMAN <=1 döner,
    bu yüzden `slope_ratio_range` band karşılaştırması tek tip olur."""
    lo, hi = sorted((abs(slope_a), abs(slope_b)))
    if hi == 0:
        return 1.0
    return lo / hi


class WedgeIndicator(BaseIndicator):
    """`mode="wedge"` -> patterns.wedge, `mode="triangle"` -> patterns.triangle."""

    def __init__(self, mode: WedgeMode = "wedge", params: WedgeParams | None = None) -> None:
        if mode not in ("wedge", "triangle"):
            raise ValueError(f"mode 'wedge' ya da 'triangle' olmalı, alınan: {mode}")
        self._mode = mode
        self._shapes = _WEDGE_SHAPES if mode == "wedge" else _TRIANGLE_SHAPES
        self.params: WedgeParams = params or WedgeParams()
        self.meta = IndicatorMeta(  # type: ignore[misc]
            name=f"patterns.{mode}",
            version="0.1.0",
            category="patterns",
            description=(
                "Takoz (falling/rising wedge) tarayıcı." if mode == "wedge"
                else "Üçgen (sym/asc/desc triangle) tarayıcı."
            ),
            supported_timeframes=(Timeframe.D1, Timeframe.H4),
        )

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        p = self.params
        pivots = find_pivots(df, p.left, p.right)
        atr_series = atr(df, p.atr_period)
        close = df["close"].to_numpy()
        volume = df["volume"].to_numpy()
        vol_ma = df["volume"].rolling(p.vol_ma_window, min_periods=5).mean().to_numpy()

        upper_lines = build_trendlines(
            df, pivots, "resistance", min_touches=2, tol_atr=p.tol_atr,
            confirm_bars=p.confirm_bars, atr_period=p.atr_period, max_lines=p.max_lines_per_side,
        )
        lower_lines = build_trendlines(
            df, pivots, "support", min_touches=2, tol_atr=p.tol_atr,
            confirm_bars=p.confirm_bars, atr_period=p.atr_period, max_lines=p.max_lines_per_side,
        )

        signals: list[Signal] = []
        levels: list[Level] = []
        lines: list[Line] = []
        markers: list[Marker] = []
        polygons: list[Polygon] = []
        last_state: dict[str, dict] = {}
        classify_params = ClassifyParams()

        for upper in upper_lines:
            for lower in lower_lines:
                conv = converging_lines(upper, lower)
                shape = classify(conv, classify_params)
                if shape is None or shape not in self._shapes:
                    continue
                if not _passes_shape_filters(conv, upper, lower, p):
                    continue

                pattern_key = (
                    f"{self._mode}_{upper.p1.bar_idx}_{upper.p2.bar_idx}"
                    f"_{lower.p1.bar_idx}_{lower.p2.bar_idx}"
                )
                height = abs(
                    upper.value_at(conv.created_idx) - lower.value_at(conv.created_idx)
                )
                apex_span = conv.apex_idx - conv.created_idx  # type: ignore[operator]
                max_bars_to_confirm = int(0.8 * apex_span)
                # 2026-09-03: kırılım ONAYI için zaten bir üst sınır vardı
                # (yukarıdaki satır) ama kırılım SONRASI hedefin gelmesi için
                # YOKTU — gerçek veride kırılım aylar/yıllar önce olup hedefe
                # tesadüfen çok sonra değinen zincirler `latest_signals()`'ta
                # bugünmüş gibi görünüyordu (bkz. `PatternTrackingConfig.
                # max_bars_to_target` docstring'i). Formasyonun kendi oluşum
                # süresinin (apex_span) makul bir katı kadar bekleniyor.
                max_bars_to_target = max(1, round(1.5 * apex_span))

                upper_points = (
                    (upper.p1.bar_time, upper.p1.price), (upper.p2.bar_time, upper.p2.price),
                )
                lines.append(
                    Line(
                        points=upper_points,
                        label=f"{pattern_key}_upper", style="pattern_boundary", extend_right=True,
                    )
                )
                lower_points = (
                    (lower.p1.bar_time, lower.p1.price), (lower.p2.bar_time, lower.p2.price),
                )
                lines.append(
                    Line(
                        points=lower_points,
                        label=f"{pattern_key}_lower", style="pattern_boundary", extend_right=True,
                    )
                )
                # Hologram dolgusu: iki sınır çizgisinin dört ANKOR noktasını
                # (yeni bir hesap değil, `upper_points`/`lower_points`'in
                # AYNISI) çevre sırasıyla birleştirir — harmonik motorun
                # üçgen dolgusuyla AYNI görsel dil.
                polygons.append(
                    Polygon(
                        points=(upper_points[0], upper_points[1], lower_points[1], lower_points[0]),
                        label=f"{pattern_key}_hologram", style="pattern_hologram",
                    )
                )

                for direction, break_tl, other_tl in _direction_candidates(shape, upper, lower):
                    target = (
                        break_tl.value_at(conv.created_idx) + height if direction == "long"
                        else break_tl.value_at(conv.created_idx) - height
                    )
                    pattern_id = f"{pattern_key}_{direction}"

                    def _invalidation(
                        t: int, _hi: float, _lo: float,
                        _other: Trendline = other_tl, _dir: str = direction,
                    ) -> bool:
                        other_val = _other.value_at(t)
                        return close[t] < other_val if _dir == "long" else close[t] > other_val

                    cfg = PatternTrackingConfig(
                        pattern_id=pattern_id, pattern_name=shape, direction=direction,
                        break_line=break_tl.value_at, target=target, confirm_bars=p.confirm_bars,
                        max_bars_to_confirm=max_bars_to_confirm, retest_tol_atr=p.retest_tol_atr,
                        atr_series=atr_series, score=0.6,
                        invalidation_check=_invalidation,
                        max_bars_to_target=max_bars_to_target,
                        extra_payload={
                            "apex_idx": float(conv.apex_idx),  # type: ignore[arg-type]
                            "apex_price": conv.apex_price, "height": height,
                        },
                    )
                    pattern_signals = track_breakout_pattern(df, conv.created_idx, cfg)

                    confirm_sig = next(
                        (s for s in pattern_signals if s.payload["event"].endswith("_confirmed")),
                        None,
                    )
                    if confirm_sig is not None:
                        vol_bar_idx = df.index.get_loc(confirm_sig.bar_time)
                        vma = vol_ma[vol_bar_idx]
                        volume_ok = (
                            not pd.isna(vma) and vma > 0 and volume[vol_bar_idx] >= p.vol_k * vma
                        )
                        confirm_sig.payload["volume_ok"] = bool(volume_ok)

                    signals.extend(pattern_signals)

                    levels.append(
                        Level(
                            price=target, label=f"{pattern_id}_target", style="pattern_target",
                            start=df.index[conv.created_idx],
                            end=level_end_from_signals(pattern_signals),
                        )
                    )
                    last_sig = pattern_signals[-1]
                    markers.append(
                        Marker(
                            t=last_sig.bar_time, price=close[df.index.get_loc(last_sig.bar_time)],
                            text=marker_text(_LABEL_TR[shape], last_sig.payload["event"], shape),
                            kind=f"pattern_{last_sig.state}:{pattern_id}",
                        )
                    )
                    last_state[pattern_id] = {
                        "shape": shape, "direction": direction, "state": last_sig.state,
                        "event": last_sig.payload["event"], "target": target,
                    }

        return IndicatorResult(
            indicator=self.meta.name, version=self.meta.version, params_hash=params_hash(p),
            symbol="", timeframe=Timeframe.D1,
            signals=signals, levels=levels, lines=lines, markers=markers, polygons=polygons,
            last_state=last_state,
        )


def _passes_shape_filters(conv, upper: Trendline, lower: Trendline, p: WedgeParams) -> bool:
    distinct_pivots = {upper.p1.bar_idx, upper.p2.bar_idx, lower.p1.bar_idx, lower.p2.bar_idx}
    if len(distinct_pivots) < p.min_pivots:
        return False
    if conv.created_idx - min(upper.p1.bar_idx, lower.p1.bar_idx) < p.min_bars:
        return False
    if conv.apex_idx is None:
        return False
    if conv.apex_idx - conv.created_idx > p.max_apex_bars:
        return False
    if conv.apex_idx - conv.created_idx < 1:
        return False
    ratio = _normalized_ratio(upper.slope, lower.slope)
    return p.slope_ratio_range[0] <= ratio <= p.slope_ratio_range[1]


def _direction_candidates(
    shape: PatternShape, upper: Trendline, lower: Trendline,
) -> list[tuple[Direction, Trendline, Trendline]]:
    if shape in _BULLISH_SHAPES:
        return [("long", upper, lower)]
    if shape in _BEARISH_SHAPES:
        return [("short", lower, upper)]
    return [("long", upper, lower), ("short", lower, upper)]  # sym_triangle: yönsüz
