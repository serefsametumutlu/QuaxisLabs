"""`tlab/indicators/patterns/boundary_adapter.py` testleri.

`WedgeIndicator`/`BroadeningIndicator`'ın kendi (zaten test edilmiş)
geometrisini yeniden hesaplamadan `contracts.BoundaryPattern`e çevirdiğini
doğrular — `test_wedge.py::test_hologram_polygon_matches_boundary_line_corners`
ile AYNI monkeypatch deseni (`build_trendlines` sahtelenir), ama pivot
`bar_time`'ları GERÇEK `df.index` değerlerinden alınır (o testte pivot'lar
`df.index`ten bağımsız keyfi tarihlerdi — bu adaptör testinde `Line.points`
ile df'in kategorik x-ekseni HİZALI olmak zorunda, aksi halde grafik
render'ı sessizce bozulur; bu, bu test dosyasını yazarken GERÇEKTEN
bulunan bir uyumsuzluk)."""

from __future__ import annotations

from dataclasses import replace

import pandas as pd
import pytest

from tlab.core.pattern_state import PatternTrackingConfig, track_breakout_pattern
from tlab.core.types import IndicatorResult, Timeframe
from tlab.features.swings import Pivot
from tlab.features.trendlines import Trendline
from tlab.indicators.patterns.boundary_adapter import select_latest, to_pattern
from tlab.indicators.patterns.wedge import WedgeIndicator, WedgeParams
from tlab.testing.fixtures import make_trend


def _pivot(df: pd.DataFrame, bar_idx: int, price: float, kind: str = "high") -> Pivot:
    return Pivot(
        bar_idx=bar_idx, bar_time=df.index[bar_idx], price=price, kind=kind,
        confirmed_idx=bar_idx + 3, confirmed_time=df.index[bar_idx + 3],
    )


def _line(
    slope: float, intercept: float, kind: str, p1: Pivot, p2: Pivot, touches: tuple[int, ...],
) -> Trendline:
    return Trendline(
        p1=p1, p2=p2, slope=slope, intercept=intercept, kind=kind,
        touches=touches, broken_at=None, created_idx=p2.confirmed_idx,
    )


def _confirmed_falling_wedge(df: pd.DataFrame) -> IndicatorResult:
    """`test_wedge.py`'nin doğrulanmış geçerli takoz geometrisiyle AYNI
    (up1/up2/lo1/lo2), ama df 35 bara kırpılır ki CONFIRMED durumda
    kalsın (kırılım sonrası `max_bars_to_target` süresi dolmadan) --
    `select_latest`'in EXPIRED'i (kırılım sonrası hedef zaman aşımı DAHIL)
    dışladığını ayrı bir testte doğruluyoruz, burada TAZE bir aday
    istiyoruz."""
    up1, up2 = _pivot(df, 0, 130.0, "high"), _pivot(df, 20, 110.0, "high")
    lo1, lo2 = _pivot(df, 5, 100.0, "low"), _pivot(df, 25, 95.0, "low")
    upper = _line(-1.0, 130.0, "resistance", up1, up2, touches=(0, 10, 20))
    lower = _line(-0.25, 101.25, "support", lo1, lo2, touches=(5, 15, 25))

    def _fake_build_trendlines(df, pivots, kind, **kwargs):
        return [upper] if kind == "resistance" else [lower]

    import unittest.mock as mock

    with mock.patch(
        "tlab.indicators.patterns.wedge.build_trendlines", _fake_build_trendlines,
    ):
        params = WedgeParams(
            min_pivots=4, min_bars=5, max_apex_bars=200, slope_ratio_range=(0.1, 1.0),
        )
        return WedgeIndicator("wedge", params).compute(df)


def test_to_pattern_builds_boundary_lines_and_numbered_touches_from_real_geometry() -> None:
    df_full = make_trend(n=200, slope=0.0, noise=1.0, seed=1)
    df = df_full.iloc[:35]
    result = _confirmed_falling_wedge(df)

    pat = to_pattern(result, df)
    assert pat is not None
    assert pat.kind == "falling_wedge"
    assert pat.title == "ALÇALAN TAKOZ"
    assert pat.state == "ONAY"

    upper_b, lower_b = pat.boundaries
    # İki sınır ORTAK bir aralıkta örneklenir (bkz. `_spanned`): geometri
    # hâlâ wedge.py'nin ürettiği doğrunun AYNISI, yalnızca iki uç nokta
    # ortak [span_start, span_end]'e taşınır. Eskiden her sınır YALNIZCA
    # kendi iki pivotu arasında çiziliyordu (üst 0-20, alt 5-25) ve
    # `Line.extend_right` sessizce DÜŞÜYORDU -- iki çizgi hiç kesişmiyor,
    # formasyon grafikte oluşmuyordu.
    assert upper_b.points[0][0] == lower_b.points[0][0]
    assert upper_b.points[-1][0] == lower_b.points[-1][0]
    # Doğrular DEĞİŞMEDİ: üst y=130-1.0*i, alt y=101.25-0.25*i.
    for b, (y0, slope) in ((upper_b, (130.0, -1.0)), (lower_b, (101.25, -0.25))):
        for t, y in b.points:
            assert y == pytest.approx(y0 + slope * df.index.get_loc(t))
    # touches, extra_payload["upper_touches"]=(0,10,20) -- Trendline.
    # touches'ın DIŞA AÇILMIŞ hâli -- ile birebir eşleşmeli.
    assert [t.label for t in upper_b.touches] == ["U1", "U2", "U3"]
    assert [t.t for t in upper_b.touches] == [df.index[0], df.index[10], df.index[20]]
    assert all(t.above for t in upper_b.touches)
    assert [t.label for t in lower_b.touches] == ["L1", "L2", "L3"]
    assert not any(t.above for t in lower_b.touches)


def test_to_pattern_signal_matches_breakout_direction() -> None:
    df_full = make_trend(n=200, slope=0.0, noise=1.0, seed=1)
    df = df_full.iloc[:35]
    result = _confirmed_falling_wedge(df)

    pat = to_pattern(result, df)
    assert pat is not None
    assert pat.signal is not None
    assert pat.signal.text == "AL"          # falling_wedge -> long -> AL
    assert pat.signal.role == "bullish"
    assert pat.signal.below is True         # AL kutusu mumun ALTINA konur


def test_to_pattern_returns_none_when_no_signals() -> None:
    empty = IndicatorResult(
        indicator="patterns.wedge", version="0.1.0", params_hash="x",
        symbol="TEST", timeframe=Timeframe.D1,
    )
    df = make_trend(n=50)
    assert to_pattern(empty, df) is None


def test_select_latest_excludes_invalidated_and_expired() -> None:
    df = make_trend(n=50, timeframe=Timeframe.D1)
    atr_series = pd.Series(1.0, index=df.index)

    def _cfg(pattern_id: str, born_idx: int, target: float) -> PatternTrackingConfig:
        return PatternTrackingConfig(
            pattern_id=pattern_id, pattern_name="falling_wedge", direction="long",
            break_line=lambda t: 1e9,   # asla kırılmaz -> PENDING kalır, sonra EXPIRED
            target=target, confirm_bars=1, max_bars_to_confirm=2,
            retest_tol_atr=0.3, atr_series=atr_series, score=0.5,
        )

    sig_expired = track_breakout_pattern(df, 0, _cfg("p_expired", 0, 999.0))
    result = IndicatorResult(
        indicator="patterns.wedge", version="0.1.0", params_hash="x",
        symbol="TEST", timeframe=Timeframe.D1,
        signals=sig_expired,
        last_state={
            "p_expired": {
                "shape": "falling_wedge", "direction": "long",
                "state": sig_expired[-1].state, "event": sig_expired[-1].payload["event"],
                "target": 999.0,
            },
        },
    )
    assert sig_expired[-1].state == "expired"
    assert select_latest(result) is None
    assert to_pattern(result, df) is None


def test_select_latest_picks_the_most_recently_signalled_candidate() -> None:
    df = make_trend(n=60, timeframe=Timeframe.D1)
    result = IndicatorResult(
        indicator="patterns.wedge", version="0.1.0", params_hash="x",
        symbol="TEST", timeframe=Timeframe.D1,
        signals=[],
        last_state={
            "old": {
                "shape": "falling_wedge", "direction": "long",
                "state": "confirmed", "event": "falling_wedge_confirmed", "target": 10.0,
            },
            "new": {
                "shape": "rising_wedge", "direction": "short",
                "state": "confirmed", "event": "rising_wedge_confirmed", "target": 20.0,
            },
        },
    )
    # last_bar bilgisi result.signals'tan geldiği için, iki pattern_id'nin
    # sinyallerini AYRI zamanlarda ekliyoruz.
    old_sig = track_breakout_pattern(
        df, 0,
        PatternTrackingConfig(
            pattern_id="old", pattern_name="falling_wedge", direction="long",
            break_line=lambda t: -1e9, target=10.0, confirm_bars=1,
            max_bars_to_confirm=None, retest_tol_atr=0.3,
            atr_series=pd.Series(1.0, index=df.index), score=0.5,
        ),
    )
    new_sig = track_breakout_pattern(
        df, 30,
        PatternTrackingConfig(
            pattern_id="new", pattern_name="rising_wedge", direction="short",
            break_line=lambda t: 1e9, target=20.0, confirm_bars=1,
            max_bars_to_confirm=None, retest_tol_atr=0.3,
            atr_series=pd.Series(1.0, index=df.index), score=0.5,
        ),
    )
    result.signals.extend(old_sig)
    result.signals.extend(new_sig)
    result.last_state["old"]["state"] = old_sig[-1].state
    result.last_state["old"]["event"] = old_sig[-1].payload["event"]
    result.last_state["new"]["state"] = new_sig[-1].state
    result.last_state["new"]["event"] = new_sig[-1].payload["event"]

    picked = select_latest(result)
    assert picked is not None
    assert picked[0] == "new"


def test_boundaries_share_one_span_so_the_pattern_actually_closes() -> None:
    """İki sınırın ZAMAN aralığı AYNI olmalı.

    Regresyon: `wedge.py` her sınırı yalnızca kendi iki pivotu arasında
    tanımlar ve uzatmayı `Line.extend_right=True`'ya devreder; adaptör bu
    bayrağı okumadığı için siteye kopuk çizgiler gidiyordu (kullanıcının
    BESTE ekran görüntüsünde alt sınır Nisan-Mayıs, üst sınır Haziran-Eylül
    aralığındaydı -- ikisi HİÇ kesişmiyordu).
    """
    df = make_trend(n=200, slope=0.0, noise=1.0, seed=1).iloc[:35]
    pat = to_pattern(_confirmed_falling_wedge(df), df)
    assert pat is not None
    upper_b, lower_b = pat.boundaries
    assert upper_b.points[0][0] == lower_b.points[0][0]
    assert upper_b.points[-1][0] == lower_b.points[-1][0]
    # Ortak aralık formasyon gövdesinin TAMAMINI (0..25 pivotları) kapsar.
    assert df.index.get_loc(upper_b.points[0][0]) == 0
    assert df.index.get_loc(upper_b.points[-1][0]) >= 25
    # ...ve sınırlar GERÇEKTEN yakınsar (alçalan takoz).
    opening = upper_b.points[0][1] - lower_b.points[0][1]
    closing = upper_b.points[-1][1] - lower_b.points[-1][1]
    assert closing < opening


def test_select_latest_rejects_a_candidate_whose_boundary_is_degenerate() -> None:
    """Bir sınırı diğerinin yanında yok denecek kadar kısa olan aday, sinyali
    daha TAZE olsa bile seçilmemeli.

    Regresyon: `wedge.py` 159 barlık bir üst sınırı 6 barlık bir alt sınırla
    eşleştiren adaylar da üretiyor ve bunların sinyalleri tipik olarak en
    tazeler; salt tazeliğe göre sıralamak bu yozlaşmış adayı SİSTEMATİK
    olarak seçiyordu. 6 barlık bir "destek çizgisi" Bulkowski'nin ~3 hafta /
    çoklu temas ölçütünü karşılamaz -- formasyon sınırı değil, gürültüdür.
    """
    df = make_trend(n=200, slope=0.0, noise=1.0, seed=1).iloc[:35]
    result = _confirmed_falling_wedge(df)
    (good_pid, good_state), = result.last_state.items()
    key = good_pid.rsplit("_", 1)[0]

    # AYNI üst sınırı, 2 barlık bir alt sınırla eşleştiren SAHTE bir aday
    # ekle; sinyali de bir bar DAHA TAZE olsun.
    fresh_pid = "degenerate_long"
    fresh_key = "degenerate"
    upper = next(ln for ln in result.lines if ln.label == f"{key}_upper")
    lower = next(ln for ln in result.lines if ln.label == f"{key}_lower")
    result.lines.append(replace(upper, label=f"{fresh_key}_upper"))
    result.lines.append(
        replace(lower, label=f"{fresh_key}_lower",
                points=((df.index[26], 95.0), (df.index[28], 94.5)))
    )
    result.last_state[fresh_pid] = dict(good_state)
    newest = max(result.signals, key=lambda s: pd.Timestamp(s.bar_time))
    result.signals.append(
        replace(newest, bar_time=df.index[-1], detected_at=df.index[-1],
                payload={**newest.payload, "pattern_id": fresh_pid})
    )
    assert pd.Timestamp(df.index[-1]) > pd.Timestamp(newest.bar_time), (
        "sahte aday GERÇEKTEN taze olmalı"
    )

    picked = select_latest(result, df)
    assert picked is not None
    assert picked[0] == good_pid, "yozlaşmış aday, daha taze olmasına rağmen seçilmemeli"

    # df verilmezse eleme YAPILMAZ (geriye dönük davranış): salt tazelik.
    assert select_latest(result)[0] == fresh_pid
