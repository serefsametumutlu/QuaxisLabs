"""Triple Barrier etiketleme (Lopez de Prado, *Advances in Financial
Machine Learning*) -- bir sinyalin ileri barlarda KAR (üst bariyer), ZARAR
(alt bariyer) veya SÜRE AŞIMI (dikey bariyer) ile mi sonuçlandığını
hesaplar. SAF MATEMATIK, I/O YOK (`abcd_pattern.py` ile AYNI katman ilkesi).

Motivasyon (2026-08-19, kullanicinin harici arastirma kaynagi --
"strateji_3_aegis_meta_filter.py" / "PREDATOR"/"AEGIS" spec'leri): meta-
etiketleme (bir ana sinyalin kaliteisini ikinci bir siniflandiriciyla
filtrelemek) icin egitim etiketi gerekir -- bu modul o etiketi uretir.
`abcd_backtest.backtest_symbol` (portfoy-seviyesi, TEK ACIK POZISYON
kisitlamasi) ile KARISTIRILMAZ -- o motor PORTFOY performansi icin,
bu fonksiyon HER sinyali BAGIMSIZ (digerlerinden etkilenmeden) etiketler,
meta-model egitimi/ozellik cikarimi icin dogru birim budur (AEGIS'in
`_label_signals` fonksiyonuyla AYNI ilke, buraya tasindi -- proje geneli
reuse edilebilir olsun diye)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class BarrierOutcome:
    win: bool
    r_multiple: float
    bars_held: int
    hit: str  # "TP" | "SL" | "TIMEOUT" | "INSUFFICIENT_DATA"


def label_outcome(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    entry_bar: int,
    entry_price: float,
    tp: float,
    sl: float,
    direction: int,
    max_hold_bars: int = 20,
) -> BarrierOutcome:
    """`entry_bar`den (dahil degil, `entry_bar+1`den baslar) ileri en fazla
    `max_hold_bars` bar tarar. Ayni barda HEM TP HEM SL araliginda kalirsa
    (intrabar belirsizlik -- gercek fitil sirasi bilinmez) SL ONCELIKLI
    sayilir (muhafazakar varsayim). `entry_bar+1` seriden tasarsa veya
    risk (|entry-sl|) sifir/negatifse INSUFFICIENT_DATA (win=False, r=0.0)
    doner -- FIRLATMAZ."""
    n = len(close)
    risk = abs(entry_price - sl)
    if entry_bar + 1 >= n or risk <= 0:
        return BarrierOutcome(win=False, r_multiple=0.0, bars_held=0, hit="INSUFFICIENT_DATA")

    end_bar = min(entry_bar + 1 + max_hold_bars, n)
    is_long = direction > 0

    for bar in range(entry_bar + 1, end_bar):
        h, l = float(high[bar]), float(low[bar])
        hit_sl = (l <= sl) if is_long else (h >= sl)
        hit_tp = (h >= tp) if is_long else (l <= tp)
        if hit_sl:
            return BarrierOutcome(win=False, r_multiple=-1.0, bars_held=bar - entry_bar, hit="SL")
        if hit_tp:
            r = abs(tp - entry_price) / risk
            return BarrierOutcome(win=True, r_multiple=float(r), bars_held=bar - entry_bar, hit="TP")

    last_bar = end_bar - 1
    last_close = float(close[last_bar])
    signed_ret = (last_close - entry_price) if is_long else (entry_price - last_close)
    r = signed_ret / risk
    return BarrierOutcome(win=r > 0, r_multiple=float(r), bars_held=last_bar - entry_bar, hit="TIMEOUT")
