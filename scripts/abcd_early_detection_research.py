"""AB=CD "erken tespit" arastirma CLI -- `src/analysis/abcd_early_detection.py`
motorunu gercek BIST evreninde/onbellekten calistirir, T_max'i ampirik
belirler, gercek vs GBM-null kova tablolarini karsilastirir, sonucu
`docs/spec/ABCD_ERKEN_TESPIT_ARASTIRMASI.md`ye yazar.

Gorev talimatinin BIREBIR istegi -- bkz. `abcd_early_detection.py` modul-ust
notu (metodoloji, "olasilik" kelimesi YASAGI, kucuk-n disiplini). Bu script
sadece I/O ORKESTRASYONU yapar (`abcd_data.fetch_ohlcv_abcd` -- zaten
parquet-onbellekli, `abcd_scanner.get_bist_universe` -- DB'den BIST ticker
listesi); hicbir istatistiksel/etiketleme mantigi burada YOKTUR.

**Bu script `scripts/abcd_research.py`/`abcd_success_factors.py` ile AYNI
ANDA calisabilir** -- ucu de sadece `fetch_ohlcv_abcd`in KENDI parquet
onbellegini okur/yazar (bkz. o script'lerin AYNI notu).

Kullanim:
    python scripts/abcd_early_detection_research.py --symbols THYAO,ASELS,TUPRS --tfs 1D --years 2
    python scripts/abcd_early_detection_research.py --tfs 1D,240             # varsayilan: TUM BIST evreni
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import pandas as pd  # noqa: E402

import config  # noqa: E402
from src.analysis.abcd_early_detection import (  # noqa: E402
    analyze_series,
    build_bucket_table,
    compare_to_null,
    compute_t_max,
    estimate_log_return_std,
    format_bucket_sentence,
    generate_gbm_series,
)
from src.analysis.abcd_pattern import Params, detect  # noqa: E402
from src.analysis.abcd_scanner import get_bist_universe  # noqa: E402
from src.fetchers.abcd_data import fetch_ohlcv_abcd  # noqa: E402

config.setup_logging()

_DEFAULT_OUT = BASE_DIR / "docs" / "spec" / "ABCD_ERKEN_TESPIT_ARASTIRMASI.md"
_BARS_PER_YEAR = {"60": 252 * 7, "120": 252 * 4, "240": 252 * 2, "1D": 252, "1W": 52}


def _parse_list(raw: str) -> list[str]:
    return [x.strip() for x in raw.split(",") if x.strip()]


def _bars_for_years(tf: str, years: float) -> int:
    return max(int(_BARS_PER_YEAR[tf] * years) + 50, 200)


def _run_for_tf(
    symbols: list[str], tf: str, years: float, params: Params, seed: int
) -> dict:
    """Tek bir zaman dilimi icin: OHLCV cek -> T_max belirle -> gercek +
    (sembol-eslestirilmis, kendi volatilitesine kalibre edilmis) GBM-null
    seriler uzerinde `analyze_series` calistir -> kova tablolarini kurup
    karsilastir. Sembol basina veri bulunamazsa (ag hatasi/olu ticker)
    sessizce ATLANIR (bkz. `fetch_ohlcv_abcd`nin Kural 9 toleransi)."""
    n_bars = _bars_for_years(tf, years)

    all_signals = []
    dfs: dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        df = fetch_ohlcv_abcd(symbol, tf, n_bars)
        if df.empty:
            continue
        dfs[symbol] = df
        all_signals.extend(detect(df, params))

    if not dfs:
        return {"tf": tf, "n_symbols": 0, "error": "hicbir sembol icin veri cekilemedi"}

    t_max = compute_t_max(all_signals)

    real_observations = []
    null_observations = []
    reason_counts: dict[str, int] = {}
    for i, (symbol, df) in enumerate(dfs.items()):
        labels, obs = analyze_series(df, params, t_max)
        real_observations.extend(obs)
        for lab in labels:
            reason_counts[lab.reason] = reason_counts.get(lab.reason, 0) + 1

        close = df["close"].to_numpy(dtype=float)
        std = estimate_log_return_std(close)
        synthetic_df = generate_gbm_series(
            n_bars=len(df), log_return_std=std, seed=seed + i, start_price=float(close[0])
        )
        _null_labels, null_obs = analyze_series(synthetic_df, params, t_max)
        null_observations.extend(null_obs)

    real_table = build_bucket_table(real_observations)
    null_table = build_bucket_table(null_observations)
    comparison = compare_to_null(real_table, null_table)

    return {
        "tf": tf,
        "n_symbols": len(dfs),
        "t_max": t_max,
        "n_signals_for_t_max": len(all_signals),
        "reason_counts": reason_counts,
        "comparison": comparison,
        "error": None,
    }


def _format_tf_section(result: dict) -> str:
    tf = result["tf"]
    if result.get("error"):
        return f"\n\n---\n\n# tf={tf}\n\n_{result['error']}._\n"

    lines = [f"\n\n---\n\n# tf={tf}\n"]
    lines.append(
        f"\n- Veri bulunan sembol sayisi: {result['n_symbols']}\n"
        f"- T_max (timeout esigi, {result['n_signals_for_t_max']} onaylanmis sinyalin "
        f"d_bar-c_bar dagiliminin p95'i): {result['t_max']} bar\n"
    )
    reasons = result["reason_counts"]
    total_candidates = sum(reasons.values())
    lines.append(
        f"- Toplam ABC adayi: {total_candidates} "
        f"(basari={reasons.get('success', 0)}, "
        f"asiri-uzama={reasons.get('overextension', 0)}, "
        f"reshuffle={reasons.get('reshuffled', 0)}, "
        f"timeout(belirsiz)={reasons.get('timeout', 0)})\n"
    )

    comparison = result["comparison"]
    n_tested = int(comparison["n_hucre_test_edilen"].iloc[0]) if not comparison.empty else 0
    eff_alpha = float(comparison["effective_alpha"].iloc[0]) if not comparison.empty else 0.05
    lines.append(
        f"\n> Null-hipotez karsilastirmasi: {n_tested} hucre (gercek VE null'da n>=30 olan) "
        f"test edildi, Bonferroni-tipi etkin anlamlilik esigi ~= {eff_alpha:.5f}.\n"
    )

    lines.append("\n## Kova tablosu -- HAM frekans + Wilson %95 GA + null-karsilastirma\n\n")
    for _, row in comparison.iterrows():
        lines.append(f"- {format_bucket_sentence(row)}\n")

    lines.append(
        "\n\n| Yon | Kova | n_basari | n_toplam | oran | Wilson GA | Guven | null-karsilastirma | p |\n"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|\n")
    for _, row in comparison.iterrows():
        oran_str = "N/A" if row["n_toplam"] == 0 else f"{row['oran']:.3f}"
        ci_str = "N/A" if row["n_toplam"] == 0 else f"[{row['wilson_ci_low']:.3f}, {row['wilson_ci_high']:.3f}]"
        p_str = "N/A" if pd.isna(row["p_value"]) else f"{row['p_value']:.4f}"
        lines.append(
            f"| {row['direction']} | {row['bucket']} | {row['n_basari']} | {row['n_toplam']} | "
            f"{oran_str} | {ci_str} | {row['guven_etiketi']} | {row['null_karsilastirma']} | {p_str} |\n"
        )

    return "".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "AB=CD 'erken tespit' arastirmasi -- D henuz onaylanmadan (ABC olusmus, C "
            "onaylanmisken) CD ilerlemesine gore tarihsel tamamlanma FREKANSI (olasilik "
            "DEGIL) + Wilson %95 GA + GBM-null karsilastirmasi."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--symbols", default=None, help="Virgullu ticker listesi (varsayilan: get_bist_universe()).")
    parser.add_argument("--tfs", default="240,1D", help="Virgullu zaman dilimi listesi (varsayilan: 240,1D).")
    parser.add_argument("--years", type=float, default=2.0, help="Sembol basina gecmis yil sayisi (varsayilan: 2.0).")
    parser.add_argument("--seed", type=int, default=42, help="GBM-null uretimi icin taban rastgele tohum (varsayilan: 42).")
    parser.add_argument("--out", default=str(_DEFAULT_OUT), help=f"Markdown rapor cikti yolu (varsayilan: {_DEFAULT_OUT}).")
    parser.add_argument("--limit-symbols", type=int, default=None, help="TEST/dogrulama amacli: sadece ilk N sembolle calistir.")
    args = parser.parse_args(argv)

    if args.symbols:
        symbols = _parse_list(args.symbols)
    else:
        print("Sembol listesi verilmedi -- get_bist_universe() ile TUM BIST evreni DB'den cekiliyor...")
        symbols = get_bist_universe()
        print(f"  {len(symbols)} sembol bulundu.")

    if args.limit_symbols is not None:
        symbols = symbols[: args.limit_symbols]
        print(f"--limit-symbols {args.limit_symbols}: ilk {len(symbols)} sembolle sinirlandi.")

    if not symbols:
        print("Sembol listesi bos -- arastirma yapilamaz.")
        return 1

    tfs = _parse_list(args.tfs)
    params = Params()

    print(f"Erken tespit arastirmasi: {len(symbols)} sembol x {len(tfs)} tf (~{args.years} yil gecmis).")
    print(
        "NOT: bu HAM FREKANS + guven araligi analizidir, olasilik modeli DEGIL -- "
        "kucuk-n hucreler ASLA gizlenmez, GUVENSIZ etiketlenir.\n"
    )

    sections: list[str] = []
    for tf in tfs:
        print(f"[{tf}] calisiyor...")
        result = _run_for_tf(symbols, tf, args.years, params, args.seed)
        if result.get("error"):
            print(f"  UYARI: {result['error']}")
        else:
            print(
                f"  {result['n_symbols']} sembol, T_max={result['t_max']} bar, "
                f"aday dagilim={result['reason_counts']}"
            )
        sections.append(_format_tf_section(result))

    header = (
        "# AB=CD Erken Tespit Arastirmasi\n\n"
        f"Sembol sayisi: {len(symbols)} | Zaman dilimleri: {', '.join(tfs)} | "
        f"Gecmis derinligi: ~{args.years} yil | GBM-null tohum: {args.seed}\n\n"
        "> Bu rapor bir OLASILIK MODELI DEGILDIR -- ABC olusup C onaylandiktan sonra, "
        "belirli bir CD-ilerleme araliginda gozlemlenen tarihsel HAM FREKANS + Wilson "
        "%95 guven araligidir. Sonuclar, ayni pipeline'in gerceklesmis volatiliteye "
        "kalibre edilmis bir GBM (geometrik Brownian hareket) rastgele-yurus null "
        "serisiyle karsilastirmasiyla birlikte okunmalidir -- 'anlamli farkli' "
        "ETIKETLENMEYEN hucreler rastgele yurusten ayirt edilemez.\n"
    )
    full_report = header + "".join(sections)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(full_report, encoding="utf-8")
    print(f"\nRapor kaydedildi: {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
