"""Momentum Confluence + Harmonik XABCD -- REJIM KOSULLU ablasyon backtesti.

Kullanici istegi (2026-08-19): "baska kosullar altinda backtestler yapar
misin -- hem momentum confluence hem de formasyon indikatorleri icin en iyi
seyleri bulmak istiyorum". Onceki ablasyonlar (`momentum_confluence_
optimizasyon.py`, `harmonic_confirmation_optimizasyon.py`) SADECE sinyal-ici
kosullari (hacim/RSI/MACD/mum vb.) degistirdi -- bu script FARKLI bir eksen
dener: PIYASA REJIMI (trend/yatay, yuksek/dusuk oynaklik). Ayni sinyal
kumesi, sinyal barindaki rejime gore GRUPLANIR -- "bu sistem HANGI piyasa
kosulunda en iyi calisiyor" sorusuna cevap.

Rejim tanimlari (SABIT esikler, veriden turetilmedi -- literatur-standart):
  - Trend/Yatay: ADX14 (Wilder) >= 25 ise TREND, < 25 ise YATAY (Wilder'in
    kendi klasik esigi, `abcd_factor_analysis._adx_wilder` REUSE edilir).
  - Oynaklik: ATR14/close oraninin son 252 barlik (yaklasik 1 yil) yuzdelik
    sirasi >= 0.5 ise YUKSEK, < 0.5 ise DUSUK (sembolun KENDI GECMISINE
    GORE goreli oynaklik -- mutlak ATR duzeyi sembol/fiyat olcegine gore
    anlamsiz olurdu).
  - Hurst rejimi (2026-08-19, dis kaynak taramasi -- `Desktop/Strateji
    kaynaklari/gecikme_direncli_stratejiler.md` "Hurst Regime Switcher"
    stratejisinden UYARLANDI): son 100 barin log-getirisi uzerinden
    basitlestirilmis R/S (rescaled range) Hurst tahmini H. H>=0.55 ->
    TRENDING_H (momentum/devamlilik rejimi), H<=0.45 -> MEAN_REV_H
    (ortalamaya-donus rejimi), arasi -> NOTR_H. BU, ADX'ten FARKLI bir
    matematiksel olcu (fraktal kendine-benzerlik, yon/egim DEGIL) --
    literatur, harmonik/mean-reversion sistemlerin H<0.5 rejiminde, trend-
    takip sistemlerin H>0.5 rejiminde daha iyi calismasi GEREKTIGINI iddia
    eder (bu script bu iddiayi BIST verisiyle SINAR, varsaymaz).
  - Gap bolgesi (2026-08-19, dis kaynak taramasi -- `Desktop/Strateji
    kaynaklari/PHASE7_2_STRATEGY_UPDATE_REPORT.md` "Gap-Ratio Giris
    Filtresi", BIST'e ozel kalibre edilmis): `gap_ratio = |fill_ref -
    entry_ref| / ATR14[signal_bar]` (fill_ref=sinyal SONRASI bardaki open,
    entry_ref=sinyal barindaki close -- HER IKI alan da Signal/PrzEvent'te
    zaten mevcut, YENIDEN hesaplanmadi). Bolge A (<=0.5 ATR)=normal acilis,
    B (0.5-2.0 ATR)=sicrama, C (>2.0 ATR)=asiri sicrama (kaynak rapor bu
    barlarda R:R'nin acilista zaten bozuldugunu, sinyalin IPTAL edilmesi
    gerektigini iddia eder -- bu script de SINAR).

Basitlestirilmis R/S Hurst tahmini SAF matematik yaklasiklamadir (DFA gibi
rigorous bir estimator DEGIL, `abcd_factor_analysis._adx_wilder`nin
"Pine-parity ZORUNLU DEGIL, kaba/standart yaklasim" gerekcesiyle AYNI
disiplin) -- rejim ETIKETLEME icin yeterli, kesin H DEGERI ICIN degil.

Mimari: sinyal uretimi (`momentum_confluence_variants.detect_variant` /
`harmonic_xabcd.detect_prz`) VE backtest (`abcd_backtest.backtest_symbol`/
`compute_metrics`) HICBIR SEKILDE degistirilmedi -- SADECE sinyal listesi
uretildikten SONRA, sinyal barindaki rejime gore post-hoc GRUPLANIR (
`harmonic_xabcd_prz_filter_backtest.py` ile AYNI "once uret, sonra filtrele/
grupla" deseni).

Kapsam (zaman/network butcesi icin BILINCLI daraltma): SADECE tf=1D (onceki
raporlarda tutarli sekilde 240'tan daha guclu bulundu, bkz. docs/spec/
HARMONIC_CONFIRMATION_OPTIMIZASYON.md ve MOMENTUM_CONFLUENCE_OPTIMIZASYON.md
"Bulgular"). Momentum: `momentum_confluence_variants.VARIANTS`in TAMAMI (18).
Harmonik: 5 formasyon x 2 yon.

Kullanim:
    python scripts/rejim_kosullu_backtest.py --limit-symbols 30  # pilot
    python scripts/rejim_kosullu_backtest.py                     # TAM BIST
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402
from src.analysis import harmonic_xabcd, momentum_confluence_variants as mcv  # noqa: E402
from src.analysis.abcd_backtest import BacktestParams, backtest_symbol, compute_metrics  # noqa: E402
from src.analysis.abcd_factor_analysis import _adx_wilder  # noqa: E402
from src.analysis.abcd_pattern import atr_wilder  # noqa: E402
from src.analysis.abcd_scanner import get_bist_universe  # noqa: E402
from src.analysis.harmonic_xabcd import ABCD_PRESET, HARMONIC_XABCD_PRESETS  # noqa: E402
from src.analysis.momentum_confluence import Params as McParams  # noqa: E402
from src.fetchers.abcd_data import fetch_ohlcv_abcd  # noqa: E402

config.setup_logging()

_DEFAULT_OUT_MD = BASE_DIR / "docs" / "spec" / "REJIM_KOSULLU_BACKTEST.md"
_DEFAULT_OUT_CSV = config.DATA_DIR / "abcd_cache" / "rejim_kosullu_events.csv"
_TF = "1D"
_N_BARS = 1000
_ADX_LEN = 14
_ADX_TREND_TH = 25.0
_ATR_LEN = 14
_ATR_PCTRANK_WINDOW = 252
_MIN_TRADES_TRUSTWORTHY = 100
_MIN_TRADES_SHOW = 10
_ALL_HARMONIC_FORMATIONS = {"ABCD": ABCD_PRESET, **HARMONIC_XABCD_PRESETS}


def _atr_pct_rank(df: pd.DataFrame, window: int = _ATR_PCTRANK_WINDOW) -> np.ndarray:
    """ATR14/close oraninin son `window` bar icindeki yuzdelik sirasi
    (0..1) -- rolling percentile rank, look-ahead YOK (`rolling().rank()`
    her noktada SADECE o noktaya KADAR olan pencereyi kullanir)."""
    close = df["close"].to_numpy(dtype=float)
    atr = atr_wilder(df, _ATR_LEN)
    with np.errstate(divide="ignore", invalid="ignore"):
        atr_ratio = np.where(close > 0, atr / close, np.nan)
    s = pd.Series(atr_ratio)
    rank = s.rolling(window, min_periods=window // 2).rank(pct=True)
    return rank.to_numpy(dtype=float)


_HURST_WINDOW = 100
_HURST_TREND_TH = 0.55
_HURST_MR_TH = 0.45


def _hurst_rs(log_returns: np.ndarray) -> float:
    """Basitlestirilmis R/S (rescaled range) Hurst tahmini -- bkz. modul ust
    notu. `log_returns` NaN icermemeli (cagiran taraf `dropna` yapar)."""
    n = len(log_returns)
    if n < 20:
        return float("nan")
    candidate_lags = [10, 20, 25, 50]
    lags = [l for l in candidate_lags if l < n]
    if len(lags) < 2:
        return float("nan")
    points: list[tuple[float, float]] = []
    for lag in lags:
        n_chunks = n // lag
        if n_chunks < 1:
            continue
        rs_chunk = []
        for i in range(n_chunks):
            chunk = log_returns[i * lag : (i + 1) * lag]
            dev = np.cumsum(chunk - chunk.mean())
            r = dev.max() - dev.min()
            s = chunk.std(ddof=0)
            if s > 0:
                rs_chunk.append(r / s)
        if rs_chunk:
            points.append((lag, float(np.mean(rs_chunk))))
    if len(points) < 2:
        return float("nan")
    log_lags = np.log([p[0] for p in points])
    log_rs = np.log([p[1] for p in points])
    slope = float(np.polyfit(log_lags, log_rs, 1)[0])
    return slope


def _hurst_series(df: pd.DataFrame, window: int = _HURST_WINDOW) -> np.ndarray:
    close = df["close"].to_numpy(dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        log_ret = np.diff(np.log(close), prepend=np.nan)
    n = len(log_ret)
    out = np.full(n, np.nan)
    for i in range(window, n):
        window_ret = log_ret[i - window : i]
        if np.any(np.isnan(window_ret)):
            continue
        out[i] = _hurst_rs(window_ret)
    return out


def _regime_tags(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    adx = _adx_wilder(df, _ADX_LEN)
    atr_rank = _atr_pct_rank(df)
    hurst = _hurst_series(df)
    trend_tag = np.where(np.isnan(adx), None, np.where(adx >= _ADX_TREND_TH, "TREND", "YATAY"))
    vol_tag = np.where(np.isnan(atr_rank), None, np.where(atr_rank >= 0.5, "YUKSEK_VOL", "DUSUK_VOL"))
    hurst_tag = np.where(
        np.isnan(hurst), None,
        np.where(hurst >= _HURST_TREND_TH, "TRENDING_H", np.where(hurst <= _HURST_MR_TH, "MEAN_REV_H", "NOTR_H")),
    )
    return trend_tag, vol_tag, hurst_tag


_GAP_ZONE_B = 0.5
_GAP_ZONE_C = 2.0


def _gap_zone(event, atr_at_signal: float) -> str | None:
    if atr_at_signal is None or not np.isfinite(atr_at_signal) or atr_at_signal <= 0:
        return None
    entry_ref = getattr(event, "entry_ref", None)
    fill_ref = getattr(event, "fill_ref", None)
    if entry_ref is None or fill_ref is None or not np.isfinite(fill_ref):
        return None
    gap_ratio = abs(fill_ref - entry_ref) / atr_at_signal
    if gap_ratio <= _GAP_ZONE_B:
        return "A_NORMAL"
    if gap_ratio <= _GAP_ZONE_C:
        return "B_SICRAMA"
    return "C_ASIRI"


def collect(symbols: list[str]) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    rows: list[dict] = []
    ohlcv_cache: dict[str, pd.DataFrame] = {}
    total = len(symbols)
    for done, symbol in enumerate(symbols, start=1):
        if done % 50 == 0:
            print(f"  ... {done}/{total} sembol islendi, su ana kadar {len(rows)} sinyal")
        df = fetch_ohlcv_abcd(symbol, _TF, _N_BARS)
        if df.empty or len(df) < _ATR_PCTRANK_WINDOW:
            continue
        ohlcv_cache[symbol] = df
        trend_tag, vol_tag, hurst_tag = _regime_tags(df)
        atr14 = atr_wilder(df, _ATR_LEN)

        for variant_name, flags in mcv.VARIANTS.items():
            signals = mcv.detect_variant(df, McParams(), flags)
            for sig in signals:
                b = sig.signal_bar
                if b < 0 or b >= len(df) or trend_tag[b] is None or vol_tag[b] is None:
                    continue
                rows.append(
                    {
                        "sistem": "MOMENTUM",
                        "varyant": variant_name,
                        "yon": "LONG",
                        "symbol": symbol,
                        "trend": trend_tag[b],
                        "vol": vol_tag[b],
                        "hurst": hurst_tag[b],
                        "gap_zone": _gap_zone(sig, atr14[b] if b < len(atr14) else float("nan")),
                        "_event": sig,
                    }
                )

        for formation_name, base_params in _ALL_HARMONIC_FORMATIONS.items():
            for direction in ("LONG", "SHORT"):
                dp = replace(base_params, enable_long=direction == "LONG", enable_short=direction == "SHORT")
                events = harmonic_xabcd.detect_prz(df, dp)
                for ev in events:
                    b = ev.d_bar
                    if b < 0 or b >= len(df) or trend_tag[b] is None or vol_tag[b] is None:
                        continue
                    rows.append(
                        {
                            "sistem": "HARMONIK",
                            "varyant": formation_name,
                            "yon": direction,
                            "symbol": symbol,
                            "trend": trend_tag[b],
                            "vol": vol_tag[b],
                            "hurst": hurst_tag[b],
                            "gap_zone": _gap_zone(ev, atr14[b] if b < len(atr14) else float("nan")),
                            "_event": ev,
                        }
                    )
    return pd.DataFrame(rows), ohlcv_cache


def _cell_stats(trades: list) -> dict:
    n = len(trades)
    if n == 0:
        return {"n": 0, "win_rate": float("nan"), "profit_factor": float("nan"), "expectancy_r": float("nan")}
    r_values = [t.r_multiple for t in trades if not math.isnan(t.r_multiple)]
    wins = [t for t in trades if t.pnl > 0]
    losses = [t for t in trades if t.pnl <= 0]
    gross_profit = sum(t.pnl for t in wins)
    gross_loss = -sum(t.pnl for t in losses)
    return {
        "n": n,
        "win_rate": len(wins) / n * 100.0,
        "profit_factor": (gross_profit / gross_loss) if gross_loss > 0 else float("inf") if gross_profit > 0 else float("nan"),
        "expectancy_r": (sum(r_values) / len(r_values)) if r_values else float("nan"),
    }


def _run_bt(sub_df: pd.DataFrame, ohlcv_cache: dict[str, pd.DataFrame]) -> dict:
    bt_params = BacktestParams()
    all_trades: list = []
    for symbol, grp in sub_df.groupby("symbol"):
        df = ohlcv_cache.get(symbol)
        if df is None:
            continue
        trades, _ = backtest_symbol(df, symbol, list(grp["_event"]), bt_params)
        all_trades.extend(trades)
    return _cell_stats(all_trades)


def _fmt(value, fmt: str = "{:.2f}") -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    if isinstance(value, float) and math.isinf(value):
        return "sonsuz" if value > 0 else "-sonsuz"
    return fmt.format(value)


def _guven(n: int) -> str:
    if n < _MIN_TRADES_SHOW:
        return "cok kucuk"
    if n < _MIN_TRADES_TRUSTWORTHY:
        return "kucuk"
    return "guvenilir"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit-symbols", type=int, default=None)
    parser.add_argument("--out", default=str(_DEFAULT_OUT_MD))
    parser.add_argument("--out-csv", default=str(_DEFAULT_OUT_CSV))
    args = parser.parse_args(argv)

    symbols = get_bist_universe()
    if args.limit_symbols is not None:
        symbols = symbols[: args.limit_symbols]
    print(f"{len(symbols)} sembol, tf={_TF}, rejim etiketleri hesaplaniyor...")

    events_df, ohlcv_cache = collect(symbols)
    print(f"Toplam {len(events_df)} rejim-etiketli sinyal toplandi.")

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    events_df.drop(columns=["_event"]).to_csv(out_csv, index=False)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Rejim Kosullu Backtest -- Momentum Confluence + Harmonik XABCD\n",
        f"\nOlusturulma: {now}\n",
        f"\n## Kapsam\n",
        f"\nSembol: {len(symbols)} · TF: {_TF} · Toplam etiketli sinyal: {len(events_df)} · "
        f"Rejim esikleri: ADX14>={_ADX_TREND_TH:.0f}=TREND, ATR/close 252-gunluk yuzdelik>=%50=YUKSEK_VOL\n",
        "\n## Trend vs Yatay -- ozet (tum varyant/formasyonlar TOPLANMIS)\n",
        "\n| Sistem | Rejim | n | Win % | PF | Beklenti (R) | Guven |\n|---|---|---|---|---|---|---|\n",
    ]
    for sistem in ("MOMENTUM", "HARMONIK"):
        for trend in ("TREND", "YATAY"):
            sub = events_df[(events_df["sistem"] == sistem) & (events_df["trend"] == trend)]
            stats = _run_bt(sub, ohlcv_cache)
            lines.append(
                f"| {sistem} | {trend} | {stats['n']} | {_fmt(stats['win_rate'])} | {_fmt(stats['profit_factor'])} | "
                f"{_fmt(stats['expectancy_r'], '{:.3f}')} | {_guven(stats['n'])} |\n"
            )

    lines.append("\n## Yuksek vs Dusuk Oynaklik -- ozet (tum varyant/formasyonlar TOPLANMIS)\n")
    lines.append("\n| Sistem | Rejim | n | Win % | PF | Beklenti (R) | Guven |\n|---|---|---|---|---|---|---|\n")
    for sistem in ("MOMENTUM", "HARMONIK"):
        for vol in ("YUKSEK_VOL", "DUSUK_VOL"):
            sub = events_df[(events_df["sistem"] == sistem) & (events_df["vol"] == vol)]
            stats = _run_bt(sub, ohlcv_cache)
            lines.append(
                f"| {sistem} | {vol} | {stats['n']} | {_fmt(stats['win_rate'])} | {_fmt(stats['profit_factor'])} | "
                f"{_fmt(stats['expectancy_r'], '{:.3f}')} | {_guven(stats['n'])} |\n"
            )

    lines.append("\n## Hurst Rejimi -- ozet (Strateji kaynakları/gecikme_direncli_stratejiler.md'den uyarlandi)\n")
    lines.append("\n| Sistem | Rejim | n | Win % | PF | Beklenti (R) | Guven |\n|---|---|---|---|---|---|---|\n")
    for sistem in ("MOMENTUM", "HARMONIK"):
        for hurst_reg in ("TRENDING_H", "MEAN_REV_H", "NOTR_H"):
            sub = events_df[(events_df["sistem"] == sistem) & (events_df["hurst"] == hurst_reg)]
            stats = _run_bt(sub, ohlcv_cache)
            lines.append(
                f"| {sistem} | {hurst_reg} | {stats['n']} | {_fmt(stats['win_rate'])} | {_fmt(stats['profit_factor'])} | "
                f"{_fmt(stats['expectancy_r'], '{:.3f}')} | {_guven(stats['n'])} |\n"
            )

    lines.append("\n## Gap Bolgesi -- ozet (PHASE7_2_STRATEGY_UPDATE_REPORT.md'den uyarlandi, BIST kalibrasyonu)\n")
    lines.append("\nA=acilis gap'i <=0.5xATR (normal) · B=0.5-2.0xATR (sicrama) · C=>2.0xATR (asiri, kaynak rapor iptal onerir)\n")
    lines.append("\n| Sistem | Bolge | n | Win % | PF | Beklenti (R) | Guven |\n|---|---|---|---|---|---|---|\n")
    for sistem in ("MOMENTUM", "HARMONIK"):
        for gap_reg in ("A_NORMAL", "B_SICRAMA", "C_ASIRI"):
            sub = events_df[(events_df["sistem"] == sistem) & (events_df["gap_zone"] == gap_reg)]
            stats = _run_bt(sub, ohlcv_cache)
            lines.append(
                f"| {sistem} | {gap_reg} | {stats['n']} | {_fmt(stats['win_rate'])} | {_fmt(stats['profit_factor'])} | "
                f"{_fmt(stats['expectancy_r'], '{:.3f}')} | {_guven(stats['n'])} |\n"
            )

    lines.append("\n## Detay -- her varyant/formasyon x tam rejim (trend x vol, 4 kova)\n")
    lines.append("\n| Sistem | Varyant/Formasyon | Yon | Rejim | n | Win % | PF | Guven |\n|---|---|---|---|---|---|---|---|\n")
    best_per_variant: list[tuple] = []
    for (sistem, varyant, yon), grp in events_df.groupby(["sistem", "varyant", "yon"]):
        variant_best = []
        for trend in ("TREND", "YATAY"):
            for vol in ("YUKSEK_VOL", "DUSUK_VOL"):
                sub = grp[(grp["trend"] == trend) & (grp["vol"] == vol)]
                stats = _run_bt(sub, ohlcv_cache)
                rejim = f"{trend}+{vol}"
                lines.append(
                    f"| {sistem} | {varyant} | {yon} | {rejim} | {stats['n']} | {_fmt(stats['win_rate'])} | "
                    f"{_fmt(stats['profit_factor'])} | {_guven(stats['n'])} |\n"
                )
                if stats["n"] >= _MIN_TRADES_SHOW and not math.isnan(stats["profit_factor"]):
                    variant_best.append((rejim, stats["profit_factor"], stats["n"]))
        if variant_best:
            best_rejim, best_pf, best_n = max(variant_best, key=lambda x: x[1])
            best_per_variant.append((sistem, varyant, yon, best_rejim, best_pf, best_n))

    lines.append("\n## Ozet -- her varyant/formasyon icin EN IYI rejim (n>=10 hucreler arasindan)\n")
    lines.append("\n| Sistem | Varyant/Formasyon | Yon | En iyi rejim | PF | n |\n|---|---|---|---|---|---|\n")
    best_per_variant.sort(key=lambda r: r[4], reverse=True)
    for sistem, varyant, yon, rejim, pf, n in best_per_variant:
        lines.append(f"| {sistem} | {varyant} | {yon} | {rejim} | {pf:.2f} | {n} |\n")

    lines.append("\n## Ham Veri\n")
    lines.append(f"\nSinyal basina rejim etiketleri: `{out_csv}`\n")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"Rapor kaydedildi: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
