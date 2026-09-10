"""`patterns.wedge`/`patterns.triangle`/`patterns.broadening`'in ZATEN
hesapladığı `IndicatorResult` çıktısını `tlab/chart`'ın `BoundaryPattern`
sözleşmesine çevirir.

`tlab/indicators/harmonics/adapter.py`'nin AYNI ilkesi: scanner'ın (CATALOG,
`tlab eod`, dashboard) KENDİ ürettiği geometriyi paylaş — yeni bir tespit
mantığı YAZMA. `WedgeIndicator`/`BroadeningIndicator` zaten `build_trendlines`
ile sınır çizgilerini, `track_breakout_pattern` ile durum makinesini
(PENDING→CONFIRMED→RETEST_HOLD/TARGET_REACHED, ya da →INVALIDATED/EXPIRED)
kuruyor; bu modül yalnızca o sonucun ARTIK-VAR-OLAN alanlarını (Line/Marker/
Signal/`extra_payload`) okuyup tipli bir `BoundaryPattern`e paketler.

Hesap YAPMAZ: hiçbir eşik/oran/geometri burada yeniden hesaplanmaz. Tek
istisna — `wedge.py`/`broadening.py`'ye bu adaptör için eklenen iki alan
(`extra_payload["upper_touches"]`/`["lower_touches"]`) zaten `build_
trendlines`'ın ürettiği `Trendline.touches`'ın DIŞA AÇILMIŞ hâli, burada
yeniden hesaplanmıyor.

Seçim kuralı: `result.last_state`'teki pattern_id'lerden invalidated/expired
OLMAYAN, en SON sinyali en GÜNCEL olan tek bir aday seçilir (kullanıcının
kuralı: "güncel yakın bir sinyal yoksa göstermesin hiçbir şey" — hiçbiri
uygun değilse `None` döner). Bu, harmonik/golden_zone renderer'ının "yalnızca
en güncel geçerli aday" declutter kuralıyla AYNI ilke.
"""

from __future__ import annotations

import pandas as pd

from tlab.chart.contracts import BoundaryLine, BoundaryPattern, BoundaryTouch, ChartSignal
from tlab.chart.tokens import Role
from tlab.core.pattern_state import SUFFIX_LABEL_TR
from tlab.core.types import IndicatorResult, Line
from tlab.indicators.patterns.wedge import _FLAT_SIDED_SHAPES

# Statik Türkçe başlık metinleri -- wedge.py/broadening.py'nin kendi özel
# (modül-içi) `_LABEL_TR` sözlükleriyle AYNI değerler, yalnızca burada da
# okunabilmesi için kopyalandı. Bunlar bir GEOMETRİ/tespit kararı DEĞİL,
# sabit metin -- iki kopyanın senkron kalması gerekmiyor bir tespit
# hatasına yol açmaz, yalnızca bir başlık string'i.
_TITLE_TR: dict[str, str] = {
    "falling_wedge": "ALÇALAN TAKOZ",
    "rising_wedge": "YÜKSELEN TAKOZ",
    "sym_triangle": "SİMETRİK ÜÇGEN",
    "asc_triangle": "YÜKSELEN ÜÇGEN",
    "desc_triangle": "ALÇALAN ÜÇGEN",
    "broadening_top": "GENİŞLEYEN FORMASYON (TEPE)",
    "broadening_bottom": "GENİŞLEYEN FORMASYON (DİP)",
}


def _pos(df: pd.DataFrame, t) -> int:
    """`t` zaman damgasının bar konumu. İndekste birebir yoksa en yakın
    (soldaki) bara yuvarlar -- `get_loc` KeyError atardı."""
    ts = pd.Timestamp(t)
    try:
        return int(df.index.get_loc(ts))
    except KeyError:
        return int(min(max(df.index.searchsorted(ts, side="right") - 1, 0), len(df) - 1))


def _spanned(
    line: Line, df: pd.DataFrame, start_pos: int, end_pos: int
) -> tuple[tuple[pd.Timestamp, float], ...]:
    """`line`'ın iki çapa noktasından geçen doğruyu ORTAK `[start_pos,
    end_pos]` aralığında yeniden örnekler.

    NEDEN: `wedge.py`/`broadening.py` her sınırı YALNIZCA kendi iki
    pivotu arasında tanımlar ve uzatmayı `Line.extend_right=True`
    bayrağına devreder (eski `renderer.py` bu bayrağı okurdu). Yeni
    `BoundaryLine` sözleşmesi ise "çizgi YALNIZCA bu noktalar arasında
    uzanır" der -- bayrak yok. Bu yüzden iki sınır kendi pivot
    aralıklarında çizilirdi: üst sınır grafiğin ortasında, alt sınır
    başka bir yerde, ikisi HİÇ kesişmezdi (SVGYO/BESTE/BARMA ekran
    görüntülerindeki kopuk çizgilerin tek sebebi buydu). Burada
    uzatmayı adaptör MADDİLEŞTİRİR: geometri wedge.py'nin ürettiği
    doğrunun AYNISI, yalnızca ortak bir aralıkta örneklenir -- yeni bir
    fit/eşik/geometri HESAPLANMAZ.
    """
    (t0, y0), (t1, y1) = line.points[0], line.points[-1]
    i0, i1 = _pos(df, t0), _pos(df, t1)
    slope = 0.0 if i1 == i0 else (float(y1) - float(y0)) / (i1 - i0)
    at = lambda i: float(y0) + slope * (i - i0)  # noqa: E731
    return (
        (pd.Timestamp(df.index[start_pos]), at(start_pos)),
        (pd.Timestamp(df.index[end_pos]), at(end_pos)),
    )


def _pattern_name_of(state_info: dict) -> str:
    # wedge.py last_state -> "shape"; broadening.py last_state -> "pattern".
    name = state_info.get("shape") or state_info.get("pattern")
    if name is None:
        raise ValueError(f"last_state girdisinde 'shape'/'pattern' yok: {state_info!r}")
    return str(name)


# Bir sınırın "gerçek" sayılması için gereken en az bar sayısı ve iki sınır
# arasındaki en düşük denge oranı. Gerekçe (Bulkowski, "Encyclopedia of Chart
# Patterns"): bir üçgen/takoz sınırı en az ~3 hafta sürmeli ve her sınıra
# birden çok kez dokunulmalı. 6 barlık bir "destek çizgisi" formasyon sınırı
# DEĞİL, gürültüdür -- kısa sınır, uzun olanın en az dörtte biri kadar
# sürmeli. Bunlar bir GEOMETRİ hesabı değil, `wedge.py`'nin ÜRETTİĞİ
# adaylar arasından KABUL EDİLEBİLİR olanları seçme ölçütü.
_MIN_SPAN_BARS = 15
_MIN_SPAN_BALANCE = 0.25


def _boundary_spans(
    result: IndicatorResult, pattern_id: str, df: pd.DataFrame
) -> tuple[int, int] | None:
    """Adayın üst/alt sınırlarının BAR cinsinden uzunluğu; çizgiler yoksa None."""
    key = pattern_id.rsplit("_", 1)[0]
    spans: list[int] = []
    for side in ("upper", "lower"):
        line = next((ln for ln in result.lines if ln.label == f"{key}_{side}"), None)
        if line is None:
            return None
        spans.append(abs(_pos(df, line.points[-1][0]) - _pos(df, line.points[0][0])))
    return spans[0], spans[1]


def select_latest(
    result: IndicatorResult, df: pd.DataFrame | None = None
) -> tuple[str, dict] | None:
    """`result.last_state`'ten, geçersiz/süresi dolmamış en güncel adayın
    (pattern_id, last_state[pattern_id]) çiftini döner; hiçbiri yoksa None.

    `df` verilirse önce YOZLAŞMIŞ adaylar (bir sınırı diğerinin yanında yok
    denecek kadar kısa olanlar) ELENİR, tazelik ondan SONRA uygulanır.
    NEDEN: `wedge.py` 159 barlık bir üst sınırı 6 barlık bir alt sınırla
    eşleştiren adaylar da üretiyor ve bunların sinyalleri TİPİK OLARAK en
    taze olanlar; salt tazeliğe göre sıralamak bu yozlaşmış adayı SİSTEMATİK
    olarak seçiyordu (temaslar da o 6 barın içine yığıldığı için grafiğin
    sağ ucunda üst üste biniyordu). Eleme tazelikten ÖNCE gelir -- yoksa
    "en taze" zaten yozlaşmış olanı işaret eder."""
    if not result.last_state:
        return None

    latest_bar: dict[str, pd.Timestamp] = {}
    for sig in result.signals:
        pid = sig.payload.get("pattern_id")
        if pid is None:
            continue
        t = pd.Timestamp(sig.bar_time)
        if pid not in latest_bar or t > latest_bar[pid]:
            latest_bar[pid] = t

    candidates = [
        (pid, st) for pid, st in result.last_state.items()
        if st.get("state") not in ("invalidated", "expired")
    ]
    if df is not None:
        kept = []
        for pid, st in candidates:
            spans = _boundary_spans(result, pid, df)
            if spans is None:
                continue
            short, long_ = min(spans), max(spans)
            if short < _MIN_SPAN_BARS or long_ == 0:
                continue
            # Denge oranı YALNIZCA iki kenarı da eğimli formasyonlara
            # uygulanır. Yükselen/alçalan üçgende düz kenar TANIM GEREĞİ
            # daha kısa olabilir (ölçüldü: geçerli bir alçalan üçgen
            # 158 barlık direnç + 22 barlık düz destek = denge 0.14) --
            # `wedge.py::_FLAT_SIDED_SHAPES`'in AYNI gerekçesi. Yozlaşmış
            # adayı eleyen asıl ölçüt zaten `_MIN_SPAN_BARS`: kullanıcının
            # SVGYO vakasındaki 6 barlık ve takozdaki 9 barlık sahte
            # sınırlar oraya takılıyor, denge oranına gerek kalmadan.
            if st.get("shape") not in _FLAT_SIDED_SHAPES:
                if short / long_ < _MIN_SPAN_BALANCE:
                    continue
            kept.append((pid, st))
        candidates = kept
    if not candidates:
        return None
    candidates.sort(key=lambda kv: latest_bar.get(kv[0], pd.Timestamp.min), reverse=True)
    return candidates[0]


def to_pattern(result: IndicatorResult, df: pd.DataFrame) -> BoundaryPattern | None:
    """Seçilen en güncel adayı `BoundaryPattern`e çevirir. Uygun aday yoksa
    (ya da adayın çizgi/temas verisi eksikse -- bu adaptörün eklendiği
    tarihten ÖNCE üretilmiş bir `IndicatorResult` gibi) `None` döner."""
    picked = select_latest(result, df)
    if picked is None:
        return None
    pattern_id, state_info = picked
    pattern_name = _pattern_name_of(state_info)
    direction = state_info["direction"]
    event = state_info["event"]
    target = state_info["target"]

    suffix = event[len(pattern_name) + 1:] if event.startswith(pattern_name + "_") else event
    state_label = SUFFIX_LABEL_TR.get(suffix, suffix.upper())

    pattern_key = pattern_id.rsplit("_", 1)[0]  # "_long"/"_short" son ekini at

    pattern_signals = [
        s for s in result.signals if s.payload.get("pattern_id") == pattern_id
    ]
    if not pattern_signals:
        return None
    born_sig = pattern_signals[0]
    last_sig = max(pattern_signals, key=lambda s: pd.Timestamp(s.bar_time))

    upper_line = next((ln for ln in result.lines if ln.label == f"{pattern_key}_upper"), None)
    lower_line = next((ln for ln in result.lines if ln.label == f"{pattern_key}_lower"), None)
    if upper_line is None or lower_line is None:
        return None

    upper_idx = born_sig.payload.get("upper_touches", ())
    lower_idx = born_sig.payload.get("lower_touches", ())
    high, low = df["high"], df["low"]
    upper_touches = tuple(
        BoundaryTouch(pd.Timestamp(df.index[i]), float(high.iloc[i]), f"U{k + 1}", True)
        for k, i in enumerate(upper_idx)
    )
    lower_touches = tuple(
        BoundaryTouch(pd.Timestamp(df.index[i]), float(low.iloc[i]), f"L{k + 1}", False)
        for k, i in enumerate(lower_idx)
    )

    role: Role = "bullish" if direction == "long" else "bearish"

    facts: list[tuple[str, str]] = []
    height = born_sig.payload.get("height")
    if height is not None:
        facts.append(("Yükseklik", f"{float(height):,.2f}"))
    apex_idx = born_sig.payload.get("apex_idx")
    if apex_idx is not None:
        apex_bars_left = int(apex_idx) - df.index.get_loc(last_sig.bar_time)
        facts.append(("Apeks'e kalan", f"{max(apex_bars_left, 0)} bar"))
    facts.append(("Temas", f"{len(upper_touches)} üst / {len(lower_touches)} alt"))
    facts.append(("Hedef", f"{float(target):,.2f}"))

    entry_marker = next(
        (
            m for m in result.markers
            if m.kind == f"pattern_entry_{direction}:{pattern_id}"
        ),
        None,
    )
    signal = None
    if entry_marker is not None:
        signal = ChartSignal(
            t=pd.Timestamp(entry_marker.t), price=entry_marker.price, text=entry_marker.text,
            role=role, below=(direction == "long"),
        )

    bars_ago = int((df.index > pd.Timestamp(last_sig.bar_time)).sum())

    # --- İki sınır için ORTAK zaman aralığı -------------------------------
    # Dört çapa (üst iki pivot + alt iki pivot) formasyon gövdesini verir;
    # sağ uç sinyal/giriş barına kadar taşınır ki kırılım oku çizgilerin
    # üstünde kalsın. Daralan formasyonlarda apeks'i AŞMAZ -- aşarsa iki
    # çizgi kesişip X'e döner.
    anchor_pos = [
        _pos(df, t)
        for ln in (upper_line, lower_line)
        for t, _ in (ln.points[0], ln.points[-1])
    ]
    body_start, body_end = min(anchor_pos), max(anchor_pos)

    right_pos = max(body_end, _pos(df, last_sig.bar_time))
    if entry_marker is not None:
        right_pos = max(right_pos, _pos(df, entry_marker.t))
    if apex_idx is not None and int(apex_idx) >= body_end:
        right_pos = min(right_pos, int(apex_idx))
    span_start = max(min(body_start, len(df) - 1), 0)
    span_end = min(max(right_pos, body_end), len(df) - 1)

    return BoundaryPattern(
        kind=pattern_name,
        title=_TITLE_TR.get(pattern_name, pattern_name.upper()),
        state=state_label,
        boundaries=(
            BoundaryLine(
                points=_spanned(upper_line, df, span_start, span_end),
                role=role, name="Üst Sınır", touches=upper_touches,
            ),
            BoundaryLine(
                points=_spanned(lower_line, df, span_start, span_end),
                role=role, name="Alt Sınır", touches=lower_touches,
            ),
        ),
        facts=tuple(facts),
        signal=signal,
        bars_ago=bars_ago,
    )
