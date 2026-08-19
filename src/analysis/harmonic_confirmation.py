"""XABCD harmonik sinyalleri icin ONAY KONTROL LISTESI -- RSI/MACD, mum
formasyonu (pin bar/engulfing), hacim sikismasi+patlamasi. SAF MANTIK, I/O
YOK (`harmonic_xabcd.py`/`abcd_pattern.py`/`abcd_factor_analysis.py` ile AYNI
katman ilkesi -- `src.fetchers.*`/`src.db.*` HICBIR modulu import ETMEZ).

Kullanici istegi (2026-08-19, paylasilan "Harmonik Formasyonlar Gelistirilmis
Teknik Analiz Raporu"): D noktasina ulasildiginda 3 filtre mekanizmasi
kontrol edilmeli -- (1) RSI pozitif/negatif uyumsuzluk + asiri alim/satim
donusu, (2) mum onayi (Pin Bar/Hammer veya Engulfing), (3) hacim (D'ye
giderken azalan hacim + donus barinda patlama). Bu modul HER UCUNU de
hesaplar ve BOOLEAN+HAM DEGER olarak doner -- `harmonic_scanner.py` bunlari
sinyali FILTRELEMEK icin degil, sinyale EKLENEN bir kontrol listesi olarak
kullanir (proje ilkesi: sinyal hicbir zaman gizlenmez, bkz. abcd_scanner.
guven_etiketi/harmonic_scanner.guven_etiketi ile AYNI disiplin). Sadece
`scripts/harmonic_confirmation_optimizasyon.py` (ayri, backtest amacli) bu
bayraklari GERIYE DONUK olarak FILTRE gibi kullanir -- hangi kombinasyonun
PF/win-rate'i yukselttigini olcmek icin.

RSI/MACD hesaplari `abcd_factor_analysis.py`nin ozel (alt cizgili) Wilder-
RSI/MACD-histogram fonksiyonlarini REUSE eder (`momentum_confluence_factors.
py` ile AYNI ithalat deseni, bkz. o modulun ust notu) -- YENI bir RSI/MACD
implementasyonu YAZILMAZ.

Divergence taban noktasi -- neden B (X degil): XABCD'de D ile AYNI pivot
tipini (yon) tasiyan en YAKIN onceki pivot B'dir (uzun sinyalde b_type=d_type
=-1/dip, kisa sinyalde b_type=d_type=1/tepe) -- X de ayni tipte olsa da
(x_type=d_type) yapisal olarak cok daha ESKI/uzak bir referanstir, RSI
uyumsuzlugu literaturde EN YAKIN karsilastirilabilir pivota (burada B) bakar.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.analysis.abcd_factor_analysis import _macd_hist, _rsi_wilder

_RSI_LENGTH = 14
_RSI_OVERSOLD = 30.0
_RSI_OVERBOUGHT = 70.0
_VOL_SMA_LEN = 20
_VOL_EXPANSION_MULT = 1.2  # donus barinda SMA'nin en az bu katindan buyuk hacim
_VOL_COMPRESSION_LOOKBACK = 5  # D'ye giden son N bar
_VOL_COMPRESSION_BASELINE = 15  # ondan onceki M bar (karsilastirma tabani)
_VOL_COMPRESSION_RATIO = 0.85  # son N bar ortalamasi, taban ortalamanin bu katindan KUCUK olmali


@dataclass(frozen=True)
class IndicatorSeries:
    """Bir sembol/tf icin TEK SEFER hesaplanir, sembol basina birden fazla
    sinyalin `evaluate_confirmations()` cagrisinda TEKRAR TEKRAR RSI/MACD
    hesaplanmasini onler (bkz. `momentum_scanner.py`nin iki-asamali tarama
    performans ilkesiyle AYNI ruh)."""

    rsi: np.ndarray
    macd_hist: np.ndarray
    volume: np.ndarray
    vol_sma: np.ndarray


def compute_indicator_series(df: pd.DataFrame) -> IndicatorSeries:
    close = df["close"].to_numpy(dtype=float)
    volume = df["volume"].to_numpy(dtype=float)
    rsi = _rsi_wilder(close, _RSI_LENGTH)
    macd_hist = _macd_hist(close)
    vol_sma = pd.Series(volume).rolling(_VOL_SMA_LEN).mean().to_numpy(dtype=float)
    return IndicatorSeries(rsi=rsi, macd_hist=macd_hist, volume=volume, vol_sma=vol_sma)


def _is_bullish_pin_bar(o: float, h: float, l: float, c: float) -> bool:
    rng = h - l
    if rng <= 0:
        return False
    body = abs(c - o)
    lower_wick = min(o, c) - l
    upper_wick = h - max(o, c)
    return lower_wick >= 2.0 * body and upper_wick <= body and c >= (l + 0.5 * rng)


def _is_bearish_pin_bar(o: float, h: float, l: float, c: float) -> bool:
    rng = h - l
    if rng <= 0:
        return False
    body = abs(c - o)
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l
    return upper_wick >= 2.0 * body and lower_wick <= body and c <= (h - 0.5 * rng)


def _is_bullish_engulfing(prev_o: float, prev_c: float, o: float, c: float) -> bool:
    return c > o and prev_c < prev_o and c >= prev_o and o <= prev_c


def _is_bearish_engulfing(prev_o: float, prev_c: float, o: float, c: float) -> bool:
    return c < o and prev_c > prev_o and c <= prev_o and o >= prev_c


def _candle_pattern_at(df: pd.DataFrame, bar: int, direction: int) -> str | None:
    """`bar` (D pivotu) icin yon-uyumlu Pin Bar/Hammer veya Engulfing var mi.
    `bar-1` yoksa (seri basi) sadece pin bar kontrol edilir."""
    if bar < 0 or bar >= len(df):
        return None
    o, h, l, c = (float(df["open"].iloc[bar]), float(df["high"].iloc[bar]), float(df["low"].iloc[bar]), float(df["close"].iloc[bar]))
    is_long = direction > 0
    pin = _is_bullish_pin_bar(o, h, l, c) if is_long else _is_bearish_pin_bar(o, h, l, c)
    if pin:
        return "PIN_BAR"
    if bar >= 1:
        prev_o, prev_c = float(df["open"].iloc[bar - 1]), float(df["close"].iloc[bar - 1])
        engulf = _is_bullish_engulfing(prev_o, prev_c, o, c) if is_long else _is_bearish_engulfing(prev_o, prev_c, o, c)
        if engulf:
            return "ENGULFING"
    return None


@dataclass(frozen=True)
class ConfirmationFlags:
    """`d_bar` (ve baglami) icin hesaplanan onay kontrol listesi -- HICBIR
    alan digerini FILTRELEMEZ, hepsi bagimsiz gosterilir (bkz. modul ust
    notu). `score` = kac kosulun (rsi/macd/candle/volume, 4 uzerinden)
    saglandigi -- Telegram'da hizli siralama/gorsel ozet icin."""

    rsi_value: float | None
    rsi_divergence: bool  # B->D arasi pozitif/negatif uyumsuzluk
    rsi_extreme_turn: bool  # asiri alim/satim bolgesinden donus
    rsi_ok: bool  # divergence OR extreme_turn (ikisinden biri yeterli -- kullanici raporu "VEYA" niteliginde)
    macd_hist: float | None
    macd_ok: bool  # histogram, yon lehine donuyor (b_bar -> d_bar arasi degil, d_bar-1 -> d_bar)
    candle_pattern: str | None  # "PIN_BAR" | "ENGULFING" | None
    candle_ok: bool
    volume_ratio: float | None  # volume[d_bar] / vol_sma[d_bar]
    volume_compression: bool  # D'ye giden son bar azalan hacim
    volume_expansion: bool  # donus barinda hacim patlamasi
    volume_ok: bool  # compression AND expansion
    score: int  # 0-4


def evaluate_confirmations(
    df: pd.DataFrame, indicators: IndicatorSeries, direction: int, b_bar: int, b_price: float, d_bar: int, d_price: float
) -> ConfirmationFlags:
    """`direction` (+1 uzun/dip-D, -1 kisa/tepe-D), `b_bar`/`b_price` (RSI
    uyumsuzluk taban noktasi -- bkz. modul ust notu), `d_bar`/`d_price`
    (guncel pivot) icin 4 onay kontrolu. `d_bar` seri disindaysa (n/a) tum
    alanlar None/False doner -- FIRLATMAZ (proje Kural 9 ile AYNI ilke)."""
    n = len(df)
    if d_bar < 0 or d_bar >= n:
        return ConfirmationFlags(
            rsi_value=None, rsi_divergence=False, rsi_extreme_turn=False, rsi_ok=False,
            macd_hist=None, macd_ok=False,
            candle_pattern=None, candle_ok=False,
            volume_ratio=None, volume_compression=False, volume_expansion=False, volume_ok=False,
            score=0,
        )

    is_long = direction > 0
    rsi_d = indicators.rsi[d_bar]
    rsi_b = indicators.rsi[b_bar] if 0 <= b_bar < n else float("nan")
    rsi_value = float(rsi_d) if not np.isnan(rsi_d) else None

    rsi_divergence = False
    if not (np.isnan(rsi_d) or np.isnan(rsi_b)):
        if is_long:
            rsi_divergence = d_price < b_price and rsi_d > rsi_b
        else:
            rsi_divergence = d_price > b_price and rsi_d < rsi_b

    rsi_extreme_turn = False
    if not np.isnan(rsi_d) and d_bar >= 1 and not np.isnan(indicators.rsi[d_bar - 1]):
        rsi_prev = indicators.rsi[d_bar - 1]
        if is_long:
            rsi_extreme_turn = rsi_d <= _RSI_OVERSOLD and rsi_d > rsi_prev
        else:
            rsi_extreme_turn = rsi_d >= _RSI_OVERBOUGHT and rsi_d < rsi_prev

    rsi_ok = rsi_divergence or rsi_extreme_turn

    macd_d = indicators.macd_hist[d_bar]
    macd_hist_value = float(macd_d) if not np.isnan(macd_d) else None
    macd_ok = False
    if not np.isnan(macd_d) and d_bar >= 1 and not np.isnan(indicators.macd_hist[d_bar - 1]):
        macd_prev = indicators.macd_hist[d_bar - 1]
        macd_ok = macd_d > macd_prev if is_long else macd_d < macd_prev

    candle_pattern = _candle_pattern_at(df, d_bar, direction)
    candle_ok = candle_pattern is not None

    vol_d = indicators.volume[d_bar]
    vol_sma_d = indicators.vol_sma[d_bar]
    volume_ratio = float(vol_d / vol_sma_d) if vol_sma_d and vol_sma_d > 0 else None
    volume_expansion = volume_ratio is not None and volume_ratio >= _VOL_EXPANSION_MULT

    volume_compression = False
    recent_start = d_bar - _VOL_COMPRESSION_LOOKBACK
    baseline_start = recent_start - _VOL_COMPRESSION_BASELINE
    if baseline_start >= 0:
        recent_avg = float(np.mean(indicators.volume[recent_start:d_bar]))
        baseline_avg = float(np.mean(indicators.volume[baseline_start:recent_start]))
        if baseline_avg > 0:
            volume_compression = recent_avg < _VOL_COMPRESSION_RATIO * baseline_avg

    volume_ok = volume_compression and volume_expansion

    score = int(rsi_ok) + int(macd_ok) + int(candle_ok) + int(volume_ok)

    return ConfirmationFlags(
        rsi_value=rsi_value, rsi_divergence=bool(rsi_divergence), rsi_extreme_turn=bool(rsi_extreme_turn), rsi_ok=bool(rsi_ok),
        macd_hist=macd_hist_value, macd_ok=bool(macd_ok),
        candle_pattern=candle_pattern, candle_ok=candle_ok,
        volume_ratio=volume_ratio, volume_compression=bool(volume_compression), volume_expansion=bool(volume_expansion), volume_ok=bool(volume_ok),
        score=score,
    )
