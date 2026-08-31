"""EWMACIndicator — Carver'ın (Systematic Trading) EWMAC trend-takip kuralı.

ewmac(fast, slow) = EMA_fast(close) - EMA_slow(close); bu ham fark önce
fiyat biriminden bağımsızlaştırılır (oynaklık normalizasyonu: son
`vol_window` bardaki günlük mutlak fiyat değişiminin EWMA ortalamasına
bölünür), sonra bir "forecast scalar" ile hedef ortalama mutlak değere
(`target_abs_forecast`, klasik Carver kuralı: 10) ölçeklenip ±`cap`
(klasik: 20) ile kırpılır.

Standart Carver çift kümesi (2,8)/(4,16)/(8,32)/(16,64)/(32,128)/(64,256)
— her biri bir öncekinin 2 katı pencere, klasik "geometrik seri" trend
takip bataryası — KULLANILIYOR (bu kısım kamuya açık/genel bilgi, kitaba
özgü değil). **TODO (K3 bekleniyor)**: `forecast_scalar` burada EMPİRİK
olarak (trailing `abs(vol_adj_ewmac)` ortalamasının tersi × 10) hesaplanır
— bu, Carver'ın KENDİ metodolojisinin genel ilkesiyle (skaler = hedef/
ortalama mutlak ham forecast) tutarlıdır ama kitabın (bilgi-bankasi/
teknik/11 — K3, HENÜZ ÇIKARILMADI) yayınladığı SABİT, geriye-dönük test
edilmiş skaler DEĞERLERİ değildir. K3 tamamlanınca `forecast_scalar_table`
parametresiyle sabit değerlere geçilebilir (bkz. görev notu: "K3 bitmediyse
Carver standart çiftlerini kullan ve TODO bırak").

Çıktı: her (fast,slow) çifti için `series["ewmac_{fast}_{slow}"]` (forecast,
-cap..+cap) + `series["ewmac_combined"]` (tüm çiftlerin ortalaması — Faz 10
forecast katmanının ilk gerçek üreticisi). Sinyaller: `ewmac_combined`'ın
sıfırı kestiği barlar (`ewmac_bullish`/`ewmac_bearish`)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from tlab.core.indicator import BaseIndicator
from tlab.core.params import BaseParams, params_hash
from tlab.core.types import Direction, IndicatorMeta, IndicatorResult, Signal, Timeframe
from tlab.features.ma import ema

_DEFAULT_PAIRS: tuple[tuple[int, int], ...] = (
    (2, 8), (4, 16), (8, 32), (16, 64), (32, 128), (64, 256),
)


@dataclass(frozen=True)
class EwmacParams(BaseParams):
    pairs: tuple[tuple[int, int], ...] = _DEFAULT_PAIRS
    vol_window: int = 25
    scalar_window: int = 252
    target_abs_forecast: float = 10.0
    cap: float = 20.0


class EWMACIndicator(BaseIndicator):
    """Carver EWMAC forecast bataryası — çoklu ufuk trend takip sinyali."""

    meta = IndicatorMeta(
        name="trend.ewmac",
        version="0.1.0",
        category="trend",
        description="Carver EWMAC forecast bataryası (vol-normalize edilmiş, -20..+20 ölçekli).",
        supported_timeframes=(Timeframe.H4, Timeframe.D1),
    )

    def __init__(self, params: EwmacParams | None = None) -> None:
        self.params: EwmacParams = params or EwmacParams()

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        p = self.params
        close = df["close"].astype(float)
        price_vol = close.diff().abs().ewm(span=p.vol_window, min_periods=p.vol_window).mean()

        series: dict[str, pd.Series] = {}
        forecasts: list[pd.Series] = []
        pair_names: list[str] = []
        for fast, slow in p.pairs:
            raw = ema(close, fast) - ema(close, slow)
            vol_adj = raw / price_vol.replace(0.0, np.nan)
            # Bkz. modül docstring'i — EMPİRİK skaler (TODO: K3 sabit tablosu).
            mean_abs = (
                vol_adj.abs().rolling(p.scalar_window, min_periods=p.vol_window * 2).mean()
            )
            scalar = p.target_abs_forecast / mean_abs.replace(0.0, np.nan)
            forecast = (vol_adj * scalar).clip(-p.cap, p.cap)
            name = f"ewmac_{fast}_{slow}"
            series[name] = forecast
            forecasts.append(forecast)
            pair_names.append(name)

        combined = pd.concat(forecasts, axis=1).mean(axis=1)
        series["ewmac_combined"] = combined
        series["ewmac_zero"] = pd.Series(0.0, index=df.index)

        signals: list[Signal] = []
        prev = combined.shift(1)
        for t in range(1, len(df)):
            now, before = combined.iloc[t], prev.iloc[t]
            if pd.isna(now) or pd.isna(before):
                continue
            direction: Direction
            if before <= 0.0 < now:
                event, direction = "ewmac_bullish", "long"
            elif before >= 0.0 > now:
                event, direction = "ewmac_bearish", "short"
            else:
                continue
            score = min(1.0, abs(float(now)) / p.cap)
            signals.append(
                Signal(
                    bar_time=df.index[t], detected_at=df.index[t],
                    direction=direction, state="confirmed", score=score,
                    payload={"event": event, "forecast": float(now)},
                )
            )

        last_combined = combined.iloc[-1]
        last_state = {
            "forecast_combined": None if pd.isna(last_combined) else float(last_combined),
            "forecast_by_pair": {
                name: (None if pd.isna(series[name].iloc[-1]) else float(series[name].iloc[-1]))
                for name in pair_names
            },
        }

        return IndicatorResult(
            indicator=self.meta.name, version=self.meta.version,
            params_hash=params_hash(p), symbol="", timeframe=Timeframe.D1,
            signals=signals, series=series,
            series_layout={"ewmac": ["ewmac_combined", "ewmac_zero"]},
            last_state=last_state,
        )
