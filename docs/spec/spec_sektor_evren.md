# SPEC: Sektör Sınıflandırması ve Evren (Universe) Altyapısı

Faz: YOL_HARİTASI.md Faz 2, adım 1. Bu spec kod üretmez; `Company` modeline eklenecek
alanları, KAP→sektör ve SIC→sektör statik eşleme tablolarını ve
`scripts/refresh_universe.py` için tazelik/checkpoint kurallarını tanımlar.
Uygulama Faz 2 adım 3'te ayrı bir oturumda yapılacaktır.

## Amaç ve kapsam

**Geçerli şirket türleri:** Tümü — sanayi/ticaret, banka, katılım bankası, sigorta,
finansman/tasarruf finansman şirketi, GYO, holding. Bu spec sınıflandırma
(taksonomi + veri) katmanını tanımlar; şirket-türüne özel skor şablonu seçimi
Faz 3'ün konusudur, ama seçimi mümkün kılacak `sirket_turu` alanı burada
tanımlanır (bkz. sektor-siniflandirma skill madde 5: "Banka/sigorta kendi
şirket-türü grubu içinde karşılaştırılır").

**Piyasalar:** BİST (KAP kaynaklı) + NASDAQ-listeli hisseler (SEC EDGAR
kaynaklı). "NASDAQ" burada **NASDAQ borsasında işlem gören** hisseler anlamına
gelir, "tüm ABD" değil — kapsam SEC'in kendi `exchange` alanından filtrelenir
(bkz. Girdiler, `company_tickers_exchange.json`). Bu netleştirme
sektor-siniflandirma skill'inin "kullanıcıyla netleştirilmedikçe NASDAQ-listeli
varsay" talimatına göre yapıldı — kullanıcı onayında teyit edilmeli.

**Kapsam dışı:** Sektör-göreli puanlama formülleri (medyan/MAD, persentil
skorlama) — bu, Faz 3'ün "temel-analiz-cercevesi" spec'inin konusu. Bu spec
sadece o formüllerin ÜZERİNE oturacağı sınıflandırma + evren verisini üretir.

---

## Girdiler

| Alan | Piyasa | Kaynak | Proje içi mevcut durum |
|---|---|---|---|
| KAP ince sektör adı | BİST | `kap.org.tr/tr/Sektorler` (Next.js RSC payload, ayrı XHR API yok) | **MEVCUT** — `src/fetchers/kap.py::fetch_sector_map()`, `Company.sector` alanına yazılıyor (`repository.update_company_sectors`) |
| KAP üyesi ticker listesi (~640) | BİST | Yukarıdaki ile aynı istek (`stockCode` alanı) | **MEVCUT** — aynı fonksiyonun yan ürünü, evren listesi için ayrı istek GEREKMEZ |
| `financial_group` (XI_29/UFRS/UFRS_KATILIM/UFRS_K/XI_29K) | BİST | İş Yatırım (`isyatirim.fetch_financials`) | **MEVCUT** — sadece şirket en az bir kez analiz edildikten SONRA dolar (`Company.financial_group`) |
| SIC kodu + açıklaması | NASDAQ | `https://data.sec.gov/submissions/CIK{cik10}.json` alanları `sic`, `sicDescription` | **YENİ** — CANLI doğrulandı (bu oturumda): AAPL→`{"sic":"3571","sicDescription":"Electronic Computers"}`, JPM→`{"sic":"6021","sicDescription":"National Commercial Banks"}`. `sec_edgar.py` şu an bu uç noktayı HİÇ çağırmıyor (sadece `companyfacts` kullanıyor) |
| Borsa (exchange) etiketi | NASDAQ evreni | `https://www.sec.gov/files/company_tickers_exchange.json` (tek istek, TÜM SEC filer'ları) | **YENİ** — CANLI doğrulandı: `{"fields":["cik","name","ticker","exchange"],"data":[[1045810,"NVIDIA CORP","NVDA","Nasdaq"],[1067983,"BERKSHIRE HATHAWAY INC","BRK-B","NYSE"], ...]}`. `sec_edgar.py` şu an sadece `company_tickers.json` (exchange alanı YOK) kullanıyor |
| CIK çözümleme | NASDAQ | `company_tickers.json` / `company_tickers_exchange.json` | **MEVCUT** — `sec_edgar.resolve_cik()`, 24 saatlik dosya önbelleği var (`_TICKER_MAP_CACHE_MAX_AGE_HOURS`) |

**Rate limit (mevcut, `sec_edgar.py` modül notu, canlı doğrulanmış):** SEC 10
istek/sn/IP; User-Agent zorunlu ve açıklayıcı (`USER_AGENT` sabiti zaten var,
aynısı yeniden kullanılacak). `submissions` uç noktası `companyfacts` ile AYNI
kısıtlamalara tabi (aynı `data.sec.gov` alan adı).

---

## Ortak üst-sektör taksonomisi

Persona talimatındaki 11 gruplu öneri (GICS'in sadeleştirilmiş hali) DEĞİŞTİRİLMEDEN
kabul edildi — gerekçe: (a) hem KAP'ın 48 ince kategorisi hem SEC'in ~450 SIC
kodu bu 11 kovaya kayıpsız/makul biçimde indirgenebiliyor (aşağıdaki tablolarla
canlı doğrulandı), (b) GICS pazarın genel kabul gördüğü referansı olduğu için
ileride 3. bir veri kaynağı eklenirse (örn. TradingView, stockanalysis.com)
eşleme yeniden icat edilmez.

| # | Üst-sektör | GICS karşılığı | Not |
|---|---|---|---|
| 1 | Enerji | Energy | Ham petrol/doğalgaz çıkarma, rafineri, boru hattı, kömür |
| 2 | Ana Metaller ve Madencilik | Materials | Çelik, metal cevheri, kimyasallar (ilaç HARİÇ), kağıt, cam/toprak |
| 3 | Sanayi | Industrials | İnşaat, makine, havacılık/savunma, ulaştırma, iş hizmetleri |
| 4 | Tüketici (Döngüsel) | Consumer Discretionary | Otomotiv, perakende (gıda dışı), tekstil, konaklama, eğlence |
| 5 | Tüketici (Temel) | Consumer Staples | Gıda/içecek/tütün üretimi, gıda perakendesi, tarım |
| 6 | Sağlık | Health Care | İlaç, tıbbi cihaz, sağlık hizmetleri |
| 7 | Finans | Financials | Banka, sigorta, aracı kurum, finansman/kiralama, holding (GYO HARİÇ) |
| 8 | Teknoloji | Information Technology | Yazılım, donanım, yarı iletken, BT hizmetleri |
| 9 | İletişim | Communication Services | Telekom, yayıncılık, medya/eğlence, **internet/reklam platformları** |
| 10 | Kamu Hizmetleri | Utilities | Elektrik/gaz/buhar/su dağıtımı |
| 11 | Gayrimenkul/GYO | Real Estate | Gayrimenkul faaliyetleri + GYO (REIT) |

**Sınır netliği (madde 9 üzerine not — CANLI bulgu):** GICS 2018'de "Communication
Services" sektörünü Telekom + Medya'dan AYRI olarak, bazı internet/platform
şirketlerini (Alphabet, Meta) Teknoloji'den ÇEKEREK oluşturdu. SIC taksonomisi
1987 vintage'dır ve bu ayrımı YAPMAZ (aşağıda kanıtlanmıştır) — bu yüzden
"İletişim" grubu SIC tarafında salt aralık kuralıyla DOLDURULAMAZ, ticker
düzeyinde bir istisna tablosu gerekir (bkz. SIC bölümü).

---

## KAP → Üst-Sektör Eşleme Tablosu (BİST)

Kaynak: `https://kap.org.tr/tr/Sektorler` sayfası bu oturumda canlı çekildi
(619 şirket kaydı ayrıştırıldı, `_FINE_SECTOR_PATTERN` ile — `kap.py` içindeki
DESENİN AYNISI). Çıkan **48 benzersiz ince sektör adı** eksiksiz aşağıda
eşlendi (tahmine dayalı DEĞİL, sayfadan türetildi).

| KAP ince sektör (`sectorName`, `Company.sector`) | Üst-sektör |
|---|---|
| TARIM VE HAYVANCILIK AVCILIK VE İLGİLİ HİZMET FAALİYETLERİ | Tüketici (Temel) |
| BALIKÇILIK VE SU ÜRÜNLERİ | Tüketici (Temel) |
| HAM PETROL VE DOĞAL GAZ ÇIKARTILMASI | Enerji |
| KÖMÜR VE LİNYİT MADENCİLİĞİ | Enerji |
| METAL CEVHERİ MADENCİLİĞİ | Ana Metaller ve Madencilik |
| DİĞER MADENCİLİK VE TAŞ OCAKÇILIĞI | Ana Metaller ve Madencilik |
| GIDA, İÇECEK VE TÜTÜN | Tüketici (Temel) |
| TEKSTİL, GİYİM EŞYASI VE DERİ | Tüketici (Döngüsel) |
| ORMAN ÜRÜNLERİ VE MOBİLYA | Tüketici (Döngüsel) |
| KAĞIT VE KAĞIT ÜRÜNLERİ BASIM | Ana Metaller ve Madencilik |
| YAYIMCILIK | İletişim |
| TELEKOMÜNİKASYON | İletişim |
| KİMYA İLAÇ PETROL LASTİK VE PLASTİK ÜRÜNLER | Ana Metaller ve Madencilik *(bkz. override notu — TUPRS gibi rafineri ağırlıklı şirketler istisna)* |
| TAŞ VE TOPRAĞA DAYALI | Ana Metaller ve Madencilik |
| ANA METAL SANAYİ | Ana Metaller ve Madencilik |
| METAL EŞYA MAKİNE ELEKTRİKLİ CİHAZLAR VE ULAŞIM ARAÇLARI | Sanayi |
| DİĞER İMALAT SANAYİİ | Sanayi |
| ELEKTRİK GAZ VE BUHAR | Kamu Hizmetleri |
| İNŞAAT VE BAYINDIRLIK İŞLERİ | Sanayi |
| TOPTAN TİCARET | Tüketici (Döngüsel) |
| PERAKENDE TİCARET | Tüketici (Döngüsel) |
| ULAŞTIRMA VE DEPOLAMA | Sanayi |
| KONAKLAMA | Tüketici (Döngüsel) |
| YİYECEK VE İÇECEK HİZMETLERİ | Tüketici (Döngüsel) |
| SEYAHAT ACENTESİ, TUR OPERATÖRÜ VE DİĞER REZERVASYON HİZMETLERİ İLE İLGİLİ FAALİYETLER | Tüketici (Döngüsel) |
| BANKALAR | Finans |
| ARACI KURUMLAR | Finans |
| SİGORTA ŞİRKETLERİ | Finans |
| FİNANSAL KİRALAMA VE FAKTORİNG ŞİRKETLERİ | Finans |
| FİNANSMAN ŞİRKETLERİ | Finans |
| VARLIK YÖNETİM ŞİRKETLERİ | Finans |
| MENKUL KIYMET YATIRIM ORTAKLIKLARI | Finans |
| GİRİŞİM SERMAYESİ YATIRIM ORTAKLIKLARI | Finans |
| HOLDİNGLER VE YATIRIM ŞİRKETLERİ | Finans |
| GAYRİMENKUL FAALİYETLERİ | Gayrimenkul/GYO |
| GAYRİMENKUL YATIRIM ORTAKLIKLARI | Gayrimenkul/GYO |
| KİRALAMA VE LEASING FAALİYETLERİ | Finans |
| BÜRO YÖNETİMİ, BÜRO DESTEĞİ VE DİĞER ŞİRKET DESTEK FAALİYETLERİ | Sanayi |
| BİLGİ HİZMET FAALİYETLERİ | Teknoloji |
| BİLİŞİM | Teknoloji |
| HUKUK VE MUHASEBE FAALİYETLERİ | Sanayi |
| MİMARLIK VE MÜHENDİSLİK FAALİYETLERİ; TEKNİK MUAYENE VE ANALİZ | Sanayi |
| REKLAMCILIK VE PAZAR ARAŞTIRMASI | İletişim |
| İNSAN SAĞLIĞI VE SOSYAL HİZMETLER | Sağlık |
| SAVUNMA | Sanayi |
| SPOR FAALİYETLERİ EĞLENCE VE OYUN FAALİYETLERİ | Tüketici (Döngüsel) |
| SPOR EĞLENCE BOŞ ZAMANLARI DEĞERLENDİRME HİZMETLERİ | Tüketici (Döngüsel) |
| YARATICI SANATLAR GÖSTERİ SANATLARI VE EĞLENCE FAALİYETLERİ | İletişim |

**Ticker-düzeyi override (KAP):** `KİMYA İLAÇ PETROL LASTİK VE PLASTİK ÜRÜNLER`
kategorisi KAP'ta rafineri (TUPRS), ilaç ve kimyasal/plastik şirketlerini AYNI
kovaya koyuyor — bu üçü farklı GICS sektörlerine (Enerji/Sağlık/Materials)
denk düşer ama KAP ince sınıflandırması bunu ayırmıyor. `explore_kap_sektor.py`
zaten TUPRS'yi bu kategoride canlı doğrulamıştı. Varsayılan eşleme (Ana
Metaller ve Madencilik) korunur, ama bilinen büyük istisnalar için elle
denetlenebilir bir override sözlüğü tutulmalı:

```python
KAP_TICKER_SECTOR_OVERRIDES: dict[str, str] = {
    "TUPRS": "Enerji",  # rafineri — KAP'ın "Kimya İlaç Petrol..." ince kategorisi
                          # bu şirketi ilaç/kimya şirketleriyle aynı kovaya koyuyor
}
```

---

## SIC → Üst-Sektör Eşleme Tablosu (NASDAQ)

Kaynak: SEC'in resmi SIC kod listesi (`sec.gov/corpfin/division-of-corporation-
finance-standard-industrial-classification-sic-code-list`, bu oturumda canlı
çekildi, "SIC Code / Office / Industry Title" üç kolonlu ~450 satır) + proje
evrenindeki 10 resmi NASDAQ hissesinin TAMAMI CANLI SIC koduyla doğrulandı:

| Ticker | SIC | `sicDescription` (CANLI) | Üst-sektör |
|---|---|---|---|
| AAPL | 3571 | Electronic Computers | Teknoloji |
| NVDA | 3674 | Semiconductors & Related Devices | Teknoloji |
| AMD | 3674 | Semiconductors & Related Devices | Teknoloji |
| MSFT | 7372 | Services-Prepackaged Software | Teknoloji |
| GOOGL | 7370 | Services-Computer Programming, Data Processing, Etc. | **İletişim (override)** |
| META | 7370 | Services-Computer Programming, Data Processing, Etc. | **İletişim (override)** |
| AMZN | 5961 | Retail-Catalog & Mail-Order Houses | Tüketici (Döngüsel) |
| TSLA | 3711 | Motor Vehicles & Passenger Car Bodies | Tüketici (Döngüsel) |
| NFLX | 7841 | Services-Video Tape Rental | İletişim |
| PYPL | 7389 | Services-Business Services, NEC | **Finans (override)** |

Bu 10 canlı sonuç, aralık-tabanlı varsayılan kuralın YETERSİZ kaldığı 3
somut örneği ortaya çıkardı: GOOGL/META SIC 7370'te (genel "bilgisayar
programlama" kovası) MSFT ile aynı kovaya düşüyor ama GICS'te Teknoloji değil
İletişim'dedir; PYPL'nin SIC 7389'u ("İş Hizmetleri, NEC") tamamen anlamsız
bir çöp-kutusu koddur, gerçek iş modeli (ödeme işleme) Finans'tır. **Sonuç:**
SIC aralık tablosu TEK BAŞINA yeterli değildir — ticker-düzeyi bir override
sözlüğü ZORUNLUDUR (aşağıda). Bu, sektor-siniflandirma skill'inin "elle
denetlenebilir statik sözlük" ilkesiyle birebir örtüşüyor.

### Aralık tablosu (varsayılan, override yoksa uygulanır)

```python
# (SIC_min, SIC_max, üst_sektör) — kapsayıcı aralıklar, sırayla denenir,
# ilk eşleşen kullanılır. SEC'in resmi major-group yapısına dayanır.
SIC_RANGE_TO_UST_SEKTOR: list[tuple[int, int, str]] = [
    (100, 999, "Tüketici (Temel)"),        # Tarım/ormancılık/balıkçılık
    (1000, 1099, "Ana Metaller ve Madencilik"),  # Metal madenciliği
    (1200, 1299, "Enerji"),                # Kömür/linyit
    (1300, 1399, "Enerji"),                # Ham petrol ve doğalgaz
    (1400, 1499, "Ana Metaller ve Madencilik"),  # Metalik olmayan maden
    (1500, 1799, "Sanayi"),                # İnşaat
    (2000, 2199, "Tüketici (Temel)"),      # Gıda/tütün
    (2200, 2299, "Tüketici (Döngüsel)"),   # Tekstil
    (2300, 2399, "Tüketici (Döngüsel)"),   # Giyim
    (2400, 2499, "Ana Metaller ve Madencilik"),  # Kereste/ahşap
    (2500, 2599, "Tüketici (Döngüsel)"),   # Mobilya
    (2600, 2699, "Ana Metaller ve Madencilik"),  # Kağıt
    (2700, 2799, "İletişim"),              # Basım/yayıncılık
    (2830, 2836, "Sağlık"),                # İlaç/biyolojik ürünler (kimya alt kümesi)
    (2800, 2899, "Ana Metaller ve Madencilik"),  # Diğer kimyasallar (2830-2836 YUKARIDA öncelikli)
    (2900, 2999, "Enerji"),                # Petrol rafinaj
    (3000, 3099, "Sanayi"),                # Kauçuk/plastik
    (3100, 3199, "Tüketici (Döngüsel)"),   # Deri
    (3200, 3299, "Ana Metaller ve Madencilik"),  # Taş/kil/cam
    (3300, 3399, "Ana Metaller ve Madencilik"),  # Ana metal
    (3400, 3499, "Sanayi"),                # İşlenmiş metal ürünler
    (3570, 3579, "Teknoloji"),             # Bilgisayar donanımı (AAPL burada)
    (3500, 3599, "Sanayi"),                # Diğer makine (3570-3579 YUKARIDA öncelikli)
    (3660, 3679, "Teknoloji"),             # Elektronik/haberleşme donanımı, yarı iletken
    (3600, 3699, "Sanayi"),                # Diğer elektrikli ekipman (3660-3679 öncelikli)
    (3711, 3711, "Tüketici (Döngüsel)"),   # Motorlu taşıtlar (TSLA)
    (3700, 3799, "Sanayi"),                # Diğer ulaşım ekipmanı (havacılık/savunma)
    (3826, 3851, "Sağlık"),                # Tıbbi/laboratuvar cihazları
    (3800, 3899, "Sanayi"),                # Diğer ölçüm/kontrol cihazları
    (3900, 3999, "Sanayi"),                # Diğer imalat
    (4000, 4599, "Sanayi"),                # Kara/hava/deniz taşımacılığı
    (4600, 4699, "Enerji"),                # Boru hatları
    (4700, 4799, "Sanayi"),                # Taşımacılık hizmetleri
    (4800, 4899, "İletişim"),              # Telefon/TV yayıncılık/kablo
    (4900, 4999, "Kamu Hizmetleri"),       # Elektrik/gaz/su
    (5000, 5199, "Tüketici (Döngüsel)"),   # Toptan ticaret
    (5400, 5499, "Tüketici (Temel)"),      # Gıda mağazaları
    (5200, 5999, "Tüketici (Döngüsel)"),   # Diğer perakende (5400-5499 öncelikli)
    (6000, 6099, "Finans"),                # Mevduat bankaları
    (6100, 6299, "Finans"),                # Kredi kuruluşları, aracı kurumlar
    (6300, 6499, "Finans"),                # Sigorta
    (6500, 6599, "Gayrimenkul/GYO"),       # Gayrimenkul
    (6798, 6798, "Gayrimenkul/GYO"),       # REIT (spesifik kod, 6700-6799'dan öncelikli)
    (6700, 6799, "Finans"),                # Diğer holding/yatırım ofisleri
    (7000, 7099, "Tüketici (Döngüsel)"),   # Otel/konaklama
    (7200, 7299, "Tüketici (Döngüsel)"),   # Kişisel hizmetler
    (7370, 7379, "Teknoloji"),             # Yazılım/BT hizmetleri (bkz. İSTİSNA override'lar)
    (7300, 7399, "Sanayi"),                # Diğer iş hizmetleri (7370-7379 öncelikli)
    (7500, 7599, "Tüketici (Döngüsel)"),   # Oto bakım/onarım
    (7800, 7899, "İletişim"),              # Sinema/video (NFLX burada)
    (7900, 7999, "Tüketici (Döngüsel)"),   # Eğlence/rekreasyon
    (8000, 8099, "Sağlık"),                # Sağlık hizmetleri
    (8200, 8299, "Tüketici (Döngüsel)"),   # Eğitim hizmetleri
    (8700, 8999, "Sanayi"),                # Mühendislik/muhasebe/diğer hizmetler
]
```

### Ticker-düzeyi override (SIC) — CANLI doğrulanmış istisnalar

```python
SIC_TICKER_SECTOR_OVERRIDES: dict[str, str] = {
    # GICS 2018 "Communication Services" ayrımı — bu şirketler SIC 7370'te
    # (genel "bilgisayar programlama") MSFT ile aynı kovaya düşüyor ama
    # reklam/medya odaklı iş modelleri İletişim'e denk düşer.
    "GOOGL": "İletişim", "GOOG": "İletişim", "GOOGM": "İletişim", "GOOGN": "İletişim",
    "META": "İletişim",
    # SIC 7389 ("İş Hizmetleri, NEC") anlamsız bir çöp-kutusu kod —
    # PYPL'nin gerçek iş modeli ödeme işleme (Finans - Transaction &
    # Payment Processing Services).
    "PYPL": "Finans",
}
```

**Kural sırası:** `SIC_TICKER_SECTOR_OVERRIDES[ticker]` varsa KULLANILIR; yoksa
`SIC_RANGE_TO_UST_SEKTOR` içinde ticker'ın SIC kodunu kapsayan İLK (en dar/en
özel) aralık kullanılır (yukarıdaki listede daha dar aralıklar KASITLI OLARAK
geniş aralıklarından ÖNCE yazıldı — örn. 2830-2836 → 2800-2899'dan önce).
Hiçbiri eşleşmezse `ust_sektor = None`, kart "N/A" gösterir (Kural 3 — None
yayılır).

---

## Şirket türü (`sirket_turu`) tanımı ve kaynağı

`sirket_turu`, ÜST-SEKTÖRDEN AYRI bir eksendir (persona kural 5): skor
şablonu seçimi için (sanayi/ticaret vs banka vs sigorta vs finansman vs GYO).
Bir GYO hem `ust_sektor="Gayrimenkul/GYO"` HEM `sirket_turu="gyo"` olabilir —
ikisi aynı bilgiyi taşıyormuş gibi görünse de kavramsal olarak ayrı
tutulmalıdır (ör. ileride bir GYO'nun asıl faaliyet konusu enerji varlıkları
olsa ust_sektor farklılaşabilir, sirket_turu hukuki/muhasebe yapısını
işaretler).

| `sirket_turu` değeri | BİST kaynağı | NASDAQ kaynağı |
|---|---|---|
| `sanayi` | `financial_group == "XI_29"` (analiz sonrası) VEYA KAP ince sektör Finans/Gayrimenkul/GYO grubunda DEĞİLSE (analiz öncesi tahmin) | SIC 6000-6999 ve 6798 DIŞINDA HER ŞEY |
| `banka` | `financial_group in ("UFRS", "UFRS_KATILIM")` | SIC 6000-6099 (mevduat bankaları) |
| `sigorta` | `financial_group == "UFRS_K"` | SIC 6300-6499 |
| `finansman` | `financial_group == "XI_29K"` | SIC 6100-6299 (6798 hariç) |
| `gyo` | KAP ince sektör `GAYRİMENKUL YATIRIM ORTAKLIKLARI` (analiz öncesi de kesin bilinir — İş Yatırım'a gitmeye gerek YOK) | SIC 6500-6599, 6798 |

**Önemli asimetri:** BİST tarafında `sirket_turu` iki kaynaktan gelebilir —
(a) KAP ince sektöründen HEMEN (evren-doldurma anında, hiçbir analiz
gerektirmeden: banka/sigorta/finansman/GYO kategorileri KAP'ta zaten ayrık),
(b) `financial_group`'tan KESİN olarak (ama SADECE şirket en az bir kez
analiz edildikten SONRA dolar). Öneri: evren-doldurma anında KAP'tan
ÖN-TAHMİN yaz (`sirket_turu` + bir iç bayrak, örn. bu spec'te ayrı bir kolon
ÖNERİLMEDİ ama uygulama fazında `sirket_turu_kaynak` gibi bir alan
düşünülebilir); `financial_group` dolduğunda (pipeline zaten
`set_company_info` çağırıyor) `sirket_turu` financial_group'tan YENİDEN
türetilip ÜZERİNE YAZILIR (KAP tahmini > analiz sonrası kesin veri yerine
GEÇER). NASDAQ tarafında böyle bir belirsizlik YOK — SIC kodu tek kaynaktır.

---

## Company modeline eklenecek alanlar

`src/db/models.py::Company` (satır 37-51) incelendi. **Mevcut `sector` alanı
KORUNUR ve DEĞİŞTİRİLMEZ** — bu alan zaten KAP'ın ince sektör adını taşıyor
(`update_company_sectors`, `get_sector_peer_tickers`, `valuation.py` ve
`pipeline.py` bunu OKUYOR) ve semantik olarak bu spec'in "alt_sektör" kavramına
BİREBİR karşılık geliyor — yeniden adlandırmak (örn. `alt_sektor`'a rename)
onlarca çağrı noktasını kırar, hiçbir fayda sağlamaz (persona kural 8: geriye
uyumlu genişlet). Bunun yerine `sector` alanının kullanım alanı NASDAQ'ı da
kapsayacak şekilde GENİŞLETİLİR (`sicDescription` buraya yazılır).

Yeni alanlar (`_migrate_add_market_column` ile AYNI idempotent ALTER TABLE
deseni; hepsi nullable, mevcut satırlarda NULL kalır, geriye dönük KIRILMAZ):

```python
class Company(Base):
    __tablename__ = "company"
    # ... mevcut alanlar (ticker, name, sector, financial_group,
    #     kap_member_id, last_updated, market) DEĞİŞMEDİ ...

    # --- Faz 2 (sektör/evren) -- YENİ alanlar ---
    ust_sektor: Mapped[str | None] = mapped_column(String(40))
    # Ortak 11-grup taksonomi değeri (bkz. "Ortak üst-sektör taksonomisi").
    # `sector` (=alt_sektor, ince) alanından KAP/SIC eşleme tablolarıyla türetilir.

    sirket_turu: Mapped[str | None] = mapped_column(String(20))
    # "sanayi" | "banka" | "sigorta" | "finansman" | "gyo" -- skor şablonu
    # seçimi için (bkz. "Şirket türü tanımı" bölümü). financial_group'tan
    # AYRI bir alan: financial_group BIST'e özel veri-çekim şeması etiketidir
    # (İş Yatırım API parametresi), sirket_turu piyasa-bağımsız ortak eksendir.

    sic_code: Mapped[str | None] = mapped_column(String(10))
    # NASDAQ icin SEC'in ham SIC kodu (orn. "3674"). Sadece market="NASDAQ"
    # icin doldurulur -- traceability/yeniden-turetme icin saklanir (SIC
    # aralik tablosu ileride degisirse SEC'e TEKRAR gitmeden ust_sektor
    # yeniden hesaplanabilir).

    exchange: Mapped[str | None] = mapped_column(String(20))
    # SEC company_tickers_exchange.json'daki ham deger (orn. "Nasdaq",
    # "NYSE"). "NASDAQ evreni" filtresi BUNDAN yapilir (bkz. Tazelik/
    # checkpoint bolumu). BIST satirlarinda None kalir (market="BIST" zaten
    # yeterli, ayri bir BIST "exchange" kavrami yok).

    cik: Mapped[str | None] = mapped_column(String(10))
    # NASDAQ icin SEC CIK'i (10 haneye sifirla doldurulmus). sec_edgar.py
    # zaten her cagride resolve_cik() ile bunu COZUYOR (24 saatlik dosya
    # onbellegiyle) -- burada saklamak toplu is (refresh_universe.py)
    # sirasinda TEKRAR ticker-map aramasi yapmayi gereksiz kilar, DB'den
    # dogrudan okunabilir.

    index_memberships: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # Orn. ["BIST30", "BIST100"] (BIST) -- NASDAQ icin bu fazda VERI KAYNAGI
    # YOK (bkz. Veri Bagimliligi), bu yuzden NASDAQ satirlarinda hep None/[]
    # kalir; alan yine de EKLENIR (semaya sonradan eklemek migration
    # gerektirir, simdiden acmak ucretsiz).

    sector_updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    # `last_updated` (finansal veri tazeligi, is_data_fresh()) ile KARISTIRILMAMALI
    # -- sektor/evren verisi AYRI bir tazelik penceresine sahiptir (bkz.
    # Tazelik bolumu, cok daha uzun: gunler degil, haftalar/aylar).
```

**Şema çakışması kontrolü:** `Company`'nin mevcut hiçbir alanı (`sector`,
`financial_group`, `kap_member_id`, `last_updated`, `market`) bu yeni
alanlarla İSİM ya da ANLAM çakışmıyor. `FinancialPeriod`, `Disclosure`,
`CommentaryCache`, `EarningsCalendar`, `Fund*`, `GeneratedCard` modelleri
sektörle İLGİSİZ, dokunulmuyor.

**Migration:** `models.py`'deki mevcut desenle (`_migrate_add_market_column`,
`_migrate_add_commentary_hook_column`) BİREBİR aynı idempotent yaklaşım:
yeni bir `_migrate_add_sector_taxonomy_columns(engine)` fonksiyonu, her sütun
için `ALTER TABLE company ADD COLUMN ...` (sütun zaten varsa atla), `init_db()`
içine `create_all()` SONRASINA eklenir. SQLite JSON sütunu TEXT affinity ile
çalışır (`CommentaryCache.positives` zaten aynı deseni kullanıyor — emsal var).

---

## Sektör-içi normalizasyon kuralları (Faz 3 bağımlılığı — burada SADECE referans)

sektor-siniflandirma skill madde 1-5 birebir geçerli: n≥5 kuralı, robust
istatistik (medyan+MAD, %5-%95 winsorize), mutlak taban/tavanla harmanlama,
dönem-bazlı DB cache, banka/sigorta ayrı havuz. **Bu spec'in sorumluluğu
DEĞİL** — Faz 3'ün "temel-analiz-cercevesi" spec'i bu kuralları somut
formüllere (hangi tablo, hangi sorgu) dökecek. Burada sadece şu bağımlılık
NOT edilir: Faz 3'teki n≥5 hesaplaması `(ust_sektor, sirket_turu)` çiftini
GRUPLAMA anahtarı olarak kullanmalı (`(sector, financial_group)` DEĞİL —
mevcut `get_sector_peer_tickers` BİST-ince-sektör bazlı çalışıyor ve NASDAQ'ı
hiç KAPSAMIYOR; Faz 3 bunu `ust_sektor`+`sirket_turu` bazlı, İKİ piyasayı
BİRLİKTE gören bir sorguya genişletmeli).

**Mevcut sınırlama tespiti (bilgi amaçlı, bu fazda DÜZELTİLMİYOR):**
`repository.get_sector_peer_tickers()` şu an n≥5 kontrolü YAPMIYOR — kaç
peer bulursa (0 dahil) onu döndürüyor, `valuation.py` bunu doğrudan
kullanıyor. sektor-siniflandirma skill'in "peer karşılaştırma geçmişte sahte
kesinlik nedeniyle kaldırıldı" notuyla ÇELİŞEN canlı bir kod yolu bu —
Faz 3'e taşınacak bir bulgu olarak burada işaretlendi.

---

## Tazelik ve checkpoint tasarımı (`scripts/refresh_universe.py`)

### BİST kolu (basit — tek istek, rate-limit riski yok)

1. `kap.fetch_sector_map()` çağrılır (TEK istek, ~640 şirket).
2. Dönen HER `(ticker, ince_sektör)` çifti için: `Company` satırı YOKSA
   oluşturulur (`market="BIST"`, `financial_group=None` — henüz analiz
   edilmemiş olabilir); `sector`, `ust_sektor` (KAP eşleme tablosuyla
   türetilir), `sirket_turu` (KAP ince sektör Finans/GYO grubundaysa KESİN,
   değilse `"sanayi"` ÖN-TAHMİNİ — bkz. yukarıdaki asimetri notu),
   `sector_updated_at=utcnow_naive()` güncellenir.
3. Bu tek-istek doğası gereği checkpoint GEREKMEZ — script başından sonuna
   tek seferde tamamlanır (mevcut `_ensure_sector_populated` ile AYNI çağrı,
   fark: TÜM evreni proaktif doldurur, sadece eksik tek şirketi değil).

### NASDAQ kolu (büyük evren — checkpoint ZORUNLU)

**Adım 1 — ucuz bulk keşif (rate-limit riski YOK, tek istek):**
`company_tickers_exchange.json` çekilir, `exchange == "Nasdaq"` filtrelenir
(CANLI doğrulandı: değer tam olarak `"Nasdaq"` string'i, `"NASDAQ"` DEĞİL —
karşılaştırma case-sensitive yapılmamalı ya da normalize edilmeli). Bu adım
TÜM NASDAQ evreninin (~4000+ ticker tahmini) `(ticker, cik, exchange)`
üçlüsünü DB'ye bare `Company` satırları olarak yazar (`sic_code=None`,
`ust_sektor=None` — henüz zenginleştirilmedi). Bu adım da checkpoint GEREKMEZ
(tek bulk dosya, SEC rate limitine tabi DEĞİL çünkü tek istek).

**Adım 2 — pahalı per-company zenginleştirme (rate-limit'e tabi, ÇOK istekli,
checkpoint ZORUNLU):** Her ticker için `submissions/CIK{cik}.json` çağrılır
(SIC kodu BAŞKA hiçbir bulk uç noktada YOK — `companyfacts` bile SIC
taşımıyor, doğrulandı). Bu, DB'nin KENDİSİNİ checkpoint olarak kullanan bir
tasarımla çözülür (yeni bir dosya/tablo GEREKMEZ, mevcut `is_data_fresh`
felsefesiyle TUTARLI):

```python
# Is kuyrugu = "sic_code IS NULL VEYA sector_updated_at cok eski" olan
# NASDAQ satirlari. Script her calistiginda bu kuyruktan bir PARTI (--limit,
# varsayilan 500) isler; SIGINT/crash/rate-limit hatasinda islenen satirlar
# ZATEN commit edilmis oldugundan bir SONRAKI calistirma KALDIGI YERDEN
# devam eder -- ayri bir checkpoint dosyasi/tablosu GEREKMEZ.
SECTOR_STALE_AFTER_DAYS = 90  # sektor/SIC nadiren degisir, gunluk yenileme GEREKSIZ

def _next_batch(session, limit: int) -> list[Company]:
    cutoff = utcnow_naive() - timedelta(days=SECTOR_STALE_AFTER_DAYS)
    return session.execute(
        select(Company)
        .where(
            Company.market == "NASDAQ",
            or_(Company.sic_code.is_(None), Company.sector_updated_at < cutoff),
        )
        .order_by(Company.sector_updated_at.asc().nullsfirst())
        .limit(limit)
    ).scalars().all()
```

3. Her satır için: `submissions/CIK{cik}.json` çağrılır (SEC 10 istek/sn
   limitine saygı için istekler arasında **0.12 sn** bekleme — mevcut
   `HTTP_RATE_LIMIT_DELAY_SECONDS=1.0` retry-backoff içindir, bu YENİ ve AYRI
   bir sabit: `SEC_BULK_PACING_SECONDS`, sadece toplu tarama script'lerinde
   kullanılır, tekil ticker analiz akışını ETKİLEMEZ). `sic`, `sicDescription`
   okunur; `SIC_TICKER_SECTOR_OVERRIDES` → yoksa `SIC_RANGE_TO_UST_SEKTOR` →
   `sirket_turu` (SIC aralığından) → `sector_updated_at=utcnow_naive()`.
4. 404/CompanyNotFoundError (bazı ticker'lar XBRL raporlamıyor olabilir) →
   satır atlanır ama `sector_updated_at` YİNE DE güncellenir (aksi halde
   kuyruk SONSUZ döngüye girer) — `sic_code=None` kalıcı olarak işaretlenir,
   kart bu ticker için `ust_sektor="N/A"` gösterir.
5. CLI: `python scripts/refresh_universe.py --market nasdaq --limit 500`
   (BİST için `--market bist`, argüman verilmezse ikisi de çalışır — BİST
   ucuz olduğu için her seferinde tam taranır, NASDAQ `--limit` ile
   kademeli). "Kademeli doldur" ilkesi (sektor-siniflandirma skill) BÖYLECE
   sağlanır: ilk çalıştırmalar kuyruğu boşaltır, sonraki çalıştırmalar
   sadece 90 günden eski/hiç işlenmemiş satırları yeniler.

**Zamanlama önerisi:** cron/manuel — BİST günlük (ucuz), NASDAQ zenginleştirme
adımı günde bir kez `--limit 500` ile (mevcut `refresh_takvim_cache.py`/
`refresh_sector_cache.py` referanslarıyla AYNI "ayrı zamanlanmış süreç, ana
pipeline'ı bloklamaz" ilkesi — bu script de `run_pipeline`'ın DIŞINDA,
bağımsız çalışır).

---

## Kenar durumlar

- **KAP ince sektörü bilinmeyen/yeni bir kategori:** `KAP_SEKTOR_TO_UST_SEKTOR`
  sözlüğünde YOKSA `ust_sektor=None` (uydurma YAPILMAZ, Kural 3). Log
  seviyesinde uyarı — KAP yeni bir sektör eklerse (nadir ama olası) elle
  tabloya eklenmesi gerekir.
- **SIC kodu aralık tablosundaki hiçbir aralığa düşmüyor** (örn. 9100+ kamu
  idaresi kodları, halka açık şirketlerde NADİR): `ust_sektor=None`.
- **Ticker hem BİST hem NASDAQ'ta kayıtlı görünüyor (sembol çakışması):**
  `TickerMarketConflictError` zaten mevcut (`repository.py`) — bu spec'in
  evren-doldurma script'i de AYNI hatayı fırlatmalı, sessizce EZMEMELİDİR.
- **`exchange` alanı `"Nasdaq"` DIŞINDA bir değer (örn. "NYSE", "NYSE
  American", "CBOE") taşıyorsa:** Adım 1'de bu satırlar HİÇ DB'ye yazılmaz
  (evren dışı) — "NASDAQ-listeli" kapsamı netliği burada UYGULANIR.
- **Bir NASDAQ şirketi ADR/yabancı özel ihraççı (B21 — NVO/TSM/SHEL gibi,
  `sec_edgar.py`'de zaten bilinen bir durum):** SIC kodu YİNE DE submissions
  API'sinden gelir (companyfacts'ten BAĞIMSIZ bir uç nokta), bu yüzden
  ifrs-full/us-gaap ayrımı bu spec'i ETKİLEMEZ.
- **`sector_updated_at` dolu ama `sic_code` None (404 sonrası kalıcı
  işaretleme):** kart "N/A" gösterir, script bu satırı BİR DAHA
  `SECTOR_STALE_AFTER_DAYS` dolana kadar TEKRAR denemez (gereksiz SEC
  isteği önlenir).

---

## Veri bağımlılığı

- **Endeks üyeliği (BIST30/BIST100):** Bu fazda CANLI bir kaynak
  DOĞRULANMADI. Adaylar: İş Yatırım'ın endeks bileşen uç noktası (mevcut
  `isyatirim.py` bunu ÇEKMİYOR, ayrı bir keşif gerekir) veya KAP'ın kendi
  endeks sayfası. `index_memberships` alanı ŞİMDİDEN şemaya eklenir (ucuz)
  ama DOLDURMA mekanizması bu spec'in kapsamı DIŞINDA — ayrı bir keşif
  görevi (`scripts/explore_bist_endeks.py` tarzı) gerektirir.
- **NASDAQ endeks üyeliği (S&P 500, Nasdaq-100 vb.):** Hiç ele alınmadı,
  proje evreninde (10 sabit ticker) şu an gerekmiyor.
- **KAP `mainSectorName` (kaba sektör):** Canlı çekimde bu alan ADI
  gözlemlendi ama regex deseni (`kap.py`'deki mevcut desen, ince sektöre
  odaklı) bu oturumda AYRIŞTIRILAMADI — ihtiyaç olursa ayrı bir keşif
  gerekir. Bu spec'te KULLANILMADI (ince sektör zaten üst-sektöre yeterince
  ayrıntılı eşleniyor).

---

## Test senaryoları

1. `KAP_SEKTOR_TO_UST_SEKTOR` içindeki her 48 anahtar için değerin 11 geçerli
   üst-sektör isminden biri olduğu (typo/eksik eşleme yakalar).
2. `SIC_RANGE_TO_UST_SEKTOR` aralıklarının ÇAKIŞMADIĞI (her SIC kodu EN FAZLA
   bir aralığa düşmeli, "en dar aralık önce" kuralı test edilir — örn. 3674
   → Teknoloji [3660-3679], 3300 → Materials [3300-3399] AMA 3300 aynı
   zamanda [3200-3299]'e DÜŞMEMELİ).
3. 10 resmi NASDAQ ticker'ının (AAPL/TSLA/NVDA/MSFT/GOOGL/AMZN/META/NFLX/
   AMD/PYPL) bu spec'teki tabloda listelenen SIC koduyla doğru
   `ust_sektor`'a eşlendiği (regresyon testi — canlı doğrulanmış değerler
   sabit test verisi olarak kullanılır, SEC'e gitmez).
4. `SIC_TICKER_SECTOR_OVERRIDES`'ın aralık tablosundan HER ZAMAN önce
   uygulandığı (GOOGL/META/PYPL için).
5. `_next_batch()` sorgusunun: (a) `sic_code IS NULL` satırları döndürdüğü,
   (b) `sector_updated_at` 90 günden eski satırları da döndürdüğü, (c) taze
   satırları DÖNDÜRMEDİĞİ, (d) `limit` parametresine uyduğu.
6. Migration idempotentliği: `_migrate_add_sector_taxonomy_columns` iki kez
   art arda çağrıldığında hata VERMEDİĞİ (mevcut `_migrate_add_market_column`
   testleriyle AYNI desen).
7. `TickerMarketConflictError`'ın evren-doldurma script'inde de (mevcut
   `_get_or_create_company` yolu üzerinden) fırlatıldığı.
8. Sınır: KAP'ın 48 kategorisinde OLMAYAN uydurma bir sektör adı verildiğinde
   `ust_sektor=None` dönüp exception FIRLATILMADIĞI.
