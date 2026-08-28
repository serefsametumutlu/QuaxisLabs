"""Plotly renderer — IndicatorResult primitiflerini çizer, HESAP YAPMAZ.

Üç mod (indikatör adının önekine göre otomatik seçilir):
- `pair.*` — 3 satırlı özel düzen (Görsel 1): normalize fiyat + tutulan dönem
  gölgeleri, portföy vs buy&hold, Z-skoru + eşikler + geçiş etiketleri.
- `harmonic.*` — mum + XAB/BCD üçgenleri (Polygon) + X→B/X→D çizgileri +
  PRZ seviyeleri + D etiketi (Görsel 5/6).
- diğerleri (`structure.*` vb.) — jenerik: mum + Level/Line/Box/Polygon/
  Marker + `series_layout`'a göre alt paneller + `vp_*` varsa sağda yatay
  hacim profili paneli (Görsel 2/3).

Hangi primitifin nerede/nasıl göründüğü tamamen `IndicatorResult` içindeki
veriden gelir — bu modül yalnızca stil/renk/yerleşim kararı verir, hiçbir
teknik hesap (swing/fib/pivot/vb.) yapmaz. `last_n` yalnızca GÖRÜNÜR x-ekseni
aralığını kısıtlar (`fig.update_xaxes(range=...)`) — hiçbir seri/primitif
budanmaz, bu yüzden hangi seri tam geçmişi taşıyor hangisi kısmi olsun fark
etmeksizin hizalama sorunu oluşmaz."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from tlab.core.types import Box, IndicatorResult, Level, Line, Marker, Polygon
from tlab.viz import labels_tr as tr
from tlab.viz.themes import (
    DARK_TERMINAL,
    LIGHT_ANALYSIS,
    Theme,
    fib_color,
    fill_color,
    line_color,
    resolve_theme,
)


def render(
    result: IndicatorResult,
    df: pd.DataFrame | None = None,
    *,
    theme: Theme | str | None = "auto",
    last_n: int | None = None,
) -> go.Figure:
    """`result`ı çizer. `df`: fiyat serisi (pair modu HARİÇ zorunlu — mum
    grafiği ve harmonik/yapı primitiflerinin x eksenini belirler)."""
    if result.indicator.startswith("pair."):
        resolved = resolve_theme(theme, default=DARK_TERMINAL)
        return _render_pair(result, resolved, last_n)

    if df is None:
        raise ValueError(f"'{result.indicator}' için render() df gerektirir")
    resolved = resolve_theme(theme, default=LIGHT_ANALYSIS)
    return _render_price_based(result, df, resolved, last_n)


# ------------------------------------------------------------------ ortak --


def _apply_layout(fig: go.Figure, theme: Theme, title: str, height: int) -> None:
    fig.update_layout(
        title=dict(text=title, font=dict(color=theme.text, size=14, family=theme.font)),
        paper_bgcolor=theme.bg,
        plot_bgcolor=theme.bg,
        font=dict(color=theme.text, family=theme.font, size=11),
        height=height,
        margin=dict(l=50, r=50, t=60, b=30),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=theme.text, size=10)),
        xaxis_rangeslider_visible=False,
        bargap=0.15,
    )
    fig.update_xaxes(gridcolor=theme.grid, zerolinecolor=theme.grid, showspikes=False)
    fig.update_yaxes(gridcolor=theme.grid, zerolinecolor=theme.grid)


def _fmt_date(t: datetime) -> str:
    return pd.Timestamp(t).strftime("%d.%m.%Y")


def _xs(index: pd.Index) -> pd.Index:
    """`_x()`'in dizi hâli — trace x= değerleri için. Aynı orjson/kaleido
    sorunu (bkz. `_x()` docstring'i) tz-aware `pd.DatetimeIndex`'in
    `to_numpy()`'ında da çıkar (dtype=object, içi ham Timestamp) — bu yüzden
    HER trace'in x'i de (yalnızca shape/annotation değil) string'e çevrilir."""
    return index.astype(str)


def _x(t: object) -> str:
    """Shape/annotation x-değerleri için ISO8601 string'e çevirir.

    `fig.write_html` kullanılan Plotly'nin KENDİ JSON encoder'ı ham
    `pd.Timestamp`/`datetime` nesnelerini shape/annotation içinde sorunsuz
    işler, ama `fig.write_image` (kaleido, orjson tabanlı) İŞLEMEZ —
    `TypeError: Type is not JSON serializable: Timestamp` fırlatır. Trace
    verisi (go.Scatter/Bar x=...) Plotly'nin veri doğrulayıcısından geçtiği
    için bu sorunu yaşamaz; yalnızca `add_shape`/`add_annotation`/`add_vrect`
    çağrılarına verilen x/x0/x1 için gereklidir."""
    return pd.Timestamp(t).isoformat()


# ------------------------------------------------------------ jenerik mod --


def _render_price_based(
    result: IndicatorResult, df: pd.DataFrame, theme: Theme, last_n: int | None
) -> go.Figure:
    layout = result.series_layout or {}
    sub_names = list(layout.keys())
    has_vp = any(name.startswith("vp_") for name in result.series)
    n_sub = len(sub_names)
    n_rows = 1 + n_sub
    n_cols = 2 if has_vp else 1

    if n_sub:
        main_h = 0.5
        sub_h = (1.0 - main_h) / n_sub
        row_heights = [main_h] + [sub_h] * n_sub
    else:
        row_heights = [1.0]

    specs: list[list[dict[str, object] | None]] = []
    if n_cols == 2:
        specs.append([{}, {}])
        specs.extend([{"colspan": 2}, None] for _ in range(n_sub))
        column_widths = [0.82, 0.18]
    else:
        specs.extend([{}] for _ in range(n_rows))
        column_widths = None

    fig = make_subplots(
        rows=n_rows, cols=n_cols, shared_xaxes=True, vertical_spacing=0.04,
        row_heights=row_heights, column_widths=column_widths, specs=specs,
        horizontal_spacing=0.02,
    )

    fig.add_trace(
        go.Candlestick(
            x=_xs(df.index), open=df["open"], high=df["high"], low=df["low"], close=df["close"],
            increasing_line_color=theme.up, decreasing_line_color=theme.down,
            increasing_fillcolor=theme.up, decreasing_fillcolor=theme.down,
            name="Fiyat", showlegend=False,
        ),
        row=1, col=1,
    )

    _draw_boxes(fig, result.boxes, theme, row=1, col=1)
    _draw_polygons(fig, result.polygons, theme, row=1, col=1)
    _draw_lines(fig, result.lines, df, theme, row=1, col=1)
    _draw_levels(fig, result.levels, df, theme, row=1, col=1)
    _draw_markers(
        fig, [m for m in result.markers if m.kind != "macd_cross"], theme, row=1, col=1
    )

    for i, name in enumerate(sub_names, start=2):
        _draw_series_panel(fig, result, name, layout[name], theme, row=i, col=1, df=df)

    if has_vp:
        _draw_volume_profile(fig, result, theme, row=1, col=2)

    for r in range(1, n_rows + 1):
        fig.update_xaxes(showticklabels=(r == n_rows), row=r, col=1)

    if last_n and last_n < len(df):
        fig.update_xaxes(range=[_x(df.index[-last_n]), _x(df.index[-1])])

    title = _build_generic_title(result)
    _apply_layout(fig, theme, title, height=520 + 160 * n_sub)
    return fig


def _build_generic_title(result: IndicatorResult) -> str:
    symbol = result.symbol or "?"
    if result.indicator.startswith("harmonic."):
        school = result.indicator.split(".", 1)[1]
        if not result.last_state:
            return f"{symbol} — {school} ekolü — eşleşen formasyon yok"
        _pid, info = next(reversed(result.last_state.items()))
        pattern = str(info["pattern"]).replace("_", " ").title()
        direction_tr = tr.tr_direction(info["direction"])
        state_tr = tr.tr_state(info["state"])
        return (
            f"{symbol} - {pattern} Formasyonu ({direction_tr}) [{state_tr}] "
            f"— SİSTEM: {school.title()} — {len(result.last_state)} eşleşme"
        )
    return f"{symbol} — {result.indicator}"


def _draw_boxes(fig: go.Figure, boxes: list[Box], theme: Theme, row: int, col: int) -> None:
    for b in boxes:
        dash = "dot" if b.style == "range_box" else "solid"
        fig.add_shape(
            type="rect", x0=_x(b.t0), x1=_x(b.t1), y0=b.low, y1=b.high,
            fillcolor=fill_color(theme, b.style, 0.18),
            line=dict(color=line_color(theme, b.style), width=1, dash=dash),
            row=row, col=col,
        )
        fig.add_annotation(
            x=_x(b.t0), y=b.high, text=tr.tr_style(b.style), showarrow=False,
            font=dict(size=9, color=line_color(theme, b.style)),
            xanchor="left", yanchor="bottom", row=row, col=col,
        )


def _draw_polygons(
    fig: go.Figure, polygons: list[Polygon], theme: Theme, row: int, col: int
) -> None:
    for p in polygons:
        xs = [_x(pt[0]) for pt in p.points] + [_x(p.points[0][0])]
        ys = [pt[1] for pt in p.points] + [p.points[0][1]]
        fig.add_trace(
            go.Scatter(
                x=xs, y=ys, mode="lines", fill="toself",
                line=dict(color=line_color(theme, p.style), width=1.5),
                fillcolor=fill_color(theme, p.style, 0.22),
                name=p.label, showlegend=False, hoverinfo="skip",
            ),
            row=row, col=col,
        )


_DASH_FOR_STYLE = {"dashed": "dash", "dotted": "dot"}


def _draw_lines(
    fig: go.Figure, lines: list[Line], df: pd.DataFrame, theme: Theme, row: int, col: int
) -> None:
    last_x = df.index[-1]
    for ln in lines:
        color = line_color(theme, ln.style)
        style_dash = _DASH_FOR_STYLE.get(ln.style, "solid")
        (t0, p0), (t1, p1) = ln.points[0], ln.points[-1]
        fig.add_trace(
            go.Scatter(
                x=[_x(t0), _x(t1)], y=[p0, p1], mode="lines",
                line=dict(color=color, width=1.6, dash=style_dash),
                name=ln.label, showlegend=False, hoverinfo="skip",
            ),
            row=row, col=col,
        )
        if ln.extend_right and t1 < last_x:
            dt1, dt0 = pd.Timestamp(t1), pd.Timestamp(t0)
            span = (dt1 - dt0).total_seconds()
            slope = (p1 - p0) / span if span > 0 else 0.0
            remaining = (pd.Timestamp(last_x) - dt1).total_seconds()
            # Uzatma, çizginin KENDİ bacağının en fazla 3 katı kadar ileri gider
            # (son bara kadar DEĞİL) — aksi halde kısa/dik bir bacağın (ör.
            # harmonik X→B) eğimi yıllarca ileri projekte edilince fiyat ekseni
            # gerçek dışı büyür (Faz 7'de gerçek veriyle bulunan bir görsel
            # bozulma; price_structure'ın uzun/yatık trendlerinde bu sınır
            # zaten remaining'den büyük olduğu için etkisiz kalır).
            extension_seconds = min(remaining, span * 3) if span > 0 else remaining
            ext_time = dt1 + pd.Timedelta(seconds=extension_seconds)
            proj = p1 + slope * extension_seconds
            fig.add_trace(
                go.Scatter(
                    x=[_x(t1), _x(ext_time)], y=[p1, proj], mode="lines",
                    line=dict(color=color, width=1.2, dash="dash"),
                    name=f"{ln.label}_uzatma", showlegend=False, hoverinfo="skip",
                ),
                row=row, col=col,
            )
            fig.add_annotation(
                x=_x(ext_time), y=proj, text=ln.label, showarrow=False,
                font=dict(size=9, color=color), xanchor="right", yanchor="bottom",
                row=row, col=col,
            )


_LEVEL_DASH = {
    "poc": "solid", "dotted": "dot", "fib_extension": "dot",
    "bullish": "dot", "bearish": "dot",
}


def _level_color(theme: Theme, lv: Level) -> str:
    if lv.style.startswith("fib_"):
        try:
            ratio = float(lv.label.rsplit("_", 1)[-1])
            return fib_color(theme, ratio)
        except ValueError:
            return theme.gray
    return line_color(theme, lv.style)


def _draw_levels(
    fig: go.Figure, levels: list[Level], df: pd.DataFrame, theme: Theme, row: int, col: int
) -> None:
    first_x, last_x = df.index[0], df.index[-1]
    for lv in levels:
        x0 = lv.start if lv.start is not None else first_x
        x1 = lv.end if lv.end is not None else last_x
        color = _level_color(theme, lv)
        dash = _LEVEL_DASH.get(lv.style, "dash")
        fig.add_shape(
            type="line", x0=_x(x0), x1=_x(x1), y0=lv.price, y1=lv.price,
            line=dict(color=color, width=1, dash=dash), row=row, col=col,
        )
        fig.add_annotation(
            x=_x(x1), y=lv.price, text=lv.label, showarrow=False,
            font=dict(size=9, color=color), xanchor="left", yanchor="bottom",
            row=row, col=col,
        )


_STRUCTURE_COLOR = {"HH": "green", "HL": "green", "LH": "red", "LL": "red"}


def _draw_markers(fig: go.Figure, markers: list[Marker], theme: Theme, row: int, col: int) -> None:
    for m in markers:
        if m.kind == "structure_label":
            color = getattr(theme, _STRUCTURE_COLOR.get(m.text, "gray"))
            above = m.text in ("HH", "LH")
            fig.add_annotation(
                x=_x(m.t), y=m.price, text=m.text, showarrow=False,
                font=dict(size=10, color=color, family=theme.font),
                yshift=12 if above else -12, row=row, col=col,
            )
        elif m.kind.startswith("harmonic_"):
            state = m.kind.removeprefix("harmonic_")
            color = line_color(theme, "bearish" if state == "invalidated" else "bullish")
            fig.add_annotation(
                x=_x(m.t), y=m.price, text=m.text, showarrow=True, arrowhead=2, arrowcolor=color,
                font=dict(size=10, color=theme.text), bgcolor=theme.bg, bordercolor=color,
                ax=30, ay=-30, row=row, col=col,
            )
        elif m.kind == "pair_signal":
            continue  # yalnızca pair modunda, _render_pair kendi çizer
        else:
            fig.add_annotation(
                x=_x(m.t), y=m.price, text=m.text, showarrow=False,
                font=dict(size=9, color=theme.muted), yshift=10, row=row, col=col,
            )


def _draw_series_panel(
    fig: go.Figure, result: IndicatorResult, name: str, series_names: list[str],
    theme: Theme, row: int, col: int, df: pd.DataFrame,
) -> None:
    if name == "hacim":
        vol = result.series.get("volume")
        if vol is not None:
            colors = [
                theme.up if c >= o else theme.down
                for o, c in zip(df["open"], df["close"], strict=True)
            ]
            fig.add_trace(
                go.Bar(
                    x=_xs(vol.index), y=vol, marker_color=colors, name="Hacim", showlegend=False
                ),
                row=row, col=col,
            )
        vol_ma = result.series.get("volume_ma")
        if vol_ma is not None:
            fig.add_trace(
                go.Scatter(
                    x=_xs(vol_ma.index), y=vol_ma, mode="lines",
                    line=dict(color=theme.blue, width=1.4), name="Hacim MA", showlegend=False,
                ),
                row=row, col=col,
            )
        return
    if name == "macd":
        hist = result.series.get("macd_hist")
        if hist is not None:
            colors = [theme.up if v >= 0 else theme.down for v in hist]
            fig.add_trace(
                go.Bar(
                    x=_xs(hist.index), y=hist, marker_color=colors,
                    name="MACD Hist", showlegend=False,
                ),
                row=row, col=col,
            )
        macd = result.series.get("macd")
        if macd is not None:
            fig.add_trace(
                go.Scatter(
                    x=_xs(macd.index), y=macd, mode="lines", line=dict(color=theme.blue, width=1.3),
                    name="MACD", showlegend=False,
                ),
                row=row, col=col,
            )
        sig = result.series.get("macd_signal")
        if sig is not None:
            fig.add_trace(
                go.Scatter(
                    x=_xs(sig.index), y=sig, mode="lines", line=dict(color=theme.orange, width=1.3),
                    name="Sinyal", showlegend=False,
                ),
                row=row, col=col,
            )
        for m in result.markers:
            if m.kind == "macd_cross":
                up = "↑" in m.text
                color = theme.up if up else theme.down
                fig.add_annotation(
                    x=_x(m.t), y=m.price, text="▲" if up else "▼", showarrow=False,
                    font=dict(size=10, color=color), row=row, col=col,
                )
        return
    for s_name in series_names:
        s = result.series.get(s_name)
        if s is not None:
            fig.add_trace(
                go.Scatter(x=_xs(s.index), y=s, mode="lines", name=s_name, showlegend=False),
                row=row, col=col,
            )


def _draw_volume_profile(
    fig: go.Figure, result: IndicatorResult, theme: Theme, row: int, col: int
) -> None:
    bins, vols = result.series.get("vp_bins"), result.series.get("vp_volumes")
    if bins is None or vols is None:
        return
    va_low = next((lv.price for lv in result.levels if lv.label == "VAL"), None)
    va_high = next((lv.price for lv in result.levels if lv.label == "VAH"), None)
    colors = []
    for p in bins.to_numpy():
        in_va = va_low is not None and va_high is not None and va_low <= p <= va_high
        colors.append(
            fill_color(theme, "bullish", 0.85) if in_va else fill_color(theme, "support_zone", 0.6)
        )
    fig.add_trace(
        go.Bar(
            x=vols.to_numpy(), y=bins.to_numpy(), orientation="h", marker_color=colors,
            name="Hacim Profili", showlegend=False,
        ),
        row=row, col=col,
    )
    gauss = result.series.get("vp_gauss")
    if gauss is not None:
        fig.add_trace(
            go.Scatter(
                x=gauss.to_numpy(), y=gauss.index.to_numpy(), mode="lines",
                line=dict(color=theme.yellow, width=2), name="Gaussian Fit", showlegend=True,
            ),
            row=row, col=col,
        )


# ---------------------------------------------------------------- pair mod --


def _render_pair(result: IndicatorResult, theme: Theme, last_n: int | None) -> go.Figure:
    s = result.series
    ls = result.last_state
    idx_full = s["y_norm"].index
    idx_dt = idx_full[-last_n:] if last_n and last_n < len(idx_full) else idx_full
    idx = _xs(idx_dt)  # trace x= için string; .loc[] seçimi idx_dt ile yapılır
    y_symbol, x_symbol = result.symbol.split("/") if "/" in result.symbol else ("Y", "X")

    def sel(key: str) -> pd.Series:
        return s[key].loc[idx_dt]

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.06,
        row_heights=[0.34, 0.33, 0.33],
        subplot_titles=(
            "1- Fiyat Yakınlığı (Normalize)",
            "2- Portföy Performansı",
            "3- Z-Skoru ve Momentum Dönüş Onaylı İşlemler",
        ),
    )

    # NOT: `add_vrect(row=...)` bir subplot'a ilk trace eklenmeden önce
    # çağrılırsa Plotly (7.x) shape'i SESSİZCE hiç eklemez (Faz 7'de gerçek
    # render ile bulunan bir davranış) — bu yüzden gölge kutuları HER
    # zaman o satırın İLK trace'inden SONRA çizilir.
    fig.add_trace(
        go.Scatter(
            x=idx, y=sel("x_norm"), mode="lines",
            line=dict(color=theme.gray, width=1.3), name=f"{x_symbol} (X)",
        ),
        row=1, col=1,
    )
    _draw_holding_boxes(fig, result.boxes, theme, row=1)
    fig.add_trace(
        go.Scatter(
            x=idx, y=sel("y_norm"), mode="lines",
            line=dict(color=theme.blue, width=1.6), name=f"{y_symbol} (Y)",
        ),
        row=1, col=1,
    )

    baseline = float(s["portfolio"].iloc[0])
    fig.add_trace(
        go.Scatter(
            x=idx, y=sel("buyhold_5050"), mode="lines",
            line=dict(color=theme.gray, width=1.2, dash="dash"), name="Buy & Hold (50/50)",
        ),
        row=2, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=idx, y=sel("portfolio"), mode="lines",
            line=dict(color=theme.green, width=1.8), name="Rölatif Momentum Portföyü",
        ),
        row=2, col=1,
    )
    fig.add_hline(y=baseline, line=dict(color=theme.muted, width=1, dash="dot"), row=2, col=1)

    fig.add_trace(
        go.Scatter(
            x=idx, y=sel("z"), mode="lines",
            line=dict(color=theme.orange, width=1.6), name="Z-Skoru",
        ),
        row=3, col=1,
    )
    _draw_holding_boxes(fig, result.boxes, theme, row=3)
    fig.add_trace(
        go.Scatter(
            x=idx, y=sel("upper"), mode="lines",
            line=dict(color=theme.red, width=1, dash="dash"),
            name=f"Aşırı Ucuz {x_symbol} Sınırı",
        ),
        row=3, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=idx, y=sel("lower"), mode="lines",
            line=dict(color=theme.green, width=1, dash="dash"),
            name=f"Aşırı Ucuz {y_symbol} Sınırı",
        ),
        row=3, col=1,
    )

    for m in result.markers:
        if m.kind != "pair_signal" or m.t not in idx_dt:
            continue
        color = theme.blue if m.text.startswith(y_symbol) else theme.gray
        fig.add_annotation(
            x=_x(m.t), y=m.price, text=m.text, showarrow=False,
            font=dict(size=9, color=theme.text), bgcolor=theme.bg, bordercolor=color, borderwidth=1,
            yshift=14 if m.price >= 0 else -14, row=3, col=1,
        )

    z_today, z_yday = ls.get("z_today"), ls.get("z_yesterday")
    z_str = (
        f"{z_yday:.3f} -> {z_today:.3f}" if z_today is not None and z_yday is not None else "---"
    )
    signal_today = ls.get("signal_today") or "DURUM"
    holding_sym = ls.get("holding") or "---"
    date_str = _fmt_date(idx[-1])
    title = f"{signal_today} | {holding_sym} AL | Z: {z_str} | {date_str}"
    _apply_layout(fig, theme, title, height=780)
    return fig


def _draw_holding_boxes(fig: go.Figure, boxes: list[Box], theme: Theme, row: int) -> None:
    for b in boxes:
        if b.style not in ("y_holding", "x_holding"):
            continue
        fig.add_vrect(
            x0=_x(b.t0), x1=_x(b.t1), fillcolor=fill_color(theme, b.style, 0.20), line_width=0,
            layer="below", row=row, col=1,
        )
