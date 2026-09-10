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
    # sınır-çizgili formasyonlar
    ("patterns.triangle", lambda: fx.triangle(kind="yukselen")),
    ("patterns.triangle", lambda: fx.triangle(kind="alcalan")),
    ("patterns.wedge", lambda: fx.wedge(kind="alcalan")),
    ("patterns.wedge", lambda: fx.wedge(kind="yukselen")),
    ("patterns.broadening", lambda: fx.broadening(kind="dip")),
    ("patterns.broadening", lambda: fx.broadening(kind="tepe")),
    # boyun çizgili dönüş formasyonları (TEK adaptör, iki gösterge)
    ("patterns.head_shoulders", fx.head_shoulders),
    ("patterns.head_shoulders", lambda: fx.head_shoulders(inverse=True)),
    ("patterns.double_top_bottom", fx.range_market),
    # harmonikler (TEK adaptör, 8 okul)
    ("harmonic.carney", fx.head_shoulders),
    ("harmonic.pesavento", fx.head_shoulders),
    # trend seri bindirmeleri
    ("trend.ma_systems", fx.head_shoulders),
    ("trend.ewmac", fx.head_shoulders),
    # arz/talep
    ("structure.supply_demand", fx.head_shoulders),
    ("structure.golden_zone", fx.impulse_retrace),
    ("trend.weekly_channel", fx.rising_channel),
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
    # Tazelik BURADA sınanmıyor (ayrı testi var); fikstürlerin bir kısmı
    # kasten eski formasyonlar taşıyor.
    resp = _call(indicator, make_df(), theme=theme, max_bars_ago=None)
    fig = json.loads(resp.body)
    assert fig["data"], "figür boş olmamalı"
    # İskelet: mum + hacim (+ hacim MA). Bunun ÜSTÜNE göstergenin kendi
    # içeriği gelmeli -- ama her komposer bunu `trace` olarak çizmez:
    # `zones` bölge bantlarını `shape` olarak koyuyor (ilk sürümde test
    # "en az 4 trace" diyordu ve arz/talep 3 trace'le kalıp patlıyordu).
    # Bu yüzden İÇERİK ölçütü trace-sayısı DEĞİL, "iskeletin ötesinde bir
    # şey var mı".
    layout = fig["layout"]
    has_content = (
        len(fig["data"]) > 3
        or bool(layout.get("shapes"))
        or len(layout.get("annotations", [])) > 2   # başlık + altyazı hariç
    )
    assert has_content, f"{indicator}: figürde göstergeye ait hiçbir içerik yok"


# Tazelik testi YALNIZCA fikstürü GÜNCEL bir sinyal üreten vakalarla
# anlamlı; `head_shoulders`/`double_top_bottom` fikstürleri kasten uzun
# ufuklu (87-112 bar) formasyonlar taşıyor.
_FRESH_CASES = [
    c for c in _CASES
    if c[0] in ("patterns.triangle", "patterns.wedge", "patterns.broadening")
]


@pytest.mark.parametrize(("indicator", "make_df"), _FRESH_CASES)
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
        # HENÜZ bağlanmamış bir gösterge (bkz. `_SUPPORTED`).
        cj.get_chart_json(symbol="X", tf="1d", indicator="trend.breakouts")
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
    # Henüz bağlanmamış olanlar ETKİLEŞİMLİ İŞARETLENMEMELİ.
    unwired = {r["name"] for r in rows if not r["interactive"]}
    assert "trend.breakouts" in unwired
    assert not (unwired & set(cj._SUPPORTED))
