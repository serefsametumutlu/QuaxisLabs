"""RelativeMomentumPair: sinyal doğruluğu, context-farkındalıklı repaint testi,
registry kaydı."""

from __future__ import annotations

import pytest

from tests.test_pairs.fixtures import build_cointegrated_pair
from tlab.core.errors import RegistryError
from tlab.core.indicator import registry
from tlab.indicators.pairs.relative_momentum import RelativeMomentumPair, RelativeMomentumParams
from tlab.testing.repaint import repaint_test

_PARAMS = RelativeMomentumParams(
    window=40, k=2.0, beta_method="one", beta_window=200, min_periods=200,
    y_symbol="YT", x_symbol="XT",
)

_EXPECTED_SIGNALS = [
    (252, "y"), (308, "x"), (357, "y"), (408, "x"), (454, "y"),
]


def _run():
    df_y, df_x = build_cointegrated_pair()
    result = RelativeMomentumPair(_PARAMS)(df_y, context={"x": df_x})
    return df_y, result


def test_signals_at_expected_bars_and_sides() -> None:
    """`result.signals` artık her geçişin kendi "hâlâ taze mi" takip
    sinyalini de içerir (state="active", 2026-09-03) -- bu test yalnızca
    GERÇEK geçiş olaylarını (state="confirmed") kontrol eder."""
    df_y, result = _run()
    actual = [
        (list(df_y.index).index(s.bar_time), s.payload["side"])
        for s in result.signals if s.state == "confirmed"
    ]
    assert actual == _EXPECTED_SIGNALS


def test_signal_confirms_reentry_not_first_breach() -> None:
    """Sinyal, eşiği İLK aşan barda değil, eşiğin İÇİNE geri DÖNDÜĞÜ barda
    üretilir (görev metnindeki "dönüş onaylandı" ayrımı)."""
    _, result = _run()
    for s in result.signals:
        z_prev, z_now = s.payload["z_prev"], s.payload["z_now"]
        if s.payload["side"] == "y":
            assert z_prev < -_PARAMS.k
            assert z_now >= -_PARAMS.k
        else:
            assert z_prev > _PARAMS.k
            assert z_now <= _PARAMS.k


def test_holding_boxes_alternate_and_are_contiguous() -> None:
    df_y, result = _run()
    idx = list(df_y.index)
    assert [b.style for b in result.boxes] == [
        "y_holding", "x_holding", "y_holding", "x_holding", "y_holding",
    ]
    for prev, nxt in zip(result.boxes, result.boxes[1:], strict=False):
        assert idx.index(nxt.t0) == idx.index(prev.t1) + 1


def test_pre_statistics_in_signal_payload() -> None:
    _, result = _run()
    for s in result.signals:
        for key in ("corr", "adf_pvalue", "halflife", "beta"):
            assert key in s.payload


def test_series_keys_present() -> None:
    _, result = _run()
    for key in ("y_norm", "x_norm", "z", "upper", "lower", "portfolio", "buyhold_5050", "holding"):
        assert key in result.series
    assert (result.series["upper"] == _PARAMS.k).all()
    assert (result.series["lower"] == -_PARAMS.k).all()


def test_last_state_fields() -> None:
    _, result = _run()
    for key in (
        "z_today", "z_yesterday", "holding", "signal_today", "portfolio_value",
        "net_pnl", "return_pct", "n_trades", "max_drawdown_pct", "win_rate_pct",
        "avg_holding_bars", "zone_state",
    ):
        assert key in result.last_state


def test_no_signal_before_min_periods() -> None:
    _, result = _run()
    assert all(
        list(build_cointegrated_pair()[0].index).index(s.bar_time) >= _PARAMS.min_periods
        for s in result.signals
    )


def test_relative_momentum_passes_context_aware_repaint() -> None:
    """repaint_test'e context verildiğinde, context DataFrame'i de df ile
    AYNI cut_time'da kesiliyor mu — bu, Faz 5'in çekirdek test altyapısına
    eklediği tek değişiklik (bkz. tlab/testing/repaint.py)."""
    df_y, df_x = build_cointegrated_pair()
    indicator = RelativeMomentumPair(_PARAMS)
    cut_points = list(range(480, len(df_y) + 1))
    report = repaint_test(indicator, df_y, cut_points=cut_points, context={"x": df_x})
    assert report.passed, report.mismatches


def test_uncut_context_gives_identical_result_here_by_construction() -> None:
    """RelativeMomentumPair, X verisini HER ZAMAN `df.index` (Y) ile inner-join
    ettikten SONRA kullanıyor (`common_idx`, Y'nin kendi kesiğiyle sınırlı) —
    bu yüzden context'i kesmeden vermek BU indikatörde fiilen fark YARATMAZ
    (leak yüzeyi yok, "join sonra kısıtla" deseni yeterli). Context-aware
    repaint_test genişletmesi (tlab/testing/repaint.py) yine de GENEL bir
    altyapı parçasıdır — gelecekteki, bu deseni takip etmeyen bir context'li
    indikatör için tek koruma budur. Bu test, mevcut indikatörün zaten
    güvenli OLDUĞUNU doğrular (repaint testinin yakalayacağı bir şey
    kalmadığını göstererek), context-kesmenin GEREKSİZLİĞİNİ değil."""
    df_y, df_x = build_cointegrated_pair()
    indicator = RelativeMomentumPair(_PARAMS)
    cut = 300
    partial_df = df_y.iloc[:cut]
    cut_time = partial_df.index[-1]

    with_full_context = indicator(partial_df, {"x": df_x})
    partial_context = {"x": df_x.loc[df_x.index <= cut_time]}
    with_cut_context = indicator(partial_df, partial_context)

    assert with_full_context.last_state["z_today"] == pytest.approx(
        with_cut_context.last_state["z_today"]
    )
    assert with_full_context.last_state["n_trades"] == with_cut_context.last_state["n_trades"]


# --- mode="mean_reversion" (Faz 2, 2C) --------------------------------------
#
# AYNI `build_cointegrated_pair()` fixture'ı + AYNI temel parametreler
# (window/k/beta_method/beta_window/min_periods) kullanılıyor -- yalnızca
# `mode`/`exit_k`/`stop_k`/`max_hold_bars`/`lockout_until_reentry`
# değişiyor. Beklenen bar/olay dizileri gerçek kod çalıştırılarak
# ÖLÇÜLDÜ (bkz. `tests/test_harmonics/test_schools.py`'deki AYNI ilke).


def _mr_params(**overrides: object) -> RelativeMomentumParams:
    base = {
        "window": 40, "k": 2.0, "beta_method": "one", "beta_window": 200,
        "min_periods": 200, "y_symbol": "YT", "x_symbol": "XT", "mode": "mean_reversion",
        "exit_k": 0.5, "stop_k": 3.0, "max_hold_bars": 100, "lockout_until_reentry": True,
    }
    base.update(overrides)
    return RelativeMomentumParams(**base)  # type: ignore[arg-type]


def _run_mr(params: RelativeMomentumParams):  # type: ignore[no-untyped-def]
    df_y, df_x = build_cointegrated_pair()
    result = RelativeMomentumPair(params)(df_y, context={"x": df_x})
    return df_y, result


def test_mean_reversion_natural_exit_reverts_inside_exit_k() -> None:
    """max_hold_bars büyük tutulunca (zaman stopu devreye girmeden) z
    exit_k'nın içine döndüğünde pozisyon KAPANIR -- rotasyonelin aksine
    burada GERÇEK bir "nakit" ara dönemi var (giriş barından ~40 bar sonra)."""
    df_y, result = _run_mr(_mr_params(max_hold_bars=100))
    idx = list(df_y.index)
    events = [(idx.index(s.bar_time), s.payload["event"]) for s in result.signals]
    assert events == [
        (244, "mr_entry_long"), (285, "mr_exit"),
        (295, "mr_entry_short"), (339, "mr_exit"),
        (346, "mr_entry_long"), (384, "mr_exit"),
        (395, "mr_entry_short"), (434, "mr_exit"),
        (444, "mr_entry_long"), (486, "mr_exit"),
        (495, "mr_entry_short"),
    ]
    # Son sinyal (495) HENÜZ kapanmadı (dizi orada bitiyor) -- confirmed kalır.
    assert result.signals[-1].state == "confirmed"


def test_mean_reversion_time_stop_forces_close_before_natural_reversion() -> None:
    """max_hold_bars kısa tutulunca (z henüz exit_k'ye dönmeden) zorunlu
    zaman-stopu devreye girer."""
    df_y, result = _run_mr(_mr_params(max_hold_bars=30))
    idx = list(df_y.index)
    time_stops = [
        idx.index(s.bar_time) for s in result.signals if s.payload["event"] == "mr_time_stop"
    ]
    assert len(time_stops) == 5  # 6 girişin ilk 5'i zaman stopuyla kapanıyor (son açık kalıyor)
    for entry_bar, stop_bar in zip([244, 295, 346, 395, 444], time_stops, strict=True):
        assert stop_bar == entry_bar + 30


def test_mean_reversion_stop_k_triggers_before_exit_or_time_stop() -> None:
    """Sıkı bir stop_k (giriş eşiği k=2.0'a yakın), z GİRİŞTEN SONRA biraz
    daha ıraksadığında zorunlu tasfiyeye yol açar."""
    df_y, result = _run_mr(_mr_params(stop_k=2.3, max_hold_bars=100))
    idx = list(df_y.index)
    first_entry = next(s for s in result.signals if s.payload["event"] == "mr_entry_long")
    first_stop = next(s for s in result.signals if s.payload["event"] == "mr_stop")
    assert idx.index(first_entry.bar_time) == 244
    assert idx.index(first_stop.bar_time) == 245
    assert abs(first_stop.payload["z"]) > _mr_params(stop_k=2.3).stop_k


def test_mean_reversion_lockout_prevents_immediate_reentry_after_stop() -> None:
    """`lockout_until_reentry=True`: stop SONRASI z hâlâ giriş bandının
    (±k) DIŞINDAYKEN yeni giriş YOK -- `lockout_until_reentry=False` AYNI
    ayarlarla HEMEN yeniden girer (t=246, entry ile stop arası TEK bar)."""
    df_y, locked = _run_mr(_mr_params(stop_k=2.3, max_hold_bars=100, lockout_until_reentry=True))
    _, unlocked = _run_mr(
        _mr_params(stop_k=2.3, max_hold_bars=100, lockout_until_reentry=False)
    )
    idx = list(df_y.index)

    locked_events = [idx.index(s.bar_time) for s in locked.signals[:3]]
    assert locked_events == [244, 245, 295]  # giriş, stop, SONRAKİ giriş çok sonra

    unlocked_events = [idx.index(s.bar_time) for s in unlocked.signals[:4]]
    assert unlocked_events == [244, 245, 246, 285]  # stoptan HEMEN sonraki barda yeniden girer


def test_mean_reversion_position_series_only_three_values() -> None:
    _, result = _run_mr(_mr_params())
    values = set(result.series["position"].unique().tolist())
    assert values <= {-1.0, 0.0, 1.0}


def test_mean_reversion_series_keys_present() -> None:
    _, result = _run_mr(_mr_params())
    for key in (
        "y_norm", "x_norm", "z", "upper", "lower", "exit_upper", "exit_lower",
        "stop_upper", "stop_lower", "portfolio", "position",
    ):
        assert key in result.series
    assert (result.series["exit_upper"] == 0.5).all()
    assert (result.series["stop_lower"] == -3.0).all()


def test_mean_reversion_last_state_fields() -> None:
    _, result = _run_mr(_mr_params())
    for key in (
        "z_today", "z_yesterday", "position", "signal_today", "portfolio_value",
        "net_pnl", "return_pct", "n_trades", "max_drawdown_pct", "win_rate_pct",
        "avg_holding_bars", "zone_state",
    ):
        assert key in result.last_state
    assert result.last_state["position"] in (
        "YT UZUN / XT KISA", "YT KISA / XT UZUN", "NAKİT",
    )


def test_mean_reversion_boxes_labeled_with_both_legs() -> None:
    _, result = _run_mr(_mr_params(max_hold_bars=100))
    assert result.boxes  # en az bir pozisyon dönemi var
    for b in result.boxes:
        assert b.style in ("y_holding", "x_holding")
        assert "UZUN" in b.label and "KISA" in b.label


def test_mean_reversion_coint_monitor_disabled_by_default() -> None:
    assert RelativeMomentumParams().coint_monitor_window is None


def test_mean_reversion_default_stop_k_and_max_hold_bars_tuned() -> None:
    """2026-09-04 kullanıcı kararı: 17-çiftlik gerçek listede IS/OOS ayrımlı
    bir parametre taraması (243 kombinasyon) `stop_k`/`max_hold_bars`'ın
    (window/k SABİT tutulup -- rotasyonel modu etkilemesin diye) 3.0/30
    yerine 4.0/40 olduğunda OOS kazanma oranını %53.2->%53.5, medyan
    getiriyi 0->+0.86%'a çıkardığını gösterdi (bkz. `stop_k` alanının
    docstring'i). Bu test o kararı kilitler -- `window`/`k` (rotasyonel
    modun da paylaştığı alanlar) KASITLI OLARAK değişmedi."""
    p = RelativeMomentumParams()
    assert p.stop_k == 4.0
    assert p.max_hold_bars == 40
    assert p.window == 60  # rotasyonel modun 2026-08-29 kararı -- DEĞİŞMEDİ
    assert p.k == 2.0  # aynı gerekçe -- DEĞİŞMEDİ
    assert p.exit_k == 0.5  # tarama zaten en iyi olarak bunu buldu, DEĞİŞMEDİ


def test_mean_reversion_coint_monitor_forces_exit_when_enabled() -> None:
    """Faz 2, 2C -- `coint_monitor_window` verilip eşik (`coint_break_p_
    threshold`) imkânsız derecede gevşek (0.0 -- her ölçülebilir p-değeri
    bunu geçer) tutulunca, HER giriş bir sonraki barda `mr_cointegration_
    broken` ile zorunlu kapatılmalı -- mekanizmanın GERÇEKTEN pozisyonu
    düzleştirdiğinin (z henüz dönmeden) doğrudan kanıtı."""
    df_y, result = _run_mr(
        _mr_params(coint_monitor_window=90, coint_break_p_threshold=0.0, max_hold_bars=100)
    )
    idx = list(df_y.index)
    events = [(idx.index(s.bar_time), s.payload["event"]) for s in result.signals[:6]]
    assert events == [
        (244, "mr_entry_long"), (245, "mr_cointegration_broken"),
        (246, "mr_entry_long"), (247, "mr_cointegration_broken"),
        (248, "mr_entry_long"), (249, "mr_cointegration_broken"),
    ]


def test_mean_reversion_rotational_default_mode_is_unaffected() -> None:
    """`mode` varsayılanı hâlâ "rotational" -- Faz 2, 2C mevcut testleri
    (bu dosyanın üstündeki `_PARAMS`, `mode` HİÇ belirtmiyor) DEĞİŞMEDEN
    geçmeye devam ediyor (bkz. dosyanın geri kalanı) -- bu test yalnızca
    varsayılanın kendisini kilitler."""
    assert RelativeMomentumParams().mode == "rotational"


def test_mean_reversion_passes_context_aware_repaint() -> None:
    df_y, df_x = build_cointegrated_pair()
    indicator = RelativeMomentumPair(_mr_params())
    cut_points = list(range(480, len(df_y) + 1))
    report = repaint_test(indicator, df_y, cut_points=cut_points, context={"x": df_x})
    assert report.passed, report.mismatches


def test_registers_in_registry() -> None:
    df_y, df_x = build_cointegrated_pair()
    try:
        registry.register(RelativeMomentumPair(), df_y, sample_context={"x": df_x})
    except RegistryError as exc:
        if "zaten kayıtlı" not in str(exc):
            raise  # baska test dosyasi (tlab.indicators.bootstrap) zaten kaydetmis olabilir
    assert registry.get("pair.relative_momentum") is RelativeMomentumPair
