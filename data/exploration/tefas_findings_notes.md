# TEFAS keşif notları (ham, canlı doğrulanmış) — 2026-08-05

## Bot koruması
- `https://www.tefas.gov.tr/` ve `/tr/fon-detayli-analiz/{kod}` HTML sayfaları F5/Distil tipi
  JS meydan okuması (TSPD cookie) arkasında — düz `httpx.get()` JS çalıştıramadığı için
  ham HTML/RSC payload'a ulaşamıyor (200 dönüyor ama içerik challenge script'i).
- 🚨 AMA `/api/funds/*` ve `/api/statistics/tefas/*` JSON uç noktaları KORUMASIZ —
  düz `httpx.post()` (tarayıcı olmadan, cookie'siz) ile CANLI doğrulandı, 200 dönüyor.

## Doğrulanmış çalışan uç noktalar (POST, JSON body)

### POST https://www.tefas.gov.tr/api/funds/fonBilgiGetir
Body: `{"fonKodu": "AFA"}`
Yanıt (CANLI, AFA ile doğrulandı, tarayıcıdaki "Fon Bilgisi" paneliyle BİREBİR eşleşti):
```json
{"errorCode":null,"errorMessage":null,"resultList":[{
  "fonKodu":"AFA","fonUnvan":"AK PORTFÖY AMERİKA YABANCI HİSSE SENEDİ FONU",
  "sonFiyat":1.259391,"gunlukGetiri":1.2529,"payAdet":4228739149,
  "portBuyukluk":5325636562.29,"fonKategori":"Hisse Senedi Fonu",
  "kategoriDerece":27,"kategoriFonSay":195,"yatirimciSayi":45243,"pazarPayi":2.37
}]}
```
→ FundInfo alanlarının çoğunun ANA kaynağı: fiyat, günlük getiri, pay adedi,
  toplam değer (piyasa değeri), yatırımcı sayısı, kategori, pazar payı.

### POST https://www.tefas.gov.tr/api/statistics/tefas/getFplFonList
Body: `{}` (parametresiz, TÜM fon evrenini döner)
Yanıt: `{"data":[{"fonKod":"AAL","unvan":"...","kurucuKod":"APY","kurucuAd":"...",
"oprKod":"ATA","oprAd":"...","durum":"AKTİF","tarih":"..."}, ...]}`
→ search_fund(query) İÇİN kullanılabilir: TÜM evreni bir kez çek (mümkünse
  önbelleğe al), sonra fonKod/unvan üzerinde alt-dize eşlemesi Python'da yap.
  ⚠️ Sunucu tarafında filtreleme parametresi bulunamadı (aşağıya bkz).

## Doğrulanamayan / bulunamayan uç noktalar

### fonUnvanAra (arama, muhtemelen doğru uç nokta ama body şeması bulunamadı)
Denenen body anahtarları (`unvan`, `aramaKelime`, `kelime`, `fonUnvan`) HEPSİ AYNI
(filtrelenmemiş görünen) listeyi döndü — doğru parametre adı BULUNAMADI. Tarayıcı
arama kutusuna yazıldığında GERÇEKTEN bu uç nokta tetikleniyor (Network sekmesinde
doğrulandı) ama gerçek request body'si (fetch/XHR interceptor React'in kendi HTTP
katmanını kullandığı için yakalanamadı) elde edilemedi.
→ ÇÖZÜM: search_fund() için fonUnvanAra YERİNE getFplFonList (yukarı bkz) kullanılacak.

### dagilimSiraliGetirT (varlık dağılımı — SINIF bazlı)
Denenen ~15 farklı body şeması (`tarih`, `sayfaNo`/`sayfaBuyuklugu`, `fonKodu` dizi
olarak, `islemTarihi`, `baslangicTarih`/`bitisTarih` vb.) HEPSİ
`"Hata:java.lang.NullPointerException"` döndü — sunucu tarafında eksik bir zorunlu
alan var ama adı BULUNAMADI. ⚠️ Denemeler sırasında 429 "Throttling limit" alındı —
DAHA FAZLA DENENMEDİ (nezaket kuralı).

🔑 AMA veri BAŞKA YOLDAN doğrulandı: `/tr/fon-detayli-analiz/{kod}` sayfasının
Next.js RSC (server-rendered) payload'ına GÖMÜLÜ olarak geliyor (KAP sektör
haritasıyla AYNI desen). CANLI görülen gerçek şema (AFA):
```json
"varlikData":[
  {"fonKodu":"AFA","fonUnvan":"...","kiymetTip":"Ters-Repo","portfoyOrani":3.09},
  {"fonKodu":"AFA","fonUnvan":"...","kiymetTip":"Yabancı Hisse Senedi","portfoyOrani":95.76},
  {"fonKodu":"AFA","fonUnvan":"...","kiymetTip":"Yatırım Fonları Katılma Payları","portfoyOrani":1.15}
]
```
🚨 BU DA GÖREVİN VARSAYIMINI DOĞRULUYOR: sadece VARLIK SINIFI (kiymetTip) + oran var,
TEK TEK HİSSE İSMİ/AĞIRLIĞI YOK. Bu sayfa bot korumasının ARKASINDA olduğu için
(yukarı bkz) production kodunda güvenilir şekilde ÇEKİLEMEZ (Playwright ile mümkün
olabilir ama kırılgan + ağır, bu faz kapsamında YAPILMADI) — allocation alanı
şimdilik None bırakılacak (Kural 3).

### fonProfilDtyGetir (muhtemelen "profil" -- işlem saatleri/valör/komisyon)
`{"fonKodu":"AFA"}`, `{"fonKodu":"AFA","tarih":...}`, `{"fonKodu":"AFA","islemTarihi":...}`
hepsi `resultList: []` (boş) döndü — doğru body şeması bulunamadı. Sayfadaki
"İşlem Başlama Saati/Valör/Komisyon" alanları (profilData) da RSC'ye gömülü.

### fonFiyatBilgiGetir (fiyat GEÇMİŞİ / grafik serisi)
Tüm denemeler (`baslangicTarihi`/`bitisTarihi`, `periyot`, `ay`, `sanalizPeriyot`)
`"Sistem Hatası!!"` döndü. Tarayıcıda SADECE 1 kez çağrıldığı gözlendi (sayfa ilk
yüklendiğinde) — grafik dönem butonlarına (Haftalık/.../5 Yıllık) tıklamak YENİ bir
ağ isteği TETİKLEMEDİ, yani muhtemelen tek çağrıda geniş bir aralık (~5 yıl) dönüp
istemci tarafında filtreleniyor. Doğru body şeması BULUNAMADI.

### Getiri bilgisi (1A/3A/6A/YB/1Y/3Y/5Y) — periyodikData
Sayfada "Getiri Bilgisi" bölümü (Son 1/3/6 Ay, YB, 1/3/5 Yıl) RSC'ye gömülü geldi,
CANLI görülen alan adları: `getiri1a, getiri3a, getiri6a, getiriyb, getiri1y,
getiri3y, getiri5y` (AFA 5 yıllık: 798.78819 = sayfadaki "%798,7882" ile eşleşti).
Bu muhtemelen `fonGetiriBazliBilgiGetir` uç noktasından geliyor ama body şeması
BULUNAMADI (denenen `{"fonKodu":..}`, `{"fonKodu":..,"tarih":..}` → `resultList: null`).

## SONUÇ (search_fund/fetch_fund_info/fetch_fund_returns/fetch_price_history için)
- ✅ search_fund → getFplFonList (tam evren) + Python alt-dize eşleme
- ✅ fetch_fund_info → fonBilgiGetir (fiyat, günlük getiri, pay adet, toplam değer,
  yatırımcı sayısı, kategori, pazar payı) — allocation alanı None (yukarı bkz)
- ❌ fetch_fund_returns → GÜVENİLİR bir uç nokta BULUNAMADI, None döner (Kural 3:
  emin olunmayan alan uydurulmaz)
- ❌ fetch_price_history → GÜVENİLİR bir uç nokta BULUNAMADI, None döner
