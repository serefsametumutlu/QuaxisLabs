"""tlab komut satırı arayüzü."""

from __future__ import annotations

import importlib
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import typer

from tlab.core.types import Market, Timeframe
from tlab.data.providers.yfinance_provider import YFinanceProvider
from tlab.data.settings import load_settings
from tlab.data.store import Store
from tlab.data.universe import load_universe
from tlab.data.validate import check_data_quality
from tlab.testing.lint_lookahead import has_errors, lint_paths
from tlab.testing.repaint import repaint_test

app = typer.Typer(add_completion=False, help="Teknik Lab (tlab) komut satırı arayüzü")

_TF_ARG_MAP = {"1h": Timeframe.H1, "1d": Timeframe.D1, "4h": Timeframe.H4}


@app.command("repaint-test")
def repaint_test_cmd(
    target: str = typer.Argument(
        ..., help="modul:SinifAdi biçiminde indikatör, örn. tlab.indicators.foo:FooIndicator"
    ),
    data: Path = typer.Option(..., "--data", help="Test için kullanılacak OHLCV parquet/csv dosyası"),
) -> None:
    """Verilen indikatör için walk-forward repaint testini çalıştırır."""
    module_name, _, class_name = target.partition(":")
    if not class_name:
        typer.echo("Hedef 'modul:SinifAdi' biçiminde olmalı", err=True)
        raise typer.Exit(code=2)

    module = importlib.import_module(module_name)
    indicator_cls = getattr(module, class_name)

    df = (
        pd.read_parquet(data)
        if data.suffix == ".parquet"
        else pd.read_csv(data, index_col=0, parse_dates=True)
    )

    report = repaint_test(indicator_cls(), df)
    if report.passed:
        typer.echo(f"PASS — {report.stats}")
    else:
        typer.echo(f"FAIL — {len(report.mismatches)} uyuşmazlık:", err=True)
        for m in report.mismatches:
            typer.echo(f"  - {m}", err=True)
        raise typer.Exit(code=1)


@app.command("lint")
def lint_cmd(
    root: Path = typer.Option(Path("."), "--root", help="Depo kökü (tlab/features, tlab/indicators aranır)"),
) -> None:
    """tlab/features ve tlab/indicators altında statik lookahead denetimi yapar."""
    issues = lint_paths(root)
    for issue in issues:
        typer.echo(str(issue))
    if has_errors(issues):
        raise typer.Exit(code=1)
    typer.echo(f"{len(issues)} bulgu (0 hata).")


@app.command("update-data")
def update_data_cmd(
    market: str = typer.Option(..., "--market", help="bist | nasdaq"),
    tf: str = typer.Option("1h,1d", "--tf", help="Virgülle ayrılmış: 1h,1d"),
    symbols: str = typer.Option(None, "--symbols", help="Virgülle ayrılmış sembol listesi"),
    all_: bool = typer.Option(
        False, "--all", help="config/universe_{market}.txt içindeki tüm semboller"
    ),
    start: str = typer.Option("2020-01-01", "--start", help="ISO tarih, ör. 2020-01-01"),
) -> None:
    """1H/1D OHLCV verisini artımlı çeker; 4H otomatik olarak 1H'den türetilir."""
    mkt = Market(market.lower())
    timeframes = tuple(
        _TF_ARG_MAP[t.strip().lower()] for t in tf.split(",") if t.strip().lower() != "4h"
    )

    if all_:
        symbol_list = load_universe(mkt)
    elif symbols:
        symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    else:
        typer.echo("--symbols veya --all belirtilmeli", err=True)
        raise typer.Exit(code=2)

    settings = load_settings()
    provider = YFinanceProvider(settings)
    store = Store(provider, settings=settings)
    start_dt = datetime.fromisoformat(start).replace(tzinfo=UTC)
    now = datetime.now(UTC)

    failures: list[str] = []
    for i, symbol in enumerate(symbol_list, 1):
        typer.echo(f"[{i}/{len(symbol_list)}] {symbol} ...")
        try:
            store.update(symbol, mkt, start_dt, now, timeframes=timeframes)
        except Exception as exc:  # noqa: BLE001 — tek sembol hatası tüm koşuyu durdurmamalı
            typer.echo(f"  HATA: {exc}", err=True)
            failures.append(symbol)

    typer.echo(f"Tamamlandı: {len(symbol_list) - len(failures)}/{len(symbol_list)} başarılı")
    if failures:
        typer.echo(f"Başarısız semboller: {failures}", err=True)
        raise typer.Exit(code=1)


@app.command("data-quality")
def data_quality_cmd(
    market: str = typer.Option(..., "--market", help="bist | nasdaq"),
    symbols: str = typer.Option(None, "--symbols", help="Virgülle ayrılmış sembol listesi"),
    all_: bool = typer.Option(
        False, "--all", help="config/universe_{market}.txt içindeki tüm semboller"
    ),
) -> None:
    """Cache'teki OHLCV verisinin veri kalitesi raporunu üretir."""
    mkt = Market(market.lower())
    symbol_list = (
        load_universe(mkt) if all_ else [s.strip() for s in (symbols or "").split(",") if s.strip()]
    )
    if not symbol_list:
        typer.echo("--symbols veya --all belirtilmeli", err=True)
        raise typer.Exit(code=2)

    store = Store(YFinanceProvider())
    any_errors = False
    for symbol in symbol_list:
        for tf in (Timeframe.H1, Timeframe.H4, Timeframe.D1):
            try:
                df = store.get(symbol, tf, mkt)
            except FileNotFoundError as exc:
                typer.echo(f"{symbol} ({tf.value}): {exc}", err=True)
                any_errors = True
                continue
            report = check_data_quality(df, symbol, mkt, tf)
            for w in report.warnings:
                typer.echo(f"{symbol} ({tf.value}) UYARI: {w}")
            for e in report.errors:
                typer.echo(f"{symbol} ({tf.value}) HATA: {e}", err=True)
            any_errors = any_errors or not report.ok

    if any_errors:
        raise typer.Exit(code=1)
    typer.echo("data-quality: hata yok.")


if __name__ == "__main__":
    app()
