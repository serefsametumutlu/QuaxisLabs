"""Faz 8D "universe" görselleri — TEKİL sembol grafiklerinden (renderer.py)
FARKLI bir şekil: bunlar bir mum grafiğini DEĞİL, `compute_universe()`'in
döndürdüğü {sembol: IndicatorResult} sözlüğünün TAMAMINI (bir bardaki
anlık görüntüsünü) çizer. `renderer.py`'nin "primitifleri çiz, hesap yapma"
ilkesi burada da geçerli — bu modül yalnızca ZATEN `last_state`'te/
`momentum_heatmap_data()`'da hazır olan sayıları Plotly şekline çevirir."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from tlab.core.types import IndicatorResult
from tlab.viz.themes import LIGHT_ANALYSIS, Theme, resolve_theme


def render_alpha_scatter(
    results: dict[str, IndicatorResult], *,
    theme: Theme | str | None = "auto", top_pct: float = 10.0,
) -> go.Figure:
    """AlphaRank evreninin ANLIK (en güncel bar) α-β saçılımı — x=β, y=α_yıllık,
    renk=rank_pct (`top_pct` içindekiler `accent` ile vurgulanır), metin=sembol."""
    th = resolve_theme(theme, default=LIGHT_ANALYSIS)
    rest: dict[str, list] = {"x": [], "y": [], "text": []}
    top: dict[str, list] = {"x": [], "y": [], "text": []}
    for symbol, result in results.items():
        ls = result.last_state
        primary = ls.get("windows", {}).get(str(ls.get("primary_window")), {})
        beta, alpha_ann = primary.get("beta"), primary.get("alpha_ann")
        rank_pct = ls.get("rank_pct")
        if beta is None or alpha_ann is None or rank_pct is None:
            continue
        bucket = top if rank_pct <= top_pct else rest
        bucket["x"].append(beta)
        bucket["y"].append(alpha_ann * 100.0)
        bucket["text"].append(symbol)

    fig = go.Figure()
    # Evrenin geri kalanı: nokta bulutu, ETİKETSİZ (yüzlerce sembolün metni
    # üst üste binip okunmaz hâle geliyordu — TASARIM KARARI: yalnızca
    # `top_pct` içindeki semboller etiketlenir, hover'da tam bilgi kalır).
    fig.add_trace(
        go.Scatter(
            x=rest["x"], y=rest["y"], mode="markers", text=rest["text"],
            marker={"color": th.muted, "size": 8, "line": {"color": th.border, "width": 1}},
            hovertemplate="%{text}<br>β=%{x:.2f}<br>α_yıllık=%{y:.1f}%<extra></extra>",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=top["x"], y=top["y"], mode="markers+text", text=top["text"],
            textposition="top center", textfont={"size": 10, "color": th.text},
            marker={"color": th.accent, "size": 14, "line": {"color": th.border, "width": 1}},
            hovertemplate="%{text}<br>β=%{x:.2f}<br>α_yıllık=%{y:.1f}%<extra></extra>",
            showlegend=False,
        )
    )
    fig.add_hline(y=0.0, line_color=th.gray, line_width=1, line_dash="dot")
    fig.add_vline(x=1.0, line_color=th.gray, line_width=1, line_dash="dot")
    fig.update_layout(
        title=f"Evren α-β Saçılımı (altın = ilk %{top_pct:g})",
        xaxis_title="β (endekse göre)", yaxis_title="Yıllık α (%)",
        paper_bgcolor=th.page_bg, plot_bgcolor=th.bg,
        font={"color": th.text, "family": th.font}, showlegend=False,
        xaxis={"gridcolor": th.grid}, yaxis={"gridcolor": th.grid},
    )
    return fig


def render_momentum_heatmap(
    heatmap_df: pd.DataFrame, *, theme: Theme | str | None = "auto",
) -> go.Figure:
    """`momentum_rank.py::momentum_heatmap_data()`'ın ürettiği sektör × ufuk
    matrisini ısı haritası olarak çizer (hücre = ham ortalama momentum, %)."""
    th = resolve_theme(theme, default=LIGHT_ANALYSIS)
    z = (heatmap_df.to_numpy() * 100.0)
    fig = go.Figure(
        go.Heatmap(
            z=z, x=list(heatmap_df.columns), y=list(heatmap_df.index),
            colorscale=[[0.0, th.red], [0.5, th.bg], [1.0, th.green]],
            zmid=0.0, colorbar={"title": "%"},
            text=[[f"{v:.1f}%" for v in row] for row in z],
            texttemplate="%{text}", hovertemplate="%{y} / %{x}: %{z:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(
        title="Sektör × Ufuk Momentum Isı Haritası",
        paper_bgcolor=th.page_bg, plot_bgcolor=th.bg,
        font={"color": th.text, "family": th.font},
    )
    return fig
