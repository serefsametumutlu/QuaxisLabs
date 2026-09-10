"""Harmonik `Candidate` -> grafik sözleşmesi (`XabcdPattern`) adaptörü.

Mevcut harmonik motor zaten X-A-B-C adaylarını, oranları ve durum
zincirini üretiyor (`geometry.py`, `state.py`). Eksik olan, bunu ÇİZİM
katmanının anlayacağı tipli bir sonuca çevirmekti — eskiden jenerik
`Line`/`Marker` torbasına düzleştiriliyor ve renderer'da anlamını
kaybediyordu.

Bu modül o çeviriyi yapar. Hesap YAPMAZ: oranlar ve PRZ, çağıranın
verdiği okul yapılandırmasından gelir.
"""

from __future__ import annotations

import pandas as pd

from tlab.chart.contracts import XabcdPattern, XabcdPoint
from tlab.core.types import IndicatorResult
from tlab.indicators.harmonics.geometry import Candidate

# Geri çekilme merdiveni — X-A bacağı üzerinden
_FIB = ((0.0, "0.0 (A)"), (0.382, "0.382"), (0.5, "0.500"),
        (0.618, "0.618"), (0.786, "0.786"), (1.0, "1.0 (X)"),
        (1.272, "1.272 (D hedefi)"), (1.618, "1.618 (max risk)"))


def to_pattern(
    cand: Candidate,
    *,
    school: str,
    pattern_name: str,
    state: str,
    df: pd.DataFrame,
    prz: tuple[float, float] | None = None,
    theoretical_d: float | None = None,
    actual_d_time: pd.Timestamp | None = None,
    actual_d_price: float | None = None,
) -> XabcdPattern:
    pts = tuple(
        XabcdPoint(p.bar_time, float(p.price), lb)
        for p, lb in ((cand.x, "X"), (cand.a, "A"), (cand.b, "B"), (cand.c, "C"))
    )

    # Fibo merdiveni X-A bacağı üzerine kurulur; 0.0 = A ucu, 1.0 = X ucu.
    xa_lo, xa_hi = sorted((float(cand.x.price), float(cand.a.price)))
    span = xa_hi - xa_lo
    a_is_high = float(cand.a.price) > float(cand.x.price)

    def at(r: float) -> float:
        return (xa_hi - span * r) if a_is_high else (xa_lo + span * r)

    fib = tuple((r, at(r), lb) for r, lb in _FIB)

    d = None
    if actual_d_time is not None and actual_d_price is not None:
        d = XabcdPoint(actual_d_time, float(actual_d_price), "D")

    anchor = d.t if d is not None else cand.c.bar_time
    bars_ago = int((df.index > anchor).sum())

    return XabcdPattern(
        school=school, pattern_name=pattern_name, direction=cand.direction,
        points=pts, state=state, prz=prz, theoretical_d=theoretical_d,
        actual_d=d, fib_levels=fib,
        ratios=(("AB/XA", f"{cand.ab_xa:.3f}"), ("BC/AB", f"{cand.bc_ab:.3f}")),
        bars_ago=bars_ago,
    )


# --- IndicatorResult -> XabcdPattern köprüsü --------------------------------
#
# `to_pattern` (yukarıda) ham `Candidate` alır; ama web rotası
# (`chart_json.py`) `compute_live`'dan bir `IndicatorResult` alıyor ve
# `Candidate` nesneleri orada YOK. Bu köprü, `scanner_indicator.py`'nin
# ZATEN ürettiği primitiflerden (polygon/level/marker/last_state) tipli
# sonucu geri kurar -- `boundary_adapter.py`'nin `patterns.wedge` için
# yaptığı işin AYNISI. Hiçbir oran/PRZ yeniden HESAPLANMAZ; yalnızca
# gösterilecek oranlar (AB/XA gibi) zaten bilinen noktalardan biçimlenir.

_STATE_TR: dict[str, str] = {
    "pending": "izlemede", "active": "aktif", "confirmed": "tamamlandi",
    "invalidated": "gecersiz", "expired": "gecersiz",
}

# `select_latest`in dışladığı durumlar -- kullanıcının kuralı: "güncel
# yakın bir sinyal yoksa göstermesin hiçbir şey".
_DEAD_STATES = frozenset({"invalidated", "expired"})


def _fmt_ratio(num: float, den: float) -> str:
    return "—" if den == 0 else f"{abs(num / den):.3f}"


def result_to_pattern(result: IndicatorResult, df: pd.DataFrame) -> XabcdPattern | None:
    """En güncel geçerli harmonik adayı `XabcdPattern`e çevirir.

    8 harmonik okulun HEPSİ `HarmonicIndicator`'ın tek çıktı biçimini
    paylaştığı için tek köprü yeter (okul adı `last_state["school"]`ten
    gelir). Uygun aday yoksa `None`.
    """
    if not result.last_state:
        return None

    # DİKKAT: `last_state` anahtarı `{okul}_{formasyon}_{aday}` biçiminde,
    # sinyal payload'ında ise `pattern_name` ile `pattern_id` AYRI alanlar.
    # İkisini doğrudan karşılaştırmak SESSİZCE hiç eşleşmez (ilk denemede
    # tam bu oldu: `bars_ago` her adayda None çıkıyordu, yani grafikte
    # "Sinyal yaşı" hiç görünmeyecekti). Bileşik anahtar burada kurulur.
    latest: dict[str, pd.Timestamp] = {}
    for sig in result.signals:
        cand_id = sig.payload.get("pattern_id")
        name = sig.payload.get("pattern_name")
        if cand_id is None or name is None:
            continue
        suffix = f"_{name}_{cand_id}"
        t = pd.Timestamp(sig.bar_time)
        for pid in result.last_state:
            if pid.endswith(suffix) and (pid not in latest or t > latest[pid]):
                latest[pid] = t

    alive = [
        (pid, st) for pid, st in result.last_state.items()
        if st.get("state") not in _DEAD_STATES
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
) -> XabcdPattern | None:
    polys = {p.label: p for p in result.polygons}
    xab, bcd = polys.get(f"{pid}_xab"), polys.get(f"{pid}_bcd")
    if xab is None or len(xab.points) < 3:
        return None

    # xab = X, A, B  ve  bcd = B, C, D -- iki kanat B'de birleşir
    # (`composers/xabcd.py`nin beklediği yapı; X ile D BİRLEŞTİRİLMEZ).
    labels = ("X", "A", "B")
    pts = [XabcdPoint(pd.Timestamp(t), float(v), lab)
           for (t, v), lab in zip(xab.points[:3], labels, strict=True)]
    actual_d: XabcdPoint | None = None
    if bcd is not None and len(bcd.points) >= 3:
        t_c, v_c = bcd.points[1]
        pts.append(XabcdPoint(pd.Timestamp(t_c), float(v_c), "C"))
        t_d, v_d = bcd.points[2]
        actual_d = XabcdPoint(pd.Timestamp(t_d), float(v_d), "D")
        pts.append(actual_d)
    if len(pts) < 4:
        return None      # __post_init__ X,A,B,C şart koşuyor

    lv = {level.label: level.price for level in result.levels}
    prz_lo, prz_hi = lv.get(f"{pid}_prz_low"), lv.get(f"{pid}_prz_high")
    prz = (float(prz_lo), float(prz_hi)) if prz_lo is not None and prz_hi is not None else None

    fib: list[tuple[float, float, str]] = []
    for label, price in lv.items():
        if label.startswith(f"{pid}_fib_"):
            ratio = label.rsplit("_", 1)[-1]
            fib.append((float(ratio), float(price), ratio))
    fib.sort()

    x, a, b, c = pts[0], pts[1], pts[2], pts[3]
    ratios = (
        ("AB/XA", _fmt_ratio(b.price - a.price, a.price - x.price)),
        ("BC/AB", _fmt_ratio(c.price - b.price, b.price - a.price)),
    )
    if actual_d is not None:
        ratios += (("CD/BC", _fmt_ratio(actual_d.price - c.price, c.price - b.price)),)

    bars_ago = None
    if last_bar is not None:
        bars_ago = int((df.index > pd.Timestamp(last_bar)).sum())

    return XabcdPattern(
        school=str(st.get("school", "")),
        pattern_name=str(st.get("pattern", "")),
        direction="bullish" if st.get("direction") == "long" else "bearish",
        points=tuple(pts),
        state=_STATE_TR.get(str(st.get("state")), str(st.get("state"))),
        prz=prz,
        theoretical_d=(sum(prz) / 2) if prz else None,
        actual_d=actual_d,
        fib_levels=tuple(fib),
        ratios=ratios,
        bars_ago=bars_ago,
    )
