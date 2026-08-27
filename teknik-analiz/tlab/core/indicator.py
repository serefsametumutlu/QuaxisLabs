"""BaseIndicator soyut arayüzü ve repaint-doğrulamalı registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

import pandas as pd

from tlab.core.errors import RegistryError
from tlab.core.params import BaseParams
from tlab.core.types import IndicatorMeta, IndicatorResult, validate_ohlcv


class BaseIndicator(ABC):
    """Tüm indikatörlerin uyduğu sözleşme.

    __call__ sırası: validate_ohlcv → compute → sonuç doğrulama (tüm
    bar_time'lar df.index içinde, detected_at >= bar_time, detected_at
    son bardan sonra olamaz — geleceğe bakış şüphesi).
    """

    meta: ClassVar[IndicatorMeta]
    params: BaseParams

    @abstractmethod
    def compute(self, df: pd.DataFrame, context: dict[str, Any] | None = None) -> IndicatorResult:
        """Verilen OHLCV DataFrame'i üzerinden IndicatorResult üretir."""

    def __call__(self, df: pd.DataFrame, context: dict[str, Any] | None = None) -> IndicatorResult:
        validate_ohlcv(df)
        result = self.compute(df, context)
        self._validate_result(df, result)
        return result

    @staticmethod
    def _validate_result(df: pd.DataFrame, result: IndicatorResult) -> None:
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


class Registry:
    """Yalnızca repaint testinden geçen indikatörleri barındıran kayıt defteri.

    Registry'e kaydedilmemiş bir indikatör tarayıcı tarafından çalıştırılamaz
    (bkz. Faz 6).
    """

    def __init__(self) -> None:
        self._indicators: dict[str, type[BaseIndicator]] = {}

    def register(self, indicator_cls: type[BaseIndicator], sample_df: pd.DataFrame) -> type[BaseIndicator]:
        """indicator_cls'i sample_df üzerinde çalıştırıp repaint testinden
        geçerse registry'e ekler; geçmezse RegistryError fırlatır."""
        from tlab.testing.repaint import repaint_test  # döngüsel import'tan kaçınma

        name = indicator_cls.meta.name
        if name in self._indicators:
            raise RegistryError(f"'{name}' zaten kayıtlı")

        report = repaint_test(indicator_cls(), sample_df)
        if not report.passed:
            raise RegistryError(
                f"'{name}' repaint testinden geçemedi:\n" + "\n".join(report.mismatches)
            )

        self._indicators[name] = indicator_cls
        return indicator_cls

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
