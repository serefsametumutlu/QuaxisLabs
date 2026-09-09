"""Harmonik / ABCD grafiği — 9 göstergeyi karşılar.

Kapsadıkları: `harmonic.carney`, `.cypher`, `.five_zero`, `.gilmore`,
`.navarro200`, `.nenstar`, `.pesavento`, `.three_drives` ve
`structure.swing_fib_abcd`.

Referanslar: `önemli/HRhIeAdbcAAL2_B.png`, `önemli/HRdEu6qaoAEaHIT.png`.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from tlab.chart.contracts import XabcdPattern
from tlab.chart.frame import ChartFrame, Panel
from tlab.chart.marks import candles, fib_ladder, signal_box, volume, zone_band
from tlab.chart.tokens import METRICS, ThemeName, rgba, role_color

_STATE_TR = {
    "izlemede": "İZLEMEDE", "aktif": "AKTİF",
    "tamamlandi": "TAMAMLANDI", "gecersiz": "GEÇERSİZ",
}


def compose(
    df: pd.DataFrame,
    pat: XabcdPattern,
    *,
    symbol: str,
    timeframe: str = "1G",
    theme: ThemeName = "light",
    width: int = 1600,
    height: int = 880,
) -> go.Figure:
    role = "bullish" if pat.direction == "bullish" else "bearish"
    color = role_color(theme, role)

    facts = [("Periyot", timeframe), ("Okul", pat.school)]
    facts += [(k, v) for k, v in pat.ratios]
    if pat.prz is not None:
        facts.append(("PRZ", f"{pat.prz[0]:,.2f} – {pat.prz[1]:,.2f}"))
    if pat.theoretical_d is not None:
        facts.append(("Teorik D", f"{pat.theoretical_d:,.2f}"))
    if pat.bars_ago is not None:
        facts.append(("Sinyal yaşı", f"{pat.bars_ago} bar"))

    cf = ChartFrame(
        panels=[
            Panel("price", METRICS.panel_ratio_price + 0.10, "Fiyat"),
            Panel("volume", METRICS.panel_ratio_sub, "Hacim"),
        ],
        theme=theme, width=width, height=height,
        title=f"{symbol} — {pat.pattern_name.upper()} — {_STATE_TR[pat.state]}",
        subtitle="  |  ".join(f"{k}: {v}" for k, v in facts),
    )

    # 1) PRZ bandı — sağ kenarda etiketli, mumların ALTINDA
    if pat.prz is not None:
        lo, hi = pat.prz
        zone_band(cf, lo, hi, role=role, label="PRZ", border=False)

    # 2) Mumlar
    candles(cf, df)

    # 3) Formasyon gövdesi — B'de BULUŞAN İKİ KANAT.
    #
    #    Referans HRhIeAdbcAAL2_B'de gövde TEK bir poligon DEĞİL: sol kanat
    #    X-A-B, sağ kanat B-C-D, ikisi B köşesinde birleşiyor. X ile D
    #    arasında HİÇ çizgi yok.
    #
    #    İlk denemede tek `toself` poligonu (X-A-B-C-D) çizilmişti; Plotly
    #    onu kapatmak için X'ten D'ye uzun bir köşegen atıyor ve formasyon
    #    grafiğin altını boydan boya kesen yanlış bir çizgi kazanıyordu.
    pts = list(pat.points) + ([pat.actual_d] if pat.actual_d else [])
    wings: list[list] = [pts[0:3]]                 # X, A, B
    if len(pts) >= 5:
        wings.append(pts[2:5])                     # B, C, D
    elif len(pts) == 4:
        wings.append(pts[2:4])                     # B, C (D henüz yok)

    for wing in wings:
        if len(wing) < 3:
            # İki noktalı kanat kapalı bir alan oluşturmaz; yalnızca çizgi.
            cf.add(
                go.Scatter(
                    x=[w.t for w in wing], y=[w.price for w in wing], mode="lines",
                    line=dict(color=color, width=METRICS.line_pattern),
                    hoverinfo="skip", showlegend=False, name=pat.pattern_name,
                ),
                "price", observe=[w.price for w in wing],
            )
            continue
        cf.add(
            go.Scatter(
                x=[w.t for w in wing] + [wing[0].t],
                y=[w.price for w in wing] + [wing[0].price],
                mode="lines", fill="toself",
                fillcolor=rgba(color, METRICS.fill_alpha_shape),
                line=dict(color=color, width=METRICS.line_pattern),
                name=pat.pattern_name, hoverinfo="skip", showlegend=False,
            ),
            "price", observe=[w.price for w in wing],
        )

    xs = [p.t for p in pts]
    ys = [p.price for p in pts]

    # 4) Köşeler — daire + harf
    cf.add(
        go.Scatter(
            x=xs, y=ys, mode="markers+text",
            marker=dict(symbol="circle", size=9, color=color,
                        line=dict(color=cf.pal.panel_bg, width=1.5)),
            text=[p.label for p in pts],
            textposition=[
                "top center" if (pat.direction == "bearish") == (i % 2 == 0)
                else "bottom center"
                for i in range(len(pts))
            ],
            textfont=dict(family=METRICS.font_family, size=12, color=cf.pal.text),
            name="Noktalar", hovertemplate="%{text}: %{y:,.2f}<extra></extra>",
            showlegend=False,
        ),
        "price",
    )

    # 5) C -> Teorik D projeksiyonu (referans HRdEu6qaoAEaHIT'teki altın
    #    noktalı çizgi). Gerçek D henüz yoksa hedefi gösterir.
    if pat.theoretical_d is not None:
        c = pat.points[3]
        end_t = pat.actual_d.t if pat.actual_d else df.index[-1]
        cf.add(
            go.Scatter(
                x=[c.t, end_t], y=[c.price, pat.theoretical_d], mode="lines+markers",
                line=dict(color=role_color(theme, "warn"), width=1.5, dash="dot"),
                marker=dict(size=[0, 11], symbol="diamond",
                            color=role_color(theme, "warn")),
                name="Teorik D",
                hovertemplate="Teorik D: %{y:,.2f}<extra></extra>", showlegend=False,
            ),
            "price", observe=[pat.theoretical_d],
        )
        # Fibo merdiveninde 1.272 seviyesi zaten "D hedefi" diye yazılı;
        # ikisi aynı sayıysa ayrıca "TEORİK D" basmak tekrar olur.
        dup = any(
            abs(price - pat.theoretical_d) < 0.005 * max(abs(price), 1.0)
            for _, price, _ in pat.fib_levels
        )
        if not dup:
            cf.edge_label(
                "price", pat.theoretical_d,
                f"TEORİK D: {pat.theoretical_d:,.2f}", role_color(theme, "warn"), weight=1,
            )

    # 6) Fibo merdiveni
    if pat.fib_levels:
        fib_ladder(cf, list(pat.fib_levels))

    # 7) Sinyal — YALNIZCA D gerçekleştiğinde. Kullanıcı kuralı: sinyal
    #    hedefe varışta değil, formasyonun TAMAMLANDIĞI noktada doğar.
    if pat.actual_d is not None and pat.state in ("aktif", "tamamlandi"):
        signal_box(
            cf, pat.actual_d.t, pat.actual_d.price,
            text="AL / GİRİŞ" if pat.direction == "bullish" else "SAT / GİRİŞ",
            role=role, below=pat.direction == "bullish",
        )

    volume(cf, df, panel="volume", ma=21)
    return cf.finish()
