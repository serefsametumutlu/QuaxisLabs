"""config/universe_{market}.txt dosyalarından sembol evreni okuma."""

from __future__ import annotations

from pathlib import Path

from tlab.core.types import Market

DEFAULT_CONFIG_ROOT = Path(__file__).resolve().parents[2] / "config"

# Faz 8D — universe-level indikatörlerin (alpha_rank/momentum_rank) alfa/
# rölatif-güç hesabı için kıyaslanacağı endeks. İç temsil ("XU100"/"^NDX")
# `to_provider_symbol()` ile aynı yoldan geçer: BIST için ".IS" eklenir
# (XU100 -> XU100.IS), NASDAQ için sembol OLDUĞU GİBİ kalır (^NDX zaten
# yfinance'ın kendi sembolü). Store/Provider'a HİÇBİR özel kod eklenmedi —
# endeks de sıradan bir sembol gibi cache'lenir (data/ohlcv/{market}/{sembol}/).
BENCHMARK_SYMBOL: dict[Market, str] = {
    Market.BIST: "XU100",
    Market.NASDAQ: "^NDX",
}


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
