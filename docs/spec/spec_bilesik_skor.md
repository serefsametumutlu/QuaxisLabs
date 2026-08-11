# SPEC: Bileşik Skor (v2 Çok-Mercekli Skorlama — 4 Merceğin Birleşimi)

## Amaç ve kapsam

**Ölçtüğü soru:** Bu spec YENİ bir "tek doğru sayı" ÜRETMEZ — dört
merceğin (Değer/Kalite/Büyüme/Güvenlik, bkz. `spec_mercek_deger.md`,
`spec_mercek_kalite.md`, `spec_mercek_buyume.md`, `spec_mercek_guvenlik.
md`) SONUÇLARINI ŞEFFAF, ağırlıklı bir ortalamayla TEK bir Bileşik Skor'a
İNDİRGEME + kartta MERCEKLERİ AYRI AYRI gösterme KURALLARINI tanımlar.
`temel-analiz-cercevesi` skill'in temel tezi ("kitaplar çelişir, çelişki
ÇÖZÜLMEZ, ayrı mercek olur; bileşik skor merceklerin şeffaf ağırlıklı
ortalamasıdır") burada UYGULANIR.

**Geçerli şirket türleri:** `sanayi`, `abd_sanayi`, `banka`, `sigorta`,
`finansman` — HER şablonun kendi mercek-içi bileşen kümesi farklıdır
(bkz. ilgili mercek spec'leri), ama 4-mercekli ÜST YAPI TÜM şablonlarda
AYNIDIR.

**Piyasalar:** BİST + NASDAQ.

**Geriye uyumluluk (KRİTİK, persona kural 8):** Mevcut 7-bileşenli Radar
Skoru (`scorer.score_industrial()` vb.) **DEĞİŞTİRİLMEZ, ÇÖPE ATILMAZ.**
v2 mimarisi bu 7 bileşeni 4 merceğe DAĞITIR (bkz. aşağıdaki eşleme
tablosu) — v1'in ÜRETTİĞİ `ScoreResult` (tek skor, tek rozet) BAĞIMSIZ
bir fonksiyon olarak ÇALIŞMAYA DEVAM EDER; v2 Bileşik Skor AYRI, YENİ bir
fonksiyon/veri yapısı olarak EKLENİR ve pipeline'da bir BAYRAKLA
(`use_multi_lens_scoring` gibi) AÇILIR — geçiş döneminde kartta İKİSİ
BİR ARADA sunulabilir (v1 rozeti + v2 4-mercek profili).

---

## Girdiler

| Girdi | Kaynak |
|---|---|
| Değer Mercek Sonucu | `spec_mercek_deger.md`'de tanımlı hesaplama |
| Kalite Mercek Sonucu | `spec_mercek_kalite.md`'de tanımlı hesaplama |
| Büyüme Mercek Sonucu | `spec_mercek_buyume.md`'de tanımlı hesaplama |
| Güvenlik Mercek Sonucu | `spec_mercek_guvenlik.md`'de tanımlı hesaplama |
| Şirket türü (`sirket_turu`) | `spec_sektor_evren.md` — hangi CONFIG şablonunun kullanılacağını belirler |
| Üst-sektör (`ust_sektor`) | `spec_sektor_evren.md` — mercek-içi n≥5 sektöre-göreli bileşenler için |

---

## Formüller

```
# 1. Her mercek KENDİ İÇİNDE zaten 0-10 skalaya normalize edilmiş
#    (bkz. ilgili mercek spec'leri, scorer.py'nin _agirlik_dagit_ve_hesapla
#    mekanizmasıyla AYNI ilke -- mercek İÇİ eksik bileşenler ORANTISAL
#    yeniden dağıtılır, mercek SEVİYESİNDE 0-10 skor + veri_yeterliligi
#    üretir).

bilesik_skor = Σ (mercek_skoru_i * mercek_agirlik_i) / Σ (mercek_agirlik_i, sadece veri_yeterli merceklerde)

# 2. Mercek-seviyesi "veri yeterliliği" kontrolü (scorer.py'nin mevcut
#    min_veri_agirlik_yuzdesi=%50 ilkesinin MERCEK SEVİYESİNE taşınmış hali):
if mercek_i.data_coverage_pct < 50:
    mercek_i.dahil_edilmez_bilesik_skora  # ağırlığı diğer merceklere yeniden dağıtılır

# 3. TÜM mercekler yetersiz veriliyse (nadiren):
if hicbir_mercek_yeterli_degil:
    bilesik_rozet = "YETERSİZ VERİ"  # mevcut YETERSIZ_VERI_ROZETI ile AYNI ilke
```

---

## Eşikler ve ağırlıklar

**4 Mercek Ağırlıkları (`sanayi`/`abd_sanayi` varsayılan, toplam %100):**

| Mercek | Ağırlık | Gerekçe |
|---|---|---|
| Değer | %30 | Mevcut Radar Skoru'nda Değerleme bileşeni zaten %17 tek başınaydı; v2'de Değer merceği İÇİNDE 7 alt-bileşene GENİŞLEDİĞİ (Graham Sayısı, Kazanç Getirisi, Greenblatt, Carlisle, NCAV, sektöre-göreli konum EKLENDİ) için üst-seviye ağırlığı da BÜYÜDÜ — kitaplar arası EN GÜÇLÜ temellenmiş mercek (00_sentez.md §6: Graham+Damodaran+kısmen Buffett). |
| Kalite | %30 | Mevcut Radar Skoru'nun EN AĞIR TEK bileşeni (Nakit Üretimi %21) BU merceğin çekirdeğidir; Buffett kitabının NEREDEYSE TAMAMI (İLKE-01-51) bu mercekte yaşar — DEĞER ile EŞİT ağırlık, çünkü 00_sentez.md §2.5 (Buffett'ın "dayanıklı avantajlı şirketler NADİREN ucuz olur" bulgusu) İKİ merceğin BİRBİRİNİ EZMEMESİ gerektiğini AÇIKÇA gösteriyor — biri diğerinden SİSTEMATİK olarak daha ağır olursa, o mercek TEK BAŞINA "doğru" cevap gibi SUNULMUŞ olur, ki bu tam da kitaplar arası çelişkinin İNKÂRIDIR. |
| Güvenlik | %25 | Piotroski + Kaldıraç + Bilanço Kalitesi ZATEN mevcut Radar Skoru'nda ~%21 (Kaldıraç %17 + Bilanço Kalitesi %4) idi; Merton köprüsü ve Toplam Yükümlülük/Özkaynak EKLENMESİYLE biraz YÜKSELTİLDİ — ama Schilit eksikliği nedeniyle (00_sentez.md §6: "ORTA-ZAYIF temellenmiş") DEĞER/KALİTE'NİN GERİSİNDE tutuldu, Schilit eklendiğinde bu ağırlık YENİDEN değerlendirilmelidir. |
| Büyüme | %15 | EN DÜŞÜK ağırlık — 00_sentez.md §6: "ÇOK ZAYIF temellenmiş (Fisher/Lynch YOK)" AÇIKÇA belirtiyor; mevcut Radar Skoru'nda Büyüme bileşeni %13 idi, v2'de Fisher/Lynch eksikliği nedeniyle YÜKSELTİLMEDİ (aksine mercek İÇİ malzeme zayıf olduğu için üst-seviye ağırlık da TEMKİNLİ tutuldu — zayıf temelli bir mercek'e YÜKSEK ağırlık vermek "sahte kesinlik" olurdu, sektor-siniflandirma skill'in "sahte kesinlik yasak" ilkesiyle AYNI mantık burada AĞIRLIK seçimine de uygulanır). |

**Toplam: %100.** Fisher/Lynch/Schilit eklendiğinde bu ağırlıklar YENİDEN
GÖZDEN GEÇİRİLMELİDİR (Büyüme ve Güvenlik'in ağırlığı muhtemelen
YÜKSELECEK, bu spec'in "sonraki revizyon" notu olarak işaretlenir).

**Rozet dili (mevcut gelenek AYNEN korunur, HEM bileşik skora HEM her
mercek KENDİ İÇİNDE):**

| Skor | Rozet | Kaynak |
|---|---|---|
| ≥8 | SAĞLAM | Mevcut `scorer.CONFIG["rozet_esikleri"]`, DEĞİŞTİRİLMEZ |
| ≥6 | DENGELİ | " |
| ≥4 | KARIŞIK | " |
| <4 | RİSKLİ | " |
| (veri kapsamı<%50) | YETERSİZ VERİ | Mevcut `YETERSIZ_VERI_ROZETI`, DEĞİŞTİRİLMEZ |

**Kart sunumu (persona/skill zorunluluğu):** "Değer: 8,2 · Kalite: 4,1 ·
Büyüme: 6,0 · Güvenlik: 7,5 → Bileşik: 6,4 DENGELİ" formatı — TEK bir
sayı DEĞİL, 4 mercek + bileşik BİRLİKTE gösterilir (`temel-analiz-
cercevesi` skill madde 8: "kullanıcıya tek skor değil profil gösterilir").

---

## Sektör ayarlaması

Bu spec'in KENDİSİ sektör-göreli bir hesaplama İÇERMEZ (o iş mercek-içi
bileşenlerde yapılır, bkz. `spec_mercek_deger.md`/`spec_mercek_kalite.md`
Sektör Ayarlaması bölümleri). Burada SADECE şu KURAL geçerlidir: bir
mercek İÇİNDE n<5 nedeniyle bir SEKTÖRE-GÖRELİ ALT-bileşen atlanmışsa, bu
durum mercek SEVİYESİNDE (`data_coverage_pct` üzerinden) ZATEN yansır —
Bileşik Skor katmanı AYRICA bir n≥5 kontrolü YAPMAZ (çift kontrol
GEREKSİZDİR, mercek katmanı bunu ZATEN garanti eder).

---

## Kenar durumlar

- **Bir mercek TAMAMEN veri eksik (örn. Büyüme merceği, halka arz sonrası
  ilk çeyrek):** O merceğin ağırlığı (%15) diğer 3 merceğe ORANTISAL
  dağıtılır (Değer %30→%35,3, Kalite %30→%35,3, Güvenlik %25→%29,4 —
  mevcut `_agirlik_dagit_ve_hesapla` ilkesinin MEVCUT MATEMATİĞİ AYNEN
  4-mercek seviyesine TAŞINIR).
- **Banka/sigorta/finansman şirketleri:** Değer/Kalite/Güvenlik merceklerinin
  İÇ bileşen kümesi KÜÇÜLÜR (bkz. ilgili spec'lerin "Sektör ayarlaması"
  bölümleri) ama 4-mercek ÜST ağırlıkları AYNI KALIR — Büyüme merceği
  sigortada Prim Büyümesine, bankada VERİ EKSİK bir yer tutucuya
  İNDİRGENİR (banka için bu mercek şimdilik SIK SIK "YETERSİZ VERİ"
  döner, ağırlığı diğer 3'e dağıtılır — bu KABUL EDİLEBİLİR bir sonuçtur,
  UYDURMA yapılmaz).
- **Çift-sayma kayıt defteri (BU spec'in MERKEZİ sorumluluğu):** Aşağıdaki
  tablo, dört mercek spec'inde işaretlenen TÜM çapraz-mercek ham veri
  kullanımlarını TEK yerde toplar (izlenebilirlik):

| Ham veri | Mercek A (doğrudan ağırlık) | Mercek B (dolaylı/girdi) | Neden çift sayma DEĞİL |
|---|---|---|---|
| ROE | Kalite (%20 iç ağırlık) | Değer (Damodaran `r`/`g` girdisi), Büyüme (Marjinal ROE/Verimlilik büyüme, %20 iç ağırlık — AMA türetilmiş, FARKLI oranlar) | Kalite'de SEVİYE, Büyüme'de DEĞİŞİM/marjinal etki, Değer'de sadece PARAMETRE — 3 FARKLI SORU |
| Nakit pozisyonu (`cash`) | Güvenlik (Kaldıraç bileşeninin girdisi — net borç negatife dönerse otomatik 10) | Kalite (Nakit Kâr Kalitesi, OCF/Net Kâr — DOLAYLI, farklı oran) | Güvenlik'te KRİZ DAYANIKLILIĞI (Buffett), diğerinde SERMAYE VERİMLİLİĞİ (Graham/Zweig) — 00_sentez.md §2.7'nin ÇÖZÜMÜ |
| Cari Oran | Güvenlik (Bilanço Kalitesi, SEVİYE) | Güvenlik (Piotroski kriter #6, YÖN) | AYNI mercek İÇİNDE, farklı sorular, TEK ağırlığa KATILIYORLAR |
| F/K (own_pe) | Değer (Mutlak Ucuzluk, Graham Çarpanı) | Büyüme (PEG'in payı) | Değer'de MUTLAK ucuzluk sinyali, Büyüme'de büyümeYE-GÖRE ucuzluk sinyali — PEG'in kanonik evi Büyüme'dir, Değer'de SADECE çapraz referans (ağırlık TAŞIMAZ) |
| EBIT/Firma Değeri (Greenblatt) | Değer (Kazanç Getirisi, %10 iç ağırlık) | Kalite (ROC, %10 iç ağırlık — FARKLI PAYDA: Yatırılan Sermaye) | Greenblatt'ın KENDİ metodolojisi zaten iki AYRI ölçüm (ucuzluk + verimlilik) BİRLEŞTİRİR — v2'de bu doğal ayrım İKİ merceğe YANSITILIR |

- **Fisher/Lynch/Schilit eklenene kadar geçerli genel sınırlama:** Büyüme
  ve Güvenlik mercekleri KASITLI olarak "eksik ama dürüst" tutulmuştur —
  Bileşik Skor bu iki merceğin EKSİKLİĞİNİ gizli bir varsayımla
  TAMAMLAMAZ (ör. Güvenlik'in Schilit boşluğunu KALİTE'nin nitel kazanç-
  kalitesi göstergeleriyle "doldurma" GİBİ bir kısayol KULLANILMAZ) —
  her mercek KENDİ mevcut malzemesiyle SINIRLI kalır, kart bu sınırı
  AÇIKÇA (mercek spec'lerindeki UYARI kutularıyla TUTARLI) gösterir.

---

## Test senaryoları

1. **Dört mercek de veri yeterli, tipik BIST sanayi şirketi (THYAO):**
   Değer=7,x, Kalite=7,x, Büyüme=5,x (enflasyon düzeltmeli), Güvenlik=5,x
   (sektörel kaldıraç) → Bileşik ≈6,x DENGELİ; kart 4 mercek + toplam
   AYRI AYRI gösterir.
2. **Buffett-tipi "dayanıklı avantajlı ama Graham'a göre pahalı" senaryo
   (varsayımsal, yüksek F/K ama çok güçlü marj/ROE):** Değer DÜŞÜK
   (~4-5), Kalite YÜKSEK (~8-9) → Bileşik ORTA (~6) ama kart AÇIKÇA "Değer
   merceği düşük (pahalı), Kalite merceği yüksek (dayanıklı avantaj) —
   bu, Buffett'ın Graham'dan KÖKTEN FARKLI felsefesinin (00_sentez.md
   §2.5) SOMUT bir örneğidir" diye YORUMLANABİLMELİDİR (metin/gerekçe
   katmanında, Gemini yorum katmanına BESLENECEK ham bulgu olarak).
3. **Banka şirketi (AKBNK):** Büyüme merceği "YETERSİZ VERİ" (prim/kredi
   büyümesi banka için henüz YOK) → ağırlığı Değer/Kalite/Güvenlik'e
   dağıtılır, Bileşik SKORU YİNE de üretilir, 3 mercek gösterilir + "Bu
   şirket türünde Büyüme merceği için yeterli veri yok" notu.
4. **Halka arzın 1. çeyreği:** Büyüme (YoY veri yok) VE Piotroski'nin
   çoğu kriteri (önceki dönem karşılaştırması gerektirir) `None` →
   Güvenlik merceği KISMİ (sadece Kaldıraç/Bilanço Kalitesi çalışır),
   Büyüme TAMAMEN "YETERSİZ VERİ" — Bileşik skor SADECE Değer+Kalite (ve
   kısmi Güvenlik) üzerinden hesaplanır, kart bunu AÇIKÇA belirtir.
5. **Tüm mercekler <%50 veri kapsamlı (aşırı uç durum, ör. çok az veri
   çekilebilen yeni bir NASDAQ tickerı):** Bileşik rozet "YETERSİZ VERİ"
   döner — mevcut `ASTS/AST SpaceMobile` canlı hatasının (scorer.py CONFIG
   yorumunda belgeli) 4-mercek seviyesindeki KARŞILIĞI, AYNI disiplinle
   (Kural 3: yanlış rakamdan iyidir) önlenmiş olur.

---

## Uygulama notu (geçiş stratejisi)

1. **Faz sıralaması:** Önce her mercek KENDİ modülünde (`src/analysis/
   lens_deger.py`, `lens_kalite.py`, `lens_buyume.py`, `lens_guvenlik.py`
   — İSİMLENDİRME önerisi, kodlama fazının kararı) BAĞIMSIZ test
   edilebilir olmalı; Bileşik Skor katmanı bunları SADECE BİRLEŞTİRİR,
   kendi hesaplama mantığı TAŞIMAZ (ince bir orkestrasyon katmanı).
2. **v1 ile v2'nin BİRLİKTE yaşaması:** `scorer.score_industrial()` (v1)
   ÇAĞRILMAYA DEVAM EDER — mevcut testler/kartlar KIRILMAZ. v2 fonksiyonu
   AYRI bir giriş noktası (`score_industrial_v2()` gibi) olarak eklenir,
   pipeline.py bir FEATURE FLAG ile hangisinin (veya İKİSİNİN BİRLİKTE)
   kullanılacağına karar verir.
3. **Kod tekrarını önleme:** `_seviye_trend_skoru`, `_lerp_score`,
   `_asymptote_to`, `_agirlik_dagit_ve_hesapla` gibi MEVCUT yardımcı
   fonksiyonlar (scorer.py) 4 mercek modülü TARAFINDAN DA kullanılır
   (import edilir, KOPYALANMAZ) — bu, kodlama fazının UYMASI gereken bir
   MİMARİ kısıttır, bu spec seviyesinde İŞARETLENİR.
