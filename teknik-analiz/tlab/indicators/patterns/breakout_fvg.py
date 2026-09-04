"""Konsolidasyon Kırılımı + Fair Value Gap (FVG) tarayıcı — Faz 8B/4b, YENİ.

Faz 4b görev metninin tarifine göre (kullanıcının paylaştığı referans
görsel + literatür karışımı — kaynak ayrımı aşağıda) DÖRT aşamalı bir
zincir: KONSOLİDASYON → KIRILIM → FVG (3 mumlu dengesizlik) → RETEST →
ONAY. `wedge.py`/`broadening.py`nin PAYLAŞTIĞI `tlab/core/pattern_state.py::
track_breakout_pattern` state makinesi BİLEREK KULLANILMADI — o makine
"kırılım çizgisi + hedef" ikilisine göre tasarlanmış (PENDING→CONFIRMED→
RETEST_HOLD/TARGET_REACHED), burada ise kırılım İLE retest arasında AYRI,
zorunlu bir ara-adım (FVG oluşumu) var; bu beşinci adımı genel makineye
zorla sığdırmak (`extra_payload` ile FVG bilgisini gizlice taşımak)
okunurluğu bozardı — kendi bespoke döngüsü yazıldı.

**Kaynak ayrımı (görev metninin istediği gibi):**
- KONSOLİDASYON/KIRILIM: Bulkowski tarzı klasik "dar kutu + kırılım"
  (`flag_pennant.py`nin `flag_atr` eşiğiyle AYNI ilke — kutu yüksekliği/ATR).
- FVG (Fair Value Gap): ICT (Inner Circle Trader / "Smart Money Concepts")
  literatüründen — 3 mumlu bir dizide `mum[i-1].high < mum[i+1].low`
  (yükseliş) ya da `mum[i-1].low > mum[i+1].high` (düşüş) olduğunda ORTA
  mumun kapladığı, iki komşu mumun DOKUNMADIĞI fiyat aralığı ("adil değer
  boşluğu" — piyasanın o aralıkta hiç işlem yapmadığı, fiyatın genelde geri
  dönüp "doldurmaya" çalıştığı bir bölge). Retest+onay mantığı da AYNI
  ekolden (fiyatın boşluğa dönüp REDDEDİLMESİ = devam sinyali).

**Non-repaint:** 3 mumlu FVG ancak ÜÇÜNCÜ mum KAPANDIĞINDA bilinir --
`bar_time=detected_at=df.index[i+1]` (orta mumun barı DEĞİL). Kutu/kırılım/
retest/onay hepsi yalnızca KENDİ barına kadar olan veriyle hesaplanır,
geriye yazım yok (`tests/test_patterns/test_breakout_fvg.py::
test_passes_repaint` bunu doğrular)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Literal

import pandas as pd

from tlab.core.indicator import BaseIndicator
from tlab.core.params import BaseParams, params_hash
from tlab.core.types import (
    Box,
    Direction,
    IndicatorMeta,
    IndicatorResult,
    Level,
    Marker,
    Signal,
    SignalState,
    Timeframe,
)
from tlab.features.volatility import atr

_SUFFIX_LABEL_TR: dict[str, str] = {
    "pending": "KONSOLİDASYON", "breakout": "KIRILIM", "fvg_formed": "FVG OLUŞTU",
    "retest": "FVG RETEST", "confirmed": "ONAY", "target_reached": "HEDEFE ULAŞTI",
    "invalidated": "GEÇERSİZ", "expired": "SÜRESİ DOLDU",
}

def _marker_text(suffix: str) -> str:
    return f"BREAKOUT+FVG [{_SUFFIX_LABEL_TR.get(suffix, suffix.upper())}]"


@dataclass(frozen=True)
class BreakoutFvgParams(BaseParams):
    consolidation_bars: int = 10
    box_atr_max: float = 1.5
    breakout_search_bars: int = 15
    min_fvg_atr: float = 0.2
    fvg_search_bars: int = 5
    max_bars_to_retest: int = 20
    confirm_bars: int = 1
    atr_period: int = 14
    vol_k: float = 1.2
    # Faz 0.5, A2 ile AYNI ilke — dördü de takvimsel bir süre (konsolidasyon
    # penceresi, kırılım/FVG/retest için üst bar sınırları); 1D taban kabul
    # edilip diğer zaman dilimlerine ölçeklenir.
    _BAR_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {"consolidation_bars", "breakout_search_bars", "fvg_search_bars", "max_bars_to_retest"}
    )
    require_volume_confirm: bool = False


_FvgDirection = Literal["long", "short"]


class BreakoutFvgIndicator(BaseIndicator):
    meta = IndicatorMeta(
        name="patterns.breakout_fvg",
        version="0.1.0",
        category="patterns",
        description="Konsolidasyon kırılımı + Fair Value Gap (FVG) retest/onay tarayıcı.",
        supported_timeframes=(Timeframe.D1, Timeframe.H4),
    )

    def __init__(self, params: BreakoutFvgParams | None = None) -> None:
        self.params: BreakoutFvgParams = params or BreakoutFvgParams()

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        p = self.params
        n = len(df)
        atr_series = atr(df, p.atr_period)
        high = df["high"].to_numpy()
        low = df["low"].to_numpy()
        close = df["close"].to_numpy()
        volume = df["volume"].to_numpy()

        signals: list[Signal] = []
        levels: list[Level] = []
        boxes: list[Box] = []
        markers: list[Marker] = []
        last_state: dict[str, dict] = {}

        scan_from = p.consolidation_bars - 1
        while scan_from < n:
            box_result = _find_consolidation_box(high, low, atr_series, scan_from, p)
            if box_result is None:
                scan_from += 1
                continue
            born_idx, box_high, box_low = box_result
            window_start = born_idx - p.consolidation_bars + 1

            chain = _track_one_candidate(
                df, born_idx, window_start, box_high, box_low, close, high, low, volume,
                atr_series, p, context,
            )
            if chain is not None:
                pid, direction, box_end_idx, fvg, signals_chain = chain
                signals.extend(signals_chain)

                boxes.append(
                    Box(
                        t0=df.index[window_start], t1=df.index[box_end_idx],
                        low=box_low, high=box_high,
                        label=f"{pid}_consolidation", style="pattern_consolidation",
                    )
                )
                if fvg is not None:
                    fvg_i, fvg_low, fvg_high, fvg_end_idx = fvg
                    boxes.append(
                        Box(
                            t0=df.index[fvg_i], t1=df.index[fvg_end_idx],
                            low=fvg_low, high=fvg_high,
                            label=f"{pid}_fvg", style="pattern_fvg",
                        )
                    )
                target = (box_high - box_low) * (1 if direction == "long" else -1)
                breakout_sig = next(
                    (s for s in signals_chain if s.payload["event"].endswith("_breakout")), None
                )
                if breakout_sig is not None:
                    target_price = float(close[df.index.get_loc(breakout_sig.bar_time)]) + target
                    end_time = _level_end(signals_chain)
                    levels.append(
                        Level(
                            price=target_price, label=f"{pid}_target", style="pattern_target",
                            start=breakout_sig.bar_time, end=end_time,
                        )
                    )
                last_sig = signals_chain[-1]
                markers.append(
                    Marker(
                        t=last_sig.bar_time,
                        price=float(close[df.index.get_loc(last_sig.bar_time)]),
                        text=_marker_text(last_sig.payload["suffix"]),
                        kind=f"pattern_{last_sig.state}:{pid}",
                    )
                )
                if last_sig.state == "confirmed":
                    markers.append(
                        Marker(
                            t=last_sig.bar_time,
                            price=float(close[df.index.get_loc(last_sig.bar_time)]),
                            text="AL" if direction == "long" else "SAT",
                            kind=f"pattern_entry_{direction}:{pid}",
                        )
                    )
                last_state[pid] = {
                    "direction": direction, "state": last_sig.state,
                    "event": last_sig.payload["event"],
                }
                scan_from = max(born_idx + 1, box_end_idx + 1)
            else:
                scan_from = born_idx + 1

        return IndicatorResult(
            indicator=self.meta.name, version=self.meta.version, params_hash=params_hash(p),
            symbol="", timeframe=Timeframe.D1,
            signals=signals, levels=levels, boxes=boxes, markers=markers,
            last_state=last_state,
        )


def _find_consolidation_box(
    high, low, atr_series: pd.Series, end_idx: int, p: BreakoutFvgParams,
) -> tuple[int, float, float] | None:
    """[end_idx-consolidation_bars+1, end_idx] penceresinin dar bir kutu
    olup olmadığını kontrol eder -- yalnızca bu ARALIKTAKİ veriyi kullanır
    (non-repaint: end_idx'ten SONRAKİ hiçbir bar okunmaz)."""
    start = end_idx - p.consolidation_bars + 1
    if start < 0:
        return None
    a = atr_series.iloc[end_idx]
    if pd.isna(a) or a <= 0:
        return None
    win_high = float(high[start : end_idx + 1].max())
    win_low = float(low[start : end_idx + 1].min())
    if (win_high - win_low) > p.box_atr_max * a:
        return None
    return end_idx, win_high, win_low


def _level_end(signals_chain: list[Signal]) -> pd.Timestamp | None:
    terminal = signals_chain[-1]
    if terminal.state in ("pending", "active"):
        return None
    return terminal.bar_time


def _track_one_candidate(  # noqa: PLR0913
    df: pd.DataFrame, born_idx: int, window_start: int, box_high: float, box_low: float,
    close, high, low, volume, atr_series: pd.Series, p: BreakoutFvgParams, context: dict | None,
) -> tuple[str, Direction, int, tuple[int, float, float, int] | None, list[Signal]] | None:
    n = len(df)
    pid = f"breakoutfvg_{window_start}_{born_idx}"
    signals: list[Signal] = [
        _sig(df, born_idx, "long", "pending", 0.5, pid, "pending"),
    ]

    breakout_idx: int | None = None
    direction: Direction | None = None
    breakout_cap = min(n - 1, born_idx + p.breakout_search_bars)
    for t in range(born_idx + 1, breakout_cap + 1):
        if close[t] > box_high:
            breakout_idx, direction = t, "long"
            break
        if close[t] < box_low:
            breakout_idx, direction = t, "short"
            break
    if breakout_idx is None or direction is None:
        signals.append(_sig(df, breakout_cap, "long", "expired", 0.5, pid, "expired"))
        # `scan_from`, çağıran tarafta `box_end_idx+1`e ilerliyor -- burada
        # `born_idx` DEĞİL `breakout_cap` döndürülür, aksi halde her bar
        # neredeyse AYNI (1 bar kaymış) bir "konsolidasyon" adayı olarak
        # yeniden bulunup gereksiz, çakışan aday spam'i üretirdi (2. iterasyonda
        # `populate_registry()` sırasında bulunan GERÇEK bir hata -- df'in
        # kuyruğuna yakın HER bar yeni bir aday doğuruyordu).
        return pid, "long", breakout_cap, None, signals

    vol_ok = True
    if p.require_volume_confirm:
        base_vol = float(volume[window_start : born_idx + 1].mean())
        vol_ok = bool(base_vol > 0 and volume[breakout_idx] >= p.vol_k * base_vol)
    signals.append(
        _sig(df, breakout_idx, direction, "active", 0.6, pid, "breakout", volume_ok=vol_ok)
    )
    if p.require_volume_confirm and not vol_ok:
        signals.append(_sig(df, breakout_idx, direction, "expired", 0.6, pid, "expired"))
        return pid, direction, breakout_idx, None, signals

    fvg = _find_fvg(high, low, breakout_idx, direction, atr_series, n, p)
    if fvg is None:
        expiry_idx = min(n - 1, breakout_idx + p.fvg_search_bars)
        signals.append(_sig(df, expiry_idx, direction, "expired", 0.6, pid, "expired"))
        return pid, direction, expiry_idx, None, signals
    fvg_i, fvg_low, fvg_high = fvg
    signals.append(_sig(df, fvg_i + 1, direction, "active", 0.65, pid, "fvg_formed"))

    retest_idx: int | None = None
    retest_cap = min(n - 1, (fvg_i + 1) + p.max_bars_to_retest)
    for t in range(fvg_i + 2, retest_cap + 1):
        touches = low[t] <= fvg_high and high[t] >= fvg_low
        if touches:
            retest_idx = t
            break
        # Geçersizlik: retest hiç olmadan fiyat konsolidasyon kutusunun
        # KARŞI kenarını kapanışla kırarsa (klasik "yanlış yönde erken
        # kırılım" kuralı, wedge.py/broadening.py'deki AYNI mantık).
        opposite_break = close[t] < box_low if direction == "long" else close[t] > box_high
        if opposite_break:
            signals.append(_sig(df, t, direction, "invalidated", 0.65, pid, "invalidated"))
            return pid, direction, t, (fvg_i, fvg_low, fvg_high, t), signals
    if retest_idx is None:
        signals.append(_sig(df, retest_cap, direction, "expired", 0.65, pid, "expired"))
        return pid, direction, retest_cap, (fvg_i, fvg_low, fvg_high, retest_cap), signals
    signals.append(_sig(df, retest_idx, direction, "active", 0.7, pid, "retest"))

    confirm_streak = 0
    confirm_idx: int | None = None
    confirm_cap = min(n - 1, retest_idx + max(p.confirm_bars, 1) * 10)
    for t in range(retest_idx, confirm_cap + 1):
        beyond = close[t] > fvg_high if direction == "long" else close[t] < fvg_low
        confirm_streak = confirm_streak + 1 if beyond else 0
        if confirm_streak >= p.confirm_bars:
            confirm_idx = t
            break
        opposite_break = close[t] < box_low if direction == "long" else close[t] > box_high
        if opposite_break:
            signals.append(_sig(df, t, direction, "invalidated", 0.7, pid, "invalidated"))
            return pid, direction, t, (fvg_i, fvg_low, fvg_high, t), signals
    if confirm_idx is None:
        signals.append(_sig(df, confirm_cap, direction, "expired", 0.7, pid, "expired"))
        return pid, direction, confirm_cap, (fvg_i, fvg_low, fvg_high, confirm_cap), signals
    signals.append(_sig(df, confirm_idx, direction, "confirmed", 0.8, pid, "confirmed"))

    target_price = (box_high - box_low) * (1 if direction == "long" else -1) + close[breakout_idx]
    target_cap = min(n - 1, confirm_idx + p.max_bars_to_retest * 2)
    for t in range(confirm_idx, target_cap + 1):
        hit = close[t] >= target_price if direction == "long" else close[t] <= target_price
        if hit:
            signals.append(_sig(df, t, direction, "completed", 0.9, pid, "target_reached"))
            return pid, direction, t, (fvg_i, fvg_low, fvg_high, t), signals

    return pid, direction, confirm_idx, (fvg_i, fvg_low, fvg_high, confirm_idx), signals


def _find_fvg(
    high, low, breakout_idx: int, direction: Direction, atr_series: pd.Series, n: int,
    p: BreakoutFvgParams,
) -> tuple[int, float, float] | None:
    """Kırılım hareketi içinde 3 mumlu bir FVG arar -- orta mum `i`,
    `mum[i-1]`/`mum[i+1]` KOMŞU mumlar. Yalnızca ÜÇÜNCÜ mum (i+1)
    KAPANDIĞINDA bilinir (çağıran taraf `bar_time=df.index[i+1]` kullanır)."""
    search_end = min(n - 2, breakout_idx + p.fvg_search_bars)
    for i in range(max(1, breakout_idx - 1), search_end):
        a = atr_series.iloc[i + 1]
        if pd.isna(a) or a <= 0:
            continue
        if direction == "long":
            gap_low, gap_high = float(high[i - 1]), float(low[i + 1])
        else:
            gap_low, gap_high = float(high[i + 1]), float(low[i - 1])
        if gap_high - gap_low >= p.min_fvg_atr * a:
            lo, hi = (gap_low, gap_high) if gap_low <= gap_high else (gap_high, gap_low)
            return i, lo, hi
    return None


def _sig(
    df: pd.DataFrame, idx: int, direction: Direction, state: SignalState, score: float,
    pid: str, suffix: str, **extra: object,
) -> Signal:
    t = df.index[idx]
    return Signal(
        bar_time=t, detected_at=t, direction=direction, state=state, score=score,
        payload={
            "pattern_id": pid, "pattern_name": "breakout_fvg",
            "event": f"breakout_fvg_{suffix}", "suffix": suffix, **extra,
        },
    )
