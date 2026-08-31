"""`tlab.core.indicator.UniverseIndicator` sözleşmesi: validate_ohlcv +
sonuç doğrulama (BaseIndicator ile PAYLAŞILAN `_validate_indicator_result`)."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import pytest

from tlab.core.errors import OHLCVError
from tlab.core.indicator import UniverseIndicator
from tlab.core.params import BaseParams
from tlab.core.types import IndicatorMeta, IndicatorResult, Signal, Timeframe

_TZ = "Europe/Istanbul"


def _df(n: int = 10, start_price: float = 100.0) -> pd.DataFrame:
    idx = pd.date_range("2024-01-02", periods=n, freq="1D", tz=_TZ)
    close = pd.Series(start_price, index=idx)
    return pd.DataFrame(
        {"open": close, "high": close + 1, "low": close - 1, "close": close, "volume": 1000.0},
        index=idx,
    )


@dataclass(frozen=True)
class _EchoParams(BaseParams):
    pass


class _EchoIndicator(UniverseIndicator):
    meta = IndicatorMeta(
        name="test.echo_universe", version="0.1.0", category="universe",
        description="test", supported_timeframes=(Timeframe.D1,),
    )

    def __init__(self, bad_signal_symbol: str | None = None) -> None:
        self.params = _EchoParams()
        self._bad_signal_symbol = bad_signal_symbol

    def compute_universe(self, universe, index_df):
        results = {}
        for symbol, df in universe.items():
            signals = []
            if symbol == self._bad_signal_symbol:
                # Kasıtlı ihlal: df.index'te olmayan bir bar_time.
                bad_time = df.index[0] - pd.Timedelta(days=1)
                signals.append(
                    Signal(
                        bar_time=bad_time, detected_at=bad_time, direction="long",
                        state="confirmed", score=1.0, payload={},
                    )
                )
            results[symbol] = IndicatorResult(
                indicator=self.meta.name, version=self.meta.version, params_hash="h",
                symbol=symbol, timeframe=Timeframe.D1, signals=signals,
            )
        return results


def test_universe_indicator_returns_subset_of_input() -> None:
    universe = {"A": _df(), "B": _df()}
    index_df = _df()
    results = _EchoIndicator()(universe, index_df)
    assert set(results) == {"A", "B"}


def test_universe_indicator_rejects_invalid_ohlcv_in_universe() -> None:
    bad = _df().copy()
    bad.iloc[0, bad.columns.get_loc("high")] = -999.0  # high < close ihlali
    with pytest.raises(OHLCVError):
        _EchoIndicator()({"A": bad}, _df())


def test_universe_indicator_validates_each_symbols_result() -> None:
    universe = {"A": _df(), "B": _df()}
    with pytest.raises(ValueError, match="df.index içinde değil"):
        _EchoIndicator(bad_signal_symbol="A")(universe, _df())
