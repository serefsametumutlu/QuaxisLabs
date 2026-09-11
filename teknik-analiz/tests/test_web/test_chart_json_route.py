"""`GET /api/chart.json` rotasının uçtan uca davranışı.

`compute_live` (Store + ağ) MOCK'lanır; geri kalan HER ŞEY gerçek yolu
kullanır: `boundary_adapter.to_pattern` -> komposer -> `plotly.io.to_json`.
Bu, gerçek BIST verisi olmadan kurulabilecek siteye EN YAKIN doğrulama.
"""

from __future__ import annotations

import json
from unittest import mock

import pandas as pd
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
    ("structure.swing_fib_abcd", fx.head_shoulders),
    ("structure.price_structure", fx.head_shoulders),
    ("patterns.flag_pennant", fx.impulse_retrace),
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
    """CATALOG'daki 27 göstergenin TAMAMI artık bağlı; bu test bilinmeyen
    bir ada karşı 422 verildiğini kilitler (yazım hatası / eski link)."""
    with pytest.raises(HTTPException) as exc:
        cj.get_chart_json(symbol="X", tf="1d", indicator="boyle.bir.gosterge.yok")
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
    # Aşama B bitti: CATALOG'un TAMAMI bağlı olmalı. Yeni bir gösterge
    # eklenip `_SUPPORTED`e yazılmazsa bu test onu yakalar.
    assert flagged == {r["name"] for r in rows}, (
        f"bağlanmamış gösterge var: {sorted({r['name'] for r in rows} - flagged)}"
    )


# --- AYRI akış kullanan göstergeler ---------------------------------------
# `pair.*` ve `momentum.*` standart `compute_live` mock'uyla sınanamaz:
# ilki `compute_pair_live` (Y+X ham serileri), ikincisi tüm EVRENİ ister.


@pytest.mark.parametrize(
    "indicator", ["pair.relative_momentum", "pair.vol_harvest"]
)
def test_pair_route_uses_its_own_branch(indicator) -> None:
    """Pair akışı: `compute_pair_live` + `df` ALMAYAN komposer imzası."""
    from tlab.indicators.pairs.relative_momentum import (
        RelativeMomentumPair,
        RelativeMomentumParams,
    )
    from tlab.indicators.pairs.vol_harvest import VolHarvestPair, VolHarvestParams

    y = fx.rising_channel(n=300, seed=5)
    x = fx.range_market(n=300, seed=9)
    x.index = y.index
    make = (
        RelativeMomentumPair(RelativeMomentumParams(y_symbol="AAA", x_symbol="BBB"))
        if indicator == "pair.relative_momentum"
        else VolHarvestPair(VolHarvestParams(y_symbol="AAA", x_symbol="BBB"))
    )
    result = make(y, context={"x": x})
    result.symbol = "AAA/BBB"
    with mock.patch.object(cj, "compute_pair_live", return_value=(result, y, x)):
        resp = cj.get_chart_json(symbol="AAA/BBB", tf="1d", indicator=indicator)
    fig = json.loads(resp.body)
    assert len(fig["data"]) >= 4


@pytest.mark.parametrize(
    "indicator", ["momentum.alpha_rank", "momentum.momentum_rank"]
)
def test_universe_route_renders(indicator) -> None:
    """Evren göstergeleri: `compute_live` evrenin TAMAMINI hesaplar
    (`live.py::_universe_cached` önbellekler); burada sonuç mock'lanır."""
    from tlab.core.types import Timeframe
    from tlab.indicators.bootstrap import scaled_factory

    uni = {f"S{i:02d}": fx.rising_channel(n=300, seed=i) for i in range(1, 26)}
    for k in uni:
        uni[k].index = uni["S01"].index
    idx = fx.rising_channel(n=300, seed=99)
    idx.index = uni["S01"].index
    results = scaled_factory(indicator, Timeframe.D1)(uni, idx)
    with mock.patch.object(
        cj, "compute_live", return_value=(results["S05"], uni["S05"])
    ):
        resp = cj.get_chart_json(
            symbol="S05", tf="1d", indicator=indicator, max_bars_ago=None
        )
    fig = json.loads(resp.body)
    assert len(fig["data"]) >= 3


def test_universe_result_is_cached_so_one_computation_serves_all_symbols() -> None:
    """Evren hesabı sembol başına TEKRARLANMAMALI.

    `UniverseIndicator` tek bir sembolün grafiği için bile 648 sembolü
    hesaplıyor; web'de her tıklamada bunu yeniden koşmak dakikalar
    sürerdi. Sonuç (gösterge, tf, market) başına önbelleklenir.
    """
    from tlab.viz import live

    live._UNIVERSE_CACHE.clear()
    calls: list[int] = []

    class _FakeStore:
        def get(self, sym, tf, mkt):
            return fx.rising_channel(n=120, seed=abs(hash(sym)) % 50 + 1)

    def _fake_factory(name, tf):
        def _run(dfs, index_df):
            calls.append(1)
            return {s: mock.MagicMock() for s in dfs}
        return _run

    with (
        mock.patch.object(live, "load_universe", return_value=["A", "B", "C"]),
        mock.patch.object(live, "scaled_factory", _fake_factory),
        mock.patch.dict(live.BENCHMARK_SYMBOL, {}, clear=False),
    ):
        from tlab.core.types import Market, Timeframe

        store = _FakeStore()
        for sym in ("A", "B", "C"):
            live._universe_cached("momentum.alpha_rank", Timeframe.D1, Market.BIST, store, sym)
    assert len(calls) == 1, f"evren {len(calls)} kez hesaplandı, 1 olmalıydı"


def test_focus_narrows_the_window_to_the_pattern() -> None:
    """`ChartFrame.focus` grafiği formasyona odaklamalı.

    Regresyon: komposerler tüm geçmişi çiziyordu ve 20-40 barlık bir
    formasyon 300 barlık eksende nokta gibi kalıyordu (kullanıcının
    tekrar eden şikâyeti). Odak İKİ şeyi birden yapar -- yalnızca x
    aralığını daraltmak yetmez, y ekseni hâlâ TÜM seriyi görüp
    formasyonu dikeyde ezer (`pole_flag`de tam bu yaşandı).
    """
    # `head_shoulders` fikstürü carney için geçerli bir aday üretiyor
    # (`harmonic_shape` üretmiyor -- fikstür adı yanıltıcı ama
    # harmonik motorun kendi oran kapıları farklı).
    df = fx.head_shoulders()
    from tlab.core.types import Timeframe
    from tlab.indicators.bootstrap import scaled_factory

    result = scaled_factory("harmonic.carney", Timeframe.D1)(df)
    with mock.patch.object(cj, "compute_live", return_value=(result, df)):
        resp = cj.get_chart_json(
            symbol="X", tf="1d", indicator="harmonic.carney", max_bars_ago=None
        )
    layout = json.loads(resp.body)["layout"]
    x_range = layout["xaxis"]["range"]
    assert x_range, "odak uygulanmamış (x aralığı serbest)"
    shown = pd.Timestamp(x_range[1]) - pd.Timestamp(x_range[0])
    full = df.index[-1] - df.index[0]
    assert shown < full, "pencere daralmamış"

    # y ekseni de GÖRÜNEN dilimden ölçeklenmeli, tüm seriden değil.
    y_range = layout["yaxis"]["range"]
    assert y_range
    lo, hi = float(y_range[0]), float(y_range[1])
    assert hi - lo < (float(df["high"].max()) - float(df["low"].min())), (
        "y ekseni hâlâ tüm seriden ölçekleniyor"
    )
