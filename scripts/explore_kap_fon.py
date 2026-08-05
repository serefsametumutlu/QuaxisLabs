"""KEŞİF SCRİPTİ (Kural 3): KAP'ta yatırım fonu "Portföy Dağılım Raporu"
arayışı -- Faz 17 (Türk yatırım fonları veri katmanı).

⚠️ BU DOSYA BİR KEZ DÜZELTİLDİ (2026-08-05, aynı oturum içinde): İLK
turda `kap.py::DISCLOSURES_ENDPOINT` (`disclosure/members/byCriteria`,
BIST şirketleri için kullanılan uç nokta) fon oid'leriyle sorgulanmış ve
HER ZAMAN boş liste dönmüştü -- bu yüzden "hisse bazlı fon içeriği KAP'ta
bulunamıyor" YANLIŞ sonucuna varılmıştı. Kullanıcı fvt.com.tr üzerinden
GERÇEK bir örnek (PHE fonu, Temmuz 2026 raporu) paylaşıp bunu düzeltti.

DOĞRU YÖNTEM (CANLI doğrulandı, TLY/AFA/PBR/PHE'nin HEPSİNDE çalıştı):

```
GET https://kap.org.tr/tr/bildirim-sorgu-sonuc
    ?srcbar=Y&cmp=N&cat=2&m=<fonun mkkMemberOid'i>
```

Bu (eski, klasik) arama sayfası -- `disclosure/members/byCriteria`'nın
AKSİNE -- fonların "FON" tipi bildirimlerini (disclosureClass="DG")
GERÇEKTEN döndürüyor. Yanıt HTML'inde `"data":[{"disclosureBasic":{...}}]`
JSON dizisi gömülü geliyor (tek-seviye ters-eğik-çizgi escape'li, bot
koruması YOK, düz `httpx` ile çalışıyor). Her satırda `title` alanı
"Portföy Dağılım Raporu" olan kayıtlar aranan rapordur -- CANLI
doğrulandı: PHE Haziran VE Temmuz 2026 için AYRI AYRI birer rapor var,
yani AYLIK yayınlanıyor.

Bildirim detay sayfası (`kap.org.tr/tr/Bildirim/{index}`) içinde ekli PDF
dosyasının indirme linki gömülü: `"attachments":[{"objId":"...",
"fileName":"..."}]` -> `https://kap.org.tr/tr/api/file/download/{objId}`.

PDF İÇERİĞİ (CANLI doğrulandı, PHE Temmuz 2026 -- 3 sayfa, 21 hisse):
HER hisse için ayrı satır(lar) -- BİST kodu, ISIN kodu, şirket adı,
nominal değer, satın alma tarihi/fiyatı, toplam değer VE üç ayrı yüzde
kolonu (grup-içi %, fon-portföyüne-göre %, fon-toplam-değerine-göre %).
Aynı hisse birden fazla "lot" satırında görünebilir (ay içinde farklı
tarihlerde alınıp satılan lotlar) -- NET ağırlık için ticker+ISIN bazında
toplanmalı. Ayrıştırma mantığı ve doğrulama yöntemi:
`src/fetchers/kap_fund_portfolio.py` modül üst notuna bkz. -- PDF'in
KENDİ "GRUP TOPLAMI" satırıyla (PHE: 21 hisse, toplam %77,05) rakam
rakam eşleşti.

Ham çıktılar: data/exploration/kap_bildirim_sorgu_sonuc_phe.html,
kap_bildirim_1643421.html, PHE_2026.07.pdf, TLY_portfoy_dagilim.pdf.

Kullanım:
    python scripts/explore_kap_fon.py [FON_KODU]
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import httpx  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

SEARCH_ENDPOINT = "https://www.kap.org.tr/tr/api/search/combined"
DISCLOSURE_LIST_ENDPOINT = "https://kap.org.tr/tr/bildirim-sorgu-sonuc"
DISCLOSURE_DETAIL_TEMPLATE = "https://kap.org.tr/tr/Bildirim/{index}"
FILE_DOWNLOAD_TEMPLATE = "https://kap.org.tr/tr/api/file/download/{obj_id}"

_DISCLOSURE_ROW_RE = re.compile(
    r'"disclosureBasic":\{"publishDate":"([^"]+)","disclosureIndex":(\d+)[^{}]*?"title":"([^"]+)"[^{}]*?'
    r'"summary":"([^"]*)"[^{}]*?"year":(\d+),"period":(\d+)'
)
_ATTACHMENT_RE = re.compile(r'"attachments":\[\{"objId":"([^"]+)","fileName":"([^"]+)"')


def _unescape(text: str) -> str:
    return text.replace('\\"', '"').replace("\\\\", "\\")


def search_fund(fund_code: str) -> dict | None:
    response = httpx.post(SEARCH_ENDPOINT, headers=_HEADERS, json={"keyword": fund_code.lower()}, timeout=20)
    payload = response.json()
    rows = next((c.get("results", []) for c in payload if c.get("category") == "companyOrFunds"), [])
    for row in rows:
        if row.get("searchType") == "F" and fund_code.lower() in (row.get("cmpOrFundCode") or "").split(","):
            return row
    return None


def find_portfolio_disclosures(fund_oid: str) -> list[tuple]:
    response = httpx.get(
        DISCLOSURE_LIST_ENDPOINT,
        params={"srcbar": "Y", "cmp": "N", "cat": "2", "m": fund_oid},
        headers=_HEADERS,
        timeout=20,
    )
    text = _unescape(response.text)
    rows = _DISCLOSURE_ROW_RE.findall(text)
    return [r for r in rows if r[2] == "Portföy Dağılım Raporu"]


def main() -> int:
    fund_code = sys.argv[1] if len(sys.argv) > 1 else "PHE"

    print(f"=== KAP fon arama: {fund_code!r} ===")
    fund = search_fund(fund_code)
    if not fund:
        print("Fon bulunamadı.")
        return 1
    print(f"Bulundu: {fund['searchValue']} (oid={fund['memberOrFundOid']})")

    print("\n=== Portföy Dağılım Raporu bildirimleri aranıyor ===")
    reports = find_portfolio_disclosures(fund["memberOrFundOid"])
    print(f"{len(reports)} rapor bulundu.")
    for publish_date, idx, _title, summary, year, period in sorted(
        reports, key=lambda r: datetime.strptime(r[0], "%d.%m.%Y %H:%M:%S"), reverse=True
    ):
        print(f"  {publish_date} | idx={idx} | {year}/{period} | {summary.strip()}")

    out_dir = BASE_DIR / "data" / "exploration"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"kap_fon_{fund_code.lower()}_dagilim_raporlari.json").write_text(
        json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if not reports:
        print("\nUYARI: Bu fon için hiç 'Portföy Dağılım Raporu' bulunamadı (bazı fonlar yayınlamıyor olabilir).")
        return 2

    print("\nDetaylı ayrıştırma: src/fetchers/kap_fund_portfolio.py::fetch_latest_portfolio()")
    print("Demo: python scripts/demo_fon.py " + fund_code)
    return 0


if __name__ == "__main__":
    sys.exit(main())
