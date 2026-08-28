"""Long-only ikili (pair) geçiş backtest motoru.

Bağımsız kullanılabilir (bir `holding` serisi + iki fiyat serisi verildiğinde
çalışır) ama `RelativeMomentumPair` indikatörü tarafından da çağrılır. Non-
repaint sorumluluğu ÇAĞIRANA aittir (fibonacci.py/stats.py ile aynı felsefe):
`holding[t]` yalnızca t ve öncesi bilgiyle üretilmiş olmalı; bu motor sadece
verilen holding dizisini MUHASEBELEŞTİRİR, sinyal üretmez.

Muhasebe: geçiş barında (holding değiştiği bar) tüm sermaye komisyon
düşülerek diğer hisseye taşınır. `execution="close"` ise geçiş barının
kapanışında, `execution="next_open"` ise BİR SONRAKİ barın açılışında
yürütülür (aynı-bar-sinyal+işlem riskinden kaçınmak için — bkz.
bilgi-bankasi/teknik/kod/ch02_pairs_arbitraj.md DISIPLIN-08)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import pandas as pd

Execution = Literal["close", "next_open"]


@dataclass(frozen=True)
class Trade:
    entry_idx: int
    entry_time: pd.Timestamp
    exit_idx: int | None
    exit_time: pd.Timestamp | None
    side: Literal["y", "x"]
    entry_price: float
    exit_price: float | None
    pnl: float | None


@dataclass(frozen=True)
class PairBacktestResult:
    portfolio: pd.Series
    buyhold_5050: pd.Series
    trades: tuple[Trade, ...] = field(default_factory=tuple)
    net_pnl: float = 0.0
    return_pct: float = 0.0
    n_trades: int = 0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    avg_holding_bars: float = 0.0


def _execution_price(
    y: pd.Series, x: pd.Series, y_open: pd.Series | None, x_open: pd.Series | None,
    side: Literal["y", "x"], switch_idx: int, execution: Execution, n: int,
) -> tuple[float, int]:
    """Geçişin fiilen hangi barda/fiyattan yürütüldüğünü döner (idx, fiyat)."""
    price_series = y if side == "y" else x
    if execution == "close":
        return float(price_series.iloc[switch_idx]), switch_idx
    exec_idx = switch_idx + 1
    if exec_idx >= n:
        return float(price_series.iloc[switch_idx]), switch_idx
    open_series = y_open if side == "y" else x_open
    price = (
        float(open_series.iloc[exec_idx])
        if open_series is not None
        else float(price_series.iloc[exec_idx])
    )
    return price, exec_idx


def run_pair_backtest(
    y: pd.Series,
    x: pd.Series,
    holding: pd.Series,
    start_capital: float = 100_000.0,
    commission_bps: float = 10.0,
    execution: Execution = "close",
    y_open: pd.Series | None = None,
    x_open: pd.Series | None = None,
) -> PairBacktestResult:
    """`holding[t]` 1.0 -> Y tutuluyor, 0.0 -> X tutuluyor, NaN -> henüz pozisyon
    yok (sinyal beklenirken sermaye nakitte/başlangıç sermayesinde sabit
    kalır). y/x aynı index'e (inner-join sonrası) hizalanmış olmalı."""
    n = len(y)
    commission = commission_bps / 10_000.0
    portfolio = pd.Series(start_capital, index=y.index, dtype=float)
    trades: list[Trade] = []

    shares = 0.0
    current_side: Literal["y", "x"] | None = None
    cash = start_capital
    pending_entry_idx: int | None = None
    pending_entry_time: pd.Timestamp | None = None
    pending_entry_price: float | None = None

    for i in range(n):
        h = holding.iloc[i]
        target_side: Literal["y", "x"] | None = (
            None if pd.isna(h) else ("y" if h >= 0.5 else "x")
        )

        if target_side is not None and target_side != current_side:
            exec_price, exec_idx = _execution_price(
                y, x, y_open, x_open, target_side, i, execution, n
            )
            if current_side is not None:
                exit_price = float(y.iloc[exec_idx] if current_side == "y" else x.iloc[exec_idx])
                cash = shares * exit_price * (1.0 - commission)
                if pending_entry_idx is not None and pending_entry_price is not None:
                    trade_pnl = shares * (exit_price - pending_entry_price)
                    trades.append(
                        Trade(
                            entry_idx=pending_entry_idx, entry_time=pending_entry_time,
                            exit_idx=exec_idx, exit_time=y.index[exec_idx],
                            side=current_side, entry_price=pending_entry_price,
                            exit_price=exit_price, pnl=trade_pnl,
                        )
                    )
            buy_cash = cash * (1.0 - commission)
            shares = buy_cash / exec_price
            current_side = target_side
            pending_entry_idx = exec_idx
            pending_entry_time = y.index[exec_idx]
            pending_entry_price = exec_price
            cash = 0.0

        if current_side is None:
            portfolio.iloc[i] = start_capital
        else:
            price = y.iloc[i] if current_side == "y" else x.iloc[i]
            portfolio.iloc[i] = shares * float(price) + cash

    if (
        current_side is not None
        and pending_entry_idx is not None
        and pending_entry_price is not None
    ):
        open_side: Literal["y", "x"] = current_side
        trades.append(
            Trade(
                entry_idx=pending_entry_idx, entry_time=pending_entry_time,
                exit_idx=None, exit_time=None, side=open_side,
                entry_price=pending_entry_price, exit_price=None, pnl=None,
            )
        )

    y0, x0 = float(y.iloc[0]), float(x.iloc[0])
    buyhold = 0.5 * start_capital * (y / y0) + 0.5 * start_capital * (x / x0)

    closed = [t for t in trades if t.pnl is not None]
    net_pnl = float(portfolio.iloc[-1] - start_capital)
    return_pct = net_pnl / start_capital * 100.0
    running_max = portfolio.cummax()
    drawdown = (portfolio - running_max) / running_max
    max_drawdown = float(drawdown.min()) * 100.0 if len(drawdown) else 0.0
    wins = sum(1 for t in closed if (t.pnl or 0.0) > 0)
    win_rate = (wins / len(closed) * 100.0) if closed else 0.0
    avg_holding = (
        sum((t.exit_idx or 0) - t.entry_idx for t in closed) / len(closed) if closed else 0.0
    )

    return PairBacktestResult(
        portfolio=portfolio, buyhold_5050=buyhold, trades=tuple(trades),
        net_pnl=net_pnl, return_pct=return_pct, n_trades=len(trades),
        max_drawdown=max_drawdown, win_rate=win_rate, avg_holding_bars=avg_holding,
    )
