"""VRP (Variance Risk Premium) tabanli sektor rotasyonu -- tam BIST backtest
orkestrasyon scripti (2026-08-19, kullanici istegi).

Mimari -- HICBIR hesaplama mantigi TEKRAR YAZILMADI:
  - VRP/GARCH: `src/analysis/vrp.py` (SAF matematik).
  - Sektor liderligi + sepet secimi + aylik rebalance motoru:
    `src/analysis/sector_rotation_backtest.py::run_sector_rotation_backtest`.
  - Bu script SADECE veri DI (`fetch_ohlcv_abcd` fiyat + `get_bist_sector_map`
    DB) baglar ve markdown rapor uretir -- `momentum_confluence_arastirma.py`
    ile AYNI sorumluluk ayrimi.

Benchmark: XU100.IS (yfinance) -- `fetch_ohlcv_abcd("XU100", "1D", ...)`
`_yf_symbol` her BIST sembolune otomatik ".IS" ekledigi icin BASKA KOD
DEGISIKLIGI GEREKMEDEN calisir (2026-08-19 preflight ile canli dogrulandi,
bkz. konusma gecmisi -- 900 barlik XU100.IS verisi basariyla dondu).

n_bars derinligi: `lookback_years` (varsayilan 3.0) SADECE rebalance
TAKVIMININ araligini belirler (bkz. sector_rotation_backtest.py ust notu) --
ama ILK rebalance tarihinde GARCH fit'inin `_GARCH_MIN_OBS=250` barlik
gecmise ihtiyaci var, bu yuzden fiyat gecmisi rebalance araliginin
BASINDAN once de uzanmali. Varsayilan `n_bars=1400` (~5.5 is-yili) bu
payi rahat karsilar; sembol daha kisa islem goruyorsa (yeni halka arz)
o sembol icin erken aylarda VRP snapshot'i None doner, sepet DISINDA
kalir (fiktif veri ICAT EDILMEZ, bkz. vrp.py/sector_rotation_backtest.py
ust notlari) -- FIRLATMAZ.

Kullanim:
    python scripts/vrp_sektor_rotasyon_arastirma.py --limit-symbols 40  # pilot
    python scripts/vrp_sektor_rotasyon_arastirma.py                     # TAM BIST evreni
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402
from src.analysis.sector_rotation_backtest import (  # noqa: E402
    MonthlyResult,
    SectorRotationParams,
    get_bist_sector_map,
    run_sector_rotation_backtest,
)
from src.fetchers.abcd_data import fetch_ohlcv_abcd  # noqa: E402

config.setup_logging()

_DEFAULT_OUT_MD = BASE_DIR / "docs" / "spec" / "VRP_SEKTOR_ROTASYON_BACKTEST.md"
_DEFAULT_OUT_CSV = config.DATA_DIR / "abcd_cache" / "vrp_sektor_rotasyon_aylik.csv"
_DEFAULT_N_BARS = 1400  # bkz. modul ust notu -- 3y rebalance araligi + 500g GARCH payi


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--limit-symbols", type=int, default=None, help="Pilot icin evreni kisitla (orn. 40)")
    p.add_argument("--n-bars", type=int, default=_DEFAULT_N_BARS)
    p.add_argument("--benchmark", type=str, default="XU100")
    p.add_argument("--lookback-years", type=float, default=3.0)
    p.add_argument("--n-leading-sectors", type=int, default=2)
    p.add_argument("--basket-size", type=int, default=5)
    p.add_argument("--min-sector-members", type=int, default=5)
    p.add_argument("--sector-momentum-window", type=int, default=21)
    p.add_argument("--out-md", type=Path, default=_DEFAULT_OUT_MD)
    p.add_argument("--out-csv", type=Path, default=_DEFAULT_OUT_CSV)
    return p.parse_args()


def _monthly_metrics(results: list[MonthlyResult]) -> dict:
    """Aylik `MonthlyResult` listesinden portfoy-seviyesi ozet istatistikler
    (`abcd_backtest.compute_metrics` ile AYNI ruhta ama trade DEGIL, aylik
    getiri serisi bazli -- bu motor icin ozel, tek noktalık formul yeterli
    oldugundan ayri bir modul cikarilmadi)."""
    if not results:
        return {}

    port_rets = np.array([r.basket_return_pct for r in results]) / 100.0
    bench_rets = np.array([r.benchmark_return_pct for r in results]) / 100.0
    alphas = np.array([r.alpha_pct for r in results])
    n_months = len(results)
    n_empty_basket = sum(1 for r in results if r.n_realized == 0)

    port_equity = results[-1].portfolio_equity
    bench_equity = results[-1].benchmark_equity

    port_curve = np.concatenate([[1.0], np.cumprod(1.0 + port_rets)])
    bench_curve = np.concatenate([[1.0], np.cumprod(1.0 + bench_rets)])
    port_dd = float(((port_curve - np.maximum.accumulate(port_curve)) / np.maximum.accumulate(port_curve)).min() * 100.0)
    bench_dd = float(((bench_curve - np.maximum.accumulate(bench_curve)) / np.maximum.accumulate(bench_curve)).min() * 100.0)

    years = n_months / 12.0
    port_cagr = float((port_equity ** (1.0 / years) - 1.0) * 100.0) if years > 0 and port_equity > 0 else float("nan")
    bench_cagr = float((bench_equity ** (1.0 / years) - 1.0) * 100.0) if years > 0 and bench_equity > 0 else float("nan")

    monthly_sharpe = float(np.mean(port_rets) / np.std(port_rets, ddof=1) * np.sqrt(12)) if np.std(port_rets, ddof=1) > 0 else float("nan")

    top3 = sorted(results, key=lambda r: r.alpha_pct, reverse=True)[:3]
    top3_alpha_sum = sum(r.alpha_pct for r in top3)
    total_alpha_sum = sum(alphas)
    top3_alpha_share_pct = float(top3_alpha_sum / total_alpha_sum * 100.0) if total_alpha_sum != 0 else float("nan")

    return {
        "n_months": n_months,
        "n_empty_basket": n_empty_basket,
        "port_total_return_pct": (port_equity - 1.0) * 100.0,
        "bench_total_return_pct": (bench_equity - 1.0) * 100.0,
        "port_cagr_pct": port_cagr,
        "bench_cagr_pct": bench_cagr,
        "port_max_dd_pct": port_dd,
        "bench_max_dd_pct": bench_dd,
        "monthly_sharpe": monthly_sharpe,
        "win_rate_vs_bench_pct": float(np.mean(alphas > 0) * 100.0),
        "avg_alpha_pct": float(np.mean(alphas)),
        "median_alpha_pct": float(np.median(alphas)),
        "top3_months": [(r.period_start.strftime("%Y-%m"), r.alpha_pct) for r in top3],
        "top3_alpha_share_pct": top3_alpha_share_pct,
    }


def _format_report(
    results: list[MonthlyResult],
    metrics: dict,
    symbols_used: int,
    sectors_used: int,
    params: SectorRotationParams,
    benchmark: str,
    generated_at: str,
    out_csv: Path,
) -> str:
    lines = [
        "# VRP Sektor Rotasyonu -- Tam BIST Backtest",
        "",
        f"Olusturulma: {generated_at}",
        "",
        "## Kapsam",
        "",
        f"Sembol sayisi: {symbols_used} · Sektor sayisi: {sectors_used} · Backtest derinligi: {params.lookback_years:.1f} yil · "
        f"Benchmark: {benchmark}.IS · Lider sektor sayisi: {params.n_leading_sectors} · Sepet buyuklugu: {params.basket_size} · "
        f"Min sektor uyesi: {params.min_sector_members} · Komisyon: %{params.commission_pct * 100:.2f}/fill",
        "",
        "## ⚠️ Yontem sinirlamalari (bkz. `src/analysis/vrp.py` modul ust notu)",
        "",
        "IV, gercek piyasa-fiyatli implied volatilite DEGIL -- kendi GARCH(1,1) ileri-tahmin PROXY'miz "
        "(kullanici karari, 2026-08-19: paylasilan quant'in tam formulu/veri kaynagi elde YOK). "
        "VRP = IV_proxy - RV (ham fark, oran DEGIL).",
        "",
    ]

    if not results:
        lines.append("**Backtest hic sonuc URETMEDI** -- rebalance takvimi < 2 tarih veya fiyat verisi yetersiz.")
        return "\n".join(lines)

    if metrics["n_empty_basket"] > 0:
        lines.append(
            f"⚠️ **{metrics['n_empty_basket']}/{metrics['n_months']} ayda sepet TAMAMEN BOS kaldi** "
            "(VRP<0 sartini gecen aday bulunamadi) -- o aylarda portfoy getirisi 0 kabul edildi, "
            "GIZLENMEDI (bkz. asagidaki aylik tablo `n_realized=0` satirlari)."
        )
        lines.append("")

    top3_str = ", ".join(f"{m} ({a:+.1f})" for m, a in metrics["top3_months"])
    lines += [
        "## Yorum -- dikkat edilmesi gereken noktalar",
        "",
        f"- **Kucuk orneklem**: N={metrics['n_months']} ay (3 yil). Tek bir piyasa rejimi (2023-2026 BIST boga "
        "donemi agirlikli) -- farkli rejimlerde (uzun ayi, yuksek faiz) test EDILMEDI.",
        f"- **Ortalama/medyan ayrismasi**: ortalama alpha {metrics['avg_alpha_pct']:+.2f} puan/ay ama MEDYAN "
        f"{metrics['median_alpha_pct']:+.2f} puan/ay -- yani TIPIK bir ay benchmark'i YENMIYOR, sonuc birkac "
        f"asiri buyuk ayin (en iyi 3 ay: {top3_str}) toplam alpha'nin %{metrics['top3_alpha_share_pct']:.0f}'ini "
        "tasimasindan geliyor. Kazanma orani zaten %50'nin ALTINDA "
        f"(%{metrics['win_rate_vs_bench_pct']:.1f}).",
        f"- **Drawdown sepette benchmark'tan KOTU** ({metrics['port_max_dd_pct']:.1f}% vs {metrics['bench_max_dd_pct']:.1f}%) "
        "-- yuksek getiri, daha yuksek oynaklik/kayip riskiyle GELIYOR, ucretsiz DEGIL.",
        "- **Bos sepet aylarinda %0 getiri varsayimi**: gercekte nakit/repo getirisi olurdu, bu basitlestirme "
        "portfoyu (ve dolayisiyla benchmark karsilastirmasini) fiilen kotumser yonde ETKILER (nakit getirisi "
        "eklenseydi sepet sonucu biraz DAHA IYI gorunurdu).",
        "",
        "## Ozet Sonuclar",
        "",
        "| Metrik | VRP Sepet | Benchmark |",
        "|---|---|---|",
        f"| Toplam getiri % | {metrics['port_total_return_pct']:.1f} | {metrics['bench_total_return_pct']:.1f} |",
        f"| CAGR % | {metrics['port_cagr_pct']:.1f} | {metrics['bench_cagr_pct']:.1f} |",
        f"| Maks. Drawdown % | {metrics['port_max_dd_pct']:.1f} | {metrics['bench_max_dd_pct']:.1f} |",
        f"| Aylik Sharpe (yillıklandirilmis) | {metrics['monthly_sharpe']:.2f} | -- |",
        f"| Benchmark'i yendigi ay orani % | {metrics['win_rate_vs_bench_pct']:.1f} | -- |",
        f"| Ort. aylik alpha (puan) | {metrics['avg_alpha_pct']:.2f} | -- |",
        f"| Medyan aylik alpha (puan) | {metrics['median_alpha_pct']:.2f} | -- |",
        f"| Ay sayisi | {metrics['n_months']} | -- |",
        "",
        "## Aylik Detay",
        "",
        "| Donem | Lider Sektorler | Sepet (n_gerceklesen) | Sepet % | Bench % | Alpha (puan) |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        period = r.period_start.strftime("%Y-%m")
        leading = ", ".join(r.leading_sectors) if r.leading_sectors else "(yok)"
        basket = ", ".join(r.basket) if r.basket else "(bos)"
        lines.append(
            f"| {period} | {leading} | {basket} ({r.n_realized}) | {r.basket_return_pct:.2f} | "
            f"{r.benchmark_return_pct:.2f} | {r.alpha_pct:+.2f} |"
        )

    lines += ["", "## Ham Veri", "", f"Aylik CSV: `{out_csv}`"]
    return "\n".join(lines)


def main() -> None:
    args = _parse_args()

    sector_map = get_bist_sector_map()
    symbols = sorted(sector_map.keys())
    if args.limit_symbols:
        symbols = symbols[: args.limit_symbols]
        sector_map = {s: sector_map[s] for s in symbols}

    print(f"[1/3] {len(symbols)} sembol icin fiyat gecmisi cekiliyor (n_bars={args.n_bars})...")
    price_fetcher = lambda symbol: fetch_ohlcv_abcd(symbol, "1D", n_bars=args.n_bars)  # noqa: E731

    benchmark_df = fetch_ohlcv_abcd(args.benchmark, "1D", n_bars=args.n_bars)
    if benchmark_df.empty:
        print(f"HATA: benchmark {args.benchmark}.IS icin veri gelmedi, durduruluyor.")
        return

    params = SectorRotationParams(
        n_leading_sectors=args.n_leading_sectors,
        sector_momentum_window=args.sector_momentum_window,
        min_sector_members=args.min_sector_members,
        basket_size=args.basket_size,
        lookback_years=args.lookback_years,
    )

    print("[2/3] aylik rebalance backtesti calistiriliyor (bu adim en uzun surer)...")
    results = run_sector_rotation_backtest(symbols, sector_map, benchmark_df, price_fetcher, params)
    metrics = _monthly_metrics(results)

    print("[3/3] rapor yaziliyor...")
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report = _format_report(
        results, metrics, len(symbols), len(set(sector_map.values())), params, args.benchmark, generated_at, args.out_csv
    )

    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(report, encoding="utf-8")
    print(f"Rapor yazildi: {args.out_md}")

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    if results:
        pd.DataFrame(
            [
                {
                    "period_start": r.period_start,
                    "period_end": r.period_end,
                    "leading_sectors": ";".join(r.leading_sectors),
                    "basket": ";".join(r.basket),
                    "n_realized": r.n_realized,
                    "basket_return_pct": r.basket_return_pct,
                    "benchmark_return_pct": r.benchmark_return_pct,
                    "alpha_pct": r.alpha_pct,
                    "portfolio_equity": r.portfolio_equity,
                    "benchmark_equity": r.benchmark_equity,
                }
                for r in results
            ]
        ).to_csv(args.out_csv, index=False)
        print(f"CSV yazildi: {args.out_csv}")

    if metrics:
        print(
            f"\nOzet: toplam getiri sepet={metrics['port_total_return_pct']:.1f}% vs "
            f"benchmark={metrics['bench_total_return_pct']:.1f}% | "
            f"alpha ort={metrics['avg_alpha_pct']:+.2f} puan/ay | "
            f"kazanma orani={metrics['win_rate_vs_bench_pct']:.1f}%"
        )


if __name__ == "__main__":
    main()
