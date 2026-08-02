"""stockanalysis.com'dan ceyreklik Satislar/Brut Kar/Esas Faaliyet Kari cekar --
SEC EDGAR'da (ozellikle genc/kucuk NASDAQ sirketlerinde, bkz. 06_BILINEN_
SORUNLAR.md §B17 -- orn. ASTS/AST SpaceMobile) EKSIK kalan bu kalemler icin
YEDEK/tamamlayici kaynaktir. SEC HER ZAMAN birincil/otoriter kaynaktir --
bu modul SADECE `src.fetchers.sec_edgar` bir alan icin None dondugunde
`src.bot.pipeline` tarafindan cagrilir (bkz. pipeline._stockanalysis_yedek_veri).

NEDEN stockanalysis.com (investing.com/tradingview.com DEGIL): CANLI arastirildi
(2026-08-03) -- investing.com duz bir HTTP istegini 403 ile REDDEDIYOR (bot
korumasi, Fintables'la AYNI durum -- bkz. §B16) VE tarayici-render edilmis
haliyle bile CIKAN rakamlar TUTARSIZDI (bir satirin degeri baska bir satirin
degeriyle AYNIYDI -- guvenilmez cikarim). tradingview.com duz HTTP ile 200
donuyor ama gercek SAYISAL degerler sunucu tarafinda RENDER EDILMIYOR (bos/
placeholder karakter iceriyor, JavaScript ile ayri bir API'den sonradan
dolduruluyor) -- basit bir istekle veri CEKILEMEZ, tam bir tarayici otomasyonu
gerektirir. stockanalysis.com ISE duz HTTP ile 200 donuyor VE gercek sayisal
veri dogrudan sunucu tarafinda render edilen HTML icine gomulu bir JS veri
blobunda (data:{datekey:[...],revenue:[...],gp:[...],opinc:[...],...})
BULUNUYOR -- ayrica bu site projede zaten BASKA yerlerde (bkz. sec_edgar.py
"gross_profit_us_gaap" modul notu) MANUEL dogrulama icin referans olarak
kullaniliyordu. CANLI dogrulandi: ASTS FY2026 Ç1 icin bu bloktaki revenue
(14.735.000 USD) SEC'ten BAGIMSIZ turetilen degerimizle BIREBIR eslesti.

KIRILGANLIK UYARISI: Bu, sitenin RESMI/belgelenmis bir API'si DEGIL -- HTML
icine gomulu, kucultulmus (minified) degisken adlarina (`gp`, `opinc`,
`netinccmn`) dayanan bir veri blobu. Site frontend'ini guncellerse (degisken
adlari degisirse) ayrıstırma SESSIZCE basarisiz olur -- bu yuzden HER hata
(ag, HTTP durumu, blok bulunamadi, dizi uzunluklari uyusmuyor) BELIRGIN bir
StockAnalysisParseError/StockAnalysisNetworkError firlatir (sessizce yanlis
veri UYDURULMAZ, Kural 3), cagiran taraf (pipeline.py) bunu Kural 9 geregi
YAKALAYIP SEC verisini N/A birakarak devam eder.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

import config

logger = logging.getLogger(__name__)

_FINANCIALS_URL_TEMPLATE = "https://stockanalysis.com/stocks/{ticker}/financials/?p=quarterly"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

# Sayfadaki gomulu veri blobunun basladigi ANKOR metni -- bkz. modul ust notu.
_BLOB_START_MARKER = "data:{datekey:["
_ARRAY_FIELD_RE_TEMPLATE = r"(?<![A-Za-z]){key}:\[([^\]]*)\]"


class StockAnalysisError(Exception):
    """Bu modulun taban hata sinifi."""


class StockAnalysisNetworkError(StockAnalysisError):
    """Ag/HTTP seviyesinde bir sorun (timeout, 404, beklenmeyen durum kodu)."""


class StockAnalysisParseError(StockAnalysisError):
    """Sayfa 200 dondu ama beklenen veri blobu bulunamadi/ayristirilamadi --
    site yapisi degismis olabilir (bkz. modul ust notu, KIRILGANLIK UYARISI)."""


@dataclass(frozen=True)
class QuarterlyIncomeSnapshot:
    period: tuple[int, int]  # (yil, ay) -- ay in {3,6,9,12}, ceyrek SONU tarihinden turetilir
    revenue: Decimal | None
    gross_profit: Decimal | None
    operating_profit: Decimal | None
    net_income: Decimal | None


@retry(
    reraise=True,
    stop=stop_after_attempt(config.HTTP_MAX_RETRIES),
    wait=wait_fixed(config.HTTP_RATE_LIMIT_DELAY_SECONDS),
    retry=retry_if_exception_type(httpx.RequestError),
)
def _fetch_page_html(ticker: str) -> str:
    url = _FINANCIALS_URL_TEMPLATE.format(ticker=ticker)
    try:
        response = httpx.get(url, headers=_HEADERS, timeout=config.HTTP_TIMEOUT_SECONDS, follow_redirects=True)
    except httpx.RequestError as exc:
        logger.warning("stockanalysis.com istegi basarisiz (%s), yeniden denenecek: %s", ticker, exc)
        raise
    if response.status_code == 404:
        raise StockAnalysisNetworkError(f"stockanalysis.com'da '{ticker}' bulunamadi (404).")
    if response.status_code != 200:
        raise StockAnalysisNetworkError(
            f"stockanalysis.com beklenmeyen HTTP durum kodu dondurdu: {response.status_code}"
        )
    return response.text


def _extract_array_field(blob: str, key: str) -> list | None:
    """`key:[...]` bicimindeki DUZ (ic ice degil -- sayilar/null/tirnakli
    tarih string'leri) bir JS dizisini Python listesine cevirir. Bulunamazsa
    veya JSON olarak ayristirilamazsa None doner (caller bunu "eksik alan"
    olarak yorumlar, hata FIRLATMAZ -- sadece o TEK alan None kalir)."""
    match = re.search(_ARRAY_FIELD_RE_TEMPLATE.format(key=re.escape(key)), blob)
    if match is None:
        return None
    try:
        return json.loads(f"[{match.group(1)}]")
    except json.JSONDecodeError:
        return None


def _to_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _parse_quarterly_blob(html: str, ticker: str) -> list[QuarterlyIncomeSnapshot]:
    anchor = html.find(_BLOB_START_MARKER)
    if anchor == -1:
        raise StockAnalysisParseError(
            f"{ticker}: beklenen veri blogu ('{_BLOB_START_MARKER}') sayfada bulunamadi -- site yapisi degismis olabilir."
        )
    # Blob "data:{ ... }" bicimindedir (KAPANAN tek '}' -- bir ust nesnenin
    # '}' ile birlikte gorunen "}}" ile sinirlanir, bkz. modul ust notu).
    end = html.find("}}", anchor)
    if end == -1:
        raise StockAnalysisParseError(f"{ticker}: veri blogunun sonu bulunamadi -- site yapisi degismis olabilir.")
    blob = html[anchor + len("data:") : end + 1]

    datekeys = _extract_array_field(blob, "datekey")
    revenues = _extract_array_field(blob, "revenue")
    gross_profits = _extract_array_field(blob, "gp")
    operating_profits = _extract_array_field(blob, "opinc")
    net_incomes = _extract_array_field(blob, "netinccmn")

    diziler = [datekeys, revenues, gross_profits, operating_profits, net_incomes]
    if any(d is None for d in diziler) or len({len(d) for d in diziler}) != 1:
        raise StockAnalysisParseError(
            f"{ticker}: veri dizileri eksik/hizasiz (site yapisi degismis olabilir): "
            f"uzunluklar={[len(d) if d is not None else None for d in diziler]}"
        )

    snapshots: list[QuarterlyIncomeSnapshot] = []
    for i, datekey in enumerate(datekeys):
        try:
            end_date = date.fromisoformat(datekey)
        except (TypeError, ValueError):
            continue
        period = (end_date.year, ((end_date.month - 1) // 3 + 1) * 3)
        snapshots.append(
            QuarterlyIncomeSnapshot(
                period=period,
                revenue=_to_decimal(revenues[i]),
                gross_profit=_to_decimal(gross_profits[i]),
                operating_profit=_to_decimal(operating_profits[i]),
                net_income=_to_decimal(net_incomes[i]),
            )
        )
    return snapshots


def fetch_quarterly_income(ticker: str) -> list[QuarterlyIncomeSnapshot]:
    """`ticker` icin stockanalysis.com'daki ceyreklik gelir tablosu ozetini
    doner (en yeniden eskiye SIRALI DEGIL -- sayfadaki HAM sira korunur,
    caller period'a gore kendi eslesmesini yapar). Hata durumunda
    (StockAnalysisNetworkError/StockAnalysisParseError) FIRLATIR -- SESSIZCE
    bos liste DONMEZ (Kural 3: belirsizlik gizlenmez); ikincil/yardimci veri
    oldugu icin pipeline'i BLOKLAMAMASI cagiran tarafin (bkz. pipeline.py
    _stockanalysis_yedek_veri) sorumlulugudur (Kural 9)."""
    ticker = ticker.strip().upper()
    html = _fetch_page_html(ticker)
    return _parse_quarterly_blob(html, ticker)
