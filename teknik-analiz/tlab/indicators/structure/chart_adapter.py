"""`structure.*` göstergelerinin `IndicatorResult`ini `tlab/chart`
sözleşmelerine çevirir. `patterns/boundary_adapter.py` ile AYNI ilke:
tarayıcının ZATEN hesapladığını okur, yeniden HESAPLAMAZ.
"""

from __future__ import annotations

import pandas as pd

from tlab.chart.composers.price_structure import StructureLine, StructureReport, StructureZone
from tlab.chart.contracts import XabcdPattern, XabcdPoint
from tlab.chart.tokens import Role
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


def swing_fib_abcd_to_pattern(
    result: IndicatorResult, df: pd.DataFrame
) -> XabcdPattern | None:
    """`structure.swing_fib_abcd` -> `XabcdPattern` (X'SİZ, 4 noktalı).

    AB=CD, XABCD'nin eksik hâli DEĞİL -- kendi başına bir formasyon;
    5 noktalı harmonikler onu İÇERİR. `XabcdPattern` sözleşmesi bu yüzden
    X'siz iskeleti de kabul ediyor ve komposer A-B-C-D'yi tek zikzak
    olarak çiziyor (harmoniğin "B'de birleşen iki kanat" gövdesi burada
    YANLIŞ olurdu).

    En GÜNCEL üçlü seçilir: son üç swing ucu = A, B, C. D, göstergenin
    kendi `D (hedef)` seviyelerinden EN YAKIN olanı (yeniden hesaplanmaz).
    """
    swings = [ln for ln in result.lines if ln.label.startswith("swing_")]
    if len(swings) < 3:
        return None
    swings.sort(key=lambda ln: int(ln.label.rsplit("_", 1)[-1]))

    # Son üç bacağın uçları ardışık dört pivot verir; son üçü A,B,C.
    tail = swings[-3:]
    pivots = [tail[0].points[0], tail[0].points[-1], tail[1].points[-1], tail[2].points[-1]]
    a, b, c = pivots[1], pivots[2], pivots[3]
    pts = [
        XabcdPoint(pd.Timestamp(a[0]), float(a[1]), "A"),
        XabcdPoint(pd.Timestamp(b[0]), float(b[1]), "B"),
        XabcdPoint(pd.Timestamp(c[0]), float(c[1]), "C"),
    ]

    # D hedefleri: "D (hedef): 102.10" etiketli Level'lar. Fiyata EN YAKIN
    # olanı gösterilir -- gösterge her oran için ayrı bir hedef üretiyor
    # (3 aktif hedef tipik) ve hepsini çizmek merdiveni kalabalıklaştırır.
    close = float(df["close"].iloc[-1])
    targets = [lv for lv in result.levels if lv.label.startswith("D (hedef)")]
    theoretical_d = (
        float(min(targets, key=lambda lv: abs(float(lv.price) - close)).price)
        if targets else None
    )

    # AB=CD oranları: bacaklar ZATEN biliniyor, yalnızca biçimlenir.
    ab = b[1] - a[1]
    bc = c[1] - b[1]
    ratios = (
        ("BC/AB", "—" if ab == 0 else f"{abs(bc / ab):.3f}"),
    )
    if theoretical_d is not None and bc != 0:
        ratios += (("CD/BC (hedef)", f"{abs((theoretical_d - c[1]) / bc):.3f}"),)

    last_sig = (
        max(result.signals, key=lambda s: pd.Timestamp(s.bar_time))
        if result.signals else None
    )
    # DURUM sinyalin `state`inden gelir. İlk denemede `last_state
    # ["last_label"]` kullanılmıştı ama o bir SWING etiketi (HH/HL/LH/LL),
    # durum değil -- komposer `_STATE_TR["LH"]` ile KeyError veriyordu.
    _STATE = {
        "completed": "tamamlandi", "invalidated": "gecersiz",
        "active": "aktif", "pending": "izlemede",
    }
    state = _STATE.get(getattr(last_sig, "state", ""), "izlemede")
    return XabcdPattern(
        school="abcd", pattern_name="AB=CD",
        direction="bullish" if c[1] < b[1] else "bearish",
        points=tuple(pts),
        state=state,
        prz=None, theoretical_d=theoretical_d, actual_d=None,
        fib_levels=(), ratios=ratios,
        bars_ago=(
            None if last_sig is None
            else int((df.index > pd.Timestamp(last_sig.bar_time)).sum())
        ),
    )


# Bir trend çizgisinin sağa uzatılabileceği en fazla süre, KENDİ
# bacağının katı olarak. Faz 7'de harmonik `xb` çizgisi için bulunan
# kural: kısa/dik bir bacağın eğimi bugüne projekte edilince fiyat
# eksenini gerçek dışı büyütüyor (100 TL'lik hissede 700 TL'lik
# projeksiyon görülmüştü). `report.py` sahnesi de aynı sınırı koydu.
_MAX_EXTEND_MULT = 3.0

# Aynı anda çizilecek en fazla trend çizgisi. `price_structure` 7-8 aktif
# çizgi üretebiliyor; hepsi çizilince grafik okunmaz oluyor (Faz 7
# "declutter" turunun bulgusu). En ÇOK TEMAS ALMIŞ olanlar seçilir --
# temas sayısı çizginin güvenilirliğinin göstergesi.
_MAX_LINES = 4


def price_structure_to_report(
    result: IndicatorResult, df: pd.DataFrame
) -> StructureReport | None:
    """`structure.price_structure` -> `StructureReport`."""
    n = len(df)
    lines: list[StructureLine] = []
    for ln in result.lines:
        # 1) KIRILMIŞ çizgi çizilmez.
        if ln.broken:
            continue
        if len(ln.points) < 2:
            continue
        (t0, y0), (t1, y1) = ln.points[0], ln.points[-1]
        i0 = int(df.index.searchsorted(pd.Timestamp(t0)))
        i1 = int(df.index.searchsorted(pd.Timestamp(t1)))
        leg = max(i1 - i0, 1)
        # 2) Uzatma bacağın 3 katıyla sınırlı.
        i_end = min(i1 + int(leg * _MAX_EXTEND_MULT), n - 1)
        slope = (float(y1) - float(y0)) / leg
        y_end = float(y1) + slope * (i_end - i1)
        role: Role = "bearish" if ln.style == "resistance" else "bullish"
        pretty = "Direnç" if ln.style == "resistance" else "Destek"
        lines.append(
            StructureLine(
                points=(
                    (pd.Timestamp(df.index[i0]), float(y0)),
                    (pd.Timestamp(df.index[i_end]), y_end),
                ),
                role=role, label=pretty, touches=ln.touches,
            )
        )
    # HER TÜRDEN en çok temas alanlar. Salt temasa göre sıralamak tek
    # tarafı seçiyordu (ölçüldü: 4 çizginin dördü de "Destek"), oysa
    # yapı raporunun işi fiyatın ÜSTÜNDE ve ALTINDA ne olduğunu birlikte
    # göstermek.
    per_side = max(_MAX_LINES // 2, 1)
    picked: list[StructureLine] = []
    for role in ("bearish", "bullish"):
        same = sorted(
            (x for x in lines if x.role == role),
            key=lambda x: (x.touches or 0), reverse=True,
        )
        picked.extend(same[:per_side])
    lines = picked

    # 3) Yalnızca AÇIK bölgeler (`Box.t1 is None` = hâlâ sürüyor).
    zones = tuple(
        StructureZone(
            low=float(b.low), high=float(b.high),
            role="bullish" if "support" in b.style else "bearish",
            label="Destek Bölgesi" if "support" in b.style else "Direnç Bölgesi",
        )
        for b in result.boxes
        if b.t1 is None and ("support" in b.style or "resistance" in b.style)
    )

    lv = {level.label: float(level.price) for level in result.levels}
    st = result.last_state or {}
    state = str(st.get("price_vs_zone", "")).upper() or "YAPI"
    last_sig = (
        max(result.signals, key=lambda s: pd.Timestamp(s.bar_time))
        if result.signals else None
    )
    if not lines and not zones and "POC" not in lv:
        return None
    return StructureReport(
        lines=tuple(lines), zones=zones,
        poc=lv.get("POC"), vah=lv.get("VAH"), val=lv.get("VAL"),
        state=state,
        bars_ago=(
            None if last_sig is None
            else int((df.index > pd.Timestamp(last_sig.bar_time)).sum())
        ),
    )
