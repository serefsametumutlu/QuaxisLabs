"""AB=CD coklu-sembol / coklu-zaman-dilimi / coklu-para-birimi arastirma
taramasi (Faz 7) -- `src.analysis.abcd_backtest.run_grid()`'i orkestre eder,
tek bir markdown rapor + ham CSV uretir.

Mimari kararlar: `docs/spec/spec_abcd_mimari_kararlar.md` (ozellikle
"Backtest metodolojisi -- quant-uzmani denetiminin sonucu" bolumu).

**BU SCRIPT KENDI BASINA GERCEK 657-sembollik BUYUK TARAMAYI CALISTIRMAZ**
-- varsayilan argumanlarla calistirilirsa (`--symbols` verilmezse) TUM BIST
evrenini `get_bist_universe()`'den cekip taramaya CALISIR; bu bilincli bir
tasarim (spec'in "tam evren" ihtiyacini karsilamak icin), ama o BUYUK kosu
AYRI bir adim/onay gerektirir -- kucuk olcekte (`--limit-symbols`) test
edilmeden calistirilmamalidir.

## LONG/SHORT ayrimi -- KRITIK bir `run_grid` sinirlamasinin cozumu

`run_grid`in hucre anahtari `(tf, currency, params_label)`dir ve
`_params_label()` SADECE `pivot_lookback`/`atr_mult`/`fib_tolerance`
iceriyor -- `enable_long`/`enable_short` ETIKETE YANSIMAZ. Bu yuzden AYNI
`run_grid` cagrisina `Params(enable_long=True, enable_short=False)` ve
`Params(enable_long=False, enable_short=True)` birlikte `detector_params`
olarak verilirse, ikisinin islemleri AYNI hucrede CARPISIP birlesirdi (yon
bilgisi kaybolurdu) -- bu istenen davranis DEGIL (kullanicinin acik istegi:
"long ve short ayri ayri"). Cozum: bu script `run_grid`'i YON BASINA AYRI
cagirir (2 ayri cagri, 2 ayri grid_warning/Bonferroni hesabi) ve sonuc
DataFrame'lerine script seviyesinde bir `yon` sutunu ekleyip birlestirir --
`run_grid`in kendisi DEGISTIRILMEDI.

## Quant-uzmani disiplinleri (spec'ten, BIREBIR uygulanir)

- `min_trades_show` (varsayilan 30) altindaki hucreler ASLA gizlenmez --
  "GUVENSIZ (n=X)" etiketiyle rapora dahil edilir.
- "En verimli 5 kosul" ozeti SADECE `trustworthy=True`
  (n >= `min_trades_trustworthy`, varsayilan 100) hucrelerden secilir.
- USD bolumu, `run_grid`in urettigi `currency_note`i ("bagimsiz sinyal
  kumesi" uyarisi -- doviz-ayarli getiri DEGIL) rapor basligindan hemen
  sonra TEKRARLAR.

Kullanim:
    python scripts/abcd_research.py                                    # TUM BIST evreni, tam grid (BUYUK -- dikkat)
    python scripts/abcd_research.py --limit-symbols 3 --tfs 1D --currencies TRY   # kucuk dogrulama kosusu
    python scripts/abcd_research.py --symbols THYAO,ASELS,TUPRS --tfs 240,1D
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
from src.analysis.abcd_backtest import BacktestParams, run_grid, save_summary  # noqa: E402
from src.analysis.abcd_pattern import Params  # noqa: E402
from src.analysis.abcd_scanner import get_bist_universe  # noqa: E402

config.setup_logging()

_DEFAULT_OUT_MD = BASE_DIR / "docs" / "spec" / "ABCD_BACKTEST_SONUCLARI.md"
_DEFAULT_OUT_CSV = config.DATA_DIR / "abcd_cache" / "backtest_research_summary.csv"


def _parse_list(raw: str) -> list[str]:
    return [x.strip() for x in raw.split(",") if x.strip()]


def _fmt_num(value: float, fmt: str = "{:.2f}") -> str:
    """`NaN`/sonsuz degerleri markdown-dostu metne cevirir (rapordan hicbir
    hucre -- N/A/sonsuz dahil -- sessizce ATILMAZ)."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    if isinstance(value, float) and math.isinf(value):
        return "sonsuz" if value > 0 else "-sonsuz"
    return fmt.format(value)


def _run_direction_grid(
    symbols: list[str],
    tfs: list[str],
    currencies: list[str],
    years: float,
    min_trades_show: int,
    min_trades_trustworthy: int,
    yon: str,
    detector_params: Params,
) -> tuple[pd.DataFrame, str]:
    """Tek bir yon (LONG veya SHORT) icin `run_grid`'i cagirir, sonuca `yon`
    sutunu ekler. `(summary, grid_warning)` doner -- `grid_warning` `concat`
    oncesi ayrica dondurulur cunku `DataFrame.attrs` concat sonrasi guvenilir
    korunmaz."""
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
    summary = summary.copy()
    summary["yon"] = yon
    return summary, grid_warning


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
    long_warning: str,
    short_warning: str,
    symbols: list[str],
    tfs: list[str],
    currencies: list[str],
    years: float,
    min_trades_show: int,
    min_trades_trustworthy: int,
    out_csv_path: Path,
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = []

    lines.append("# ABCD Backtest Arastirma Raporu\n")
    lines.append(f"\nOlusturulma: {now}\n")

    lines.append("\n## ⚠️ METODOLOJI UYARISI -- ONCE BU BOLUMU OKUYUN\n")
    lines.append(
        f"\nKucuk n'lerde sahte kesinlik riskine karsi (bkz. `docs/spec/spec_abcd_mimari_kararlar.md`, "
        f"\"Backtest metodolojisi\"): `min_trades_show={min_trades_show}` altindaki hucreler ASLA "
        "gizlenmez -- \"GUVENSIZ (n=X)\" olarak acikca etiketlenip tabloda TUTULUR. "
        f"\"En verimli kosul\" iddialari SADECE `min_trades_trustworthy={min_trades_trustworthy}` "
        "esigini gecen hucrelerden secilir. Secilen herhangi bir konfigurasyon, ayri bir "
        "out-of-sample donemde/sembol alt-kumesinde AYRICA dogrulanmalidir.\n"
    )
    lines.append(f"\n- Sembol sayisi: {len(symbols)}\n")
    lines.append(f"- Zaman dilimleri: {', '.join(tfs)}\n")
    lines.append(f"- Para birimleri: {', '.join(currencies)}\n")
    lines.append(f"- Backtest derinligi: ~{years} yil (60/120/240dk zaman dilimlerinde yfinance siniri nedeniyle fiilen ~2 yilla sinirli olabilir)\n")
    lines.append("- Yon: LONG ve SHORT AYRI AYRI backtest edildi -- her biri kendi bagimsiz `run_grid` cagrisinda, kendi Bonferroni-tipi uyarisiyla.\n")

    lines.append("\n### Grid boyutu / coklu-karsilastirma (Bonferroni-tipi) uyarisi\n")
    lines.append(f"\n**LONG grid:** {long_warning}\n")
    lines.append(f"\n**SHORT grid:** {short_warning}\n")

    lines.append(f"\n## En Verimli 5 Kosul (SADECE GUVENILIR, n >= {min_trades_trustworthy} hucrelerden)\n")
    trustworthy = combined[combined["trustworthy"] == True] if not combined.empty else combined  # noqa: E712
    if trustworthy.empty:
        lines.append(
            "\n_Hicbir hucre `min_trades_trustworthy` esigini gecmedi -- \"en verimli kosul\" iddiasi "
            "YAPILAMAZ (kucuk n'de sahte kesinlik riski)._\n"
        )
    else:
        top5 = trustworthy.sort_values(["profit_factor", "expectancy_r"], ascending=[False, False]).head(5)
        lines.append("\n| Sira | Yon | TF | Para Birimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % |\n")
        lines.append("|---|---|---|---|---|---|---|---|---|\n")
        for i, (_, row) in enumerate(top5.iterrows(), start=1):
            lines.append(
                f"| {i} | {row['yon']} | {row['tf']} | {row['currency']} | {int(row['n_trades'])} | "
                f"{_fmt_num(row['win_rate'])} | {_fmt_num(row['profit_factor'])} | "
                f"{_fmt_num(row['expectancy_r'], '{:.3f}')} | {_fmt_num(row['avg_max_drawdown_pct'])} |\n"
            )

    for currency in currencies:
        lines.append(f"\n## {currency} Grafigi Sonuclari\n")
        if currency == "USD":
            usd_rows = combined[combined["currency"] == "USD"]
            note = (
                usd_rows["currency_note"].iloc[0]
                if not usd_rows.empty and usd_rows["currency_note"].iloc[0]
                else (
                    "USD-payda grafiginde BAGIMSIZ tespit -- ayni sinyalin doviz-ayarli hali DEGIL: "
                    "to_usd() sonrasi detect() USD-payda serisinde YENIDEN calistirilir, pivotlar "
                    "(A/B/C/D) TL serisinden FARKLI cikabilir."
                )
            )
            lines.append(f"\n> **{note}**\n")

        for yon in ("LONG", "SHORT"):
            lines.append(f"\n### {yon}\n")
            sub = combined[(combined["currency"] == currency) & (combined["yon"] == yon)]
            lines.append(_cell_table(sub))

    lines.append("\n## Ham Veri\n")
    lines.append(f"\nTum hucrelerin ham tablosu (LONG+SHORT birlikte): `{out_csv_path}`\n")

    return "".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="AB=CD coklu-sembol/coklu-tf/coklu-para-birimi arastirma taramasi -- LONG/SHORT ayri, markdown rapor + CSV uretir.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--symbols", default=None, help="Virgullu ticker listesi (varsayilan: get_bist_universe() -- TUM BIST evreni, DB'den).")
    parser.add_argument("--tfs", default="60,120,240,1D,1W", help="Virgullu zaman dilimi listesi (varsayilan: 60,120,240,1D,1W).")
    parser.add_argument("--years", type=float, default=2.0, help="Sembol basina gecmis yil sayisi (varsayilan: 2.0).")
    parser.add_argument("--currencies", default="TRY,USD", help="Virgullu para birimi listesi (varsayilan: TRY,USD).")
    parser.add_argument("--min-trades-show", type=int, default=30, help="Bu esigin altindaki hucreler GUVENSIZ etiketlenir, ASLA gizlenmez (varsayilan: 30).")
    parser.add_argument("--min-trades-trustworthy", type=int, default=100, help="\"En verimli kosul\" iddialari icin gereken minimum islem sayisi (varsayilan: 100).")
    parser.add_argument("--out", default=str(_DEFAULT_OUT_MD), help=f"Markdown rapor cikti yolu (varsayilan: {_DEFAULT_OUT_MD}).")
    parser.add_argument("--out-csv", default=str(_DEFAULT_OUT_CSV), help=f"Ham tablo CSV cikti yolu (varsayilan: {_DEFAULT_OUT_CSV}).")
    parser.add_argument("--limit-symbols", type=int, default=None, help="TEST/dogrulama amacli: sadece ilk N sembolle calistir.")
    parser.add_argument(
        "--pivot-lookback", type=int, default=5,
        help="abcd_pattern.Params.pivot_lookback (varsayilan: 5, Pine kaynagiyla AYNI). Dusurmek "
        "onay gecikmesini azaltir (bkz. abcd_scanner.py ScannedSignal modul notu) ama pivot tespitini "
        "gurultuye acar -- bu script FARKLI degerleri KARSILASTIRMAK icin var, TEK BASINA bir tavsiye DEGIL.",
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
        f"Grid: {len(symbols)} sembol x {len(tfs)} tf x {len(currencies)} para birimi x 2 yon "
        f"(LONG+SHORT ayri backtest, ~{args.years} yil gecmis)."
    )

    if args.pivot_lookback != 5:
        print(f"UYARI: pivot_lookback={args.pivot_lookback} (Pine varsayilani 5 DEGIL) -- karsilastirma/deney kosusu.")

    print(f"[1/2] LONG grid calisiyor ({len(symbols)} sembol x {len(tfs)} tf x {len(currencies)} para birimi)...")
    long_summary, long_warning = _run_direction_grid(
        symbols, tfs, currencies, args.years, args.min_trades_show, args.min_trades_trustworthy,
        yon="LONG", detector_params=Params(enable_long=True, enable_short=False, pivot_lookback=args.pivot_lookback),
    )
    print(f"  LONG tamamlandi: {len(long_summary)} hucre uretildi.")

    print(f"[2/2] SHORT grid calisiyor ({len(symbols)} sembol x {len(tfs)} tf x {len(currencies)} para birimi)...")
    short_summary, short_warning = _run_direction_grid(
        symbols, tfs, currencies, args.years, args.min_trades_show, args.min_trades_trustworthy,
        yon="SHORT", detector_params=Params(enable_long=False, enable_short=True, pivot_lookback=args.pivot_lookback),
    )
    print(f"  SHORT tamamlandi: {len(short_summary)} hucre uretildi.")

    combined = pd.concat([long_summary, short_summary], ignore_index=True)

    out_csv_path = Path(args.out_csv)
    saved_csv = save_summary(combined, path=out_csv_path)
    print(f"Ham CSV kaydedildi: {saved_csv}")

    report_md = _build_report(
        combined, long_warning, short_warning, symbols, tfs, currencies, args.years,
        args.min_trades_show, args.min_trades_trustworthy, saved_csv,
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report_md, encoding="utf-8")
    print(f"Rapor kaydedildi: {out_path}")

    n_guvenilir = int((combined["trustworthy"] == True).sum())  # noqa: E712
    n_guvensiz = len(combined) - n_guvenilir
    print(f"Ozet: {len(combined)} hucre ({n_guvenilir} guvenilir, {n_guvensiz} guvensiz/dusuk-guven).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
