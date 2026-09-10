"""Yapı raporu — `structure.price_structure`.

Projenin en BİLGİ YOĞUN grafiği: trend çizgileri (temas sayılarıyla),
destek/direnç bölgeleri, hacim profili seviyeleri (POC/VAH/VAL) ve
altta hacim + MACD panelleri. Tek bir "formasyon" değil, fiyatın
etrafındaki YAPININ tamamı.

`market_structure` komposerinden AYRI: o, pivot üçgeni + BOS/CHoCH
çizer (SMC dili); bu, klasik trend çizgisi + bölge + hacim profili
dilidir. İkisi farklı sorulara cevap veriyor, birleştirmek ikisini de
okunmaz yapardı.

`tlab/viz/svg/scenes/report.py`'nin (Faz 4a) öğe listesini izler ve
ORADA gerçek veriyle bulunmuş üç dersi baştan uygular:
  1. Kırılmış trend çizgileri çizilmez (pencere-dışı son temas yüzünden
     "aktif" görünüyorlardı).
  2. Kısa/dik bir bacaktan gelip bugüne projekte edilen çizgi fiyatı
     ekran dışına savuruyor -> uzatma bacağın KENDİ süresinin 3 katıyla
     sınırlı (Faz 7'nin harmonik `xb` kuralının aynısı).
  3. Yalnızca hâlâ AÇIK bölgeler çizilir.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go

from tlab.chart.frame import ChartFrame, Panel
from tlab.chart.marks import candles, line_series, volume, zone_band
from tlab.chart.tokens import METRICS, Role, ThemeName, role_color


@dataclass(frozen=True)
class StructureLine:
    """Bir trend çizgisi + göstergenin ZATEN saydığı temas sayısı."""

    points: tuple[tuple[pd.Timestamp, float], ...]
    role: Role
    label: str
    touches: int | None = None


@dataclass(frozen=True)
class StructureZone:
    low: float
    high: float
    role: Role
    label: str


@dataclass(frozen=True)
class StructureReport:
    lines: tuple[StructureLine, ...]
    zones: tuple[StructureZone, ...]
    poc: float | None
    vah: float | None
    val: float | None
    state: str
    bars_ago: int | None = None


def compose(
    df: pd.DataFrame,
    rep: StructureReport,
    *,
    symbol: str,
    timeframe: str = "1G",
    theme: ThemeName = "light",
    width: int = 1600,
    height: int = 900,
) -> go.Figure:
    facts: list[tuple[str, str]] = [("Periyot", timeframe)]
    facts.append(("Trend çizgisi", str(len(rep.lines))))
    if rep.poc is not None:
        facts.append(("POC", f"{rep.poc:,.2f}"))
    if rep.bars_ago is not None:
        facts.append(("Sinyal yaşı", f"{rep.bars_ago} bar"))

    cf = ChartFrame(
        panels=[
            Panel("price", METRICS.panel_ratio_price, "Fiyat"),
            Panel("volume", METRICS.panel_ratio_sub, "Hacim"),
            Panel("macd", METRICS.panel_ratio_sub, "MACD"),
        ],
        theme=theme, width=width, height=height,
        title=f"{symbol} — YAPI RAPORU — {rep.state}",
        subtitle="  |  ".join(f"{k}: {v}" for k, v in facts),
    )

    # Bölgeler mumların ALTINDA kalsın diye ÖNCE çizilir.
    for z in rep.zones:
        zone_band(cf, z.low, z.high, role=z.role, label=z.label)

    candles(cf, df)

    for ln in rep.lines:
        color = role_color(theme, ln.role)
        xs = [p[0] for p in ln.points]
        ys = [p[1] for p in ln.points]
        cf.add(
            go.Scatter(
                x=xs, y=ys, mode="lines", name=ln.label,
                line=dict(color=color, width=METRICS.line_pattern),
                hovertemplate=f"{ln.label}: %{{y:,.2f}}<extra></extra>",
                showlegend=False,
            ),
            "price", observe=ys,
        )
        # Temas sayısı çizginin SAĞ ucunda: hangi çizgi kaç kez test
        # edilmiş, efsaneye bakmadan görünsün (referans görsellerdeki
        # "(Temas:N)" rozeti).
        text = ln.label if ln.touches is None else f"{ln.label} ({ln.touches} temas)"
        cf.edge_label("price", ys[-1], text, color)

    for value, name, role in (
        (rep.poc, "POC", "accent"), (rep.vah, "VAH", "neutral"), (rep.val, "VAL", "neutral"),
    ):
        if value is None:
            continue
        cf.add(
            go.Scatter(
                x=[df.index[0], df.index[-1]], y=[value, value], mode="lines",
                line=dict(color=role_color(theme, role), width=1.2, dash="dash"),
                name=name, hovertemplate=f"{name}: %{{y:,.2f}}<extra></extra>",
                showlegend=False,
            ),
            "price", observe=[value],
        )
        cf.edge_label("price", value, f"{name}: {value:,.2f}", role_color(theme, role))

    volume(cf, df, panel="volume", ma=21)

    close = df["close"]
    macd_line = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
    signal = macd_line.ewm(span=9, adjust=False).mean()
    warm = 60
    line_series(cf, macd_line.index[warm:], macd_line.iloc[warm:], "macd",
                name="MACD", role="accent", fmt=".3f")
    line_series(cf, signal.index[warm:], signal.iloc[warm:], "macd",
                name="Sinyal", role="warn", fmt=".3f")
    return cf.finish()
