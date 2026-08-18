"""BIST yeni iş anlaşması bildirimlerini (`bist-yeni-is-anlasmalari-2025-2026.md`,
statik Fintables/KAP dökümü) yıllık toplamlara çevirip önceki yılın hasılatıyla
kıyaslayan ARAŞTIRMA scripti -- kullanıcı fikri (2026-08-18): "her yıl geçen
yılın satış gelirlerinden %20 daha fazla iş anlaşması yapan şirketler" gibi bir
filtre için ÖNCE veriye bakıp yöntemin mantıklı olup olmadığını doğrulamak.

Kullanıcı kararları (2026-08-18):
  1. Yenileme sözleşmeleri ("Sözleşme yenilenmesi") HARİÇ tutulur -- YENİ
     hasılat değil, mevcut gelirin devamıdır.
  2. Güvenle ayrıştırılamayan (belirsiz çoklu-para-birimi) tutarlar toplama
     KATILMAZ, ama şirketin o yılki "kapsam %"i (kaç anlaşmanın sayılabildiği)
     AYRICA gösterilir -- "gerçek toplam muhtemelen daha yüksek" açıkça belirtilir.
  3. Bu script SADECE bir ARAŞTIRMA raporu üretir, DB'ye/dashboard'a HENÜZ
     dokunmaz -- sonuçlar birlikte değerlendirildikten SONRA kalıcı entegrasyon
     (yeni tablo + dashboard sütunu) ayrı bir adımda yapılacak.

Para birimi çevrimi: USD/EUR tutarlar, ANLAŞMA TARİHİNDEKİ tarihsel USDTRY/
EURTRY kapanışına çevrilir (güncel kur DEĞİL -- geçmiş bir anlaşmayı bugünün
kuruyla değerlemek yanlış olur). `abcd_data.py`nin USDTRY altyapısı BURADA
YENİDEN KULLANILMAZ (o modül ABCD'ye özgü intraday/onbellek ihtiyaçları için
tasarlandı) -- bu script kendi basit, gunluk, yfinance tabanli FX serisini
çeker (tek seferlik arastirma kosusu, kalici bir onbellek gerekmiyor).

Kullanim:
    python scripts/is_anlasma_arastirma.py
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import pandas as pd  # noqa: E402
import yfinance as yf  # noqa: E402

import config  # noqa: E402
from decimal import Decimal  # noqa: E402
from src.analysis.is_anlasma_parser import DealRow, parse_deals_table  # noqa: E402
from src.db import repository  # noqa: E402

config.setup_logging()

_SOURCE_MD = BASE_DIR / "bist-yeni-is-anlasmalari-2025-2026.md"
_OUT_MD = BASE_DIR / "docs" / "spec" / "IS_ANLASMALARI_ARASTIRMA.md"
_OUT_CSV = config.DATA_DIR / "abcd_cache" / "is_anlasmalari_yillik.csv"
# Kullanici isteği (2026-08-19): "iş anlaşmaları ve miktarları belli olan
# her hisse için yazmak zorundayız hepsini yazabilecek şekilde güncelle" --
# yillik TOPLAM'in yaninda, TEK TEK anlasma satirlarini da (tarih/karsi
# taraf/aciklama/tutar) ayri bir CSV'de saklariz ki company_detail.py
# HERHANGI bir ticker icin GERCEKTEN neyin dahil/haric oldugunu gosterebilsin
# (yenileme sozlesmeleri DAHIL -- toplama katilmazlar ama GORUNMEZ degiller,
# "yenileme_mi" bayragiyla ACIKCA isaretlenir, Kural 3: sessizce gizlenmez).
_OUT_DEAL_CSV = config.DATA_DIR / "abcd_cache" / "is_anlasmalari_detay.csv"
_ORAN_ESIGI = Decimal("1.20")  # kullanicinin "%20 daha fazla" -> oran >= 1.20


def _fetch_fx_series(yf_symbol: str, start: date) -> pd.Series:
    """`yf_symbol` (orn. "USDTRY=X") icin gunluk kapanis serisini `start`den
    bugune ceker, tarihe gore siralanmis bir `pd.Series` (index=date) doner.
    Ag hatasi/bos veri durumunda BOS Series doner (FIRLATMAZ -- Kural 9)."""
    try:
        raw = yf.Ticker(yf_symbol).history(start=start.isoformat(), interval="1d", auto_adjust=False)
    except Exception:
        return pd.Series(dtype=float)
    if raw is None or raw.empty:
        return pd.Series(dtype=float)
    s = raw["Close"].dropna()
    s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
    return s.sort_index()


def _fx_rate_asof(series: pd.Series, on: date) -> Decimal | None:
    """`on` tarihine EN YAKIN, ONDAN ONCEKI (veya AYNI gun) FX kapanisini
    doner -- anlasma tarihinden SONRAKI bir kur asla kullanilmaz (look-ahead
    olmasin diye)."""
    if series.empty:
        return None
    ts = pd.Timestamp(on)
    idx = series.index[series.index <= ts]
    if len(idx) == 0:
        return None
    value = float(series.loc[idx[-1]])
    if value != value:  # NaN (bkz. modul notu: bazi FX ciftlerinde -- orn. GBPTRY -- eksik gun olabilir)
        return None
    return Decimal(str(value))


def _to_try(row: DealRow, usdtry: pd.Series, eurtry: pd.Series, gbptry: pd.Series) -> Decimal | None:
    if row.amount_value is None or row.amount_currency is None:
        return None
    if row.amount_currency == "TRY":
        return row.amount_value
    series = {"USD": usdtry, "EUR": eurtry, "GBP": gbptry}.get(row.amount_currency)
    if series is None:
        return None
    rate = _fx_rate_asof(series, row.deal_date)
    if rate is None:
        return None
    return row.amount_value * rate


def _annual_revenue(financials: dict[tuple[int, int], dict], year: int) -> Decimal | None:
    period = financials.get((year, 12))
    if not period:
        return None
    return period.get("revenue_cum")


def main() -> int:
    print(f"Kaynak dosya okunuyor: {_SOURCE_MD}")
    text = _SOURCE_MD.read_text(encoding="utf-8")
    all_rows = parse_deals_table(text)
    print(f"Toplam satir: {len(all_rows)}")

    rows = [r for r in all_rows if not r.is_renewal]
    n_renewal = len(all_rows) - len(rows)
    print(f"Yenileme (haric tutulan): {n_renewal} | Kalan (yeni is): {len(rows)}")

    earliest = min(r.deal_date for r in all_rows) - timedelta(days=10)
    print(f"FX serileri cekiliyor ({earliest} -> bugun)...")
    usdtry = _fetch_fx_series("USDTRY=X", earliest)
    eurtry = _fetch_fx_series("EURTRY=X", earliest)
    gbptry = _fetch_fx_series("GBPTRY=X", earliest)
    print(f"  USDTRY: {len(usdtry)} gun, EURTRY: {len(eurtry)} gun, GBPTRY: {len(gbptry)} gun")

    tickers = sorted({r.ticker for r in rows})
    print(f"{len(tickers)} sirket icin finansal veri cekiliyor...")
    financials_by_ticker: dict[str, dict] = {}
    with repository.get_session() as session:
        for ticker in tickers:
            financials_by_ticker[ticker] = repository.get_financials(session, ticker, n_periods=16)

    # (ticker, year) -> {"toplam_try": Decimal, "n_toplam": int, "n_ayristirilan": int}
    yearly: dict[tuple[str, int], dict] = {}
    for r in rows:
        key = (r.ticker, r.deal_date.year)
        cell = yearly.setdefault(key, {"toplam_try": Decimal(0), "n_toplam": 0, "n_ayristirilan": 0})
        cell["n_toplam"] += 1
        try_value = _to_try(r, usdtry, eurtry, gbptry)
        if try_value is not None:
            cell["toplam_try"] += try_value
            cell["n_ayristirilan"] += 1

    csv_rows = []
    for (ticker, year), cell in sorted(yearly.items()):
        financials = financials_by_ticker.get(ticker, {})
        prior_revenue = _annual_revenue(financials, year - 1)
        if prior_revenue is not None and prior_revenue.is_nan():
            prior_revenue = None  # savunmaci: DB'de NaN olarak kaydedilmis olabilir, "veri yok" sayilir
        kapsam_pct = (cell["n_ayristirilan"] / cell["n_toplam"] * 100.0) if cell["n_toplam"] else 0.0
        oran = (cell["toplam_try"] / prior_revenue) if prior_revenue and prior_revenue > 0 else None
        csv_rows.append(
            {
                "ticker": ticker,
                "yil": year,
                "yeni_is_toplami_try": float(cell["toplam_try"]),
                "n_anlasma": cell["n_toplam"],
                "n_ayristirilan": cell["n_ayristirilan"],
                "kapsam_pct": round(kapsam_pct, 1),
                "onceki_yil_hasilat_try": float(prior_revenue) if prior_revenue else None,
                "oran": float(oran) if oran is not None else None,
                "esik_gecti_mi": bool(oran is not None and oran >= _ORAN_ESIGI),
            }
        )

    df = pd.DataFrame(csv_rows)
    out_csv = _OUT_CSV
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    print(f"Ham CSV kaydedildi: {out_csv}")

    # Tek tek anlasma satirlari (yenileme DAHIL, ACIKCA isaretli) -- bkz.
    # modul ust notu, kullanici isteği (2026-08-19).
    deal_csv_rows = []
    for r in sorted(all_rows, key=lambda r: (r.ticker, r.deal_date)):
        try_value = _to_try(r, usdtry, eurtry, gbptry) if not r.is_renewal else None
        deal_csv_rows.append(
            {
                "ticker": r.ticker,
                "tarih": r.deal_date.isoformat(),
                "karsi_taraf": r.counterparty,
                "aciklama": r.description,
                "tutar_ham": r.amount_raw,
                "tutar_try": float(try_value) if try_value is not None else None,
                "yenileme_mi": r.is_renewal,
            }
        )
    deal_df = pd.DataFrame(deal_csv_rows)
    out_deal_csv = _OUT_DEAL_CSV
    out_deal_csv.parent.mkdir(parents=True, exist_ok=True)
    deal_df.to_csv(out_deal_csv, index=False)
    print(f"Anlasma-detay CSV kaydedildi: {out_deal_csv} ({len(deal_df)} satir)")

    n_with_revenue = int(df["oran"].notna().sum())
    n_over_threshold = int(df["esik_gecti_mi"].sum())
    print(f"Hasilat verisi olan (ticker,yil) hucresi: {n_with_revenue}/{len(df)}")
    print(f"Esigi (>=%20) gecen: {n_over_threshold}")

    lines = [
        "# BIST Yeni İş Anlaşmaları -- Yıllık Hasılat Kıyaslaması Araştırması\n",
        f"\nKaynak: `{_SOURCE_MD.name}` (statik dökümü, 134 hisse, 2025-01-01 – 2026-12-31 KAP bildirimleri).\n",
        "\n## ⚠️ Metodoloji -- OKUMADAN sonuçları yorumlamayın\n",
        "\n- **Yenileme sözleşmeleri hariç** -- \"Sözleşme yenilenmesi\" ifadesi geçen kayıtlar toplama katılmadı "
        f"({n_renewal} kayıt).\n",
        "- **Belirsiz (çoklu para birimi karışık toplam) tutarlar toplama katılmadı** -- her (şirket, yıl) hücresi "
        "için \"kapsam %\" (kaç anlaşmanın sayılabildiği) ayrıca gösterilir; düşük kapsamda gerçek toplam "
        "muhtemelen tablodakinden YÜKSEKTİR.\n",
        "- **Döviz çevrimi anlaşma TARİHİNDEKİ tarihsel USDTRY/EURTRY/GBPTRY kapanışıyla** yapıldı -- güncel kur "
        "DEĞİL.\n",
        "- **Önceki yıl hasılatı** DB'deki `revenue_cum` (yıl sonu, period=12) alanından -- bu veri şirkette "
        "yoksa (henüz açıklanmamış/DB'de yok) oran hesaplanamaz, `N/A` gösterilir (ASLA 0 varsayılmaz).\n",
        f"- Eşik: yeni iş toplamı ≥ önceki yıl hasılatının **%{(_ORAN_ESIGI - 1) * 100:.0f} fazlası** (oran ≥ {_ORAN_ESIGI}).\n",
        f"\n- Toplam kayıt: {len(all_rows)} (yenileme hariç: {len(rows)})\n",
        f"- Hasılat verisiyle kıyaslanabilen (ticker, yıl) hücresi: {n_with_revenue}/{len(df)}\n",
        f"- Eşiği geçen (ticker, yıl) hücresi: {n_over_threshold}\n",
        "\n## Eşiği Geçenler (oran ≥ 1.20)\n",
        "\n| Ticker | Yıl | Yeni İş Toplamı (TL) | Önceki Yıl Hasılatı (TL) | Oran | Kapsam % | n anlaşma |\n",
        "|---|---|---|---|---|---|---|\n",
    ]
    over = df[df["esik_gecti_mi"]].sort_values("oran", ascending=False)
    if over.empty:
        lines.append("\n_Eşiği geçen şirket bulunamadı._\n")
    else:
        for _, row in over.iterrows():
            lines.append(
                f"| {row['ticker']} | {row['yil']} | {row['yeni_is_toplami_try']:,.0f} | "
                f"{row['onceki_yil_hasilat_try']:,.0f} | {row['oran']:.2f} | {row['kapsam_pct']:.0f}% | "
                f"{row['n_anlasma']} |\n"
            )

    lines.append("\n## Tüm Hücreler (ham veri)\n")
    lines.append(f"\nHam tablo: `{out_csv}`\n")

    out_path = _OUT_MD
    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"Rapor kaydedildi: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
