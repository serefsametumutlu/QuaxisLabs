"""Arz/Talep (Supply/Demand) bölgeleri: taban (base) + patlama (impulse) ->
bölge; test/reaksiyon/kırılım izleme; altın oran (golden zone) bandı.

Bir S/D bölgesi, fiyatın bir "taban" (dar konsolidasyon) içinde bekleyip
oradan güçlü/tek yönlü bir "patlama" ile ayrıldığı fiyat aralığıdır — bölge
sınırları TABANIN kendisidir (patlamanın değil). Bölge, PATLAMA ONAYLANDIĞI
barda (`impulse.t1_idx`) doğar; bu bardan ÖNCE hiçbir sonuçta görünemez
(non-repaint). `update_zones`, `ranges.py`/`zones.py` ile AYNI "extend-only
touches, bir kez atanan broken_at" mimarisini paylaşır.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from tlab.features.fibonacci import retracement
from tlab.features.swings import Pivot
from tlab.features.volatility import atr

SDKind = Literal["demand", "supply"]
ImpulseDirection = Literal["up", "down"]


@dataclass(frozen=True)
class Base:
    """[t0_idx, t1_idx] penceresi (dahil) dar bir konsolidasyon (taban) adayı."""

    t0_idx: int
    t1_idx: int
    low: float
    high: float


def find_bases(
    df: pd.DataFrame, base_max: int = 5, base_atr: float = 0.6, atr_period: int = 14
) -> list[Base]:
    """Her t1 barı için, [t1-L+1, t1] penceresinin (L=1..base_max) high-low
    genişliği `base_atr * ATR[t1]`'den DAR ise bir Base adayı üretir.

    Üst üste binen (aynı t1, farklı L) adaylar BAĞIMSIZ döner — hangisinin
    "gerçek" taban olduğuna `make_sd_zones` (patlamayla eşleştirirken en
    uzun/olgun adayı seçerek) karar verir, tıpkı `ranges.detect_ranges`'in
    seçim kararını caller'a bırakması gibi."""
    n = len(df)
    atr_series = atr(df, atr_period)
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()

    bases: list[Base] = []
    for t1 in range(n):
        a = atr_series.iloc[t1]
        if pd.isna(a) or a == 0:
            continue
        for length in range(1, base_max + 1):
            t0 = t1 - length + 1
            if t0 < 0:
                break
            window_high = float(high[t0 : t1 + 1].max())
            window_low = float(low[t0 : t1 + 1].min())
            if (window_high - window_low) <= base_atr * a:
                bases.append(Base(t0_idx=t0, t1_idx=t1, low=window_low, high=window_high))
    return bases


@dataclass(frozen=True)
class Impulse:
    """t0_idx'ten t1_idx'e (dahil, k bar) tek yönlü güçlü hareket.

    strength: |close[t1]-close[t0]| / ATR[t1] (ATR-normalize edilmiş güç).
    """

    t0_idx: int
    t1_idx: int
    direction: ImpulseDirection
    strength: float


def find_impulses(
    df: pd.DataFrame, k: int = 3, impulse_atr: float = 2.0, atr_period: int = 14
) -> list[Impulse]:
    """[t1-k, t1] net hareketi (close[t1]-close[t1-k]) ATR[t1]'e göre
    `impulse_atr` katından BÜYÜKSE VE en az k-1 bar aynı yönlü gövdeye
    (close>open yukarı / close<open aşağı) sahipse patlama sayılır — yalnızca
    [t1-k, t1] barlarını kullanır, non-repaint."""
    n = len(df)
    atr_series = atr(df, atr_period)
    close = df["close"].to_numpy()
    open_ = df["open"].to_numpy()

    impulses: list[Impulse] = []
    for t1 in range(k, n):
        t0 = t1 - k
        a = atr_series.iloc[t1]
        if pd.isna(a) or a == 0:
            continue
        net = close[t1] - close[t0]
        strength = abs(net) / a
        if strength < impulse_atr:
            continue
        direction: ImpulseDirection = "up" if net > 0 else "down"
        same_dir_bodies = sum(
            1 for i in range(t0 + 1, t1 + 1) if (close[i] > open_[i]) == (direction == "up")
        )
        if same_dir_bodies < k - 1:
            continue
        impulses.append(Impulse(t0_idx=t0, t1_idx=t1, direction=direction, strength=strength))
    return impulses


@dataclass(frozen=True)
class SDZone:
    kind: SDKind
    low: float
    high: float
    created_idx: int
    base_bars: int
    impulse_strength: float
    fresh: bool = True


def make_sd_zones(
    bases: list[Base], impulses: list[Impulse], max_zones: int | None = None
) -> list[SDZone]:
    """Her impulse, TAM olarak kendi `t0_idx`'inde biten (`base.t1_idx ==
    impulse.t0_idx`) bazlarla eşleştirilir; birden fazla uzunluk adayı varsa
    EN UZUN (en olgun) taban seçilir. Bölge doğum barı `impulse.t1_idx`'tir.
    max_zones verilirse en güçlü (impulse_strength) + en güncel öncelikli
    kesilir (seçim kriteri caller'a bırakılmaz, çünkü S/D taraması tipik
    olarak "en taze/en güçlü N bölge" ister)."""
    bases_by_end: dict[int, list[Base]] = {}
    for b in bases:
        bases_by_end.setdefault(b.t1_idx, []).append(b)

    zones: list[SDZone] = []
    for imp in impulses:
        candidates = bases_by_end.get(imp.t0_idx)
        if not candidates:
            continue
        best = max(candidates, key=lambda b: b.t1_idx - b.t0_idx)
        kind: SDKind = "demand" if imp.direction == "up" else "supply"
        zones.append(
            SDZone(
                kind=kind,
                low=best.low,
                high=best.high,
                created_idx=imp.t1_idx,
                base_bars=best.t1_idx - best.t0_idx + 1,
                impulse_strength=imp.strength,
                fresh=True,
            )
        )

    if max_zones is not None:
        zones = sorted(zones, key=lambda z: (-z.impulse_strength, -z.created_idx))[:max_zones]
    return zones


@dataclass(frozen=True)
class SDZoneState:
    """`update_zones`'un bir bölge için ürettiği durum — test_idxs extend-only
    (yalnızca büyür), first_reaction_idx/broken_at bir kez atanınca DEĞİŞMEZ."""

    zone: SDZone
    test_idxs: tuple[int, ...]
    first_reaction_idx: int | None
    broken_at: int | None
    fresh: bool


def update_zones(zones: list[SDZone], df: pd.DataFrame, t: int) -> list[SDZoneState]:
    """Her bölge için created_idx'ten `t`'ye (dahil) kadar, yalnızca
    [0, t] barlarını kullanarak test/reaksiyon/kırılım geçişlerini hesaplar.

    Bar-bar sırayla: (1) KIRILIM — kapanış bölgenin YANLIŞ tarafına geçerse
    (demand: close<low, supply: close>high) broken_at bu barda sabitlenir,
    izleme durur; (2) TEST — bar bölgeye değiyorsa (low<=high VE high>=low)
    test_idxs'e eklenir; (3) REAKSİYON — bir test barından SONRAKİ bir barda
    kapanış bölgenin DOĞRU tarafına (dışına, lehte) dönerse first_reaction_idx
    bu barda sabitlenir (yalnızca İLK reaksiyon kaydedilir).

    `t`'yi büyüterek tekrar çağırmak SONUÇLARI YALNIZCA İLERİYE DOĞRU
    büyütür (extend-only) — non-repaint, çünkü hesap her zaman created_idx'ten
    başlayan AYNI deterministik taramadır."""
    n_eff = min(len(df), t + 1)
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    close = df["close"].to_numpy()

    states: list[SDZoneState] = []
    for zone in zones:
        if zone.created_idx >= n_eff:
            states.append(
                SDZoneState(
                    zone=zone, test_idxs=(), first_reaction_idx=None, broken_at=None, fresh=True
                )
            )
            continue

        test_idxs: list[int] = []
        first_reaction_idx: int | None = None
        broken_at: int | None = None

        for i in range(zone.created_idx, n_eff):
            is_broken = close[i] < zone.low if zone.kind == "demand" else close[i] > zone.high
            if is_broken:
                broken_at = i
                break

            in_zone = low[i] <= zone.high and high[i] >= zone.low
            if in_zone:
                test_idxs.append(i)
                continue

            if test_idxs and first_reaction_idx is None:
                favorable = close[i] > zone.high if zone.kind == "demand" else close[i] < zone.low
                if favorable:
                    first_reaction_idx = i

        states.append(
            SDZoneState(
                zone=zone,
                test_idxs=tuple(test_idxs),
                first_reaction_idx=first_reaction_idx,
                broken_at=broken_at,
                fresh=not test_idxs,
            )
        )
    return states


def find_pivot_zones(
    df: pd.DataFrame,
    pivots: list[Pivot],
    *,
    ctx_bars: int = 3,
    cluster_atr: float = 0.5,
    height_cap_atr: float = 2.75,
    min_height_atr: float = 0.15,
    atr_period: int = 14,
) -> list[SDZone]:
    """Swing pivotlarına ÇİPALI arz/talep bölgeleri — `find_bases`/
    `find_impulses`/`make_sd_zones` (rally-base-drop) YÖNTEMİNE ALTERNATİF
    bir üreteç, ama AYNI `SDZone`/`update_zones`/kalite akışına besler
    (Faz 4d, `docs/GORSEL_HATA_TESHISI.md` bölüm A1 — kullanıcının/`ornek1.
    png`nin kullandığı yöntem, kaynak: swing-çıpalı bölge + temas skorlaması
    [tradingview.com/script/ZUAYemgd], order block anatomisi [liquidityfinder.
    com/news/anatomy-of-a-valid-order-block-in-smart-money-concepts]).

    Çipa: swing HIGH -> supply (dış kenar = pivot fiyatı, iç kenar AŞAĞIDA);
    swing LOW -> demand (dış kenar = pivot fiyatı, iç kenar YUKARIDA). İç
    kenar, pivotu ÖNCELEYEN `ctx_bars` mumun ortalama toplam aralığından
    (high-low) türetilir (`min_height_atr*ATR` ile `height_cap_atr*ATR`
    arasına kelepçelenir) — böylece bölge GERÇEK tepki alanını kapsar, ince
    bir çizgi değil.

    "ATR doğrulaması" (pivottan uzaklaşan hareket ATR katını aşmalı) AYRICA
    burada UYGULANMAZ — `pivots` zaten `significant_pivots(method="atr",
    atr_mult=...)`in KENDİ dönüş eşiğinden geçmiş olmalı (bir pivot ancak
    `atr_mult*ATR` kadar bir ters hareketle ONAYLANIR, bkz. `swings.py::
    atr_zigzag`); bu yüzden filtre burada TEKRARLANMAZ, `impulse_strength`
    yalnızca SKORLAMA için (pivotu ONAYLAYAN -- zigzag'daki bir ÖNCEKİ karşıt
    pivottan gelen -- bacağın ATR-normalize büyüklüğü) hesaplanır.

    Kümeleme: AYNI türden (ikisi de supply/demand) bölgelerin fiyat aralığı
    çakışıyor ya da `cluster_atr*ATR` içinde YAKINSA TEK bölgede birleşir
    (dış sınırların BİRLEŞİMİ alınır, güç = kümedeki en yüksek impulse_
    strength, created_idx = kümedeki EN ERKEN pivotun confirmed_idx'i). BU,
    `wedge`/`broadening`'in trendline aday havuzuyla AYNI kategori bir "aday
    havuzu" deseni -- df büyüdükçe yeni bir pivot bir önceki bölgeyi
    genişletebilir; `SupplyDemandIndicator` bu yüzden ZATEN generic
    `repaint_test` dışında (`register_verified_elsewhere`, bkz. modülün
    kendi docstring'i), non-repaint hedefli testlerle doğrulanır."""
    n = len(df)
    atr_series = atr(df, atr_period)
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()

    raw: list[SDZone] = []
    for i, p in enumerate(pivots):
        if p.confirmed_idx >= n:
            continue
        a = atr_series.iloc[p.confirmed_idx]
        if pd.isna(a) or a <= 0:
            continue

        lo_ctx = max(0, p.bar_idx - ctx_bars + 1)
        ranges = [high[j] - low[j] for j in range(lo_ctx, p.bar_idx + 1)]
        avg_range = sum(ranges) / len(ranges) if ranges else a
        height = min(max(avg_range, min_height_atr * a), height_cap_atr * a)

        prev_price = pivots[i - 1].price if i > 0 else None
        leg = abs(p.price - prev_price) if prev_price is not None else height
        strength = leg / a if a > 0 else 0.0

        if p.kind == "high":
            kind: SDKind = "supply"
            zone_high, zone_low = p.price, p.price - height
        else:
            kind = "demand"
            zone_low, zone_high = p.price, p.price + height

        raw.append(
            SDZone(
                kind=kind, low=zone_low, high=zone_high, created_idx=p.confirmed_idx,
                base_bars=1, impulse_strength=strength, fresh=True,
            )
        )

    return _cluster_pivot_zones(raw, atr_series, cluster_atr, height_cap_atr)


def _cluster_pivot_zones(
    zones: list[SDZone], atr_series: pd.Series, cluster_atr: float, height_cap_atr: float,
) -> list[SDZone]:
    """GERÇEK bir hata (2026-09-05, THYAO'da GÖRÜLEREK bulundu): art arda
    YAKIN pivotların ZİNCİRLEME birleşmesi (A~B, B~C, C~D — ama A ile D
    doğrudan yakın DEĞİL) `height_cap_atr`i tamamen atlayıp onlarca ATR'lik
    dev bir "bölge" üretebiliyordu (9 pivot, 33 puanlık bir demand kutusu
    -- artık bir "seviye" değil, koca bir trend bacağı). Düzeltme: bir
    birleşme, SONUÇTAKİ yükseklik `height_cap_atr*ATR`i AŞACAKSA
    REDDEDİLİR (kümeye eklenmez, kendi ayrı kümesi olarak kalır) — `find_
    pivot_zones`'un tek-pivot yükseklik tavanıyla AYNI tavan, kümeleme
    SONRASINDA da korunur."""
    result: list[SDZone] = []
    for kind in ("supply", "demand"):
        same = sorted((z for z in zones if z.kind == kind), key=lambda z: z.created_idx)
        clusters: list[SDZone] = []
        for z in same:
            a = atr_series.iloc[z.created_idx]
            a_val = float(a) if not pd.isna(a) else 0.0
            tol = cluster_atr * a_val
            cap = height_cap_atr * a_val if a_val > 0 else float("inf")
            merged = False
            for i, c in enumerate(clusters):
                gap = max(z.low, c.low) - min(z.high, c.high)
                new_low, new_high = min(z.low, c.low), max(z.high, c.high)
                if gap <= tol and (new_high - new_low) <= cap:
                    clusters[i] = SDZone(
                        kind=kind, low=new_low, high=new_high,
                        created_idx=min(z.created_idx, c.created_idx),
                        base_bars=c.base_bars + 1,
                        impulse_strength=max(z.impulse_strength, c.impulse_strength),
                        fresh=True,
                    )
                    merged = True
                    break
            if not merged:
                clusters.append(z)
        result.extend(clusters)
    return result


def golden_zone(
    swing_start: float, swing_end: float, lo: float = 0.618, hi: float = 0.786
) -> tuple[float, float]:
    """swing_start->swing_end hareketinin [lo,hi] Fibonacci geri çekilme bandı.

    `fibonacci.retracement(p0=swing_start, p1=swing_end)`'in doğrudan bir
    kullanımıdır — bu yüzden YÖN NE OLURSA OLSUN simetriktir: yükseliş
    (swing_start=düşük, swing_end=yüksek) için bant swing_end'in ALTINDA,
    düşüş (swing_start=yüksek, swing_end=düşük) için bant swing_end'in
    ÜSTÜNDE çıkar — çağıranın YALNIZCA hangi ucun ÖNCE (start) geldiğini
    doğru sırada vermesi yeterlidir.

    TASARIM NOTU: master spec bu fonksiyonu 'golden_zone(swing_low,
    swing_high, ...)' adlarıyla tanımlıyordu; burada swing_start/swing_end'e
    yeniden adlandırıldı çünkü 'low'/'high' isimleri yalnızca yükseliş
    senaryosunda doğru anlam taşır (düşüş senaryosunda "önce gelen" nokta
    swing_high'tır ve yine İLK argüman olarak verilmesi gerekir) — bu saf
    bir isimlendirme netliği, davranış fibonacci.retracement ile birebir
    aynıdır. Dönen bant her zaman (alt, üst) sıralı döner."""
    levels = retracement(swing_start, swing_end, levels=(lo, hi))
    a, b = levels[lo], levels[hi]
    return (a, b) if a <= b else (b, a)
