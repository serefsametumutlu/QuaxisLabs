"""Cache'ten veri okuyup bir indikatörü ÇALIŞTIRIP render eden ince yardımcı.

`renderer.py`'nin kendisi hesap yapmaz (yalnızca zaten üretilmiş bir
`IndicatorResult`'ı çizer) — burası ise `tlab plot` CLI komutu ile
`report.py::ensure_chart`'ın PAYLAŞTIĞI, "sembol adından canlı grafiğe" kısa
yolu barındırır (CATALOG + Store + render tek yerde)."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from tlab.core.indicator import BaseIndicator
from tlab.core.types import IndicatorResult, Market, Timeframe
from tlab.data.providers.yfinance_provider import YFinanceProvider
from tlab.data.store import Store
from tlab.data.universe import BENCHMARK_SYMBOL, load_universe
from tlab.indicators.bootstrap import CATALOG
from tlab.indicators.pairs.relative_momentum import RelativeMomentumPair, RelativeMomentumParams
from tlab.indicators.pairs.vol_harvest import VolHarvestPair, VolHarvestParams
from tlab.viz.renderer import render, render_structure_report
from tlab.viz.themes import Theme

_TF_MAP = {"1H": Timeframe.H1, "4H": Timeframe.H4, "1D": Timeframe.D1, "W1": Timeframe.W1}

# "structure.report" gerçek bir Registry indikatörü DEĞİLDİR (CATALOG'ta yok)
# — `structure.price_structure` + `structure.swing_fib_abcd`'i TEK bir
# "aracı kurum raporu" grafiğinde birleştiren salt-görsel bir bileşim adı
# (bkz. renderer.py::render_structure_report docstring'i, 2026-08-30).
STRUCTURE_REPORT_NAME = "structure.report"


def compute_live(
    indicator_name: str, symbol: str, timeframe: str, market: str
) -> tuple[IndicatorResult, pd.DataFrame | None]:
    """`symbol` pair indikatörler için "Y/X" biçiminde olmalı (ör. "TCELL/ISCTR").
    Dönen df, pair modunda None'dır (renderer bu modda df istemez)."""
    if indicator_name not in CATALOG:
        raise ValueError(f"Bilinmeyen indikatör: {indicator_name} (bkz. tlab list-indicators)")
    spec = CATALOG[indicator_name]
    mkt = Market(market.lower())
    tf = _TF_MAP.get(timeframe.upper())
    if tf is None:
        raise ValueError(f"Geçersiz tf: {timeframe} (1h|4h|1d bekleniyor)")
    store = Store(YFinanceProvider())

    if spec.needs_context:
        if "/" not in symbol:
            raise ValueError("Pair indikatörler için symbol 'Y/X' biçiminde olmalı")
        y_sym, x_sym = symbol.split("/", 1)
        pair_instance: BaseIndicator
        if indicator_name == "pair.relative_momentum":
            pair_instance = RelativeMomentumPair(
                RelativeMomentumParams(y_symbol=y_sym, x_symbol=x_sym)
            )
        elif indicator_name == "pair.vol_harvest":
            pair_instance = VolHarvestPair(VolHarvestParams(y_symbol=y_sym, x_symbol=x_sym))
        else:
            pair_instance = spec.factory()
        df_y = store.get(y_sym, tf, mkt)
        df_x = store.get(x_sym, tf, mkt)
        result = pair_instance(df_y, context={"x": df_x})
        result.symbol = symbol
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
        instance = spec.factory()
        results = instance(universe_dfs, index_df)
        if symbol not in results:
            raise ValueError(
                f"'{symbol}' için {indicator_name} sonucu üretilemedi "
                "(yetersiz geçmiş/likidite — bkz. min_history_bars/min_liquidity_try)"
            )
        result = results[symbol]
        return result, universe_dfs[symbol]

    instance = spec.factory()
    df = store.get(symbol, tf, mkt)
    result = instance(df)
    result.symbol = symbol
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
    store = Store(YFinanceProvider())
    df = store.get(symbol, tf, mkt)

    ps_result = CATALOG["structure.price_structure"].factory()(df)
    ps_result.symbol = symbol
    sf_result = CATALOG["structure.swing_fib_abcd"].factory()(df)
    sf_result.symbol = symbol
    return ps_result, sf_result, df


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


def render_live(
    indicator_name: str, symbol: str, timeframe: str, market: str,
    *, theme: Theme | str | None = "auto", last_n: int | None = None, declutter: bool = True,
) -> go.Figure:
    if indicator_name == STRUCTURE_REPORT_NAME:
        return render_structure_report_live(
            symbol, timeframe, market, theme=theme, last_n=last_n, declutter=declutter,
        )
    result, df = compute_live(indicator_name, symbol, timeframe, market)
    return render(result, df, theme=theme, last_n=last_n, declutter=declutter)
