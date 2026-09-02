"""Bayrak (flag) / Flama (pennant) devam formasyonu tarayıcı — Faz 8B.

Direk (pole) tespiti `tlab/features/zones_sd.py::find_impulses`'in DOĞRUDAN
yeniden kullanımıdır (k=pole_bars, impulse_atr=pole_atr) — ayrı bir "rolling
net hareket" hesabı YAZILMADI, S/D bölgelerinin patlama tespitiyle AYNI
tanım (Faz 8C'de zaten var olan bir birincil özellik).

`wedge.py`/`head_shoulders.py`'nin aksine konsolidasyon kanalı burada
`trendlines.build_trendlines`'ın pivot-tabanlı aday havuzuyla DEĞİL, direk
SONRASI SABİT `flag_min_bars` uzunluğundaki pencerenin high/low serisine
OLS (numpy.polyfit derece-1) fit edilerek kurulur — bu pencere ve fit,
PENDING doğduğu barda (`born_idx = pole.t1_idx + flag_min_bars`) SABİTLENİR,
bir daha büyümez (extend-only değil, "dondur" — `weekly_channel.py`'nin
`channel_frozen_*` deseniyle aynı felsefe). `patterns_geom.converging_lines`
BİLEREK kullanılmadı: o fonksiyon gerçek pivot-tabanlı `Trendline` nesneleri
ister, burada kanal saf bir OLS fiti (pivot YOK) — sentetik Pivot/Trendline
nesneleri üretmek gereksiz bir dolaylama olurdu.

Şekil ayrımı (bayrak/flama) basit bir sezgidir (kitap referansı YOK, pragmatik
geometri): pencere sonunda üst-alt aralık başlangıca göre belirgin daralmışsa
("flama" — üçgene yakınsıyor), aksi halde "bayrak" (kanal/dikdörtgene yakın).

Kırılım: direk yönünde (up pole -> üst çizginin üstüne kapanış, down pole ->
alt çizginin altına) kapanış. Hedef: kırılım çizgisinin born barındaki
değeri + direk boyu (fiyat cinsinden ölçülü hareket). Geçersizlik: born
barından SONRA kapanışın, direğin `max_retrace` oranından fazlasını geri
alması (klasik kural: bayrak/flama direğin YARISINDAN fazlasını geri
almamalı). Süre aşımı: `flag_max_bars` (direk sonundan itibaren) içinde
kırılım gelmezse EXPIRED.

Aday havuzu zamanlaması burada YOKTUR (born_idx tek bir sabit pencereden
belirlenir, `max_lines` tarzı bir "üstten kes" seçimi yok) — bu yüzden
generic `Registry.register()`'a TEMİZ kaydolur."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
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
from tlab.features.volatility import atr
from tlab.features.zones_sd import find_impulses

_LABEL_TR = {"bayrak": "BAYRAK", "flama": "FLAMA"}


@dataclass(frozen=True)
class FlagPennantParams(BaseParams):
    pole_bars: int = 5
    pole_atr: float = 2.0
    flag_min_bars: int = 5
    flag_max_bars: int = 20
    flag_atr: float = 1.5
    max_retrace: float = 0.5
    confirm_bars: int = 1
    vol_k: float = 1.2
    retest_tol_atr: float = 0.3
    atr_period: int = 14


class FlagPennantIndicator(BaseIndicator):
    meta = IndicatorMeta(
        name="patterns.flag_pennant",
        version="0.1.0",
        category="patterns",
        description="Direk + dar konsolidasyon devam formasyonu (bayrak/flama) tarayıcı.",
        supported_timeframes=(Timeframe.D1, Timeframe.H4),
    )

    def __init__(self, params: FlagPennantParams | None = None) -> None:
        self.params: FlagPennantParams = params or FlagPennantParams()

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        p = self.params
        n = len(df)
        atr_series = atr(df, p.atr_period)
        close = df["close"].to_numpy()
        high = df["high"].to_numpy()
        low = df["low"].to_numpy()
        volume = df["volume"].to_numpy()
        poles = find_impulses(df, k=p.pole_bars, impulse_atr=p.pole_atr, atr_period=p.atr_period)

        signals: list[Signal] = []
        levels: list[Level] = []
        lines: list[Line] = []
        boxes: list[Box] = []
        markers: list[Marker] = []
        last_state: dict[str, dict] = {}

        for pole in poles:
            window_start = pole.t1_idx + 1
            born_idx = window_start + p.flag_min_bars - 1
            if born_idx >= n:
                continue

            a_born = atr_series.iloc[born_idx]
            if pd.isna(a_born) or a_born == 0:
                continue
            win_high = high[window_start : born_idx + 1]
            win_low = low[window_start : born_idx + 1]
            if (win_high.max() - win_low.min()) > p.flag_atr * a_born:
                continue

            pole_range_price = abs(close[pole.t1_idx] - close[pole.t0_idx])
            if pole_range_price == 0:
                continue
            direction: Direction = "long" if pole.direction == "up" else "short"

            max_giveback = p.max_retrace * pole_range_price
            retrace_breached = False
            for t in range(window_start, born_idx + 1):
                if direction == "long":
                    retrace_breached = close[t] < close[pole.t1_idx] - max_giveback
                else:
                    retrace_breached = close[t] > close[pole.t1_idx] + max_giveback
                if retrace_breached:
                    break
            if retrace_breached:
                continue

            x = np.arange(p.flag_min_bars, dtype=float)
            upper_slope, upper_intercept = np.polyfit(x, win_high, 1)
            lower_slope, lower_intercept = np.polyfit(x, win_low, 1)
            gap_start = upper_intercept - lower_intercept
            upper_end = upper_slope * x[-1] + upper_intercept
            lower_end = lower_slope * x[-1] + lower_intercept
            gap_end = upper_end - lower_end
            shape = "flama" if (gap_start > 0 and gap_end < 0.7 * gap_start) else "bayrak"

            def _upper_at(
                t: int, _s: float = upper_slope, _i: float = upper_intercept,
                _ws: int = window_start,
            ) -> float:
                return _s * (t - _ws) + _i

            def _lower_at(
                t: int, _s: float = lower_slope, _i: float = lower_intercept,
                _ws: int = window_start,
            ) -> float:
                return _s * (t - _ws) + _i

            break_line = _upper_at if direction == "long" else _lower_at
            other_line = _lower_at if direction == "long" else _upper_at
            channel_val_at_born = break_line(born_idx)
            target = (
                channel_val_at_born + pole_range_price if direction == "long"
                else channel_val_at_born - pole_range_price
            )

            def _invalidation(
                t: int, _hi: float, _lo: float, _other: object = other_line, _dir: str = direction,
            ) -> bool:
                other_val = _other(t)  # type: ignore[operator]
                return close[t] < other_val if _dir == "long" else close[t] > other_val

            pattern_id = f"flagpennant_{pole.t0_idx}_{pole.t1_idx}"
            # 2026-09-03: bkz. `PatternTrackingConfig.max_bars_to_target`
            # docstring'i -- bayrak/flama kısa vadeli devam formasyonları
            # olduğu için ölçek direğin (pole) kendi süresinden alınır.
            pole_span = max(1, pole.t1_idx - pole.t0_idx)
            max_bars_to_target = max(1, round(2.0 * (pole_span + p.flag_max_bars)))
            cfg = PatternTrackingConfig(
                pattern_id=pattern_id, pattern_name=shape, direction=direction,
                break_line=break_line, target=target, confirm_bars=p.confirm_bars,
                max_bars_to_confirm=max(0, (window_start + p.flag_max_bars - 1) - born_idx),
                retest_tol_atr=p.retest_tol_atr, atr_series=atr_series, score=0.55,
                invalidation_check=_invalidation,
                extra_payload={"pole_range": pole_range_price},
                max_bars_to_target=max_bars_to_target,
            )
            pattern_signals = track_breakout_pattern(df, born_idx, cfg)

            confirm_sig = next(
                (s for s in pattern_signals if s.payload["event"].endswith("_confirmed")), None
            )
            if confirm_sig is not None:
                pole_vol = float(volume[pole.t0_idx : pole.t1_idx + 1].mean())
                flag_vol = float(volume[window_start : born_idx + 1].mean())
                confirm_sig.payload["volume_profile_ok"] = bool(
                    flag_vol > 0 and pole_vol >= p.vol_k * flag_vol
                )

            signals.extend(pattern_signals)

            lines.append(
                Line(
                    points=(
                        (df.index[pole.t0_idx], float(close[pole.t0_idx])),
                        (df.index[pole.t1_idx], float(close[pole.t1_idx])),
                    ),
                    label=f"{pattern_id}_pole", style="pattern_pole",
                )
            )
            boxes.append(
                Box(
                    t0=df.index[window_start], t1=df.index[born_idx],
                    low=float(win_low.min()), high=float(win_high.max()),
                    label=f"{pattern_id}_consolidation", style="pattern_consolidation",
                )
            )
            levels.append(
                Level(
                    price=target, label=f"{pattern_id}_target", style="pattern_target",
                    start=df.index[born_idx], end=level_end_from_signals(pattern_signals),
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
            signals=signals, levels=levels, lines=lines, boxes=boxes, markers=markers,
            last_state=last_state,
        )
