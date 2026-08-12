# SPEC: Yeni Veri Kalemlerinin Mercek Ağırlıklarına Bağlanması (V-01…V-13 İkinci Tur)

## Amaç ve kapsam

**Ölçtüğü soru:** Bu bir yeni-formül spec'i DEĞİLDİR — `docs/spec/spec_veri_
tamlik_yol_haritasi.md`'nin "İlk Dalga + GRUP 2" turunda (2026-08-12)
`calculator.Ratios`'a EKLENEN ama HİÇBİR mercek ağırlık tablosuna
BAĞLANMAMIŞ 13 veri kaleminin (V-04/hazine-hissesi-ROE HARİÇ, o zaten
`spec_mercek_kalite.md`'ye bağlıydı — bkz. o spec'in Girdiler/Kenar Durumlar
bölümü) her biri için **(a) hangi mercek(ler)e ait olduğu, (b) skorlanan bir
bileşen mi yoksa kart notu mu olacağı, (c) skorlanıyorsa hangi ağırlıkla ve
hangi mevcut bileşen(ler)den bu ağırlığın çekileceği** kararını verir.

Kod-geliştirici bu turda BİLEREK ağırlık İCAT ETMEDİ (kendi devir notu,
`spec_veri_tamlik_yol_haritasi.md` "Spec-eki" bölümü) — bu spec o boşluğu
kapatır. **Bu dosya `spec_mercek_{kalite,buyume,guvenlik}.md`'yi DOĞRUDAN
DEĞİŞTİRMEZ** — aşağıdaki her bölüm bir "TALİMAT" kutusu içerir, kod-
geliştirici (veya bir sonraki spec-yazım turu) bu talimatları ilgili spec
dosyalarının "Eşikler ve ağırlıklar" tablolarına AYNEN işler. `spec_mercek_
deger.md` bu turda **hiçbir talimat almaz** (gerekçe aşağıda, §4).

**Geçerli şirket türleri / piyasalar:** `sanayi`/`abd_sanayi` (yeni
bileşenlerin TÜMÜ bu şablonlarda yaşıyor — banka/sigorta/finansman zaten
kendi ayrı alt-kümeleriyle çalışıyor, bu turda DOKUNULMUYOR).

**Kaynaklar:** `src/analysis/calculator.py` (Ratios dataclass, satır 202-261
ve 792-831 — CANLI kod okundu), `src/analysis/liquidity.py` (V-05 köprüsü,
CANLI okundu), `src/fetchers/isyatirim.py`/`pipeline.py` (V-07 pretax_profit
ham alan durumu, CANLI okundu), `bilgi-bankasi/{01,02,03}_*.md` (İLKE-177/
178/180/181, FORMÜL-02/03/05/19/28, Tablo 2.4 — CANLI okundu, tam metin
alıntılandı), `docs/spec/spec_mercek_{kalite,buyume,guvenlik,deger}.md`
(mevcut ağırlık tabloları — CANLI okundu, birebir aktarıldı).

---

## Özet tablo (13 kalem → karar)

| # | Kalem | Ratios alanı | Mercek | Karar | Ağırlık |
|---|---|---|---|---|---|
| V-04 | Hazine Hissesi Düz. ROE | (zaten bağlı) | Kalite | ZATEN SKORLANIYOR | — (kapsam dışı, bu spec dokunmuyor) |
| V-01 | SG&A/Brüt Kâr | `sga_to_gross_profit_pct` | Kalite | **SKORLA** | %5 |
| V-02 | Ar-Ge/Brüt Kâr | `rd_to_gross_profit_pct` | Kalite | **SKORLA** (gerilim notlu) | %3 |
| V-08 | Faiz Gideri/Faaliyet Kârı | `interest_expense_to_operating_profit_pct` | Kalite | **SKORLA** | %7 |
| V-08 | Faiz Karşılama Oranı | (V-08'in TERS çevrilmiş hali) | Güvenlik | **SKORLA** | %10 |
| V-09/V-10 | Capex/Net Kâr | `capex_to_net_income_pct` | Büyüme | **SKORLA** | %8 |
| V-11/V-12 | Payout Oranı | `payout_ratio_pct` | Büyüme | **SKORLA** | %5 |
| V-03 | Temettü Verimi/DPS | `ttm_dividend_per_share` | Değer | KART NOTU | — |
| V-07 | Vergi Öncesi Kâr → Efektif Vergi Oranı | `pretax_profit`/`tax_provision` (henüz oran bile YOK) | Kalite | KART NOTU | — |
| V-05 | Devir Hızı/Amihud İlliklidite | `liquidity.py` (Ratios'ta bile değil) | Güvenlik | KART NOTU (kalibrasyon bekliyor) | — |
| V-12 | Ödenen Temettü+Finansman Faal. | `ttm_share_buyback`/`ttm_net_financing_debt_change` | Güvenlik | KART NOTU | — |
| V-13 | Opsiyon/Warrant Seyreltme | `diluted_dilution_pct` | Değer | KART NOTU | — |

**Sayım notu:** Kullanıcının belirttiği "13 kalem" = V-04 (zaten bağlı, 1) +
yukarıdaki 12 satır (bazıları BİRLEŞTİRİLMİŞ V-numaraları taşıyor çünkü aynı
ham veri iki piyasada/iki mercekte yaşıyor — `spec_veri_tamlik_yol_
haritasi.md`'nin kendi "Çift-sayma/tekrar kontrolü notu" ile TUTARLI).
**6 kalem SKORLANDI (4 mercek ağırlık tablosundan 3'ü değişti — Değer
DEĞİŞMEDİ), 6 kalem KART NOTU olarak kaldı** (gerekçe aşağıda, her biri
kendi bölümünde).

---

## §1 — KALİTE merceği (`spec_mercek_kalite.md`'ye işlenecek)

### TALİMAT — güncellenmiş ağırlık tablosu

| Bileşen | Eski ağırlık | Yeni ağırlık | Değişim |
|---|---|---|---|
| Nakit Üretimi (FAVÖK marjı) | %25 | **%20** | -5 |
| Özkaynak Kârlılığı (ROE) | %20 | **%18** | -2 |
| Kârlılık (Net Marj) | %15 | **%13** | -2 |
| Brüt Kâr Marjı | %15 | **%13** | -2 |
| Greenblatt ROC | %10 | **%8** | -2 |
| ROA | %5 | **%4** | -1 |
| Nakit Kâr Kalitesi (OCF/Net Kâr) | %10 | **%9** | -1 |
| **SG&A/Brüt Kâr (YENİ)** | — | **%5** | +5 |
| **Ar-Ge/Brüt Kâr (YENİ)** | — | **%3** | +3 |
| **Faiz Gideri/Faaliyet Kârı (YENİ)** | — | **%7** | +7 |
| **Toplam** | %100 | **%100** | 0 |

### Gerekçe — neden bu 3 kalem, neden bu shave dağılımı

Bu üç kalem, Buffett kitabının kendi metninde "gelir tablosunun HER kalemini
incele" (İLKE-01) felsefesinin **somut, sayısal karşılığıdır** — kitap zaten
bu üç oran için HAZIR eşik tablosu üretmişti (`spec_mercek_kalite.md`
Eşikler bölümü, satır 138-142) ve o tablo şimdiye dek "VERİ EKSİK" notuyla
0-ağırlıklı bekliyordu; NASDAQ tarafında veri artık MEVCUT (`sec_edgar.py`
standart `us-gaap:*` tag'leri), bu yüzden tam da spec'in kendi öngördüğü
"veri gelince YÜKSELTİLİR" adımı budur.

**Shave kaynağı seçimi bilinçli:** FAVÖK marjından EN BÜYÜK payı (-5) kestik
çünkü bu bileşenin KENDİSİ zaten `spec_mercek_kalite.md`'nin kendi "DÜZELTME
(kullanıcı denetimi)" notunda Buffett'ın FAVÖK/EBITDA kullanımını AÇIKÇA
ELEŞTİRDİĞİ (02/İLKE-06) belgeli — kitabın kendi yazarının şüpheyle
baktığı bir metriğin payını, kitabın hiç çekişmesiz/doğrudan önerdiği üç
yeni metriğe (SG&A/Ar-Ge/Faiz Gideri, hiçbiri kitap içi çelişki taşımıyor)
kaydırmak "kitap-sadakati" argümanını GÜÇLENDİRİR. Diğer 6 bileşenden KÜÇÜK
(1-2 puanlık) eşit-benzeri kesintiler yapıldı — hiçbiri tek başına
"öze" dokunmayacak kadar küçük.

**Kalem-içi ağırlık sıralaması (Faiz Gideri > SG&A > Ar-Ge):** Roadmap'in
kendi V-08 gerekçesi Faiz Gideri/Faaliyet Kârı'nı "02/FORMÜL-05, kitabın EN
ÇOK vurguladığı gösterge" olarak işaretliyor — bu yüzden %7 (en yüksek).
SG&A %5 (FORMÜL-02, ikinci sırada belirgin vurgu). Ar-Ge EN DÜŞÜK (%3)
BİLEREK — gerekçe aşağıda ayrı bir "GERİLİM" notu olarak açıklanıyor.

### Formüller ve eşikler (mevcut spec'teki HAZIR tablo AYNEN kullanılır)

```
# SG&A/Brüt Kâr — DÜŞÜK=iyi (ters yön, Amortisman Oranı ile AYNI mekanizma,
# quant_denetim_01.md Y5b'deki "dusuk_iyi parametresi/ön-dönüşüm" seçeneği):
sga_orani_pct = Ratios.sga_to_gross_profit_pct
# Eşik (spec_mercek_kalite.md satır 140, DEĞİŞMEDİ): <%30 fantastik (9-10),
# %30-80 mümkün (kademeli 8→3), ~%100+ kırmızı bayrak (0-2)

# Ar-Ge/Brüt Kâr — DÜŞÜK=iyi (Buffett'ın "moat sürekli yeniden-icat
# gerektirmez" tezi):
rd_orani_pct = Ratios.rd_to_gross_profit_pct
# Eşik (satır 141): %0 en iyi (10), ~%30 kırılgan sınırı (5), tavan %50+ (0-2)

# Faiz Gideri/Faaliyet Kârı — DÜŞÜK=iyi:
faiz_orani_pct = Ratios.interest_expense_to_operating_profit_pct
# Eşik (satır 142): <%15 güçlü (Buffett tüketici ürünleri üst sınırı, 9-10),
# %15-40 orta (kademeli), >%40 zayıf (0-3)
```

**Kaynak:** 02/FORMÜL-02, FORMÜL-03, FORMÜL-05, BAYRAK-06.

### GERİLİM notu (Ar-Ge — persona kural 4, çözülmez ama belgelenir)

Buffett'ın çerçevesi (FORMÜL-03) DÜŞÜK Ar-Ge/Brüt Kâr oranını dayanıklı
rekabet avantajı sinyali sayar (örnek tablo: Coca-Cola tipi şirket %0 vs
Intel tipi şirket %16,8 — s.574). Fisher'ın çerçevesi (**HENÜZ İŞLENMEDİ**,
`spec_mercek_buyume.md`'nin kendi UYARI notuyla TUTARLI) muhtemelen TERS
yönde okurdu — YÜKSEK ama VERİMLİ Ar-Ge, özellikle NASDAQ'ın teknoloji
ağırlıklı evreninde, bir moat-İNŞA aracı olarak OLUMLU sayılabilir. Bu
gerilim 00_sentez.md §2.5'teki Graham/Buffett çelişkisiyle AYNI TÜRDEN bir
durum — **çözülmez, BİLİNÇLİ tutulur**: (a) ağırlık kasıtlı olarak EN DÜŞÜK
tutuldu (%3, üç yeni bileşenin en küçüğü), (b) kart açıklaması "yüksek Ar-Ge
oranı bu NASDAQ teknoloji şirketinde OTOMATİK olumsuz sayılmamalı — Fisher
merceği eklendiğinde bu yön YENİDEN değerlendirilecek" notunu TAŞIMALI.

### Kenar durumlar

- **BİST'te HER ZAMAN None:** Üç alan da SADECE NASDAQ'ta dolu olur (BİST
  XI_29 haritasında bu ham alanlar hiç çekilmiyor — V-14/V-15 GRUP 3
  "PAHALI" olarak KALDI, `spec_veri_tamlik_yol_haritasi.md`). BİST
  şirketlerinde bu 3 bileşen `None`, ağırlığı (%15 toplam) KALİTE
  merceğinin diğer 7 bileşenine ORANTISAL yeniden dağıtılır (mevcut
  `_agirlik_dagit_ve_hesapla` mekanizması) — **BİST kartı fiilen v1'e YAKIN
  bir 7-bileşenli KALİTE görür, NASDAQ kartı 10-bileşenli** — bu piyasa
  asimetrisi kartta "SG&A/Ar-Ge/Faiz Gideri verisi BİST'te henüz mevcut
  değil (araştırma gerekiyor)" notuyla AÇIKÇA belirtilmeli (sessiz
  asimetri YASAK, Kural 3).
- **Faiz Gideri/Faaliyet Kârı — net faiz geliri riski:** `interest_expense`
  bazı NASDAQ şirketlerinde NET (gider-gelir birleşik) raporlanabilir
  (spec'in kendi Girdiler notu) — negatif/anormal düşük değer çıkarsa kart
  "net faiz geliri/gideri birleşik raporlanmış olabilir, dikkatli
  yorumlanmalı" notu taşımalı.
- **`gross_profit<=0`:** Üç oran da (payda brüt kâr) `None` döner (mevcut
  `_margin_pct` guard'ı, `spec_mercek_kalite.md`'nin Brüt Marj kenar
  durumuyla AYNI).

---

## §2 — GÜVENLİK merceği (`spec_mercek_guvenlik.md`'ye işlenecek)

### TALİMAT — güncellenmiş ağırlık tablosu

| Bileşen | Eski ağırlık | Yeni ağırlık | Değişim |
|---|---|---|---|
| Kaldıraç (Net Borç/FAVÖK) | %30 | **%29** | -1 |
| Bilanço Kalitesi | %20 | **%18** | -2 |
| Piotroski F-Skoru | %25 | **%24** | -1 |
| Toplam Yükümlülük/Özkaynak | %15 | **%12** | -3 |
| Merton Temerrüt Olasılığı (EDF) | %10 | **%7** | -3 |
| **Faiz Karşılama Oranı (YENİ — "yer tutucu" satırdan YÜKSELTİLDİ)** | %0 (kart notu) | **%10** | +10 |
| **Toplam** | %100 | **%100** | 0 |

Mevcut spec'in "Doğrudan skorlanmayan, kart notu/uyarı olarak eklenen
bulgular" tablosundaki **"Faiz Karşılama Oranı yer tutucu" satırı SİLİNİR**
(HER ZAMAN tetiklenen bir kart-notu değil, artık NASDAQ'ta GERÇEK bir
skorlanan bileşen; BİST'te bileşen `None` döndüğü için oradaki "veri eksik"
davranışı zaten mevcut Kural 3 mekanizmasıyla otomatik karşılanıyor, AYRI
bir kart-notu satırına gerek KALMADI).

### Gerekçe — neden %10, neden bu shave dağılımı

Faiz Karşılama Oranı kitaplar arası **EN SIK tekrarlanan tekil açık** (6+
kez, `spec_veri_tamlik_yol_haritasi.md` V-08 gerekçesi) VE **ÜÇ kitabın
BAĞIMSIZ olarak kendi HAZIR eşik tablosunu ürettiği** (Graham sektör-bazlı
7x/5x, Buffett <%15, Damodaran Tablo 2.4 14-kademeli sentetik kredi notu —
`spec_mercek_guvenlik.md`'nin kendi "HAZIR eşik tablosu" bölümü) TEK
metriktir — bu, projenin şu ana kadar bağladığı en OLGUN/en ÇOK-KAYNAKLI
tekil bileşenlerden biridir, %10 ağırlık (Merton'la EŞİT, Piotroski'nin
altında ama Bilanço Kalitesi'ne yakın) bu olgunluğu YANSITIR.

**Shave kaynağı seçimi:** Merton'dan EN BÜYÜK payı (-3) kestik çünkü Merton
BİZZAT `spec_mercek_guvenlik.md`'nin kendi Uygulama Notu'nda "PROJENİN
HİÇBİR yerinde ÇAĞRILMIYOR" (BAYRAK-79/80) diye işaretli — yani bu ağırlık
şu an FİİLEN hiç üretilmiyor (her kart bileşeni None döndürüyor, ağırlığı
zaten dinamik olarak diğerlerine dağılıyor). Merton'un STATİK ağırlığını
küçültüp o payı GERÇEKTEN üretilen, üç kitaptan doğrulanmış bir metriğe
kaydırmak, "kağıt üstünde büyük ama fiilen sıfır üreten" bir bileşenden
"küçük ama fiilen her NASDAQ kartında dolu" bir bileşene kaymaktır — bu,
"kalibre edilmiş çekirdeği koru" ilkesini İHLAL etmez çünkü Merton zaten
HİÇ kalibre EDİLMEMİŞ bir bileşen (henüz bağlanmadı). Toplam Yükümlülük/
Özkaynak'tan da (-3) kesildi çünkü bu KENDİSİ de yakın zamanda eklenen,
"literatür-kaynaklı ama nihai kalibre değil" (K3b notu) bir bileşen —
Kaldıraç/Bilanço Kalitesi/Piotroski (kalibre edilmiş ÜÇ ÇEKİRDEK) EN AZ
zarar gördü (-1,-2,-1).

### Formüller ve eşikler (Damodaran Tablo 2.4, CANLI kitap metninden alındı)

```
# Faiz Karşılama Oranı = FVÖK (Faaliyet Kârı ile YAKLAŞIK) / Faiz Gideri.
# Kod-geliştirici NOTU: `interest_expense`'in KENDİSİ ayrı bir Ratios
# alanı olarak YOK, sadece ORANI (interest_expense_to_operating_profit_pct)
# var -- coverage TERS çevirerek türetilir (yeni fetcher/alan GEREKMEZ):
if interest_expense_to_operating_profit_pct is None or interest_expense_to_operating_profit_pct <= 0:
    faiz_karsilama_orani = None   # faiz gideri sıfır/negatif/net-gelir
    # ise oran anlamsız -- Kural 3, uydurma YAPILMAZ, "faiz gideri
    # raporlanmamış/anlamsız" notu kartta gösterilir.
else:
    faiz_karsilama_orani = 100 / interest_expense_to_operating_profit_pct

# Damodaran Tablo 2.4 (03/Tablo 2.4, CANLI okundu) -- breakpoint tablosu,
# kod-geliştirici ARDIŞIK breakpoint'ler arasında `_lerp_score` ile
# YUMUŞATABİLİR (mevcut motorun sürekli-skor felsefesiyle TUTARLI):
# oran > 12,50           -> 10,0  (AAA)
# oran 9,50 - 12,50      -> 9,0-10,0  (AA)
# oran 7,50 - 9,50       -> 8,0-9,0   (A+)
# oran 6,00 - 7,50       -> 7,5-8,0   (A)   <- Graham'ın sanayi "en iyi 7x" ile ÇAPRAZ TUTARLI
# oran 4,50 - 6,00       -> 6,5-7,5   (A-)
# oran 4,00 - 4,50       -> 6,0-6,5   (BBB)
# oran 3,50 - 4,00       -> 5,5-6,0   (BB+)
# oran 3,00 - 3,50       -> 5,0-5,5   (BB)   <- Graham'ın sanayi "en kötü 5x" ALTI burada başlar
# oran 2,50 - 3,00       -> 4,0-5,0   (B+)
# oran 2,00 - 2,50       -> 3,0-4,0   (B)
# oran 1,50 - 2,00       -> 2,0-3,0   (B-)
# oran 1,25 - 1,50       -> 1,5-2,0   (CCC)
# oran 0,80 - 1,25       -> 1,0-1,5   (CC)
# oran 0,50 - 0,80       -> 0,5-1,0   (C)
# oran < 0,50            -> 0,0-0,5   (D)
```

**Kaynak:** 03/Tablo 2.4, FORMÜL-19 (Interest Coverage Ratio); 01/FORMÜL-18
(Graham'ın sanayi sektörü 7x/5x bandı, ÇAPRAZ referans olarak kart
açıklamasında anılır); 02/FORMÜL-05 (Buffett <%15 — bu, KALİTE'deki §1
bileşeniyle AYNI ham veri, FARKLI formül, "TEK satırda BİRLEŞTİRİLDİ" ilkesi
ile çift-sayma SAYILMAZ).

### Kenar durumlar

- **BİST'te HER ZAMAN None** (aynı V-08/V-15 asimetrisi, §1'deki BİST notu
  ile AYNI) — ağırlık (%10) diğer 5 GÜVENLİK bileşenine ORANTISAL dağıtılır.
- **Damodaran Tablo 2.4'ün kendisi "2004, küçük sanayi şirketleri" için
  kalibre edilmiş** (kitap metninde AÇIKÇA yazılı) — büyük/mega-cap NASDAQ
  şirketlerinde (AAPL, MSFT gibi) bu bantlar KATI olmayabilir, kart "bu
  bant küçük/orta ölçekli sanayi şirketleri için kalibre edilmiştir, mega-
  cap şirketlerde gevşek yorumlanmalı" notu taşımalı (uydurma YAPILMADAN,
  kitabın KENDİ sınırlaması AKTARILIYOR).

---

## §3 — BÜYÜME merceği (`spec_mercek_buyume.md`'ye işlenecek)

### TALİMAT — güncellenmiş ağırlık tablosu

| Bileşen | Eski ağırlık | Yeni ağırlık | Değişim |
|---|---|---|---|
| Hasılat Büyümesi (reel, seviye+trend) | %55 | **%55** | 0 |
| PEG Oranı (Lynch) | %25 | **%15** | -10 |
| Marjinal ROE + Verimlilik Kaynaklı Büyüme | %20 | **%17** | -3 |
| **Capex/Net Kâr (Yeniden Yatırım Kalitesi, YENİ)** | — | **%8** | +8 |
| **Payout Oranı (Temettü Disiplini, YENİ)** | — | **%5** | +5 |
| **Toplam** | %100 | **%100** | 0 |

### Gerekçe — neden Hasılat Büyümesi DOKUNULMADI, neden PEG'den kesildi

`spec_mercek_buyume.md`'nin kendi metni Hasılat Büyümesi'nin %55 ağırlığını
AÇIKÇA "mercek zayıf temellenmiş (Fisher/Lynch henüz işlenmedi), sağlam olan
TEK bileşene fazla ağırlık vermek YAPAY otorite vermekten daha DÜRÜST"
gerekçesiyle SAVUNUYOR — bu argüman İKİ yeni, kitap-doğrulanmış bileşen
eklendikten SONRA da GEÇERLİLİĞİNİ KORUYOR (mercek hâlâ Fisher/Lynch
eksikliği taşıyor), bu yüzden bu bileşene DOKUNULMADI.

PEG'den BÜYÜK pay (-10) kesildi çünkü PEG'in KENDİSİ spec'in kendi metninde
"BİLİNEN TANIM SAPMASI: büyüme bazı revenue (net kâr/HBK OLMALI, 03/FORMÜL-
74)" olarak zaten kusurlu işaretli — kusurlu-tanımlı bir bileşenin payını,
temiz-tanımlı iki yeni bileşene (Capex/Net Kâr — FORMÜL-28 doğrudan eşik
verir; Payout Oranı — İLKE-178 doğrudan eşik verir) kaydırmak "kitap-
sadakati" argümanını GÜÇLENDİRİR (KALİTE'deki FAVÖK-kesintisiyle AYNI
mantık). Marjinal ROE'den küçük bir pay (-3) kesildi (kendi ağırlığı zaten
"kalibrasyon scriptiyle YENİDEN gözden geçirilecek" notuyla GEÇİCİ
işaretliydi, K5b).

### Formüller ve eşikler

```
# Capex/Net Kâr — DÜŞÜK=iyi (ters yön), 02/FORMÜL-28'İN KENDİ SAYISAL
# eşiği DOĞRUDAN kullanılıyor (uydurma DEĞİL, kitaptan BİREBİR):
capex_orani_pct = Ratios.capex_to_net_income_pct
# Eşik (FORMÜL-28, s.175-176): <%25 mükemmel (9-10), %25-50 kabul
# edilebilir/dayanıklı avantaj olası (kademeli 8->5), >%50 zayıf/sermaye-
# yoğun (kademeli 4->0, tavan %100)

# Payout Oranı (Temettü Disiplini) — BANTLI (monotonik DEĞİL, PEG'in
# U-şekli sorunuyla (BAYRAK-23) AYNI TÜRDEN bir tasarım, ama burada YENİ
# bir bileşen olduğu için BAŞTAN doğru -- iki-taraflı lerp):
payout_pct = Ratios.payout_ratio_pct
if 60 <= payout_pct <= 75:
    payout_skoru = _lerp_score(abs(payout_pct - 67.5), 0, 7.5, 10, 9)  # bant ortası (67,5) tepe
elif payout_pct < 60:
    payout_skoru = _lerp_score(payout_pct, 0, 60, 4, 9)   # düşük payout -- İLKE-180 hafif ceza, SIFIRA vurmaz
else:  # payout_pct > 75
    payout_skoru = _lerp_score(payout_pct, 75, 100, 9, 3)  # aşırı yüksek payout -- İLKE-177 tersi ucu
```

**Kaynak:** 02/FORMÜL-25,28 (Capex — "kitabın bu bölümde EN ÇOK vurguladığı
gösterge"); 01/İLKE-177 (yeniden yatırım ≥1 birim değer yaratmalı, aksi
halde dağıtılmalı), İLKE-178 (%60-75 tercih bandı), İLKE-180 (Zweig/Arnott
&Asness: düşük temettü ödeyenlerde gelecek 10 yıl kazanç büyümesi ort. 3,9
puan DAHA DÜŞÜK), İLKE-181 (temettü artırımı sonraki 4 yıl daha iyi
performans/kârlılıkla ilişkili).

### GERİLİM notu (Payout Oranı — atıf hijyeni uyarısı)

**ÖNEMLİ DÜZELTME (bu spec'in kendi bulgusu, kaynak atfı hatası
ÖNLENDİ):** Buffett'ın "equity bond" kavramı (02/İLKE-52) kuponun
**"vergi öncesi kâr, TEMETTÜ DEĞİL"** olduğunu AÇIKÇA belirtiyor
(s.182-183, kitaptan BİREBİR alıntı) — bu yüzden Payout Oranı bileşeni
İLKE-52-57 ailesine ATIFLA GEREKÇELENDİRİLMEDİ (DEĞER merceğinin Kazanç
Getirisi bileşeni zaten o aileyi DOĞRU kullanıyor, `spec_mercek_deger.md`
satır 158). Bu, `spec_mercek_kalite.md`'nin kendi belgelediği FAVÖK/İLKE-06
atıf-hijyeni düzeltmesiyle AYNI TÜRDEN bir titizlik denetimidir — Payout
Oranı bileşeni SADECE İLKE-177/178/180/181'e (Böl.45, GERÇEKTEN temettü
hakkında konuşan bölüm) atıfla kurulmuştur.

### Kenar durumlar

- **BİST'te de ÇALIŞIR (V-09/V-10, V-11/V-12 İKİ piyasada da tamamlandı):**
  Capex ve Payout bileşenleri, mercek çoğunluğundan FARKLI olarak, BU
  turda **piyasa simetriktir** — BİST XI_29 şirketlerinde de dolu olur
  (isyatirim.py "4CAI"/"4CBB" itemCode'ları). Kart açıklamasında bu
  simetri AÇIKÇA "BİST+NASDAQ'ta eşit kapsam" notuyla belirtilebilir
  (§1/§2'deki NASDAQ-only asimetriden FARKLI bir durum).
- **`ttm_net_income<=0`:** Her iki bileşen de zaten `calculator.py`'de bu
  guard'a sahip (mevcut kod, `capex_to_net_income_pct`/`payout_ratio_pct`
  tanımları) — `None`, ağırlık diğer 3 BÜYÜME bileşenine ORANTISAL
  dağıtılır.
- **BİST'te DPS per-share YOK ama toplam payout ÇALIŞIYOR:** V-11 devir
  notu ile TUTARLI — Payout Oranı hisse-başına kırılım GEREKTİRMEZ
  (`dividends_paid_ttm/net_income_ttm`), bu yüzden BİST'te DPS eksikliği
  BU bileşeni ENGELLEMİYOR (ama §4'teki Temettü Verimi'ni ENGELLİYOR).

---

## §4 — DEĞER merceği: BU TURDA YENİ AĞIRLIKLI BİLEŞEN ALMIYOR

### TALİMAT

`spec_mercek_deger.md`'nin ağırlık tablosu **DEĞİŞMEZ**. Kalan 4 kalem (V-03
Temettü Verimi, V-07 Efektif Vergi Oranı [DEĞER-tarafı, alt bölüm], V-13
Opsiyon Seyreltme) DEĞER merceğinde kart notu olarak kalıyor — gerekçe
aşağıda ve §5'te.

### Gerekçe — neden Temettü Verimi SKORLANMADI

Görev talimatı, V-03'ün "DEĞER'in Kazanç Getirisi/Güvenlik Marjı bileşenini
AÇTIĞINI" öngörüyordu; bu spec bu öngörüyü **canlı kitap doğrulamasıyla
ELEDİ** — üç somut engel bulundu:

1. **Atıf hijyeni riski:** Buffett'ın equity-bond kuponu TEMETTÜ DEĞİL,
   vergi öncesi kâr'dır (İLKE-52, bkz. §3 GERİLİM notu) — Kazanç Getirisi
   bileşeni (F/K bazlı) zaten BU kavramı DOĞRU temsil ediyor, Temettü
   Verimini AYNI aileye eklemek YANLIŞ bir atıf üretirdi.
2. **Graham'ın GERÇEK kriteri TTM'le KARŞILANAMIYOR:** `01_graham_akilli_
   yatirimci.md` satır 934 kitabın KENDİ sentez notu — "QuaxisLabs'ın açık
   veri boşlukları: ... (2) temettü geçmişi ... Bu üç boşluk 7 kriterin
   3'ünün uygulanmasını ENGELLİYOR." KONTROL N madde 4 "Son 20 yıl boyunca
   KESİNTİSİZ temettü ödemesi" — QuaxisLabs SADECE TTM verisine sahip
   (`trends.py` 12 çeyrek/~3 yıl sınırı, V-21 yapısal bloker). TTM'de
   "temettü ödedi/ödemedi" ikili sinyalini bu 20-yıllık KRİTERİN YERİNE
   koymak, V-13'ün (opsiyon seyreltme) "kaba vekil" hassasiyet-kaybı
   sorununu TEKRARLARDI — ve bu kez kitabın KENDİSİ bu tam boşluğu
   AÇIKÇA belgelemiş durumda (uydurma riski YÜKSEK).
3. **Temiz bir "yüksek verim=iyi" eşiği hiçbir kaynakta YOK:** Yüksek
   temettü verimi hem OLUMLU (Graham'ın gelir odaklı yatırımcı profili) hem
   OLUMSUZ (aşırı yüksek verim genelde bir DİSTRESS/sürdürülemezlik
   sinyalidir, Zweig'ın kendi literatüründe de dolaylı kabul edilir)
   okunabilir — banded bir formül İCAT ETMEK (Payout Oranı'nda yaptığımız
   gibi) burada kitap-temelli DEĞİL, tahmini olurdu.

**Sonuç:** `ttm_dividend_per_share` DEĞER merceğinde **kart notu** olarak
kalır — "Bu şirket son 12 ayda [X] TL/USD hisse başına temettü ödedi
(TTM) — Graham'ın 20 yıllık kesintisiz kayıt kriteri için yeterli çok-yıllı
veri PROJEDE HENÜZ YOK" formatında. Payout Oranı (BÜYÜME merceğinde
SKORLANAN, §3) bu ham veriden TÜRETİLEN farklı bir soruya (sürdürülebilirlik
disiplini, TTM'le zaten anlamlı) cevap verir — çift-standart DEĞİLDİR,
İKİ farklı SORUYA iki farklı VERİ-YETERLİLİK cevabı verilmiştir.

---

## §5 — Kart notu olarak kalan 6 kalem (skorsuz, gerekçeli)

Aşağıdaki kalemler **hiçbir mercek ağırlık tablosuna girmez** — nedenleri
kalem bazında, mevcut Güvenlik spec'inin "Doğrudan skorlanmayan, kart notu/
uyarı olarak eklenen bulgular" tablo formatıyla TUTARLI şekilde belgelenir.

| Kalem | Ratios/modül alanı | Ev sahibi mercek (kart) | Neden skorlanmadı |
|---|---|---|---|
| Temettü Verimi/DPS | `ttm_dividend_per_share` | Değer | §4 — atıf hijyeni + Graham'ın 20-yıl kriteri TTM'le karşılanamıyor |
| Opsiyon/Warrant Seyreltme | `diluted_dilution_pct` | Değer | Aşağıda |
| Efektif Vergi Oranı | `pretax_profit`/`tax_provision` (henüz ORAN bile YOK) | Kalite | Aşağıda |
| Devir Hızı/Amihud İlliklidite | `liquidity.py` (Ratios'ta hiç YOK) | Güvenlik | Aşağıda |
| Ödenen Temettü+Finansman Faal. | `ttm_share_buyback`/`ttm_net_financing_debt_change` | Güvenlik | Aşağıda |

### Opsiyon/Warrant Seyreltme (V-13) — Değer, kart notu

Mevcut `spec_mercek_deger.md` bu kalemi ZATEN "kaba vekil" (03/İLKE-167-169)
olarak nitelendirmişti (Kenar Durumlar bölümü) — bu spec bu nitelendirmeyi
DOĞRULAR ve resmileştirir: (a) SADECE NASDAQ'ta dolu (BİST'te opsiyon bazlı
ücretlendirme standart bir XBRL etiketiyle raporlanmıyor, TAM bloker) —
piyasa-asimetrik bir bileşeni DEĞER'in ana ağırlık tablosuna eklemek,
BİST şirketlerini SİSTEMATİK olarak "bu bileşen eksik" durumuna düşürür
(sektör bilinci ilkesinin piyasa-versiyonu); (b) "kaba vekil" olduğu
kitabın KENDİSİNCE de ima ediliyor (tam Black-Scholes değerleme V-29,
GRUP 4 "NİTEL/dipnot okuma gerektirir" olarak ayrıca işaretli — bu, kaba
vekilin TAM formülün YERİNE GEÇEMEYECEĞİNİN kitap-içi kanıtıdır). Kart notu:
"[X]% seyreltme (TTM, basit-ağırlıklı vs seyreltilmiş pay sayısı farkı) —
kaba bir vekildir, opsiyon/warrant dipnot detayı İÇERMEZ."

### Efektif Vergi Oranı (V-07 ikinci yarısı) — Kalite, kart notu

**VERİ BAĞIMLILIĞI:** Bu kalem `spec_mercek_kalite.md`'nin diğer 3
bileşeninden (§1) YAPISAL OLARAK FARKLI bir durumda — `pretax_profit`/
`tax_provision` HENÜZ bir `Ratios` ORANI bile DEĞİL, sadece `FIELD_LABELS_
TR` üzerinden kart satırı olarak PASS-THROUGH ediliyor (calculator.py satır
124-132, CANLI doğrulandı). Skorlanan bir bileşen olması için ÖNCE
`effective_tax_rate_pct = tax_provision / pretax_profit * 100` gibi KÜÇÜK
bir formül adımının `Ratios`'a eklenmesi gerekir (kod-geliştiriciye NOT,
bu spec'in kapsamı DIŞINDA bir kodlama görevi).

Bu formül adımı eklense BİLE, bu spec BİLEREK bunu SKORLANAN bir bileşene
YÜKSELTMEZ, üç nedenle: (1) Türkiye (~%25 + teşvik rejimleri) ve ABD
(~%21 federal + eyalet) arasında "normal" efektif vergi oranı BAMBAŞKA
bir taban çizgisine sahip — TEK bir mutlak eşik (Değer/Kalite'nin diğer
bileşenlerinde olduğu gibi) İKİ piyasada AYNI ANLAMA GELMEZ, ikili bir
eşik seti İCAT ETMEK bu turun kapsamı dışında bir araştırma gerektirir;
(2) DÜŞÜK/negatif efektif vergi oranı ÇOK sinyal taşır (vergi teşviki,
tek seferlik vergi geliri, agresif vergi pozisyonu, geçmiş zarar mahsubu)
— "düşük=iyi" ya da "düşük=kötü" YÖNÜ tek başına BELİRSİZ, bu tam olarak
Schilit'in (06, HENÜZ İŞLENMEDİ) sistematik kazanç-manipülasyonu
çerçevesinin konusu; (3) roadmap'in kendisi bu kalemi V-23 (Muhasebe
Kalitesi/Manipülasyon, "NİTEL — ayrı mimari") ailesiyle AYNI ruhta
işaretliyor. **Karar:** kart notu, "efektif vergi oranı %[X] (vergi
karşılığı/vergi öncesi kâr) — anormal derecede düşük/negatifse kazanç
kalitesi açısından ayrıca incelenmeli (Schilit'in konusu, henüz projeye
işlenmedi)" formatında; SKORLANMAZ.

### Devir Hızı/Amihud İlliklidite (V-05) — Güvenlik, kart notu (kalibrasyon bekliyor)

`liquidity.py` modülü ZATEN yazılmış (SIFIR yeni fetcher, kendi docstring'i
"BİLİNÇLİ OLARAK SKORLANMAYAN" diyor) ama roadmap'in TEK somut kaynağı
(`bilgi-bankasi/_ilerleme.md` Kısım 7 notu, CANLI okundu) Damodaran'ın
Ch.14 (Likidite Değeri) çerçevesinin "BÜYÜK ÖLÇÜDE ÖZEL şirket odaklı
(kısıtlı hisse/QMDM)" olduğunu, halka açık hisseler için turnover-tabanlı
PROXY'nin kitaptan DEĞİL, projenin KENDİ mühendislik kararından geldiğini
AÇIKÇA belirtiyor — yani **hiçbir kitapta bu oran için sayısal bir eşik
YOK** (Damodaran'ın Ch.14 formülleri kısıtlı-hisse iskonto YÜZDESİ üretir,
turnover% BANDI değil). `spec_mercek_buyume.md`'nin Marjinal ROE bileşeni
BİLE (±15 puanlık) bir "literatür-kaynaklı başlangıç değeri" bulabilmişti
(Goldman Sachs 2005 örneği) — Devir Hızı/Amihud için BÖYLE bir başlangıç
noktası YOK, "proje kalibrasyonu" dili DAHİ şu an elde CANLI bir kalibrasyon
koşusu (örn. `scripts/kalibrasyon_v2.py` emsali) OLMADAN kullanılamaz.
**Karar:** kart notu ("[X]% devir hızı, Amihud illikidite [Y]" ham
rakamlar), SKORLANMAZ; **ÖNERİLEN sonraki adım** (bu spec'in kapsamı
dışında): BİST+NASDAQ evreninin TAMAMında (n≥30 hedefiyle) canlı bir
persentil-bazlı kalibrasyon koşusu, ardından GÜVENLİK merceğine bonus/
malus tipi bir bileşen olarak (NCAV'ın DEĞER merceğindeki "taban etkili
bonus" deseniyle AYNI) eklenmesi.

### Ödenen Temettü + Finansman Faaliyetleri (V-12) — Güvenlik, kart notu

Kod-geliştiricinin KENDİ V-12 devir notu bu kalemin kanonik ev sahibini
GÜVENLİK olarak ÖNERMİŞTİ ("sermaye tahsisi disiplini sinyali") — bu spec bu
öneriyi KABUL EDER ama SKORLAMAZ, çünkü: (1) `ttm_share_buyback` (SADECE
NASDAQ) ve `ttm_net_financing_debt_change` (SADECE BİST, "4CBA" — net
FİNANSMAN BORCU değişimi, GERÇEK bir hisse geri alımı DEĞİL) **kavramsal
olarak FARKLI şeyleri ölçer** — BİST tarafında POZİTİF değer "daha çok
borçlandı" anlamına gelebilirken NASDAQ tarafında `ttm_share_buyback`
"hissedara nakit iade etti" anlamına gelir; TEK bir formülde birleştirmek
piyasalar arası ELMA-ARMUT kıyası üretir (persona kural 3(b)'nin piyasa
versiyonu — sektör bilinci gibi PİYASA bilinci de gerekir); (2) her iki
alan da MUTLAK PARA BİRİMİ tutarıdır (TL/USD), NORMALİZE edilmemiş (market
cap veya net kârla oranlanmamış) — farklı büyüklükteki şirketleri
kıyaslamak matematiksel olarak ANLAMSIZ, önce bir oran formülü tasarlanması
gerekir (bu spec'in kapsamı DIŞINDA, çünkü normalizasyon YÖNTEMİ [market
cap mi, FCF mi, net kâr mı] başlı başına bir tasarım kararı). **Karar:**
kart notu, "TTM ödenen temettü [X], [BİST: net finansman borcu değişimi /
NASDAQ: hisse geri alımı] [Y]" ham rakamlar; SKORLANMAZ. Gelecek bir tur
BU normalizasyon kararını verirse, GÜVENLİK'in "sermaye tahsisi disiplini"
bileşeni olarak yükseltilebilir.

---

## Uygulama notu (izlenebilirlik)

- Bu spec'in TÜM ağırlık değişiklikleri **`_agirlik_dagit_ve_hesapla`
  mekanizmasının STATİK/tasarım-zamanı girdisidir** — DİNAMİK yeniden
  dağıtım (bir bileşen `None` döndüğünde) davranışı BU spec'le
  DEĞİŞMEMİŞTİR, sadece "hepsi doluyken" temel ağırlıklar değişmiştir.
- SG&A/Ar-Ge/Faiz Gideri/Faiz Karşılama/Capex/Payout — 6 SKORLANAN
  bileşenin TAMAMI **quant_denetim_01.md K1'in "cliff" sorununu miras
  alan `_seviye_trend_skoru`/`kademeli_enterpolasyon` ailesini KULLANIYORSA**
  aynı düzeltme (sürekli ceza-çarpanı, uçları-çakışan bantlar) BU 6 yeni
  bileşen için de GEÇERLİDİR — spec seviyesinde AYRICA TEKRARLANMAZ,
  `spec_mercek_deger.md` §Formüller-1'deki devir notu TÜM mercekler için
  zaten kapsayıcı.
- Bu spec'in ağırlık değişiklikleri kod-geliştirici tarafından
  `spec_mercek_{kalite,buyume,guvenlik}.md`'nin "Eşikler ve ağırlıklar"
  tablolarına AYNEN işlendiğinde, o dosyalardaki "SG&A/Ar-Ge/Faiz Gideri
  VERİ EKSİK olduğu için şimdilik SKORLANMAZ" cümlesi (spec_mercek_kalite.md
  satır 131-136) ve "Faiz Karşılama Oranı yer tutucu" satırı (spec_mercek_
  guvenlik.md satır 130) **SİLİNMELİDİR** (artık doğru değil).

---

## Test senaryoları

1. **NASDAQ teknoloji şirketi (örn. AAPL benzeri, düşük Ar-Ge, düşük SG&A,
   düşük faiz gideri):** KALİTE'nin 3 yeni bileşeni YÜKSEK puan üretir,
   toplam KALİTE skoru eski ağırlıklandırmaya göre BİRAZ ARTAR (FAVÖK
   marjı payı küçüldüğü için bu artış SINIRLI kalır, aşırı ŞİŞMEZ).
2. **NASDAQ ilaç/biyoteknoloji şirketi (yüksek Ar-Ge, örn. %25-30/brüt
   kâr):** Ar-Ge bileşeni DÜŞÜK puan üretir AMA kart açıklaması GERİLİM
   notunu (Fisher eklenene kadar bu yön TARTIŞMALI) TAŞIR — düşük ağırlık
   (%3) toplam skoru BÜYÜK ÖLÇÜDE ETKİLEMEZ.
3. **BİST sanayi şirketi (herhangi biri):** KALİTE'nin 3 yeni bileşeni +
   GÜVENLİK'in Faiz Karşılama bileşeni HEPSİ `None` — KALİTE skoru diğer 7
   bileşene, GÜVENLİK skoru diğer 5 bileşene ORANTISAL olarak yeniden
   dağıtılmış ağırlıklarla YİNE ÜRETİLİR (mercek çökmesi YOK); kart "SG&A/
   Ar-Ge/Faiz Gideri/Faiz Karşılama verisi BİST'te henüz mevcut değil"
   notu taşır.
4. **BİST/NASDAQ karşılaştırması, ikisi de sağlıklı temettü ödeyen olgun
   şirket (örn. bir BİST holding %65 payout, bir NASDAQ tüketici şirketi
   %68 payout):** BÜYÜME'nin Payout Oranı bileşeni İKİSİNDE de Graham'ın
   %60-75 bandına YAKIN, YÜKSEK puan üretir (piyasa-simetrik davranış
   doğrulanır) — AYNI şirketlerin DEĞER merceğinde Temettü Verimi hâlâ
   sadece kart notu olarak görünür (skor ETKİLENMEZ).
5. **Yüksek kaldıraçlı, düşük faiz karşılamalı bir NASDAQ şirketi (oran
   <1,5x, Damodaran "B-/CCC" bandı):** GÜVENLİK'in yeni Faiz Karşılama
   bileşeni ÇOK DÜŞÜK puan üretir; bu, MEVCUT Kaldıraç bileşeniyle (Net
   Borç/FAVÖK, muhtemelen YÜKSEK/kötü) AYNI YÖNDE işaret etmeli (çapraz
   tutarlılık testi — eğer ikisi ZIT yönde çıkarsa bu bir VERİ TUTARSIZLIĞI
   sinyalidir, kartta işaretlenmelidir, `spec_mercek_guvenlik.md` Test
   senaryosu 4 ile AYNI ilke).
