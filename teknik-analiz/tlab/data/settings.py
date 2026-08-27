"""config/settings.yaml'ı okuyan tip güvenli ayar yükleyicisi."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

DEFAULT_SETTINGS_PATH = Path(__file__).resolve().parents[2] / "config" / "settings.yaml"

NasdaqSplit = Literal["session_aligned", "equal_split"]


@dataclass(frozen=True)
class Settings:
    """tlab veri katmanı için deterministik ayar seti (frozen — çalışma zamanında değişmez)."""

    adjusted: bool = True
    csv_data_dir: str = "data/external"
    nasdaq_4h_split: NasdaqSplit = "session_aligned"
    yfinance_h1_max_lookback_days: int = 729


def load_settings(path: Path = DEFAULT_SETTINGS_PATH) -> Settings:
    """Yoksa/eksikse varsayılanlara düşen ayar yükleyici."""
    if not path.exists():
        return Settings()
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    data = raw.get("data", {})
    resample = raw.get("resample", {})
    yfinance_cfg = raw.get("providers", {}).get("yfinance", {})

    return Settings(
        adjusted=bool(data.get("adjusted", True)),
        csv_data_dir=str(data.get("csv_data_dir", "data/external")),
        nasdaq_4h_split=resample.get("nasdaq_4h_split", "session_aligned"),
        yfinance_h1_max_lookback_days=int(
            yfinance_cfg.get("h1_max_lookback_days", 729)
        ),
    )
