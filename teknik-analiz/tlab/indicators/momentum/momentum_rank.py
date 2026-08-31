"""MomentumRank — Faz 8D "universe" kategorisi: evren-geneli momentum
sıralaması + göreli güç (RS) kırılımı. `AlphaRank` ile AYNI mimari
(`UniverseIndicator`, tüm evren TEK çağrıda, cross-sectional `rank_pct`
`pandas.rank(axis=1, pct=True)` ile — bkz. `alpha_rank.py` docstring'i).

Bileşenler (hepsi `tlab/features/xsec.py`/`volatility.py`/`ma.py`'den,
Faz 2-EK bu amaçla yazılmıştı):
- `momentum_horizons`: "12-1" tarzı çoklu ufuk momentum (skip son `skip`
  barı dışlar).
- vol-ayarlı momentum: her ufuk momentumu `realized_vol * sqrt(ufuk)`'a
  bölünür (kaba bir "Sharpe benzeri" normalizasyon — TASARIM KARARI, master
  prompt tam formül vermiyor).
- `rs_line` + eğim/t-istatistiği: `_rolling_trend_tstat` (bu modülde,
  `xsec.rolling_alpha_beta`'nın AYNI kapalı-form OLS yaklaşımı ama zamana
  karşı regresyon — y=rs, x=bar_index).
- `fip`: getiri tutarlılığı (düşük |fip| = pürüzsüz trend).
- `trend_score`: close/EMA20/EMA50/EMA200 sıralaması + eğim işaretleri
  (0..1, 5 koşulun ortalaması).

Skor = ortalama vol-ayarlı momentum + trend_score - |fip| (TASARIM KARARI,
basit toplam — ağırlıklar master prompt'ta verilmedi). Sinyaller:
`momentum_top_entry`/`momentum_top_exit` (rank_pct `top_pct` eşiğine giriş/
çıkış, `alpha_rank.py` ile AYNI desen) + `rs_breakout` (RS çizgisinin ÖNCEKİ
`rs_breakout_window` barın kesin ÜSTÜNE çıkması — bugünün barı HARİÇ trailing
maksimuma göre, "gerçek yeni zirve" için)."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from tlab.core.indicator import UniverseIndicator
from tlab.core.params import BaseParams, params_hash
from tlab.core.types import IndicatorMeta, IndicatorResult, Line, Signal, Timeframe
from tlab.features.ma import ema
from tlab.features.volatility import realized_vol
from tlab.features.xsec import fip, momentum_horizons, rs_line


@dataclass(frozen=True)
class MomentumRankParams(BaseParams):
    horizons: tuple[int, ...] = (21, 63, 126, 252)
    skip: int = 21
    fip_n: int = 126
    vol_adjust: bool = True
    vol_window: int = 20
    rs_slope_window: int = 63
    rs_breakout_window: int = 252
    ema_fast: int = 20
    ema_mid: int = 50
    ema_slow: int = 200
    top_pct: float = 10.0
    min_history_bars: int = 260


def _rolling_trend_tstat(series: pd.Series, window: int) -> tuple[pd.Series, pd.Series]:
    """`series`nin (zamana karşı) rolling OLS eğimi + t-istatistiği.
    `rolling_alpha_beta`'nın AYNI kapalı-form formülleri, x = 0..window-1
    (bar indeksi) — yalnızca [t-window+1,t] penceresini kullanır (non-repaint)."""
    values = series.to_numpy(dtype=float)
    n = len(values)
    slope = np.full(n, np.nan)
    tstat = np.full(n, np.nan)
    x = np.arange(window, dtype=float)
    x_mean = x.mean()
    x_var = float(((x - x_mean) ** 2).sum())
    dof = window - 2
    if window >= 2 and dof > 0 and x_var > 0:
        for t in range(window - 1, n):
            y = values[t - window + 1 : t + 1]
            if np.isnan(y).any():
                continue
            y_mean = y.mean()
            b = float(((x - x_mean) * (y - y_mean)).sum() / x_var)
            a = y_mean - b * x_mean
            resid = y - (a + b * x)
            resid_var = float((resid**2).sum() / dof)
            se_b = math.sqrt(resid_var / x_var) if resid_var > 0 else 0.0
            slope[t] = b
            tstat[t] = (b / se_b) if se_b > 0 else np.nan
    return pd.Series(slope, index=series.index), pd.Series(tstat, index=series.index)


@dataclass(frozen=True)
class _SymbolMomentumData:
    common_idx: pd.DatetimeIndex
    score: pd.Series
    ema_fast: pd.Series
    ema_mid: pd.Series
    ema_slow: pd.Series
    rs: pd.Series
    rs_slope: pd.Series
    rs_tstat: pd.Series
    fip: pd.Series
    trend_score: pd.Series
    raw_mom: dict[int, pd.Series]
    vol_adj_mom: dict[int, pd.Series]


class MomentumRank(UniverseIndicator):
    """Evren-geneli çoklu-ufuk momentum sıralaması + RS kırılımı."""

    meta = IndicatorMeta(
        name="momentum.momentum_rank",
        version="0.1.0",
        category="momentum",
        description="Evren-geneli çoklu-ufuk (12-1 tarzı) momentum sıralaması + RS kırılımı.",
        supported_timeframes=(Timeframe.D1,),
    )

    def __init__(self, params: MomentumRankParams | None = None) -> None:
        self.params: MomentumRankParams = params or MomentumRankParams()

    def _symbol_data(
        self, df: pd.DataFrame, index_close: pd.Series
    ) -> _SymbolMomentumData | None:
        p = self.params
        if len(df) < p.min_history_bars:
            return None
        close = df["close"].astype(float)
        common_idx = close.index.intersection(index_close.index).sort_values()
        if len(common_idx) < p.min_history_bars:
            return None

        close_c = close.reindex(common_idx)
        index_close_c = index_close.reindex(common_idx)
        ret_c = close_c.pct_change()

        raw_mom = momentum_horizons(close_c, p.horizons, p.skip)
        vol = realized_vol(close_c, p.vol_window, annualize=False)
        vol_adj_mom = {
            h: raw_mom[h] / (vol * math.sqrt(h)).replace(0.0, np.nan) for h in p.horizons
        } if p.vol_adjust else raw_mom
        score = pd.concat(vol_adj_mom.values(), axis=1).mean(axis=1)

        rs = rs_line(close_c, index_close_c)
        rs_slope, rs_tstat = _rolling_trend_tstat(np.log(rs), p.rs_slope_window)

        fip_series = fip(ret_c, p.fip_n)

        ema_f = ema(close_c, p.ema_fast)
        ema_m = ema(close_c, p.ema_mid)
        ema_s = ema(close_c, p.ema_slow)
        conditions = [
            close_c > ema_f, ema_f > ema_m, ema_m > ema_s,
            ema_f.diff() > 0, ema_m.diff() > 0,
        ]
        trend_score = sum(c.astype(float) for c in conditions) / len(conditions)

        combined_score = score + trend_score - fip_series.abs()

        return _SymbolMomentumData(
            common_idx=common_idx, score=combined_score, ema_fast=ema_f, ema_mid=ema_m,
            ema_slow=ema_s, rs=rs, rs_slope=rs_slope, rs_tstat=rs_tstat, fip=fip_series,
            trend_score=trend_score, raw_mom=raw_mom, vol_adj_mom=vol_adj_mom,
        )

    def compute_universe(
        self, universe: dict[str, pd.DataFrame], index_df: pd.DataFrame
    ) -> dict[str, IndicatorResult]:
        index_close = index_df["close"].astype(float)

        per_symbol: dict[str, _SymbolMomentumData] = {}
        for symbol, df in universe.items():
            data = self._symbol_data(df, index_close)
            if data is not None:
                per_symbol[symbol] = data

        if not per_symbol:
            return {}

        all_dates = sorted(set().union(*(d.common_idx for d in per_symbol.values())))
        all_dates_index = pd.DatetimeIndex(all_dates)
        score_df = pd.concat(
            {symbol: d.score.reindex(all_dates_index) for symbol, d in per_symbol.items()}, axis=1,
        )
        rank_pct_df = score_df.rank(axis=1, ascending=False, pct=True) * 100.0

        results: dict[str, IndicatorResult] = {}
        for symbol, d in per_symbol.items():
            rank_series = rank_pct_df[symbol].reindex(d.common_idx)
            results[symbol] = self._build_result(symbol, d, rank_series)
        return results

    def _build_result(
        self, symbol: str, d: _SymbolMomentumData, rank_series: pd.Series
    ) -> IndicatorResult:
        p = self.params
        idx = d.common_idx
        now, before = rank_series, rank_series.shift(1)
        entry_mask = ((before > p.top_pct) & (now <= p.top_pct)).fillna(False).to_numpy()
        exit_mask = ((before <= p.top_pct) & (now > p.top_pct)).fillna(False).to_numpy()

        prior_max = d.rs.shift(1).rolling(
            p.rs_breakout_window, min_periods=p.rs_breakout_window
        ).max()
        breakout_mask = (d.rs > prior_max).fillna(False).to_numpy()

        score_arr = d.score.reindex(idx).to_numpy()
        trend_arr = d.trend_score.reindex(idx).to_numpy()

        signals: list[Signal] = []
        for t in np.flatnonzero(entry_mask):
            sc = score_arr[t]
            conf = 0.5 if np.isnan(sc) else float(min(max(sc, 0.0), 1.0))
            signals.append(
                Signal(
                    bar_time=idx[t], detected_at=idx[t], direction="long", state="confirmed",
                    score=conf,
                    payload={
                        "event": "momentum_top_entry", "rank_pct": float(now.iloc[t]),
                        "score": None if np.isnan(sc) else float(sc),
                        "trend_score": None if np.isnan(trend_arr[t]) else float(trend_arr[t]),
                    },
                )
            )
        for t in np.flatnonzero(exit_mask):
            signals.append(
                Signal(
                    bar_time=idx[t], detected_at=idx[t], direction="neutral", state="confirmed",
                    score=0.3,
                    payload={"event": "momentum_top_exit", "rank_pct": float(now.iloc[t])},
                )
            )
        for t in np.flatnonzero(breakout_mask):
            signals.append(
                Signal(
                    bar_time=idx[t], detected_at=idx[t], direction="long", state="confirmed",
                    score=0.6,
                    payload={
                        "event": "rs_breakout", "rs": float(d.rs.iloc[t]),
                        "window": p.rs_breakout_window,
                    },
                )
            )
        signals.sort(key=lambda s: s.bar_time)

        lines = [
            Line(
                points=tuple(
                    (t, float(v)) for t, v in ema_series.reindex(idx).items() if not pd.isna(v)
                ),
                label=f"EMA{period}", style=f"ma_{period}",
            )
            for ema_series, period in (
                (d.ema_fast, p.ema_fast), (d.ema_mid, p.ema_mid), (d.ema_slow, p.ema_slow),
            )
        ]

        series: dict[str, pd.Series] = {
            "rs": d.rs.reindex(idx),
            "rs_slope": d.rs_slope.reindex(idx),
            "rs_tstat": d.rs_tstat.reindex(idx),
            "rs_tstat_upper": pd.Series(2.0, index=idx),
            "rs_tstat_lower": pd.Series(-2.0, index=idx),
            "fip": d.fip.reindex(idx),
            "trend_score": d.trend_score.reindex(idx),
        }
        for h in p.horizons:
            series[f"mom_{h}"] = d.vol_adj_mom[h].reindex(idx)

        last_rank = rank_series.iloc[-1] if len(rank_series) else float("nan")
        last_state = {
            "rank_pct": None if pd.isna(last_rank) else float(last_rank),
            "in_top_pct": bool(not pd.isna(last_rank) and last_rank <= p.top_pct),
            "score": None if pd.isna(d.score.iloc[-1]) else float(d.score.iloc[-1]),
            "trend_score": (
                None if pd.isna(d.trend_score.iloc[-1]) else float(d.trend_score.iloc[-1])
            ),
            "fip": None if pd.isna(d.fip.iloc[-1]) else float(d.fip.iloc[-1]),
            "rs_slope": None if pd.isna(d.rs_slope.iloc[-1]) else float(d.rs_slope.iloc[-1]),
            "rs_tstat": None if pd.isna(d.rs_tstat.iloc[-1]) else float(d.rs_tstat.iloc[-1]),
            "momentum_by_horizon": {
                str(h): (None if pd.isna(d.raw_mom[h].iloc[-1]) else float(d.raw_mom[h].iloc[-1]))
                for h in p.horizons
            },
        }

        return IndicatorResult(
            indicator=self.meta.name, version=self.meta.version,
            params_hash=params_hash(p), symbol=symbol, timeframe=Timeframe.D1,
            signals=signals, lines=lines, series=series,
            series_layout={
                "rs": ["rs"],
                "rs_egim_t_istatistik": [
                    "rs_slope", "rs_tstat", "rs_tstat_upper", "rs_tstat_lower",
                ],
                "ufuklar": [f"mom_{h}" for h in p.horizons],
                "fip": ["fip"],
            },
            last_state=last_state,
        )


def momentum_heatmap_data(
    results: dict[str, IndicatorResult], sector_map: dict[str, str], horizons: tuple[int, ...],
) -> pd.DataFrame:
    """`results` (compute_universe çıktısı) + sektör haritasından sektör ×
    ufuk ortalama HAM (vol-ayarsız) momentum matrisi — `tlab/viz/
    universe_charts.py::render_momentum_heatmap` bunu tüketir. Evren-geneli,
    salt biçimlendirme (hiçbir yeni hesap yok — `last_state["momentum_by_
    horizon"]`in olduğu gibi toplanması)."""
    rows: list[dict[str, float | str]] = []
    for symbol, result in results.items():
        sector = sector_map.get(symbol)
        if sector is None:
            continue
        by_horizon = result.last_state.get("momentum_by_horizon", {})
        row: dict[str, float | str] = {"sector": sector}
        for h in horizons:
            value = by_horizon.get(str(h))
            row[f"{h}g"] = float("nan") if value is None else value
        rows.append(row)
    if not rows:
        return pd.DataFrame(columns=[f"{h}g" for h in horizons])
    df = pd.DataFrame(rows).set_index("sector")
    return df.groupby("sector").mean(numeric_only=True)
