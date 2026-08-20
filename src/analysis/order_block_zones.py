"""Order Block / Arz-Talep Bolgesi (Supply-Demand Zone) Tespiti -- SMC/ICT
literaturunun tam algoritmik tanimi. SAF MATEMATIK, I/O YOK (`abcd_pattern.py`
ile AYNI katman ilkesi).

Kaynak (2026-08-20, kullanicinin masaustu arastirmasi -- rally_precursor
kesif calismasi icin "supply demand zones" talebi): `ABCD formasyonu/
01_OrderBlock_Zone_Architecture_V3.2.md`. Bu, projedeki DIGER strateji
kaynaklarindan (kitap ozetleri, genel raporlar) FARKLI olarak TAM, kesin,
OHLCV-hesaplanabilir bir 3-asamali algoritma icerir -- "belki boyle
olabilir" DEGIL, somut esik degerleriyle tanimlanmis bir spesifikasyon.

## 3 Asamali Tespit (kaynak dokumandaki TANIM, degistirilmeden kodlandi)

1. **TABAN (base)**: N=5-8 ardisik bar, `(en_yuksek_high - en_dusuk_low) <=
   1.5*ATR14` (sikisma/konsolidasyon), HICBIR barin govdesi `1.5*ort_govde
   (son 50 bar)`i ASMAZ (sakin bar'lar).
2. **YER DEGISTIRME (displacement)**: taban BITTIKTEN 1-3 bar SONRA,
   govde `>= 2.0*ATR14` VE govde/aralik orani `>= 0.6` (guclu, kararli
   mum) VE kapanis tabanin disina `0.3*ATR` tasar (yukselen: `close >
   taban_high + 0.3*ATR`). Kalite bonusu: Fair Value Gap (FVG, 3-bar
   doldurulmamis bosluk: `low[t] > high[t-2]`) VARSA.
3. **KOKEN MUMU (origin) + bolge sinirlari**: yer-degistirmenin BASLADIGI
   bardan geriye (<=5 bar) SON TERS renkli mumu (yukselen yer-degistirme
   icin SON kirmizi/dusen mum) bul -- bu "Bullish Order Block/Talep
   Bolgesi"nin KOKENIDIR. Bolge tavani = koken mumun high'i, tabani =
   koken mumun low'u. Bulunamazsa (5 bar icinde ters mum yok): tabanin
   EN DUSUK barini FALLBACK olarak kullan.

## Bolge Yasam Dongusu (mitigation state machine)

Bir bolge, olusumundan (`origin_bar`) SONRAKI her barda 3 durumdan birinde:
  - `UNMITIGATED`: fiyat bolgeye HIC DEGMEDI (en kaliteli).
  - `TESTED`: fiyat bolgeye GIRDI ama KAPANIS bolgenin DISINDA kaldi
    (kaynak dokuman ACIKCA fitil-tabanli DEGIL, KAPANIS-tabanli kontrol
    onerir -- fitil dokunuslari YANLIS-mitigation sayilmasin diye).
  - `MITIGATED`: fiyat KAPANISI bolgenin ICINDEN GECTI (gecersiz).

## Kalite Skoru (kaynak dokumandaki agirliklar, MTF bonusu HARIC --
bu modul TEK zaman dilimi calisir, "coklu-zaman-dilimi bolge ortusumu"
+15 puani bu yuzden UYGULANAMAZ, ULASILABILIR MAKSIMUM 85/100):
  +25 FVG var · +20 yer-degistirme hacmi > 1.5x(50-bar ort) · +15 taban
  >=5 bar · +15 hic test edilmemis · +10 yer-degistirme bir yapisal
  swing noktasini kirdi (pivot_high'i asti). Esik: kaynak dokuman
  `>=50` onerir -- bu modulde ayni MUTLAK esik korunur (ulasilabilir
  85 uzerinden, oransal olarak biraz daha SIKI bir filtre, BILINCLI
  -- MTF onayi olmadan tek-TF bolgelerin daha temkinli degerlendirilmesi
  makul)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.analysis.abcd_pattern import atr_wilder, pivot_high, pivot_low

OHLC_COLUMNS = ("time", "open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class Params:
    base_min_bars: int = 5
    base_max_bars: int = 8
    base_range_atr_mult: float = 1.5
    base_body_mult: float = 1.5  # ort. govdenin (50 bar) bu katini asan bar TABAN DISI sayilir
    displacement_atr_mult: float = 2.0
    displacement_body_range_ratio: float = 0.6
    displacement_close_beyond_atr: float = 0.3
    displacement_max_bars_after_base: int = 3
    origin_search_bars: int = 5
    fvg_bonus: int = 25
    volume_bonus: int = 20
    volume_bonus_mult: float = 1.5
    base_length_bonus: int = 15
    untested_bonus: int = 15
    structure_break_bonus: int = 10
    quality_threshold: int = 50


@dataclass(frozen=True)
class OrderBlockZone:
    origin_bar: int
    displacement_bar: int
    zone_low: float
    zone_high: float
    quality: int
    has_fvg: bool
    base_bars: int


def _find_bullish_order_blocks(df: pd.DataFrame, params: Params = Params()) -> list[OrderBlockZone]:
    """Serinin TAMAMINI (causal degil -- bu fonksiyon TUM gecmisi tarar,
    `zone_state_at`in KENDISI causal'dir, bkz. asagisi) tarayip TUM
    (gecmis, tekrar-hesaplamaya gerek kalmadan) yukselen Order Block'lari
    doner. Performans: tek gecis, `harmonic_confirmation.py`nin "TEK SEFER
    hesapla" ilkesiyle AYNI."""
    n = len(df)
    open_ = df["open"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    volume = df["volume"].to_numpy(dtype=float)
    atr14 = atr_wilder(df, 14)

    body = np.abs(close - open_)
    avg_body_50 = pd.Series(body).rolling(50, min_periods=20).mean().to_numpy()
    avg_vol_50 = pd.Series(volume).rolling(50, min_periods=20).mean().to_numpy()
    ph = pivot_high(high, 5)

    zones: list[OrderBlockZone] = []

    for base_len in range(params.base_min_bars, params.base_max_bars + 1):
        for base_start in range(0, n - base_len):
            base_end = base_start + base_len - 1  # dahil
            atr_at_base_end = atr14[base_end]
            if np.isnan(atr_at_base_end) or atr_at_base_end <= 0 or np.isnan(avg_body_50[base_end]):
                continue
            base_high = float(high[base_start : base_end + 1].max())
            base_low = float(low[base_start : base_end + 1].min())
            if (base_high - base_low) > params.base_range_atr_mult * atr_at_base_end:
                continue
            base_bodies = body[base_start : base_end + 1]
            if np.any(base_bodies > params.base_body_mult * avg_body_50[base_end]):
                continue

            for disp_bar in range(base_end + 1, min(base_end + 1 + params.displacement_max_bars_after_base, n)):
                atr_at_disp = atr14[disp_bar]
                if np.isnan(atr_at_disp) or atr_at_disp <= 0:
                    continue
                disp_body = body[disp_bar]
                disp_range = high[disp_bar] - low[disp_bar]
                if disp_range <= 0:
                    continue
                is_bullish_disp = close[disp_bar] > open_[disp_bar]
                if not is_bullish_disp:
                    continue
                if disp_body < params.displacement_atr_mult * atr_at_disp:
                    continue
                if (disp_body / disp_range) < params.displacement_body_range_ratio:
                    continue
                if close[disp_bar] <= base_high + params.displacement_close_beyond_atr * atr_at_disp:
                    continue

                # KOKEN: yer-degistirmeden GERIYE (<=origin_search_bars) SON kirmizi mum.
                origin_bar = None
                for j in range(disp_bar - 1, max(disp_bar - 1 - params.origin_search_bars, -1), -1):
                    if close[j] < open_[j]:
                        origin_bar = j
                        break
                if origin_bar is None:
                    origin_bar = int(base_start + np.argmin(low[base_start : base_end + 1]))
                    zone_low, zone_high = float(low[origin_bar]), float(high[origin_bar])
                else:
                    zone_low, zone_high = float(low[origin_bar]), float(high[origin_bar])

                has_fvg = disp_bar >= 2 and low[disp_bar] > high[disp_bar - 2]
                vol_ok = not np.isnan(avg_vol_50[disp_bar]) and avg_vol_50[disp_bar] > 0 and volume[disp_bar] > params.volume_bonus_mult * avg_vol_50[disp_bar]
                broke_structure = not np.isnan(ph[disp_bar]) if disp_bar < len(ph) else False
                # 'broke_structure': bu barda YENI bir pivot-high ONAYLANDIYSA
                # (ph[disp_bar] NaN degil), yer-degistirme YAKIN GECMISTE bir
                # yapisal swing'i asmis olabilir -- kaba ama nedensel-yonlu bir
                # yaklasiklik (kesin "hangi swing'i astı" takibi KAPSAM DISI).

                quality = 0
                if has_fvg:
                    quality += params.fvg_bonus
                if vol_ok:
                    quality += params.volume_bonus
                if base_len >= 5:
                    quality += params.base_length_bonus
                quality += params.untested_bonus  # olusum aninda HENUZ test edilmedi (asagida zone_state_at GUNCEL durumu kontrol eder)
                if broke_structure:
                    quality += params.structure_break_bonus

                zones.append(
                    OrderBlockZone(
                        origin_bar=origin_bar, displacement_bar=disp_bar,
                        zone_low=zone_low, zone_high=zone_high,
                        quality=quality, has_fvg=has_fvg, base_bars=base_len,
                    )
                )
                break  # bu taban icin ilk gecerli yer-degistirme yeterli

    # Farkli `base_len` denemeleri AYNI (origin_bar, displacement_bar) ciftini
    # tekrar tekrar bulabilir (ortusen taban pencereleri) -- EN YUKSEK
    # kaliteliyi tut, geri kalanini AT (tekilleştirme, dogruluk ETKILENMEZ).
    best_by_key: dict[tuple[int, int], OrderBlockZone] = {}
    for z in zones:
        key = (z.origin_bar, z.displacement_bar)
        if key not in best_by_key or z.quality > best_by_key[key].quality:
            best_by_key[key] = z
    return sorted(best_by_key.values(), key=lambda z: z.displacement_bar)


def zone_state_at(zone: OrderBlockZone, close: np.ndarray, as_of_bar: int) -> str:
    """`zone`in `as_of_bar`DAKI (dahil) durumu -- `UNMITIGATED`/`TESTED`/
    `MITIGATED`. KAPANIS-tabanli (kaynak dokumanin ACIK onerisi, fitil
    DEGIL). SADECE `close[:as_of_bar+1]` kullanir -- causal/look-ahead
    guvenli (bkz. modul ust notu)."""
    if as_of_bar < zone.displacement_bar:
        return "UNMITIGATED"
    segment = close[zone.displacement_bar : as_of_bar + 1]
    if np.any(segment < zone.zone_low):
        return "MITIGATED"
    if np.any((segment >= zone.zone_low) & (segment <= zone.zone_high)):
        return "TESTED"
    return "UNMITIGATED"


def nearest_unmitigated_zone(
    zones: list[OrderBlockZone], close: np.ndarray, as_of_bar: int, price: float, atr_val: float | None,
    min_quality: int = Params().quality_threshold,
) -> tuple[OrderBlockZone, float] | None:
    """`as_of_bar`da (causal) HALA UNMITIGATED olan, kalite esigini gecen
    bolgeler arasindan `price`e EN YAKIN olani + ATR-normalize mesafesini
    doner. Hicbiri yoksa `None`. `zones[i].displacement_bar > as_of_bar`
    olan (henuz OLUSMAMIS) bolgeler ZATEN elenir (bkz. asagisi)."""
    if atr_val is None or not np.isfinite(atr_val) or atr_val <= 0:
        return None
    best: tuple[OrderBlockZone, float] | None = None
    for zone in zones:
        if zone.displacement_bar > as_of_bar:
            continue
        if zone.quality < min_quality:
            continue
        if zone_state_at(zone, close, as_of_bar) != "UNMITIGATED":
            continue
        if price < zone.zone_low:
            dist = zone.zone_low - price
        elif price > zone.zone_high:
            dist = price - zone.zone_high
        else:
            dist = 0.0
        dist_atr = dist / atr_val
        if best is None or dist_atr < best[1]:
            best = (zone, dist_atr)
    return best
