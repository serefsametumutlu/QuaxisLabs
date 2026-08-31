"""BaseIndicator soyut arayüzü ve repaint-doğrulamalı registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

import pandas as pd

from tlab.core.errors import RegistryError
from tlab.core.params import BaseParams
from tlab.core.types import IndicatorMeta, IndicatorResult, validate_ohlcv


def _validate_indicator_result(df: pd.DataFrame, result: IndicatorResult) -> None:
    """`BaseIndicator`/`UniverseIndicator` arasında paylaşılan sonuç doğrulaması
    (tüm bar_time'lar df.index içinde, detected_at >= bar_time, detected_at
    son bardan sonra olamaz — geleceğe bakış şüphesi)."""
    last_bar = df.index[-1]
    for signal in result.signals:
        if signal.bar_time not in df.index:
            raise ValueError(f"Signal.bar_time df.index içinde değil: {signal.bar_time}")
        if signal.detected_at < signal.bar_time:
            raise ValueError(
                f"Signal.detected_at ({signal.detected_at}) "
                f"bar_time'dan ({signal.bar_time}) önce olamaz"
            )
        if signal.detected_at > last_bar:
            raise ValueError(
                f"Signal.detected_at ({signal.detected_at}) son bardan "
                f"({last_bar}) sonra olamaz — geleceğe bakış şüphesi"
            )


class BaseIndicator(ABC):
    """Tüm TEKİL (symbol, timeframe) indikatörlerinin uyduğu sözleşme.

    __call__ sırası: validate_ohlcv → compute → sonuç doğrulama (tüm
    bar_time'lar df.index içinde, detected_at >= bar_time, detected_at
    son bardan sonra olamaz — geleceğe bakış şüphesi). Evren-geneli (Faz 8D
    "universe" kategorisi) indikatörler için bkz. `UniverseIndicator` —
    FARKLI bir sözleşme (tek df yerine {symbol: df} sözlüğü + endeks df'si,
    tek IndicatorResult yerine {symbol: IndicatorResult} sözlüğü) gerektiği
    için bu sınıftan TÜRETİLMEZ, kardeş bir ABC'dir.
    """

    meta: ClassVar[IndicatorMeta]
    params: BaseParams

    @abstractmethod
    def compute(self, df: pd.DataFrame, context: dict[str, Any] | None = None) -> IndicatorResult:
        """Verilen OHLCV DataFrame'i üzerinden IndicatorResult üretir."""

    def __call__(self, df: pd.DataFrame, context: dict[str, Any] | None = None) -> IndicatorResult:
        validate_ohlcv(df)
        result = self.compute(df, context)
        _validate_indicator_result(df, result)
        return result


class UniverseIndicator(ABC):
    """Faz 8D "universe" kategorisi indikatörlerinin uyduğu sözleşme
    (`alpha_rank`/`momentum_rank`) — sıralama (rank_pct) TANIM GEREĞİ tüm
    evrenin AYNI bardaki skorlarını birlikte görmeyi gerektirir, bu yüzden
    `BaseIndicator.compute(df, context)`'in tekil-sembol imzasına UYMAZ.

    `__call__`, TÜM evren df'lerini + endeks df'sini `validate_ohlcv`'den
    geçirir, `compute_universe`'i çağırır, dönen HER sembolün
    IndicatorResult'ını KENDİ df'sine göre doğrular (`BaseIndicator` ile
    AYNI `_validate_indicator_result`).
    """

    meta: ClassVar[IndicatorMeta]
    params: BaseParams

    @abstractmethod
    def compute_universe(
        self, universe: dict[str, pd.DataFrame], index_df: pd.DataFrame
    ) -> dict[str, IndicatorResult]:
        """`universe`: {sembol: OHLCV df}, `index_df`: kıyaslama endeksi
        (bkz. `tlab/data/universe.py::BENCHMARK_SYMBOL`). Dönen sözlük
        `universe`'in bir ALT KÜMESİ olabilir (ör. yetersiz geçmişi olan
        semboller atlanabilir) — FAZLASI olamaz."""

    def __call__(
        self, universe: dict[str, pd.DataFrame], index_df: pd.DataFrame
    ) -> dict[str, IndicatorResult]:
        for df in universe.values():
            validate_ohlcv(df)
        validate_ohlcv(index_df)
        results = self.compute_universe(universe, index_df)
        for symbol, result in results.items():
            _validate_indicator_result(universe[symbol], result)
        return results


class Registry:
    """Yalnızca repaint testinden geçen indikatörleri barındıran kayıt defteri.

    Registry'e kaydedilmemiş bir indikatör tarayıcı tarafından çalıştırılamaz
    (bkz. Faz 6).
    """

    def __init__(self) -> None:
        self._indicators: dict[str, type[BaseIndicator]] = {}

    def register(
        self,
        indicator: BaseIndicator,
        sample_df: pd.DataFrame,
        sample_context: dict[str, pd.DataFrame] | None = None,
    ) -> BaseIndicator:
        """`indicator` ÖRNEĞİNİ (sınıf değil — bkz. aşağıdaki not) sample_df
        (+ context alan indikatörler için sample_context, ör.
        RelativeMomentumPair'in ikinci sembolü) üzerinde çalıştırıp repaint
        testinden geçerse registry'e ekler; geçmezse RegistryError fırlatır.

        Örnek (class değil) alır çünkü `HarmonicIndicator` gibi TEK bir
        sınıf birden fazla mantıksal indikatörü temsil edebilir (8 ekol,
        `meta.name` yalnızca `__init__`'te, INSTANCE üzerinde bilinir —
        class-level `meta` niteliği yok). `type(indicator)` ile sınıf
        kaydedilir, `get()` yine bir SINIF döner (geriye dönük uyumlu)."""
        from tlab.testing.repaint import repaint_test  # döngüsel import'tan kaçınma

        name = indicator.meta.name
        if name in self._indicators:
            raise RegistryError(f"'{name}' zaten kayıtlı")

        report = repaint_test(indicator, sample_df, context=sample_context)
        if not report.passed:
            raise RegistryError(
                f"'{name}' repaint testinden geçemedi:\n" + "\n".join(report.mismatches)
            )

        self._indicators[name] = type(indicator)
        return indicator

    def register_verified_elsewhere(self, indicator: BaseIndicator) -> BaseIndicator:
        """`register()`'ın generic `repaint_test`'i ÇALIŞTIRMAYAN istisna
        yolu — YALNIZCA non-repaint sözleşmesi zaten DEDICATED bir test
        suite'i ile doğrulanmış, dokümante edilmiş bir istisna için
        kullanılır (bkz. `tlab/indicators/bootstrap.py` docstring'i —
        şu an tek örnek: `PriceStructure`, Faz 4 "BİLİNEN SINIRLAMA").
        Keyfi bir kaçış kapısı DEĞİLDİR — yeni bir çağıran eklerken önce
        neden generic teste giremediğini belgelemelisiniz."""
        name = indicator.meta.name
        if name in self._indicators:
            raise RegistryError(f"'{name}' zaten kayıtlı")
        self._indicators[name] = type(indicator)
        return indicator

    def get(self, name: str) -> type[BaseIndicator]:
        try:
            return self._indicators[name]
        except KeyError as exc:
            raise RegistryError(f"'{name}' registry'de kayıtlı değil") from exc

    def list(self, category: str | None = None) -> list[str]:
        if category is None:
            return sorted(self._indicators)
        return sorted(
            name for name, cls in self._indicators.items() if cls.meta.category == category
        )


registry = Registry()
