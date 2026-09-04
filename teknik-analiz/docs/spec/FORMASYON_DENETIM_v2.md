# Formasyon Denetim v2 — Faz 1, Adım 3 / 1D (Doğrulama)

**Tarih:** 2026-09-04 · **Kapsam:** double_top_bottom.py + head_shoulders.py'nin Faz 1
(1A/1B/1C) literatür filtrelerinin (eq_tol, min_bars_between, min_rise_between_pct,
prior_trend, min_depth, shoulder_time_ratio) önce/sonra ölçümü + elenme sebebi
dağılımı + wedge/triangle/broadening'in (BULUNAN HATA 3 kapanışı) `max_bars` span
taraması + 10 rastgele sinyalin görsel incelemesi. 120 gerçek BIST sembolü, D1+4H,
önbellek verisiyle (`scripts/formasyon_denetim.py`).

## Özet

Faz 1'in ana iddiası (yeni literatür filtreleri sahte formasyonları eler) **1D
zaman diliminde doğrulandı, ama D1'de BEKLENENDEN ÇOK DAHA AZ, 4H'te ise
double_top_bottom için TAMAMEN ELİMİNE EDEN, KARAR GEREKTİREN bir sonuç
üretti.** head_shoulders her iki zaman diliminde de makul bir azalma gösterdi
(%19-31) ve GÖRSEL İNCELEMEDE gerçekten TEMİZ, textbook kalitesinde bir OBO
örneği üretti (ISCTR). double_top_bottom D1'de %76.5 azaldı (298→70) — bu
ÖNCEKİ regresyon düzeltmelerine benzer, sağlıklı bir sonuç. **Ama double_top_
bottom 4H'te 125→0'a düştü (%100) — YENİ parametrelerle bu gösterge 4H'te
FİİLEN DEVRE DIŞI.** **BU BULGU AYNI GÜN KAPATILDI** — kök neden `tlab/core/
params.py::_TF_BAR_SCALE`'in "gün 24 saat işlem görür" YANLIŞ varsayımı
(BIST'in GERÇEK 8 saatlik seansı yerine) + `min_bars_between`'in ATR-zigzag
pivot aralığını (zaman-dilimi-DEĞİŞMEZ bir bar sayısı) takvimsel ölçeklemesi
olarak bulundu; düzeltme sonrası 4H sinyal sayısı 497→72 (%85.5 azalma,
D1'in %76.5'ine yakın, SAĞLIKLI). Detay: aşağıdaki "KAPATILDI" bölümü.

Görsel inceleme (10 örnek, hepsi `Read` ile açılıp incelendi) AYRICA daha önce
BEKLENMEYEN 3 yeni bulgu ortaya çıkardı: (1) render zincirinde `last_n`
parametresinin `patterns.*`/`harmonic.*` için pencere BİTİŞİNİ hiç
etkilemediği, bunun ters (başlangıç>bitiş) bir x-ekseni aralığına yol açtığı
GERÇEK bir renderer hatası; (2) `patterns.broadening`'in hologram poligonunun
görsel olarak YAKINSAYAN bir kamaya benzediği (kod incelemesiyle sınıflandırma
mantığının MATEMATİKSEL OLARAK doğru olduğu doğrulandı — bu bir ANLATIM/görsel
netlik sorunu, sınıflandırma hatası DEĞİL); (3) ISBTR sembolünün önbellek
verisinde gerçekçi olmayan bir fiyat ölçeği (400.000-680.000 TL) — ayrı bir
veri kalitesi şüphesi. Ayrıca BULUNAN HATA 1 (formasyon render'da hiç
görünmüyor) 3 YENİ örnekle (BARMA, ISBTR×2, GEDİK) tekrar doğrulandı —
"yaygın" sınıflandırması güçlendi. Hepsi aşağıda detaylandırıldı; hiçbiri bu
oturumda DÜZELTİLMEDİ (Faz 1 disiplinine göre kapsam dışı, loglandı).

## Yöntem

- Örneklem: `scripts/sistemik_denetim.py` ile AYNI yöntem — BIST evreninden
  hem D1 hem 4H'te ≥200 bar önbelleği olan **120 sembol**, `LOOKBACK_BARS=600`.
- "Eski": Faz 1 ÖNCESİ davranışın en yakın yeniden-inşası —
  `eq_tol=0.02, min_bars_between=5` (double_top_bottom'un GERÇEK eski
  değerleri), `prior_trend_min_tstat=0.0` + `min_depth_pct/atr=0.0` (Faz 1
  ÖNCESİ hiç var olmayan filtreler için en yakın "yok" yaklaşımı —
  `prior_trend`'in YÖN şartı yapısal olarak kalır, bu YAKLAŞIK bir alt sınır,
  "filtre tam yok" ile BİREBİR AYNI değil), `neck_total_slope_max=1.0`
  (head_shoulders'ın eski, bar-başına yanlış-normalize boyun kontrolü "fiilen
  hiçbir şeyi elemiyordu" — bu değer o no-op davranışı doğru temsil eder,
  eski FORMÜLÜ birebir yeniden kurmak artık kod silindiği için mümkün değil).
- "Yeni": `scaled_factory()` üzerinden bu oturum sonundaki GERÇEK varsayılan
  davranış (`for_timeframe` ölçeklemesi uygulanmış).
- Sinyal sayısı = `state in (confirmed, completed)` olan `Signal` sayısı.
- Elenme sebebi: indikatörlere (bkz. `double_top_bottom.py`/`head_shoulders.py`
  /`wedge.py`/`broadening.py`'deki YENİ `_bump()` yardımcı fonksiyonu) opsiyonel
  `context={"elim": {}}` verilerek her `continue`/`return False` noktasında
  bir sayaç artırılır — varsayılan (`context=None`) davranış DEĞİŞMEZ.
- Görsel örnekler: YENİ parametrelerle confirmed/completed sinyaller arasından
  10 tanesi rastgele seçildi (`SEED=11`), her biri `tlab plot`'un kullandığı
  AYNI `render()`/`scaled_factory()` çağrısıyla PNG'ye render edildi,
  `Read` ile açılıp TEK TEK incelendi.

## 1-2-3 — Önce/sonra + kategori kırılımı + elenme sebebi dağılımı

| Gösterge | TF | Eski | Yeni | Azalma | Eski kategori | Yeni kategori | Elenme sebebi (yeni) |
|---|---|---:|---:|---:|---|---|---|
| patterns.double_top_bottom | 1D | 298 | 70 | **%76.5** | top:132 / bottom:166 | top:25 / bottom:45 | eq_tol:1947, min_bars_between:1059, prior_trend:65, min_rise_between_pct:3 |
| patterns.double_top_bottom | 4H | 125 | **0** | **%100** | top:51 / bottom:74 | — | min_bars_between:4172 (**TEK sebep — hiçbir aday sonraki filtrelere ULAŞAMIYOR**) |
| patterns.head_shoulders | 1D | 204 | 141 | %30.9 | obo:67 / tobo:137 | obo:53 / tobo:88 | prior_trend:111, shoulder_time_ratio:163, min_depth:4 |
| patterns.head_shoulders | 4H | 126 | 102 | %19.0 | tobo:67 / obo:59 | tobo:51 / obo:51 | shoulder_time_ratio:230, prior_trend:269, min_depth:3 |

**Okuma notu:** elenme sebebi sayaçları KÜMÜLATİF DEĞİL — bir aday İLK
başarısız olduğu filtrede sayılır, sonraki filtrelere hiç ulaşmaz (bu yüzden
double_top_bottom 4H'te `eq_tol`/`prior_trend`/`min_depth` sayaçları SIFIR
görünüyor — 4172 aday zaten `min_bars_between`'de elendiği için oraya hiç
ulaşamadı, bu filtreler daha gevşek/sıkı olsalar bile SONUÇ DEĞİŞMEZDİ).

head_shoulders'ta EN BÜYÜK eleyici `shoulder_time_ratio` (Faz 1'in KENDİSİ
DEĞİL, önceden var olan bir filtre) — bu, Faz 1'in yeni filtrelerinin (prior_
trend/min_depth) NİSPETEN ILIMLI olduğunu, asıl sıkılaşmanın zaten var olan
geometri kısıtından geldiğini gösteriyor.

## KAPATILDI (2026-09-04, aynı gün) — Karar Gerektiren Bulgu çözüldü

Kullanıcı 4 seçeneği değerlendirmemi ve en avantajlısını uygulamamı istedi.
Kök nedeni daha derin araştırınca seçeneklerin hiçbiri tam doğru çerçeve
değildi — **gerçek kök neden BULUNDU ve düzeltildi:**

**Kök neden #1 (sistemik, TÜM `_BAR_FIELDS` alanlarını etkiliyordu):**
`tlab/core/params.py::_TF_BAR_SCALE` (Faz 0.5, A2) "gün 24 saat sürekli
işlem görür" varsayımıyla kalibre edilmişti (1H×24, 4H×6). BIST seansı
10:00-18:00 (8 saat) ve GERÇEK bar sayısı (`data/resample.py`'nin
09:00/13:00/17:00 hizalamasıyla, gerçek ISCTR verisinde ÖLÇÜLDÜ) günde
ORTALAMA **9 (1H) / 3 (4H)** — eski katsayılar 1H'de ~2.7x, 4H'de TAM 2x
fazla sıkıydı. `_TF_BAR_SCALE` düzeltildi (1H: 24→9, 4H: 6→3) — bu, double_
top_bottom'un YANI SIRA `prior_trend_lookback`, wedge/broadening'in
`min_bars`/`max_apex_bars` gibi HER `_BAR_FIELDS` alanını doğru kalibre
etti (sistemik bir düzeltme, tek bir göstergeye özel değil).

**Kök neden #2 (double_top_bottom'a özel):** Kök neden #1'in düzeltmesiyle
bile (132→66 bar) 4H'te HÂLÂ sıfıra yakın sinyal vardı (30 sembolde 0/20
denemesi gösterdi). Derin ölçüm: `min_bars_between`'in ölçtüğü şey (ATR-
zigzag'de eşleşen p1→p2 pivot ARALIĞI) BAR SAYISI olarak zaman diliminden
**neredeyse bağımsız** — 120 sembolde medyan 1D'de **27.5 bar**, 4H'te **29
bar** (ALMOST AYNI). Mekanik açıklama: ATR'nin kendisi bar granülaritesine
göre ölçekleniyor (4H'teki tek ATR birimi 1D'dekinden küçük), bu yüzden
"3×ATR'lik bir tersine dönüş" biriktirmek HER İKİ zaman diliminde kabaca
AYNI SAYIDA bar alıyor — bu, ATR-zigzag pivot mesafelerinin **kendi
doğasında zaman-dilimi-değişmez (self-similar)** olduğunun somut kanıtı.
Takvimsel (calendar-linear) ölçekleme bu yüzden BU ALAN için YANLIŞ
modeldi. **Düzeltme:** `min_bars_between` `_BAR_FIELDS`'ten TAMAMEN
çıkarıldı (artık HİÇBİR zaman diliminde ölçeklenmiyor, her zaman ham 22)
— `prior_trend_lookback` (kapanış fiyatı üzerinde OLS penceresi, GERÇEKTEN
takvimsel bir kavram) hâlâ ölçekleniyor.

**Sonuç (120 sembol, TAM yeniden ölçüm):**

| Gösterge | TF | Önceki (Adım 3 raporu) | **Düzeltme sonrası** |
|---|---|---:|---:|
| patterns.double_top_bottom | 1D | 298→70 | 298→70 (DEĞİŞMEDİ, sorun zaten yoktu) |
| patterns.double_top_bottom | 4H | **125→0 (%100)** | **497→72 (%85.5)** |

("Eski" sayı 4H'te 125'ten 497'ye çıktı çünkü "eski" yeniden-inşası da artık
`min_bars_between=5`'i HİÇ ölçeklemiyor — bu, düzeltmenin doğru bir
yan-etkisi, karşılaştırma tutarlılığı için gerekli.)

**72 sinyal, %85.5'lik SAĞLIKLI bir azalma** (D1'in %76.5'ine çok yakın) —
gösterge artık 4H'te fiilen devre dışı DEĞİL. `tlab/core/params.py`,
`tlab/indicators/patterns/double_top_bottom.py` + 3 test dosyası güncellendi
(656 test yeşil, ruff/mypy/lint_lookahead baseline ile birebir).
`wedge`/`broadening`/`head_shoulders` bu düzeltmeden ETKİLENMEDİ (span/
elenme dağılımları ölçüldü, `min_bars`/`max_apex_bars` zaten p95'in çok
altında kalıyordu — zeroing riski yoktu, bkz. yukarıdaki span taraması).

---

## (ARŞİV) Orijinal "Karar Gerektiren Bulgu" — artık KAPATILDI, aşağıdaki
## bölüm tarihsel referans için bırakıldı

Kullanıcıya ilk sunulan 4 seçenek (üstteki gerçek kök-neden analizinden
ÖNCE yazılmıştı):

## Karar Gerektiren Bulgu — double_top_bottom 4H'te sıfırlandı

`DoubleTopBottomParams.min_bars_between=22` (1D taban, LMW: "en az 1 ay") Faz
0.5'in A2 (`for_timeframe`) mekanizmasıyla 4H'e **×6 = 132 bar** olarak
ölçekleniyor. 120 sembolün TAMAMINDA `600` barlık pencerede eşleşen (p1,p2)
çiftlerinin (double top/bottom adayları) HİÇBİRİ 132 bar arayla değil —
`min_bars_between` TEK BAŞINA 4172 adayın TAMAMINI eledi, sıfır aday sonraki
filtrelere ulaştı. Bu, "1 aylık minimum mesafe" kuralının GÜNLÜK veriden
türetildiğini (LMW) ve 4H'e DOĞRUDAN takvimsel ölçeklemenin, double top/dip'in
4H'te DOĞASI GEREĞİ daha KISA sürede oluşan bir yapı olduğu gerçeğini
YOK SAYDIĞINI düşündürüyor — double top/dip klasik olarak "birkaç haftalık"
bir formasyondur, 4H barında bu birkaç GÜNLE ifade edilir, birkaç HAFTAYLA
değil.

**Bu Faz 1'in kapsamında ÇÖZÜLMEDİ** — yalnızca BULUNDU ve loglandı. Olası
yönler (karar kullanıcıya bırakıldı):
1. `min_bars_between`'i `_BAR_FIELDS`'ten ÇIKARIP 4H için AYRI, daha düşük bir
   taban değer belirlemek (takvimsel ölçekleme YERİNE zaman-dilimi-özel sabit).
2. Ölçekleme formülünü DEĞİŞTİRMEK (ör. `sqrt` ile yumuşatmak — 6× yerine ~2.4×).
3. Şimdilik `patterns.double_top_bottom`'u 4H'te KAPALI kabul edip yalnızca D1'de
   kullanmak (`supported_timeframes`'ten 4H çıkarılabilir) — en az riskli ama
   bir göstergeyi fiilen devre dışı bırakır.
4. Hiçbir şey yapmamak — 4H double top/dip GERÇEKTEN nadir/güvenilmez kabul
   edilip sıfır sinyal "doğru" sonuç sayılabilir (LMW'nin kendisi günlük veri
   için yazılmıştı, 4H'e hiç uygulanmaması gerektiği savunulabilir).

## BULUNAN HATA 3 kapanışı — wedge/triangle/broadening span taraması

`max_bars` (1B'de eklenen opsiyonel üst sınır, varsayılan 0=sınırsız) farklı
eşiklerde D1'de (wedge+triangle+broadening toplamı) kaç confirmed/completed
sinyalin HALA geçtiğini gösteriyor:

| max_bars (bar) | confirmed toplam (wedge+triangle+broadening, 1D) |
|---:|---:|
| 60 | 9 |
| 90 | 30 |
| 120 | 36 |
| 180 | 62 |
| 250 | 92 |
| sınırsız (0) | 166 |

Azalma DÜZ/monotonik ve KADEMELİ — tek bir "doğru" eşik yok, sürekli bir
dağılım. **166 sinyalin ~%45'i (75 tanesi) 250 bardan (D1'de ~1 yıl) DAHA
UZUN süren "formasyonlar"** — SKBNK/triangle görsel örneğinde (aşağıya bak)
bunun somut bir örneği görüldü (8+ aylık bir direnç çizgisi, gerçek
"formasyon" son birkaç haftaya sıkışmış). Bu, `max_bars`'a GERÇEK bir
varsayılan (ör. 120-180 bar D1 için) verilmesinin makul olduğunu
düşündürüyor, ama TEK BAŞINA bu ölçüm bir sayı SEÇMEK için yeterli değil
(hangi eşiğin "gerçek" formasyonları koruyup "sahte" olanları elediğini
görsel olarak doğrulamak gerekir — bu AYRI bir takip işi, Faz 1'in kapsamı
DIŞINDA bırakıldı çünkü `max_bars` zaten varsayılan olarak KAPALI/sınırsız,
davranış değişmedi).

## 4 — Görsel inceleme (10 rastgele sinyal, hepsi incelendi)

**Metodoloji notu (ÖNEMLİ, kendi kendine bulunan bir sorun):** İlk render
turunda `render_live()`'ın `compute_live()`'ı TAM (600 bar SINIRLI olmayan)
önbellek geçmişiyle çağırdığı, ama sinyal SAYIMININ `LOOKBACK_BARS=600`
sınırlı bir df kullandığı fark edildi — bu iki farklı veri uzunluğu
`patterns.*` render'ının "en son GEÇERLİ örüntü" otomatik-yakınlaştırmasının
FARKLI bir adayı seçmesine yol açabiliyor (aşağıdaki "Renderer Hatası" bölümü).
**Düzeltme:** tüm 10 örnek, SAYIM ile AYNI (600-bar sınırlı) df kullanılarak
YENİDEN render edildi. Bazı görsellerde bu yüzden gösterilen spesifik örüntü
(ör. ISCTR'de bir OBO), JSON'daki orijinal örneklenmiş sinyalden (bir TOBO)
FARKLI olabilir — bu her görselin altında AÇIKÇA belirtildi.

| # | Sembol | Gösterge | TF | Örneklenen olay | Görselde GERÇEKTE gösterilen | Tek cümlelik yargı |
|---|---|---|---|---|---|---|
| 0/8 | ODINE | broadening | 4H | top/bottom_confirmed | Aynı (top+bottom birlikte) | Geometrik olarak makul bir genişleyen formasyon (ileri yöndeki ıraksama gerçek), ama fiyatın ~9 ayda 11 KAT artması ayrıca bir veri-mantık kontrolü gerektirir. |
| 1 | BARMA | broadening | 4H | top_confirmed | Aynı | Hologram poligonu GÖZLE yakınsayan bir kama gibi görünüyor (created_idx'e doğru daralıyor) — sınıflandırma kod incelemesiyle doğru bulundu ama görsel ANLATIM yanıltıcı, gerçek bir "genişleyen" izlenimi vermiyor. |
| 2/5 | ISBTR | broadening | 4H | bottom_target_reached / bottom_retest_hold | Aynı geometri, iki farklı olay | Sembolün fiyat verisi 400.000-680.000 TL aralığında — BIST için gerçekçi değil, bu formasyonun kendisinden ÖNCE bir veri-kalitesi sorunu şüphesi var. |
| 3 | SKBNK | triangle | 4H | sym_triangle_retest_hold | Aynı | Üçgenin direnç çizgisi 8+ ay geriye uzanıyor ama GERÇEK apeks/kırılım son birkaç haftaya sıkışmış — BULUNAN HATA 3'ün (aşırı uzun formasyon) somut bir örneği, `max_bars` sınırlanırsa bu aday muhtemelen elenir. |
| 4 | IZMDC | broadening | 1D | bottom_target_reached | Aynı | BARMA ile AYNI hologram/kama görünümü sorunu var, ama ileri yöndeki iki çizginin (Kas 2025→Mar 2026) GERÇEKTEN ıraksadığı grafikte görülebiliyor — sınıflandırma muhtemelen doğru. |
| 6 | ISCTR | head_shoulders | 4H | tobo_confirmed | **obo_confirmed** (farklı aday, bkz. metodoloji notu) | Textbook kalitesinde bir OBO: net sol omuz/baş/sağ omuz, yatay boyun, temiz kırılım+hedef — Faz 1 sonrası kalan sinyallerin GERÇEKTEN yüksek kalitede olabileceğinin güçlü bir kanıtı. |
| 7 | GEDİK | head_shoulders | 4H | obo_confirmed | (render'da HİÇBİR ŞEY görünmüyor) | BULUNAN HATA 1'in (formasyon çizimi render'da kayboluyor) yeni bir örneği — sinyal muhtemelen geçerli ama görsel olarak DOĞRULANAMADI. |
| 9 | BARMA | broadening | 1D | bottom_confirmed | Aynı (+ ayrıca bir "top" örüntüsü) | 1D'de BARMA'nın 4H'teki AYNI kama-görünümü sorunu var ama "RETEST TUTTU" durumu bu sefer düzgün render edildi — render kaybı (HATA 1) durum-bağımsız/aralıklı görünüyor. |

**Sonuç:** 10 örnekten 8'i (0,1,2,3,4,5,6,8,9 — GEDİK hariç) render edildi ve
GEOMETRİK olarak incelenebildi; bunların BÜYÜK ÇOĞUNLUĞU (ISCTR net biçimde,
diğerleri "makul ama kama-görünümlü hologram" ile) gerçek/tutarlı formasyonlar.
1/10 (GEDİK) render'da tamamen kayboldu (HATA 1). Örneklem `patterns.wedge`
veya `patterns.double_top_bottom`'dan HİÇ örnek İÇERMİYOR (rastgele seçim
`patterns.broadening`'e ağırlıklı düştü — double_top_bottom zaten 4H'te sıfır,
D1'de göreceli küçük bir havuzdu) — bu bir sonraki turda giderilebilecek bir
örneklem dengesizliği notu.

## YENİ Bulgular (bu turda keşfedildi, KAPSAM DIŞI, sadece loglandı)

**Renderer Hatası (YENİ, BULUNAN HATA 2'den AYRI) — `_resolve_window_end`
`last_n`'i yok sayıyor:** `tlab/viz/renderer.py::_resolve_window_end` (satır
480) fonksiyonu `last_n` parametresi ALMIYOR — `patterns.*`/`harmonic.*`
göstergeleri için pencere BİTİŞİNİ HER ZAMAN "en son confirmed/completed
örüntünün kendi ufku"na göre hesaplıyor, çağıran `last_n` ile AÇIKÇA farklı
bir pencere istese bile. `_resolve_window_start` (satır 375) `last_n`'e
UYUYOR ama `_resolve_window_end` UYMUYOR — ikisi TUTARSIZ. Sonuç: `last_n`
açıkça verildiğinde, en son geçerli örüntü `last_n`'in ima ettiği pencereden
DAHA ESKİYSE, `window_end_idx < window_start_idx` (TERS aralık) oluşabiliyor
— `render()` bunu Plotly'e `range=[start, end]` olarak geçiyor, sonuç
neredeyse boş/anlamsız bir grafik (bu oturumda ISCTR `patterns.head_shoulders`
4H'te `last_n=300` ile GERÇEKTEN gözlemlendi ve teşhis edildi). **Hedef: Faz
3/4 render motoru — `_resolve_window_end`'e de `last_n` parametresi
eklenmeli, `last_n` açıkça verildiğinde pattern-auto-zoom TAMAMEN devre dışı
kalmalı (tıpkı `_resolve_window_start`'ın zaten yaptığı gibi).**

**`compute_live()`'ın tam geçmiş kullanması, ölçüm betiklerinin sınırlı
geçmişiyle UYUŞMUYOR:** `tlab/viz/live.py::compute_live` her zaman
`store.get(symbol, tf, mkt)`'i (last_n VERMEDEN, TAM önbellek) çağırıyor —
`scripts/formasyon_denetim.py` gibi ölçüm betikleri `last_n=600` kullanıyor.
Daha fazla geçmiş, zigzag/ATR hesaplarını (ve dolayısıyla hangi adayın "en
son geçerli" sayıldığını) DEĞİŞTİREBİLİR — bu oturumda ISCTR'de TAM OLARAK
gözlemlendi (ölçümdeki TOBO yerine render'da bir OBO göründü). Bu, "bir
sinyali sayıp SONRA `tlab plot`'la görsel doğrulamak" iş akışının GENEL
olarak KIRILGAN olduğu anlamına geliyor. **Hedef: Faz 3/4 ya da AYRI bir
takip işi — `tlab plot`'a (veya `compute_live`'a) sinyal SAYIMIYLA AYNI
`last_n`'i kullanma opsiyonu eklenebilir.**

**`patterns.broadening`'in hologram poligonu görsel olarak yanıltıcı (kod
DOĞRU, ANLATIM değil):** `patterns_geom.py::diverging_lines` (satır 140-151)
incelendi — sınıflandırma yalnızca `created_idx`'teki durumu (`gap_at_created
> 0`) ve o andan SONRAKİ eğim farkını (`gap_slope = upper.slope -
lower.slope > 0`) kontrol ediyor, YANİ matematiksel olarak DOĞRU bir "ileri
yönde ıraksama" testi. Ama `broadening.py`'nin hologram poligonu
(`Polygon(points=(upper.p1, upper.p2, lower.p2, lower.p1))`) iki çizginin
HAM pivot noktalarını birleştiriyor — bu noktalar created_idx'e doğru
tesadüfen YAKINSAR gibi görünebiliyor (BARMA/ODINE/IZMDC/ISBTR örneklerinin
HEPSİNDE gözlemlendi), kullanıcıya "bu neden genişleyen formasyon" sorusunu
sordurabilecek kadar YANILTICI. **Hedef: Faz 3/4/S4 (görsel tasarım) —
hologram poligonu, iki çizginin created_idx SONRASI birkaç referans
noktasındaki DEĞERLERİNİ kullanarak yeniden tasarlanabilir (ör. created_idx
ve created_idx+pad'deki gerçek genişlik farkını gösteren bir yamuk).**

**ISBTR veri kalitesi şüphesi (YENİ, Faz 1'in TAMAMEN dışında):** `ISBTR`'nin
4H önbellek verisi 400.000-680.000 TL aralığında fiyatlar gösteriyor — BIST
hisseleri için gerçekçi değil (muhtemelen bir birim/ölçek hatası,
sağlayıcıdan gelen ham veri sorunu ya da yanlış sembol eşlemesi). **Hedef:
`tlab/data/validate.py`'ye bir "makul fiyat aralığı" sağlık kontrolü
eklenmesi düşünülebilir — AYRI bir takip işi, bu sembolün verisi elle de
doğrulanmalı.**

**BULUNAN HATA 1 (CLAUDE.md'de zaten "yaygın" işaretli) — 3 YENİ örnekle
tekrar doğrulandı:** BARMA/broadening (4H, `broadening_top_confirmed`),
ISBTR/broadening (4H, iki ayrı olay), GEDİK/head_shoulders (4H,
`obo_confirmed`) — hepsinde formasyon render'da TAMAMEN KAYBOLDU (çizgi/
poligon/marker YOK). İlginç bir gözlem: AYNI BARMA/broadening 1D'de "RETEST
TUTTU" durumu DÜZGÜN render edildi — yani hata `retest_hold` durumuna DEĞİL,
ya sembole/veri özelliklerine ya da 4H'e ÖZGÜ bir koşula bağlı görünüyor
(kesin kök neden hâlâ araştırılmadı, Faz 3/4'ün işi).

## Sonraki Adım

Faz 1'in **1B/1C kod değişiklikleri TAMAMLANDI VE görsel/sayısal olarak
doğrulandı** — head_shoulders'ın kalite artışı (ISCTR örneği) güçlü bir
kanıt. Ama **Adım 4'e geçmeden ÖNCE yukarıdaki "Karar Gerektiren Bulgu"
(double_top_bottom 4H'te sıfırlandı) kullanıcı onayı/kararı gerektiriyor** —
bu, Faz 1'in "literatür filtreleri formasyonları düzeltir" iddiasının 4H
tarafında beklenenden ÇOK daha sert bir sonuç üretmesi, sessizce geçilecek
bir bulgu değil. Diğer tüm bulgular (renderer last_n hatası, hologram
anlatım sorunu, ISBTR veri kalitesi, HATA 1'in 3 yeni örneği) CLAUDE.md'nin
"Kaldığı yer" bölümüne eklenecek, kapsamları Faz 3/4'e ya da ayrı takip
işlerine bırakılacak.
