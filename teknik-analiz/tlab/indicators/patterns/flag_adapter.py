"""`patterns.flag_pennant` -> `PoleFlag`.

Bulkowski'nin tanımı dört bileşenli: dik DİREK, paralel/paralele yakın
trend çizgileriyle sınırlı küçük konsolidasyon, konsolidasyon boyunca
DÜŞEN hacim, hacim teyitli kırılım. Bu adaptör dördünü de göstergenin
KENDİ çıktısından okur -- hiçbirini yeniden hesaplamaz.

Not: bayrak sınırları (`{pid}_upper`/`_lower`) göstergeye bu adaptör
için EKLENDİ; kanal zaten kırılım kararının dayanağıydı ama dışa
açılmıyordu (yalnızca konsolidasyon kutusu vardı, onun da eğimi yok).
"""

from __future__ import annotations

import pandas as pd

from tlab.core.types import IndicatorResult
from tlab.indicators.patterns.pole_flag import PoleFlag

_DEAD = frozenset({"invalidated", "expired"})
_STATE = {
    "pending": "olusuyor", "confirmed": "onaylandi", "retest_hold": "onaylandi",
    "completed": "onaylandi", "target_reached": "onaylandi", "expired": "suresi_doldu",
}


def to_pattern(result: IndicatorResult, df: pd.DataFrame) -> PoleFlag | None:
    if not result.last_state:
        return None

    latest: dict[str, pd.Timestamp] = {}
    for sig in result.signals:
        pid = sig.payload.get("pattern_id")
        if pid is None:
            continue
        t = pd.Timestamp(sig.bar_time)
        if pid not in latest or t > latest[pid]:
            latest[pid] = t

    alive = [
        (pid, st) for pid, st in result.last_state.items()
        if st.get("state") not in _DEAD
    ]
    if not alive:
        return None
    alive.sort(key=lambda kv: latest.get(kv[0], pd.Timestamp.min), reverse=True)

    for pid, st in alive:
        pat = _build(result, df, pid, st, latest.get(pid))
        if pat is not None:
            return pat
    return None


def _build(
    result: IndicatorResult, df: pd.DataFrame, pid: str, st: dict,
    last_bar: pd.Timestamp | None,
) -> PoleFlag | None:
    lines = {ln.label: ln for ln in result.lines}
    pole = lines.get(f"{pid}_pole")
    up, lo = lines.get(f"{pid}_upper"), lines.get(f"{pid}_lower")
    if pole is None or up is None or lo is None:
        return None

    def _pair(ln):
        (t0, y0), (t1, y1) = ln.points[0], ln.points[-1]
        return ((pd.Timestamp(t0), float(y0)), (pd.Timestamp(t1), float(y1)))

    (pt0, pp0), (pt1, pp1) = _pair(pole)
    born = next((s for s in result.signals if s.payload.get("pattern_id") == pid), None)
    pole_range = float(born.payload.get("pole_range", abs(pp1 - pp0))) if born else abs(pp1 - pp0)

    brk = next(
        (m for m in result.markers if m.kind == f"pattern_breakout:{pid}"), None
    )
    breakout = (pd.Timestamp(brk.t), float(brk.price)) if brk is not None else None

    # Direk grafikte TAM görünsün: pencere direğin BAŞLAMASINDAN birkaç
    # bar öncesinden başlar (Faz 4b'de bir kez düzeltilen sorun -- direk
    # kadraja sığmayınca formasyon havada duruyordu).
    i_pole = int(df.index.searchsorted(pt0))
    view_start = pd.Timestamp(df.index[max(i_pole - 6, 0)])

    i_flag0 = int(df.index.searchsorted(_pair(up)[0][0]))
    i_flag1 = int(df.index.searchsorted(_pair(up)[1][0]))

    # Hacim daralması: konsolidasyon ortalaması / direk ortalaması.
    # Bulkowski'nin "konsolidasyonda hacim düşer" ölçütünün SAYISAL hâli;
    # gösterge bunu `volume_profile_ok` olarak zaten değerlendiriyor,
    # burada ORAN gösterilmek üzere biçimlenir.
    vol = df["volume"]
    pole_v = float(vol.iloc[i_pole : int(df.index.searchsorted(pt1)) + 1].mean())
    flag_v = float(vol.iloc[i_flag0 : i_flag1 + 1].mean())
    contraction = (flag_v / pole_v) if pole_v else 1.0

    ref = float(df["close"].iloc[i_pole]) or 1.0
    return PoleFlag(
        direction=str(st.get("direction", "long")),
        shape=str(st.get("shape", "bayrak")),
        pole_start=(pt0, pp0), pole_end=(pt1, pp1),
        upper=_pair(up), lower=_pair(lo),
        breakout=breakout, target=st.get("target"),
        state=_STATE.get(str(st.get("state")), "olusuyor"),
        # KESİR (yüzde DEĞİL): komposer `pf.pole_pct * 100` yapıyor
        # (`pole_flag.py:44`). `depth_pct` ile AYNI tuzak -- yüzde
        # verilince grafikte "Direk: %421.2" yazıyordu.
        pole_pct=pole_range / ref,
        flag_bars=max(i_flag1 - i_flag0, 0),
        vol_contraction=contraction,
        view_start=view_start,
        bars_ago=(
            None if last_bar is None else int((df.index > pd.Timestamp(last_bar)).sum())
        ),
        is_htf=bool(st.get("is_htf", False)),
    )
