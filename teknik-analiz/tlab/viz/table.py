"""Görsel 4 formatında metrik tablosu (Plotly `go.Table`). Hesap yapmaz —
yalnızca `last_state`/parametre değerlerini okuyup biçimlendirir."""

from __future__ import annotations

import plotly.graph_objects as go

from tlab.viz.themes import DARK_TERMINAL, Theme

Row = tuple[str, str, str]  # (metrik, değer, durum: "pos" | "neg" | "neutral")


def build_metrics_table(
    rows: list[Row], *, title: str = "", subtitle: str = "", theme: Theme = DARK_TERMINAL,
) -> go.Figure:
    row_fill_pos = _blend(theme.green, theme.bg, 0.22)
    row_fill_neg = _blend(theme.red, theme.bg, 0.22)
    row_fill_neutral = theme.bg
    fill_by_status = {"pos": row_fill_pos, "neg": row_fill_neg, "neutral": row_fill_neutral}
    font_by_status = {"pos": theme.green, "neg": theme.red, "neutral": theme.text}

    metrics = [r[0] for r in rows]
    values = [r[1] for r in rows]
    statuses = [r[2] for r in rows]
    row_colors = [fill_by_status.get(s, row_fill_neutral) for s in statuses]
    value_font_colors = [font_by_status.get(s, theme.text) for s in statuses]
    status_labels = [s.upper() if s != "neutral" else "---" for s in statuses]

    fig = go.Figure(
        data=[
            go.Table(
                columnwidth=[220, 160, 100],
                header=dict(
                    values=["METRİK", "DEĞER", "DURUM"],
                    fill_color=theme.bg,
                    font=dict(color=theme.text, size=12, family=theme.font),
                    align="center", height=30, line_color=theme.grid,
                ),
                cells=dict(
                    values=[metrics, values, status_labels],
                    fill_color=[row_colors, row_colors, row_colors],
                    font=dict(
                        color=[[theme.text] * len(rows), value_font_colors, value_font_colors],
                        size=11, family=theme.font,
                    ),
                    align=["left", "right", "center"], height=26, line_color=theme.grid,
                ),
            )
        ]
    )
    full_title = f"{title}<br><sub>{subtitle}</sub>" if subtitle else title
    fig.update_layout(
        title=dict(text=full_title, font=dict(color=theme.text, size=13, family=theme.font)),
        paper_bgcolor=theme.bg, plot_bgcolor=theme.bg,
        margin=dict(l=10, r=10, t=60 if subtitle else 40, b=10),
        height=60 + 26 * len(rows) + 60,
    )
    return fig


def pair_metrics_rows(last_state: dict, start_capital: float) -> list[Row]:
    net = last_state.get("net_pnl", 0.0)
    status = "pos" if net >= 0 else "neg"
    return [
        ("Baslangic Sermayesi (TL)", f"{start_capital:,.2f}", "neutral"),
        ("Guncel Portfoy (TL)", f"{last_state.get('portfolio_value', 0.0):,.2f}", status),
        ("Net Kar / Zarar (TL)", f"{net:,.2f}", status),
        ("Getiri Orani (%)", f"{last_state.get('return_pct', 0.0):+.2f}%", status),
        ("Gecis (Trade) Sayisi", str(last_state.get("n_trades", 0)), "neutral"),
        ("Son Gun Z-Skoru", _fmt_opt(last_state.get("z_today")), "neutral"),
        ("Onceki Gun Z-Skoru", _fmt_opt(last_state.get("z_yesterday")), "neutral"),
        ("Sinyal", last_state.get("signal_today") or "---", "neutral"),
    ]


def _fmt_opt(v: float | None) -> str:
    return f"{v:.2f}" if v is not None else "---"


def _blend(hex_a: str, hex_b: str, t: float) -> str:
    a, b = hex_a.lstrip("#"), hex_b.lstrip("#")
    ra, ga, ba = int(a[0:2], 16), int(a[2:4], 16), int(a[4:6], 16)
    rb, gb, bb = int(b[0:2], 16), int(b[2:4], 16), int(b[4:6], 16)
    r = round(ra * t + rb * (1 - t))
    g = round(ga * t + gb * (1 - t))
    bl = round(ba * t + bb * (1 - t))
    return f"rgb({r},{g},{bl})"
