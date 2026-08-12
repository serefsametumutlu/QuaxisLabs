# SPEC: Sektör Taksonomisi İnceltme — Havacılık Ekosistemi ve Benzer Bulgular

## Amaç ve kapsam

**Ölçtüğü soru:** THYAO/PGSUS/TAVHL/ÇELEBİ kullanıcı tarafından "aynı
sektör" olarak algılanıyor ama mevcut mimaride (`src/fetchers/kap.py::
KAP_SEKTOR_TO_UST_SEKTOR`) ya geniş "Sanayi" üst-sektörüne dağılıyor ya da
(TAVHL'de olduğu gibi) HİÇ oraya bile düşmüyor — bu spec bu somut şikayeti
**CANLI veri ile doğrular**, iki mimari çözümü (yeni 12. üst-sektör grubu vs
görsel-amaçlı alt-etiket) karşılaştırır, ve `.claude/skills/sektor-
siniflandirma/SKILL.md` madde 1'in n≥5 kısıtıyla UYUMLU somut bir öneri
sunar. Bu spec `docs/spec/spec_sektor_evren.md`'nin (Faz 2, taksonomi
inşası) **üzerine** oturur, onu DEĞİŞTİRMEZ — o dosyanın 11-grup üst-
sektör taksonomisi ve KAP/SIC eşleme tabloları TEMEL alınır.

**Geçerli şirket türleri / piyasalar:** BİST (KAP kaynaklı), bu tur
NASDAQ'a dokunmuyor (kullanıcının somut örnekleri BİST-özel).

**Kod içermez, sadece bulgu + öneri + kod-geliştiriciye devredilebilir
adımlar.**

---

## Kaynaklar (CANLI doğrulandı, bu oturumda)

1. `src/fetchers/kap.py::KAP_SEKTOR_TO_UST_SEKTOR` (satır 416-482) — statik
   sözlük, CANLI okundu: `"ULAŞTIRMA VE DEPOLAMA": "Sanayi"`.
2. `data/exploration/kap_sektor_map.json` — KAP'ın `fetch_sector_map()`
   uç noktasının CANLI çekilmiş TAM dökümü (~640 BİST şirketi, ticker→ince
   sektör). Bu dosya `spec_sektor_evren.md`'nin KENDİ KAP→üst-sektör eşleme
   tablosunu türetirken kullandığı AYNI kaynak — bu spec de AYNI dosyayı
   kanonik kabul eder (proje mimarisiyle TUTARLI, DB'ye ayrı bir salt-okuma
   sorgusu GEREKMEDİ çünkü bu dosya `Company.sector` alanının doğrudan
   kaynağıdır ve DB'deki güncel değerle birebir örtüşür).
3. WebSearch (bu oturumda, 5 sorgu) — KAP'ın "ULAŞTIRMA VE DEPOLAMA"
   kategorisindeki 12 şirketin GERÇEK iş modelini doğrulamak için (KAP'ın
   ince sektör adı tek başına iş modelini AYIRT ETMİYOR, bkz. aşağı).
4. `.claude/skills/sektor-siniflandirma/SKILL.md` madde 1 (n≥5 kuralı).

---

## Bulgu 1 — "ULAŞTIRMA VE DEPOLAMA" kategorisinin GERÇEK bileşimi

KAP'ın ince sektör sınıflandırmasında bu kategoriye düşen **12 BİST
şirketi** (CANLI liste, `kap_sektor_map.json`):

| Ticker | KAP'taki tam unvan (WebSearch doğrulamalı) | Gerçek iş modeli | Havacılık ekosistemi mi? |
|---|---|---|---|
| THYAO | Türk Hava Yolları | Havayolu (yolcu/kargo taşımacılığı) | **EVET** |
| PGSUS | Pegasus Hava Taşımacılığı | Havayolu (düşük maliyetli taşıyıcı) | **EVET** |
| CLEBI | Çelebi Hava Servisi | Havalimanı yer hizmetleri | **EVET** |
| BEYAZ | Beyaz Filo Oto Kiralama | Kara — araç/filo kiralama | Hayır |
| GRSEL | Gür-Sel Turizm Taşımacılık | Kara — yolcu/otobüs taşımacılığı | Hayır |
| GSDDE | GSD Denizcilik | Deniz — kuru yük gemi taşımacılığı | Hayır |
| HOROZ | Horoz Lojistik | Kara/demiryolu — lojistik, depolama, dağıtım | Hayır |
| HRKET | Hareket Proje Taşımacılığı ve Yük Mühendisliği | Ağır/proje kargo mühendisliği (kara/deniz/hava KARIŞIK, ağırlık kara) | Hayır (kısmi hava bileşeni var ama ÇEKİRDEK iş değil) |
| PASEU | Pasifik Eurasia Lojistik Dış Ticaret | Çok-modlu (kara/deniz/demiryolu ağırlıklı) taşımacılık/dış ticaret | Hayır |
| RYSAS | Reysaş Lojistik | Kara — karayolu taşımacılığı, depolama | Hayır |
| TLMAN | Trabzon Liman İşletmeciliği | Deniz — liman/limanı işletmeciliği | Hayır |
| TUREX | Tureks Turizm Taşımacılık | Kara — turizm/yolcu taşımacılığı | Hayır |

**Sonuç: 12 şirketten SADECE 3'ü (THYAO/PGSUS/CLEBI) gerçek havacılık
ekosistemi üyesi; 9'u kara/deniz taşımacılığı, lojistik/depolama veya
liman işletmeciliği** — kullanıcının sezgisiyle TUTARLI: "ULAŞTIRMA VE
DEPOLAMA" adı altında GERÇEKTEN farklı 3 alt-sektör (havacılık, kara,
deniz/liman) karışık duruyor.

---

## Bulgu 2 — TAVHL bu kategoride BİLE DEĞİL (daha ciddi bir sorun)

CANLI veri: `"TAVHL": "HOLDİNGLER VE YATIRIM ŞİRKETLERİ"` (satır 557,
`kap_sektor_map.json`) → `KAP_SEKTOR_TO_UST_SEKTOR` üzerinden **`ust_sektor
= "Finans"`**. Yani TAV Havalimanları Holding şu an istatistiksel olarak
THYAO/PGSUS/CLEBI'nin (Sanayi) yanında BİLE DEĞİL — **bankalar, sigorta
şirketleri, aracı kurumlar VE gerçek çok-sektörlü holding'lerle (KCHOL,
SAHOL) AYNI havuzda** karşılaştırılıyor. Bu, "geniş Sanayi'de kaybolma"
şikayetinden **daha ciddi** bir durum: TAVHL'nin sektöre-göreli F/K/PD-DD
konumu şu an bankaların/sigortacıların çarpanlarıyla kıyaslanıyor — bir
havalimanı işletmecisinin ekonomik yapısıyla (yolcu trafiği, imtiyaz bazlı
capex, havacılık dışı gelir) HİÇBİR ilgisi yok.

**Kök neden:** KAP'ın ince sektör taksonomisi, TAV Havalimanları'nın hukuki
yapısını (bir "Holding" şirketi — birden çok ülkede havalimanı işleten
bağlı ortaklıkları var) tek iş kolu OLMAYAN çok-sektörlü bir yatırım
holdingiyle (KCHOL/SAHOL tipi) AYNI kovaya koyuyor — hukuki KABUK (holding
yapısı) ile GERÇEK iş modeli (tek-iş: havalimanı işletmeciliği) arasındaki
FARK burada somutlaşıyor. WebSearch bu bulguyu DIŞ kaynaklarla da
doğruladı: fintables.com TAVHL'yi kendi rakip-analizi sayfasında
`/ulastirma` (ulaştırma) yoluna koyuyor — yani üçüncü taraf platformlar
BİLE KAP'ın "Holdingler" etiketini TAKİP ETMİYOR, kendi düzeltmelerini
yapıyorlar.

---

## Bulgu 3 — n≥5 kısıtı: "Havacılık" GERÇEKTEN kaç şirket?

En cömert tanımla bile (havayolu + yer hizmetleri + havalimanı işletmeciliği
— kullanıcının kendi 4 örneği) BİST'te toplam **n=4**: THYAO, PGSUS, CLEBI,
TAVHL. `sektor-siniflandirma` skill madde 1 ("n≥5 şirket yoksa sektör
karşılaştırması DEVRE DIŞI") gereği **bu grup HER ZAMAN "yetersiz örneklem"
uyarısıyla çalışacaktır** — ne YENİ bir 12. üst-sektör grubu açılsa ne de
BAŞKA bir yöntem denense, **istatistiksel karşılaştırma bu n ile ASLA
anlamlı hale gelmez** (mevcut mekanizma bunu zaten doğru şekilde işaretler,
bkz. Öneri bölümü). Havacılığa daha komşu bir kategori (SAVUNMA — ASELS/
ALTNY/ONRYT/SDTTR) eklenerek n≥5'e ulaşmak DENENMEDİ — çünkü savunma
sanayii ekonomisi (devlet ihaleleri/bütçeleri, elektronik/silah üretimi)
ticari havacılıkla (yolcu trafiği/yakıt maliyeti/turizm döngüselliği)
YAPISAL OLARAK farklıdır; bunu zorlamak "anlamlı grup" ilkesini çiğner,
sadece n rakamını KOZMETİK olarak yükseltirdi — persona kural 3'ün
"sahte kesinlik yasak" ilkesine DOĞRUDAN AYKIRI olurdu.

---

## Ödünleşim analizi — iki mimari seçenek

### Seçenek A: Yeni 12. üst-sektör grubu ("Havacılık")

`ust_sektor` alanına THYAO/PGSUS/CLEBI/TAVHL için "Havacılık" değeri
yazılır (mevcut 11-grup GICS-sadeleştirilmiş listeye EK).

- **Artı:** Dashboard'un `_build_sectors()` gruplaması (satır 507-529,
  `src/render/dashboard.py`) OTOMATİK olarak bu 4 şirketi ayrı bir başlık
  altında gösterir, sıfır ek kod GEREKTİRMEZ (mevcut gruplama zaten
  `row.ust_sektor` okuyor).
- **Eksi (BÜYÜK):** `ust_sektor` AYNI ZAMANDA `valuation.py`'nin
  istatistiksel sektör-göreli hesaplamasının (F/K/PD-DD medyan/MAD,
  `spec_mercek_deger.md` §Sektör ayarlaması) GRUPLAMA anahtarıdır — bu
  alanı değiştirmek o hesaplamayı da DEĞİŞTİRİR. n=4 olduğu için bu YENİ
  grup **HER ZAMAN** "yetersiz örneklem" durumuna düşer — yani Bulgu 3'ün
  gösterdiği gibi, hiçbir GERÇEK istatistiksel kazanım SAĞLAMAZ, sadece
  4 şirketi geniş "Sanayi"nin (n çok daha büyük, ANLAMLI karşılaştırma
  sağlayan) istatistiksel havuzundan ÇIKARIR — net etki: THYAO/PGSUS/CLEBI
  için istatistiksel karşılaştırma kalitesi AZALIR (önce n-büyük Sanayi
  havuzuyla mutlak+göreli harman vardı, şimdi SADECE mutlak eşiklerle baş
  başa kalırlar, göreli bileşen ağırlığı otomatik mutlak tarafa
  kayar — bkz. `spec_mercek_deger.md` §Sektör ayarlaması madde 4). Ayrıca
  `_build_sectors()`, `sektor-siniflandirma` skill referansları, olası
  başka "11 grup" varsayımlı downstream kod (test/dokümantasyon) 12.
  bir grupla GÜNCELLENMELİDİR — kapsam GENİŞ.

### Seçenek B: Görsel-amaçlı alt-etiket (istatistiksel `ust_sektor` DOKUNULMAZ)

`Company`'ye YENİ, SADECE-görüntüleme amaçlı bir alan eklenir (öneri adı:
`ekosistem_etiketi`), ticker-bazlı statik bir sözlükle (mevcut
`KAP_TICKER_SECTOR_OVERRIDES` deseninin AYNISI) doldurulur:
`{"THYAO": "Havacılık", "PGSUS": "Havacılık", "CLEBI": "Havacılık",
"TAVHL": "Havacılık"}`. `ust_sektor` (istatistik) DEĞİŞMEZ — THYAO/PGSUS/
CLEBI "Sanayi" havuzunda (büyük n, ANLAMLI istatistik) kalır.

- **Artı:** İstatistiksel bütünlük KORUNUR (Seçenek A'nın eksisi burada
  YOK); dashboard `_build_sectors()` OPSİYONEL olarak bu etiketi bir
  ALT-BAŞLIK (Sanayi › Havacılık) ya da kart üzerinde bir rozet olarak
  gösterebilir — kullanıcının "aynı sektör olarak GÖRME" ihtiyacı
  KARŞILANIR, istatistiksel doğruluk FEDA EDİLMEZ; mimari değişiklik KÜÇÜK
  (tek yeni nullable kolon + statik sözlük, `spec_sektor_evren.md`'nin
  KENDİ `_migrate_add_sector_taxonomy_columns` idempotent deseniyle
  BİREBİR TUTARLI).
- **Eksi:** Kullanıcı "Havacılık" grubunu bir PEER SETİ (sektör-göreli F/K
  kıyası) olarak görmek isterse YİNE "yetersiz örneklem (n=4)" uyarısıyla
  karşılaşır — ama bu, Seçenek A'da DA aynı şekilde gerçekleşirdi (Bulgu 3),
  yani Seçenek B bu konuda HİÇBİR ŞEY KAYBETMİYOR, sadece B'nin dışında
  Seçenek A'nın GETİRDİĞİ ek istatistik-bozulma riskini TAŞIMIYOR.

### ÖNERİ: Seçenek B (görsel-amaçlı alt-etiket)

**Gerekçe (özet):** n=4 olduğu için Seçenek A'nın TEK potansiyel avantajı
(daha temiz istatistiksel peer seti) fiilen HİÇ gerçekleşmiyor — n≥5
tavanına HİÇBİR ZAMAN ulaşmıyor. Seçenek A'nın maliyeti (mimari kapsam,
"11 grup" varsayımlı downstream kod güncellemesi, THYAO/PGSUS/CLEBI'nin
MEVCUT geniş-ama-anlamlı Sanayi karşılaştırmasını KAYBETMESİ) hiçbir
KARŞILIK almadan ödenmiş olurdu. Seçenek B ise kullanıcının GERÇEK isteğini
(dashboard'da/kartta "bunlar aynı sektör" GÖRÜNMESİ) SIFIRA yakın riskle
karşılar.

---

## Kod-geliştiriciye devredilebilir somut adımlar

1. **TAVHL düzeltmesi (öncelik: YÜKSEK, düşük risk, Bulgu 2'nin somut
   çözümü):** `src/fetchers/kap.py::KAP_TICKER_SECTOR_OVERRIDES`'a
   `"TAVHL": "Sanayi"` eklenir — MEVCUT `"TUPRS": "Enerji"` deseninin
   BİREBİR aynısı (yeni bir mekanizma İCAT EDİLMİYOR). Bu, TAVHL'nin
   istatistiksel sektör-göreli konumunu bankalar/sigortacılardan
   ÇIKARIP en azından geniş Sanayi havuzuna (THYAO/PGSUS/CLEBI ile AYNI
   havuz) TAŞIR — Seçenek A/B kararından BAĞIMSIZ, HER İKİ senaryoda da
   yapılması gereken bir düzeltme.
2. **Görsel etiket (öncelik: ORTA, Seçenek B'nin uygulanması):**
   - `Company` modeline `ekosistem_etiketi: Mapped[str | None] =
     mapped_column(String(40))` eklenir — `spec_sektor_evren.md`'nin
     `_migrate_add_sector_taxonomy_columns` idempotent ALTER TABLE
     deseniyle AYNI şekilde migrate edilir (yeni bir migration fonksiyonu
     GEREKMEZ, mevcut fonksiyona bir sütun daha eklenir).
   - `kap.py`'ye `KAP_TICKER_EKOSISTEM_ETIKETI: dict[str, str] =
     {"THYAO": "Havacılık", "PGSUS": "Havacılık", "CLEBI": "Havacılık",
     "TAVHL": "Havacılık"}` eklenir (piyasa-bağımsız isimlendirme —
     NASDAQ'ta şu an eşdeğer bir örnek YOK ama alan ADI genel tutuldu,
     ileride gerekirse `sec_edgar.py` tarafında da doldurulabilir).
   - `scripts/refresh_universe.py`'nin BİST kolu bu sözlüğü `Company.
     ekosistem_etiketi`'ne yazacak şekilde GENİŞLETİLİR (mevcut sektör
     doldurma adımına PARALEL, `spec_sektor_evren.md` "BİST kolu" bölümü).
   - `src/render/dashboard.py::_build_sectors()` OPSİYONEL olarak bu
     etiketi bir alt-grup/rozet olarak gösterir (KESİN tasarım — tam
     ekranda nerede/nasıl görüneceği — bu spec'in kapsamı DIŞINDA, ayrı
     bir dashboard tasarım kararı gerektirir).
3. **`valuation.py`/`get_sector_peer_tickers` DOKUNULMAZ** — istatistiksel
   peer seti HER ZAMAN `(ust_sektor, sirket_turu)` okur, `ekosistem_
   etiketi` ASLA bu sorguya karışmaz (persona kural 3'ün "sahte kesinlik
   yasak" ilkesinin somut UYGULANMASI — n=4 ile istatistik ÜRETİLMEZ, sadece
   İSİMLENDİRME iyileştirilir).

---

## Kenar durumlar

- **THYAO/PGSUS/CLEBI zaten "Sanayi" ust_sektor'ünde, `ekosistem_etiketi`
  eklendikten sonra bile değişmiyor** — sadece DAHA fazla bilgi TAŞINIYOR,
  mevcut hiçbir davranış BOZULMUYOR (geriye uyumlu, persona kural 8).
- **Gelecekte n≥5'e ulaşılırsa** (yeni bir havayolu/yer-hizmeti/havalimanı
  IPO'su): bu, Seçenek A'yı YENİDEN gündeme getirecek doğal bir TETİKLEYİCİ
  noktasıdır — bu spec bunu KALICI bir "hayır" olarak DEĞİL, "şu an n
  yetersiz" olarak İŞARETLER, gelecekte n=5'e ulaşıldığında `ust_sektor`
  taksonomisinin 12. gruba genişletilmesi YENİDEN değerlendirilmelidir.
- **`ekosistem_etiketi` boş olan TÜM diğer BİST/NASDAQ şirketleri:** `None`
  kalır, kart/dashboard'da hiçbir ek rozet GÖSTERMEZ (Kural 3 ile tutarlı,
  uydurma etiket YOK).
- **HRKET/PASEU'nun KISMİ hava bileşeni:** Bu iki şirketin faaliyet konusu
  metninde "hava taşımacılığı" da GEÇİYOR (WebSearch bulgusu) ama ÇEKİRDEK
  işleri değil (proje kargo mühendisliği / çok-modlu lojistik) — bu spec
  onları BİLEREK "Havacılık" etiketine DAHİL ETMEDİ (kullanıcının kendi 4
  örneğiyle SINIRLI kalındı, spekülatif genişleme YAPILMADI, persona
  görev talimatı "aşırıya kaçma" notuyla TUTARLI). İleride bu ikisi için
  ayrı bir "Karma Lojistik" ara-etiket düşünülebilir ama bu turun kapsamı
  DIŞINDA bırakıldı.

---

## Benzer potansiyel iyileştirmeler (kullanıcının somut isteğine bitişik, 3 bulgu)

### 1. "HOLDİNGLER VE YATIRIM ŞİRKETLERİ" → "Finans" — TAVHL'nin kök nedeniyle AYNI desen, DAHA GENİŞ

CANLI veri, bu kategoride TAVHL DIŞINDA da benzer "hukuki kabuk gerçek işi
gizliyor" örnekleri gösteriyor: **SISE** (Şişecam) — cam/kimya
ÜRETİCİSİ, gerçek iş modeli AÇIKÇA "Ana Metaller ve Madencilik" (Materials)
sektörüne aittir, ama KAP'ta "Holding" unvanı taşıdığı için `ust_sektor=
"Finans"`e düşüyor. Buna karşılık **KCHOL** (Koç Holding) ve **SAHOL**
(Sabancı Holding) GERÇEKTEN çok-sektörlü, TEK bir baskın iş kolu OLMAYAN
yatırım holdingleridir — bunları "Finans" kovasında tutmak MAKUL bir
basitleştirmedir (GICS'in kendisi de saf çok-sektörlü konglomeralar için
iyi bir kutuya sahip değildir). **Bulgu:** sorun "Holding" kelimesinin
KENDİSİ değil, KAP'ın bu unvanı taşıyan şirketleri TEK bir kovaya
(gerçekten çeşitlendirilmiş olsun ya da olmasın) ATMASI. **Bu turda
AKSİYON ALINMADI** (kullanıcının somut isteği havacılıkla SINIRLIYDI) —
gelecekte `KAP_TICKER_SECTOR_OVERRIDES`'a `"SISE": "Ana Metaller ve
Madencilik"` gibi BENZER tekil düzeltmeler eklenmesi önerilir, TAVHL
düzeltmesiyle AYNI desenle (tek-iş-kollu, "Holding" unvanlı şirketler
tek tek incelenerek).

### 2. "KİMYA İLAÇ PETROL LASTİK VE PLASTİK ÜRÜNLER" — ilaç üreticileri Sağlık'tan KAYIP

Aynı CANLI taramada, bu kovada AÇIKÇA ilaç/farma odaklı isimler var: **DEVA**
(Deva Holding), **GENKM** (Gen İlaç), **SANFM** (Sanifarma), **ONCSM**
(Oncosem Onkoloji), **MEDTR** (Meditera) — hepsi `ust_sektor="Ana Metaller
ve Madencilik"`e düşüyor, oysa GICS'te ilaç üretimi AÇIKÇA "Sağlık" (Health
Care) sektörüdür (nitekim proje TABLOSUNDA "İNSAN SAĞLIĞI VE SOSYAL
HİZMETLER" kategorisi zaten "Sağlık"a eşleniyor — ama bu SADECE sağlık
HİZMETLERİ [hastane, MPARK/LKMNH tipi] şirketlerini kapsıyor, ilaç
ÜRETİCİLERİNİ DEĞİL). Bu, KAP'ın "KİMYA İLAÇ PETROL LASTİK VE PLASTİK
ÜRÜNLER" kovasının (spec_sektor_evren.md'nin KENDİ metninde zaten TUPRS
için "override" olarak işaretlenmiş bilinen bir sorunlu kova) TUPRS'den
BAĞIMSIZ İKİNCİ bir alt-karışımı — kimyasal/petrol/lastik/plastik
ÜRETİCİLERİ (AKSA, PETKM, BRISA, GUBRF, HEKTS — GERÇEKTEN "Ana Metaller ve
Madencilik") ile ilaç ÜRETİCİLERİ (DEVA, GENKM, SANFM, ONCSM, MEDTR —
"Sağlık" OLMALI) AYNI kovada. **Bu turda AKSİYON ALINMADI** (kapsam dışı),
ama TAVHL/SISE ile AYNI ÖNCELİK sınıfında, gelecek bir turda ticker-bazlı
override listesiyle (5 şirket, n≥5 kuralını bile TEK BAŞINA karşılayacak
büyüklükte bir "gerçek İlaç" alt-grubu potansiyeli TAŞIYOR — bu, havacılık
örneğinden FARKLI olarak, düzeltilirse GERÇEK bir istatistiksel kazanım
SAĞLAYABİLİR, çünkü n=5 tam sınırda) çözülmesi ÖNERİLİR.

### 3. Bankalar/GYO/Teknoloji-İletişim ayrımı — ZATEN DOĞRU, aksiyon GEREKMİYOR

Kullanıcının sorduğu diğer olası şüpheli örnekler CANLI kontrol edildi ve
**sorunsuz** bulundu: (a) **Bankalar** ÇİFT izole — hem `ust_sektor=
"Finans"` hem `sirket_turu="banka"` (financial_group UFRS/UFRS_KATILIM
üzerinden) AYRI bir eksende işaretleniyor, sektör-göreli karşılaştırma asla
sanayi havuzuyla KARIŞMIYOR (`spec_sektor_evren.md` "Şirket türü" bölümü,
zaten doğru tasarlanmış). (b) **GYO'lar** benzer şekilde ÇİFT izole
(`ust_sektor="Gayrimenkul/GYO"` + `sirket_turu="gyo"`), "GAYRİMENKUL
FAALİYETLERİ" (GYO OLMAYAN emlak şirketleri, örn. ADESE/SONME) ile AYNI
üst-sektörde ama `sirket_turu` FARKLI olduğu için skor şablonu YİNE
AYRIŞIYOR — kasıtlı ve MAKUL bir tasarım. (c) **Teknoloji/İletişim ayrımı**
GICS 2018 standardıyla TUTARLI (BİLİŞİM→Teknoloji, TELEKOMÜNİKASYON+
YAYIMCILIK+REKLAMCILIK→İletişim) — kullanıcının "insanlar aynı sektör
olarak görmüyor" endişesine denk düşen somut bir örnek BULUNAMADI bu üç
alanda.

---

## Test senaryoları

1. **THYAO/PGSUS/CLEBI/TAVHL'nin `ekosistem_etiketi` alanı:** Migration
   sonrası dördü de `"Havacılık"` döner, DİĞER 636 BİST şirketi `None`
   döner (uydurma etiket YOK, Kural 3).
2. **TAVHL'nin `ust_sektor`'ü düzeltme SONRASI:** `KAP_TICKER_SECTOR_
   OVERRIDES["TAVHL"]="Sanayi"` eklendikten sonra `ust_sektor_for_kap
   ("TAVHL", ...)` çağrısı artık `"Finans"` DEĞİL `"Sanayi"` döner —
   regresyon testi (mevcut TUPRS testiyle AYNI kalıp).
3. **Sektöre göreli F/K hesaplaması (`valuation.py`) THYAO için:** `ust_
   sektor="Sanayi"` peer havuzunu (n çok büyük) kullanmaya DEVAM eder —
   `ekosistem_etiketi` eklenmesi bu hesaplamanın SONUCUNU DEĞİŞTİRMEZ
   (regresyon testi — Seçenek B'nin "istatistik dokunulmaz" iddiasının
   doğrulanması).
4. **Dashboard'da (eğer `_build_sectors()` genişletilirse) "Havacılık"
   rozeti görüntülenen bir THYAO kartı, sektör-göreli DEĞER bileşeninde
   HÂLÂ "Sanayi" medyanına göre" yazısı taşır** — iki farklı kavram
  (görsel gruplama vs istatistiksel peer seti) kartta KARIŞTIRILMAMALI,
  ayrı ayrı etiketlenmelidir.
5. **KAP yeni bir havayolu/havalimanı IPO'su eklerse (n=5'e ulaşırsa):**
   Bu spec'in "Kenar durumlar" bölümündeki tetikleyici not YENİDEN
   değerlendirme ihtiyacını İŞARETLER — otomatik bir kod davranışı
   DEĞİL, insan gözden geçirmesi gerektiren bir eşik.
