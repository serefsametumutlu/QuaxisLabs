"""Momentum Confluence -- KOŞUL ABLASYONU (hangi bileşeni ekleyip/çıkarsak
win rate/profit factor nasıl değişir) ARAŞTIRMASI icin AYRI, deneysel modul.

Kullanici talebi (2026-08-19): "en iyi kombinasyonlari bulmamiz gerekiyor
hangi zaman diliminde en iyisi kosullara ne ekleyip ne cikarsak daha saglam
win rate orani ve profit orani yuksek sinyaller yakalayabiliriz".

Neden `momentum_confluence.py`nin ICINE eklenmedi (harmonic_xabcd.py'nin
abcd_pattern.py'ye yaptigi AYNI ayrim): o modulun docstring'i acikca "Pine
kaynagiyla LOCKSTEP, Pine'da OLMAYAN bir filtre EKLENMEZ" der -- V1/V2
detect() FONKSIYONLARI kullanicinin TradingView'da GORDUGU indikatorlerle
birebir ayni kalmali. Bu modul ise BILEREK Pine'da OLMAYAN kombinasyonlari
(orn. "hacim filtresi olmadan", "sadece WaveTrend onayiyla", "hacim oranina
UST SINIR koyarak") dener -- research amaçli, indikatorun KENDISI DEGIL.

TRF/EMA/WaveTrend/hacim hesaplama mantigi `momentum_confluence.py`den
KOPYALANMISTIR (o modulun ozel/alt-cizgili yardimcilarini disaridan import
etmek katman/kapsulleme ihlali olurdu) -- degisen SADECE hangi kosullarin
`confluence` bayragina DAHIL EDILDIGI, cekirdek matematik AYNI kalir.

Metodoloji: `docs/spec/MOMENTUM_CONFLUENCE_BACKTEST.md`deki AYNI TP/SL
(1.5xATR SL, 1R/2R kismi cikis) + AYNI `min_trades_show`/`trustworthy`
disiplini (kucuk n asla gizlenmez, "GUVENSIZ" etiketlenir).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.analysis.abcd_pattern import atr_wilder
from src.analysis.momentum_confluence import Params, Signal

OHLC_COLUMNS = ("time", "open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class VariantFlags:
    """Hangi kosullarin `confluence` bayragina dahil edildigini kontrol
    eder -- her biri bagimsiz acilip/kapatilabilir (V1/V2'nin sabit
    kombinasyonlarinin OTESINDE, kullanicinin "neyi ekleyip cikarsak"
    sorusuna cevap vermek icin)."""

    name: str
    require_volume: bool = True
    vol_mult: float | None = None  # None -> params.vol_mult kullanilir
    vol_ratio_max: float | None = None  # UST SINIR (faktor analizi bulgusu: asiri hacim kazanmiyor)
    require_wavetrend: bool = False
    require_green_candle: bool = False
    require_strict_ema: bool = False  # ema5>=ema8 VE close>=ema5*ema_above_pct


def _sma(values: np.ndarray, length: int) -> np.ndarray:
    return pd.Series(values).rolling(length).mean().to_numpy()


def _ema(values: np.ndarray, span: int) -> np.ndarray:
    """`momentum_confluence._ema` ile BIREBIR ayni (NaN-seed duzeltmesi
    dahil) -- bkz. o modulun ust notu, buraya KOPYALANDI (katman ayrimi)."""
    n = len(values)
    out = np.full(n, np.nan)
    if n == 0:
        return out
    alpha = 2.0 / (span + 1)
    start = 0
    while start < n and np.isnan(values[start]):
        start += 1
    if start == n:
        return out
    out[start] = values[start]
    for i in range(start + 1, n):
        if np.isnan(values[i]):
            out[i] = out[i - 1]
        else:
            out[i] = out[i - 1] + (values[i] - out[i - 1]) * alpha
    return out


def _compute_trf(src: np.ndarray, per1: int, mult1: float, per2: int, mult2: float) -> tuple[np.ndarray, np.ndarray]:
    n = len(src)
    diff = np.zeros(n)
    diff[1:] = np.abs(src[1:] - src[:-1])
    smrng1 = _ema(_ema(diff, per1), per1 * 2 - 1) * mult1
    smrng2 = _ema(_ema(diff, per2), per2 * 2 - 1) * mult2
    smrng = (smrng1 + smrng2) / 2.0

    filt = np.empty(n)
    upward = np.zeros(n)
    for i in range(n):
        prev_filt = filt[i - 1] if i > 0 else src[i]
        if src[i] > prev_filt:
            candidate = src[i] - smrng[i]
            filt[i] = prev_filt if candidate < prev_filt else candidate
        else:
            candidate = src[i] + smrng[i]
            filt[i] = prev_filt if candidate > prev_filt else candidate
        if i == 0:
            continue
        if filt[i] > filt[i - 1]:
            upward[i] = upward[i - 1] + 1
        elif filt[i] < filt[i - 1]:
            upward[i] = 0.0
        else:
            upward[i] = upward[i - 1]
    return filt, upward


def _compute_wavetrend(high: np.ndarray, low: np.ndarray, close: np.ndarray, chan_len: int, avg_len: int, smooth: int) -> tuple[np.ndarray, np.ndarray]:
    ap = (high + low + close) / 3.0
    esa = _ema(ap, chan_len)
    d = _ema(np.abs(ap - esa), chan_len)
    with np.errstate(divide="ignore", invalid="ignore"):
        ci = np.where(d != 0, (ap - esa) / (0.015 * d), np.nan)
    wt1 = _ema(ci, avg_len)
    wt2 = _sma(wt1, smooth)
    return wt1, wt2


def detect_variant(df: pd.DataFrame, params: Params, flags: VariantFlags) -> list[Signal]:
    """TRF flip tetiklendiginde, `flags`in ACTIVE ettigi kosullarin HEPSI
    saglaniyorsa sinyal uretir. EMA sikisma+kirilim (`is_squeezed`+
    `ema_breakout`) HER ZAMAN zorunludur (bu, "Momentum Confluence"
    kimliginin cekirdegidir -- TAMAMEN kaldirilirsa artik bu indikator
    OLMAZ, farkli bir strateji olurdu)."""
    n = len(df)
    time_col = df["time"]
    open_ = df["open"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    volume = df["volume"].to_numpy(dtype=float)

    filt, upward = _compute_trf(close, params.per1, params.mult1, params.per2, params.mult2)
    downward = np.zeros(n)
    for i in range(1, n):
        if filt[i] < filt[i - 1]:
            downward[i] = downward[i - 1] + 1
        elif filt[i] > filt[i - 1]:
            downward[i] = 0.0
        else:
            downward[i] = downward[i - 1]

    ema5 = _ema(close, params.ema_fast)
    ema8 = _ema(close, params.ema_mid)
    ema13 = _ema(close, params.ema_slow)
    ema_max = np.maximum.reduce([ema5, ema8, ema13])
    ema_min = np.minimum.reduce([ema5, ema8, ema13])
    with np.errstate(divide="ignore", invalid="ignore"):
        ema_spread = np.where(ema_min != 0, (ema_max - ema_min) / ema_min * 100.0, np.nan)

    vol_sma = _sma(volume, params.vol_len)
    with np.errstate(divide="ignore", invalid="ignore"):
        vol_ratio = np.where(vol_sma > 0, volume / vol_sma, np.nan)

    atr14 = atr_wilder(df, 14)

    wt1 = wt2 = None
    if flags.require_wavetrend:
        wt1, wt2 = _compute_wavetrend(high, low, close, params.wt_chan_len, params.wt_avg_len, params.wt_smooth)

    vol_mult_eff = flags.vol_mult if flags.vol_mult is not None else params.vol_mult

    cond_ini = 0
    signals: list[Signal] = []

    for i in range(n):
        if i == 0:
            long_cond = False
        else:
            src_gt_filt = close[i] > filt[i]
            src_gt_prev = close[i] > close[i - 1]
            src_lt_prev = close[i] < close[i - 1]
            long_cond = (src_gt_filt and src_gt_prev and upward[i] > 0) or (src_gt_filt and src_lt_prev and upward[i] > 0)

        prev_cond_ini = cond_ini
        if i > 0:
            src_lt_filt = close[i] < filt[i]
            short_cond = (src_lt_filt and close[i] < close[i - 1] and downward[i] > 0) or (
                src_lt_filt and close[i] > close[i - 1] and downward[i] > 0
            )
        else:
            short_cond = False
        cond_ini = 1 if long_cond else (-1 if short_cond else cond_ini)
        trf_long_trigger = long_cond and prev_cond_ini == -1

        if not trf_long_trigger or i < 1:
            continue

        is_squeezed = not np.isnan(ema_spread[i]) and ema_spread[i] <= params.squeeze_pct
        ema_breakout = close[i] > ema_max[i] and close[i - 1] <= ema_max[i - 1]
        if not (is_squeezed and ema_breakout):
            continue

        if flags.require_strict_ema:
            if not (ema5[i] >= ema8[i] and close[i] >= ema5[i] * params.ema_above_pct):
                continue

        if flags.require_volume:
            if np.isnan(vol_ratio[i]) or volume[i] < vol_mult_eff * vol_sma[i]:
                continue
        if flags.vol_ratio_max is not None:
            if np.isnan(vol_ratio[i]) or vol_ratio[i] > flags.vol_ratio_max:
                continue

        if flags.require_wavetrend:
            wt_exact_cross = i >= 1 and wt1[i - 1] < wt2[i - 1] and wt1[i] > wt2[i]
            wt_prior_history = i >= 2 and wt1[i - 1] < wt2[i - 1] and wt1[i - 2] < wt2[i - 2]
            wt_level_ok = not np.isnan(wt1[i]) and wt1[i] < params.wt_max_lvl
            if not (wt_exact_cross and wt_prior_history and wt_level_ok):
                continue

        if flags.require_green_candle and not (close[i] > open_[i]):
            continue

        entry_ref = float(close[i])
        fill_bar = i + 1
        fill_ref = float(open_[fill_bar]) if fill_bar < n else float("nan")

        atr_at_signal = atr14[i]
        if np.isnan(atr_at_signal) or atr_at_signal <= 0:
            continue

        sl = entry_ref - params.atr_mult * atr_at_signal
        risk = entry_ref - sl
        tp1 = entry_ref + 1.0 * risk
        tp2 = entry_ref + 2.0 * risk

        signals.append(
            Signal(
                direction=1,
                signal_bar=i,
                signal_time=time_col.iloc[i],
                entry_ref=entry_ref,
                fill_ref=fill_ref,
                tp1=float(tp1), tp2=float(tp2), sl=float(sl),
                ema_spread_pct=float(ema_spread[i]) if not np.isnan(ema_spread[i]) else float("nan"),
                volume_ratio=float(vol_ratio[i]) if not np.isnan(vol_ratio[i]) else float("nan"),
                downward_streak_before_flip=int(downward[i - 1]) if i > 0 else 0,
                wt1_at_signal=float(wt1[i]) if wt1 is not None and not np.isnan(wt1[i]) else float("nan"),
            )
        )

    return signals


# --- Arastirilacak varyantlar (kullanici sorusuna dogrudan cevap: "neyi
#     eklesek/cikarsak") -- V1/V2'nin SABIT kombinasyonlarinin OTESINDE,
#     her degisikligin TEK BASINA etkisini izole eder. -----------------------
VARIANTS: dict[str, VariantFlags] = {
    "V1_BASELINE": VariantFlags(name="V1_BASELINE", require_volume=True),
    "V1_HACIMSIZ": VariantFlags(name="V1_HACIMSIZ", require_volume=False),
    "V1_HACIM_BANDI": VariantFlags(name="V1_HACIM_BANDI", require_volume=True, vol_ratio_max=3.0),
    "V1_HACIM_GEVSEK": VariantFlags(name="V1_HACIM_GEVSEK", require_volume=True, vol_mult=1.2),
    "V1_ARTI_WT": VariantFlags(name="V1_ARTI_WT", require_volume=True, require_wavetrend=True),
    "V1_ARTI_YESIL": VariantFlags(name="V1_ARTI_YESIL", require_volume=True, require_green_candle=True),
    "V1_ARTI_SIKI_EMA": VariantFlags(name="V1_ARTI_SIKI_EMA", require_volume=True, require_strict_ema=True),
    "V2_BASELINE": VariantFlags(
        name="V2_BASELINE", require_volume=True, require_wavetrend=True,
        require_green_candle=True, require_strict_ema=True,
    ),
    "V2_YESILSIZ": VariantFlags(
        name="V2_YESILSIZ", require_volume=True, require_wavetrend=True,
        require_green_candle=False, require_strict_ema=True,
    ),
    "V2_GEVSEK_HACIM": VariantFlags(
        name="V2_GEVSEK_HACIM", require_volume=True, vol_mult=1.2, require_wavetrend=True,
        require_green_candle=True, require_strict_ema=True,
    ),
    "V2_ARTI_HACIM_BANDI": VariantFlags(
        name="V2_ARTI_HACIM_BANDI", require_volume=True, vol_ratio_max=3.0, require_wavetrend=True,
        require_green_candle=True, require_strict_ema=True,
    ),
}
