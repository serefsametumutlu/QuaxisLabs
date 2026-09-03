"""Faz 0.5 sistemik denetim -- A1 (ortak pivot girisi) + A2 (zaman dilimi
olcekleme) + A3 (supported_timeframes kapisi) + A4 (hacim onayi)
degisikliklerinin ONCESI/SONRASI olcumu.

Gercek BIST onbellek verisiyle calisir (network YOK -- data/ohlcv/bist/
zaten indirilmis, `Store.get()` yalnizca parquet okur). Bkz.
docs/TANI_VE_YOL_HARITASI_v2.md FAZ 0.5, Bolum D ve
docs/STRATEJI_DENETIM_TAM.md Bolum A.

Cikti: konsola tablo + docs/spec/SISTEMIK_DENETIM_v1.md'ye yazilacak
ozet (bu betik yazmaz -- ciktisi elle/ayri bir adimda o dosyaya islenir).
"""

from __future__ import annotations

import json
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from tlab.core.types import Market, Timeframe  # noqa: E402
from tlab.data.providers.yfinance_provider import YFinanceProvider  # noqa: E402
from tlab.data.store import Store  # noqa: E402
from tlab.data.universe import load_universe  # noqa: E402
from tlab.features.swings import significant_pivots  # noqa: E402
from tlab.indicators.bootstrap import scaled_factory  # noqa: E402
from tlab.indicators.patterns.broadening import BroadeningIndicator, BroadeningParams  # noqa: E402
from tlab.indicators.patterns.double_top_bottom import (  # noqa: E402
    DoubleTopBottomIndicator,
    DoubleTopBottomParams,
)
from tlab.indicators.patterns.head_shoulders import (  # noqa: E402
    HeadShouldersIndicator,
    HeadShouldersParams,
)
from tlab.indicators.patterns.wedge import WedgeIndicator, WedgeParams  # noqa: E402
from tlab.indicators.structure.golden_zone import (  # noqa: E402
    GoldenZoneIndicator,
    GoldenZoneParams,
)
from tlab.indicators.structure.price_structure import (  # noqa: E402
    PriceStructure,
    PriceStructureParams,
)

N_SYMBOLS = 120
LOOKBACK_BARS = 600
SEED = 7
_STABLE_STATES = frozenset({"confirmed", "completed"})
_ZONE_EVENTS = frozenset({"zone_touch", "zone_break", "range_breakout"})


def _sample_universe() -> list[str]:
    store = Store(YFinanceProvider())
    uni = load_universe(Market.BIST)
    ok: list[str] = []
    for sym in uni:
        try:
            d1 = store.get(sym, Timeframe.D1, Market.BIST, last_n=LOOKBACK_BARS)
            h4 = store.get(sym, Timeframe.H4, Market.BIST, last_n=LOOKBACK_BARS)
        except FileNotFoundError:
            continue
        if len(d1) >= 200 and len(h4) >= 200:
            ok.append(sym)
        if len(ok) >= N_SYMBOLS:
            break
    return ok


@dataclass(frozen=True)
class _Case:
    name: str
    old_factory: object  # () -> BaseIndicator, "eski" (fixed 3/3, olceksiz) ayarla
    new_name: str  # CATALOG anahtari -- scaled_factory(new_name, tf) "yeni" ayarla
    stable_events: frozenset | None = None  # None = state IN (confirmed, completed)


_CASES: list[_Case] = [
    _Case(
        "patterns.head_shoulders",
        lambda: HeadShouldersIndicator(HeadShouldersParams(zigzag_method="fixed")),
        "patterns.head_shoulders",
    ),
    _Case(
        "patterns.double_top_bottom",
        lambda: DoubleTopBottomIndicator(DoubleTopBottomParams(zigzag_method="fixed")),
        "patterns.double_top_bottom",
    ),
    _Case(
        "patterns.wedge",
        lambda: WedgeIndicator("wedge", WedgeParams(zigzag_method="fixed")),
        "patterns.wedge",
    ),
    _Case(
        "patterns.triangle",
        lambda: WedgeIndicator("triangle", WedgeParams(zigzag_method="fixed")),
        "patterns.triangle",
    ),
    _Case(
        "patterns.broadening",
        lambda: BroadeningIndicator(BroadeningParams(zigzag_method="fixed")),
        "patterns.broadening",
    ),
    _Case(
        "structure.golden_zone",
        lambda: GoldenZoneIndicator(GoldenZoneParams(zigzag_method="fixed")),
        "structure.golden_zone",
    ),
    _Case(
        "structure.price_structure (zone/range)",
        lambda: PriceStructure(PriceStructureParams(zigzag_method="fixed")),
        "structure.price_structure",
        stable_events=_ZONE_EVENTS,
    ),
]


def _count_signals(result, stable_events: frozenset | None) -> int:
    if stable_events is None:
        return sum(1 for s in result.signals if s.state in _STABLE_STATES)
    return sum(1 for s in result.signals if s.payload.get("event") in stable_events)


def _run_before_after(symbols: list[str]) -> list[dict]:
    store = Store(YFinanceProvider())
    rows: list[dict] = []
    for case in _CASES:
        for tf in (Timeframe.H4, Timeframe.D1):
            old_count = 0
            new_count = 0
            old_errors = 0
            new_errors = 0
            for sym in symbols:
                df = store.get(sym, tf, Market.BIST, last_n=LOOKBACK_BARS)
                try:
                    old_result = case.old_factory()(df)
                    old_count += _count_signals(old_result, case.stable_events)
                except Exception:  # noqa: BLE001 -- olcum betigi, tek sembol hatasi durdurmasin
                    old_errors += 1
                try:
                    new_indicator = scaled_factory(case.new_name, tf)
                    new_result = new_indicator(df)
                    new_count += _count_signals(new_result, case.stable_events)
                except Exception:  # noqa: BLE001
                    new_errors += 1
            reduction = (
                100.0 * (old_count - new_count) / old_count if old_count > 0 else float("nan")
            )
            rows.append(
                {
                    "case": case.name, "tf": tf.value,
                    "eski": old_count, "yeni": new_count, "azalma_pct": reduction,
                    "eski_hata": old_errors, "yeni_hata": new_errors,
                }
            )
            azalma_str = f"  azalma=%{reduction:5.1f}" if old_count > 0 else ""
            print(
                f"  {case.name:38s} {tf.value:3s}  eski={old_count:5d}  yeni={new_count:5d}"
                f"{azalma_str}"
            )
    return rows


def _atr_mult_sweep(symbols: list[str]) -> list[dict]:
    store = Store(YFinanceProvider())
    rows: list[dict] = []
    for mult in (2.0, 2.5, 3.0, 3.5):
        leg_bars: list[float] = []
        confirmed_total = 0
        for sym in symbols:
            df = store.get(sym, Timeframe.D1, Market.BIST, last_n=LOOKBACK_BARS)
            zz = significant_pivots(df, method="atr", atr_mult=mult, atr_period=14)
            for a, b in zip(zz, zz[1:], strict=False):
                leg_bars.append(b.bar_idx - a.bar_idx)
            for params_cls, indicator_cls in (
                (DoubleTopBottomParams, DoubleTopBottomIndicator),
                (HeadShouldersParams, HeadShouldersIndicator),
            ):
                params = params_cls(zigzag_method="atr", atr_mult=mult)
                indicator = indicator_cls(params)
                try:
                    result = indicator(df)
                    confirmed_total += _count_signals(result, None)
                except Exception:  # noqa: BLE001
                    pass
        avg_leg = sum(leg_bars) / len(leg_bars) if leg_bars else float("nan")
        rows.append(
            {"atr_mult": mult, "confirmed_toplam": confirmed_total, "ort_bacak_bar": avg_leg}
        )
        print(
            f"  atr_mult={mult:3.1f}  confirmed_toplam={confirmed_total:5d}"
            f"  ort_bacak={avg_leg:6.1f} bar"
        )
    return rows


def _a2_scaling_demo() -> None:
    p = DoubleTopBottomParams()
    print(f"  DoubleTopBottomParams.min_bars_between varsayilan (1D taban): {p.min_bars_between}")
    for tf in (Timeframe.H1, Timeframe.H4, Timeframe.D1, Timeframe.W1):
        scaled = p.for_timeframe(tf)
        print(f"    {tf.value:3s} -> min_bars_between={scaled.min_bars_between}")


def _a3_gate_demo(symbols: list[str]) -> dict:
    """`engine.run()`'ı gerçekten çağırmak `ProcessPoolExecutor`'ın
    Windows'ta her seferinde yeni süreç açma maliyetini (ağır import
    ağacının süreç başına yeniden yüklenmesi) taşır -- bu betikte defalarca
    çağrılan bir "demo" için gereksiz yavaş. Kapının KENDİSİ (bkz.
    `engine.run()`'daki `spec.supported_timeframes` kontrolü) zaten
    `tests/test_scanner/test_supported_timeframes_gate.py`'de gerçek
    `engine.run()` üzerinden doğrulanmış -- burada yalnızca CATALOG'un
    KENDİ verdiği sözleşmeyi (kapının okuduğu TEK kaynak) göstermek
    yeterli."""
    from tlab.indicators.bootstrap import CATALOG

    demo_names = ["momentum.alpha_rank", "momentum.momentum_rank", "trend.weekly_channel"]
    skipped_at_4h = []
    for name in demo_names:
        supported = [t.value for t in CATALOG[name].supported_timeframes]
        skip = "4H" not in supported
        durum = "ATLANIR" if skip else "çalışır"
        print(f"  {name:26s} supported_timeframes={supported}  4H'te {durum}")
        if skip:
            skipped_at_4h.append(name)
    return {"skipped_at_4h": skipped_at_4h}


def _a4_volume_confirm_demo(symbols: list[str]) -> dict:
    store = Store(YFinanceProvider())
    ok = 0
    fail = 0
    for sym in symbols:
        df = store.get(sym, Timeframe.D1, Market.BIST, last_n=LOOKBACK_BARS)
        result = scaled_factory("patterns.double_top_bottom", Timeframe.D1)(df)
        for s in result.signals:
            if s.state == "confirmed":
                if s.payload.get("volume_ok"):
                    ok += 1
                else:
                    fail += 1
    total = ok + fail
    pct = 100.0 * fail / total if total else float("nan")
    print(f"  patterns.double_top_bottom (1D, YENİ ayarlar): {total} confirmed sinyal, "
          f"{fail} tanesi hacim onayindan GECMIYOR (%{pct:.1f}) -- require_volume_confirm=True "
          f"olsaydi bunlar confirmed'a hic terfi etmezdi.")
    return {"confirmed_total": total, "volume_fail": fail, "volume_fail_pct": pct}


def _pick_visual_samples(symbols: list[str], n: int = 10) -> list[dict]:
    store = Store(YFinanceProvider())
    candidates: list[dict] = []
    for case in _CASES[:-1]:  # price_structure ayri sozlesme, cikar
        for tf in (Timeframe.H4, Timeframe.D1):
            for sym in symbols:
                df = store.get(sym, tf, Market.BIST, last_n=LOOKBACK_BARS)
                try:
                    indicator = scaled_factory(case.new_name, tf)
                    result = indicator(df)
                except Exception:  # noqa: BLE001
                    continue
                for s in result.signals:
                    if s.state in _STABLE_STATES:
                        candidates.append(
                            {
                                "symbol": sym, "indicator": case.new_name, "tf": tf.value,
                                "pattern_name": s.payload.get("pattern_name"),
                                "event": s.payload.get("event"),
                                "bar_time": s.bar_time.isoformat(),
                            }
                        )
    random.Random(SEED).shuffle(candidates)
    return candidates[:n]


def main() -> int:
    t0 = time.time()
    print(f"Örneklem: BIST'ten en az {N_SYMBOLS} sembol (D1+H4 önbellekli, >=200 bar)...")
    symbols = _sample_universe()
    print(f"  {len(symbols)} sembol bulundu.\n")

    print("=== A1 -- önce/sonra sinyal sayısı (7 gösterge x 2 tf) ===")
    before_after = _run_before_after(symbols)

    print("\n=== A1 -- atr_mult taraması (1D, double_top_bottom+head_shoulders) ===")
    sweep = _atr_mult_sweep(symbols)

    print("\n=== A2 -- zaman dilimi ölçekleme demosu ===")
    _a2_scaling_demo()

    print("\n=== A3 -- supported_timeframes kapısı demosu ===")
    a3 = _a3_gate_demo(symbols)

    print("\n=== A4 -- hacim onayı demosu ===")
    a4 = _a4_volume_confirm_demo(symbols)

    print("\n=== Görsel inceleme için 10 rastgele örnek seçiliyor ===")
    samples = _pick_visual_samples(symbols, n=10)
    for s in samples:
        print(f"  {s['symbol']:10s} {s['indicator']:28s} {s['tf']:3s} {s['event']}")

    out = {
        "n_symbols": len(symbols), "symbols": symbols,
        "before_after": before_after, "atr_mult_sweep": sweep,
        "a3_gate": a3, "a4_volume_confirm": a4, "visual_samples": samples,
    }
    out_path = Path("outputs/reports/sistemik_denetim_v1.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    print(f"\nJSON çıktı: {out_path} ({time.time() - t0:.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
