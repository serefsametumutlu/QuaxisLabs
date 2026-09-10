"""`structure.*` göstergelerinin `IndicatorResult`ini `tlab/chart`
sözleşmelerine çevirir. `patterns/boundary_adapter.py` ile AYNI ilke:
tarayıcının ZATEN hesapladığını okur, yeniden HESAPLAMAZ.
"""

from __future__ import annotations

import pandas as pd

from tlab.core.types import IndicatorResult
from tlab.indicators.structure.fib_retracement import FibLevel, FibRetracement
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


def golden_zone_to_fib(result: IndicatorResult, df: pd.DataFrame) -> FibRetracement | None:
    """`structure.golden_zone` -> `FibRetracement` (EN GÜNCEL swing).

    Gösterge her swing için ayrı bir altın bölge üretiyor (fikstürlerde
    5-9 tane). Hepsini çizmek `tlab/viz`de "curcuna"ya yol açmıştı
    (renderer'ın `_declutter_levels` kuralı da aynı sonuca varmıştı):
    yalnızca EN GÜNCEL swing çizilir.

    Bölge sınırları YENİDEN HESAPLANMAZ -- `last_state["band_low"]`/
    `["band_high"]` göstergenin KENDİ güncel bandı.
    """
    swings = [ln for ln in result.lines if ln.label.startswith("swing_")]
    if not swings:
        return None
    # BASKIN swing seçilir (en büyük fiyat açıklığı), EN YENİ değil.
    #
    # Göstergenin kendi `last_state` bandı EN SON swing'e bağlı ve o swing
    # minik bir düzeltme olabiliyor: `impulse_retrace` fikstüründe son
    # swing 125.60->118.37 (6 bar) iken fiyat 210'a çıkıp 150'ye dönmüştü;
    # altın bölge ekranın dibinde anlamsız bir şerit olarak kalıyordu
    # (GÖRÜLEREK bulundu). `structure/fib_retracement.py` tespit edicisi
    # de aynı sonuca varmış ve BASKIN swing'i seçiyor.
    #
    # AÇIK KARAR: "hangi swing güncel altın bölgeyi tanımlar" bir TESPİT
    # sorusu; gösterge (en yeni) ile bu adaptör (en baskın) FARKLI cevap
    # veriyor. Kalıcı çözüm göstergenin kendisinde olmalı -- bkz.
    # docs/KALAN_ISLER.md "karar gerekenler".
    def _span(ln) -> float:
        return abs(float(ln.points[-1][1]) - float(ln.points[0][1]))

    dominant = max(swings, key=_span)
    (t0, p0), (t1, p1) = dominant.points[0], dominant.points[-1]
    p0, p1 = float(p0), float(p1)

    # Bölge, SEÇİLEN swing'in 0.618-0.786 geri çekilmesi (standart tanım).
    # Göstergenin `band_*` alanı son swing'e ait olduğu için burada
    # KULLANILAMAZ -- farklı bir swing çizildiğinde uyumsuz kalırdı.
    band_low = p1 - (p1 - p0) * 0.786
    band_high = p1 - (p1 - p0) * 0.618

    # Fib merdiveni: bu swing'in kendi 0.382/0.5/0.618/0.786 seviyeleri.
    # Göstergenin `levels`i hangi swing'e ait olduğunu TAŞIMIYOR (hepsi
    # "fib_0.5" adında), bu yüzden merdiven swing uçlarından biçimlenir --
    # oranlar SABİT, yeni bir tespit kararı değil.
    span = p1 - p0
    levels = tuple(
        FibLevel(r, p1 - span * r, f"{r:.3f}")
        for r in (0.382, 0.5, 0.618, 0.786)
    )

    close = float(df["close"].iloc[-1])
    return FibRetracement(
        start_time=pd.Timestamp(t0), start_price=p0,
        end_time=pd.Timestamp(t1), end_price=p1,
        direction="up" if p1 > p0 else "down",
        levels=levels,
        golden_low=float(min(band_low, band_high)),
        golden_high=float(max(band_low, band_high)),
        in_golden_zone=min(band_low, band_high) <= close <= max(band_low, band_high),
    )
