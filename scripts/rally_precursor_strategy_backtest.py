"""Buyuk Yukselis Onculu Stratejisi -- tam BIST backtest + "capture rate"
olcumu (kullanicinin asil sikayeti: "buyuk yukselisleri KACIRIYORUZ" --
bu script SADECE PF/WR DEGIL, GERCEK buyuk yukselislerin KACINI
YAKALADIGIMIZI da olcer).

Mimari: `rally_precursor_strategy.detect()` (4 skor esigi: min_score=1..4,
en dusuk sinyal seti bir kez uretilir, digerleri FILTRELENIR -- tekrar
tespit YAPILMAZ) + `abcd_backtest.backtest_symbol` (PF/WR/n) + `rally_
precursor.find_rally_candidates` (AYNI %50/120-bar tanimla GERCEK buyuk
yukselisleri bulur, capture-rate PAYDASI).

Capture rate: `rally_precursor_strategy`nin pivot_lookback'i `rally_
precursor.find_rally_candidates`inkiyle AYNI (varsayilan 10) oldugu icin
IKISI de AYNI low_bar'lari pivot olarak tanir -- bir GERCEK buyuk-yukselis
dip'inin (label=1) low_bar'inda strateji ARTIK skor esigini GECIP sinyal
URETTI Mi sorusu DOGRUDAN karsilastirilabilir.

Kullanim:
    python scripts/rally_precursor_strategy_backtest.py --limit-symbols 30  # pilot
    python scripts/rally_precursor_strategy_backtest.py                     # TAM BIST
"""

from __future__ import annotations

import argparse
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import pandas as pd  # noqa: E402

import config  # noqa: E402
from src.analysis import rally_precursor as rp  # noqa: E402
from src.analysis import rally_precursor_strategy as rps  # noqa: E402
from src.analysis.abcd_backtest import BacktestParams, backtest_symbol, compute_metrics  # noqa: E402
from src.analysis.abcd_scanner import get_bist_universe  # noqa: E402
from src.fetchers.abcd_data import fetch_ohlcv_abcd  # noqa: E402

config.setup_logging()

_DEFAULT_OUT_MD = BASE_DIR / "docs" / "spec" / "RALLY_PRECURSOR_STRATEJI_BACKTEST.md"
_N_BARS = 2000
_RALLY_THRESHOLD = 50.0
_MAX_LOOKAHEAD_BARS = 120
_MIN_TRADES_SHOW = 20
_MIN_TRADES_TRUSTWORTHY = 50
_SCORE_LEVELS = (1, 2, 3, 4)


def _fmt(value, spec: str = "{:.2f}") -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    if isinstance(value, float) and math.isinf(value):
        return "sonsuz" if value > 0 else "-sonsuz"
    return spec.format(value)


def _guven(n: int) -> str:
    if n < _MIN_TRADES_SHOW:
        return "cok kucuk"
    if n < _MIN_TRADES_TRUSTWORTHY:
        return "kucuk"
    return "guvenilir (n>=50)"


def _cell_stats(trades: list) -> dict:
    n = len(trades)
    if n == 0:
        return {"n": 0, "win_rate": float("nan"), "profit_factor": float("nan"), "expectancy_r": float("nan")}
    wins = [t for t in trades if t.pnl > 0]
    losses = [t for t in trades if t.pnl <= 0]
    gross_profit = sum(t.pnl for t in wins)
    gross_loss = -sum(t.pnl for t in losses)
    r_values = [t.r_multiple for t in trades if not math.isnan(t.r_multiple)]
    return {
        "n": n,
        "win_rate": len(wins) / n * 100.0,
        "profit_factor": (gross_profit / gross_loss) if gross_loss > 0 else float("inf") if gross_profit > 0 else float("nan"),
        "expectancy_r": (sum(r_values) / len(r_values)) if r_values else float("nan"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit-symbols", type=int, default=None)
    parser.add_argument("--out", default=str(_DEFAULT_OUT_MD))
    args = parser.parse_args(argv)

    symbols = get_bist_universe()
    if args.limit_symbols is not None:
        symbols = symbols[: args.limit_symbols]
    total = len(symbols)
    print(f"{total} sembol -- skor seviyeleri {_SCORE_LEVELS}, capture-rate + PF/WR olculecek...")

    bt_params = BacktestParams()
    trades_by_score: dict[int, list] = {s: [] for s in _SCORE_LEVELS}
    n_signals_by_score: dict[int, int] = {s: 0 for s in _SCORE_LEVELS}
    n_symbols_with_bars: dict[int, int] = {s: 0 for s in _SCORE_LEVELS}  # sembol basina yillik frekans icin

    total_true_rallies = 0
    caught_by_score: dict[int, int] = {s: 0 for s in _SCORE_LEVELS}
    total_symbol_years = 0.0

    for done, symbol in enumerate(symbols, start=1):
        if done % 50 == 0:
            print(f"  ... {done}/{total} sembol islendi")
        df = fetch_ohlcv_abcd(symbol, "1D", _N_BARS)
        if df.empty or len(df) < 300:
            continue

        # min_score=1 (EN GEVSEK) sinyal seti -- daha yuksek skorlar bunun ALT KUMESI.
        all_signals = rps.detect(df, rps.Params(min_score=1))
        for score_level in _SCORE_LEVELS:
            level_signals = [s for s in all_signals if s.score >= score_level]
            if not level_signals:
                continue
            n_signals_by_score[score_level] += len(level_signals)
            n_symbols_with_bars[score_level] += 1
            trades, _curve = backtest_symbol(df, symbol, level_signals, bt_params)
            trades_by_score[score_level].extend(trades)

        # Capture-rate: GERCEK buyuk yukselisler (AYNI %50/120-bar tanim).
        candidates = rp.find_rally_candidates(df, symbol, "1D", pivot_lookback=10, max_lookahead_bars=_MAX_LOOKAHEAD_BARS)
        true_rallies = [c for c in candidates if c.rally_pct >= _RALLY_THRESHOLD]
        total_true_rallies += len(true_rallies)
        true_rally_low_bars = {c.low_bar for c in true_rallies}

        signal_low_bars_by_score: dict[int, set] = {s: set() for s in _SCORE_LEVELS}
        for sig in all_signals:
            low_bar = sig.signal_bar - rps.Params().pivot_lookback
            for score_level in _SCORE_LEVELS:
                if sig.score >= score_level:
                    signal_low_bars_by_score[score_level].add(low_bar)
        for score_level in _SCORE_LEVELS:
            caught_by_score[score_level] += len(true_rally_low_bars & signal_low_bars_by_score[score_level])

        total_symbol_years += len(df) / 252.0

    print("Backtest tamamlandi, rapor yaziliyor...")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Buyuk Yukselis Onculu Stratejisi -- Tam BIST Backtest + Capture Rate\n",
        f"\nOlusturulma: {now}\n",
        "\n## Kapsam\n",
        f"\nSembol: {total} · Derinlik: ~{_N_BARS} bar (1D) · Toplam sembol-yili: {total_symbol_years:.0f} · "
        f"Toplam GERCEK buyuk yukselis (>=%{_RALLY_THRESHOLD:.0f}): {total_true_rallies}\n",
        "\n## Strateji Kurallari\n",
        "\n`docs/spec/RALLY_PRECURSOR_ARASTIRMASI.md`nin HOLDOUT'TA DOGRULANAN 4 kosulundan (35 ozellik "
        "arasindan secilen EN GUCLU 4'u) puanlama: (1) hacim kurumasi <=0.45, (2) talep bolgesine yakinlik "
        "<=3.0xATR, (3) gap-down girisi <=-%0.3, (4) ATR yuzdelik sirasi >=0.55. Skor 0-4, esik ayarlanabilir.\n",
        "\n## Sonuclar -- Skor Esigine Gore (PF/WR + Sinyal Sikligi + Capture Rate)\n",
        "\n| Min Skor | n_islem | Win Rate % | PF | Beklenti (R) | Guven | Sinyal/sembol-yili | "
        "Yakalanan buyuk yukselis | Capture Rate % |\n|---|---|---|---|---|---|---|---|---|\n",
    ]
    for score_level in _SCORE_LEVELS:
        stats = _cell_stats(trades_by_score[score_level])
        freq_per_year = n_signals_by_score[score_level] / total_symbol_years if total_symbol_years > 0 else float("nan")
        capture_rate = caught_by_score[score_level] / total_true_rallies * 100.0 if total_true_rallies > 0 else float("nan")
        lines.append(
            f"| >={score_level}/4 | {stats['n']} | {_fmt(stats['win_rate'])} | {_fmt(stats['profit_factor'])} | "
            f"{_fmt(stats['expectancy_r'], '{:.3f}')} | {_guven(stats['n'])} | {freq_per_year:.2f} | "
            f"{caught_by_score[score_level]}/{total_true_rallies} | {_fmt(capture_rate, '{:.1f}')} |\n"
        )

    lines.append(
        "\n> **Not:** 'Sinyal/sembol-yili' -- ortalama bir hissede yilda kac sinyal geldigi (kullanicinin "
        "'yilda 2-3' hedefiyle DOGRUDAN karsilastirilabilir). 'Capture Rate' -- BUTUN BIST'teki gercek "
        "buyuk yukselislerin (>=%50, ~8 yil) kaci bu skor esiginde bir sinyalle YAKALANDI. Bu ikisi "
        "GENELLIKLE ters yonlu trade-off'tur -- daha siki skor esigi DAHA AZ sinyal (istenen frekansa "
        "yaklasir) ama DAHA AZ yukselis yakalar (capture rate duser).\n"
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"Rapor: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
