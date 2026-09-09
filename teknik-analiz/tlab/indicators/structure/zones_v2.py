"""Arz/talep bölgeleri — pivot çıpalı, sade.

Kullanıcının şikâyeti (2026-09-05): *"her hissenin her durumda dip ve
tepelerine göre supply ve demand bölgeleri bellidir... supply kırmızı
demand yeşil ile resmedilmeli"*, ve (2026-09-08): *"sade ve temiz bir şey
olmalı... her grafikte sadece sağ tarafına mesela demand zone yazmalı ve
o aralıktaki değerler yazılmalı"*.

Metodoloji (araştırma sonucu):
  - Bölge bir SWING PIVOTUNA çıpalanır: swing high -> arz, swing low ->
    talep. Rastgele bir fiyat aralığı değil.
  - DIŞ kenar swing'in ekstremi, İÇ kenar çevredeki mumların gövde
    sınırıdır (fitil ortalaması).
  - Bölgeden çıkış hareketi ATR ile doğrulanır: zayıf bir çıkış bölge
    saymaz.
  - Bölge yüksekliği ATR'nin belli bir katını aşamaz (aşarsa "bölge"
    değil, gürültüdür).
  - GÜÇ = temas sayısı. Tazelik: taze / test edildi / kırıldı.

Ekranda AZ SAYIDA bölge olmalı: en güçlü N tanesi gösterilir. Eski
uygulamanın hatası her adayı çizmesiydi.

Hesap yapar, çizmez.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from tlab.features.swings import find_pivots


@dataclass(frozen=True)
class Zone:
    kind: str            # "arz" | "talep"
    low: float
    high: float
    created: pd.Timestamp
    touches: int
    freshness: str       # "taze" | "test_edildi" | "kirildi"
    departure_atr: float
    distance_pct: float  # son kapanışa uzaklık

    @property
    def mid(self) -> float:
        return (self.low + self.high) / 2


def _atr_series(df: pd.DataFrame, period: int = 14) -> pd.Series:
    h, low, c = df["high"], df["low"], df["close"]
    prev = c.shift(1)
    tr = pd.concat([h - low, (h - prev).abs(), (low - prev).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def detect_zones(
    df: pd.DataFrame,
    *,
    left: int = 3,
    right: int = 3,
    max_height_atr: float = 2.5,
    min_departure_atr: float = 1.8,
    wick_window: int = 2,
    max_zones_per_side: int = 2,
    merge_gap_atr: float = 0.5,
) -> list[Zone]:
    """En güçlü arz ve talep bölgeleri. Bulunamazsa BOŞ liste."""
    if len(df) < 60:
        return []

    atr = _atr_series(df)
    close = df["close"]
    last = float(close.iloc[-1])
    o, h, low_, c = (df[k].to_numpy() for k in ("open", "high", "low", "close"))
    n = len(df)

    out: list[Zone] = []
    for p in find_pivots(df, left=left, right=right):
        i = p.bar_idx
        a = float(atr.iloc[i])
        if not np.isfinite(a) or a <= 0:
            continue

        lo_w = max(0, i - wick_window)
        hi_w = min(n, i + wick_window + 1)
        is_supply = p.kind == "high"

        # Dış kenar: swing ekstremi. İç kenar: çevredeki gövde sınırı.
        if is_supply:
            outer = float(h[lo_w:hi_w].max())
            inner = float(np.maximum(o[lo_w:hi_w], c[lo_w:hi_w]).mean())
        else:
            outer = float(low_[lo_w:hi_w].min())
            inner = float(np.minimum(o[lo_w:hi_w], c[lo_w:hi_w]).mean())
        z_low, z_high = min(outer, inner), max(outer, inner)

        if (z_high - z_low) > max_height_atr * a:
            continue                                   # bölge değil, gürültü

        # Çıkış hareketi: bölgeden sonraki 10 barda ne kadar uzaklaşıldı
        j = min(n, i + 11)
        if j - i < 4:
            continue
        seg = c[i:j]
        departure = (float(seg.min()) - z_low if is_supply else z_high - float(seg.max()))
        departure = abs(departure) / a
        if departure < min_departure_atr:
            continue                                   # zayıf çıkış -> bölge saymaz

        # Temas ve kırılma: bölge doğduktan SONRAKİ barlar
        after = slice(i + right + 1, n)
        hh, ll, cc = h[after], low_[after], c[after]
        if len(cc) == 0:
            continue
        inside = (hh >= z_low) & (ll <= z_high)
        touches = int(np.count_nonzero(np.diff(np.r_[False, inside].astype(int)) == 1))
        broken = bool((cc > z_high).any()) if is_supply else bool((cc < z_low).any())

        freshness = "kirildi" if broken else ("taze" if touches == 0 else "test_edildi")
        out.append(
            Zone(
                kind="arz" if is_supply else "talep",
                low=z_low, high=z_high, created=p.bar_time, touches=touches,
                freshness=freshness, departure_atr=float(departure),
                distance_pct=abs(((z_low + z_high) / 2 - last) / max(last, 1e-9)),
            )
        )

    # Kırılmış bölgeler GÖSTERİLMEZ (kullanıcı: "sade ve temiz").
    alive = [z for z in out if z.freshness != "kirildi"]

    # ÇAKIŞAN bölgeler birleştirilir. Aynı tepeyi çevreleyen komşu
    # pivotlar neredeyse aynı aralığı üretiyor; ikisini birden çizmek
    # grafiği kalabalıklaştırıyordu (ilk denemede iki arz bölgesi
    # 61.46-62.39 ve 62.06-62.91 olarak üst üste bindi).
    merged: list[Zone] = []
    for kind in ("arz", "talep"):
        side = sorted((z for z in alive if z.kind == kind), key=lambda z: z.low)
        cur: Zone | None = None
        gap = float(atr.iloc[-1]) * merge_gap_atr
        for z in side:
            # Yalnızca ÇAKIŞANLAR değil, aralarında ATR'nin yarısından az
            # boşluk olanlar da birleşir: ilk denemede 61.46-63.32 ile
            # 63.65-64.55 çakışmadıkları için ayrı kaldı ama grafikte
            # ince bir çizgiyle ayrılmış TEK bir blok gibi göründüler.
            if cur is not None and z.low <= cur.high + gap:
                cur = Zone(
                    kind=kind, low=min(cur.low, z.low), high=max(cur.high, z.high),
                    created=min(cur.created, z.created),
                    touches=max(cur.touches, z.touches),
                    freshness="taze" if cur.freshness == z.freshness == "taze" else "test_edildi",
                    departure_atr=max(cur.departure_atr, z.departure_atr),
                    distance_pct=min(cur.distance_pct, z.distance_pct),
                )
            else:
                if cur is not None:
                    merged.append(cur)
                cur = z
        if cur is not None:
            merged.append(cur)

    # Fiyata en yakın ve en güçlü olanlar seçilir.
    picked: list[Zone] = []
    for kind in ("arz", "talep"):
        side = [z for z in merged if z.kind == kind]
        side.sort(key=lambda z: (z.distance_pct, -z.touches))
        picked.extend(side[:max_zones_per_side])
    return picked
