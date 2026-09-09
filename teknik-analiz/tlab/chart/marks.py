"""Ortak çizim öğeleri — referans görsellerdeki işaretlerin birebir karşılıkları.

Buradaki her fonksiyon `teknik-analiz/önemli/` altındaki bir referans
görselden ölçülerek yazıldı; yorumlarda hangi görselden geldiği yazıyor.
Hiçbiri HESAP YAPMAZ: hepsi hazır değer alır, yalnızca çizer.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go

from tlab.chart.frame import ChartFrame
from tlab.chart.tokens import METRICS, Role, rgba, role_color


def candles(cf: ChartFrame, df: pd.DataFrame, panel: str = "price", name: str = "Fiyat") -> None:
    """Mum serisi. Hover'da OHLC tek kutuda (`x unified`) görünür."""
    p = cf.pal
    cf.add(
        go.Candlestick(
            x=df.index, open=df["open"], high=df["high"], low=df["low"], close=df["close"],
            name=name,
            increasing=dict(line=dict(color=p.candle_up_line, width=1), fillcolor=p.candle_up),
            decreasing=dict(line=dict(color=p.candle_down_line, width=1), fillcolor=p.candle_down),
            whiskerwidth=0.0, showlegend=False,
            # Hover'da ham float basmasın: "62.2713" değil "62.27".
            yhoverformat=",.2f",
        ),
        panel,
        observe=pd.concat([df["low"], df["high"]]),
    )
    # rangeslider'ı make_subplots sonrası Plotly yeniden açabiliyor
    cf.fig.update_layout(xaxis_rangeslider_visible=False)


def volume(cf: ChartFrame, df: pd.DataFrame, panel: str = "volume", ma: int | None = 21) -> None:
    """Hacim çubukları + isteğe bağlı hareketli ortalama (referans: AEFES,
    DENGE görselleri — çubuklar yön rengine göre soluk, MA turuncu ince)."""
    p = cf.pal
    up = df["close"] >= df["open"]
    colors = [rgba(p.candle_up, 0.40) if u else rgba(p.candle_down, 0.40) for u in up]
    cf.add(
        go.Bar(
            x=df.index, y=df["volume"], marker=dict(color=colors, line=dict(width=0)),
            name="Hacim", showlegend=False, hovertemplate="Hacim: %{y:,.0f}<extra></extra>",
        ),
        panel,
        observe=df["volume"],
    )
    if ma:
        vma = df["volume"].rolling(ma).mean()
        cf.add(
            go.Scatter(
                x=df.index, y=vma, mode="lines", name=f"Hacim MA{ma}",
                line=dict(color=p.warn, width=METRICS.line_series),
                hovertemplate=f"MA{ma}: %{{y:,.0f}}<extra></extra>", showlegend=False,
            ),
            panel,
            observe=vma,
        )


def line_series(
    cf: ChartFrame, x, y, panel: str, *, name: str, role: Role = "accent",
    width: float | None = None, dash: str | None = None, fmt: str = ".2f",
) -> None:
    """Gösterge serisi (RSI, MACD, MA...). K1 hatasının olamayacağı yol:
    burada x/y TAM dizi olarak geçer, iki uç noktaya indirgenmez."""
    cf.add(
        go.Scatter(
            x=x, y=y, mode="lines", name=name,
            line=dict(
                color=role_color(cf.theme, role),
                width=width or METRICS.line_series,
                dash=dash or "solid",
            ),
            hovertemplate=f"{name}: %{{y:{fmt}}}<extra></extra>", showlegend=False,
        ),
        panel,
        observe=y,
    )


def guide_level(cf: ChartFrame, value: float, panel: str, *, dash: str = "dot") -> None:
    """RSI 30/70 gibi soluk kılavuz çizgisi — hover'a girmez."""
    cf.fig.add_hline(
        y=value, row=cf.row(panel), col=1,
        line=dict(color=rgba(cf.pal.text_muted, 0.35), width=METRICS.line_guide, dash=dash),
    )


@dataclass(frozen=True)
class Touch:
    """Bir sınır çizgisine temas noktası. Referans: HRihBa2WIAIZjP_ (U1..U3 /
    L1..L3) ve HRjNKRZWAAAhfSy (U1..U4 / L1..L4)."""

    t: pd.Timestamp
    price: float
    label: str          # "U1", "L3", ...
    above: bool         # etiket noktanın üstünde mi


def boundary(
    cf: ChartFrame, points: list[tuple[pd.Timestamp, float]], *, role: Role,
    name: str, touches: list[Touch] | None = None, panel: str = "price",
    dash: str | None = None, width: float | None = None,
) -> None:
    """Formasyon sınırı + üzerindeki temas noktaları.

    Kullanıcının isteği: "kaç tepeye temas ederek oluştuğu bile yazıyor".
    Referans görselde bu, çizgi üstünde NUMARALI içi boş dairelerle
    yapılmış — metin rozetiyle değil. Aynısı burada.

    Çizgi YALNIZCA verilen noktalar arasında uzanır; grafiğin sol kenarına
    kadar uzatılmaz (referans görsellerin hepsinde böyle).
    """
    color = role_color(cf.theme, role)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    cf.add(
        go.Scatter(
            x=xs, y=ys, mode="lines", name=name,
            line=dict(color=color, width=width or METRICS.line_pattern, dash=dash or "solid"),
            hoverinfo="skip", showlegend=False,
        ),
        panel,
        observe=ys,
    )
    if not touches:
        return
    # Etiket çakışma çözücü: art arda gelen iki temas x ekseninde birbirine
    # çok yakınsa etiketleri aynı yükseklikte üst üste biner (ilk denemede
    # L5, sinyal kutusunun altında kayboldu). İkincisi bir kademe dışa alınır.
    span = (max(t.t for t in touches) - min(t.t for t in touches)) or pd.Timedelta(days=1)
    near = span / 18
    positions: list[str] = []
    prev_t = None
    staggered = False
    for t in touches:
        close_to_prev = prev_t is not None and (t.t - prev_t) < near
        staggered = close_to_prev and not staggered
        if t.above:
            positions.append("top right" if staggered else "top center")
        else:
            positions.append("bottom right" if staggered else "bottom center")
        prev_t = t.t

    cf.add(
        go.Scatter(
            x=[t.t for t in touches], y=[t.price for t in touches],
            mode="markers+text",
            marker=dict(
                symbol="circle-open", size=METRICS.marker_touch,
                color=color, line=dict(color=color, width=1.8),
            ),
            text=[t.label for t in touches],
            textposition=positions,
            textfont=dict(family=METRICS.font_family, size=METRICS.font_label, color=color),
            name=f"{name} temas",
            hovertemplate="%{text}: %{y:.2f}<extra></extra>", showlegend=False,
        ),
        panel,
    )


def zone_band(
    cf: ChartFrame, low: float, high: float, *, role: Role, label: str,
    panel: str = "price", x0=None, x1=None, edge_label: bool = True,
    border: bool = True,
) -> None:
    """Arz/talep bölgesi ya da aralık bandı.

    Kullanıcı 2026-09-08: "supply demand ... sade ve temiz bir şey olmalı ...
    her grafikte sadece sağ tarafına mesela demand zone yazmalı ve o
    aralıktaki değerler yazılmalı".

    Bu yüzden: yumuşak dolgu + ince kenar, etiket GRAFİĞİN İÇİNDE DEĞİL,
    sağ kenar boşluğunda (referans: HRjNKRZWAAAhfSy'deki tam genişlik bandı
    ve kullanıcının paylaştığı koyu temalı talep kutusu).
    """
    color = role_color(cf.theme, role)
    yr = cf.yref(panel)
    xr = cf.xref(panel)
    shape = dict(
        type="rect", yref=yr, y0=low, y1=high,
        fillcolor=rgba(color, METRICS.fill_alpha_zone),
        line=dict(color=rgba(color, 0.45) if border else "rgba(0,0,0,0)", width=1 if border else 0),
        layer="below",
    )
    if x0 is None or x1 is None:
        shape.update(xref=f"{xr} domain", x0=0, x1=1)
    else:
        shape.update(xref=xr, x0=x0, x1=x1)
    cf.fig.add_shape(**shape)

    next(p for p in cf.panels if p.name == panel).observe([low, high])

    if edge_label:
        # weight=2: bölge başlığı yerini korur, fibo seviyeleri etrafından akar
        cf.edge_label(
            panel, (low + high) / 2,
            f"<b>{label}</b><br>{low:,.2f} – {high:,.2f}", color, weight=2,
        )


def fib_ladder(
    cf: ChartFrame, levels: list[tuple[float, float, str]], *, panel: str = "price",
) -> None:
    """Fibonacci merdiveni — (oran, fiyat, etiket) üçlüleri.

    Kullanıcının şikâyeti: "0.5 - 261.75 yazıyor ... fibo da çizilmeli ve
    fiyatlar fibo değerleri yazılmalı". Referans HRhIeAdbcAAL2_B'de her
    seviye KENDİ renginde kesikli bir çizgi, etiketi GRAFİĞİN SAĞINDA,
    çizgiyle aynı renkte ve "0.618: 185.00" biçiminde.
    """
    # oran -> rol: uçlar nötr, orta bölge (0.382-0.618 altın bölge) vurgulu
    def role_for(ratio: float) -> Role:
        if ratio <= 0.0 or ratio >= 1.0:
            return "neutral"
        if 0.382 <= ratio <= 0.618:
            return "warn"
        return "accent"

    xr, yr = cf.xref(panel), cf.yref(panel)
    prices = []
    for ratio, price, label in levels:
        color = role_color(cf.theme, role_for(ratio))
        cf.fig.add_shape(
            type="line", xref=f"{xr} domain", x0=0, x1=1, yref=yr, y0=price, y1=price,
            line=dict(color=color, width=1.2, dash="dash"), layer="below",
        )
        cf.edge_label(panel, price, f"{label}: {price:,.2f}", color)
        prices.append(price)
    next(p for p in cf.panels if p.name == panel).observe(prices)


def signal_box(
    cf: ChartFrame, t: pd.Timestamp, price: float, *, text: str, role: Role,
    panel: str = "price", below: bool = True,
) -> None:
    """AL/SAT kutusu. Referans HRdEu6qaoAEaHIT: kutunun kendisi çerçeveli,
    fiyat noktasına DİKEY ince bir bağlayıcıyla bağlanıyor; mumların
    ortasına gömülmüyor."""
    color = role_color(cf.theme, role)
    cf.fig.add_annotation(
        x=t, y=price, xref=cf.xref(panel), yref=cf.yref(panel),
        text=f"<b>{text}</b>", showarrow=True,
        arrowhead=0, arrowwidth=1.2, arrowcolor=color,
        ax=0, ay=44 if below else -44,
        bgcolor=cf.pal.panel_bg, bordercolor=color, borderwidth=1.2, borderpad=4,
        font=dict(family=METRICS.font_family, size=METRICS.font_label, color=color),
    )


def pivot_markers(
    cf: ChartFrame, pivots: list[tuple[pd.Timestamp, float, str]], *, panel: str = "price",
) -> None:
    """HH/LH/HL/LL üçgenleri. Referans ornek1.png ve HRdEu6qaoAEaHIT:
    tepelerin ÜSTÜNE aşağı bakan, diplerin ALTINA yukarı bakan küçük
    üçgenler + kısa etiket. Aralarına zigzag ÇİZİLMEZ."""
    highs = [(t, p, lb) for t, p, lb in pivots if lb in ("HH", "LH")]
    lows = [(t, p, lb) for t, p, lb in pivots if lb in ("HL", "LL")]
    for group, symbol, pos, role in (
        (highs, "triangle-down", "top center", "warn"),
        (lows, "triangle-up", "bottom center", "accent"),
    ):
        if not group:
            continue
        color = role_color(cf.theme, role)
        cf.add(
            go.Scatter(
                x=[g[0] for g in group], y=[g[1] for g in group],
                mode="markers+text",
                marker=dict(symbol=symbol, size=METRICS.marker_pivot, color=color),
                text=[g[2] for g in group], textposition=pos,
                textfont=dict(family=METRICS.font_family, size=9, color=color),
                name="Yapı", hovertemplate="%{text}: %{y:.2f}<extra></extra>",
                showlegend=False,
            ),
            panel,
        )


def regime_shading(
    cf: ChartFrame, spans: list[tuple[pd.Timestamp, pd.Timestamp, str]], *, panels=None,
) -> None:
    """Düşey rejim gölgeleri — TÜM panellerin arkasına.

    Referans `önemli/HRcUk75bgAApv6n.png`'de dört panelin arkasında farklı
    tonlarda düşey bantlar var; dönemleri (rejimleri) ayırıyorlar. Grafiğin
    okunuşunu kolaylaştıran, veriyi örtmeyen bir katman.

    `spans`: (başlangıç, bitiş, rol) üçlüleri.
    """
    targets = panels or [p.name for p in cf.panels]
    for t0, t1, role in spans:
        color = role_color(cf.theme, role)
        for name in targets:
            cf.fig.add_shape(
                type="rect", xref=cf.xref(name), x0=t0, x1=t1,
                yref=f"{cf.yref(name)} domain", y0=0, y1=1,
                fillcolor=rgba(color, 0.055), line=dict(width=0), layer="below",
            )
