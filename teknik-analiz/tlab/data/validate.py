"""Veri kalitesi denetimi: boşluk, hacim anomalisi, aşırı gap, tekrar/tz hatası.

core.types.validate_ohlcv şema/iç-tutarlılık denetimidir (sert kural, ihlalde
istisna fırlatır). Bu modül takvime göre eksik seans gibi daha "yumuşak" veri
kalitesi sinyallerini raporlar (DataQualityReport: warnings/errors) — hata
fırlatmaz, rapor döner; hangi sembollerin taramadan dışlanacağına çağıran
(CLI) karar verir.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from tlab.core.types import Market, Timeframe
from tlab.data.calendar import is_trading_day

_LOG_RETURN_GAP_THRESHOLD = 0.5


@dataclass
class DataQualityReport:
    symbol: str
    timeframe: Timeframe
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def check_data_quality(
    df: pd.DataFrame, symbol: str, market: Market, timeframe: Timeframe
) -> DataQualityReport:
    report = DataQualityReport(symbol=symbol, timeframe=timeframe)

    if df.index.tz is None:
        report.errors.append("Index tz-aware değil")
    if df.index.has_duplicates:
        dupes = df.index[df.index.duplicated()].tolist()
        report.errors.append(f"Tekrarlayan zaman damgası: {dupes[:5]}")

    non_positive = df.index[df["volume"] <= 0]
    if len(non_positive) > 0:
        report.warnings.append(
            f"Sıfır/negatif hacim: {len(non_positive)} bar, örn. {non_positive[:5].tolist()}"
        )

    ratio = df["close"].div(df["close"].shift(1))
    with np.errstate(divide="ignore", invalid="ignore"):
        log_returns = pd.Series(np.log(ratio.to_numpy()), index=ratio.index)
    big_gaps = log_returns[log_returns.abs() > _LOG_RETURN_GAP_THRESHOLD]
    if not big_gaps.empty:
        report.warnings.append(
            f"Split şüphesi — |log getiri| > {_LOG_RETURN_GAP_THRESHOLD} olan "
            f"{len(big_gaps)} bar: {big_gaps.index[:5].tolist()}"
        )

    if timeframe is Timeframe.D1 and len(df) > 0:
        present_dates = set(df.index.date)
        all_days = pd.date_range(df.index[0].date(), df.index[-1].date(), freq="D")
        missing = [
            d.date()
            for d in all_days
            if is_trading_day(d.date(), market) and d.date() not in present_dates
        ]
        if missing:
            report.warnings.append(
                f"Takvime göre eksik seans: {len(missing)} gün, örn. {missing[:5]}"
            )

    return report
