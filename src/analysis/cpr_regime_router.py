"""CPR (Central Pivot Range) Genisligi -- ILERIYE-DONUK rejim ongorucusu +
alt-sinyal yonlendirici. "51 Trading Strategies" kaynakli (kullanicinin
masaustu arastirmasi, 2026-08-19). SAF MATEMATIK, I/O YOK. SADECE gunluk
(1D) barlarda anlamli -- CPR klasik gun-ici pivot yapisi.

Mantik: Pivot=(H+L+C)/3, BC=(H+L)/2, TC=2*Pivot-BC (ONCEKI GUNUN barindan --
bugunun CPR'i, bugun BASLAMADAN ONCE zaten bilinir, look-ahead YOK). CPR
genisligi = |TC-BC|/Pivot. Mevcut ADX rejim filtresi GERIYE-DONUKTUR ("su an
trend mi"); CPR genisligi ILERIYE-DONUKTUR ("YARIN trend gunu mu olacak") --
DAR CPR (kendi 60-gunluk yuzdelik sirasina gore alt %30) -> yarin trend
gunu beklenir, MOMENTUM alt-sinyali kullanilir; GENIS CPR (ust %30) -> yarin
yatay/donus gunu beklenir, ORTALAMAYA-DONUS alt-sinyali kullanilir. Bu,
`regime_filters.py`nin (Hurst) "hangi rejimde hangi motoru kullan" ilkesiyle
AYNI ruhta ama TAMAMEN farkli/ileriye-donuk bir olcu."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.analysis.abcd_pattern import atr_wilder

OHLC_COLUMNS = ("time", "open", "high", "low", "close", "volume")

_WIDTH_PCTRANK_WINDOW = 60
_NARROW_PCT = 0.30
_WIDE_PCT = 0.70


@dataclass(frozen=True)
class Params:
    atr_period: int = 14
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
    cpr_regime: str  # "DAR_MOMENTUM" | "GENIS_ORTALAMAYA_DONUS"


def detect(df: pd.DataFrame, params: Params = Params()) -> list[Signal]:
    n = len(df)
    time_col = df["time"]
    open_ = df["open"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    atr = atr_wilder(df, params.atr_period)

    prev_high, prev_low, prev_close = high[:-1], low[:-1], close[:-1]
    pivot = (prev_high + prev_low + prev_close) / 3.0
    bc = (prev_high + prev_low) / 2.0
    tc = 2.0 * pivot - bc
    with np.errstate(divide="ignore", invalid="ignore"):
        width = np.where(pivot != 0, np.abs(tc - bc) / pivot, np.nan)
    width = np.concatenate([[np.nan], width])  # bugunun CPR'i -- df[i] icin df[i-1]den turer, hizalama icin kaydir
    bc_today = np.concatenate([[np.nan], bc])
    pivot_today = np.concatenate([[np.nan], pivot])

    width_rank = pd.Series(width).rolling(_WIDTH_PCTRANK_WINDOW, min_periods=_WIDTH_PCTRANK_WINDOW // 2).rank(pct=True).to_numpy()

    signals: list[Signal] = []
    for i in range(1, n):
        if np.isnan(width_rank[i]) or np.isnan(atr[i]) or atr[i] <= 0:
            continue

        direction = 0
        regime = ""
        if width_rank[i] <= _NARROW_PCT:
            # DAR CPR -- momentum alt-sinyali: bugun yesil VE dunku kapanisin ustunde
            if close[i] > open_[i] and close[i] > close[i - 1]:
                direction, regime = 1, "DAR_MOMENTUM"
        elif width_rank[i] >= _WIDE_PCT:
            # GENIS CPR -- ortalamaya-donus alt-sinyali: gun ici BC'nin altina
            # sarkip BC'nin USTUNDE kapanan (red mumu) -> LONG
            if low[i] < bc_today[i] <= close[i] and not np.isnan(bc_today[i]):
                direction, regime = 1, "GENIS_ORTALAMAYA_DONUS"

        if direction == 0:
            continue

        entry_ref = float(close[i])
        fill_bar = i + 1
        fill_ref = float(open_[fill_bar]) if fill_bar < n else float("nan")
        risk = params.sl_atr_mult * atr[i]
        sl = entry_ref - direction * risk
        tp1 = entry_ref + direction * risk * params.tp1_r
        tp2 = entry_ref + direction * risk * params.tp2_r

        signals.append(
            Signal(
                direction=direction, signal_bar=i, signal_time=time_col.iloc[i],
                entry_ref=entry_ref, fill_ref=fill_ref, tp1=float(tp1), tp2=float(tp2), sl=float(sl),
                cpr_regime=regime,
            )
        )
    return signals
