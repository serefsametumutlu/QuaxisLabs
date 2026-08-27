"""tlab.features.volume_profile için birim testleri ve repaint testi.

profile() zaman/onay kavramı taşımaz (fibonacci.py ile aynı felsefe) — bu
yüzden repaint sarmalayıcısı, her bar için KENDİ sabit geriye dönük
penceresini hesaplayan bir "genişleyen tarihçe" olarak tasarlandı: her end
barı için hesaplanan POC/value-area yalnızca o bardan ÖNCEKİ (dahil)
verilere bağlıdır, bu yüzden birikimli sonuç repaint_test ile doğrulanabilir.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from zoneinfo import ZoneInfo

import pandas as pd

from tlab.core.indicator import BaseIndicator
from tlab.core.params import BaseParams, params_hash
from tlab.core.types import IndicatorMeta, IndicatorResult, Level, Timeframe
from tlab.features.volume_profile import profile
from tlab.testing.fixtures import make_trend
from tlab.testing.repaint import repaint_test

TZ = ZoneInfo("Europe/Istanbul")


def _controlled_window() -> pd.DataFrame:
    """5 bin (100-110, bin genişliği 2), hacimler: 10,50,100,30,5 -> POC bin2
    (105), value_area(0.70) -> [102,106]."""
    idx = pd.date_range("2024-01-02 10:00", periods=5, freq="1D", tz=TZ)
    rows = [
        {"open": 101.05, "high": 101.1, "low": 100.0, "close": 101.05, "volume": 10.0},
        {"open": 103.0, "high": 103.1, "low": 102.9, "close": 103.0, "volume": 50.0},
        {"open": 105.0, "high": 105.1, "low": 104.9, "close": 105.0, "volume": 100.0},
        {"open": 107.0, "high": 107.1, "low": 106.9, "close": 107.0, "volume": 30.0},
        {"open": 109.0, "high": 110.0, "low": 108.1, "close": 109.0, "volume": 5.0},
    ]
    return pd.DataFrame(rows, index=idx)


# --- profile ---------------------------------------------------------------


def test_profile_poc_is_highest_volume_bin() -> None:
    vp = profile(_controlled_window(), bins=5, value_area_pct=0.70)
    assert math.isclose(vp.poc, 105.0)


def test_profile_value_area_expands_from_poc() -> None:
    vp = profile(_controlled_window(), bins=5, value_area_pct=0.70)
    assert math.isclose(vp.value_area_low, 102.0)
    assert math.isclose(vp.value_area_high, 106.0)


def test_profile_bin_count_and_total_volume_preserved() -> None:
    vp = profile(_controlled_window(), bins=5)
    assert len(vp.price_bins) == 5
    assert len(vp.volumes) == 5
    assert math.isclose(sum(vp.volumes), 195.0)


def test_profile_gaussian_fit_returns_floats_or_none() -> None:
    vp = profile(_controlled_window(), bins=5)
    if vp.gaussian_mu is not None:
        assert isinstance(vp.gaussian_mu, float)
        assert isinstance(vp.gaussian_sigma, float)
        # tek belirgin tepe (bin2) civarında olmalı, aşırı sapmasın
        assert 100.0 <= vp.gaussian_mu <= 110.0


def test_profile_flat_price_window_does_not_raise() -> None:
    idx = pd.date_range("2024-01-02 10:00", periods=3, freq="1D", tz=TZ)
    df = pd.DataFrame(
        {"open": [100.0] * 3, "high": [100.0] * 3, "low": [100.0] * 3,
         "close": [100.0] * 3, "volume": [10.0, 20.0, 30.0]},
        index=idx,
    )
    vp = profile(df, bins=4)
    assert math.isclose(sum(vp.volumes), 60.0)


# --- mini-indikatör repaint testi -------------------------------------------


@dataclass(frozen=True)
class RollingVPParams(BaseParams):
    window: int = 15
    bins: int = 8


class RollingVolumeProfileIndicator(BaseIndicator):
    """Her bar için, o bara kadarki son `window` barlık SABİT pencereyle
    profile() hesaplar; POC/value-area Level olarak birikimli yayınlanır.
    Her bar kendi (yalnızca geçmişe bakan) penceresine bağlı olduğundan,
    repaint_test bu birikimli tarihçeyi tam eşitlikle doğrulayabilir."""

    meta = IndicatorMeta(
        name="test.rolling_volume_profile",
        version="0.1.0",
        category="testing",
        description="Faz 2 volume_profile.py repaint kanıt sarmalayıcısı.",
        supported_timeframes=(Timeframe.D1, Timeframe.H4),
    )

    def __init__(self, params: RollingVPParams | None = None) -> None:
        self.params = params or RollingVPParams()

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        window, bins = self.params.window, self.params.bins
        levels: list[Level] = []
        for end in range(window - 1, len(df)):
            w = df.iloc[end - window + 1 : end + 1]
            vp = profile(w, bins=bins)
            t = df.index[end]
            levels.append(Level(price=vp.poc, label=f"poc_{end}", style="poc", start=t))
            levels.append(Level(price=vp.value_area_high, label=f"vah_{end}", style="va", start=t))
            levels.append(Level(price=vp.value_area_low, label=f"val_{end}", style="va", start=t))

        return IndicatorResult(
            indicator=self.meta.name, version=self.meta.version,
            params_hash=params_hash(self.params), symbol="TEST", timeframe=Timeframe.D1,
            levels=levels,
        )


def test_rolling_volume_profile_indicator_passes_repaint() -> None:
    df = make_trend(n=60, slope=0.3, noise=1.5, seed=17)
    report = repaint_test(RollingVolumeProfileIndicator(), df, tail=30)
    assert report.passed, report.mismatches
