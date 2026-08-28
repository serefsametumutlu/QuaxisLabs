"""`tlab/viz/renderer.py` için hedefli testler — Faz 7'de GERÇEK veriyle
render edilirken bulunan 3 hatanın regresyonları + iki temel duman testi.
Bu modül HESAP yapmadığı (yalnızca IndicatorResult primitiflerini çizdiği)
için repaint_test kapsamı dışıdır; burada doğrulanan yalnızca "veri doğruysa
çıktı figürü de doğru mu" sorusu."""

from __future__ import annotations

import re

from tests.test_pairs.fixtures import build_cointegrated_pair
from tlab.core.types import IndicatorResult, Line, Timeframe
from tlab.indicators.pairs.relative_momentum import RelativeMomentumPair, RelativeMomentumParams
from tlab.indicators.structure.price_structure import PriceStructure, PriceStructureParams
from tlab.testing.fixtures import make_trend
from tlab.viz.renderer import render
from tlab.viz.themes import DARK_TERMINAL, fill_color, line_color

_PAIR_PARAMS = RelativeMomentumParams(
    window=40, k=2.0, beta_method="one", beta_window=200, min_periods=200,
    y_symbol="YT", x_symbol="XT",
)


def _rgb(rgba: str) -> tuple[int, int, int]:
    m = re.match(r"rgba?\((\d+),(\d+),(\d+)", rgba)
    assert m is not None, rgba
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def test_generic_render_produces_candlestick_and_subpanels() -> None:
    df = make_trend(n=250, slope=0.1, noise=1.2)
    result = PriceStructure(PriceStructureParams())(df)
    result.symbol = "TEST"
    fig = render(result, df, theme="light")
    trace_types = {t.type for t in fig.data}
    assert "candlestick" in trace_types
    # series_layout iki alt panel istiyor (hacim, macd) -> en az 3 farklı yaxis
    yaxes = {getattr(t, "yaxis", "y") or "y" for t in fig.data}
    assert len(yaxes) >= 3


def test_pair_render_draws_holding_period_shading() -> None:
    """Regresyon: `add_vrect(row=...)`, o satıra ilk trace eklenmeden ÖNCE
    çağrılırsa Plotly (7.x) şekli SESSİZCE hiç eklemiyordu — tutulan-dönem
    gölgeleri (Görsel 1) bu yüzden hiç görünmüyordu."""
    df_y, df_x = build_cointegrated_pair()
    result = RelativeMomentumPair(_PAIR_PARAMS)(df_y, context={"x": df_x})
    result.symbol = "YT/XT"
    assert len(result.boxes) > 0  # fixture holding-box üretecek şekilde tasarlandı

    fig = render(result, theme="dark")
    assert len(fig.layout.shapes) >= len(result.boxes)


def test_line_extension_is_capped_not_unbounded() -> None:
    """Regresyon: kısa/dik bir bacağın (ör. harmonik X→B) eğimi ham hâliyle
    grafiğin en son barına kadar projekte edilince fiyat ekseni gerçek dışı
    büyüyordu. Uzatma artık bacağın KENDİ süresinin en fazla 3 katıyla
    sınırlı."""
    df = make_trend(n=200, slope=0.0, noise=0.1, start_price=100.0)
    t0, t1 = df.index[5], df.index[7]  # yalnızca 2 barlık, DİK bir bacak
    result = IndicatorResult(
        indicator="structure.fake_test", version="0.1.0", params_hash="h",
        symbol="TEST", timeframe=Timeframe.D1,
        lines=[
            Line(
                points=((t0, 100.0), (t1, 130.0)), label="dik_bacak",
                style="dashed", extend_right=True,
            )
        ],
    )
    fig = render(result, df, theme="light")
    ext_trace = next(t for t in fig.data if t.name == "dik_bacak_uzatma")
    # Sınırsız (ham eğim * kalan ~193 gün) projeksiyon >2900 verirdi;
    # sınırlı (en fazla 3x bacak süresi = 6 gün) projeksiyon ~190 civarı olmalı.
    assert max(ext_trace.y) < 300


def test_fill_and_line_colors_agree_on_direction() -> None:
    """Regresyon: `_FILL_STYLE_COLOR`'da bullish/bearish ters eşlenmişti —
    yeşil çizgili bir boğa üçgeni kırmızı dolgulu görünüyordu."""
    for style, expected_hex in (("bullish", DARK_TERMINAL.green), ("bearish", DARK_TERMINAL.red)):
        line_hex = line_color(DARK_TERMINAL, style)
        assert line_hex == expected_hex
        fill_rgb = _rgb(fill_color(DARK_TERMINAL, style, 0.5))
        expected_rgb = tuple(int(expected_hex.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
        assert fill_rgb == expected_rgb
