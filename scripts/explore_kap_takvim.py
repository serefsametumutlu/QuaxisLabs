"""Faz 12 kesif scripti: "Yaklasan Bilanco Tarihleri" icin KAP'ta hangi veri
gercekten var? Iki soruyu cevaplar:

  YAKLASIM 1 (sirket beyani): KAP'ta "Faaliyet Takvimi" / "Finansal Rapor
  Aciklama Tarihi" turu ILERIYE DONUK bir bildirim kategorisi var mi?
  Birkac sirketin (THYAO, TAVHL, ASELS) son 90 gunluk TUM bildirim
  kategorilerini (subject alani) tarar, "takvim" gecen basliklari listeler.

  YAKLASIM 3 (gecmis davranis): kap_financials._fetch_disclosures_raw ile
  ayni sirketin gecmis ~365 gunluk 'Finansal Rapor' (FR, disclosureCategory
  == "FR") bildirimlerini ceker, HER birinin publish_date'ini o donemin
  takvim ceyrek sonuna gore kac gun GECIKMELI yayinlandigini hesaplar.

Kullanim:
    python scripts/explore_kap_takvim.py THYAO TAVHL ASELS
"""

from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402
from src.fetchers import kap, kap_financials  # noqa: E402

config.setup_logging()

_QUARTER_END_MONTH_DAY = {3: (3, 31), 6: (6, 30), 9: (9, 30), 12: (12, 31)}


def _quarter_end_date(year: int, period: int) -> date:
    month, day = _QUARTER_END_MONTH_DAY[period]
    return date(year, month, day)


def explore_yaklasim1(ticker: str) -> None:
    print(f"\n===== YAKLASIM 1 -- {ticker}: son 90 gun TUM bildirim kategorileri =====")
    try:
        disclosures = kap.fetch_disclosures(ticker, days=90)
    except kap.KapError as exc:
        print(f"  HATA: {exc}")
        return

    categories = sorted({d.category for d in disclosures})
    print(f"  Toplam {len(disclosures)} bildirim, {len(categories)} farkli kategori:")
    for cat in categories:
        print(f"    - {cat}")

    takvim_keywords = ("takvim", "faaliyet raporu", "finansal rapor aciklama", "aciklama tarihi")
    matches = [
        d for d in disclosures
        if any(kw in (d.category + " " + d.title).lower() for kw in takvim_keywords)
    ]
    print(f"  'takvim'/'aciklama tarihi' gecen bildirim sayisi: {len(matches)}")
    for m in matches[:10]:
        print(f"    [{m.date}] ({m.category}) {m.title}")


def explore_yaklasim3(ticker: str) -> None:
    print(f"\n===== YAKLASIM 3 -- {ticker}: son 365 gunun 'Finansal Rapor' (FR) bildirimleri =====")
    try:
        company = kap.search_company(ticker)
        rows = kap_financials._fetch_disclosures_raw(company.member_oid, days=365)
    except Exception as exc:  # noqa: BLE001 -- kesif scripti, hatayi konsola yazip devam
        print(f"  HATA: {exc}")
        return

    fr_rows = [r for r in rows if r.get("disclosureCategory") == "FR" and r.get("year") and r.get("period")]
    print(f"  Toplam {len(rows)} bildirim, {len(fr_rows)} tanesi FR (Finansal Rapor) kategorisinde.")

    # Ayni (year,period) icin birden fazla aday olabilir (Konsolide/Solo cifti) --
    # en erken yayinlanani (ilk yayinlanan varyanti) baz al.
    by_period: dict[tuple[int, int], datetime] = {}
    for r in fr_rows:
        publish_date = datetime.strptime(r["publishDate"], "%d.%m.%Y %H:%M:%S")
        year, kap_period = r["year"], r["period"]
        key = (year, kap_period)
        if key not in by_period or publish_date < by_period[key]:
            by_period[key] = publish_date

    print(f"  {len(by_period)} farkli (yil,kap_period) kombinasyonu bulundu:")
    lags = []
    for (year, kap_period), publish_date in sorted(by_period.items()):
        # kap_period 1/2/3/4 -> takvim ceyregi VARSAYIMI burada YAPILMAZ (kap_period'un
        # sirkete gore farkli anlam tasiyabildigi biliniyor, bkz. kap_financials.py notu) --
        # sadece 4 olasi ceyrek sonundan HANGISINE en yakin dustugunu (publish_date'ten
        # ONCE, min_lag_days ile) goster, kesin kabul ETME.
        cutoff = publish_date.date() - timedelta(days=14)
        inferred_period = None
        for candidate_period in (12, 9, 6, 3):
            if _quarter_end_date(cutoff.year, candidate_period) <= cutoff:
                inferred_period = (cutoff.year, candidate_period)
                break
        if inferred_period is None:
            inferred_period = (cutoff.year - 1, 12)

        q_end = _quarter_end_date(*inferred_period)
        lag_days = (publish_date.date() - q_end).days
        lags.append(lag_days)
        print(
            f"    KAP(yil={year},period={kap_period}) -> tahmini gercek donem={inferred_period}, "
            f"ceyrek sonu={q_end}, yayin={publish_date.date()}, gecikme={lag_days} gun"
        )

    if lags:
        lags_sorted = sorted(lags)
        n = len(lags_sorted)
        median = lags_sorted[n // 2] if n % 2 == 1 else (lags_sorted[n // 2 - 1] + lags_sorted[n // 2]) / 2
        print(f"  Gecikme (gun) listesi: {lags_sorted}")
        print(f"  MEDYAN gecikme: {median} gun")


def main() -> int:
    tickers = sys.argv[1:] if len(sys.argv) > 1 else ["THYAO", "TAVHL", "ASELS"]
    for ticker in tickers:
        explore_yaklasim1(ticker)
        explore_yaklasim3(ticker)
    return 0


if __name__ == "__main__":
    sys.exit(main())
