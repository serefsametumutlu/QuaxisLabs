"""Harmonik formasyon ailesi karsilastirmasi (ABCD vs Gartley/Bat/Butterfly/
Crab) -- `src.analysis.harmonic_presets.HARMONIC_PRESETS`in her birini
`src.analysis.abcd_backtest.run_grid()` uzerinden TAM BIST evreninde LONG+
SHORT ayri ayri, TL grafiginde calistirir, tek bir siralanmis karsilastirma
raporu uretir.

Mimari kararlar: `docs/spec/spec_abcd_mimari_kararlar.md`,
`src/analysis/harmonic_presets.py` (formasyon on-ayarlarinin matematiksel
gerekcesi/sinirlamalari icin -- BURADA TEKRARLANMAZ).

`scripts/abcd_research.py`nin ikizi -- AYNI iki disiplini uygular (bkz. o
dosyanin ust notu, "Quant-uzmani disiplinleri"):

- `min_trades_show` (varsayilan 30) altindaki hucreler ASLA gizlenmez.
- "En iyi N kombinasyon" ozeti SADECE `trustworthy=True`
  (n >= `min_trades_trustworthy`, varsayilan 100) hucrelerden secilir.

## Neden `run_grid`e TEK cagrida `detector_params=[...]` VERILMEDI

`run_grid`in hucre anahtari `(tf, currency, params_label)`dir ve
`_params_label()` SADECE `pivot_lookback`/`atr_mult`/`fib_tolerance`
iceriyor -- `min_bc_retrace`/`max_bc_retrace`/`cd_min_ext`/`cd_max_ext`/
`enable_long`/`enable_short` ETIKETE YANSIMAZ. `abcd_research.py` bu
sorunu YON icin zaten cozmustu (ayri `run_grid` cagrilari); bu script AYNI
sorunu FORMASYON icin de cozer: her (formasyon x yon) kombinasyonu KENDI
ayri `run_grid` cagrisinda calisir (5 formasyon x 2 yon = 10 cagri), sonuc
DataFrame'lerine script seviyesinde `formasyon`/`yon` sutunlari eklenip
birlestirilir -- `run_grid`in kendisi DEGISTIRILMEDI.

## Coklu-karsilastirma uyarisi -- GLOBAL, sadece per-cagri DEGIL

Bu script tek bir arastirma sorusu icin ("hangi formasyon/yon/tf en iyi
performansi veriyor?") 10 AYRI `run_grid` cagrisi yapar; asil karsilastirma
YUZEYI bu 10 cagrinin urettigi TUM hucrelerdir, sadece bir cagrininki degil.
Bu yuzden `_build_report()` her sub-grid'in kendi `grid_warning`ini (ham
referans icin) tutmakla birlikte, TUM hucreler uzerinden hesaplanan bir
GLOBAL Bonferroni-tipi duzeltmeyi (`effective_alpha = 0.05 / n_hucre_toplam`)
raporun basinda ONE CIKARIR -- gercek karar/secim bu global esige gore
yapilmalidir.

Kullanim:
    python scripts/harmonic_karsilastirma.py                                   # TUM BIST evreni (BUYUK -- dikkat)
    python scripts/harmonic_karsilastirma.py --limit-symbols 5                 # kucuk dogrulama kosusu
    python scripts/harmonic_karsilastirma.py --symbols THYAO,ASELS,TUPRS
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
from dataclasses import replace  # noqa: E402
from src.analysis.abcd_backtest import BacktestParams, run_grid, save_summary  # noqa: E402
from src.analysis.abcd_scanner import get_bist_universe  # noqa: E402
from src.analysis.harmonic_presets import HARMONIC_PRESETS  # noqa: E402

config.setup_logging()

_DEFAULT_OUT_MD = BASE_DIR / "docs" / "spec" / "ABCD_HARMONIK_FORMASYON_KARSILASTIRMASI.md"
_DEFAULT_OUT_CSV = config.DATA_DIR / "abcd_cache" / "harmonic_karsilastirma_summary.csv"

_YONLER = ("LONG", "SHORT")


def _parse_list(raw: str) -> list[str]:
    return [x.strip() for x in raw.split(",") if x.strip()]


def _fmt_num(value: float, fmt: str = "{:.2f}") -> str:
    """`NaN`/sonsuz degerleri markdown-dostu metne cevirir (rapordan hicbir
    hucre -- N/A/sonsuz dahil -- sessizce ATILMAZ). `scripts/abcd_research.py`
    ile AYNI davranis."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    if isinstance(value, float) and math.isinf(value):
        return "sonsuz" if value > 0 else "-sonsuz"
    return fmt.format(value)


def _run_one_cell_grid(
    symbols: list[str],
    tfs: list[str],
    currencies: list[str],
    years: float,
    min_trades_show: int,
    min_trades_trustworthy: int,
    formasyon: str,
    yon: str,
    base_params,
    pivot_lookback: int,
) -> tuple[pd.DataFrame, str, int]:
    """Tek bir (formasyon x yon) kombinasyonu icin `run_grid`i cagirir,
    sonuca `formasyon`/`yon` sutunlarini ekler. `(summary, grid_warning,
    n_hucre)` doner -- `grid_warning`/`n_hucre` `concat` oncesi ayrica
    dondurulur cunku `DataFrame.attrs` concat sonrasi guvenilir korunmaz
    (`abcd_research.py::_run_direction_grid` ile AYNI teknik)."""
    enable_long = yon == "LONG"
    detector_params = replace(
        base_params,
        enable_long=enable_long,
        enable_short=not enable_long,
        pivot_lookback=pivot_lookback,
    )
    summary = run_grid(
        symbols=symbols,
        tfs=tfs,
        backtest_params=BacktestParams(),
        denominators=tuple(currencies),
        years=years,
        min_trades_show=min_trades_show,
        min_trades_trustworthy=min_trades_trustworthy,
        detector_params=[detector_params],
    )
    grid_warning = summary.attrs.get("grid_warning", "(grid_warning hesaplanamadi -- hic hucre uretilmedi)")
    n_hucre = int(summary.attrs.get("n_hucre", len(summary)))
    summary = summary.copy()
    summary["formasyon"] = formasyon
    summary["yon"] = yon
    return summary, grid_warning, n_hucre


def _cell_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "\n_Bu kombinasyon icin hicbir hucre uretilmedi (veri cekilemedi ya da hic sinyal yok)._\n"
    lines = [
        "\n| Zaman Dilimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % | Guven |\n",
        "|---|---|---|---|---|---|---|\n",
    ]
    for _, row in df.sort_values("tf").iterrows():
        lines.append(
            f"| {row['tf']} | {int(row['n_trades'])} | {_fmt_num(row['win_rate'])} | "
            f"{_fmt_num(row['profit_factor'])} | {_fmt_num(row['expectancy_r'], '{:.3f}')} | "
            f"{_fmt_num(row['avg_max_drawdown_pct'])} | {row['guven_etiketi']} |\n"
        )
    return "".join(lines)


def _build_report(
    combined: pd.DataFrame,
    per_cell_warnings: list[tuple[str, str, str]],
    n_hucre_toplam: int,
    symbols: list[str],
    tfs: list[str],
    currencies: list[str],
    years: float,
    min_trades_show: int,
    min_trades_trustworthy: int,
    out_csv_path: Path,
    top_n: int,
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = []

    lines.append("# ABCD Harmonik Formasyon Karsilastirmasi\n")
    lines.append(f"\nOlusturulma: {now}\n")

    lines.append("\n## Kapsam\n")
    lines.append(
        "\nBu rapor, `src/analysis/harmonic_presets.py`deki 5 formasyon on-ayarini "
        "(ABCD referans + Gartley/Bat/Butterfly/Crab) TAM BIST evreninde, LONG ve SHORT "
        "AYRI AYRI, TL grafiginde karsilastirir. **On-ayarlarin matematiksel gerekcesi/"
        "bilinen sinirlamalari** (CD/AB vs CD/BC donusumu, X noktasi/XD oraninin "
        "kontrol edilememesi) `src/analysis/harmonic_presets.py` modul dokumantasyonundadir "
        "-- burada TEKRARLANMAZ, okumadan sonuclari YORUMLAMAYIN.\n"
    )

    lines.append("\n## ⚠️ METODOLOJI UYARISI -- ONCE BU BOLUMU OKUYUN\n")
    lines.append(
        f"\nKucuk n'lerde sahte kesinlik riskine karsi (bkz. `docs/spec/spec_abcd_mimari_kararlar.md`, "
        f"\"Backtest metodolojisi\"): `min_trades_show={min_trades_show}` altindaki hucreler ASLA "
        "gizlenmez -- \"GUVENSIZ (n=X)\" olarak acikca etiketlenip tabloda TUTULUR. "
        f"\"En iyi {top_n} kombinasyon\" iddialari SADECE `min_trades_trustworthy="
        f"{min_trades_trustworthy}` esigini gecen hucrelerden secilir. Secilen herhangi bir "
        "formasyon/yon/tf kombinasyonu, ayri bir out-of-sample donemde/sembol alt-kumesinde "
        "AYRICA dogrulanmalidir.\n"
    )
    lines.append(f"\n- Sembol sayisi: {len(symbols)}\n")
    lines.append(f"- Zaman dilimleri: {', '.join(tfs)}\n")
    lines.append(f"- Para birimleri: {', '.join(currencies)}\n")
    lines.append(f"- Formasyonlar: {', '.join(HARMONIC_PRESETS.keys())}\n")
    lines.append(f"- Backtest derinligi: ~{years} yil\n")
    lines.append(
        "- Yon: LONG ve SHORT AYRI AYRI backtest edildi. Formasyon: her formasyon KENDI ayri "
        f"`run_grid` cagrisinda calisti ({len(HARMONIC_PRESETS)} formasyon x {len(_YONLER)} yon "
        "= 10 ayri cagri) -- `run_grid`in hucre-etiketleme sinirlamasi (`_params_label` BC/CD "
        "bantlarini icermez) nedeniyle formasyonlar AYNI cagriya karistirilamazdi, bkz. bu "
        "scriptin modul ust notu.\n"
    )

    lines.append("\n## Coklu-karsilastirma (Bonferroni-tipi) GLOBAL uyari\n")
    effective_alpha = 0.05 / max(n_hucre_toplam, 1)
    lines.append(
        f"\nBu karsilastirma toplamda **{n_hucre_toplam} hucre** uretti (formasyon x yon x tf x "
        f"para birimi -- 10 ayri `run_grid` cagrisinin TOPLAMI). Bonferroni-tipi duzeltmeyle "
        f"etkin anlamlilik esigi ~= **{effective_alpha:.5f}** (0.05/{n_hucre_toplam}). Asagidaki "
        "\"en iyi\" siralamayi bu global esige gore degerlendirin -- tek bir hucrenin one cikmasi "
        "10 ayri deneyin en sansli sonucu olabilir, formasyon-basina/yon-basina hesaplanan alt "
        "uyarilar (asagida) bu global riski KUCUMSER.\n"
    )
    lines.append("\n<details>\n<summary>Formasyon x yon basina ham grid_warning (referans)</summary>\n\n")
    for formasyon, yon, warning in per_cell_warnings:
        lines.append(f"- **{formasyon} / {yon}:** {warning}\n")
    lines.append("\n</details>\n")

    lines.append(f"\n## En Iyi {top_n} Kombinasyon (SADECE GUVENILIR, n >= {min_trades_trustworthy} hucrelerden)\n")
    trustworthy = combined[combined["trustworthy"] == True] if not combined.empty else combined  # noqa: E712
    if trustworthy.empty:
        lines.append(
            f"\n_Hicbir hucre `min_trades_trustworthy={min_trades_trustworthy}` esigini gecmedi -- "
            "\"en iyi kombinasyon\" iddiasi YAPILAMAZ (kucuk n'de sahte kesinlik riski)._\n"
        )
    else:
        topn = trustworthy.sort_values(["profit_factor", "expectancy_r"], ascending=[False, False]).head(top_n)
        lines.append(
            "\n| Sira | Formasyon | Yon | TF | Para Birimi | n_trades | Win Rate % | "
            "Profit Factor | Expectancy (R) | Ort. Max DD % |\n"
        )
        lines.append("|---|---|---|---|---|---|---|---|---|---|\n")
        for i, (_, row) in enumerate(topn.iterrows(), start=1):
            lines.append(
                f"| {i} | {row['formasyon']} | {row['yon']} | {row['tf']} | {row['currency']} | "
                f"{int(row['n_trades'])} | {_fmt_num(row['win_rate'])} | {_fmt_num(row['profit_factor'])} | "
                f"{_fmt_num(row['expectancy_r'], '{:.3f}')} | {_fmt_num(row['avg_max_drawdown_pct'])} |\n"
            )

    lines.append("\n## Formasyon Basina Detay\n")
    for formasyon in HARMONIC_PRESETS.keys():
        lines.append(f"\n### {formasyon}\n")
        for yon in _YONLER:
            lines.append(f"\n#### {yon}\n")
            sub = combined[(combined["formasyon"] == formasyon) & (combined["yon"] == yon)]
            lines.append(_cell_table(sub))

    lines.append("\n## Ham Veri\n")
    lines.append(f"\nTum hucrelerin ham tablosu (5 formasyon x LONG+SHORT birlikte): `{out_csv_path}`\n")

    return "".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "ABCD/Gartley/Bat/Butterfly/Crab formasyon on-ayarlarini TAM BIST evreninde "
            "LONG+SHORT ayri, TL grafiginde karsilastirir -- siralanmis markdown rapor + CSV uretir."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--symbols", default=None, help="Virgullu ticker listesi (varsayilan: get_bist_universe() -- TUM BIST evreni, DB'den).")
    parser.add_argument("--tfs", default="1D,240", help="Virgullu zaman dilimi listesi (varsayilan: 1D,240 -- onceki arastirmada edge SADECE bu ikisinde bulundu).")
    parser.add_argument("--years", type=float, default=2.0, help="Sembol basina gecmis yil sayisi (varsayilan: 2.0).")
    parser.add_argument("--currencies", default="TRY", help="Virgullu para birimi listesi (varsayilan: TRY).")
    parser.add_argument("--min-trades-show", type=int, default=30, help="Bu esigin altindaki hucreler GUVENSIZ etiketlenir, ASLA gizlenmez (varsayilan: 30).")
    parser.add_argument("--min-trades-trustworthy", type=int, default=100, help="\"En iyi kombinasyon\" iddialari icin gereken minimum islem sayisi (varsayilan: 100).")
    parser.add_argument("--top-n", type=int, default=10, help="Rapordaki 'en iyi N kombinasyon' tablosunun boyutu (varsayilan: 10).")
    parser.add_argument("--out", default=str(_DEFAULT_OUT_MD), help=f"Markdown rapor cikti yolu (varsayilan: {_DEFAULT_OUT_MD}).")
    parser.add_argument("--out-csv", default=str(_DEFAULT_OUT_CSV), help=f"Ham tablo CSV cikti yolu (varsayilan: {_DEFAULT_OUT_CSV}).")
    parser.add_argument("--limit-symbols", type=int, default=None, help="TEST/dogrulama amacli: sadece ilk N sembolle calistir.")
    parser.add_argument(
        "--pivot-lookback", type=int, default=5,
        help="abcd_pattern.Params.pivot_lookback (varsayilan: 5, Pine kaynagiyla AYNI) -- TUM formasyonlara AYNI uygulanir.",
    )
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
        print("Sembol listesi bos -- islem yapilamaz.")
        return 1

    tfs = _parse_list(args.tfs)
    currencies = _parse_list(args.currencies)

    print(
        f"Grid: {len(symbols)} sembol x {len(tfs)} tf x {len(currencies)} para birimi x "
        f"{len(HARMONIC_PRESETS)} formasyon x 2 yon (~{args.years} yil gecmis, "
        f"{len(HARMONIC_PRESETS) * len(_YONLER)} ayri run_grid cagrisi)."
    )
    if args.pivot_lookback != 5:
        print(f"UYARI: pivot_lookback={args.pivot_lookback} (Pine varsayilani 5 DEGIL) -- karsilastirma/deney kosusu.")

    all_summaries: list[pd.DataFrame] = []
    per_cell_warnings: list[tuple[str, str, str]] = []
    n_hucre_toplam = 0

    step = 0
    total_steps = len(HARMONIC_PRESETS) * len(_YONLER)
    for formasyon, base_params in HARMONIC_PRESETS.items():
        for yon in _YONLER:
            step += 1
            print(f"[{step}/{total_steps}] {formasyon} / {yon} calisiyor...")
            summary, warning, n_hucre = _run_one_cell_grid(
                symbols, tfs, currencies, args.years, args.min_trades_show, args.min_trades_trustworthy,
                formasyon=formasyon, yon=yon, base_params=base_params, pivot_lookback=args.pivot_lookback,
            )
            print(f"  tamamlandi: {len(summary)} hucre uretildi.")
            all_summaries.append(summary)
            per_cell_warnings.append((formasyon, yon, warning))
            n_hucre_toplam += n_hucre

    combined = pd.concat(all_summaries, ignore_index=True) if all_summaries else pd.DataFrame()

    out_csv_path = Path(args.out_csv)
    saved_csv = save_summary(combined, path=out_csv_path)
    print(f"Ham CSV kaydedildi: {saved_csv}")

    report_md = _build_report(
        combined, per_cell_warnings, n_hucre_toplam, symbols, tfs, currencies, args.years,
        args.min_trades_show, args.min_trades_trustworthy, saved_csv, args.top_n,
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report_md, encoding="utf-8")
    print(f"Rapor kaydedildi: {out_path}")

    if not combined.empty:
        n_guvenilir = int((combined["trustworthy"] == True).sum())  # noqa: E712
        n_guvensiz = len(combined) - n_guvenilir
        print(f"Ozet: {len(combined)} hucre ({n_guvenilir} guvenilir, {n_guvensiz} guvensiz/dusuk-guven).")
    else:
        print("Ozet: hicbir hucre uretilmedi.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
