"""Buyuk Yukselis Onculu Analizi -- tam BIST arastirmasi.

Kullanici istegi (2026-08-20): "Wavelet Trend Rider'i filtreleye filtreleye
sinyal sayisini cok azalttik, buyuk yukselislerin cogunu KACIRIYORUZ --
bunun YERINE GERCEK buyuk yukselisleri BULUP, o yukselislerin BASLADIGI
noktalarda hangi teknik kosullar/degerler ORTAK oldugunu (altin oran dahil)
ISTATISTIKSEL olarak KESFEDELIM, elimizdeki TUM strateji/kosullardan
faydalanarak."

Mimari: `src/analysis/rally_precursor.py` (aday toplama + ozellik cikarimi)
+ `abcd_factor_analysis.run_factor_analysis` (kronolojik split/FDR/holdout/
lojistik regresyon motoru, DOGRUDAN REUSE -- hesaplama mantigi IKI YERDE
YASAMASIN ilkesi). Etiket: `rally_pct >= --rally-threshold` (varsayilan
%25) ise 1 (BUYUK yukselisin baslangici), degilse 0.

Kullanim:
    python scripts/rally_precursor_arastirma.py --limit-symbols 40  # pilot
    python scripts/rally_precursor_arastirma.py                     # TAM BIST
"""

from __future__ import annotations

import argparse
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402
from src.analysis import rally_precursor as rp  # noqa: E402
from src.analysis.abcd_factor_analysis import format_report, run_factor_analysis  # noqa: E402
from src.analysis.abcd_scanner import get_bist_universe  # noqa: E402
from src.fetchers.abcd_data import fetch_ohlcv_abcd  # noqa: E402

config.setup_logging()

_DEFAULT_OUT_MD = BASE_DIR / "docs" / "spec" / "RALLY_PRECURSOR_ARASTIRMASI.md"
_DEFAULT_OUT_CSV = config.DATA_DIR / "abcd_cache" / "rally_precursor_candidates.csv"
_N_BARS = 2000  # ~8 yil 1D -- coklu piyasa rejimi kapsasin diye BILEREK derin
_METHODOLOGY_NOTE = (
    "Butun bulgular ILISKISELDIR, NEDENSELLIK iddia edilmez -- 'X kosulu yukselise SEBEP OLUR/"
    "GARANTI EDER' turu ifadeler YASAKTIR; sadece 'buyuk yukselisle baslayan dipler ile "
    "baslamayanlar arasinda X ozelliginde ISTATISTIKSEL FARK var (n=.., p=.., FDR q=.., "
    "holdout: dogrulandi/dogrulanmadi)' turu ifadeler kullanilir. Etiket = dipten sonraki "
    "N barda ulasilan en yuksek fiyatin dip'e gore yuzde artisi >= esik mi (gelecek verisi "
    "SADECE etikette kullanilir, ozellik cikariminda ASLA -- bkz. rally_precursor.py ust notu)."
)


def _fmt(value, spec: str = "{:.3f}") -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    return spec.format(value)


def _fib_zone(retr: float) -> str:
    if retr < 0.382:
        return "0.000-0.382"
    if retr < 0.5:
        return "0.382-0.500"
    if retr < 0.618:
        return "0.500-0.618"
    if retr < 0.786:
        return "0.618-0.786"
    if retr <= 1.0:
        return "0.786-1.000"
    return ">1.000 (X asildi)"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit-symbols", type=int, default=None)
    parser.add_argument("--rally-threshold", type=float, default=25.0, help="Buyuk yukselis esigi (yuzde).")
    parser.add_argument("--pivot-lookback", type=int, default=10)
    parser.add_argument("--max-lookahead-bars", type=int, default=120)
    parser.add_argument("--n-bars", type=int, default=_N_BARS)
    parser.add_argument("--out", default=str(_DEFAULT_OUT_MD))
    parser.add_argument("--out-csv", default=str(_DEFAULT_OUT_CSV))
    args = parser.parse_args(argv)

    symbols = get_bist_universe()
    if args.limit_symbols is not None:
        symbols = symbols[: args.limit_symbols]
    total = len(symbols)
    print(f"{total} sembol -- pivot_lookback={args.pivot_lookback}, max_lookahead={args.max_lookahead_bars} bar, esik=%{args.rally_threshold}")

    all_rows: list[dict] = []
    ohlcv_cache: dict[tuple[str, str], pd.DataFrame] = {}

    for done, symbol in enumerate(symbols, start=1):
        if done % 50 == 0:
            print(f"  ... {done}/{total} sembol islendi, su ana kadar {len(all_rows)} aday")
        df = fetch_ohlcv_abcd(symbol, "1D", args.n_bars)
        if df.empty or len(df) < 300:
            continue
        candidates = rp.find_rally_candidates(
            df, symbol, "1D", currency="TRY",
            pivot_lookback=args.pivot_lookback, max_lookahead_bars=args.max_lookahead_bars,
        )
        if not candidates:
            continue
        ohlcv_cache[(symbol, "1D")] = df
        for c in candidates:
            row = c.__dict__.copy()
            row["entry_time"] = c.signal_time
            all_rows.append(row)

    print(f"Toplam {len(all_rows)} aday toplandi. Ozellik cikarimi + istatistik analiz basliyor...")
    trades_df = pd.DataFrame(all_rows)

    if trades_df.empty:
        print("HATA: hic aday bulunamadi.")
        return 1

    label_fn = lambda row: 1 if row["rally_pct"] >= args.rally_threshold else 0  # noqa: E731

    result = run_factor_analysis(
        trades_df, ohlcv_cache,
        label_fn=label_fn,
        methodology_note=_METHODOLOGY_NOTE,
        feature_names=rp.ALL_FEATURES,
        categorical_features=rp.CATEGORICAL_FEATURES,
        extract_features_fn=rp.extract_features,
    )

    print(f"Analiz tamamlandi: n_total={result['n_total']}, n_skipped={result.get('n_skipped')}")

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    trades_df.to_csv(out_csv, index=False)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    n_rally = int((trades_df["rally_pct"] >= args.rally_threshold).sum())
    n_total_candidates = len(trades_df)
    base_rate = n_rally / n_total_candidates * 100.0 if n_total_candidates else float("nan")

    lines = [
        "# Buyuk Yukselis Onculu Analizi -- Tam BIST Arastirmasi\n",
        f"\nOlusturulma: {now}\n",
        "\n## Kapsam\n",
        f"\nSembol: {total} · Derinlik: ~{args.n_bars} bar (1D, ~8 yil) · Pivot lookback: {args.pivot_lookback} · "
        f"Ileri-bakis penceresi: {args.max_lookahead_bars} bar · Buyuk yukselis esigi: %{args.rally_threshold}\n",
        f"\n- Toplam aday (pivot dip): {n_total_candidates}\n",
        f"- Bunlardan BUYUK yukselisle baslayan (>=%{args.rally_threshold}): {n_rally} (taban oran: %{base_rate:.1f})\n",
        "\n## Motivasyon\n",
        "\nOnceki yaklasim (Wavelet Trend Rider ablasyonu) DISARIDAN gelen bir stratejiyi FILTRELEYEREK "
        "sinyal kalitesini artirmaya calisti -- sonuc COK AZ sinyal, BUYUK yukselislerin cogu KACIRILDI. "
        "Bu arastirma TERSTEN gider: GERCEK buyuk yukselisleri (pivot dip -> sonraki N barda ulasilan "
        "en yuksek fiyat) objektif olarak BULUR, o dip anindaki (VE ONCESINDEKI, causal) teknik kosullari "
        "olcer, BUYUK yukselisle baslayanlarla BASLAMAYANLARI karsilastirir.\n",
    ]

    # Fibonacci bolge tablosu -- "altin oran" sorusuna DOGRUDAN, sezgisel cevap.
    def _zone_for_row(r: pd.Series) -> str:
        ph, pl, lp = r.get("prior_high_price"), r.get("prior_low_price"), r.get("low_price")
        if pd.isna(ph) or pd.isna(pl) or pd.isna(lp):
            return "N/A (onceki bacak yok)"
        leg = float(ph) - float(pl)
        if leg <= 0:
            return "N/A (onceki bacak yok)"
        return _fib_zone((float(ph) - float(lp)) / leg)

    trades_df["_fib_zone"] = trades_df.apply(_zone_for_row, axis=1)
    trades_df["_is_rally"] = trades_df["rally_pct"] >= args.rally_threshold

    lines.append("\n## Fibonacci Geri-Cekilme Bolgesi -- \"Altin Oran\" Sorusuna Dogrudan Cevap\n")
    lines.append("\nHer dip, ONCEKI yukselis bacaginin (prior_low->prior_high) hangi Fibonacci bolgesinde olustu -- o bolgede BUYUK yukselis baslama orani ne?\n")
    lines.append("\n| Fibonacci Bolgesi | n | Buyuk Yukselis Orani % |\n|---|---|---|\n")
    zone_order = ["0.000-0.382", "0.382-0.500", "0.500-0.618", "0.618-0.786", "0.786-1.000", ">1.000 (X asildi)", "N/A (onceki bacak yok)"]
    for zone in zone_order:
        sub = trades_df[trades_df["_fib_zone"] == zone]
        if len(sub) == 0:
            continue
        rate = sub["_is_rally"].mean() * 100.0
        lines.append(f"| {zone} | {len(sub)} | {rate:.1f} |\n")

    lines.append("\n## Istatistiksel Faktor Analizi (kronolojik split/FDR/holdout -- abcd_factor_analysis.py motoru)\n")
    report_body = format_report(result)
    # format_report basligini ("# AB=CD Basari Faktoru Analizi") bu baglama uyarlamak icin ilk satiri atla.
    report_body_lines = report_body.split("\n")[1:]
    lines.append("\n" + "\n".join(report_body_lines))

    lines.append(f"\n\n## Ham Veri\n\nHer aday + ozellikler: `{out_csv}`\n")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"Rapor: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
