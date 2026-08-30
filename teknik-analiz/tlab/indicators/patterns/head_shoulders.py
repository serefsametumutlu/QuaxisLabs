"""Omuz-Baş-Omuz (OBO, tepe) / Ters Omuz-Baş-Omuz (TOBO, dip) tarayıcı — Faz 8B.

`tlab/features/hs_pattern.py::find_hs`'in ince sarmalayıcısı. Girdi zigzag
`swings.alternate_pivots` ile üretilir — HER pivot ZATEN kesinleşmiştir
(`structure.golden_zone`/`structure.swing_fib_abcd` ile AYNI mimari, "top-N"
tarzı bir aday-havuzu seçimi YOK, `find_hs` her 5'li pencereyi bağımsız
değerlendirir). Bu yüzden `wedge.py`'nin aksine generic `Registry.register()`'a
TEMİZ kaydolur.

Kırılım = boyun çizgisinin (`neckline_value_at`) kapanışla kırılması; hedef
= `HSPattern.target` (ölçülü hareket, boyun + baş derinliği). Geçersizlik
= kapanışın sağ omuz EKSTREMİNİN ötesine geçmesi (TOBO: l3.price altına,
OBO: l3.price üstüne — klasik kural: sağ omuz kırılırsa boyun hiç test
edilmeden formasyon geçersizdir).

**GERÇEK bulgu (bu modül yazılırken bulundu)**: PENDING doğum barı olarak
`HSPattern.created_idx` (= `hs_pattern.py`'nin KENDİ sözleşmesine göre
`l3.confirmed_idx`) DEĞİL, `hs.l3.finalized_idx` kullanılır. Aradaki fark
ince ama gerçek: `l3.confirmed_idx`, l3'ün yerel bir ekstrem olarak
ONAYLANDIĞI barı verir — ama `alternate_pivots`'un zigzag'e onu FİİLEN
EKLEMESİ (bir daha daha ekstrem bir pivotla İPTAL EDİLEMEYECEĞİ
kesinleştiğinde) ancak `finalized_idx`'te olur (`GoldenZoneIndicator`'ın
"A onay barında DEĞİL finalized_idx'inde doğar" kararıyla AYNI gerekçe).
`created_idx`'i doğrudan kullanmak, walk-forward'da (df kesilip
`alternate_pivots` yeniden çalıştırıldığında l3 henüz zigzag'e HİÇ
girmeyeceği için) gerçek bir repaint'e yol açardı — `tests/test_patterns/
test_head_shoulders.py` bunu hedefli bir senaryoyla doğrular."""

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
    Signal,
    Timeframe,
)
from tlab.features.hs_pattern import HSKind, HSPattern, find_hs, neckline_value_at
from tlab.features.swings import alternate_pivots, find_pivots
from tlab.features.volatility import atr

HSFilter = Literal["tobo", "obo", "both"]

_LABEL_TR: dict[HSKind, str] = {"tobo": "TOBO", "obo": "OBO"}


@dataclass(frozen=True)
class HeadShouldersParams(BaseParams):
    left: int = 3
    right: int = 3
    kind: HSFilter = "both"
    sym_tol: float = 0.5
    neck_slope_max: float = 0.01
    shoulder_time_ratio: tuple[float, float] = (0.5, 2.0)
    confirm_bars: int = 1
    vol_k: float = 1.2
    max_bars_to_confirm_mult: float = 3.0
    retest_tol_atr: float = 0.3
    atr_period: int = 14


class HeadShouldersIndicator(BaseIndicator):
    meta = IndicatorMeta(
        name="patterns.head_shoulders",
        version="0.1.0",
        category="patterns",
        description="Omuz-Baş-Omuz (OBO) / Ters Omuz-Baş-Omuz (TOBO) formasyon tarayıcı.",
        supported_timeframes=(Timeframe.D1, Timeframe.H4),
    )

    def __init__(self, params: HeadShouldersParams | None = None) -> None:
        self.params: HeadShouldersParams = params or HeadShouldersParams()

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        p = self.params
        n = len(df)
        zigzag = alternate_pivots(find_pivots(df, p.left, p.right))
        atr_series = atr(df, p.atr_period)
        close = df["close"].to_numpy()
        volume = df["volume"].to_numpy()

        kinds: tuple[HSKind, ...] = ("tobo", "obo") if p.kind == "both" else (p.kind,)
        signals: list[Signal] = []
        levels: list[Level] = []
        lines: list[Line] = []
        markers: list[Marker] = []
        last_state: dict[str, dict] = {}

        for kind in kinds:
            candidates = find_hs(
                zigzag, kind=kind, sym_tol=p.sym_tol, neck_slope_max=p.neck_slope_max,
            )
            for hs in candidates:
                # NOT: `hs.created_idx` (=hs.l3.confirmed_idx) BİLEREK DEĞİL,
                # `hs.l3.finalized_idx` kullanılıyor — l3, zigzag'e SADECE
                # finalized_idx'inde (kendisinden SONRA zıt türde bir pivot
                # KESİNLEŞTİĞİNDE, `alternate_pivots` sayesinde artık daha
                # ekstrem bir pivotla İPTAL EDİLEMEYECEĞİ kesinleştiğinde)
                # girer; `confirmed_idx` yalnızca "yerel ekstrem olarak
                # ONAYLANDI" demektir, o bar ile finalized_idx arasında HÂLÂ
                # daha ekstrem bir pivotla değiştirilebilir (GoldenZoneIndicator
                # "A onay barında DEĞİL finalized_idx'inde doğar" kararıyla
                # AYNI gerekçe). `hs.created_idx`'i doğrudan kullanmak, walk-
                # forward'da (df kesildiğinde `alternate_pivots` l3'ü henüz
                # zigzag'e HİÇ SOKMAYACAĞI için) gerçek bir repaint'e yol
                # açardı — bu, bu modülü yazarken bulunan GERÇEK bir hataydı.
                born_idx = hs.l3.finalized_idx
                if born_idx is None or born_idx >= n:
                    continue
                left_span = hs.head.bar_idx - hs.l1.bar_idx
                right_span = hs.l3.bar_idx - hs.head.bar_idx
                if left_span <= 0 or right_span <= 0:
                    continue
                ratio = right_span / left_span
                if not (p.shoulder_time_ratio[0] <= ratio <= p.shoulder_time_ratio[1]):
                    continue

                pattern_id = f"{kind}_{hs.l1.bar_idx}_{hs.head.bar_idx}_{hs.l3.bar_idx}"
                direction: Direction = "long" if kind == "tobo" else "short"
                shoulder_extreme = hs.l3.price

                def _invalidation(
                    t: int, _hi: float, _lo: float,
                    _extreme: float = shoulder_extreme, _dir: str = direction,
                ) -> bool:
                    return close[t] < _extreme if _dir == "long" else close[t] > _extreme

                def _break_line(t: int, _hs: HSPattern = hs) -> float:
                    return neckline_value_at(_hs, t)

                max_bars_to_confirm = int(p.max_bars_to_confirm_mult * (left_span + right_span))
                cfg = PatternTrackingConfig(
                    pattern_id=pattern_id, pattern_name=kind, direction=direction,
                    break_line=_break_line, target=hs.target,
                    confirm_bars=p.confirm_bars, max_bars_to_confirm=max_bars_to_confirm,
                    retest_tol_atr=p.retest_tol_atr, atr_series=atr_series, score=0.65,
                    invalidation_check=_invalidation,
                    extra_payload={"depth": hs.depth},
                )
                pattern_signals = track_breakout_pattern(df, born_idx, cfg)

                confirm_sig = next(
                    (s for s in pattern_signals if s.payload["event"].endswith("_confirmed")), None
                )
                if confirm_sig is not None:
                    right_shoulder_vol = float(
                        volume[hs.h2.bar_idx : hs.l3.bar_idx + 1].mean()
                    ) if hs.l3.bar_idx > hs.h2.bar_idx else float(volume[hs.h2.bar_idx])
                    breakout_idx = df.index.get_loc(confirm_sig.bar_time)
                    breakout_vol = volume[breakout_idx]
                    confirm_sig.payload["volume_profile_ok"] = bool(
                        right_shoulder_vol > 0 and breakout_vol >= p.vol_k * right_shoulder_vol
                    )

                signals.extend(pattern_signals)

                lines.append(
                    Line(
                        points=((hs.h1.bar_time, hs.h1.price), (hs.h2.bar_time, hs.h2.price)),
                        label=f"{pattern_id}_neckline", style="pattern_boundary", extend_right=True,
                    )
                )
                levels.append(
                    Level(
                        price=hs.target, label=f"{pattern_id}_target", style="pattern_target",
                        start=hs.l3.bar_time, end=level_end_from_signals(pattern_signals),
                    )
                )
                markers.append(
                    Marker(t=hs.l1.bar_time, price=hs.l1.price, text="SOL OMUZ", kind="hs_shoulder")
                )
                markers.append(
                    Marker(t=hs.head.bar_time, price=hs.head.price, text="BAŞ", kind="hs_head")
                )
                markers.append(
                    Marker(t=hs.l3.bar_time, price=hs.l3.price, text="SAĞ OMUZ", kind="hs_shoulder")
                )

                last_sig = pattern_signals[-1]
                markers.append(
                    Marker(
                        t=last_sig.bar_time, price=close[df.index.get_loc(last_sig.bar_time)],
                        text=marker_text(_LABEL_TR[kind], last_sig.payload["event"], kind),
                        kind=f"pattern_{last_sig.state}",
                    )
                )
                last_state[pattern_id] = {
                    "kind": kind, "direction": direction, "state": last_sig.state,
                    "event": last_sig.payload["event"], "target": hs.target,
                }

        return IndicatorResult(
            indicator=self.meta.name, version=self.meta.version, params_hash=params_hash(p),
            symbol="", timeframe=Timeframe.D1,
            signals=signals, levels=levels, lines=lines, markers=markers,
            series={"volume": df["volume"]}, series_layout={"hacim": ["volume"]},
            last_state=last_state,
        )
