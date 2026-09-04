"""`tlab/viz/svg/scenes/reversal_map.py` -- Faz 4a'nın SON sahnesi (6/6),
`confluence` IndicatorResult'ı için.

THYAO (1D, classic) + AKBNK (1D, dark) + ISCTR (1D, editorial) gerçek
veriyle 3 iterasyon geçti (bkz. `docs/design/iterasyon/iter{1,2,3}_
confluence_*`). 1. iterasyonda GERÇEK bir hata bulundu: "Dönüş kaynakları:
..." kaynak açıklama metni panelin ALTINDAKİ x-ekseni ay etiketleriyle
(neredeyse aynı y konumu) üst üste biniyordu -- düzeltme: metin artık
panelin İÇİNE, sol-alt köşeye yarı saydam bir arkaplan kutusuyla konur
(`render_reversal_map`in [Plotly] `bgcolor` çözümüyle AYNI ilke).

`compute_reversal_map`in `live.py`ye eklediği köprü + `build_reversal_map`in
kendisi ayrı ayrı zaten `tests/test_scanner/test_confluence.py`de test
ediliyor -- burada yalnızca SAHNE (SVG çizim) katmanı test edilir, aynı
dosyanın `_fake_result`/`_make_dipping_series` fixture'ları TEKRAR
KULLANILIR (gerçek `build_reversal_map` çağrısıyla üretilmiş GERÇEK bir
`IndicatorResult`, uydurma değil)."""

from __future__ import annotations

import re

import pytest

from tests.test_scanner.test_confluence import _fake_result, _make_dipping_series
from tlab.core.types import Box
from tlab.scanner.confluence import ConfluenceParams, build_reversal_map
from tlab.viz.svg import render_svg, supports
from tlab.viz.svg.scenes.reversal_map import build
from tlab.viz.svg.theme import CLASSIC, DARK, EDITORIAL


def _result():
    df = _make_dipping_series()
    close = float(df["close"].iloc[-1])
    born = df.index[10]
    below_box = Box(
        t0=born, t1=df.index[-1], low=close - 20, high=close - 15,
        label="DEMAND", style="demand",
    )
    sd_result = _fake_result(boxes=[below_box])
    result = build_reversal_map(
        "TEST", "1D", df, {"structure.supply_demand": sd_result}, ConfluenceParams()
    )
    return result, df


def test_supports_reports_confluence() -> None:
    assert supports("confluence") is True


def test_build_returns_main_panel_and_side_panel() -> None:
    result, df = _result()
    out = build(result, df, CLASSIC)
    assert out.two_up is None
    assert out.panels is not None and len(out.panels) == 1
    assert out.side is not None


def test_source_caption_is_inside_panel_not_below_x_axis_labels() -> None:
    """1. iterasyonda GERÇEK bir hata: kaynak metni x-ekseni ay etiketleriyle
    (chart.inner_y1+22 civarı) üst üste biniyordu. Artık panelin İÇİNDE
    (chart.inner_y0/y1 arasında) kalmalı."""
    result, df = _result()
    out = build(result, df, CLASSIC)
    svg_text = out.panels[0].svg
    pattern = r'<text x="[\d.]+" y="([\d.]+)"[^>]*>Dönüş kaynakları'
    ys = [float(m) for m in re.findall(pattern, svg_text)]
    assert ys, "kaynak metni SVG'de bulunamadı"
    # panel yüksekliği 440, margin_t=20/margin_b=28 -- caption bu aralıkta
    # kalmalı, x-ekseni etiketlerinin (~440-6=434 civarı) ÇOK ALTINA DEĞİL.
    assert all(y < 420 for y in ys)


@pytest.mark.parametrize("theme", [CLASSIC, DARK, EDITORIAL])
def test_render_svg_produces_well_formed_svg_in_all_three_themes(theme) -> None:
    result, df = _result()
    svg_text = render_svg(result, df, theme=theme)
    assert svg_text.startswith("<svg")
    assert svg_text.strip().endswith("</svg>")
    # ana panel + yan (yoğunluk profili) panel = en az 2 iç <svg>
    assert svg_text.count("<svg") >= 3


def test_render_svg_handles_zero_source_case_gracefully() -> None:
    """GERÇEK veri davranışı (THYAO'da GÖZLEMLENDİ): swing low hiçbir
    kaynakla eşleşmeyebilir (`n_sources=0`) -- sahne çökmemeli."""
    df = _make_dipping_series()
    result = build_reversal_map("TEST", "1D", df, {}, ConfluenceParams())
    assert result.last_state["n_sources"] == 0
    svg_text = render_svg(result, df, theme=CLASSIC)
    assert svg_text.startswith("<svg")
