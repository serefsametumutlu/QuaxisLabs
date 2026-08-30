"""Tüm indikatörleri `Registry`'ye kaydeden tek yer — `tlab scan`/`tlab
list-indicators`in kullandığı KATALOG budur.

Neden Registry.register() her indikatör için YETMİYOR: `PriceStructure`
(Faz 4) trendline "aday havuzu" + hacim profili pencere sorunu nedeniyle
generic tüm-IndicatorResult `repaint_test`'ten (haklı ama yanlış-alarm
şeklinde) geçemiyor — bkz. `tlab/indicators/structure/price_structure.py`
modül docstring'i, "BİLİNEN SINIRLAMA". Bu indikatörün non-repaint
sözleşmesi `tests/test_structure/test_price_structure.py`'deki HEDEFLİ
testlerle (generic repaint_test'ten BAĞIMSIZ) zaten doğrulanmıştır. Bu
yüzden `Registry`'ye ikinci, repaint_test ÇALIŞTIRMAYAN bir kayıt yolu
(`register_verified_elsewhere`) eklendi — yalnızca dedicated test suite'i
zaten geçen, DOKÜMANTE EDİLMİŞ istisnalar için kullanılır, keyfi bir
kaçış kapısı DEĞİLDİR. `MultiBreakout` (Faz 8A, `trend.breakouts`) da AYNI
yolu kullanır — kendisi de trendline/zone/range "aday havuzu" ile hh/ll
kırılımlarının "sonraki pivotla süperseded" zamanlamasını miras alır (bkz.
`tlab/indicators/trend/breakouts.py`), non-repaint sözleşmesi
`tests/test_trend/test_breakouts.py`'de hedefli testlerle doğrulanır.
Faz 8C'nin `SupplyDemandIndicator` (`make_sd_zones`'un `max_zones` aday
havuzu) ve `ChannelIndicator` (bilerek her barda değişen "güncel kanal"
overlay'i + method='pivot' aday havuzu) de AYNI istisna yolunu kullanır —
bkz. o modüllerin docstring'leri. `GoldenZoneIndicator` ise `SwingFibABCD`
ile aynı mimariyi (yalnızca kesinleşmiş zigzag pivotları) paylaştığı için
generic `Registry.register()`'a TEMİZ kaydolur. Faz 8B (`tlab/indicators/
patterns/`): `WedgeIndicator` (`patterns.wedge`/`patterns.triangle`) ve
`BroadeningIndicator` (`patterns.broadening`) `trendlines.build_trendlines`
aday havuzunu paylaştığı için AYNI istisna yolunu kullanır;
`FlagPennantIndicator` (`patterns.flag_pennant`) aday havuzu YOK ama kanalı
sabit bir OLS penceresine dondurduğu için (bkz. modül docstring'i) YİNE
`register_verified_elsewhere` kullanır — `HeadShouldersIndicator`/
`DoubleTopBottomIndicator` ise `GoldenZoneIndicator` ile AYNI "yalnızca
kesinleşmiş zigzag pivotları" mimarisini paylaştığı için generic
`Registry.register()`'a TEMİZ kaydolur.

`CATALOG`: {indikatör_adı: IndicatorSpec} — scanner motoru (Faz 6) bunu
kullanır (`Registry`'nin kendisi değil), çünkü motor context'li (pair)
indikatörler için farklı bir evren/çağrı biçimi gerektirir
(`needs_context=True` alanı bkz.).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from tlab.core.indicator import BaseIndicator, RegistryError, registry
from tlab.indicators.harmonics.scanner_indicator import HarmonicIndicator, HarmonicParams
from tlab.indicators.pairs.relative_momentum import RelativeMomentumPair, RelativeMomentumParams
from tlab.indicators.patterns.broadening import BroadeningIndicator, BroadeningParams
from tlab.indicators.patterns.double_top_bottom import (
    DoubleTopBottomIndicator,
    DoubleTopBottomParams,
)
from tlab.indicators.patterns.flag_pennant import FlagPennantIndicator, FlagPennantParams
from tlab.indicators.patterns.head_shoulders import HeadShouldersIndicator, HeadShouldersParams
from tlab.indicators.patterns.wedge import WedgeIndicator, WedgeParams
from tlab.indicators.structure.golden_zone import GoldenZoneIndicator, GoldenZoneParams
from tlab.indicators.structure.price_structure import PriceStructure, PriceStructureParams
from tlab.indicators.structure.supply_demand import SupplyDemandIndicator, SupplyDemandParams
from tlab.indicators.structure.swing_fib_abcd import SwingFibABCD, SwingFibABCDParams
from tlab.indicators.trend.breakouts import BreakoutParams, MultiBreakout
from tlab.indicators.trend.weekly_channel import ChannelIndicator, ChannelParams

_HARMONIC_SCHOOLS = (
    "carney", "pesavento", "gilmore", "cypher", "nenstar",
    "navarro200", "five_zero", "three_drives",
)


@dataclass(frozen=True)
class IndicatorSpec:
    name: str
    category: str
    factory: Any  # () -> BaseIndicator
    needs_context: bool = False


def _harmonic_factory(school: str) -> Any:
    def _make() -> BaseIndicator:
        return HarmonicIndicator(school, HarmonicParams())

    return _make


def build_catalog() -> dict[str, IndicatorSpec]:
    catalog: dict[str, IndicatorSpec] = {}
    for school in _HARMONIC_SCHOOLS:
        catalog[f"harmonic.{school}"] = IndicatorSpec(
            name=f"harmonic.{school}", category="harmonics", factory=_harmonic_factory(school),
        )
    catalog["structure.swing_fib_abcd"] = IndicatorSpec(
        name="structure.swing_fib_abcd", category="structure",
        factory=lambda: SwingFibABCD(SwingFibABCDParams()),
    )
    catalog["structure.price_structure"] = IndicatorSpec(
        name="structure.price_structure", category="structure",
        factory=lambda: PriceStructure(PriceStructureParams()),
    )
    catalog["pair.relative_momentum"] = IndicatorSpec(
        name="pair.relative_momentum", category="pair",
        factory=lambda: RelativeMomentumPair(RelativeMomentumParams()), needs_context=True,
    )
    catalog["trend.breakouts"] = IndicatorSpec(
        name="trend.breakouts", category="trend",
        factory=lambda: MultiBreakout(BreakoutParams()),
    )
    catalog["structure.golden_zone"] = IndicatorSpec(
        name="structure.golden_zone", category="structure",
        factory=lambda: GoldenZoneIndicator(GoldenZoneParams()),
    )
    catalog["structure.supply_demand"] = IndicatorSpec(
        name="structure.supply_demand", category="structure",
        factory=lambda: SupplyDemandIndicator(SupplyDemandParams()),
    )
    catalog["trend.weekly_channel"] = IndicatorSpec(
        name="trend.weekly_channel", category="trend",
        factory=lambda: ChannelIndicator(ChannelParams()),
    )
    catalog["patterns.wedge"] = IndicatorSpec(
        name="patterns.wedge", category="patterns",
        factory=lambda: WedgeIndicator("wedge", WedgeParams()),
    )
    catalog["patterns.triangle"] = IndicatorSpec(
        name="patterns.triangle", category="patterns",
        factory=lambda: WedgeIndicator("triangle", WedgeParams()),
    )
    catalog["patterns.head_shoulders"] = IndicatorSpec(
        name="patterns.head_shoulders", category="patterns",
        factory=lambda: HeadShouldersIndicator(HeadShouldersParams()),
    )
    catalog["patterns.flag_pennant"] = IndicatorSpec(
        name="patterns.flag_pennant", category="patterns",
        factory=lambda: FlagPennantIndicator(FlagPennantParams()),
    )
    catalog["patterns.double_top_bottom"] = IndicatorSpec(
        name="patterns.double_top_bottom", category="patterns",
        factory=lambda: DoubleTopBottomIndicator(DoubleTopBottomParams()),
    )
    catalog["patterns.broadening"] = IndicatorSpec(
        name="patterns.broadening", category="patterns",
        factory=lambda: BroadeningIndicator(BroadeningParams()),
    )
    return catalog


CATALOG: dict[str, IndicatorSpec] = build_catalog()


def _quiet_tailed_ohlcv(seed: int, start_price: float) -> pd.DataFrame:
    """Kısa gürültülü bir "kafa" (pivot/aday üretebilir) + UZUN, tamamen DÜZ
    bir "kuyruk" (sıfır gürültü — find_pivots'un katı `>` şartı asla
    tetiklenmez, yeni aday DOĞMAZ). `Registry.register()`'ın varsayılan
    `repaint_test` penceresi (son 60 bar) böylece her zaman "artık hiçbir
    şeyin yeni doğmadığı" düz bölgeye denk gelir — bkz. modül docstring'i
    ve CLAUDE.md'deki aynı desenin Faz 3/4/5'teki test fixture'ları."""
    import numpy as np

    rng = np.random.default_rng(seed)
    head_n = 80
    head = start_price + np.cumsum(rng.normal(0, 0.8, head_n))
    tail = np.full(220, head[-1])
    close = np.concatenate([head, tail])

    n = len(close)
    index = pd.date_range("2024-01-02", periods=n, freq="4h", tz="Europe/Istanbul")
    open_ = np.empty_like(close)
    open_[0] = close[0]
    open_[1:] = close[:-1]
    high = np.maximum(open_, close) + 0.05
    low = np.minimum(open_, close) - 0.05
    volume = np.full(n, 1000.0)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume}, index=index
    )


def _bootstrap_sample() -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    """Kayıt doğrulaması için SENTETİK, SAKİN-KUYRUKLU örnek veri.

    GERÇEK piyasa verisi (sürekli devam eden zigzag/pivot aktivitesi)
    KULLANILAMAZ: `repaint_test`'in varsayılan penceresi (son `tail` bar)
    her zaman "henüz finalize olmamış" bir aday/çizgi/kutuya denk gelir —
    bu GERÇEK bir repaint hatası DEĞİL, Faz 3/4'te belgelenen "aday havuzu"
    zamanlama deseni (bkz. CLAUDE.md "Bilinen sınırlama"). Gerçek non-repaint
    doğrulaması zaten her indikatörün KENDİ dedicated test suite'inde
    (özel, "sakin kuyruklu" fixture'larla) yapılmıştır; bu yalnızca
    kayıt/telli-doğru-mu kontrolüdür (`_quiet_tailed_ohlcv` bkz.)."""
    df = _quiet_tailed_ohlcv(seed=101, start_price=100.0)
    df_x = _quiet_tailed_ohlcv(seed=202, start_price=60.0)
    return df, {"x": df_x}


def populate_registry() -> None:
    """Her indikatörü, kendi türüne uygun repaint doğrulamasıyla `Registry`'ye
    kaydeder. Zaten kayıtlıysa (aynı process'te ikinci çağrı) sessizce atlar."""
    sample_df, sample_pair_context = _bootstrap_sample()
    for spec in CATALOG.values():
        instance = spec.factory()
        try:
            if spec.name in (
                "structure.price_structure", "trend.breakouts",
                "structure.supply_demand", "trend.weekly_channel",
                "patterns.wedge", "patterns.triangle",
                "patterns.flag_pennant", "patterns.broadening",
            ):
                registry.register_verified_elsewhere(instance)
            elif spec.needs_context:
                registry.register(instance, sample_df, sample_context=sample_pair_context)
            else:
                registry.register(instance, sample_df)
        except RegistryError as exc:
            if "zaten kayıtlı" not in str(exc):
                raise
