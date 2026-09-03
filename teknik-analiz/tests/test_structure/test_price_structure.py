"""PriceStructure: trendline/range/zone/hacim profili/MACD entegrasyonu.

Repaint stratejisi: generic (tüm IndicatorResult'ı kıyaslayan) `repaint_test`
BİLEREK kullanılmaz — bkz. price_structure.py modül docstring'indeki
"BİLİNEN SINIRLAMA" notu (trendline "aday havuzu" + hacim profilinin
dizinin-sonuna-göre-kayan penceresi). Bunun yerine GERÇEKTEN non-repaint
olması gereken parçalar (range/zone kutuları + kırılım sinyalleri, MACD/
hacim serileri) hedefli testlerle doğrulanır.
"""

from __future__ import annotations

import pandas as pd

from tests.test_structure.fixtures import build_structure_ohlcv
from tlab.indicators.structure.price_structure import PriceStructure, PriceStructureParams

_PARAMS = PriceStructureParams(
    pivot_left=2, pivot_right=2, range_min_bars=8, range_atr_mult=1.5,
    trendline_min_touches=2, trendline_tol_atr=1.0, zone_band_atr=1.0,
    zone_min_pivots=2, profile_window_bars=40, volume_ma_window=10,
    # Faz 0.5: sistem varsayılanı zigzag_method="atr"; bu dosyanın küçük
    # (build_structure_ohlcv) fixture'ı ATR zigzag'in ısınma penceresine
    # sığmıyor -- trendline/range/zone MEKANİĞİNİ hedefleyen bu testler
    # bilinçli olarak eski "fixed" davranışına sabitlendi.
    zigzag_method="fixed",
)


def _run():
    df = build_structure_ohlcv()
    return df, PriceStructure(_PARAMS)(df)


def test_trendlines_and_breakout_signals() -> None:
    _, result = _run()
    resistance = [ln for ln in result.lines if ln.style == "resistance"]
    support = [ln for ln in result.lines if ln.style == "support"]
    assert len(resistance) >= 1
    assert len(support) >= 1
    assert any("Temas:" in ln.label for ln in resistance + support)

    events = {s.payload.get("event") for s in result.signals}
    assert "trendline_breakout" in events
    assert "range_breakout" in events
    assert "zone_touch" in events
    assert "zone_break" in events


def test_trendline_breakout_direction_matches_kind() -> None:
    """Regresyon: `direction`, resistance/support ile TERS eşlenmişti
    (Faz 8A'da breakouts.py yazılırken bulunan gerçek bir hata — hiçbir
    test bu alanı doğrulamıyordu). `build_trendlines`'ın kendi `beyond`
    tanımı: resistance kırılımı close > line (boğa/long), support kırılımı
    close < line (ayı/short)."""
    _, result = _run()
    breakouts = [s for s in result.signals if s.payload.get("event") == "trendline_breakout"]
    assert breakouts
    for s in breakouts:
        expected = "long" if s.payload["kind"] == "resistance" else "short"
        assert s.direction == expected


def test_boxes_include_ranges_and_both_zone_kinds() -> None:
    _, result = _run()
    assert any(b.style == "range_box" for b in result.boxes)
    assert any(b.style == "resistance_zone" for b in result.boxes)
    assert any(b.style == "support_zone" for b in result.boxes)


def test_volume_and_macd_series_present() -> None:
    _, result = _run()
    for key in ("volume", "volume_ma", "macd", "macd_signal", "macd_hist"):
        assert key in result.series
        assert len(result.series[key]) == len(result.series["volume"])


def test_rsi_series_present_and_time_indexed() -> None:
    """2026-08-30: `structure.report` (birleşik grafik) RSI paneli için
    eklendi — `oscillators.rsi`'nin doğrudan sarmalanması, yeni bir hesap
    yöntemi DEĞİL."""
    df, result = _run()
    assert "rsi_14" in result.series
    assert result.series["rsi_14"].index.equals(df.index)
    assert result.series_layout["rsi"] == ["rsi_14"]
    finite = result.series["rsi_14"].dropna()
    assert not finite.empty
    assert finite.between(0.0, 100.0).all()


def test_volume_profile_series_are_price_indexed_not_time_indexed() -> None:
    """vp_bins/vp_volumes: index FİYAT bin merkezleridir, df.index (zaman)
    DEĞİLDİR — bkz. price_structure.py modül docstring'i."""
    df, result = _run()
    assert "vp_bins" in result.series
    assert "vp_volumes" in result.series
    vp_index = result.series["vp_volumes"].index
    assert not vp_index.equals(df.index)
    assert all(isinstance(x, float) for x in vp_index[:3])


def test_vp_hvn_series_is_binary_and_price_indexed() -> None:
    """`vp_hvn`: 1.0 (HVN) / 0.0, `vp_bins`/`vp_volumes` ile AYNI fiyat
    indeksini taşır — `find_hvn_nodes`'un doğrudan sarmalanması (renderer
    burada hiçbir hesap yapmaz, bkz. viz/renderer.py::_draw_volume_profile)."""
    df, result = _run()
    assert "vp_hvn" in result.series
    hvn = result.series["vp_hvn"]
    assert hvn.index.equals(result.series["vp_bins"].index)
    assert set(hvn.unique()).issubset({0.0, 1.0})


def test_last_state_fields() -> None:
    _, result = _run()
    for key in (
        "active_trendlines", "open_range_box", "price_vs_zone",
        "poc_distance", "poc_reclaimed_last_bar",
    ):
        assert key in result.last_state


def test_range_box_extend_only_and_birth_bar_on_cut() -> None:
    """Bir kutu, kendi detected_idx'inden ÖNCE hiçbir kesitte görünmemeli;
    kesitte görülen bir kutu, tam seride AYNI low/high ile (t1 büyüyebilir,
    küçülemez) bulunmalı — bkz. ranges.py docstring'indeki extend-only ve
    doğum-barı sözleşmesi."""
    df = build_structure_ohlcv()
    full = PriceStructure(_PARAMS)(df)
    full_range_boxes = [b for b in full.boxes if b.style == "range_box"]
    assert full_range_boxes

    cut = 45  # ilk konsolidasyon kutusunun doğumundan SONRA, kırılımından ÖNCE
    partial = PriceStructure(_PARAMS)(df.iloc[:cut])
    partial_range_boxes = [b for b in partial.boxes if b.style == "range_box"]
    assert partial_range_boxes, "kesitte en az bir range kutusu doğmuş olmalı"

    for pb in partial_range_boxes:
        match = next(
            (
                fb for fb in full_range_boxes
                if fb.t0 == pb.t0 and fb.low == pb.low and fb.high == pb.high
            ),
            None,
        )
        assert match is not None, f"kesitteki kutu tam seride bulunamadı: {pb}"
        assert match.t1 >= pb.t1, "extend-only ihlali: tam seride t1 küçülmüş"
        assert pb.t0 <= df.index[cut - 1], "kutu, kesitten SONRAKİ bir barda doğmuş olamaz"


def test_zone_box_extend_only_and_birth_bar_on_cut() -> None:
    """Aynı sözleşme, zone (destek/direnç bölgesi) kutuları için — bkz.
    zones.py docstring'indeki formed_idx (doğum barı) ve extend-only notu."""
    df = build_structure_ohlcv()
    full = PriceStructure(_PARAMS)(df)
    full_zone_boxes = [b for b in full.boxes if b.style in ("resistance_zone", "support_zone")]
    assert full_zone_boxes

    cut = 35
    partial = PriceStructure(_PARAMS)(df.iloc[:cut])
    zone_styles = ("resistance_zone", "support_zone")
    partial_zone_boxes = [b for b in partial.boxes if b.style in zone_styles]
    assert partial_zone_boxes, "kesitte en az bir bölge doğmuş olmalı"

    for pb in partial_zone_boxes:
        match = next(
            (
                fb for fb in full_zone_boxes
                if fb.t0 == pb.t0 and fb.low == pb.low
                and fb.high == pb.high and fb.style == pb.style
            ),
            None,
        )
        assert match is not None, f"kesitteki bölge tam seride bulunamadı: {pb}"
        assert match.t1 >= pb.t1, "extend-only ihlali: tam seride t1 küçülmüş"
        assert pb.t0 <= df.index[cut - 1], "bölge, kesitten SONRAKİ bir barda doğmuş olamaz"


def test_range_and_zone_signals_are_repaint_consistent() -> None:
    """range_breakout/zone_touch/zone_break sinyalleri (trendline HARİÇ —
    bkz. modül docstring'i) kesitte var olan HER ŞEY tam seride BİREBİR
    bulunmalı (Signal identity: bar_time/detected_at/direction/state)."""
    df = build_structure_ohlcv()
    full = PriceStructure(_PARAMS)(df)
    stable_events = {"range_breakout", "zone_touch", "zone_break"}
    full_stable = [s for s in full.signals if s.payload.get("event") in stable_events]

    for cut in (35, 40, 45, 50, 55):
        partial = PriceStructure(_PARAMS)(df.iloc[:cut])
        cut_time = df.index[cut - 1]
        partial_stable = [s for s in partial.signals if s.payload.get("event") in stable_events]
        for ps in partial_stable:
            match = next(
                (
                    fs for fs in full_stable
                    if fs.bar_time == ps.bar_time and fs.detected_at == ps.detected_at
                    and fs.direction == ps.direction and fs.state == ps.state
                    and fs.payload.get("event") == ps.payload.get("event")
                ),
                None,
            )
            assert match is not None, f"cut={cut}: kesitteki sinyal tam seride yok: {ps}"
        for fs in full_stable:
            if fs.detected_at > cut_time:
                continue
            match = next(
                (
                    ps for ps in partial_stable
                    if fs.bar_time == ps.bar_time and fs.detected_at == ps.detected_at
                    and fs.direction == ps.direction and fs.state == ps.state
                ),
                None,
            )
            assert match is not None, f"cut={cut}: tam seride var, kesitte yok: {fs}"


def test_macd_and_volume_series_match_on_overlap() -> None:
    """MACD/hacim serileri tamamen geçmişe bakar (ema/sma) — kesikte
    hesaplanan değerler, tam seride AYNI zaman damgalarında BİREBİR aynı
    olmalı (walk-forward eşitliği, IndicatorResult repaint_test'inden
    bağımsız ama aynı ilke)."""
    df = build_structure_ohlcv()
    full = PriceStructure(_PARAMS)(df)
    cut = 40
    partial = PriceStructure(_PARAMS)(df.iloc[:cut])

    for key in ("volume_ma", "macd", "macd_signal", "macd_hist", "rsi_14"):
        full_s = full.series[key]
        partial_s = partial.series[key]
        common = partial_s.index.intersection(full_s.index)
        assert len(common) > 0
        pd.testing.assert_series_equal(
            partial_s.loc[common], full_s.loc[common], check_names=False
        )


def test_registers_in_registry() -> None:
    """PriceStructure, generic Registry.register() ile KAYDEDİLMEZ — bkz.
    modül docstring'indeki "BİLİNEN SINIRLAMA" (trendline aday havuzu +
    hacim profili penceresi, generic tüm-IndicatorResult repaint_test'iyle
    doğası gereği uyumsuz). Bunun yerine arayüz uyumluluğu (meta, compute,
    IndicatorResult tipi) doğrudan doğrulanır."""
    from tlab.core.types import IndicatorResult

    df = build_structure_ohlcv()
    result = PriceStructure()(df)
    assert isinstance(result, IndicatorResult)
    assert result.indicator == "structure.price_structure"
