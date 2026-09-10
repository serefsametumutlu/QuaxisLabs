"""`structure.*` göstergelerinin `IndicatorResult`ini `tlab/chart`
sözleşmelerine çevirir. `patterns/boundary_adapter.py` ile AYNI ilke:
tarayıcının ZATEN hesapladığını okur, yeniden HESAPLAMAZ.
"""

from __future__ import annotations

import pandas as pd

from tlab.core.types import IndicatorResult
from tlab.indicators.structure.zones_v2 import Zone

# `supply_demand.py`nin Box.style'ları -> sözleşmedeki `kind`/`freshness`.
_ZONE_KIND = {"demand": "talep", "supply": "arz",
              "demand_broken": "talep", "supply_broken": "arz"}


def supply_demand_to_zones(result: IndicatorResult, df: pd.DataFrame) -> list[Zone] | None:
    """`structure.supply_demand` -> `list[Zone]` (en fazla 1 arz + 1 talep).

    HANGİ bölgenin gösterileceğini ADAPTÖR SEÇMEZ: gösterge bunu zaten
    `last_state["nearest_demand"]`/`["nearest_supply"]` ile karara
    bağlamış (ATR-normalize uzaklığa göre). Burada yalnızca o karar
    okunur; `created` için kutulardan eşleşen kayıt bulunur (arama, yeni
    bir hesap DEĞİL).

    Kırılmış bölgeler ÇİZİLMEZ: `flip=True` mekanizması kırılan bölgeyi
    AYNI [low,high] ile karşıt türde yeniden doğurduğu için eski+yeni
    neredeyse özdeş kutular üst üste biniyordu; kullanıcı bunu 4 ayrı
    sembolde "her yerde alakasız kesikli çizgiler" diye bildirmişti
    (bkz. PROGRESS_LOG 2026-09-05).
    """
    st = result.last_state or {}
    close = float(df["close"].iloc[-1])
    zones: list[Zone] = []

    for key, kind in (("nearest_demand", "talep"), ("nearest_supply", "arz")):
        info = st.get(key)
        if not isinstance(info, dict):
            continue
        low, high = float(info["low"]), float(info["high"])
        created = _created_of(result, kind, low, high, df)
        mid = (low + high) / 2
        zones.append(
            Zone(
                kind=kind, low=low, high=high, created=created,
                touches=0,                     # göstergede taşınmıyor
                freshness="taze" if info.get("fresh") else "test_edildi",
                departure_atr=float(info.get("distance_atr", 0.0)),
                distance_pct=abs(mid - close) / close * 100 if close else 0.0,
            )
        )
    return zones or None


def _created_of(
    result: IndicatorResult, kind: str, low: float, high: float, df: pd.DataFrame,
) -> pd.Timestamp:
    """Bölgenin doğum barını kutulardan bul; bulunamazsa ilk bar."""
    want = {"talep": "demand", "arz": "supply"}[kind]
    best, best_err = None, float("inf")
    for b in result.boxes:
        if b.style != want:
            continue
        err = abs(float(b.low) - low) + abs(float(b.high) - high)
        if err < best_err:
            best, best_err = b, err
    # Eşleşme fiyat aralığının %1'inden uzaksa GÜVENME -- yanlış kutunun
    # tarihini göstermektense grafiğin başını kullan.
    span = max(high - low, 1e-9)
    if best is not None and best_err <= span * 0.01:
        return pd.Timestamp(best.t0)
    return pd.Timestamp(df.index[0])
