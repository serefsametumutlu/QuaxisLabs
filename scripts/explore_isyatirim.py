"""Is Yatirim MaliTablo uc noktasinin GERCEK yanit seklini kesfetmek icin script.

isyatirim.py parser'ini varsayima dayali yazmamak icin once bu script
calistirilir, donen ham JSON incelenir, parser gercek yanita gore yazilir.

Kullanim ornekleri:
    python scripts/explore_isyatirim.py THYAO
    python scripts/explore_isyatirim.py AKBNK --group UFRS
    python scripts/explore_isyatirim.py THYAO --periods 2026:3 2025:12 2025:9 2025:6
    python scripts/explore_isyatirim.py THYAO --method post

Cikti:
    - Konsola: kullanilan yontem/grup, HTTP durumu, JSON yapisinin ozeti
      (ust duzey anahtarlar, "value" listesi uzunlugu, ornek satirlar,
      benzersiz itemCode'lardan bir kesit).
    - Diske: data/exploration/<TICKER>_<GRUP>_<zaman damgasi>.json (tam ham yanit)

Ust duzeydeki ozet, sohbete tam JSON'u yapistirmak yerine sadece gerekli
kismi paylasabilmeniz icin kucuk tutulmustur; tam yanit dosyada saklanir.
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

import config  # noqa: E402  (sys.path ayarlandiktan sonra import edilmeli)

ENDPOINT = "https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/Common/Data.aspx/MaliTablo"

FINANCIAL_GROUPS = ["XI_29", "UFRS", "UFRS_K"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.isyatirim.com.tr/",
}

EXPLORATION_DIR = BASE_DIR / "data" / "exploration"


def normalize_company_code(ticker: str) -> str:
    """'THYAO.IS' -> 'THYAO' seklinde Is Yatirim'in bekledigi koda cevirir."""
    code = ticker.strip().upper()
    if code.endswith(".IS"):
        code = code[: -len(".IS")]
    return code


def previous_quarter(year: int, period: int) -> tuple[int, int]:
    """Bir onceki ceyregin (yil, donem) ciftini doner. Donem: 3, 6, 9, 12."""
    if period == 3:
        return year - 1, 12
    return year, period - 3


_QUARTER_END_MONTH_DAY = {3: (3, 31), 6: (6, 30), 9: (9, 30), 12: (12, 31)}


def _quarter_end_date(year: int, period: int) -> date:
    month, day = _QUARTER_END_MONTH_DAY[period]
    return date(year, month, day)


def guess_last_periods(count: int = 4, lag_days: int = 75) -> list[tuple[int, int]]:
    """Bugunun tarihine gore en olasi son `count` ceyregi tahmin eder.

    BIST sirketleri (konsolide) ceyrek sonundan ~10-14 hafta sonra rapor
    aciklar; bu fonksiyon bir gecikme payi birakip cutoff tarihinden ONCE
    veya O GUNE biten en son ceyregi bulur (sadece ay bazli bolme degil,
    ceyrek bitis GUNUNU de kontrol eder). Bu sadece kesif icin bir baslangic
    noktasidir -- kesin degildir, bu yuzden --periods ile elle de verilebilir.
    """
    cutoff = date.today() - timedelta(days=lag_days)

    year = cutoff.year
    period = None
    for candidate_period in (12, 9, 6, 3):
        if _quarter_end_date(year, candidate_period) <= cutoff:
            period = candidate_period
            break
    if period is None:
        year -= 1
        period = 12

    periods: list[tuple[int, int]] = []
    for _ in range(count):
        periods.append((year, period))
        year, period = previous_quarter(year, period)
    return periods


def parse_periods_arg(raw_values: list[str]) -> list[tuple[int, int]]:
    """'2026:3' formatindaki CLI degerlerini (yil, donem) ciftlerine cevirir."""
    periods = []
    for raw in raw_values:
        try:
            year_str, period_str = raw.split(":")
            periods.append((int(year_str), int(period_str)))
        except ValueError as exc:
            raise ValueError(
                f"Gecersiz donem formati: '{raw}'. Beklenen format: YIL:DONEM (orn. 2026:3)"
            ) from exc
    return periods


def build_params(company_code: str, financial_group: str, periods: list[tuple[int, int]]) -> dict:
    params: dict[str, object] = {
        "companyCode": company_code,
        "exchange": "TRY",
        "financialGroup": financial_group,
    }
    for index, (year, period) in enumerate(periods, start=1):
        params[f"year{index}"] = year
        params[f"period{index}"] = period
    return params


def try_request(method: str, params: dict) -> httpx.Response:
    if method == "get":
        return httpx.get(ENDPOINT, params=params, headers=HEADERS, timeout=config.HTTP_TIMEOUT_SECONDS)
    if method == "post":
        return httpx.post(ENDPOINT, json=params, headers=HEADERS, timeout=config.HTTP_TIMEOUT_SECONDS)
    raise ValueError(f"Bilinmeyen yontem: {method}")


def fetch_raw(
    company_code: str,
    financial_group: str,
    periods: list[tuple[int, int]],
    method_preference: str,
) -> tuple[str, httpx.Response]:
    """Once GET, basarisiz olursa POST (veya tersi) dener; kullanilan yontemi de doner."""
    params = build_params(company_code, financial_group, periods)
    methods_to_try = ["get", "post"] if method_preference == "both" else [method_preference]

    last_exc: Exception | None = None
    for method in methods_to_try:
        try:
            response = try_request(method, params)
        except httpx.RequestError as exc:
            last_exc = exc
            print(f"  [{method.upper()}] Ag hatasi: {exc}")
            continue

        print(f"  [{method.upper()}] HTTP {response.status_code}, content-type={response.headers.get('content-type')}")
        if response.status_code == 200:
            return method, response
        last_exc = RuntimeError(f"HTTP {response.status_code}")

    raise RuntimeError(f"Is Yatirim'a ulasilamadi. Son hata: {last_exc}")


def summarize_json(payload: object, max_rows: int = 5, max_item_codes: int = 40) -> None:
    if isinstance(payload, dict):
        print(f"  Ust duzey anahtarlar: {list(payload.keys())}")
        value_list = payload.get("value")
        if isinstance(value_list, list):
            print(f"  'value' listesi uzunlugu: {len(value_list)}")
            item_codes = []
            for row in value_list:
                if isinstance(row, dict) and "itemCode" in row:
                    item_codes.append(row["itemCode"])
            unique_codes = sorted(set(item_codes))
            print(f"  Benzersiz itemCode sayisi: {len(unique_codes)}")
            print(f"  Ilk {max_item_codes} itemCode: {unique_codes[:max_item_codes]}")
            print(f"  Ilk {max_rows} satir:")
            for row in value_list[:max_rows]:
                print(f"    {row}")
        else:
            print("  'value' anahtari bulunamadi veya liste degil.")
            print(f"  Ham icerik (ilk 1000 karakter): {json.dumps(payload, ensure_ascii=False)[:1000]}")
    elif isinstance(payload, list):
        print(f"  Ust duzey bir liste donmus, uzunluk: {len(payload)}")
        for row in payload[:max_rows]:
            print(f"    {row}")
    else:
        print(f"  Beklenmeyen JSON tipi: {type(payload)}")


def save_raw_response(ticker: str, financial_group: str, method: str, response: httpx.Response) -> Path:
    EXPLORATION_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = EXPLORATION_DIR / f"{ticker}_{financial_group}_{method}_{timestamp}.json"
    out_path.write_text(response.text, encoding="utf-8")
    return out_path


def run(args: argparse.Namespace) -> int:
    company_code = normalize_company_code(args.ticker)

    if args.periods:
        try:
            periods = parse_periods_arg(args.periods)
        except ValueError as exc:
            print(f"HATA: {exc}")
            return 1
    else:
        periods = guess_last_periods(count=4)

    print(f"Sirket kodu : {company_code}")
    print(f"Donemler    : {periods}  (yil, donem[3/6/9/12])")
    print(f"Yontem      : {args.method}")
    print()

    groups_to_try = [args.group] if args.group else FINANCIAL_GROUPS
    for i, group in enumerate(groups_to_try):
        print(f"--- financialGroup={group} deneniyor ---")
        try:
            method_used, response = fetch_raw(company_code, group, periods, args.method)
        except RuntimeError as exc:
            print(f"  BASARISIZ: {exc}")
            if i < len(groups_to_try) - 1:
                print(f"  {config.HTTP_RATE_LIMIT_DELAY_SECONDS} sn bekleyip sonraki grup denenecek...")
                _sleep(config.HTTP_RATE_LIMIT_DELAY_SECONDS)
            continue

        out_path = save_raw_response(company_code, group, method_used, response)
        print(f"  Ham yanit kaydedildi: {out_path}")

        try:
            payload = response.json()
        except json.JSONDecodeError:
            print("  Yanit JSON olarak parse edilemedi. Ilk 1000 karakter:")
            print(f"  {response.text[:1000]}")
            if i < len(groups_to_try) - 1:
                _sleep(config.HTTP_RATE_LIMIT_DELAY_SECONDS)
            continue

        summarize_json(payload)

        value_list = payload.get("value") if isinstance(payload, dict) else None
        if value_list:
            print(f"\n  --> financialGroup={group} icin veri bulundu. Kesif basarili.")
            return 0

        print(f"  --> financialGroup={group} bos veri dondu, sonraki grup denenecek.")
        if i < len(groups_to_try) - 1:
            _sleep(config.HTTP_RATE_LIMIT_DELAY_SECONDS)
        print()

    print("\nHicbir financialGroup icin veri bulunamadi. Sirket kodunu ve donemleri kontrol et.")
    return 1


def _sleep(seconds: float) -> None:
    import time

    time.sleep(seconds)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ticker", help="BIST hisse kodu (orn. THYAO veya THYAO.IS)")
    parser.add_argument(
        "--group",
        choices=FINANCIAL_GROUPS,
        default=None,
        help="Tek bir financialGroup dene (belirtilmezse XI_29 -> UFRS -> UFRS_K sirayla denenir)",
    )
    parser.add_argument(
        "--periods",
        nargs="+",
        default=None,
        help="YIL:DONEM formatinda en fazla 4 donem (orn. 2026:3 2025:12 2025:9 2025:6). Verilmezse otomatik tahmin edilir.",
    )
    parser.add_argument(
        "--method",
        choices=["get", "post", "both"],
        default="both",
        help="HTTP yontemi (varsayilan: once GET sonra POST dene)",
    )
    return parser.parse_args(argv)


def main() -> int:
    config.setup_logging()
    args = parse_args(sys.argv[1:])
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
