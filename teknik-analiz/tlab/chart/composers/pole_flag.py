"""Bayrak / flama grafiği. Referans: `önemli/HRaULXwaEAA60Z5.png`."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from tlab.chart.composers.boundary_pattern import rsi
from tlab.chart.frame import ChartFrame, Panel
from tlab.chart.marks import candles, guide_level, line_series, signal_box, volume
from tlab.chart.tokens import METRICS, ThemeName, rgba, role_color
from tlab.indicators.patterns.pole_flag import PoleFlag

_STATE_TR = {
    "olusuyor": "OLUŞUYOR", "onaylandi": "KIRILIM ONAYLANDI",
    "suresi_doldu": "SÜRESİ DOLDU",
}


def compose(
    df: pd.DataFrame,
    pf: PoleFlag,
    *,
    symbol: str,
    timeframe: str = "1G",
    theme: ThemeName = "light",
    width: int = 1600,
    height: int = 900,
) -> go.Figure:
    role = "bullish" if pf.direction == "long" else "bearish"
    color = role_color(theme, role)

    cf = ChartFrame(
        panels=[
            Panel("price", METRICS.panel_ratio_price, "Fiyat"),
            Panel("volume", METRICS.panel_ratio_sub, "Hacim"),
            Panel("rsi", METRICS.panel_ratio_sub, "RSI", y_range=(0, 100)),
        ],
        theme=theme, width=width, height=height,
        title=f"{symbol} — {'YÜKSELİŞ' if pf.direction == 'long' else 'DÜŞÜŞ'} "
              f"{pf.shape.upper()} — {_STATE_TR[pf.state]}",
        subtitle="  |  ".join([
            f"Periyot: {timeframe}",
            f"Direk: %{pf.pole_pct * 100:.1f}",
            f"Konsolidasyon: {pf.flag_bars} bar",
            f"Hacim daralması: {pf.vol_contraction:.2f}x",
            f"Hedef: {pf.target:,.2f}" if pf.target else "",
            f"Sinyal yaşı: {pf.bars_ago} bar" if pf.bars_ago is not None else "",
        ]).replace("  |    |  ", "  |  "),
    )

    candles(cf, df)

    # 1) DİREK — kalın, tam boy. Kullanıcının "yarım kalmış çizgi"
    #    şikâyetinin karşılığı: çizgi başlangıç pivotundan bitiş
    #    pivotuna KADAR gider, bir yerde kesilmez.
    cf.add(
        go.Scatter(
            x=[pf.pole_start[0], pf.pole_end[0]], y=[pf.pole_start[1], pf.pole_end[1]],
            mode="lines+markers", name="Direk",
            line=dict(color=color, width=2.8),
            marker=dict(size=8, symbol="circle", color=color,
                        line=dict(color=cf.pal.panel_bg, width=1.5)),
            hovertemplate="Direk ucu: %{y:,.2f}<extra></extra>", showlegend=False,
        ),
        "price", observe=[pf.pole_start[1], pf.pole_end[1]],
    )

    # 2) Konsolidasyon kanalı — iki sınır, formasyonun kendi aralığında
    for pts, nm in ((pf.upper, "Üst sınır"), (pf.lower, "Alt sınır")):
        cf.add(
            go.Scatter(
                x=[pts[0][0], pts[1][0]], y=[pts[0][1], pts[1][1]],
                mode="lines", name=nm,
                line=dict(color=color, width=METRICS.line_level, dash="dash"),
                hoverinfo="skip", showlegend=False,
            ),
            "price", observe=[pts[0][1], pts[1][1]],
        )

    # 3) Hedef
    if pf.target is not None:
        cf.fig.add_shape(
            type="line", xref=f"{cf.xref('price')} domain", x0=0, x1=1,
            yref=cf.yref("price"), y0=pf.target, y1=pf.target,
            line=dict(color=rgba(color, 0.5), width=1.2, dash="dot"), layer="below",
        )
        cf.edge_label("price", pf.target, f"HEDEF: {pf.target:,.2f}", rgba(color, 0.85))
        next(p for p in cf.panels if p.name == "price").observe([pf.target])

    # 4) KIRILIM — sinyal burada. Hedefte DEĞİL.
    if pf.breakout is not None:
        t, price = pf.breakout
        cf.add(
            go.Scatter(
                x=[t], y=[price], mode="markers",
                marker=dict(
                    symbol="triangle-up" if pf.direction == "long" else "triangle-down",
                    size=METRICS.marker_signal, color=color,
                ),
                name="Kırılım", hovertemplate="Kırılım: %{y:,.2f}<extra></extra>",
                showlegend=False,
            ),
            "price",
        )
        signal_box(
            cf, t, price,
            text="AL / KIRILIM" if pf.direction == "long" else "SAT / KIRILIM",
            role=role, below=pf.direction == "long",
        )

    volume(cf, df, panel="volume", ma=21)
    r = rsi(df["close"]).iloc[42:]
    line_series(cf, r.index, r, "rsi", name="RSI(14)", role="accent", fmt=".1f")
    guide_level(cf, 70, "rsi")
    guide_level(cf, 30, "rsi")

    fig = cf.finish()
    # 5) Görünüm penceresi: direğin BAŞLANGICINDAN birkaç bar ÖNCE başlar.
    #    Kullanıcı: "mumları çizginin başladığı dibinden bir 5-6 mum
    #    öncesinden başlatmak gerekiyordu".
    # SAĞ kenar da sınırlı. `view_start`den df'in SONUNA kadar çizmek
    # 11 barlık bir direk+bayrağı 190 barlık bir grafiğe sıkıştırıyordu
    # (GÖRÜLEREK bulundu: formasyon sol kenarda nokta gibi kalıyor).
    # Formasyonun kendi genişliğinin ~3 katı kadar sağa bakılır --
    # hedefin gerçekleşip gerçekleşmediğini görmeye yeter.
    _i0 = int(df.index.searchsorted(pf.view_start))
    _i_end = int(df.index.searchsorted(pf.upper[-1][0]))
    if pf.breakout is not None:
        _i_end = max(_i_end, int(df.index.searchsorted(pf.breakout[0])))
    _span = max(_i_end - _i0, 10)
    _right = min(_i_end + _span * 3, len(df) - 1)
    fig.update_xaxes(range=[pf.view_start, df.index[_right]])
    # Y ekseni GÖRÜNEN pencereden ölçeklenir. Otomatik ölçek TÜM seriyi
    # görüyor; x-aralığı SONRADAN kısıtlandığı için grafik boş alana
    # yayılıyordu (fikstür 30'dan başlıyor, bayrak 47'de -- eksen 28-51
    # çıkıyordu). `GORSEL_HATA_TESHISI.md` K2'nin aynısı.
    _vis = df.iloc[_i0 : _right + 1]
    if len(_vis):
        _lo = float(_vis["low"].min())
        _hi = float(_vis["high"].max())
        for _v in (pf.target, pf.pole_start[1], pf.pole_end[1]):
            if _v is not None:
                _lo, _hi = min(_lo, float(_v)), max(_hi, float(_v))
        _pad = (_hi - _lo) * 0.08 or 1.0
        fig.update_yaxes(range=[_lo - _pad, _hi + _pad], row=1, col=1)
    return fig
