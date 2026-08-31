"""Walk-forward eşitlik testi: repaint/lookahead ihlallerini tespit eder.

Yöntem: Tam seri (`full`) ile her kesim noktasında hesaplanan kesik seri
(`partial`) karşılaştırılır. Kesik serinin kesim anına kadar ürettiği HER
ŞEY (signal, level, line, box, polygon), zaten o ana kadarki veriyle
hesaplanabilir olduğu için, tam seri de kesim anına kadar AYNI öğeleri
BİREBİR üretmek zorundadır — ne eksik, ne fazla, ne değişmiş. Aksi halde
(tam seride kesim anından önceki bir bara ait, kesik seride bulunmayan bir
öğe varsa) bu, "bilgi sonradan geriye yazıldı" anlamına gelir — klasik
repaint hatası. Box/Polygon için tek istisna "extend-only" büyümedir
(t1 ilerleyebilir, ama t0/low/high değişemez).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable

import pandas as pd

from tlab.core.indicator import BaseIndicator, UniverseIndicator
from tlab.core.types import Signal

_TOL = 1e-9


@dataclass
class RepaintReport:
    passed: bool
    mismatches: list[str] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)


def _num_close(a: Any, b: Any) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(float(a), float(b), abs_tol=_TOL, rel_tol=_TOL)
    return bool(a == b)


def _payload_equal(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return a.keys() == b.keys() and all(_num_close(v, b[k]) for k, v in a.items())


def _signal_equal(a: Signal, b: Signal) -> bool:
    return (
        a.bar_time == b.bar_time
        and a.detected_at == b.detected_at
        and a.direction == b.direction
        and a.state == b.state
        and _payload_equal(a.payload, b.payload)
    )


def _diff_signals(
    cut: int,
    cut_time: pd.Timestamp,
    partial: list[Signal],
    full_upto: list[Signal],
    mismatches: list[str],
) -> None:
    unmatched_partial = list(partial)
    unmatched_full = list(full_upto)
    for sig in partial:
        match = next((f for f in unmatched_full if _signal_equal(sig, f)), None)
        if match is not None:
            unmatched_full.remove(match)
            unmatched_partial.remove(sig)

    for sig in unmatched_partial:
        mismatches.append(
            f"[cut={cut}, t={cut_time}] Sinyal kesikte var, tamda yok/değişmiş "
            f"(sonradan farklılaştı — repaint): bar_time={sig.bar_time}, "
            f"detected_at={sig.detected_at}, direction={sig.direction}, state={sig.state}"
        )
    for sig in unmatched_full:
        mismatches.append(
            f"[cut={cut}, t={cut_time}] Sinyal tamda var ama kesikte yok "
            f"(bar sonradan ortaya çıktı — repaint): bar_time={sig.bar_time}, "
            f"detected_at={sig.detected_at}, direction={sig.direction}, state={sig.state}"
        )


def _diff_dated(
    cut: int,
    cut_time: pd.Timestamp,
    partial: list[Any],
    full_upto: list[Any],
    key_fn: Callable[[Any], Any],
    label: str,
    mismatches: list[str],
) -> None:
    unmatched_full = list(full_upto)
    for item in partial:
        match = next((f for f in unmatched_full if key_fn(f) == key_fn(item)), None)
        if match is None:
            mismatches.append(f"[cut={cut}, t={cut_time}] {label} kesikte var, tamda yok: {key_fn(item)}")
        else:
            unmatched_full.remove(match)
    for item in unmatched_full:
        mismatches.append(
            f"[cut={cut}, t={cut_time}] {label} tamda var, kesikte yok "
            f"(sonradan ortaya çıktı — repaint): {key_fn(item)}"
        )


def _diff_extend_only(
    cut: int,
    cut_time: pd.Timestamp,
    partial: list[Any],
    full_upto_by_key: dict[Any, Any],
    key_fn: Callable[[Any], Any],
    bounds_fn: Callable[[Any], tuple[Any, float, float]],
    label: str,
    mismatches: list[str],
) -> None:
    seen_full_keys = set()
    for item in partial:
        key = key_fn(item)
        match = full_upto_by_key.get(key)
        if match is None:
            mismatches.append(f"[cut={cut}, t={cut_time}] {label} kesikte var, tamda yok: {key}")
            continue
        seen_full_keys.add(key)
        t1_p, low_p, high_p = bounds_fn(item)
        t1_f, low_f, high_f = bounds_fn(match)
        if t1_f < t1_p:
            mismatches.append(f"[cut={cut}, t={cut_time}] {label} t1 küçüldü (repaint şüphesi): {key}")
        if not (_num_close(low_p, low_f) and _num_close(high_p, high_f)):
            mismatches.append(f"[cut={cut}, t={cut_time}] {label} low/high değişti (repaint şüphesi): {key}")
    for key in full_upto_by_key:
        if key not in seen_full_keys:
            mismatches.append(
                f"[cut={cut}, t={cut_time}] {label} tamda var, kesikte yok "
                f"(sonradan ortaya çıktı — repaint): {key}"
            )


def repaint_test(
    indicator: BaseIndicator,
    df: pd.DataFrame,
    cut_points: list[int] | None = None,
    tail: int = 60,
    stride: int = 1,
    context: dict[str, pd.DataFrame] | None = None,
) -> RepaintReport:
    """indicator'ü tam seri ve seçilen kesim noktalarında çalıştırıp karşılaştırır.

    cut_points verilmezse, son `tail` barın her biri (stride ile seyreltilerek)
    kesim noktası olarak kullanılır. indicator compute'u pahalıysa stride
    büyütülerek kontrol edilen kesim sayısı azaltılabilir.

    `context` verilirse (Faz 5: `RelativeMomentumPair` gibi ikinci bir seri
    alan indikatörler için), içindeki HER DataFrame de `df` ile AYNI kesim
    ANINA (cut_time — TARİHE göre, pozisyona göre DEĞİL, çünkü iki serinin
    bar sayısı farklı olabilir) kesilerek indikatöre verilir. Aksi halde
    context tam bırakılıp yalnızca `df` kesilirse, indikatör context'teki
    GELECEK barları görebilir — sessiz bir lookahead. `df` ile `context`
    aynı cut'ta kesilmezse walk-forward eşitliği anlamsızlaşır."""
    n = len(df)
    if cut_points is None:
        start = max(1, n - tail)
        cut_points = list(range(start, n, max(1, stride)))

    full = indicator(df, context)
    mismatches: list[str] = []
    checked_cuts = 0

    for cut in cut_points:
        if cut < 1 or cut > n:
            continue
        partial_df = df.iloc[:cut]
        cut_time = partial_df.index[-1]
        partial_context = (
            {key: value.loc[value.index <= cut_time] for key, value in context.items()}
            if context is not None
            else None
        )
        partial = indicator(partial_df, partial_context)
        checked_cuts += 1

        full_signals_upto = [s for s in full.signals if s.detected_at <= cut_time]
        _diff_signals(cut, cut_time, partial.signals, full_signals_upto, mismatches)

        full_levels_upto = [lv for lv in full.levels if lv.start is None or lv.start <= cut_time]
        _diff_dated(
            cut, cut_time, partial.levels, full_levels_upto,
            key_fn=lambda x: (x.price, x.label, x.start), label="Level", mismatches=mismatches,
        )

        full_lines_upto = [ln for ln in full.lines if ln.points and ln.points[0][0] <= cut_time]
        _diff_dated(
            cut, cut_time, partial.lines, full_lines_upto,
            key_fn=lambda x: (x.points, x.label), label="Line", mismatches=mismatches,
        )

        full_boxes_upto = {(b.t0, b.label): b for b in full.boxes if b.t0 <= cut_time}
        _diff_extend_only(
            cut, cut_time, partial.boxes, full_boxes_upto,
            key_fn=lambda x: (x.t0, x.label),
            bounds_fn=lambda x: (x.t1, x.low, x.high),
            label="Box", mismatches=mismatches,
        )

        full_polys_upto = {
            (p.points[0][0], p.label): p for p in full.polygons if p.points and p.points[0][0] <= cut_time
        }
        _diff_extend_only(
            cut, cut_time, partial.polygons, full_polys_upto,
            key_fn=lambda x: (x.points[0][0], x.label),
            bounds_fn=lambda x: (
                max(t for t, _ in x.points),
                min(p for _, p in x.points),
                max(p for _, p in x.points),
            ),
            label="Polygon", mismatches=mismatches,
        )

    return RepaintReport(
        passed=not mismatches,
        mismatches=mismatches,
        stats={"n_bars": n, "cuts_checked": checked_cuts},
    )


def universe_repaint_test(
    indicator: UniverseIndicator,
    universe: dict[str, pd.DataFrame],
    index_df: pd.DataFrame,
    cut_dates: list[pd.Timestamp] | None = None,
    tail: int = 20,
) -> RepaintReport:
    """`repaint_test`'in Faz 8D "universe" kategorisi karşılığı — TEK bir
    df yerine `universe`'in HER df'i + `index_df` AYNI `cut_time`'da (tarihe
    göre) kesilir, `compute_universe` yeniden çalıştırılır. Rank_pct her
    barda YALNIZCA o bardaki (t VE ÖNCESİ verilerle hesaplanmış) skorlara
    bağlı olduğu için — bkz. `alpha_rank.py`/`momentum_rank.py` docstring'i
    — kesik ⊆ tam eşitliği (`repaint_test` ile AYNI mantık) burada da geçerli
    OLMALIDIR: bir sembolün kesikte ürettiği HER sinyal, tam koşunun o ana
    kadar ürettiği sinyallerin İÇİNDE olmalı. Kesik evrende bir sembolün HİÇ
    görünmemesi (ör. `min_history_bars` o kadar geriye gitmiyorsa) repaint
    DEĞİLDİR — yalnızca o sembol kesikte KARŞILAŞTIRILMAZ (dışlanmaz, hata
    sayılmaz)."""
    if cut_dates is None:
        all_dates = index_df.index
        start = max(0, len(all_dates) - tail)
        cut_dates = list(all_dates[start::max(1, tail // 10) or 1])

    full = indicator(universe, index_df)
    mismatches: list[str] = []
    checked = 0

    for cut_time in cut_dates:
        partial_index = index_df.loc[index_df.index <= cut_time]
        partial_universe = {
            sym: df.loc[df.index <= cut_time]
            for sym, df in universe.items()
            if (df.index <= cut_time).any()
        }
        if len(partial_index) < 2 or not partial_universe:
            continue
        partial = indicator(partial_universe, partial_index)
        checked += 1

        for symbol, partial_result in partial.items():
            full_result = full.get(symbol)
            if full_result is None:
                mismatches.append(
                    f"[cut={cut_time}] {symbol} kesikte sonuç üretti, tam koşuda HİÇ YOK"
                )
                continue
            partial_signals = partial_result.signals
            full_signals_upto = [s for s in full_result.signals if s.detected_at <= cut_time]
            _diff_signals(0, cut_time, partial_signals, full_signals_upto, mismatches)

    return RepaintReport(
        passed=not mismatches, mismatches=mismatches, stats={"cuts_checked": checked},
    )


def allocation_repaint_test(
    compute_fn: Callable[[list[pd.Timestamp]], dict[pd.Timestamp, dict[str, float]]],
    recompute_dates: list[pd.Timestamp],
) -> RepaintReport:
    """Faz 10'un PERİYODİK (adım-fonksiyonu) `allocation.py::
    periodic_handcraft_schedule` gibi çıktıları için `universe_repaint_test`
    ile AYNI "kesik ⊆ tam" mantığı — ama bir SERİ yerine {recompute_tarihi:
    ağırlıklar} sözlüğü üzerinde: her kesim noktasında (yalnızca o ana
    kadarki recompute noktaları `compute_fn`'e verilir) üretilen ağırlıklar,
    TAM koşunun o tarihte ürettiği ağırlıkla BİREBİR eşleşmeli (bkz. `docs/
    spec/tlab_10_portfolio.md`, "Durum makinesi")."""
    full = compute_fn(recompute_dates)
    mismatches: list[str] = []
    checked = 0

    for cut_i in range(1, len(recompute_dates) + 1):
        cut_dates = recompute_dates[:cut_i]
        partial = compute_fn(cut_dates)
        checked += 1
        for dt in cut_dates:
            partial_w = partial.get(dt)
            full_w = full.get(dt)
            if partial_w is None and full_w is None:
                continue
            if partial_w is None or full_w is None or not _weights_close(partial_w, full_w):
                mismatches.append(
                    f"[cut={cut_dates[-1]}] {dt} tarihindeki ağırlık kesimde değişti "
                    f"(partial={partial_w}, full={full_w})"
                )

    return RepaintReport(
        passed=not mismatches, mismatches=mismatches, stats={"cuts_checked": checked},
    )


def _weights_close(a: dict[str, float], b: dict[str, float]) -> bool:
    if set(a) != set(b):
        return False
    return all(math.isclose(a[k], b[k], abs_tol=_TOL, rel_tol=_TOL) for k in a)
