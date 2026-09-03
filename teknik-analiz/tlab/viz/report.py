"""EOD HTML raporu — özet (yeni sinyal/durum geçişi/repaint alarmı sayıları),
indikatör/tf sekmeleri, sinyal tablosu; her satır tekil grafiğe LİNK verir.

Rapor sayfasının KENDİSİ Plotly İÇERMEZ (yalnızca HTML/CSS/az miktarda vanilla
JS sekme geçişi) — tekil grafikler `ensure_chart()` ile AYRI dosyalarda,
LAZY (istendiğinde) üretilir ve `include_plotlyjs="cdn"` kullanır (her biri
~3MB'lık plotly.js'i tekrar tekrar gömmemek için — bkz. Faz 7 görev metni,
madde 4)."""

from __future__ import annotations

import html
from collections import defaultdict
from pathlib import Path
from typing import Any

from tlab.scanner.results import ResultsStore
from tlab.viz import labels_tr as tr
from tlab.viz.live import render_live

CHARTS_DIR_NAME = "charts"


def chart_relpath(run_id: str, symbol: str, timeframe: str, indicator: str) -> str:
    safe_symbol = symbol.replace("/", "-")
    return f"{CHARTS_DIR_NAME}/{run_id}/{safe_symbol}_{timeframe}_{indicator}.html"


def ensure_chart(
    run_id: str, market: str, symbol: str, timeframe: str, indicator: str,
) -> Path:
    """`outputs/{chart_relpath}` yoksa üretir (cache'teki veriyi okuyup
    indikatörü yeniden çalıştırarak — ResultsStore'daki JSON zaten `df`
    taşımadığı için render() için gerekli, bkz. `live.py`). Pair indikatörler
    `symbol` formatı "Y/X" bekler."""
    out_path = Path("outputs") / chart_relpath(run_id, symbol, timeframe, indicator)
    if out_path.exists():
        return out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig = render_live(indicator, symbol, timeframe, market, theme="auto")
    fig.write_html(str(out_path), include_plotlyjs="cdn")
    return out_path


def build_report_html(store: ResultsStore, run_id: str, *, generate_charts: bool = False) -> str:
    run = store.get_run(run_id)
    if run is None:
        raise ValueError(f"run bulunamadı: {run_id}")

    rows = store.query(run_id=run_id)
    prior_runs = [r for r in store.list_runs(run.market, status="completed") if r != run_id]
    diff = store.diff(prior_runs[0], run_id) if prior_runs else None

    if generate_charts:
        for r in rows:
            if r["state"] == "error":
                continue
            ensure_chart(run_id, run.market, r["symbol"], r["timeframe"], r["indicator"])

    by_indicator: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_indicator[r["indicator"]].append(r)

    summary_html = _build_summary(rows, diff)
    tabs_nav, tabs_body = _build_tabs(run_id, by_indicator)

    return f"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8">
<title>QuaxisLabs EOD Raporu — {html.escape(run.market)} — {html.escape(run_id)}</title>
<style>{_CSS}</style>
</head><body>
<h1>QuaxisLabs Gün Sonu (EOD) Raporu</h1>
<div class="meta">run_id: <code>{html.escape(run_id)}</code> | market: {html.escape(run.market)} |
başladı: {html.escape(run.started_at)} | bitti: {html.escape(run.finished_at or '---')} |
evren: {run.universe_size} sembol | git: {html.escape(run.git_sha or '---')}</div>
{summary_html}
<div class="tabs-nav">{tabs_nav}</div>
{tabs_body}
<script>{_JS}</script>
</body></html>"""


def _build_summary(rows: list[dict], diff: Any) -> str:
    n_by_state: dict[str, int] = defaultdict(int)
    for r in rows:
        n_by_state[r["state"]] += 1
    state_cells = "".join(
        f'<div class="stat"><span class="n">{n}</span><span class="l">{tr.tr_state(s)}</span></div>'
        for s, n in sorted(n_by_state.items())
    )
    diff_html = ""
    if diff is not None:
        n_missing = len(diff.missing_signals)
        alarm = (
            f'<div class="alarm">⚠ REPAINT ALARMI: {n_missing} sinyal kayboldu</div>'
            if diff.has_repaint_alarm else ""
        )
        n_new, n_trans = len(diff.new_signals), len(diff.transitions)
        diff_html = f"""
<div class="summary-row">
  <div class="stat"><span class="n">{n_new}</span><span class="l">Yeni Sinyal</span></div>
  <div class="stat"><span class="n">{n_trans}</span><span class="l">Durum Geçişi</span></div>
</div>
{alarm}"""
    return f'<div class="summary-row">{state_cells}</div>{diff_html}'


def _build_tabs(run_id: str, by_indicator: dict[str, list[dict]]) -> tuple[str, str]:
    nav_items, bodies = [], []
    for i, (indicator, rows) in enumerate(sorted(by_indicator.items())):
        tab_id = f"tab-{i}"
        active = " active" if i == 0 else ""
        nav_items.append(
            f'<button class="tab-btn{active}" onclick="showTab(\'{tab_id}\', event)">'
            f"{html.escape(indicator)} ({len(rows)})</button>"
        )
        table_rows = "".join(_signal_row(run_id, r) for r in rows)
        bodies.append(f"""
<div id="{tab_id}" class="tab-body{active}">
<table>
<thead><tr><th>Sembol</th><th>TF</th><th>Durum</th><th>Yön</th><th>Bar</th><th>Skor</th><th></th></tr></thead>
<tbody>{table_rows}</tbody>
</table>
</div>""")
    return "".join(nav_items), "".join(bodies)


def _signal_row(run_id: str, r: dict) -> str:
    href = chart_relpath(run_id, r["symbol"], r["timeframe"], r["indicator"])
    return (
        "<tr>"
        f"<td>{html.escape(r['symbol'])}</td><td>{html.escape(r['timeframe'])}</td>"
        f"<td class=\"state-{html.escape(r['state'])}\">{html.escape(tr.tr_state(r['state']))}</td>"
        f"<td>{html.escape(tr.tr_direction(r['direction']))}</td>"
        f"<td>{html.escape(r['bar_time'])}</td><td>{r['score']:.2f}</td>"
        f'<td><a href="{html.escape(href)}" target="_blank">grafik</a></td>'
        "</tr>"
    )


_CSS = """
body { background:#0b0e11; color:#d7dde3; font-family: Consolas, monospace; margin: 24px; }
h1 { color:#e0c72f; font-size: 18px; }
.meta { color:#8b98a5; font-size: 12px; margin-bottom: 16px; }
.summary-row { display:flex; gap: 16px; margin-bottom: 8px; flex-wrap: wrap; }
.stat {
  background:#141a20; border:1px solid #20262e; border-radius:6px;
  padding:10px 16px; text-align:center;
}
.stat .n { display:block; font-size:20px; color:#2ecc71; }
.stat .l { display:block; font-size:11px; color:#8b98a5; }
.alarm { color:#e74c3c; font-weight:bold; margin: 8px 0; }
.tabs-nav { margin-top: 16px; border-bottom: 1px solid #20262e; }
.tab-btn {
  background:none; border:none; color:#8b98a5; padding:8px 14px;
  cursor:pointer; font-family:inherit;
}
.tab-btn.active { color:#e0c72f; border-bottom: 2px solid #e0c72f; }
.tab-body { display:none; padding-top: 12px; }
.tab-body.active { display:block; }
table { border-collapse: collapse; width: 100%; font-size: 12px; }
th, td { border-bottom: 1px solid #20262e; padding: 6px 10px; text-align: left; }
th { color:#8b98a5; }
td a { color:#4c8ef7; }
.state-confirmed, .state-completed { color:#2ecc71; }
.state-invalidated, .state-expired, .state-error { color:#e74c3c; }
"""

_JS = """
function showTab(id, evt) {
  document.querySelectorAll('.tab-body').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  evt.target.classList.add('active');
}
"""
