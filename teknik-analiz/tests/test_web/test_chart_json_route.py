"""`GET /api/chart.json` rotasının uçtan uca davranışı.

`compute_live` (Store + ağ) MOCK'lanır; geri kalan HER ŞEY gerçek yolu
kullanır: `boundary_adapter.to_pattern` -> komposer -> `plotly.io.to_json`.
Bu, gerçek BIST verisi olmadan kurulabilecek siteye EN YAKIN doğrulama.
"""

from __future__ import annotations

import json
from unittest import mock

import pytest
from fastapi import HTTPException

import web.backend.routes.chart_json as cj
from tlab.chart import fixtures as fx
from tlab.core.types import Timeframe
from tlab.indicators.bootstrap import scaled_factory

_CASES = [
    ("patterns.triangle", lambda: fx.triangle(kind="yukselen")),
    ("patterns.triangle", lambda: fx.triangle(kind="alcalan")),
    ("patterns.wedge", lambda: fx.wedge(kind="alcalan")),
    ("patterns.wedge", lambda: fx.wedge(kind="yukselen")),
    ("patterns.broadening", lambda: fx.broadening(kind="dip")),
    ("patterns.broadening", lambda: fx.broadening(kind="tepe")),
]


def _call(indicator, df, **kw):
    result = scaled_factory(indicator, Timeframe.D1)(df)
    with mock.patch.object(cj, "compute_live", return_value=(result, df)):
        return cj.get_chart_json(symbol="ORNEK", tf="1d", indicator=indicator, **kw)


@pytest.mark.parametrize(("indicator", "make_df"), _CASES)
@pytest.mark.parametrize("theme", ["dark", "classic", "editorial"])
def test_route_renders_every_supported_indicator_in_every_theme(
    indicator, make_df, theme
) -> None:
    resp = _call(indicator, make_df(), theme=theme)
    fig = json.loads(resp.body)
    assert fig["data"], "figür boş olmamalı"
    # mum + hacim + RSI en az; sınırlar ve işaretler üstüne gelir
    assert len(fig["data"]) >= 4


@pytest.mark.parametrize(("indicator", "make_df"), _CASES)
def test_default_freshness_gate_does_not_hide_live_patterns(indicator, make_df) -> None:
    """Varsayılan tazelik kapısı GEÇERLİ bir formasyonu gizlememeli.

    Regresyon: kapı önce `/scan` ile aynı 3 bara ayarlanmıştı; 4 barlık bir
    ONAY sinyali bile 404'e düşüyordu (= "eksik sinyal"). Grafik sayfasında
    asıl doğruluk filtresi durum makinesi (`invalidated`/`expired` zaten
    gelmiyor); tazelik yalnızca "artık bakmaya değmez" sınırı.
    """
    assert _call(indicator, make_df()).body


def test_freshness_gate_still_blocks_a_stale_pattern() -> None:
    """Kullanıcının BARMA vakası ("Sinyal yaşı: 262 bar") engellenmeye devam
    etmeli -- kapıyı gevşetmek onu geri getirmemiş olmalı."""
    with pytest.raises(HTTPException) as exc:
        _call("patterns.triangle", fx.triangle(kind="yukselen"), max_bars_ago=1)
    assert exc.value.status_code == 404
    assert "bayat" in exc.value.detail


def test_unsupported_indicator_returns_clear_422() -> None:
    with pytest.raises(HTTPException) as exc:
        cj.get_chart_json(symbol="X", tf="1d", indicator="harmonic.carney")
    assert exc.value.status_code == 422
    assert "bağlanmadı" in exc.value.detail


def test_catalog_interactive_flag_is_derived_from_the_route_not_duplicated() -> None:
    """`/api/catalog`'un `interactive` alanı `_SUPPORTED`ten türemeli.

    Regresyon: frontend'de ELLE yazılı ikinci bir liste vardı
    (`CHART_JSON_INDICATORS = ["patterns.triangle"]`); backend'e wedge/
    broadening eklendiğinde o liste güncellenmediği için siteye HÂLÂ eski
    PNG yolundan geliyorlardı. Tek doğru kaynak `chart_json._SUPPORTED`.
    """
    from web.backend.routes.catalog import get_catalog

    rows = get_catalog()
    flagged = {r["name"] for r in rows if r["interactive"]}
    assert flagged == set(cj._SUPPORTED)
    assert not any(r["interactive"] for r in rows if r["name"].startswith("harmonic."))
