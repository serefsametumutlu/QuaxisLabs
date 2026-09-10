"""`patterns.head_shoulders` ve `patterns.double_top_bottom` ->
`NecklinePattern` (boyun çizgili dönüş formasyonları).

İki gösterge AYNI çıktı biçimini paylaşır (boyun `Line`ı + hologram
üçgenleri + vertex marker'ları + `last_state`), bu yüzden TEK adaptör
yeter -- `harmonics/adapter.py`nin 8 okulu tek köprüyle karşılaması gibi.

`boundary_adapter.py` ile AYNI ilke: hesap YAPMAZ, tarayıcının KENDİ
geometrisini okur.
"""

from __future__ import annotations

import pandas as pd

from tlab.core.types import IndicatorResult
from tlab.indicators.patterns.neckline_v2 import Hologram, NecklinePattern, NecklinePoint

_DEAD = frozenset({"invalidated", "expired"})

# `last_state["kind"]` -> sözleşmedeki tür adı.
_KIND = {
    "obo": "obo", "tobo": "ters_obo",
    "double_top": "cift_tepe", "double_bottom": "cift_dip",
    "cift_tepe": "cift_tepe", "cift_dip": "cift_dip",
}

_STATE = {
    "pending": "olusuyor", "confirmed": "onaylandi", "retest_hold": "onaylandi",
    "completed": "onaylandi", "target_reached": "onaylandi",
    "invalidated": "gecersiz", "expired": "gecersiz",
}


def to_pattern(result: IndicatorResult, df: pd.DataFrame) -> NecklinePattern | None:
    """En güncel geçerli adayı `NecklinePattern`e çevirir; yoksa None."""
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


def _marker(result: IndicatorResult, prefix: str, pid: str):
    return next((m for m in result.markers if m.kind == f"{prefix}:{pid}"), None)


def _build(
    result: IndicatorResult, df: pd.DataFrame, pid: str, st: dict,
    last_bar: pd.Timestamp | None,
) -> NecklinePattern | None:
    direction = str(st.get("direction", "long"))
    # `head_shoulders` anahtarı "kind", `double_top_bottom` "pattern"
    # kullanıyor (broadening'in AYNI ikiliği) -- ikisi de okunur.
    raw_kind = str(st.get("kind") or st.get("pattern") or "")
    kind = _KIND.get(raw_kind, raw_kind)

    # BOYUN İKİ BİÇİMDE GELİR:
    #  * `head_shoulders` -> EĞİMLİ, `Line` olarak (`{pid}_neckline`)
    #  * `double_top_bottom` -> YATAY, `Level` olarak (aynı ad)
    # İlk sürüm yalnızca `Line` arıyordu, bu yüzden çift tepe/dip
    # adaptörden HİÇ geçmiyordu (ölçüldü: `to_pattern` None dönüyordu).
    neck_line = next((ln for ln in result.lines if ln.label == f"{pid}_neckline"), None)
    neck_level = next((lv for lv in result.levels if lv.label == f"{pid}_neckline"), None)
    if neck_line is None and neck_level is None:
        return None

    # Köşe noktaları vertex marker'larından -- metinleri (SOL OMUZ / BAŞ /
    # SAĞ OMUZ ya da T1/T2) ZATEN gösterge yazıyor, yeniden adlandırılmaz.
    # `double_top_bottom` vertex metni yalnızca "1"/"2" -- sözleşmenin
    # beklediği T1/T2 (tepe) ya da B1/B2 (dip) biçimine çevrilir.
    prefix = {"cift_tepe": "T", "cift_dip": "B"}.get(kind)
    pts = tuple(
        NecklinePoint(
            pd.Timestamp(m.t), float(m.price),
            f"{prefix}{m.text}" if prefix and m.text.isdigit() else m.text,
        )
        for m in result.markers
        if m.kind == f"pattern_vertex:{pid}"
    )
    if not pts:
        return None
    # Yatay boyun: formasyonun uçları arasında iki noktaya açılır.
    if neck_line is not None and len(neck_line.points) >= 2:
        neck = (
            (pd.Timestamp(neck_line.points[0][0]), float(neck_line.points[0][1])),
            (pd.Timestamp(neck_line.points[-1][0]), float(neck_line.points[-1][1])),
        )
    else:
        price = float(neck_level.price)          # type: ignore[union-attr]
        neck = ((pts[0].t, price), (pts[-1].t, price))

    # Hologram: gösterge her omuz/tepe için AYRI bir üçgen poligonu
    # üretiyor; sözleşme tek bir yol istiyor -- hepsi zaman sırasında
    # birleştirilir (nokta KOPYALANMAZ, ardışık tekrarlar atlanır).
    times: list[pd.Timestamp] = []
    prices: list[float] = []
    for poly in result.polygons:
        if poly.label != f"{pid}_hologram":
            continue
        for t, v in poly.points:
            ts = pd.Timestamp(t)
            if times and times[-1] == ts:
                continue
            times.append(ts)
            prices.append(float(v))
    holo = Hologram(tuple(times), tuple(prices)) if len(times) >= 3 else None

    brk_marker = _marker(result, "pattern_breakout", pid)
    breakout = (
        NecklinePoint(pd.Timestamp(brk_marker.t), float(brk_marker.price), "KIRILIM")
        if brk_marker is not None else None
    )
    retest_marker = _marker(result, "pattern_retest", pid)
    retest = (
        NecklinePoint(pd.Timestamp(retest_marker.t), float(retest_marker.price), "RETEST")
        if retest_marker is not None else None
    )

    born = next((s for s in result.signals if s.payload.get("pattern_id") == pid), None)
    break_rule = str(born.payload.get("break_rule", "")) if born else ""
    depth = float(born.payload.get("depth", 0.0)) if born else 0.0
    # Tetik seviyesi: gösterge kırılımı hangi seviyeye göre onayladıysa O.
    # Eğimli boyunda bu koltukaltı olabilir (Bulkowski) -- kural adı
    # `break_rule` payload'ında ZATEN yazıyor.
    if born is not None and "break_price" in born.payload:
        trigger = float(born.payload["break_price"])
    elif born is not None and "neckline" in born.payload:
        trigger = float(born.payload["neckline"])
    else:
        trigger = float(neck[-1][1])
    trigger_note = "sağ koltukaltı" if break_rule == "right_armpit" else "boyun çizgisi"

    sep = 0
    if len(pts) >= 2:
        i0 = int(df.index.searchsorted(pts[0].t))
        i1 = int(df.index.searchsorted(pts[-1].t))
        sep = max(i1 - i0, 0)

    return NecklinePattern(
        kind=kind, direction=direction, points=pts,
        neckline=neck,
        trigger_price=trigger, trigger_note=trigger_note,
        breakout=breakout, target=st.get("target"),
        state=_STATE.get(str(st.get("state")), str(st.get("state", ""))),
        bars_ago=(
            None if last_bar is None else int((df.index > pd.Timestamp(last_bar)).sum())
        ),
        separation_bars=sep,
        # İKİ tuzak üst üste:
        #  1. `depth` payload'ı MUTLAK FİYAT mesafesi (`|baş - boyun|`,
        #     bkz. `features/hs_pattern.py:124`), oran DEĞİL.
        #  2. `depth_pct` ADI yanıltıcı: sözleşmenin kendi tespit edicisi
        #     oraya KESİR koyuyor (`neckline_v2.py:248` -> depth/p1.price)
        #     ve komposer 100 ile ÇARPIYOR (`neckline.py:43`).
        # İkisi karıştırılınca grafikte önce "%2869.9", düzeltmenin ilk
        # turunda da "%1451.0" yazdı. Doğrusu: KESİR döndür.
        depth_pct=(depth / trigger) if trigger else 0.0,
        hologram=holo, retest=retest,
    )
