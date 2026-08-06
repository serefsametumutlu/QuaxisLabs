"""KESIF: TradingView scanner uc noktasinin BIST hisseleri icin gunluk
getiri (% degisim) alanini ne kadar TAZE dondurdugunu dogrular -- Faz 19.1
kullanici raporu (fon tahmininin FVT'ye kiyasla asiri sapmasi) sonrasi.

BULGU (2026-08-06, CANLI): `scanner.tradingview.com/turkey/scan` TEK bir
POST istekle BIRDEN FAZLA BIST sembolunun `change` (onceki kapanisa gore
% degisim) alanini donuyor; yanit meta verisinde `update_mode:
"delayed_streaming_900"` -- yani 15 DAKIKA gecikmeli CANLI akis (fvt.com.tr
sitesinin de kendi belirttigi "Veriler 15 dakika gecikmelidir" ile BIREBIR
ORTUSUYOR). Bu, `yahoo_quote.py`'nin GUNLUK BAR dizisinden (sadece
GERCEKLESEN islemde guncellenir, az islem goren hisselerde dakikalarca/
saatlerce bayat kalabilir, bkz. o modulun ust notu #2) YAPISAL OLARAK
FARKLI ve daha taze bir kaynak -- CANLI kiyaslandi: ayni anda DSTKF icin
TradingView +%7,74 donerken FVT'nin ekran goruntusu +%7,37 gosteriyordu
(Yahoo ise +%4,05 -- daha bayat/farkli).

Bu uc nokta proje icinde ZATEN GUVENILIR sayiliyor -- `company_logo.py`
(scanner.tradingview.com/symbol) ve `earnings_calendar.py`
(scanner.tradingview.com/turkey/scan, BIST piyasa degeri siralamasi icin)
AYNI aileyi kullaniyor.

Kullanim: python scripts/explore_tradingview_quote.py OZATD THYAO GARAN DSTKF
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

_ENDPOINT = "https://scanner.tradingview.com/turkey/scan"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.tradingview.com/",
}


def main() -> None:
    tickers = sys.argv[1:] or ["OZATD", "THYAO", "GARAN", "DSTKF", "TEHOL"]
    body = {
        "symbols": {"tickers": [f"BIST:{t.upper()}" for t in tickers]},
        "columns": ["close", "change", "change_abs", "update_mode", "currency"],
    }
    response = httpx.post(_ENDPOINT, json=body, headers=_HEADERS, timeout=15)
    response.raise_for_status()
    payload = response.json()

    print(f"HTTP {response.status_code}, totalCount={payload.get('totalCount')}\n")
    for row in payload.get("data", []):
        symbol = row["s"]
        close, change, change_abs, update_mode, currency = row["d"]
        print(f"{symbol:14} close={close:>12} degisim=%{change:>8.4f} guncelleme_modu={update_mode} para_birimi={currency}")

    out_dir = Path(__file__).resolve().parent.parent / "data" / "exploration"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"tradingview_scanner_quote_{stamp}.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nHam yanit kaydedildi: {out_path}")


if __name__ == "__main__":
    main()
