"""YFinanceProvider için gerçek ağ bağlantısı gerektiren duman testi.

Varsayılan pytest koşusunda çalışmaz (pyproject.toml: addopts = "-m 'not network'").
Elle çalıştırmak için: pytest tests/test_yfinance_provider.py -m network
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from tlab.core.types import Market, Timeframe, validate_ohlcv
from tlab.data.providers.yfinance_provider import YFinanceProvider


@pytest.mark.network
def test_fetch_daily_bist_returns_valid_ohlcv() -> None:
    provider = YFinanceProvider()
    end = datetime.now(UTC)
    start = end - timedelta(days=30)
    df = provider.fetch("THYAO", Market.BIST, Timeframe.D1, start, end)
    validate_ohlcv(df)
    assert not df.empty
    assert "close_raw" in df.columns
