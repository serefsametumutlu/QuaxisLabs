"""KEŞİF SCRİPTİ (Kural 3): KAP'ta yatırım fonu "Portföy Dağılım Raporu"
arayışı -- Faz 17 (Türk yatırım fonları veri katmanı).

YÖNTEM: kap.py'nin (BIST şirketleri için) zaten kullandığı
`/tr/api/search/combined` + `/tr/api/disclosure/members/byCriteria` uç
noktaları FONLAR için de çalışıyor mu diye CANLI test edildi.

BULGULAR (2026-08-05, CANLI doğrulandı):

1. KAP'ın arama uç noktası fonları da tanıyor -- `searchType` alanı
   şirketler için "C", fonlar için "F". Örnek: "afa" araması
   `{"searchValue":"AK PORTFÖY AMERİKA YABANCI HİSSE SENEDİ FONU",
   "searchType":"F","memberOrFundOid":"33E5FED7E40B00EAE0530A4A622B2AEA",
   "cmpOrFundCode":"afa"}` döndü.

2. 🚨 AMA `disclosure/members/byCriteria` bu fon oid'i ile sorgulandığında
   (90/180/365 gün pencereleri denendi) HER SEFERİNDE BOŞ liste döndü --
   fon, KAP'ın standart bildirim akışında (bu oid altında) HİÇBİR
   bildirim YAYINLAMAMIŞ görünüyor.

3. Fonun KURUCUSU (portföy yönetim şirketi, "AK PORTFÖY YÖNETİMİ A.Ş.")
   AYRI bir KAP şirket kaydı olarak bulundu (searchType "C",
   oid "4028e4a240e8d16e0140e8f3623d0043") VE bu şirketin GERÇEKTEN
   bildirimleri var -- ama 60 günlük pencerede görülen 7 bildirimin
   TAMAMI şirketin KENDİ kurumsal bildirimleri (Faaliyet Raporu, Finansal
   Rapor, Şirket Genel Bilgi Formu, Sorumluluk Beyanı) -- HİÇBİRİ "Portföy
   Dağılım Raporu" veya benzeri bir fon-portföyü içeriği DEĞİL.

SONUÇ: Bu oturumda test edilen örnekte (AK PORTFÖY / AFA fonu), hisse
bazlı fon portföy dağılımı KAP'ın PUBLIC disclosure API'si (kap.py'nin
zaten kullandığı `disclosure/members/byCriteria` uç noktası) üzerinden
GÜVENİLİR ŞEKİLDE ÇEKİLEMEDİ -- ne fonun kendi oid'i ne de kurucusunun
oid'i altında böyle bir bildirim bulunabildi. Ayrıca kap.org.tr'nin
"Yatırım Fonları" navigasyon linki (`/tr/YatirimFonlari`,
`/tr/YatirimFonlari/BYF`) tarayıcıda 404 olarak gözlendi (bu gözlem bir
tarayıcı oturumu çökmesiyle aynı ana denk geldiği için TAM güvenilir
değil, ama en azından bu URL kalıbının GÜVENİLİR bir "fon bilgi sayfası"
olmadığını gösteriyor).

🚨 Bu, görev tanımının §"BİLİNEN DURUM" bölümünde belirtilen riski
DOĞRULUYOR: "Hisse bazlı içerik SADECE KAP'taki aylık Portföy Dağılım
Raporu'nda bulunur" varsayımı bu oturumda GÜVENİLİR ŞEKİLDE
doğrulanamadı -- rapor GERÇEKTEN var olabilir ama (a) KAP'ın farklı bir
alt sistemi/uç noktası üzerinden yayınlanıyor olabilir (bu oturumda
bulunamadı), (b) sadece BELİRLİ fon TÜRLERİ için (örn. gayrimenkul/
girişim sermayesi fonları, "F" tipi özel durumlar) zorunlu olabilir,
ya da (c) gerçekten KAP'ın public API'sinde YOKTUR.

ÖNERİ (Kural 3 gereği, uydurma veriyle DEVAM EDİLMEDİ):
`src/fetchers/kap_fund_portfolio.py` fon+kurucu oid'lerini arayıp
bulunan bildirimler arasında başlığında "portföy dağılım"/"portföy
bilgi" geçenleri filtreler (böyle bir bildirim GERÇEKTEN varsa
yakalar) -- ama bulunamazsa None döner, ASLA fabrike veri üretmez.
Faz 18/19'un kapsamı bu bulguya göre daraltılmalı (bkz. teslim raporu).

Kullanım:
    python scripts/explore_kap_fon.py [FON_KODU_VEYA_ARAMA_KELIMESI]
"""

from __future__ import annotations

import json
import sys
import time
from datetime import date, timedelta
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
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Referer": "https://www.kap.org.tr/",
}

SEARCH_ENDPOINT = "https://www.kap.org.tr/tr/api/search/combined"
DISCLOSURES_ENDPOINT = "https://www.kap.org.tr/tr/api/disclosure/members/byCriteria"

_PORTFOLIO_REPORT_HINTS = ("portföy dağılım", "portfoy dagilim", "portföy bilgi", "portföy raporu")


def search_kap(keyword: str) -> list[dict]:
    response = httpx.post(SEARCH_ENDPOINT, headers=_HEADERS, json={"keyword": keyword}, timeout=20)
    response.raise_for_status()
    payload = response.json()
    for category in payload:
        if category.get("category") == "companyOrFunds":
            return category.get("results", [])
    return []


def fetch_disclosures(member_oid: str, days: int = 365) -> list[dict]:
    to_date = date.today()
    from_date = to_date - timedelta(days=days)
    body = {"fromDate": from_date.isoformat(), "toDate": to_date.isoformat(), "mkkMemberOidList": [member_oid]}
    response = httpx.post(DISCLOSURES_ENDPOINT, headers=_HEADERS, json=body, timeout=20)
    response.raise_for_status()
    return response.json()


def main() -> int:
    query = sys.argv[1] if len(sys.argv) > 1 else "afa"

    print(f"=== KAP arama: {query!r} ===")
    results = search_kap(query)
    funds = [r for r in results if r.get("searchType") == "F"]
    companies = [r for r in results if r.get("searchType") == "C"]
    print(f"{len(funds)} fon, {len(companies)} şirket eşleşmesi bulundu.")

    out_dir = BASE_DIR / "data" / "exploration"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"kap_fon_arama_{query.replace(' ', '_')}.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if not funds:
        print("Fon bulunamadı.")
        return 1

    fund = funds[0]
    print(f"\nFon: {fund['searchValue']} (oid={fund['memberOrFundOid']})")
    print("Fonun kendi oid'i ile bildirimler aranıyor (365 gün)...")
    time.sleep(1)
    fund_disclosures = fetch_disclosures(fund["memberOrFundOid"])
    print(f"  {len(fund_disclosures)} bildirim bulundu.")
    for row in fund_disclosures[:20]:
        print("   -", row.get("publishDate"), "|", row.get("subject"), "|", (row.get("summary") or "")[:60])

    portfolio_hits = [
        row
        for row in fund_disclosures
        if any(hint in f"{row.get('subject', '')} {row.get('summary', '')}".lower() for hint in _PORTFOLIO_REPORT_HINTS)
    ]
    print(f"\n  'Portföy Dağılım Raporu' benzeri başlık içeren bildirim sayısı: {len(portfolio_hits)}")

    if not portfolio_hits and companies:
        # Kurucu şirketin oid'i ile de dene (fon kendi kaydında bildirim yayınlamıyor olabilir).
        founder = next((c for c in companies if "portföy yönetimi" in c["searchValue"].lower()), None)
        if founder:
            print(f"\nKurucu şirket: {founder['searchValue']} (oid={founder['memberOrFundOid']})")
            time.sleep(1)
            founder_disclosures = fetch_disclosures(founder["memberOrFundOid"], days=60)
            print(f"  {len(founder_disclosures)} bildirim bulundu (60 gün).")
            for row in founder_disclosures[:20]:
                print("   -", row.get("publishDate"), "|", row.get("subject"))
            portfolio_hits = [
                row
                for row in founder_disclosures
                if any(
                    hint in f"{row.get('subject', '')} {row.get('summary', '')}".lower()
                    for hint in _PORTFOLIO_REPORT_HINTS
                )
            ]
            print(f"  Kurucuda 'Portföy Dağılım Raporu' benzeri bildirim sayısı: {len(portfolio_hits)}")

    print("\nDetaylı keşif notları ve sonuç: modülün üst docstring'i +")
    print("PROJE_HAFIZASI teslim raporu.")
    return 0 if portfolio_hits else 2


if __name__ == "__main__":
    sys.exit(main())
