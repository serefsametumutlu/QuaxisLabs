# Site Tasarım Yol Haritası

**Tarih:** 2026-09-03 · Görsel referans: luxalgo.com · Mevcut durum: Next.js + FastAPI, **2 sayfa** (`/scan`, `/chart`), ~1.400 satır frontend

Bu bir ön bilgi ve yol haritasıdır. `docs/TANI_VE_YOL_HARITASI_v2.md`'deki **Faz 7'nin yerini alır** — Faz 7 "3 temayı tutarlı kıl + hız" idi, bu belge aynı işi tam bir ürün yüzeyi olarak tarif ediyor.

---

## 0 · LuxAlgo burada ne, ne değil

**Sadece görsel bir referans.** Kullanıcının kendi ifadesiyle: *"sistemsel bir örnek vermedim, sadece site tasarımı için fena gelmedi gözüme, tasarımsal bir örnek. Mantıksal olarak çok farklı olduğumuzun farkındayım."* Bu belge de öyle kullanıyor — **görsel dil ve yüzey düzeni** için bakılacak, ürün mantığı için değil.

Alınacak olan üç şey, hepsi görsel/yapısal:

1. **Yoğunluk dili** — koyu zemin, tablo-ağırlıklı, bilgi yoğun ama gürültüsüz. Bir tarama aracının bilgi yoğunluğu böyle taşınır.
2. **Yüzeylerin net ayrılması** — her ekranın tek bir işi var ve adı ne yaptığını söylüyor.
3. **Kademelendirme okunurluğu** — hangi katman neyi açıyor, ilk bakışta belli.

Alınmayacak olan: **görsel kimliğin kendisi.** Hem hukuken riskli, hem gereksiz — `docs/design/grafik_stil_vitrini.html`'de kendi üç temanız zaten tanımlı ve karakterli (Klasik Beyaz Rapor / Terminal Koyu / Kağıt Rapor). LuxAlgo tek koyu temada; üç temalı olmak bir fark, kayıp değil. Onların yoğunluk dilini **kendi paletinizle** kurmak doğru hedef.

**Mantık tarafındaki fark zaten biliniyor** ve bu belgede yalnızca bir yerde işe yarıyor — pazarlama sayfasının konumlandırmasında (S7): LuxAlgo TradingView'in *içinde* çalışan gösterge paketi satıyor; QuaxisLabs veriyi, sinyali, grafiği, raporu kendi üretiyor. Bu, sitede söylenecek bir cümle; kopyalanacak bir mimari değil.

---

## 1 · Ürün yüzeyi haritası (piksel yazmadan önce)

Şu an iki sayfa var. Bir ürün olması için altı yüzey gerekiyor:

| Yüzey | Ne yapar | Şimdiki durum |
|---|---|---|
| **Tarama** | "Bugün hangi hissede hangi strateji sinyal verdi" — ana giriş noktası | `/scan` var, tazelik filtresi yok, tablo seyrek |
| **Grafik** | Tek sembol + tek strateji, tam görsel kanıt + AI raporu | `/chart` var, Plotly PNG |
| **Evren** | Tüm BİST'i bir bakışta: alpha dağılımı, momentum ısı haritası, sektör rotasyonu | ❌ yok (kod var, route yok) |
| **Alarmlar** | Sinyal geldiğinde haber ver (e-posta / Telegram / push) | ❌ yok |
| **Portföy** | `tlab/portfolio/` çıktısı: pozisyon boyutlandırma, risk, tahsis | ❌ yok (Faz 10 kodu yazıldı, arayüzü yok) |
| **Strateji kütüphanesi** | 24 stratejinin ne olduğu, nasıl okunacağı, tarihsel isabeti | ⚠️ `ChartGuide` var ama sayfa değil |

Sol raydaki "Stratejiler" listesi şu an ham katalog kategorilerinden geliyor (`harmonics`, `structure`, `patterns`…). Bunlar iç adlandırma; kullanıcıya paket olarak sunulmalı. Öneri — kataloğun `category` alanını ürün paketine çevirin:

- **Formasyon Paketi** — `patterns.*` + `harmonic.*` (klasik + harmonik formasyonlar)
- **Yapı Paketi** — `structure.*` + `trend.breakouts` (destek/direnç, arz-talep, golden zone, kırılımlar)
- **Trend & Momentum Paketi** — `trend.*` + `momentum.*` (EWMAC, MA sistemleri, alfa/momentum sıralaması)
- **İstatistiksel Arbitraj Paketi** — `pair.*`

Bu, hem sidebar'ı hem ileride fiyatlandırmayı düzenler.

---

## 2 · Fazlar

### S1 · Tasarım sistemi ve bileşen kütüphanesi

**Neden ilk:** Şu an her sayfa kendi Tailwind sınıflarını yazıyor. Yeni dört yüzey eklenmeden ortak dil kurulmazsa tutarsızlık altı katına çıkar.

**Kapsam:**
- `globals.css` token setini `docs/design/grafik_stil_vitrini.html`'in shell CSS'iyle (`--shell-*`) hizala: yarıçap ölçeği, gölge katmanları, eyebrow/section-label tipografisi, tema başına üçlü font (display / body / mono).
- Fontlar `next/font` ile **yerel** — CDN bağımlılığı yok, Türkçe glifler (İıĞğŞşÇçÖöÜü) render testinden geçer.
- `components/ui/`: `Card`, `Panel`, `SectionLabel`, `Eyebrow`, `Pill`, `Badge`, `Tab`, `StatTile`, `DataTable`, `Sparkline`, `EmptyState`, `Skeleton`.
- `DataTable` bu işin kalbi: sıralanabilir, sanallaştırılmış (500+ satır), sabit başlık, `tabular-nums`, satır-üzeri önizleme kancası, kolon göster/gizle.
- Semantik renk (iyi/uyarı/kritik) marka aksanından **ayrı** — aksan altın/hardal, semantik yeşil/kırmızı yön anlamı taşır ve karıştırılmaz.

**Bitti kriteri:** üç tema, altı bileşen, Storybook benzeri bir `/tasarim` iç sayfası (bileşenleri üç temada yan yana gösterir), `npm run build` temiz.

---

### S2 · Uygulama kabuğu ve navigasyon

**Kapsam:**
- Sol rayda ürün paketleri (yukarıdaki dört paket) + altı yüzey; üstte global arama (sembol / strateji), piyasa seçici, tema seçici, son tarama zamanı.
- **Komut paleti (⌘K)** — sembol, strateji, sayfa araması. Yoğun kullanıcı bunu klavyeden kullanır; bir tarama aracında en yüksek etki/maliyet oranlı özelliklerden biri.
- Sayfa iskeleti: `başlık şeridi → filtre şeridi → içerik → detay paneli`. Detay paneli **sağdan açılan** bir çekmece (tarama satırından grafiğe geçerken sayfayı terk etmeden).
- Yükleme durumları: iskelet (skeleton), boş durum, hata durumu — üçü de tasarlanmış olmalı; şu an `/chart` "Grafik oluşturuluyor…" düz metniyle idare ediyor.

---

### S3 · Tarama yüzeyi (ürünün kalbi)

Kullanıcının kendi tarifi: *"bana AL sinyali gelecek, ben grafiğine bakacağım ve son mumunda o sinyali göreceğim."* Sayfa bu cümleye göre kurulmalı.

**Kapsam:**
- **Üst şerit — bugünün özeti:** kaç yeni sinyal, kaç AL / kaç SAT, hangi paketten, önceki güne göre değişim. Dört `StatTile`.
- **Tazelik birinci sınıf filtre** (Faz 0'da backend'i geliyor): Son 1 mum / Son 3 mum / Son 10 mum / Tümü. Varsayılan **Son 3 mum**. "Yaş" kolonu her satırda.
- **Yoğun tablo:** Sembol · Sektör · Strateji · Yön · Durum · Yaş · Skor · Zaman dilimi · Tarihsel isabet (Faz 8'den) · mini sparkline.
- **Satır üzerine gelince grafik önizlemesi** — `/api/chart.svg`'den küçük boyutlu. Bu tek özellik, tarama → grafik gidiş gelişini ortadan kaldırır.
- **Kaydedilmiş taramalar:** filtre kombinasyonunu isimlendirip saklama (`config/scans.yaml` preset mekanizması **zaten var**, arayüze bağlanmamış).
- **Çoklu seçim → karşılaştırma:** 2-4 sembolü işaretleyip yan yana grafik.
- Sinyal yoksa dürüst boş durum: "Son 3 mumda bu filtreye uyan sinyal yok" + filtreyi gevşetme önerisi.

---

### S4 · Grafik detay yüzeyi

**Kapsam:**
- Artifact'in "stage" düzeni: kart çerçevesi → grafik → `stage-caption` → "Nasıl Okunur" 4 kutulu grid → AL sinyali kutusu → AI raporu kartı.
- **Strateji değiştirici sekme olarak**, dropdown değil — aynı sembolde stratejiler arasında hızlı geçiş.
- **Zaman dilimi geçişi grafiği yeniden yüklerken önceki görseli tutar** (flaş yok).
- SVG **inline** gömülü (Faz 3-4 sonrası): tema değişince yeniden fetch yok, CSS değişkenleriyle anında geçer, seçilebilir metin, her zoom'da net.
- Sağda dar bir "sinyal geçmişi" rayı: bu sembolde bu stratejinin geçmiş sinyalleri ve sonuçları.

---

### S5 · Evren yüzeyi

`docs/TANI_VE_YOL_HARITASI_v2.md` Faz 6 bunu tarif ediyor — alpha dağılımı, momentum ısı haritası, sektör kartları, sıralanabilir tam tablo, sektörel/tüm-evren sekmeleri. Ek olarak bu belge kapsamında:

- **Sektör rotasyon şeridi:** son 1/3/6 ayda hangi sektör lider, hangisi geride — tek satırlık yatay bir sıralama görseli.
- **Piyasa genişliği (breadth):** kaç sembol 50/200 günlük ortalamanın üstünde, yeni zirve/dip sayısı. Basit ama piyasa rejimini tek bakışta veriyor.

---

### S6 · Alarm ve bildirim yüzeyi

LuxAlgo'nun üç ayağından biri bu ve QuaxisLabs'ta hiç yok — oysa `eod.py::notify()` **boş bir hook olarak zaten duruyor**.

**Kapsam:**
- Alarm kuralı: (piyasa, semboller veya sektör, strateji/paket, yön, tazelik) → kanal.
- Kanallar: Telegram (Bilanço Radar tarafında bot **zaten var**, aynı altyapı), e-posta, tarayıcı push.
- Alarm akışı sayfası: tetiklenen alarmların zaman çizelgesi, her biri grafiğe tıklanabilir.
- Sessizlik kuralları: aynı sembol+strateji için gün içinde tekrar bildirme, piyasa kapalıyken biriktir.

---

### S7 · Pazarlama sitesi

Bu, uygulamadan **ayrı** bir yüzey ve ayrı bir iş. Ürün hazır olmadan yapılmamalı; ama yapısı şimdiden belli:

- **Hero:** tek cümlelik konum + **canlı ürün görüntüsü** (statik mockup değil — gerçek bir taramanın ekran görüntüsü ya da otomatik dönen üç grafik). LuxAlgo'nun ve iyi SaaS sitelerinin ortak paydası bu.
- **Fark bölümü:** "Gösterge kiralamıyoruz — veriyi biz çekiyoruz, sinyali biz üretiyoruz, grafiği biz çiziyoruz, ve yakında temel analizle birleştiriyoruz." Mantık tarafındaki farkın sitede karşılığı **tek bir yerde** olmalı: burada.
- **Paket bölümü:** dört paket, her biri 2-3 gerçek grafikle.
- **Kanıt bölümü:** Faz 8'in forward-return tablosu. *Bu, çoğu rakibin yapamadığı şey* — "stratejilerimizin tarihsel isabetini yayınlıyoruz" güçlü ve dürüst bir iddia. **Yalnızca Faz 8 gerçekten koşulduktan sonra**, ve olduğu gibi (çalışmayan stratejiler dahil).
- **Fiyatlandırma:** üç kademe. Ücretsiz katman gerçek bir değer taşımalı (ör. günde 1 tarama, 3 strateji) — LuxAlgo'nun ücretsiz TradingView kütüphanesinin işlevi bu.
- **Dokümantasyon:** her stratejinin ne olduğu, hangi kaynağa dayandığı, nasıl okunacağı. `tlab/viz/labels_tr.py` + `ChartGuide` içeriği zaten yazılmış durumda — sayfaya dönüştürülecek.
- **Yasal:** her sayfada "yatırım tavsiyesi değildir" uyarısı; QuaxisLabs'ın mevcut ilkesi bu ve korunmalı.

---

### S8 · Performans, erişilebilirlik, mobil

- **Performans bütçesi:** ilk anlamlı boyama < 1.5 sn, tarama tablosu 500 satırda 60 fps, grafik isteği < 300 ms (SVG'ye geçtikten sonra ulaşılabilir).
- **Sunucu tarafı önbellek:** `(symbol, tf, indicator, theme, son_bar)` anahtarıyla. Şu an yalnızca tarayıcı `Cache-Control` var.
- **Mobil:** tarama tablosu mobilde kart listesine dönüşür; grafik tam genişlik + yatay kaydırma; komut paleti alt sayfa olur.
- **Erişilebilirlik:** klavye ile tam gezinme, görünür odak halkası, `prefers-reduced-motion`, WCAG AA kontrast (üç temada da doğrulanacak — koyu temada altın aksan sınırda).

---

## 3 · Sıra ve bağımlılıklar

```
TANI Faz 0 (tazelik)  ─┐
TANI Faz 3-4 (SVG)    ─┼─→  S1 ─→ S2 ─→ S3 ─→ S4
TANI Faz 6 (evren)    ─┘                  └─→ S5
                                          └─→ S6
TANI Faz 8 (doğrulama) ─────────────────────→ S7
```

- **S1/S2 hemen başlayabilir** — SVG motorunu beklemez, sadece kabuğu düzenler.
- **S3/S4 SVG'yi bekler** (inline SVG ve satır-üzeri önizleme buna bağlı).
- **S7 (pazarlama) Faz 8'i bekler** — kanıtsız bir pazarlama sayfası, ürünün en güçlü kozunu boşa harcar.

**Gerçekçi büyüklük:** S1–S6 arası, mevcut hızda **8–12 oturum**. S7 ayrı bir iş (içerik + copywriting + görsel üretimi), muhtemelen bir o kadar daha. Bu, TANI belgesindeki 9 fazın **üstüne** gelir — ikisini paralel yürütmek istemezsin; önce sinyal doğru olsun, sonra vitrin.

---

## 4 · Hazır promptlar

> Her prompt, `docs/TANI_VE_YOL_HARITASI_v2.md`'deki **ORTAK BAĞLAM** bloğuyla başlar — onu kopyalayıp promptun başına yapıştır.

### 4.1 · S1 + S2 — Tasarım sistemi ve uygulama kabuğu

```
[TANI_VE_YOL_HARITASI_v2.md'deki ORTAK BAĞLAM bloğunu yapıştır]

GÖREV — SİTE S1+S2: Tasarım sistemi ve uygulama kabuğu

ÖNCE OKU:
- docs/design/grafik_stil_vitrini.html'in KABUK CSS'i (satır ~4-135):
  --shell-* değişkenleri, .pick-card, .tab, .stage-wrap, .chart-note,
  .signal-box, .ai-report, .notes-card, .filmstrip. Hedeflenen kabuk dili bu.
- docs/SITE_TASARIM_YOL_HARITASI.md (bu belge) bölüm 1 ve 2.
- Mevcut web/frontend/ (2 sayfa, ~1400 satır) — her sayfa kendi Tailwind
  sınıflarını yazıyor, ortak bileşen YOK.

HEDEF: LuxAlgo sınıfı bir ürün yüzeyinin ALTYAPISI. Bu turda yeni SAYFA
yazılmayacak; mevcut iki sayfa yeni sisteme taşınacak.

--- S1: TASARIM SİSTEMİ ---

1. web/frontend/app/globals.css: token setini artifact'in shell'iyle hizala.
   Eksik olanlar: --radius ölçeği (sm/md/lg), --shadow katmanları (1/2/3),
   eyebrow ve section-label tipografisi, tema başına ÜÇLÜ font:
     classic   -> Source Serif 4 (display) + Inter (body) + IBM Plex Mono
     dark      -> JetBrains Mono (display) + Inter (body) + JetBrains Mono
     editorial -> Playfair Display + Source Serif 4 + IBM Plex Mono
   Fontlar next/font ile YEREL yüklensin (CDN bağımlılığı YOK).
   Türkçe glifleri (İ ı Ğ ğ Ş ş Ç ç Ö ö Ü ü) her üç temada render testinden
   geçir -- ekran görüntüsü al ve GÖR.

2. web/frontend/lib/themes.ts: üç temanın TAM token seti, artifact'in
   THEMES.classic/.dark/.editorial değerleriyle BİREBİR. saas ve neon
   EKLENMEYECEK (kullanıcı kararı: 3 tema).

3. SEMANTİK RENK AYRIMI: marka aksanı (altın/hardal) ile yön anlamı taşıyan
   yeşil/kırmızı AYRI token ailesi. Aksan "karara değer" öğeler için ayrılmış
   (bilinçli kıtlık); yeşil/kırmızı yalnızca yön/durum. Bu ayrım tokenlarda
   isimle görünsün (--accent-* vs --semantic-*).

4. web/frontend/components/ui/ altında bileşenler:
   Card, Panel, SectionLabel, Eyebrow, Pill, Badge, Tab, TabGroup, StatTile,
   DataTable, Sparkline, EmptyState, Skeleton.
   DataTable ZORUNLU ÖZELLİKLER: sıralanabilir kolonlar, sanallaştırma
   (500+ satırda 60fps -- @tanstack/react-virtual veya eşdeğeri),
   sabit başlık, font-variant-numeric: tabular-nums, satır-üzeri (hover)
   kancası, kolon göster/gizle, klavye gezinmesi.

--- S2: UYGULAMA KABUĞU ---

5. Sol ray yeniden düzenlensin. Şu anki "Stratejiler" listesi ham
   kategorilerden geliyor; bunun yerine DÖRT ÜRÜN PAKETİ:
     Formasyon Paketi      -> patterns.* + harmonic.*
     Yapı Paketi           -> structure.* + trend.breakouts
     Trend & Momentum      -> trend.* (breakouts hariç) + momentum.*
     İstatistiksel Arbitraj -> pair.*
   Eşleme tlab/viz/labels_tr.py'de TEK KAYNAKTAN tanımlansın (yeni bir
   PACKAGE_TR sözlüğü), backend /api/categories bunu döndürsün -- frontend'de
   elle bakımlı ikinci bir liste OLMASIN.
   NOT: "Pair (Rölatif Momentum)" etiketi "İstatistiksel Arbitraj" olacak
   (bkz. TANI 1.4a -- gerçek arbitraj bu değil, beklenti karışıyor).

6. Üst şerit: global arama (sembol + strateji), piyasa seçici, tema seçici,
   "son tarama: X saat önce" göstergesi.

7. KOMUT PALETİ (⌘K / Ctrl+K): sembol, strateji ve sayfa araması. Yoğun
   kullanıcı bunu klavyeden kullanır; tarama aracında en yüksek etki/maliyet
   oranlı özelliklerden biri. Kütüphane kullanma, ~150 satırlık kendi
   uygulaman yeterli (input + filtrelenmiş liste + klavye gezinmesi).

8. YÜKLEME/BOŞ/HATA durumları üçü de tasarlansın ve mevcut iki sayfada
   kullanılsın. Şu an /chart "Grafik oluşturuluyor…" düz metniyle idare
   ediyor -- Skeleton bileşeniyle değiştir.

9. Mevcut /scan ve /chart sayfalarını yeni bileşenlere TAŞI. Davranış
   değişmesin, yalnızca görünüm ve yapı.

--- DOĞRULAMA (ZORUNLU) ---

10. scripts/ui_snapshot.py (ya da Playwright testi): /scan ve /chart
    sayfalarını 3 temada, 2 genişlikte (1440 ve 768) ekran görüntüsü alsın ->
    docs/design/ui/<sayfa>_<tema>_<genislik>.png
11. Bu PNG'leri Read ile AÇ VE GÖR. Sorunları madde madde yaz, düzelt,
    tekrarla. EN AZ 3 İTERASYON. Türkçe glif kontrolünü ekran görüntüsünde
    GÖZLE doğrula.
12. /tasarim adında bir iç sayfa: tüm ui/ bileşenlerini üç temada yan yana
    gösterir (Storybook yerine tek sayfa). Bu sayfa gelecekteki her tasarım
    işinin referansı olur.

BİTTİ KRİTERİ:
- Üç tema, 13 bileşen, /tasarim sayfası.
- DataTable 500+ satırda takılmıyor (ölç ve raporla).
- Komut paleti çalışıyor.
- /scan ve /chart yeni sisteme taşınmış, davranış değişmemiş.
- docs/design/ui/ altında 2 sayfa × 3 tema × 2 genişlik görüntü, hepsi
  GÖRÜLMÜŞ, en az 3 iterasyon geçmiş.
- npm run build + npm run lint temiz.
```

---

### 4.2 · S3 + S4 — Tarama ve grafik yüzeyi

**Ön koşul:** S1+S2 bitmiş (bileşen kütüphanesi + kabuk), TANI Faz 3-4 bitmiş (SVG motoru ve sahneler).

```
[ORTAK BAĞLAM bloğunu buraya yapıştır]

GÖREV — SİTE S3+S4: Tarama ve grafik yüzeyi

ÖNCE OKU:
- docs/SITE_TASARIM_YOL_HARITASI.md bölüm S3 ve S4.
- docs/design/grafik_stil_vitrini.html'in "stage" düzeni (.stage-wrap,
  .stage-caption, .note-wrap, .chart-note, .signal-box, .ai-report,
  .filmstrip) -- /chart sayfasının hedeflenen iskeleti bu.
- web/frontend/components/ui/ (S1'de kurulan bileşenler). Yeni bileşen
  yazmadan ÖNCE oradakine bak; eksikse oraya EKLE, sayfaya gömme.

Kullanıcının kendi cümlesi, sayfanın tasarım ölçütü budur:
"bana AL sinyali gelecek, ben grafiğine bakacağım ve SON MUMUNDA o sinyali
göreceğim."

--- S3: TARAMA YÜZEYİ (/scan) ---

1. ÜST ŞERİT -- bugünün özeti, dört StatTile: yeni sinyal sayısı, kaç AL /
   kaç SAT, en çok sinyal veren paket, önceki koşuya göre değişim.
   Veriler /api/signals'ın ZATEN döndürdüğü alanlardan türetilir; yeni bir
   backend hesabı EKLEME (gerekiyorsa /api/signals/summary route'u aç ve
   hesabı ResultsStore'a sor -- route içinde hesap YAPMA).

2. TAZELİK BİRİNCİ SINIF FİLTRE (Faz 0'da backend'i geldi):
   chip grubu -> Son 1 mum / Son 3 mum / Son 10 mum / Tümü. Varsayılan
   Son 3 mum. "Yaş" kolonu her satırda ("son mum", "3 mum önce").
   Tablo varsayılan sıralaması bars_ago artan (en taze en üstte).

3. YOĞUN TABLO (S1'deki DataTable ile):
   Sembol · Sektör · Paket · Strateji · Yön · Durum · Yaş · Skor · TF ·
   Tarihsel isabet (Faz 8 sonrası; yoksa kolon gizli).
   Kart DEĞİL tablo -- Bloomberg/Koyfin yoğunluğu hedef.
   Satır tıklaması SAĞDAN AÇILAN detay çekmecesi (sayfa değiştirmez);
   çekmecede grafik + sinyal payload'ı + "tam sayfada aç" bağlantısı.

4. SATIR ÜZERİNE GELİNCE GRAFİK ÖNİZLEMESİ -- /api/chart.svg'den küçük
   boyutlu (ör. 420x220). Bu tek özellik tarama<->grafik gidiş gelişini
   ortadan kaldırır. Debounce 250ms; aynı satıra tekrar gelince yeniden
   istek ATMA (istemci içi önbellek).

5. KAYDEDİLMİŞ TARAMALAR -- config/scans.yaml preset mekanizması ZATEN VAR
   (bkz. tlab/scanner/filter_expr.py + `tlab scan --preset`), arayüze hiç
   bağlanmamış. /api/presets route'u aç, filtre kombinasyonunu isimlendirip
   kaydetmeyi ve yüklemeyi ekle.

6. ÇOKLU SEÇİM -> KARŞILAŞTIRMA: 2-4 satır işaretlenip "Karşılaştır"
   denince yan yana grafik gösteren bir görünüm.

7. BOŞ DURUM DÜRÜST OLSUN: "Son 3 mumda bu filtreye uyan sinyal yok" +
   tazeliği gevşetme önerisi. Sahte veri ya da "yakında" metni YOK.

--- S4: GRAFİK YÜZEYİ (/chart) ---

8. Sayfayı artifact'in "stage" düzenine taşı:
   stage-wrap (kart çerçevesi + grafik + stage-caption)
   -> note-wrap (.chart-note 4 kutulu grid: NEREYE BAK / NE ÖLÇER /
      DEĞERLER NE DEMEK -- ChartGuide.tsx bunu ZATEN üretiyor, yalnızca
      grid'e oturt)
   -> signal-box (sol kenarlıklı vurgu: "AL SİNYALİ NE ZAMAN OLUŞUR")
   -> ai-report (ayrı kart, dashed tag)

9. STRATEJİ DEĞİŞTİRİCİ SEKME olarak, dropdown DEĞİL. Paket bazlı
   gruplanmış sekmeler; aynı sembolde stratejiler arası hızlı geçiş.

10. SVG'yi <img src> yerine INLINE göm. Kazanç: tema değişince yeniden
    fetch YOK (CSS değişkenleriyle anında geçer), her zoom'da net, metin
    seçilebilir. PNG indirme mevcut canvas yöntemiyle çalışmaya devam
    etsin (SVG -> canvas -> toBlob).

11. ZAMAN DİLİMİ / SEMBOL GEÇİŞİNDE FLAŞ YOK: yeni grafik gelene kadar
    eskisi soluk (opacity .5) kalsın, üstünde Skeleton değil ince bir
    ilerleme çizgisi olsun. (Mevcut ChartImage'daki prevSrc deseni
    korunacak -- o GERÇEK bir hata düzeltmesiydi, bozma.)

12. SAĞDA "SİNYAL GEÇMİŞİ" RAYI: bu sembolde bu stratejinin geçmiş
    sinyalleri (tarih, yön, durum, sonuç). /api/signals'a symbol+indicator
    filtresi ZATEN var, all_states=true ile çekilir.

--- DOĞRULAMA (ZORUNLU) ---

13. scripts/ui_snapshot.py ile /scan ve /chart'ı 3 temada, 2 genişlikte
    (1440/768) yakala -> docs/design/ui/. PNG'leri Read ile AÇ VE GÖR,
    sorunları madde madde yaz, düzelt. EN AZ 3 İTERASYON.
14. Tablo performansını ÖLÇ: 500 satırda kaydırma akıcılığı, satır-üzeri
    önizlemenin gecikmesi. Raporla.

BİTTİ KRİTERİ:
- /scan: özet şeridi, tazelik chip'leri, yaş kolonu, yoğun tablo, satır
  önizlemesi, detay çekmecesi, kaydedilmiş taramalar, karşılaştırma.
- /chart: stage düzeni, sekme değiştirici, inline SVG, flaşsız geçiş,
  sinyal geçmişi rayı.
- Yeni bileşen gerekiyorsa components/ui/'ye eklenmiş (sayfaya gömülmemiş).
- docs/design/ui/ altında görüntüler, hepsi GÖRÜLMÜŞ, 3+ iterasyon.
- npm run build + npm run lint temiz; pytest -q -m "not network" yeşil.
```

---

### 4.3 · S6 — Alarm ve bildirim

**Ön koşul:** S1+S2. Faz 0'ın tazelik altyapısı alarm kurallarının temeli.

```
[ORTAK BAĞLAM bloğunu buraya yapıştır]

GÖREV — SİTE S6: Alarm ve bildirim yüzeyi

Durum: tlab/scanner/eod.py::notify() BOŞ BİR HOOK olarak zaten duruyor
(Faz 6'da bilinçli olarak "Telegram sonra" diye bırakılmış). Bilanço Radar
tarafında çalışan bir Telegram botu VAR. Yani altyapının iki ucu hazır,
arası boş.

--- BACKEND ---

1. tlab/alerts/ (YENİ paket):
   - rules.py: AlertRule dataclass (id, ad, market, semboller|sektör|hepsi,
     paketler/göstergeler, yön, min_skor, max_bars_ago, kanallar, aktif).
     Kurallar SQLite'ta (scanner/results.py'nin ZATEN kullandığı DB, yeni
     bir alerts tablosu) saklanır.
   - match.py: run_eod'un ürettiği diff çıktısını (yeni sinyaller + durum
     geçişleri) kurallarla eşleştirir. SAF FONKSİYON -- I/O yok, test
     edilebilir. eod.py'nin diff() çıktısını girdi alır.
   - channels/: telegram.py, email.py, webhook.py. Her biri aynı
     Notifier protokolüne uyar (send(rule, signals) -> bool).
     Gizli anahtarlar ortam değişkeninden (.env.example'a ekle),
     ASLA koda gömülmez.
   - dedupe.py: sessizlik kuralları -- aynı (sembol, gösterge, pattern_id)
     için `quiet_bars` içinde tekrar bildirme; piyasa kapalıyken biriktir
     (tlab/data/calendar.py ZATEN seans bilgisini biliyor), açılışta tek
     bir özet gönder.

2. eod.py::notify() gerçek uygulamasını buraya bağla. Bildirim
   GÖNDERİLEMEZSE tarama BAŞARISIZ SAYILMAZ -- hata loglanır, run devam
   eder (bildirim yan etki, ana iş değil).

3. Route'lar: GET/POST/DELETE /api/alerts (kural CRUD),
   GET /api/alerts/feed (tetiklenen alarmların zaman çizelgesi),
   POST /api/alerts/{id}/test (kuralı son koşuya karşı çalıştır, GÖNDERME
   -- kaç sinyal eşleşirdi onu döndür). Bu son madde önemli: kullanıcı
   kuralı kaydetmeden önce ne kadar gürültü üreteceğini görmeli.

--- FRONTEND ---

4. /alarmlar sayfası:
   - Kural listesi (aktif/pasif toggle, son tetiklenme, 30 günlük
     tetiklenme sayısı).
   - Kural düzenleyici: adım adım DEĞİL tek form; her alan değiştikçe
     "bu kural son 30 günde N kez tetiklenirdi" canlı önizlemesi
     (/api/alerts/{id}/test ile, debounce'lu). Bu, alarm gürültüsünü
     kurulum anında engelleyen tek şey.
   - Akış (feed): tetiklenen alarmların zaman çizelgesi, her satır
     grafiğe tıklanabilir.
5. /scan'de bir satırdan "Bu sinyal için alarm kur" kısayolu -- filtreleri
   önceden doldurulmuş kural düzenleyicisini açar.

BİTTİ KRİTERİ:
- tlab/alerts/ + match.py için en az 8 test (saf fonksiyon, gerçek diff
  çıktısı fixture'ıyla).
- Telegram kanalı gerçek bir mesaj gönderiyor (test kanalına).
- Sessizlik kuralları test edilmiş (aynı sinyal iki kez gönderilmiyor).
- /alarmlar sayfası: kural CRUD + canlı "kaç kez tetiklenirdi" önizlemesi
  + akış.
- notify() hatası taramayı düşürmüyor (test edilmiş).
- pytest -q -m "not network" yeşil.
```

---

### 4.4 · S8 — Performans, erişilebilirlik, mobil

**Ön koşul:** S3+S4 bitmiş (ölçülecek bir şey olsun).

```
[ORTAK BAĞLAM bloğunu buraya yapıştır]

GÖREV — SİTE S8: Performans, erişilebilirlik, mobil

Bu görevde ÖNCE ÖLÇ, SONRA DÜZELT. Ölçmeden yapılan optimizasyon tahmindir.

--- ÖLÇÜM ---

1. scripts/perf_olcum.py (ya da Playwright): /scan, /chart, /evren için
   ölç ve docs/spec/PERF_v1.md'ye yaz:
   - İlk anlamlı boyama (FCP/LCP)
   - /api/chart.svg yanıt süresi -- gösterge başına ayrı (price_structure
     O(n^2) olduğu için tek başına bir uç değer olacak, ayrı raporla)
   - /scan tablosu 500 satırda kaydırma akıcılığı (fps)
   - İlk yüklemede kaç ağ isteği, kaçı ardışık (waterfall)

--- HEDEF BÜTÇE ---
   FCP < 1.5 sn · tablo 60 fps · grafik isteği < 300 ms (SVG'ye geçildikten
   sonra ulaşılabilir olmalı; değilse SEBEBİNİ bul, hedefi düşürme)

--- DÜZELTMELER ---

2. SUNUCU TARAFI ÖNBELLEK: /api/chart.svg için anahtar
   (symbol, tf, indicator, theme, son_bar_zamani). Şu an yalnızca tarayıcı
   Cache-Control var; price_structure gibi pahalı göstergelerde sunucu her
   istekte yeniden hesaplıyor. LRU, bellek sınırlı.
3. İLK YÜKLEME PARALELLEŞTİRME: /api/catalog + /api/categories +
   /api/runs + /api/signals şu an ardışık gidiyor. Promise.all.
4. Tablo sanallaştırması (S1'de DataTable'a girdiyse doğrula, girmediyse
   ekle).

--- MOBİL ---

5. Tarama tablosu mobilde KART LİSTESİNE dönüşür (sembol + strateji + yön
   + yaş üstte, gerisi katlanır). Yatay kaydırma YOK.
6. Grafik tam genişlik; SVG'nin kendi iç kaydırması (viewBox sabit,
   container overflow-x: auto).
7. Komut paleti mobilde alt sayfa (bottom sheet) olur.

--- ERİŞİLEBİLİRLİK ---

8. Klavye ile tam gezinme: tablo satırları arasında ok tuşları, Enter ile
   detay, Esc ile kapat. Görünür odak halkası (:focus-visible) her
   etkileşimli öğede.
9. WCAG AA kontrast denetimi ÜÇ TEMADA da. DİKKAT: koyu temada altın
   aksan (#f5b400) koyu zemin üstünde sınırda -- ölç, geçmiyorsa aksanı
   metin rengi olarak kullanma, yalnızca dolgu/kenarlık olarak kullan.
10. prefers-reduced-motion: tüm geçişler kapansın.
11. Grafik SVG'lerine <title> ve <desc> ekle (ekran okuyucu için
    "TCELL 4H, çift dip formasyonu, AL sinyali" gibi) -- bu, göstergenin
    ZATEN ürettiği badge/subtitle'dan türetilir.

BİTTİ KRİTERİ:
- docs/spec/PERF_v1.md: önce/sonra ölçümleri.
- Bütçe hedeflerinin hangileri tutuldu, hangisi tutulmadı ve NEDEN --
  dürüstçe yazılmış.
- Mobil görüntüler (375px) docs/design/ui/ altında, GÖRÜLMÜŞ.
- Klavye gezintisi ve kontrast denetimi raporlanmış.
```

---

### 4.5 · S5 ve S7 hakkında

**S5 (Evren yüzeyi)** ayrı bir prompt istemiyor — `docs/TANI_VE_YOL_HARITASI_v2.md`'deki **Faz 6** promptu bu işi zaten kapsıyor. Bu belgenin S5 bölümündeki iki ek (sektör rotasyon şeridi + piyasa genişliği) o promptun sonuna bir madde olarak eklenebilir.

**S7 (Pazarlama sitesi)** için hazır prompt bilinçli olarak yazılmadı. Sebebi: içeriğinin yarısı **senin iş kararların** — fiyat kademeleri, ücretsiz katmanın sınırı, hedef kitle, marka sesi. Ayrıca en güçlü bölümü (kanıt bölümü) **Faz 8'in gerçek ölçümünü** bekliyor. Sırası geldiğinde bu kararları konuşup promptu o zaman yazmak, şimdi varsayımlarla yazmaktan iyi.

---

## 5 · Kaynaklar

- LuxAlgo ürün mimarisi ve kademeleri: [Signals & Overlays](https://www.luxalgo.com/library/indicator/luxalgo-signals-overlays/) · [inceleme derlemesi](https://aitradingcamp.com/reviews/luxalgo) · [inceleme](https://thetradeadvice.com/luxalgo-review/)
- Yoğun veri arayüzü ve koyu tema pratikleri: [Trading App Design (Lollypop, 2026)](https://lollypop.design/blog/2026/june/trading-app-design/) · [TradingView UI vaka çalışması](https://rondesignlab.com/cases/tradingview-platform-for-traders) · [Designing Data-Dense Dashboards](https://pixel-show.com/blog/designing-data-dense-dashboards)
- Kendi tasarım şartnamemiz: `docs/design/grafik_stil_vitrini.html`
