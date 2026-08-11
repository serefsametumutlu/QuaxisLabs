"""Faz 3a kalibrasyon scripti (bkz. docs/spec/quant_denetim_01.md, GÖREV 2).

SADECE OKUR: `data/bilanco_radar.db`'deki (config.DATABASE_URL) MEVCUT
`FinancialPeriod` verisinden 5 mercek spec'inde (spec_mercek_deger.md,
spec_mercek_kalite.md, spec_mercek_buyume.md, spec_mercek_guvenlik.md,
spec_bilesik_skor.md) önerilen ham metrik dağılımlarını, önerilen
eşik/bantların gerçek evrende kaç şirketi hangi banda düşürdüğünü ve
sektör n<5 durumunu raporlar. DB'ye HİÇBİR YAZMA yapmaz (session sadece
`select`, hiçbir yerde `session.commit()`/`add()` çağrılmaz) -- idempotent,
tekrar tekrar çalıştırılabilir, aynı DB anlık görüntüsünden hep aynı
sonucu üretir.

Kapsam notu (dürüstlük ilkesi -- persona "Görmediğin veriye güvenme"):
`Company` tablosunda Faz 2'nin sektör/evren taraması sayesinde 643 BİST +
~4350 NASDAQ satırı var, AMA bunların SADECE bir alt kümesinde gerçek mali
tablo verisi (`FinancialPeriod`) mevcut -- her ticker SADECE bir kullanıcı
onu sorguladığında (veya bir demo/test script'i çalıştırdığında) taranır,
TOPLU bir doldurma süreci YOKTUR (bkz. valuation.py modül üst notu, AYNI
uyarı). Bu script o GERÇEK alt kümeyi (bu satırların yazıldığı anda 180
BİST + 22 NASDAQ) dürüstçe raporlar -- "evrenin TAMAMI" gibi bir iddia
YAPILMAZ.

Fiyat (F/K, PD/DD, FD/FAVÖK gibi çarpanlar için gerekli) HİÇBİR DB
tablosunda SAKLANMAZ (canlı çekilir, bkz. calculator.compute_valuation).
`--with-price` bayrağı verilirse SADECE BİST tickerları için
`isyatirim.fetch_latest_price()` ile CANLI fiyat çekilir (NASDAQ atlanır --
runtime/ayrı-fetcher-bağımlılığı nedeniyle bu koşunun kapsamı dışında
tutuldu, bu AÇIKÇA raporlanır). Bayrak verilmezse F/K/PD/DD bölümü
"çalıştırılmadı" notuyla atlanır -- script YİNE DE hatasız biter (fiyatsız
metrikler -- ROE/marj/kaldıraç/büyüme -- TAM raporlanır).

Kullanım:
    python scripts/kalibrasyon_v2.py                 # fiyatsız (hızlı, ağsız)
    python scripts/kalibrasyon_v2.py --with-price     # + BİST F/K/PD/DD (yavaş, ağa bağımlı)
    python scripts/kalibrasyon_v2.py --with-price --limit 30   # test için kısıtlı
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from src.analysis import calculator, scorer
from src.db import repository
from src.db.models import Company, FinancialPeriod, default_engine

# --- Genel yardımcılar -----------------------------------------------------


def _to_float(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _percentile(sorted_values: list[float], pct: float) -> float:
    """Doğrusal enterpolasyonlu persentil (numpy'siz, saf python).

    n=1 ise tek değeri döner; pct [0,100] aralığında olmalı.
    """
    if not sorted_values:
        raise ValueError("bos liste")
    if len(sorted_values) == 1:
        return sorted_values[0]
    k = (pct / 100) * (len(sorted_values) - 1)
    lo = int(k)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = k - lo
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * frac


def _dist_line(label: str, raw_values: list[float | None]) -> str:
    values = sorted(v for v in raw_values if v is not None)
    n = len(values)
    n_missing = len(raw_values) - n
    if n == 0:
        return f"  {label}: n=0 (veri yok, {n_missing} eksik)"
    stats = {
        "min": values[0],
        "p10": _percentile(values, 10),
        "p25": _percentile(values, 25),
        "medyan": _percentile(values, 50),
        "p75": _percentile(values, 75),
        "p90": _percentile(values, 90),
        "max": values[-1],
    }
    stats_str = " / ".join(f"{k}={v:,.2f}" for k, v in stats.items())
    return f"  {label}: n={n} (eksik={n_missing}) -- {stats_str}"


def _band_count(label: str, raw_values: list[float | None], bands: list[tuple[str, float | None, float | None]]) -> str:
    """bands: (etiket, alt_sinir_dahil_degil, ust_sinir_dahil) ucluleri --
    None sinirsiz demektir. Deger sirayla ILK eslesen banda dusurulur."""
    values = [v for v in raw_values if v is not None]
    n = len(values)
    lines = [f"  {label} (n={n}):"]
    for band_label, lo, hi in bands:
        count = sum(1 for v in values if (lo is None or v >= lo) and (hi is None or v < hi))
        pct = (count / n * 100) if n else 0.0
        lines.append(f"    {band_label}: {count} sirket (%{pct:.1f})")
    return "\n".join(lines)


# --- DB'den ham veri toplama -----------------------------------------------------


@dataclass
class TickerBundle:
    ticker: str
    market: str
    financial_group: str | None
    ust_sektor: str | None
    sirket_turu: str | None
    analysis: object | None = None
    price: Decimal | None = None
    share_field_value: Decimal | None = None
    valuation: object | None = None


def _load_company_meta(session) -> dict[str, Company]:
    rows = session.execute(select(Company)).scalars().all()
    return {c.ticker: c for c in rows}


def _tickers_with_financials(session) -> list[str]:
    rows = session.execute(select(FinancialPeriod.ticker).distinct()).scalars().all()
    return sorted(rows)


def _build_bundle(session, ticker: str, company: Company | None) -> TickerBundle:
    fg = company.financial_group if company else None
    market = company.market if company else "BIST"
    bundle = TickerBundle(
        ticker=ticker,
        market=market,
        financial_group=fg,
        ust_sektor=company.ust_sektor if company else None,
        sirket_turu=company.sirket_turu if company else None,
    )
    financials_by_period = repository.get_financials(session, ticker, n_periods=8)
    if not financials_by_period:
        return bundle
    try:
        if fg == "US_GAAP":
            bundle.analysis = calculator.analyze_us(ticker, financials_by_period)
            bundle.share_field_value = financials_by_period.get(bundle.analysis.latest_period, {}).get("shares_outstanding")
        elif fg in ("UFRS", "UFRS_KATILIM"):
            variant = "participation" if fg == "UFRS_KATILIM" else "conventional"
            bundle.analysis = calculator.analyze_bank(ticker, financials_by_period, bank_variant=variant)
        elif fg == "UFRS_K":
            bundle.analysis = calculator.analyze_insurance(ticker, financials_by_period)
        elif fg == "XI_29K":
            bundle.analysis = calculator.analyze_financing(ticker, financials_by_period)
        else:  # XI_29 (varsayilan) VEYA financial_group hic bilinmiyor -- sanayi varsay
            bundle.analysis = calculator.analyze(ticker, financials_by_period)
            bundle.share_field_value = financials_by_period.get(bundle.analysis.latest_period, {}).get("share_capital")
    except Exception as exc:  # kalibrasyon scripti -- tek bir bozuk ticker tum kosuyu DUSURMEMELI
        print(f"  [uyari] {ticker}: analiz basarisiz ({exc!r}), atlaniyor.")
    return bundle


def _maybe_fetch_price(bundle: TickerBundle) -> None:
    """SADECE BIST (XI_29/sanayi) icin -- bkz. modul ust notu kapsam siniri."""
    if bundle.market != "BIST" or bundle.financial_group not in (None, "XI_29"):
        return
    if bundle.analysis is None or bundle.share_field_value is None:
        return
    from src.fetchers import isyatirim

    try:
        bundle.price = isyatirim.fetch_latest_price(bundle.ticker)
    except Exception:
        bundle.price = None
    if bundle.price is not None:
        bundle.valuation = calculator.compute_valuation(bundle.analysis, bundle.price, bundle.share_field_value)


# --- Rapor bolumleri -----------------------------------------------------


def report_sector_universe(session) -> None:
    print("\n## 1. Sektor evreni: TOPLAM Company kaydi vs GERCEK mali veri (n)\n")
    print("(persona notu: 'BIST Saglik/Enerji sektorunde n=4' iddiasinin canli dogrulamasi)\n")

    rows_total = session.execute(
        select(Company.market, Company.ust_sektor, Company.sirket_turu, Company.ticker)
    ).all()
    rows_analyzed = session.execute(
        select(Company.market, Company.ust_sektor, Company.sirket_turu, Company.ticker)
        .join(FinancialPeriod, FinancialPeriod.ticker == Company.ticker)
        .distinct()
    ).all()

    def _grouped(rows):
        out: dict[tuple[str, str, str], set[str]] = {}
        for market, ust, turu, ticker in rows:
            key = (market, ust or "N/A", turu or "N/A")
            out.setdefault(key, set()).add(ticker)
        return out

    total_g = _grouped(rows_total)
    analyzed_g = _grouped(rows_analyzed)

    print(f"{'Piyasa':<8}{'Ust-sektor':<28}{'Sirket turu':<14}{'Toplam evren':<14}{'Analiz edilmis (n)':<20}{'n<5 mi?'}")
    for key in sorted(total_g, key=lambda k: -len(total_g[k])):
        market, ust, turu = key
        total_n = len(total_g[key])
        analyzed_n = len(analyzed_g.get(key, set()))
        flag = "EVET (sektor-goreli DEVRE DISI)" if analyzed_n < 5 else "hayir"
        print(f"{market:<8}{ust:<28}{turu:<14}{total_n:<14}{analyzed_n:<20}{flag}")


def report_raw_metric_distributions(bundles: list[TickerBundle]) -> None:
    print("\n## 2. Ham metrik dagilimlari (fiyat GEREKTIRMEYEN, DB-only)\n")

    def _sanayi_like(b: TickerBundle) -> bool:
        return b.financial_group in (None, "XI_29", "US_GAAP") and b.analysis is not None

    sanayi_bist = [b for b in bundles if _sanayi_like(b) and b.market == "BIST"]
    sanayi_us = [b for b in bundles if _sanayi_like(b) and b.market == "NASDAQ"]

    for label, group in (("BIST sanayi (XI_29)", sanayi_bist), ("NASDAQ sanayi (US_GAAP)", sanayi_us)):
        print(f"\n### {label} (n={len(group)})\n")
        r = [b.analysis.ratios for b in group]
        print(_dist_line("ROE (yillik., %)", [_to_float(x.roe_annualized) for x in r]))
        print(_dist_line("Cari oran", [_to_float(x.current_ratio) for x in r]))
        print(_dist_line("Borc/Ozkaynak (dar, finansal borc)", [_to_float(x.debt_to_equity) for x in r]))
        print(_dist_line("Net Borc/FAVOK (x)", [_to_float(x.net_debt_to_ebitda) for x in r]))
        print(_dist_line("FAVOK marji (%)", [_to_float(x.ebitda_margin_current) for x in r]))
        print(_dist_line("Brut kar marji (%)", [_to_float(x.gross_margin_current) for x in r]))
        print(_dist_line("Net marj (%)", [_to_float(x.net_margin_current) for x in r]))
        print(_dist_line("Hasilat YoY buyume (%, nominal)", [_to_float(x.revenue_growth_yoy_pct) for x in r]))

        # ROA (YENI, kalite spec) -- ham veriden turetilir (calculator.Ratios'ta YOK)
        roa_values: list[float | None] = []
        toplam_yukumluluk_ozkaynak: list[float | None] = []
        ncav_negatif_sayisi = 0
        ncav_toplam = 0
        for b in group:
            bs = b.analysis.balance_sheet
            total_assets = bs.total_assets.current
            equity = bs.equity.current
            ttm_ni = b.analysis.ratios.ttm_net_income
            if total_assets and total_assets != 0 and ttm_ni is not None:
                roa_values.append(_to_float(ttm_ni / total_assets * 100))
            else:
                roa_values.append(None)
            if equity is not None and equity != 0 and total_assets is not None:
                total_liab = total_assets - equity
                if equity > 0:
                    toplam_yukumluluk_ozkaynak.append(_to_float(total_liab / equity))
                else:
                    # K3 bulgusunun canli kaniti: negatif ozkaynakta oran negatife doner
                    toplam_yukumluluk_ozkaynak.append(_to_float(total_liab / equity))
            else:
                toplam_yukumluluk_ozkaynak.append(None)
            current_assets = bs.current_assets.current
            if current_assets is not None and total_assets is not None and equity is not None:
                total_liab = total_assets - equity
                net_isletme_sermayesi = current_assets - total_liab
                ncav_toplam += 1
                if net_isletme_sermayesi <= 0:
                    ncav_negatif_sayisi += 1

        print(_dist_line("ROA (YENI, TTM net kar/toplam varlik, %)", roa_values))
        print(_dist_line("Toplam Yukumluluk/Ozkaynak (genis tanim, x)", toplam_yukumluluk_ozkaynak))
        if ncav_toplam:
            print(
                f"  NCAV/net-net K2 riski: {ncav_negatif_sayisi}/{ncav_toplam} sirket "
                f"(%{ncav_negatif_sayisi / ncav_toplam * 100:.1f}) net isletme sermayesi <= 0 "
                f"-- net_net_iskonto_pct formulu bu sirketlerde PATLAR/isareti ters doner (bkz. K2)."
            )
        equity_negatif = sum(1 for b in group if (b.analysis.balance_sheet.equity.current or 0) < 0)
        print(f"  Negatif ozkaynakli sirket sayisi: {equity_negatif}/{len(group)} (K3 riskinin canli olcegi)")


def report_threshold_bands(bundles: list[TickerBundle]) -> None:
    print("\n## 3. Spec'lerde onerilen bant/esiklerin gercek evrende dagilimi\n")

    def _sanayi_like(b: TickerBundle, market: str) -> bool:
        return b.analysis is not None and b.market == market and b.financial_group in (None, "XI_29", "US_GAAP")

    bist = [b for b in bundles if _sanayi_like(b, "BIST")]
    nasdaq = [b for b in bundles if _sanayi_like(b, "NASDAQ")]

    print("\n### FAVOK marji bandi (spec_mercek_kalite.md, Nakit Uretimi -- ayni bant iki sablonda da)\n")
    favok_bands = [("dusuk (<10)", None, 10.0), ("orta (10-20)", 10.0, 20.0), ("guclu (>=20)", 20.0, None)]
    print(_band_count("BIST sanayi", [_to_float(b.analysis.ratios.ebitda_margin_current) for b in bist], favok_bands))
    print(_band_count("NASDAQ sanayi", [_to_float(b.analysis.ratios.ebitda_margin_current) for b in nasdaq], favok_bands))

    print("\n### ROE bandi (spec_mercek_kalite.md, Ozkaynak Karliligi)\n")
    roe_bands = [("zayif (<10)", None, 10.0), ("orta (10-15)", 10.0, 15.0), ("guclu (>=15)", 15.0, None)]
    print(_band_count("BIST sanayi", [_to_float(b.analysis.ratios.roe_annualized) for b in bist], roe_bands))
    print(_band_count("NASDAQ sanayi", [_to_float(b.analysis.ratios.roe_annualized) for b in nasdaq], roe_bands))

    print("\n### Kaldirac (Net Borc/FAVOK) bandi (spec_mercek_guvenlik.md)\n")
    kaldirac_bands = [
        ("cok iyi (<1)", None, 1.0),
        ("iyi (1-2.5)", 1.0, 2.5),
        ("orta (2.5-4)", 2.5, 4.0),
        ("yuksek (4-8)", 4.0, 8.0),
        ("asiri (>=8 veya negatif=net nakit ayri sayilir)", 8.0, None),
    ]
    print(_band_count("BIST sanayi", [_to_float(b.analysis.ratios.net_debt_to_ebitda) for b in bist], kaldirac_bands))
    print(_band_count("NASDAQ sanayi", [_to_float(b.analysis.ratios.net_debt_to_ebitda) for b in nasdaq], kaldirac_bands))

    print("\n### Cari Oran bandi (spec_mercek_guvenlik.md, Bilanco Kalitesi -- Graham >=2,0 vs Buffett <1 celismesi)\n")
    cari_bands = [("<1 (Buffett'in 'normal' bulgusu bolgesi)", None, 1.0), ("1-1.5", 1.0, 1.5), (">=1.5 (Graham esigi)", 1.5, None)]
    print(_band_count("BIST sanayi", [_to_float(b.analysis.ratios.current_ratio) for b in bist], cari_bands))
    print(_band_count("NASDAQ sanayi", [_to_float(b.analysis.ratios.current_ratio) for b in nasdaq], cari_bands))

    print("\n### Hasilat buyume bandi (spec_mercek_buyume.md, NOMINAL -- enflasyon duzeltmesi bu koşuda YOK)\n")
    buyume_bands = [
        ("taban-alti (<-20)", None, -20.0),
        ("negatif (-20..0)", -20.0, 0.0),
        ("orta (0-15)", 0.0, 15.0),
        ("guclu (>=15)", 15.0, None),
    ]
    print(_band_count("BIST sanayi", [_to_float(b.analysis.ratios.revenue_growth_yoy_pct) for b in bist], buyume_bands))
    print(_band_count("NASDAQ sanayi", [_to_float(b.analysis.ratios.revenue_growth_yoy_pct) for b in nasdaq], buyume_bands))


def report_price_dependent(bundles: list[TickerBundle], with_price: bool) -> None:
    print("\n## 4. Fiyata bagimli carpanlar (F/K, PD/DD) -- SADECE BIST, --with-price ile\n")
    if not with_price:
        print("  --with-price verilmedi, bu bolum ATLANDI (canli fiyat cekimi calistirilmadi).")
        return

    priced = [b for b in bundles if b.valuation is not None]
    print(f"  Fiyati basariyla cekilen BIST sanayi sirketi: {len(priced)}")
    print(_dist_line("F/K (own_pe)", [_to_float(b.valuation.pe_ratio) for b in priced]))
    print(_dist_line("PD/DD (own_pb)", [_to_float(b.valuation.pb_ratio) for b in priced]))
    print(_dist_line("FD/FAVOK", [_to_float(b.valuation.ev_ebitda) for b in priced]))

    fk_bands_sanayi = [("ucuz (<8)", None, 8.0), ("makul (8-15)", 8.0, 15.0), ("pahali (15-25)", 15.0, 25.0), ("cok pahali (>=25)", 25.0, None)]
    pb_bands_sanayi = [("ucuz (<1)", None, 1.0), ("makul (1-2.5)", 1.0, 2.5), ("pahali (2.5-5)", 2.5, 5.0), ("cok pahali (>=5)", 5.0, None)]
    print(_band_count("F/K bandi (sanayi CONFIG esikleri)", [_to_float(b.valuation.pe_ratio) for b in priced], fk_bands_sanayi))
    print(_band_count("PD/DD bandi (sanayi CONFIG esikleri)", [_to_float(b.valuation.pb_ratio) for b in priced], pb_bands_sanayi))

    graham_carpani = [
        _to_float(b.valuation.pe_ratio * b.valuation.pb_ratio)
        for b in priced
        if b.valuation.pe_ratio is not None and b.valuation.pe_ratio > 0 and b.valuation.pb_ratio is not None and b.valuation.pb_ratio > 0
    ]
    print(_dist_line("Graham Carpani (F/K x PD/DD)", graham_carpani))
    if graham_carpani:
        ucuz = sum(1 for v in graham_carpani if v <= 22.5)
        print(f"  Graham <=22,5 esigini gecen: {ucuz}/{len(graham_carpani)} (%{ucuz / len(graham_carpani) * 100:.1f})")


def report_v1_score_distribution(bundles: list[TickerBundle], with_price: bool) -> None:
    print("\n## 5. v1 Radar Skoru dagilimi (v2 lens kodu HENUZ YAZILMADI -- en yakin calisan proxy)\n")
    print("  (Persona sorusu: 'her sey 7-8'e yigiliyorsa ayristirma gucu yok demektir' -- bu proxy ile test ediliyor.)\n")

    def _sanayi_like(b: TickerBundle, market: str) -> bool:
        return b.analysis is not None and b.market == market and b.financial_group in (None, "XI_29", "US_GAAP")

    bist = [b for b in bundles if _sanayi_like(b, "BIST")]
    nasdaq = [b for b in bundles if _sanayi_like(b, "NASDAQ")]

    for label, group, template in (("BIST sanayi", bist, "sanayi"), ("NASDAQ sanayi", nasdaq, "abd_sanayi")):
        scores: list[float | None] = []
        badges: dict[str, int] = {}
        for b in group:
            valuation_input = None
            if with_price and b.valuation is not None:
                valuation_input = scorer.ValuationInput(pe_ratio=b.valuation.pe_ratio, pb_ratio=b.valuation.pb_ratio)
            result = scorer.score_industrial(b.analysis, valuation=valuation_input, template=template)
            scores.append(_to_float(result.total_score) if result.data_sufficient else None)
            badges[result.badge] = badges.get(result.badge, 0) + 1
        print(f"\n### {label} (n={len(group)}, valuation={'DAHIL' if with_price else 'HARIC -- Degerleme bileseni None, yeniden dagitildi'})\n")
        print(_dist_line("v1 toplam skor (0-10)", scores))
        print(f"  Rozet dagilimi: {badges}")
        near_top = sum(1 for s in scores if s is not None and 7.0 <= s <= 8.5)
        total_scored = sum(1 for s in scores if s is not None)
        if total_scored:
            print(f"  [7,0-8,5] araliginda yigilma: {near_top}/{total_scored} (%{near_top / total_scored * 100:.1f})")


# --- Ana akis -----------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-price", action="store_true", help="BIST icin canli fiyat cek (F/K/PD/DD bolumu icin gerekli, yavas).")
    parser.add_argument("--limit", type=int, default=None, help="Test icin islenen ticker sayisini sinirla.")
    parser.add_argument("--pacing-seconds", type=float, default=0.15, help="--with-price ile istekler arasi bekleme (SEC/isyatirim nezaketi icin degil, IsYatirim icin de dusuk-riskli bir tampon).")
    args = parser.parse_args()

    print("=" * 78)
    print("FAZ 3a KALIBRASYON RAPORU (scripts/kalibrasyon_v2.py) -- SADECE OKUMA")
    print("=" * 78)

    from src.db.models import init_db

    init_db(default_engine)  # idempotent -- yeni sutun/tablo eklemez, DB'de zaten var olan semayi dogrular

    with repository.get_session() as session:
        company_meta = _load_company_meta(session)
        report_sector_universe(session)

        tickers = _tickers_with_financials(session)
        if args.limit:
            tickers = tickers[: args.limit]
        print(f"\n[bilgi] Toplam analiz edilecek ticker sayisi: {len(tickers)}")

        bundles: list[TickerBundle] = []
        t_start = time.time()
        for i, ticker in enumerate(tickers, 1):
            bundle = _build_bundle(session, ticker, company_meta.get(ticker))
            if args.with_price:
                _maybe_fetch_price(bundle)
                time.sleep(args.pacing_seconds)
            bundles.append(bundle)
            if i % 40 == 0:
                print(f"  [ilerleme] {i}/{len(tickers)} islendi ({time.time() - t_start:.0f}s).")

        bundles = [b for b in bundles if b.analysis is not None]
        print(f"\n[bilgi] Basariyla analiz edilen ticker sayisi: {len(bundles)} ({time.time() - t_start:.0f}s surdu).")

        report_raw_metric_distributions(bundles)
        report_threshold_bands(bundles)
        report_price_dependent(bundles, with_price=args.with_price)
        report_v1_score_distribution(bundles, with_price=args.with_price)

    print("\n" + "=" * 78)
    print("BITTI -- DB'ye hicbir yazma yapilmadi (sadece SELECT).")
    print("=" * 78)


if __name__ == "__main__":
    main()
