"""Paralel kanal tespiti — CMT Association kuralına göre.

Kullanıcının verdiği kaynak: *"düzgün trend çizgisinin benzer büyüklükteki
support/resistance pivotlarını bağlaması gerektiği, kanalın da karşı
taraftaki pivot üzerinden paralel çizgiyle oluşturulduğu"*.

Uygulama tam olarak bu: bir taraf pivotlara EN KÜÇÜK KARELER ile uydurulur,
karşı taraf AYNI EĞİMLE, en uç pivottan geçecek şekilde ötelenir. İki
bağımsız çizgi uydurmak kanalı paralel olmaktan çıkarır.

Hesap yapar, çizmez.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from tlab.features.swings import Pivot, find_pivots


@dataclass(frozen=True)
class ChannelTouch:
    bar_time: pd.Timestamp
    price: float
    index: int
    side: str            # "upper" | "lower"


@dataclass(frozen=True)
class Channel:
    slope_per_bar: float
    upper_at: tuple[tuple[pd.Timestamp, float], tuple[pd.Timestamp, float]]
    lower_at: tuple[tuple[pd.Timestamp, float], tuple[pd.Timestamp, float]]
    upper_touches: tuple[ChannelTouch, ...]
    lower_touches: tuple[ChannelTouch, ...]
    direction: str       # "yukselen" | "alcalan" | "yatay"
    width_pct: float
    state: str           # "ALT BANT TEMASI" | "ÜST BANT TEMASI" | "BANT İÇİNDE"
    # GÜNCEL temas: fiyatın ŞU AN banda yakın olması. Geçmiş pivot
    # temaslarından (upper/lower_touches) AYRI bir kavram -- bir pivot
    # onaylanmak için `right` bar bekler, oysa güncel temas son barda olur.
    # Referans HRihBa2WIAIZjP_ de ikisini ayrı gösteriyor: numaralı daireler
    # geçmiş temaslar, yeşil üçgen + "TEMAS L4" güncel olan.
    current_touch: ChannelTouch | None
    bars_ago: int | None


def _fit(idxs: np.ndarray, prices: np.ndarray) -> tuple[float, float]:
    """En küçük kareler doğrusu: (eğim, kesişim)."""
    a, b = np.polyfit(idxs, prices, 1)
    return float(a), float(b)


def detect_channel(
    df: pd.DataFrame, *, left: int = 3, right: int = 3,
    min_touches: int = 3, tol_atr: float = 0.9, touch_atr: float = 0.6,
) -> Channel | None:
    if len(df) < 80:
        return None

    pivots = find_pivots(df, left=left, right=right)
    highs = [p for p in pivots if p.kind == "high"]
    lows = [p for p in pivots if p.kind == "low"]
    if len(highs) < min_touches or len(lows) < min_touches:
        return None

    h, low_, c = df["high"], df["low"], df["close"]
    prev = c.shift(1)
    tr = pd.concat([h - low_, (h - prev).abs(), (low_ - prev).abs()], axis=1).max(axis=1)
    atr = float(tr.ewm(alpha=1 / 14, adjust=False).mean().iloc[-1])
    if atr <= 0:
        return None

    # 1) Dipleri bağlayan doğru — kanalın taşıyıcı ekseni
    li = np.array([p.bar_idx for p in lows], dtype=float)
    lp = np.array([p.price for p in lows], dtype=float)
    slope, lower_b = _fit(li, lp)

    # 2) Aynı eğim, tepelere ötelenmiş (CMT: paralel)
    hi = np.array([p.bar_idx for p in highs], dtype=float)
    hp = np.array([p.price for p in highs], dtype=float)
    upper_b = float(np.max(hp - slope * hi))

    width = upper_b - lower_b
    if width <= 0:
        return None

    def on(b: float, idx: float) -> float:
        return slope * idx + b

    # 3) Gerçek temaslar: çizgiye ATR'nin belirli bir kesri kadar yakın pivotlar
    def touches(ps: list[Pivot], b: float, side: str) -> tuple[ChannelTouch, ...]:
        out, i = [], 0
        for p in ps:
            if abs(p.price - on(b, p.bar_idx)) <= touch_atr * atr:
                i += 1
                out.append(ChannelTouch(p.bar_time, float(p.price), i, side))
        return tuple(out)

    up_t = touches(highs, upper_b, "upper")
    lo_t = touches(lows, lower_b, "lower")
    if len(up_t) < min_touches or len(lo_t) < min_touches:
        return None

    n = len(df) - 1
    start_idx = float(min(min(li), min(hi)))
    x0, x1 = df.index[int(start_idx)], df.index[n]

    last_close = float(c.iloc[-1])
    if abs(last_close - on(lower_b, n)) <= tol_atr * atr:
        state = "ALT BANT TEMASI"
    elif abs(last_close - on(upper_b, n)) <= tol_atr * atr:
        state = "ÜST BANT TEMASI"
    else:
        state = "BANT İÇİNDE"

    # Güncel temas SON BARDA doğar; numarası, o taraftaki geçmiş temasların
    # devamıdır (referansta "TEMAS L4" böyle okunuyor).
    if state == "ALT BANT TEMASI":
        current = ChannelTouch(df.index[n], on(lower_b, n), len(lo_t) + 1, "lower")
    elif state == "ÜST BANT TEMASI":
        current = ChannelTouch(df.index[n], on(upper_b, n), len(up_t) + 1, "upper")
    else:
        current = None
    bars_ago = 0 if current is not None else None

    span_pct = slope * len(df) / max(float(c.iloc[0]), 1e-9)
    direction = "yukselen" if span_pct > 0.05 else ("alcalan" if span_pct < -0.05 else "yatay")

    return Channel(
        slope_per_bar=slope,
        upper_at=((x0, on(upper_b, start_idx)), (x1, on(upper_b, n))),
        lower_at=((x0, on(lower_b, start_idx)), (x1, on(lower_b, n))),
        upper_touches=up_t, lower_touches=lo_t,
        direction=direction,
        width_pct=width / max(on(lower_b, n), 1e-9),
        state=state, current_touch=current, bars_ago=bars_ago,
    )
