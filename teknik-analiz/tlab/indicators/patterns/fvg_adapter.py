"""`patterns.breakout_fvg` -> `BoundaryPattern`.

Zincir: KONSOLİDASYON → KIRILIM → FVG → RETEST → ONAY. Grafikte
karşılığı:
  * konsolidasyon kutusunun KIRILAN kenarı  -> tek `BoundaryLine`
  * FVG (adil değer boşluğu)                -> `band` (renkli şerit)
  * giriş                                   -> `signal`
`BoundaryPattern.band` tam bu iş için var; ayrı bir sözleşme gerekmiyor.
"""

from __future__ import annotations

import pandas as pd

from tlab.chart.contracts import BoundaryLine, BoundaryPattern, ChartSignal
from tlab.chart.tokens import Role
from tlab.core.types import IndicatorResult

_DEAD = frozenset({"invalidated", "expired"})
_STATE = {
    "pending": "KUTU OLUŞTU", "breakout": "KIRILDI", "fvg_formed": "FVG OLUŞTU",
    "retest": "RETEST", "confirmed": "ONAY", "completed": "HEDEFE ULAŞTI",
    "target_reached": "HEDEFE ULAŞTI",
}


def to_pattern(result: IndicatorResult, df: pd.DataFrame) -> BoundaryPattern | None:
    if not result.last_state:
        return None
    alive = [
        (pid, st) for pid, st in result.last_state.items()
        if st.get("state") not in _DEAD
    ]
    if not alive:
        return None

    latest: dict[str, pd.Timestamp] = {}
    for sig in result.signals:
        pid = sig.payload.get("pattern_id")
        if pid is None:
            continue
        t = pd.Timestamp(sig.bar_time)
        if pid not in latest or t > latest[pid]:
            latest[pid] = t
    alive.sort(key=lambda kv: latest.get(kv[0], pd.Timestamp.min), reverse=True)
    pid, st = alive[0]

    boxes = {b.style: b for b in result.boxes if pid in b.label}
    cons, fvg = boxes.get("pattern_consolidation"), boxes.get("pattern_fvg")
    if cons is None:
        return None

    up = str(st.get("direction")) == "long"
    role: Role = "bullish" if up else "bearish"
    # KIRILAN kenar: yukarı kırılımda kutunun TAVANI, aşağıda TABANI.
    edge = float(cons.high) if up else float(cons.low)
    t0 = pd.Timestamp(cons.t0)
    t1 = pd.Timestamp(cons.t1) if cons.t1 is not None else pd.Timestamp(df.index[-1])

    entry = next(
        (m for m in result.markers if m.kind.startswith("pattern_entry_") and pid in m.kind),
        None,
    )
    target = next((lv.price for lv in result.levels if pid in lv.label), None)

    facts: list[tuple[str, str]] = [
        ("Kutu", f"{float(cons.low):,.2f} – {float(cons.high):,.2f}"),
        ("Kırılan kenar", f"{edge:,.2f}"),
    ]
    if fvg is not None:
        facts.append(("FVG", f"{float(fvg.low):,.2f} – {float(fvg.high):,.2f}"))
    if target is not None:
        facts.append(("Hedef", f"{float(target):,.2f}"))

    last_bar = latest.get(pid)
    return BoundaryPattern(
        kind="breakout_fvg", title="KIRILIM + FVG",
        state=_STATE.get(str(st.get("state")), str(st.get("state", "")).upper()),
        boundaries=(
            BoundaryLine(
                points=((t0, edge), (t1, edge)),
                role=role, name="Kırılan Kenar", dash="dash",
            ),
        ),
        band=(float(fvg.low), float(fvg.high)) if fvg is not None else None,
        band_label="FVG (adil değer boşluğu)", band_role=role,
        facts=tuple(facts),
        signal=(
            ChartSignal(
                t=pd.Timestamp(entry.t), price=float(entry.price),
                text=entry.text, role=role, below=up,
            )
            if entry is not None else None
        ),
        bars_ago=(
            None if last_bar is None else int((df.index > pd.Timestamp(last_bar)).sum())
        ),
    )
