"""Bayrak / flama — direk + konsolidasyon + kırılım.

Kullanıcının şikâyeti (2026-09-05): *"aşağıdan yukarı gelen çizgi yarım
kalmış... mumları en azından çizginin başladığı dibinden bir 5-6 mum
öncesinden başlatmak gerekiyordu... kırılımda ve onayda sinyal vermesi
gerekiyordu... fakat taa hedefe geldiği noktada al yazıyor"*.

Üçünün de karşılığı burada:
  - Direk, BAŞLANGIÇ pivotundan ölçülür ve grafik penceresi direğin
    başlangıcından geriye pay bırakacak şekilde raporlanır (`view_start`).
  - Sinyal KIRILIM barında doğar.
  - Hedef ayrı bir seviyedir, sinyalin yeri değildir.

Bulkowski: bayrak/flama en fazla 3 hafta sürer; direk dik ve hacimli
olmalı; konsolidasyon boyunca hacim daralır.

Hesap yapar, çizmez.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from tlab.features.swings import alternate_pivots, find_pivots


@dataclass(frozen=True)
class PoleFlag:
    direction: str                  # "long" | "short"
    shape: str                      # "bayrak" | "flama"
    pole_start: tuple[pd.Timestamp, float]
    pole_end: tuple[pd.Timestamp, float]
    upper: tuple[tuple[pd.Timestamp, float], tuple[pd.Timestamp, float]]
    lower: tuple[tuple[pd.Timestamp, float], tuple[pd.Timestamp, float]]
    breakout: tuple[pd.Timestamp, float] | None
    target: float | None
    state: str                      # "olusuyor" | "onaylandi" | "suresi_doldu"
    pole_pct: float
    flag_bars: int
    vol_contraction: float          # konsolidasyon hacmi / direk hacmi
    view_start: pd.Timestamp        # grafiğin başlaması gereken bar
    bars_ago: int | None
    # docs/KALAN_ISLER.md madde 2.3 -- Bulkowski'nin "High and Tight Flag"
    # ayrımı (direk ≥%90 KISA sürede). `shape` (kanal geometrisi) ile
    # ORTOGONAL, ADDİTİF bir bayrak -- varsayılan False, eski çağıranları
    # bozmaz.
    is_htf: bool = False

    def __post_init__(self) -> None:
        if self.direction not in ("long", "short"):
            raise ValueError(f"yön 'long'/'short' olmalı — alınan {self.direction!r}")


def detect_pole_flag(
    df: pd.DataFrame,
    *,
    left: int = 3,
    right: int = 3,
    min_pole_pct: float = 0.12,
    max_flag_bars: int = 15,        # Bulkowski: en fazla ~3 hafta
    min_flag_bars: int = 4,
    max_retrace: float = 0.50,
    view_pad_bars: int = 6,         # kullanıcı: "5-6 mum öncesinden"
) -> PoleFlag | None:
    if len(df) < 60:
        return None

    zig = alternate_pivots(find_pivots(df, left=left, right=right))
    if len(zig) < 3:
        return None

    for i in range(len(zig) - 2, -1, -1):
        p0, p1 = zig[i], zig[i + 1]
        pole = (p1.price - p0.price) / max(p0.price, 1e-9)
        if abs(pole) < min_pole_pct:
            continue
        direction = "long" if pole > 0 else "short"

        flag_slice = df.iloc[p1.confirmed_idx : p1.confirmed_idx + max_flag_bars + 1]
        if len(flag_slice) < min_flag_bars:
            continue

        # Konsolidasyon direğin en fazla yarısını geri almalı
        depth = abs(float(flag_slice["close"].min() if direction == "long"
                          else flag_slice["close"].max()) - p1.price)
        if depth / max(abs(p1.price - p0.price), 1e-9) > max_retrace:
            continue

        hi = flag_slice["high"].to_numpy()
        lo = flag_slice["low"].to_numpy()
        idx = np.arange(len(flag_slice), dtype=float)
        sl_hi, b_hi = np.polyfit(idx, hi, 1)
        sl_lo, b_lo = np.polyfit(idx, lo, 1)

        # Flama: sınırlar YAKINSAR. Bayrak: kabaca paralel.
        w0 = (sl_hi * 0 + b_hi) - (sl_lo * 0 + b_lo)
        w1 = (sl_hi * (len(idx) - 1) + b_hi) - (sl_lo * (len(idx) - 1) + b_lo)
        shape = "flama" if w1 < w0 * 0.72 else "bayrak"

        t_f0, t_f1 = flag_slice.index[0], flag_slice.index[-1]
        upper = ((t_f0, float(b_hi)), (t_f1, float(sl_hi * (len(idx) - 1) + b_hi)))
        lower = ((t_f0, float(b_lo)), (t_f1, float(sl_lo * (len(idx) - 1) + b_lo)))

        pole_vol = float(df["volume"].iloc[p0.bar_idx : p1.bar_idx + 1].mean())
        flag_vol = float(flag_slice["volume"].mean())
        contraction = flag_vol / pole_vol if pole_vol > 0 else float("nan")

        after = df.iloc[p1.confirmed_idx + len(flag_slice) :]
        brk, state = None, "olusuyor"
        if len(after):
            lvl = upper[1][1] if direction == "long" else lower[1][1]
            hit = after[after["close"] > lvl] if direction == "long" else after[after["close"] < lvl]
            if len(hit):
                brk = (hit.index[0], float(hit.iloc[0]["close"]))
                state = "onaylandi"
            elif len(after) > max_flag_bars * 2:
                state = "suresi_doldu"

        # Ölçülen hareket: direk boyu, kırılım noktasından yansıtılır
        pole_h = abs(p1.price - p0.price)
        base = brk[1] if brk else (upper[1][1] if direction == "long" else lower[1][1])
        target = base + pole_h if direction == "long" else base - pole_h

        # Kullanıcı isteği: mumlar direğin başlangıcından ÖNCE başlasın
        vs_idx = max(0, p0.bar_idx - view_pad_bars)
        anchor = brk[0] if brk else t_f1
        bars_ago = int((df.index > anchor).sum())

        return PoleFlag(
            direction=direction, shape=shape,
            pole_start=(p0.bar_time, float(p0.price)),
            pole_end=(p1.bar_time, float(p1.price)),
            upper=upper, lower=lower, breakout=brk, target=target, state=state,
            pole_pct=float(pole), flag_bars=int(len(flag_slice)),
            vol_contraction=contraction, view_start=df.index[vs_idx], bars_ago=bars_ago,
        )
    return None
