"""Faz 1, 1D -- DOGRULAMA (bu fazin en onemli parcasi, bkz.
docs/TANI_VE_YOL_HARITASI_v2.md "--- 1D: DOGRULAMA ---").

double_top_bottom.py + head_shoulders.py'nin YENI literatur filtrelerinin
(min_bars_between, prior_trend, min_depth, eq_tol, min_rise_between_pct,
shoulder_time_ratio) ONCESI/SONRASI olcumu + ELENME SEBEBI dagilimi + wedge/
triangle/broadening'in (BULUNAN HATA 3 kapanisi) opsiyonel max_bars knob'u
icin bir span-dagilimi taramasi.

Gercek BIST onbellek verisiyle calisir (network YOK -- data/ohlcv/bist/ zaten
indirilmis, Store.get() yalnizca parquet okur).

Cikti: konsola tablo + outputs/reports/formasyon_denetim_v2.json (bu betik
yazar) + docs/spec/FORMASYON_DENETIM_v2.md (AYRI, elle/bir sonraki adimda
yazilir -- gorsel inceleme adimi Read tool'u gerektirdigi icin bu betigin
disinda kalir)."""

from __future__ import annotations

import json
import random
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from tlab.core.types import Market, Timeframe  # noqa: E402
from tlab.data.providers.yfinance_provider import YFinanceProvider  # noqa: E402
from tlab.data.store import Store  # noqa: E402
from tlab.data.universe import load_universe  # noqa: E402
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

N_SYMBOLS = 120
LOOKBACK_BARS = 600
SEED = 11
_STABLE_STATES = frozenset({"confirmed", "completed"})
_TFS = (Timeframe.D1, Timeframe.H4)


def _sample_universe() -> list[str]:
    """`scripts/sistemik_denetim.py::_sample_universe` ile AYNI (>=120
    sembol, D1+H4 onbellekte >=200 bar) -- gorev metni "en az 100" diyor,
    onceki Faz 0.5 olcumuyle TUTARLI kalmak icin 120 kullanildi."""
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


# --- ESKI (Faz 1 ONCESI) parametre yeniden-insasi ---------------------------
#
# double_top_bottom: eq_tol/min_bars_between'in ESKI degerleri geri
# yuklendi; prior_trend/min_depth Faz 1'den ONCE HIC YOKTU -- en yakin
# "yok" yaklasimi: prior_trend_min_tstat=0.0 (anlamlilik sarti kalkar, YON
# sarti -- long icin egim<0 -- yapisal olarak KALIR, bu YAKLASIK bir alt
# sinir, tam "filtre yok" DEGIL, bkz. rapordaki not) + min_depth_pct/atr=0.0
# (TAM devre disi -- bunlar salt esitsizlik, 0.0 hicbir seyi elemez).
#
# head_shoulders: neck_total_slope_max Faz 1 ONCESI'nin (eski, bar-basina
# YANLIS normalize) davranisina en yakin yaklasim -- kendi docstring'i "fiilen
# hicbir seyi elemiyordu" diyor, bu yuzden neck_total_slope_max=1.0 (fiilen
# sinirsiz) o eski "no-op" davranisi dogru temsil ediyor (eski FORMULU
# birebir yeniden kurmak MUMKUN DEGIL -- kod artik silindi/deprecated).


def _old_dtb_params(tf: Timeframe) -> DoubleTopBottomParams:
    return DoubleTopBottomParams(
        eq_tol=0.02, min_bars_between=5, max_bars_between=0, min_rise_between_pct=0.0,
        prior_trend_min_tstat=0.0, min_depth_pct=0.0, min_depth_atr=0.0,
    ).for_timeframe(tf)


def _old_hs_params(tf: Timeframe) -> HeadShouldersParams:
    return HeadShouldersParams(
        neck_total_slope_max=1.0, prior_trend_min_tstat=0.0, min_depth_pct=0.0, min_depth_atr=0.0,
    ).for_timeframe(tf)


@dataclass(frozen=True)
class _Case:
    name: str
    old_factory: object  # (tf) -> Params, ESKI ayarlar
    new_name: str  # CATALOG anahtari -- scaled_factory(new_name, tf) YENI ayarlar
    indicator_cls: object  # Params -> BaseIndicator, ESKI taraf icin


_CASES: list[_Case] = [
    _Case("patterns.double_top_bottom", _old_dtb_params,
          "patterns.double_top_bottom", DoubleTopBottomIndicator),
    _Case("patterns.head_shoulders", _old_hs_params,
          "patterns.head_shoulders", HeadShouldersIndicator),
]


def _category_counts(signals) -> Counter:
    c: Counter = Counter()
    for s in signals:
        if s.state in _STABLE_STATES:
            name = s.payload.get("pattern_name", "?")
            c[name] += 1
    return c


def _run_before_after(symbols: list[str]) -> tuple[list[dict], dict]:
    """1-2-3: ESKI/YENI toplam + kategori kirilimi + (YENI parametrelerle)
    elenme sebebi dagilimi -- AYNI dongude, iki kez taramamak icin."""
    store = Store(YFinanceProvider())
    rows: list[dict] = []
    elim_by_case_tf: dict[str, Counter] = {}
    for case in _CASES:
        for tf in _TFS:
            old_cat: Counter = Counter()
            new_cat: Counter = Counter()
            elim: Counter = Counter()
            old_errors = 0
            new_errors = 0
            for sym in symbols:
                df = store.get(sym, tf, Market.BIST, last_n=LOOKBACK_BARS)
                try:
                    old_result = case.indicator_cls(case.old_factory(tf)).compute(df)
                    old_cat.update(_category_counts(old_result.signals))
                except Exception:  # noqa: BLE001 -- olcum betigi, tek sembol hatasi durdurmasin
                    old_errors += 1
                try:
                    new_indicator = scaled_factory(case.new_name, tf)
                    new_result = new_indicator.compute(df, context={"elim": elim})
                    new_cat.update(_category_counts(new_result.signals))
                except Exception:  # noqa: BLE001
                    new_errors += 1
            old_total = sum(old_cat.values())
            new_total = sum(new_cat.values())
            reduction = (
                100.0 * (old_total - new_total) / old_total if old_total > 0 else float("nan")
            )
            rows.append(
                {
                    "case": case.name, "tf": tf.value,
                    "eski_toplam": old_total, "yeni_toplam": new_total,
                    "azalma_pct": reduction,
                    "eski_kategori": dict(old_cat), "yeni_kategori": dict(new_cat),
                    "elenme_sebebi": dict(elim),
                    "eski_hata": old_errors, "yeni_hata": new_errors,
                }
            )
            elim_by_case_tf[f"{case.name}_{tf.value}"] = elim
            azalma_str = f"  azalma=%{reduction:5.1f}" if old_total > 0 else ""
            print(
                f"  {case.name:28s} {tf.value:3s}  eski={old_total:4d}  yeni={new_total:4d}"
                f"{azalma_str}  elenme={dict(elim)}"
            )
    return rows, elim_by_case_tf


def _wedge_span_sweep(symbols: list[str]) -> list[dict]:
    """BULUNAN HATA 3 (wedge/triangle/broadening) icin: max_bars=0
    (sinirsiz, mevcut varsayilan) ile, GERCEKTE confirmed'a ulasan
    adaylarin P1-P2 mesafesi (span) nasil dagiliyor -- gercek bir varsayilan
    esik gerekip gerekmedigine bu karar verir. Yontem: farkli max_bars
    esikleriyle YENIDEN tarayip her esikte kac sinyalin HALA gectigini
    say (esik ne kadar dusukse o kadar cok sinyal ELENIR -- azalma egrisi
    "makul" bir esigi isaret eder)."""
    store = Store(YFinanceProvider())
    thresholds = (60, 90, 120, 180, 250, 0)
    rows: list[dict] = []
    for max_bars in thresholds:
        total = 0
        for sym in symbols:
            df = store.get(sym, Timeframe.D1, Market.BIST, last_n=LOOKBACK_BARS)
            for indicator in (
                WedgeIndicator("wedge", WedgeParams(max_bars=max_bars)),
                WedgeIndicator("triangle", WedgeParams(max_bars=max_bars)),
                BroadeningIndicator(BroadeningParams(max_bars=max_bars)),
            ):
                try:
                    result = indicator(df)
                    total += sum(1 for s in result.signals if s.state in _STABLE_STATES)
                except Exception:  # noqa: BLE001
                    pass
        rows.append({"max_bars": max_bars, "confirmed_toplam": total})
        label = "sinirsiz" if max_bars == 0 else str(max_bars)
        print(f"  max_bars={label:>8s}  confirmed_toplam(wedge+triangle+broadening, 1D)={total}")
    return rows


def _pick_visual_samples(symbols: list[str], n: int = 10) -> list[dict]:
    """YENI (mevcut/production) parametrelerle confirmed/completed
    sinyaller arasindan n tanesini rastgele secer -- `tlab plot`'un
    varsayilan pencerelemesinin (BULUNAN HATA 2, Faz 1 kapsami DISINDA)
    sinyali gorunmez kilmasini ONLEMEK icin, sinyalin dogum barinin
    df'in SON 200 barinin icinde olmasiyla SINIRLANIR (bilinclı secim
    kisiti, docs/spec/FORMASYON_DENETIM_v2.md'de belgelenir)."""
    store = Store(YFinanceProvider())
    candidates: list[dict] = []
    indicator_names = [
        "patterns.double_top_bottom", "patterns.head_shoulders",
        "patterns.wedge", "patterns.triangle", "patterns.broadening",
    ]
    for name in indicator_names:
        for tf in _TFS:
            for sym in symbols:
                df = store.get(sym, tf, Market.BIST, last_n=LOOKBACK_BARS)
                try:
                    result = scaled_factory(name, tf)(df)
                except Exception:  # noqa: BLE001
                    continue
                n_bars = len(df)
                for s in result.signals:
                    if s.state not in _STABLE_STATES:
                        continue
                    bar_pos = df.index.get_loc(s.bar_time)
                    if n_bars - bar_pos > 200:
                        continue
                    candidates.append(
                        {
                            "symbol": sym, "indicator": name, "tf": tf.value,
                            "pattern_name": s.payload.get("pattern_name"),
                            "event": s.payload.get("event"), "state": s.state,
                            "bar_time": s.bar_time.isoformat(),
                        }
                    )
    random.Random(SEED).shuffle(candidates)
    return candidates[:n]


def _render_samples(samples: list[dict]) -> None:
    from tlab.viz.live import render_live

    out_dir = Path("outputs/samples/formasyon_denetim_v2")
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, s in enumerate(samples):
        fig = render_live(
            s["indicator"], s["symbol"], s["tf"], "bist", last_n=0, declutter=True,
        )
        out_path = out_dir / f"{i:02d}_{s['symbol']}_{s['indicator']}_{s['tf']}.png"
        fig.write_image(str(out_path), width=1600, height=900, scale=1.5)
        s["png"] = str(out_path)
        print(f"  [{i}] {out_path}")


def main() -> int:
    t0 = time.time()
    print(f"Örneklem: BIST'ten en az {N_SYMBOLS} sembol (D1+H4 önbellekli, >=200 bar)...")
    symbols = _sample_universe()
    print(f"  {len(symbols)} sembol bulundu.\n")

    print("=== 1-2-3: önce/sonra + kategori kırılımı + elenme sebebi dağılımı ===")
    before_after, _elim = _run_before_after(symbols)

    print("\n=== BULUNAN HATA 3 -- wedge/triangle/broadening span/max_bars taraması ===")
    span_sweep = _wedge_span_sweep(symbols)

    print("\n=== 4: Görsel inceleme için 10 rastgele örnek seçiliyor (son 200 bar içi) ===")
    samples = _pick_visual_samples(symbols, n=10)
    for s in samples:
        print(f"  {s['symbol']:10s} {s['indicator']:28s} {s['tf']:3s} {s['event']}")

    print("\n=== PNG'ler render ediliyor ===")
    _render_samples(samples)

    out = {
        "n_symbols": len(symbols), "symbols": symbols,
        "before_after": before_after, "span_sweep": span_sweep, "visual_samples": samples,
    }
    out_path = Path("outputs/reports/formasyon_denetim_v2.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    print(f"\nJSON çıktı: {out_path} ({time.time() - t0:.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
