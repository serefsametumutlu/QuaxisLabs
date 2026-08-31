"""Tarama motoru: evren × zaman dilimi × indikatör, hata izole, paralel.

Worker fonksiyonları (`_run_single_worker`/`_run_pair_worker`) MODÜL
SEVİYESİNDE (top-level) tanımlıdır — `ProcessPoolExecutor` yalnızca
picklable çağrılabilirleri işçi sürece gönderebilir; bir closure/bound
method GÖNDERİLEMEZ. Aynı sebeple worker'lar `IndicatorResult`'ı ham
dataclass olarak değil, `to_json()` string'i olarak döndürür (pandas
Series/Timestamp pickling sürüm/ortam farklılıklarına karşı en sağlam yol).
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import UTC, datetime

import pandas as pd

from tlab.core.types import IndicatorResult, Market, Timeframe
from tlab.data.calendar import last_closed_session
from tlab.data.providers.yfinance_provider import YFinanceProvider
from tlab.data.store import Store
from tlab.data.universe import BENCHMARK_SYMBOL
from tlab.data.validate import DataQualityReport, check_data_quality
from tlab.scanner.results import DataQualityRecord, SymbolIndicatorRun


@dataclass(frozen=True)
class IndicatorRunResult:
    symbol: str
    market: str
    timeframe: str
    indicator: str
    params_hash: str
    result: IndicatorResult | None
    error: str | None
    duration_s: float

    def to_symbol_indicator_run(self) -> SymbolIndicatorRun:
        return SymbolIndicatorRun(
            symbol=self.symbol, market=self.market, timeframe=self.timeframe,
            indicator=self.indicator, params_hash=self.params_hash,
            result=self.result, error=self.error,
        )


@dataclass(frozen=True)
class ScanRun:
    run_id: str
    started_at: datetime
    finished_at: datetime
    market: str
    timeframes: list[str]
    universe_size: int
    indicator_names: list[str]
    results: list[IndicatorRunResult] = field(default_factory=list)
    data_quality: list[DataQualityRecord] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for r in self.results if r.error is not None)


def _fetch_and_prepare(
    symbol: str, market: Market, timeframe: Timeframe, lookback_bars: int, drop_open_bar: bool
) -> pd.DataFrame:
    store = Store(YFinanceProvider())
    df = store.get(symbol, timeframe, market, last_n=lookback_bars)
    if drop_open_bar and len(df) > 0 and timeframe is Timeframe.D1:
        closed_date = last_closed_session(datetime.now(UTC), market)
        if df.index[-1].date() > closed_date:
            df = df.iloc[:-1]
    return df


def _run_single_worker(
    symbol: str, market_value: str, timeframe_value: str, indicator_name: str,
    lookback_bars: int, drop_open_bar: bool,
) -> dict:
    from tlab.indicators.bootstrap import CATALOG  # process-local import

    t0 = time.perf_counter()
    market, timeframe = Market(market_value), Timeframe(timeframe_value)
    try:
        df = _fetch_and_prepare(symbol, market, timeframe, lookback_bars, drop_open_bar)
        indicator = CATALOG[indicator_name].factory()
        result = indicator(df)
        return {
            "symbol": symbol, "market": market_value, "timeframe": timeframe_value,
            "indicator": indicator_name, "params_hash": result.params_hash,
            "result_json": result.to_json(), "error": None,
            "duration_s": time.perf_counter() - t0,
        }
    except Exception as exc:  # noqa: BLE001 — hata izolasyonu: tek indikatör patlaması taramayı durdurmaz
        return {
            "symbol": symbol, "market": market_value, "timeframe": timeframe_value,
            "indicator": indicator_name, "params_hash": "", "result_json": None,
            "error": f"{type(exc).__name__}: {exc}", "duration_s": time.perf_counter() - t0,
        }


def _run_pair_worker(
    y_symbol: str, x_symbol: str, market_value: str, timeframe_value: str, indicator_name: str,
    lookback_bars: int, drop_open_bar: bool,
) -> dict:
    from tlab.indicators.bootstrap import CATALOG

    t0 = time.perf_counter()
    market, timeframe = Market(market_value), Timeframe(timeframe_value)
    symbol_label = f"{y_symbol}/{x_symbol}"
    try:
        df_y = _fetch_and_prepare(y_symbol, market, timeframe, lookback_bars, drop_open_bar)
        df_x = _fetch_and_prepare(x_symbol, market, timeframe, lookback_bars, drop_open_bar)
        indicator = CATALOG[indicator_name].factory()
        result = indicator(df_y, context={"x": df_x})
        return {
            "symbol": symbol_label, "market": market_value, "timeframe": timeframe_value,
            "indicator": indicator_name, "params_hash": result.params_hash,
            "result_json": result.to_json(), "error": None,
            "duration_s": time.perf_counter() - t0,
        }
    except Exception as exc:  # noqa: BLE001 — bkz. _run_single_worker
        return {
            "symbol": symbol_label, "market": market_value, "timeframe": timeframe_value,
            "indicator": indicator_name, "params_hash": "", "result_json": None,
            "error": f"{type(exc).__name__}: {exc}", "duration_s": time.perf_counter() - t0,
        }


def _run_universe_worker(
    indicator_name: str, market_value: str, timeframe_value: str, universe_symbols: list[str],
    lookback_bars: int, drop_open_bar: bool,
) -> dict:
    """Faz 8D "universe" kategorisi (`needs_universe=True`) için TEK bir iş:
    tüm evren + endeks çekilir, indikatör BİR KEZ çağrılır (`{symbol:
    IndicatorResult}` döner). Sembol başına başarısız veri çekimi TÜM işi
    durdurmaz (`symbol_errors`'a düşer); indikatörün KENDİSİ de yetersiz
    geçmişi olan sembolleri sessizce atlayabilir (bkz. `UniverseIndicator`
    docstring'i — dönen sözlük `universe`'in ALT KÜMESİ olabilir), bu da
    `symbol_errors`'a DÜŞMEZ (hata değil, tasarım gereği filtre)."""
    from tlab.indicators.bootstrap import CATALOG

    t0 = time.perf_counter()
    market, timeframe = Market(market_value), Timeframe(timeframe_value)
    out: dict = {
        "indicator": indicator_name, "market": market_value, "timeframe": timeframe_value,
        "symbol_results": {}, "symbol_errors": {}, "error": None, "duration_s": 0.0,
    }
    try:
        universe_dfs: dict[str, pd.DataFrame] = {}
        for symbol in universe_symbols:
            try:
                universe_dfs[symbol] = _fetch_and_prepare(
                    symbol, market, timeframe, lookback_bars, drop_open_bar
                )
            except Exception as exc:  # noqa: BLE001 — tek sembol veri hatası taramayı durdurmamalı
                out["symbol_errors"][symbol] = f"{type(exc).__name__}: {exc}"

        benchmark_symbol = BENCHMARK_SYMBOL[market]
        index_df = _fetch_and_prepare(
            benchmark_symbol, market, timeframe, lookback_bars, drop_open_bar
        )
        indicator = CATALOG[indicator_name].factory()
        results = indicator(universe_dfs, index_df)
        out["symbol_results"] = {sym: r.to_json() for sym, r in results.items()}
    except Exception as exc:  # noqa: BLE001 — bkz. _run_single_worker
        out["error"] = f"{type(exc).__name__}: {exc}"
    out["duration_s"] = time.perf_counter() - t0
    return out


def _universe_result_to_runs(raw: dict) -> list[IndicatorRunResult]:
    """`_run_universe_worker`'ın TEK sözlük çıktısını, motorun geri
    kalanının (ResultsStore/diff/dashboard) beklediği düz `IndicatorRunResult`
    listesine açar — bu satırdan SONRASI universe/tekil ayrımını bilmez."""
    if raw["error"] is not None:
        # İndikatör/endeks düzeyinde genel bir hata — hangi sembole ait
        # olduğu bilinmiyor, tek bir "evren" satırı olarak kaydedilir.
        return [
            IndicatorRunResult(
                symbol=f"__universe__:{raw['indicator']}", market=raw["market"],
                timeframe=raw["timeframe"], indicator=raw["indicator"], params_hash="",
                result=None, error=raw["error"], duration_s=raw["duration_s"],
            )
        ]
    runs = []
    for symbol, result_json in raw["symbol_results"].items():
        result = IndicatorResult.from_json(result_json)
        runs.append(
            IndicatorRunResult(
                symbol=symbol, market=raw["market"], timeframe=raw["timeframe"],
                indicator=raw["indicator"], params_hash=result.params_hash,
                result=result, error=None,
                duration_s=raw["duration_s"] / max(1, len(raw["symbol_results"])),
            )
        )
    runs += [
        IndicatorRunResult(
            symbol=symbol, market=raw["market"], timeframe=raw["timeframe"],
            indicator=raw["indicator"], params_hash="", result=None, error=error, duration_s=0.0,
        )
        for symbol, error in raw["symbol_errors"].items()
    ]
    return runs


def _to_indicator_run_result(raw: dict) -> IndicatorRunResult:
    result = (
        IndicatorResult.from_json(raw["result_json"]) if raw["result_json"] is not None else None
    )
    return IndicatorRunResult(
        symbol=raw["symbol"], market=raw["market"], timeframe=raw["timeframe"],
        indicator=raw["indicator"], params_hash=raw["params_hash"], result=result,
        error=raw["error"], duration_s=raw["duration_s"],
    )


def _check_data_quality_for(
    symbols: list[str], market: Market, timeframes: list[Timeframe]
) -> list[DataQualityRecord]:
    store = Store(YFinanceProvider())
    records: list[DataQualityRecord] = []
    for symbol in symbols:
        for tf in timeframes:
            try:
                df = store.get(symbol, tf, market)
            except FileNotFoundError as exc:
                report = DataQualityReport(symbol=symbol, timeframe=tf, errors=[str(exc)])
            else:
                report = check_data_quality(df, symbol, market, tf)
            records.append(
                DataQualityRecord(
                    symbol=symbol, timeframe=tf.value, status="ok" if report.ok else "error",
                    report={"warnings": report.warnings, "errors": report.errors},
                )
            )
    return records


def run(
    run_id: str,
    universe: list[str],
    timeframes: list[Timeframe],
    indicator_names: list[str],
    market: Market,
    lookback_bars: int = 600,
    workers: int | None = None,
    drop_open_bar: bool = True,
    pairs: list[tuple[str, str]] | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> ScanRun:
    """`indicator_names` "pair" kategorisindeyse `pairs` listesi (Y,X)
    çiftleri üzerinde çalışır (`universe` YOK SAYILIR bu indikatörler için);
    "universe" kategorisindeyse (`needs_universe=True`, Faz 8D) her zaman
    dilimi için TEK bir iş olarak (evrenin TAMAMI + endeks) çalışır; diğerleri
    `universe`'in her sembolü için ayrı ayrı çalışır."""
    from tlab.indicators.bootstrap import CATALOG, populate_registry

    populate_registry()
    started_at = datetime.now(UTC)
    jobs_single: list[tuple] = []
    jobs_pair: list[tuple] = []
    jobs_universe: list[tuple] = []

    for name in indicator_names:
        spec = CATALOG.get(name)
        if spec is None:
            continue
        for tf in timeframes:
            if spec.needs_context:
                for y_sym, x_sym in pairs or []:
                    jobs_pair.append(
                        (y_sym, x_sym, market.value, tf.value, name, lookback_bars, drop_open_bar)
                    )
            elif spec.needs_universe:
                jobs_universe.append(
                    (name, market.value, tf.value, universe, lookback_bars, drop_open_bar)
                )
            else:
                for symbol in universe:
                    jobs_single.append(
                        (symbol, market.value, tf.value, name, lookback_bars, drop_open_bar)
                    )

    max_workers = workers if workers is not None else max(1, (os.cpu_count() or 2) - 1)
    total_jobs = len(jobs_single) + len(jobs_pair) + len(jobs_universe)
    raw_results: list[dict] = []
    raw_universe_results: list[dict] = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_run_single_worker, *job) for job in jobs_single]
        futures += [executor.submit(_run_pair_worker, *job) for job in jobs_pair]
        universe_futures = [executor.submit(_run_universe_worker, *job) for job in jobs_universe]
        for done, future in enumerate(as_completed(futures), start=1):
            raw_results.append(future.result())
            if progress is not None:
                progress(done, total_jobs)
        for done, future in enumerate(as_completed(universe_futures), start=len(futures) + 1):
            raw_universe_results.append(future.result())
            if progress is not None:
                progress(done, total_jobs)

    results = [_to_indicator_run_result(r) for r in raw_results]
    for raw_universe in raw_universe_results:
        results += _universe_result_to_runs(raw_universe)

    dq_symbols = sorted(set(universe) | {s for pair in (pairs or []) for s in pair})
    data_quality = (
        _check_data_quality_for(dq_symbols, market, timeframes) if dq_symbols else []
    )

    return ScanRun(
        run_id=run_id, started_at=started_at, finished_at=datetime.now(UTC),
        market=market.value, timeframes=[tf.value for tf in timeframes],
        universe_size=len(universe), indicator_names=indicator_names,
        results=results, data_quality=data_quality,
    )
