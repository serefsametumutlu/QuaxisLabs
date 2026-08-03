"""KEŞİF SCRİPTİ (Kural 3): KAP'ın BIST şirketleri sektör sınıflandırması.

Bulgu (2026-08-03): `https://kap.org.tr/tr/Sektorler` sayfası AYRI bir XHR/
fetch API'si İLE DEĞİL, sayfanın kendi HTML'İNE (Next.js sunucu tarafı
render / RSC push payload) GÖMÜLÜ olarak TÜM (~640) BIST şirketinin sektör
bilgisini döner -- ayrı bir "sektör API'si" YOKTUR, Network sekmesinde XHR
olarak GÖRÜNMEZ (kullanıcı canlı doğruladı).

Her şirket için İKİ seviyeli sınıflandırma var:
  - "mainSectorName" (kaba, orn. "İMALAT" -- çok geniş, EREGL/FROTO/TUPRS
    gibi çok farklı iş kolundaki şirketleri AYNI kovaya atar, PEER
    KARŞILAŞTIRMASI için YETERSİZ)
  - "sectorName" (ince, orn. TUPRS için "KİMYA İLAÇ PETROL LASTİK VE
    PLASTİK ÜRÜNLER", EREGL için "ANA METAL SANAYİ" -- BUNU kullanıyoruz)

Bu script canlı yanıtı çeker, ayrıştırır, data/exploration/ altına kaydeder
ve BİLİNEN şirketlerle (kullanıcının/genel bilginin doğrulayabileceği)
karşılaştırır:
    THYAO -> Ulaştırma ve Depolama (havayolu, doğru)
    TUPRS -> Kimya İlaç Petrol Lastik ve Plastik Ürünler (rafineri, doğru)
    EREGL -> Ana Metal Sanayi (çelik, doğru)
    FROTO -> Metal Eşya Makine Elektrikli Cihazlar ve Ulaşım Araçları (otomotiv, doğru)
    SISE/KCHOL -> Holdingler ve Yatırım Şirketleri (doğru)
    AKBNK -> Mali Kuruluşlar (banka, doğru)
    BIMAS -> Toptan ve Perakende Ticaret (doğru)
    ENKAI -> İnşaat ve Bayındırlık (doğru)

⚠️ SADECE BIST kapsar (KAP verisi) -- NASDAQ şirketleri için bu kaynak
KULLANILAMAZ (ayrı bir sınıflandırma -- örn. SEC SIC kodu -- gerekir, bu
oturumda YAPILMADI).

Kullanım:
    python scripts/explore_kap_sektor.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import httpx  # noqa: E402

SEKTORLER_URL = "https://kap.org.tr/tr/Sektorler"

# İnce ("sectorName") alanlı gömülü şirket nesnelerini yakalar -- bkz. modül
# üst notu, veri sayfanın Next.js RSC push string'i içinde ÇİFT ESCAPED
# (\" olarak) geliyor.
_FINE_SECTOR_PATTERN = re.compile(
    r'\{\\"sectorName\\":\\"[^"]*?\\".*?\\"stockCode\\":\\"[^"]*?\\".*?\\"kapTypes\\":\[[^\]]*?\]\}'
)

_KNOWN_TICKERS_FOR_VALIDATION = {
    # Değerler CANLI çekilip TEK TEK doğrulanmıştır (2026-08-03) -- ilk
    # denemede AKBNK/BIMAS/ENKAI için burada YANLIŞ (fazla kaba) bir tahmin
    # yazılmıştı ("Mali Kuruluşlar"/"Toptan ve Perakende Ticaret"/"İnşaat ve
    # Bayındırlık") -- KAP'ın GERÇEK ince sınıflandırması daha spesifik
    # çıktı (Bankalar/Perakende Ticaret/İnşaat ve Bayındırlık İşleri),
    # aşağıdaki değerler KAP'ın kendi CANLI yanıtıyla düzeltildi.
    "THYAO": "ULAŞTIRMA VE DEPOLAMA",
    "TUPRS": "KİMYA İLAÇ PETROL LASTİK VE PLASTİK ÜRÜNLER",
    "EREGL": "ANA METAL SANAYİ",
    "FROTO": "METAL EŞYA MAKİNE ELEKTRİKLİ CİHAZLAR VE ULAŞIM ARAÇLARI",
    "SISE": "HOLDİNGLER VE YATIRIM ŞİRKETLERİ",
    "KCHOL": "HOLDİNGLER VE YATIRIM ŞİRKETLERİ",
    "AKBNK": "BANKALAR",
    "BIMAS": "PERAKENDE TİCARET",
    "ENKAI": "İNŞAAT VE BAYINDIRLIK İŞLERİ",
}


def fetch_sector_map() -> dict[str, str]:
    """Ticker -> ince sektör adı (BÜYÜK HARF, KAP'ın kendi yazımıyla)."""
    response = httpx.get(SEKTORLER_URL, timeout=20, follow_redirects=True)
    response.raise_for_status()
    response.encoding = "utf-8"
    text = response.text

    sector_map: dict[str, str] = {}
    for match in _FINE_SECTOR_PATTERN.findall(text):
        unescaped = match.replace('\\"', '"')
        try:
            obj = json.loads(unescaped)
        except json.JSONDecodeError:
            continue
        sector = obj.get("sectorName")
        if not sector:
            continue
        for code in (obj.get("stockCode") or "").split(","):
            code = code.strip()
            if code:
                sector_map[code] = sector
    return sector_map


def main() -> int:
    print(f"{SEKTORLER_URL} çekiliyor...")
    sector_map = fetch_sector_map()
    print(f"{len(sector_map)} benzersiz ticker için sektör bulundu.\n")

    print("Doğrulama (bilinen şirketler):")
    all_match = True
    for ticker, expected in _KNOWN_TICKERS_FOR_VALIDATION.items():
        actual = sector_map.get(ticker)
        ok = actual == expected
        all_match = all_match and ok
        print(f"  {'OK ' if ok else 'FARK'} {ticker}: beklenen={expected!r} bulunan={actual!r}")

    out_path = BASE_DIR / "data" / "exploration" / "kap_sektor_map.json"
    out_path.write_text(json.dumps(sector_map, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(f"\nTam harita kaydedildi: {out_path}")

    if not all_match:
        print("\nUYARI: bazı bilinen şirketler beklenenle eşleşmedi -- haritaya güvenmeden önce incele.")
        return 1
    print("\nTüm bilinen şirketler doğru eşleşti.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
