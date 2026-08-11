# SPEC: Kalite Merceği (v2 Çok-Mercekli Skorlama — Mercek 2/4)

## Amaç ve kapsam

**Ölçtüğü soru:** Rekabet avantajı + kârlılık kalitesi — şirket parasını ne
kadar İYİ ve SÜRDÜRÜLEBİLİR biçimde kazanıyor? (Fiyattan BAĞIMSIZ bir soru
— DEĞER merceğiyle KASITLI olarak ayrık tutulur, bkz. 00_sentez.md §2.5:
Buffett'ın "dayanıklı avantajlı şirketler NADİREN Graham tarzı ucuz
fiyattan işlem görür" bulgusu.)

**Geçerli şirket türleri:** `sanayi`, `abd_sanayi` BİRİNCİL (Buffett/Clark
kitabının TAMAMI imalat/perakende/marka şirketleri örnekleriyle yazılmış).
`banka`/`sigorta`/`finansman` için KISMİ geçerlilik — bu şablonlarda
marj/SG&A/Ar-Ge kavramları ANLAMSIZDIR (banka faiz marjı farklı bir
mantıkla çalışır, zaten `net_faiz_marji`/`aktif_karliligi` mevcut ayrı
bileşenlerdir); KALİTE merceği banka/sigorta için SADECE ROE + ROA alt-
kümesiyle çalışır, aşağıda "Sektör ayarlaması" bölümünde ayrıştırılmıştır.

**Piyasalar:** BİST + NASDAQ.

**Kapsam dışı:** Nitel yönetim kalitesi değerlendirmesi (Fisher'ın 15
maddesi HENÜZ işlenmedi) — bu mercek SADECE ÖLÇÜLEBİLİR/sayısal
göstergeleri kapsar; nitel sorular Gemini yorum katmanına ayrı "kontrol
listesi" olarak gider (bkz. `temel-analiz-cercevesi` skill madde 6).

---

## Girdiler

| Alan | Kaynak | Durum |
|---|---|---|
| FAVÖK marjı (seviye+trend) | `calculator.Ratios.ebitda_margin_current/prior_year/change_points` | MEVCUT |
| Net marj (seviye+trend) | `calculator.Ratios.net_margin_current/prior_year/change_points` | MEVCUT |
| Brüt kâr marjı (seviye+trend) | `calculator.Ratios.gross_margin_current/prior_year/change_points` | MEVCUT — HENÜZ skorlanmıyor |
| ROE (seviye) | `calculator.Ratios.roe_annualized` | MEVCUT (scorer.py'de zaten sanayi şablonuna eklenmiş) |
| ROA | YOK, `net_income/total_assets` ile TÜRETİLEBİLİR | **YENİ (ucuz)** — ham veri hazır |
| Amortisman/Brüt Kâr | YOK, `depreciation_amortization/gross_profit` | **YENİ (ucuz)** — ham veri hazır |
| SG&A/Brüt Kâr | YOK | VERİ EKSİK — `sga_expenses` XI_29 haritasında standalone yok |
| Ar-Ge/Brüt Kâr | YOK | VERİ EKSİK |
| Faiz Gideri/Faaliyet Kârı | YOK (sanayi) | VERİ EKSİK — kitaplar arası EN SIK tekrarlanan açık (6+ kez) |
| Greenblatt ROC (EBIT/(NWC+Net Sabit Varlık)) | `fundamental_screens.GreenblattResult.return_on_capital_pct` | MEVCUT (SADECE BIST XI_29 sanayi) |
| Marjinal ROE (ΔNet Kâr/Δönceki-yıl-Özkaynak) | `net_income`, `equity` (ham veri MEVCUT, çok-dönemli) | **YENİ (ucuz)** |
| Verimlilik kaynaklı ek büyüme (ΔROE/ROE_t-1) | `roe_annualized` YoY serisi (MEVCUT, `trends.py` sınırlı ufuk) | **YENİ (ucuz)** |
| Nakit Kâr Kalitesi (OCF/Net Kâr) | `operating_cash_flow`, `net_income` (ham veri MEVCUT) | **YENİ (ucuz)** — Piotroski kriter #4 ile AYNI ham veri, burada SÜREKLİ skor olarak |
| Hazine Hissesi Düzeltmeli ROE | `treasury_stock` YOK | VERİ EKSİK |

---

## Formüller

```
# 1. Seviye+trend bileşenleri (MEVCUT motor, scorer._seviye_trend_skoru
#    AYNEN kullanılır — sadece hangi mercekte YAŞADIĞI değişir):
favok_marji_skoru = seviye_trend_skoru(ebitda_margin_current, ebitda_margin_change_points, ...)
net_marj_skoru    = seviye_trend_skoru(net_margin_current, net_margin_change_points, ...)
brut_marj_skoru   = seviye_trend_skoru(gross_margin_current, gross_margin_change_points, ...)   # YENİ
roe_skoru         = seviye_trend_skoru(roe_annualized, None, ...)

# 2. ROA (YENİ, ucuz):
roa_pct = net_income / total_assets * 100
roa_skoru = seviye_trend_skoru(roa_pct, roa_change_points, ...)

# 3. Amortisman/Brüt Kâr (YENİ, ucuz — DÜŞÜK=iyi, ceza YÖNÜ TERS):
amortisman_orani_pct = depreciation_amortization / gross_profit * 100
# düşük = dayanıklı avantaj göstergesi (02/FORMÜL-04) → skorlama TERS yönde
# (seviye_trend_skoru'nun "düşük=kötü" varsayılan yönü BURADA TERSİNE
#  ÇEVRİLİR, bkz. Eşikler tablosu "yön" sütunu)

# 4. Marjinal ROE (YENİ, ucuz, Damodaran FORMÜL-42):
marjinal_roe_pct = (net_income_t - net_income_t-1) / equity_t-1 * 100

# 5. Verimlilik kaynaklı ek büyüme (YENİ, ucuz, Damodaran FORMÜL-43):
verimlilik_buyume_pct = (roe_t - roe_t-1) / roe_t-1 * 100

# 6. Nakit Kâr Kalitesi (YENİ, ucuz):
nakit_kar_kalitesi_orani = operating_cash_flow / net_income   # ideal ~1'e yakın veya üstü
```

---

## Eşikler ve ağırlıklar

**KALİTE merceği iç ağırlıkları (`sanayi`/`abd_sanayi`, toplam %100):**

| Bileşen | Ağırlık | Eşikler | Gerekçe / kaynak |
|---|---|---|---|
| Nakit Üretimi (FAVÖK marjı) | %25 | Mevcut scorer.py `nakit_uretimi` cfg AYNEN taşınır (güçlü≥20, orta≥10, tavan30) | Kalibre edilmiş, canlı doğrulanmış çekirdek KORUNUR (persona kural 8). Ayrıca 02/İLKE-01-06 (Warren gelir tablosunun HER kalemini kazanç KALİTESİ için inceler). |
| Özkaynak Kârlılığı (ROE) | %20 | Mevcut scorer.py `ozkaynak_karliligi` cfg AYNEN taşınır (güçlü≥15, orta≥10, tavan25) | 02/FORMÜL-22, İLKE-40,41 — kitabın Böl.47-48'de EN ÇOK vurguladığı formül; Graham/Buffett/Munger/Lynch/O'Neil ORTAK kesişimi (00_sentez.md §1.3). |
| Kârlılık (Net Marj) | %15 | Mevcut scorer.py `karlilik` cfg AYNEN taşınır | 02/FORMÜL-07, İLKE-13 — net marj>%20 dayanıklı avantaj olasılığı yüksek (Coca-Cola %21, Moody's %31), <%10 rekabetçi sektör göstergesi (istisna: banka/finansta TERS kural, bkz. Kenar Durumlar). |
| Brüt Kâr Marjı (seviye+trend, YENİ) | %15 | güçlü≥%40, orta≥%20, tavan%70 (Coca-Cola %60+, Moody's %73 örnekleri; ≤%20 "sürdürülebilir avantajı olmayan, aşırı rekabetçi sektör") | 02/FORMÜL-01, İLKE-02,03 — Buffett'ın "dayanıklılık testinin özü" (en az 10 yıllık TUTARLILIK, tek yıl YETERSİZ — QuaxisLabs'ta 12 çeyrek/~3 yıl trend penceresiyle KISMİ karşılanır, kart bu sınırı belirtir). |
| Greenblatt ROC (EBIT/Yatırılan Sermaye) | %10 | Mevcut fundamental_screens.py bantları (Yüksek≥25, Düşük≤10) AYNEN taşınır | Greenblatt'ın "Sihirli Formül"ünün KALİTE bacağı — sermaye verimliliği; Damodaran'ın ROC-cost of capital farkı ilkesiyle (03/İLKE-201-213) KAVRAMSAL OLARAK örtüşür (fazla getiri = değer yaratan büyüme koşulu, bkz. `spec_mercek_buyume.md`). |
| ROA (YENİ) | %5 | güçlü≥%8, orta≥%3, tavan%20 (BIST/NASDAQ sanayi ortalamalarına göre KABACA, gerçek veriyle kalibrasyon BEKLEMEDE — bkz. Kenar Durumlar) | 02/FORMÜL-13, İLKE-26 — DİKKAT: çok yüksek ROA (düşük varlık tabanı) TEK BAŞINA "iyi" değildir, düşük sermaye giriş bariyeri riskini TAŞIYABİLİR (02/İLKE-26, BAYRAK-20) — bu yüzden ağırlık DÜŞÜK tutuldu, tek başına belirleyici DEĞİL. |
| Nakit Kâr Kalitesi (OCF/Net Kâr, YENİ) | %10 | ≥1,0 güçlü, 0,7-1,0 orta, <0,7 zayıf (kaba, Piotroski'nin ikili OCF>NetKâr kriterinin SÜREKLİ versiyonu) | Tahakkuk/nakit ayrışması — kazanç KALİTESİNİN doğrudan göstergesi (01/Ch.12 KONTROL L, kısmen Schilit'in konusu ÖNCÜLÜ — Schilit eklendiğinde bu bileşen GENİŞLETİLECEK). |

**Toplam: %100.** Marjinal ROE ve Verimlilik Kaynaklı Ek Büyüme
bileşenleri BU mercekte SKORLANMAZ (ağırlık taşımaz) — bunlar `spec_
mercek_buyume.md`'de "büyüme kalitesi" alt-bileşenleri olarak yaşar (bkz.
Uygulama notu, çift-sayma önleme); burada SADECE veri kaynağı olarak
listelenmiştir çünkü ham verisi ROE ile aynıdır.

**SG&A/Brüt Kâr, Ar-Ge/Brüt Kâr, Faiz Gideri/Faaliyet Kârı:** VERİ EKSİK
olduğu için şimdilik SKORLANMAZ. Eşik tabloları (gelecekte veri gelirse
kullanılmak üzere) belgelenir:

| Gösterge | Eşik | Kaynak |
|---|---|---|
| SG&A/Brüt Kâr | <%30 fantastik, %30-80 mümkün, ~%100+ tekrarlayan=kırmızı bayrak | 02/FORMÜL-02, Eşikler tablosu |
| Ar-Ge/Brüt Kâr | %0 en iyi, ~%30 sürdürmek zorunda/kırılgan | 02/FORMÜL-03 |
| Faiz Gideri/Faaliyet Kârı | <%15 (tüketici ürünleri sektörü tipik üst sınır) | 02/FORMÜL-05, BAYRAK-06 |

---

## Sektör ayarlaması

1. **Banka/sigorta/finansman:** KALİTE merceği bu şablonlarda SADECE ROE +
   ROA (banka/finansman için zaten mevcut `aktif_karliligi` bileşeni ile
   AYNI ham veri) ile çalışır — FAVÖK/Brüt Marj/ROC kavramsal olarak
   UYGULANAMAZ (Greenblatt'ın kendi kapsam dışı bırakması, bkz. `spec_
   mercek_deger.md` amaç bölümü). Ağırlıklar bu iki bileşene ORANTISAL
   yeniden dağıtılır (ROE %70, ROA %30 — banka CONFIG'indeki mevcut
   göreli ağırlık oranı KORUNARAK).
2. **Sektör-göreli marj karşılaştırması (n≥5):** Brüt/Net marj mutlak
   eşiklerinin YANINDA (Buffett'ın kitabı zaten sektör-BAĞIMSIZ mutlak
   bantlar önerir, ör. %40 brüt marj), `sektor-siniflandirma` skill'in
   n≥5 kuralına uyan bir SEKTÖRE GÖRELİ ikinci okuma da EKLENEBİLİR (ör.
   "bu marj Sanayi üst-sektöründe medyan/üstünde mi") — bu, mutlak bandın
   YERİNE GEÇMEZ, TAMAMLAYICI bir bağlam notudur (mutlak taban/tavan
   kuralı: sektör toptan düşük-marjlı olsa bile [ör. perakende] "sektörün
   en iyisi" mutlak %15 net marjla asla "güçlü" ETİKETİ ALAMAZ — mutlak
   eşik HER ZAMAN üst sınırı belirler).
3. **ROC sektör bağımlılığı:** Greenblatt'ın kendi eşikleri (Yüksek≥25,
   Düşük≤10) sermaye-yoğun sektörlerde (ör. Enerji, Ana Metaller) sistemik
   olarak DÜŞÜK, hafif-varlıklı sektörlerde (Teknoloji, İletişim) sistemik
   olarak YÜKSEK çıkma eğilimindedir — bu SEKTÖR-BAĞIMLI eğilim kartta
   "bu sektörde ROC tipik olarak [düşük/yüksek] seyreder" notuyla
   (n≥5 varsa medyan verisiyle) belirtilir, ama MUTLAK eşik DEĞİŞTİRİLMEZ
   (Greenblatt'ın kendi metodolojisi zaten TÜM sektörlere aynı ölçütle
   bakmayı SAVUNUR — bu bilinçli bir metodoloji tercihidir, sektöre göre
   gevşetmek "Sihirli Formül"ün ÖZÜNÜ bozar).

---

## Kenar durumlar

- **Banka/finans net marj TERS kuralı (02/İLKE-13, BAYRAK-08):** Banka/
  finans şirketlerinde ANORMAL YÜKSEK net kâr marjı KALİTE değil RİSK
  sinyalidir (gevşek risk yönetimi) — bu şablonlarda Net Marj bileşeni
  HİÇ KULLANILMAZ (zaten yukarıdaki sektör ayarlamasında ROE+ROA'ya
  indirgendi), bu yüzden çelişki fiilen ORTADAN KALKAR.
- **Negatif özkaynak (ROE tanımsız/anormal):** 02/İLKE-36,41'in KRİTİK
  ayrımı UYGULANIR — negatif özkaynak/anormal yüksek ROE İKİ NEDENDEN
  gelebilir: (a) güçlü/tutarlı net kâr geçmişiyle BİRLİKTE bilinçli tam-
  dağıtım politikası (Microsoft örneği, OLUMLU), (b) zayıf net kâr
  geçmişiyle BİRLİKTE iflasa sürüklenme (GM örneği, OLUMSUZ). QuaxisLabs
  bu ayrımı YAPACAK çok-yıllı net kâr trend serisine SAHİP DEĞİL (12
  çeyrek/~3 yıl sınırı) — bu yüzden negatif özkaynak durumunda ROE
  bileşeni SESSİZCE yüksek/düşük puan ÜRETMEZ, "negatif özkaynak — Warren
  Buffett çerçevesine göre bu ya bilinçli tam-dağıtım politikası (olumlu)
  ya iflas riski (olumsuz) anlamına gelebilir, ayrım için çok-yıllı kazanç
  geçmişi gerekir" NİTEL notuyla `None` döner (bileşen ATLANIR, ağırlığı
  yeniden dağıtılır) — Kural 3 (uydurma yapma) burada AÇIKÇA uygulanır.
- **AAPL-tipi düşük özkaynak tabanı:** SCORING_METHODOLOGY.md'nin bilinen
  sınırı (agresif geri alım → yapay yüksek ROE) KORUNUR; KALİTE
  merceğinde bu durum "ROE %25 tavanının ÇOK ÜZERİNDE (asimptotik skor
  ~10'a yakın) AMA düşük özkaynak tabanlı — hazine hissesi düzeltmeli ROE
  verisi eksik, tek başına yorumlanmamalı" notuyla İŞARETLENİR (Damodaran
  BAYRAK-25'in DEĞER merceğindeki ROE-ke kontrolüyle KESİŞİR, çapraz
  referans verilir).
- **Eksik brüt kâr (bazı hizmet/finansal şirketlerde `gross_profit`
  anlamsız):** Brüt Marj bileşeni `None` ise atlanır, ağırlığı diğerlerine
  dağıtılır (mevcut Kural 3 mekanizması).
- **Nakit Kâr Kalitesi negatif net kârda:** `net_income<=0` iken oran
  matematiksel olarak ANLAMSIZ (işaret tersine döner) — bu durumda
  bileşen `None` döner, ATLANIR (uydurma yapılmaz).

---

## Test senaryoları

1. **THYAO (BIST sanayi):** FAVÖK marjı ~%15-20 (orta-güçlü), ROE ~%20+
   (güçlü), Net marj ~%8-12 (orta), Brüt marj hava taşımacılığında
   genelde düşük-orta (%20-30 bandı, sektöre göre "orta" ETİKETİ) → KALİTE
   toplamı orta-güçlü aralıkta, açık büyük zayıflık YOK.
2. **Sermaye-hafif bir BIST teknoloji şirketi:** Yüksek ROC (Greenblatt
   Yüksek bandı), yüksek ROA, ama küçük ölçek nedeniyle FAVÖK marjı
   OYNAK → bileşenler ARASINDA gerilim, kart bunu "kaliteli sermaye
   verimliliği ama kârlılık istikrarı henüz kanıtlanmadı" diye
   YANSITMALI (bileşenlerin AYRI AYRI gösterilmesi zaten bunu sağlar).
3. **Negatif özkaynaklı bir BIST şirketi (örn. büyük kur zararı yaşamış
   sanayi şirketi):** ROE bileşeni `None`, nitel not görünür; diğer
   bileşenler (FAVÖK marjı, Brüt marj, ROC) BAĞIMSIZ çalışmaya devam
   eder — toplam KALİTE skoru YİNE ÜRETİLİR (tek bileşen eksikliği tüm
   mercek çökmesine yol AÇMAZ).
4. **Banka (örn. AKBNK):** KALİTE merceği SADECE ROE+ROA'dan oluşur,
   diğer 4 bileşen "bu şirket türünde uygulanamaz" notuyla HİÇ
   GÖSTERİLMEZ (None değil, YAPISAL OLARAK YOK — kartta boş satır DEĞİL,
   şablon farkı AÇIKÇA belirtilir).

---

## Uygulama notu (izlenebilirlik ve çift-sayma)

- **ROE çift-sayma:** ROE hem burada (doğrudan skorlanan KALİTE bileşeni,
  %20 ağırlık) hem DEĞER merceğinde (Damodaran FCFE modelinin `g/ROE`
  girdisi, DOLAYLI) hem BÜYÜME merceğinde (temel büyüme = tutma oranı×ROE,
  DOLAYLI) kullanılır. `temel-analiz-cercevesi` skill madde 7 gereği bu
  KORELASYON `spec_bilesik_skor.md`'de merkezi bir NOT olarak işaretlenir
  — sadece BU mercekte (KALİTE) DOĞRUDAN ağırlık taşır, diğer ikisinde
  GİRDİ PARAMETRESİ rolündedir (farklı SORULARA cevap verir: "ne kadar
  kaliteli" vs "ne kadar ucuz" vs "ne kadar büyüyor").
- **Greenblatt ROC vs mevcut FAVÖK/Net Marj:** ROC (EBIT/Yatırılan
  Sermaye) ile FAVÖK Marjı (FAVÖK/Hasılat) FARKLI PAYDALARA sahiptir
  (sermaye vs hasılat) — biri VERİMLİLİK, diğeri OPERASYONEL KÂRLILIK
  ölçer, KAVRAMSAL olarak AYRI sinyallerdir, çift sayma sayılmaz.
- **Marjinal ROE / Verimlilik Kaynaklı Büyüme:** Bu iki YENİ bileşenin
  ev sahibi BÜYÜME merceğidir (bkz. `spec_mercek_buyume.md`) — burada
  SADECE veri kaynağı/formül referansı olarak listelenmiştir, KALİTE
  toplamına KATILMAZ (aynı ham veriden [ROE serisi] türedikleri için
  KALİTE'nin ROE bileşeniyle ÇİFT SAYILMASINI önlemek amacıyla BİLİNÇLİ
  olarak tek mercekte tutulur).
