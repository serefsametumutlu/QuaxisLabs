"""MultiBreakout — çoklu kırılım tarayıcısı (Faz 8A).

Tek indikatör, çok tür (Bölüm 12.5 tablosu): downtrend_break, uptrend_break,
range_breakout_up/down, zone_break_up/down, hh_break, ll_break,
n_week_high_{26,52}, ma_break_ema{50,200}, channel_break_up/down,
donchian_break_up/down_{20,55}, bb_break_up/down — hepsi KAPANIŞ ile ve
kendi barında (`confirm_bars` parametreli, bkz. `_confirmed_crossings`),
üstüne her kırılım için (kaynağı ne olursa olsun) `retest_hold`/`false_break`
takip taraması (bkz. `_scan_retest_and_false_break`).

Mimari: trendline/range/zone kaynaklı kırılımlar `tlab/features/`'ın KENDİ
touches/broken_at mekanizmasını kullanır (aynı `PriceStructure`'daki gibi);
pivot/MA/Donchian/Bollinger/kanal kaynaklı kırılımlar TEK bir jenerik
"seviye dizisi + confirm_bars" tarayıcısından (`_generic_break_events`)
geçer — bu ikisi arasında touches/level_age hesabı FARKLIDIR (öncekiler
kendi geçmişini taşır, sonrakiler `tol_atr` içinde yakınlık sayımıyla
türetilir) ve bu modülün kendi docstring'lerinde ayrı ayrı belgelenir.

Kalite skoru (`quality_score`, görev metninin sabit ağırlıkları): hacim 0.30,
seviye yaşı 0.20, temas 0.20, gövde oranı 0.15, mesafe (ATR) 0.15 — her
bileşen 0..1'e normalize edilir (normalizasyon sabitleri `BreakoutParams`'ta,
görev metninde belirtilmediği için makul varsayılanlarla, kod içinde
gerekçelendirilmiş)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
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
from tlab.features.channels import regression_channel
from tlab.features.ma import ema, sma
from tlab.features.ranges import Range, detect_ranges
from tlab.features.swings import Pivot, PivotKind, alternate_pivots, find_pivots, label_structure
from tlab.features.trendlines import Trendline, TrendlineKind, build_trendlines
from tlab.features.volatility import atr, bollinger
from tlab.features.zones import Zone, cluster_zones


@dataclass(frozen=True)
class BreakoutParams(BaseParams):
    pivot_left: int = 3
    pivot_right: int = 3
    atr_period: int = 14
    confirm_bars: int = 1
    trendline_min_touches: int = 2
    trendline_tol_atr: float = 0.3
    trendline_max_lines: int = 4
    range_min_bars: int = 10
    range_atr_mult: float = 1.5
    zone_band_atr: float = 0.5
    zone_min_pivots: int = 2
    vol_ma_window: int = 20
    vol_k: float = 1.5
    ema_periods: tuple[int, ...] = (50, 200)
    n_week_periods: tuple[int, ...] = (26, 52)
    trading_days_per_week: int = 5
    donchian_periods: tuple[int, ...] = (20, 55)
    bb_period: int = 20
    bb_k: float = 2.0
    bb_bandwidth_lookback: int = 100
    bb_bandwidth_pctile: float = 0.20
    channel_n: int = 100
    channel_k: float = 2.0
    retest_tol_atr: float = 0.3
    retest_max_bars: int = 10
    false_break_bars: int = 5
    # Kalite skoru normalizasyon sabitleri (görev metninde belirtilmedi,
    # makul varsayılanlar — bkz. modül docstring'i):
    quality_age_norm_bars: float = 50.0
    quality_touch_norm: float = 5.0
    quality_touch_lookback: int = 60
    quality_distance_atr_norm: float = 1.0


class MultiBreakout(BaseIndicator):
    """Çoklu kırılım tarayıcısı — bkz. modül docstring'i."""

    meta = IndicatorMeta(
        name="trend.breakouts",
        version="0.1.0",
        category="trend",
        description=(
            "Trendline/range/zone/pivot/MA/Donchian/Bollinger/kanal kırılımları "
            "+ retest/false-break."
        ),
        supported_timeframes=(Timeframe.D1, Timeframe.H4),
    )

    def __init__(self, params: BreakoutParams | None = None) -> None:
        self.params: BreakoutParams = params or BreakoutParams()

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        p = self.params
        close = df["close"].to_numpy(dtype=float)
        atr_series = atr(df, p.atr_period)
        atr_arr = atr_series.to_numpy(dtype=float)
        vol_ma_series = sma(df["volume"], p.vol_ma_window)

        ctx = _Ctx(
            df=df, p=p, close=close, atr_arr=atr_arr,
            volume=df["volume"].to_numpy(dtype=float),
            vol_ma=vol_ma_series.to_numpy(dtype=float),
            open_=df["open"].to_numpy(dtype=float),
            high=df["high"].to_numpy(dtype=float),
            low=df["low"].to_numpy(dtype=float),
        )

        signals: list[Signal] = []
        levels: list[Level] = []
        lines: list[Line] = []
        boxes: list[Box] = []
        markers: list[Marker] = []

        raw_pivots = find_pivots(df, p.pivot_left, p.pivot_right)
        zigzag = label_structure(alternate_pivots(raw_pivots))

        # trendline/zone kırılımları RAW pivotları kullanır (PriceStructure
        # ile AYNI konvansiyon — bkz. price_structure.py::_trendlines/_zones):
        # bir trendline/bölgenin temas noktaları alternate_pivots'un
        # ALTERNE ETTİĞİ (H-L-H-L zorunluluğuyla elediği) ara-pivotları da
        # içerebilir, bu yüzden ALTERNE EDİLMEMİŞ ham liste kullanılır.
        # hh_break/ll_break ve "structure_ok" (HL etiketi) ise TANIM GEREĞİ
        # alterne edilmiş/etiketlenmiş zigzag'a ihtiyaç duyar.
        _add_trendline_breaks(ctx, raw_pivots, zigzag, signals, lines, markers)
        _add_range_breaks(ctx, boxes, signals, markers)
        _add_zone_breaks(ctx, raw_pivots, boxes, signals, markers)
        _add_pivot_breaks(ctx, zigzag, levels, signals, markers)
        _add_n_week_high_breaks(ctx, levels, signals, markers)
        _add_ma_breaks(ctx, levels, signals, markers)
        _add_donchian_breaks(ctx, levels, signals, markers)
        _add_bb_breaks(ctx, levels, signals, markers)
        _add_channel_breaks(ctx, levels, signals, markers)

        series = {"volume": df["volume"], "volume_ma": vol_ma_series}
        last_state = {
            "n_breaks": len(
                [s for s in signals if s.payload.get("event") == "break"]
            ),
            "n_retest_hold": len(
                [s for s in signals if s.payload.get("event") == "retest_hold"]
            ),
            "n_false_break": len(
                [s for s in signals if s.payload.get("event") == "false_break"]
            ),
        }

        return IndicatorResult(
            indicator=self.meta.name, version=self.meta.version,
            params_hash=params_hash(p), symbol="", timeframe=Timeframe.D1,
            signals=signals, levels=levels, lines=lines, boxes=boxes, markers=markers,
            series=series, series_layout={"hacim": ["volume", "volume_ma"]},
            last_state=last_state,
        )


@dataclass
class _Ctx:
    """Tüm `_add_*` yardımcılarının paylaştığı salt-okunur bağlam (parametre
    tekrarını azaltmak için) — hiçbir alan compute() dışında mutasyona
    uğramaz."""

    df: pd.DataFrame
    p: BreakoutParams
    close: np.ndarray
    atr_arr: np.ndarray
    volume: np.ndarray
    vol_ma: np.ndarray
    open_: np.ndarray
    high: np.ndarray
    low: np.ndarray

    @property
    def n(self) -> int:
        return len(self.df)


# ------------------------------------------------------------- ortak kalite --


def _quality_and_payload(
    ctx: _Ctx, confirmed_idx: int, level_value: float, touches: int, level_age_bars: int,
) -> dict:
    p = ctx.p
    vol_ratio = (
        ctx.volume[confirmed_idx] / ctx.vol_ma[confirmed_idx]
        if not np.isnan(ctx.vol_ma[confirmed_idx]) and ctx.vol_ma[confirmed_idx] > 0
        else float("nan")
    )
    volume_ok = bool(not np.isnan(vol_ratio) and vol_ratio >= p.vol_k)
    o, c = ctx.open_[confirmed_idx], ctx.close[confirmed_idx]
    hi, lo = ctx.high[confirmed_idx], ctx.low[confirmed_idx]
    body_ratio = abs(c - o) / (hi - lo) if hi > lo else 0.0
    a = ctx.atr_arr[confirmed_idx]
    distance_atr = abs(c - level_value) / a if not np.isnan(a) and a > 0 else 0.0

    vol_score = 0.0 if np.isnan(vol_ratio) else min(vol_ratio / (2.0 * p.vol_k), 1.0)
    age_score = min(max(level_age_bars, 0) / p.quality_age_norm_bars, 1.0)
    touch_score = min(touches / p.quality_touch_norm, 1.0)
    distance_score = min(distance_atr / p.quality_distance_atr_norm, 1.0)
    quality = (
        0.30 * vol_score + 0.20 * age_score + 0.20 * touch_score
        + 0.15 * body_ratio + 0.15 * distance_score
    )

    return {
        "level_value": float(level_value),
        "level_age_bars": int(level_age_bars),
        "touches": int(touches),
        "volume_ratio": None if np.isnan(vol_ratio) else float(vol_ratio),
        "volume_ok": volume_ok,
        "body_ratio": float(body_ratio),
        "distance_atr": float(distance_atr),
        "quality_score": float(quality),
    }


def _emit_break(
    ctx: _Ctx, break_type: str, direction: Direction, origin_idx: int, confirmed_idx: int,
    level_value: float, touches: int, level_age_bars: int,
    signals: list[Signal], markers: list[Marker], extra: dict | None = None,
) -> str:
    df = ctx.df
    pattern_id = f"{break_type}_{origin_idx}_{confirmed_idx}"
    payload = {
        "event": "break", "break_type": break_type, "pattern_id": pattern_id,
        "retest_state": "pending",
        **_quality_and_payload(ctx, confirmed_idx, level_value, touches, level_age_bars),
    }
    if extra:
        payload.update(extra)
    signals.append(
        Signal(
            bar_time=df.index[confirmed_idx], detected_at=df.index[confirmed_idx],
            direction=direction, state="confirmed", score=payload["quality_score"],
            payload=payload,
        )
    )
    quality_pct = int(round(payload["quality_score"] * 100))
    vol_txt = (
        f"×{payload['volume_ratio']:.1f}" if payload["volume_ratio"] is not None else "?"
    )
    yon_txt = "YUKARI" if direction == "long" else "AŞAĞI"
    marker_text = (
        f"Kırılım: {yon_txt} | {break_type} | Temas:{touches} | "
        f"Hacim {vol_txt} | Q:{quality_pct}"
    )
    markers.append(
        Marker(t=df.index[confirmed_idx], price=level_value, text=marker_text, kind="breakout")
    )
    signals.extend(
        _scan_retest_and_false_break(
            ctx, direction, level_value, pattern_id, break_type, confirmed_idx,
        )
    )
    return pattern_id


def _scan_retest_and_false_break(
    ctx: _Ctx, direction: Direction, level_value: float, pattern_id: str,
    break_type: str, confirmed_idx: int,
) -> list[Signal]:
    """Kırılımdan sonra `false_break_bars` içinde kapanış seviyenin GERİSİNE
    dönerse `false_break`; aksi halde `retest_max_bars` içinde fiyat
    seviyeye `retest_tol_atr*ATR` içine gelip kapanış hâlâ doğru tarafta
    kalırsa `retest_hold`. ORİJİNAL kırılım kaydı (yukarıdaki Signal) BU
    fonksiyondan SONRA asla değiştirilmez/silinmez — yalnızca YENİ, ayrı
    Signal'ler (aynı `pattern_id` ile) eklenir."""
    p = ctx.p
    df = ctx.df
    n = ctx.n
    window_end = min(n, confirmed_idx + 1 + max(p.retest_max_bars, p.false_break_bars))

    for t in range(confirmed_idx + 1, window_end):
        a = ctx.atr_arr[t]
        tol = p.retest_tol_atr * a if not np.isnan(a) else 0.0
        c = ctx.close[t]

        if t < confirmed_idx + 1 + p.false_break_bars:
            reversed_ = c < level_value if direction == "long" else c > level_value
            if reversed_:
                payload = {
                    "event": "false_break", "break_type": break_type,
                    "pattern_id": pattern_id, "retest_state": "failed",
                }
                return [
                    Signal(
                        bar_time=df.index[t], detected_at=df.index[t],
                        direction=direction, state="invalidated", score=0.0,
                        payload=payload,
                    )
                ]

        if t < confirmed_idx + 1 + p.retest_max_bars:
            touched_back = (
                (ctx.low[t] <= level_value + tol) if direction == "long"
                else (ctx.high[t] >= level_value - tol)
            )
            held = c > level_value if direction == "long" else c < level_value
            if touched_back and held:
                payload = {
                    "event": "retest_hold", "break_type": break_type,
                    "pattern_id": pattern_id, "retest_state": "held",
                }
                return [
                    Signal(
                        bar_time=df.index[t], detected_at=df.index[t],
                        direction=direction, state="confirmed", score=1.0,
                        payload=payload,
                    )
                ]
    return []


# --------------------------------------------------- jenerik seviye tarayıcı --


def _confirmed_crossings(
    close: np.ndarray, level: np.ndarray, above: bool, confirm_bars: int
) -> list[tuple[int, int]]:
    """(origin_idx, confirmed_idx) — `level` NaN olan barlar atlanır (state
    sıfırlanır). `above`: close > level "ötesinde" sayılır; aksi halde
    close < level. Bir origin, ardışık `confirm_bars` barında ötesinde
    kalırsa `origin+confirm_bars-1`'de TEK SEFER onaylanır; arada geri
    dönülürse o origin iptal olur (yeni origin, state 'ötesinde-değil'e
    döndükten SONRA açılabilir) — non-repaint: bir bar için karar bir kez
    verilir, sonraki barlar geçmiş kararı değiştirmez."""
    events: list[tuple[int, int]] = []
    was_beyond = False
    streak_start: int | None = None
    streak_len = 0
    confirmed_this_streak = False

    for t in range(len(close)):
        lv = level[t]
        if np.isnan(lv):
            was_beyond, streak_start, streak_len, confirmed_this_streak = False, None, 0, False
            continue
        beyond = close[t] > lv if above else close[t] < lv
        if beyond:
            if not was_beyond:
                streak_start, streak_len, confirmed_this_streak = t, 0, False
            streak_len += 1
            if not confirmed_this_streak and streak_len >= confirm_bars:
                assert streak_start is not None
                events.append((streak_start, t))
                confirmed_this_streak = True
        else:
            streak_start, streak_len, confirmed_this_streak = None, 0, False
        was_beyond = beyond
    return events


def _first_valid_idx(level: np.ndarray) -> int | None:
    valid = np.flatnonzero(~np.isnan(level))
    return int(valid[0]) if len(valid) else None


def _generic_break_events(
    ctx: _Ctx, level: np.ndarray, level_start_idx: int, above: bool,
) -> list[dict]:
    """`level`: `close` ile aynı uzunlukta dizi (NaN = henüz geçerli değil).
    `touches`: origin'den ÖNCEKİ `quality_touch_lookback` bar içinde fiyatın
    seviyeye `retest_tol_atr*ATR` içine gelip AŞMADIĞI bar sayısı — bu,
    trendline/zone'un kendi touches'ından FARKLI bir proxy'dir (o ikisi
    kendi geçmişini taşır, burası yalnızca yakınlık sayar); `level_age_bars`
    = origin - level_start_idx (seviye ne zamandır geçerli)."""
    p = ctx.p
    events = _confirmed_crossings(ctx.close, level, above, p.confirm_bars)
    out = []
    for origin_idx, confirmed_idx in events:
        lookback_start = max(level_start_idx, origin_idx - p.quality_touch_lookback)
        touches = 0
        for t in range(lookback_start, origin_idx):
            a = ctx.atr_arr[t]
            lv = level[t]
            if np.isnan(a) or np.isnan(lv):
                continue
            near = abs(ctx.close[t] - lv) <= p.retest_tol_atr * a
            beyond_t = ctx.close[t] > lv if above else ctx.close[t] < lv
            if near and not beyond_t:
                touches += 1
        out.append(
            {
                "origin_idx": origin_idx, "confirmed_idx": confirmed_idx,
                "level_value": float(level[origin_idx]), "touches": touches,
                "level_age_bars": origin_idx - level_start_idx,
            }
        )
    return out


# ------------------------------------------------------- trendline kaynaklı --


def _last_low_label_before(zigzag: list[Pivot], idx: int) -> str | None:
    candidates = [
        pv for pv in zigzag
        if pv.kind == "low" and pv.finalized_idx is not None and pv.finalized_idx <= idx
    ]
    return candidates[-1].label if candidates else None


def _add_trendline_breaks(
    ctx: _Ctx, raw_pivots: list[Pivot], zigzag: list[Pivot],
    signals: list[Signal], lines: list[Line], markers: list[Marker],
) -> None:
    p = ctx.p
    trendline_specs: list[tuple[TrendlineKind, str, Direction]] = [
        ("resistance", "downtrend_break", "long"),
        ("support", "uptrend_break", "short"),
    ]
    for kind, break_type, direction in trendline_specs:
        trendlines: list[Trendline] = build_trendlines(
            ctx.df, raw_pivots, kind, p.trendline_min_touches, p.trendline_tol_atr,
            p.confirm_bars, p.atr_period, p.trendline_max_lines,
        )
        for tl in trendlines:
            line_style = "broken_up" if direction == "long" else "broken_down"
            lines.append(
                Line(
                    points=((tl.p1.bar_time, tl.p1.price), (tl.p2.bar_time, tl.p2.price)),
                    label=f"{break_type} adayı", style=line_style, extend_right=True,
                )
            )
            if tl.broken_at is None:
                continue
            level_value = tl.value_at(tl.broken_at)
            extra = {}
            if break_type == "downtrend_break":
                extra["structure_ok"] = _last_low_label_before(zigzag, tl.broken_at) == "HL"
            _emit_break(
                ctx, break_type, direction, tl.created_idx, tl.broken_at, level_value,
                len(tl.touches), tl.broken_at - tl.created_idx, signals, markers, extra,
            )


# ---------------------------------------------------------- range kaynaklı --


def _add_range_breaks(
    ctx: _Ctx, boxes: list[Box], signals: list[Signal], markers: list[Marker]
) -> None:
    p = ctx.p
    ranges: list[Range] = detect_ranges(
        ctx.df, p.range_min_bars, p.range_atr_mult, p.confirm_bars, p.atr_period
    )
    for rng in ranges:
        style = "broken_up" if rng.breakout_direction == "up" else (
            "broken_down" if rng.breakout_direction == "down" else "pending"
        )
        boxes.append(
            Box(
                t0=rng.t0_time, t1=rng.t1_time, low=rng.low, high=rng.high,
                label="Konsolidasyon", style=style,
            )
        )
        if rng.breakout_idx is None:
            continue
        direction: Direction = "long" if rng.breakout_direction == "up" else "short"
        level_value = rng.high if rng.breakout_direction == "up" else rng.low
        break_type = (
            "range_breakout_up" if rng.breakout_direction == "up" else "range_breakout_down"
        )
        touches = rng.breakout_idx - rng.t0_idx
        level_age_bars = rng.breakout_idx - rng.detected_idx
        _emit_break(
            ctx, break_type, direction, rng.t0_idx, rng.breakout_idx, level_value,
            touches, level_age_bars, signals, markers,
        )


# ----------------------------------------------------------- zone kaynaklı --


def _add_zone_breaks(
    ctx: _Ctx, raw_pivots: list[Pivot], boxes: list[Box],
    signals: list[Signal], markers: list[Marker],
) -> None:
    p = ctx.p
    for kind in ("high", "low"):
        kind_pivots = [pv for pv in raw_pivots if pv.kind == kind]
        zones: list[Zone] = cluster_zones(
            ctx.df, kind_pivots, p.zone_min_pivots, p.zone_band_atr, p.confirm_bars, p.atr_period,
        )
        for zone in zones:
            t1 = ctx.df.index[zone.broken_at] if zone.broken_at is not None else ctx.df.index[-1]
            style = (
                "broken_up" if zone.broken_direction == "up"
                else "broken_down" if zone.broken_direction == "down" else "pending"
            )
            boxes.append(
                Box(
                    t0=zone.formed_time, t1=t1, low=zone.low, high=zone.high,
                    label="Bölge", style=style,
                )
            )
            if zone.broken_at is None:
                continue
            direction: Direction = "long" if zone.broken_direction == "up" else "short"
            level_value = zone.high if zone.broken_direction == "up" else zone.low
            break_type = "zone_break_up" if zone.broken_direction == "up" else "zone_break_down"
            _emit_break(
                ctx, break_type, direction, zone.formed_idx, zone.broken_at, level_value,
                len(zone.touches), zone.broken_at - zone.formed_idx, signals, markers,
            )


# ---------------------------------------------------- pivot (HH/LL) kaynaklı --


def _add_pivot_breaks(
    ctx: _Ctx, zigzag: list[Pivot], levels: list[Level],
    signals: list[Signal], markers: list[Marker],
) -> None:
    """hh_break/ll_break: her onaylı swing high/low, KENDİSİNDEN SONRAKİ
    aynı-türden pivot doğana kadar "aktif" bir kırılım seviyesidir (bir
    sonraki pivot doğunca eskisi süperseded olur — swing_fib_abcd'deki
    ABC üçlü zincir deseniyle AYNI mimari)."""
    pivot_specs: list[tuple[PivotKind, str, Direction]] = [
        ("high", "hh_break", "long"),
        ("low", "ll_break", "short"),
    ]
    for kind, break_type, direction in pivot_specs:
        ordered = sorted((pv for pv in zigzag if pv.kind == kind), key=lambda pv: pv.bar_idx)
        for i, piv in enumerate(ordered):
            start = piv.finalized_idx
            if start is None or start >= ctx.n:
                continue
            end = ctx.n
            if i + 1 < len(ordered):
                next_finalized = ordered[i + 1].finalized_idx
                if next_finalized is not None:
                    end = min(next_finalized, ctx.n)
            level = np.full(ctx.n, np.nan)
            level[start:end] = piv.price
            for ev in _generic_break_events(ctx, level, start, above=(kind == "high")):
                pid = _emit_break(
                    ctx, break_type, direction, ev["origin_idx"], ev["confirmed_idx"],
                    ev["level_value"], ev["touches"], ev["level_age_bars"], signals, markers,
                )
                levels.append(
                    Level(
                        price=ev["level_value"], label=f"{break_type} ({pid})",
                        style="broken_up" if direction == "long" else "broken_down",
                        start=piv.bar_time, end=ctx.df.index[ev["confirmed_idx"]],
                    )
                )


# -------------------------------------------------------- N-haftalık yüksek --


def _add_n_week_high_breaks(
    ctx: _Ctx, levels: list[Level], signals: list[Signal], markers: list[Marker],
) -> None:
    """`weeks*trading_days_per_week` bar (BIST/NASDAQ için ~5 işlem günü/hafta
    yaklaşımı — W1 zaman dilimi henüz yok, bkz. CLAUDE.md Faz 2-EK notu)
    öncesindeki EN YÜKSEK high'ın üzerine kapanış. Bugünün barı HARİÇ
    (`.shift(1)`) — klasik lookahead tuzağı, testi var."""
    p = ctx.p
    high_series = ctx.df["high"]
    for weeks in p.n_week_periods:
        window = weeks * p.trading_days_per_week
        level = high_series.rolling(window, min_periods=window).max().shift(1).to_numpy(dtype=float)
        start_idx = _first_valid_idx(level)
        if start_idx is None:
            continue
        break_type = f"n_week_high_{weeks}"
        for ev in _generic_break_events(ctx, level, start_idx, above=True):
            _emit_break(
                ctx, break_type, "long", ev["origin_idx"], ev["confirmed_idx"],
                ev["level_value"], ev["touches"], ev["level_age_bars"], signals, markers,
            )
            levels.append(
                Level(
                    price=ev["level_value"], label=break_type, style="broken_up",
                    start=ctx.df.index[ev["origin_idx"]], end=ctx.df.index[ev["confirmed_idx"]],
                )
            )


# ---------------------------------------------------------------- MA kırılımı --


def _add_ma_breaks(
    ctx: _Ctx, levels: list[Level], signals: list[Signal], markers: list[Marker]
) -> None:
    close_series = ctx.df["close"]
    for period in ctx.p.ema_periods:
        ema_arr = ema(close_series, period).to_numpy(dtype=float)
        start_idx = 0
        directional_specs: list[tuple[bool, Direction, str]] = [
            (True, "long", "up"), (False, "short", "down"),
        ]
        for above, direction, suffix in directional_specs:
            break_type = f"ma_break_ema{period}_{suffix}"
            for ev in _generic_break_events(ctx, ema_arr, start_idx, above=above):
                _emit_break(
                    ctx, break_type, direction, ev["origin_idx"], ev["confirmed_idx"],
                    ev["level_value"], ev["touches"], ev["level_age_bars"], signals, markers,
                )
                levels.append(
                    Level(
                        price=ev["level_value"], label=break_type,
                        style="broken_up" if above else "broken_down",
                        start=ctx.df.index[ev["origin_idx"]], end=ctx.df.index[ev["confirmed_idx"]],
                    )
                )


# ------------------------------------------------------------ Donchian kanalı --


def _add_donchian_breaks(
    ctx: _Ctx, levels: list[Level], signals: list[Signal], markers: list[Marker],
) -> None:
    """Kanal SADECE kapalı geçmiş barlardan (`.shift(1)`, bugünün barı
    HARİÇ) — klasik lookahead tuzağı, testi var."""
    for period in ctx.p.donchian_periods:
        upper = (
            ctx.df["high"].rolling(period, min_periods=period).max()
            .shift(1).to_numpy(dtype=float)
        )
        lower = (
            ctx.df["low"].rolling(period, min_periods=period).min()
            .shift(1).to_numpy(dtype=float)
        )
        donchian_specs: list[tuple[np.ndarray, bool, Direction, str]] = [
            (upper, True, "long", "up"), (lower, False, "short", "down"),
        ]
        for level, above, direction, suffix in donchian_specs:
            start_idx = _first_valid_idx(level)
            if start_idx is None:
                continue
            break_type = f"donchian_break_{suffix}_{period}"
            for ev in _generic_break_events(ctx, level, start_idx, above=above):
                _emit_break(
                    ctx, break_type, direction, ev["origin_idx"], ev["confirmed_idx"],
                    ev["level_value"], ev["touches"], ev["level_age_bars"], signals, markers,
                )
                levels.append(
                    Level(
                        price=ev["level_value"], label=break_type,
                        style="broken_up" if above else "broken_down",
                        start=ctx.df.index[ev["origin_idx"]], end=ctx.df.index[ev["confirmed_idx"]],
                    )
                )


# --------------------------------------------------------------- Bollinger --


def _add_bb_breaks(
    ctx: _Ctx, levels: list[Level], signals: list[Signal], markers: list[Marker]
) -> None:
    p = ctx.p
    bb = bollinger(ctx.df["close"], p.bb_period, p.bb_k)
    upper, lower = bb.upper.to_numpy(dtype=float), bb.lower.to_numpy(dtype=float)
    bandwidth = bb.bandwidth
    bw_pctile = bandwidth.rolling(p.bb_bandwidth_lookback, min_periods=p.bb_period).apply(
        lambda w: float((w <= w.iloc[-1]).mean()), raw=False,
    ).to_numpy(dtype=float)

    bb_specs: list[tuple[np.ndarray, bool, Direction, str]] = [
        (upper, True, "long", "up"), (lower, False, "short", "down"),
    ]
    for level, above, direction, suffix in bb_specs:
        start_idx = _first_valid_idx(level)
        if start_idx is None:
            continue
        break_type = f"bb_break_{suffix}"
        for ev in _generic_break_events(ctx, level, start_idx, above=above):
            origin = ev["origin_idx"]
            squeeze_pctile = bw_pctile[origin] if origin < len(bw_pctile) else float("nan")
            squeeze_ok = bool(
                not np.isnan(squeeze_pctile) and squeeze_pctile <= p.bb_bandwidth_pctile
            )
            _emit_break(
                ctx, break_type, direction, origin, ev["confirmed_idx"],
                ev["level_value"], ev["touches"], ev["level_age_bars"], signals, markers,
                extra={"squeeze_ok": squeeze_ok},
            )
            levels.append(
                Level(
                    price=ev["level_value"], label=break_type,
                    style="broken_up" if above else "broken_down",
                    start=ctx.df.index[origin], end=ctx.df.index[ev["confirmed_idx"]],
                )
            )


# ------------------------------------------------------------ Regresyon kanalı --


def _add_channel_breaks(
    ctx: _Ctx, levels: list[Level], signals: list[Signal], markers: list[Marker],
) -> None:
    p = ctx.p
    channel = regression_channel(ctx.df, p.channel_n, p.channel_k)
    upper, lower = channel.upper.to_numpy(dtype=float), channel.lower.to_numpy(dtype=float)
    channel_specs: list[tuple[np.ndarray, bool, Direction, str]] = [
        (upper, True, "long", "channel_break_up"), (lower, False, "short", "channel_break_down"),
    ]
    for level, above, direction, break_type in channel_specs:
        start_idx = _first_valid_idx(level)
        if start_idx is None:
            continue
        for ev in _generic_break_events(ctx, level, start_idx, above=above):
            _emit_break(
                ctx, break_type, direction, ev["origin_idx"], ev["confirmed_idx"],
                ev["level_value"], ev["touches"], ev["level_age_bars"], signals, markers,
            )
            levels.append(
                Level(
                    price=ev["level_value"], label=break_type,
                    style="broken_up" if above else "broken_down",
                    start=ctx.df.index[ev["origin_idx"]], end=ctx.df.index[ev["confirmed_idx"]],
                )
            )
