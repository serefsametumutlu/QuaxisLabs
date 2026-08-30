"""tlab komut satırı arayüzü."""

from __future__ import annotations

import importlib
import json
from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd
import typer
import yaml

from tlab.core.types import Market, Timeframe
from tlab.data.providers.yfinance_provider import YFinanceProvider
from tlab.data.settings import load_settings
from tlab.data.store import Store
from tlab.data.universe import load_universe
from tlab.data.validate import check_data_quality
from tlab.indicators.bootstrap import CATALOG
from tlab.indicators.pairs.relative_momentum import RelativeMomentumPair, RelativeMomentumParams
from tlab.scanner import engine
from tlab.scanner.eod import run_eod
from tlab.scanner.results import ResultsStore
from tlab.testing.lint_lookahead import has_errors, lint_paths
from tlab.testing.repaint import repaint_test
from tlab.viz.live import render_live
from tlab.viz.report import build_report_html

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


@app.command("pair")
def pair_cmd(
    y: str = typer.Option(..., "--y", help="Y hissesi (ör. TCELL)"),
    x: str = typer.Option(..., "--x", help="X hissesi (ör. ISCTR)"),
    market: str = typer.Option("bist", "--market", help="bist | nasdaq"),
    tf: str = typer.Option("1d", "--tf", help="1h | 4h | 1d"),
    window: int = typer.Option(90, "--window"),
    k: float = typer.Option(2.0, "--k"),
) -> None:
    """RelativeMomentumPair'i Y<->X üzerinde çalıştırır; last_state ve metrik
    tablosunu konsola yazar, IndicatorResult JSON'unu outputs/'a kaydeder."""
    mkt = Market(market.lower())
    tf_map = {"1h": Timeframe.H1, "4h": Timeframe.H4, "1d": Timeframe.D1}
    timeframe = tf_map.get(tf.lower())
    if timeframe is None:
        typer.echo(f"Geçersiz --tf: {tf} (1h|4h|1d bekleniyor)", err=True)
        raise typer.Exit(code=2)

    store = Store(YFinanceProvider())
    try:
        df_y = store.get(y, timeframe, mkt)
        df_x = store.get(x, timeframe, mkt)
    except FileNotFoundError as exc:
        typer.echo(f"Veri bulunamadı: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    params = RelativeMomentumParams(window=window, k=k, y_symbol=y, x_symbol=x)
    result = RelativeMomentumPair(params)(df_y, context={"x": df_x})
    ls = result.last_state

    typer.echo(f"LONG-ONLY ROLATIF GECIS | {y} <-> {x} | {tf.upper()}")
    typer.echo(f"Sinyal: {ls['signal_today'] or '---'} | Tutulan: {ls['holding'] or 'yok'}")
    typer.echo("-" * 58)
    typer.echo(f"{'METRIK':<28} {'DEGER':>20}")
    typer.echo(f"{'Baslangic Sermayesi (TL)':<28} {params.start_capital:>20,.2f}")
    typer.echo(f"{'Guncel Portfoy (TL)':<28} {ls['portfolio_value']:>20,.2f}")
    typer.echo(f"{'Net Kar/Zarar (TL)':<28} {ls['net_pnl']:>20,.2f}")
    typer.echo(f"{'Getiri Orani (%)':<28} {ls['return_pct']:>20.2f}")
    typer.echo(f"{'Gecis (Trade) Sayisi':<28} {ls['n_trades']:>20}")
    if ls["z_today"] is not None:
        typer.echo(f"{'Son Gun Z-Skoru':<28} {ls['z_today']:>20.3f}")
    z_yesterday = ls["z_yesterday"]
    if z_yesterday is not None:
        typer.echo(f"{'Onceki Gun Z-Skoru':<28} {z_yesterday:>20.3f}")
    typer.echo(f"{'Max Drawdown (%)':<28} {ls['max_drawdown_pct']:>20.2f}")
    typer.echo(f"{'Kazanan Gecis Orani (%)':<28} {ls['win_rate_pct']:>20.2f}")

    out_dir = Path("outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"pair_{y}_{x}_{tf}.json"
    out_path.write_text(result.to_json(), encoding="utf-8")
    typer.echo(f"\nJSON: {out_path}")


def _load_pairs_yaml(path: str = "config/pairs.yaml") -> list[tuple[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return [(entry["y"], entry["x"]) for entry in raw.get("pairs", [])]


@app.command("list-indicators")
def list_indicators_cmd() -> None:
    """Katalogdaki tüm indikatörleri (isim, kategori, context gerekir mi) listeler."""
    for name, spec in sorted(CATALOG.items()):
        ctx = " (context gerekir)" if spec.needs_context else ""
        typer.echo(f"{name:<28} [{spec.category}]{ctx}")


def _load_scan_preset(name: str, path: str = "config/scans.yaml") -> tuple[list[str], dict]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    preset = (raw.get("presets") or {}).get(name)
    if preset is None:
        raise ValueError(f"'{name}' preset'i {path} içinde bulunamadı")
    return list(preset.get("indicators", [])), dict(preset.get("filter", {}))


def _signal_passes_filter(signal, filt: dict) -> bool:
    """`config/scans.yaml`'daki bir preset'in `filter` bloğunu uygular.

    `break_types` (yalnızca `trend.breakouts` için `payload["break_type"]`)
    tarihsel/özel bir alandır; `events`/`zone_kind` GENEL bir mekanizmadır —
    `payload["event"]`/`payload["zone_kind"]` değeri verilen listede mi diye
    bakar, herhangi bir indikatörle çalışır. `fresh` verilirse
    `payload["fresh"]` tam eşleşmeli (bkz. `structure.supply_demand`'ın
    `sd_new` sinyali — yeni doğan bir bölge her zaman fresh=True taşır)."""
    break_types = filt.get("break_types")
    if break_types and signal.payload.get("break_type") not in break_types:
        return False
    events = filt.get("events")
    if events and signal.payload.get("event") not in events:
        return False
    zone_kind = filt.get("zone_kind")
    if zone_kind and signal.payload.get("zone_kind") not in zone_kind:
        return False
    if "fresh" in filt and signal.payload.get("fresh") != filt["fresh"]:
        return False
    return True


@app.command("scan")
def scan_cmd(
    market: str = typer.Option(..., "--market", help="bist | nasdaq"),
    tf: str = typer.Option("4h,1d", "--tf", help="Virgülle ayrılmış: 4h,1d"),
    indicators: str = typer.Option("all", "--indicators", help="'all' veya virgülle liste"),
    preset: str = typer.Option(
        None, "--preset",
        help="config/scans.yaml'daki bir preset adı (--indicators'ı geçersiz kılar)",
    ),
    symbols: str = typer.Option(None, "--symbols", help="Virgülle ayrılmış (boşsa tam evren)"),
    workers: int = typer.Option(None, "--workers"),
) -> None:
    """Tek seferlik tarama — Registry.register() koşulmaz, sonuç konsola +
    outputs/scan_{market}.json'a yazılır (kalıcı DB için `tlab eod` kullanın).
    `--preset` verilirse indikatör listesi VE sonuç filtresi (ör. yalnızca
    belirli break_type'lar) config/scans.yaml'dan okunur."""
    mkt = Market(market.lower())
    tf_map = {"1h": Timeframe.H1, "4h": Timeframe.H4, "1d": Timeframe.D1, "w1": Timeframe.W1}
    tf_list = [tf_map[t.strip().lower()] for t in tf.split(",") if t.strip()]

    signal_filter: dict = {}
    if preset:
        indicator_names, signal_filter = _load_scan_preset(preset)
    else:
        indicator_names = list(CATALOG.keys()) if indicators == "all" else [
            s.strip() for s in indicators.split(",") if s.strip()
        ]
    universe = (
        [s.strip() for s in symbols.split(",") if s.strip()] if symbols else load_universe(mkt)
    )
    pairs = _load_pairs_yaml()

    scan = engine.run(
        run_id=f"scan_{datetime.now(UTC).isoformat()}", universe=universe, timeframes=tf_list,
        indicator_names=indicator_names, market=mkt, workers=workers, pairs=pairs,
        progress=lambda done, total: typer.echo(f"  {done}/{total}"),
    )
    typer.echo(f"Tamamlandı: {len(scan.results)} sonuç, {scan.error_count} hata")
    for r in scan.results:
        if r.error is not None:
            typer.echo(f"  HATA {r.symbol} {r.timeframe} {r.indicator}: {r.error}", err=True)

    out_path = Path("outputs") / f"scan_{mkt.value}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = []
    for r in scan.results:
        n_signals = 0
        if r.result is not None:
            n_signals = sum(1 for s in r.result.signals if _signal_passes_filter(s, signal_filter))
        payload.append(
            {
                "symbol": r.symbol, "timeframe": r.timeframe, "indicator": r.indicator,
                "error": r.error, "n_signals": n_signals,
            }
        )
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(f"Özet: {out_path}")


@app.command("eod")
def eod_cmd(
    market: str = typer.Option(..., "--market", help="bist | nasdaq"),
    eod_date: str = typer.Option(None, "--date", help="ISO tarih (varsayılan: son kapanmış seans)"),
    force: bool = typer.Option(False, "--force", help="Aynı gün için var olan run'ı yeniden koş"),
) -> None:
    """Gün sonu akışını çalıştırır: veri güncelleme → tarama → kayıt → diff → rapor."""
    date_ = date.fromisoformat(eod_date) if eod_date else None
    pairs = _load_pairs_yaml()
    report = run_eod(market=market, date_=date_, force=force, pairs=pairs)
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2))


@app.command("signals")
def signals_cmd(
    run: str = typer.Option("latest", "--run", help="run_id veya 'latest'"),
    market: str = typer.Option("bist", "--market", help="'latest' ile birlikte kullanılır"),
    state: str = typer.Option(None, "--state"),
    indicator: str = typer.Option(None, "--indicator", help="Tam ad veya 'harmonic.*' öneki"),
    tf: str = typer.Option(None, "--tf"),
) -> None:
    """Kayıtlı sinyalleri tablo halinde listeler."""
    store = ResultsStore()
    run_id = store.latest_run(market) if run == "latest" else run
    if run_id is None:
        typer.echo(f"{market} için tamamlanmış bir run yok.", err=True)
        raise typer.Exit(code=1)

    rows = store.query(run_id=run_id, state=state, timeframe=tf)
    if indicator:
        prefix = indicator.rstrip("*")
        rows = [r for r in rows if r["indicator"].startswith(prefix)]

    typer.echo(f"run_id={run_id} ({len(rows)} sinyal)")
    typer.echo(
        f"{'symbol':<12} {'tf':<4} {'indicator':<26} {'state':<12} {'bar_time':<26} {'dir':<6}"
    )
    for r in rows:
        typer.echo(
            f"{r['symbol']:<12} {r['timeframe']:<4} {r['indicator']:<26} "
            f"{r['state']:<12} {r['bar_time']:<26} {r['direction']:<6}"
        )
    store.close()


@app.command("diff")
def diff_cmd(
    a: str = typer.Option(..., "--a", help="Önceki run_id"),
    b: str = typer.Option(..., "--b", help="Sonraki run_id"),
) -> None:
    """İki run arasındaki farkı (yeni sinyal / durum geçişi / kaybolan sinyal) yazdırır."""
    store = ResultsStore()
    d = store.diff(a, b)
    typer.echo(f"Yeni sinyaller: {len(d.new_signals)}")
    for r in d.new_signals:
        typer.echo(
            f"  + {r['symbol']} {r['timeframe']} {r['indicator']} {r['state']} {r['bar_time']}"
        )
    typer.echo(f"Durum geçişleri: {len(d.transitions)}")
    for r in d.transitions:
        typer.echo(
            f"  ~ {r['symbol']} {r['timeframe']} {r['indicator']} "
            f"{r['from_states']} -> {r['state']} ({r['bar_time']})"
        )
    if d.has_repaint_alarm:
        typer.echo(f"\n⚠ REPAINT ALARMI: {len(d.missing_signals)} sinyal kayboldu:", err=True)
        for r in d.missing_signals:
            typer.echo(
                f"  - {r['symbol']} {r['timeframe']} {r['indicator']} "
                f"{r['state']} {r['bar_time']}",
                err=True,
            )
    store.close()


@app.command("plot")
def plot_cmd(
    symbol: str = typer.Option(
        ..., "--symbol", help="Sembol; pair indikatörler için 'Y/X' (ör. TCELL/ISCTR)"
    ),
    tf: str = typer.Option("1d", "--tf", help="1h | 4h | 1d | w1"),
    indicator: str = typer.Option(
        ..., "--indicator",
        help=(
            "Katalogdaki ad (ör. structure.price_structure) veya 'structure.report' "
            "— price_structure+swing_fib_abcd'i tek bir 'aracı kurum raporu' "
            "grafiğinde birleştiren, Özet Raporu panelli özel görünüm"
        ),
    ),
    market: str = typer.Option("bist", "--market", help="bist | nasdaq"),
    theme: str = typer.Option("auto", "--theme", help="auto | dark | light"),
    last_n: int = typer.Option(
        None, "--last-n",
        help="Yalnızca son N barı göster (0=tüm geçmiş; boş=otomatik: "
             "harmonikte en güncel adaya yakınlaştırır, diğerlerinde son 250 bar)",
    ),
    show_all: bool = typer.Option(
        False, "--show-all",
        help="Eski/çözülmüş aday ve seviyeleri de tam etiketle (varsayılan: yalnızca en güncel)",
    ),
    out: str = typer.Option(
        None, "--out", help="Çıktı yolu (.html veya .png); varsayılan outputs/samples/"
    ),
    open_: bool = typer.Option(False, "--open", help="Üretilen HTML'i tarayıcıda aç"),
) -> None:
    """Tek bir (sembol, tf, indikatör) grafiğini üretir (outputs/samples/'a
    HTML olarak kaydeder; --out ile .png verilirse kaleido kullanılır).
    Varsayılan olarak yalnızca en güncel aday/seviye tam etiketlenir (eskiler
    şekil olarak kalır) — `--show-all` ile eski davranışa dönülebilir."""
    try:
        fig = render_live(
            indicator, symbol, tf, market, theme=theme,
            last_n=last_n, declutter=not show_all,
        )
    except (ValueError, FileNotFoundError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    safe_symbol = symbol.replace("/", "-")
    out_path = (
        Path(out) if out else Path("outputs") / "samples" / f"{safe_symbol}_{tf}_{indicator}.html"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.suffix == ".png":
        fig.write_image(str(out_path), scale=2)
    else:
        fig.write_html(str(out_path), include_plotlyjs="cdn")
    typer.echo(f"Grafik: {out_path}")
    if open_:
        import webbrowser

        webbrowser.open(out_path.resolve().as_uri())


@app.command("report")
def report_cmd(
    run: str = typer.Option("latest", "--run", help="run_id veya 'latest'"),
    market: str = typer.Option("bist", "--market", help="'latest' ile birlikte kullanılır"),
    generate_charts: bool = typer.Option(
        False, "--generate-charts",
        help="Her sinyal için tekil grafiği ÖNCEDEN üret (yavaş olabilir)",
    ),
    out: str = typer.Option(None, "--out"),
) -> None:
    """EOD run'ı için HTML özet raporu üretir."""
    store = ResultsStore()
    run_id = store.latest_run(market) if run == "latest" else run
    if run_id is None:
        typer.echo(f"{market} için tamamlanmış bir run yok.", err=True)
        raise typer.Exit(code=1)

    content = build_report_html(store, run_id, generate_charts=generate_charts)
    out_path = Path(out) if out else Path("outputs") / "reports" / f"eod_report_{run_id}.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    typer.echo(f"Rapor: {out_path}")
    store.close()


if __name__ == "__main__":
    app()
