"""Momentum Confluence (TRF Flip + EMA Squeeze + Volume [+ WaveTrend, V2])
-- Pine parity, SAF MANTIK, I/O YOK.

Kaynak: `pine/momentum confluence 1.txt` (V1: TRF flip + EMA squeeze breakout
+ hacim patlaması) ve `pine/momentum confluence 2.txt` (V2: V1'in TÜMÜ +
WaveTrend kesişim onayı + yeşil mum filtresi + daha sıkı EMA sıralama/mesafe
koşulu -- bu yüzden V2 V1'den daha SEYREK sinyal üretir). İkisi de SADECE
LONG (kaynakta hiç SHORT/exit mantığı yok, `plotshape` ile görsel bir
indikatördür, strateji/backtest kodu İÇERMEZ) -- bu modül `abcd_pattern.py`
ile AYNI ilkeyle (Pine kaynağıyla LOCKSTEP, Pine'da OLMAYAN bir filtre
EKLENMEZ) tespit mantığını birebir taşır.

## TP/SL -- kaynakta YOK, bu modülde EKLENDİ (kullanıcı isteği, 2026-08-18)

Kaynak Pine dosyalarının HİÇBİRİNDE TP/SL/pozisyon yönetimi yoktur (saf
görsel indikatör). Kullanıcı "düzgün ve doğru bir biçimde TP ve SL noktaları
ekle" dedi -- bu modül, projenin GERİ KALANIYLA (abcd_pattern.py'nin ATR14
Wilder SL'i, abcd_backtest.py'nin 1R/2R kısmi-çıkış yapısı) TUTARLI, R-katlı
(risk-multiple) bir yapı kullanır, YENİ bir mantık İCAT ETMEZ:

    SL  = entry - atr_mult * ATR14(Wilder, sinyal barı)   (abcd_pattern.py
          ile AYNI ATR fonksiyonu, `src.analysis.abcd_pattern.atr_wilder`)
    risk = entry - SL
    TP1 = entry + 1.0 * risk   (1R)
    TP2 = entry + 2.0 * risk   (2R)

Bu, `abcd_backtest.py`'nin TP1/TP2 kısmi-çıkış motoruyla (duck-typing,
`direction`/`signal_bar`/`entry_ref`/`fill_ref`/`tp1`/`tp2`/`sl` alan
sözleşmesi) DOĞRUDAN uyumludur -- backtest motoru TEKRAR YAZILMAZ, aynen
`harmonic_xabcd.py`nin yaptığı gibi REUSE edilir.

Katman disiplini: `abcd_pattern.py` ile AYNI -- `src.fetchers.*`/`src.db.*`
HİÇBİR modülü import etmez, tamamen float + numpy/pandas (Pine float64
parity zorunluluğu).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.analysis.abcd_pattern import atr_wilder

OHLC_COLUMNS = ("time", "open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class Params:
    """Pine dosyalarındaki her `input.*` ile birebir aynı isim/varsayılan
    (iki dosya da AYNI TRF/EMA/Hacim varsayılanlarını paylaşır)."""

    # TRF (Twin Range Filter)
    per1: int = 12
    mult1: float = 1.0
    per2: int = 4
    mult2: float = 2.0
    # EMA Squeeze Breakout
    ema_fast: int = 5
    ema_mid: int = 8
    ema_slow: int = 13
    squeeze_pct: float = 1.0
    # Volume Surge
    vol_len: int = 20
    vol_mult: float = 1.5
    # WaveTrend (SADECE V2)
    wt_chan_len: int = 10
    wt_avg_len: int = 21
    wt_smooth: int = 4
    wt_max_lvl: float = 15.0
    # V2'ye özgü ek EMA sıkılığı (kaynakta sabit, burada parametrik yapıldı)
    ema_above_pct: float = 1.0075  # close >= ema5 * bu katsayı
    # Bu modülün EKLEDİĞİ (kaynakta olmayan) risk yönetimi
    atr_mult: float = 1.5


@dataclass(frozen=True)
class Signal:
    """Onaylanmış tek bir Momentum Confluence sinyali. Alan adları
    `abcd_pattern.Signal`/`harmonic_xabcd.Signal` ile UYUMLU (direction/
    signal_bar/entry_ref/fill_ref/tp1/tp2/sl) -- `abcd_backtest.backtest_symbol`
    HİÇBİR DEĞİŞİKLİK olmadan bu sinyallerle de çalışır (duck-typing)."""

    direction: int  # HER ZAMAN +1 (kaynakta SADECE LONG var)
    signal_bar: int
    signal_time: pd.Timestamp
    entry_ref: float
    fill_ref: float
    tp1: float
    tp2: float
    sl: float
    # --- teşhis/faktör-analizi alanları (kazanan/kaybeden ayrımı icin) ---
    ema_spread_pct: float  # sinyal anindaki EMA sikisma yuzdesi (dusuk = daha siki)
    volume_ratio: float  # hacim / SMA(hacim, vol_len)
    downward_streak_before_flip: int  # flip ONCESI kac bar dusustu (TRF)
    wt1_at_signal: float  # SADECE V2 -- V1'de NaN


def _sma(values: np.ndarray, length: int) -> np.ndarray:
    return pd.Series(values).rolling(length).mean().to_numpy()


def _ema(values: np.ndarray, span: int) -> np.ndarray:
    """Pine'in `ta.ema()` portu -- ilk deger ile seed edilen standart
    ussel hareketli ortalama (`abcd_factor_analysis._ema` ile AYNI tanim,
    burada BAGIMSIZ tutuldu ki bu modul `abcd_factor_analysis`a -- bir
    FAKTOR ANALIZI modulune -- bagimli OLMASIN, katman disiplini).

    CANLI HATA + DUZELTME (2026-08-18, kullanici canli test raporu: "V2
    hic sinyal uretmiyor"): WaveTrend'in `ci = (ap-esa)/(0.015*d)`
    hesabinda bar 0'da `d[0]=0` (esa bar 0'da ap[0]'a esitlenerek seed
    edildigi icin) `ci[0]` NaN doner (sifira bolme korumasi) -- eski
    `_ema`, `out[0] = values[0]` satiriyla bu TEK NaN'i seed olarak
    aliyordu, ardindan `out[i] = out[i-1] + (...)*alpha` formulu NaN'i
    SONSUZA KADAR yayiyordu (NaN + herhangi bir sayi = NaN) -- sonuc:
    wt1/wt2 serisinin TAMAMI NaN, WaveTrend onayi HICBIR ZAMAN
    saglanamiyordu (V2'nin 0 sinyal uretmesinin kok nedeni buydu, sadece
    "V2 daha siki" degil). Simdi: ilk NaN-olmayan degerle seed edilir,
    aradaki (ve sonraki tekil) NaN girdilerde onceki EMA degeri KORUNUR
    (Pine'in na-atlama davranisiyla tutarli, `atr_wilder`'in bar-0
    fallback ilkesiyle AYNI ruhta)."""
    n = len(values)
    out = np.full(n, np.nan)
    if n == 0:
        return out
    alpha = 2.0 / (span + 1)
    start = 0
    while start < n and np.isnan(values[start]):
        start += 1
    if start == n:
        return out  # tum seri NaN
    out[start] = values[start]
    for i in range(start + 1, n):
        if np.isnan(values[i]):
            out[i] = out[i - 1]
        else:
            out[i] = out[i - 1] + (values[i] - out[i - 1]) * alpha
    return out


def _compute_trf(src: np.ndarray, per1: int, mult1: float, per2: int, mult2: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Twin Range Filter (`filt`) + `upward`/`downward` sayaclarini doner
    -- Pine kaynagindaki BIREBIR ayni state machine (bkz. modul ust notu)."""
    n = len(src)
    diff = np.zeros(n)
    diff[1:] = np.abs(src[1:] - src[:-1])  # bar 0: onceki close yok -> 0 (atr_wilder ile AYNI ilke)

    smrng1 = _ema(_ema(diff, per1), per1 * 2 - 1) * mult1
    smrng2 = _ema(_ema(diff, per2), per2 * 2 - 1) * mult2
    smrng = (smrng1 + smrng2) / 2.0

    filt = np.empty(n)
    upward = np.zeros(n)
    downward = np.zeros(n)

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

        if filt[i] < filt[i - 1]:
            downward[i] = downward[i - 1] + 1
        elif filt[i] > filt[i - 1]:
            downward[i] = 0.0
        else:
            downward[i] = downward[i - 1]

    return filt, upward, downward


def _compute_wavetrend(high: np.ndarray, low: np.ndarray, close: np.ndarray, chan_len: int, avg_len: int, smooth: int) -> tuple[np.ndarray, np.ndarray]:
    """LazyBear WaveTrend Oscillator portu (`wt1`, `wt2`) -- SADECE V2."""
    ap = (high + low + close) / 3.0
    esa = _ema(ap, chan_len)
    d = _ema(np.abs(ap - esa), chan_len)
    with np.errstate(divide="ignore", invalid="ignore"):
        ci = np.where(d != 0, (ap - esa) / (0.015 * d), np.nan)
    wt1 = _ema(ci, avg_len)
    wt2 = _sma(wt1, smooth)
    return wt1, wt2


def detect(df: pd.DataFrame, params: Params, variant: str = "v1") -> list[Signal]:
    """`variant`: "v1" (TRF flip + EMA squeeze + hacim) veya "v2" (v1'in
    TÜMÜ + WaveTrend kesişim onayı + yeşil mum + daha siki EMA sirali/mesafe
    kosulu -- bkz. modul ust notu). `df` kolonlari [time, open, high, low,
    close, volume], artan zamana sirali."""
    if variant not in ("v1", "v2"):
        raise ValueError(f"Bilinmeyen variant: {variant!r} (v1 veya v2 olmali)")

    n = len(df)
    time_col = df["time"]
    open_ = df["open"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    volume = df["volume"].to_numpy(dtype=float)

    filt, upward, downward = _compute_trf(close, params.per1, params.mult1, params.per2, params.mult2)

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
    if variant == "v2":
        wt1, wt2 = _compute_wavetrend(high, low, close, params.wt_chan_len, params.wt_avg_len, params.wt_smooth)

    cond_ini = 0
    signals: list[Signal] = []

    for i in range(n):
        if i == 0:
            long_cond = short_cond = False
        else:
            src_gt_filt = close[i] > filt[i]
            src_lt_filt = close[i] < filt[i]
            src_gt_prev = close[i] > close[i - 1]
            src_lt_prev = close[i] < close[i - 1]
            long_cond = (src_gt_filt and src_gt_prev and upward[i] > 0) or (src_gt_filt and src_lt_prev and upward[i] > 0)
            short_cond = (src_lt_filt and src_lt_prev and downward[i] > 0) or (src_lt_filt and src_gt_prev and downward[i] > 0)

        prev_cond_ini = cond_ini
        cond_ini = 1 if long_cond else (-1 if short_cond else cond_ini)
        trf_long_trigger = long_cond and prev_cond_ini == -1

        if not trf_long_trigger or i < 1:
            continue

        is_squeezed = not np.isnan(ema_spread[i]) and ema_spread[i] <= params.squeeze_pct
        ema_breakout = close[i] > ema_max[i] and close[i - 1] <= ema_max[i - 1]
        vol_surge = not np.isnan(vol_ratio[i]) and volume[i] >= params.vol_mult * vol_sma[i]

        if variant == "v1":
            ema_confluence = is_squeezed and ema_breakout
            confluence = ema_confluence and vol_surge
        else:
            ema_order_ok = ema5[i] >= ema8[i]
            ema_above_pct = close[i] >= ema5[i] * params.ema_above_pct
            ema_confluence = is_squeezed and ema_breakout and ema_order_ok and ema_above_pct

            wt_exact_cross = i >= 1 and wt1[i - 1] < wt2[i - 1] and wt1[i] > wt2[i]
            wt_prior_history = i >= 2 and wt1[i - 1] < wt2[i - 1] and wt1[i - 2] < wt2[i - 2]
            wt_level_ok = not np.isnan(wt1[i]) and wt1[i] < params.wt_max_lvl
            wt_confluence = wt_exact_cross and wt_prior_history and wt_level_ok

            green_candle = close[i] > open_[i]
            confluence = ema_confluence and vol_surge and wt_confluence and green_candle

        if not confluence:
            continue

        entry_ref = float(close[i])
        fill_bar = i + 1
        fill_ref = float(open_[fill_bar]) if fill_bar < n else float("nan")

        atr_at_signal = atr14[i]
        if np.isnan(atr_at_signal) or atr_at_signal <= 0:
            continue  # ATR henuz tanimsiz (ilk ~14 bar) -- SL hesaplanamaz, sinyal atlanir

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
                tp1=float(tp1),
                tp2=float(tp2),
                sl=float(sl),
                ema_spread_pct=float(ema_spread[i]) if not np.isnan(ema_spread[i]) else float("nan"),
                volume_ratio=float(vol_ratio[i]) if not np.isnan(vol_ratio[i]) else float("nan"),
                downward_streak_before_flip=int(downward[i - 1]) if i > 0 else 0,
                wt1_at_signal=float(wt1[i]) if variant == "v2" and wt1 is not None and not np.isnan(wt1[i]) else float("nan"),
            )
        )

    return signals
