"""AlphaRank — Faz 8D "universe" kategorisi: evren-geneli rolling-alfa
sıralaması. `UniverseIndicator` (bkz. `tlab/core/indicator.py`) — tekil
`BaseIndicator.compute(df, context)` yerine `compute_universe({sembol: df},
index_df)` alır, çünkü sıralama (rank_pct) TANIM GEREĞİ tüm evrenin AYNI
bardaki skorlarını birlikte görmeyi gerektirir.

Her sembol için `rolling_alpha_beta` (bkz. `tlab/features/xsec.py`, TAM
BU AMAÇLA Faz 2-EK'te yazılmıştı) her yapılandırılan `windows` penceresinde
alpha/beta/t_stat üretir; skor = pencereler arası ORTALAMA t_stat (ölçek-
bağımsız, farklı ufuklar arası birleştirmeye alpha_ann'dan daha uygun —
TASARIM KARARI, master prompt tam formül vermiyor). `persistence` =
1 - |fip(aktif_getiri, window)| (`fip` zaten "tutarlılık" ölçüsü için var,
Faz 8D notunda AÇIKÇA bu amaç için işaret edilmişti).

Sıralama: TÜM sembollerin skor serileri ORTAK bir {tarih: sembol} matrisinde
toplanır (`score_df`), her SATIR (bar) için `pandas.rank(axis=1, pct=True)`
ile cross-sectional yüzdelik dilim hesaplanır — `xsec.rank_pct`'in AYNI
"en iyi -> en küçük pct" yönü, ama TEK bir anlık görüntü yerine TÜM tarihçe
için vektörize edilmiş hâli (`xsec.rank_pct`'in kendisi `last_state`'teki
GÜNCEL anlık görüntü için ayrıca kullanılır — modülün kendi docstring'inde
işaret ettiği kullanım). Likidite filtresi (`min_liquidity_try`) ZAMANA
GÖRE DEĞİŞİR: bir sembolün `liquidity_window` barlık ortalama cirosu
(close*volume) eşiğin altındaysa O BARDA skoru NaN'a çevrilir (o barın
sıralamasından TAMAMEN çıkar) — sabit/tek seferlik bir filtre DEĞİL.

Sinyaller (`alpha_entry`/`alpha_exit`): rank_pct'in `top_pct` eşiğine
GİRİŞ/ÇIKIŞ barı (bkz. `momentum_rank.py`'deki AYNI desen)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from tlab.core.indicator import UniverseIndicator
from tlab.core.params import BaseParams, params_hash
from tlab.core.types import IndicatorMeta, IndicatorResult, Signal, Timeframe
from tlab.features.xsec import fip, rolling_alpha_beta


@dataclass(frozen=True)
class AlphaRankParams(BaseParams):
    windows: tuple[int, ...] = (60, 120, 250)
    min_liquidity_try: float = 5_000_000.0
    liquidity_window: int = 20
    top_pct: float = 10.0
    min_history_bars: int = 260


@dataclass(frozen=True)
class _SymbolAlphaData:
    common_idx: pd.DatetimeIndex
    score: pd.Series
    liquidity_ok: pd.Series
    window_stats: dict[int, dict[str, pd.Series]]
    close_norm: pd.Series
    index_norm: pd.Series
    cum_epsilon: pd.Series


class AlphaRank(UniverseIndicator):
    """Evren-geneli rolling-alfa sıralaması (rank_pct <= top_pct -> alfa girişi)."""

    meta = IndicatorMeta(
        name="momentum.alpha_rank",
        version="0.1.0",
        category="momentum",
        description="Evren-geneli rolling-alfa (endekse göre) sıralaması.",
        supported_timeframes=(Timeframe.D1,),
    )

    def __init__(self, params: AlphaRankParams | None = None) -> None:
        self.params: AlphaRankParams = params or AlphaRankParams()

    def _symbol_data(self, df: pd.DataFrame, index_ret: pd.Series) -> _SymbolAlphaData | None:
        p = self.params
        if len(df) < p.min_history_bars:
            return None
        close = df["close"].astype(float)
        ret = close.pct_change()
        common_idx = ret.index.intersection(index_ret.index).sort_values()
        if len(common_idx) < p.min_history_bars:
            return None

        ret_c = ret.reindex(common_idx)
        idx_c = index_ret.reindex(common_idx)

        window_stats: dict[int, dict[str, pd.Series]] = {}
        t_stats: list[pd.Series] = []
        for w in p.windows:
            rab = rolling_alpha_beta(ret_c, idx_c, w)
            active_ret = ret_c - idx_c
            persistence = 1.0 - fip(active_ret, w).abs()
            window_stats[w] = {
                "alpha_ann": rab.alpha * 252.0, "beta": rab.beta,
                "t_stat": rab.t_stat, "persistence": persistence,
            }
            t_stats.append(rab.t_stat)
        score = pd.concat(t_stats, axis=1).mean(axis=1)

        turnover = (close * df["volume"].astype(float)).reindex(common_idx)
        liquidity_avg = turnover.rolling(p.liquidity_window, min_periods=p.liquidity_window).mean()
        liquidity_ok = liquidity_avg >= p.min_liquidity_try

        primary_window = p.windows[len(p.windows) // 2]
        primary = window_stats[primary_window]
        epsilon = ret_c - (primary["alpha_ann"] / 252.0 + primary["beta"] * idx_c)
        cum_epsilon = epsilon.fillna(0.0).cumsum()

        close_c = close.reindex(common_idx)
        return _SymbolAlphaData(
            common_idx=common_idx, score=score, liquidity_ok=liquidity_ok,
            window_stats=window_stats, close_norm=close_c / close_c.iloc[0] * 100.0,
            index_norm=pd.Series(dtype=float), cum_epsilon=cum_epsilon,
        )

    def compute_universe(
        self, universe: dict[str, pd.DataFrame], index_df: pd.DataFrame
    ) -> dict[str, IndicatorResult]:
        p = self.params
        index_close = index_df["close"].astype(float)
        index_ret = index_close.pct_change()

        per_symbol: dict[str, _SymbolAlphaData] = {}
        for symbol, df in universe.items():
            data = self._symbol_data(df, index_ret)
            if data is None:
                continue
            idx_close_c = index_close.reindex(data.common_idx)
            data = _SymbolAlphaData(
                common_idx=data.common_idx, score=data.score, liquidity_ok=data.liquidity_ok,
                window_stats=data.window_stats, close_norm=data.close_norm,
                index_norm=idx_close_c / idx_close_c.iloc[0] * 100.0,
                cum_epsilon=data.cum_epsilon,
            )
            per_symbol[symbol] = data

        if not per_symbol:
            return {}

        all_dates = sorted(set().union(*(d.common_idx for d in per_symbol.values())))
        all_dates_index = pd.DatetimeIndex(all_dates)

        def _masked_score(d: _SymbolAlphaData) -> pd.Series:
            s = d.score.reindex(all_dates_index)
            liq = d.liquidity_ok.reindex(all_dates_index).fillna(False)
            return s.where(liq)

        score_df = pd.concat(
            {symbol: _masked_score(d) for symbol, d in per_symbol.items()}, axis=1,
        )
        rank_pct_df = score_df.rank(axis=1, ascending=False, pct=True) * 100.0

        primary_window = p.windows[len(p.windows) // 2]
        results: dict[str, IndicatorResult] = {}
        for symbol, d in per_symbol.items():
            rank_series = rank_pct_df[symbol].reindex(d.common_idx)
            results[symbol] = self._build_result(symbol, d, rank_series, primary_window)
        return results

    def _build_result(
        self, symbol: str, d: _SymbolAlphaData, rank_series: pd.Series, primary_window: int,
    ) -> IndicatorResult:
        p = self.params
        idx = d.common_idx
        now, before = rank_series, rank_series.shift(1)
        entry_mask = ((before > p.top_pct) & (now <= p.top_pct)).fillna(False).to_numpy()
        exit_mask = ((before <= p.top_pct) & (now > p.top_pct)).fillna(False).to_numpy()

        primary = d.window_stats[primary_window]
        stat_arrays = {key: s.reindex(idx).to_numpy() for key, s in primary.items()}

        def _payload_at(event: str, t: int) -> dict:
            def _val(key: str) -> float | None:
                v = stat_arrays[key][t]
                return None if np.isnan(v) else float(v)

            return {
                "event": event, "window": primary_window,
                "alpha_ann": _val("alpha_ann"), "t_stat": _val("t_stat"), "beta": _val("beta"),
            }

        signals: list[Signal] = []
        for t in np.flatnonzero(entry_mask):
            t_stat_val = stat_arrays["t_stat"][t]
            score = 0.5 if np.isnan(t_stat_val) else float(min(abs(t_stat_val) / 4.0, 1.0))
            signals.append(
                Signal(
                    bar_time=idx[t], detected_at=idx[t], direction="long", state="confirmed",
                    score=score, payload=_payload_at("alpha_entry", int(t)),
                )
            )
        for t in np.flatnonzero(exit_mask):
            signals.append(
                Signal(
                    bar_time=idx[t], detected_at=idx[t], direction="neutral", state="confirmed",
                    score=0.3, payload=_payload_at("alpha_exit", int(t)),
                )
            )
        signals.sort(key=lambda s: s.bar_time)

        t_stat_series = primary["t_stat"].reindex(idx)
        series = {
            "close_norm": d.close_norm.reindex(idx),
            "index_norm": d.index_norm.reindex(idx),
            "alpha_ann": primary["alpha_ann"].reindex(idx),
            "t_stat": t_stat_series,
            "t_stat_upper": pd.Series(2.0, index=idx),
            "t_stat_lower": pd.Series(-2.0, index=idx),
            "beta": primary["beta"].reindex(idx),
            "cum_epsilon": d.cum_epsilon.reindex(idx),
        }

        last_rank = rank_series.iloc[-1] if len(rank_series) else float("nan")
        windows_state = {}
        for w, stats in d.window_stats.items():
            windows_state[str(w)] = {
                key: (None if pd.isna(s.iloc[-1]) else float(s.iloc[-1]))
                for key, s in stats.items()
            }
        last_state = {
            "rank_pct": None if pd.isna(last_rank) else float(last_rank),
            "in_top_pct": bool(not pd.isna(last_rank) and last_rank <= p.top_pct),
            "liquidity_ok": bool(d.liquidity_ok.iloc[-1]) if len(d.liquidity_ok) else False,
            "primary_window": primary_window,
            "windows": windows_state,
        }

        return IndicatorResult(
            indicator=self.meta.name, version=self.meta.version,
            params_hash=params_hash(p), symbol=symbol, timeframe=Timeframe.D1,
            signals=signals, series=series,
            series_layout={
                "vs_endeks": ["close_norm", "index_norm"],
                "alfa_t_istatistik": ["alpha_ann", "t_stat", "t_stat_upper", "t_stat_lower"],
                "beta": ["beta"],
                "kumulatif_epsilon": ["cum_epsilon"],
            },
            last_state=last_state,
        )
