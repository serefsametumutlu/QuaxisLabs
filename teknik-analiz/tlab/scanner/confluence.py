"""Dönüş haritası (reversal map) — Faz 8E. `tlab/indicators/`'de DEĞİL burada:
girdisi ham OHLCV DEĞİL, ZATEN hesaplanmış birden fazla indikatörün sonucudur
(`structure.supply_demand`, `structure.golden_zone`, `structure.price_structure`,
`trend.weekly_channel`, `harmonic.*`, `structure.swing_fib_abcd`) — bu yüzden
`BaseIndicator`'ın tekil `compute(df, context)` sözleşmesine UYMAZ, ayrı bir
"post-processing" katmanıdır (`scanner/` altında yaşaması bunun içindir).

**Kapsam (bilinçli): yalnızca DESTEK/DİP tarafı.** Görev metninin kendi
`bottom_probability` adlandırması ve "DİPTE OLASI" etiketi bunu doğruluyor —
yalnızca GÜNCEL KAPANIŞIN ALTINDAKİ (potansiyel destek) seviyeler toplanır;
direnç/tepe tarafı bu turun kapsamı DIŞINDA (simetrik bir "TEPEDE OLASI" haritası
ileride aynı iskeletle eklenebilir, ayrı bir takip işi).

Ağırlıklandırma = kaynak_türü_temel_ağırlığı × tazelik(yaş) × tf_ağırlığı
(W1=1.5, 1D=1.0, 4H=0.6 — görev metninin verdiği SABİT tf çarpanları). Kaynak
türü temel ağırlıkları görev metninde SAYISAL olarak verilmiyor — TASARIM
KARARI (aşağıda `_SOURCE_BASE_WEIGHT`), gerekçesi kod içinde belgelendi.
Tazelik = `2^(-yaş_gün / freshness_halflife_days)` (üstel yarı-ömür çürümesi —
projedeki EWMA/EWMAC üstel çürüme desenleriyle TUTARLI bir seçim)."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from tlab.core.params import BaseParams, params_hash
from tlab.core.types import (
    Box,
    Direction,
    IndicatorResult,
    Marker,
    Signal,
    Timeframe,
)
from tlab.features.swings import alternate_pivots, find_pivots
from tlab.features.volatility import atr as atr_feature
from tlab.scanner.results import ResultsStore

_TF_WEIGHT: dict[str, float] = {"1W": 1.5, "1D": 1.0, "4H": 0.6}

# TASARIM KARARI — görev metni kaynak türlerine göre ağırlıklandırmayı istiyor
# ("kaynak tipi") ama SAYISAL değer vermiyor. Sıralama mantığı: doğrudan bu
# amaç için tasarlanmış, dar/keskin bölgeler (arz-talep, golden zone, harmonik
# PRZ) EN YÜKSEK; genel yapısal seviyeler (destek bölgesi, haftalık kanal alt
# bandı) ORTA; istatistiksel referans seviyeleri (POC/VAH/VAL) ve HENÜZ
# TAMAMLANMAMIŞ bir projeksiyon (AB=CD D hedefi) EN DÜŞÜK.
_SOURCE_BASE_WEIGHT: dict[str, float] = {
    "structure.supply_demand": 1.0,
    "structure.golden_zone": 1.0,
    "structure.price_structure.zone": 0.8,
    "structure.price_structure.level": 0.6,
    "trend.weekly_channel": 0.9,
    "structure.swing_fib_abcd": 0.7,
}
_HARMONIC_BASE_WEIGHT = 1.1


@dataclass(frozen=True)
class ConfluenceParams(BaseParams):
    bucket_atr_fraction: float = 0.10
    atr_period: int = 14
    freshness_halflife_days: float = 45.0
    bucket_span: int = 60
    bottom_probability_scale: float = 3.0
    swing_left: int = 3
    swing_right: int = 3


@dataclass(frozen=True)
class _Candidate:
    indicator: str
    price_low: float
    price_high: float
    label: str
    born_time: pd.Timestamp
    weight: float


def _freshness(born_time: pd.Timestamp, now: pd.Timestamp, halflife_days: float) -> float:
    age_days = max(0.0, (now - born_time).total_seconds() / 86400.0)
    return 2.0 ** (-age_days / halflife_days)


def _candidates_from_supply_demand(result: IndicatorResult, close: float) -> list[Box]:
    return [b for b in result.boxes if b.style == "demand" and b.high <= close]


def _candidates_from_golden_zone(result: IndicatorResult, close: float) -> list[Box]:
    styles = ("golden_zone", "golden_zone_alt")
    return [b for b in result.boxes if b.style in styles and b.high <= close]


def _candidates_from_price_structure(
    result: IndicatorResult, close: float
) -> tuple[list[Box], list]:
    zones = [b for b in result.boxes if b.style == "support_zone" and b.high <= close]
    levels = [
        lv for lv in result.levels
        if lv.style in ("poc", "value_area") and lv.price <= close
    ]
    return zones, levels


def _candidates_from_weekly_channel(result: IndicatorResult, close: float) -> list:
    out = []
    for ln in result.lines:
        if ln.style not in ("channel", "channel_current") or "lower" not in ln.label:
            continue
        if not ln.points:
            continue
        price = float(ln.points[-1][1])
        if price <= close:
            out.append((price, ln.points[-1][0], ln.label))
    return out


def _candidates_from_swing_fib_abcd(result: IndicatorResult, close: float) -> list:
    out = []
    for lv in result.levels:
        if not lv.label.startswith("D (hedef)") or lv.end is not None:
            continue
        if lv.price <= close and lv.start is not None:
            out.append((lv.price, lv.start, lv.label))
    return out


def _candidates_from_harmonic(
    result: IndicatorResult, close: float
) -> list[tuple[str, float, float]]:
    """PRZ alt/üst Level'larını `{pid}_prz_low`/`{pid}_prz_high` etiket
    önekiyle eşleştirir; yalnızca hâlâ GEÇERLİ (pending/active/confirmed —
    invalidated/expired HARİÇ) adayların PRZ'si, YALNIZCA tamamı güncel
    kapanışın ALTINDAYSA alınır."""
    lows: dict[str, float] = {}
    highs: dict[str, float] = {}
    for lv in result.levels:
        if lv.label.endswith("_prz_low"):
            lows[lv.label[: -len("_prz_low")]] = lv.price
        elif lv.label.endswith("_prz_high"):
            highs[lv.label[: -len("_prz_high")]] = lv.price
    out = []
    for pid in lows.keys() & highs.keys():
        info = result.last_state.get(pid)
        state = info.get("state") if isinstance(info, dict) else None
        if state in ("invalidated", "expired"):
            continue
        lo, hi = lows[pid], highs[pid]
        if max(lo, hi) <= close:
            out.append((pid, min(lo, hi), max(lo, hi)))
    return out


def build_reversal_map(
    symbol: str,
    tf: str,
    df: pd.DataFrame,
    sources: dict[str, IndicatorResult],
    params: ConfluenceParams | None = None,
) -> IndicatorResult:
    """Saf çekirdek fonksiyon — `sources` ZATEN hesaplanmış indikatör
    sonuçlarının {indikatör_adı: IndicatorResult} sözlüğüdür (results.db'den
    ya da canlı hesaptan gelebilir, bu fonksiyon FARK ETMEZ). `df`: `symbol`in
    kendi OHLCV'si (ATR + son onaylı swing low için)."""
    p = params or ConfluenceParams()
    close = float(df["close"].iloc[-1])
    now = df.index[-1]

    candidates: list[_Candidate] = []

    sd = sources.get("structure.supply_demand")
    if sd is not None:
        base_w = _SOURCE_BASE_WEIGHT["structure.supply_demand"]
        for b in _candidates_from_supply_demand(sd, close):
            w = base_w * _TF_WEIGHT.get(sd.timeframe.value, 1.0)
            candidates.append(
                _Candidate("structure.supply_demand", b.low, b.high, b.label, b.t0, w)
            )

    gz = sources.get("structure.golden_zone")
    if gz is not None:
        base_w = _SOURCE_BASE_WEIGHT["structure.golden_zone"]
        for b in _candidates_from_golden_zone(gz, close):
            w = base_w * _TF_WEIGHT.get(gz.timeframe.value, 1.0)
            candidates.append(_Candidate("structure.golden_zone", b.low, b.high, b.label, b.t0, w))

    ps = sources.get("structure.price_structure")
    if ps is not None:
        ps_zones, levels = _candidates_from_price_structure(ps, close)
        zone_base_w = _SOURCE_BASE_WEIGHT["structure.price_structure.zone"]
        for b in ps_zones:
            w = zone_base_w * _TF_WEIGHT.get(ps.timeframe.value, 1.0)
            candidates.append(
                _Candidate("structure.price_structure", b.low, b.high, b.label, b.t0, w)
            )
        level_base_w = _SOURCE_BASE_WEIGHT["structure.price_structure.level"]
        for lv in levels:
            w = level_base_w * _TF_WEIGHT.get(ps.timeframe.value, 1.0)
            born = lv.start if lv.start is not None else now
            candidates.append(
                _Candidate("structure.price_structure", lv.price, lv.price, lv.label, born, w)
            )

    wc = sources.get("trend.weekly_channel")
    if wc is not None:
        base_w = _SOURCE_BASE_WEIGHT["trend.weekly_channel"]
        for price, born, label in _candidates_from_weekly_channel(wc, close):
            w = base_w * _TF_WEIGHT.get(wc.timeframe.value, 1.0)
            candidates.append(_Candidate("trend.weekly_channel", price, price, label, born, w))

    sf = sources.get("structure.swing_fib_abcd")
    if sf is not None:
        base_w = _SOURCE_BASE_WEIGHT["structure.swing_fib_abcd"]
        for price, born, label in _candidates_from_swing_fib_abcd(sf, close):
            w = base_w * _TF_WEIGHT.get(sf.timeframe.value, 1.0)
            candidates.append(_Candidate("structure.swing_fib_abcd", price, price, label, born, w))

    for indicator_name, result in sources.items():
        if not indicator_name.startswith("harmonic."):
            continue
        for pid, lo, hi in _candidates_from_harmonic(result, close):
            born = None
            for ln in result.lines:
                if ln.label == f"{pid}_xab" and ln.points:
                    born = ln.points[0][0]
                    break
            if born is None:
                born = now
            w = _HARMONIC_BASE_WEIGHT * _TF_WEIGHT.get(result.timeframe.value, 1.0)
            candidates.append(
                _Candidate(indicator_name, lo, hi, f"{indicator_name}:{pid}", born, w)
            )

    weighted: list[tuple[_Candidate, float]] = [
        (c, c.weight * _freshness(c.born_time, now, p.freshness_halflife_days)) for c in candidates
    ]

    last_atr = float(atr_feature(df, p.atr_period).iloc[-1])
    bucket_size = max(last_atr * p.bucket_atr_fraction, close * 1e-5)
    center_bucket = round(close / bucket_size)
    bucket_idx_range = range(center_bucket - p.bucket_span, center_bucket + p.bucket_span + 1)
    bucket_prices = [i * bucket_size for i in bucket_idx_range]
    density = {i: 0.0 for i in bucket_idx_range}

    for c, eff_weight in weighted:
        lo_idx = math.floor(c.price_low / bucket_size)
        hi_idx = math.ceil(c.price_high / bucket_size)
        i_start = max(lo_idx, bucket_idx_range.start)
        i_stop = min(hi_idx, bucket_idx_range.stop - 1) + 1
        for i in range(i_start, i_stop):
            density[i] = density.get(i, 0.0) + eff_weight

    swing_low_price, swing_low_time = _last_confirmed_swing_low(df, p.swing_left, p.swing_right)
    at_swing_bucket = (
        round(swing_low_price / bucket_size) if swing_low_price is not None else center_bucket
    )
    density_at_swing = density.get(at_swing_bucket, 0.0)
    bottom_probability = 1.0 - math.exp(-density_at_swing / p.bottom_probability_scale)

    # Eşleşme toleransı: bucket_size/2 (tek-fiyatlı kaynaklar — POC, kanal
    # bandı, D hedefi — sıfır genişlikli olduğu için AYNI bucket'a düşen
    # bir swing low'u da "eşleşiyor" saymak gerekir, tam fiyat eşitliği DEĞİL).
    matching_sources: list[_Candidate] = []
    if swing_low_price is not None:
        tol = bucket_size * 0.5
        matching_sources = [
            c for c, _ in weighted
            if (c.price_low - tol) <= swing_low_price <= (c.price_high + tol)
        ]
    source_desc = ", ".join(sorted({c.indicator for c in matching_sources})) or "kaynak yok"

    max_weight = max((w for _, w in weighted), default=1.0) or 1.0
    boxes: list[Box] = []
    zones: list[dict[str, float | str]] = []
    for c, eff_weight in weighted:
        boxes.append(
            Box(
                t0=c.born_time, t1=now, low=c.price_low, high=max(c.price_high, c.price_low),
                label=c.label, style="confluence_zone",
            )
        )
        zones.append(
            {
                "indicator": c.indicator, "label": c.label, "low": c.price_low,
                "high": max(c.price_high, c.price_low), "weight": eff_weight,
                "weight_norm": eff_weight / max_weight,
            }
        )

    markers: list[Marker] = []
    if swing_low_price is not None and swing_low_time is not None:
        markers.append(
            Marker(
                t=swing_low_time, price=swing_low_price,
                text=f"DİPTE OLASI: {bottom_probability:.2f} | {len(matching_sources)} kaynak",
                kind="reversal_map_swing_low",
            )
        )

    signals: list[Signal] = []
    if swing_low_price is not None and swing_low_time is not None and matching_sources:
        direction: Direction = "long"
        signals.append(
            Signal(
                bar_time=swing_low_time, detected_at=swing_low_time, direction=direction,
                state="confirmed", score=min(1.0, bottom_probability),
                payload={
                    "event": "reversal_confluence", "bottom_probability": bottom_probability,
                    "n_sources": len(matching_sources), "sources": source_desc,
                    "swing_low_price": swing_low_price,
                },
            )
        )

    # `vp_bins`/`vp_volumes` — `structure.price_structure`'ın AYNI sözleşmesi
    # (bkz. o modülün docstring'i): index=fiyat, `vp_bins` değerleri de fiyat
    # (renderer `_draw_volume_profile`'ın `bins.to_numpy()`'sini y-ekseni
    # olarak kullanması için), `vp_volumes` değerleri yoğunluk (ağırlık
    # toplamı — hacim DEĞİL, ama AYNI paneli/çizim yolunu paylaşır).
    density_values = [density[i] for i in bucket_idx_range]
    price_index = pd.Index(bucket_prices, name="price")
    series = {
        "vp_bins": pd.Series(bucket_prices, index=price_index),
        "vp_volumes": pd.Series(density_values, index=price_index),
    }

    last_state = {
        "bottom_probability": bottom_probability,
        "n_sources": len(matching_sources),
        "sources": source_desc,
        "swing_low_price": swing_low_price,
        "swing_low_time": swing_low_time.isoformat() if swing_low_time is not None else None,
        "close": close,
        "n_candidates": len(candidates),
        "zones": zones,
    }

    p_hash = params_hash(p)
    tf_enum = Timeframe(tf)
    return IndicatorResult(
        indicator="confluence", version="0.1.0", params_hash=p_hash, symbol=symbol,
        timeframe=tf_enum, signals=signals, boxes=boxes, markers=markers,
        series=series, last_state=last_state,
    )


def _last_confirmed_swing_low(
    df: pd.DataFrame, left: int, right: int
) -> tuple[float | None, pd.Timestamp | None]:
    """Son ONAYLANMIŞ (finalized_idx'i olan, yani bir SONRAKİ zıt-türde
    pivotla kesinleşmiş) swing low — non-repaint: `detected_at` pivotun
    KENDİ barı değil, `finalized_idx` (onay barı) olmalı (bkz. modül
    docstring'i, projedeki yerleşik "finalized_idx not confirmed_idx"
    ilkesi — GoldenZone/HeadShoulders ile AYNI gerekçe)."""
    pivots = find_pivots(df, left=left, right=right)
    finalized = [
        p for p in alternate_pivots(pivots) if p.kind == "low" and p.finalized_idx is not None
    ]
    if not finalized:
        return None, None
    last = finalized[-1]
    return float(last.price), df.index[last.finalized_idx]


def build_reversal_map_from_run(
    store: ResultsStore, run_id: str, symbol: str, tf: str, df: pd.DataFrame,
    params: ConfluenceParams | None = None,
) -> IndicatorResult:
    """`results.db`'den (tamamlanmış bir EOD run'ından) ZATEN kayıtlı olan
    kaynak indikatörleri okuyup `build_reversal_map`'i çağırır — üretim
    (EOD) yolu. `structure.weekly_channel`'ın W1 koşusu varsa ONU (yoksa
    aynı sembolün 1D koşusunu) kullanır (bkz. modül docstring'i, "W1'den
    1D'ye taşınır")."""
    source_names = [
        "structure.supply_demand", "structure.golden_zone", "structure.price_structure",
        "structure.swing_fib_abcd",
    ]
    sources: dict[str, IndicatorResult] = {}
    for name in source_names:
        result = store.read_result(run_id, symbol, tf, name)
        if result is not None:
            sources[name] = result

    weekly = store.read_result(run_id, symbol, "1W", "trend.weekly_channel")
    if weekly is None:
        weekly = store.read_result(run_id, symbol, tf, "trend.weekly_channel")
    if weekly is not None:
        sources["trend.weekly_channel"] = weekly

    for symbol_tf_indicator in store.list_symbol_indicators(run_id, tf):
        _, _, indicator = symbol_tf_indicator
        if indicator.startswith("harmonic.") and symbol_tf_indicator[0] == symbol:
            result = store.read_result(run_id, symbol, tf, indicator)
            if result is not None:
                sources[indicator] = result

    return build_reversal_map(symbol, tf, df, sources, params)
