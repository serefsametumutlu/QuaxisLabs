"""config/universe_{market}.txt dosyalarından sembol evreni okuma."""

from __future__ import annotations

from pathlib import Path

from tlab.core.types import Market

DEFAULT_CONFIG_ROOT = Path(__file__).resolve().parents[2] / "config"


def load_universe(market: Market, root: Path = DEFAULT_CONFIG_ROOT) -> list[str]:
    """Satır başına bir sembol; '#' ile başlayan satırlar ve boş satırlar yok sayılır."""
    path = root / f"universe_{market.value}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Evren dosyası yok: {path}")
    symbols: list[str] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            symbols.append(line.split()[0])
    return symbols
