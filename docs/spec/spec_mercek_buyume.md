# SPEC: Büyüme Merceği (v2 Çok-Mercekli Skorlama — Mercek 3/4)

> **UYARI — ZAYIF TEMELLENMİŞ MERCEK (bkz. 00_sentez.md §5, §6 özet
> tablosu):** Bu merceğin BİRİNCİL kaynakları Fisher ("Sıradan Hisseler
> Sıradışı Karlar") ve Lynch ("Borsada Tek Başına") HENÜZ İŞLENMEDİ
> (kullanıcı kararıyla Faz 3 sonrasına ERTELENDİ). Bu spec SADECE
> Damodaran'ın DCF-büyüme METODOLOJİK çerçevesi (Ch.4, "Forecasting Cash
> Flows") ve Graham'ın büyüme hisselerine yönelik ŞÜPHECİLİK çerçevesi
> (karşı-ağırlık olarak) üzerine kuruludur — "büyüme KALİTESİ nasıl
> tanınır" (Ar-Ge verimliliği, pazar payı genişlemesi, ürün döngüsü,
> yönetim vizyonu — Fisher'ın asıl konusu) ve "büyüme KATEGORİLERİ" (hızlı
> büyüyen / yavaş büyüyen / döngüsel / dönüş hikayesi — Lynch'in asıl
> konusu) bu mercekte EKSİKTİR. **Fisher/Lynch eklendiğinde bu spec
> GENİŞLETİLMELİDİR** — bu turdaki bileşen sayısı (5) bilinçli olarak
> AZ tutulmuştur, "eksik malzemeyi doldurmak için sayı uydurma" riskinden
> kaçınmak amacıyla.

## Amaç ve kapsam

**Ölçtüğü soru:** Büyümenin gücü VE sürdürülebilirliği — şirket büyüyor
mu, bu büyüme DEĞER YARATIYOR mu (sermaye getirisi sermaye maliyetini
aşıyor mu — 03/İLKE-78), yoksa sadece BÜYÜYOR mü (kırılgan/sermaye-yakan
büyüme)?

**Geçerli şirket türleri:** `sanayi`, `abd_sanayi` BİRİNCİL. `banka`/
`sigorta`/`finansman` için sadece Hasılat/Prim Büyümesi bileşeni geçerlidir
(zaten scorer.py'de sigorta şablonunda `prim_buyumesi` olarak MEVCUT).

**Piyasalar:** BİST + NASDAQ. BİST tarafında Türkiye'nin yüksek enflasyon
gerçeği (nominal/reel ayrımı) bu merceğin EN KRİTİK tasarım kısıtıdır
(bkz. aşağı).

**Kapsam dışı:** Analist konsensüs büyüme tahminleri (forward growth) —
QuaxisLabs SADECE GERÇEKLEŞMİŞ (geçmiş) veriyle çalışır, GELECEK
projeksiyonu ÜRETMEZ (03/İLKE-455: "Değerleme modeli sayısı sorun
DEĞİLDİR... asıl sorun DOĞRU modeli seçmektir" — QuaxisLabs'ın mimarisi
zaten geriye-dönük/tanımlayıcı bir tarayıcıdır, ileriye-dönük bir
projeksiyon motoru DEĞİLDİR, bu spec bu sınırı DEĞİŞTİRMEZ).

---

## Girdiler

| Alan | Kaynak | Durum |
|---|---|---|
| Hasılat YoY büyümesi (nominal/reel) | `calculator.Ratios.revenue_growth_yoy_pct` | MEVCUT (scorer.py'nin mevcut "Büyüme" bileşeni) |
| Enflasyon oranı (reel düzeltme için) | Pipeline'dan dışarıdan verilir (`enflasyon_yoy_pct` parametresi) | MEVCUT (opsiyonel, verilmezse nominal kullanılır) |
| PEG oranı (Lynch) | `valuation.py::compute_valuation_assessment` (peg_ratio) | MEVCUT — **kanonik ev sahibi BU mercektir** (bkz. Uygulama notu) |
| Marjinal ROE | `net_income`, `equity` (çok-dönemli, MEVCUT ham veri) | **YENİ (ucuz)** — Damodaran FORMÜL-42 |
| Verimlilik Kaynaklı Ek Büyüme | `roe_annualized` YoY serisi (MEVCUT) | **YENİ (ucuz)** — Damodaran FORMÜL-43 |
| Damodaran temel büyüme (g=tutma oranı×ROE) | `valuation.py` Damodaran bloğunda DOLAYLI kullanılıyor | MEVCUT (metodoloji notu olarak, doğrudan skorlanmaz) |
| 10+ yıllık kazanç/hasılat serisi | YOK | VERİ EKSİK — `trends.py` 12 çeyrek (~3 yıl) sınırlı, kitaplar arası EN SIK tekrarlanan (6+ kez) yapısal kısıt |
| DPS/payout oranı | YOK | VERİ EKSİK — büyüme SÜRDÜRÜLEBİLİRLİĞİNİN (tutma oranı) girdisi |
| Capex/Ar-Ge (yeniden yatırım kalitesi) | YOK | VERİ EKSİK |
| Satış/Sermaye oranı | `total_assets`/`equity`/`financial_debt` (KISMEN türetilebilir) | VERİ EKSİK (tam invested capital tanımı yok) |

---

## Formüller

```
# 1. Hasılat Büyümesi (seviye+trend, MEVCUT motor, sadece mercek değişir):
reel_buyume_pct = hasilat_yoy_pct - enflasyon_yoy_pct   (enflasyon verilmişse)
buyume_skoru = seviye_trend_skoru(reel_buyume_pct, None, guclu_esik, orta_esik, tavan, taban)

# 2. PEG Oranı (MEVCUT, taşınır — BÜYÜME merceğinin kanonik ev sahipliği):
peg_ratio = own_pe / buyume_orani_pct
# Lynch kuralı: PEG<0,9 ucuz, 0,9-1,1 makul, >1,1 pahalı (valuation.py
# _PEG_CHEAP_CEILING/_PEG_EXPENSIVE_FLOOR AYNEN korunur)

# 3. Marjinal ROE (Damodaran FORMÜL-42, YENİ):
marjinal_roe_pct = (net_income_t - net_income_t-1) / equity_t-1 * 100
# "yeni yatırımların kalitesi" sinyali -- standart ROE'den DAHA DOĞRUDAN

# 4. Verimlilik Kaynaklı Ek Büyüme (Damodaran FORMÜL-43, YENİ):
verimlilik_buyume_pct = (roe_t - roe_t-1) / roe_t-1 * 100
# ROE İYİLEŞTİKÇE (yeni yatırım OLMASA BİLE) kazanç büyür -- "temel"
# büyümeden AYRI bir bileşen (İLKE-86)

# 5. Büyüme İstikrarı/Sürdürülebilirlik Çekincesi (Graham şüpheciliği,
#    ÇARPAN olarak, DOĞRUDAN skorlanmaz -- bkz. Eşikler):
if buyume_orani_pct > 25..30:  # Zweig, İLKE-72
    kart_uyarisi = "yüksek büyüme (%X) -- 5-10 yıl SÜRDÜRME istatistiksel olarak NADİR (Fortune 150'nin sadece %5,3'ü 20 yıl ≥%15 büyüttü)"
```

---

## Eşikler ve ağırlıklar

**BÜYÜME merceği iç ağırlıkları (`sanayi`/`abd_sanayi`, toplam %100):**

| Bileşen | Ağırlık | Eşikler | Gerekçe / kaynak |
|---|---|---|---|
| Hasılat Büyümesi (reel, seviye+trend) | %55 | Mevcut scorer.py `buyume` cfg AYNEN taşınır (sanayi: güçlü≥15/orta≥0/tavan30/taban-20; abd_sanayi: güçlü≥10/orta≥0/tavan25/taban-15) | Kalibre edilmiş, canlı doğrulanmış çekirdek KORUNUR (persona kural 8). ÇOĞUNLUK ağırlığı BU bileşende toplanır çünkü Fisher/Lynch eksikliği nedeniyle MERCEĞİN geri kalanı ZAYIF temellenmiştir — sağlam olan TEK bileşene fazla ağırlık vermek, zayıf-temellenmiş bileşenlere YAPAY otorite VERMEKTEN daha DÜRÜST bir tasarım. |
| PEG Oranı (Lynch, büyümeye göre değerleme) | %25 | Mevcut valuation.py bantları AYNEN (PEG<0,9 ucuz/0,9-1,1 makul/>1,1 pahalı) | Lynch'in GARP (Growth At a Reasonable Price) felsefesinin ÖZÜ — büyümeyi FİYATLA BİRLİKTE değerlendirir (03/İLKE-159,175: PEG'in doğrusallık varsayımı İHLAL edilir, U-şekli %24-26 büyümede diplenir — bu NÜANS kart açıklamasında BELİRTİLİR, bkz. Kenar Durumlar). **BİLİNEN TANIM SAPMASI:** büyüme bazı revenue (net kâr/HBK OLMALI, 03/FORMÜL-74) — düzeltme çok-yıllı net kâr serisi GEREKTİRİR, şimdilik AÇIKÇA belgelenir. |
| Marjinal ROE + Verimlilik Kaynaklı Büyüme | %20 | Marjinal ROE: güçlü≥standart ROE'nin ÜSTÜNDE, zayıf≥standart ROE'nin ALTINDA (kaba, standart ROE'ye GÖRELİ bir kıyas — mutlak eşik henüz kalibre edilmedi). Verimlilik büyüme: pozitifse EK puan, negatifse (ROE kötüleşiyor) "büyüme miktarı yüksek olsa bile KALİTESİ sorgulanmalı" notu. | 03/İLKE-85,86 (Damodaran) — Goldman Sachs 2005 örneği: standart ROE %18,49 iken marjinal ROE ÇOK DAHA DÜŞÜK, "yeni yatırımların GETİRİSİNİN düştüğüne dair UYARI". Bu, Fisher'ın "büyüme kalitesi" sorusuna Damodaran'ın SAYISAL yaklaşımıdır — Fisher'ın kendisi eklenene kadar GEÇİCİ vekil. |

**Toplam: %100.**

**Büyüme İstikrarı/Sürdürülebilirlik Çekincesi (DOĞRUDAN AĞIRLIK TAŞIMAZ,
kart notu/uyarı olarak eklenir):**

| Eşik | Yorum | Kaynak |
|---|---|---|
| Hasılat büyümesi >%25-30 (sürekli) | "Sürdürme istatistiksel olarak NADİR" uyarısı | 01/İLKE-72 (Zweig): Fortune 500'ün en büyük 150'sinden sadece 8'i (2 tam onyıl ≥%15) |
| Büyük şirket + çok yüksek büyüme birlikte | "Büyük şirketler ORTALAMADAN HIZLI büyümez" — şüpheyle karşılanmalı | 01/İLKE-73: 1951-1998, en büyük %20 dilim %9,3 (piyasa ortalaması %9,7'den DÜŞÜK) |
| F/K>25-30× + yüksek büyüme iddiası | Tehlikeli bölge, DEĞER merceğiyle ÇAPRAZ okunmalı | 01/İLKE-72, BAYRAK-16 (>80-120× + "hızlanacağız" iddiası — Nortel/Cisco 2000) |

---

## Sektör ayarlaması

1. **Enflasyon rejimi (BİST-özel):** Reel büyüme kullanımı (mevcut
   `enflasyon_yoy_pct` parametresi) BİREBİR korunur — bu, "sahte büyüme"
   görüntüsünü (TL değer kaybından kaynaklanan) engelleyen ZATEN VAR OLAN
   bir TMS-29 farkındalığıdır (SCORING_METHODOLOGY.md'de belgeli).
2. **Sektöre göreli büyüme konumu (n≥5):** Ham büyüme oranının YANINDA,
   `(ust_sektor, sirket_turu)` grubu içinde n≥5 varsa "bu büyüme oranı
   sektör medyanının ÜSTÜNDE/ALTINDA" bağlam notu EKLENEBİLİR — Damodaran'ın
   "büyüklük+pazar payı" ilkesi (03/İLKE-77: küçük firma+büyük toplam
   pazar=uzun sürdürebilir büyüme potansiyeli) sektör bağlamıyla daha
   ANLAMLI hale gelir. Mutlak eşik (yukarıdaki tablo) HER ZAMAN birincil
   kalır — "sektörün en hızlı büyüyeni" bile mutlak taban altındaysa
   (ör. sektör geneli daralıyorsa) yüksek BÜYÜME puanı ALAMAZ.
3. **Banka/sigorta:** Hasılat Büyümesi bileşeni Prim Büyümesi (sigorta,
   zaten `scorer.CONFIG["sigorta"]["prim_buyumesi"]` mevcut) veya kredi/
   mevduat büyümesi (banka, VERİ EKSİK) ile DEĞİŞTİRİLİR; diğer 2 bileşen
   (PEG, Marjinal ROE) bu şablonlarda da KAVRAMSAL OLARAK geçerlidir (ROE
   zaten banka CONFIG'inde MEVCUT).

---

## Kenar durumlar

- **Negatif/sıfır büyüme:** Mevcut taban (%-20 sanayi, %-15 abd_sanayi)
  KORUNUR — bu seviyenin ALTINDA skor 0'a SABİTLENİR (mevcut davranış).
- **Negatif kazanç nedeniyle PEG hesaplanamıyor:** `own_pe<=0` veya
  `buyume_orani_pct<=0` ise PEG bileşeni `None`, ağırlığı diğer ikisine
  yeniden dağıtılır (mevcut `valuation.py` davranışı KORUNUR).
- **PEG'in U-şekli (03/İLKE-175, BAYRAK-23):** Çok DÜŞÜK büyümeli (%0'a
  yakın) şirketler PEG'de SİSTEMATİK OLARAK "pahalı" görünür (gerçek
  ilişki U-şeklidir, ~%24-26 büyümede DİPLENİR, sonra TEKRAR yükselir) —
  bu NÜANS özellikle DÜŞÜK büyümeli (ör. olgun BIST holding) şirketlerde
  kart açıklamasında "PEG düşük büyümeli şirketlerde YAPISAL OLARAK
  yüksek çıkar, bu tek başına 'pahalı' anlamına GELMEZ" notuyla
  YUMUŞATILIR (skor DEĞİŞTİRİLMEZ, sadece YORUM eklenir).
- **Marjinal ROE'nin volatilitesi:** Tek dönemlik `Δnet_kâr/Δönceki-yıl-
  özkaynak` küçük özkaynak değişimlerinde AŞIRI OYNAK olabilir (payda
  küçükse oran patlayabilir) — bu bileşen bir "en az 4 çeyreklik TTM
  bazlı" pencereyle hesaplanır (Piotroski/scorer.py'nin geri kalanıyla
  AYNI TTM ilkesi), tek çeyrek kullanılmaz.
- **Halka arz sonrası kısa geçmiş:** YoY büyüme (Hasılat) ilk 4 çeyrekte
  `None` — bileşen ATLANIR; PEG de `own_pe` yeni şirkette genelde MEVCUT
  olduğundan çalışabilir (kazanç varsa).
- **Fisher/Lynch eklenene kadar geçerli sınırlama:** "Büyüme KATEGORİSİ"
  (Lynch'in hızlı-büyüyen/yavaş-büyüyen/döngüsel/dönüş-hikayesi/varlık-
  oyunu sınıflandırması) HİÇ UYGULANMAZ — TÜM şirketler AYNI mutlak
  eşiklerle değerlendirilir, bu YAPISAL bir basitleştirmedir (Lynch'in
  kendi çerçevesi tam da bunun YANLIŞ olduğunu söyler — "yavaş büyüyen"
  bir şirketten %25 büyüme BEKLEMEK gerçekçi değildir). Bu spec Fisher/
  Lynch eklenene kadar bu basitleştirmeyi BİLEREK kabul eder.

---

## Test senaryoları

1. **Yüksek enflasyon döneminde bir BIST sanayi şirketi (nominal +%60
   hasılat büyümesi, enflasyon %55):** Reel büyüme ≈%5 → "orta" bandı,
   NOMİNAL rakamla (+%60) yanıltıcı biçimde "güçlü" GÖRÜNMEZ — bu test
   mevcut enflasyon düzeltme mantığının BÜYÜME merceğinde de DOĞRU
   çalıştığını doğrular.
2. **PEG U-şekli testi — düşük büyümeli olgun bir BIST holding (%3
   büyüme, F/K=8):** PEG=8/3=2,67 → "pahalı" bandı, AMA kart notu "düşük
   büyümede PEG YAPISAL OLARAK yüksek çıkar" UYARISINI TAŞIMALI.
3. **Goldman Sachs tipi finans şirketi (yüksek standart ROE ama düşen
   marjinal ROE):** Standart ROE bileşeni (KALİTE merceğinde) YÜKSEK,
   ama BU mercekte Marjinal ROE/Verimlilik bileşeni DÜŞÜK/NEGATİF →
   BÜYÜME toplamı MODERE edilir, "kâr büyük ama yeni yatırımların
   getirisi düşüyor" mesajı ÜRETİLMELİDİR.
4. **F/K=90, büyüme %8 iddialı bir NASDAQ şirketi:** Büyüme İstikrarı
   çekincesi TETİKLENMEZ (büyüme oranı kendisi %25 eşiğinin ALTINDA),
   AMA DEĞER merceğiyle çapraz okunduğunda F/K aşırılığı zaten oradaki
   Mutlak Ucuzluk bileşeninde YAKALANIR (mercekler arası ÇAPRAZ tutarlılık
   testi, çift skorlama DEĞİL, iki farklı SORUYA iki farklı CEVAP).

---

## Uygulama notu (izlenebilirlik ve çift-sayma)

- **PEG'in kanonik evi:** `temel-analiz-cercevesi` skill'in kendi örnek
  tablosunda PEG açıkça BÜYÜME merceği altında listelenmiştir ("PEG,
  Lynch kategorisine göre beklenti kalibrasyonu") — bu spec bu kararı
  TAKİP EDER. `spec_mercek_deger.md`'de PEG'e sadece ÇAPRAZ REFERANS
  verilir (DEĞER merceğinin kendi ağırlığına KATILMAZ), çünkü PEG zaten
  bir DEĞER girdisi (F/K) İÇERİR — iki mercekte AYNI ANDA tam ağırlıkla
  sayılırsa ÇİFT SAYMA olurdu.
- **Marjinal ROE/Verimlilik Büyüme'nin kanonik evi:** `spec_mercek_
  kalite.md`'de bu iki bileşen SADECE veri kaynağı olarak listelenmiş,
  ağırlık TAŞIMAMASI AÇIKÇA belirtilmiştir — kanonik ev BURASIDIR (BÜYÜME),
  çünkü ölçtükleri şey "yeni yatırımların büyümeye katkısı"dır, mevcut
  KALİTE'nin ROE bileşeni ise "GENEL sermaye verimliliği"dir — FARKLI
  sorular, ama AYNI ham veriden (ROE serisi) türedikleri için TEK
  mercekte tutulmaları çift-sayma riskini SIFIRLAR.
- **Damodaran temel büyüme (g=tutma oranı×ROE):** `valuation.py`'nin
  Damodaran FCFE modelinde DOLAYLI olarak kullanılan bu özdeşlik
  (`reinvestment_rate=g/ROE`) DEĞER merceğinde YAŞAR (Damodaran fiyat
  hesaplama bağlamında) — BU mercekte SADECE metodolojik referans olarak
  anılır, AYRI bir sayısal bileşen OLUŞTURULMAZ (aynı formülün iki
  mercekte AYRI ağırlıklarla sayılması ÖNLENİR).
