"""Cache'ten veri okuyup bir indikatörü ÇALIŞTIRIP render eden ince yardımcı.

`renderer.py`'nin kendisi hesap yapmaz (yalnızca zaten üretilmiş bir
`IndicatorResult`'ı çizer) — burası ise `tlab plot` CLI komutu ile
`report.py::ensure_chart`'ın PAYLAŞTIĞI, "sembol adından canlı grafiğe" kısa
yolu barındırır (CATALOG + Store + render tek yerde)."""

from __future__ import annotations

from typing import Literal, overload

import pandas as pd
import plotly.graph_objects as go

from tlab.core.indicator import BaseIndicator
from tlab.core.types import IndicatorResult, Level, Line, Marker, Market, Timeframe
from tlab.data.providers.yfinance_provider import YFinanceProvider
from tlab.data.store import Store
from tlab.data.universe import BENCHMARK_SYMBOL, load_universe
from tlab.features.ma import ema
from tlab.features.market_structure import detect_market_structure
from tlab.features.swings import label_structure, significant_pivots
from tlab.indicators.bootstrap import CATALOG, scaled_factory
from tlab.indicators.pairs.relative_momentum import RelativeMomentumPair, RelativeMomentumParams
from tlab.indicators.pairs.vol_harvest import VolHarvestPair, VolHarvestParams
from tlab.scanner.confluence import build_reversal_map
from tlab.viz.renderer import render, render_reversal_map, render_structure_report
from tlab.viz.svg import render_svg
from tlab.viz.svg import supports as svg_supports
from tlab.viz.themes import Theme

Engine = Literal["svg", "plotly"]


def _theme_to_svg_key(theme: Theme | str | None) -> str | None:
    if theme is None or isinstance(theme, str):
        return theme
    _MAP = {"light_analysis": "classic", "dark_terminal": "dark", "kagit_raporu": "editorial"}
    return _MAP.get(theme.name, "classic")

_TF_MAP = {"1H": Timeframe.H1, "4H": Timeframe.H4, "1D": Timeframe.D1, "W1": Timeframe.W1}

# "structure.report" gerçek bir Registry indikatörü DEĞİLDİR (CATALOG'ta yok)
# — `structure.price_structure` + `structure.swing_fib_abcd`'i TEK bir
# "aracı kurum raporu" grafiğinde birleştiren salt-görsel bir bileşim adı
# (bkz. renderer.py::render_structure_report docstring'i, 2026-08-30).
STRUCTURE_REPORT_NAME = "structure.report"

# "confluence" da CATALOG'ta yok — `tlab/scanner/confluence.py::
# build_reversal_map`in girdisi ZATEN hesaplanmış birden fazla indikatörün
# sonucudur (`{indikatör_adı: IndicatorResult}`), `BaseIndicator`ın tekil
# `compute(df)` sözleşmesine UYMAZ (bkz. o modülün docstring'i). `render_
# reversal_map` (Plotly, Faz 8E'de yazıldı) o zamandan beri HİÇBİR canlı
# giriş noktasına (CLI/web) bağlanmamıştı -- `compute_reversal_map` bu
# eksik köprüyü tamamlar.
REVERSAL_MAP_NAME = "confluence"

_REVERSAL_MAP_SOURCE_NAMES = (
    "structure.supply_demand", "structure.golden_zone",
    "structure.price_structure", "structure.swing_fib_abcd",
)

# "structure.market_structure" da CATALOG'ta yok — Faz 4d (`ornek1.png`
# standardı, `docs/GORSEL_HATA_TESHISI.md` bölüm 4/5): pivot üçgenleri +
# temas-sayılı trend çizgisi + BOS/CHoCH + pivot-çıpalı arz/talep + tek MA
# TEK bir "SMC yapı görünümü"nde birleşir. `structure.price_structure`
# (trendline'lar) + `structure.supply_demand` (varsayılan method="pivot"
# zaten Faz 4d'nin istediği çıpalama) İKİ MEVCUT indikatörün olduğu gibi
# çağrılması + BOS/CHoCH'un burada TAZE hesaplanması (CATALOG'ta ayrı bir
# indikatör DEĞİL, `confluence`nin zone'ları gibi salt bir "post-processing"
# katmanı — `tlab/features/market_structure.py` saf fonksiyon, kendi
# IndicatorResult'ı yok).
MARKET_STRUCTURE_NAME = "structure.market_structure"
_MARKET_STRUCTURE_EMA_SPAN = 50


def _require_supported_timeframe(indicator_name: str, tf: Timeframe) -> None:
    """Faz 0.5, A3: `engine.run()`'daki AYNI kapı — grafik ile tarama AYNI
    sonucu üretmeli. Burada sessizce yanlış/anlamsız bir sonuç üretmek
    yerine NET bir hata fırlatılır (`momentum.alpha_rank`in D1-only
    sözleşmesini çiğneyip 4H'te "çalışır gibi görünmesi" tam da STRATEJI_
    DENETIM_TAM.md A3'ün belgelediği sessiz hataydı)."""
    supported = CATALOG[indicator_name].supported_timeframes
    if supported and tf not in supported:
        names = ", ".join(t.value for t in supported)
        raise ValueError(
            f"{indicator_name} {tf.value}'te çalışmıyor (desteklenen zaman dilimleri: {names})"
        )


def compute_live(
    indicator_name: str, symbol: str, timeframe: str, market: str
) -> tuple[IndicatorResult, pd.DataFrame | None]:
    """`symbol` pair indikatörler için "Y/X" biçiminde olmalı (ör. "TCELL/ISCTR").
    Dönen df, pair modunda None'dır (renderer bu modda df istemez).

    2026-09-04 GERÇEK HATA (bulunup düzeltildi): `BaseParams`/`for_timeframe()`
    yalnızca `_BAR_FIELDS`'i ölçekler, tf'nin KENDİSİNİ hiçbir params alanında
    SAKLAMAZ -- bu yüzden HER indikatörün `compute()`'u kendi `IndicatorResult`
    ini `timeframe=Timeframe.D1` SABİT değeriyle kurar (18/18 dosya, istisnasız).
    Sonuç: `result.timeframe` her zaman D1'di, gerçek tf 1H/4H olsa bile --
    bu yalnızca `report_text.py`'nin "Zaman Dilimi: ..." metnini değil,
    `renderer.py::_rangebreaks_for`'un GECE/hafta-sonu boşluğu gizleme
    mantığını da (yalnızca `Timeframe.H1`/`H4` iken devreye girer) SESSİZCE
    devre dışı bırakıyordu -- yani 1H/4H grafiklerde mum gövdeleri gerçekte
    olduğundan daha sıkışık görünüyordu (2026-08-30'da BİR KEZ bulunup
    düzeltilen sorunun ta kendisi, farklı bir kaynaktan geri gelmiş hâli).
    Düzeltme `result.symbol = symbol`'la AYNI desende: compute() kendi
    tf'sini bilemediği için, onu BİLEN çağıran (burası) sonradan atıyor."""
    if indicator_name not in CATALOG:
        raise ValueError(f"Bilinmeyen indikatör: {indicator_name} (bkz. tlab list-indicators)")
    spec = CATALOG[indicator_name]
    mkt = Market(market.lower())
    tf = _TF_MAP.get(timeframe.upper())
    if tf is None:
        raise ValueError(f"Geçersiz tf: {timeframe} (1h|4h|1d bekleniyor)")
    _require_supported_timeframe(indicator_name, tf)
    store = Store(YFinanceProvider())

    if spec.needs_context:
        if "/" not in symbol:
            raise ValueError("Pair indikatörler için symbol 'Y/X' biçiminde olmalı")
        y_sym, x_sym = symbol.split("/", 1)
        pair_instance: BaseIndicator
        if indicator_name == "pair.relative_momentum":
            pair_instance = RelativeMomentumPair(
                RelativeMomentumParams(y_symbol=y_sym, x_symbol=x_sym).for_timeframe(tf)
            )
        elif indicator_name == "pair.vol_harvest":
            pair_instance = VolHarvestPair(
                VolHarvestParams(y_symbol=y_sym, x_symbol=x_sym).for_timeframe(tf)
            )
        else:
            pair_instance = scaled_factory(indicator_name, tf)
        df_y = store.get(y_sym, tf, mkt)
        df_x = store.get(x_sym, tf, mkt)
        result = pair_instance(df_y, context={"x": df_x})
        result.symbol = symbol
        result.timeframe = tf
        return result, None

    if spec.needs_universe:
        # Faz 8D "universe" kategorisi (`UniverseIndicator`) — `rank_pct`
        # TANIM GEREĞİ tüm evreni birlikte görmeyi gerektirdiği için TEK bir
        # sembolün "tekil" grafiği bile evrenin TAMAMININ hesaplanmasını
        # gerektirir (bkz. `tlab/core/indicator.py::UniverseIndicator`).
        # DÜRÜST NOT: bu, `tlab plot`'un diğer tüm indikatörlerden ÇOK daha
        # yavaş olmasına yol açar (tam evren × cache okuma + cross-sectional
        # rank) — `tlab universe-plot` zaten AYNI maliyeti evren-geneli
        # görseller (saçılım/ısı haritası) için taşıyordu, burada yalnızca
        # TEK sembolün sonucu seçilip standart `render()`'a verilir.
        universe_symbols = load_universe(mkt)
        universe_dfs: dict[str, pd.DataFrame] = {}
        for sym in universe_symbols:
            try:
                universe_dfs[sym] = store.get(sym, tf, mkt)
            except FileNotFoundError:
                continue
        if symbol not in universe_dfs:
            universe_dfs[symbol] = store.get(symbol, tf, mkt)
        index_df = store.get(BENCHMARK_SYMBOL[mkt], tf, mkt)
        instance = scaled_factory(indicator_name, tf)
        results = instance(universe_dfs, index_df)
        if symbol not in results:
            raise ValueError(
                f"'{symbol}' için {indicator_name} sonucu üretilemedi "
                "(yetersiz geçmiş/likidite — bkz. min_history_bars/min_liquidity_try)"
            )
        result = results[symbol]
        result.timeframe = tf
        return result, universe_dfs[symbol]

    instance = scaled_factory(indicator_name, tf)
    df = store.get(symbol, tf, mkt)
    result = instance(df)
    result.symbol = symbol
    result.timeframe = tf
    return result, df


def compute_structure_report(
    symbol: str, timeframe: str, market: str
) -> tuple[IndicatorResult, IndicatorResult, pd.DataFrame]:
    """`structure.price_structure` + `structure.swing_fib_abcd`'i AYNI df
    üzerinde çalıştırır — `render_structure_report`'ın ihtiyaç duyduğu iki
    hazır sonucu üretir, hiçbir ek hesap yapmaz (iki mevcut indikatörün
    olduğu gibi çağrılması)."""
    mkt = Market(market.lower())
    tf = _TF_MAP.get(timeframe.upper())
    if tf is None:
        raise ValueError(f"Geçersiz tf: {timeframe} (1h|4h|1d bekleniyor)")
    _require_supported_timeframe("structure.price_structure", tf)
    _require_supported_timeframe("structure.swing_fib_abcd", tf)
    store = Store(YFinanceProvider())
    df = store.get(symbol, tf, mkt)

    ps_result = scaled_factory("structure.price_structure", tf)(df)
    ps_result.symbol = symbol
    ps_result.timeframe = tf
    sf_result = scaled_factory("structure.swing_fib_abcd", tf)(df)
    sf_result.symbol = symbol
    sf_result.timeframe = tf
    return ps_result, sf_result, df


def compute_structure_report_merged(
    symbol: str, timeframe: str, market: str
) -> tuple[IndicatorResult, pd.DataFrame]:
    """`compute_structure_report`'un iki ayrı sonucunu TEK bir
    `IndicatorResult`ta birleştirir (`indicator="structure.report"`) --
    `web/backend/routes/chart.py::get_chart`'ın ZATEN yaptığı birleştirmeyle
    AYNI (eskiden orada tekrarlanıyordu, buraya taşındı: `/api/chart` JSON
    uç noktası ile SVG `report` sahnesi [`Scene.build()`'in tek-`result`
    sözleşmesi gereği] artık TEK doğru kaynağı paylaşıyor). `series`/
    `series_layout` yalnızca `ps_result`ten gelir (RSI/MACD/hacim/vp_* zaten
    `price_structure`e ait, `swing_fib_abcd`'in kendi series'i yok)."""
    ps_result, sf_result, df = compute_structure_report(symbol, timeframe, market)
    merged = IndicatorResult(
        indicator=STRUCTURE_REPORT_NAME,
        version=ps_result.version,
        params_hash=ps_result.params_hash,
        symbol=ps_result.symbol,
        timeframe=ps_result.timeframe,
        signals=ps_result.signals + sf_result.signals,
        levels=ps_result.levels + sf_result.levels,
        lines=ps_result.lines + sf_result.lines,
        boxes=ps_result.boxes,
        polygons=[],
        markers=ps_result.markers + sf_result.markers,
        series=ps_result.series,
        series_layout=ps_result.series_layout,
        last_state={**ps_result.last_state, **sf_result.last_state},
    )
    return merged, df


def compute_reversal_map(
    symbol: str, timeframe: str, market: str
) -> tuple[IndicatorResult, pd.DataFrame]:
    """`confluence.py::build_reversal_map`in ihtiyaç duyduğu `sources`
    sözlüğünü (ZATEN hesaplanmış indikatör sonuçları) canlı olarak kurar --
    `compute_structure_report_merged`in AYNI "iki mevcut indikatörün olduğu
    gibi çağrılması" ilkesi, burada 4 tekil-sembol indikatörü + haftalık
    kanal + 8 harmonik ekol için genişletilmiş hâli.

    Haftalık kanal: `build_reversal_map_from_run`'ın (EOD/DB yolu) BELGELİ
    kuralıyla AYNI ("varsa W1, yoksa 1D'nin kendisi") -- `trend.weekly_
    channel` yalnızca W1/D1 destekliyor, bu yüzden istenen `tf` (ör. 4H)
    burada YOK SAYILIR, her zaman W1 veya D1 kullanılır."""
    mkt = Market(market.lower())
    tf = _TF_MAP.get(timeframe.upper())
    if tf is None:
        raise ValueError(f"Geçersiz tf: {timeframe} (1h|4h|1d|w1 bekleniyor)")
    for name in _REVERSAL_MAP_SOURCE_NAMES:
        _require_supported_timeframe(name, tf)
    store = Store(YFinanceProvider())
    df = store.get(symbol, tf, mkt)

    sources: dict[str, IndicatorResult] = {}
    for name in _REVERSAL_MAP_SOURCE_NAMES:
        result = scaled_factory(name, tf)(df)
        result.symbol = symbol
        result.timeframe = tf
        sources[name] = result

    try:
        wc_df, wc_tf = store.get(symbol, Timeframe.W1, mkt), Timeframe.W1
    except FileNotFoundError:
        # `df` yalnızca istenen `tf` D1 iken doğrudan yeniden kullanılabilir
        # -- aksi hâlde (ör. tf=4H) `df` YANLIŞ zaman dilimi olurdu.
        wc_df = df if tf == Timeframe.D1 else store.get(symbol, Timeframe.D1, mkt)
        wc_tf = Timeframe.D1
    wc_result = scaled_factory("trend.weekly_channel", wc_tf)(wc_df)
    wc_result.symbol = symbol
    wc_result.timeframe = wc_tf
    sources["trend.weekly_channel"] = wc_result

    for name in CATALOG:
        if not name.startswith("harmonic."):
            continue
        h_result = scaled_factory(name, tf)(df)
        h_result.symbol = symbol
        h_result.timeframe = tf
        sources[name] = h_result

    result = build_reversal_map(symbol, tf.value, df, sources)
    return result, df


_MS_EVENT_TEXT = {
    "bos_up": "BOS↑", "bos_down": "BOS↓", "choch_up": "CHoCH↑", "choch_down": "CHoCH↓",
}
_MS_LABEL_TEXT = {"HH": "HH", "HL": "HL", "LH": "LH", "LL": "LL"}


def compute_market_structure_merged(
    symbol: str, timeframe: str, market: str
) -> tuple[IndicatorResult, pd.DataFrame]:
    """`structure.price_structure` (trend çizgileri) + `structure.supply_
    demand` (varsayılan `method="pivot"` — Faz 4d'nin çıpalama isteğinin
    KENDİSİ) + burada TAZE hesaplanan BOS/CHoCH (`tlab/features/market_
    structure.py`) + pivot yapı etiketleri (HH/HL/LH/LL, `structure.
    swing_fib_abcd`nin ZATEN ürettiği `structure_label` Marker'larıyla AYNI
    sözleşme) + tek bir EMA-50 çizgisini TEK bir `IndicatorResult`ta
    birleştirir — `compute_structure_report_merged`/`compute_reversal_map`
    ile AYNI "post-processing köprüsü" deseni (bkz. o fonksiyonların
    docstring'i)."""
    mkt = Market(market.lower())
    tf = _TF_MAP.get(timeframe.upper())
    if tf is None:
        raise ValueError(f"Geçersiz tf: {timeframe} (1h|4h|1d bekleniyor)")
    _require_supported_timeframe("structure.price_structure", tf)
    _require_supported_timeframe("structure.supply_demand", tf)
    store = Store(YFinanceProvider())
    df = store.get(symbol, tf, mkt)

    ps_result = scaled_factory("structure.price_structure", tf)(df)
    ps_result.symbol, ps_result.timeframe = symbol, tf
    sd_instance = scaled_factory("structure.supply_demand", tf)
    sd_result = sd_instance(df)
    sd_result.symbol, sd_result.timeframe = symbol, tf

    sd_params = sd_instance.params
    pivots = label_structure(significant_pivots(
        df, method=sd_params.zigzag_method, left=sd_params.pivot_left,
        right=sd_params.pivot_right, atr_mult=sd_params.atr_mult,
        atr_period=sd_params.atr_period, min_swing_atr=sd_params.min_swing_atr,
    ))

    struct_markers: list[Marker] = [
        Marker(t=p.bar_time, price=p.price, text=p.label, kind="structure_label")
        for p in pivots if p.label is not None
    ]

    events = detect_market_structure(df, pivots)
    ms_levels: list[Level] = []
    ms_markers: list[Marker] = []
    for i, ev in enumerate(events):
        style = ev.kind  # "bos_up"|"bos_down"|"choch_up"|"choch_down"
        end_time = events[i + 1].bar_time if i + 1 < len(events) else None
        ms_levels.append(
            Level(price=ev.level, label=style, style=style, start=ev.bar_time, end=end_time)
        )
        text = _MS_EVENT_TEXT[ev.kind]
        if i == len(events) - 1:
            text += " / AKTİF"
        ms_markers.append(Marker(t=ev.bar_time, price=ev.level, text=text, kind=f"ms_{style}"))

    ema_series = ema(df["close"], _MARKET_STRUCTURE_EMA_SPAN)
    ema_line = Line(
        points=tuple(
            (t, float(v)) for t, v in ema_series.items() if not pd.isna(v)
        ),
        label=f"EMA{_MARKET_STRUCTURE_EMA_SPAN}", style="single_ma",
    )

    merged = IndicatorResult(
        indicator=MARKET_STRUCTURE_NAME,
        version=ps_result.version,
        params_hash=ps_result.params_hash,
        symbol=symbol,
        timeframe=tf,
        signals=ps_result.signals + sd_result.signals,
        levels=ps_result.levels + ms_levels,
        lines=[*ps_result.lines, ema_line],
        boxes=sd_result.boxes,
        polygons=[],
        markers=struct_markers + sd_result.markers + ms_markers,
        last_state={**ps_result.last_state, **sd_result.last_state},
    )
    return merged, df


def render_structure_report_live(
    symbol: str, timeframe: str, market: str,
    *, theme: Theme | str | None = "auto", last_n: int | None = None, declutter: bool = True,
) -> go.Figure:
    """**2026-08-30 deneme + geri alma**: kullanıcı "golden zone ve supply
    demand kısımlarını structure reporta koymamız gerekmiyor mu" diye
    sordu; `render_structure_report`'a bunun için `gz_result`/`sd_result`
    parametreleri eklendi ve burada denendi — ama gerçek TCELL verisiyle
    render edilince `structure.price_structure`'ın ZATEN yoğun bölge/
    trend/swing etiketleriyle BİRLEŞİNCE ana paneli daha da kalabalıklaştırdı
    (bu KENDİSİ ayrı ayrı gayet okunur olan iki indikatörün toplamı, ama
    üçüncü bir katman olarak EKLENİNCE aşırıya kaçtı). Karar: birleştirme
    YAPILMADI — `render_structure_report`'un `gz_result`/`sd_result`
    parametreleri (opsiyonel, `None` varsayılan) KOD OLARAK kalıyor (ileride
    farklı bir declutter stratejisiyle tekrar denenebilir), ama bu canlı
    kısayol onları GEÇMİYOR — `structure.golden_zone`/`structure.supply_
    demand` kendi AYRI, temiz grafiklerinde kalmaya devam ediyor."""
    ps_result, sf_result, df = compute_structure_report(symbol, timeframe, market)
    return render_structure_report(
        ps_result, sf_result, df, theme=theme, last_n=last_n, declutter=declutter,
    )


@overload
def render_live(
    indicator_name: str, symbol: str, timeframe: str, market: str,
    *, theme: Theme | str | None = ..., last_n: int | None = ..., declutter: bool = ...,
    engine: Literal["plotly"] = ...,
) -> go.Figure: ...
@overload
def render_live(
    indicator_name: str, symbol: str, timeframe: str, market: str,
    *, theme: Theme | str | None = ..., last_n: int | None = ..., declutter: bool = ...,
    engine: Literal["svg"],
) -> go.Figure | str: ...
def render_live(
    indicator_name: str, symbol: str, timeframe: str, market: str,
    *, theme: Theme | str | None = "auto", last_n: int | None = None, declutter: bool = True,
    engine: Engine = "plotly",
) -> go.Figure | str:
    """`engine="svg"` istenirse VE `indicator_name` için bir SVG sahnesi
    portlanmışsa SVG METNİ (str) döner; aksi hâlde (Plotly istenmiş VEYA
    henüz portlanmamış bir gösterge) her zamanki gibi `go.Figure` döner --
    Faz 3 spec'inin "bir sahne henüz portlanmadıysa plotly'ye düş" kuralı.

    **Varsayılan `engine="plotly"`** -- TANI_VE_YOL_HARITASI_v2.md Faz 3,
    3D'nin önerdiği "varsayılan svg" yerine BİLİNÇLİ bir sapma: bu
    fonksiyonun 3 mevcut çağıranı (`tlab/cli.py::plot`, `tlab/dashboard.py`,
    `tlab/viz/report.py::ensure_chart`) hâlâ KOŞULSUZ `go.Figure` API'sini
    (`.write_image`/`.write_html`/Streamlit'in `plotly_chart`) kullanıyor --
    varsayılanı `svg` yapmak, tek bir portlanmış gösterge (`patterns.
    double_top_bottom`) için bu üç yeri SESSİZCE kırardı. SVG yolu şimdilik
    yalnızca AÇIKÇA `engine="svg"` isteyen iki YENİ entegrasyon noktasından
    (`web/backend/routes/chart_svg.py`, `chart_png.py`nin SVG-öncelikli
    rasterleştirmesi) çalışır -- Faz 4'te kalan 18 sahne portlanıp üç eski
    çağıran da güncellenince varsayılan `svg`'ye çevrilebilir."""
    if indicator_name == STRUCTURE_REPORT_NAME:
        if engine == "svg" and svg_supports(STRUCTURE_REPORT_NAME):
            merged, df = compute_structure_report_merged(symbol, timeframe, market)
            svg_theme = _theme_to_svg_key(theme) or "classic"
            return render_svg(merged, df, theme=svg_theme, last_n=last_n)
        return render_structure_report_live(
            symbol, timeframe, market, theme=theme, last_n=last_n, declutter=declutter,
        )
    if indicator_name == REVERSAL_MAP_NAME:
        result, df = compute_reversal_map(symbol, timeframe, market)
        if engine == "svg" and svg_supports(REVERSAL_MAP_NAME):
            svg_theme = _theme_to_svg_key(theme) or "classic"
            return render_svg(result, df, theme=svg_theme, last_n=last_n)
        return render_reversal_map(result, df, theme=theme, last_n=last_n)
    if indicator_name == MARKET_STRUCTURE_NAME:
        # Faz 4d'nin YENİ sahnesi — hiçbir Plotly karşılığı YOK (eski
        # renderer.py'ye "düşülecek" bir şey yok), bu yüzden `engine`
        # ne olursa olsun SVG döner (bkz. modülün üst tanımındaki not).
        result, df = compute_market_structure_merged(symbol, timeframe, market)
        svg_theme = _theme_to_svg_key(theme) or "classic"
        return render_svg(result, df, theme=svg_theme, last_n=last_n)
    result, df = compute_live(indicator_name, symbol, timeframe, market)
    if engine == "svg" and df is not None and svg_supports(indicator_name):
        return render_svg(result, df, theme=_theme_to_svg_key(theme) or "classic", last_n=last_n)
    return render(result, df, theme=theme, last_n=last_n, declutter=declutter)
