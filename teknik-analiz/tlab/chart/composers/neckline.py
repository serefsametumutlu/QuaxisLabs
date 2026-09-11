"""Boyun çizgili dönüş formasyonları — çift tepe/dip ve OBO.

Kullanıcının şikâyeti hem tespitte hem çizimdeydi. Çizim tarafında
istenen: formasyonun NEREDE olduğu bir bakışta anlaşılsın, AL sinyali
KIRILIM barında dursun (hedefte değil), hedef ayrı bir seviye olarak
görünsün.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from tlab.chart.composers.boundary_pattern import rsi
from tlab.chart.frame import ChartFrame, Panel
from tlab.chart.marks import candles, guide_level, line_series, signal_box, volume
from tlab.chart.tokens import METRICS, ThemeName, rgba, role_color
from tlab.indicators.patterns.neckline_v2 import NecklinePattern

_KIND_TR = {
    "cift_dip": "ÇİFT DİP", "cift_tepe": "ÇİFT TEPE",
    "obo": "OMUZ-BAŞ-OMUZ", "ters_obo": "TERS OMUZ-BAŞ-OMUZ",
}
_STATE_TR = {"olusuyor": "OLUŞUYOR", "onaylandi": "ONAYLANDI", "gecersiz": "GEÇERSİZ"}


def compose(
    df: pd.DataFrame,
    pat: NecklinePattern,
    *,
    symbol: str,
    timeframe: str = "1G",
    theme: ThemeName = "light",
    width: int = 1600,
    height: int = 900,
) -> go.Figure:
    role = "bullish" if pat.direction == "long" else "bearish"
    color = role_color(theme, role)

    facts = [
        ("Periyot", timeframe),
        ("Uçlar arası", f"{pat.separation_bars} bar"),
        ("Derinlik", f"%{pat.depth_pct * 100:.1f}"),
        ("Tetik", f"{pat.trigger_price:,.2f}"),
    ]
    if pat.target is not None:
        facts.append(("Hedef", f"{pat.target:,.2f}"))
    if pat.bars_ago is not None:
        facts.append(("Sinyal yaşı", f"{pat.bars_ago} bar"))

    cf = ChartFrame(
        panels=[
            Panel("price", METRICS.panel_ratio_price, "Fiyat"),
            Panel("volume", METRICS.panel_ratio_sub, "Hacim"),
            Panel("rsi", METRICS.panel_ratio_sub, "RSI", y_range=(0, 100)),
        ],
        theme=theme, width=width, height=height,
        title=f"{symbol} — {_KIND_TR[pat.kind]} — {_STATE_TR[pat.state]}",
        subtitle="  |  ".join(f"{k}: {v}" for k, v in facts),
    )

    candles(cf, df)

    # 1) GÖVDE — boyun çizgisi ile fiyat yolu arasındaki dolgulu alan.
    #
    #    Referans (kullanıcının 2026-09-09'da paylaştığı TOBO görseli):
    #    formasyon sadece çizgi değil, üstten boyun çizgisiyle sınırlı,
    #    alttan fiyatın gerçek yolunu izleyen YARI SAYDAM bir gövde.
    #    xabcd'deki kanat mantığının aynısı; ilk çizimde sadece iskelet
    #    çizgisi vardı ve formasyon "oturmuş" görünmüyordu.
    if pat.hologram is not None:
        (nt0, ny0), (nt1, ny1) = pat.neckline
        span = max((nt1 - nt0).total_seconds(), 1.0)

        def neck_at(t: pd.Timestamp) -> float:
            f = (t - nt0).total_seconds() / span
            return ny0 + (ny1 - ny0) * min(max(f, 0.0), 1.0)

        ht = list(pat.hologram.times)
        hp = list(pat.hologram.prices)
        body_x = ht + ht[::-1]
        body_y = hp + [neck_at(t) for t in ht[::-1]]
        cf.add(
            go.Scatter(
                x=body_x, y=body_y, mode="lines", fill="toself",
                fillcolor=rgba(color, METRICS.fill_alpha_shape),
                line=dict(color="rgba(0,0,0,0)", width=0),
                name=_KIND_TR[pat.kind], hoverinfo="skip", showlegend=False,
            ),
            "price", observe=hp,
        )
        # Fiyat yolu (hologram) gövdenin alt kenarı olarak net çizilir
        cf.add(
            go.Scatter(
                x=ht, y=hp, mode="lines", name="Hologram",
                line=dict(color=rgba(color, 0.85), width=2.0),
                hoverinfo="skip", showlegend=False,
            ),
            "price",
        )

    # 2) İSKELET — YALNIZCA hologram yoksa.
    #
    #    İskelet, pivotları düz çizgilerle birleştirir (omuz->baş->omuz).
    #    Hologram VARKEN ikisi birden çizilince bu düz çizgiler mumların
    #    üstünden geçip TREND ÇİZGİSİ gibi görünüyor -- kullanıcının
    #    bildirdiği hata tam buydu ("trend çizgileri hatalı gösteriliyor
    #    bu yapılmamalı"), referans TOBO görselinde böyle bir çizgi YOK.
    #    Formasyonun şeklini zaten hologram (fiyatın GERÇEK yolu)
    #    anlatıyor; iskelet yalnızca hologramsız adaylar için bir yedek.
    if pat.hologram is None:
        skeleton = list(pat.points)
        if pat.outer is not None:
            skeleton = [pat.outer[0], *skeleton, pat.outer[1]]
        cf.add(
            go.Scatter(
                x=[p.t for p in skeleton], y=[p.price for p in skeleton],
                mode="lines", name="İskelet",
                line=dict(color=color, width=METRICS.line_pattern),
                hoverinfo="skip", showlegend=False,
            ),
            "price", observe=[p.price for p in skeleton],
        )

    # 3) KÖŞELER — küçük üçgen + KUTULU etiket (referanstaki rozetler).
    #    Düz metin, mumların üstünde kayboluyordu.
    up = pat.direction == "long"
    for i, pt in enumerate(pat.points):
        if not pt.label:
            continue          # koltukaltı: iskelette var, etiketi yok
        is_neck = pt.label == "BOYUN"
        # uçlar bir yöne, orta nokta ters yöne
        below = up if not is_neck else not up
        cf.add(
            go.Scatter(
                x=[pt.t], y=[pt.price], mode="markers",
                marker=dict(
                    symbol="triangle-up" if below else "triangle-down",
                    size=METRICS.marker_pivot + 3, color=color,
                    line=dict(color=cf.pal.panel_bg, width=1.2),
                ),
                name=pt.label,
                hovertemplate=f"{pt.label}: %{{y:,.2f}}<extra></extra>", showlegend=False,
            ),
            "price",
        )
        cf.fig.add_annotation(
            x=pt.t, y=pt.price, xref=cf.xref("price"), yref=cf.yref("price"),
            text=f"<b>{pt.label}</b>", showarrow=False,
            yshift=-18 if below else 18,
            bgcolor=rgba(color, 0.90), bordercolor=color, borderwidth=1, borderpad=3,
            font=dict(family=METRICS.font_family, size=10, color=cf.pal.bg),
        )

    # 4) Boyun çizgisi — dolgunun üst kenarı; onay seviyesi budur.
    #    Tespit edici formasyonun KENDİ aralığını verir; burada eğimi
    #    koruyarak grafiğin sağ kenarına uzatılır.
    (t0, y0), (t1, y1) = pat.neckline
    # Eğimli bir boyun çizgisi grafiğin sonuna kadar uzatılırsa fiyattan
    # tamamen kaçar (ilk denemede 78'den 60'a indi ve etiket fiyat
    # alanının dışına düştü). Bulkowski'nin "eğimli boyun kaçar" uyarısının
    # görsel karşılığı budur. Bu yüzden çizgi, kırılım/retest barından
    # biraz SONRASINA kadar uzatılır, daha ileri değil.
    anchor_t = t1
    for ev in (pat.breakout, pat.retest):
        if ev is not None and ev.t > anchor_t:
            anchor_t = ev.t

    # Boyun çizgisi (eğimli olabilir) YALNIZCA formasyonun kendi
    # aralığında çizilir.
    cf.add(
        go.Scatter(
            x=[t0, t1], y=[y0, y1], mode="lines", name="Boyun çizgisi",
            line=dict(color=color, width=METRICS.line_level, dash="dot"),
            hoverinfo="skip", showlegend=False,
        ),
        "price", observe=[y0, y1],
    )

    # TETİK çizgisi AYRI ve YATAY. Eğimli boyun sağa uzatılırsa fiyattan
    # kaçar ve kırılım/retest işaretleri çizginin ters tarafında kalır --
    # kullanıcının "kırılım çizgisi yamuk duruyor" bildirimi tam olarak
    # buydu. Onay seviyesi zaten TEK bir fiyattır (eğimli boyunda sağ
    # koltukaltı), dolayısıyla yatay çizilmesi hem doğru hem okunaklı.
    margin = (t1 - t0) * 0.45
    t_trig_end = min(anchor_t + margin, df.index[-1])
    cf.add(
        go.Scatter(
            x=[t0, t_trig_end], y=[pat.trigger_price, pat.trigger_price],
            mode="lines", name="Tetik",
            line=dict(color=color, width=METRICS.line_level, dash="dash"),
            hovertemplate="Tetik: %{y:,.2f}<extra></extra>", showlegend=False,
        ),
        "price", observe=[pat.trigger_price],
    )
    # Etiket TETİK seviyesinde durur; çizginin ucunda değil.
    cf.edge_label("price", pat.trigger_price,
                  f"BOYUN / TETİK: {pat.trigger_price:,.2f}", color, weight=2)

    # 5) Hedef seviyesi — ölçülen hareket
    if pat.target is not None:
        cf.fig.add_shape(
            type="line", xref=f"{cf.xref('price')} domain", x0=0, x1=1,
            yref=cf.yref("price"), y0=pat.target, y1=pat.target,
            line=dict(color=rgba(color, 0.5), width=1.2, dash="dot"), layer="below",
        )
        cf.edge_label("price", pat.target, f"HEDEF: {pat.target:,.2f}", rgba(color, 0.85))
        next(p for p in cf.panels if p.name == "price").observe([pat.target])

    # 6) KIRILIM ve RETEST — kılavuz çizgili kutular (referanstaki gibi).
    #    Sinyal kırılımda doğar; retest ikinci giriş fırsatıdır.
    # Kırılım ve retest birbirine çok yakın barlarda olur; etiketleri
    # hem yatay hem DİKEY ayırmak gerekiyor, yoksa üst üste biniyorlar.
    events = [(pat.breakout, "KIRILIM", 58, 46), (pat.retest, "RETEST", 132, 84)]
    for point, label, offset, drop in events:
        if point is None:
            continue
        cf.add(
            go.Scatter(
                x=[point.t], y=[point.price], mode="markers",
                marker=dict(size=8, symbol="circle", color=cf.pal.panel_bg,
                            line=dict(color=color, width=2)),
                name=label, hovertemplate=f"{label}: %{{y:,.2f}}<extra></extra>",
                showlegend=False,
            ),
            "price",
        )
        cf.fig.add_annotation(
            x=point.t, y=point.price, xref=cf.xref("price"), yref=cf.yref("price"),
            text=f"<b>{label}</b>", showarrow=True,
            arrowhead=0, arrowwidth=1.1, arrowcolor=rgba(cf.pal.text_muted, 0.8),
            ax=offset, ay=drop if up else -drop,
            bgcolor=cf.pal.panel_bg, bordercolor=cf.pal.text_muted,
            borderwidth=1, borderpad=4,
            font=dict(family=METRICS.font_family, size=10, color=cf.pal.text),
        )

    # Formasyona odaklan: köşeler + boyun + kırılım/retest.
    _ts = [p.t for p in pat.points]
    _ts += [pat.neckline[0][0], pat.neckline[-1][0]]
    for _ev in (pat.breakout, pat.retest):
        if _ev is not None:
            _ts.append(_ev.t)
    if pat.hologram is not None and pat.hologram.times:
        _ts += [pat.hologram.times[0], pat.hologram.times[-1]]
    if _ts:
        cf.focus(df, min(_ts), max(_ts))

    volume(cf, df, panel="volume", ma=21)
    r = rsi(df["close"]).iloc[42:]
    line_series(cf, r.index, r, "rsi", name="RSI(14)", role="accent", fmt=".1f")
    guide_level(cf, 70, "rsi")
    guide_level(cf, 30, "rsi")
    return cf.finish()
