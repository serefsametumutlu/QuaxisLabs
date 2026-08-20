"""Wavelet Trend Rider -- dalgacik (wavelet) gurultu temizlemesi + momentum
ivmesi. SAF MATEMATIK, I/O YOK (`abcd_pattern.py` ile AYNI katman ilkesi).

Kaynak (2026-08-19, kullanicinin masaustu arastirmasi): "Quant Playbook/
strateji_1_wavelet_trend_rider.py" -- baska bir proje (AxiQuant) icin
yazilmis, BIST30 4H+1D. Kullanici bunu "iyi gorunuyordu" diye ozellikle
isaret etti -- bu modul, ORIJINAL SINYAL MANTIGINI (EMA/ADX/RSI/velocity/
acceleration/MTF kosullari) DEGISTIRMEDEN, bilanco-radar'in veri/backtest
altyapisina (`fetch_ohlcv_abcd` "240"+"1D", `abcd_backtest` duck-typing)
PORT eder.

## Yontem -- CAUSAL à trous (SWT) Daubechies-8 kaskadi (2026-08-20 DUZELTME)

Ilk surum `pywt.wavedec()`/`waverec()` kullaniyordu (kaynak script'in
KENDI yontemi) -- ama bu, TUM `close` dizisini TEK SEFERDE (batch) islediği
icin NON-CAUSAL'di: bar `i`deki `denoised[i]`, hem ONCEKI hem SONRAKI
barlardan etkileniyordu (gurultu esigi TUM diziden hesaplaniyor, ters-
donusum matematiksel olarak iki-yonlu). Bu, `docs/spec/YENI_10_STRATEJI_
BACKTEST.md`deki PF=2.21 sonucunu ILERI-BAKIS SIZINTISIYLA sisirmis olabilir
-- kullanicinin TradingView'de gordugu "sinyal cogu zaman tepe civarinda
geliyor, SL'ye gidiyor" sikayeti bunun CANLI KANITIdir (bkz. `pine/wavelet_
trend_rider_v1_indicator.pine`nin BUNU ilk fark ettigi commit).

Bu surum artik TAMAMEN CAUSAL: `pywt.Wavelet('db8').dec_lo / sqrt(2)`den
(sqrt(2) -- ayrik/decimated DWT normu, à trous/undecimated kullanimda
DUZELTILMESI gereken olcek, bkz. `_DB8_H` ust notu) turetilmis 16 katsayili
alcak-gecis filtresi, 4 seviyeli à trous (Starck-Murtagh "starlet") kaskadi
ile uygulanir -- HER seviye SADECE kendinden ONCEKI seviyenin (ve ondan
ONCEKI barlarin) verisini kullanir, gelecek ASLA sizmaz. Bu, artik `pine/
wavelet_trend_rider_v1_indicator.pine` ile SAYISAL OLARAK OZDES (Python'da
ayrica dogrulandi, bkz. `tests/test_wavelet_trend_rider.py` "causal"
regresyon testi). `pywt` bagimliligi bu yuzden KALDIRILDI (katsayilar SABIT
gomulu, tekrar hesaplamaya gerek yok).

MTF hizalama -- neden orijinalden FARKLI: kaynak script pandas reindex/
ffill kullaniyordu; bu port HER 4H bari icin "o barin takvim gununden
KESINLIKLE ONCEKI son gunluk bar"ini `np.searchsorted` ile bulur (ayni gun
ICINDEKI gunluk bari ASLA gormez) -- projenin "asla look-ahead" ilkesiyle
birebir, orijinalden daha basit/saglam bir uygulama.

RSI/ADX/EMA/ATR formulleri -- neden `abcd_pattern`/`abcd_factor_analysis`
REUSE EDILMEDI: kaynak script'in RSI/ADX'i Wilder RMA DEGIL, basit `.ewm
(alpha=1/period)` smoothing kullaniyor -- projenin geri kalanindan (Wilder)
FARKLI bir zamanlama/gecikme profili verir. "Kaynak mantik degistirilmedi"
ilkesine sadik kalmak icin BU MODULE OZEL, orijinalle BIREBIR ayni yerel
kopyalar tutulur (`momentum_confluence_variants.py`nin kendi RSI/EMA
kopyalarini tutma gerekcesiyle AYNI).

## Kotu sinyal teshis alanlari (2026-08-20, kullanici canli TradingView
raporu -- "sinyallerin cogu hissenin tepesinde geliyor, SL'ye gidiyor")

`Signal`e 3 teshis alani eklendi (`dist_from_denoised_atr`, `is_new_high_20`,
`pullback_bars`) -- bunlar HENUZ hicbir kosulu FILTRELEMIYOR (baseline
`detect()` DEGISMEDI), sadece "kotu sinyal" hipotezlerini olcmek icin veri
saglar. Gercek filtre ablasyonu `wavelet_trend_rider_variants.py`de (bkz. o
modulun ust notu) ve `scripts/wavelet_trend_rider_optimizasyon.py`de yapilir
-- bu modulun KENDISI `momentum_confluence.py`nin harmonic_xabcd.py'ye
gore oynadigi ROLU oynar: "Pine-parity temel", deneysel filtreler AYRI.

TP/SL kaynakta zaten VARDI (SL=2xATR, TP1=3xATR, TP2=6xATR) -- DEGISTIRILMEDI.
`abcd_backtest.backtest_symbol` ile duck-typing uyumlu (Signal alan adlari
`momentum_confluence.Signal` ile AYNI ilke).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

OHLC_COLUMNS = ("time", "open", "high", "low", "close", "volume")

# `pywt.Wavelet('db8').dec_lo` (ayrisim alcak-gecis filtresi, 16 katsayi)
# sqrt(2)'ye bolunerek NORMALIZE edilmistir -- ayrik/decimated DWT'nin dogal
# normu sqrt(2)'dir (sum(dec_lo)=sqrt(2)), ama à trous/undecimated kullanimda
# (bu modulun/Pine'in yaptigi gibi, HER seviyede AYNI filtreyi tekrar tekrar
# uygulamak) bu normalizasyon OLMADAN deger her seviyede sqrt(2) kati
# BUYUYUP patlar -- bu, gelistirme sirasinda Python'da SAYISAL olarak
# tespit edilip (`sum(H)=1` olacak sekilde) DUZELTILDI, `pine/wavelet_
# trend_rider_v1_indicator.pine` ile BIREBIR AYNI katsayilar (bkz. o
# dosyanin ust notu -- ayni turetim).
_DB8_H: tuple[float, ...] = (
    -0.00008306863068661, 0.00047761485564963, -0.00027700227447939, -0.00344385962844181,
    0.00618442240981592, 0.00988607964835076, -0.03117510332513943, -0.01228195052284841,
    0.09103817842365775, 0.00033409704622012, -0.20082931639048901, -0.01119286766688022,
    0.41390826621119586, 0.47774307521387360, 0.22123362357612489, 0.03847781105407623,
)
_DB8_LEVELS = 4


@dataclass(frozen=True)
class Params:
    ema_fast: int = 50
    ema_slow: int = 100
    adx_period: int = 14
    adx_threshold: float = 20.0
    rsi_period: int = 14
    rsi_upper: float = 70.0
    atr_period: int = 14
    sl_atr_mult: float = 2.0
    tp1_atr_mult: float = 3.0
    tp2_atr_mult: float = 6.0


@dataclass(frozen=True)
class Signal:
    """`abcd_backtest.backtest_symbol` ile duck-typing uyumlu."""

    direction: int  # HER ZAMAN +1 (kaynakta SADECE LONG var)
    signal_bar: int
    signal_time: pd.Timestamp
    entry_ref: float
    fill_ref: float
    tp1: float
    tp2: float
    sl: float
    velocity: float
    acceleration: float
    adx: float
    # --- teshis alanlari (2026-08-20, "kotu sinyal" hipotez testi -- bkz. modul ust notu) ---
    dist_from_denoised_atr: float  # (entry - denoised)/ATR -- buyuk pozitif = fiyat trendden COK uzamis
    is_new_high_20: bool  # kapanis, son 20 barin (bu bar DAHIL) en yuksegi mi
    pullback_bars: int  # flip ONCESI ardisik kac bar velocity<=0 idi (0 = gercek bir "dip" YOK, duz devam)


def _ema(series: np.ndarray, period: int) -> np.ndarray:
    return pd.Series(series).ewm(span=period, adjust=False).mean().to_numpy()


def _atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
    prev_close = pd.Series(close).shift(1)
    tr = pd.concat(
        [pd.Series(high) - pd.Series(low), (pd.Series(high) - prev_close).abs(), (pd.Series(low) - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.rolling(period, min_periods=1).mean().to_numpy()


def _rsi(close: np.ndarray, period: int) -> np.ndarray:
    delta = pd.Series(close).diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    return (100.0 - 100.0 / (1.0 + rs)).to_numpy()


def _adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
    high_s, low_s, close_s = pd.Series(high), pd.Series(low), pd.Series(close)
    prev_close = close_s.shift(1)
    tr = pd.concat([high_s - low_s, (high_s - prev_close).abs(), (low_s - prev_close).abs()], axis=1).max(axis=1)
    atr_val = tr.ewm(span=period, adjust=False).mean()

    up_move = high_s.diff()
    down_move = -low_s.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    plus_dm_s = pd.Series(plus_dm, index=high_s.index).ewm(span=period, adjust=False).mean()
    minus_dm_s = pd.Series(minus_dm, index=high_s.index).ewm(span=period, adjust=False).mean()

    plus_di = 100.0 * plus_dm_s / (atr_val + 1e-10)
    minus_di = 100.0 * minus_dm_s / (atr_val + 1e-10)
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-10)
    return dx.ewm(span=period, adjust=False).mean().to_numpy()


def _db8_atrous_smooth(series: np.ndarray, step: int) -> np.ndarray:
    """à trous (undecimated) TEK seviye alcak-gecis filtreleme -- `series[i]`
    icin SADECE `series[i], series[i-step], ..., series[i-15*step]` kullanir
    (look-ahead YOK). k uzerinde vektorize (n uzerinde DEGIL) -- 16 numpy
    islemi, `n` buyuklugunden bagimsiz sabit maliyet (bkz. modul ust notu
    performans notu, Python'da dogrulandi: loop-tabanli referans uygulamayla
    BIREBIR AYNI sonuc, `tests/test_wavelet_trend_rider.py`)."""
    n = len(series)
    out = np.zeros(n)
    valid = np.ones(n, dtype=bool)
    for k, h in enumerate(_DB8_H):
        lag = k * step
        shifted = np.full(n, np.nan)
        if lag == 0:
            shifted = series.astype(float, copy=True)
        else:
            shifted[lag:] = series[:-lag]
        out = out + h * np.nan_to_num(shifted, nan=0.0)
        valid = valid & ~np.isnan(shifted)
    return np.where(valid, out, np.nan)


def _causal_wavelet_denoise(close: np.ndarray, levels: int = _DB8_LEVELS) -> np.ndarray:
    """4 seviyeli à trous db8 kaskadi -- her seviye ONCEKI seviyenin
    CIKTISINI girdi alir (adim 1,2,4,8,...). Seviye `levels`in ciktisi
    "temizlenmis" (denoised) fiyattir -- Pine'daki `denoised` ile AYNI
    (bkz. `pine/wavelet_trend_rider_v1_indicator.pine`)."""
    c = close.astype(float, copy=True)
    for j in range(1, levels + 1):
        c = _db8_atrous_smooth(c, step=2 ** (j - 1))
    return c


def _daily_series_aligned(bar_times: pd.Series, daily_df: pd.DataFrame, daily_values: np.ndarray) -> np.ndarray:
    """Her `bar_times` elemani icin, o barin takvim gununden KESINLIKLE
    ONCEKI son gunluk bara ait `daily_values[i]`yi doner -- look-ahead YOK
    (bkz. modul ust notu). `daily_values`, `daily_df` ile AYNI uzunlukta
    onceden hesaplanmis herhangi bir seri olabilir (EMA, close, vb.)."""
    if daily_df.empty:
        return np.full(len(bar_times), np.nan)
    daily_dates = pd.to_datetime(daily_df["time"]).dt.tz_localize(None).dt.normalize().to_numpy()
    bar_dates = pd.to_datetime(bar_times).dt.tz_localize(None).dt.normalize().to_numpy()
    idx = np.searchsorted(daily_dates, bar_dates, side="left") - 1
    out = np.full(len(bar_times), np.nan)
    valid = idx >= 0
    out[valid] = daily_values[idx[valid]]
    return out


def detect(df: pd.DataFrame, df_daily: pd.DataFrame, params: Params = Params()) -> list[Signal]:
    """`df` = 4H (tf="240") bar serisi, `df_daily` = 1D bar serisi (AYNI
    sembol). Kaynak scriptin `generate_signals`inin PORTU -- kosullar
    DEGISMEDI, SADECE dalgacik hesaplamasi artik causal (bkz. modul ust
    notu)."""
    p = params
    n = len(df)
    warmup = min(p.ema_slow, n // 3)
    if n <= warmup:
        return []

    close = df["close"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    time_col = df["time"]

    ema_fast = _ema(close, p.ema_fast)
    ema_slow = _ema(close, p.ema_slow)
    adx = _adx(high, low, close, p.adx_period)
    rsi = _rsi(close, p.rsi_period)
    atr = _atr(high, low, close, p.atr_period)

    denoised = _causal_wavelet_denoise(close)
    velocity = np.diff(denoised, prepend=np.nan)
    acceleration = np.diff(velocity, prepend=np.nan)

    roll_high_20 = pd.Series(close).rolling(20, min_periods=1).max().to_numpy()

    daily_ema_series = _ema(df_daily["close"].to_numpy(dtype=float), p.ema_fast) if not df_daily.empty else np.array([])
    daily_ema = _daily_series_aligned(time_col, df_daily, daily_ema_series)
    daily_close_aligned = _daily_series_aligned(time_col, df_daily, df_daily["close"].to_numpy(dtype=float))

    signals: list[Signal] = []
    for i in range(warmup, n):
        if any(
            np.isnan(v)
            for v in (ema_fast[i], ema_slow[i], adx[i], rsi[i], atr[i], velocity[i], acceleration[i], daily_ema[i], daily_close_aligned[i])
        ):
            continue
        long_ok = (
            close[i] > ema_fast[i] > ema_slow[i]
            and adx[i] > p.adx_threshold
            and velocity[i] > 0
            and acceleration[i] > 0
            and rsi[i] < p.rsi_upper
            and daily_close_aligned[i] > daily_ema[i]
        )
        if not long_ok:
            continue

        entry_ref = float(close[i])
        fill_bar = i + 1
        fill_ref = float(df["open"].iloc[fill_bar]) if fill_bar < n else float("nan")
        sl = entry_ref - atr[i] * p.sl_atr_mult
        tp1 = entry_ref + atr[i] * p.tp1_atr_mult
        tp2 = entry_ref + atr[i] * p.tp2_atr_mult

        pullback_bars = 0
        j = i - 1
        while j >= 0 and not np.isnan(velocity[j]) and velocity[j] <= 0:
            pullback_bars += 1
            j -= 1

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
                velocity=float(velocity[i]),
                acceleration=float(acceleration[i]),
                adx=float(adx[i]),
                dist_from_denoised_atr=float((entry_ref - denoised[i]) / atr[i]) if atr[i] > 0 else float("nan"),
                is_new_high_20=bool(close[i] >= roll_high_20[i]),
                pullback_bars=pullback_bars,
            )
        )

    return signals
