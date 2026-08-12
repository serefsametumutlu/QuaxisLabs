# SPEC: Kapsam-Cezalı Mercek Skoru (Nominal Ağırlık, Eksik=Sıfır)

**Bağlam:** Kullanıcı denetimi (2026-08-12, canlı AYES örneği) — KALİTE
merceğinde 7 bileşenden sadece 2'si (ROE %20 nominal, ROA %5 nominal)
veri buldu; mevcut `_agirlik_dagit_ve_hesapla` mekanizması eksik %75'i
KALAN 2 bileşene ORANTISAL yeniden dağıttı (ROE efektif %80'e, ROA
efektif %20'ye çıktı) ve ROE=9,3/ROA=8,8 gibi yüksek ham skorlardan
9,21/10 GİBİ, kapsamın sadece %25 olduğu gerçeğini gizleyen yanıltıcı bir
toplam üretti. Acil geçici yama (commit `c5c8499`) badge=YETERSİZ VERİ
olduğunda skoru TAMAMEN "N/A" yaptı; kullanıcı bunu da reddetti ("N/A
tamamen yazsın demedim... ölçebildiğimiz değerler nominal ağırlığa göre
saysın"). Bu spec üçüncü, kalıcı yaklaşımı tanımlar: **NOMİNAL ağırlık ×
skor katkısı, eksik bileşen SIFIR katkı sağlar, ağırlık yeniden
dağıtılmaz.**

Bu spec `docs/spec/spec_bilesik_skor.md` ve mercek spec'lerini
**DEĞİŞTİRMEZ** — mevcut `_agirlik_dagit_ve_hesapla` (efektif-ağırlık
yeniden dağıtımı) TÜM mercek modüllerinde AYNEN kalır. Burada tanımlanan
sayı, mevcut mekanizmanın YANINDA, SADECE düşük-kapsamlı durumlarda
GÖSTERİLECEK **ikinci, tamamlayıcı bir sayı**dır (persona kural 8:
genişlet, çöpe atma).

---

## 1. Matematiksel temel — S′ = S × kapsam/100 (ispatlı özdeşlik)

`_agirlik_dagit_ve_hesapla` içindeki mevcut toplam skor (S):

```
S = Σ_i [ skor_i × (nominal_i / mevcut_nominal_toplam) ]      (sadece skor_i != None olan bileşenler)
mevcut_nominal_toplam = data_coverage_pct = Σ nominal_i (skoru mevcut olan bileşenlerin nominal ağırlıkları toplamı, 0-100)
```

Önerilen "nominal ağırlık, eksik=sıfır" skoru (S′):

```
S′ = Σ_i [ skor_i × (nominal_i / 100) ]      (sadece skor_i != None olan bileşenler, ağırlık YENİDEN DAĞITILMAZ)
```

Bu iki ifadeyi birleştirirsek **cebirsel bir özdeşlik** ortaya çıkar:

```
S′ = S × (data_coverage_pct / 100)
```

**Bu özdeşlik önemlidir çünkü:** kod-geliştiricinin S′'yü bileşenlerden
sıfırdan yeniden hesaplamasına GEREK YOKTUR — `ScoreResult.total_score`
ve `ScoreResult.data_coverage_pct` ZATEN mevcut, S′ tek satırlık bir
ÇARPMA işlemidir. AYES doğrulaması: S=9,21, kapsam=%25 → S′ =
9,21×0,25 = **2,30** — kullanıcının elle hesapladığı örnekle (1,86+0,44+0
=2,30) BİREBİR eşleşir.

**Bu özdeşlik SADECE bileşen→mercek (lens içi) toplamada geçerlidir.**
Mercek→bileşik (4 mercek→tek sayı) toplamasında AYNI özdeşlik
GEÇERLİ DEĞİLDİR, çünkü `hesapla_bilesik_skor` mercek dahil etmeyi
SÜREKLİ değil, İKİLİ (data_sufficient True/False) bir kapıyla yapar ve
`hesapla_veri_kapsam_ozeti` FARKLI bir "kapsam" tanımı (mercek-içi
coverage'ların nominal ağırlıklı ortalaması) kullanır — bkz. §5 Bileşik
Skor Seviyesi.

---

## 2. Soru 1 — İki farklı şeyi tek sayıda birleştirmek savunulabilir mi?

**Evet, KOŞULLU olarak — ayrı gösterimin YANINDA, YERİNE DEĞİL.**

- Skor ("şirket ne kadar kaliteli") ve kapsam ("ne kadar veri biliyoruz")
  ZATEN ayrı iki alan olarak taşınıyor (`ScoreResult.total_score`,
  `ScoreResult.data_coverage_pct`) ve kart/detay sayfası ZATEN ikisini
  YAN YANA gösteriyor (`company_detail.html` satır 260:
  `{{ lens.score_display }}` + `kapsam: {{ lens.data_coverage_pct_display }}`,
  `dashboard.html` satır 612: düşük kapsamda △ bayrağı). Bu spec BU
  ayrımı ORTADAN KALDIRMAZ — S′ göstergesi kapsam yüzdesiyle BİRLİKTE,
  ONUN YERİNE DEĞİL sunulur (bkz. §4).
- S′'nün kendisi zaten çarpımsal olarak AYRIŞTIRILABİLİR (S′=S×kapsam/100)
  — yani "tek sayı" aslında GİZLİ bir birleşim değil, İKİ AYRI ölçülebilir
  büyüklüğün AÇIKÇA yazılmış çarpımıdır; kullanıcı isterse zihninden
  S=9,21'i kapsam=%25 ile çarpıp S′=2,30'u kendisi de üretebilir. Bu,
  "sahte kesinlik" değil — AKSİNE mevcut S'nin (kapsamı gizleyerek) ürettiği
  sahte kesinliği GİDEREN bir dönüşümdür.
- Riski: S′'yü TEK başına (kapsam yüzdesi olmadan) bir kart/liste
  görünümünde göstermek YANLIŞ OKUNABİLİR ("Kalite: 2,3/10" tek başına
  "şirket kötü" anlamına gelir, "veri az" anlamına gelmez) — bu yüzden §4
  metin şablonu ZORUNLU kılar: S′ HER ZAMAN kapsam yüzdesiyle AYNI CÜMLEDE
  gösterilir, asla yalnız başına değil.

---

## 3. Soru 2 — n=0 (kapsam=%0) durumu: S′=0 mı, yoksa None mı?

**Kalibrasyonla DOĞRULANMIŞ somut tehlike (bkz. §6 script çıktısı):**
kapsam=%0 olan satırlarda mevcut S ZATEN 0,00 (hiçbir bileşen katkı
vermediği için toplam otomatik 0'dır) — bu durumda S′=S×0/100=0,00 da
OTOMATİK olarak 0 çıkar. Eğer bu 0,00 değeri normal rozet eşikleriyle
(`_badge`) etiketlenirse **"RİSKLİ"** rozetine düşer — script çıktısında
TBORG/MPARK/ODAS/AVGO/BORSK gibi kapsam=%0 satırlarının HEPSİ bu şekilde
"YETERSİZ VERİ"den "RİSKLİ"ye kayıyor. Bu, persona'nın AÇIKÇA uyardığı
tuzağın TAM KENDİSİDİR: **"veri yok" ile "şirket kötü" KARIŞTIRILIYOR.**

**Kural (somut eşik):**

```
kapsam == 0  →  skor GÖSTERİLMEZ (score_display="N/A", mevcut davranış AYNEN kalır), badge=YETERSİZ VERİ
0 < kapsam < 50  →  S′ HESAPLANIR VE GÖSTERİLİR, badge YİNE DE YETERSİZ VERİ kalır (RİSKLİ'ye ASLA düşürülmez)
kapsam >= 50  →  mevcut davranış (S, `_badge(S)`) AYNEN kalır — bu spec BURAYI DEĞİŞTİRMEZ (bkz. §6 kalibrasyon riski)
```

Bu, mevcut `MIN_SECTOR_N=5` / `min_veri_agirlik_yuzdesi=%50` mantığıyla
TUTARLIDIR: nasıl ki n<5 sektör-göreli bileşeni SESSİZCE değil AÇIKÇA
devre dışı bırakıyorsa (evrensel eşiğe düşüyor, "belki ortalamadır"
varsaymıyor), kapsam=%0 da AYNI ilkeyle "hiç ölçemedik" der, "0/10 kötü"
DEMEZ. Badge katmanı (kategorik: SAĞLAM/DENGELİ/KARIŞIK/RİSKLİ/YETERSİZ
VERİ) bu spec'te **DEĞİŞTİRİLMEZ** — sadece kapsam<%50 bandında
YETERSİZ VERİ rozetinin YANINA, "N/A" yerine, dürüst bir SAYI eklenir.

---

## 4. Sunum şablonu (kart / dashboard / detay sayfası)

**Tek cümlede hem sayı hem bağlam (görev şartı):**

```
"{Mercek}: {S′ 1 ondalık} /10 (YETERSİZ VERİ — kapsam %{kapsam} — sadece {n_mevcut}/{n_toplam} bileşen ölçülebildi)"
```

Örnek (AYES, Kalite): **"Kalite: 2,3/10 (YETERSİZ VERİ — kapsam %25 — sadece 2/7 bileşen ölçülebildi)"**

- `n_mevcut`/`n_toplam`: `ScoreResult.components` listesinden
  `score is not None` olanların sayısı / toplam bileşen sayısı — YENİ bir
  alan İCAT EDİLMEZ, mevcut `components` listesinden türetilir.
- Kapsam=%0 durumunda cümle "N/A" olarak KALIR (§3), n_mevcut/n_toplam
  metni de gösterilmez (0/7 zaten anlamsız bir vurgu olurdu).
- **YENİ bir rozet İCAT ETMEYE gerek YOK** (görev sorusu): "YETERSİZ
  VERİ" rozeti + yanındaki dürüst sayı + "%X kapsam, N/M bileşen" metni
  ÜÇÜ BİRLİKTE zaten yeterince konuşuyor; ayrı bir "KAPSAM CEZALI" rozeti
  eklemek rozet enflasyonu yaratır (mevcut 5 rozetin üzerine 6.'yı
  eklemek, kullanıcının ZATEN "çok fazla sayı" şikayetine ters düşer).
- **Görsel işaret mevcut altyapıdan aynen kullanılır:** `dashboard.py`
  `LOW_COVERAGE_THRESHOLD_PCT=50` + `dusuk_kapsam` bayrağı ve
  `dashboard.html`'deki △ ikonu ZATEN bu amaç için VAR — YENİ bir CSS
  sınıfı/ikon EKLENMESİNE gerek YOK, sadece `dusuk_kapsam=True`
  durumundaki `score_display`'in İÇERİĞİ (bugün "N/A") S′'ye DEĞİŞİR.

---

## 5. Bileşik Skor seviyesi — AYNI ilke taşınmalı mı?

**Bu turda HAYIR — sadece mercek seviyesinde uygulanır, kompozit seviyesi
bu spec'in kapsamı DIŞINDA bırakılır.** Gerekçe:

1. §1'deki özdeşlik (S′=S×kapsam/100) kompozit seviyeye MATEMATİKSEL
   OLARAK doğrudan TAŞINMAZ — `hesapla_bilesik_skor` mercek dahil etmeyi
   sürekli değil İKİLİ (`data_sufficient`) bir kapıyla yapıyor, ve
   `hesapla_veri_kapsam_ozeti` FARKLI bir soru soruyor ("genel olarak ne
   kadar veriye dayanıyoruz", mercek dahil/hariç DEĞİL) — bu yüzden analog
   bir "kompozit S′" formülü SIFIRDAN yazılması gereken AYRI bir
   fonksiyon olurdu, mevcut alanlardan ÜCRETSİZ türetilemez.
2. **Kullanıcının şikayeti MERCEK seviyesindeydi** (kart üzerinde tek bir
   mercek badge'i) — kapsamı kompozite genişletmek, şikayet edilmemiş bir
   alana dokunmak olurdu.
3. **Kalibrasyon riski (bkz. §6):** Değer ve Büyüme mercekleri kapsam≥%50
   olsa BİLE S ile S′ arasında BÜYÜK fark üretiyor (ortalama ~1,3-1,5
   puan, rozet bandının ~%42-53'ünde DEĞİŞİYOR). Eğer bu davranış
   kompozit seviyeye — mercek başına DEĞİL, TÜM sistem genelinde — hiç
   kalibre edilmeden taşınırsa, ŞU AN "yeterli" sayılan onlarca DENGELİ/
   SAĞLAM rozetli şirketin rozet bandı DEĞİŞİR — bu, kullanıcının talep
   ETMEDİĞİ, çok daha büyük bir kapsam genişlemesi olurdu.

**Öneri:** Bu spec onaylanıp mercek seviyesinde YAŞADIKTAN sonra, AYRI
bir kalibrasyon turunda kompozit seviyesi için özel bir "nominal
ağırlıklı, eksik mercek=sıfır" varyantı (Σ mercek_skoru_i ×
MERCEK_AGIRLIKLARI[i]/100, sadece data_sufficient merceklerde, dahil
edilmeyenler sıfır katkı) ayrı bir spec'te ele alınmalı — burada SADECE
bir "sonraki tur" notu olarak İŞARETLENİR, ŞİMDİ uygulanmaz.

---

## 6. Kalibrasyon (GERÇEK veriyle doğrulandı)

**Script:** `scripts/kalibrasyon_kapsam_cezali_skor.py` — `MarketScanResult`
tablosundaki (Faz 5 toplu tarama, PID arka planda süren tam evren
taramasının O ANKİ anlık görüntüsü) **557 "ok" taranmış şirket** (527 BİST
+ 30 NASDAQ) üzerinde ÇALIŞTIRILDI. Tam çıktı script çalıştırılarak
yeniden üretilebilir; öne çıkan bulgular:

**Kapsam dağılımı (mercek başına, medyan):**

| Mercek | Medyan kapsam | <%50 kapsamlı şirket | Yorum |
|---|---|---|---|
| Kalite | %90 | 22/557 (%4,0) | ÇOĞUNLUKLA yüksek/tam kapsam — AYES (kapsam %25) İSTİSNADIR, kural DEĞİL |
| Güvenlik | %100 | 23/557 (%4,1) | Aynı desen — bimodal (ya neredeyse tam, ya çok düşük) |
| Değer | %55 | 85/557 (%15,3) | DAHA DÜŞÜK, DAHA DAĞINIK kapsam — sistemik bir örüntü |
| Büyüme | %55 | 31/557 (%5,6) | Değer'e benzer, ORTA bandında (%50-75) yoğunlaşmış |

**Kritik bulgu — "kapsam≥%50 pratikte mevcut davranışla aynı mı?" sorusunun cevabı MERCEĞE GÖRE DEĞİŞİYOR:**

| Mercek | kapsam≥%50 alt-kümede \|S−S′\| ortalama | kapsam≥%50'de rozet bandı DEĞİŞEN oran |
|---|---|---|
| Kalite | 0,21 puan | %8,4 |
| Güvenlik | 0,23 puan | %7,9 |
| **Değer** | **1,52 puan** | **%53,0** |
| **Büyüme** | **1,33 puan** | **%41,6** |

Kalite/Güvenlik'te kapsam≥%50 bandı S ve S′ neredeyse ÖZDEŞ (bu spec'in
§5'te "kompozit seviyeye TAŞIMA" konusunda ihtiyatlı olma gerekçesinin
SAYISAL KANITIDIR — Değer/Büyüme'de aynı ihtiyat YOKSA sistemik bir rozet
kayması OLUŞUR). Bu FARK, Değer/Büyüme mercek spec'lerindeki bileşen
sayısının FAZLA (7 alt-bileşen) ve bunların bir kısmının (temettü verimi,
NCAV, sektöre-göreli konum vb.) HALEN veri-eksik olmasından kaynaklanıyor
(bkz. `docs/spec/veri_tamlik_notu.md`) — Kalite/Güvenlik'te ise bileşenler
ya HEPSİ mevcut ya da (banka/sigorta şablonunda) yapısal olarak zaten
KÜÇÜK bir kümeye indirgenmiş durumda, bu yüzden "kısmi eksik" ara-bandı
görece NADİR.

**n=0 tehlikesi (§3'ün somut kanıtı):** kapsam=%0 satırlarında (TBORG,
MPARK, ODAS, AVGO, BORSK, ANSGR, GOOGL'ın Güvenlik'i vb.) ham S=0,00 —
eğer bu değer normal rozet eşikleriyle etiketlenseydi "RİSKLİ" çıkardı;
§3'teki kural (kapsam=%0 → skor GÖSTERİLMEZ, badge YETERSİZ VERİ kalır)
tam olarak bunu ÖNLÜYOR.

**AYES-benzeri somut örnekler (kapsam<%30, eski S≥7,0):**
- Kalite: BKNG (kapsam %5, S=8,37→S′=0,42), AVGO (kapsam %20, S=7,34→S′=1,47), **AYES (kapsam %25, S=9,21→S′=2,30)**
- Büyüme: YBTAS, ISBIR, BASCM, ORMA, AYES (hepsi kapsam %20, S 7,8-10,0 aralığında iken S′ 1,6-2,0 aralığına düşüyor)

Bu örnekler, AYES'in TEK/izole bir olay olmadığını, aynı yanıltıcı
örüntünün (çok az bileşen + yüksek ham skor → şişirilmiş toplam) hem BİST
hem NASDAQ'ta, hem Kalite hem Büyüme merceğinde TEKRARLANDIĞINI
doğruluyor — düzeltme sadece AYES'e özel değil, sistemik bir düzeltmedir.

---

## 7. Kenar durumlar

- **Banka/sigorta/finansman şablonları (Kalite: sadece ROE+ROA, nominal
  80/20):** Aynı formül AYNEN uygulanır — iki bileşenden SADECE biri
  varsa (örn. sigortada ROA hiç hesaplanamıyor, bkz. `lens_kalite.py`
  satır 205-208) S′ = skor_ROE × 0,80 olur, kapsam=%80 zaten ≥%50 olduğu
  için bu durum §3'ün <%50 dalına bile GİRMEZ (mevcut davranış zaten
  geçerli kalır).
- **Tek bileşenli mercekler (aşırı uç, teorik):** S′ = tek bileşenin
  skoru × nominal_ağırlığı/100 — nominal ağırlık %100 değilse (mercek
  içinde başka bileşenler tanımlıysa ama hepsi None) S′ MATEMATİKSEL
  OLARAK asla o bileşenin ham skoruna ULAŞAMAZ, bu KASITLI ve
  İSTENEN davranıştır (görev metninin AÇIKÇA istediği "tavan" etkisi).
- **Yuvarlama/Decimal:** Tüm hesap `Decimal` ile yapılır (proje anayasası)
  — S′ = S × data_coverage_pct / Decimal(100), `_num_str`/`format_number_tr`
  ile GÖSTERİM anında 1 ondalığa yuvarlanır, ARA hesaplarda yuvarlama
  YAPILMAZ (mevcut `_agirlik_dagit_ve_hesapla` deseniyle TUTARLI).

---

## 8. Test senaryoları

1. **AYES (Kalite, kapsam %25, S=9,21):** S′=2,30, badge=YETERSİZ VERİ,
   kart metni "Kalite: 2,3/10 (YETERSİZ VERİ — kapsam %25 — 2/7 bileşen)".
2. **THYAO (Kalite, kapsam %100, S=X):** S′=S (özdeşlik: kapsam=100 →
   S′=S×1=S) — mevcut davranış BİREBİR korunur, GÖRSEL FARK YOK.
3. **Kapsam=%0 (örn. TBORG Değer merceği):** score_display="N/A" (mevcut
   davranış AYNEN), badge=YETERSİZ VERİ, "RİSKLİ"YE ASLA düşürülmez.
4. **Kapsam=%50 (tam sınırda):** Bu durum ZATEN mevcut
   `min_veri_agirlik_yuzdesi=%50` kuralı gereği "veri_yeterli=True" sayılır
   (`>=` karşılaştırması) — §3'ün <%50 dalına GİRMEZ, mevcut S gösterilir
   (S′ formülü BU sınırda TETİKLENMEZ, süreksizlik YOKTUR çünkü S′ zaten
   sadece <%50 bandında DEVREYE girer, =%50'de KENDİLİĞİNDEN mevcut
   davranışa devrolur).
5. **Banka Kalite (ROE var, ROA yok, kapsam %80):** §3'ün ≥%50 dalına
   girer, mevcut S gösterilir (S′ hesaplanmaz/gösterilmez) — DEĞİŞİKLİK
   YOK.

---

## 9. Uygulama sırası (kod-geliştirici devir listesi — SEN kod yazma, bu SADECE sıradaki adımlar)

1. **`src/analysis/lens_common.py` VEYA `scorer.py`'ye küçük bir yardımcı
   ekle** (yeni, PARALEL fonksiyon — mevcut `_agirlik_dagit_ve_hesapla`
   DOKUNULMAZ): `kapsam_cezali_skor(sonuc: ScoreResult) -> Decimal:
   return sonuc.total_score * sonuc.data_coverage_pct / Decimal(100)`.
   Tek satırlık, test edilmesi kolay, `ScoreResult`'ın MEVCUT alanlarından
   türetilir (§1 özdeşliği).
2. **`scripts/tarama_toplu.py::_scan_one`**: `MarketScanResult`'a S′ için
   yeni bir sütun eklenmesine GEREK YOK (mevcut `{lens}_score` +
   `{lens}_coverage_pct` ZATEN saklanıyor, S′ RENDER katmanında,
   gösterim anında hesaplanabilir — DB şişirilmez).
3. **`src/render/dashboard.py::_mercek_block`**: `c5c8499`'daki
   `if badge == YETERSIZ_VERI_ROZETI: return {...score_display: "N/A"...}`
   bloğu §3/§4 kuralına göre GÜNCELLENİR:
   - `coverage == 0` (veya `coverage is None`) → `score_display="N/A"`
     AYNEN kalır (mevcut c5c8499 davranışı BU dalda KORUNUR).
   - `0 < coverage < 50` → `score_display` = `kapsam_cezali_skor(...)`
     formatlanmış hali + (mümkünse) template katmanında §4'teki tam
     cümle (n_mevcut/n_toplam `components`'tan sayılır).
   - `coverage >= 50` zaten bu `if` bloğuna hiç GİRMİYOR (badge != YETERSİZ
     VERİ), DOKUNULMAZ.
4. **`src/render/company_detail.py::_mercek_summary`**: AYNI mantık (satır
   193-201 civarı, `c5c8499` diff'i) — `score_display` hesaplaması
   dashboard.py ile BİREBİR TUTARLI güncellenir (iki dosyada kod tekrarı
   varsa, ORTAK bir yardımcıya (`src/render/` içinde) ÇIKARILMASI
   ÖNERİLİR — kod tekrarını önleme ilkesi).
5. **`src/render/templates/dashboard.html` / `company_detail.html`**:
   Değişiklik GEREKMEZ — △ ikonu ve `dusuk_kapsam`/`data_coverage_pct_display`
   ZATEN mevcut, sadece `score_display`'in İÇERİĞİ değişiyor. §4'teki
   "N/M bileşen ölçülebildi" ek cümlesi eklenecekse `_mercek_block`/
   `_mercek_summary`'nin döndürdüğü dict'e yeni bir `n_mevcut`/`n_toplam`
   alanı eklenip template'te (İSTEĞE BAĞLI, kart sıkışıklığına göre
   kod-geliştirici karar verir) gösterilebilir.
6. **Testler:** `tests/test_dashboard.py`/`tests/test_company_detail.py`
   içindeki `c5c8499` regresyon testleri (blanket "N/A" bekleyen testler)
   §3 kuralına göre GÜNCELLENMELİDİR (kapsam=%0 testi AYNEN kalır,
   0<kapsam<50 testi ARTIK "N/A" değil S′ sayısını BEKLEMELİDİR — AYES
   benzeri bir fixture: kapsam=%25, S=9,21 → beklenen S′="2,3").
7. **Kompozit seviyesi (§5):** Bu turda DOKUNULMAZ — `lens_bilesik_skor.py`
   ve `hesapla_bilesik_skor`/`hesapla_veri_kapsam_ozeti` DEĞİŞMEZ.
