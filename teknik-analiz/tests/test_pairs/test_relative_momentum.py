"""RelativeMomentumPair: sinyal doğruluğu, context-farkındalıklı repaint testi,
registry kaydı."""

from __future__ import annotations

import pytest

from tests.test_pairs.fixtures import build_cointegrated_pair
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
    df_y, result = _run()
    actual = [(list(df_y.index).index(s.bar_time), s.payload["side"]) for s in result.signals]
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


def test_registers_in_registry() -> None:
    df_y, df_x = build_cointegrated_pair()
    registry.register(RelativeMomentumPair, df_y, sample_context={"x": df_x})
    assert registry.get("pair.relative_momentum") is RelativeMomentumPair
