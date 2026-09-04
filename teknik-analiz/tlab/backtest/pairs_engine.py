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


@dataclass(frozen=True)
class WeightedPairBacktestResult:
    """`run_pair_backtest_weighted` (Faz 8E, `mode="weights"`) çıktısı —
    `PairBacktestResult`'tan FARKLI: pozisyon 0/100% ikili değil, SÜREKLİ bir
    Y ağırlığı (`actual_weight`). `harvest`, aktif rebalans'ın (rebalance_band
    aşıldığında hedefe dönüş) STATİK (hiç rebalans edilmeyen, başlangıç
    ağırlığında sürüklenen) bir al-tut'a göre FAZLA getirisidir — "oynaklık
    hasadı" alfa'sının izolasyonu."""

    portfolio: pd.Series
    buyhold_static: pd.Series
    harvest: pd.Series
    actual_weight: pd.Series
    target_weight: pd.Series
    rebalanced: pd.Series
    rebalance_count: int
    net_pnl: float
    return_pct: float
    max_drawdown: float


def run_pair_backtest_weighted(
    y: pd.Series,
    x: pd.Series,
    target_weight: pd.Series,
    start_capital: float = 100_000.0,
    commission_bps: float = 10.0,
    rebalance_band: float = 0.05,
    initial_weight: float = 0.5,
    execution: Execution = "close",
    y_open: pd.Series | None = None,
    x_open: pd.Series | None = None,
) -> WeightedPairBacktestResult:
    """`target_weight[t]` (0..1, Y'nin hedef payı) ÇAĞIRANIN (`VolHarvestPair`)
    sorumluluğundadır — yalnızca t ve öncesiyle üretilmiş olmalı (non-repaint
    burada da DENETLENMEZ, `RelativeMomentumPair`/`run_pair_backtest` ile AYNI
    "muhasebe motoru sinyal üretmez" felsefesi). Gerçek (`actual_weight`)
    ağırlık fiyat hareketleriyle DOĞAL olarak sürüklenir; yalnızca
    `|actual - target| > rebalance_band` olduğunda TAM hedefe rebalans edilir
    (küçük/sık işlemleri önlemek için — Carver'ın "position inertia"sıyla AYNI
    ilke, bkz. bilgi-bankasi/teknik/11/"FORMÜL ZİNCİRİ" adım 13)."""
    n = len(y)
    commission = commission_bps / 10_000.0
    portfolio = pd.Series(start_capital, index=y.index, dtype=float)
    actual_weight = pd.Series(float("nan"), index=y.index, dtype=float)
    rebalanced = pd.Series(False, index=y.index, dtype=bool)
    rebalance_count = 0

    def _rebalance(capital: float, w: float, price_y: float, price_x: float) -> tuple[float, float]:
        return (capital * w) / price_y, (capital * (1.0 - w)) / price_x

    shares_y, shares_x = _rebalance(
        start_capital * (1.0 - commission), initial_weight, float(y.iloc[0]), float(x.iloc[0])
    )
    rebalance_count += 1

    for i in range(n):
        target = target_weight.iloc[i]
        price_y, price_x = float(y.iloc[i]), float(x.iloc[i])
        value = shares_y * price_y + shares_x * price_x
        current_w = (shares_y * price_y) / value if value > 0 else initial_weight

        if not pd.isna(target) and abs(current_w - target) > rebalance_band:
            exec_price_y, exec_idx = _execution_price(y, x, y_open, x_open, "y", i, execution, n)
            exec_price_x, _ = _execution_price(y, x, y_open, x_open, "x", i, execution, n)
            value_at_exec = shares_y * float(y.iloc[exec_idx]) + shares_x * float(x.iloc[exec_idx])
            value_after_cost = value_at_exec * (1.0 - commission)
            shares_y, shares_x = _rebalance(value_after_cost, target, exec_price_y, exec_price_x)
            rebalance_count += 1
            rebalanced.iloc[i] = True
            price_y, price_x = float(y.iloc[i]), float(x.iloc[i])
            value = shares_y * price_y + shares_x * price_x
            current_w = (shares_y * price_y) / value if value > 0 else target

        portfolio.iloc[i] = value
        actual_weight.iloc[i] = current_w

    y0, x0 = float(y.iloc[0]), float(x.iloc[0])
    static_shares_y = (start_capital * initial_weight * (1.0 - commission)) / y0
    static_shares_x = (start_capital * (1.0 - initial_weight) * (1.0 - commission)) / x0
    buyhold_static = static_shares_y * y + static_shares_x * x
    harvest = portfolio - buyhold_static

    net_pnl = float(portfolio.iloc[-1] - start_capital)
    return_pct = net_pnl / start_capital * 100.0
    running_max = portfolio.cummax()
    drawdown = (portfolio - running_max) / running_max
    max_drawdown = float(drawdown.min()) * 100.0 if len(drawdown) else 0.0

    return WeightedPairBacktestResult(
        portfolio=portfolio, buyhold_static=buyhold_static, harvest=harvest,
        actual_weight=actual_weight, target_weight=target_weight.reindex(y.index),
        rebalanced=rebalanced, rebalance_count=rebalance_count, net_pnl=net_pnl,
        return_pct=return_pct, max_drawdown=max_drawdown,
    )


@dataclass(frozen=True)
class MarketNeutralTrade:
    """Faz 2, 2C — `run_pair_backtest`'in `Trade`'inden FARKLI: tek bir
    sembolde değil, EŞ ZAMANLI iki bacakta (Y+X) tutulan bir pozisyon."""

    entry_idx: int
    entry_time: pd.Timestamp
    exit_idx: int | None
    exit_time: pd.Timestamp | None
    direction: Literal["long_y_short_x", "short_y_long_x"]
    beta: float
    entry_price_y: float
    entry_price_x: float
    exit_price_y: float | None
    exit_price_x: float | None
    pnl: float | None


@dataclass(frozen=True)
class MarketNeutralBacktestResult:
    portfolio: pd.Series
    trades: tuple[MarketNeutralTrade, ...] = field(default_factory=tuple)
    net_pnl: float = 0.0
    return_pct: float = 0.0
    n_trades: int = 0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    avg_holding_bars: float = 0.0


def run_pair_backtest_market_neutral(
    y: pd.Series,
    x: pd.Series,
    position: pd.Series,
    beta: pd.Series,
    start_capital: float = 100_000.0,
    commission_bps: float = 10.0,
    execution: Execution = "close",
    y_open: pd.Series | None = None,
    x_open: pd.Series | None = None,
) -> MarketNeutralBacktestResult:
    """Faz 2, 2C — `RelativeMomentumPair(mode="mean_reversion")` için beta-
    ölçekli EŞ ZAMANLI long/short muhasebesi (CLAUDE.md backlog madde 5'in
    uygulanması). `run_pair_backtest`'in (ROTASYONEL, her an ya Y ya X'te
    %100) AKSİNE burada Y VE X aynı anda, TERS yönlerde tutulur.

    `position[t]`: `+1.0` = Y long / X short, `-1.0` = Y short / X long,
    `0.0` = nakit (flat, pozisyon YOK), `NaN` = henüz sinyal yok (nakitte,
    `start_capital` sabit -- `run_pair_backtest`'in NaN semantiğiyle AYNI).
    `beta[t]`: pozisyon AÇILDIĞI bardaki hedge oranı (spread = log(Y) -
    beta*log(X) ile AYNI beta) kullanılır ve pozisyon KAPANANA kadar SABİT
    kalır (pozisyon içindeyken rolling beta'nın değişmesi muhasebeyi
    karmaşıklaştırmasın diye -- sinyal katmanının sorumluluğu, bu motor
    yalnızca MUHASEBELEŞTİRİR, sinyal üretmez).

    Dolar tahsisi: mevcut nakitin `n_y = nakit/(1+beta)` payı Y'ye, kalanı
    (`beta*n_y`) X'e -- toplam brüt maruziyet nakite eşit. Bu oran, spread'in
    KENDİ hassasiyet katsayısını (dY/Y ~ d(log Y) küçük hareketler için)
    dolar-getiri uzayına taşır: pozisyon değeri `sign*n_y*(Y_t/Y_0-1) -
    sign*n_x*(X_t/X_0-1)` şeklinde, X'teki beta-ölçekli hareket Y'dekini
    KISMEN dengeler. `beta<=0` (geçersiz/anlamsız hedge) ise o barda
    pozisyon AÇILMAZ (nakitte kalınır) -- sinyal katmanı bunu ÖNCEDEN
    filtrelemeli, burada yalnızca bir güvenlik ağı."""
    n = len(y)
    commission = commission_bps / 10_000.0
    portfolio = pd.Series(start_capital, index=y.index, dtype=float)
    trades: list[MarketNeutralTrade] = []

    shares_y = 0.0
    shares_x = 0.0
    current_dir: Literal["long_y_short_x", "short_y_long_x"] | None = None
    cash = start_capital
    entry_idx: int | None = None
    entry_time: pd.Timestamp | None = None
    entry_price_y: float | None = None
    entry_price_x: float | None = None
    position_gross = 0.0

    for i in range(n):
        p = position.iloc[i]
        target_dir: Literal["long_y_short_x", "short_y_long_x"] | None
        if pd.isna(p):
            target_dir = None
        elif p >= 0.5:
            target_dir = "long_y_short_x"
        elif p <= -0.5:
            target_dir = "short_y_long_x"
        else:
            target_dir = None

        if target_dir != current_dir:
            if execution == "close":
                exec_idx = i
            else:
                exec_idx = min(i + 1, n - 1)
            price_y = float((y_open if y_open is not None else y).iloc[exec_idx]) \
                if execution == "next_open" else float(y.iloc[exec_idx])
            price_x = float((x_open if x_open is not None else x).iloc[exec_idx]) \
                if execution == "next_open" else float(x.iloc[exec_idx])

            if current_dir is not None:
                assert entry_price_y is not None and entry_price_x is not None
                assert entry_idx is not None and entry_time is not None
                sign = 1.0 if current_dir == "long_y_short_x" else -1.0
                pnl = (
                    sign * shares_y * (price_y - entry_price_y)
                    - sign * shares_x * (price_x - entry_price_x)
                )
                exit_notional = abs(shares_y) * price_y + abs(shares_x) * price_x
                cash += position_gross + pnl - exit_notional * commission
                position_gross = 0.0
                trades.append(
                    MarketNeutralTrade(
                        entry_idx=entry_idx, entry_time=entry_time,
                        exit_idx=exec_idx, exit_time=y.index[exec_idx],
                        direction=current_dir, beta=shares_x / shares_y if shares_y else 0.0,
                        entry_price_y=entry_price_y, entry_price_x=entry_price_x,
                        exit_price_y=price_y, exit_price_x=price_x, pnl=pnl,
                    )
                )
                shares_y = shares_x = 0.0
                current_dir = None

            if target_dir is not None:
                beta_t = float(beta.iloc[i])
                if not (beta_t > 0):
                    target_dir = None
                else:
                    gross = cash * (1.0 - commission)
                    n_y = gross / (1.0 + beta_t)
                    n_x = gross - n_y
                    shares_y = n_y / price_y
                    shares_x = n_x / price_x
                    cash = 0.0
                    position_gross = gross
                    current_dir = target_dir
                    entry_idx, entry_time = exec_idx, y.index[exec_idx]
                    entry_price_y, entry_price_x = price_y, price_x

        if current_dir is None:
            portfolio.iloc[i] = cash
        else:
            assert entry_price_y is not None and entry_price_x is not None
            sign = 1.0 if current_dir == "long_y_short_x" else -1.0
            price_y_now, price_x_now = float(y.iloc[i]), float(x.iloc[i])
            unrealized = (
                sign * shares_y * (price_y_now - entry_price_y)
                - sign * shares_x * (price_x_now - entry_price_x)
            )
            portfolio.iloc[i] = cash + position_gross + unrealized

    if current_dir is not None and entry_idx is not None and entry_time is not None:
        assert entry_price_y is not None and entry_price_x is not None
        trades.append(
            MarketNeutralTrade(
                entry_idx=entry_idx, entry_time=entry_time, exit_idx=None, exit_time=None,
                direction=current_dir, beta=shares_x / shares_y if shares_y else 0.0,
                entry_price_y=entry_price_y, entry_price_x=entry_price_x,
                exit_price_y=None, exit_price_x=None, pnl=None,
            )
        )

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

    return MarketNeutralBacktestResult(
        portfolio=portfolio, trades=tuple(trades), net_pnl=net_pnl, return_pct=return_pct,
        n_trades=len(trades), max_drawdown=max_drawdown, win_rate=win_rate,
        avg_holding_bars=avg_holding,
    )
