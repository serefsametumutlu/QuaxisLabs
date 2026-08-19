"""Basarisiz Kirilim Donusu (Failed Breakout Reversal / "Trap and Reverse")
-- Building Winning Trading Systems With TradeStation kaynakli (kullanicinin
masaustu arastirmasi, 2026-08-19). SAF MATEMATIK, I/O YOK.

Mantik: fiyat N-barlik Donchian kanalinin USTUNE cikar (kirilim), ama sonraki
M bar icinde kapanis o kirilma seviyesinin ALTINA geri duserse -- bu "tuzak"
kirilimin BASARISIZ oldugunu ve piyasanin kirilim yonunde islem yapanlari
"cezalandirdigini" gosterir -- TERS yonde (SHORT) sinyal uretilir. Alt kanal
kirilimi + geri donus simetrigi LONG uretir. Mevcut Donchian/harmonik
sistemlerin AKSINE bu bir DEVAM DEGIL, bir TUZAK/TERS DONUS paterni.

SL, tuzagin ULASTIGI ASIRI noktanin (kirilim sonrasi en yuksek/dusuk) az
otesi -- kitabin kendi mantigi ("stop beyond the trap"), ATR DEGIL."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

OHLC_COLUMNS = ("time", "open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class Params:
    channel_len: int = 20
    max_bars_to_fail: int = 5
    sl_buffer_pct: float = 0.002  # tuzak asirisinin %0.2 otesi
    tp1_r: float = 1.0
    tp2_r: float = 2.0
    enable_long: bool = True
    enable_short: bool = True


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
    broken_level: float
    trap_bar: int  # ilk kirilimin gerceklestigi bar


def detect(df: pd.DataFrame, params: Params = Params()) -> list[Signal]:
    n = len(df)
    time_col = df["time"]
    open_ = df["open"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)

    ch_high = pd.Series(high).shift(1).rolling(params.channel_len).max().to_numpy()
    ch_low = pd.Series(low).shift(1).rolling(params.channel_len).min().to_numpy()

    signals: list[Signal] = []
    pending_high: tuple[float, int] | None = None  # (kirilan seviye, kirilim bari)
    pending_low: tuple[float, int] | None = None
    trap_extreme_high = float("-inf")
    trap_extreme_low = float("inf")

    for i in range(params.channel_len + 1, n):
        if np.isnan(ch_high[i]) or np.isnan(ch_low[i]):
            continue

        if params.enable_short and high[i] > ch_high[i] and pending_high is None:
            pending_high = (float(ch_high[i]), i)
            trap_extreme_high = high[i]
        if params.enable_long and low[i] < ch_low[i] and pending_low is None:
            pending_low = (float(ch_low[i]), i)
            trap_extreme_low = low[i]

        if pending_high is not None:
            level, bar0 = pending_high
            trap_extreme_high = max(trap_extreme_high, high[i])
            if i > bar0 and close[i] < level:
                entry_ref = float(close[i])
                fill_bar = i + 1
                fill_ref = float(open_[fill_bar]) if fill_bar < n else float("nan")
                sl = trap_extreme_high * (1.0 + params.sl_buffer_pct)
                risk = sl - entry_ref
                if risk > 0:
                    tp1 = entry_ref - risk * params.tp1_r
                    tp2 = entry_ref - risk * params.tp2_r
                    signals.append(
                        Signal(
                            direction=-1, signal_bar=i, signal_time=time_col.iloc[i],
                            entry_ref=entry_ref, fill_ref=fill_ref, tp1=float(tp1), tp2=float(tp2), sl=float(sl),
                            broken_level=level, trap_bar=bar0,
                        )
                    )
                pending_high = None
            elif i - bar0 > params.max_bars_to_fail:
                pending_high = None

        if pending_low is not None:
            level, bar0 = pending_low
            trap_extreme_low = min(trap_extreme_low, low[i])
            if i > bar0 and close[i] > level:
                entry_ref = float(close[i])
                fill_bar = i + 1
                fill_ref = float(open_[fill_bar]) if fill_bar < n else float("nan")
                sl = trap_extreme_low * (1.0 - params.sl_buffer_pct)
                risk = entry_ref - sl
                if risk > 0:
                    tp1 = entry_ref + risk * params.tp1_r
                    tp2 = entry_ref + risk * params.tp2_r
                    signals.append(
                        Signal(
                            direction=1, signal_bar=i, signal_time=time_col.iloc[i],
                            entry_ref=entry_ref, fill_ref=fill_ref, tp1=float(tp1), tp2=float(tp2), sl=float(sl),
                            broken_level=level, trap_bar=bar0,
                        )
                    )
                pending_low = None
            elif i - bar0 > params.max_bars_to_fail:
                pending_low = None

    signals.sort(key=lambda s: s.signal_bar)
    return signals
