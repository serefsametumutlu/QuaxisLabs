"""VolHarvestPair — sürekli ağırlıklı ("oynaklık hasadı") pair rebalans stratejisi.

`RelativeMomentumPair` (Faz 5) ile AYNI Z-skor makinesini (spread = log(Y) - β·log(X),
z = zscore(spread, window)) paylaşır ama sinyal İKİLİ (Y'ye TAM geç / X'e TAM geç)
DEĞİL — Z-skora göre SÜREKLİ bir hedef ağırlık `w_target(z)` üretir ve yalnızca
`rebalance_band` aşıldığında rebalans eder (bkz. `tlab/backtest/pairs_engine.py::
run_pair_backtest_weighted`). "Hasat" (harvest) serisi = aktif rebalans edilen
portföyün, HİÇ rebalans edilmeyen statik bir al-tut'a göre FAZLASI — spread ortalamaya
dönerken (mean-reversion) tekrar tekrar "ucuzu al, pahalıyı sat" yaparak kazanılan
alfa'yı izole eder.

**Duraklama (pause) mekanizması — backlog'daki "kointegrasyon çürüme izleyicisi"
notunun (CLAUDE.md, 2026-08-29) doğal karşılığı:** rolling ADF p-değeri
`adf_pause_p`'yi AŞARSA (kointegrasyon zayıflıyor) veya rolling halflife
`halflife_max`'ı AŞARSA (ortalamaya dönüş çok yavaşladı) veya (opsiyonel)
oynaklık rejimi aşırı uçtaysa (`vol_regime_filter`) — hedef ağırlık SON değerinde
DONDURULUR (z'yi takip etmeyi durdurur, mevcut pozisyon korunur, yeni rebalans
TETİKLENMEZ). Koşullar normale dönünce otomatik "resume" olur. ADF/halflife
kontrolü HER barda değil `check_stride` barda bir yapılır (GARCH `refit_stride`
ile AYNI performans gerekçesi — ADF testi ucuz değildir)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
import pandas as pd

from tlab.backtest.pairs_engine import Execution, run_pair_backtest_weighted
from tlab.core.indicator import BaseIndicator
from tlab.core.params import BaseParams, params_hash
from tlab.core.types import (
    Box,
    Direction,
    IndicatorMeta,
    IndicatorResult,
    Marker,
    Signal,
    Timeframe,
)
from tlab.features.stats import adf_pvalue, halflife, log_spread, rolling_beta, rolling_corr, zscore
from tlab.features.volatility import vol_zscore

BetaMethod = Literal["one", "rolling_ols"]
WeightFn = Literal["linear", "grid"]


@dataclass(frozen=True)
class VolHarvestParams(BaseParams):
    window: int = 60
    beta_method: BetaMethod = "rolling_ols"
    beta_window: int = 60
    min_periods: int = 60
    weight_fn: WeightFn = "linear"
    slope: float = 0.15
    w_min: float = 0.1
    w_max: float = 0.9
    grid_levels: tuple[float, ...] = (1.0, 1.5, 2.0, 2.5)
    grid_step: float = 0.125
    rebalance_band: float = 0.05
    vol_regime_filter: bool = True
    vol_regime_window: int = 20
    vol_regime_zscore_window: int = 100
    vol_regime_zscore_threshold: float = 2.0
    adf_pause_p: float = 0.10
    halflife_max: float = 60.0
    check_stride: int = 21
    commission_bps: float = 10.0
    start_capital: float = 100_000.0
    initial_weight: float = 0.5
    execution: Execution = "close"
    y_symbol: str = "Y"
    x_symbol: str = "X"


def _target_weight_from_z(z: float, p: VolHarvestParams) -> float:
    if p.weight_fn == "linear":
        raw = 0.5 - p.slope * z
    else:
        steps = sum(1 for lv in p.grid_levels if abs(z) >= lv)
        raw = 0.5 - math.copysign(steps * p.grid_step, z)
    return float(min(max(raw, p.w_min), p.w_max))


def _zone_state_from_z(z_today: float | None, k: float) -> str:
    """`relative_momentum.py::_zone_state`'in AYNISI (üç kademeli sınıflama,
    `renderer.py::_ZONE_STATE_TR`'nin beklediği AYNI anahtar kümesi) —
    kopyalanmadı, KASITLI olarak burada tekrar tanımlandı çünkü iki
    indikatör arasında paylaşılan bir bağımlılık kurmak (`relative_
    momentum.py`'yi import etmek) gereksiz bir bağ oluştururdu."""
    if z_today is None:
        return "veri_yok"
    az = abs(z_today)
    if az >= k:
        return "asiri_bolgede"
    if az >= 0.75 * k:
        return "bolgeye_yaklasiyor"
    return "notr"


def _beta_series(y_log: pd.Series, x_log: pd.Series, p: VolHarvestParams) -> pd.Series:
    rolling = rolling_beta(y_log, x_log, p.beta_window)
    if p.beta_method == "rolling_ols":
        return rolling
    first_valid = rolling.first_valid_index()
    if first_valid is None:
        return pd.Series(float("nan"), index=y_log.index)
    fixed_value = float(rolling.loc[first_valid])
    beta = pd.Series(float("nan"), index=y_log.index)
    beta.loc[first_valid:] = fixed_value
    return beta


class VolHarvestPair(BaseIndicator):
    """Z-skora göre SÜREKLİ ağırlıklı pair rebalans + "oynaklık hasadı" alfa'sı."""

    meta = IndicatorMeta(
        name="pair.vol_harvest",
        version="0.1.0",
        category="pair",
        description="Sürekli ağırlıklı pair rebalansı (Z-skor bazlı) + volatilite hasadı.",
        supported_timeframes=(Timeframe.D1, Timeframe.H4),
    )

    def __init__(self, params: VolHarvestParams | None = None) -> None:
        self.params: VolHarvestParams = params or VolHarvestParams()

    def compute(self, df: pd.DataFrame, context: dict[str, Any] | None = None) -> IndicatorResult:
        if context is None or "x" not in context:
            raise ValueError("VolHarvestPair context={'x': df_x} gerektirir")
        p = self.params
        df_x = context["x"]

        common_idx = df.index.intersection(df_x.index)
        if len(common_idx) < p.min_periods + 2:
            raise ValueError(
                f"Hizalanan {len(common_idx)} bar, min_periods+2={p.min_periods + 2}'den az"
            )

        y = df.loc[common_idx, "close"].astype(float)
        x = df_x.loc[common_idx, "close"].astype(float)
        y_open = df.loc[common_idx, "open"].astype(float) if "open" in df.columns else None
        x_open = df_x.loc[common_idx, "open"].astype(float) if "open" in df_x.columns else None

        y_log, x_log = np.log(y), np.log(x)
        beta = _beta_series(y_log, x_log, p)
        spread = log_spread(y, x, beta)
        z = zscore(spread, p.window)
        corr_series = rolling_corr(y_log, x_log, p.window)

        y_vol_z = vol_zscore(y, p.vol_regime_window, p.vol_regime_zscore_window)
        x_vol_z = vol_zscore(x, p.vol_regime_window, p.vol_regime_zscore_window)

        n = len(common_idx)
        first_ok = max(p.window, p.beta_window, p.min_periods)

        target_weight = pd.Series(float("nan"), index=common_idx)
        paused_series = pd.Series(False, index=common_idx)
        pause_reason: dict[int, tuple[str, float, float]] = {}

        paused = False
        last_target = p.initial_weight
        adf_p_last, hl_last = float("nan"), float("nan")

        for t in range(n):
            if t < first_ok:
                continue
            z_t = z.iloc[t]

            if (t - first_ok) % p.check_stride == 0:
                window_start = max(0, t - p.window + 1)
                spread_window = spread.iloc[window_start : t + 1].dropna()
                try:
                    adf_p_last = (
                        adf_pvalue(spread_window) if len(spread_window) >= 8 else float("nan")
                    )
                except ValueError:
                    adf_p_last = float("nan")
                try:
                    hl_last = halflife(spread_window) if len(spread_window) >= 3 else float("nan")
                except ValueError:
                    hl_last = float("nan")

            regime_extreme = False
            if p.vol_regime_filter:
                yv, xv = y_vol_z.iloc[t], x_vol_z.iloc[t]
                regime_extreme = (
                    (not pd.isna(yv) and abs(yv) > p.vol_regime_zscore_threshold)
                    or (not pd.isna(xv) and abs(xv) > p.vol_regime_zscore_threshold)
                )
            cointegration_broken = (not pd.isna(adf_p_last) and adf_p_last > p.adf_pause_p) or (
                not pd.isna(hl_last) and hl_last > p.halflife_max
            )
            should_pause = cointegration_broken or regime_extreme

            if should_pause and not paused:
                reason = "adf" if cointegration_broken else "vol_regime"
                pause_reason[t] = (reason, adf_p_last, hl_last)
            elif not should_pause and paused:
                pause_reason[t] = ("resumed", adf_p_last, hl_last)
            paused = should_pause

            if not paused and not pd.isna(z_t):
                last_target = _target_weight_from_z(float(z_t), p)
            target_weight.iloc[t] = last_target
            paused_series.iloc[t] = paused

        result = run_pair_backtest_weighted(
            y, x, target_weight, p.start_capital, p.commission_bps, p.rebalance_band,
            p.initial_weight, p.execution, y_open, x_open,
        )

        signals: list[Signal] = []
        markers: list[Marker] = []
        for t, (reason, adf_at_t, hl_at_t) in sorted(pause_reason.items()):
            event = "harvest_paused" if reason != "resumed" else "harvest_resumed"
            direction: Direction = "neutral"
            signals.append(
                Signal(
                    bar_time=common_idx[t], detected_at=common_idx[t], direction=direction,
                    state="confirmed", score=1.0,
                    payload={
                        "event": event, "reason": reason,
                        "adf_pvalue": None if pd.isna(adf_at_t) else adf_at_t,
                        "halflife": None if pd.isna(hl_at_t) or math.isinf(hl_at_t) else hl_at_t,
                    },
                )
            )
        for rb_idx in np.flatnonzero(result.rebalanced.to_numpy()):
            rb_i = int(rb_idx)
            w_now = float(result.actual_weight.iloc[rb_i])
            markers.append(
                Marker(
                    t=common_idx[rb_i], price=w_now, text=f"Rebalans w_{p.y_symbol}={w_now:.2f}",
                    kind="harvest_rebalance",
                )
            )

        boxes = _holding_dominant_boxes(
            common_idx, result.actual_weight, y, x, p.y_symbol, p.x_symbol
        )

        series = {
            "y_norm": y / y.iloc[0] * 100.0,
            "x_norm": x / x.iloc[0] * 100.0,
            "z": z,
            "upper": pd.Series(2.0, index=common_idx),
            "lower": pd.Series(-2.0, index=common_idx),
            "w_target": target_weight,
            "w_actual": result.actual_weight,
            "portfolio": result.portfolio,
            "buyhold_static": result.buyhold_static,
            # `buyhold_5050` — `_render_pair`'in (Faz 5, `RelativeMomentumPair`
            # için yazıldı) BEKLEDİĞİ sabit anahtar; `initial_weight=0.5`
            # varsayılanında `buyhold_static` ile ZATEN AYNI şey. DÜRÜST NOT:
            # `_render_pair`'in 4. paneli (w_Y adım grafiği + rebalans
            # markerları, görev metninin istediği) HENÜZ YOK — bu alias yalnızca
            # MEVCUT 3 paneli (fiyat/portföy/Z-skor) ücretsiz yeniden kullanmak
            # için; `w_target`/`w_actual`/`harvest` serileri ve `harvest_rebalance`
            # marker'ları IndicatorResult'ta HAZIR duruyor, ayrı bir görsel
            # geliştirme turunda 4. panel eklenebilir.
            "buyhold_5050": result.buyhold_static,
            "harvest": result.harvest,
            "paused": paused_series.astype(float),
        }

        z_today = float(z.iloc[-1]) if not pd.isna(z.iloc[-1]) else None
        z_yesterday = float(z.iloc[-2]) if n > 1 and not pd.isna(z.iloc[-2]) else None
        corr_today = float(corr_series.iloc[-1]) if not pd.isna(corr_series.iloc[-1]) else None
        w_actual_last = result.actual_weight.iloc[-1]
        w_actual_today = float(w_actual_last) if not pd.isna(w_actual_last) else None
        rebalanced_today = bool(result.rebalanced.iloc[-1]) if len(result.rebalanced) else False
        last_state = {
            "z_today": z_today,
            "z_yesterday": z_yesterday,
            "corr_today": corr_today,
            "w_target": (
                float(target_weight.iloc[-1]) if not pd.isna(target_weight.iloc[-1]) else None
            ),
            "w_actual": w_actual_today,
            "paused": bool(paused_series.iloc[-1]),
            "adf_pvalue": None if pd.isna(adf_p_last) else adf_p_last,
            "halflife": None if pd.isna(hl_last) or math.isinf(hl_last) else hl_last,
            "portfolio_value": float(result.portfolio.iloc[-1]),
            "net_pnl": result.net_pnl,
            "return_pct": result.return_pct,
            "harvest_value": float(result.harvest.iloc[-1]),
            "harvest_pct": (
                float(result.harvest.iloc[-1]) / p.start_capital * 100.0
            ),
            "rebalance_count": result.rebalance_count,
            "max_drawdown_pct": result.max_drawdown,
            # Aşağıdaki 4 alan YENİ bir hesap DEĞİL — `_render_pair`'in (Faz 5,
            # RelativeMomentumPair için yazıldı) `_pair_header_lines`'ının
            # beklediği alan adlarıyla UYUMLU biçimde YUKARIDAKİ değerlerin
            # yeniden ifadesi (bkz. vol_harvest.py docstring'i, "buyhold_5050"
            # alias'ıyla AYNI gerekçe — mevcut pair başlığını ücretsiz yeniden
            # kullanmak için).
            "holding": (
                p.y_symbol if w_actual_today is not None and w_actual_today >= 0.5 else p.x_symbol
            ),
            "signal_today": "YENİ REBALANS" if rebalanced_today else None,
            "zone_state": _zone_state_from_z(z_today, k=2.0),
            "n_trades": result.rebalance_count,
        }

        return IndicatorResult(
            indicator=self.meta.name, version=self.meta.version,
            params_hash=params_hash(p), symbol=f"{p.y_symbol}/{p.x_symbol}",
            timeframe=Timeframe.D1,
            signals=signals, boxes=boxes, markers=markers,
            series=series, last_state=last_state,
        )


def _holding_dominant_boxes(
    index: pd.Index, actual_weight: pd.Series, y: pd.Series, x: pd.Series,
    y_symbol: str, x_symbol: str,
) -> list[Box]:
    """`RelativeMomentumPair._holding_boxes` ile AYNI "tutulan dönem gölgesi"
    deseni ama İKİLİ değil — ağırlık >0.5 olan taraf o dönemde "baskın"
    (dominant) sayılır (extend-only, giriş barındaki fiyat aralığına
    sabitlenir)."""
    boxes: list[Box] = []
    n = len(index)
    run_start: int | None = None
    run_side: float | None = None

    def emit(start: int, end: int, side: float) -> None:
        symbol = y_symbol if side >= 0.5 else x_symbol
        style = "y_holding" if side >= 0.5 else "x_holding"
        entry_low = float(min(y.iloc[start], x.iloc[start]))
        entry_high = float(max(y.iloc[start], x.iloc[start]))
        boxes.append(
            Box(
                t0=index[start], t1=index[end], low=entry_low, high=entry_high,
                label=f"{symbol} Baskın", style=style,
            )
        )

    for i in range(n):
        w = actual_weight.iloc[i]
        side = None if pd.isna(w) else (1.0 if w >= 0.5 else 0.0)
        if side != run_side:
            if run_start is not None and run_side is not None:
                emit(run_start, i - 1, run_side)
            run_start, run_side = (i, side) if side is not None else (None, None)
    if run_start is not None and run_side is not None:
        emit(run_start, n - 1, run_side)
    return boxes
