"""MultiBreakout (Faz 8A): duman testi + iki lookahead-tuzağı regresyonu
(donchian/n_week_high `.shift(1)`), confirm_bars semantiği, retest_hold/
false_break zincir bütünlüğü."""

from __future__ import annotations

from tests.test_trend.fixtures import (
    build_confirm_bars_case,
    build_donchian_lookahead_case,
    build_false_break_case,
    build_noisy_uptrend,
    build_retest_hold_case,
)
from tlab.indicators.trend.breakouts import BreakoutParams, MultiBreakout

_REQUIRED_PAYLOAD_KEYS = {
    "event", "break_type", "pattern_id", "retest_state", "level_value",
    "level_age_bars", "touches", "volume_ratio", "volume_ok", "body_ratio",
    "distance_atr", "quality_score",
}


def test_smoke_many_break_types_fire_with_full_payload() -> None:
    df = build_noisy_uptrend()
    result = MultiBreakout(BreakoutParams(pivot_left=2, pivot_right=2))(df)

    breaks = [s for s in result.signals if s.payload.get("event") == "break"]
    assert len(breaks) > 10
    seen_types = {s.payload["break_type"] for s in breaks}
    # görev metnindeki türlerden en az bu kadarı gürültülü bir yükseliş
    # trendinde doğal olarak tetiklenmeli:
    assert {"hh_break", "donchian_break_up_20", "ma_break_ema50_up"} <= seen_types
    for s in breaks:
        assert _REQUIRED_PAYLOAD_KEYS <= s.payload.keys()
        assert 0.0 <= s.payload["quality_score"] <= 1.0
        assert s.payload["retest_state"] == "pending"


def test_donchian_break_uses_prior_bars_only_not_own_bar() -> None:
    """Regresyon/lookahead tuzağı: `.shift(1)` olmasaydı sıçrama barının
    KENDİ high'ı kendi Donchian penceresine girer, kırılımı bastırırdı."""
    df = build_donchian_lookahead_case(period=5)
    result = MultiBreakout(
        BreakoutParams(donchian_periods=(5,), confirm_bars=1, pivot_left=2, pivot_right=2)
    )(df)

    breaks = [
        s for s in result.signals
        if s.payload.get("event") == "break" and s.payload["break_type"] == "donchian_break_up_5"
    ]
    assert breaks, "sıçrama barında kırılım tetiklenmeliydi (shift(1) doğruysa)"
    spike_bar = df.index[5]  # 0..4 sabit taban, 5. bar sıçrama
    assert breaks[0].bar_time == spike_bar
    assert breaks[0].payload["level_value"] == 100.0 + 0.01  # önceki barların high'ı (wick dahil)


def test_confirm_bars_two_stamps_second_bar() -> None:
    df = build_confirm_bars_case()
    p1 = BreakoutParams(ema_periods=(50,), confirm_bars=1, pivot_left=2, pivot_right=2)
    p2 = BreakoutParams(ema_periods=(50,), confirm_bars=2, pivot_left=2, pivot_right=2)

    r1 = MultiBreakout(p1)(df)
    r2 = MultiBreakout(p2)(df)

    up1 = [
        s for s in r1.signals
        if s.payload.get("event") == "break" and s.payload["break_type"] == "ma_break_ema50_up"
    ]
    up2 = [
        s for s in r2.signals
        if s.payload.get("event") == "break" and s.payload["break_type"] == "ma_break_ema50_up"
    ]
    assert up1 and up2
    # confirm_bars=1: ilk üstte kapanan barda (index 120); confirm_bars=2:
    # yalnızca KALICI üstte kalışın 2. barında (index 123) tetiklenir —
    # 121 (99.5, içeri düşüş) 1 barlık seriyi bozduğu için 120-121 asla
    # onaylanmaz.
    assert list(df.index).index(up1[0].bar_time) == 120
    assert list(df.index).index(up2[0].bar_time) == 123
    assert up2[0].detected_at == up2[0].bar_time


def test_false_break_does_not_alter_original_signal() -> None:
    df = build_false_break_case()
    result = MultiBreakout(
        BreakoutParams(
            donchian_periods=(5,), confirm_bars=1, false_break_bars=3,
            pivot_left=2, pivot_right=2,
        )
    )(df)

    original = [
        s for s in result.signals
        if s.payload.get("event") == "break" and s.payload["break_type"] == "donchian_break_up_5"
    ]
    assert len(original) == 1
    pid = original[0].payload["pattern_id"]

    false_breaks = [
        s for s in result.signals
        if s.payload.get("event") == "false_break" and s.payload["pattern_id"] == pid
    ]
    assert len(false_breaks) == 1
    assert false_breaks[0].state == "invalidated"

    # ORİJİNAL kayıt (state/payload) aynı sonuç içinde DEĞİŞMEDEN duruyor:
    still_there = [
        s for s in result.signals
        if s.payload.get("event") == "break" and s.payload.get("pattern_id") == pid
    ]
    assert still_there == original


def test_retest_hold_fires_when_price_returns_but_close_stays() -> None:
    df = build_retest_hold_case()
    result = MultiBreakout(
        BreakoutParams(
            donchian_periods=(5,), confirm_bars=1, retest_max_bars=5, retest_tol_atr=0.5,
            pivot_left=2, pivot_right=2,
        )
    )(df)

    holds = [s for s in result.signals if s.payload.get("event") == "retest_hold"]
    assert holds
    assert holds[0].payload["retest_state"] == "held"


def test_registers_via_verified_elsewhere() -> None:
    """PriceStructure ile AYNI durum: trendline/zone/range aday-havuzu +
    hh/ll'nin sonraki-pivotla-süperseded zamanlaması, generic repaint_test'in
    'var olma kanıtı' varsayımıyla uyuşmuyor (bkz. modül docstring'i ve
    CLAUDE.md'deki aynı desenin Faz 3/4 notları) — bu yüzden bu indikatör de
    `register_verified_elsewhere` ile kaydedilir, dedicated testlerle
    (bu dosya) doğrulanır."""
    from tlab.core.errors import RegistryError
    from tlab.core.indicator import registry

    try:
        registry.register_verified_elsewhere(MultiBreakout())
    except RegistryError as exc:
        if "zaten kayıtlı" not in str(exc):
            raise
    assert registry.get("trend.breakouts") is MultiBreakout
