"""tlab.features.trendlines için birim testleri ve prefix-tutarlılık (repaint)
testi.

Dokunuş/kırılım zamanlamasını kesin kontrol edebilmek için elle inşa edilmiş
bir OHLCV serisi kullanılır: y=x+95 doğrusu (p1=(5,100), p2=(15,110)), t=19 ve
t=23'te dokunuş, t=26-27'de (confirm_bars=2) kırılım. "Uzak" barlarda fiyat
çizgiden bilinçli olarak çok uzak tutulur (ATR ne olursa olsun yanlış
sınıflanmasın diye); kırılım kontrolü zaten ATR'den bağımsızdır (yalnızca
close vs line_val).
"""

from __future__ import annotations

from dataclasses import dataclass
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from tlab.core.indicator import BaseIndicator
from tlab.core.params import BaseParams, params_hash
from tlab.core.types import IndicatorMeta, IndicatorResult, Line, Signal, Timeframe
from tlab.features.swings import Pivot
from tlab.features.trendlines import Trendline, TrendlineKind, _select_top, build_trendlines
from tlab.testing.repaint import repaint_test

TZ = ZoneInfo("Europe/Istanbul")


def _line_val(t: int) -> float:
    return t + 95.0  # slope=1.0, intercept=95.0 (p1=(5,100), p2=(15,110))


def _build_resistance_scenario() -> tuple[pd.DataFrame, list[Pivot]]:
    n = 30
    idx = pd.date_range("2024-01-02 10:00", periods=n, freq="1D", tz=TZ)

    close = {
        0: 50.0, 1: 59.8, 2: 69.6, 3: 79.4, 4: 89.2, 5: 99.0, 6: 100.0, 7: 101.0,
        8: 102.0, 9: 103.0, 10: 104.0, 11: 105.0, 12: 106.0, 13: 107.0, 14: 108.0,
        15: 109.0, 16: 99.5,
        # created_idx=17'den itibaren: uzak, uzak, DOKUNUŞ(19), uzak x3, DOKUNUŞ(23),
        # uzak x2, KIRILIM başlangıcı(26), KIRILIM onayı(27, confirm_bars=2), ...
        17: 90.0, 18: 91.0, 19: 113.8, 20: 92.0, 21: 93.0, 22: 94.0, 23: 117.8,
        24: 95.0, 25: 96.0, 26: 127.0, 27: 128.0, 28: 129.0, 29: 130.0,
    }
    high = dict(close)
    low = dict(close)
    for t in range(n):
        high[t] = close[t] + 1.0
        low[t] = close[t] - 1.0
    # pivot barları ve dokunuş barları: çizgiye göre kesin konumlandırma
    high[5], low[5] = 100.0, 98.0
    high[15], low[15] = 110.0, 108.0
    high[19], low[19] = _line_val(19) - 0.05, _line_val(19) - 2.05  # neredeyse tam temas
    high[23], low[23] = _line_val(23) - 0.05, _line_val(23) - 2.05

    df = pd.DataFrame(
        {
            "open": [close[t] for t in range(n)],
            "high": [high[t] for t in range(n)],
            "low": [low[t] for t in range(n)],
            "close": [close[t] for t in range(n)],
            "volume": [1000.0] * n,
        },
        index=idx,
    )

    p1 = Pivot(
        bar_idx=5, bar_time=idx[5], price=100.0, kind="high",
        confirmed_idx=7, confirmed_time=idx[7],
    )
    p2 = Pivot(
        bar_idx=15, bar_time=idx[15], price=110.0, kind="high",
        confirmed_idx=17, confirmed_time=idx[17],
    )
    return df, [p1, p2]


# --- build_trendlines: dokunuş/kırılım tespiti -----------------------------


def test_build_trendlines_detects_touches_and_break() -> None:
    df, pivots = _build_resistance_scenario()
    lines = build_trendlines(
        df, pivots, "resistance", min_touches=0, max_lines=None, confirm_bars=2
    )

    assert len(lines) == 1
    ln = lines[0]
    assert ln.p1.bar_idx == 5 and ln.p2.bar_idx == 15
    assert ln.created_idx == 17
    assert ln.touches == (19, 23)
    assert ln.broken_at == 27


def test_build_trendlines_min_touches_filters() -> None:
    df, pivots = _build_resistance_scenario()
    lines_ok = build_trendlines(df, pivots, "resistance", min_touches=2, confirm_bars=2)
    assert len(lines_ok) == 1

    lines_excluded = build_trendlines(df, pivots, "resistance", min_touches=3, confirm_bars=2)
    assert lines_excluded == []


def test_build_trendlines_invalid_kind_raises() -> None:
    df, pivots = _build_resistance_scenario()
    with pytest.raises(ValueError):
        build_trendlines(df, pivots, "up")  # type: ignore[arg-type]


def test_build_trendlines_no_line_before_created_idx() -> None:
    """created_idx, df sınırlarının dışındaysa (df henüz o kadar uzun değil) çizgi üretilmez."""
    df, pivots = _build_resistance_scenario()
    short_df = df.iloc[:10]  # p2.confirmed_idx=17 > 10
    lines = build_trendlines(short_df, pivots, "resistance", min_touches=0, max_lines=None)
    assert lines == []


# --- _select_top -------------------------------------------------------


def _fake_line(touches: tuple[int, ...], broken_at: int | None, created_idx: int = 0) -> Trendline:
    dummy = Pivot(
        bar_idx=0, bar_time=pd.Timestamp("2024-01-01"), price=0.0, kind="high",
        confirmed_idx=0, confirmed_time=pd.Timestamp("2024-01-01"),
    )
    return Trendline(
        p1=dummy, p2=dummy, slope=0.0, intercept=0.0, kind="resistance",
        touches=touches, broken_at=broken_at, created_idx=created_idx,
    )


def test_select_top_prefers_unbroken_then_most_touches_then_longest() -> None:
    broken = _fake_line(touches=(1, 2, 3, 4, 5), broken_at=10, created_idx=0)
    few_touches = _fake_line(touches=(1,), broken_at=None, created_idx=0)
    many_touches_short = _fake_line(touches=(1, 2, 3), broken_at=None, created_idx=8)
    many_touches_long = _fake_line(touches=(1, 2, 3), broken_at=None, created_idx=0)

    ranked = _select_top(
        [broken, few_touches, many_touches_short, many_touches_long], max_lines=4
    )
    assert ranked[0] is many_touches_long  # unbroken, en çok temas, en uzun
    assert ranked[1] is many_touches_short  # unbroken, en çok temas, daha kısa
    assert ranked[2] is few_touches  # unbroken, az temas
    assert ranked[3] is broken  # kırılmış -> en sonda


def test_select_top_respects_max_lines() -> None:
    lines = [_fake_line((), None, i) for i in range(5)]
    assert len(_select_top(lines, max_lines=2)) == 2


# --- prefix-tutarlılık (repaint-safety), Trendline nesnesi düzeyinde ------


@pytest.mark.parametrize("cut", [17, 18, 19, 20, 24, 27, 28, 30])
def test_trendline_touches_and_break_prefix_consistent(cut: int) -> None:
    df, pivots = _build_resistance_scenario()
    full_lines = build_trendlines(
        df, pivots, "resistance", min_touches=0, max_lines=None, confirm_bars=2
    )
    full_line = next(ln for ln in full_lines if ln.p1.bar_idx == 5 and ln.p2.bar_idx == 15)

    partial_df = df.iloc[:cut]
    partial_lines = build_trendlines(
        partial_df, pivots, "resistance", min_touches=0, max_lines=None, confirm_bars=2
    )
    partial_line = next(
        (ln for ln in partial_lines if ln.p1.bar_idx == 5 and ln.p2.bar_idx == 15), None
    )
    if partial_line is None:
        assert cut <= pivots[1].confirmed_idx  # yalnızca çizgi henüz "var" değilken None olabilir
        return

    expected_touches = tuple(t for t in full_line.touches if t < cut)
    assert partial_line.touches == expected_touches, f"cut={cut}"

    if full_line.broken_at is not None and full_line.broken_at < cut:
        assert partial_line.broken_at == full_line.broken_at
    else:
        assert partial_line.broken_at is None


# --- mini-indikatör repaint testi ------------------------------------------


@dataclass(frozen=True)
class TrendlineParams(BaseParams):
    pass


class TrendlineIndicator(BaseIndicator):
    """Sabit (dışarıdan verilen) pivotlarla build_trendlines'ı sarmalar.

    Pivotlar sabit tutulur ki bu test yalnızca trendlines.py'nin KENDİ
    non-repaint davranışını izole etsin (find_pivots/swings zaten ayrı
    test edildi). min_touches=0, max_lines=None: "hangi adaylar öne
    çıkıyor" seçimi devre dışı — bkz. trendlines.py modül docstring'i,
    bu seçim df büyüdükçe değişebilir ve mevcut Line-diffing altyapısı
    (points[0][0] baz alınarak) bunun için tasarlanmadı.
    """

    meta = IndicatorMeta(
        name="test.trendline",
        version="0.1.0",
        category="testing",
        description="Faz 2 trendlines.py repaint kanıt sarmalayıcısı.",
        supported_timeframes=(Timeframe.D1, Timeframe.H4),
    )

    def __init__(self, pivots: list[Pivot], kind: TrendlineKind = "resistance") -> None:
        self.params = TrendlineParams()
        self._pivots = pivots
        self._kind = kind

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        lines = build_trendlines(
            df, self._pivots, self._kind, min_touches=0, max_lines=None, confirm_bars=2
        )

        out_lines: list[Line] = []
        signals: list[Signal] = []
        for ln in lines:
            label = f"tl_{ln.p1.bar_idx}_{ln.p2.bar_idx}"
            out_lines.append(
                Line(
                    points=((ln.p1.bar_time, ln.p1.price), (ln.p2.bar_time, ln.p2.price)),
                    label=label, style=ln.kind, extend_right=True,
                )
            )
            direction = "short" if ln.kind == "resistance" else "long"
            for t in ln.touches:
                signals.append(
                    Signal(df.index[t], df.index[t], direction, "active", 1.0, {"line": label})
                )
            if ln.broken_at is not None:
                break_dir = "long" if ln.kind == "resistance" else "short"
                signals.append(
                    Signal(
                        df.index[ln.broken_at], df.index[ln.broken_at], break_dir, "confirmed",
                        1.0, {"line": label, "event": "break"},
                    )
                )

        return IndicatorResult(
            indicator=self.meta.name, version=self.meta.version,
            params_hash=params_hash(self.params), symbol="TEST", timeframe=Timeframe.D1,
            lines=out_lines, signals=signals,
        )


def test_trendline_indicator_passes_repaint() -> None:
    df, pivots = _build_resistance_scenario()
    indicator = TrendlineIndicator(pivots, "resistance")
    # cut_points, çizginin gerçekten üretildiği created_idx+1'den (df.iloc[:cut]
    # bar 17'yi içersin diye) itibaren seçildi — öncesinde Line'ın
    # points[0][0]'ı (p1.bar_time, bar 5) zaten cut_time'dan küçük/eşit olur
    # ama çizgi henüz üretilmemiştir (created_idx=17 >= n); bu, mevcut
    # Line-diffing altyapısının points ile "gerçek oluşum barı"nı ayırt
    # edemediği bilinen bir sınırlama (bkz. trendlines.py docstring).
    report = repaint_test(indicator, df, cut_points=list(range(18, len(df) + 1)))
    assert report.passed, report.mismatches
