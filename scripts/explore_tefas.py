"""KEŞİF SCRİPTİ (Kural 3): TEFAS (tefas.gov.tr) yeni backend'inin GERÇEK
API uç noktaları -- Faz 17 (Türk yatırım fonları veri katmanı).

NASIL BULUNDU: TEFAS'ın HTML sayfaları (`/`, `/tr/fon-detayli-analiz/{kod}`)
F5/Distil tipi bir bot koruması (TSPD cookie, JS meydan okuması) ARKASINDADIR
-- düz `httpx.get()` ile çekilince 200 döner ama içerik sadece bir JS
challenge script'idir, GERÇEK HTML/veri YOKTUR. Bu yüzden kap.py'nin JS bundle
tarama yöntemi burada da kullanıldı: tarayıcıda sayfa GERÇEKTEN açılıp
(bot korumasını GEÇEBİLEN gerçek bir tarayıcı oturumuyla) Ağ sekmesi izlendi,
gerçek uç nokta adları bulundu, sonra sitenin `_next/static/chunks/*.js`
paketleri (bunlar STATİK dosyalardır, bot korumasının DIŞINDADIR, düz
`httpx.get()` ile çekilebilir) indirilip aranarak tam yol listesi + bazı
gerçek request body şemaları çıkarıldı.

🚨 EN ÖNEMLİ BULGU: `/tr/...` SAYFALARI bot korumasının ARKASINDA olsa da,
`https://www.tefas.gov.tr/api/funds/*` ve `/api/statistics/tefas/*` JSON
API'leri **KORUMASIZDIR** -- düz `httpx.post()` ile (tarayıcı/cookie
GEREKMEDEN) CANLI doğrulandı, 200 OK + gerçek veri döner. Bu, tefas.py'nin
tamamen hafif (httpx + tenacity, Playwright GEREKMEZ) yazılabilmesini sağlar.

Doğrulanan uç noktalar (bkz. modül altındaki fonksiyonlar):
  - POST /api/funds/fonBilgiGetir           {"fonKodu": "AFA"}
        -> fiyat, günlük getiri, pay adet, toplam değer, kategori, kategori
           sırası, yatırımcı sayısı, pazar payı. AFA ile CANLI doğrulandı,
           tarayıcıda görünen "Fon Bilgisi" panosuyla BİREBİR eşleşti.
  - POST /api/statistics/tefas/getFplFonList {}
        -> TÜM TEFAS fon evreni (kod, unvan, kurucu, operatör, durum) TEK
           istekte. search_fund() bunu bir kez çekip Python'da alt-dize
           eşlemesi yaparak uygular (TEFAS'ın kendi "fonUnvanAra" uç
           noktasının GERÇEK body şeması bu oturumda bulunamadı -- aşağıya
           bkz., Kural 3 gereği varsayımsal bir body ile "çalışıyormuş gibi
           görünen ama aslında filtrelemeyen" bir eşleme YAZILMADI).

🚨 BULUNAMAYAN (Kural 3: varsayımsal eşleme YAPILMADI, None/boş liste
döner, kod tabanına eklenmedi):
  - Fiyat GEÇMİŞİ (fonFiyatBilgiGetir çoklu-dönem body'si): denenen tüm
    body şemaları ("baslangicTarihi/bitisTarihi", "periyot", "ay",
    "sanalizPeriyot") "Sistem Hatası!!" döndü. Tarayıcıda sayfa İLK
    yüklendiğinde SADECE 1 kez çağrıldığı gözlendi (grafik dönem
    butonlarına tıklamak YENİ istek TETİKLEMEDİ) -- muhtemelen tek
    çağrıda geniş bir aralık dönüp istemci tarafında filtreleniyor, ama
    doğru body şeması bulunamadı.
  - Getiri bilgisi (1A/3A/6A/YB/1Y/3Y/5Y): sayfada GÖRÜNÜYOR (örn. AFA
    5 yıllık %798,7882) ve Next.js sunucu-taraflı render (RSC) payload'ına
    `periyodikData` adıyla GÖMÜLÜ geliyor (`getiri1a/getiri3a/.../getiri5y`
    alan adları CANLI görüldü) -- ama bu veri istemci tarafından ayrı bir
    API çağrısıyla DEĞİL, SUNUCU TARAFINDA (SSR, bot korumasının
    ARKASINDA) üretiliyor. `fonGetiriBazliBilgiGetir`/`fonTurDnmGetiriGetir`
    denendi, boş/null resultList döndü -- doğru body şeması bulunamadı.
  - Varlık dağılımı (dagilimSiraliGetirT): ~15 farklı body denendi, HEPSİ
    "NullPointerException" döndü (429 "Throttling limit" alınana kadar --
    nezaket kuralı gereği durduruldu). AMA veri BAŞKA yoldan doğrulandı:
    aynı RSC payload'ına `varlikData` adıyla gömülü geliyor, şema:
    `{"fonKodu","fonUnvan","kiymetTip","portfoyOrani"}` -- kiymetTip
    SADECE varlık SINIFI (örn. "Yabancı Hisse Senedi", "Ters-Repo"),
    TEK TEK HİSSE İSMİ YOK. Bu, görev tanımının varsaydığı en kritik
    kısıtı DOĞRULAR.
  - `fonProfilDtyGetir` (işlem saatleri/valör/komisyon): tüm denemeler
    boş resultList döndü, doğru body şeması bulunamadı (RSC'de `profilData`
    adıyla gömülü geliyor).
  - Bu üç RSC-gömülü veri (getiri/varlık dağılımı/profil) için bir
    PLAYWRIGHT tabanlı yedek de denendi (proje zaten card.py'de Playwright
    kullanıyor) -- CANLI SONUÇ: headless Chromium isteği
    "Request Rejected" (WAF, muhtemelen F5 BIG-IP ASM) ile REDDEDİLDİ.
    Yani bu veriler bu oturumda GÜVENİLİR şekilde otomatikleştirilemedi;
    tefas.py'de bu üç alan/fonksiyon None/boş döner (Kural 3).

Ham keşif çıktıları: data/exploration/tefas_findings_notes.md,
data/exploration/tefas_*.js (indirilen statik JS paketleri, referans için).

Kullanım:
    python scripts/explore_tefas.py [FON_KODU]
"""

from __future__ import annotations

import json
import sys
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
    "Referer": "https://www.tefas.gov.tr/tr/fon-detayli-analiz/",
    "Origin": "https://www.tefas.gov.tr",
}

FUNDS_BASE = "https://www.tefas.gov.tr/api/funds"
STATISTICS_BASE = "https://www.tefas.gov.tr/api/statistics/tefas"

# CANLI doğrulanmış (2026-08-05) -- referans karşılaştırma için: tarayıcıda
# AFA fonunun "Fon Bilgisi" panosunda görünen değerler.
_AFA_EXPECTED = {
    "fonKodu": "AFA",
    "fonKategori": "Hisse Senedi Fonu",
    "yatirimciSayi": 45243,
}


def fetch_fund_info_raw(fon_kodu: str) -> dict:
    """POST /api/funds/fonBilgiGetir -- CANLI doğrulanmış, korumasız uç nokta."""
    response = httpx.post(f"{FUNDS_BASE}/fonBilgiGetir", headers=_HEADERS, json={"fonKodu": fon_kodu}, timeout=20)
    response.raise_for_status()
    return response.json()


def fetch_fund_universe_raw() -> dict:
    """POST /api/statistics/tefas/getFplFonList -- CANLI doğrulanmış, TÜM
    TEFAS fon evrenini (parametresiz) tek istekte döner."""
    response = httpx.post(f"{STATISTICS_BASE}/getFplFonList", headers=_HEADERS, json={}, timeout=30)
    response.raise_for_status()
    return response.json()


def main() -> int:
    fon_kodu = sys.argv[1] if len(sys.argv) > 1 else "AFA"

    print(f"=== fonBilgiGetir({fon_kodu!r}) ===")
    info = fetch_fund_info_raw(fon_kodu)
    print(json.dumps(info, ensure_ascii=False, indent=2))

    out_dir = BASE_DIR / "data" / "exploration"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"tefas_fonBilgiGetir_{fon_kodu}.json").write_text(
        json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    all_match = True
    if fon_kodu.upper() == "AFA":
        result = (info.get("resultList") or [{}])[0]
        print("\nDoğrulama (bilinen AFA değerleri):")
        for key, expected in _AFA_EXPECTED.items():
            actual = result.get(key)
            ok = actual == expected
            all_match = all_match and ok
            print(f"  {'OK ' if ok else 'FARK'} {key}: beklenen={expected!r} bulunan={actual!r}")

    print("\n=== getFplFonList() (TÜM fon evreni) ===")
    universe = fetch_fund_universe_raw()
    rows = universe.get("data") or []
    print(f"{len(rows)} fon bulundu.")
    (out_dir / "tefas_fon_evreni.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Tam liste kaydedildi: {out_dir / 'tefas_fon_evreni.json'}")

    if not all_match:
        print("\nUYARI: bilinen değerlerle eşleşmeyen alanlar var -- eşlemeye güvenmeden önce incele.")
        return 1
    print("\nTüm bilinen değerler doğru eşleşti.")
    print("\nDetaylı keşif notları: data/exploration/tefas_findings_notes.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
