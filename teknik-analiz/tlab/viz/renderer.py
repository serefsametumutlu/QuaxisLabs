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

import textwrap
from dataclasses import dataclass, replace
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from tlab.core.types import Box, IndicatorResult, Level, Line, Marker, Polygon
from tlab.viz import labels_tr as tr
from tlab.viz.report_text import build_summary_lines
from tlab.viz.themes import (
    DARK_TERMINAL,
    LIGHT_ANALYSIS,
    Theme,
    fib_color,
    fill_color,
    line_color,
    resolve_theme,
    with_alpha,
)


def render(
    result: IndicatorResult,
    df: pd.DataFrame | None = None,
    *,
    theme: Theme | str | None = "auto",
    last_n: int | None = None,
    declutter: bool = True,
) -> go.Figure:
    """`result`ı çizer. `df`: fiyat serisi (pair modu HARİÇ zorunlu — mum
    grafiği ve harmonik/yapı primitiflerinin x eksenini belirler).

    `last_n`: `None` (varsayılan) = OTOMATİK — `harmonic.*` için en güncel
    adayın kendi zaman aralığına yakınlaştırır (bkz. `_harmonic_auto_
    window_start`), diğerleri için sabit `_DEFAULT_LAST_N` (250) bar.
    `0` = tüm geçmiş. `N>0` = tam olarak son N bar.

    `declutter` (varsayılan AÇIK): gerçek çok-yıllık/gürültülü veride aynı
    stildeki DÜZİNELERCE Level/Box/Line/Marker (ör. her ABC üçlüsünün 8
    fib seviyesi, her harmonik adayın PRZ etiketleri, her trendline
    adayının "(Temas:N)" yazısı) üst üste binip grafiği okunmaz hâle
    getiriyordu (Faz 7 sonrası kullanıcı geri bildirimiyle bulundu — bkz.
    `_declutter_levels`/`_latest_label_keys`). Bu AÇIKKEN yalnızca her
    "stil grubu"nun EN GÜNCEL örneği tam etiketlenir; daha eskiler şekil
    olarak (çizgi/kutu/üçgen) hâlâ çizilir, yalnızca metin/etiket
    yığılması bastırılır — hiçbir veri gizlenmez, yalnızca metin
    gösterimi seçicileştirilir. `declutter=False` ile eski (tam) davranışa
    dönülebilir (`tlab plot --show-all`)."""
    if result.indicator.startswith("pair."):
        resolved = resolve_theme(theme, default=DARK_TERMINAL)
        return _render_pair(result, resolved, last_n)

    if df is None:
        raise ValueError(f"'{result.indicator}' için render() df gerektirir")
    resolved = resolve_theme(theme, default=LIGHT_ANALYSIS)
    return _render_price_based(result, df, resolved, last_n, declutter)


# ------------------------------------------------------------------ ortak --


_DEFAULT_WIDTH = 1600


@dataclass(frozen=True)
class _Header:
    """Masthead için önceden biçimlendirilmiş metin alanları — `_draw_header`
    bunları `xref/yref="paper"` annotation'larla aracı-kurum-raporu tarzı bir
    üst şerit olarak çizer (eski tek satırlık `title=` YERİNE). Burada HİÇBİR
    teknik hesap yapılmaz — yalnızca zaten `IndicatorResult`/`df`'de mevcut
    değerlerin (son kapanış, önceki kapanış, `last_state`) metne çevrilmesi
    (biçimlendirme, bkz. görev kısıtı: son fiyat/yüzde değişim gibi basit
    OHLC aritmetiği ihlal SAYILMAZ)."""

    symbol: str
    subtitle: str
    value_str: str
    change_str: str | None = None
    change_positive: bool | None = None
    highlighted: bool = False
    date_str: str = ""


_MARGIN_L = 56
_MARGIN_R = 116
_MARGIN_T = 112
_MARGIN_B = 60
# Masthead/dipnot, `yref="paper"` (0..1 = yalnızca ÇİZİM alanı, kenar
# boşlukları HARİÇ) üzerinden `y>1`/`y<0` ile üst/alt kenar boşluğuna taşan
# annotation/shape'lerle çizilir. Bu fraksiyon, TOPLAM figür yüksekliğine
# göre değil yalnızca çizim alanının (height - t - b) yüksekliğine göre
# ölçeklenir — bu yüzden SABİT bir `y=1.2` gibi bir değer, alt-panelli
# (hacim/MACD) uzun bir figürde (çizim alanı büyük → aynı fraksiyon çok daha
# fazla piksele karşılık gelir) kenar boşluğunun DIŞINA taşıp görünmez
# oluyordu (gerçek render ile bulunan bir hata — ör. `structure.
# price_structure`'da 2 alt panel varken masthead'in sembol/fiyat satırı
# hiç görünmüyordu). Bunun yerine SABİT bir piksel ofseti (`_HEADER_ROW1_PX`
# vb.) hesaplanıp `_apply_layout` içinde figüre özgü paper-fraksiyonuna
# çevrilir — böylece masthead'in ekrandaki piksel konumu figür
# yüksekliğinden BAĞIMSIZ, her zaman `_MARGIN_T`/`_MARGIN_B` içinde kalır.
_HEADER_ROW1_PX = 46.0
_HEADER_ROW2_PX = 18.0
_HEADER_RULE_PX = 8.0
_FOOTER_PX = 32.0
_FOOTER_TEXT = "Yalnızca teknik analiz amaçlıdır, yatırım tavsiyesi değildir — tlab"


def _apply_layout(
    fig: go.Figure, theme: Theme, header: _Header, height: int, width: int = _DEFAULT_WIDTH,
) -> None:
    """Jenerik/harmonik (`light_analysis`) mod için ortak "aracı kurum
    raporu" masthead/kart/dipnot çerçevesi. **Pair modu (2026-08-29'dan
    itibaren) BUNU KULLANMAZ** — kullanıcı bu paylaşılan tasarımı pair
    grafiği için reddetti, kendi ayrık `_apply_pair_layout`/`_draw_pair_
    header`'ı var (bkz. `_render_pair`). Bu fonksiyon yalnızca `_render_
    price_based`'in çağırdığı hâliyle kalmalı; pair'e ÖZGÜ hiçbir dal
    eklenmemeli."""
    margin_t = _MARGIN_T
    fig.update_layout(
        paper_bgcolor=theme.page_bg,
        plot_bgcolor=theme.bg,
        font=dict(color=theme.text, family=theme.font, size=11),
        height=height,
        width=width,
        # r: bazı Level etiketleri (ör. "Fib Geri Çekilme") en son bara
        # (x1=last_x, xanchor="left") sabitlenir ve `vp` paneli olmayan
        # (tek kolonlu) grafiklerde bu, figürün SAĞ kenarına dayanıp
        # kırpılıyordu (gerçek veriyle bulunan bir davranış — bkz.
        # `_draw_levels`); `_MARGIN_R` bu tür etiketlere + kart kenar
        # boşluğuna yetecek kadar pay bırakır. t/b, masthead (2 satır +
        # ayraç) ve dipnot şeridi için (bkz. `_draw_header`/`_draw_footer`).
        margin=dict(l=_MARGIN_L, r=_MARGIN_R, t=margin_t, b=_MARGIN_B),
        legend=dict(
            bgcolor=with_alpha(theme.bg, 0.92), bordercolor=theme.border, borderwidth=1,
            font=dict(color=theme.text, size=10),
        ),
        xaxis_rangeslider_visible=False,
        bargap=0.15,
    )
    fig.update_xaxes(gridcolor=theme.grid, zerolinecolor=theme.grid, showspikes=False)
    fig.update_yaxes(gridcolor=theme.grid, zerolinecolor=theme.grid)
    plot_h = max(height - margin_t - _MARGIN_B, 50.0)
    _draw_card_frame(fig, theme)
    _draw_header(fig, theme, header, plot_h)
    _draw_footer(fig, theme, plot_h)


def _draw_card_frame(fig: go.Figure, theme: Theme) -> None:
    """Çizim alanının etrafına ince bir "kart" çerçevesi — `paper_bgcolor`
    (dış "sayfa") üzerinde oturan, kurumsal bir rapor sayfası hissi veren
    TEK ince kenarlık (`theme.border`). Aşırıya kaçmamak için yalnızca bu —
    gölge/döşeme YOK."""
    fig.add_shape(
        type="rect", xref="paper", yref="paper", x0=0.0, x1=1.0, y0=0.0, y1=1.0,
        line=dict(color=theme.border, width=1), fillcolor="rgba(0,0,0,0)", layer="above",
    )


def _draw_header(fig: go.Figure, theme: Theme, h: _Header, plot_h: float) -> None:
    """Aracı-kurum-raporu tarzı üst şerit: sol=sembol (büyük), sağ=değer +
    (varsa) yön-renkli değişim; alt satır sol=kategori/formasyon alt
    başlığı, sağ=üretim tarihi; ince bir marka-rengi (`accent`) ayraç
    çizgisiyle grafikten ayrılır. `plot_h`: bkz. `_HEADER_ROW1_PX` grubu
    docstring'i — piksel ofsetlerini BU figüre özgü paper-fraksiyonuna
    çevirmek için gerekli. Yalnızca `_render_price_based` çağırır — pair
    modunun kendi (çok daha küçük/2-satır) `_draw_pair_header`'ı var."""
    row1_y = 1.0 + _HEADER_ROW1_PX / plot_h
    row2_y = 1.0 + _HEADER_ROW2_PX / plot_h
    rule_y = 1.0 + _HEADER_RULE_PX / plot_h

    change_color = theme.text
    arrow = ""
    if h.change_positive is True:
        change_color, arrow = theme.up, "▲ "
    elif h.change_positive is False:
        change_color, arrow = theme.down, "▼ "
    elif h.highlighted:
        change_color = theme.accent

    value_text = h.value_str if h.change_str is None else f"{h.value_str}   {arrow}{h.change_str}"

    fig.add_annotation(
        x=0.0, y=row1_y, xref="paper", yref="paper", xanchor="left", yanchor="bottom",
        text=f"<b>{h.symbol}</b>", showarrow=False,
        font=dict(family=theme.font, size=21, color=theme.text),
    )
    fig.add_annotation(
        x=1.0, y=row1_y, xref="paper", yref="paper", xanchor="right", yanchor="bottom",
        text=f"<b>{value_text}</b>", showarrow=False,
        font=dict(family=theme.font, size=16, color=change_color),
    )
    fig.add_annotation(
        x=0.0, y=row2_y, xref="paper", yref="paper", xanchor="left", yanchor="bottom",
        text=h.subtitle, showarrow=False,
        font=dict(family=theme.font, size=11, color=theme.muted),
    )
    fig.add_annotation(
        x=1.0, y=row2_y, xref="paper", yref="paper", xanchor="right", yanchor="bottom",
        text=f"Üretim: {h.date_str}", showarrow=False,
        font=dict(family=theme.font, size=10, color=theme.muted),
    )
    fig.add_shape(
        type="line", xref="paper", yref="paper", x0=0.0, x1=1.0, y0=rule_y, y1=rule_y,
        line=dict(color=theme.accent, width=2), layer="above",
    )


def _draw_footer(fig: go.Figure, theme: Theme, plot_h: float) -> None:
    footer_y = -_FOOTER_PX / plot_h
    fig.add_annotation(
        x=0.5, y=footer_y, xref="paper", yref="paper", xanchor="center", yanchor="top",
        text=_FOOTER_TEXT, showarrow=False,
        font=dict(family=theme.font, size=9, color=theme.muted),
    )


def _last_close_change(df: pd.DataFrame | None) -> tuple[float, float] | None:
    """Son kapanış ve BİR ÖNCEKİ bara göre yüzde değişimi döner — ham
    OHLC üzerinde basit görüntüleme aritmetiği (indikatör HESABI değil,
    bkz. görev kısıtı: "son kapanış/periyot % değişimi" formatlama olarak
    açıkça İZİNLİ). `df` yoksa veya tek barlıksa `None`."""
    if df is None or len(df) < 2:
        return None
    last = float(df["close"].iloc[-1])
    prev = float(df["close"].iloc[-2])
    if prev == 0:
        return last, 0.0
    return last, (last - prev) / prev * 100.0


def _category_tr(indicator: str) -> str:
    prefix = indicator.split(".", 1)[0]
    key = "harmonics" if prefix == "harmonic" else prefix
    return tr.INDICATOR_CATEGORY_TR.get(key, prefix.title())


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


_DEFAULT_LAST_N = 250
_HARMONIC_ZOOM_PAD_BARS = 20

# Annotation kaynakları (box/line-uzatma/level) aynı fiyat civarında (ör. bir
# direnç bölgesinin tepesi = POC'a yakın = trendline izdüşümüyle aynı seviye
# — "confluence" bölgesi) sık sık çakışıyordu. Her kaynağa AYRI bir taban
# dikey ofset vermek YETERLİ DEĞİL — kullanıcı geri bildirimiyle (TCELL/
# THYAO/ASELS gerçek verisi, 2026-08-30) bulundu: üç kaynak da (box/level
# TEK bir merdivende, line-uzatma AYRI bir merdivende) kendi listesi
# İÇİNDE çakışmayı önlese de, iki merdiven birbirinden HABERSİZ hesaplandığı
# için bir direnç ÇİZGİSİ projeksiyonu bir direnç BÖLGESİ etiketinin TAM
# ÜSTÜNE denk gelebiliyordu (aynı gerçek destek/direnç seviyesini temsil
# ettikleri için fiyatça yakın olmaları BEKLENEN bir durum, nadir değil).
# Düzeltme: `_stagger_yshifts` artık HER öğenin KENDİ taban ofsetini taşıdığı
# TEK bir birleşik liste alır (bkz. `render()`'daki çağrı) — üç kaynak da
# aynı "cetvel"de, price'a göre sıralı işlenir; taban işareti farklı olsa
# bile (box/level yukarı `+`, line-uzatma aşağı `-`) çakışma kontrolü artık
# TÜM öğeler arasında geçerli, yalnızca aynı kategori içinde değil.
_BOX_YSHIFT_BASE = 10.0
_LINE_EXT_YSHIFT = -24.0
_LEVEL_YSHIFT_BASE = 38.0


def _resolve_window_start(result: IndicatorResult, df: pd.DataFrame, last_n: int | None) -> int:
    """Görünür pencerenin BAŞLANGIÇ bar indeksini belirler.

    `last_n == 0`: tüm geçmiş (`--show-all`/`--last-n 0`). `last_n > 0`:
    tam olarak o kadar bar. `last_n is None` (varsayılan/otomatik):
    `harmonic.*` için EN GÜNCEL adayın kendi zaman aralığına otomatik
    yakınlaştırır (aksi halde bir formasyonun üçgeni yıllarca geçmiş
    içinde tek pikselik bir çizgiye düşer — kullanıcı geri bildirimiyle
    bulundu); diğerleri için sabit `_DEFAULT_LAST_N` bar."""
    n = len(df)
    if last_n == 0:
        return 0
    if last_n:
        return max(0, n - last_n)
    if result.indicator.startswith("harmonic."):
        return _harmonic_auto_window_start(result, df)
    return max(0, n - _DEFAULT_LAST_N)


def _harmonic_auto_window_start(result: IndicatorResult, df: pd.DataFrame) -> int:
    """En son eklenen adayın (xab+bcd — aynı adayın iki poligonu ardışık
    eklenir, bkz. `scanner_indicator.py`) X noktasından `_HARMONIC_ZOOM_PAD_
    BARS` kadar önce başlayan pencereyi döner. Aday yoksa varsayılan
    pencereye düşer."""
    if not result.polygons:
        return max(0, len(df) - _DEFAULT_LAST_N)
    recent = result.polygons[-2:]
    earliest_t = min(pt[0] for poly in recent for pt in poly.points)
    try:
        idx = df.index.get_loc(earliest_t)
    except KeyError:
        idx = 0
    if not isinstance(idx, int):
        idx = 0
    return max(0, idx - _HARMONIC_ZOOM_PAD_BARS)


def _right_edge_cutoff(df: pd.DataFrame, window_start_idx: int) -> datetime:
    """VP paneli varken sağ kenara yakın box/level etiketlerinin komşu
    panele taşmasını önlemek için kullanılan eşik zaman damgası — bkz.
    `_render_price_based`'deki çağrı yeri ve `_draw_boxes`/`_draw_levels`.
    Görünür pencerenin (yalnızca `window_start_idx`'ten sonrası) son %20'lik
    dilimindeki HERHANGİ bir nokta bu eşiğin ötesinde sayılır."""
    visible = df.index[window_start_idx:]
    if len(visible) == 0:
        return df.index[-1]
    pos = min(max(0, int(len(visible) * 0.80)), len(visible) - 1)
    return visible[pos]


def _visible_price_bounds(df: pd.DataFrame, window_start_idx: int) -> tuple[float, float] | None:
    """Görünür pencerenin PADDED fiyat aralığı — `_sync_price_yaxis`'in
    ekseni ayarlarken kullandığı AYNI formül, tek doğru kaynak burası
    (`_stagger_yshifts`'in `price_bounds`'ı da BUNU kullanır — bir etiketin
    fanlanırken taştığı "sınır", ekranda GERÇEKTEN görünen y-ekseni
    aralığıyla AYNI olmalı, aksi halde etiket "sınır içinde" sanılıp yine de
    görünmez bir bölgeye (margin/masthead) taşabilir)."""
    visible = df.iloc[window_start_idx:]
    if visible.empty:
        return None
    low, high = float(visible["low"].min()), float(visible["high"].max())
    pad = (high - low) * 0.05 or 1.0
    return (low - pad, high + pad)


def _sync_price_yaxis(
    fig: go.Figure, df: pd.DataFrame, window_start_idx: int, has_vp: bool
) -> None:
    """Ana panel ile sağ hacim-profili panelinin y-eksenini (fiyat) AYNI
    aralığa sabitler — aksi halde vp paneli kendi (genelde çok daha dar)
    penceresine göre otomatik ölçeklenip iki panel görsel olarak KOPUK
    görünüyordu (Görsel 2 referansında ikisi hizalı — kullanıcı geri
    bildirimiyle bulundu)."""
    bounds = _visible_price_bounds(df, window_start_idx)
    if bounds is None:
        return
    y_range = list(bounds)
    fig.update_yaxes(range=y_range, row=1, col=1)
    if has_vp:
        fig.update_yaxes(range=y_range, row=1, col=2)


# ------------------------------------------------------------ jenerik mod --


def _render_price_based(
    result: IndicatorResult, df: pd.DataFrame, theme: Theme, last_n: int | None,
    declutter: bool = True,
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
        main_h = 1.0
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

    levels = _declutter_levels(result.levels) if declutter else result.levels
    boxes, lines = result.boxes, result.lines
    if declutter:
        lines = _cap_frozen_channels(lines)
    markers = [m for m in result.markers if m.kind != "macd_cross"]
    latest_box_t0 = (
        _latest_per_group(boxes, lambda b: b.style, lambda b: b.t0) if declutter else None
    )
    latest_line_end = (
        _latest_per_group(lines, lambda ln: ln.style, lambda ln: ln.points[-1][0])
        if declutter else None
    )

    # Etiket çakışması (yshift fan-out) eşiği, TAM geçmişin fiyat aralığı
    # değil GÖRÜNÜR pencerenin aralığı üzerinden hesaplanır — aksi halde
    # (ör. yıllarca eski/uçuk fiyatlı barlar dahil edilince) eşik gerçek
    # ekran-piksel yoğunluğuna göre çok küçük kalıp fan-out'u tetiklemiyordu.
    window_start_idx = _resolve_window_start(result, df, last_n)
    visible = df.iloc[window_start_idx:]
    visible_price_range = (
        float(visible["high"].max() - visible["low"].min()) if not visible.empty else 0.0
    ) or 1.0
    # Etiket çakışma-tespiti PİKSEL cinsinden yapılmalı (bkz. `_stagger_
    # yshifts` docstring'i) — bunun için ana panelin GERÇEK piksel
    # yüksekliğini (`_apply_layout`'un kullanacağı toplam figür yüksekliğiyle
    # AYNI formül) fiyat aralığına bölerek kaba bir "piksel/fiyat-birimi"
    # oranı tahmin ediyoruz (kenar boşlukları/panel aralıkları için ~90px
    # düşülüyor — kesin değil ama fan-out tetiklemesi için yeterince yakın).
    total_height = 600 + 180 * n_sub
    main_row_px = max((total_height - 90) * main_h, 50.0)
    px_per_unit = main_row_px / visible_price_range if visible_price_range else 1.0

    # Box-etiketleri (Direnç/Destek Bölgesi, Konsolidasyon) ve Level-etiketleri
    # (POC/VAH/VAL) genellikle AYNI fiyat civarında yoğunlaşır ("confluence"
    # bölgesi) — iki kategoriyi AYRI şeritlerde (sabit taban ofsetleriyle)
    # fanlamak, bir kategori kendi kümesinde büyürken diğerinin şeridine
    # girip yeniden çakışmasına yol açabiliyordu (gerçek veriyle bulunan bir
    # davranış). Bunun yerine ikisi TEK bir ortak merdivende (aynı `_stagger_
    # yshifts` çağrısı, karışık liste) fanlanır — genel bir yerleşim çözücü
    # DEĞİL, hâlâ tek geçişli açgözlü bir sezgi, ama artık iki kategori
    # arasında da minimum ayrımı garanti eder.
    labeled_boxes = [
        b for b in boxes if latest_box_t0 is None or b.t0 == latest_box_t0.get(b.style)
    ]
    # Line-uzatma izdüşümleri de AYNI birleşik merdivene katılır (2026-08-30
    # düzeltmesi, bkz. `_stagger_yshifts` docstring'i) — bir direnç ÇİZGİSİ
    # projeksiyonu bir direnç/destek BÖLGESİ ya da POC/VAH/VAL etiketiyle
    # aynı fiyat civarına düşebiliyordu (üçü de aynı gerçek seviyeyi temsil
    # ettiği için beklenen bir durum), önceden bu üçüncü kaynak AYRI/
    # habersiz bir merdivende hesaplanıyordu.
    line_extensions = _line_extensions(lines, df)
    labeled_line_ext = [
        (ln, proj) for ln, (_et, proj) in line_extensions.items()
        if latest_line_end is None or ln.points[-1][0] == latest_line_end.get(ln.style)
    ]
    box_level_yshifts = _stagger_yshifts(
        [(b, b.high, _BOX_YSHIFT_BASE) for b in labeled_boxes]
        + [(lv, lv.price, _BOX_YSHIFT_BASE) for lv in levels]
        + [(ln, proj, _LINE_EXT_YSHIFT) for ln, proj in labeled_line_ext],
        px_per_unit=px_per_unit, step=14.0,
        price_bounds=_visible_price_bounds(df, window_start_idx),
    )
    # `has_vp` sağdaki hacim-profili panelini de içeren grafiklerde, sağ
    # kenara YAKIN box/level etiketleri (ör. POC/VAH/VAL — `Level.end`
    # HER ZAMAN `None`, yani her zaman `last_x`'e sabit, bkz. `_draw_
    # levels`) `xanchor="left"` ile sağa doğru büyüyünce komşu vp paneline
    # ve onun y-ekseni tik yazısına BİNİYORDU (gerçek veriyle bulunan bir
    # çakışma — bkz. CLAUDE.md). `edge_cutoff`, görünür pencerenin son
    # %20'lik dilimini işaretler; bu dilimdeki etiketler `_draw_boxes`/
    # `_draw_levels` içinde otomatik `xanchor="right"`e çevrilir (metin
    # SOLA büyür, panelin İÇİNDE kalır).
    edge_cutoff = _right_edge_cutoff(df, window_start_idx)

    _draw_boxes(
        fig, boxes, theme, row=1, col=1, latest_t0=latest_box_t0,
        px_per_unit=px_per_unit, yshifts=box_level_yshifts,
        has_vp=has_vp, edge_cutoff=edge_cutoff,
    )
    _draw_polygons(fig, result.polygons, theme, row=1, col=1)
    _draw_harmonic_vertices(fig, result, theme, row=1, col=1, declutter=declutter)
    _draw_lines(
        fig, lines, df, theme, row=1, col=1, latest_end=latest_line_end,
        px_per_unit=px_per_unit, yshifts=box_level_yshifts,
    )
    _draw_levels(
        fig, levels, df, theme, row=1, col=1, px_per_unit=px_per_unit,
        yshifts=box_level_yshifts, has_vp=has_vp, edge_cutoff=edge_cutoff,
    )
    _draw_markers(fig, markers, theme, row=1, col=1, declutter=declutter)

    for i, name in enumerate(sub_names, start=2):
        _draw_series_panel(fig, result, name, layout[name], theme, row=i, col=1, df=df)

    if has_vp:
        _draw_volume_profile(fig, result, theme, row=1, col=2)

    for r in range(1, n_rows + 1):
        fig.update_xaxes(showticklabels=(r == n_rows), row=r, col=1)

    if window_start_idx > 0:
        fig.update_xaxes(range=[_x(df.index[window_start_idx]), _x(df.index[-1])])
    _sync_price_yaxis(fig, df, window_start_idx, has_vp)

    header = _price_header(result, df)
    _apply_layout(fig, theme, header, height=600 + 180 * n_sub)
    return fig


def _build_subtitle(result: IndicatorResult) -> str:
    """Masthead'in ikinci (alt başlık) satırı — formasyon/ekol veya
    indikatör adının okunur biçimi. Sembol BURADA tekrarlanmaz (`_Header.
    symbol` ayrı, birinci satırda büyük puntoyla zaten var)."""
    if result.indicator.startswith("harmonic."):
        school = result.indicator.split(".", 1)[1]
        if not result.last_state:
            return f"{school.title()} ekolü — eşleşen formasyon yok"
        _pid, info = next(reversed(result.last_state.items()))
        pattern = str(info["pattern"]).replace("_", " ").title()
        direction_tr = tr.tr_direction(info["direction"])
        state_tr = tr.tr_state(info["state"])
        return (
            f"{pattern} Formasyonu ({direction_tr}) [{state_tr}] "
            f"— Sistem: {school.title()} — {len(result.last_state)} eşleşme"
        )
    return result.indicator.split(".", 1)[-1].replace("_", " ").title()


def _price_header(result: IndicatorResult, df: pd.DataFrame) -> _Header:
    """Fiyat-tabanlı (jenerik/harmonik) mod için masthead içeriği — son
    kapanış + bir-önceki-bara-göre % değişim (biçimlendirme, bkz.
    `_last_close_change` docstring'i), kategori (`labels_tr.
    INDICATOR_CATEGORY_TR`) + formasyon/indikatör alt başlığı, üretim
    tarihi (bugün — grafiğin ÜRETİLDİĞİ an, verinin son bar tarihi
    DEĞİL)."""
    subtitle = f"{_category_tr(result.indicator)} — {_build_subtitle(result)}"
    change = _last_close_change(df)
    if change is None:
        value_str, change_str, positive = "—", None, None
    else:
        last, pct = change
        value_str, change_str, positive = f"{last:.2f}", f"{pct:+.2f}%", pct >= 0
    return _Header(
        symbol=result.symbol or "?", subtitle=subtitle, value_str=value_str,
        change_str=change_str, change_positive=positive, date_str=_fmt_date(datetime.now()),
    )


def _latest_per_group(items: list, group_key, time_key) -> dict:
    """`items`ı `group_key(item)`e göre gruplar, her grubun EN BÜYÜK
    `time_key(item)` değerini döner (`{grup: en_yeni_zaman}`). Declutter
    modunda yalnızca bu "en yeni" zamana sahip öğe tam etiketlenir —
    diğerleri (aynı stilin eski/çözülmüş kopyaları) şekil olarak
    kalır, metinleri bastırılır."""
    best: dict = {}
    for it in items:
        g, t = group_key(it), time_key(it)
        if g not in best or t > best[g]:
            best[g] = t
    return best


_MAX_FROZEN_CHANNELS = 2


def _cap_frozen_channels(lines: list[Line]) -> list[Line]:
    """`trend.weekly_channel`'ın `channel_frozen` çizgileri HER dokunuş/kırılım
    sinyalinde bir çift (alt+üst) üretir (bkz. weekly_channel.py docstring'i)
    — dar bir `n` penceresiyle çok-yıllık veride bu, `_latest_per_group`'un
    yalnızca ETİKETİ kısıtlayan mekanizmasından (şekiller yine de hepsi
    çizilir) etkilenmeyen, onlarca üst üste binen çizgi anlamına geliyordu
    (gerçek TCELL verisiyle bulunan bir "curcuna" — harmonik marker'ların
    `_MAX_HARMONIC_MARKERS` ile çözdüğü sorunla AYNI kategori, ama çizgi
    STİLİ tek başına ayırt edici olmadığı için şekil düzeyinde kesim
    gerekiyor). Yalnızca EN GÜNCEL `_MAX_FROZEN_CHANNELS` dondurulmuş kanalın
    şekli (alt+üst çizgi çifti) tutulur; diğer stiller etkilenmez."""
    frozen = [ln for ln in lines if ln.style == "channel_frozen"]
    if len(frozen) <= _MAX_FROZEN_CHANNELS * 2:
        return lines
    keep_times = sorted({ln.points[-1][0] for ln in frozen})[-_MAX_FROZEN_CHANNELS:]
    keep_set = set(keep_times)
    return [ln for ln in lines if ln.style != "channel_frozen" or ln.points[-1][0] in keep_set]


_STAGGER_TRIGGER_PX = 18.0  # ~ tek satır 11px yazı için "görsel olarak değecek" eşik
# Bir "confluence" bölgesinde ÇOK SAYIDA öğe (ör. birleşik rapor grafiğinde
# aynı anda 3 AB=CD hedefi + POC/VAH/VAL + bölge/trendline etiketleri hep aynı
# fiyat aralığında) birikirse, sınırsız büyüyen `n` offset'i grafiğin üst
# kenar boşluğuna/masthead'e kadar taşabiliyordu (gerçek TCELL verisiyle
# `structure.report` birleşik grafiğinde bulunan bir davranış — bkz. CLAUDE.md
# 2026-08-30 kaydı). Bu üst sınır aşılınca fanlama DURUR (kabul edilebilir bir
# artık örtüşme pahasına) — etiketin plot alanının DIŞINA taşmasındansa aynı
# bölgede birkaç etiketin hafifçe üst üste binmesi tercih edilir.
_STAGGER_MAX_OFFSET_PX = 100.0


def _stagger_yshifts(
    items: list[tuple[object, float, float]], px_per_unit: float, step: float = 10.0,
    price_bounds: tuple[float, float] | None = None,
) -> dict[object, float]:
    """Fiyatça birbirine YAKIN öğelerin etiketleri aynı pikselde üst üste
    biner (ör. bir direnç bölgesinin tepesi + bir trendline izdüşümü + bir
    fib/PRZ seviyesi hep aynı fiyatın civarında — gerçek çok-yıllık veride
    konsolidasyon bölgelerinde `_draw_boxes`'ın farklı stildeki kutuları da
    aynı sorunu yaşıyordu). Genel bir yerleşim çözücü DEĞİL, tek geçişli
    açgözlü bir "cetvel" sezgisi (görev metninin istediği basitlik düzeyi):
    her `(item, price, base)` üçlüsü KENDİ taban ofsetini taşır (ör. kutu/
    seviye etiketleri hep yukarı `+`, çizgi-uzatma etiketleri hep aşağı `-`
    büyür — `base`in işareti yönü belirler); `price`e göre sıralanır, her
    öğeye `base + yön*n*step` (n=0,1,2,…) biçiminde artan bir ofset atanır;
    `n`, bu öğenin EKRAN konumunu (`price + offset/px_per_unit`) bir ÖNCEKİ
    öğenin (zaten atanmış) ekran konumundan en az `_STAGGER_TRIGGER_PX`
    piksel uzaklaştıracak KADAR büyütülür. `item` (ilk öğe) HASHLENEBİLİR
    olmalı (`Level`/`Box`/`Line` frozen dataclass'ları).

    **2026-08-30 genelleme** (kullanıcı geri bildirimi, TCELL/THYAO/ASELS
    gerçek verisi): eskiden TEK bir `base` tüm listeye uygulanıyordu — bu,
    box+level'ı BİRLEŞTİREN çağrının kendi içinde çakışmayı önlerken, ayrı
    çağrılan line-uzatma merdiveniyle HİÇ haberleşmiyordu; bir direnç
    ÇİZGİSİ projeksiyonu bir direnç BÖLGESİ etiketinin ÜSTÜNE biniyordu
    (aynı seviyeyi temsil ettikleri için fiyatça yakın olmaları beklenen
    bir durum). Artık HER üç kaynak da (`render()`'da) TEK bir birleşik
    listede, kendi taban ofsetleriyle bu fonksiyona verilir — çakışma
    kontrolü artık kategoriler ARASI da geçerli.

    ÖNEMLİ — `n` hiçbir zaman KÜÇÜLTÜLMEZ (öğeler arası "cetvel" ilerledikçe
    yalnızca büyür, sıfırlanmaz): aksi halde (her öğe kendi `n=0`'ından
    yeniden arasaydı) bir SONRAKİ öğe bir ÖNCEKİNİN aldığı büyük ofsetten
    "kurtulup" küçük bir ofsetle yetinebiliyor, bu da onu ÖNCEKİNİN
    öncesindeki (bitişik olmayan) başka bir öğeyle çakıştırabiliyordu
    (gerçek veriyle bulunan bir davranış — `n` hiç küçülmediği için
    ekran konumları `price` sırasıyla TUTARLI biçimde artar/azalır, bu da
    "yalnızca bir öncekiyle kıyasla" kontrolünü TÜM çiftler için geçerli
    kılar, yalnızca komşular için değil).

    `price_bounds` (opsiyonel, `(alt, üst)`): verilirse fanlama, öğenin EKRAN
    konumu bu aralığın DIŞINA taşacaksa durur (kabul edilebilir bir örtüşme
    pahasına) — `_STAGGER_MAX_OFFSET_PX`'in SABİT piksel tavanı tek başına
    YETERSİZDİ: gerçek THYAO verisiyle bulundu (2026-08-30) — hisse fiyatı
    yüksek/geniş bir aralıkta (ör. 260-360) olduğunda AYNI piksel bütçesi çok
    daha FAZLA fiyat birimine karşılık geliyor (`px_per_unit` küçük), bu da
    üst sınıra rağmen bir etiketin (VAH) grafiğin görünür fiyat aralığının
    tamamen DIŞINA, masthead'in bile üstüne taşmasına yol açtı. Asıl doğru
    sınır SABİT piksel DEĞİL, o öğenin görünür ekseni AŞMAMASI — bu yüzden
    `price_bounds` (görünür y-ekseni aralığı, `_sync_price_yaxis`'teki AYNI
    pad'li hesap) birincil sınır, `_STAGGER_MAX_OFFSET_PX` yalnızca `price_
    bounds` verilmediğinde (ör. testler/`yshifts=None` fallback yolu) devreye
    giren bir yedek."""
    min_gap = _STAGGER_TRIGGER_PX / px_per_unit if px_per_unit > 0 else 0.0
    # `n=0` (henüz hiç fanlanmamış) EKRAN konumuna göre sıralanır — SALT
    # `price`e göre sıralamak (eski davranış) yalnızca TÜM öğeler AYNI
    # işaretli `base` taşıdığında güvenliydi (o zaman `price` sırası =
    # ekran konumu sırası). Artık kutu/seviye (+base, yukarı büyür) VE
    # line-uzatma (-base, aşağı büyür) TEK listede karışabildiği için
    # (2026-08-30 genelleme) `price` sırası ekran konumu sırasını GARANTİ
    # ETMEZ — ör. `price=344.5, base=-24` öğesinin n=0 ekran konumu,
    # `price=341.88, base=+10` öğesininkinden DAHA DÜŞÜK olabilir (raw
    # price daha büyük olsa bile). Yalnızca `price`e göre sıralayıp bunu
    # gözden kaçırmak, ASLA bitişik-öncekiyle karşılaştırılmayan (çünkü
    # sırada yanlış yerde duran) gizli çakışmalara yol açıyordu — gerçek
    # ASELS verisiyle bulunan bir davranış (VAL/Destek Bölgesi/Destek
    # Temas-N üçlüsü hâlâ üst üste biniyordu).
    order = sorted(items, key=lambda kv: kv[1] + (kv[2] / px_per_unit if px_per_unit > 0 else 0.0))
    yshifts: dict[object, float] = {}
    n = 0
    prev_effective: float | None = None
    for item, price, base in order:
        direction = 1.0 if base >= 0 else -1.0
        while True:
            offset = base + direction * n * step
            effective = price + (offset / px_per_unit if px_per_unit > 0 else 0.0)
            if price_bounds is not None:
                lo, hi = price_bounds
                out_of_bounds = effective > hi if direction > 0 else effective < lo
                if out_of_bounds:
                    # Paylaşılan `n` sayacı ÖNCEKİ öğelerden ZATEN yüksek
                    # gelmiş olabilir (bkz. "n hiç küçülmez" ilkesi) — TEK
                    # bir geri adım yetmeyebilir, sınırın İÇİNE dönene (ya da
                    # n=0'a) kadar geri sarılır (gerçek THYAO verisiyle
                    # bulunan bir hata: tek adımlık geri dönüş VAH'ı 377'den
                    # 375'e indiriyordu, hâlâ 360'lık sınırın ÇOK dışında).
                    while n > 0 and out_of_bounds:
                        n -= 1
                        offset = base + direction * n * step
                        effective = price + (offset / px_per_unit if px_per_unit > 0 else 0.0)
                        out_of_bounds = effective > hi if direction > 0 else effective < lo
                    break
            elif abs(offset) >= _STAGGER_MAX_OFFSET_PX:
                break  # sabit yedek sınır — bkz. `price_bounds` docstring notu
            if prev_effective is None or abs(effective - prev_effective) >= min_gap:
                break
            n += 1
        yshifts[item] = float(offset)
        prev_effective = effective
    return yshifts


def _draw_boxes(
    fig: go.Figure, boxes: list[Box], theme: Theme, row: int, col: int,
    latest_t0: dict | None = None, px_per_unit: float = 1.0,
    yshifts: dict[object, float] | None = None,
    has_vp: bool = False, edge_cutoff: datetime | None = None,
) -> None:
    labeled = [b for b in boxes if latest_t0 is None or b.t0 == latest_t0.get(b.style)]
    # Kutu etiketleri HER ZAMAN yukarı (+) yönde fanlanır — `_BOX_YSHIFT_
    # BASE` pozitif olduğu için `_stagger_yshifts` tek yönde büyür, ASLA
    # `_LINE_EXT_YSHIFT`in negatif "şeridi"ne (uzatma etiketlerinin yaşadığı
    # bölge) düşmez. `yshifts` verilmezse (ör. doğrudan/testte çağrılırsa)
    # kendi başına, yalnızca kutular arasında hesaplar — `_render_price_
    # based` normalde Level'larla BİRLEŞTİRİLMİŞ bir sözlük geçirir (bkz.
    # çağrı yeri).
    if yshifts is None:
        yshifts = _stagger_yshifts(
            [(b, b.high, _BOX_YSHIFT_BASE) for b in labeled], px_per_unit=px_per_unit, step=10.0,
        )
    for b in boxes:
        dash = "dot" if b.style == "range_box" else "solid"
        fig.add_shape(
            type="rect", x0=_x(b.t0), x1=_x(b.t1), y0=b.low, y1=b.high,
            fillcolor=fill_color(theme, b.style, 0.18),
            line=dict(color=line_color(theme, b.style), width=1, dash=dash),
            row=row, col=col,
        )
        if latest_t0 is not None and b.t0 != latest_t0.get(b.style):
            continue  # declutter: yalnızca bu stilin EN GÜNCEL kutusu etiketlenir
        # Sağ kenara yakın kutular (ör. yeni oluşmuş bir Direnç/Destek
        # Bölgesi) VP paneli varken sağa doğru büyüyünce panele taşıyordu —
        # bkz. `_right_edge_cutoff` çağrı yeri. Yalnızca ANCHOR yönü
        # değişir, konum (b.t0) AYNI kalır.
        near_edge = has_vp and edge_cutoff is not None and b.t0 >= edge_cutoff
        fig.add_annotation(
            x=_x(b.t0), y=b.high, text=tr.tr_style(b.style), showarrow=False,
            font=dict(size=11, color=line_color(theme, b.style)),
            xanchor="right" if near_edge else "left", yanchor="bottom",
            yshift=yshifts.get(b, _BOX_YSHIFT_BASE), row=row, col=col,
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


def _draw_harmonic_vertices(
    fig: go.Figure, result: IndicatorResult, theme: Theme, row: int, col: int,
    declutter: bool = True,
) -> None:
    """XAB/BCD üçgenlerinin gerçek fiyat pivotlarına (X, A, B, C) küçük bir
    nokta + kısa harf etiketi ekler — önceden yalnızca son D etiketi vardı,
    referans görselde ise (Görsel 5/6) A/C açıkça, X/B örtük olarak
    işaretli. D noktası burada TEKRAR etiketlenmez (`_draw_markers` zaten
    "D: fiyat [DURUM]" kutusunu çiziyor; `bcd` poligonunun 3. noktası zaten
    gerçek bir pivot değil, `prz.center`).

    `pid` (ör. `f"{school}_{pattern}_{pattern_id}"`) polygon etiketinin
    (`{pid}_xab` / `{pid}_bcd`, bkz. `scanner_indicator.py`) son ekini
    kırparak çıkarılır; hangi pid'lerin "en güncel" sayıldığı `_draw_
    markers`'daki `visible_harmonic` seçimiyle AYNI mantıkla belirlenir
    (harmonik Marker'lar `pid` taşımaz, ama `HarmonicIndicator.compute()`
    her aday için TAM OLARAK bir Marker'ı `last_state[pid]` ile aynı
    sırada ekler — bu yüzden `last_state` anahtarları ile ham (sıralanmamış)
    harmonik Marker listesi indeks bazında eşleşir)."""
    if not result.polygons:
        return

    harmonic_markers = [m for m in result.markers if m.kind.startswith("harmonic_")]
    pids = list(result.last_state.keys())
    recent_pids: set[str] | None = None
    if declutter and pids and len(pids) == len(harmonic_markers):
        paired = sorted(
            zip(pids, harmonic_markers, strict=True), key=lambda pm: pm[1].t, reverse=True
        )
        recent_pids = {pid for pid, _m in paired[:_MAX_HARMONIC_MARKERS]}

    by_pid: dict[str, dict[str, Polygon]] = {}
    for p in result.polygons:
        if p.label.endswith("_xab"):
            by_pid.setdefault(p.label[: -len("_xab")], {})["xab"] = p
        elif p.label.endswith("_bcd"):
            by_pid.setdefault(p.label[: -len("_bcd")], {})["bcd"] = p

    for pid, parts in by_pid.items():
        if recent_pids is not None and pid not in recent_pids:
            continue
        xab, bcd = parts.get("xab"), parts.get("bcd")
        vertices: list[tuple[object, float, str]] = []
        if xab is not None and len(xab.points) >= 3:
            (tx, px), (ta, pa), (tb, pb) = xab.points[0], xab.points[1], xab.points[2]
            vertices += [(tx, px, "X"), (ta, pa, "A"), (tb, pb, "B")]
        if bcd is not None and len(bcd.points) >= 2:
            tc, pc = bcd.points[1]
            vertices.append((tc, pc, "C"))
        if not vertices:
            continue
        style = xab.style if xab is not None else bcd.style if bcd is not None else "bullish"
        color = line_color(theme, style)
        fig.add_trace(
            go.Scatter(
                x=[_x(t) for t, _p, _lbl in vertices], y=[p for _t, p, _lbl in vertices],
                mode="markers",
                marker=dict(size=6, color=color, line=dict(width=1, color=theme.bg)),
                showlegend=False, hoverinfo="skip",
            ),
            row=row, col=col,
        )
        for t, price, label in vertices:
            fig.add_annotation(
                # Etiket rengi KASITLI OLARAK nokta/üçgen rengiyle (yön-renkli
                # yeşil/kırmızı) AYNI DEĞİL — `theme.text` (nötr, yüksek
                # kontrast) kullanılır: X/B noktaları çoğunlukla yoğun bir
                # mum kümesinin TAM ORTASINA denk geliyor, yön-renkli metin
                # (ör. yeşil "B", yeşil mumların üstünde) neredeyse görünmez
                # oluyordu (gerçek veriyle bulunan bir davranış). `bgcolor`
                # ile hafif bir "halo" da mumların üstünde okunabilirliği
                # artırıyor.
                x=_x(t), y=price, text=label, showarrow=False,
                font=dict(size=12, color=theme.text, family=theme.font),
                bgcolor=with_alpha(theme.bg, 0.75),
                yshift=14, row=row, col=col,
            )


_DASH_FOR_STYLE = {"dashed": "dash", "dotted": "dot"}

_LABEL_SUFFIX_TR: dict[str, str] = {
    "_xb": "X-B",
    "_xd_envelope": "Hedef Zarfı",
    "_prz_low": "PRZ Alt",
    "_prz_high": "PRZ Üst",
}


def _looks_like_raw_id(label: str) -> bool:
    """`label`, insan için yazılmış kısa/okunur bir etiket DEĞİL de ham bir
    dahili kompozit kimlik gibi mi görünüyor? (ör. harmonik `pid`:
    `f"{school}_{pattern}_{x_idx}_{a_idx}_{b_idx}_{c_idx}"` — boşluksuz,
    çok sayıda alt çizgi taşıyan, indeks yığını). `price_structure.py`/
    `swing_fib_abcd.py`'nin ürettiği ZATEN kısa/anlamlı etiketler
    ("VAH", "POC", "fib_0.618", "Direnç (Temas:6)", "Kırılım 2026-05-08
    (Temas:3)") bu testten YANLIŞLIKLA geçmesin diye eşik bilinçli olarak
    "boşluksuz VE ≥2 alt çizgi" — tek alt çizgili ("fib_0.618", "swing_2")
    ya da boşluklu/parantezli (yukarıdaki Türkçe cümleler) etiketler
    ham kimlik SAYILMAZ."""
    return " " not in label and label.count("_") >= 2


def _display_text(label: str, style: str) -> str:
    """`Line.label`/`Level.label` bazı indikatörlerde (özellikle harmonik
    tarayıcı) eşleştirme/declutter amacıyla taşınan UZUN kompozit bir kimlik
    olabilir (ör. `f"{school}_{pattern}_{pattern_id}_prz_low"`) — bu ASLA
    ekranda görünmemeli. Ama AYNI alan başka indikatörlerde ZATEN kısa/
    Türkçe/anlamlı bir etiket taşıyor (`"VAH"`, `"POC"`, `"fib_0.618"`,
    `"Direnç (Temas:6)"`) — bunları körü körüne `style`e indirgemek bilgi
    kaybı olurdu (ör. VAH/VAL ikisi de `style="value_area"`, yalnızca
    `label` ayırt eder). Bu yüzden yalnızca (a) bilinen bir ham-kimlik son
    eki (`_LABEL_SUFFIX_TR`) VEYA (b) `_looks_like_raw_id()` ham kimlik
    deseni eşleşirse `style`'dan kısa bir Türkçe metin türetilir; aksi
    halde `label` OLDUĞU GİBİ gösterilir. `.label`'ın kendisi HİÇBİR yerde
    değiştirilmez — yalnızca canvas'a yazılan `text=` bundan türetilir."""
    for suffix, short in _LABEL_SUFFIX_TR.items():
        if label.endswith(suffix):
            return short
    if _looks_like_raw_id(label):
        return tr.tr_style(style)
    return label


def _line_extensions(lines: list[Line], df: pd.DataFrame) -> dict[Line, tuple[object, float]]:
    """`extend_right=True` VE `t1 < last_x` olan her `Line` için (ext_time,
    proj) izdüşüm noktasını hesaplar — `_draw_lines`'ın soluk uzatma
    çizgisini çizmesi VE `render()`'ın bu izdüşümleri box/level'larla AYNI
    birleşik "confluence" merdivenine (`_stagger_yshifts`) katması için
    PAYLAŞILAN TEK kaynak (aynı eğim/uzatma geometrisi iki kez hesaplanmasın,
    ve iki yer FARKLI sonuç üretmesin diye)."""
    last_x = df.index[-1]
    out: dict[Line, tuple[object, float]] = {}
    for ln in lines:
        (t0, p0), (t1, p1) = ln.points[0], ln.points[-1]
        if not (ln.extend_right and t1 < last_x):
            continue
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
        out[ln] = (ext_time, proj)
    return out


def _draw_lines(
    fig: go.Figure, lines: list[Line], df: pd.DataFrame, theme: Theme, row: int, col: int,
    latest_end: dict | None = None, px_per_unit: float = 1.0,
    yshifts: dict[object, float] | None = None,
) -> None:
    extensions = _line_extensions(lines, df)
    # `yshifts` verilmezse (ör. doğrudan/testte çağrılırsa) kendi başına,
    # yalnızca line-uzatmaları arasında hesaplar — `render()` normalde
    # box/level'larla BİRLEŞTİRİLMİŞ tek bir sözlük geçirir (bkz. çağrı yeri
    # ve `_stagger_yshifts` docstring'indeki 2026-08-30 genelleme notu).
    if yshifts is None:
        yshifts = _stagger_yshifts(
            [
                (ln, proj, _LINE_EXT_YSHIFT) for ln, (_et, proj) in extensions.items()
                if latest_end is None or ln.points[-1][0] == latest_end.get(ln.style)
            ],
            px_per_unit=px_per_unit, step=14.0,
        )

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
        ext = extensions.get(ln)
        if ext is None:
            continue
        ext_time, proj = ext
        # Uzatma çizgisi bilinçli olarak SOLUK — bacağın kendisi (yukarıdaki
        # trace) sinyal taşır, uzatma yalnızca "izdüşüm yönü" gösteren
        # yumuşak bir kılavuzdur; parlak/kalın olursa gerçek çizgiyle
        # yarışıp görsel gürültü üretiyordu (kullanıcı geri bildirimi).
        ext_color = with_alpha(theme.muted, 0.6)
        fig.add_trace(
            go.Scatter(
                x=[_x(t1), _x(ext_time)], y=[p1, proj], mode="lines",
                line=dict(color=ext_color, width=1.0, dash="dash"),
                name=f"{ln.label}_uzatma", showlegend=False, hoverinfo="skip",
            ),
            row=row, col=col,
        )
        if latest_end is not None and t1 != latest_end.get(ln.style):
            continue
        fig.add_annotation(
            x=_x(ext_time), y=proj, text=_display_text(ln.label, ln.style),
            showarrow=False, font=dict(size=10, color=theme.muted),
            xanchor="right", yanchor="bottom",
            yshift=yshifts.get(ln, _LINE_EXT_YSHIFT), row=row, col=col,
        )


_LEVEL_DASH = {
    "poc": "solid", "dotted": "dot", "fib_extension": "dot",
    "bullish": "dot", "bearish": "dot",
}


def _declutter_levels(levels: list[Level], keep_recent: int = 1) -> list[Level]:
    """Aynı `style`'daki Level'lar (ör. her ABC üçlüsünün 8'li fib merdiveni,
    her harmonik adayın PRZ üst/alt seviyesi) `start` bazında gruplanır;
    yalnızca EN GÜNCEL `keep_recent` grup(lar) TUTULUR, gerisi TAMAMEN
    ÇIKARILIR. Level'lar Box/Line/Polygon'un aksine tek başına anlamlı
    DEĞİL — "D (hedef): 106.75" yazısı hangi üçlüye ait olduğu bağlamı
    olmadan salt gürültüdür, bu yüzden Box/Line'daki gibi "yalnızca
    etiketi bastır" değil, TAMAMEN gizlemek tercih edildi (Faz 7 sonrası
    kullanıcı geri bildirimiyle: gerçek çok-yıllık veride onlarca çözülmüş
    eski hedef/PRZ üst üste binip grafiği okunmaz kılıyordu). `start=None`
    olan Level'lar (ör. tekil POC/VAH/VAL) HER ZAMAN kalır."""
    by_style: dict[str, list[Level]] = {}
    for lv in levels:
        by_style.setdefault(lv.style, []).append(lv)

    kept: list[Level] = []
    for group in by_style.values():
        starts = sorted({lv.start for lv in group if lv.start is not None}, reverse=True)
        keep = set(starts[:keep_recent])
        kept.extend(lv for lv in group if lv.start is None or lv.start in keep)
    return kept


def _level_color(theme: Theme, lv: Level) -> str:
    if lv.style.startswith("fib_"):
        try:
            ratio = float(lv.label.rsplit("_", 1)[-1])
            return fib_color(theme, ratio)
        except ValueError:
            return theme.gray
    return line_color(theme, lv.style)


def _level_display_text(lv: Level) -> str:
    """Fib seviyeleri için referans ekran görüntüsündeki gibi "oran - fiyat"
    biçimi (ör. "0.618 - 39.83") — yalnızca oranı gösteren eski `fib_0.618`
    yerine, ekstra bir okuma yapmadan (fiyat zaten `lv.price`'ta hazır)."""
    if lv.style.startswith("fib_"):
        try:
            ratio = float(lv.label.rsplit("_", 1)[-1])
            return f"{ratio:g} - {lv.price:.2f}"
        except ValueError:
            pass
    return _display_text(lv.label, lv.style)


def _draw_levels(
    fig: go.Figure, levels: list[Level], df: pd.DataFrame, theme: Theme, row: int, col: int,
    px_per_unit: float = 1.0, yshifts: dict[object, float] | None = None,
    has_vp: bool = False, edge_cutoff: datetime | None = None,
    labeled: set[Level] | None = None,
) -> None:
    """`labeled` (varsayılan `None` = HEPSİ etiketlenir, `_render_price_based`'in
    ORİJİNAL davranışı DEĞİŞMEDİ): verilirse yalnızca bu kümedeki Level'lar
    metin alır, diğerleri şekil (yatay çizgi) olarak çizilmeye devam eder ama
    ETİKETSİZ kalır. Birleşik rapor grafiğinde (`render_structure_report`)
    kullanılır — AB=CD'nin `max_active_targets` kadar hedefi (ör. 3 ayrı oran)
    `structure.price_structure`'ın KENDİ POC/VAH/VAL/fib seviyeleriyle AYNI
    dar fiyat bandında birikince (`_stagger_yshifts`'in "n hiç küçülmez" zincir
    etkisiyle) etiketler grafiğin üst kenar boşluğuna kadar taşabiliyordu
    (gerçek TCELL verisiyle bulunan bir davranış, bkz. CLAUDE.md 2026-08-30) —
    en yakın hedef DIŞINDAKİLER hâlâ çizgi olarak görünür (bilgi kaybı yok),
    yalnızca metin yığılması azalır."""
    first_x, last_x = df.index[0], df.index[-1]
    # Level'lar HER ZAMAN yukarı (+) yönde fanlanır (aynı gerekçe: bkz.
    # `_draw_boxes`), `_LINE_EXT_YSHIFT`in negatif şeridine ASLA düşmez.
    # `yshifts` verilmezse (ör. doğrudan/testte çağrılırsa) kendi başına,
    # yalnızca Level'lar arasında hesaplar — `_render_price_based` normalde
    # Box'larla BİRLEŞTİRİLMİŞ bir sözlük geçirir (bkz. çağrı yeri, iki
    # kategori de AYNI "confluence" bölgesinde toplanabildiği için tek ortak
    # merdivende fanlanmaları gerekiyordu).
    if yshifts is None:
        yshifts = _stagger_yshifts(
            [(lv, lv.price, _LEVEL_YSHIFT_BASE) for lv in levels], px_per_unit=px_per_unit,
            step=10.0,
        )
    for lv in levels:
        x0 = lv.start if lv.start is not None else first_x
        x1 = lv.end if lv.end is not None else last_x
        color = _level_color(theme, lv)
        dash = _LEVEL_DASH.get(lv.style, "dash")
        fig.add_shape(
            type="line", x0=_x(x0), x1=_x(x1), y0=lv.price, y1=lv.price,
            line=dict(color=color, width=1, dash=dash), row=row, col=col,
        )
        # POC/VAH/VAL gibi `end=None` Level'lar HER ZAMAN x1=last_x'e
        # sabitlenir — VP paneli varken bu, etiketin sağa doğru büyüyüp
        # komşu panele/y-ekseni tik yazısına binmesine yol açıyordu (gerçek
        # veriyle bulunan bir çakışma — bkz. CLAUDE.md 2026-08-29 kaydı).
        # Konum (x1) AYNI kalır, yalnızca ANCHOR yönü değişir (metin SOLA
        # büyür, panelin İÇİNDE kalır).
        if labeled is not None and lv not in labeled:
            continue
        near_edge = has_vp and edge_cutoff is not None and x1 >= edge_cutoff
        fig.add_annotation(
            x=_x(x1), y=lv.price, text=_level_display_text(lv), showarrow=False,
            font=dict(size=11, color=color), xanchor="right" if near_edge else "left",
            yanchor="bottom", yshift=yshifts.get(lv, _LEVEL_YSHIFT_BASE), row=row, col=col,
        )


_STRUCTURE_COLOR = {"HH": "green", "HL": "green", "LH": "red", "LL": "red"}


_MAX_HARMONIC_MARKERS = 3


def _draw_markers(
    fig: go.Figure, markers: list[Marker], theme: Theme, row: int, col: int,
    declutter: bool = True,
) -> None:
    harmonic_markers = sorted(
        (m for m in markers if m.kind.startswith("harmonic_")), key=lambda m: m.t, reverse=True,
    )
    # declutter: her okulda onlarca aday birikebilir (özellikle uzun/gürültülü
    # gerçek veride) — yalnızca EN GÜNCEL birkaç "D: fiyat [DURUM]" kutusu
    # gösterilir, gerisi (üçgen/PRZ hâlâ çizili) etiketsiz kalır.
    visible_harmonic = set(harmonic_markers[:_MAX_HARMONIC_MARKERS]) if declutter else None

    for m in markers:
        if m.kind == "structure_label":
            color = getattr(theme, _STRUCTURE_COLOR.get(m.text, "gray"))
            above = m.text in ("HH", "LH")
            fig.add_annotation(
                x=_x(m.t), y=m.price, text=m.text, showarrow=False,
                font=dict(size=11, color=color, family=theme.font),
                yshift=12 if above else -12, row=row, col=col,
            )
        elif m.kind.startswith("harmonic_"):
            if visible_harmonic is not None and m not in visible_harmonic:
                continue
            state = m.kind.removeprefix("harmonic_")
            color = line_color(theme, "bearish" if state == "invalidated" else "bullish")
            fig.add_annotation(
                x=_x(m.t), y=m.price, text=m.text, showarrow=True, arrowhead=2, arrowcolor=color,
                font=dict(size=11, color=theme.text), bgcolor=theme.bg, bordercolor=color,
                ax=30, ay=-30, row=row, col=col,
            )
        elif m.kind == "pair_signal":
            continue  # yalnızca pair modunda, _render_pair kendi çizer
        else:
            fig.add_annotation(
                x=_x(m.t), y=m.price, text=m.text, showarrow=False,
                font=dict(size=10, color=theme.muted), yshift=10, row=row, col=col,
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
    if name == "rsi":
        rsi = result.series.get("rsi_14")
        if rsi is not None:
            fig.add_trace(
                go.Scatter(
                    x=_xs(rsi.index), y=rsi, mode="lines",
                    line=dict(color=theme.purple, width=1.4), name="RSI", showlegend=False,
                ),
                row=row, col=col,
            )
        # 70/50/30 eşik çizgileri — RSI'ın KENDİSİ zaten hesaplanmış bir seri;
        # bu üç değer sabit referans çizgisidir (yeni bir hesap DEĞİL, MACD
        # panelindeki kesişim okları gibi salt görsel kılavuz). `add_hline`
        # ÖNCE değil rsi trace'inden SONRA çağrılır (bkz. `_render_pair`'deki
        # `add_vrect` sessiz no-op notu — aynı sıralama kısıtı).
        for y, color, dash in (
            (70, theme.red, "dot"), (50, theme.muted, "dash"), (30, theme.green, "dot"),
        ):
            fig.add_hline(
                y=y, line=dict(color=color, width=1, dash=dash), row=row, col=col,
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
    fig: go.Figure, result: IndicatorResult, theme: Theme, row: int, col: int,
    legend_name: str | None = None,
) -> None:
    bins, vols = result.series.get("vp_bins"), result.series.get("vp_volumes")
    if bins is None or vols is None:
        return
    # HVN (Yüksek Hacim Düğümü) — `vp_hvn` (varsa) `PriceStructure`'ın KENDİSİ
    # tarafından önceden hesaplanır (`find_hvn_nodes`, saf histogram
    # tepe-noktası tespiti); renderer burada HİÇBİR hesap yapmaz, yalnızca
    # bu hazır bayrağa göre renk seçer. Seri yoksa (ör. eski/başka bir
    # indikatörün ürettiği vp_* — geriye uyumluluk) value-area tabanlı eski
    # renklendirmeye düşer.
    hvn = result.series.get("vp_hvn")
    colors: list[str] = []
    if hvn is not None:
        default_color = with_alpha(theme.blue, 0.35)
        hvn_color = theme.green
        for h in hvn.to_numpy():
            colors.append(hvn_color if h >= 0.5 else default_color)
    else:
        va_low = next((lv.price for lv in result.levels if lv.label == "VAL"), None)
        va_high = next((lv.price for lv in result.levels if lv.label == "VAH"), None)
        for p in bins.to_numpy():
            in_va = va_low is not None and va_high is not None and va_low <= p <= va_high
            colors.append(
                fill_color(theme, "bullish", 0.85) if in_va
                else fill_color(theme, "support_zone", 0.6)
            )
    fig.add_trace(
        go.Bar(
            x=vols.to_numpy(), y=bins.to_numpy(), orientation="h", marker_color=colors,
            name="Hacim Profili", showlegend=False,
        ),
        row=row, col=col,
    )
    if hvn is not None and hvn.to_numpy().any():
        _add_hvn_legend_swatch(fig, theme, row, col, legend_name)
    gauss = result.series.get("vp_gauss")
    if gauss is not None:
        legend_kwargs = {"legend": legend_name} if legend_name else {}
        fig.add_trace(
            go.Scatter(
                x=gauss.to_numpy(), y=gauss.index.to_numpy(), mode="lines",
                # `theme.accent` (marka rengi) — bkz. themes.py docstring'i:
                # bu eğri hacim profilinin KARARA-DEĞER özeti (yoğunlaşma
                # şekli), eskiden keyfi bir sarıydı.
                line=dict(color=theme.accent, width=2), name="Gaussian Fit", showlegend=True,
                **legend_kwargs,
            ),
            row=row, col=col,
        )


def _add_hvn_legend_swatch(
    fig: go.Figure, theme: Theme, row: int, col: int, legend_name: str | None = None,
) -> None:
    """`_draw_volume_profile`'ın HVN bin'leri TEK bir çok-renkli `Bar` trace'i
    içinde boyandığı için Plotly legend'ına kendiliğinden ayrı bir "HVN"
    girdisi olarak GİRMEZ — pair modundaki `_add_holding_legend_swatches`
    ile AYNI çözüm: verisiz (yalnızca legend-amaçlı) bir marker trace'i.
    `legend_name`: birleşik rapor modunda (`render_structure_report`) vp
    paneli sağda geniş bir "Özet Raporu" sütunuyla komşu olduğu için
    varsayılan (figürün sağ ÜST köşesi) legend konumu artık vp panelinin
    ÜSTÜNDE değil rapor sütununun üstünde kalıyordu — ayrı bir `legend2`
    grubuna atanıp vp panelinin KENDİ konumuna göre konumlandırılır (bkz.
    `_position_vp_legend`)."""
    legend_kwargs = {"legend": legend_name} if legend_name else {}
    fig.add_trace(
        go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(symbol="square", size=10, color=theme.green),
            name="HVN (Yüksek Hacim Düğümü)", showlegend=True, hoverinfo="skip",
            **legend_kwargs,
        ),
        row=row, col=col,
    )


def _position_vp_legend(fig: go.Figure, theme: Theme) -> None:
    """`legend2`'yi (bkz. `_draw_volume_profile`'ın `legend_name` parametresi)
    vp panelinin (row=1, col=2) KENDİ x/y domain'inin hemen ÜSTÜNE
    yerleştirir — `_apply_pair_legends`'daki "sabit kesir varsayma, gerçek
    domain'i oku" ilkesiyle AYNI (make_subplots'ın column_widths/row_heights'
    tan hesapladığı domain, sabit bir sayı değil)."""
    x0 = fig.layout.xaxis2.domain[0]
    y1 = fig.layout.yaxis2.domain[1]
    fig.update_layout(
        legend2=dict(
            x=x0, y=y1 + 0.015, xanchor="left", yanchor="bottom", orientation="v",
            bgcolor="rgba(0,0,0,0)", bordercolor=theme.border, borderwidth=0,
            font=dict(color=theme.text, size=9.5, family=theme.font),
        ),
    )


# ------------------------------------------------------- birleşik rapor modu --
#
# 2026-08-30: kullanıcı, `structure.price_structure` (zone/trendline/
# POC-VAH-VAL/hacim profili/MACD) ile `structure.swing_fib_abcd`'i (swing
# HH/HL/LH/LL yapısı + fib merdiveni + AB=CD hedefleri) referans mockup'a
# (images/Ekran görüntüsü 2026-08-29 165109.png) göre TEK bir "aracı kurum
# raporu" grafiğinde BİRLEŞTİRİLMESİNİ istedi, artı sağda deterministik bir
# "Özet Raporu" metin sütunu (bkz. `report_text.py` — LLM YOK, yalnızca zaten
# hesaplanmış değerlerin kural-tabanlı Türkçe cümlelere çevrilmesi). Bu,
# `_render_price_based`'İN YERİNE GEÇMEZ (o TEK indikatörlük genel görünüm
# olarak kalır) — burası viz katmanının HİÇBİR hesap yapmadan iki HAZIR
# `IndicatorResult`'ı aynı çizim yardımcılarıyla (`_draw_boxes`/`_draw_levels`/
# `_draw_lines`/`_draw_markers`/`_stagger_yshifts`) TEK bir figürde birleştiren
# ayrı bir fonksiyon.


_REPORT_COL_WIDTH = 0.24
_REPORT_WRAP_CHARS = 34


def render_structure_report(
    ps_result: IndicatorResult, sf_result: IndicatorResult, df: pd.DataFrame,
    *, theme: Theme | str | None = "auto", last_n: int | None = None, declutter: bool = True,
) -> go.Figure:
    """`structure.price_structure` + `structure.swing_fib_abcd` çıktısını TEK
    grafikte birleştirir. Ana panel (zone/trendline/POC-VAH-VAL + swing yapı
    etiketleri + fib merdiveni + AB=CD hedefleri) yalnızca `last_n`
    penceresine yakınlaşır; hacim/MACD/RSI alt panelleri TAM GEÇMİŞİ gösterir
    (referans mockup'ın kendi tasarımı — ana panel "şu an"a odaklanırken alt
    osilatörler uzun vadeli bağlamı korur, bu yüzden `shared_xaxes=False` —
    aksi halde Plotly satırların x-eksenini birbirine kilitleyip ana panelin
    zoom'unu alt panellere de yansıtırdı). Sağdaki üçüncü kolon deterministik
    bir "Özet Raporu" metnidir (bkz. `report_text.build_summary_lines`)."""
    resolved = resolve_theme(theme, default=LIGHT_ANALYSIS)

    sub_names = list(ps_result.series_layout.keys())
    n_sub = len(sub_names)
    n_rows = 1 + n_sub
    main_h = 0.42 if n_sub else 1.0
    sub_h = (1.0 - main_h) / n_sub if n_sub else 0.0
    row_heights = [main_h] + [sub_h] * n_sub

    has_vp = any(name.startswith("vp_") for name in ps_result.series)
    vp_w = 0.16 if has_vp else 0.0
    main_w = 1.0 - _REPORT_COL_WIDTH - vp_w
    column_widths = [main_w, vp_w or 0.001, _REPORT_COL_WIDTH]

    specs: list[list[dict[str, object] | None]] = [[{}, {}, {"rowspan": n_rows}]]
    specs.extend([{"colspan": 2}, None, None] for _ in range(n_sub))

    fig = make_subplots(
        rows=n_rows, cols=3, shared_xaxes=False, vertical_spacing=0.04,
        row_heights=row_heights, column_widths=column_widths, specs=specs,
        horizontal_spacing=0.02,
    )

    fig.add_trace(
        go.Candlestick(
            x=_xs(df.index), open=df["open"], high=df["high"], low=df["low"], close=df["close"],
            increasing_line_color=resolved.up, decreasing_line_color=resolved.down,
            increasing_fillcolor=resolved.up, decreasing_fillcolor=resolved.down,
            name="Fiyat", showlegend=False,
        ),
        row=1, col=1,
    )

    combined_levels = ps_result.levels + sf_result.levels
    levels = _declutter_levels(combined_levels) if declutter else combined_levels
    boxes = ps_result.boxes
    lines = ps_result.lines + sf_result.lines
    markers = [m for m in ps_result.markers if m.kind != "macd_cross"] + sf_result.markers

    # İki indikatörün seviyeleri (POC/VAH/VAL/zone + AB=CD hedefleri + fib
    # merdiveni) BİRLEŞİNCE, ikisi ayrı ayrı iken sorun olmayan yoğunluk aynı
    # dar fiyat bandında (ör. "güncel fiyat" civarı) üst üste binmeye
    # başlıyordu (gerçek TCELL verisiyle bulunan bir davranış — bkz. CLAUDE.md
    # 2026-08-30). İki hedefli azaltma (şekil HER ZAMAN kalır, yalnızca metin
    # kısıtlanır — bkz. `_draw_levels`'ın `labeled` parametresi):
    # 1) Aynı ABC üçlüsünün BİRDEN FAZLA AB=CD hedefinden (ör. 3 oran) yalnızca
    #    fiyata EN YAKINI etiketlenir.
    # 2) Fib merdiveninde yalnızca klasik "altın bölge" (%61.8/%78.6 — zaten
    #    `accent` rengiyle vurgulanan iki basamak) etiketlenir; diğer basamaklar
    #    (%23.6/%38.2/%50/%100/uzatmalar) çizgi olarak kalır.
    close = float(df["close"].iloc[-1])
    labeled_levels: set[Level] | None = set(levels) if declutter else None
    if declutter:
        d_targets = [lv for lv in levels if lv.label.startswith("D (hedef)")]
        by_direction: dict[str, list[Level]] = {}
        for lv in d_targets:
            by_direction.setdefault(lv.style, []).append(lv)
        nearest_targets = {
            min(group, key=lambda lv: abs(lv.price - close)) for group in by_direction.values()
        }
        assert labeled_levels is not None
        labeled_levels -= set(d_targets) - nearest_targets

        def _is_golden_fib(lv: Level) -> bool:
            try:
                return float(lv.label.rsplit("_", 1)[-1]) in (0.618, 0.786)
            except ValueError:
                return False

        non_golden_fib = {
            lv for lv in levels
            if lv.style in ("fib_retracement", "fib_extension") and not _is_golden_fib(lv)
        }
        labeled_levels -= non_golden_fib

    latest_box_t0 = (
        _latest_per_group(boxes, lambda b: b.style, lambda b: b.t0) if declutter else None
    )
    latest_line_end = (
        _latest_per_group(lines, lambda ln: ln.style, lambda ln: ln.points[-1][0])
        if declutter else None
    )

    window_start_idx = _resolve_window_start(ps_result, df, last_n)
    visible = df.iloc[window_start_idx:]
    visible_price_range = (
        float(visible["high"].max() - visible["low"].min()) if not visible.empty else 0.0
    ) or 1.0
    total_height = 700 + 200 * n_sub
    main_row_px = max((total_height - 90) * main_h, 50.0)
    px_per_unit = main_row_px / visible_price_range if visible_price_range else 1.0

    labeled_boxes = [
        b for b in boxes if latest_box_t0 is None or b.t0 == latest_box_t0.get(b.style)
    ]
    line_extensions = _line_extensions(lines, df)
    labeled_line_ext = [
        (ln, proj) for ln, (_et, proj) in line_extensions.items()
        if latest_line_end is None or ln.points[-1][0] == latest_line_end.get(ln.style)
    ]
    levels_for_stagger = [lv for lv in levels if labeled_levels is None or lv in labeled_levels]
    box_level_yshifts = _stagger_yshifts(
        [(b, b.high, _BOX_YSHIFT_BASE) for b in labeled_boxes]
        + [(lv, lv.price, _BOX_YSHIFT_BASE) for lv in levels_for_stagger]
        + [(ln, proj, _LINE_EXT_YSHIFT) for ln, proj in labeled_line_ext],
        px_per_unit=px_per_unit, step=14.0,
        price_bounds=_visible_price_bounds(df, window_start_idx),
    )
    edge_cutoff = _right_edge_cutoff(df, window_start_idx)

    _draw_boxes(
        fig, boxes, resolved, row=1, col=1, latest_t0=latest_box_t0,
        px_per_unit=px_per_unit, yshifts=box_level_yshifts, has_vp=has_vp, edge_cutoff=edge_cutoff,
    )
    _draw_lines(
        fig, lines, df, resolved, row=1, col=1, latest_end=latest_line_end,
        px_per_unit=px_per_unit, yshifts=box_level_yshifts,
    )
    _draw_levels(
        fig, levels, df, resolved, row=1, col=1, px_per_unit=px_per_unit,
        yshifts=box_level_yshifts, has_vp=has_vp, edge_cutoff=edge_cutoff,
        labeled=labeled_levels,
    )
    _draw_markers(fig, markers, resolved, row=1, col=1, declutter=declutter)

    for i, name in enumerate(sub_names, start=2):
        _draw_series_panel(
            fig, ps_result, name, ps_result.series_layout[name], resolved, row=i, col=1, df=df,
        )
        # Alt paneller TAM GEÇMİŞİ gösterir — ana panelin `last_n` zoom'undan
        # BİLİNÇLİ OLARAK bağımsız (bkz. fonksiyon docstring'i).
        fig.update_xaxes(range=[_x(df.index[0]), _x(df.index[-1])], row=i, col=1)

    if has_vp:
        _draw_volume_profile(fig, ps_result, resolved, row=1, col=2, legend_name="legend2")

    for r in range(1, n_rows + 1):
        fig.update_xaxes(showticklabels=(r == n_rows), row=r, col=1)

    if window_start_idx > 0:
        fig.update_xaxes(
            range=[_x(df.index[window_start_idx]), _x(df.index[-1])], row=1, col=1,
        )
    _sync_price_yaxis(fig, df, window_start_idx, has_vp)

    summary_lines = build_summary_lines(ps_result, sf_result, df)
    _draw_summary_panel(fig, summary_lines, resolved, row=1, col=3)

    # Alt başlık, `ps_result.indicator` ("structure.price_structure") yerine
    # BU birleşik görünümü yansıtmalı (`_price_header` tek-indikatör varsayımı
    # yapar) — yalnızca `subtitle` alanı override edilir, diğer alanlar
    # (fiyat/değişim/tarih) aynı biçimlendirmeden (`_price_header`) gelir.
    header = replace(
        _price_header(ps_result, df),
        subtitle=f"{_category_tr(ps_result.indicator)} — Birleşik Rapor (Yapı + Swing/Fibonacci)",
    )
    _apply_layout(fig, resolved, header, height=total_height, width=1750)
    if has_vp:
        _position_vp_legend(fig, resolved)
    return fig


def _draw_summary_panel(
    fig: go.Figure, lines: list[str], theme: Theme, row: int, col: int,
) -> None:
    """Sağdaki "Özet Raporu" sütunu — gerçek bir veri ekseni taşımaz, yalnızca
    sabit [0,1]x[0,1] bir "tuval" üzerinde üstten alta metin satırları
    (`report_text.build_summary_lines` — deterministik, LLM'siz). Boş bir
    `Scatter` trace'i eklenir (bkz. `add_vrect`/`add_shape`'in bir satırın
    İLK trace'inden önce çağrılırsa sessizce no-op olması — modüldeki `_render_
    pair` notuyla AYNI kısıt, burada annotation'lar için tedbiren uygulanıyor)."""
    fig.update_xaxes(visible=False, range=[0, 1], showgrid=False, row=row, col=col)
    fig.update_yaxes(visible=False, range=[0, 1], showgrid=False, row=row, col=col)
    fig.add_trace(
        go.Scatter(
            x=[0, 1], y=[0, 1], mode="markers", marker=dict(opacity=0),
            showlegend=False, hoverinfo="skip",
        ),
        row=row, col=col,
    )
    fig.add_annotation(
        x=0.0, y=0.99, xanchor="left", yanchor="top", showarrow=False,
        text="<b>ÖZET RAPORU</b>", font=dict(size=13, color=theme.accent, family=theme.font),
        row=row, col=col,
    )
    fig.add_shape(
        type="line", x0=0.0, x1=1.0, y0=0.955, y1=0.955,
        line=dict(color=theme.border, width=1), row=row, col=col,
    )
    y = 0.90
    for raw_line in lines:
        wrapped_lines = textwrap.wrap(raw_line, _REPORT_WRAP_CHARS) or [""]
        for j, wrapped in enumerate(wrapped_lines):
            prefix = "•  " if j == 0 else "    "
            fig.add_annotation(
                x=0.0, y=y, xanchor="left", yanchor="top", showarrow=False,
                text=prefix + wrapped, font=dict(size=11, color=theme.text, family=theme.font),
                row=row, col=col,
            )
            y -= 0.034
        y -= 0.018  # madde aralarında ekstra boşluk


# ---------------------------------------------------------------- pair mod --
#
# 2026-08-29: kullanıcı, `_render_pair`e (o zaman) az önce uygulanan
# paylaşılan "aracı kurum raporu" tasarım geçişini (`_apply_layout`/
# `_draw_header`'ın büyük 2 satırlık masthead'i + tek sağ-taraf legend'ı +
# `light_analysis` kart/dipnot çerçevesi) BU grafik için reddetti — referans
# ekran görüntüsüne (`images/Ekran görüntüsü 2026-08-26 203751.png`) yakın,
# KENDİNE ÖZGÜ küçük/derli-toplu bir üst şerit + panel-başına legend + saf
# siyah zemin istedi. `_render_price_based`/`light_analysis` (yapı/harmonik
# panelleri) tarafı kullanıcının ZATEN memnun olduğu, DOKUNULMAYAN kısım —
# bu yüzden pair modu artık `_apply_layout`/`_draw_header`/`_draw_card_frame`ı
# HİÇ ÇAĞIRMIYOR, kendi `_apply_pair_layout`/`_draw_pair_header`'ına sahip
# (yalnızca ortak, nötr `_draw_footer`'ı — dipnot metni — paylaşıyor).


_PAIR_SUBPLOT_TITLES = (
    "1- Fiyat Yakınlığı (Normalize)",
    "2- Portföy Performansı",
    "3- Z-Skoru ve Momentum Dönüş Onaylı İşlemler",
)

_PAIR_MARGIN_T = 58.0
_PAIR_MARGIN_B = 40.0
_PAIR_HEADER_ROW1_PX = 36.0
_PAIR_HEADER_ROW2_PX = 14.0

_ZONE_STATE_TR: dict[str, str] = {
    "asiri_bolgede": "AŞIRI BÖLGEDE",
    "bolgeye_yaklasiyor": "BÖLGEYE YAKLAŞIYOR",
    "notr": "NÖTR",
    "veri_yok": "VERİ YOK",
}
_STRATEGY_NAME_TR = "LONG-ONLY ROLATIF MOMENTUM (Dönüş Onaylı)"


def _render_pair(result: IndicatorResult, theme: Theme, last_n: int | None) -> go.Figure:
    s = result.series
    idx_full = s["y_norm"].index
    idx_dt = idx_full[-last_n:] if last_n and last_n < len(idx_full) else idx_full
    idx = _xs(idx_dt)  # trace x= için string; .loc[] seçimi idx_dt ile yapılır
    y_symbol, x_symbol = result.symbol.split("/") if "/" in result.symbol else ("Y", "X")

    def sel(key: str) -> pd.Series:
        return s[key].loc[idx_dt]

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.08,
        row_heights=[0.34, 0.33, 0.33],
        subplot_titles=_PAIR_SUBPLOT_TITLES,
    )
    _style_pair_subplot_titles(fig, theme)

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
    _add_holding_legend_swatches(fig, theme, y_symbol, x_symbol, row=1)

    baseline = float(s["portfolio"].iloc[0])
    fig.add_trace(
        go.Scatter(
            x=idx, y=sel("buyhold_5050"), mode="lines",
            line=dict(color=theme.gray, width=1.2, dash="dash"), name="Buy & Hold (50/50)",
            legend="legend2",
        ),
        row=2, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=idx, y=sel("portfolio"), mode="lines",
            line=dict(color=theme.green, width=1.8), name="Rölatif Momentum Portföyü",
            legend="legend2",
        ),
        row=2, col=1,
    )
    # `add_hline` (shape) yerine gerçek bir trace: hem çizgiyi çizer hem de
    # "Başlangıç" panel-2 legend'ında bir öğe olarak görünmesini sağlar
    # (shape'ler Plotly legend'ına hiç girmez).
    fig.add_trace(
        go.Scatter(
            x=[idx[0], idx[-1]], y=[baseline, baseline], mode="lines",
            line=dict(color=theme.muted, width=1, dash="dot"), name="Başlangıç",
            legend="legend2", hoverinfo="skip",
        ),
        row=2, col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=idx, y=sel("z"), mode="lines",
            line=dict(color=theme.orange, width=1.6), name="Z-Skoru", legend="legend3",
        ),
        row=3, col=1,
    )
    _draw_holding_boxes(fig, result.boxes, theme, row=3)
    # Eşik değeri (`k`) etikete eklenir — referans ekran görüntüsü
    # "(+2.0)"/"(-2.0)" gösteriyor; bu YENİ bir hesap değil, `upper`/`lower`
    # serileri zaten SABİT `±k` değerini taşıyor (bkz. relative_momentum.py),
    # burada yalnızca aynı sabitin biçimlendirilmesi.
    upper_k = float(sel("upper").iloc[0])
    lower_k = float(sel("lower").iloc[0])
    fig.add_trace(
        go.Scatter(
            x=idx, y=sel("upper"), mode="lines",
            line=dict(color=theme.red, width=1, dash="dash"),
            name=f"Aşırı Ucuz {x_symbol} Sınırı ({upper_k:+.1f})", legend="legend3",
        ),
        row=3, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=idx, y=sel("lower"), mode="lines",
            line=dict(color=theme.green, width=1, dash="dash"),
            name=f"Aşırı Ucuz {y_symbol} Sınırı ({lower_k:+.1f})", legend="legend3",
        ),
        row=3, col=1,
    )

    for m in result.markers:
        if m.kind != "pair_signal" or m.t not in idx_dt:
            continue
        color = theme.blue if m.text.startswith(y_symbol) else theme.gray
        fig.add_annotation(
            x=_x(m.t), y=m.price, text=m.text, showarrow=False,
            font=dict(size=10, color=theme.text), bgcolor=theme.bg,
            bordercolor=color, borderwidth=1,
            yshift=14 if m.price >= 0 else -14, row=3, col=1,
        )

    line1_text, line1_color, line2_text = _pair_header_lines(
        result, theme, y_symbol, x_symbol, idx_dt[-1],
    )
    _apply_pair_layout(fig, theme, line1_text, line1_color, line2_text, height=860, width=1500)
    return fig


def _style_pair_subplot_titles(fig: go.Figure, theme: Theme) -> None:
    """`make_subplots(subplot_titles=...)`'ın varsayılan gri başlık rengi
    yerine referans ekran görüntüsündeki yeşil vurguyu uygular. Metne göre
    hedefler (yalnızca bilinen 3 pair alt-panel başlığı) — HESAP yapılmaz,
    salt stil; bu fonksiyon `make_subplots()`'tan HEMEN sonra, başka hiçbir
    annotation eklenmeden önce çağrılmalı (metin eşleşmesinin belirsizliğe
    düşmemesi için, gerçi metinler zaten proje-içi sabit/benzersiz)."""
    color = theme.green
    fig.for_each_annotation(
        lambda a: a.update(font=dict(color=color, size=13, family=theme.font))
        if a.text in _PAIR_SUBPLOT_TITLES else None
    )


def _add_holding_legend_swatches(
    fig: go.Figure, theme: Theme, y_symbol: str, x_symbol: str, row: int,
) -> None:
    """Tutulan-dönem gölgeleri `add_vrect` (shape) ile çizildiği için Plotly
    legend'ına kendiliğinden GİRMEZ — referans ekran görüntüsü panel 1
    legend'ında "TCELL Tutulan Dönemler"/"ISCTR Tutulan Dönemler" renk
    kareleri gösteriyor, bu yüzden verisiz (yalnızca legend-amaçlı) iki
    `Scatter` eklenir (bkz. `_FILL_STYLE_COLOR`'daki y_holding/x_holding
    renkleri — themes.py)."""
    # `x=[None]` (tek, ama boş bir nokta) kasıtlı — `x=[]` (tam boş dizi)
    # kaleido'nun statik PNG dışa aktarımında legend girdisini SESSİZCE
    # düşürüyordu (gerçek render ile bulunan bir davranış; HTML/interaktif
    # görünümde sorun yoktu, yalnızca `fig.write_image` yolunda).
    fig.add_trace(
        go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(symbol="square", size=10, color=fill_color(theme, "y_holding", 0.9)),
            name=f"{y_symbol} Tutulan Dönemler", showlegend=True, hoverinfo="skip",
        ),
        row=row, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(symbol="square", size=10, color=fill_color(theme, "x_holding", 0.9)),
            name=f"{x_symbol} Tutulan Dönemler", showlegend=True, hoverinfo="skip",
        ),
        row=row, col=1,
    )


def _pair_header_lines(
    result: IndicatorResult, theme: Theme, y_symbol: str, x_symbol: str, last_dt: object,
) -> tuple[str, str, str]:
    """Referans ekran görüntüsündeki 2 satırlık kompakt başlığın metnini
    üretir — TAMAMI zaten `last_state`'te hesaplanmış özet istatistiklerin
    (`net_pnl`/`return_pct`/`n_trades`/`z_today`/`zone_state`/`holding`)
    BİÇİMLENDİRİLMESİ, yeni bir indikatör hesabı DEĞİL (görev kısıtıyla
    aynı — eski tek satırlık başlık da bunu yapıyordu). Satır 1: sinyal
    durumu (bugün yeni sinyal varsa `signal_today` metni + yeşil; yoksa
    `zone_state`'in Türkçe karşılığı + nötr/beyaz) | pozisyon | Z geçişi |
    tarih. Satır 2: strateji adı (sabit metin) | çift | net K/Z | geçiş
    sayısı."""
    ls = result.last_state
    z_today, z_yday = ls.get("z_today"), ls.get("z_yesterday")
    z_str = (
        f"Z: {z_yday:.3f} → {z_today:.3f}"
        if z_today is not None and z_yday is not None else "Z: —"
    )
    holding_sym = ls.get("holding")
    signal_today = ls.get("signal_today")

    if signal_today:
        durum, color = str(signal_today), theme.green
    else:
        durum, color = _ZONE_STATE_TR.get(str(ls.get("zone_state")), "NÖTR"), theme.text

    if holding_sym is None:
        pos_str = "Pozisyon Yok"
    else:
        side_desc = (
            "Y Ucuz -> Dönüş Onaylandı" if holding_sym == y_symbol
            else "X Ucuz -> Dönüş Onaylandı"
        )
        pos_str = f"{holding_sym} AL ({side_desc})"

    line1 = f"{durum} | {pos_str} | {z_str} | {_fmt_date(last_dt)}"

    net_pnl = ls.get("net_pnl") or 0.0
    return_pct = ls.get("return_pct") or 0.0
    n_trades = ls.get("n_trades") or 0
    line2 = (
        f"{_STRATEGY_NAME_TR} | {y_symbol} <-> {x_symbol} | "
        f"K/Z: {net_pnl:+,.0f} TL (%{return_pct:+.1f}) | Geçiş: {n_trades} kez"
    )
    return line1, color, line2


def _apply_pair_layout(
    fig: go.Figure, theme: Theme, line1_text: str, line1_color: str, line2_text: str,
    height: int, width: int,
) -> None:
    """`_apply_layout`'un pair-moduna özgü KÜÇÜK karşılığı — büyük masthead/
    kart çerçevesi/tek sağ-legend YERİNE: saf siyah zemin, 2 satırlık
    kompakt sol-hizalı başlık, panel-başına legend (`legend`/`legend2`/
    `legend3`). Dipnot (`_draw_footer`) hâlâ paylaşılıyor — o nötr, pair'e
    özgü hiçbir varsayım taşımıyor."""
    fig.update_layout(
        paper_bgcolor=theme.page_bg,
        plot_bgcolor=theme.bg,
        font=dict(color=theme.text, family=theme.font, size=11),
        height=height,
        width=width,
        margin=dict(l=56, r=40, t=_PAIR_MARGIN_T, b=_PAIR_MARGIN_B),
        xaxis_rangeslider_visible=False,
    )
    fig.update_xaxes(gridcolor=theme.grid, zerolinecolor=theme.grid, showspikes=False)
    fig.update_yaxes(gridcolor=theme.grid, zerolinecolor=theme.grid)
    plot_h = max(height - _PAIR_MARGIN_T - _PAIR_MARGIN_B, 50.0)
    _draw_pair_header(fig, theme, line1_text, line1_color, line2_text, plot_h)
    _draw_footer(fig, theme, plot_h)
    _apply_pair_legends(fig, theme)


def _draw_pair_header(
    fig: go.Figure, theme: Theme, line1_text: str, line1_color: str, line2_text: str,
    plot_h: float,
) -> None:
    """Referans ekran görüntüsündeki gibi küçük/sol-hizalı 2 satır — jenerik
    modun büyük sol-sembol/sağ-değer masthead'inin AKSİNE tek bir sol
    sütunda, ayraç çizgisi yok (referansta da yok)."""
    row1_y = 1.0 + _PAIR_HEADER_ROW1_PX / plot_h
    row2_y = 1.0 + _PAIR_HEADER_ROW2_PX / plot_h
    fig.add_annotation(
        x=0.0, y=row1_y, xref="paper", yref="paper", xanchor="left", yanchor="bottom",
        text=f"<b>{line1_text}</b>", showarrow=False,
        font=dict(family=theme.font, size=13, color=line1_color),
    )
    fig.add_annotation(
        x=0.0, y=row2_y, xref="paper", yref="paper", xanchor="left", yanchor="bottom",
        text=line2_text, showarrow=False,
        font=dict(family=theme.font, size=10.5, color=theme.muted),
    )


def _apply_pair_legends(fig: go.Figure, theme: Theme) -> None:
    """Görev kısıtı: tek sağ-taraf legend YERİNE panel-başına (sol-üst
    köşe) 3 ayrı legend — Plotly 5.15+'da desteklenen `legend`/`legend2`/
    `legend3` mekanizması (yüklü sürüm burada kontrol EDİLMEZ, çağıran
    modül seviyesinde `plotly.__version__` kontrolü yapılmış olmalı; proje
    ortamında 7.0.0 doğrulandı). Her legend'ın y konumu, o satırın GERÇEK
    (make_subplots'ın row_heights/vertical_spacing'den hesapladığı) yaxis
    domain'inin tepesinden okunur — sabit bir kesir VARSAYILMAZ, çünkü
    row_heights değişirse (ör. ileride) domain de değişir."""
    y1 = fig.layout.yaxis.domain
    y2 = fig.layout.yaxis2.domain
    y3 = fig.layout.yaxis3.domain
    common = dict(
        bgcolor=with_alpha(theme.bg, 0.75), bordercolor=theme.border, borderwidth=1,
        font=dict(color=theme.text, size=9),
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(x=0.008, y=y1[1] - 0.012, xanchor="left", yanchor="top", **common),
        legend2=dict(x=0.008, y=y2[1] - 0.012, xanchor="left", yanchor="top", **common),
        legend3=dict(x=0.008, y=y3[1] - 0.012, xanchor="left", yanchor="top", **common),
    )


def _draw_holding_boxes(fig: go.Figure, boxes: list[Box], theme: Theme, row: int) -> None:
    for b in boxes:
        if b.style not in ("y_holding", "x_holding"):
            continue
        fig.add_vrect(
            # 0.20 -> 0.28: referans ekran görüntüsündeki "fairly saturated"
            # (görev metninin kendi ifadesi) gölge, saf siyah zemine karşı
            # eski opaklıkla fazla soluk kalıyordu.
            x0=_x(b.t0), x1=_x(b.t1), fillcolor=fill_color(theme, b.style, 0.28), line_width=0,
            layer="below", row=row, col=1,
        )
