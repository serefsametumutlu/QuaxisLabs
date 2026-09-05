"""SupplyDemandIndicator — `features/zones_sd.py`'nin (find_bases/
find_impulses/make_sd_zones/update_zones) ince bir sarmalayıcısı: bölgeleri
Box/Signal/Marker olarak üretir, kalite skoru hesaplar, kırılan demand'ı
supply'a (veya tersi) "flip" eder.

**BİLİNEN SINIRLAMA (kod DOĞRU, generic `Registry.register()` kapsamı
DIŞINDA — `structure.price_structure`/`trend.breakouts` ile AYNI istisna
yolu, `register_verified_elsewhere`):** `make_sd_zones`'un `max_zones`
kesmesi (`-impulse_strength, -created_idx` sıralamasıyla üstten kesme) bir
"aday havuzu"dur — df büyüdükçe DAHA GÜÇLÜ yeni bir bölge, önceden top-N
içinde olan daha zayıf bir bölgeyi listeden DÜŞÜREBİLİR. Bu, o bölgenin
KENDİ sınırlarının (low/high/created_idx) sonradan değiştiği anlamına
GELMEZ (find_bases/find_impulses/update_zones'un hepsi `tests/
test_zones_sd.py`'de hypothesis ile "kesik ⊆ tam" özelliği doğrulanmış saf
fonksiyonlardır) — yalnızca "şu an top-12'de mi" sorusunun cevabı zamanla
değişebilir, tıpkı `trendlines.build_trendlines`'ın `max_lines` seçimi
gibi. Non-repaint sözleşmesi bu yüzden generic repaint_test yerine
`tests/test_structure/test_supply_demand.py`'deki HEDEFLİ testlerle
(sabit low/high/created_idx, extend-only t1, flip'in yeni bir pattern_id
alması) doğrulanır.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

import pandas as pd

from tlab.core.indicator import BaseIndicator
from tlab.core.params import BaseParams, params_hash
from tlab.core.types import (
    Box,
    Direction,
    IndicatorMeta,
    IndicatorResult,
    Marker,
    Signal,
    Timeframe,
)
from tlab.features.swings import ZigzagMethod, significant_pivots
from tlab.features.volatility import atr
from tlab.features.zones_sd import (
    SDKind,
    SDZone,
    find_bases,
    find_impulses,
    find_pivot_zones,
    make_sd_zones,
    update_zones,
)

SDMethod = Literal["pivot", "rbd", "both"]


@dataclass(frozen=True)
class SupplyDemandParams(BaseParams):
    # Faz 4d (2026-09-05, `docs/GORSEL_HATA_TESHISI.md` bölüm A1) —
    # varsayılan "rbd" (rally-base-drop, orijinal yöntem) idi; gerçek veride
    # (INTEM) TEK arz bölgesi + SIFIR talep bölgesi üretmesi ("temel yöntem
    # ama gerçek dünyada çok seyrek doğuruyor") bulunup kullanıcının/
    # `ornek1.png`nin kullandığı pivot-çıpalı yönteme ("pivot") geçildi.
    # "both" iki yöntemi de çalıştırır, çakışan bölgelerin skorunu birleştirir.
    method: SDMethod = "pivot"
    base_max: int = 5
    base_atr: float = 0.6
    impulse_bars: int = 3
    impulse_atr: float = 2.0
    # Faz 0.5, A1 — ortak pivot girişi (yalnızca method="pivot"/"both" iken
    # kullanılır). Varsayılan "atr" — golden_zone/swing_fib_abcd'nin AYNI
    # kararı: bir S/D bölgesi de "yapının kendisi" (major swing), wedge'in
    # trendline aday havuzu sorunuyla AYNI kategori DEĞİL.
    zigzag_method: ZigzagMethod = "atr"
    pivot_left: int = 3
    pivot_right: int = 3
    atr_mult: float = 3.0
    min_swing_atr: float | None = None
    pivot_cluster_atr: float = 0.5
    pivot_height_cap_atr: float = 2.75
    pivot_min_height_atr: float = 0.15
    max_zones: int = 12
    flip: bool = True
    atr_period: int = 14


class SupplyDemandIndicator(BaseIndicator):
    """Arz/Talep bölgeleri: doğum = patlama barı; test/reaksiyon/kırılım
    izleme; kırılan bölge (flip=True iken) karşıt türde yeni bir bölgeye
    döner (TEK seviyeli flip — bir flip bölgesi kendisi bir daha flip
    OLMAZ, spec'in "kırılan demand -> supply" ifadesi zincirleme değil tek
    seferlik bir dönüşüm olarak yorumlandı)."""

    meta = IndicatorMeta(
        name="structure.supply_demand",
        version="0.1.0",
        category="structure",
        description="Arz/Talep (taban+patlama) bölgeleri, test/reaksiyon/kırılım izlemesi.",
        supported_timeframes=(Timeframe.D1, Timeframe.H4),
    )

    def __init__(self, params: SupplyDemandParams | None = None) -> None:
        self.params: SupplyDemandParams = params or SupplyDemandParams()

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        p = self.params
        n = len(df)
        close = df["close"].to_numpy()
        atr_series = atr(df, p.atr_period)
        last_atr = atr_series.iloc[-1]

        zones = _build_zones(df, p)

        boxes: list[Box] = []
        signals: list[Signal] = []
        markers: list[Marker] = []
        nearest: dict[str, dict | None] = {"demand": None, "supply": None}

        entries: list[tuple[str, SDZone, bool]] = [
            (f"sd_{zone.kind}_{zone.created_idx}_{i}", zone, False) for i, zone in enumerate(zones)
        ]

        i = 0
        while i < len(entries):
            pattern_id, zone, is_flip = entries[i]
            i += 1
            if zone.created_idx >= n:
                continue

            state = update_zones([zone], df, t=n - 1)[0]
            quality = _quality_score(zone, state.fresh, atr_series, p)
            broken = state.broken_at is not None
            end_time = df.index[state.broken_at] if broken else df.index[-1]
            style = zone.kind if not broken else f"{zone.kind}_broken"

            distance_atr: float | None = None
            if not broken:
                if zone.low <= close[-1] <= zone.high:
                    distance_atr = 0.0
                elif close[-1] > zone.high and not pd.isna(last_atr) and last_atr > 0:
                    distance_atr = (close[-1] - zone.high) / last_atr
                elif close[-1] < zone.low and not pd.isna(last_atr) and last_atr > 0:
                    distance_atr = (zone.low - close[-1]) / last_atr

            fresh_tr = "taze" if state.fresh else "test edildi"
            label = f"{'DEMAND' if zone.kind == 'demand' else 'SUPPLY'} ({fresh_tr})"
            if distance_atr is not None:
                label += f" | {distance_atr:.1f} ATR"

            boxes.append(
                Box(
                    t0=df.index[zone.created_idx], t1=end_time, low=zone.low, high=zone.high,
                    label=label, style=style,
                )
            )

            direction: Direction = "long" if zone.kind == "demand" else "short"
            signals.append(
                Signal(
                    bar_time=df.index[zone.created_idx], detected_at=df.index[zone.created_idx],
                    direction=direction, state="pending", score=quality,
                    payload={
                        "event": "sd_new", "pattern_id": pattern_id, "zone_kind": zone.kind,
                        "fresh": True,
                    },
                )
            )
            for t in state.test_idxs:
                signals.append(
                    Signal(
                        bar_time=df.index[t], detected_at=df.index[t], direction=direction,
                        state="active", score=quality,
                        payload={
                            "event": "sd_test", "pattern_id": pattern_id, "zone_kind": zone.kind,
                            "fresh": state.fresh,
                        },
                    )
                )
            if state.first_reaction_idx is not None:
                t = state.first_reaction_idx
                signals.append(
                    Signal(
                        bar_time=df.index[t], detected_at=df.index[t], direction=direction,
                        state="confirmed", score=quality,
                        payload={
                            "event": "sd_reaction", "pattern_id": pattern_id,
                            "zone_kind": zone.kind,
                        },
                    )
                )
                markers.append(Marker(df.index[t], close[t], "REAKSİYON", "sd_reaction"))
            if broken:
                broken_t = state.broken_at
                assert broken_t is not None
                signals.append(
                    Signal(
                        bar_time=df.index[broken_t], detected_at=df.index[broken_t],
                        direction=("short" if zone.kind == "demand" else "long"),
                        state="invalidated", score=quality,
                        payload={
                            "event": "sd_broken", "pattern_id": pattern_id, "zone_kind": zone.kind,
                        },
                    )
                )
                markers.append(Marker(df.index[broken_t], close[broken_t], "KIRILDI", "sd_broken"))

                if p.flip and not is_flip:
                    flip_kind: SDKind = "supply" if zone.kind == "demand" else "demand"
                    flip_zone = replace(
                        zone, kind=flip_kind, created_idx=broken_t, fresh=True,
                    )
                    entries.append((f"{pattern_id}_flip", flip_zone, True))

            if not broken and distance_atr is not None:
                current = nearest[zone.kind]
                if current is None or distance_atr < current["distance_atr"]:
                    nearest[zone.kind] = {
                        "low": zone.low, "high": zone.high, "distance_atr": distance_atr,
                        "fresh": state.fresh,
                    }

        overall = None
        for cand in (nearest["demand"], nearest["supply"]):
            if cand is not None and (
                overall is None or cand["distance_atr"] < overall["distance_atr"]
            ):
                overall = cand

        last_state = {
            "nearest_demand": nearest["demand"],
            "nearest_supply": nearest["supply"],
            "in_zone": bool(overall is not None and overall["distance_atr"] == 0.0),
            "distance_atr": overall["distance_atr"] if overall is not None else None,
        }

        return IndicatorResult(
            indicator=self.meta.name, version=self.meta.version, params_hash=params_hash(p),
            symbol="", timeframe=Timeframe.D1,
            signals=signals, boxes=boxes, markers=markers, last_state=last_state,
        )


def _rbd_zones(df: pd.DataFrame, p: SupplyDemandParams) -> list[SDZone]:
    bases = find_bases(df, p.base_max, p.base_atr, p.atr_period)
    impulses = find_impulses(df, p.impulse_bars, p.impulse_atr, p.atr_period)
    return make_sd_zones(bases, impulses, max_zones=None)


def _pivot_zones(df: pd.DataFrame, p: SupplyDemandParams) -> list[SDZone]:
    pivots = significant_pivots(
        df, method=p.zigzag_method, left=p.pivot_left, right=p.pivot_right,
        atr_mult=p.atr_mult, atr_period=p.atr_period, min_swing_atr=p.min_swing_atr,
    )
    return find_pivot_zones(
        df, pivots, cluster_atr=p.pivot_cluster_atr, height_cap_atr=p.pivot_height_cap_atr,
        min_height_atr=p.pivot_min_height_atr, atr_period=p.atr_period,
    )


def _merge_both(pivot_zones: list[SDZone], rbd_zones: list[SDZone]) -> list[SDZone]:
    """`method="both"`: pivot-çıpalı bölgeler BİRİNCİL (spec'in tercihi) —
    bir rally-base-drop bölgesi AYNI türden bir pivot bölgesiyle fiyatça
    ÇAKIŞIYORSA, pivot bölgesinin skorunu güçlendirir ("aynı bölgeyi işaret
    ediyorlarsa güç skoru artsın"); çakışmayan rbd bölgeleri de AYRICA
    (pivot yönteminin kaçırdığı bir bölge olabilir) eklenir."""
    boosted: list[SDZone] = []
    used_rbd: set[int] = set()
    for pz in pivot_zones:
        best: tuple[float, int, SDZone] | None = None
        for i, rz in enumerate(rbd_zones):
            if rz.kind != pz.kind or i in used_rbd:
                continue
            overlap = min(pz.high, rz.high) - max(pz.low, rz.low)
            if overlap > 0 and (best is None or overlap > best[0]):
                best = (overlap, i, rz)
        if best is not None:
            _, best_i, best_rbd = best
            used_rbd.add(best_i)
            boosted.append(
                replace(
                    pz,
                    impulse_strength=max(pz.impulse_strength, best_rbd.impulse_strength) * 1.25,
                )
            )
        else:
            boosted.append(pz)
    boosted.extend(rz for i, rz in enumerate(rbd_zones) if i not in used_rbd)
    return boosted


def _build_zones(df: pd.DataFrame, p: SupplyDemandParams) -> list[SDZone]:
    if p.method == "rbd":
        zones = _rbd_zones(df, p)
    elif p.method == "pivot":
        zones = _pivot_zones(df, p)
    else:
        zones = _merge_both(_pivot_zones(df, p), _rbd_zones(df, p))
    if p.max_zones is not None:
        zones = sorted(zones, key=lambda z: (-z.impulse_strength, -z.created_idx))[: p.max_zones]
    return zones


def _quality_score(
    zone: SDZone, fresh: bool, atr_series: pd.Series, p: SupplyDemandParams
) -> float:
    """Kalite = patlama gücü × baz darlığı × tazelik (spec'in verdiği
    normalizasyon sabitleri YOK — burada makul varsayılanlarla belgeleniyor,
    BreakoutParams'ın quality_score'undaki AYNI yaklaşım, bkz. Faz 8A):
    - strength_score: impulse_strength (zaten ATR-normalize) / 5.0'a kapatılır
      (impulse_atr eşiği tipik olarak 2.0 civarında; 5x eşik "çok güçlü" kabul).
    - tightness_score: bölge yüksekliğinin (yöntem-uyumlu bir tavan *
      o barın ATR'si)'ne oranı — `method="rbd"` için `base_atr` (find_bases
      zaten <= base_atr*ATR garanti eder), `method="pivot"/"both"` için
      `pivot_height_cap_atr` (find_pivot_zones'un KENDİ tavanı, bkz. o
      fonksiyonun docstring'i) — Faz 4d ÖNCESİ burada HER ZAMAN `base_atr`
      kullanılıyordu, bu pivot bölgeleri (tipik yükseklik ~0.15-2.75*ATR)
      için sistemli olarak neredeyse-sıfır tightness_score üretirdi
      (height_ratio hep >=1 çıkardı). DAHA DAR (oran küçük) -> DAHA YÜKSEK
      skor.
    - freshness_score: hiç test edilmemişse 1.0, edilmişse 0.5.
    Üçü de 0..1 olduğu için çarpım da 0..1'dir (Signal.score kısıtı)."""
    strength_score = min(1.0, zone.impulse_strength / 5.0)

    height_ref_atr = p.base_atr if p.method == "rbd" else p.pivot_height_cap_atr
    zone_atr = atr_series.iloc[zone.created_idx]
    if pd.isna(zone_atr) or zone_atr <= 0:
        tightness_score = 0.5
    else:
        height_ratio = (zone.high - zone.low) / (height_ref_atr * zone_atr)
        tightness_score = max(0.0, 1.0 - min(1.0, height_ratio))

    freshness_score = 1.0 if fresh else 0.5
    return round(strength_score * tightness_score * freshness_score, 4)
