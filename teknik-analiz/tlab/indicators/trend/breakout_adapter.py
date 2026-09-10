"""`trend.breakouts` -> `BoundaryPattern` (TEK kırılım).

**KARAR: neden tek kırılım?** Bu gösterge ~20 kırılım türü tarıyor ve
tek bir sembolde 126 kırılım + 78 retest + 29 yanlış-kırılım üretebiliyor.
Hepsini çizmek okunmaz -- Faz 8A'da bu gösterge tam bu yüzden galeriden
ÇIKARILMIŞTI ("düzeltemiyorsak kaldıralım"). Çözüm çizmemek değil,
SEÇMEK: göstergenin KENDİ `quality_score`u (hacim 0.30 / seviye yaşı
0.20 / temas 0.20 / gövde 0.15 / mesafe 0.15) zaten bu iş için var.

Seçim kuralı:
  1. YANLIŞ ÇIKMIŞ kırılımlar elenir (`false_break` ile zincirlenenler),
  2. son `window` bar içindekiler arasından
  3. `quality_score`u EN YÜKSEK olan seçilir.

Tazelik ÖNCE, kalite SONRA değil -- tersi: pencere bir KAPI, skor
sıralayıcı. Yoksa dünkü çöp bir kırılım, üç gün önceki sağlam olanı
gölgeliyor.

`BoundaryPattern` sözleşmesi bunu zaten kapsıyor (docstring'inde
"kırılım seviyeleri" yazılı): tek sınır = KIRILAN seviye.
"""

from __future__ import annotations

import pandas as pd

from tlab.chart.contracts import BoundaryLine, BoundaryPattern, ChartSignal
from tlab.chart.tokens import Role
from tlab.core.types import IndicatorResult

# Kırılım kaç bar geriye kadar aday sayılır. Rotanın tazelik kapısıyla
# (60) AYNI mantık; buradaki daha dar çünkü bir kırılım "haber"dir,
# formasyon gibi haftalarca olgunlaşmaz.
_WINDOW_BARS = 40

_TYPE_TR: dict[str, str] = {
    "downtrend_break": "DÜŞEN TREND KIRILIMI",
    "uptrend_break": "YÜKSELEN TREND KIRILIMI",
    "range_breakout_up": "YATAY ARALIK KIRILIMI (YUKARI)",
    "range_breakout_down": "YATAY ARALIK KIRILIMI (AŞAĞI)",
    "zone_break_up": "BÖLGE KIRILIMI (YUKARI)",
    "zone_break_down": "BÖLGE KIRILIMI (AŞAĞI)",
    "hh_break": "TEPE KIRILIMI",
    "ll_break": "DİP KIRILIMI",
    "channel_break_up": "KANAL KIRILIMI (YUKARI)",
    "channel_break_down": "KANAL KIRILIMI (AŞAĞI)",
    "bb_break_up": "BOLLINGER KIRILIMI (YUKARI)",
    "bb_break_down": "BOLLINGER KIRILIMI (AŞAĞI)",
}


def to_pattern(result: IndicatorResult, df: pd.DataFrame) -> BoundaryPattern | None:
    breaks = [s for s in result.signals if s.payload.get("event") == "break"]
    if not breaks:
        return None

    # 1) Yanlış çıkmış olanları ele.
    failed = {
        s.payload.get("pattern_id")
        for s in result.signals
        if s.payload.get("event") == "false_break"
    }
    # 2) Pencere kapısı.
    cutoff_i = max(len(df) - _WINDOW_BARS, 0)
    cutoff = pd.Timestamp(df.index[cutoff_i])
    fresh = [
        s for s in breaks
        if s.payload.get("pattern_id") not in failed
        and pd.Timestamp(s.bar_time) >= cutoff
    ]
    if not fresh:
        return None
    # 3) En yüksek kalite.
    best = max(fresh, key=lambda s: float(s.payload.get("quality_score", 0.0)))

    pid = best.payload.get("pattern_id")
    level = best.payload.get("level_value")
    if level is None:
        return None
    level = float(level)
    up = str(best.direction) == "long"
    role: Role = "bullish" if up else "bearish"

    # Kırılan seviye YATAY bir sınır olarak: seviyenin doğduğu bardan
    # (yaşı payload'da) kırılımın birkaç bar sonrasına.
    brk_t = pd.Timestamp(best.bar_time)
    i_brk = int(df.index.searchsorted(brk_t))
    age = int(best.payload.get("level_age_bars", 0) or 0)
    i0 = max(i_brk - age, 0)
    i1 = min(i_brk + max(age // 2, 10), len(df) - 1)

    btype = str(best.payload.get("break_type", ""))
    facts: list[tuple[str, str]] = [
        ("Kırılan seviye", f"{level:,.2f}"),
        ("Kalite", f"{float(best.payload.get('quality_score', 0.0)):.2f}"),
        ("Seviye yaşı", f"{age} bar"),
        ("Temas", str(best.payload.get("touches", "—"))),
    ]
    vr = best.payload.get("volume_ratio")
    if vr is not None:
        ok = "✓" if str(best.payload.get("volume_ok")) == "True" else "✗"
        facts.append(("Hacim", f"{float(vr):.2f}x {ok}"))

    # Retest bu kırılımı TUTTU mu?
    held = any(
        s.payload.get("event") == "retest_hold" and s.payload.get("pattern_id") == pid
        for s in result.signals
    )
    state = "RETEST TUTTU" if held else "KIRILDI"

    return BoundaryPattern(
        kind="breakout",
        title=_TYPE_TR.get(btype, btype.replace("_", " ").upper() or "KIRILIM"),
        state=state,
        boundaries=(
            BoundaryLine(
                points=(
                    (pd.Timestamp(df.index[i0]), level),
                    (pd.Timestamp(df.index[i1]), level),
                ),
                role=role, name="Kırılan Seviye", dash="dash",
            ),
        ),
        facts=tuple(facts),
        signal=ChartSignal(
            t=brk_t, price=level, text="AL" if up else "SAT",
            role=role, below=up,
        ),
        bars_ago=int((df.index > brk_t).sum()),
    )
