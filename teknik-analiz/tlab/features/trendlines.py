"""Non-repainting trend çizgisi (trendline) tespiti ve bar-bar izleme.

DİKKAT (seçim kriterleri hakkında): min_touches ve max_lines, HANGİ
aday çizgilerin döndürüleceğine karar verir; bu karar df büyüdükçe
DEĞİŞEBİLİR (bir aday zamanla daha çok temas biriktirip öne çıkabilir).
Bu, o çizginin KENDİ geometrisinin/touches geçmişinin sonradan
değişmesi anlamına GELMEZ — yalnızca "şu an hangi adaylar öne çıkıyor"
sorusunun cevabı, tıpkı canlı bir tarayıcıda olduğu gibi, zamanla
netleşir. Var olan mevcut repaint_test/Line altyapısı bu "aday havuzu"
deseni için tasarlanmadığından (bkz. tests/test_trendlines.py), bunun
repaint-safety'si `touches`/`broken_at`in tekil bir (p1,p2) çizgi için
prefix-tutarlılığı üzerinden doğrudan test edilir.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from tlab.features.swings import Pivot
from tlab.features.volatility import atr

TrendlineKind = Literal["resistance", "support"]


@dataclass(frozen=True)
class Trendline:
    """p1'den p2'ye çizilen, index-tabanlı (value_at(i)=slope*i+intercept) doğru.

    touches: temas eden bar indeksleri (yalnızca BÜYÜR, extend-only).
    broken_at: kırılımın onaylandığı bar (bir kez atanır, bir daha değişmez).
    created_idx: çizginin var olmaya başladığı bar (p2.confirmed_idx) — bu
    bardan ÖNCEKİ hiçbir bar için touches/broken_at değerlendirilmez.
    """

    p1: Pivot
    p2: Pivot
    slope: float
    intercept: float
    kind: TrendlineKind
    touches: tuple[int, ...]
    broken_at: int | None
    created_idx: int

    def value_at(self, idx: int) -> float:
        return self.slope * idx + self.intercept


def build_trendlines(
    df: pd.DataFrame,
    pivots: list[Pivot],
    kind: TrendlineKind,
    min_touches: int = 2,
    tol_atr: float = 0.3,
    confirm_bars: int = 1,
    atr_period: int = 14,
    max_lines: int | None = None,
) -> list[Trendline]:
    """Aynı türden pivot çiftlerinden (kind="resistance" -> high pivotlar,
    "support" -> low pivotlar) aday çizgiler kurar; her biri oluştuğu bardan
    (p2.confirmed_idx) itibaren df'nin sonuna kadar bar-bar izlenir.

    Bir barda TEMAS: ilgili fiyat (resistance->high, support->low) çizgiye
    tol_atr*ATR içinde VE kapanış çizgiyi henüz geçmemiş. KIRILIM: kapanış
    çizginin ötesinde `confirm_bars` ardışık barda — broken_at bu serinin
    SON barıdır (kırılım, ardışık bar sayısı tamamlanana kadar onaylanmaz).
    Kırılan çizgi için izleme durur (touches/broken_at donar).

    min_touches'a ulaşmayan çizgiler elenir. max_lines verilirse, kırılmamış
    + en çok temaslı + en uzun süreli öncelikli sıralamayla üstten kesilir.
    """
    if kind not in ("resistance", "support"):
        raise ValueError("kind 'resistance' ya da 'support' olmalı")
    pivot_kind: Literal["high", "low"] = "high" if kind == "resistance" else "low"

    same_kind = sorted((p for p in pivots if p.kind == pivot_kind), key=lambda p: p.bar_idx)
    n = len(df)
    atr_series = atr(df, atr_period)
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    close = df["close"].to_numpy()

    lines: list[Trendline] = []
    for i, p1 in enumerate(same_kind):
        for p2 in same_kind[i + 1 :]:
            slope = (p2.price - p1.price) / (p2.bar_idx - p1.bar_idx)
            intercept = p1.price - slope * p1.bar_idx
            created_idx = p2.confirmed_idx
            if created_idx >= n:
                continue

            touches: list[int] = []
            broken_at: int | None = None
            break_streak = 0

            for t in range(created_idx, n):
                a = atr_series.iloc[t]
                if pd.isna(a):
                    continue
                line_val = slope * t + intercept
                tol = tol_atr * a

                beyond = close[t] > line_val if kind == "resistance" else close[t] < line_val
                near = (
                    abs(high[t] - line_val) <= tol
                    if kind == "resistance"
                    else abs(low[t] - line_val) <= tol
                )

                if beyond:
                    break_streak += 1
                    if break_streak >= confirm_bars:
                        broken_at = t
                        break
                else:
                    break_streak = 0
                    if near:
                        touches.append(t)

            if len(touches) < min_touches:
                continue

            lines.append(
                Trendline(
                    p1=p1,
                    p2=p2,
                    slope=slope,
                    intercept=intercept,
                    kind=kind,
                    touches=tuple(touches),
                    broken_at=broken_at,
                    created_idx=created_idx,
                )
            )

    if max_lines is not None:
        lines = _select_top(lines, max_lines)
    return lines


def _select_top(lines: list[Trendline], max_lines: int) -> list[Trendline]:
    """Kırılmamış, en çok temaslı, en uzun süreli çizgiler öncelikli."""

    def sort_key(ln: Trendline) -> tuple[int, int, int]:
        broken_rank = 0 if ln.broken_at is None else 1
        last_bar = ln.broken_at if ln.broken_at is not None else (
            ln.touches[-1] if ln.touches else ln.created_idx
        )
        duration = last_bar - ln.created_idx
        return (broken_rank, -len(ln.touches), -duration)

    return sorted(lines, key=sort_key)[:max_lines]
