"""PriceStructure — trend çizgileri, konsolidasyon kutuları, destek/direnç
bölgeleri, hacim profili ve momentum osilatörlerini TEK indikatörde toplayan
"fiyat yapısı" görünümü. Hesap yapmaz denecek kadar az — mevcut `tlab/features/`
fonksiyonlarını (trendlines, ranges, zones, volume_profile, ma, oscillators)
sarmalayıp IndicatorResult primitiflerine çevirir; non-repaint garantisi
tamamen bu alt modüllerden miras alınır.

Zone/trendline kind ayrımı (sarı direnç / mavi destek): `cluster_zones` ve
`build_trendlines` kind-agnostik oldukları için, pivotlar `kind` alanına göre
önceden filtrelenip her ikisi de İKİ AYRI ÇAĞRI ile (resistance/support)
çalıştırılır.

DİKKAT — vp_bins/vp_volumes/vp_gauss/vp_hvn series'leri ZAMAN EKSENLİ DEĞİLDİR:
diğer series'ler (volume, macd, rsi_14, ...) df.index (datetime) ile
hizalıyken, bu dördü FİYAT bin merkezleriyle indexlenir
(pd.Series(volumes, index=price_bins)). `vp_hvn`: her bin için 1.0 (Yüksek
Hacim Düğümü/HVN) veya 0.0 — `features/volume_profile.py::find_hvn_nodes`'un
saf histogram tepe-noktası tespiti, value area'dan bağımsız. Renderer (Faz 7)
bunları sağ panelde ayrı bir yatay histogram olarak çizmelidir — zaman
eksenine karşı çizilmemelidir.

BİLİNEN SINIRLAMA — İKİ PARÇA generic `repaint_test`/`Registry.register()`
KAPSAMI DIŞINDA tutulur (kod DOĞRU çalışıyor, ama walk-forward eşitlik testi
bu ikisi için doğası gereği uygulanabilir değil):

1. **Trendline Line/Signal'leri.** `build_trendlines`'ın kendi docstring'i
   zaten bunu belgeliyor: min_touches/max_lines'a göre HANGİ (p1,p2) aday
   çizginin döndürüleceği df büyüdükçe DEĞİŞEBİLİR (yeni pivotlar yeni aday
   çiftleri doğurur — "aday havuzu" deseni). Bu, dönen bir çizginin KENDİ
   touches/broken_at geçmişinin sonradan değişmesi DEĞİLDİR (o zaten
   prefix-tutarlıdır, bkz. trendlines.py testleri) — yalnızca "şu an hangi
   adaylar öne çıkıyor" sorusunun cevabı zamanla netleşir. Bu proje bunu
   `Line.label`'a "(Temas:N)" olarak yansıttığı ve `trendline_breakout`
   sinyalinin payload'ına `touches` koyduğu için, generic IndicatorResult
   düzeyindeki repaint_test bunu (haklı olarak, ama bu bağlamda YANLIŞ
   ALARM olarak) repaint şüphesi sayar.
2. **POC/VAH/VAL Level'leri (ve dolayısıyla eski poc_reclaim sinyali).**
   Hacim profili `df.iloc[-window_bars:]` gibi DİZİNİN SONUNA göre kayan bir
   pencere kullanır (`volume_profile.py`'nin kendi sözleşmesi: pencere
   SABİT olmalı, ama burada "şu anki son N bar" — df büyüdükçe kayar).
   Bu yüzden POC/VAH/VAL, geçmişte "o an ne olduğu" değil, HER ZAMAN "şu an
   görünen pencerede ne olduğu"nu temsil eder — canlı/güncel bir gösterge,
   kalıcı bir tarihsel kayıt DEĞİL. Bu nedenle `poc_reclaim` bir Signal
   OLARAK üretilmez (tarihsel bir sinyal, tanımı gereği pencere kaydıkça
   değişirdi); bunun yerine `last_state["poc_reclaimed_last_bar"]` olarak
   yalnızca "şu an" bilgisi taşınır.

Bu iki parça `tests/test_structure/test_price_structure.py`'de generic
`repaint_test` yerine hedefli testlerle (ranges/zones extend-only + doğum
barı, macd/volume series eşitliği) doğrulanır.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import numpy as np
import pandas as pd

from tlab.core.indicator import BaseIndicator
from tlab.core.params import BaseParams, params_hash
from tlab.core.types import (
    Box,
    Direction,
    IndicatorMeta,
    IndicatorResult,
    Level,
    Line,
    Marker,
    Signal,
    Timeframe,
)
from tlab.features.ma import crossovers, sma
from tlab.features.oscillators import macd as compute_macd
from tlab.features.oscillators import rsi as compute_rsi
from tlab.features.ranges import detect_ranges
from tlab.features.swings import Pivot, ZigzagMethod, atr_zigzag, find_pivots
from tlab.features.trendlines import Trendline, build_trendlines
from tlab.features.volume_profile import find_hvn_nodes
from tlab.features.volume_profile import profile as compute_profile
from tlab.features.zones import cluster_zones


@dataclass(frozen=True)
class PriceStructureParams(BaseParams):
    pivot_left: int = 3
    pivot_right: int = 3
    atr_period: int = 14
    # Faz 0.5, A1 — ortak pivot girişi (bkz. tlab/features/swings.py::
    # significant_pivots). YALNIZCA `_zones`'u etkiler -- `_trendlines`
    # HER ZAMAN ham find_pivots kullanır (bkz. compute()'taki gerekçe: ATR
    # seyrekleştirmesi trendline aday havuzunda ciddi yanlış-pozitif
    # artışına yol açtığı ölçüldü). Varsayılan "atr" _zones için ölçümle
    # doğrulandı (scripts/sistemik_denetim.py); atr_period yukarıdaki
    # alanla PAYLAŞILIR (modülün geri kalanı zaten aynı ATR'yi kullanıyor).
    zigzag_method: ZigzagMethod = "atr"
    atr_mult: float = 3.0
    min_swing_atr: float | None = None
    # Faz 0.5, A2 — konsolidasyon kutusu için minimum bar sayısı takvimsel
    # bir süre (kaç bar boyunca fiyat dar bir bantta kaldı); 1D taban kabul
    # edilip diğer zaman dilimlerine göre ölçeklenir. profile_window_bars
    # BİLİNÇLİ OLARAK dışarıda bırakıldı -- kendi docstring'i bunu bir
    # takvim süresi değil "tipik görünür pencere" (viz) varsayımı olarak
    # tanımlıyor.
    _BAR_FIELDS: ClassVar[frozenset[str]] = frozenset({"range_min_bars"})
    trendline_min_touches: int = 2
    trendline_tol_atr: float = 0.3
    trendline_confirm_bars: int = 1
    trendline_max_lines: int = 4
    range_min_bars: int = 10
    range_atr_mult: float = 1.5
    range_breakout_confirm: int = 1
    zone_band_atr: float = 0.5
    zone_min_pivots: int = 2
    zone_breakout_confirm: int = 1
    # 60 -> 250 (2026-08-30): varsayılan grafik yakınlaştırması (renderer.py::
    # _DEFAULT_LAST_N) ~250 bar iken hacim profili yalnızca son 60 barı
    # kapsıyordu — sağdaki vp panelinin dikey ekseni ana panelin GÖRÜNÜR fiyat
    # aralığıyla senkronize edildiği için (`_sync_price_yaxis`) bu, çubukların
    # panelin yalnızca dar bir dilimine sıkışıp geri kalanının boş kalmasına
    # yol açıyordu (kullanıcı geri bildirimi, referans ekran görüntüsüyle
    # kıyaslanınca "çok cılız/kendi alanını doldurmuyor" — images/Ekran
    # görüntüsü 2026-08-26 203900.png). 250, viz katmanına SIKI BAĞLI değil
    # (bu dosya renderer.py'yi import etmez) — yalnızca aynı "tipik görünür
    # pencere" varsayımını paylaşan bağımsız bir varsayılan.
    profile_window_bars: int = 250
    profile_bins: int = 24
    profile_va_pct: float = 0.70
    volume_ma_window: int = 20
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    rsi_period: int = 14
    hvn_top_n: int = 3
    hvn_min_ratio: float = 0.55


class PriceStructure(BaseIndicator):
    """Trend çizgileri + konsolidasyon kutuları + destek/direnç bölgeleri +
    hacim profili + hacim/MACD serileri."""

    meta = IndicatorMeta(
        name="structure.price_structure",
        version="0.1.0",
        category="structure",
        description="Trendlines, ranges, zones, hacim profili ve MACD/hacim serileri.",
        supported_timeframes=(Timeframe.D1, Timeframe.H4),
    )

    def __init__(self, params: PriceStructureParams | None = None) -> None:
        self.params: PriceStructureParams = params or PriceStructureParams()

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        p = self.params
        # Faz 0.5 (A1) session notu: `_trendlines`'ın candidate-havuzuna
        # `significant_pivots`'un ALTERNATİFLENMİŞ/SEYRELTİLMİŞ çıktısını
        # vermek `scripts/sistemik_denetim.py`'nin gerçek BIST ölçümünde
        # `patterns.wedge`/`patterns.broadening` için ciddi bir yanlış-
        # pozitif ARTIŞINA yol açtığı bulundu (bkz. o dosyaların docstring'i,
        # docs/spec/SISTEMIK_DENETIM_v1.md) -- `build_trendlines` + geometrik
        # yakınsama/ıraksama testi SEYREK pivotlarla anlamını yitiriyor (az
        # nokta neredeyse her zaman "geçerli" bir çizgiye oturuyor). Bu
        # modülün trendline'ları AYNI `build_trendlines` mekanizmasını
        # paylaştığı için (ayrıca ölçülmedi ama tutarlılık/güvenlik için)
        # HER ZAMAN HAM `find_pivots` kullanır -- `zigzag_method`'dan
        # BAĞIMSIZ (o parametre yalnızca `_zones`'u etkiler, aşağı bakınız).
        #
        # `_zones` ise KENDİ, generic repaint_test'e HİÇ girmeyen ama BU
        # dosyanın kendi hedefli testiyle (`test_range_and_zone_signals_
        # are_repaint_consistent`) doğrulanan, GERÇEK bir non-repaint
        # garantisi taşıyor -- bu garanti, alternate_pivots'un "hangi pivot
        # kesinleşti" kararının df büyüdükçe DEĞİŞEBİLMESİNE (aynı aday
        # havuzu etkisi) DAYANIYOR OLMAMALI. Bu yüzden `_zones` KASITLI
        # OLARAK HAM (alternate_pivots'tan GEÇMEMİŞ) pivot adaylarını
        # kullanır -- find_pivots/atr_zigzag'in KENDİSİ, tek başına, ileri-
        # yalnızca (append-only) ve prefix-tutarlıdır.
        trend_pivots = find_pivots(df, p.pivot_left, p.pivot_right)
        zone_pivots = (
            atr_zigzag(df, atr_mult=p.atr_mult, atr_period=p.atr_period)
            if p.zigzag_method == "atr"
            else find_pivots(df, p.pivot_left, p.pivot_right)
        )

        lines, trendline_signals = _trendlines(df, trend_pivots, p)
        boxes_ranges, range_signals = _ranges(df, p)
        boxes_zones, zone_signals = _zones(df, zone_pivots, p)
        profile_levels, profile_series, poc_reclaimed_last_bar = _volume_profile(df, p)
        series = _volume_macd_rsi_series(df, p)
        osc_markers = _macd_cross_markers(series)

        last_state = _last_state(
            lines, boxes_ranges, boxes_zones, profile_levels, poc_reclaimed_last_bar, df
        )

        return IndicatorResult(
            indicator=self.meta.name, version=self.meta.version,
            params_hash=params_hash(p), symbol="", timeframe=Timeframe.D1,
            signals=trendline_signals + range_signals + zone_signals,
            levels=profile_levels,
            lines=lines,
            boxes=boxes_ranges + boxes_zones,
            markers=osc_markers,
            series={**series, **profile_series},
            series_layout={
                "hacim": ["volume", "volume_ma"],
                "macd": ["macd", "macd_signal", "macd_hist"],
                "rsi": ["rsi_14"],
            },
            last_state=last_state,
        )


def _trendline_label(line: Trendline, df: pd.DataFrame) -> str:
    kind_tr = "Direnç" if line.kind == "resistance" else "Destek"
    if line.broken_at is not None:
        date_str = pd.Timestamp(df.index[line.broken_at]).date().isoformat()
        return f"Kırılım {date_str} (Temas:{len(line.touches)})"
    return f"{kind_tr} (Temas:{len(line.touches)})"


def _trendlines(
    df: pd.DataFrame, pivots: list[Pivot], p: PriceStructureParams
) -> tuple[list[Line], list[Signal]]:
    lines: list[Line] = []
    signals: list[Signal] = []
    for kind in ("resistance", "support"):
        trendlines = build_trendlines(
            df, pivots, kind, p.trendline_min_touches, p.trendline_tol_atr,
            p.trendline_confirm_bars, p.atr_period, p.trendline_max_lines,
        )
        for tl in trendlines:
            lines.append(
                Line(
                    points=((tl.p1.bar_time, tl.p1.price), (tl.p2.bar_time, tl.p2.price)),
                    label=_trendline_label(tl, df), style=kind, extend_right=True,
                )
            )
            if tl.broken_at is not None:
                # build_trendlines'ın "beyond" tanımı: resistance (high
                # pivotlarından çizilir) kırılımı close > line_val (YUKARI,
                # boğa); support (low pivotlarından) kırılımı close < line_val
                # (AŞAĞI, ayı). Önceki sürüm bunu ters atıyordu (Faz 8A'da
                # breakouts.py yazılırken bulunan gerçek bir hata — hiçbir
                # test direction alanını doğrulamıyordu).
                direction: Direction = "long" if kind == "resistance" else "short"
                signals.append(
                    Signal(
                        bar_time=df.index[tl.broken_at], detected_at=df.index[tl.broken_at],
                        direction=direction, state="confirmed", score=1.0,
                        payload={
                            "event": "trendline_breakout", "kind": kind,
                            "touches": len(tl.touches),
                        },
                    )
                )
    return lines, signals


def _ranges(df: pd.DataFrame, p: PriceStructureParams) -> tuple[list[Box], list[Signal]]:
    boxes: list[Box] = []
    signals: list[Signal] = []
    ranges = detect_ranges(
        df, p.range_min_bars, p.range_atr_mult, p.range_breakout_confirm, p.atr_period
    )
    for rng in ranges:
        boxes.append(
            Box(
                t0=rng.t0_time, t1=rng.t1_time, low=rng.low, high=rng.high,
                label="Konsolidasyon", style="range_box",
            )
        )
        if rng.breakout_idx is not None:
            direction: Direction = "long" if rng.breakout_direction == "up" else "short"
            signals.append(
                Signal(
                    bar_time=df.index[rng.breakout_idx], detected_at=df.index[rng.breakout_idx],
                    direction=direction, state="confirmed", score=1.0,
                    payload={"event": "range_breakout", "direction": rng.breakout_direction},
                )
            )
    return boxes, signals


def _zones(
    df: pd.DataFrame, pivots: list[Pivot], p: PriceStructureParams
) -> tuple[list[Box], list[Signal]]:
    boxes: list[Box] = []
    signals: list[Signal] = []
    last_time = df.index[-1]

    for kind, style in (("high", "resistance_zone"), ("low", "support_zone")):
        kind_pivots = [pv for pv in pivots if pv.kind == kind]
        zones = cluster_zones(
            df, kind_pivots, p.zone_min_pivots, p.zone_band_atr,
            p.zone_breakout_confirm, p.atr_period,
        )
        for zone in zones:
            t1 = df.index[zone.broken_at] if zone.broken_at is not None else last_time
            boxes.append(
                Box(
                    t0=zone.formed_time, t1=t1, low=zone.low, high=zone.high,
                    label=style, style=style,
                )
            )
            for t in zone.touches:
                direction: Direction = "short" if kind == "high" else "long"
                signals.append(
                    Signal(
                        bar_time=df.index[t], detected_at=df.index[t], direction=direction,
                        state="active", score=1.0, payload={"event": "zone_touch", "kind": style},
                    )
                )
            if zone.broken_at is not None:
                direction = "long" if zone.broken_direction == "up" else "short"
                signals.append(
                    Signal(
                        bar_time=df.index[zone.broken_at], detected_at=df.index[zone.broken_at],
                        direction=direction, state="confirmed", score=1.0,
                        payload={"event": "zone_break", "kind": style},
                    )
                )
    return boxes, signals


def _volume_profile(
    df: pd.DataFrame, p: PriceStructureParams
) -> tuple[list[Level], dict[str, pd.Series], bool]:
    n = len(df)
    window_bars = min(p.profile_window_bars, n)
    if window_bars < 2:
        return [], {}, False

    window_start = n - window_bars
    window = df.iloc[window_start:]
    vp = compute_profile(window, p.profile_bins, p.profile_va_pct)
    window_start_time = df.index[window_start]

    levels = [
        Level(price=vp.poc, label="POC", style="poc", start=window_start_time),
        Level(price=vp.value_area_high, label="VAH", style="value_area", start=window_start_time),
        Level(price=vp.value_area_low, label="VAL", style="value_area", start=window_start_time),
    ]

    price_index = pd.Index(vp.price_bins, name="price")
    hvn_idx = set(find_hvn_nodes(vp.volumes, p.hvn_top_n, p.hvn_min_ratio))
    series: dict[str, pd.Series] = {
        "vp_bins": pd.Series(vp.price_bins, index=price_index),
        "vp_volumes": pd.Series(vp.volumes, index=price_index),
        "vp_hvn": pd.Series(
            [1.0 if i in hvn_idx else 0.0 for i in range(len(vp.price_bins))], index=price_index
        ),
    }
    if vp.gaussian_mu is not None and vp.gaussian_sigma is not None:
        amplitude = max(vp.volumes) if vp.volumes else 0.0
        gauss_values = amplitude * np.exp(
            -0.5 * ((np.array(vp.price_bins) - vp.gaussian_mu) / vp.gaussian_sigma) ** 2
        )
        series["vp_gauss"] = pd.Series(gauss_values, index=price_index)

    reclaimed_last_bar = False
    if n >= 2:
        prev_c, cur_c = float(df["close"].iloc[-2]), float(df["close"].iloc[-1])
        reclaimed_last_bar = prev_c < vp.poc <= cur_c or prev_c > vp.poc >= cur_c
    return levels, series, reclaimed_last_bar


def _volume_macd_rsi_series(df: pd.DataFrame, p: PriceStructureParams) -> dict[str, pd.Series]:
    macd_result = compute_macd(df["close"], p.macd_fast, p.macd_slow, p.macd_signal)
    return {
        "volume": df["volume"],
        "volume_ma": sma(df["volume"], p.volume_ma_window),
        "macd": macd_result.macd,
        "macd_signal": macd_result.signal,
        "macd_hist": macd_result.histogram,
        "rsi_14": compute_rsi(df["close"], p.rsi_period),
    }


def _macd_cross_markers(series: dict[str, pd.Series]) -> list[Marker]:
    if "macd" not in series or "macd_signal" not in series:
        return []
    crosses = crossovers(series["macd"], series["macd_signal"])
    markers: list[Marker] = []
    for t, direction in crosses.items():
        if pd.isna(direction):
            continue
        text = "MACD ↑" if direction == "up" else "MACD ↓"
        price = float(series["macd"].loc[t])
        markers.append(Marker(t=t, price=price, text=text, kind="macd_cross"))
    return markers


def _last_state(
    lines: list[Line], range_boxes: list[Box], zone_boxes: list[Box],
    profile_levels: list[Level], poc_reclaimed_last_bar: bool, df: pd.DataFrame,
) -> dict:
    active_lines = sum(1 for ln in lines if "Kırılım" not in ln.label)
    last_close = float(df["close"].iloc[-1])
    open_box = any(b.style == "range_box" and b.t1 == df.index[-1] for b in range_boxes)

    zone_position = "dışında"
    for b in zone_boxes:
        if b.low <= last_close <= b.high:
            zone_position = "içinde"
            break

    poc = next((lv.price for lv in profile_levels if lv.label == "POC"), None)
    poc_distance = abs(last_close - poc) if poc is not None else None

    return {
        "active_trendlines": active_lines,
        "open_range_box": open_box,
        "price_vs_zone": zone_position,
        "poc_distance": poc_distance,
        "poc_reclaimed_last_bar": poc_reclaimed_last_bar,
    }
