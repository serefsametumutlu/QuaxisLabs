"""Yari-Omur (Half-Life) Uyarlamali Ortalamaya-Donus Z-Skoru -- Ernest Chan,
"Algorithmic Trading: Winning Strategies and Their Rationale" kaynakli
(kullanicinin masaustu arastirmasi, 2026-08-19). SAF MATEMATIK, I/O YOK.

Mantik: sabit 20/50-gunluk pencere yerine, HISSEYE OZGU "ortalamaya donus
hizi" AR(1) regresyonuyla tahmin edilir: dP(t) = lambda*P(t-1) + mu + eps;
yari_omur = -ln(2)/lambda (SADECE lambda<0 -- yani seri GERCEKTEN ortalamaya
donuyorsa -- anlamlidir). Bu yari-omur, z-skor penceresi olarak kullanilir:
z = (close - rolling_mean(pencere)) / rolling_std(pencere). z asiri negatife
duserse LONG (asiri ucuz, ortalamaya donmesi beklenir), asiri pozitife
cikarsa SHORT.

Performans notu: yari-omur, TUM mevcut gecmis uzerinde TEK SEFER (sembol
basina, bar-bar DEGIL) hesaplanir -- Chan'in "hisseye ozgu optimal pencere"
fikrinin ozunu korur, ama tam-BIST taramada pratik olsun diye HER barda
yeniden regresyon KOSULMAZ (bilincli sadelestirme, bkz. `harmonic_
confirmation.py`nin benzer performans notlariyla AYNI ruh).

`abcd_pattern.pivot_high/low`in AKSINE bu modul TREND DEGIL, ORTALAMAYA-
DONUS varsayimiyla calisir -- mevcut sistemlerin (harmonik disinda) COGU
devam/kirilim aradigi icin GENUINELY farkli bir mekanizma temsil eder."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

OHLC_COLUMNS = ("time", "open", "high", "low", "close", "volume")

_HALFLIFE_MIN = 5
_HALFLIFE_MAX = 60
_HALFLIFE_FALLBACK = 20  # lambda>=0 (mean-reverting DEGIL) durumunda -- muhafazakar orta deger


def compute_half_life(close: np.ndarray) -> int:
    p = close[~np.isnan(close)]
    if len(p) < 30:
        return _HALFLIFE_FALLBACK
    y = p[1:]
    y_lag = p[:-1]
    dy = y - y_lag
    x_mat = np.column_stack([y_lag, np.ones_like(y_lag)])
    coef, *_ = np.linalg.lstsq(x_mat, dy, rcond=None)
    lam = float(coef[0])
    if not np.isfinite(lam) or lam >= 0:
        return _HALFLIFE_FALLBACK
    hl = -np.log(2.0) / lam
    if not np.isfinite(hl):
        return _HALFLIFE_FALLBACK
    return int(np.clip(round(hl), _HALFLIFE_MIN, _HALFLIFE_MAX))


@dataclass(frozen=True)
class Params:
    entry_z: float = 1.5
    sl_z: float = 3.0
    tp2_z: float = 0.5  # ortalamanin OTESINE gecen kucuk asiri-tepki hedefi
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
    z_score: float
    half_life: int


def detect(df: pd.DataFrame, params: Params = Params()) -> list[Signal]:
    n = len(df)
    close = df["close"].to_numpy(dtype=float)
    open_ = df["open"].to_numpy(dtype=float)
    time_col = df["time"]

    half_life = compute_half_life(close)
    roll_mean = pd.Series(close).rolling(half_life).mean().to_numpy()
    roll_std = pd.Series(close).rolling(half_life).std(ddof=0).to_numpy()

    signals: list[Signal] = []
    for i in range(half_life, n):
        if np.isnan(roll_mean[i]) or np.isnan(roll_std[i]) or roll_std[i] <= 0:
            continue
        z = (close[i] - roll_mean[i]) / roll_std[i]

        direction = 0
        if params.enable_long and z <= -params.entry_z:
            direction = 1
        elif params.enable_short and z >= params.entry_z:
            direction = -1
        if direction == 0:
            continue

        entry_ref = float(close[i])
        fill_bar = i + 1
        fill_ref = float(open_[fill_bar]) if fill_bar < n else float("nan")
        mean_i, std_i = roll_mean[i], roll_std[i]
        sl = mean_i - direction * params.sl_z * std_i
        tp1 = mean_i  # ortalamaya donus
        tp2 = mean_i + direction * params.tp2_z * std_i

        signals.append(
            Signal(
                direction=direction, signal_bar=i, signal_time=time_col.iloc[i],
                entry_ref=entry_ref, fill_ref=fill_ref, tp1=float(tp1), tp2=float(tp2), sl=float(sl),
                z_score=float(z), half_life=half_life,
            )
        )
    return signals
