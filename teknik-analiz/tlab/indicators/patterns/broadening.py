"""Genişleyen Formasyon (broadening/megaphone) tarayıcı — Faz 8B.

`wedge.py` ile AYNI "aday havuzu" mimarisi (`trendlines.build_trendlines`'ın
resistance/support çizgi adaylarından her (upper,lower) çifti dener) — tek
fark `patterns_geom.converging_lines`/`classify` yerine YENİ
`patterns_geom.diverging_lines`'ın kullanılması (iki çizgi YAKINSAMAK yerine
UZAKLAŞIYOR, apex/hedef-tavan kavramı YOK). Bu yüzden `wedge.py` gibi
generic `Registry.register()`'a DEĞİL `register_verified_elsewhere()`'e
kaydolur.

Yön: genişleyen formasyon doğası gereği YÖNSÜZDÜR (`patterns/wedge.py`'nin
sym_triangle'ı gibi) — kırılım hangi çizgiden önce gelirse o yön onaylanır,
HER İKİ yön bağımsız birer aday olarak izlenir. `top`/`bottom` etiketi
YALNIZCA açıklayıcıdır (sinyal üretimini ETKİLEMEZ): formasyon başlamadan
`prior_trend_lookback` bar önceki kapanışa göre önceki trend yukarıysa
"broadening_top" (klasik tepe bağlamı — olası dönüş), aşağıysa
"broadening_bottom" — bu basit bir bağlamsal sezgidir, kitap referansı
yoktur, TASARIM KARARI olarak belgelenmiştir.

Hedef: kırılım anındaki genişlik (created_idx'teki upper-lower farkı) kadar
kırılım yönünde projeksiyon (ölçülü hareket, wedge ile AYNI mantık).
Geçersizlik: kırılımdan ÖNCE fiyat KARŞI çizgiyi kapanışla kırarsa. Süre
aşımı: apex olmadığı için sabit `max_bars_to_confirm` parametresi kullanılır."""

from __future__ import annotations

from dataclasses import dataclass

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
from tlab.features.patterns_geom import diverging_lines
from tlab.features.swings import find_pivots
from tlab.features.trendlines import Trendline, build_trendlines
from tlab.features.volatility import atr

_LABEL_TR = {
    "broadening_top": "GENİŞLEYEN FORMASYON (TEPE)",
    "broadening_bottom": "GENİŞLEYEN FORMASYON (DİP)",
}


@dataclass(frozen=True)
class BroadeningParams(BaseParams):
    left: int = 3
    right: int = 3
    min_pivots: int = 4
    min_bars: int = 15
    tol_atr: float = 0.3
    confirm_bars: int = 1
    vol_k: float = 1.2
    max_lines_per_side: int = 6
    max_bars_to_confirm: int = 90
    # 2026-09-03: bkz. `PatternTrackingConfig.max_bars_to_target` docstring'i
    # -- diğer formasyonlar geometriden ölçekliyor, broadening'in apex'i
    # olmadığı için (yukarıdaki `max_bars_to_confirm` gibi) sabit bir değer.
    max_bars_to_target: int = 130
    retest_tol_atr: float = 0.3
    atr_period: int = 14
    prior_trend_lookback: int = 20
    vol_ma_window: int = 20


class BroadeningIndicator(BaseIndicator):
    meta = IndicatorMeta(
        name="patterns.broadening",
        version="0.1.0",
        category="patterns",
        description="Genişleyen formasyon (broadening/megaphone) tarayıcı.",
        supported_timeframes=(Timeframe.D1, Timeframe.H4),
    )

    def __init__(self, params: BroadeningParams | None = None) -> None:
        self.params: BroadeningParams = params or BroadeningParams()

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

        for upper in upper_lines:
            for lower in lower_lines:
                dv = diverging_lines(upper, lower)
                if not dv.is_diverging:
                    continue
                distinct_pivots = {
                    upper.p1.bar_idx, upper.p2.bar_idx, lower.p1.bar_idx, lower.p2.bar_idx,
                }
                if len(distinct_pivots) < p.min_pivots:
                    continue
                start_idx = min(upper.p1.bar_idx, lower.p1.bar_idx)
                if dv.created_idx - start_idx < p.min_bars:
                    continue

                prior_ref_idx = max(0, start_idx - p.prior_trend_lookback)
                was_uptrend = close[start_idx] >= close[prior_ref_idx]
                pattern_name = "broadening_top" if was_uptrend else "broadening_bottom"
                pattern_key = (
                    f"broadening_{upper.p1.bar_idx}_{upper.p2.bar_idx}"
                    f"_{lower.p1.bar_idx}_{lower.p2.bar_idx}"
                )

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
                polygons.append(
                    Polygon(
                        points=(upper_points[0], upper_points[1], lower_points[1], lower_points[0]),
                        label=f"{pattern_key}_hologram", style="pattern_hologram",
                    )
                )

                height = abs(upper.value_at(dv.created_idx) - lower.value_at(dv.created_idx))
                direction_candidates: list[tuple[Direction, Trendline, Trendline]] = [
                    ("long", upper, lower), ("short", lower, upper),
                ]
                for direction, break_tl, other_tl in direction_candidates:
                    target = (
                        break_tl.value_at(dv.created_idx) + height if direction == "long"
                        else break_tl.value_at(dv.created_idx) - height
                    )
                    pattern_id = f"{pattern_key}_{direction}"

                    def _invalidation(
                        t: int, _hi: float, _lo: float,
                        _other: Trendline = other_tl, _dir: str = direction,
                    ) -> bool:
                        other_val = _other.value_at(t)
                        return close[t] < other_val if _dir == "long" else close[t] > other_val

                    cfg = PatternTrackingConfig(
                        pattern_id=pattern_id, pattern_name=pattern_name, direction=direction,
                        break_line=break_tl.value_at, target=target, confirm_bars=p.confirm_bars,
                        max_bars_to_confirm=p.max_bars_to_confirm, retest_tol_atr=p.retest_tol_atr,
                        atr_series=atr_series, score=0.55, invalidation_check=_invalidation,
                        extra_payload={"height": height},
                        max_bars_to_target=p.max_bars_to_target,
                    )
                    pattern_signals = track_breakout_pattern(df, dv.created_idx, cfg)

                    confirm_sig = next(
                        (s for s in pattern_signals if s.payload["event"].endswith("_confirmed")),
                        None,
                    )
                    if confirm_sig is not None:
                        vol_bar_idx = df.index.get_loc(confirm_sig.bar_time)
                        vma = vol_ma[vol_bar_idx]
                        confirm_sig.payload["volume_ok"] = bool(
                            not pd.isna(vma) and vma > 0 and volume[vol_bar_idx] >= p.vol_k * vma
                        )

                    signals.extend(pattern_signals)
                    levels.append(
                        Level(
                            price=target, label=f"{pattern_id}_target", style="pattern_target",
                            start=df.index[dv.created_idx],
                            end=level_end_from_signals(pattern_signals),
                        )
                    )
                    last_sig = pattern_signals[-1]
                    marker_price = close[df.index.get_loc(last_sig.bar_time)]
                    marker_label = marker_text(
                        _LABEL_TR[pattern_name], last_sig.payload["event"], pattern_name,
                    )
                    markers.append(
                        Marker(
                            t=last_sig.bar_time, price=marker_price, text=marker_label,
                            kind=f"pattern_{last_sig.state}",
                        )
                    )
                    last_state[pattern_id] = {
                        "pattern": pattern_name, "direction": direction, "state": last_sig.state,
                        "event": last_sig.payload["event"], "target": target,
                    }

        return IndicatorResult(
            indicator=self.meta.name, version=self.meta.version, params_hash=params_hash(p),
            symbol="", timeframe=Timeframe.D1,
            signals=signals, levels=levels, lines=lines, markers=markers, polygons=polygons,
            last_state=last_state,
        )
