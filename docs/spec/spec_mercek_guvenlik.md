# SPEC: Güvenlik Merceği (v2 Çok-Mercekli Skorlama — Mercek 4/4)

> **UYARI — ORTA-ZAYIF TEMELLENMİŞ MERCEK (bkz. 00_sentez.md §5, §6 özet
> tablosu):** Bu merceğin BİRİNCİL kaynağı Schilit ("Financial Shenanigans"
> — sistematik muhasebe hilesi tespit teknikleri: tahakkuk/nakit ayrışması
> oranı, alacak-envanter/hasılat büyüme ayrışması oranı, agresif gelir
> kaydı desenleri) HENÜZ İŞLENMEDİ. Bu spec SADECE Graham'ın kırmızı
> bayrakları (Ch.12 kazanç kalitesi, KONTROL L), Buffett'ın bilanço/
> kaldıraç disiplini VE Damodaran'ın mali sıkıntı maliyeti çerçevesi
> (Ch.17, Kısım 9) üzerine kuruludur — **SİSTEMATİK muhasebe hilesi
> tespiti (Schilit'in asıl konusu) bu mercekte EKSİKTİR**, mevcut malzeme
> NİTEL uyarılar düzeyinde kalır. **Schilit eklendiğinde bu spec'in
> "Muhasebe Kalitesi Kırmızı Bayrak Sayacı" bölümü SİSTEMATİK bir sayısal
> kontrole DÖNÜŞTÜRÜLMELİDİR.**

## Amaç ve kapsam

**Ölçtüğü soru:** Muhasebe hilesi + bilanço riski — bu şirket YAKINDA
ZOR duruma düşer mi, ve raporlanan rakamlara GÜVENİLEBİLİR mi?

**Geçerli şirket türleri:** `sanayi`, `abd_sanayi` BİRİNCİL. `banka`/
`sigorta`/`finansman` için KISMEN geçerli — kaldıraç kavramı bu
sektörlerde YAPISAL OLARAK FARKLIDIR (Buffett İLKE-31: bankalar
İSTİSNADIR, mutlak eşik yerine SEKTÖR İÇİ kıyas GEREKİR), aşağıda
ayrıştırılmıştır.

**Piyasalar:** BİST + NASDAQ.

**Kapsam dışı:** Tahvil/kredi enstrümanı fiyatlaması, ülke kredi notu
karşılaştırması (Damodaran Kısım 9'un bazı formülleri — QuaxisLabs tahvil
fiyatı ÇEKMİYOR, hisse-odaklı mimari).

---

## Girdiler

| Alan | Kaynak | Durum |
|---|---|---|
| Net Borç/FAVÖK (kaldıraç) | `calculator.Ratios.net_debt_to_ebitda` | MEVCUT (scorer.py'nin mevcut "Kaldıraç" bileşeni) |
| Cari Oran | `calculator.Ratios.current_ratio` | MEVCUT |
| Özkaynak/Toplam Varlık | `equity/total_assets` (türetilmiş) | MEVCUT (scorer.py'nin "Bilanço Kalitesi" bileşeninin YARISI) |
| Borç/Özkaynak (dar, sadece finansal borç) | `calculator.Ratios.debt_to_equity` | MEVCUT |
| Piotroski F-Skoru (9 kriter) | `fundamental_screens.PiotroskiResult` | MEVCUT (SADECE BIST XI_29 sanayi) |
| Merton Distance-to-Default / EDF | `src/analysis/merton.py::compute_merton_dd_edf()` | MEVCUT ama **HİÇBİR modüle BAĞLI DEĞİL** (BAYRAK-79/80, en düşük maliyetli mimari bulgu) |
| Nakit Yakma Oranı (negatif FAVÖK'te) | `cash`, `ebitda()` (ham veri MEVCUT) | **YENİ (ucuz)** — Damodaran FORMÜL-164 |
| Toplam Yükümlülük/Özkaynak (geniş tanım) | `short_term_liabilities+long_term_liabilities`/`equity` (ham veri MEVCUT) | **YENİ (ucuz)** — Buffett FORMÜL-16 |
| Faiz Karşılama Oranı (FVÖK/Faiz Gideri) | `interest_expense` (sanayi/XI_29) YOK | VERİ EKSİK — kitaplar arası EN SIK tekrarlanan açık (6+ kez, bkz. Kenar Durumlar Merton köprüsü ile KISMİ telafi) |
| Kredi Notu / Temerrüt Olasılığı (harici) | YOK | VERİ EKSİK — Merton EDF sentetik bir vekil sunar (bkz. aşağı) |
| Sıkıntı sinyali (F/K yok ama FD/FAVÖK var) | `pe_ratio`, `pb_ratio`, `ev_ebitda`, `ev_revenue` (HEPSİ MEVCUT) | **YENİ (sıfır yeni veri)** — Damodaran BAYRAK-76 |
| Negatif özkaynak / derin sıkıntı etiketi | `equity` (MEVCUT) | **YENİ (sıfır yeni veri)** — Damodaran BAYRAK-83 |

---

## Formüller

```
# 1. Kaldıraç + Bilanço Kalitesi (MEVCUT motor, AYNEN taşınır):
kaldirac_skoru = skor_kaldirac(net_debt_to_ebitda, cfg)   # scorer.py'den birebir
bilanco_kalitesi_skoru = skor_bilanco_kalitesi(current_ratio, equity/assets, cfg)

# 2. Piotroski F-Skoru (MEVCUT, taşınır -- SÜREKLİ skora dönüştürülür):
f_skoru_pct = (piotroski.score / piotroski.criteria_evaluated) * 100  # criteria_evaluated>=5 sartiyla
guvenlik_f_skoru_katkisi = seviye_trend_skoru(f_skoru_pct, None, guclu_esik=78, orta_esik=44, tavan=100)
  # 78% ~ 7/9, 44% ~ 4/9 (Piotroski'nin kendi orijinal 2000 makalesi bandına yakın)

# 3. Nakit Yakma Oranı (YENİ, SADECE FAVÖK<0 iken anlamlı):
if ebitda < 0:
    nakit_yakma_orani = cash / abs(ebitda)   # kaç DÖNEMDE nakit tükenir (kaba)

# 4. Toplam Yükümlülük/Özkaynak (geniş tanım, YENİ):
toplam_yukumluluk_ozkaynak = (short_term_liabilities + long_term_liabilities) / equity
  # MEVCUT dar debt_to_equity'nin YANINA eklenir, YERİNE GEÇMEZ (bkz. Kenar Durumlar)

# 5. Sıkıntı Sinyali (YENİ, sıfır yeni veri, BAYRAK-76):
if (pe_ratio is None or pb_ratio is None) and (ev_ebitda is not None or ev_revenue is not None):
    sikinti_notu = "F/K veya PD/DD hesaplanamıyor (zarar/negatif özkaynak) ama FD-bazlı çarpan mevcut -- bu durumun kendisi bir sıkıntı sinyalidir"

# 6. Derin Sıkıntı / Negatif Özkaynak Etiketi (YENİ, sıfır yeni veri, BAYRAK-83):
if equity < 0:
    derin_sikinti_etiketi = "negatif defter özkaynağı -- standart PD/DD ANLAMSIZ, opsiyon-teorik olarak (Merton çerçevesi) pozitif piyasa değeri YİNE DE NORMAL olabilir (bkz. Eurotunnel 1997 örneği)"

# 7. Merton EDF Köprüsü (YENİ ORKESTRASYON, sıfır yeni veri, BAYRAK-79/80):
merton_sonucu = compute_merton_dd_edf(...)   # ZATEN MEVCUT fonksiyon, sadece ÇAĞRILMASI eksik
temerrut_olasiligi_pct = merton_sonucu.default_probability_pct
```

---

## Eşikler ve ağırlıklar

**GÜVENLİK merceği iç ağırlıkları (`sanayi`/`abd_sanayi`, toplam %100):**

| Bileşen | Ağırlık | Eşikler | Gerekçe / kaynak |
|---|---|---|---|
| Kaldıraç (Net Borç/FAVÖK) | %30 | Mevcut scorer.py `kaldirac` cfg AYNEN taşınır (çok iyi<1, iyi<2,5, orta<4, tavan8) | Kalibre edilmiş, canlı doğrulanmış çekirdek KORUNUR. Moody's/S&P kaldıraç bantlarıyla UYUMLU (evrensel kredi analizi pratiği, SCORING_METHODOLOGY.md). |
| Bilanço Kalitesi (Cari Oran + Özkaynak/Varlık) | %20 | Mevcut scorer.py `bilanco_kalitesi` cfg AYNEN taşınır (cari oran iyi≥1,5/orta≥1; özkaynak/varlık iyi≥%40/orta≥%25) | 01/FORMÜL-26 (cari oran≥2,0 SANAYİ, Ch.14), 01/İLKE-154 (girişimci≥1,5, Ch.15) — mevcut eşikler Buffett'ın istisna bulgusuyla (İLKE-20) GERİLİM İÇİNDEDİR, bu GERİLİM ÇÖZÜLMEZ, BİLİNÇLİ olarak burada TUTULUR (bkz. Kenar Durumlar). |
| Piotroski F-Skoru (finansal sağlık) | %25 | 9 kriterden ≥5'i değerlendirilebiliyorsa: oran≥%78 güçlü, %44-78 orta, <%44 zayıf | Joseph Piotroski (2000) — mevcut `fundamental_screens.py` çekirdeği, KALDIRAÇ ve KALİTE'yi (tahakkuk/nakit ayrışması dahil) TEK bir sayıda BİRLEŞTİRİR, bu yüzden GÜVENLİK merceğinde AĞIRLIKLI bir bileşen. |
| Toplam Yükümlülük/Özkaynak (geniş tanım) | %15 | İKİNCİL/tamamlayıcı gösterge — mevcut dar `debt_to_equity` ile BİRLİKTE gösterilir, AYRI eşiklendirilmez (kaba: <1 güçlü, 1-2 orta, >2 zayıf — Buffett'ın hazine-hissesi-düzeltmesiz "ham" versiyonu, ~0,80 altı finansal kuruluş-dışı şirketlerde "dayanıklı avantaj olasılığı yüksek" [FORMÜL-17] EŞİĞİNE YAKLAŞTIRILMIŞ kaba bant) | 02/FORMÜL-16, İLKE-30 — "Toplam Yükümlülük/Özkaynak" (ticari borç+tahakkuk+ertelenmiş vergi DAHİL) mevcut dar `debt_to_equity`'den (SADECE finansal borç) YAPISAL OLARAK FARKLI bir soruya cevap verir (00_sentez.md §2.3: üç farklı "borç/özkaynak" kavramı var, hepsi meşru). |
| Merton Temerrüt Olasılığı (EDF) | %10 | Düşük EDF (≤%1-2) güçlü, orta (%2-10) izlenmeli, yüksek (>%10) risk sinyali (kaba bant, Damodaran Tablo 17.1 kredi notu-temerrüt eşleşmesiyle KABACA hizalı: BBB 10y kümülatif %4,27, B 10y %32,75) | 03/İLKE-441-444, FORMÜL-171/172 — Merton'un opsiyon-teorik özkaynak çerçevesi; **mevcut `merton.py` modülü ZATEN kodda var, sadece skorlama motoruna BAĞLANMASI gerekiyor** (BAYRAK-79, kitap genelinde tespit edilen en düşük maliyetli/en yüksek etkili bulgu). Veri yoksa (Merton hesaplanamıyorsa — fiyat oynaklığı serisi eksikse) bileşen ATLANIR, ağırlığı diğerlerine dağıtılır. |

**Toplam: %100.**

**Doğrudan skorlanmayan, kart notu/uyarı olarak eklenen bulgular:**

| Bulgu | Tetikleme koşulu | Kaynak |
|---|---|---|
| Sıkıntı sinyali (BAYRAK-76) | F/K veya PD/DD `None` AMA FD/FAVÖK veya FD/Hasılat geçerli | 03/İLKE-435 |
| Derin sıkıntı/opsiyon karakteri (BAYRAK-83) | `equity<0` | 03/İLKE-441-442 |
| Nakit Yakma Oranı | `ebitda<0` | 03/FORMÜL-164 |
| Faiz Karşılama Oranı yer tutucu | HER ZAMAN (veri eksik) | 01/FORMÜL-18, 02/FORMÜL-05, 03/Tablo 2.4 — eşik tablosu HAZIR tutulur (bkz. aşağı), veri gelince DOĞRUDAN skorlanan bileşene YÜKSELTİLİR |

**Faiz Karşılama Oranı — HAZIR eşik tablosu (veri gelene kadar UYGULANAMAZ,
sadece belgelenir):**

| Sektör | Ort.-7-yıl / En-kötü-yıl | Kaynak |
|---|---|---|
| Sanayi | 7x / 5x | 01/FORMÜL-18 |
| Perakende | 5x / 4x | 01/FORMÜL-18 |
| Kamu hizmeti | 4x / 3x | 01/FORMÜL-18 |
| Tüketici ürünleri (Buffett üst sınır) | <%15 (Faiz Gideri/Faaliyet Kârı) | 02/FORMÜL-05 |
| Damodaran sentetik kredi notu (>12,5 AAA … <0,5 D) | Tablo 2.4, 14 kademe | 03/Tablo 2.4 |

---

## Sektör ayarlaması

1. **Banka/sigorta/finansman:** Kaldıraç (Net Borç/FAVÖK) ve Toplam
   Yükümlülük/Özkaynak KAVRAMSAL OLARAK UYGULANAMAZ (02/İLKE-31: bankalar
   iş modeli gereği ~10:1 kaldıraçla NORMAL çalışır) — bu şablonlarda
   GÜVENLİK merceği `özkaynak_aktif_orani` (zaten CAMELS-esinli
   `scorer.CONFIG["banka"]` içinde MEVCUT, "Capital Adequacy" ruhuna
   uygun) + Piotroski BENZERİ bir finansal sağlık taraması (bankalar için
   henüz YOK, iskelet) ile ÇALIŞIR. Ağırlıklar bu iki mevcut/kısmi
   bileşene yeniden dağıtılır.
2. **Sektöre göreli kaldıraç kıyası (n≥5):** Kaldıraç mutlak eşiği HER
   ZAMAN birincil kalır (Moody's/S&P bantları EVRENSELDİR, ülke/sektör
   ayrımı yapmaz — SCORING_METHODOLOGY.md'de zaten bu gerekçeyle "sanayi"
   ve "abd_sanayi" AYNI bırakıldı). Sektör-göreli bağlam SADECE bir
   İKİNCİL not olarak eklenebilir ("bu kaldıraç [ust_sektor] medyanının
   üstünde/altında") — mutlak taban/tavan DEĞİŞMEZ (persona kural 3(c):
   sektör toptan kötü kaldıraçlı olsa bile "sektörünün en iyisi" mutlak
   yüksek GÜVENLİK puanı ALAMAZ).

---

## Kenar durumlar

- **Cari Oran çelişkisi (Graham ≥2,0 ZORUNLU vs Buffett <1 dayanıklı-
  avantajlı şirkette NORMAL, 00_sentez.md §2.4):** ÇÖZÜLMEZ, ama
  YORUMLANIR: Graham'ın eşiği BU mercekte (GÜVENLİK/muhafazakarlık
  sinyali) mevcut sürekli enterpolasyonla (`_seviye_trend_skoru`)
  KORUNUR — cari oran<1 DÜŞÜK GÜVENLİK puanı üretmeye DEVAM EDER. AMA
  kart, KALİTE merceğinin (bkz. `spec_mercek_kalite.md`) o dönemki
  FAVÖK marjı/Nakit Kâr Kalitesi bileşenleri GÜÇLÜYSE, "düşük cari oran
  BU şirkette Buffett'ın işaret ettiği türden — istikrarlı/güçlü kazanç
  gücü nedeniyle düşük likidite yastığı ihtiyacı azalmış olabilir; GÜVENLİK
  puanını KALİTE puanıyla BİRLİKTE okuyun" NİTEL notunu EKLER — GÜVENLİK
  bileşeninin SAYISI DEĞİŞMEZ, sadece BAĞLAM eklenir (iki mercek AYRI
  AYRI gösterilir, kullanıcı ikisini BİRLİKTE yorumlar — `temel-analiz-
  cercevesi` skill madde 4'ün TAM UYGULAMASI).
- **Nakit pozisyonu çelişkisi (Graham/Zweig "fazla nakit=verimsizlik" vs
  Buffett "nakit kraldır", 00_sentez.md §2.7):** ÇÖZÜLÜR — Buffett'ın
  vurgusu KRİZ DAYANIKLILIĞI (GÜVENLİK ekseni, BURADA yaşar: yüksek nakit
  Kaldıraç bileşenini [net borç negatife döner] otomatik 10 puana taşır,
  mevcut scorer.py davranışı KORUNUR), Graham/Zweig'in eleştirisi SERMAYE
  VERİMLİLİĞİ (DEĞER/KALİTE ekseni, `spec_mercek_kalite.md`'de ROE/ROA
  bileşenlerinde DOLAYLI olarak yakalanır: aşırı nakit biriktiren ama
  büyümeyen şirket düşük Marjinal ROE üretir). AYNI ham veri (`cash`) İKİ
  mercekte ZIT işaretlerle KULLANILIR — bu `temel-analiz-cercevesi` madde
  7'nin (çift sayma denetimi) SOMUT test vakasıdır, `spec_bilesik_skor.
  md`'de NOT olarak işaretlenir.
- **Faiz karşılama oranı eksikliğinin Merton ile KISMİ telafisi:** Merton
  EDF (`merton.py`) YAKLAŞIK bir vekildir — kitaptaki interest coverage
  formülünün BİREBİR YERİNE GEÇMEZ (farklı girdi: hisse fiyat oynaklığı +
  borç yüzü değeri, BLACK-SCHOLES tersine mühendislik), ama AYNI SORUYA
  ("bu firma temerrüde ne kadar YAKIN") CEVAP verir. Kart, Merton EDF
  bileşenini "sentetik/dolaylı temerrüt göstergesi (faiz karşılama oranı
  verisi eksikliği nedeniyle)" notuyla SUNAR — kitabın kendi formülüyle
  KARIŞTIRILMAMASI için AÇIKÇA farklı bir etiket ("Merton EDF") kullanılır.
- **Negatif FAVÖK'te Kaldıraç bileşeni:** `net_debt_to_ebitda` tanımsız
  (payda negatif) — mevcut `calculator.py` davranışı `None` DÖNER, bileşen
  ATLANIR; BU durumda Nakit Yakma Oranı (YENİ) DEVREYE GİRER (aynı
  senaryonun ALTERNATİF bir okuması, ÇAKIŞMAZ çünkü ikisi FARKLI koşullarda
  aktif: Kaldıraç FAVÖK>0 iken, Nakit Yakma FAVÖK<0 iken).
- **Merton verisi yoksa (fiyat oynaklığı serisi eksik/yeni halka arz):**
  bileşen `None`, ağırlığı diğer 4 bileşene ORANTISAL dağıtılır (mevcut
  genel mekanizma).
- **Piotroski <5 kriter değerlendirilebiliyorsa:** Mevcut `fundamental_
  screens.py` davranışı KORUNUR — `band=None`, GÜVENLİK merceğindeki F-
  Skoru bileşeni de bu durumda `None` döner (Kural 3: çok az kriterle
  yorum YAPILMAZ).
- **Banka/finansman şirketlerinde Piotroski:** Greenblatt'ın kendi kapsam
  dışı bırakmasıyla TUTARLI olarak Piotroski de SADECE BIST XI_29 sanayi
  için hesaplanır (mevcut modül kısıtı) — bu şablonlarda F-Skoru bileşeni
  YAPISAL OLARAK YOK sayılır (None değil, "bu şirket türünde
  uygulanamaz").

---

## Test senaryoları

1. **THYAO (BIST sanayi, dönemsel yüksek kaldıraç):** Net Borç/FAVÖK
   muhtemelen orta-yüksek bandda (havayolu sektörü tipik olarak
   sermaye-yoğun) → Kaldıraç bileşeni orta-düşük; Cari Oran havayolu
   sektöründe genelde <1,5 (işletme sermayesi döngüsü farklı) → Bilanço
   Kalitesi bileşeni de DÜŞÜK olabilir; KALİTE merceğindeki güçlü ROE ile
   BİRLİKTE okunmalı (Buffett istisna notu tetiklenir).
2. **Negatif özkaynaklı bir BIST/NASDAQ şirketi:** `pb_ratio=None`, BAYRAK-
   83 etiketi ("derin sıkıntı/opsiyon karakteri") GÖRÜNÜR; Kaldıraç ve
   Bilanço Kalitesi bileşenleri (özkaynak/varlık negatif) YAPISAL OLARAK
   çok DÜŞÜK puan üretir — GÜVENLİK skoru muhtemelen RİSKLİ bandında.
3. **F/K ve PD/DD hesaplanamayan ama FD/FAVÖK geçerli bir şirket:**
   BAYRAK-76 notu TETİKLENİR, kart "sınırlı çarpan seti, sıkıntı sinyali
   olabilir" der; GÜVENLİK bileşenleri (Kaldıraç, Piotroski) bu durumu
   BAĞIMSIZ olarak zaten YAKALAMALIDIR (çapraz doğrulama — eğer
   BAYRAK-76 tetiklenip Kaldıraç/Piotroski YİNE DE "güçlü" çıkıyorsa, bu
   bir TUTARSIZLIK sinyalidir, kartta İŞARETLENMELİDİR).
4. **Merton bağlantısı kurulduktan SONRA (mimari değişiklik uygulandığında)
   yüksek EDF'li bir şirket:** Diğer GÜVENLİK bileşenleri (özellikle
   Kaldıraç) İLE Merton EDF'nin AYNI YÖNDE işaret edip ETMEDİĞİ test
   edilmeli — büyük SAPMA varsa (ör. düşük kaldıraç ama yüksek EDF, fiyat
   oynaklığı kaynaklı) kart bunu "piyasa fiyat oynaklığı, bilanço
   verisinden DAHA YÜKSEK risk fiyatlıyor" notuyla YANSITMALIDIR.

---

## Uygulama notu (izlenebilirlik, çift-sayma ve öncelikli mimari değişiklik)

- **En yüksek öncelikli, EN DÜŞÜK maliyetli somut değişiklik:**
  `src/analysis/merton.py::compute_merton_dd_edf()` PROJENİN HİÇBİR
  yerinde ÇAĞRILMIYOR (grep ile doğrulandı, bkz. 00_sentez.md BAYRAK-79/
  80 orijinal kaynağı 03_damodaran_degerleme.md Kısım 9). Bu spec'in
  GÜVENLİK merceğine Merton EDF bileşenini (%10 ağırlık) EKLEYEBİLMESİ
  için TEK gereken şey `scorer.py`'ye bu fonksiyonu ÇAĞIRAN bir
  orkestrasyon adımıdır — SIFIR yeni veri, SIFIR yeni fetcher. Bu, spec
  dışı bir KODLAMA görevidir ama spec seviyesinde EN YÜKSEK öncelikli
  "quick win" olarak işaretlenir.
- **Piotroski ile Kaldıraç arasındaki KISMİ örtüşme:** Piotroski'nin 5.
  kriteri ("Uzun Vadeli Kaldıraç Azaldı") kaldıraç YÖNÜNÜ (azalıyor mu)
  ölçer, scorer'ın Kaldıraç bileşeni SEVİYEYİ (ne kadar yüksek) ölçer —
  FARKLI sorular (yön vs seviye), çift sayma SAYILMAZ, ama `spec_bilesik_
  skor.md`'de bir KORELASYON NOTU olarak işaretlenir.
- **Cari Oran'ın İKİ mercekte GÖRÜNMESİ:** Bilanço Kalitesi (BURADA,
  GÜVENLİK) SEVİYE ölçer; Piotroski'nin 6. kriteri de cari oranın YoY
  YÖNÜNÜ ölçer — AYNI ham veri (`current_ratio`), FARKLI SORU (seviye vs
  yön), TEK mercekte (GÜVENLİK) toplanmıştır, ÇİFT SAYMA riski YOKTUR
  (ikisi zaten AYNI merceğin İÇİNDE, birleşik ağırlığa KATILIRLAR).
