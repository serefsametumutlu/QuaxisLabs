# SPEC: Değer Merceği (v2 Çok-Mercekli Skorlama — Mercek 1/4)

## Amaç ve kapsam

**Ölçtüğü soru:** Fiyat ↔ değer farkı var mı — hisse, ödediğiniz paraya göre ucuz mu?
Bu mercek Graham'ın "ucuzluk" disiplinini (mutlak eşikler) ve Damodaran'ın
"göreli/DCF değerleme" çerçevesini (sektöre/zamana göre kayan eşikler,
istatistiksel titizlik) **AYRI AYRI** sunar — 00_sentez.md §2.1'de
belgelenen çelişki (Graham'ın sabit eşikleri vs Damodaran'ın "ortalamaya
göre ucuz" yanılgısı eleştirisi) burada ÇÖZÜLMEZ, iki alt-mercek (Mutlak
Ucuzluk + Göreli Konum) olarak YAN YANA sunulur.

**Geçerli şirket türleri:** `sanayi`, `abd_sanayi`, `banka`, `sigorta`,
`finansman` — DÖRDÜ de (scorer.py'de zaten CONFIG altında ayrı eşik
setleriyle var). `gyo` için ayrı eşik seti bu spec'in kapsamı DIŞINDA
(veri/kalibrasyon yok — mevcut `sanayi` şablonuna geçici olarak düşer, Faz
sonrası ayrı ele alınmalı).

**Piyasalar:** BİST + NASDAQ. NASDAQ tarafında `abd_sanayi` eşik seti
kullanılır (SCORING_METHODOLOGY.md'de CANLI araştırılmış F/K~18-25,
PD/DD~2,9-6,0 medyan/ortalama bantları).

**Kapsam dışı:** Tahvil/imtiyazlı hisse değerlemesi (Graham Ch.16, Kısım
5), portföy-seviyesi hisse/tahvil tahsisi, fon seçimi (Graham Ch.9) —
QuaxisLabs tekil hisse/kripto analiz motorudur.

---

## Girdiler

| Alan | Kaynak | Durum |
|---|---|---|
| `pe_ratio` (F/K, TTM) | `calculator.ValuationMetrics.pe_ratio` | MEVCUT |
| `pb_ratio` (PD/DD) | `calculator.ValuationMetrics.pb_ratio` | MEVCUT |
| `ev_ebitda` (FD/FAVÖK) | `calculator.ValuationMetrics.ev_ebitda` | MEVCUT |
| `ev_revenue` (FD/Hasılat) | `calculator.ValuationMetrics.ev_revenue` | MEVCUT |
| `price_to_operating_profit` (PD/EFK) | `calculator.ValuationMetrics.price_to_operating_profit` | MEVCUT — **TANIM HATASI** (bkz. Kenar Durumlar) |
| Greenblatt Kazanç Getirisi (EBIT/FD) | `fundamental_screens.GreenblattResult.earnings_yield_pct` | MEVCUT (SADECE BIST XI_29 sanayi) |
| Carlisle Acquirer's Multiple (FD/EBIT) | `fundamental_screens.AcquirersMultipleResult` | MEVCUT (SADECE BIST XI_29 sanayi) |
| Graham Çarpanı/Sayısı (F/K×PD/DD≤22,5) | `valuation.py::compute_valuation_assessment` (graham_*) VE `fundamental_screens._compute_graham` | MEVCUT — **İKİ modülde AYNI formül, TEK kaynaktan besleniyor gibi görünmeli (bkz. Uygulama notu)** |
| Peter Lynch PEG oranı | `valuation.py::compute_valuation_assessment` (peg_ratio) | MEVCUT — **büyüme bazı revenue (kitaba göre net kâr/HBK olmalı), TANIM SAPMASI (bkz. Kenar Durumlar); kanonik ev sahibi BÜYÜME merceğidir, bkz. `spec_mercek_buyume.md`** |
| Damodaran İstikrarlı Büyüme FCFE | `valuation.py::compute_valuation_assessment` (damodaran_*) | MEVCUT (β=1, statik risksiz faiz/prim) |
| Sektöre göreli F/K, PD/DD konumu | `valuation.py::compute_valuation_assessment` (sector_avg_*, verdict) | MEVCUT — n≥3 kuralı `sektor-siniflandirma` skill'in n≥5 kuralıyla ÇAKIŞIYOR, YÜKSELTİLMELİ (bkz. Sektör Ayarlaması) |
| Kazanç Getirisi (E/P) | YOK, `1/pe_ratio` ile TÜRETİLEBİLİR | **YENİ (ucuz)** — kod ile DOĞRULANDI (`pe_ratio` mevcut, tek satır türetim) |
| NCAV / Net-Net testi | `current_assets`, `total_assets`, `equity` (ham veri MEVCUT) | **YENİ (orta maliyet)** |
| Nakit-arındırılmış F/K, PD/DD | `cash`, `market_cap`, `equity` (ham veri MEVCUT) | **YENİ (ucuz)** |
| DPS / temettü verimi | YOK | VERİ EKSİK — **BİST:** KAP XBRL `ifrs-full_DividendsPaid`/`ifrs-full_DividendPerShare` ile Faz sonrası araştırma+fetcher gerekir, ORTA maliyet (00_sentez.md §4 öncelik #1). **NASDAQ:** `us-gaap:CommonStockDividendsPerShareDeclared`/`us-gaap:PaymentsOfDividends` standart US GAAP taksonomi tag'leridir — `sec_edgar.py`'nin mevcut `STANDARD_ITEM_MAP_US_GAAP` desenine (aday-tag listesi) DÜŞÜK maliyetle eklenebilir (bkz. `docs/spec/veri_tamlik_notu.md` D2). |
| Risksiz faiz oranı (canlı) | `valuation._RISK_FREE_RATE_PCT` (statik) | KISMEN — elle güncellenen sabit (`{"TRY": 32, "USD": 4.3}`, kod ile doğrulandı) |

---

## Formüller

### 1. Mutlak Ucuzluk Alt-Mercek

```
# Mevcut scorer._skor_degerleme() MANTIĞI KORUNUR — sadece "Değerleme"
# bileşeni artık DEĞER merceğinin ÇEKİRDEĞİ olarak yaşar (Kural 8: çöpe
# atma, genişleyerek taşı).
pe_skor = kademeli_enterpolasyon(pe, [0, fk_ucuz, fk_makul, fk_pahali, fk_tavan], [10,9→8,6→5,3→2,0])
pb_skor = kademeli_enterpolasyon(pb, [0, pddd_ucuz, pddd_makul, pddd_pahali, pddd_tavan], [10,9→8,6→5,3→2,0])
mutlak_ucuzluk_skoru = ortalama(pe_skor varsa, pb_skor varsa)
# F/K negatifse (zarar) VE PD/DD tek başına katkı veriyorsa: "değer tuzağı
# tavanı" 7,5'e kırpma KORUNUR (scorer.py satır 634-641, AYNEN taşınır).
```

> **KOD-GELİŞTİRİCİ DEVİR NOTU (quant_denetim_01.md K1):** `kademeli_
> enterpolasyon`, mevcut `_seviye_trend_skoru`/`_lerp_score` ailesinin AYNI
> "bozuluyor" dalı mantığını miras alıyorsa, trend işareti sıfırı geçtiği
> an ~5+ puanlık sert bir skor uçurumu (cliff) oluşabilir — somut kanıt
> (kalibrasyon scripti + kod okumasıyla doğrulandı): FAVÖK marjı %40 iken
> `trend_puan=-0,01`→`+0,00` arası skor **4,00→9,33** sıçrıyor. Ayrıca
> bant sınırları `[0,4]-[5,7]-[8,10]` şeklinde ARALARINDA BOŞLUK bırakacak
> tanımlı (4→5 ve 7→8 arası atlanıyor, süreklilik YOK). **Düzeltme:**
> "bozuluyor" dalı sert eşik yerine trend büyüklüğüne göre SÜREKLİ bir
> ceza-çarpanına çevrilmeli (örn. `ceza_carpani = _lerp_score(trend_puan,
> -X, 0, 0.5, 1.0)`, normal skorla ÇARPILARAK uygulanır), bant sınırları
> UÇLARI ÇAKIŞACAK şekilde `[0,4]-[4,7]-[7,10]` olarak yeniden tanımlanmalı.
> Bu motor DEĞER/KALİTE/BÜYÜME/GÜVENLİK'in DÖRDÜNDE de kullanıldığı için
> düzeltme `scorer.py` çekirdeğinde TEK yerde yapılmalı, spec'ler sadece bu
> devir notunu taşır (tam kanıt/kalibrasyon detayı: `quant_denetim_01.md` K1).

### 2. Kazanç Getirisi vs Risksiz Oran (YENİ)

```
kazanc_getirisi_pct = 100 / pe_ratio   (pe_ratio > 0 ise; pe_ratio <= 0 → None)
risksiz_fark_puan = kazanc_getirisi_pct - risksiz_faiz_pct[currency]
# Graham FORMÜL-03/36: E/P >= risksiz faiz ZORUNLU minimum; tercihli hedef
# risksiz faizden anlamlı ölçüde (+2-3 puan) yüksek.
```

### 3. Graham Çarpanı / Sayısı (MEVCUT, taşınır)

```
graham_carpani = own_pe * own_pb
graham_adil_fiyat = current_price * sqrt(22.5 / graham_carpani)   # own_pe,own_pb > 0 ZORUNLU
```

### 4. NCAV / Net-Net Testi (YENİ)

```
net_isletme_sermayesi = current_assets - total_liabilities
  # total_liabilities = total_assets - equity (TÜRETİLİR)
if net_isletme_sermayesi <= 0:
    net_net_iskonto_pct = None   # bonus TETİKLENMEZ, 0 katkı (ceza YOK)
    # DÜZELTME (quant_denetim_01.md K2 — KALİBRASYONLA DOĞRULANDI):
    # BİST sanayi örnekleminde %52,1 (86/165), NASDAQ sanayi'de %71,4
    # (15/21) şirkette bu KOŞUL tetiklenir -- "nadir bir kenar durum"
    # DEĞİL, örneklemin YARISINDAN FAZLASINI etkileyen SİSTEMİK bir
    # guard'dır; bu yüzden kod YORUMU değil, formülün AYRILMAZ bir DALI
    # olarak (aşağıdaki gibi) yazılmalıdır.
else:
    ncav_hisse_basi = net_isletme_sermayesi / share_capital
    net_net_iskonto_pct = (market_cap - net_isletme_sermayesi) / net_isletme_sermayesi * 100
      # negatifse: piyasa değeri NCAV'ın ALTINDA -- Graham "bargain" sinyali
```

### 5. Greenblatt Kazanç Getirisi + Carlisle Acquirer's Multiple (MEVCUT, taşınır)

```
earnings_yield_pct = ebit / enterprise_value * 100      # zaten fundamental_screens.py'de
acquirers_multiple = enterprise_value / ebit             # zaten fundamental_screens.py'de
```

### 6. Sektöre Göreli Çarpan Konumu (MEVCUT ama YÜKSELTİLİR)

```
# Mevcut basit ortalama YERİNE (bkz. Sektör Ayarlaması):
sektor_medyan_fk, sektor_mad_fk = robust_istatistik(ust_sektor, sirket_turu, "pe_ratio")
# DÜZELTME (quant_denetim_01.md Y2): "Robust istatistik" başlığı MAD-
# normalize edilmiş bir z-skor VAAT EDİYOR ama önceki taslakta
# sektor_mad_fk hesaplanıp SKORLAMA formülünde HİÇ KULLANILMIYORDU (sadece
# düz yüzde sapma). Skorlama İÇİN gerçek robust z-skor kullanılır (BİST
# FAVÖK marjı gibi geniş varyanslı metriklerde düz yüzde-sapma GÜRÜLTÜLÜ
# bir sinyaldir — kalibrasyon kanıtı: p10=-6,44/p90=42,51):
sektor_z_skoru = (own_pe - sektor_medyan_fk) / (1.4826 * sektor_mad_fk)   # sektor_mad_fk>0 ZORUNLU, aksi halde None
# Kart GÖRÜNÜMÜ için insan-okunur yüzde sapma AYRICA hesaplanır (SKORLAMAYA
# GİRMEZ, sadece açıklama metninde kullanılır):
sapma_pct = (own_pe - sektor_medyan_fk) / sektor_medyan_fk * 100
```

### 7. Damodaran İstikrarlı Büyüme FCFE (MEVCUT, taşınır, değişmez)

```
reinvestment_rate = g / ROE
fcfe = ttm_net_income * (1 - reinvestment_rate)
ozkaynak_degeri = fcfe * (1+g) / (r-g)
```

---

## Eşikler ve ağırlıklar

**DEĞER merceği iç ağırlıkları (mercek-içi bileşik, toplam %100):**

| Bileşen | Ağırlık | Gerekçe / kaynak |
|---|---|---|
| Mutlak Ucuzluk (F/K+PD/DD, mevcut scorer çekirdeği) | %35 | Kalibre edilmiş, canlı doğrulanmış — mercek çekirdeği KORUNUR (persona kural 8). Kaynak: 01/FORMÜL-02 (F/K bandı), 01/İLKE-80,133 (PD/DD ≤1,33× Ch.8 / ≤1,5× Ch.13-14 — İKİSİ AYRI kullanılır, bkz. Kenar Durumlar), SCORING_METHODOLOGY.md mevcut kalibrasyonu. |
| Sektöre Göreli Konum (medyan bazlı, n≥5) | %20 | Damodaran BAYRAK-20 ("ortalamaya göre ucuz" sistematik yanılgı) uyarısını doğrudan uygular; mutlak eşiğin TEK BAŞINA yeterli olmadığı (03/İLKE-197: "FD/FAVÖK<7x=ucuz" kuralının 1.500 firma tarafından çürütülmesi) prensipçe kabul edilir. n<5 ise ağırlık mutlak-ucuzluğa devredilir (bkz. Sektör Ayarlaması). |
| Kazanç Getirisi vs Risksiz Oran | %15 | Üç kitabın da bağımsız vurguladığı kesişim (01/FORMÜL-03,36; 02/İLKE-52-57 equity bond; 03/FORMÜL-84) — 00_sentez.md §1.4'te "en olgun kesişim" olarak işaretlendi. |
| Graham Çarpanı (F/K×PD/DD≤22,5) | %10 | 01/FORMÜL-21,32 — kitabın kendi "savunmacı yatırımcı" resmi eşiği, zaten kalibre kod var (`valuation.py`). |
| Greenblatt Kazanç Getirisi (EBIT/FD) | %10 | Greenblatt'in "Sihirli Formül"ünün DEĞER bacağı — FD-bazlı olduğu için borç etkisini F/K'dan daha iyi kapsar (kaynak: proje mevcut `fundamental_screens.py` modül notu, SADECE XI_29 sanayi). Veri yoksa (banka/sigorta/NASDAQ) ağırlık diğerlerine dağıtılır. |
| Carlisle Acquirer's Multiple (FD/EBIT) | %5 | Greenblatt'in tek-çarpanlı sadeleştirmesi — DÜŞÜK ağırlık çünkü Kazanç Getirisi ile aynı ham veriden türer (çift sayma riski düşük tutmak için hafif ağırlık, bkz. Uygulama notu). |
| NCAV / Net-Net Bonus | %5 (bonus, taban etkisi) | 01/İLKE-64,66,75, FORMÜL-01,12,14 — Graham'ın "en kolay tanımlanabilir pazarlık" testi; SADECE hisse NCAV'ın ALTINDA fiyatlanıyorsa devreye girer (aksi halde 0 katkı, CEZALANDIRMAZ). |

**Mutlak Ucuzluk alt-eşikleri:** `scorer.py CONFIG[template]["degerleme"]`
BİREBİR KORUNUR (sanayi: F/K ucuz<8/makul<15/pahalı<25/tavan40, PD/DD
ucuz<1/makul<2,5/pahalı<5/tavan8; abd_sanayi: F/K ucuz<12/makul<20/pahalı
<30/tavan50, PD/DD ucuz<1,5/makul<3/pahalı<6/tavan12; banka/sigorta/
finansman kendi CONFIG'leri) — gerekçe zaten SCORING_METHODOLOGY.md'de
belgeli, TEKRAR YAZILMAZ.

> **GÜNCELLİK UYARISI (quant_denetim_01.md GÖREV 2, kalibrasyonla
> doğrulandı):** `scripts/kalibrasyon_v2.py`'nin 165/167 BİST sanayi
> şirketi için CANLI fiyatla çalıştırılan koşusu, mevcut `fk_ucuz=8`
> eşiğinin örneklemin **%59,7'sini** (95/159), `pddd_ucuz=1` eşiğinin
> **%42,4'ünü** (70/165) ve Graham Çarpanı ≤22,5 eşiğinin **%54,4'ünü**
> (49/90) "ucuz" bandına düşürdüğünü gösterdi — bu, 00_sentez §2.1'in
> Damodaran uyarısının ("sabit eşikler zaman/piyasaya göre kayar, 'ucuz'
> etiketi sistematik olarak ÇOK FAZLA firmayı kapsayabilir") BU GÜNKÜ
> BİST rejiminde SOMUT/CANLI kanıtıdır. **Bu turda eşik DEĞİŞTİRİLMİYOR**
> (v1 kalibrasyonu AYNEN taşınır, persona kural 8) — sadece gelecekte
> GÜNCEL bir medyan/persentil bazlı kalibrasyon turunun (winsorize edilmiş
> uç değerlerle) gerekli olduğu belgelenir.

**Kazanç Getirisi eşikleri:**

| Durum | Yorum | Kaynak |
|---|---|---|
| E/P < risksiz faiz | Güvenlik marjı YOK — hisse tahvilden DAHA AZ (risksiz) getiri vaat ediyor | 01/FORMÜL-03,36 |
| risksiz faiz ≤ E/P < risksiz faiz+2 puan | Sınırda, minimum şart karşılanıyor | 01/İLKE-140,141 (AA tahvil bazlı dinamik F/K tavanı) |
| E/P ≥ risksiz faiz+2 puan | Tercihli hedef karşılanıyor | 01/İLKE-140-141, 03/FORMÜL-84 |

---

## Sektör ayarlaması

`sektor-siniflandirma` skill madde 1-3 BİREBİR uygulanır:

1. **n≥5 kuralı:** Sektöre Göreli Konum bileşeni SADECE `(ust_sektor,
   sirket_turu)` grubunda n≥5 taranmış şirket varsa hesaplanır (mevcut
   `valuation.py`'nin n≥3 eşiği `_MIN_PEER_COUNT_FOR_SECTOR_COMPARISON`
   **5'E YÜKSELTİLMELİDİR** — sektor-siniflandirma skill'in n≥5 kuralıyla
   TUTARLI olması için; ayrıca gruplama anahtarı `(sector, financial_group)`
   yerine `(ust_sektor, sirket_turu)` olmalı, bkz. `spec_sektor_evren.md`
   "Mevcut sınırlama tespiti" notu). BİST Sağlık/Enerji (n=4) için kartta
   "sektör karşılaştırması için yetersiz örneklem (n=4)" notu ZORUNLU.
2. **Robust istatistik:** Ortalama YERİNE MEDYAN + MAD (%5-%95 winsorize) —
   03/BAYRAK-20 (pozitif çarpıklık, ortalama HER ZAMAN medyandan yüksek,
   Ocak 2005 örneği: medyan P/E 23 vs ortalama 48). **Küçük n uyarısı
   (quant_denetim_01.md Y3, kalibrasyonla doğrulandı):** gerçek DB
   dağılımında n<10 olan gruplar (BİST sigorta n=4, BİST bankalar n=8 gibi)
   ÇOĞUNLUKTA — bu gruplarda %5-%95 winsorizasyonu PRATİKTE en fazla 0-1
   gözlemi etkiler, fiilen ETKİSİZDİR. Bu bir hata değil, kod yorumunda
   AÇIKÇA belgelenmesi gereken bilinen bir SINIRDIR.
3. **Mutlak taban/tavan harmanı:** Sektöre göreli "ucuz" (medyan altı) skoru
   TEK BAŞINA kullanılmaz — Mutlak Ucuzluk bileşeniyle HARMANLANIR (ağırlık
   tablosunda %35 vs %20). Gerekçe: "kötü sektörün en iyisi" (tüm sektör
   toptan pahalı/riskli olsa bile sektör-içi en düşük çarpanlı şirket)
   mutlak yüksek DEĞER puanı ALAMAZ — 03/İLKE-186 (çapraz ülke P/E kıyası
   örneği: Japonya ham P/E'de en pahalı ama makro kontrol sonrası
   Brezilya çıkması) AYNI mantığın somut kanıtı.
4. **n<5 durumunda:** Sektöre Göreli Konum ağırlığı (%20) Mutlak Ucuzluğa
   (%35→%55) ORANTISAL yeniden dağıtılır (scorer.py'nin genel `_agirlik_
   dagit_ve_hesapla` mekanizmasıyla AYNI ilke).
5. **Negatif kazançlı şirketler örneklem dışı bırakma yanlılığı (03/İLKE-156,
   BAYRAK-21):** Sektör medyanı hesaplanırken F/K için zarar eden şirketler
   örneklemden düşer — bu YANLILIK kart üzerinde "sektör medyanı N/[toplam
   sektör şirketi] üzerinden" notuyla AÇIKÇA belirtilir.

---

## Kenar durumlar

- **Negatif özkaynak (PD/DD tanımsız):** `pb_ratio` None kalır (mevcut
  davranış). Bir de: bu durumun KENDİSİ 03/İLKE-441-442 (Eurotunnel örneği
  — negatif defter özkaynağına RAĞMEN pozitif piyasa değeri NORMAL
  olabilir, özkaynak bir call opsiyonudur) uyarınca "derin sıkıntı/opsiyon
  karakteri" etiketiyle GÜVENLİK merceğine (bkz. `spec_mercek_guvenlik.md`
  BAYRAK-83) çapraz referans verilir — DEĞER merceğinde "N/A" gösterilir,
  UYDURULMAZ.
- **Zarar eden şirket (F/K negatif):** Mutlak Ucuzluk alt-mercek SADECE
  PD/DD'den hesaplanır, "değer tuzağı tavanı" (7,5) mevcut mantıkla
  KORUNUR. Kazanç Getirisi bileşeni de None kalır (E/P tanımsız) — 03/
  İLKE-156'nın önerdiği "her firma için hesaplanabilen TERSİNİ kullan"
  çözümü BİLEREK uygulanmaz (E/P negatif kazançta MATEMATİKSEL olarak
  hesaplanabilir ama YORUMU yanıltıcıdır — negatif E/P'nin "büyüklüğü"
  zarar büyüklüğünü değil kazanç YAKINLIĞINI yanlış sıralar); bu yüzden
  Kazanç Getirisi bileşeni de "değerlendirme dışı" sayılır ve ağırlığı
  yeniden dağıtılır.
- **Şirket türü PD/DD eşiği ikiliği (Graham'ın kendi iç tutarsızlığı):**
  Ch.8 (≤1,33×, genel muhafazakar kılavuz) ve Ch.13/14 (≤1,5×, resmi
  7-kriter listesi) AYRI bağlamlardır (00_sentez.md §2.2). v2'de Graham
  Sayısı (F/K×PD/DD≤22,5, kod tarafı ≤1,5× varsayımına dayanır) TEK resmi
  eşik olarak KULLANILIR; ≤1,33× SADECE kart açıklama metninde "daha
  muhafazakar bir alternatif eşik de literatürde mevcuttur" notuyla anılır,
  AYRI bir skorlanan bileşen OLUŞTURULMAZ (ikisini AYNI ANDA skorlamak
  çift sayma riski taşır).
- **NASDAQ opsiyon/warrant/dönüştürülebilir seyreltme:** 03/İLKE-167-169
  (opsiyon-katkılı özkaynak) VERİ EKSİK (çalışan opsiyon verisi yok) —
  NCAV ve Graham Sayısı hesaplarında seyreltme DÜZELTMESİ YAPILMAZ, kart
  "tam seyreltilmiş olmayan pay sayısına göre" notuyla İŞARETLENİR.
  **NÜANS (bkz. `docs/spec/veri_tamlik_notu.md` D3):** bu TAM bir bloker
  DEĞİL — `sec_edgar.py` satır 395'te `us-gaap:WeightedAverageNumberOf
  DilutedSharesOutstanding` ZATEN pay-sayısı YEDEK tag'i olarak kullanılıyor;
  `us-gaap:WeightedAverageNumberOfSharesOutstandingBasic` (temel pay sayısı)
  eklenip bu ikisinin FARKI alınarak KABA bir opsiyon-seyreltme yüzdesi
  (SADECE NASDAQ) türetilebilir, dipnot/metin okuma GEREKTİRMEZ. Bu, 00_
  sentez §4'ün 13 maddesine henüz GİRMEMİŞ bir kalemdir — gelecek turda
  §4'e 14. madde olarak eklenmesi önerilir. BİST tarafında (opsiyon bazlı
  ücretlendirme KAP'ta standart bir XBRL etiketiyle raporlanmıyor) TAM
  bloker olarak KALIR.
- **Azınlık payı kirliliği (BAYRAK-28/29):** Konsolide holding şirketlerinde
  `pb_ratio`'nun paydası (`equity`, azınlık payı DAHİL) ile payı
  (`market_cap`, ana ortaklık-only) AYNI kapsamı YANSITMAZ — bu YAPISAL
  bir tutarsızlıktır (veri eksikliği DEĞİL, TANIM sorunu). Önemli-azınlık-
  paylı BIST holdinglerinde (KAP ince sektör "HOLDİNGLER VE YATIRIM
  ŞİRKETLERİ") kartta "bu şirkette PD/DD azınlık payı nedeniyle yapay
  düşük çıkabilir" UYARISI eklenmelidir (veri eksikliği giderilene kadar).
  `pe_ratio` bu sorunu TAŞIMAZ (hem `market_cap` hem `net_income` ana-
  ortaklık-only) — bu ASİMETRİ kart dokümantasyonunda AÇIKÇA belirtilmeli.
- **PD/EFK tanım hatası (BAYRAK-19):** `price_to_operating_profit`
  (`market_cap/ttm_operating_profit`) pay-özkaynak/payda-firma-geneli
  TUTARSIZLIĞI taşır — yüksek borçlu şirketler bu metrikte YAPAY ucuz
  görünür. **Önerilen düzeltme:** `enterprise_value/ttm_operating_profit`
  (FD/EFK) olarak YENİDEN TANIMLANMALI (ham veri zaten mevcut,
  `enterprise_value` hesaplı) — bu bir kod değişikliği önerisidir, spec
  seviyesinde işaretlenir.
- **Sıkıntı sinyali (BAYRAK-76):** F/K veya PD/DD hesaplanamıyor (negatif
  kazanç/özkaynak) AMA FD/FAVÖK veya FD/Hasılat GEÇERLİ değer üretiyorsa,
  bu DURUMUN KENDİSİ (03/İLKE-435) bir GÜVENLİK sinyalidir — DEĞER
  merceğinde "sınırlı çarpan seti, dikkatli yorumlanmalı" notu, tam analiz
  `spec_mercek_guvenlik.md`'ye yönlendirilir.
- **Eksik çeyrek / kısmi TTM:** Mevcut Kural 3 (`_trailing_4q_sum`) AYNEN
  korunur — 4 çeyreğin tamamı yoksa `None`, "N/A".
- **Halka arz sonrası kısa geçmiş:** Sektöre Göreli Konum n≥5 kuralı zaten
  bu durumu KISMEN kapsar (yeni şirketin KENDİSİ n sayımına dahil olur,
  engel değildir); ama NCAV/Graham Sayısı gibi TEK dönemlik metrikler
  ETKİLENMEZ (çok-yıllı seri gerektirmezler) — SADECE Damodaran FCFE
  modelinin `g` girdisi (hasılat YoY büyümesi) ilk çeyrekte `None` olacağı
  için o alt-bileşen atlanır.

---

## Test senaryoları

1. **THYAO (BIST, sanayi, sektör Sanayi/Ulaştırma):** F/K=6,2, PD/DD=1,1 →
   Mutlak Ucuzluk ≈9,x (F/K ucuz bandın altında, PD/DD ucuz bandın hemen
   üstünde); sektörde n≥5 varsa medyan karşılaştırması eklenir; Kazanç
   Getirisi = 100/6,2=%16,1, TRY risksiz faiz %32'nin ALTINDA → bu
   bileşen DÜŞÜK puan (nominal yüksek enflasyon rejiminde E/P'nin TL
   risksiz faizle kıyaslanmasının SERTLİĞİ kart açıklamasında not
   düşülmeli — TMS-29 etkisiyle nominal TL faiz oranları karşılaştırma
   tabanını YAPAY yüksek tutar, bu YAPISAL bir Türkiye çekincesidir).
2. **Zarar eden ama düşük PD/DD'li bir BIST sanayi şirketi (örn. BORSK
   tipi, kullanıcı geri bildiriminde geçen):** F/K None, PD/DD=0,6 →
   Mutlak Ucuzluk SADECE PD/DD'den, "değer tuzağı tavanı" 7,5'e kırpılır;
   Kazanç Getirisi None (ağırlığı yeniden dağıtılır); NCAV testi AYRI
   çalışabilir (negatif kazanç NCAV hesabını ENGELLEMEZ, sadece bilanço
   verisine bakar).
3. **AAPL (NASDAQ, abd_sanayi):** F/K=~28-32 (abd_sanayi bandında "makul-
   pahalı" arası), PD/DD çok yüksek (düşük özkaynak tabanı, agresif geri
   alım) → Mutlak Ucuzluk PD/DD'de DÜŞÜK puan üretir ama kart açıklaması
   "düşük özkaynak tabanı, aşırı kârlılık değil" notunu (mevcut
   SCORING_METHODOLOGY.md bilinen sınırı) TAŞIR; NCAV testi ANLAMSIZ
   (ABD teknoloji şirketleri net-net bandının ÇOK ÜZERİNDE), bu yüzden
   NCAV bonusu hiç TETİKLENMEZ (0 katkı, ceza YOK).
4. **KAP holding şirketi (yüksek azınlık payı, örn. büyük bir BIST
   holding):** PD/DD hesaplanır ama BAYRAK-28/29 notu kartta GÖRÜNÜR —
   test, notun DOĞRU KOŞULDA (KAP ince sektör = "HOLDİNGLER VE YATIRIM
   ŞİRKETLERİ") tetiklendiğini doğrular.
5. **n=4 sektör (BİST Sağlık):** Sektöre Göreli Konum bileşeni ATLANIR,
   "yetersiz örneklem (n=4)" notu görünür, ağırlık Mutlak Ucuzluğa
   devredilir — toplam DEĞER skoru YİNE de üretilir (sadece o alt-bileşen
   eksik).

---

## Uygulama notu (izlenebilirlik ve çift-sayma)

- `valuation.py::_compute_graham` (fundamental_screens.py içinde) ve
  `compute_valuation_assessment` (valuation.py içinde) AYNI Graham
  formülünü BAĞIMSIZ olarak yeniden hesaplıyor (kod modül notu bunu zaten
  KABUL EDİYOR: "iki modul BAGIMSIZ... sabitin kendisi Graham'in KENDI,
  degismeyen tarihsel esigi oldugu icin ayni deger IKI modulde de tekrar
  tanimlanir"). v2 skorlama katmanında bu İKİ çıktı TEK bir DEĞER mercek
  bileşenine (Graham Çarpanı, %10 ağırlık) BİRLEŞTİRİLİR — hangi modülün
  çağrıldığı çağıran koda (pipeline.py) bağlıdır, spec seviyesinde ikisi
  de "aynı kaynak" sayılır, ÇİFT SAYILMAZ.
- Greenblatt Kazanç Getirisi (EBIT/FD) ile mevcut F/K (Net Kâr/Piyasa
  Değeri) FARKLI paydalar (Firma vs Özkaynak) kullanır — bu YAPISAL fark
  ("borç etkisini kapsar/kapsamaz") bilinçlidir, ÇİFT SAYMA sayılmaz
  (03/İLKE-152 tutarlılık testi: ikisi de kendi içinde tutarlı tanımlar).
- ROE, hem DEĞER merceğinde (Damodaran FCFE modelinin `r`/`g` girdisi
  olarak DOLAYLI) hem KALİTE merceğinde (doğrudan skorlanan bileşen)
  kullanılır — `temel-analiz-cercevesi` skill madde 7 gereği bu bir
  KORELASYON NOTU olarak bileşik skor spec'inde (`spec_bilesik_skor.md`)
  işaretlenir, DEĞER merceğinin kendi ağırlığından düşülmez (rolü
  FARKLIDIR: burada girdi parametresi, orada doğrudan ölçüm).
