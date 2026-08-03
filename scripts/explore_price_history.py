"""Is Yatirim HisseTekil / Yahoo chart uc noktalarinin GERCEK yanit seklini
kesfetmek icin script.

Faz 15 (Teknik Analiz) fiyat gecmisi fetcher'i yazilmadan once, bu uc noktalarin
sadece gunluk kapanis mi dondurdugunu yoksa OHLC (acilis/yuksek/dusuk) + hacim
de icerip icermedigini KANITLAMAK icin kullanilir (Kural 3 - varsayimla eslenmez).

Kullanim:
    python scripts/explore_price_history.py THYAO --market BIST
    python scripts/explore_price_history.py THYAO --market BIST --days 400
    python scripts/explore_price_history.py AAPL --market NASDAQ --days 400

Cikti:
    - Konsola: HTTP durumu, yanitin ust duzey anahtarlari, ilk satirin TUM
      alan adlari + degerleri, satir sayisi, ilk/son tarih.
    - Diske: data/exploration/<TICKER>_<kaynak>_<zaman damgasi>.json (ham yanit)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import httpx

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config  # noqa: E402

ISYATIRIM_ENDPOINT = "https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/Common/Data.aspx/HisseTekil"
YAHOO_ENDPOINT = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"

ISYATIRIM_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.isyatirim.com.tr/",
}
YAHOO_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

EXPLORATION_DIR = BASE_DIR / "data" / "exploration"


def normalize_company_code(ticker: str) -> str:
    code = ticker.strip().upper()
    if code.endswith(".IS"):
        code = code[: -len(".IS")]
    return code


def _save(company_code: str, source: str, payload: dict) -> Path:
    EXPLORATION_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = EXPLORATION_DIR / f"{company_code}_{source}_{timestamp}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def run_bist(ticker: str, days: int) -> int:
    company_code = normalize_company_code(ticker)
    end = date.today()
    start = end - timedelta(days=days)
    params = {
        "hisse": company_code,
        "startdate": start.strftime("%d-%m-%Y"),
        "enddate": end.strftime("%d-%m-%Y"),
    }

    print(f"Sirket kodu : {company_code}")
    print(f"Tarih araligi: {start} -> {end} ({days} gun istendi)")
    print()

    response = httpx.get(
        ISYATIRIM_ENDPOINT, params=params, headers=ISYATIRIM_HEADERS, timeout=config.HTTP_TIMEOUT_SECONDS
    )
    print(f"HTTP durumu: {response.status_code}, content-type={response.headers.get('content-type')}")
    if response.status_code != 200:
        print(f"Ham govde (ilk 1000 karakter): {response.text[:1000]}")
        return 1

    payload = response.json()
    print(f"Ust duzey anahtarlar: {list(payload.keys())}")

    rows = payload.get("value") or []
    print(f"Satir sayisi: {len(rows)}")
    if not rows:
        print("Bos yanit - bu ticker/tarih araligi icin veri yok.")
        return 1

    first_row, last_row = rows[0], rows[-1]
    print()
    print("Ilk satirdaki TUM alanlar (anahtar: deger):")
    for key, value in first_row.items():
        print(f"  {key!r}: {value!r}")

    print()
    print(f"Ilk satir: {first_row}")
    print(f"Son satir : {last_row}")

    out_path = _save(company_code, "hissetekil", payload)
    print()
    print(f"Ham yanit kaydedildi: {out_path}")
    return 0


def run_nasdaq(ticker: str, days: int) -> int:
    company_code = ticker.strip().upper()
    # Yahoo 'range' parametresi gun sayisi degil onceden tanimli etiketler
    # kabul eder (1y, 2y, 5y, max, ...) -- 400 gunu rahatca kapsamasi icin
    # en yakin buyuk etiket secilir.
    range_label = "1y" if days <= 365 else "2y"
    params = {"range": range_label, "interval": "1d"}

    print(f"Sirket kodu  : {company_code}")
    print(f"Yahoo range  : {range_label} (istenen {days} gun icin)")
    print()

    url = YAHOO_ENDPOINT.format(ticker=company_code)
    response = httpx.get(url, params=params, headers=YAHOO_HEADERS, timeout=config.HTTP_TIMEOUT_SECONDS)
    print(f"HTTP durumu: {response.status_code}, content-type={response.headers.get('content-type')}")
    if response.status_code != 200:
        print(f"Ham govde (ilk 1000 karakter): {response.text[:1000]}")
        return 1

    payload = response.json()
    try:
        result = payload["chart"]["result"][0]
    except (KeyError, IndexError, TypeError) as exc:
        print(f"Beklenmeyen yanit sekli: {exc}")
        print(json.dumps(payload, ensure_ascii=False)[:1000])
        return 1

    print(f"Ust duzey anahtarlar: {list(payload['chart'].keys())}")
    print(f"'result[0]' anahtarlari: {list(result.keys())}")
    meta = result.get("meta", {})
    print(f"'meta' anahtarlari: {list(meta.keys())}")

    timestamps = result.get("timestamp") or []
    quote = (result.get("indicators", {}).get("quote") or [{}])[0]
    print(f"'indicators.quote[0]' anahtarlari: {list(quote.keys())}")
    print(f"Bar sayisi (timestamp): {len(timestamps)}")

    if timestamps:
        idx_first, idx_last = 0, len(timestamps) - 1
        for label, idx in (("Ilk bar", idx_first), ("Son bar", idx_last)):
            row = {key: values[idx] for key, values in quote.items()} if quote else {}
            row_date = datetime.fromtimestamp(timestamps[idx]).date()
            print(f"{label} ({row_date}): {row}")

    out_path = _save(company_code, "yahoo_chart", payload)
    print()
    print(f"Ham yanit kaydedildi: {out_path}")
    return 0


def main() -> int:
    config.setup_logging()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ticker", help="Hisse kodu (BIST: THYAO / NASDAQ: AAPL)")
    parser.add_argument("--market", choices=["BIST", "NASDAQ"], default="BIST")
    parser.add_argument("--days", type=int, default=30, help="Kac gun geriye gidilecek (varsayilan 30)")
    args = parser.parse_args(sys.argv[1:])
    if args.market == "BIST":
        return run_bist(args.ticker, args.days)
    return run_nasdaq(args.ticker, args.days)


if __name__ == "__main__":
    sys.exit(main())
