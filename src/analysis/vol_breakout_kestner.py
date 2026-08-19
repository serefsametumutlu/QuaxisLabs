"""Kestner Oynaklik Kirilimi (Volatility Breakout) -- Larry Williams
kokenli, Lars Kestner'in "Nicel Trading Stratejileri" kitabindan (kullanicinin
masaustu arastirmasi, 2026-08-19). SAF MATEMATIK, I/O YOK.

Mantik: Referans Fiyat (dunku kapanis) + Oynaklik Olcusu (ATR14) x Carpan
-- ust tetik = Referans + k*ATR, fiyat KAPANISI bunun ustune cikarsa LONG
(alt tetik simetrigi SHORT). Kitabin rasyoneli: buyuk/bilgili oyuncularin
hareketleri, yavas kurumsal sermaye tepki vermeden ONCE kisa-vadeli oynaklik
genislemesiyle "telgraflanir". Mevcut Donchian/harmonik/momentum sistemlerin
HICBIRINDEN farkli -- BAGIMSIZ bir giris tetigi (filtre degil).

`abcd_pattern.atr_wilder` REUSE edilir (Wilder ATR, proje geneli standart).
TP/SL, `abcd_backtest`in 1R/2R kismi-cikis motoruyla uyumlu R-katli yapida
(kaynakta yok, `momentum_confluence.py`/`harmonic_xabcd.py` ile AYNI ilke:
proje-standardi risk yonetimi eklenir)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.analysis.abcd_pattern import atr_wilder

OHLC_COLUMNS = ("time", "open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class Params:
    atr_period: int = 14
    vol_mult: float = 1.0
    enable_long: bool = True
    enable_short: bool = True
    sl_atr_mult: float = 1.5
    tp1_r: float = 1.0
    tp2_r: float = 2.0


@dataclass(frozen=True)
class Signal:
    direction: int
    signal_bar: int
    signal_time: pd.Timestamp
    entry_ref: float
    fill_ref: float
    tp1: float
    tp2: float
    sl: float
    trigger_price: float  # tetiklenen ust/alt bant seviyesi


def detect(df: pd.DataFrame, params: Params = Params()) -> list[Signal]:
    n = len(df)
    time_col = df["time"]
    open_ = df["open"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    atr = atr_wilder(df, params.atr_period)

    signals: list[Signal] = []
    for i in range(1, n):
        if np.isnan(atr[i - 1]) or atr[i - 1] <= 0:
            continue
        ref = close[i - 1]
        upper = ref + params.vol_mult * atr[i - 1]
        lower = ref - params.vol_mult * atr[i - 1]

        direction = 0
        trigger = float("nan")
        if params.enable_long and close[i] > upper:
            direction, trigger = 1, upper
        elif params.enable_short and close[i] < lower:
            direction, trigger = -1, lower
        if direction == 0:
            continue

        entry_ref = float(close[i])
        fill_bar = i + 1
        fill_ref = float(open_[fill_bar]) if fill_bar < n else float("nan")
        risk = params.sl_atr_mult * atr[i]
        if not np.isfinite(risk) or risk <= 0:
            continue
        sl = entry_ref - direction * risk
        tp1 = entry_ref + direction * risk * params.tp1_r
        tp2 = entry_ref + direction * risk * params.tp2_r

        signals.append(
            Signal(
                direction=direction, signal_bar=i, signal_time=time_col.iloc[i],
                entry_ref=entry_ref, fill_ref=fill_ref, tp1=float(tp1), tp2=float(tp2), sl=float(sl),
                trigger_price=float(trigger),
            )
        )
    return signals
