"""RelativeMomentumPair — long-only rölatif momentum geçişi (pair trading).

`context={"x": df_x}` alan İLK indikatör (Faz 0'dan beri BaseIndicator.compute
context parametresini destekliyordu, ama Faz 3/4'teki hiçbir indikatör
kullanmamıştı). `df` = Y hissesi, `context["x"]` = X hissesi.

Hesap: spread = log(Y) - β·log(X); z = (spread - rolling_mean)/rolling_std
(bkz. tlab/features/stats.py — bu modül Faz 2'de tam bu amaçla yazılmıştı).
Sinyal DÖNÜŞ ONAYLIDIR (eşiği İLK aşan bar değil, eşiğin İÇİNE geri dönen
bar): z[t-1] < -k ve z[t] >= -k -> Y ucuzdu, dönüş onaylandı -> "Y AL";
z[t-1] > +k ve z[t] <= +k -> "X AL". Yalnızca kapanmış barlarla, yalnızca
min_periods sonrası.

bilgi-bankasi/teknik/kod/ch02_pairs_arbitraj.md (K2, STRAT-08) disiplinleri:
- DISIPLIN-08: β geçmişten (yalnızca t'den ÖNCEki pencere) tahmin edilir,
  sinyal t'de üretilir, işlem execution parametresine göre t'nin kapanışında
  ya da t+1'in açılışında yürütülür — üç zaman dilimi hiç karışmaz.
- DISIPLIN-06 (bkz. discovery.py): bu indikatörün KENDİSİ çift seçmez,
  yalnızca VERİLEN bir çiftin sinyalini üretir — seçim-lookahead riski
  discovery.py'nin sorumluluğundadır, burada YOKTUR.

Context güvenlik deseni: `context["x"]` HER ZAMAN önce `df.index` (Y) ile
inner-join edilir (`common_idx`), SONRA tüm hesaplar `common_idx`'e
kısıtlanmış Series'ler üzerinden yapılır. Bu yüzden context DataFrame'i
`df`'den daha uzun/gelecek barlar içerse bile sızıntı YOKTUR — kesilme
sınırı her zaman `df`'nin kendi uzunluğundan gelir. `tlab/testing/
repaint.py`'nin context'i de kesen genel mekanizması yine de gelecekteki
(bu deseni takip etmeyen) context'li indikatörler için bağımsız bir
güvenlik ağıdır."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import pandas as pd

from tlab.backtest.pairs_engine import run_pair_backtest
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

BetaMethod = Literal["one", "rolling_ols"]
InitialHolding = Literal["y", "x", "none_until_signal"]
Execution = Literal["close", "next_open"]


@dataclass(frozen=True)
class RelativeMomentumParams(BaseParams):
    window: int = 90
    k: float = 2.0
    beta_method: BetaMethod = "rolling_ols"
    beta_window: int = 90
    min_periods: int = 90
    execution: Execution = "close"
    commission_bps: float = 10.0
    start_capital: float = 100_000.0
    initial_holding: InitialHolding = "none_until_signal"
    y_symbol: str = "Y"
    x_symbol: str = "X"


def _beta_series(y_log: pd.Series, x_log: pd.Series, p: RelativeMomentumParams) -> pd.Series:
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


class RelativeMomentumPair(BaseIndicator):
    """İki hisse (Y=df, X=context["x"]) arasında long-only rölatif momentum
    geçişi: Z-skoru ±k eşiğinden dönüş onaylandığında ucuz kalan tarafa
    geçiş yapılır."""

    meta = IndicatorMeta(
        name="pair.relative_momentum",
        version="0.1.0",
        category="pair",
        description="Long-only rölatif momentum geçişi (Z-skor dönüş onaylı) + backtest.",
        supported_timeframes=(Timeframe.D1, Timeframe.H4),
    )

    def __init__(self, params: RelativeMomentumParams | None = None) -> None:
        self.params: RelativeMomentumParams = params or RelativeMomentumParams()

    def compute(self, df: pd.DataFrame, context: dict[str, Any] | None = None) -> IndicatorResult:
        if context is None or "x" not in context:
            raise ValueError("RelativeMomentumPair context={'x': df_x} gerektirir")
        p = self.params
        df_x = context["x"]

        common_idx = df.index.intersection(df_x.index)
        dropped_y = len(df) - len(common_idx)
        dropped_x = len(df_x) - len(common_idx)
        if len(common_idx) < p.min_periods + 2:
            raise ValueError(
                f"Hizalanan {len(common_idx)} bar, min_periods+2={p.min_periods + 2}'den az"
            )

        y = df.loc[common_idx, "close"].astype(float)
        x = df_x.loc[common_idx, "close"].astype(float)
        y_open = df.loc[common_idx, "open"].astype(float) if "open" in df.columns else None
        x_open = df_x.loc[common_idx, "open"].astype(float) if "open" in df_x.columns else None

        y_log, x_log = y.apply(_safe_log), x.apply(_safe_log)
        beta = _beta_series(y_log, x_log, p)
        spread = log_spread(y, x, beta)
        z = zscore(spread, p.window)
        corr_series = rolling_corr(y_log, x_log, p.window)

        n = len(common_idx)
        first_signal_ok = max(p.window, p.beta_window, p.min_periods)

        holding = _initial_holding_series(common_idx, p.initial_holding)
        signals: list[Signal] = []
        markers: list[Marker] = []

        for t in range(1, n):
            if t < first_signal_ok:
                continue
            z_prev, z_now = z.iloc[t - 1], z.iloc[t]
            if pd.isna(z_prev) or pd.isna(z_now):
                continue

            side: Literal["y", "x"] | None = None
            if z_prev < -p.k and z_now >= -p.k:
                side = "y"
            elif z_prev > p.k and z_now <= p.k:
                side = "x"
            if side is None:
                continue

            holding.iloc[t:] = 1.0 if side == "y" else 0.0
            direction: Direction = "long"
            symbol = p.y_symbol if side == "y" else p.x_symbol
            window_start = max(0, t - p.window + 1)
            corr_t = corr_series.iloc[t]
            corr = float(corr_t) if not pd.isna(corr_t) else float("nan")
            spread_window = spread.iloc[window_start : t + 1].dropna()
            try:
                adf_p = adf_pvalue(spread_window) if len(spread_window) >= 8 else float("nan")
            except ValueError:
                adf_p = float("nan")
            try:
                hl = halflife(spread_window) if len(spread_window) >= 3 else float("nan")
            except ValueError:
                hl = float("nan")

            payload = {
                "event": "regime_switch", "side": side, "symbol": symbol,
                "z_prev": float(z_prev), "z_now": float(z_now),
                "beta": float(beta.iloc[t]) if not pd.isna(beta.iloc[t]) else None,
                "corr": corr, "adf_pvalue": adf_p, "halflife": hl,
            }
            signals.append(
                Signal(
                    bar_time=common_idx[t], detected_at=common_idx[t], direction=direction,
                    state="confirmed", score=1.0, payload=payload,
                )
            )
            markers.append(
                Marker(t=common_idx[t], price=float(z_now), text=f"{symbol} AL", kind="pair_signal")
            )

        result = run_pair_backtest(
            y, x, holding, p.start_capital, p.commission_bps, p.execution, y_open, x_open,
        )

        boxes = _holding_boxes(common_idx, holding, y, x, p.y_symbol, p.x_symbol)

        series = {
            "y_norm": y / y.iloc[0] * 100.0,
            "x_norm": x / x.iloc[0] * 100.0,
            "z": z,
            "upper": pd.Series(p.k, index=common_idx),
            "lower": pd.Series(-p.k, index=common_idx),
            "portfolio": result.portfolio,
            "buyhold_5050": result.buyhold_5050,
            "holding": holding,
        }

        z_today = float(z.iloc[-1]) if not pd.isna(z.iloc[-1]) else None
        z_yesterday = float(z.iloc[-2]) if n > 1 and not pd.isna(z.iloc[-2]) else None
        last_signal = signals[-1] if signals else None
        fired_today = last_signal is not None and last_signal.bar_time == common_idx[-1]
        signal_today = "YENİ AL SİNYALİ" if fired_today else None
        last_holding = holding.iloc[-1]
        holding_symbol = (
            None if pd.isna(last_holding) else (p.y_symbol if last_holding >= 0.5 else p.x_symbol)
        )
        last_state = {
            "z_today": z_today,
            "z_yesterday": z_yesterday,
            "holding": holding_symbol,
            "signal_today": signal_today,
            "portfolio_value": float(result.portfolio.iloc[-1]),
            "net_pnl": result.net_pnl,
            "return_pct": result.return_pct,
            "n_trades": result.n_trades,
            "max_drawdown_pct": result.max_drawdown,
            "win_rate_pct": result.win_rate,
            "avg_holding_bars": result.avg_holding_bars,
            "dropped_bars_y": dropped_y,
            "dropped_bars_x": dropped_x,
            "zone_state": _zone_state(z_today, p.k),
        }

        return IndicatorResult(
            indicator=self.meta.name, version=self.meta.version,
            params_hash=params_hash(p), symbol=f"{p.y_symbol}/{p.x_symbol}",
            timeframe=Timeframe.D1,
            signals=signals, boxes=boxes, markers=markers,
            series=series, last_state=last_state,
        )


def _safe_log(v: float) -> float:
    import math

    return math.log(v) if v > 0 else float("nan")


def _initial_holding_series(index: pd.Index, initial_holding: InitialHolding) -> pd.Series:
    if initial_holding == "none_until_signal":
        return pd.Series(float("nan"), index=index)
    value = 1.0 if initial_holding == "y" else 0.0
    return pd.Series(value, index=index)


def _zone_state(z_today: float | None, k: float) -> str:
    """Faz 6 tarama panosu için üç kademeli sınıflama (bkz. images/ referans
    ekran görüntüsü: YENİ AL SİNYALİ / DEVAM EDEN FIRSAT / BÖLGEYE
    YAKLAŞIYOR) — burada yalnızca ANLIK durum hesaplanır, sıralama Faz 6'nın işi."""
    if z_today is None:
        return "veri_yok"
    az = abs(z_today)
    if az >= k:
        return "asiri_bolgede"
    if az >= 0.75 * k:
        return "bolgeye_yaklasiyor"
    return "notr"


def _holding_boxes(
    index: pd.Index, holding: pd.Series, y: pd.Series, x: pd.Series, y_symbol: str, x_symbol: str
) -> list[Box]:
    """Tutulan dönem kutuları — low/high, o pencerede Y ve X fiyatlarının
    kapladığı aralıktır (renderer bunu fiyat panelinin ARKASINA tam
    yükseklikte gölge olarak çizecek, bkz. Faz 7 — bu alan yalnızca
    o pencerenin gerçek fiyat aralığını kaydeder, extend-only sözleşmesi
    gereği kutu bittiğinde bir daha değişmez)."""
    boxes: list[Box] = []
    n = len(index)
    run_start: int | None = None
    run_side: float | None = None

    def emit(start: int, end: int, side: float) -> None:
        # low/high YALNIZCA giriş barından (start) hesaplanır ve bir daha
        # değişmez (ranges.py/zones.py'deki "sınırlar tespit anında
        # sabitlenir" ilkesiyle aynı) — pencerenin TÜM aralığından
        # (start..end) hesaplamak, kutu hâlâ açıkken (end ileri kaydıkça)
        # low/high'ın sonradan değişmesine (repaint) yol açardı.
        symbol = y_symbol if side >= 0.5 else x_symbol
        style = "y_holding" if side >= 0.5 else "x_holding"
        entry_low = float(min(y.iloc[start], x.iloc[start]))
        entry_high = float(max(y.iloc[start], x.iloc[start]))
        boxes.append(
            Box(
                t0=index[start], t1=index[end], low=entry_low, high=entry_high,
                label=f"{symbol} Tutulan Dönem", style=style,
            )
        )

    for i in range(n):
        h = holding.iloc[i]
        side = None if pd.isna(h) else (1.0 if h >= 0.5 else 0.0)
        if side != run_side:
            if run_start is not None and run_side is not None:
                emit(run_start, i - 1, run_side)
            run_start, run_side = (i, side) if side is not None else (None, None)
    if run_start is not None and run_side is not None:
        emit(run_start, n - 1, run_side)
    return boxes
