"""Wavelet Trend Rider -- dalgacik (wavelet) gurultu temizlemesi + momentum
ivmesi. SAF MATEMATIK, I/O YOK (`abcd_pattern.py` ile AYNI katman ilkesi).

Kaynak (2026-08-19, kullanicinin masaustu arastirmasi): "Quant Playbook/
strateji_1_wavelet_trend_rider.py" -- baska bir proje (AxiQuant) icin
yazilmis, BIST30 4H+1D. Kullanici bunu "iyi gorunuyordu" diye ozellikle
isaret etti -- bu modul, ORIJINAL SINYAL MANTIGINI DEGISTIRMEDEN, bilanco-
radar'in veri/backtest altyapisina (`fetch_ohlcv_abcd` "240"+"1D",
`abcd_backtest` duck-typing) PORT eder.

Yontem: kapanis fiyati Daubechies-8 dalgaciğiyla (pywt, seviye 4, yumusak
esikleme, evrensel esik sigma*sqrt(2*ln(N))) gurultuden arindirilir; bu
"temiz" fiyatin 1. farki (velocity) ve 2. farki (acceleration) momentum
ivmesini olcer. LONG: close>EMA50>EMA100, ADX14>20, velocity>0, ivme>0,
RSI14<70, GUNLUK kapanis>GUNLUK EMA50 (coklu-zaman-dilimi onayi).

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

## ⚠️ KRITIK SINIRLAMA -- `_wavelet_denoise()` NON-CAUSAL (look-ahead icerir)

2026-08-20'de (Pine portu calismasi sirasinda) fark edildi: `pywt.wavedec()`/
`waverec()` TUM `close` dizisini TEK SEFERDE (batch) isler -- gurultu esigi
(sigma), dizinin SON barina kadarki TUM detay katsayilarindan hesaplanir,
VE ters-donusum (waverec) matematiksel olarak non-causal'dir (bar `i`deki
`clean_price[i]`, hem `i`den ONCEKI hem SONRAKI barlardan etkilenir). Yani
`docs/spec/YENI_10_STRATEJI_BACKTEST.md`deki PF=2.21/WR=%59.3 sonucu bir
miktar ILERI-BAKIS SIZINTISI icerebilir -- projenin genelindeki "asla
look-ahead yok" ilkesinin FARKINA VARILMAMIS bir ihlalidir (bu modul ilk
yazildiginda ACIKCA belgelenmemisti, simdi duzeltiliyor). Gercek/canli
etki BILINMIYOR -- ne kadar sizinti oldugu olcumlenmedi.

TradingView Pine portu (`pine/wavelet_trend_rider_v1_indicator.pine`)
ZORUNLU olarak TAMAMEN CAUSAL calisir (canli grafikte gelecek gorulemez)
-- bu yuzden Python'un `pywt.wavedec/waverec`i YERINE, matematiksel olarak
FARKLI bir teknik (causal à trous/SWT Daubechies-8 kaskadi, Starck-Murtagh)
kullanir. Iki taraf SAYISAL OLARAK OZDES DEGILDIR -- Pine sonuclari bu
Python backtestindeki PF'yi AYNEN TEKRARLAMAYACAKTIR (muhtemelen DAHA
MUTEVAZI, cunku look-ahead sizintisi YOK). Bu modul (Python) SADECE
arastirma/backtest amaclidir, look-ahead-safe bir "canli" tarayici/kart
icin KULLANILMAMALIDIR -- canli kullanim icin Pine portu (veya ondan
turetilecek ayri bir causal Python modulu) tercih edilmelidir.

TP/SL kaynakta zaten VARDI (SL=2xATR, TP1=3xATR, TP2=6xATR) -- DEGISTIRILMEDI.
`abcd_backtest.backtest_symbol` ile duck-typing uyumlu (Signal alan adlari
`momentum_confluence.Signal` ile AYNI ilke).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import pywt

OHLC_COLUMNS = ("time", "open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class Params:
    wavelet: str = "db8"
    wavelet_level: int = 4
    threshold_mode: str = "soft"
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


def _wavelet_denoise(prices: np.ndarray, wavelet: str, level: int, mode: str) -> np.ndarray:
    prices = np.array(prices, dtype=float, copy=True)  # pywt yazilabilir/contiguous bellek ister
    if len(prices) < 2**level:
        return prices.copy()
    coeffs = pywt.wavedec(prices, wavelet, level=level)
    sigma = float(np.median(np.abs(coeffs[-1])) / 0.6745)
    threshold = sigma * np.sqrt(2.0 * np.log(len(prices)))
    denoised = [coeffs[0]] + [pywt.threshold(c, threshold, mode=mode) for c in coeffs[1:]]
    result = pywt.waverec(denoised, wavelet)
    return result[: len(prices)]


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
    sembol). Kaynak scriptin `generate_signals`inin PORTU."""
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

    clean = _wavelet_denoise(close, p.wavelet, p.wavelet_level, p.threshold_mode)
    velocity = np.diff(clean, prepend=np.nan)
    acceleration = np.diff(velocity, prepend=np.nan)

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
            )
        )

    return signals
