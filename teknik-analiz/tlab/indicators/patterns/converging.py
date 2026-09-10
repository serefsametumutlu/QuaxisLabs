"""Yakınsayan/ıraksayan sınırlı formasyonlar — TEK tespit edici, beş tür.

Üçgen (simetrik/yükselen/alçalan), kama (yükselen/alçalan) ve genişleyen
formasyon aslında AYNI geometridir: tepelere bir doğru, diplere bir doğru
uydurulur. Türü belirleyen şey yalnızca iki eğimin İŞARETİ ve
yakınsayıp ıraksadıklarıdır.

Bu yüzden ayrı ayrı tespit ediciler yazmak yerine tek bir tanesi:

    üst ↓, alt ↑, yakınsıyor          → simetrik üçgen
    üst ~yatay, alt ↑                 → yükselen üçgen
    üst ↓, alt ~yatay                 → alçalan üçgen
    üst ↑, alt ↑, yakınsıyor          → yükselen kama
    üst ↓, alt ↓, yakınsıyor          → alçalan kama
    ıraksıyor                          → genişleyen formasyon

Bulkowski ölçütleri uygulanır:
  - Kama en az 5 temas ister (bir tarafta 3, diğerinde 2).
  - Formasyon en az 3 hafta sürmeli (günlükte ~15 bar).
  - Hacim formasyon boyunca genelde daralır (bilgi olarak taşınır,
    eleme ölçütü DEĞİL — Bulkowski'de de vakaların ~%79'u).

Onay, sınırın KAPANIŞLA kırılmasıdır; formasyonun kendisi değil.

Hesap yapar, çizmez. Çizimi `tlab/chart/composers/converging.py` yapar.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from tlab.features.swings import Pivot, find_pivots


@dataclass(frozen=True)
class BoundaryTouchPoint:
    bar_time: pd.Timestamp
    price: float
    index: int
    side: str            # "upper" | "lower"


@dataclass(frozen=True)
class ConvergingPattern:
    kind: str            # "simetrik_ucgen" | "yukselen_ucgen" | ... | "genisleyen"
    direction: str       # "long" | "short" | "notr"
    upper: tuple[tuple[pd.Timestamp, float], tuple[pd.Timestamp, float]]
    lower: tuple[tuple[pd.Timestamp, float], tuple[pd.Timestamp, float]]
    upper_touches: tuple[BoundaryTouchPoint, ...]
    lower_touches: tuple[BoundaryTouchPoint, ...]
    apex: tuple[pd.Timestamp, float] | None
    breakout: tuple[pd.Timestamp, float] | None
    breakout_side: str   # "upper" | "lower" | ""
    target: float | None
    state: str           # "olusuyor" | "onaylandi" | "suresi_doldu"
    width_change_pct: float
    vol_contraction: float
    bars: int
    bars_ago: int | None

    def __post_init__(self) -> None:
        if self.direction not in ("long", "short", "notr"):
            raise ValueError(f"yön 'long'/'short'/'notr' olmalı — alınan {self.direction!r}")

    @property
    def touch_count(self) -> int:
        return len(self.upper_touches) + len(self.lower_touches)


_MIN_TOUCH = {"kama": (3, 2), "ucgen": (2, 2), "genisleyen": (2, 2)}


def _classify(sl_hi: float, sl_lo: float, norm: float, flat: float) -> tuple[str, str]:
    """(tür, yön). `norm` fiyat ölçeği, `flat` yatay sayılma eşiği."""
    up_hi, up_lo = sl_hi / norm, sl_lo / norm
    hi_flat, lo_flat = abs(up_hi) < flat, abs(up_lo) < flat

    if hi_flat and up_lo > flat:
        return "yukselen_ucgen", "long"
    if lo_flat and up_hi < -flat:
        return "alcalan_ucgen", "short"
    if up_hi < -flat and up_lo > flat:
        return "simetrik_ucgen", "notr"
    if up_hi > flat and up_lo > flat:
        # ikisi de yukarı: alt daha dik ise yakınsıyor -> yükselen kama
        return ("yukselen_kama", "short") if up_lo > up_hi else ("genisleyen", "notr")
    if up_hi < -flat and up_lo < -flat:
        return ("alcalan_kama", "long") if up_hi > up_lo else ("genisleyen", "notr")
    return "genisleyen", "notr"


def detect_converging(
    df: pd.DataFrame,
    *,
    left: int = 3,
    right: int = 3,
    lookback: int = 160,
    min_bars: int = 15,            # Bulkowski: en az ~3 hafta
    touch_atr: float = 0.7,
    flat_slope: float = 0.0004,    # bar başına oransal eğim; altı "yatay"
    break_atr: float = 0.4,        # kırılım sayılması için ATR cinsinden aşım
    refit_rounds: int = 3,
) -> ConvergingPattern | None:
    """Son yakınsayan/ıraksayan formasyonu bulur. Yoksa `None`."""
    if len(df) < min_bars + left + right + 10:
        return None

    window = df.iloc[-lookback:] if len(df) > lookback else df
    pivots = find_pivots(window, left=left, right=right)
    highs = [p for p in pivots if p.kind == "high"]
    lows = [p for p in pivots if p.kind == "low"]
    if len(highs) < 2 or len(lows) < 2:
        return None

    h, low_, c = window["high"], window["low"], window["close"]
    prev = c.shift(1)
    tr = pd.concat([h - low_, (h - prev).abs(), (low_ - prev).abs()], axis=1).max(axis=1)
    atr = float(tr.ewm(alpha=1 / 14, adjust=False).mean().iloc[-1])
    if atr <= 0:
        return None
    norm = float(c.mean())

    # --- Sınırların uydurulması -------------------------------------
    # Naif yaklaşım (tüm pivotlara tek seferde uydurmak) KIRILIM
    # BACAĞINI da hesaba katar ve eğimleri bozar: simetrik bir üçgende
    # üst sınırın eğimi negatif olması gerekirken pozitif çıkıyordu ve
    # formasyon "yükselen üçgen" diye sınıflanıyordu.
    #
    # Çözüm: uydur → kırılımı bul → kırılımdan ÖNCEKİ pivotlarla yeniden
    # uydur. Birkaç turda oturur.
    fit_end = len(window) - 1
    sl_hi = b_hi = sl_lo = b_lo = 0.0
    hi_used: list[Pivot] = []
    lo_used: list[Pivot] = []

    for _ in range(max(refit_rounds, 1)):
        hi_used = [p for p in highs if p.bar_idx <= fit_end]
        lo_used = [p for p in lows if p.bar_idx <= fit_end]
        if len(hi_used) < 2 or len(lo_used) < 2:
            return None
        sl_hi, b_hi = np.polyfit(
            np.array([p.bar_idx for p in hi_used], float),
            np.array([p.price for p in hi_used], float), 1,
        )
        sl_lo, b_lo = np.polyfit(
            np.array([p.bar_idx for p in lo_used], float),
            np.array([p.price for p in lo_used], float), 1,
        )
        first = int(min(hi_used[0].bar_idx, lo_used[0].bar_idx))
        margin = break_atr * atr
        new_end = len(window) - 1
        for i in range(first + min_bars, len(window)):
            px = float(c.iloc[i])
            if px > sl_hi * i + b_hi + margin or px < sl_lo * i + b_lo - margin:
                new_end = i - 1
                break
        if new_end == fit_end:
            break
        fit_end = max(new_end, first + min_bars)

    highs, lows = hi_used, lo_used
    start_idx = int(min(highs[0].bar_idx, lows[0].bar_idx))
    end_idx = fit_end
    bars = end_idx - start_idx
    if bars < min_bars:
        return None

    def up_at(i: float) -> float:
        return sl_hi * i + b_hi

    def lo_at(i: float) -> float:
        return sl_lo * i + b_lo

    # Formasyonun başındaki ve sonundaki genişlik: yakınsama/ıraksama
    # ölçüsü VE ölçülen-hareket hedefinin dayanağı.
    w0 = up_at(start_idx) - lo_at(start_idx)
    w1 = up_at(end_idx) - lo_at(end_idx)
    if w0 <= 0 or w1 <= 0:
        return None

    kind, direction = _classify(float(sl_hi), float(sl_lo), norm, flat_slope)
    family = "kama" if "kama" in kind else ("genisleyen" if kind == "genisleyen" else "ucgen")
    need_a, need_b = _MIN_TOUCH[family]

    def touches(ps: list[Pivot], line, side: str) -> tuple[BoundaryTouchPoint, ...]:
        out, k = [], 0
        for p in ps:
            if abs(p.price - line(p.bar_idx)) <= touch_atr * atr:
                k += 1
                out.append(BoundaryTouchPoint(p.bar_time, float(p.price), k, side))
        return tuple(out)

    up_t = touches(highs, up_at, "upper")
    lo_t = touches(lows, lo_at, "lower")
    if max(len(up_t), len(lo_t)) < need_a or min(len(up_t), len(lo_t)) < need_b:
        return None

    # Tepe noktası (apex): iki doğrunun kesiştiği yer — yalnızca yakınsıyorsa
    apex = None
    if sl_hi != sl_lo:
        xa = (b_lo - b_hi) / (sl_hi - sl_lo)
        if start_idx < xa <= end_idx + lookback:
            pos = int(round(xa))
            t_ap = window.index[pos] if pos <= end_idx else window.index[-1]
            apex = (t_ap, float(up_at(xa)))

    t0, t1 = window.index[start_idx], window.index[end_idx]
    upper = ((t0, float(up_at(start_idx))), (t1, float(up_at(end_idx))))
    lower = ((t0, float(lo_at(start_idx))), (t1, float(lo_at(end_idx))))

    # Kırılım: son barlarda sınırın KAPANIŞLA aşılması
    # Kırılım, formasyonun BİTTİĞİ yerden sonra ve ATR payı kadar
    # DECİSİF olmalı; salınımın sınıra değmesi kırılım değildir.
    brk, side, state = None, "", "olusuyor"
    margin = break_atr * atr
    for i in range(end_idx + 1, len(window)):
        px = float(c.iloc[i])
        if px > up_at(i) + margin:
            brk, side, state = (window.index[i], px), "upper", "onaylandi"
            break
        if px < lo_at(i) - margin:
            brk, side, state = (window.index[i], px), "lower", "onaylandi"
            break
    if brk is None and apex is not None and window.index[end_idx] > apex[0]:
        state = "suresi_doldu"

    # Ölçülen hareket: formasyonun BAŞLANGIÇ genişliği, kırılımdan yansıtılır
    target = None
    if brk is not None:
        target = brk[1] + w0 if side == "upper" else brk[1] - w0

    vol_first = float(window["volume"].iloc[start_idx : start_idx + max(bars // 3, 1)].mean())
    vol_last = float(window["volume"].iloc[end_idx - max(bars // 3, 1) : end_idx + 1].mean())
    contraction = vol_last / vol_first if vol_first > 0 else float("nan")

    anchor = brk[0] if brk else t1
    bars_ago = int((df.index > anchor).sum())

    return ConvergingPattern(
        kind=kind, direction=direction, upper=upper, lower=lower,
        upper_touches=up_t, lower_touches=lo_t, apex=apex,
        breakout=brk, breakout_side=side, target=target, state=state,
        width_change_pct=float((w1 - w0) / w0), vol_contraction=contraction,
        bars=int(bars), bars_ago=bars_ago,
    )
