# Quant Denetim 01 — Faz 3a Spec'leri (Değer/Kalite/Büyüme/Güvenlik/Bileşik Skor)

**Kapsam:** `docs/spec/spec_mercek_deger.md`, `spec_mercek_kalite.md`,
`spec_mercek_buyume.md`, `spec_mercek_guvenlik.md`, `spec_bilesik_skor.md`
(commit f3f63b9, taslak/onay bekliyor) + bu spec'lerin dayandığı mevcut kod
(`src/analysis/scorer.py`, `valuation.py`, `calculator.py`, `fundamental_screens.py`).
Referans: `bilgi-bankasi/00_sentez.md`, `.claude/skills/quaxis-mimari/SKILL.md`,
`.claude/skills/temel-analiz-cercevesi/SKILL.md`.

**Yöntem:** 6 boyut (sayısal kararlılık, birim tutarlılığı, monotonluk, çift
sayma, küçük sektör davranışı, eksik veri yeniden dağıtımı) altında spec
metni + spec'in "aynen taşınır" dediği mevcut kod BİRLİKTE okunarak
denetlendi. Kod düzeltmesi burada YAPILMADI — bulgular kod-gelistirici'ye
devir için yazıldı. Kalibrasyon iddiaları `scripts/kalibrasyon_v2.py`
GERÇEKTEN çalıştırılarak (DB'deki 202 tickerlık gerçek örneklem üzerinde)
doğrulandı — aşağıdaki her KRİTİK bulgunun yanında, mümkün olduğunda,
scriptin ürettiği GERÇEK sayı verilmiştir (bkz. dosya sonu GÖREV 2 için
tam çıktı özeti).

---

## ÖZET — KRİTİK bulgular (hızlı tarama için)

| # | Başlık | Dosya/Bölüm | Kalibrasyonla doğrulandı mı? |
|---|---|---|---|
| K1 | `_seviye_trend_skoru`'nun "bozuluyor" dalında ~5+ puanlık skor uçurumu (cliff) — trend işareti sıfırı geçtiği an sert sıçrama; ayrıca bant sınırlarında (`guclu_esik`/`orta_esik`) ~1 puanlık ek sıçramalar | `scorer.py::_seviye_trend_skoru` — TÜM 4 mercek spec'i bu motoru "AYNEN" genişletiyor | Matematiksel ispat (kod okuması), ayrıca v1 skor dağılımı kalibrasyonda üretildi |
| K2 | NCAV/Net-Net iskonto formülü sıfıra/negatife bölünebilir, işareti öngörülemez şekilde döner | `spec_mercek_deger.md` §Formüller-4 | **EVET** — BİST sanayi'de %52,1, NASDAQ sanayi'de %71,4 şirkette payda ≤0 |
| K3 | "Toplam Yükümlülük/Özkaynak" (geniş tanım) — negatif özkaynakta işaret tersine döner (distressed şirket "GÜÇLÜ" görünür) + spec metni kendi içinde çelişkili | `spec_mercek_guvenlik.md` §Formüller-4, §Eşikler tablosu | **EVET** — BİST sanayi'de 4/167 şirket (canlı örnek: negatif oran üretiyor) |
| K4 | Oran-tipi (x-katı, YÜZDE OLMAYAN) yeni bileşenler `_seviye_trend_skoru`/`format_percent_tr` ile beslenirse "1,0" "%1,0" olarak YANLIŞ gösterilir | `spec_mercek_kalite.md` §Formüller-6, `spec_mercek_guvenlik.md` §Formüller-4 | Kod okuması (statik) |
| K5 | Marjinal ROE: payda (`equity_t-1`) küçük/negatif olduğunda oran patlar; BÜYÜME spec'inde eşiği SAYISAL OLARAK tanımsız | `spec_mercek_buyume.md` §Formüller-3, §Eşikler tablosu | Kod okuması + negatif özkaynak oranı (K3 ile aynı kanıt kümesi) |

Aşağıda tüm bulgular ayrıntılı biçimde, önem sırasıyla listelenir.

---

## KRİTİK

### K1. `_seviye_trend_skoru`'da trend-işareti sınırında sert skor uçurumu (cliff)

**Konum:** `src/analysis/scorer.py::_seviye_trend_skoru` (satır 394-447) —
mevcut ÜRETİM kodu. Bu fonksiyon 4 yeni mercek spec'inin TÜMÜNDE ("MEVCUT
motor AYNEN kullanılır") çok daha fazla bileşene (Brüt Marj, ROA, Nakit
Kâr Kalitesi'nin band'ı vb.) genişletilerek taşınıyor — yani bug'ın yüzey
alanı v2 ile ÇOĞALIYOR.

**Arıza senaryosu (somut sayılarla):** FAVÖK marjı bileşeni (`nakit_uretimi`
cfg: `guclu_esik=20, orta_esik=10, tavan=30`). Bir şirketin FAVÖK marjı
%40 (güçlü bandın çok üstünde):

- `trend_puan = 0.00` (tam yatay) → "seviye>guclu_esik" dalı:
  `_asymptote_to(40-20=20, 30-20=10, 8, 10)` → `t=20/30=0,667` →
  **skor ≈ 9,33**.
- `trend_puan = -0.01` (yüzde puan bazında GÖZLE GÖRÜLMEZ, negligible bir
  bozulma) → "bozuluyor" dalı devreye girer:
  `_lerp_score(40, taban=0, orta_esik=10, 0, 4)` → seviye=40 >> orta_esik=10
  → `t` 1'e kırpılır → **skor = 4,00**.

Yani trend_puan'ın işareti **-0,01 ile +0,00 arasında** değişince skor
**9,33'ten 4,00'e** (RİSKLİ/KARIŞIK sınırına) düşüyor — ~5,3 puanlık bir
uçurum, girdideki değişime KIYASLA orantısız. Bu, persona talimatının
açıkça sorduğu "keskin basamak (cliff) etkisi" sorusuna somut bir EVET
cevabıdır.

**İkincil, daha küçük ama sistemik sıçramalar:** `_lerp_score` bantları
`[0,4]`, `[5,7]`, `[8,10]` şeklinde ARALARINDA BOŞLUK bırakacak biçimde
tanımlı (4→5 ve 7→8 arası atlanıyor). `seviye == orta_esik` sınırında
skor 4'ten 5'e, `seviye == guclu_esik` sınırında 7'den 8'e SIÇRIYOR
(süreklilik yok, `_asymptote_to`'nun kendi docstring'inin vaat ettiği
"eşikte süreklilik, sıçrama yok" ilkesi SADECE `guclu_esik`'in KENDİSİNDE
değil, `orta_esik`↔`guclu_esik` ARA sınırında İHLAL ediliyor).

**Kalibrasyonla dolaylı doğrulama:** Kalibrasyon scripti BİST sanayi
örnekleminde v1 Radar Skoru'nu (Değerleme bileşeni hariç, veri yoksa
None) hesapladı — dağılım `min=0,99 / p25=3,91 / medyan=4,93 / p75=6,23 /
p90=7,44 / max=9,36`, [7,0-8,5] aralığında sadece %9,0 yığılma var. Bu,
BİST örnekleminde şu an ciddi bir yığılma OLMADIĞINI gösteriyor (v1'in
kendisi zaten sürekli enterpolasyon kullandığı için) — AMA NASDAQ
örnekleminde (n=18) dağılım ÇOK DAHA SIKIŞIK ve YUKARI KAYIK:
`p25=6,03 / medyan=7,49 / p75=9,08 / p90=9,47` — yani örneklemin
YARISINDAN FAZLASI 6-9,5 aralığında toplanıyor, ayrıştırma gücü zayıf.
Bu, K1'in öngördüğü "trend sıfırına yakın kümelenmiş şirketlerde ani
sıçramalar" riskinin NEDEN önemli olduğunu somut biçimde destekliyor —
V2'de Brüt Marj/ROA gibi YENİ bileşenler eklendiğinde bu motor DAHA FAZLA
kullanılacağı için, mevcut NASDAQ-tipi sıkışma riski BÜYÜYEBİLİR.

**Önerilen düzeltme:** `bozuluyor` dalını sert (`trend_puan<0` ikili eşik)
yerine trend büyüklüğüne göre YUMUŞAK bir ceza çarpanına çevirin — örn.
`ceza_carpani = _lerp_score(trend_puan, -X, 0, 0.5, 1.0)` (trend_puan -X
ile 0 arasında iken skoru %50-%100 arasında ölçekleyen sürekli bir
fonksiyon) ve bunu seviyeye göre hesaplanan "normal" skorla ÇARPARAK
uygulayın — böylece trend_puan=0 civarında SÜREKLİLİK garanti edilir.
Ayrıca `[0,4]-[5,7]-[8,10]` bant boşlukları `[0,4]-[4,7]-[7,10]` gibi
UÇLARI ÇAKIŞAN aralıklara çevrilmeli (her iki komşu bandın sınır
noktasında AYNI değeri üretmesi matematiksel süreklilik için ZORUNLU).

**Doğrulama yöntemi:** Yukarıdaki kalibrasyon zaten uygulandı; ek olarak
`_seviye_trend_skoru`'nun trend_puan=-0,001 ile +0,001 arasındaki fark
için maksimum |Δskor| değerini test eden bir birim testi (mevcut motorun
TÜM `guclu_esik`/`orta_esik` kombinasyonları için) eklenmesi önerilir.

---

### K2. NCAV / Net-Net iskonto formülünde sıfıra/negatife bölünme

**Konum:** `spec_mercek_deger.md` §Formüller-4:

```
net_isletme_sermayesi = current_assets - total_liabilities
net_net_iskonto_pct = (market_cap - net_isletme_sermayesi) / net_isletme_sermayesi * 100
```

**Arıza senaryosu — KALİBRASYONLA DOĞRULANDI:** Script, DB'deki 202
tickerlık gerçek örneklemde `net_isletme_sermayesi <= 0` oranını
hesapladı:

- **BİST sanayi (XI_29): 86/165 şirket (%52,1)**
- **NASDAQ sanayi (US_GAAP): 15/21 şirket (%71,4)**

Yani örneklemin YARISINDAN FAZLASINDA bu formülün paydası SIFIR VEYA
NEGATİF — bu, "nadir bir kenar durum" DEĞİL, EVRENİN ÇOĞUNLUĞUNU
etkileyen SİSTEMİK bir risktir. Spec, formülü SADECE "piyasa değeri
NCAV'ın altında" senaryosunda kullanılacağını test senaryosunda ima
ediyor ama FORMÜLÜN KENDİSİNDE `net_isletme_sermayesi > 0` KOŞULU YOK —
kod-geliştirici formülü OLDUĞU GİBİ implemente ederse, örneklemin
yarısından fazlasında sıfıra bölme hatası veya işareti öngörülemez bir
sonuç üretir.

**Önerilen düzeltme:** Formülün başına AÇIKÇA `if net_isletme_sermayesi <=
0: net_net_iskonto_pct = None (bonus tetiklenmez)` guard'ı eklenmeli —
zaten spec'in kendi ruhu ("SADECE hisse NCAV'ın ALTINDA fiyatlanıyorsa
devreye girer, aksi halde 0 katkı") bunu ima ediyor ama FORMÜL METNİNDE
yazılı değil.

**Doğrulama yöntemi:** Yukarıdaki kalibrasyon zaten uygulandı (bkz.
GÖREV 2 tam çıktısı) — düzeltme kod'a uygulandıktan sonra aynı script
`net_net_iskonto_pct is None` oranının bu payda≤0 oranıyla (%52,1/%71,4)
BİREBİR eşleştiğini doğrulayan bir regresyon kontrolü olarak yeniden
kullanılabilir.

---

### K3. "Toplam Yükümlülük/Özkaynak" (geniş tanım) — işaret tersine dönmesi + spec içi çelişki

**Konum:** `spec_mercek_guvenlik.md` §Formüller-4 ve §Eşikler tablosu.

**(a) İşaret sorunu — KALİBRASYONLA DOĞRULANDI:** `toplam_yukumluluk_
ozkaynak = (short_term_liabilities + long_term_liabilities) / equity`.
Kalibrasyon scripti BİST sanayi örnekleminde **4/167 şirketin** negatif
özkaynağa sahip olduğunu ve bu şirketlerde geniş tanımlı oranın (kod
üzerinde birebir aynı formülle hesaplandığında) `min=-39,70` gibi
BÜYÜK NEGATİF değerler ürettiğini gösterdi (tüm örneklem dağılımı:
`min=-39.70 / p10=0.10 / medyan=0.60 / p90=2.41`). Bant tablosu "<1
güçlü, 1-2 orta, >2 zayıf" — `-39,70` gibi bir değer `<1` koşulunu
sağladığı için YANLIŞLIKLA "GÜÇLÜ" bandına düşer. Yani **negatif
özkaynaklı, derin sıkıntıdaki bir şirket bu bileşende en YÜKSEK puanı
alır** — GÜVENLİK merceğinin amacına doğrudan aykırı bir işaret/
monotonluk hatası. Spec'in "Negatif özkaynak" kenar durumu bölümü BU
YENİ bileşeni AÇIKÇA kapsamıyor.

**(b) Spec içi çelişki:** Aynı bölüm önce "İKİNCİL/tamamlayıcı gösterge...
**AYRI EŞİKLENDİRİLMEZ**" diyor, hemen ardından somut bir bant tablosu
(`<1 güçlü, 1-2 orta, >2 zayıf`) VE ağırlık tablosunda **%15 ağırlık**
veriyor. Bir bileşen ya (i) 0-10 skora dönüştürülüp `_agirlik_dagit_ve_
hesapla`'nın %15'lik payına girer (bu durumda "eşiklendirilmez" ifadesi
YANLIŞ), ya (ii) hiç skorlanmaz ve sadece bilgi notu olarak gösterilir
(bu durumda ağırlık tablosundaki %15 satırı YANLIŞ, diğer 4 bileşenin
ağırlığı YENİDEN dağıtılmalı). Bu İKİ YORUM birbirini dışlar.

**Önerilen düzeltme:** (a) `equity <= 0` durumunda bileşen `None` dönmeli
(diğer negatif-özkaynak guard'larıyla TUTARLI); (b) spec metni netleştirilmeli
— eğer %15 ağırlık gerçekten uygulanacaksa "ayrı eşiklendirilmez" ifadesi
kaldırılıp somut 0-10 dönüşüm formülü yazılmalı.

**Doğrulama yöntemi:** Yukarıdaki kalibrasyon zaten uygulandı; kod
düzeltmesi sonrası `equity<0` olan 4 BİST şirketinin bu bileşende
`None` döndüğünü (10 veya rastgele bir yüksek puan DEĞİL) doğrulayan
birim testi eklenmeli.

---

### K4. Oran-tipi (x-katı) yeni bileşenlerde birim/format karışıklığı riski

**Konum:** `spec_mercek_kalite.md` §Formüller-6 (Nakit Kâr Kalitesi,
`operating_cash_flow/net_income`, ~1,0 civarı bir ORAN) ve
`spec_mercek_guvenlik.md` §Formüller-4 (Toplam Yükümlülük/Özkaynak,
~0,5-2,0 civarı bir ORAN, bkz. K3) — ikisi de YÜZDE değil, ÇIPLAK ORAN
(x-katı) olarak tanımlanmış ve eşik tabloları da (`≥1,0 güçlü`, `<1 güçlü`
gibi) bu şekilde yazılmış.

**Arıza senaryosu:** Mevcut kodda `_seviye_trend_skoru` fonksiyonu
`seviye` parametresini `format_percent_tr(seviye)` ile (YÜZDE varsayarak)
metne döker (örn. "FAVÖK marjı %20,0"). Eğer bir kod-geliştirici bu YENİ
oran-tipi bileşenleri (nakit kâr kalitesi ~1,0, toplam yükümlülük/özkaynak
~0,8) DOĞRUDAN bu fonksiyona beslerse, ekranda **"Nakit Kâr Kalitesi
%1,0"** gibi YANLIŞ bir metin üretilir (gerçek anlamı "1,0 katı" / "%100"
olmalı — TAM DA persona talimatının sorduğu "0.15 mi %15 mi" karışıklığının
bir varyantı).

Mevcut kod zaten bu ayrımı BİLİYOR: `net_debt_to_ebitda`/`debt_to_equity`
gibi x-katı metrikler `_seviye_trend_skoru` yerine ÖZEL yazılmış
`_skor_kaldirac` gibi fonksiyonlarla, `_num_str` (ham sayı, "2,3x" tarzı)
formatlanarak skorlanıyor — `format_percent_tr` HİÇ kullanılmıyor. Ama
KALİTE/GÜVENLİK spec'leri bu iki yeni bileşen için "MEVCUT motor
kullanılır" demiyor, formülü veriyor ama HANGİ fonksiyon ailesiyle
(yüzde-varsayan `_seviye_trend_skoru` mı, x-katı-varsayan özel bir
fonksiyon mu) skorlanacağını AÇIKÇA belirtmiyor.

**Önerilen düzeltme:** Her iki spec'te bu iki bileşenin yanına AÇIKÇA
"YÜZDE DEĞİL, x-katı oran — `_skor_kaldirac` ailesindeki gibi özel
formatlanmalı, `format_percent_tr`/`_seviye_trend_skoru` ile DOĞRUDAN
beslenmemeli (aksi halde 1,0 → '%1,0' yanlış metni üretilir)" notu
eklenmeli.

**Doğrulama yöntemi:** Birim testi — nakit kâr kalitesi=1,0 için üretilen
`reasoning_tr` metninin "%1,0" DEĞİL "1,0x" veya "%100" içerdiğini
doğrulayan bir regresyon testi.

---

### K5. Marjinal ROE — payda instabilitesi + tanımsız eşik

**Konum:** `spec_mercek_kalite.md` §Formüller-4 (veri kaynağı olarak) ve
`spec_mercek_buyume.md` §Formüller-3 + §Eşikler tablosu (SKORLANAN
bileşen, %20 ağırlık).

```
marjinal_roe_pct = (net_income_t - net_income_t-1) / equity_t-1 * 100
```

**(a) Sayısal kararlılık:** BÜYÜME spec'in kendisi "Kenar Durumlar"da bu
oranın "AŞIRI OYNAK olabilir (payda küçükse oran patlayabilir)" olduğunu
KABUL EDİYOR ama tek önlem olarak "TTM bazlı pencere" öneriyor — bu,
`equity_t-1`'in NEGATİF olmasını (K3'te tespit edilen 4/167 BİST şirketi
İLE AYNI kanıt kümesi — bu şirketlerin geçmiş dönemlerinde de negatif
özkaynak periyotları büyük olasılıkla vardır) ÇÖZMEZ. `equity_t-1 <= 0`
durumunda sonuç işaretsiz/anlamsızdır. Ne KALİTE ne BÜYÜME spec'i bu
durumda `None` dönülmesi gerektiğini AÇIKÇA yazmıyor.

**(b) Eşik belirsizliği:** BÜYÜME spec'inin ağırlık tablosunda bu
bileşenin eşiği: *"Marjinal ROE: güçlü≥standart ROE'nin ÜSTÜNDE, zayıf≥
standart ROE'nin ALTINDA (kaba, standart ROE'ye GÖRELİ bir kıyas, **mutlak
eşik henüz kalibre edilmedi**)"*. Bu, `_seviye_trend_skoru`'nun beklediği
somut `guclu_esik`/`orta_esik`/`tavan` sayılarını VERMİYOR — kod-
geliştirici bu sayıları KENDİSİ UYDURMAK zorunda kalır, ki bu doğrudan
`quaxis-mimari` anayasa madde 4'ü ("her eşik/ağırlık kaynaklı gerekçeyle
belgelenir") ve `temel-analiz-cercevesi` madde 1'i ("izlenebilirlik zinciri
zorunlu") ihlal eder. %20 ağırlık taşıyan bir bileşenin matematiksel
tanımı EKSİK.

**Önerilen düzeltme:** (a) `equity_t-1 <= 0` → `marjinal_roe_pct = None`
guard'ı eklensin. (b) Somut bir eşik formülü tanımlanmalı — örn.
`fark_puan = marjinal_roe_pct - standart_roe_pct` üzerinden bir
`_lerp_score(fark_puan, -X, +X, 0, 10)` gibi SÜREKLİ, standart ROE'ye
göreli ama SAYISAL SINIRLARI belli bir fonksiyon (X'in kendisi ayrı bir
kaynakla gerekçelendirilmeli — örn. 03/İLKE-85,86'daki Goldman Sachs
örneğinin büyüklüğü referans alınabilir) — "henüz kalibre edilmedi" ifadesi
spec onaylanmadan ÖNCE giderilmeli.

**Doğrulama yöntemi:** Kalibrasyon scripti ROE dağılımını zaten üretti
(BİST sanayi: `min=-222,78 / p25=-7,11 / medyan=3,01 / p75=13,37 /
max=694,23` — uç değerlerin BÜYÜKLÜĞÜNE dikkat: bu, standart ROE'nin
KENDİSİNİN bile küçük özkaynak paydası nedeniyle patladığının kanıtı,
Marjinal ROE'nin ek bir fark alma işlemiyle DAHA DA oynak olacağını
gösterir) — script'e Marjinal ROE'nin kendisini (iki ardışık dönem
gerektirdiği için ek bir sorgu ile) eklemek, X'in kalibrasyonu için bir
sonraki adım olarak önerilir.

---

## YÜKSEK

### Y1. KALİTE banka/sigorta yeniden dağıtımı orantısal DEĞİL

**Konum:** `spec_mercek_kalite.md` §Sektör ayarlaması madde 1: *"Ağırlıklar
bu iki bileşene ORANTISAL yeniden dağıtılır (ROE %70, ROA %30 — banka
CONFIG'indeki mevcut göreli ağırlık oranı KORUNARAK)"*.

KALİTE merceğinin KENDİ nominal ağırlıkları ROE=%20, ROA=%5 (toplam
sanayi/abd_sanayi tablosunda). Bu ikisi arasında GERÇEK orantısal
dağılım `20/(20+5)=%80` ROE, `5/25=%20` ROA verir — spec'in yazdığı
`%70/%30` bu orandan FARKLI. Spec, kendi mercek-içi ağırlıklarını
kullanmak yerine TAMAMEN AYRI bir kaynaktan (scorer.py'nin `banka`
CONFIG'indeki `ozkaynak_karliligi`=%25 vs `aktif_karliligi`=%20 oranı,
ki bu da 25/45=%55,6 / %44,4 eder, %70/%30 DEĞİL) türetilmiş bir rakam
kullanıyor — üstelik bu ikinci kaynağın oranı BİLE %70/%30 vermiyor,
rakamın kendisi HANGİ hesaptan geldiği belirsiz.

**Önem:** `_agirlik_dagit_ve_hesapla`'nın "orantısal yeniden dağıtım"
ilkesi projenin ANAYASA maddesi (kural 3) — bu spec SESSİZCE (açık bir
"istisna" işareti KOYMADAN) bu ilkeyi ihlal ediyor.

**Önerilen düzeltme:** Ya (a) gerçek orantısal değeri (%80/%20) kullanın,
ya (b) %70/%30'u KORUMAK isteniyorsa bunun NEDEN bilinçli bir istisna
olduğu AÇIKÇA gerekçelendirilmeli.

**Doğrulama yöntemi:** Kod incelemesi — birim testi: banka şablonunda
ROA=None olduğunda ROE'nin efektif ağırlığının %100 olduğunu, ikisi de
mevcutken oranın spec'te YAZILI DEĞERLE eşleştiğini doğrulayan test.

---

### Y2. Sektöre Göreli Çarpan Konumu — MAD hesaplanıyor ama kullanılmıyor

**Konum:** `spec_mercek_deger.md` §Formüller-6 ve §Sektör ayarlaması
madde 2.

```
sektor_medyan_fk, sektor_mad_fk = robust_istatistik(...)
sapma_pct = (own_pe - sektor_medyan_fk) / sektor_medyan_fk * 100
```

Persona talimatı (ve spec'in kendi "Robust istatistik" başlığı) "medyan +
MAD" tabanlı bir robust z-skor vaat ediyor, ama VERİLEN formül SADECE
medyana göre düz YÜZDE SAPMA hesaplıyor — `sektor_mad_fk` hesaplanıyor
ama `sapma_pct` formülünde HİÇ KULLANILMIYOR.

**Kalibrasyonla ilgili gözlem:** BİST sanayi FAVÖK marjı dağılımı
`p10=-6,44` ile `p90=42,51` arası (çok geniş varyans) — böyle geniş
varyanslı bir metrikte düz yüzde-sapma, MAD-normalize edilmiş bir z-skora
kıyasla çok daha GÜRÜLTÜLÜ bir sinyal üretir; sektör alt kırılımlarında
(n küçükken) bu fark daha da belirginleşir.

**Önerilen düzeltme:** Ya formülü gerçek MAD-normalize edilmiş robust
z-skora çevirin (`z = (own_pe - medyan) / (1.4826 * MAD)`), ya da "robust
istatistik" başlığını "medyan sapması (MAD sadece winsorizasyon için
kullanılır)" olarak YENİDEN ADLANDIRIP beklentiyi netleştirin.

---

### Y3. Winsorizasyon (%5-95) küçük n'de fiilen etkisiz

**Konum:** `spec_mercek_deger.md` §Sektör ayarlaması madde 2.

**Kalibrasyonla doğrulandı:** Script'in Bölüm 1 çıktısı (aşağıya bakınız)
gerçek `(ust_sektor, sirket_turu)` gruplarının BÜYÜK ÇOĞUNLUĞUNUN n<5
(hatta n=0-1) olduğunu gösteriyor — n=5-9 aralığındaki gruplarda (örn.
BİST bankalar n=8, BİST sigorta n=4) %5-%95 winsorizasyonu PRATİKTE en
fazla 0-1 gözlemi etkiler.

**Önerilen düzeltme:** n<10 olan gruplarda winsorizasyonun neredeyse
etkisiz olduğu kod yorumunda AÇIKÇA belgelensin.

---

### Y4. Bileşik skor formülünde sıfıra bölme guard'ı YAZILI DEĞİL

**Konum:** `spec_bilesik_skor.md` §Formüller-1. Formülün kendisi (mevcut
`_agirlik_dagit_ve_hesapla` referansı olmadan okunduğunda) sıfıra bölme
riski taşıyormuş gibi görünüyor; pratikte güvenli çünkü Uygulama notu
mevcut fonksiyonu yeniden kullanmayı şart koşuyor — ama bu guard'ı
formülün YANINA da AÇIKÇA yazmak, "sıfırdan" implementasyon riskini
azaltır.

**Önerilen düzeltme:** Formülün altına "Σ(mercek_agirlik_i)=0 ise sonuç
hesaplanmaz, YETERSİZ VERİ dalına düşülür — guard `_agirlik_dagit_ve_
hesapla`'dan İTHAL edilir" notu eklensin.

---

### Y5. Amortisman/Brüt Kâr — payda instabilitesi + "yön tersine çevirme" mekanizması tanımsız

**Konum:** `spec_mercek_kalite.md` §Formüller-3.

```
amortisman_orani_pct = depreciation_amortization / gross_profit * 100
```

**(a) Kalibrasyonla ilgili gözlem:** Script, BİST sanayi örnekleminde
Brüt Kâr Marjı'nın (`gross_profit/revenue`) `min=-215,82` gibi DERİN
NEGATİF değerler alabildiğini gösterdi — yani `gross_profit`'in KENDİSİ
negatif olabilen bir şirket örneklemi GERÇEKTEN var; bu durumda
amortisman oranı işareti YANLIŞ döner (K1/K4 ailesiyle aynı sınıf risk).

**(b)** Spec, "düşük=iyi" için `_seviye_trend_skoru`'nun yönünün TERSİNE
ÇEVRİLDİĞİNİ" söylüyor ama fonksiyonun KENDİSİNDE böyle bir parametre
YOK — mekanizma tanımsız.

**Önerilen düzeltme:** (a) `gross_profit <= 0` → bileşen `None`. (b)
`_seviye_trend_skoru`'ya AÇIK bir "düşük=iyi" modu eklensin veya
`1/(1+oran)` gibi monotonik bir ön-dönüşüm spec'te AÇIKÇA yazılsın.

---

## ORTA

### O1. Nakit pozisyonu "çift sayma çözümü" iddiası ampirik olarak doğrulanmamış

`spec_bilesik_skor.md` ve `spec_mercek_guvenlik.md`, Graham/Zweig
"fazla nakit=verimsizlik" vs Buffett "nakit kraldır" çelişkisinin GÜVENLİK
(Kaldıraç, `cash` DOĞRUDAN girdi) ile KALİTE/BÜYÜME (Marjinal ROE, ROA —
DOLAYLI) arasında "çözüldüğünü" iddia ediyor. Ama KALİTE/BÜYÜME
bileşenleri `cash` ALANINI DOĞRUDAN kullanmıyor (Marjinal ROE=`net_income`/
`equity`, ROA=`net_income`/`total_assets`) — "aynı ham veri" iddiası
teknik olarak İMPRESİF değil, ÇÖZÜMÜN GERÇEKTEN "iptal ettiği" ampirik
olarak doğrulanmamış. v2 lens kodu tamamlandığında yüksek-nakit
şirketlerde Güvenlik (yüksek) ile Kalite'nin ROA/Marjinal-ROE
bileşenlerinin (düşük mü?) gerçek korelasyonu test edilmeli.

### O2. Paylaşılan ham girdilerin (ROE, EBIT) korelasyonu belgeleniyor ama sayısallaştırılmıyor

Persona görev tanımı "korelasyonu belgele VE AĞIRLIKTA HESABA KAT" diyor
— spec'ler SADECE belgeleme kısmını yapıyor. v2 lens kodu tamamlandıktan
sonra DEĞER/KALİTE/BÜYÜME mercek skorları arasındaki Pearson korelasyonu
GERÇEK örneklemde hesaplanmalı; yüksek korelasyon (>0,6) çıkarsa ağırlıklar
gözden geçirilmeli.

### O3. Nakit Yakma Oranı — hangi EBITDA'nın (çeyreklik mi TTM mi) kullanıldığı belirsiz

`spec_mercek_guvenlik.md` §Formüller-3: `cash/abs(ebitda)` — TTM mi tek
çeyrek mi belirtilmemiş, 4 kat fark yaratır. `ttm_ebitda` kullanılacaksa
AÇIKÇA yazılmalı, etiket "kaç YILDA nakit tükenir" olarak netleştirilmeli.

### O4. Sıkıntı sinyali/negatif özkaynak uyarılarının birden fazla mercekte tekrar tetiklenmesi

DEĞER spec'i BAYRAK-76/83'e "çapraz referans" veriyor, GÜVENLİK spec'i
aynı bayrakları BİRİNCİL üretiyor — kartta AYNI uyarının İKİ kez görünme
riski var, deduplikasyon kuralı yazılmamış (skor matematiğini etkilemez,
UX/tutarlılık notu).

---

## DÜŞÜK

### D1. Greenblatt EBIT'in iki merceğin payında ortak olması

DEĞER'in Kazanç Getirisi (`EBIT/FD`) ile KALİTE'nin ROC'unun (`EBIT/
Yatırılan Sermaye`) PAYI (EBIT) ortak — tanım olarak çift sayma değil ama
artık-korelasyon var, kalibrasyonda ölçülmeli.

### D2. PD/EFK tanım hatası düzeltmesi henüz kodda uygulanmamış

`spec_mercek_deger.md` zaten DOĞRU düzeltmeyi (`enterprise_value/
ttm_operating_profit`) öneriyor — spec hatası değil, izlenebilirlik notu.

### D3. Merton EDF ile Kaldıraç'ın farklı doğal ölçeklerde olması

Biri olasılık (%), diğeri x-katı oran — ikisinin de AYRI AYRI 0-10'a
dönüştürülmesi gerektiği AÇIKÇA yazılmamış, küçük bir netlik eksikliği.

---

## GÖREV 2 — Kalibrasyon çıktısı (tam özet)

`scripts/kalibrasyon_v2.py` yazıldı ve ÇALIŞTIRILDI (idempotent, SADECE
`SELECT` — DB'ye hiçbir yazma yapılmadı; `python scripts/kalibrasyon_v2.py`
ile tekrar çalıştırılabilir; `--with-price` bayrağı BİST için canlı F/K/
PD/DD çarpanlarını `isyatirim.fetch_latest_price()` ile ekler, ~170
istek × ~1,2 sn nedeniyle ayrı/uzun bir koşu gerektirir).

**Kapsam notu (dürüstlük ilkesi):** `Company` tablosunda 643 BİST +
~4352 NASDAQ satırı var, ama `FinancialPeriod` (gerçek mali tablo) verisi
olan SADECE **202 ticker** (180 BİST + 22 NASDAQ) mevcut — her ticker
sadece bir kullanıcı onu sorguladığında taranıyor, TOPLU bir doldurma
süreci YOK. Bu script o 202'lik GERÇEK örneklemi raporlar; "evrenin
TAMAMI" iddiası YAPILMAZ.

### 1. Sektör evreni — n<5 durumu (canlı doğrulama)

Script, `(piyasa, üst-sektör, şirket-türü)` üçlüsü bazında hem TOPLAM
Company kaydını hem GERÇEKTEN analiz edilmiş (n) alt kümeyi karşılaştırdı.
Öne çıkan bulgular:

- **BİST Enerji/sanayi: toplam evren 4, analiz edilmiş n=1** —
  `_ilerleme.md`'deki "n=4" iddiası TOPLAM evren için doğru, ama
  SEKTÖRE-GÖRELİ SKORLAMA için asıl geçerli sayı analiz edilmiş n=1'dir
  (n<5 kuralı yine devreye girer, ama gerekçe biraz farklı: n=4 bile
  yetersizken, gerçek veri n=1'e düşüyor).
- **BİST Sağlık/sanayi: toplam 4, analiz edilmiş n=1** — aynı desen.
- **BİST İletişim/sanayi: toplam 7, analiz edilmiş n=1.**
- **BİST sigorta: toplam 7, analiz edilmiş n=4** — n<5 sınırında.
- **NASDAQ tarafında NEREDEYSE TÜM gruplar n<5** (çoğu n=0) — Faz 2'nin
  NASDAQ SIC-zenginleştirmesi ve mali veri taraması İKİSİ DE henüz çok
  erken aşamada; NASDAQ için sektöre-göreli DEĞER/KALİTE/BÜYÜME
  bileşenleri PRATİKTE neredeyse HİÇ tetiklenmeyecek (evrensel eşiklere
  düşecek) — bu, spec'in "n<5 ise evrensel eşiğe düş" ilkesinin doğru
  tasarlandığını, ama NASDAQ tarafında bu istisnanın KURAL haline
  geleceğini gösteriyor.
- En kalabalık, sektöre-göreli skorlamanın ANLAMLI çalışacağı gruplar:
  BİST Ana Metaller ve Madencilik (n=44), BİST Sanayi (n=27), BİST
  Tüketici Döngüsel (n=18), BİST GYO (n=16), BİST Tüketici Temel (n=15).

### 2. Ham metrik dağılımları (202 ticker, fiyat gerektirmeyen)

| Metrik | BİST sanayi (n) | medyan | p10 | p90 | Not |
|---|---|---|---|---|---|
| ROE (%) | 159 | 3,01 | -26,70 | 24,85 | max=694,23 (uç değer — küçük özkaynak paydası) |
| Cari oran | 165 | 1,40 | 0,66 | 7,03 | %25,5'i <1 (Buffett-tipi bölge) |
| Borç/Özkaynak (dar) | 147 | 0,18 | 0,00 | 1,01 | |
| Net Borç/FAVÖK | 138 | 0,59 | -2,68 | 6,22 | |
| FAVÖK marjı (%) | 153 | 12,82 | -6,44 | 42,51 | |
| Brüt kâr marjı (%) | 159 | 19,71 | 2,53 | 83,69 | min=-215,82 (negatif brüt kâr VAR) |
| Net marj (%) | 159 | 2,06 | -63,83 | 29,91 | |
| Hasılat YoY (%, nominal) | 148 | 42,24 | -15,34 | 131,88 | yüksek enflasyon etkisi (nominal, reel düzeltme YOK) |
| ROA (YENİ, %) | 159 | 1,22 | -11,49 | 14,89 | |
| Toplam Yükümlülük/Özkaynak (YENİ) | 165 | 0,60 | 0,10 | 2,41 | min=-39,70 (K3'ün kanıtı) |

NASDAQ sanayi (n=22, küçük örneklem) genel olarak DAHA YÜKSEK ROE
(medyan %28,97), DAHA YÜKSEK FAVÖK marjı (medyan %34,92) ve DAHA DÜŞÜK
kaldıraç (Net Borç/FAVÖK medyan 0,25) gösteriyor — beklenen (büyük/
olgun teknoloji ağırlıklı bir alt küme, evrenin tamamını TEMSİL ETMEZ).

### 3. Eşik bandı sayımları (öne çıkanlar)

- **FAVÖK marjı (KALİTE):** BİST sanayi'de "düşük" bandı (%38,6) en
  kalabalık grup — mevcut kalibrasyonun BİST için "güçlü" (%33,3) ile
  neredeyse EŞİT büyüklükte olması, bandın AYRIŞTIRICI olduğunu (yığılma
  yok) gösteriyor.
- **ROE (KALİTE):** BİST sanayi'de %67,3 "zayıf" (<%10) — bu, ROE
  eşiğinin BİST bağlamında OLDUKÇA SIKI olduğunu, "güçlü" (%21,4) rozeti
  kazananın azınlıkta kaldığını gösteriyor (ayrıştırma gücü YÜKSEK, iyi).
- **Kaldıraç (GÜVENLİK):** BİST sanayi'de %61,6 "çok iyi" (<1x) — bu
  ORANIN yüksekliği dikkat çekici: net nakit pozisyonlu/düşük kaldıraçlı
  şirket örneklemde ÇOĞUNLUKTA (kısmen örneklem yanlılığı olabilir —
  DB'de analiz edilen şirketler rastgele değil, kullanıcı ilgisine göre
  seçilmiş).
- **Hasılat büyümesi (BÜYÜME):** BİST sanayi'de %68,2 "güçlü" (≥%15
  NOMİNAL) — bu, spec'in kendi uyardığı "yüksek enflasyon nominal
  büyümeyi YAPAY yüksek gösterir" riskinin SOMUT KANITIDIR: reel düzeltme
  OLMADAN BİST örnekleminin üçte ikisi "güçlü büyüyen" görünüyor, bu
  muhtemelen büyük ölçüde ENFLASYONİST bir yanılsama.

### 4. Fiyata bağımlı çarpanlar (F/K, PD/DD) — `--with-price` koşusu TAMAMLANDI

`--with-price` koşusu (165/167 BİST sanayi şirketi için canlı fiyat
başarıyla çekildi, ~411 sn sürdü, `isyatirim.fetch_latest_price()` ile)
GERÇEKTEN tamamlandı. Sonuçlar:

| Metrik | n | medyan | p10 | p90 | Not |
|---|---|---|---|---|---|
| F/K (own_pe) | 159 | 4,16 | -37,64 | 39,42 | min=-629,07, max=4.604,33 — UÇ DEĞERLER aşırı geniş, kırpma/winsorizasyon OLMADAN kullanılırsa mutlak-eşik bandı ciddi çarpıtılır |
| PD/DD (own_pb) | 165 | 1,25 | 0,36 | 5,97 | min=-5,99 (negatif özkaynak), max=71,88 |
| FD/FAVÖK | 138 | 7,21 | -17,75 | 28,65 | min=-1.173,98 |

**F/K bandı (sanayi CONFIG eşikleri, n=159):** ucuz(<8) 95 şirket
(%59,7) — **BİST örnekleminin YARISINDAN FAZLASI "ucuz" bandına
düşüyor.** Bu, Damodaran'ın 00_sentez §2.1'de aktarılan uyarısının
("sabit eşikler zaman/piyasaya göre kayar, 'ucuz' etiketi sistematik
olarak ÇOK FAZLA firmayı kapsayabilir") CANLI, somut bir kanıtıdır —
mevcut `fk_ucuz=8` eşiği (v1'den AYNEN taşınan) BİST'in mevcut (yüksek
enflasyon/düşük reel çarpan) rejiminde AŞIRI GEVŞEK kalmış olabilir,
"ucuz" etiketinin ayırt edicilik gücünü zayıflatıyor. **PD/DD bandı
(n=165):** ucuz(<1) 70 şirket (%42,4) — benzer bir örüntü, daha ILIMLI.
**Graham Çarpanı (F/K×PD/DD, n=90, ikisi de pozitif olan alt küme):**
medyan 20,16, ama `p90=157,71` ve `max=19.415,36` — UÇ DEĞERLERİN
BÜYÜKLÜĞÜ dikkat çekici (bkz. Y2/Y3, winsorizasyon önerisi burada da
geçerli). Graham'ın ≤22,5 eşiğini geçen (yani "ucuz") oran: **49/90
(%54,4)** — yine örneklemin yarısından fazlası.

**Sonuç:** Mevcut v1 F/K/PD/DD eşikleri (spec'in "AYNEN taşınır" dediği
`fk_ucuz=8`/`pddd_ucuz=1` gibi sabitler) BU GÜNKÜ BİST örnekleminde
şirketlerin %40-60'ını "ucuz" bandına düşürüyor — DEĞER merceğinin
Mutlak Ucuzluk bileşeni (spec'te %35 ağırlık) bu haliyle GÜÇLÜ bir
ayrıştırıcı DEĞİL, çoğunluğu aynı (yüksek) tarafa yığan bir filtre gibi
davranıyor. **Kod-geliştiriciye öneri:** F/K/PD/DD mutlak eşiklerinin
BİST için GÜNCEL bir kalibrasyon turu (medyan/persentil bazlı, bu
scriptin ürettiği türden) ile gözden geçirilmesi, en azından `fk_ucuz`
eşiğinin 8'den YUKARI çekilmesinin (örn. p25≈? -- uç değerler
winsorize edildikten SONRA yeniden hesaplanmalı) değerlendirilmesi
önerilir — bu bir SPEC değişikliği değil, MEVCUT (v1'den taşınan)
kalibrasyonun güncelliğine dair bir gözlemdir.

### 5. v1 Radar Skoru dağılımı (v2 lens kodu henüz yazılmadığı için proxy)

- **BİST sanayi (n=167, Değerleme DAHİL — gerçek fiyat verisiyle):**
  `min=1,79 / p10=3,07 / p25=4,23 / medyan=5,08 / p75=6,27 / p90=7,32 /
  max=9,36`. Rozet dağılımı: KARIŞIK 80, RİSKLİ 36, DENGELİ 38, SAĞLAM 8,
  YETERSİZ VERİ 5. [7,0-8,5] aralığında yığılma SADECE %11,7 (19/162) —
  **ayrıştırma gücü SAĞLIKLI, persona'nın "her şey 7-8'e yığılıyorsa"
  endişesi BU örneklemde (fiyat DAHİL, GERÇEK F/K/PD/DD ile) DOĞRULANMADI.**
  Değerleme bileşeni eklenince medyan hafifçe yükseldi (4,93→5,08) ve
  dağılım biraz daha SIKI toparlandı ama HÂLÂ geniş — sağlıklı.
- **NASDAQ sanayi (n=18, Değerleme HARİÇ — bu alt küme için canlı fiyat
  çekilmedi, script kapsamı BİLEREK SADECE BİST'i kapsıyor, bkz. modül üst
  notu):** `min=2,10 / p25=6,03 / medyan=7,49 / p75=9,08 / p90=9,47 /
  max=9,76` — medyan/p75/p90 ÜÇÜ DE 7'nin üzerinde, örneklemin
  ÇOĞUNLUĞU SAĞLAM/DENGELİ bandında toplanıyor. Bu YIĞILMA, BİST'in
  aksine, Değerleme bileşeni EKSİKKEN bile gözlemleniyor — küçük örneklem
  (n=18) ve seçim yanlılığı (DB'de analiz edilen NASDAQ şirketleri
  muhtemelen zaten "bilinen büyük/kaliteli" isimler, AAPL/MSFT/NVDA
  gibi) en olası açıklama, ama **v2 lens kodu yazıldığında bu sinyal
  Değer merceği DAHİL edilerek YENİDEN test edilmeli** (bu script'in
  --with-price kapsamı NASDAQ'ı içermiyor, sonraki bir kalibrasyon
  turunun konusu).

**Script kaynağı ve tekrar çalıştırma:** `scripts/kalibrasyon_v2.py`
(bkz. dosya). `python scripts/kalibrasyon_v2.py` (hızlı, ağsız, ~1 sn) veya
`python scripts/kalibrasyon_v2.py --with-price [--limit N]` (BİST F/K/
PD/DD dahil, ~7 dk, 202 tickerlık tam koşu BU raporun temelini oluşturdu).
