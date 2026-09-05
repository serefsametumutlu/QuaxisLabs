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

from dataclasses import dataclass, replace
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from tlab.core.types import Box, IndicatorResult, Level, Line, Marker, Polygon, Timeframe
from tlab.viz import labels_tr as tr
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


# 1600 -> 1750 (2026-08-30): kullanıcı geri bildirimi — referans ekran
# görüntülerine göre mumlar bizde daha ince/sıkışık görünüyordu (son mumları
# ayırt etmek "neredeyse imkansız"). Bkz. `_DEFAULT_LAST_N`'in AYNI gerekçeyle
# küçültülmesi — ikisi birlikte piksel/bar oranını referansa yaklaştırır.
_DEFAULT_WIDTH = 1750


@dataclass(frozen=True)
class _Header:
    """Masthead için önceden biçimlendirilmiş metin alanları — `_draw_header`
    bunları `xref/yref="paper"` annotation'larla TEK, sade bir başlık satırı
    olarak çizer. Burada HİÇBİR teknik hesap yapılmaz — yalnızca zaten
    `IndicatorResult`'ta mevcut değerlerin (sembol, formasyon/ekol adı) metne
    çevrilmesi.

    2026-08-30 (kullanıcı geri bildirimi — "hepsi rezalet... images/
    klasöründeki görsellerle birebir aynı olacak şekilde güncelle"): önceki
    "aracı kurum raporu" tasarımı (2 satır + sağ-hizalı fiyat/değişim +
    accent ayraç çizgisi + kart çerçevesi + dipnot) kullanıcının kendi
    referans ekran görüntülerinin HİÇBİRİYLE örtüşmüyordu — o görsellerin
    hepsi TEK satırlık düz metin bir başlık kullanıyor (ör. "TCELL - Swing
    Yapısı, Fibonacci ve AB=CD Analizi (Düşüş)", "ALARK.IS - Kelebek
    Formasyonu (SAT) [AKTIF] — SİSTEM: Pesavento"). Bu sınıf artık yalnızca
    `symbol`/`subtitle` taşır, `_draw_header` bunları TEK satırda birleştirir."""

    symbol: str
    subtitle: str


_MARGIN_L = 56
_MARGIN_R = 116
_MARGIN_T = 56
_MARGIN_B = 40
# Masthead, `yref="paper"` (0..1 = yalnızca ÇİZİM alanı, kenar boşlukları
# HARİÇ) üzerinden `y>1` ile üst kenar boşluğuna taşan annotation'larla
# çizilir. Bu fraksiyon, TOPLAM figür yüksekliğine göre değil yalnızca çizim
# alanının (height - t - b) yüksekliğine göre ölçeklenir — bu yüzden SABİT
# bir `y=1.2` gibi bir değer, alt-panelli (hacim/MACD) uzun bir figürde
# (çizim alanı büyük → aynı fraksiyon çok daha fazla piksele karşılık gelir)
# kenar boşluğunun DIŞINA taşıp görünmez oluyordu (gerçek render ile bulunan
# bir hata). Bunun yerine SABİT bir piksel ofseti (`_HEADER_ROW1_PX`)
# hesaplanıp `_apply_layout` içinde figüre özgü paper-fraksiyonuna çevrilir.
_HEADER_ROW1_PX = 34.0
_FOOTER_PX = 32.0
_FOOTER_TEXT = "Yalnızca teknik analiz amaçlıdır, yatırım tavsiyesi değildir — QuaxisLabs"


def _apply_layout(
    fig: go.Figure, theme: Theme, header: _Header, height: int, width: int = _DEFAULT_WIDTH,
) -> None:
    """Jenerik/harmonik (`light_analysis`) mod için ortak yerleşim: TEK
    satırlık düz başlık + panel çerçeveleri. **Pair modu (2026-08-29'dan
    itibaren) BUNU KULLANMAZ** — kendi ayrık `_apply_pair_layout`/`_draw_
    pair_header`'ı var (bkz. `_render_pair`). Bu fonksiyon yalnızca
    `_render_price_based`'in çağırdığı hâliyle kalmalı; pair'e ÖZGÜ hiçbir
    dal eklenmemeli.

    2026-08-30: eskiden burada ayrıca bir dış "kart" çerçevesi (`_draw_
    card_frame`) ve bir dipnot şeridi (`_draw_footer`) de çiziliyordu —
    kullanıcının referans ekran görüntülerinin (`images/`) hiçbirinde bu
    ikisi YOK, kaldırıldı (bkz. `_Header` docstring'i)."""
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
        # `_draw_levels`); `_MARGIN_R` bu tür etiketlere yetecek kadar pay
        # bırakır. t, tek satırlık başlık için (bkz. `_draw_header`).
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
    _draw_panel_frames(fig, theme)
    _draw_header(fig, theme, header, plot_h)


def _draw_panel_frames(fig: go.Figure, theme: Theme) -> None:
    """Birden fazla alt panel varken (mum+vp, hacim, MACD, RSI, ...) HER
    birinin KENDİ ince çerçevesini çizer — referans ekran görüntüsündeki
    ("aracı kurum raporu" mockup'ı, images/Ekran görüntüsü 2026-08-26
    203900.png) "widget grid" hissi: her panel kendi kutusunda, net
    sınırlarla ayrılmış. `_draw_card_frame`'in TÜM figürü saran TEK
    çerçevesine EK olarak çalışır (onun yerine değil). Panel sayısı/düzeni
    ÖNCEDEN bilinmez — doğrudan `fig.layout`'taki eksen ÇİFTLERİNDEN
    (xaxisN/yaxisN, `select_xaxes`'in döndürdüğü `plotly_name` sonekiyle
    eşleştirilir) okunur, bu yüzden tek panelli (vp'siz/alt panelsiz)
    grafiklerde tek bir çerçeve (zaten `_draw_card_frame`'inkiyle çakışan)
    çizip fazladan bir şey eklemez."""
    for xaxis in fig.select_xaxes():
        suffix = xaxis.plotly_name.removeprefix("xaxis")
        yaxis = getattr(fig.layout, f"yaxis{suffix}", None)
        if yaxis is None or xaxis.domain is None or yaxis.domain is None:
            continue
        x0, x1 = xaxis.domain
        y0, y1 = yaxis.domain
        fig.add_shape(
            type="rect", xref="paper", yref="paper", x0=x0, x1=x1, y0=y0, y1=y1,
            line=dict(color=theme.border, width=1), fillcolor="rgba(0,0,0,0)", layer="above",
        )


def _draw_header(fig: go.Figure, theme: Theme, h: _Header, plot_h: float) -> None:
    """TEK satırlık düz metin başlık: `"{sembol} - {açıklama}"`, sol-hizalı,
    normal (rapor-branding'i olmayan) bir başlık gibi — referans ekran
    görüntülerinin (`images/`) hepsinin kullandığı biçim. `plot_h`: bkz.
    `_HEADER_ROW1_PX` docstring'i. Yalnızca `_render_price_based` çağırır —
    pair modunun kendi `_draw_pair_header`'ı var."""
    row1_y = 1.0 + _HEADER_ROW1_PX / plot_h
    text = f"<b>{h.symbol}</b> - {h.subtitle}" if h.subtitle else f"<b>{h.symbol}</b>"
    fig.add_annotation(
        x=0.0, y=row1_y, xref="paper", yref="paper", xanchor="left", yanchor="bottom",
        text=text, showarrow=False,
        font=dict(family=theme.font, size=15, color=theme.text),
    )


def _draw_footer(fig: go.Figure, theme: Theme, plot_h: float) -> None:
    """Yalnızca pair modu (`_apply_pair_layout`) kullanır — jenerik/harmonik
    `_apply_layout` artık dipnot şeridi çizmiyor (bkz. `_Header` docstring'i)."""
    footer_y = -_FOOTER_PX / plot_h
    fig.add_annotation(
        x=0.5, y=footer_y, xref="paper", yref="paper", xanchor="center", yanchor="top",
        text=_FOOTER_TEXT, showarrow=False,
        font=dict(family=theme.font, size=9, color=theme.muted),
    )


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


_RIGHT_PAD_BARS = 12.0
# 0.6 -> 12.0 (2026-09-02): kullanıcı geri bildirimi — 0.6 bar'lık pay yalnızca
# "son mum gövdesi eksen dışına taşıp kesilmesin" sorununu çözüyordu (bkz. alt
# satırlardaki eski gerekçe), ama referans görsellerin (ornek1/ornek2.png,
# TradingView tarzı) son bardan SONRA bıraktığı GENİŞ boşlukla aynı şey
# DEĞİL — kullanıcı "son mumun sağında boş kısım kalsın" dedi, mumlar hâlâ
# panelin sağ kenarına yapışık duruyordu. `lightweight-charts`'ın Faz 1'de
# kullanılan `rightOffset: 12` ayarıyla AYNI değer (görsel tutarlılık için).


def _right_padded_x(df: pd.DataFrame, end_idx: int) -> str:
    """`fig.update_xaxes(range=[...])` sağ kenarı için — eksenin sağ sınırına
    son bardan sonra `_RIGHT_PAD_BARS` kadar boş zaman payı eklenir (en yakın
    komşu bar aralığından türetilir, sabit bir gün sayısı VARSAYILMAZ — 4H/1D/
    W1 hepsi farklı adımlarda çalışır). Bu hem "son mum sağa yapışık"
    şikayetini çözer hem de (daha önce çözülmüş) mum gövdesinin eksen dışına
    taşıp kesilmesi sorununu ZATEN kapsar (12 bar >> 0.6 bar)."""
    end_idx = min(end_idx, len(df) - 1)
    if end_idx <= 0:
        step = pd.Timedelta(days=1)
    else:
        step = df.index[end_idx] - df.index[end_idx - 1]
        if step <= pd.Timedelta(0):
            step = pd.Timedelta(days=1)
    return _x(df.index[end_idx] + step * _RIGHT_PAD_BARS)


def _rangebreaks_for(df: pd.DataFrame, timeframe: Timeframe) -> list[dict[str, object]]:
    """GERÇEK HATA (bulunup düzeltildi, 2026-09-02): Plotly'nin tarih eksen'i
    varsayılan olarak SÜREKLİ zaman akışı varsayar — hafta sonları VE
    (4H/1H gibi gün-içi zaman dilimlerinde) seans dışı gece saatleri de
    eksende PAY alıyordu. BIST 4H'te bir gün yalnızca ~3 bar üretirken
    (bkz. `tlab/data/calendar.py`), eksen 24 saatlik takvim gününe göre
    ölçeklendiği için o 3 gerçek mumun kapladığı pay, gece boşluğuna göre
    orantısız küçülüyordu — kullanıcının "mumlar çubuk grafiği gibi, gövde
    görünmüyor" şikayetinin `_DEFAULT_LAST_N` küçültmesinden (aynı sorunun
    başka bir yüzü) BAĞIMSIZ, muhtemelen daha büyük bir bileşeni.
    Piyasa/seans saatlerini burada yeniden TANIMLAMAK yerine (bu modül
    `market` parametresi almıyor, `tlab/data/calendar.py::SESSION_HOURS`e
    bağımlı olmak istemiyoruz), gün-içi aktif saat aralığı DOĞRUDAN
    `df.index`'in kendisinden (gerçekte hangi saatlerde bar VARSA) türetilir
    — piyasadan bağımsız, sağlam bir yöntem. Günlük/haftalık zaman
    dilimlerinde saat kısıtı UYGULANMAZ (gün-içi boşluk sorunu yok)."""
    breaks: list[dict[str, object]] = [{"bounds": ["sat", "mon"]}]
    if timeframe in (Timeframe.H1, Timeframe.H4) and len(df) > 1:
        hours = df.index.hour
        active_start, active_end = int(hours.min()), int(hours.max())
        if active_start > 0 or active_end < 23:
            # Son aktif saatten BİR SONRAKİ günün ilk aktif saatine kadar
            # (gece boyu) eksende gizlenir — `bounds=[a, b]` a>b iken
            # gece yarısını saracak şekilde yorumlanır (Plotly semantiği).
            breaks.append({"bounds": [active_end + 1, active_start], "pattern": "hour"})
    return breaks


# 0.18 -> 0.24 (2026-08-30): kullanıcı geri bildirimi — hacim profili paneli
# (HVN+Gaussian Fit) referansla kıyaslayınca dar geliyordu, çubuklar/eğri
# panelin sağ kenarına fazla yakın duruyordu. Bkz. `_draw_volume_profile`'daki
# eşlik eden x-ekseni dolgu payı (aynı gerekçe, panelin İÇİNDE daha ferah
# durması için).
_VP_COLUMN_WIDTH = 0.24

# 250 -> 150 (2026-08-30) -> 90 (2026-09-02): kullanıcı geri bildirimi —
# 150'de bile mumlar "çubuk grafiği gibi, mum gövdesi görünmüyor" (doji/
# harami gibi mum formasyonlarını ayırt edemiyor) diye bildirdi. Kök neden:
# bu sabit PNG'nin (1750px, `scale=2` ile 3500px dışa aktarılıyor) STANDALONE
# görüntüleyicide (ör. `tlab plot` çıktısını doğrudan açmak) NASIL
# göründüğüne göre ayarlanmıştı — web arayüzünde ise tarayıcı bu 3500px'lik
# görseli ~1200-1400px'lik bir karta sığdırmak için KÜÇÜLTÜYOR (ek bir
# ölçek faktörü, önceki ayarlamalar bunu hesaba KATMAMIŞTI), bu da her mum
# gövdesinin ekranda birkaç piksele (bazen 1px'in altına) düşmesine yol
# açıyordu. 90 bar, aynı panel genişliğinde her muma önceki ayardan ~%65
# daha fazla piksel bırakır.
_DEFAULT_LAST_N = 90
# K2 düzeltmesi bölüm 3 (2026-09-05, bkz. docs/GORSEL_HATA_TESHISI.md):
# panel yükseklik oranı standardı -- ana panel >= %55, her alt panel <= %15.
_SUB_PANEL_H_TARGET = 0.15
_MAIN_PANEL_H_MIN = 0.55
_HARMONIC_ZOOM_PAD_BARS = 20
# Bir adayın X'inden BAŞLAYIP HER ZAMAN veri setinin GERÇEK son barına kadar
# uzanan pencere — aday çok eskiyse (o zamandan beri yeni bir aday doğmadıysa,
# ör. ALARK) grafiğin çoğunun boş/düz mum olduğu bir görünüm yaratıyordu
# (kullanıcı geri bildirimiyle bulunan bir davranış — referans ekran
# görüntüleri formasyonu HER ZAMAN ekranın büyük bölümünü dolduracak şekilde
# yakınlaştırıyor). `_resolve_window_end` artık pencereyi adayın KENDİ
# ufkunda (`born_time` + bu pay) keser — GERÇEKTEN daha yeni veri varsa
# (aday güncel), zaten `min(..., n-1)` gerçek son bara düşer, davranış
# DEĞİŞMEZ.
#
# 2026-09-01: SABİT 60 bar, kısa ömürlü (birkaç haftalık) adaylarda formasyonu
# yine küçük bir köşeye sıkıştırıyordu — kuyruk, deseninin kendisinden DAHA
# UZUN olabiliyordu (gerçek TCELL/pesavento verisiyle bulunan bir durum,
# kullanıcı "mockup'la birebir aynı, karışıklık istemiyorum" dedi). Artık
# adayın KENDİ X→D açıklığının bir kesri (`_HARMONIC_END_PAD_FRACTION`),
# `_HARMONIC_END_PAD_MIN/MAX_BARS` ile alt/üst sınırlanır — kısa adaylar kısa
# kuyruk, uzun adaylar (three_drives gibi çok bacaklı ekoller) hâlâ makul bir
# üst sınırda kalır.
_HARMONIC_END_PAD_MIN_BARS = 15
_HARMONIC_END_PAD_MAX_BARS = 60
_HARMONIC_END_PAD_FRACTION = 0.5

# 2026-09-03 GERÇEK bulgu (TRHOL `patterns.broadening` render'ıyla bulundu):
# yukarıdaki bar-SAYISI tabanlı pad tek başına yetmiyordu -- eski (hedefe
# çoktan ulaşmış) bir örüntünün pad penceresi içine, örüntüyle TAMAMEN
# alakasız devasa bir rallı (fiyatın birkaç katına çıkması) girince Y-ekseni
# bu hareketle eziliyor, örüntünün kendisi ekranın dibinde görünmez bir
# çizgiye dönüşüyordu. Yalnızca `patterns.*` için (harmonik'e dokunulmadı,
# zaten ayrı doğrulanmış bir pad mantığı var): pad penceresi fiyatça da
# sınırlanır -- örüntünün KENDİ (start_idx..idx) fiyat aralığının birkaç
# katını aşan bir bara ulaşınca genişleme ORADA durur.
_PATTERN_END_PAD_PRICE_MULT = 2.0

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
    if result.indicator.startswith("patterns."):
        return _pattern_auto_window_start(result, df)
    return max(0, n - _DEFAULT_LAST_N)


def _recent_harmonic_time_range(
    result: IndicatorResult,
) -> tuple[object, object] | None:
    """En son eklenen adayın (xab+bcd — aynı adayın iki poligonu ardışık
    eklenir, bkz. `scanner_indicator.py`) TÜM noktalarının en erken/en geç
    zaman damgalarını döner — `_harmonic_auto_window_start` (erken uç,
    pencere BAŞLANGICI) ve `_resolve_window_end` (geç uç, pencere BİTİŞİ)
    tarafından PAYLAŞILAN tek kaynak. Aday yoksa `None`."""
    if not result.polygons:
        return None
    recent = result.polygons[-2:]
    times = [pt[0] for poly in recent for pt in poly.points]
    return min(times), max(times)


def _harmonic_auto_window_start(result: IndicatorResult, df: pd.DataFrame) -> int:
    """En son eklenen adayın X noktasından `_HARMONIC_ZOOM_PAD_BARS` kadar
    önce başlayan pencereyi döner. Aday yoksa varsayılan pencereye düşer."""
    time_range = _recent_harmonic_time_range(result)
    if time_range is None:
        return max(0, len(df) - _DEFAULT_LAST_N)
    earliest_t, _latest_t = time_range
    try:
        idx = df.index.get_loc(earliest_t)
    except KeyError:
        idx = 0
    if not isinstance(idx, int):
        idx = 0
    return max(0, idx - _HARMONIC_ZOOM_PAD_BARS)


def _recent_pattern_time_range(result: IndicatorResult) -> tuple[object, object] | None:
    """`patterns.*` için `_recent_harmonic_time_range`'in eşdeğeri (2026-09-03,
    gerçek ODAS/TRHOL verisiyle bulundu: en güncel geçerli örüntü aylarca
    eski olduğunda, sabit `_DEFAULT_LAST_N` (90 bar) penceresi onu TAMAMEN
    dışarıda bırakıyordu — grafik "hiçbir şey yok" gibi BOMBOŞ görünüyordu).

    2026-09-04 GERÇEK bulgu (PGSUS `patterns.head_shoulders`'da bulundu,
    kullanıcı: "AL sinyalini kontrol ettim hiç düzelme göremedim"): eski
    sürüm birden fazla şekil türü (ör. hem Şubat'taki bir OBO hem
    Eylül'deki bir TOBO) aynı anda geçerliyse İKİSİNİN de zaman aralığını
    kapsayacak şekilde min/max alıyordu — 7 aylık bir pencere GÜNCEL
    TOBO'yu birkaç fiyat biriminden ibaret, üst üste binen etiketli
    okunaksız bir şeride sıkıştırıyordu (üçgenler TEKNİK OLARAK doğruydu,
    görsel olarak fark edilemeyecek kadar küçüktü). Artık yalnızca EN SON
    onaylanan/tamamlanan TEK örüntünün kendi zaman aralığı kullanılıyor
    — daha eski ama hâlâ "geçerli" farklı şekilli örüntüler pencere
    boyutuna KATILMIYOR (yine de son pencereye denk gelirse çizilmeye
    devam eder, yalnızca pencereyi ONLARA göre GENİŞLETMİYORUZ)."""
    outcome_times: dict[str, datetime] = {}
    for m in result.markers:
        if m.kind.startswith("pattern_confirmed:") or m.kind.startswith("pattern_completed:"):
            outcome_times[m.kind.split(":", 1)[1]] = m.t
    if not outcome_times:
        return None
    latest_pid = max(outcome_times, key=lambda p: outcome_times[p])
    times = [outcome_times[latest_pid]]
    for m in result.markers:
        if not m.kind.startswith("pattern_vertex:"):
            continue
        if m.kind.removeprefix("pattern_vertex:") == latest_pid:
            times.append(m.t)
    return min(times), max(times)


def _pattern_auto_window_start(result: IndicatorResult, df: pd.DataFrame) -> int:
    """Varsayılan pencereden (`_DEFAULT_LAST_N`) DAHA DAR bir aralığa asla
    zoom yapmaz — yalnızca en güncel geçerli örüntü o pencerenin DIŞINDA
    kaldığında devreye girip geriye doğru genişler (harmonik'in AYNI
    felsefesi, bkz. `_harmonic_auto_window_start`)."""
    default_start = max(0, len(df) - _DEFAULT_LAST_N)
    time_range = _recent_pattern_time_range(result)
    if time_range is None:
        return default_start
    earliest_t, _latest_t = time_range
    try:
        idx = df.index.get_loc(earliest_t)
    except KeyError:
        return default_start
    if not isinstance(idx, int):
        return default_start
    return min(default_start, max(0, idx - _HARMONIC_ZOOM_PAD_BARS))


def _resolve_window_end(result: IndicatorResult, df: pd.DataFrame) -> int:
    """Görünür pencerenin BİTİŞ bar indeksini belirler — bkz. `_HARMONIC_END_
    PAD_BARS` docstring'i. `harmonic.*`/`patterns.*` için (VE bir aday/örüntü
    varsa) o adayın/örüntünün kendi ufkuna (+ pay) kısıtlar; diğer tüm
    durumlarda HER ZAMAN gerçek son bar (`n-1`) döner — davranış DEĞİŞMEZ."""
    n = len(df)
    if result.indicator.startswith("harmonic."):
        time_range = _recent_harmonic_time_range(result)
    elif result.indicator.startswith("patterns."):
        time_range = _recent_pattern_time_range(result)
    else:
        return n - 1
    if time_range is None:
        return n - 1
    earliest_t, latest_t = time_range
    try:
        idx = df.index.get_loc(latest_t)
    except KeyError:
        return n - 1
    if not isinstance(idx, int):
        return n - 1
    pad = _HARMONIC_END_PAD_MAX_BARS
    try:
        start_idx = df.index.get_loc(earliest_t)
    except KeyError:
        start_idx = None
    if isinstance(start_idx, int):
        span = max(0, idx - start_idx)
        pad = min(
            _HARMONIC_END_PAD_MAX_BARS,
            max(_HARMONIC_END_PAD_MIN_BARS, int(span * _HARMONIC_END_PAD_FRACTION)),
        )
    max_end = min(n - 1, idx + pad)
    if (
        result.indicator.startswith("patterns.")
        and isinstance(start_idx, int)
        and max_end > idx
    ):
        own_low = float(df["low"].iloc[start_idx : idx + 1].min())
        own_high = float(df["high"].iloc[start_idx : idx + 1].max())
        own_span = max(own_high - own_low, own_high * 0.02, 1e-9)
        limit_low = own_low - own_span * _PATTERN_END_PAD_PRICE_MULT
        limit_high = own_high + own_span * _PATTERN_END_PAD_PRICE_MULT
        low_arr = df["low"].to_numpy()
        high_arr = df["high"].to_numpy()
        capped_end = idx
        for t in range(idx + 1, max_end + 1):
            if low_arr[t] < limit_low or high_arr[t] > limit_high:
                break
            capped_end = t
        max_end = capped_end
    return max_end


def _harmonic_price_bounds(
    result: IndicatorResult, df: pd.DataFrame, window_start_idx: int, window_end_idx: int,
) -> tuple[float, float] | None:
    """`harmonic.*` için Y-ekseni aralığını yalnızca GÖRÜNÜR mumların değil,
    aynı pencereye düşen Polygon/Level (PRZ, fib merdiveni) fiyatlarının da
    BİRLEŞİMİNDEN hesaplar.

    **Gerçek hata** (ACSEL örneğinde bulundu, kullanıcı geri bildirimiyle):
    D hedefi/PRZ merkezi, görünür mum aralığının dışında (ör. çok daha
    aşağıda) kalınca eskiden YALNIZCA mum yüksek/düşüklerini kullanan
    `_visible_price_bounds` bunu hesaba katmıyordu — BCD üçgeni ekranın
    dışına taşıp tuhaf bir şekilde kesiliyor, "D: ... [GEÇERSİZ]" etiketi de
    görünmez bir y-koordinatına yerleşip grafikte ALAKASIZ bir noktadaymış
    gibi GÖRÜNÜYORDU (aslında yalnızca çizim alanının dışındaydı, konumu
    kendi içinde tutarlıydı)."""
    visible = df.iloc[window_start_idx : window_end_idx + 1]
    prices: list[float] = []
    if not visible.empty:
        prices.append(float(visible["low"].min()))
        prices.append(float(visible["high"].max()))
    start_t, end_t = df.index[window_start_idx], df.index[window_end_idx]
    for poly in result.polygons:
        prices.extend(p for t, p in poly.points if start_t <= t <= end_t)
    for lv in result.levels:
        lv_time = lv.start if lv.start is not None else start_t
        if start_t <= lv_time <= end_t:
            prices.append(lv.price)
    if not prices:
        return None
    low, high = min(prices), max(prices)
    pad = (high - low) * 0.08 or 1.0
    return (low - pad, high + pad)


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
    fig: go.Figure, df: pd.DataFrame, window_start_idx: int, has_vp: bool,
    bounds: tuple[float, float] | None = None,
) -> None:
    """Ana panel ile sağ hacim-profili panelinin y-eksenini (fiyat) AYNI
    aralığa sabitler — aksi halde vp paneli kendi (genelde çok daha dar)
    penceresine göre otomatik ölçeklenip iki panel görsel olarak KOPUK
    görünüyordu (Görsel 2 referansında ikisi hizalı — kullanıcı geri
    bildirimiyle bulundu). `bounds` verilirse (harmonik mod — bkz.
    `_harmonic_price_bounds`) `_visible_price_bounds`'un salt mum-tabanlı
    hesabı YERİNE kullanılır."""
    if bounds is None:
        bounds = _visible_price_bounds(df, window_start_idx)
    if bounds is None:
        return
    y_range = list(bounds)
    fig.update_yaxes(range=y_range, row=1, col=1)
    if has_vp:
        fig.update_yaxes(range=y_range, row=1, col=2)


def _panel_series_for_bounds(
    name: str, series_names: list[str], result: IndicatorResult,
) -> list[pd.Series]:
    """`_draw_series_panel`'ın panel adına göre HANGİ serileri çizdiğiyle
    BİREBİR aynı eşleme -- `_sync_subpanel_yaxes`'in y-ekseni sınırlarını
    doğru serilerden hesaplaması için PAYLAŞILAN TEK kaynak (iki fonksiyon
    farklı serileri dikkate alırsa tutarsız/yanlış bir eksen üretilir)."""
    if name == "hacim":
        keys = ["volume", "volume_ma"]
    elif name == "macd":
        keys = ["macd", "macd_signal", "macd_hist"]
    elif name == "rsi":
        keys = ["rsi_14"]
    else:
        keys = series_names
    return [result.series[k] for k in keys if result.series.get(k) is not None]


def _sync_subpanel_yaxes(
    fig: go.Figure, result: IndicatorResult, sub_names: list[str],
    layout: dict[str, list[str]], df: pd.DataFrame,
    window_start_idx: int, window_end_idx: int, row_start: int = 2,
) -> None:
    """K2 düzeltmesi (2026-09-05, bkz. docs/GORSEL_HATA_TESHISI.md): `render()`
    `last_n`/pencere ile yalnızca GÖRÜNÜR X aralığını kısıtlıyor (hiçbir seri
    budanmıyor) -- ama Plotly'nin alt-panel y-ekseni OTOMATİK ölçeklemesi
    trace'in TAMAMINA bakıyordu. Sonuç: geçmişte (görünür pencerenin çok
    dışında) tek bir aykırı hacim/MACD değeri, ekseni açıp barları panelin
    dibine sıkıştırıyordu (hacim/MACD panellerinde doğrulandı; RSI doğası
    gereği 0-100 sınırlı olduğu için bu sorunu hiç yaşamıyordu -- bu
    fonksiyon RSI'ı özel olarak dışlamaz, aynı genel mantıktan geçer ama
    davranışı fiilen değişmez).

    Her panelin y-ekseni SADECE `[window_start_idx, window_end_idx]`
    aralığındaki (görünür) veriden hesaplanıp sabitlenir; taban doğal
    olarak sıfır olan seriler (hacim gibi, hiçbir değeri negatif değilse)
    için alt sınır 0'da tutulur."""
    if window_end_idx < window_start_idx or not sub_names:
        return
    start_t, end_t = df.index[window_start_idx], df.index[window_end_idx]
    for i, name in enumerate(sub_names, start=row_start):
        series_list = _panel_series_for_bounds(name, layout.get(name, []), result)
        vals: list[float] = []
        for s in series_list:
            seg = s[(s.index >= start_t) & (s.index <= end_t)].dropna()
            if len(seg):
                vals.append(float(seg.min()))
                vals.append(float(seg.max()))
        if name == "rsi":
            vals.extend([0.0, 100.0])
        if not vals:
            continue
        lo, hi = min(vals), max(vals)
        span = hi - lo
        pad = span * 0.05 if span > 0 else (abs(hi) * 0.05 or 1.0)
        lo_r, hi_r = lo - pad, hi + pad
        if name == "hacim":
            lo_r = 0.0
        elif lo >= 0 and lo_r < 0:
            lo_r = 0.0
        fig.update_yaxes(range=[lo_r, hi_r], row=i, col=1)


# ------------------------------------------------------------ jenerik mod --


def _render_price_based(
    result: IndicatorResult, df: pd.DataFrame, theme: Theme, last_n: int | None,
    declutter: bool = True,
) -> go.Figure:
    if declutter and result.indicator.startswith("patterns."):
        result = _filter_confirmed_patterns(result)
    if declutter and result.indicator.startswith("harmonic."):
        result = _filter_harmonic_result(result)
    layout = result.series_layout or {}
    sub_names = list(layout.keys())
    has_vp = any(name.startswith("vp_") for name in result.series)
    n_sub = len(sub_names)
    n_rows = 1 + n_sub
    n_cols = 2 if has_vp else 1

    # K2 düzeltmesi bölüm 3 (2026-09-05): eskiden `main_h=0.5` sabitti --
    # 3 alt panelli göstergelerde (ör. `structure.price_structure`:
    # hacim+macd+rsi) her biri toplam yüksekliğin ~%17'sini kaplıyor, ana
    # panel yalnızca yarısını alıyordu. Artık her alt panel SABİT `%15`,
    # ana panel kalanı (ama en az `%55`) alır.
    if n_sub:
        sub_h = _SUB_PANEL_H_TARGET
        main_h = 1.0 - sub_h * n_sub
        if main_h < _MAIN_PANEL_H_MIN:
            main_h = _MAIN_PANEL_H_MIN
            sub_h = (1.0 - main_h) / n_sub
        row_heights = [main_h] + [sub_h] * n_sub
    else:
        main_h = 1.0
        row_heights = [1.0]

    specs: list[list[dict[str, object] | None]] = []
    if n_cols == 2:
        specs.append([{}, {}])
        specs.extend([{"colspan": 2}, None] for _ in range(n_sub))
        column_widths = [1.0 - _VP_COLUMN_WIDTH, _VP_COLUMN_WIDTH]
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
    prz_pairs, levels = _extract_prz_pairs(levels)
    boxes, lines = result.boxes, result.lines
    if declutter:
        boxes = _declutter_single_instance_boxes(boxes)
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
        b for b in boxes if latest_box_t0 is None or b is latest_box_t0.get(b.style)
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
        if latest_line_end is None or ln is latest_line_end.get(ln.style)
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
    _draw_harmonic_vertices(fig, result, theme, row=1, col=1)
    _draw_prz_bands(fig, prz_pairs, df, theme, row=1, col=1)
    _draw_lines(
        fig, lines, df, theme, row=1, col=1, latest_end=latest_line_end,
        px_per_unit=px_per_unit, yshifts=box_level_yshifts,
    )
    _draw_levels(
        fig, levels, df, theme, row=1, col=1, px_per_unit=px_per_unit,
        yshifts=box_level_yshifts, has_vp=has_vp, edge_cutoff=edge_cutoff,
    )
    _draw_markers(fig, markers, theme, row=1, col=1, declutter=declutter, px_per_unit=px_per_unit)

    for i, name in enumerate(sub_names, start=2):
        _draw_series_panel(fig, result, name, layout[name], theme, row=i, col=1, df=df)

    if has_vp:
        _draw_volume_profile(fig, result, theme, row=1, col=2)

    # Kullanıcı geri bildirimi: alt panellerin "hangisi ne" olduğu belli
    # değildi (ör. `trend.weekly_channel`'ın kanal-pozisyonu osilatörü).
    _draw_panel_titles(theme=theme, fig=fig, n_cols=n_cols, titles_by_row={
        i: name for i, name in enumerate(sub_names, start=2)
    })

    for r in range(1, n_rows + 1):
        fig.update_xaxes(showticklabels=(r == n_rows), row=r, col=1)

    window_end_idx = _resolve_window_end(result, df)
    fig.update_xaxes(
        range=[_x(df.index[window_start_idx]), _right_padded_x(df, window_end_idx)],
        rangebreaks=_rangebreaks_for(df, result.timeframe),
    )
    # 2026-09-03 GERÇEK HATA (TRHOL/genişleyen formasyon örneğinde bulundu):
    # `patterns.*` için pencere BİTİŞİ artık (yukarıdaki `_resolve_window_
    # end` değişikliğiyle) eski örüntülerde `n-1`'den (bugün) ÇOK daha erken
    # olabiliyor, ama Y-ekseni hâlâ `_visible_price_bounds` üzerinden
    # `window_start_idx:` (BİTİŞ SINIRI OLMADAN, df'nin SONUNA kadar)
    # hesaplanıyordu — X ekseni 2025'e zoom yaparken Y ekseni hâlâ BUGÜNÜN
    # (çok daha yüksek/düşük) fiyatını da işin içine katıp mumları ekranın
    # dibine sıkıştırıyordu. `_harmonic_price_bounds` (adına rağmen
    # harmonik'e özgü bir mantık TAŞIMIYOR — yalnızca `window_start_idx`/
    # `window_end_idx` ile sınırlı mum+Polygon+Level fiyatlarını kullanıyor)
    # bu yüzden `patterns.*` için de kullanılıyor.
    custom_price_bounds = (
        _harmonic_price_bounds(result, df, window_start_idx, window_end_idx)
        if result.indicator.startswith(("harmonic.", "patterns.")) else None
    )
    _sync_price_yaxis(fig, df, window_start_idx, has_vp, bounds=custom_price_bounds)
    _sync_subpanel_yaxes(fig, result, sub_names, layout, df, window_start_idx, window_end_idx)

    header = _price_header(result)
    _apply_layout(fig, theme, header, height=600 + 180 * n_sub)
    return fig


_INDICATOR_EXPLAIN_TR: dict[str, str] = {
    # Kullanıcı geri bildirimi: "golden zone ve supply demand... ne ifade
    # ediyor belli değil" — indikatör adı tek başına yeterince açıklayıcı
    # değildi, masthead'e kısa bir tanım eklendi.
    "structure.golden_zone": (
        "Golden Zone — bir swing'in %61.8-%78.6 geri çekilme bandı "
        "(potansiyel dönüş bölgesi)"
    ),
    "structure.supply_demand": (
        "Arz/Talep Bölgeleri — güçlü bir harekete öncülük eden dar "
        "konsolidasyon bantları"
    ),
    "trend.weekly_channel": "Haftalık Trend Kanalı — regresyon/pivot kanalı + kanal içi pozisyon",
    "structure.swing_fib_abcd": "Swing Yapısı, Fibonacci ve AB=CD Analizi",
    "structure.price_structure": "Fiyat Yapısı — Destek/Direnç, Trend Çizgileri, Hacim Profili",
    "patterns.wedge": "Takoz Formasyonu",
    "patterns.triangle": "Üçgen Formasyonu",
    "patterns.head_shoulders": "Omuz Baş Omuz Formasyonu",
    "patterns.flag_pennant": "Bayrak/Flama Formasyonu",
    "patterns.double_top_bottom": "Çift Tepe/Dip Formasyonu",
    "patterns.broadening": "Genişleyen Formasyon",
    "trend.ma_systems": (
        "Çoklu MA Sistemi — kesişim, sıralama (ribbon) durumu, bant sıkışma/genişleme"
    ),
    "trend.ewmac": "EWMAC Forecast Bataryası (Carver) — çoklu ufuk trend takip sinyali",
    "momentum.alpha_rank": "Alfa Sıralaması — evren-geneli rolling-alfa (endekse göre)",
    "momentum.momentum_rank": (
        "Momentum Sıralaması — çoklu-ufuk (12-1 tarzı) momentum + RS kırılımı"
    ),
}


def _shown_harmonic_pid(result: IndicatorResult) -> str | None:
    """`result.polygons`ta (bkz. `_filter_harmonic_result` — bu noktada
    `declutter=True` iken ZATEN tek adaya indirgenmiş olur) FİİLEN çizilen
    adayın pid'ini döner. `_build_subtitle` bunu kullanır — eskiden `last_
    state`in SON dict girdisini alıyordu, ki bu GERÇEKTEN GÖSTERİLEN
    aday ile AYNI olmak ZORUNDA değildi (ör. en son eklenen aday geçersiz
    çıkıp filtre bir ÖNCEKİ, hâlâ geçerli adayı seçtiğinde başlık "[GEÇERSİZ]"
    derken grafik "[TAMAMLANDI]" bir üçgen gösterebiliyordu — gerçek veriyle
    bulunan bir tutarsızlık, bkz. CLAUDE.md)."""
    for p in result.polygons:
        if p.label.endswith("_xab"):
            return p.label[: -len("_xab")]
        if p.label.endswith("_bcd"):
            return p.label[: -len("_bcd")]
    return None


def _build_subtitle(result: IndicatorResult) -> str:
    """Masthead'in başlık satırındaki açıklama kısmı — formasyon/ekol veya
    indikatör adının okunur biçimi. Sembol BURADA tekrarlanmaz (`_Header.
    symbol` ayrı, `_draw_header` bunu öne ekler)."""
    if result.indicator in _INDICATOR_EXPLAIN_TR:
        return _INDICATOR_EXPLAIN_TR[result.indicator]
    if result.indicator.startswith("harmonic."):
        school = result.indicator.split(".", 1)[1]
        pid = _shown_harmonic_pid(result)
        info = result.last_state.get(pid) if pid is not None else None
        if info is None:
            return f"{school.title()} Formasyonu — eşleşen formasyon yok"
        pattern = str(info["pattern"]).replace("_", " ").title()
        direction_tr = tr.tr_direction(info["direction"])
        state_tr = tr.tr_state(info["state"])
        return (
            f"{pattern} Formasyonu ({direction_tr}) [{state_tr}] "
            f"— Sistem: {school.title()} — Tarama eşleşmesi"
        )
    return result.indicator.split(".", 1)[-1].replace("_", " ").title()


def _price_header(result: IndicatorResult) -> _Header:
    """Fiyat-tabanlı (jenerik/harmonik) mod için masthead içeriği — TEK
    satırlık `"{sembol} - {formasyon/indikatör açıklaması}"` (bkz. `_Header`
    docstring'i: 2026-08-30'dan itibaren fiyat/değişim/kategori/tarih
    satırları KALDIRILDI, referans ekran görüntülerinin hiçbirinde yoktu)."""
    return _Header(symbol=result.symbol or "?", subtitle=_build_subtitle(result))


def _latest_per_group(items: list, group_key, time_key) -> dict:
    """`items`ı `group_key(item)`e göre gruplar, her grubun EN GÜNCEL
    `time_key(item)`e sahip TEK öğesini döner (`{grup: öğe}`). Declutter
    modunda yalnızca bu öğe tam etiketlenir — diğerleri (aynı stilin eski/
    çözülmüş kopyaları) şekil olarak kalır, metinleri bastırılır.

    2026-09-02 GERÇEK HATA düzeltmesi: eskiden `{grup: en_yeni_zaman_DEĞERİ}`
    döndürüyordu ve çağıran taraf `item.<alan> == best[group]` (DEĞER
    eşitliği) ile karşılaştırıyordu — birden fazla öğe TAM OLARAK aynı
    zamanda bitiyorsa (ör. `trend.breakouts`'ta birçok trendline adayı
    `extend_right=True` ile AYNI son bara uzatıldığı için `points[-1][0]`
    çakışıyordu — gerçek ISCTR verisiyle bulunan bir durum: "uptrend_break
    adayı" etiketi İKİ KEZ görünüyordu) bu eşitliği paylaşan HEPSİ etiket
    alıyordu. Artık ÖĞENİN KENDİSİ döndürülür, çağıran taraf KİMLİK (`is`)
    karşılaştırması yapar — kaç öğe zamanı paylaşırsa paylaşsın kesin
    olarak TEK bir öğe (liste sırasına göre SONUNCU, `>=`) kazanır."""
    best_time: dict = {}
    best_item: dict = {}
    for it in items:
        g, t = group_key(it), time_key(it)
        if g not in best_time or t >= best_time[g]:
            best_time[g] = t
            best_item[g] = it
    return best_item


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


_VALID_PATTERN_STATES = frozenset({"confirmed", "completed"})


def _filter_confirmed_patterns(result: IndicatorResult) -> IndicatorResult:
    """Faz 8B (`patterns.*`) için: yalnızca GERÇEKTEN onaylanmış/hedefe
    ulaşmış (confirmed/completed) formasyonlar grafiğe girer — henüz
    oluşmakta olan (pending) veya başarısız (invalidated/expired) denemeler
    HİÇ ÇİZİLMEZ (kullanıcı geri bildirimi: "geçersiz olan denemeler
    gösterilmemeli, sadece tam olarak obo/tobo olan noktalar gösterilmeli").

    Bu SALT bir görsel filtredir — `result.signals`/`result.last_state`
    (tarama/SQLite kaydı, `_render_price_based`'e giden ayrı bir KOPYA
    üzerinde çalışılır) DEĞİŞMEZ, yalnızca boxes/lines/levels/markers budanır.

    Eşleştirme iki yolla yapılır: (1) Marker'lar `kind="pattern_{state}"`
    taşır (5 modülün ORTAK sözleşmesi, bkz. `pattern_state.py`) — state
    doğrudan kind'tan okunur, last_state'e bakmaya gerek YOK. (2) Line/Box/
    Level/Polygon'lar `label="{pattern_id}_{ek}"` taşır (hologram Polygon'u
    da `_hologram` ekiyle AYNI sözleşmeyi paylaşır, 2026-09-01); `pattern_id`
    `wedge.py`/`broadening.py`'de yön soneki içerir (`{...}_long`/
    `{...}_short`) ama Line/Box/Polygon etiketleri YÖNSÜZ bir `pattern_key`
    kullanır (aynı takoz/genişleyen-formasyon şekli her iki yöne de aday
    olabildiği için) — bu yüzden `valid_base_keys`, hem tam `pattern_id`'yi
    hem yön soneki kırpılmış hâlini içerir; bir label ikisinden BİRİYLE
    eşleşirse (herhangi bir yönü onaylanmışsa) şekil gösterilir."""
    valid_ids = {
        pid for pid, info in result.last_state.items()
        if info.get("state") in _VALID_PATTERN_STATES
    }
    if not valid_ids:
        return replace(result, boxes=[], lines=[], levels=[], markers=[], polygons=[])

    # 2026-09-03 GERÇEK bulgu (kullanıcının paylaştığı ATATP grafiğiyle
    # bulundu): state filtresi TEK BAŞINA yetmiyordu -- aynı şekil türü
    # (ör. TOBO) için birden fazla GEÇMİŞ onaylanmış örnek aynı anda
    # görünür kalabiliyor, üst üste binen SOL OMUZ/BAŞ/SAĞ OMUZ etiketleri
    # ve yakın tarihli AYRI formasyonların (ör. bir TOBO'nun "HEDEFE
    # ULAŞTI" etiketiyle hemen yanındaki tamamen ayrı bir OBO'nun üçgeni)
    # görsel olarak çakışması "saçma" bir grafiğe yol açıyordu. Bu,
    # harmoniklerin `_filter_harmonic_result`/`_MAX_HARMONIC_MARKERS` ile
    # çözdüğü AYNI kategori sorun -- burada da şekil türüne (TOBO/OBO,
    # yükselen/alçalan takoz, çift tepe/dip, boğa/ayı bayrağı vb., bkz.
    # `_shape_key`) göre gruplanıp yalnızca EN GÜNCEL örnek bırakılıyor.
    # `pattern_{state}:{pattern_id}` Marker kind'ı (5 formasyon dosyasına
    # da eklendi) recency kaynağı; bir sebeple bulunamazsa (beklenmedik
    # şekil uyuşmazlığı) o patern GÜVENLİ TARAFTA kalır, gizlenmez.
    def _shape_key(pid: str) -> str:
        info = result.last_state[pid]
        return str(info.get("kind") or info.get("pattern") or info.get("shape") or pid)

    marker_time: dict[str, datetime] = {}
    for m in result.markers:
        if m.kind.startswith("pattern_confirmed:") or m.kind.startswith("pattern_completed:"):
            pid = m.kind.split(":", 1)[1]
            if pid in valid_ids:
                marker_time[pid] = m.t

    latest_per_shape: dict[str, str] = {}
    latest_time: dict[str, datetime] = {}
    unresolved: set[str] = set()
    for pid in valid_ids:
        t = marker_time.get(pid)
        if t is None:
            unresolved.add(pid)
            continue
        key = _shape_key(pid)
        if key not in latest_time or t >= latest_time[key]:
            latest_time[key] = t
            latest_per_shape[key] = pid
    if latest_per_shape or unresolved:
        valid_ids = set(latest_per_shape.values()) | unresolved

    valid_base_keys: set[str] = set()
    for pid in valid_ids:
        valid_base_keys.add(pid)
        for suffix in ("_long", "_short"):
            if pid.endswith(suffix):
                valid_base_keys.add(pid[: -len(suffix)])

    def _matches(label: str) -> bool:
        return any(label == base or label.startswith(base + "_") for base in valid_base_keys)

    # 2026-09-03 GERÇEK bulgu (ODAS `patterns.triangle` render'ıyla
    # bulundu): `_target` Level'leri `wedge.py`/`broadening.py`'de YÖN-
    # ÖZGÜ `pattern_id`'den geliyor (`{pattern_key}_{direction}_target`),
    # ama yukarıdaki `_matches` yön soneki KIRPILMIŞ `pattern_key`'e göre
    # de eşleşiyor -- bu yüzden AYNI üçgen/takoz geometrisinin GEÇERSİZ
    # (invalidated) yönünün hedef çizgisi de, geçerli yönün yanında,
    # başıboş bir "Hedef" olarak sızıyordu (kaynağı belirsiz, ekrandaki
    # fiyattan çok uzak bir seviyede). Hedef Level'leri bu yüzden yalnızca
    # TAM (yön dahil) `pattern_id` ile eşleşmeli -- paylaşılan geometri
    # (sınır çizgileri/hologram/vertex marker) hâlâ yön-agnostik kalır.
    def _matches_target(label: str) -> bool:
        return any(label == pid or label.startswith(pid + "_") for pid in valid_ids)

    def _keep_marker(m: Marker) -> bool:
        if m.kind.startswith("pattern_confirmed:") or m.kind.startswith("pattern_completed:"):
            return m.kind.split(":", 1)[1] in valid_ids
        if m.kind.startswith("pattern_entry_long:") or m.kind.startswith("pattern_entry_short:"):
            # AL/SAT işareti hedef Level'i gibi YÖNE ÖZGÜ -- tam pid eşleşmeli.
            return m.kind.split(":", 1)[1] in valid_ids
        # K3 düzeltmesi (2026-09-05): KIRILIM/ONAY/HEDEF -- yeni üç işaret de
        # (bkz. `pattern_state.py::confirm_signal` çağıranları) AL/SAT gibi
        # YÖNE ÖZGÜ tam `pattern_id` ile eşleşir.
        if (
            m.kind.startswith("pattern_breakout:")
            or m.kind.startswith("pattern_retest_ok:")
            or m.kind.startswith("pattern_target_hit:")
        ):
            return m.kind.split(":", 1)[1] in valid_ids
        if m.kind.startswith("pattern_vertex:"):
            return _matches(m.kind.removeprefix("pattern_vertex:"))
        return False

    markers = [m for m in result.markers if _keep_marker(m)]
    levels = [lv for lv in result.levels if _matches_target(lv.label)]
    lines = [ln for ln in result.lines if _matches(ln.label)]
    boxes = [b for b in result.boxes if _matches(b.label)]
    polygons = [pg for pg in result.polygons if _matches(pg.label)]
    return replace(
        result, boxes=boxes, lines=lines, levels=levels, markers=markers, polygons=polygons,
    )


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
    labeled = [b for b in boxes if latest_t0 is None or b is latest_t0.get(b.style)]
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
        if latest_t0 is not None and b is not latest_t0.get(b.style):
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


# 2026-08-30 (kullanıcı geri bildirimi — "images/ klasöründeki görsellerle
# birebir aynı olacak şekilde güncelle, karmaşıklık istemiyorum artık"):
# referans harmonik ekran görüntülerinin HER BİRİ TEK BİR üçgen çifti (XAB +
# BCD) gösteriyor — hiçbirinde birden fazla aday üst üste binmiyor, ve hiçbiri
# beklemede/geçersiz/süresi dolmuş bir deneme göstermiyor. Eskiden
# `_MAX_HARMONIC_MARKERS=3` idi VE `_draw_polygons`/PRZ-fib Level'ları/X-B
# Line'ları hiç filtre uygulamadan HER adayı çiziyordu (yalnızca üçgenin köşe
# etiketleri/D kutusu kısıtlıydı) — gerçek çok-yıllık veride bu, onlarca yarı
# saydam renkli üçgenin ve PRZ/fib çizgisinin üst üste binip grafiği tam
# olarak kullanıcının tarif ettiği "rezalet" hâline getiriyordu; bir aday
# GEÇERSİZ olsa bile PRZ/X-B çizgileri hâlâ görünürdü. `_filter_harmonic_
# result()` bunu TEK bir yerde çözer (bkz. `_render_price_based`'in ilk
# satırı) — `_filter_confirmed_patterns`'ın (`patterns.*`) harmoniklere
# uyarlanmış hâli.
_MAX_HARMONIC_MARKERS = 1
_HARMONIC_VISIBLE_STATES = frozenset({"active", "confirmed", "completed"})


def _filter_harmonic_result(result: IndicatorResult) -> IndicatorResult:
    """Yalnızca EN GÜNCEL, hâlâ geçerli (aktif/tamamlanmış) harmonik adayın
    üçgenini (Polygon), köşelerini, PRZ/fib seviyelerini (Level) ve X-B/hedef
    zarfı çizgilerini (Line) bırakır; `last_state` anahtarları (pids) ile ham
    (sıralanmamış) harmonik Marker listesi indeks bazında eşleşir (bkz.
    `HarmonicIndicator.compute()` — her aday için tam olarak bir Marker, aynı
    sırada eklenir). `declutter=False` (`--show-all`) çağıran taraftan hiç
    çağrılmaz, bu fonksiyon her zaman filtreler."""
    harmonic_markers = [m for m in result.markers if m.kind.startswith("harmonic_")]
    pids = list(result.last_state.keys())
    if not pids or len(pids) != len(harmonic_markers):
        return result  # beklenmedik şekil uyuşmazlığı — güvenli tarafta kal, filtreleme

    paired = sorted(
        zip(pids, harmonic_markers, strict=True), key=lambda pm: pm[1].t, reverse=True,
    )
    valid = [
        (pid, m) for pid, m in paired
        if m.kind.removeprefix("harmonic_") in _HARMONIC_VISIBLE_STATES
    ]
    visible = {pid for pid, _m in valid[:_MAX_HARMONIC_MARKERS]}
    visible_markers = {m for _pid, m in valid[:_MAX_HARMONIC_MARKERS]}

    def _kept(label: str) -> bool:
        return any(label == pid or label.startswith(pid + "_") for pid in visible)

    return replace(
        result,
        polygons=[p for p in result.polygons if _kept(p.label)],
        levels=[lv for lv in result.levels if _kept(lv.label)],
        lines=[ln for ln in result.lines if _kept(ln.label)],
        markers=[
            m for m in result.markers
            if not m.kind.startswith("harmonic_") or m in visible_markers
        ],
    )


def _draw_polygons(
    fig: go.Figure, polygons: list[Polygon], theme: Theme, row: int, col: int,
) -> None:
    for p in polygons:
        xs = [_x(pt[0]) for pt in p.points] + [_x(p.points[0][0])]
        ys = [pt[1] for pt in p.points] + [p.points[0][1]]
        # 2026-09-02: mockup'ta klasik formasyon hologramı (`pattern_hologram`)
        # kesikli kenarlıklı ("henüz teyit gerektiren aday" hissi), harmonik
        # XAB/BCD üçgeni ise düz çizgili — bu ayrım burada da korunuyor.
        dash = "dash" if p.style == "pattern_hologram" else "solid"
        fig.add_trace(
            go.Scatter(
                x=xs, y=ys, mode="lines", fill="toself",
                line=dict(color=line_color(theme, p.style), width=1.5, dash=dash),
                fillcolor=fill_color(theme, p.style, 0.22),
                name=p.label, showlegend=False, hoverinfo="skip",
            ),
            row=row, col=col,
        )


def _draw_harmonic_vertices(
    fig: go.Figure, result: IndicatorResult, theme: Theme, row: int, col: int,
) -> None:
    """XAB/BCD üçgenlerinin gerçek fiyat pivotlarına (X, A, B, C) küçük bir
    nokta + kısa harf etiketi ekler — önceden yalnızca son D etiketi vardı,
    referans görselde ise (Görsel 5/6) A/C açıkça, X/B örtük olarak
    işaretli. D noktası burada TEKRAR etiketlenmez (`_draw_markers` zaten
    "D: fiyat [DURUM]" kutusunu çiziyor; `bcd` poligonunun 3. noktası zaten
    gerçek bir pivot değil, `prz.center`).

    `result.polygons`, `declutter=True` iken çağıran taraf (`_render_price_
    based`) tarafından `_filter_harmonic_result()` ile ZATEN tek adaya
    indirgenmiş olur — bu fonksiyon ayrıca bir seçim YAPMAZ, yalnızca ne
    varsa çizer."""
    if not result.polygons:
        return

    by_pid: dict[str, dict[str, Polygon]] = {}
    for p in result.polygons:
        if p.label.endswith("_xab"):
            by_pid.setdefault(p.label[: -len("_xab")], {})["xab"] = p
        elif p.label.endswith("_bcd"):
            by_pid.setdefault(p.label[: -len("_bcd")], {})["bcd"] = p

    for parts in by_pid.values():
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


def _extract_prz_pairs(levels: list[Level]) -> tuple[list[tuple[Level, Level]], list[Level]]:
    """`{pid}_prz_low`/`{pid}_prz_high` Level çiftlerini (bkz.
    `scanner_indicator.py`'nin PRZ üretimi) ayırır. Dönüş: (eşleşen çiftler,
    geri kalan Level'lar — eşleşmeyen tek bir prz_low/high dahil, ör. aktif
    bir adayda henüz PRZ oluşmamışsa normal çizgi olarak çizilmeye devam
    eder)."""
    by_pid: dict[str, dict[str, Level]] = {}
    others: list[Level] = []
    for lv in levels:
        if lv.label.endswith("_prz_low"):
            by_pid.setdefault(lv.label[: -len("_prz_low")], {})["low"] = lv
        elif lv.label.endswith("_prz_high"):
            by_pid.setdefault(lv.label[: -len("_prz_high")], {})["high"] = lv
        else:
            others.append(lv)
    pairs: list[tuple[Level, Level]] = []
    for parts in by_pid.values():
        low, high = parts.get("low"), parts.get("high")
        if low is not None and high is not None:
            pairs.append((low, high))
        else:
            others.extend(parts.values())
    return pairs, others


def _draw_prz_bands(
    fig: go.Figure, pairs: list[tuple[Level, Level]], df: pd.DataFrame, theme: Theme,
    row: int, col: int,
) -> None:
    """PRZ alt/üst çiftini iki ayrı kesikli çizgi+etiket YERİNE tek bir yarı
    saydam dolgulu bant + ortak "Hedef Bölge (PRZ): low–high" etiketiyle
    çizer — "Grafik Stil Vitrini" mockup'ının (`harmonicPanel`) PRZ
    dolgusuyla birebir aynı görsel dil (bkz. proje planı, 2026-09-01)."""
    first_x, last_x = df.index[0], df.index[-1]
    for low, high in pairs:
        x0 = low.start if low.start is not None else first_x
        x1 = low.end if low.end is not None else last_x
        fig.add_shape(
            type="rect", x0=_x(x0), x1=_x(x1), y0=low.price, y1=high.price,
            fillcolor=with_alpha(theme.accent, 0.12),
            line=dict(color=theme.accent, width=1, dash="dash"),
            row=row, col=col,
        )
        fig.add_annotation(
            x=_x(x0), y=high.price, xanchor="left", yanchor="bottom",
            text=f"Hedef Bölge (PRZ): {low.price:.1f}–{high.price:.1f}",
            showarrow=False, font=dict(size=10, color=theme.accent, family=theme.font),
            row=row, col=col,
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
                if latest_end is None or ln is latest_end.get(ln.style)
            ],
            px_per_unit=px_per_unit, step=14.0,
        )

    for ln in lines:
        color = line_color(theme, ln.style)
        style_dash = _DASH_FOR_STYLE.get(ln.style, "solid")
        # K1 düzeltmesi (2026-09-05, bkz. docs/GORSEL_HATA_TESHISI.md):
        # eskiden yalnızca İLK ve SON nokta alınıp aralarına düz bir doğru
        # çiziliyordu -- 2 noktalı bir trendline/kanal/hedef-projeksiyonu
        # için matematiksel olarak zararsızdı, ama `trend.ma_systems`'ın her
        # EMA'sının TAM (çok-noktalı) serisini tek bir Line'da taşıdığı
        # durumda EMA'yı yatay bir doğruya çöktürüyordu. Artık TAM polyline
        # çizilir; 2 noktalı Line'ların davranışı DEĞİŞMEZ (xs/ys sırasıyla
        # [t0,t1]/[p0,p1] ile birebir aynı).
        t0, p0 = ln.points[0]
        t1, p1 = ln.points[-1]
        xs = [_x(t) for t, _ in ln.points]
        ys = [p for _, p in ln.points]
        # 2026-09-04 GERÇEK bulgu (flag_pennant "Direk" hiç görünmüyordu --
        # kullanıcı: "sistemde bu görselle alakası olmayan şekiller
        # oluşuyor"): direk çizgisi `extend_right=False` olduğu için
        # aşağıdaki `if ext is None: continue` onu HİÇ etikete uğratmadan
        # atlıyordu -- `_line_extensions` yalnızca `extend_right=True` olan
        # çizgileri işliyor. Direk zaten sağa uzamayan, sabit bir bacak
        # (formasyonun KENDİSİ, bir sınır/projeksiyon değil) -- bu yüzden
        # uzatma mekanizmasına girmeden, KENDİ orta noktasına, daha kalın
        # bir çizgiyle etiketleniyor (mockup'taki "DİREK" pill'inin sade
        # karşılığı).
        is_pole = ln.style == "pattern_pole"
        fig.add_trace(
            go.Scatter(
                x=xs, y=ys, mode="lines",
                line=dict(color=color, width=2.4 if is_pole else 1.6, dash=style_dash),
                name=ln.label, showlegend=False, hoverinfo="skip",
            ),
            row=row, col=col,
        )
        if is_pole:
            mid_t = t0 + (pd.Timestamp(t1) - pd.Timestamp(t0)) / 2
            fig.add_annotation(
                x=_x(mid_t), y=(p0 + p1) / 2, text=_display_text(ln.label, ln.style),
                showarrow=False, font=dict(size=10, color=color, family=theme.font),
                bgcolor=with_alpha(theme.bg, 0.75), xanchor="right", yanchor="bottom",
                yshift=6, row=row, col=col,
            )
            continue
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
        if latest_end is not None and ln is not latest_end.get(ln.style):
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


# 2026-09-02: `structure.golden_zone`/`structure.supply_demand` gerçek
# çok-aylık veride HER swing/taban için bir Box üretir — mockup ise (ve
# kullanıcının "sade, karmaşık değil" isteği) yalnızca EN GÜNCEL örneği
# gösteriyor. Önceki tasarım kararı ("her biri farklı bir bölgeye ait,
# bilgi kaybı olur" — bkz. `_DECLUTTER_GENERIC_KINDS` docstring'i) az
# sayıda örnek varsayıyordu; gerçek ALARK/ASELS verisiyle bu varsayım
# YANLIŞ çıktı (düzinelerce kutu üst üste bindi). `_draw_boxes` diğer
# stiller (resistance_zone/support_zone/range_box) için TÜM şekilleri
# BİLEREK korumaya devam ediyor (orada birden fazla eşzamanlı seviye
# anlamlı) — bu fonksiyon yalnızca "tek-örnek" ailesini kısıtlar.
_SINGLE_INSTANCE_BOX_STYLES = frozenset(
    {"golden_zone", "golden_zone_alt", "demand", "supply", "demand_broken", "supply_broken"}
)


def _declutter_single_instance_boxes(boxes: list[Box], keep_recent: int = 1) -> list[Box]:
    rest = [b for b in boxes if b.style not in _SINGLE_INSTANCE_BOX_STYLES]
    by_style: dict[str, list[Box]] = {}
    for b in boxes:
        if b.style in _SINGLE_INSTANCE_BOX_STYLES:
            by_style.setdefault(b.style, []).append(b)
    kept = list(rest)
    for group in by_style.values():
        starts = sorted({b.t0 for b in group}, reverse=True)
        keep = set(starts[:keep_recent])
        kept.extend(b for b in group if b.t0 in keep)
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


# 2026-08-30: kullanıcı geri bildirimi — eskiden TÜM durumlar (pending/
# active/confirmed) invalidated HARİÇ aynı yeşili alıyordu ("bearish" if
# state=="invalidated" else "bullish"), yani "sinyal gerçekten geldi mi
# (confirmed) yoksa henüz mi (pending/active)" sorusunun cevabı görsel
# olarak AYIRT EDİLEMİYORDU. Artık her durumun KENDİ rengi var: `confirmed`/
# `completed` (sinyal GELDİ) `accent` (projedeki "en karara-değer" marka
# rengi — bkz. themes.py); `active` (yaklaşıyor) `orange`; `pending` (yeni
# doğdu, henüz erken) `gray`; `invalidated`/`expired` (artık geçerli değil)
# `red`/`gray`. `pending`/`invalidated`/`expired` fiilen HİÇ ÇİZİLMEZ artık
# (bkz. `_HARMONIC_VISIBLE_STATES`) — renkleri yalnızca `declutter=False`
# ("--show-all") modunda kullanılır.
_HARMONIC_STATE_COLOR: dict[str, str] = {
    "confirmed": "accent", "completed": "accent", "active": "orange", "pending": "gray",
    "invalidated": "red", "expired": "gray",
}


# Faz 8B (patterns/*): `_filter_confirmed_patterns` zaten yalnızca
# confirmed/completed marker'ları bıraktığı için burada declutter'a GEREK
# YOK — outcome marker'ı (`pattern_{state}`) harmonik `confirmed` durumuyla
# AYNI muamele (renkli/kalın kutu+ok) alır; `pattern_vertex:{pid}` (SOL
# OMUZ/BAŞ/SAĞ OMUZ, çift tepe/dip "1"/"2") harmonik X/A/B/C vertex'leriyle
# AYNI halo'lu (bgcolor) düz metin muamelesi alır — ikisi de "harmonikler
# gibi net çizilmeli" geri bildirimine karşılık gelir.
_PATTERN_OUTCOME_COLOR: dict[str, str] = {"confirmed": "accent", "completed": "green"}


# 2026-09-02: "her kategoriden 1" tek başına yetersizdi — `trend.breakouts`
# ~20 farklı break_type üretir, kategori-başına-1 bile 15-20 uzun ("Kırılım:
# YUKARI | channel_break_up | Temas:0 | Hacim ×1.4 | Q:58" gibi) etiketin
# AYNI ANDA üst üste binmesine yol açıyordu (gerçek ISCTR verisiyle bulunan,
# kullanıcının "rezalet" diye tarif ettiği durum). Kategori bütçesi
# KORUNUYOR (bir tür diğerini tamamen dışlamasın diye), ama tüm kategoriler
# TOPLANDIKTAN SONRA global bir üst sınıra (`_MAX_GENERIC_MARKERS_TOTAL`) da
# tabi tutuluyor — yalnızca en güncel N tanesi görünür kalır.
_MAX_GENERIC_MARKERS_PER_GROUP = 1
_MAX_GENERIC_MARKERS_TOTAL = 4
# Yalnızca BU kind için sıkı declutter uygulanır (bkz. `_generic_marker_
# group_key` docstring'i) — `structure.golden_zone`/`structure.supply_
# demand`'ın "REAKSİYON"/"BAŞARILI"/"KIRILDI" gibi generic marker'ları
# ZATEN az sayıda ve HER biri farklı bir swing/bölgeye ait, bilgi taşıyan
# bir geçmiş (kutu declutter'ı gibi "yalnızca en güncel" uygulamak burada
# BİLGİ KAYBI olurdu — sorun yalnızca `trend.breakouts`'ta gözlemlendi).
_DECLUTTER_GENERIC_KINDS = frozenset({
    "breakout",
    # golden_zone.py / supply_demand.py — bkz. `_declutter_single_instance_
    # boxes` docstring'i, AYNI gerekçe: gerçek veride onlarca "REAKSİYON"/
    # "BAŞARILI"/"BAŞARISIZ"/"KIRILDI" markerı üst üste biniyordu.
    "golden_zone_reaction", "golden_zone_fail", "golden_zone_success",
    "sd_reaction", "sd_new", "sd_test", "sd_broken",
})


def _generic_marker_group_key(m: Marker) -> str:
    """`trend.breakouts` (`MultiBreakout`) TÜM markerlerini AYNI `kind`
    ("breakout") altında toplar — gerçek kategori (`channel_break_up`/
    `donchian_break_down`/`zone_touch` vb., ~20 tür) yalnızca `Marker.text`in
    içine gömülü (`"Kırılım: YUKARI | {break_type} | ..."`, bkz. `breakouts.
    py::_emit_break`). Bu ayrıştırma OLMADAN declutter tek bir paylaşılan
    "en güncel N" bütçesi uygulardı — sık tekrar eden bir tür (ör.
    `zone_touch`) nadir ama önemli bir türü (ör. `channel_break_up`) bütçeden
    dışlayabilirdi (gerçek TCELL verisiyle bulunan bir davranış: 2 yıllık
    veride 282 kırılım olayı TEK panelde üst üste binip grafiği tamamen
    okunmaz kılıyordu). `"|"` içermeyen (bu deseni izlemeyen) genel
    marker'lar için `kind`e düşer."""
    parts = m.text.split("|")
    return f"{m.kind}:{parts[1].strip()}" if len(parts) >= 2 else m.kind


def _short_generic_text(m: Marker) -> str:
    """`_generic_marker_group_key`'in ayrıştırdığı uzun cümleyi (ör. "Kırılım:
    YUKARI | channel_break_up | Temas:0 | Hacim ×1.4 | Q:58") grafik üzerinde
    okunur kalacak kısa bir "yön oku + tür" etiketine indirger (ör. "▲
    channel_break_up") — Temas/Hacim/Q gibi ayrıntılar annotation'ın
    `hovertext`'ine taşınır, bilgi kaybı yok, yalnızca varsayılan görünüm
    sadeleşiyor."""
    parts = [p.strip() for p in m.text.split("|")]
    arrow = "▲" if "YUKARI" in parts[0].upper() else "▼" if "AŞAĞI" in parts[0].upper() else ""
    kind = parts[1] if len(parts) >= 2 else parts[0]
    return f"{arrow} {kind}".strip()


def _draw_markers(
    fig: go.Figure, markers: list[Marker], theme: Theme, row: int, col: int,
    declutter: bool = True, px_per_unit: float = 1.0,
) -> None:
    harmonic_markers = sorted(
        (
            m for m in markers
            if m.kind.startswith("harmonic_")
            and m.kind.removeprefix("harmonic_") in _HARMONIC_VISIBLE_STATES
        ),
        key=lambda m: m.t, reverse=True,
    )
    # declutter: her okulda onlarca aday birikebilir (özellikle uzun/gürültülü
    # gerçek veride) — beklemede/geçersiz/süresi dolmuş denemeler yukarıda
    # ZATEN elendi; kalan (aktif/tamamlandı) adaylardan da yalnızca EN GÜNCEL
    # `_MAX_HARMONIC_MARKERS` (=1) tanesi "D: fiyat [DURUM]" kutusu alır —
    # referans ekran görüntülerinin hepsi TEK bir aday gösteriyor.
    visible_harmonic = set(harmonic_markers[:_MAX_HARMONIC_MARKERS]) if declutter else None

    # Jenerik (structure_label/harmonic_*/pair_signal DIŞINDAKİ, ör.
    # `trend.breakouts`'un "breakout" kind'li) marker'lar — HER kategoriden
    # (bkz. `_generic_marker_group_key`) yalnızca EN GÜNCEL örnek etiketlenir.
    # Level'lardaki gibi (`_declutter_levels`) TAMAMEN gizlenir (şekil değil,
    # salt metin olduğu için "eski + bağlamsız" gösterimin bir anlamı yok).
    visible_generic: set[Marker] | None = None
    if declutter:
        by_group: dict[str, list[Marker]] = {}
        for m in markers:
            if m.kind not in _DECLUTTER_GENERIC_KINDS:
                continue
            by_group.setdefault(_generic_marker_group_key(m), []).append(m)
        visible_generic = set()
        for group in by_group.values():
            group.sort(key=lambda m: m.t, reverse=True)
            visible_generic.update(group[:_MAX_GENERIC_MARKERS_PER_GROUP])
        if len(visible_generic) > _MAX_GENERIC_MARKERS_TOTAL:
            newest = sorted(visible_generic, key=lambda m: m.t, reverse=True)
            visible_generic = set(newest[:_MAX_GENERIC_MARKERS_TOTAL])

    # 2026-09-02 GERÇEK HATA düzeltmesi: `visible_generic`e kadar birden
    # fazla FARKLI kategori (ör. "zone_break_down"/"ma_break_ema50_up")
    # kalabiliyor (bilerek — her biri farklı bilgi taşıyor, tek bir örneğe
    # indirgemek bilgi kaybı olurdu), ama HEPSİ sabit `yshift=10` kullanıyordu
    # — gerçek ISCTR verisiyle bulunan bir durum: aynı fiyat/zaman civarına
    # düşen 2-3 marker'ın metni üst üste binip okunmaz bir "harf çorbası"
    # oluşturuyordu. `_stagger_yshifts` (Level/Box etiketlerinin ZATEN
    # kullandığı "cetvel" sezgisi) burada da uygulanır.
    generic_yshifts = (
        _stagger_yshifts(
            [(m, m.price, 10.0) for m in visible_generic], px_per_unit=px_per_unit, step=14.0,
        )
        if visible_generic else {}
    )

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
            color = getattr(theme, _HARMONIC_STATE_COLOR.get(state, "gray"))
            # `confirmed` (sinyal fiilen GELDİ) kalın/dolgulu bir kutuyla
            # diğerlerinden (ince kenarlıklı) ayrılır — yalnızca renk
            # yeterince göze çarpmayabilir (ör. accent altın tonu, ince bir
            # çizgide soluk kalabilir).
            confirmed = state == "confirmed"
            # 2026-09-01: mockup'taki (`Grafik Stil Vitrini`) D rozeti TAM
            # dolgulu bir "pill" — eskiden `confirmed` durumda bile yalnızca
            # %15 opaklıkta dolgu kullanılıyordu, mockup'la birebir eşleşmesi
            # için `confirmed` artık tam opak dolgu + zıt renkte metin alır
            # (`badgeStyle` ilkesi: `dark_terminal`in parlak altın vurgusunda
            # koyu metin, diğer temaların daha mat altın/kahve vurgusunda
            # beyaz metin — ikisi de mockup'ın kendi kararı).
            bgcolor = color if confirmed else with_alpha(color, 0.15)
            confirmed_text = "#0a0c10" if theme.name == "dark_terminal" else "#ffffff"
            text_color = confirmed_text if confirmed else theme.text
            fig.add_annotation(
                x=_x(m.t), y=m.price, text=f"<b>{m.text}</b>" if confirmed else m.text,
                showarrow=True, arrowhead=2, arrowcolor=color, arrowwidth=2 if confirmed else 1,
                font=dict(size=11, color=text_color), bgcolor=bgcolor,
                bordercolor=color, borderwidth=2 if confirmed else 1,
                ax=30, ay=-30, row=row, col=col,
            )
        elif m.kind == "pair_signal":
            continue  # yalnızca pair modunda, _render_pair kendi çizer
        elif m.kind.startswith("pattern_confirmed:") or m.kind.startswith("pattern_completed:"):
            # 2026-09-02: harmonik D rozetinin "confirmed = tam dolgulu pill"
            # düzeltmesiyle AYNI — mockup'ın "TOBO · ONAY"/"BAYRAK · DEVAM"
            # rozetleri de HER ZAMAN solid dolgu (bu iki durum zaten "sinyal
            # arrived" anlamına geliyor, harmonikteki pending/active gibi ayrı
            # bir "henüz gelmedi" hâli YOK).
            # 2026-09-03: kind artık `pattern_{state}:{pattern_id}` (aynı
            # şekildeki eski/çakışan örnekleri ayırt edip declutter etmek
            # için `_filter_confirmed_patterns`'a eklendi) — `:` öncesi kısım
            # state'i taşır.
            state = m.kind.split(":", 1)[0].removeprefix("pattern_")
            color = getattr(theme, _PATTERN_OUTCOME_COLOR[state])
            confirmed_text = "#0a0c10" if theme.name == "dark_terminal" else "#ffffff"
            fig.add_annotation(
                x=_x(m.t), y=m.price, text=f"<b>{m.text}</b>",
                showarrow=True, arrowhead=2, arrowcolor=color, arrowwidth=2,
                font=dict(size=11, color=confirmed_text), bgcolor=color,
                bordercolor=color, borderwidth=2, ax=30, ay=-30, row=row, col=col,
            )
        elif m.kind.startswith("pattern_entry_long:") or m.kind.startswith("pattern_entry_short:"):
            # 2026-09-04: kullanıcı "nerede AL sinyali geldiğini de yazman
            # gerekiyor" dedi -- mockup'taki (Breakout→FVG sahnesi) dolgulu
            # üçgen + kalın "AL"/"SAT" metniyle AYNI dil, gerçek ONAY
            # rozetinin (`pattern_confirmed:`) TAM AYNI nokta/bar'ında,
            # ayrı ve göze çarpan bir işaret olarak eklenir.
            is_long = m.kind.startswith("pattern_entry_long:")
            color = theme.up if is_long else theme.down
            # 2026-09-04 GERÇEK bulgu (AKBNK flag_pennant'ta bulundu): SAT
            # işareti eskiden fiyatın ÜSTÜNE (yukarı) yerleşiyordu -- ama
            # `pattern_confirmed:`/`pattern_completed:` onay rozeti HER
            # ZAMAN yukarı-sağa sabit (`ax=30, ay=-30`) yerleşiyor, yön
            # farketmeksizin -- ikisi ÇAKIŞIYORDU ("SAT" yazısı "BAYRAK
            # [HEDEFE ULAŞTI]" rozetinin İÇİNE gömülmüştü). Artık AL/SAT
            # HER ZAMAN aşağı yerleşiyor (rozetin ZATEN işgal ettiği yukarı
            # bölgeden kaçınmak için), yalnızca ok yönü/renk/metin değişir.
            tri_shift, text_shift = -16, -32
            fig.add_annotation(
                x=_x(m.t), y=m.price, text="▲" if is_long else "▼",
                showarrow=False, font=dict(size=15, color=color),
                yshift=tri_shift, row=row, col=col,
            )
            fig.add_annotation(
                x=_x(m.t), y=m.price, text=f"<b>{'AL' if is_long else 'SAT'}</b>",
                showarrow=False, font=dict(size=11, color=color, family=theme.font),
                bgcolor=with_alpha(theme.bg, 0.85), yshift=text_shift, row=row, col=col,
            )
        elif m.kind.startswith("pattern_breakout:"):
            # K3 düzeltmesi (2026-09-05, bkz. docs/GORSEL_HATA_TESHISI.md):
            # "KIRILIM" -- kırılım çizgisinin/boynun/trendline'ın kapanışla
            # aşıldığı bar (`confirm_signal()`ın bulduğu `*_confirmed`
            # olayı). İçi boş daire + önder çizgi (ok gövdesi, `arrowhead=0`)
            # + metin -- AL/SAT'ın (dolgulu üçgen) BİR ADIM ÖNCESİ, aynı
            # barda çakışabilir (bilerek -- ikisi FARKLI bilgi taşır: biri
            # "fiyat kırdı", diğeri "giriş noktası").
            color = theme.blue
            fig.add_trace(
                go.Scatter(
                    x=[_x(m.t)], y=[m.price], mode="markers",
                    marker=dict(
                        symbol="circle-open", size=10,
                        line=dict(width=2, color=color),
                    ),
                    showlegend=False, hoverinfo="skip",
                ),
                row=row, col=col,
            )
            fig.add_annotation(
                x=_x(m.t), y=m.price, text="KIRILIM", showarrow=True, arrowhead=0,
                arrowcolor=color, arrowwidth=1.3, ax=0, ay=-26,
                font=dict(size=10, color=color, family=theme.font),
                bgcolor=with_alpha(theme.bg, 0.8), row=row, col=col,
            )
        elif m.kind.startswith("pattern_retest_ok:"):
            # "ONAY" -- kırılım seviyesine geri dönüp TUTMA (retest_hold)
            # barı. İçi dolu daire (kırılımın "içi boş" dairesinden ayırt
            # edilsin diye) + metin.
            color = theme.accent
            fig.add_trace(
                go.Scatter(
                    x=[_x(m.t)], y=[m.price], mode="markers",
                    marker=dict(symbol="circle", size=9, color=color),
                    showlegend=False, hoverinfo="skip",
                ),
                row=row, col=col,
            )
            fig.add_annotation(
                x=_x(m.t), y=m.price, text="ONAY", showarrow=True, arrowhead=0,
                arrowcolor=color, arrowwidth=1.3, ax=0, ay=22,
                font=dict(size=10, color=color, family=theme.font),
                bgcolor=with_alpha(theme.bg, 0.8), row=row, col=col,
            )
        elif m.kind.startswith("pattern_target_hit:"):
            # "HEDEF ✓" -- hedefe ulaşma barı, küçük başarı rozeti (genel
            # durum rozetinin -- `pattern_completed:` -- AYNI barda olması
            # BEKLENİR, bu YİNE DE ayrı/ek bir işarettir, bkz. görev metni).
            # Genel durum rozeti HER ZAMAN yukarı-sağa yerleşiyor (`ax=30,
            # ay=-30`) -- aynı bara denk geldiklerinde üst üste binmesinler
            # diye HEDEF rozeti bilinçli olarak AŞAĞI-SOLA yerleşir.
            color = theme.green
            confirmed_text = "#0a0c10" if theme.name == "dark_terminal" else "#ffffff"
            fig.add_annotation(
                x=_x(m.t), y=m.price, text="<b>HEDEF ✓</b>", showarrow=True,
                arrowhead=2, arrowcolor=color, arrowwidth=1.6,
                font=dict(size=10, color=confirmed_text), bgcolor=color,
                bordercolor=color, borderwidth=1.5, ax=-34, ay=30, row=row, col=col,
            )
        elif m.kind.startswith("pattern_vertex:"):
            fig.add_annotation(
                x=_x(m.t), y=m.price, text=m.text, showarrow=False,
                font=dict(size=11, color=theme.text, family=theme.font),
                bgcolor=with_alpha(theme.bg, 0.75), yshift=14, row=row, col=col,
            )
        else:
            if (
                visible_generic is not None
                and m.kind in _DECLUTTER_GENERIC_KINDS
                and m not in visible_generic
            ):
                continue
            text = _short_generic_text(m) if m.kind in _DECLUTTER_GENERIC_KINDS else m.text
            fig.add_annotation(
                x=_x(m.t), y=m.price, text=text, showarrow=False, hovertext=m.text,
                font=dict(size=10, color=theme.muted),
                yshift=generic_yshifts.get(m, 10.0), row=row, col=col,
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


_PANEL_TITLE_TR: dict[str, str] = {
    "hacim": "Hacim",
    "macd": "MACD (Trend Momentumu)",
    "rsi": "RSI (Göreceli Güç Endeksi)",
    "channel_position": "Kanal İçi Pozisyon (%)",
    # Faz 8D (momentum.alpha_rank/momentum_rank, trend.ma_systems/ewmac)
    "vs_endeks": "Hisse vs Endeks (Normalize)",
    "alfa_t_istatistik": "Yıllık Alfa + T-İstatistiği",
    "beta": "Beta (Endekse Göre)",
    "kumulatif_epsilon": "Kümülatif Artık Getiri (ε)",
    "rs": "Rölatif Güç (RS)",
    "rs_egim_t_istatistik": "RS Eğimi + T-İstatistiği",
    "ufuklar": "Ufuklara Göre Momentum",
    "fip": "FIP (Trend Tutarlılığı)",
    "bant_genisligi": "MA Bant Genişliği (Sıkışma/Genişleme)",
    "ewmac": "EWMAC Forecast (Carver)",
}


def _draw_panel_titles(
    fig: go.Figure, theme: Theme, titles_by_row: dict[int, str], n_cols: int = 1,
) -> None:
    """Her alt panelin SOL ÜST köşesine küçük bir başlık ekler — kullanıcı
    geri bildirimi: "hangisi ne belli değil" (RSI/Hacim/MACD paneli
    birbirinden ayırt edilemiyordu, ne gösterdiği anlaşılmıyordu).
    `titles_by_row`: `{satır_no: panel_adı}` (panel_adı `series_layout`
    anahtarı, ör. "rsi") — `_PANEL_TITLE_TR`'de bilinmeyen bir ad gelirse
    olduğu gibi (Title Case) gösterilir. `n_cols`: 1. satırın kaç eksen
    TÜKETTİĞİ (vp paneli varsa 2, yoksa 1).

    **Gerçek hata** (TCELL'de bulundu): Plotly eksen numaralandırması
    SATIR-ÖNCELİKLİ ve `specs`teki HER hücreye (`None` hariç) ayrı bir sayı
    verir — vp paneli varken 1. satır TEK DEĞİL İKİ eksen tüketir (yaxis +
    yaxis2), bu yüzden 2. satırın (ör. "hacim") KENDİ ekseni `yaxis2`
    DEĞİL, `yaxis3`'tür. Bu ayrım gözden kaçırılınca "Hacim" başlığı
    yanlışlıkla vp panelinin (row=1, col=2) üstüne çiziliyordu — konum
    HESAPLANMIYOR, `fig.layout`'taki GERÇEK domain'den okunuyor olsa da,
    YANLIŞ eksene bakılırsa yine de yanlış yere iner."""
    for row, name in titles_by_row.items():
        axis_num = row if row == 1 else n_cols + (row - 1)
        yaxis_name = "yaxis" if axis_num == 1 else f"yaxis{axis_num}"
        yaxis = getattr(fig.layout, yaxis_name, None)
        if yaxis is None or yaxis.domain is None:
            continue
        text = _PANEL_TITLE_TR.get(name, name.replace("_", " ").title())
        fig.add_annotation(
            x=0.005, y=yaxis.domain[1] - 0.008, xref="paper", yref="paper",
            xanchor="left", yanchor="top", text=f"<b>{text}</b>", showarrow=False,
            font=dict(size=10.5, color=theme.muted, family=theme.font),
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
    # Çubuklar arasında BOŞLUK bırakılmaz (`width`, bin merkezleri arası
    # mesafeye eşitlenir) — referans ekran görüntüsündeki gibi "dolu dolu",
    # birbirine bitişik bir histogram görünümü (varsayılan `bargap` global
    # bir figür ayarıdır, bu TEK trace'e özgü boşluksuzluk `width` ile
    # sağlanır). Kullanıcı geri bildirimi: eski hâli ince/aralıklı
    # çubuklarla "cılız" görünüyordu.
    bin_centers = bins.to_numpy()
    bin_height = (
        float(bin_centers[1] - bin_centers[0]) if len(bin_centers) > 1 else 1.0
    )
    fig.add_trace(
        go.Bar(
            x=vols.to_numpy(), y=bin_centers, orientation="h", marker_color=colors,
            width=bin_height, name="Hacim Profili", showlegend=False,
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

    # Sağ kenarda bilinçli bir boşluk payı — kullanıcı geri bildirimi:
    # çubuklar/Gaussian eğrisi panelin sağ ÇERÇEVESİNE fazla yakın/bitişik
    # duruyordu ("kendi alanının içine" konması istendi). Plotly'nin
    # varsayılan autorange'i zaten küçük bir pay bırakır, ama bar+eğri
    # ikisi de AYNI (max hacim) tepe noktasına ulaştığı için bu pay yetersiz
    # kalıyordu — burada GERÇEK veriden (bar/eğri, hangisi büyükse) hesaplanan
    # açık bir %12'lik pay veriliyor.
    max_x = float(vols.max())
    if gauss is not None and not gauss.empty:
        max_x = max(max_x, float(gauss.max()))
    if max_x > 0:
        fig.update_xaxes(range=[0, max_x * 1.12], row=row, col=col)


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
    vp panelinin (row=1, col=2) KENDİ x/y domain'inin SAĞ-ÜST köşesine,
    panelin İÇİNE yerleştirir — `_apply_pair_legends`'daki "sabit kesir
    varsayma, gerçek domain'i oku" ilkesiyle AYNI (make_subplots'ın column_
    widths/row_heights'tan hesapladığı domain, sabit bir sayı değil).
    **Gerçek hata (ilk taslak)**: `yanchor="bottom"` ile domain'in HEMEN
    ÜSTÜNE (`y1+0.015`) yerleştirilmişti — ama bir legend kutusu `yanchor=
    "bottom"` iken YUKARI doğru büyür, bu da onu masthead'in (sembol/fiyat
    satırı) tam ÜSTÜNE bindiriyordu (ASELS'te "404.00" fiyatıyla görsel
    olarak iç içe geçmişti). Düzeltme: `yanchor="top"`, panelin KENDİ üst
    kenarının hemen altına (panelin İÇİNE, bar'ların üstüne biner — hafif
    saydam arkaplanla okunur kalır) — artık panel yüksekliğinden BAĞIMSIZ
    olarak asla masthead'e taşmaz."""
    x1 = fig.layout.xaxis2.domain[1]
    y1 = fig.layout.yaxis2.domain[1]
    fig.update_layout(
        legend2=dict(
            x=x1, y=y1 - 0.005, xanchor="right", yanchor="top", orientation="v",
            bgcolor=with_alpha(theme.bg, 0.85), bordercolor=theme.border, borderwidth=1,
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


def render_structure_report(
    ps_result: IndicatorResult, sf_result: IndicatorResult, df: pd.DataFrame,
    *, gz_result: IndicatorResult | None = None, sd_result: IndicatorResult | None = None,
    theme: Theme | str | None = "auto", last_n: int | None = None, declutter: bool = True,
) -> go.Figure:
    """`structure.price_structure` + `structure.swing_fib_abcd` çıktısını TEK
    grafikte birleştirir. Ana panel (zone/trendline/POC-VAH-VAL + swing yapı
    etiketleri + fib merdiveni + AB=CD hedefleri) yalnızca `last_n`
    penceresine yakınlaşır; hacim/MACD/RSI alt panelleri TAM GEÇMİŞİ gösterir
    (referans mockup'ın kendi tasarımı — ana panel "şu an"a odaklanırken alt
    osilatörler uzun vadeli bağlamı korur, bu yüzden `shared_xaxes=False` —
    aksi halde Plotly satırların x-eksenini birbirine kilitleyip ana panelin
    zoom'unu alt panellere de yansıtırdı).

    **2026-08-30 NOT — "Özet Raporu" görselden ÇIKARILDI**: ilk taslak
    grafiğin sağına 3. bir kolon olarak deterministik bir metin paneli
    ekliyordu; kullanıcı bunu beğenmedi ("görselde vermeyelim... metin
    olarak verelim") — anlatı artık GÖRSELİN DIŞINDA, ayrı bir metin
    olarak `tlab/viz/quant_report.py::generate_quant_report()` (gerçek bir
    LLM çağrısıyla, "quant gibi" serbest metin) tarafından üretiliyor. Bu
    fonksiyon artık YALNIZCA `_render_price_based` ile AYNI 2 kolonlu
    (mum+vp) düzeni kullanıyor — tek farkı iki (opsiyonel olarak DÖRT)
    `IndicatorResult`'ı birleştirmesi ve alt panellerin tam geçmiş
    göstermesi.

    **2026-08-30 ikinci düzeltme — `gz_result`/`sd_result` (opsiyonel)**:
    kullanıcı "golden zone ve supply demand kısımlarını structure reporta
    koymamız gerekmiyor mu" diye sordu — `structure.golden_zone`/`structure.
    supply_demand`'ın Box/Level/Line/Marker'ları verilirse AYNI birleşik
    çizim/declutter/stagger hattına (`_draw_boxes`/`_draw_levels`/
    `_stagger_yshifts`) katılır; verilmezse (ör. eski çağıranlar/testler)
    davranış DEĞİŞMEZ, yalnızca iki indikatörlü eski görünüm kalır."""
    resolved = resolve_theme(theme, default=LIGHT_ANALYSIS)

    sub_names = list(ps_result.series_layout.keys())
    n_sub = len(sub_names)
    n_rows = 1 + n_sub
    # K2 düzeltmesi bölüm 3 (2026-09-05) -- `_render_price_based`'in AYNI
    # panel-yüksekliği standardı: ana panel >= %55, alt panel <= %15.
    if n_sub:
        sub_h = _SUB_PANEL_H_TARGET
        main_h = 1.0 - sub_h * n_sub
        if main_h < _MAIN_PANEL_H_MIN:
            main_h = _MAIN_PANEL_H_MIN
            sub_h = (1.0 - main_h) / n_sub
    else:
        main_h, sub_h = 1.0, 0.0
    row_heights = [main_h] + [sub_h] * n_sub

    has_vp = any(name.startswith("vp_") for name in ps_result.series)
    n_cols = 2 if has_vp else 1
    column_widths = [1.0 - _VP_COLUMN_WIDTH, _VP_COLUMN_WIDTH] if has_vp else None

    if n_cols == 2:
        specs: list[list[dict[str, object] | None]] = [[{}, {}]]
        specs.extend([{"colspan": 2}, None] for _ in range(n_sub))
    else:
        specs = [[{}] for _ in range(n_rows)]

    fig = make_subplots(
        rows=n_rows, cols=n_cols, shared_xaxes=False, vertical_spacing=0.04,
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

    # `window_start_idx` normalde bu fonksiyonda DAHA SONRA hesaplanır — ama
    # golden_zone/supply_demand'ın (varsa) ÇOK YILLIK geçmişini FİLTRELEMEK
    # için burada ERKEN gerekiyor (bkz. `_filter_recent` çağrıları hemen
    # altında). Kullanıcı geri bildirimi: bu ikisinin TÜM geçmişi (`structure.
    # golden_zone`'un KENDİ tekil grafiğinde gayet OKUNUR) `structure.price_
    # structure`'ın ZATEN yoğun bölge/trend çizgisi/swing etiketleriyle
    # BİRLEŞİNCE aşırı kalabalıklaşıyordu — birleşik görünümde yalnızca
    # GÖRÜNÜR pencereye düşen olaylar/bölgeler anlamlı, geçmiş TAMAMI değil.
    window_start_idx_early = _resolve_window_start(ps_result, df, last_n)
    _cutoff_time = df.index[window_start_idx_early]

    def _filter_recent(items: list, time_key) -> list:
        return [it for it in items if time_key(it) >= _cutoff_time]

    extra_results = [er for er in (gz_result, sd_result) if er is not None]
    for extra_result in extra_results:
        extra_result.boxes = _filter_recent(extra_result.boxes, lambda b: b.t0)
        extra_result.markers = _filter_recent(extra_result.markers, lambda m: m.t)
        extra_result.levels = _filter_recent(
            extra_result.levels, lambda lv: lv.start or _cutoff_time
        )

    combined_levels = (
        ps_result.levels + sf_result.levels + [lv for r in extra_results for lv in r.levels]
    )
    levels = _declutter_levels(combined_levels) if declutter else combined_levels
    boxes = ps_result.boxes + [b for r in extra_results for b in r.boxes]
    lines = ps_result.lines + sf_result.lines + [ln for r in extra_results for ln in r.lines]
    markers = (
        [m for m in ps_result.markers if m.kind != "macd_cross"]
        + sf_result.markers
        + [m for r in extra_results for m in r.markers]
    )

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

    window_start_idx = window_start_idx_early
    visible = df.iloc[window_start_idx:]
    visible_price_range = (
        float(visible["high"].max() - visible["low"].min()) if not visible.empty else 0.0
    ) or 1.0
    total_height = 700 + 200 * n_sub
    main_row_px = max((total_height - 90) * main_h, 50.0)
    px_per_unit = main_row_px / visible_price_range if visible_price_range else 1.0

    labeled_boxes = [
        b for b in boxes if latest_box_t0 is None or b is latest_box_t0.get(b.style)
    ]
    line_extensions = _line_extensions(lines, df)
    labeled_line_ext = [
        (ln, proj) for ln, (_et, proj) in line_extensions.items()
        if latest_line_end is None or ln is latest_line_end.get(ln.style)
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
    _draw_markers(
        fig, markers, resolved, row=1, col=1, declutter=declutter, px_per_unit=px_per_unit,
    )

    # 2026-09-02 GERİ ALINDI — "alt paneller TAM GEÇMİŞİ gösterir" (bkz. Git
    # geçmişi): kullanıcı bunu "Hacim/MACD/RSI net ve özenli değil" olarak
    # yorumladı — ana panel yalnızca ~90 bar'a yakınlaşırken alt paneller
    # 2+ yıllık geçmişi AYNI panel genişliğine sıkıştırıyordu, bu da
    # onlardaki en son (asıl ilgi alanı) kısmı tanınmaz kadar küçültüyordu.
    # Referans görseller (ornek1/ornek2.png) osilatörleri HER ZAMAN ana
    # panelle AYNI zoom'da gösteriyor — artık burada da öyle.
    zoomed_range = [_x(df.index[window_start_idx]), _right_padded_x(df, len(df) - 1)]
    rangebreaks = _rangebreaks_for(df, ps_result.timeframe)
    for i, name in enumerate(sub_names, start=2):
        _draw_series_panel(
            fig, ps_result, name, ps_result.series_layout[name], resolved, row=i, col=1, df=df,
        )
        fig.update_xaxes(range=zoomed_range, rangebreaks=rangebreaks, row=i, col=1)
    fig.update_xaxes(range=zoomed_range, rangebreaks=rangebreaks, row=1, col=1)

    if has_vp:
        _draw_volume_profile(fig, ps_result, resolved, row=1, col=2, legend_name="legend2")

    # Kullanıcı geri bildirimi: alt panellerin "hangisi ne" olduğu belli
    # değildi (RSI/Hacim/MACD arasında ayrım yoktu) — HER panelin sol üst
    # köşesine küçük bir başlık eklenir.
    _draw_panel_titles(
        fig, resolved, {i: name for i, name in enumerate(sub_names, start=2)}, n_cols=n_cols,
    )

    # Ana panel (row=1) ve alt panel grubu (row=2..n_rows, TAM GEÇMİŞ) FARKLI
    # x-aralığını (bkz. yukarıdaki `zoomed_range` bloğu, 2026-09-02) — artık
    # bütün paneller AYNI zoom'landığı için tarih etiketini yalnızca EN
    # ALTTAKİ satır gösterir (standart yerleşim, gereksiz tekrar yok).
    for r in range(1, n_rows + 1):
        fig.update_xaxes(showticklabels=(r == n_rows), row=r, col=1)

    _sync_price_yaxis(fig, df, window_start_idx, has_vp)
    # K2 düzeltmesi (2026-09-05): sub panelleri artık ana panelle AYNI
    # (`zoomed_range`) x-aralığını gösteriyor (2026-09-02 geri alma) --
    # y-eksenleri de AYNI görünür pencereden hesaplanmalı, `len(df) - 1`
    # `zoomed_range`'in bitiş ucuyla birebir aynı.
    _sync_subpanel_yaxes(
        fig, ps_result, sub_names, ps_result.series_layout, df, window_start_idx, len(df) - 1,
    )

    # Alt başlık, `ps_result.indicator` ("structure.price_structure") yerine
    # BU birleşik görünümü yansıtmalı (`_price_header` tek-indikatör varsayımı
    # yapar) — yalnızca `subtitle` alanı override edilir.
    extras_tr = []
    if gz_result is not None:
        extras_tr.append("Golden Zone")
    if sd_result is not None:
        extras_tr.append("Arz/Talep")
    extras_suffix = f" + {' + '.join(extras_tr)}" if extras_tr else ""
    header = replace(
        _price_header(ps_result),
        subtitle=f"Birleşik Rapor (Yapı + Swing/Fibonacci{extras_suffix})",
    )
    _apply_layout(fig, resolved, header, height=total_height, width=_DEFAULT_WIDTH)
    if has_vp:
        _position_vp_legend(fig, resolved)
    return fig


# ---------------------------------------------------------- dönüş haritası --
#
# Faz 8E (`tlab/scanner/confluence.py::build_reversal_map`) — HESAP burada
# YAPILMAZ, yalnızca `result.last_state["zones"]`teki (ZATEN ağırlıklandırılmış)
# bölgeler + `vp_bins`/`vp_volumes` (yoğunluk profili, `_draw_volume_profile`
# ile PAYLAŞILAN aynı çizim yolu) çizilir. Genel `_draw_boxes`'ı KULLANMAZ —
# o fonksiyon sabit opaklık varsayar, burada "opaklık = ağırlık" (görev
# metninin kendi isteği) gerektiği için özel bir kutu çizim döngüsü var.


def render_reversal_map(
    result: IndicatorResult, df: pd.DataFrame,
    *, theme: Theme | str | None = "auto", last_n: int | None = None,
) -> go.Figure:
    """`confluence` IndicatorResult'ını çizer: katmanlı bölgeler (opaklık =
    ağırlık), sağ panelde destek yoğunluk profili, "DİPTE OLASI: X | N kaynak"
    etiketi + kısa dönüş-kaynağı açıklama kutusu."""
    resolved = resolve_theme(theme, default=LIGHT_ANALYSIS)
    has_vp = "vp_bins" in result.series and "vp_volumes" in result.series
    n_cols = 2 if has_vp else 1

    specs: list[list[dict[str, object]]] = [[{}, {}]] if has_vp else [[{}]]
    column_widths = [1.0 - _VP_COLUMN_WIDTH, _VP_COLUMN_WIDTH] if has_vp else None
    fig = make_subplots(
        rows=1, cols=n_cols, shared_xaxes=False, specs=specs,
        column_widths=column_widths, horizontal_spacing=0.02,
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

    window_start_idx = _resolve_window_start(result, df, last_n)

    zones = result.last_state.get("zones") or []
    for zone in sorted(zones, key=lambda z: z["weight_norm"]):
        opacity = 0.06 + 0.40 * float(zone["weight_norm"])
        color = with_alpha(resolved.green, opacity)
        fig.add_shape(
            type="rect", xref="x", yref="y",
            x0=_x(df.index[window_start_idx]), x1=_x(df.index[-1]),
            y0=zone["low"], y1=zone["high"],
            fillcolor=color, line=dict(width=0), layer="below",
            row=1, col=1,
        )

    swing_price = result.last_state.get("swing_low_price")
    bottom_probability = result.last_state.get("bottom_probability", 0.0)
    n_sources = result.last_state.get("n_sources", 0)
    if swing_price is not None:
        swing_time = result.last_state.get("swing_low_time")
        fig.add_trace(
            go.Scatter(
                x=[_x(swing_time)] if swing_time else [], y=[swing_price],
                mode="markers+text",
                marker=dict(color=resolved.accent, size=11, symbol="triangle-up"),
                text=[f"DİPTE OLASI: {bottom_probability:.2f} | {n_sources} kaynak"],
                textposition="bottom center", textfont=dict(color=resolved.accent, size=11),
                showlegend=False, name="Dönüş",
            ),
            row=1, col=1,
        )

    sources_desc = result.last_state.get("sources", "")
    fig.add_annotation(
        x=0.01, y=0.02, xref="x domain", yref="y domain", xanchor="left", yanchor="bottom",
        text=f"Dönüş kaynakları: {sources_desc}", showarrow=False, align="left",
        bgcolor=with_alpha(resolved.bg, 0.85), bordercolor=resolved.border, borderwidth=1,
        font=dict(color=resolved.text, size=10.5, family=resolved.font),
        row=1, col=1,
    )

    if has_vp:
        _draw_volume_profile(fig, result, resolved, row=1, col=2)
        _sync_price_yaxis(fig, df, window_start_idx, has_vp)

    header = _Header(symbol=result.symbol, subtitle="Dönüş Haritası (Confluence)")
    _apply_layout(fig, resolved, header, height=650, width=_DEFAULT_WIDTH)
    if has_vp:
        _position_vp_legend(fig, resolved)
    fig.update_xaxes(
        range=[_x(df.index[window_start_idx]), _right_padded_x(df, len(df) - 1)],
        rangebreaks=_rangebreaks_for(df, result.timeframe), row=1, col=1,
    )
    return fig


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
# Faz 8E — `pair.vol_harvest` `_render_pair`'in MEVCUT 3 panelini (bkz.
# `vol_harvest.py`'nin `buyhold_5050` alias'ı) yeniden kullanıyor ama FARKLI
# bir stratejidir (ikili geçiş değil, sürekli ağırlık) — sabit tek isim
# YANLIŞ olurdu, indikatöre göre seçiliyor.
_STRATEGY_NAME_TR_BY_INDICATOR: dict[str, str] = {
    "pair.relative_momentum": _STRATEGY_NAME_TR,
    "pair.vol_harvest": "SÜREKLİ AĞIRLIKLI OYNAKLIK HASADI (Z-Skor Rebalans)",
}


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
    strategy_name = _STRATEGY_NAME_TR_BY_INDICATOR.get(result.indicator, _STRATEGY_NAME_TR)
    line2 = (
        f"{strategy_name} | {y_symbol} <-> {x_symbol} | "
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
