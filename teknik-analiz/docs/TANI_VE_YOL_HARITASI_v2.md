# QuaxisLabs / Teknik Analiz — Tanı ve Yol Haritası v2

**Tarih:** 2026-09-03 · **Kapsam:** `teknik-analiz/` (tlab + web) · **Durum:** 560 test yeşil, Faz 0–8E + 10 tamam, arayüz Faz 3'te takılı

Bu belge iki parçadan oluşur:
1. **TANI** — sistemi baştan sona taradıktan sonra bulunan kök nedenler, her biri kanıtla (kod satırı, Monte Carlo, literatür).
2. **YOL HARİTASI** — 9 faz, her fazın sonunda Sonnet'e olduğu gibi yapıştırılacak **eksiksiz prompt** ve **bitti sayılma kriteri**.

Tasarım referansı repoya alındı: **`docs/design/grafik_stil_vitrini.html`** — 19 grafik türünün tamamının çalışan SVG üreteci. Bundan sonra "artifact gibi görünsün" demek yerine **"bu dosyadaki `sceneXxx()` fonksiyonunu birebir Python'a çevir"** diyeceğiz. Tasarım artık bir hedef değil, **çalıştırılabilir bir şartname**.

---

## 0 · Yönetici özeti — altı kök neden

| # | Kök neden | Kanıt | Faz |
|---|---|---|---|
| 1 | **Plotly, bu iş için yanlış araç.** Grafikler artifact'e benzemiyor çünkü artifact saf SVG, sistem ise Plotly+kaleido. | `renderer.py` 2884 satır ve büyük kısmı Plotly'yi yenmeye çalışan el yapımı declutter/stagger sezgileri; CLAUDE.md'de belgelenmiş 3 ayrı "Plotly'nin sessizce yaptığı şey" hatası | 3, 4 |
| 2 | **Klasik formasyonlarda kural eksik, geometri gevşek.** Çift dip 5 bar arayla, %2 toleransla, ön trend şartı olmadan kabul ediliyor. | `double_top_bottom.py:60-68`; literatürde 22 bar + %1.5 + düşen ön trend + %10 ara yükseliş | 1 |
| 3 | **Sinyal tazeliği diye bir kavram yok.** 6 ay önceki bir "confirmed" bugün "AL sinyali geldi" olarak listeleniyor. | `results.py::latest_signals` — `bar_time` üzerinde HİÇBİR filtre yok; ALTNY ekran görüntüsü (Temmuz formasyonu, Eylül grafiği) | 0 |
| 4 | **Arbitraj testi istatistiksel olarak yanlış + çoklu-test düzeltmesi yok.** 8754 testten 606 "doğrulanmış çift" = %6.9; gürültünün kendi oranı %3.2–4.0. | Monte Carlo (aşağıda) + BH-FDR: 606 → **36** | 2 |
| 5 | **Evren taraması (alpha dağılımı, momentum ısı haritası) CLI'da var, web'de yok.** | `tlab/viz/universe_charts.py` yazılmış; `web/backend/routes/` altında karşılığı yok | 6 |
| 6 | **Görsel doğrulama döngüsü yok.** Kartlar için zorunlu (`kart-tasarim-sistemi` skill'i), grafikler için hiç yok — Sonnet kendi çizdiği grafiği hiç görmedi. | `.claude/skills/` altında grafik karşılığı yok; `teknik-analiz/.claude/` klasörü hiç yok | Araçlar |

---

## 1 · TANI

### 1.1 Grafikler neden artifact'e benzemiyor

Sorun yetenek değil, **araç seçimi**. Artifact 1975 satırlık düz SVG ile her pikseli kontrol ediyor; sistem ise Plotly'nin annotation motorunu kullanıyor. Plotly'de **olmayan** ve artifact'in her sahnede kullandığı şeyler:

- **Etiket çakışma çözücü.** Plotly'de yok. `renderer.py` bunun yerine `_stagger_yshifts` diye elle yazılmış bir "cetvel" sezgisi ve `_declutter_levels` diye bir "en güncel olan hariç hepsini gizle" kuralı taşıyor. Yani problem, çözülmek yerine **bilgi silinerek** bastırılmış.
- **Önder çizgili (leader line) etiket kutuları.** Artifact'te `KIRILIM`/`RETEST` kutuları mum kalabalığının dışına çıkıp noktaya ince bir çizgiyle bağlanıyor (`sceneClassicPatterns`, satır ~695). Plotly'nin `add_annotation(arrowhead=...)`'ı bu görünümü vermiyor.
- **Hap (pill) rozetler.** Sabit yükseklik, iç boşluk, yuvarlak köşe, dolgu + kontrast metin. Plotly annotation'ında `bgcolor` var ama padding/radius/tipografi kontrolü yok.
- **Dolgulu giriş üçgeni + kalın `AL`.** Artifact `svgPoly('polygon', ...)` ile çiziyor; Plotly'de marker sembolü ile yaklaşık bir taklit yapılıyor.
- **Sahneye özel yerleşim.** Artifact'te `twoUp` (yan yana iki panel), sağ dikey hacim profili, alt panel oranları — her sahne kendi `makeChart({marginL, marginR, ...})`'ını kuruyor. Plotly `make_subplots` bu esnekliği vermiyor.

Ayrıca CLAUDE.md'nin kendisi Plotly'nin üç ayrı sessiz tuzağını belgeliyor: `add_vrect(row=)` ilk trace'ten önce **sessizce hiçbir şey yapmıyor**; kaleido'nun orjson encoder'ı `pd.Timestamp`'te çöküyor; `_FILL_STYLE_COLOR` ters eşlemesi aylarca fark edilmedi. Bunlar tek tek düzeltildi ama **hepsi aynı kategoriden**: araç, çizdiğin şeyi sana göstermiyor.

**Hız tarafı da aynı yere bakıyor.** `fig.to_image()` her çağrıda kaleido üzerinden bir headless Chromium turu demek. Saf SVG üretimi ölçüldü: **300 mumluk bir grafiğin mum gövdeleri 0.46 ms**. Tüm overlay/etiket/yerleşim katmanı 10x maliyet getirse bile grafik başına ~5 ms — kaleido'nun iki-üç mertebe üstünde.

> **Karar:** `tlab/viz/renderer.py` (Plotly) yerine `tlab/viz/svg/` (saf SVG) yazılacak. Aynı `IndicatorResult` primitif modeli, aynı "renderer hesap yapmaz" ilkesi — sadece çizim arka ucu değişiyor. Plotly bir süre `--engine plotly` altında geri-uyumluluk için kalır, sonra silinir.

### 1.2 Klasik formasyon motorunda kural eksikleri

**Çift Tepe / Çift Dip** (`tlab/indicators/patterns/double_top_bottom.py`)

| Kural | Şu anki kod | Literatür | Sonuç |
|---|---|---|---|
| İki uç arası mesafe | `min_bars_between = 5` | Lo–Mamaysky–Wang: **en az 22 işlem günü**; Bulkowski: "birkaç hafta" | 5 barlık bir titreşim "çift dip" sayılıyor — **kullanıcının "çift dip göremiyorum" şikayetinin doğrudan sebebi** |
| İki ucun fiyat farkı | `eq_tol = 0.02` (%2) | LMW: ortalamanın **%1.5**'i; Bulkowski istatistik için **%4**, pratikte %6 | Kabul edilebilir ama gevşek uçta |
| Ön trend | **YOK** | Bulkowski: çift dipten önce **düşen bir trend** şart | Yükseliş içinde oluşan iki eşit taban da "çift dip" sayılıyor |
| İki dip arası yükseliş | **YOK** | Bulkowski: **en az %10** | Dümdüz bir taban "çift dip" oluyor |
| Minimum derinlik | **YOK** | — | ATR'ye/fiyata göre önemsiz derinlikteki formasyonlar geçiyor |
| Hacim | `volume_ok` payload'a **yazılıyor ama filtrelenmiyor** | Kırılım hacmi 20-periyot ortalamanın %5–10 üstü | Filtre yok |
| Hologram | Gerçek kapanış yolunu izliyor (`path_idxs`) | — | Geometrik olarak doğru ama **görsel olarak amorf** — ALTNY görselindeki mavi leke tam da bu |

**Omuz-Baş-Omuz** (`head_shoulders.py` + `features/hs_pattern.py`)

- `neck_slope_max = 0.01` **bar başına** uygulanıyor: `abs(neck_slope)/avg_price > 0.01`. 40 barlık bir formasyonda bu, boyun çizgisinin toplamda **%40** eğilebileceği anlamına gelir. "Yaklaşık yatay boyun" kuralı fiilen hiçbir şeyi elemiyor. **Doğrusu: toplam eğimi formasyon süresine göre normalize etmek.**
- Yukarı eğimli boyunlu formasyonlar tamamen **eleniyor**. Bulkowski'nin kuralı bunları elemek değil, **farklı bir tetik kullanmak**: yukarı eğimli boyunda sinyal, boyun çizgisi değil **sağ koltukaltı tepesinin** kapanışla aşılmasıdır.
- Ön trend şartı **yok** (OBO yükselişten sonra, TOBO düşüşten sonra gelmeli).
- Minimum derinlik şartı **yok** — ZOREN görselindeki formasyonun derinliği fiyatın ~%3'ü; bu, 4H gürültüsünden ayırt edilemez.
- Hacim profili (sol omuz/baş yüksek, sağ omuz düşük) `volume_profile_ok` olarak **yazılıyor ama filtrelenmiyor**.

**Tutarlılık boşluğu:** `broadening.py` içinde `prior_trend_lookback: int = 20` **var**. Yani ön-trend kontrolü deseni projede zaten mevcut, sadece iki ana formasyona uygulanmamış.

### 1.3 Sinyal tazeliği — sistemin en ucuz ve en etkili hatası

`tlab/scanner/results.py::latest_signals` her `(symbol, timeframe, indicator, pattern_id)` zincirinin en son satırını döndürüyor ve `state IN ('confirmed','completed')` ile filtreliyor. **`bar_time` üzerinde hiçbir kısıt yok.** Sonuç: Temmuz'da onaylanmış bir formasyon, Eylül'deki taramada "AL sinyali geldi" olarak listeleniyor.

ALTNY ekran görüntüsü tam olarak bunu gösteriyor: Temmuz–Ağustos arası bir yapı, "ÇİFT DİP (RETEST TUTTU)" etiketiyle Eylül grafiğinde duruyor.

Kullanıcının istediği model açık: **"son mumda sinyal", ya da lookback varsa "son N mumda sinyal"**. Bu, tarama motorunda tek bir filtre + arayüzde tek bir sütun ("kaç mum önce") demek.

### 1.4 Arbitraj — asıl büyük bulgu

#### (a) İsimlendirme: sistemde "arbitraj" olarak geçen şey arbitraj değil

Kullanıcının işaret ettiği kaynakta (`awesome-quant-ai/book/myquant/chapter3.md`) **arbitraj** = nakit-vadeli arbitrajı, put-call paritesi (conversion/reverse conversion), dönüştürülebilir tahvil arbitrajı. Bunlar gerçekten **nadir sinyal veren**, fiyatlama ilişkisine dayalı, neredeyse risksiz stratejilerdir. Pair trading / kointegrasyon **chapter2**'de ve adı **istatistiksel arbitraj** — risksiz değil, "ortalamaya dönüş bahsi". Sistemdeki `pair.*` göstergeleri ikinci kategoriden. Bu ayrım arayüzde de yapılmalı ("İstatistiksel Arbitraj"), yoksa beklenti hep yanlış kalibre olur.

#### (b) GERÇEK HATA — ham ADF, tahmin edilmiş kalıntı üzerinde kullanılıyor

`tlab/features/stats.py::adf_pvalue` ham `statsmodels.tsa.stattools.adfuller`'ı çağırıyor ve `discovery.py` bunu **OLS ile tahmin edilmiş** bir β'dan üretilmiş spread'e uyguluyor. Bu, ekonometrinin klasik hatalarından biri: OLS kalıntısı **kareler toplamını minimize edecek şekilde seçildiği için** durağan görünmeye eğilimlidir. Standart ADF kritik değerleri bu durumda geçersizdir; **Engle-Granger / MacKinnon kritik değerleri** gerekir (`statsmodels.tsa.stattools.coint`).

**Monte Carlo ile ölçüldü** (400 deneme × 3 örneklem boyu, iki **bağımsız** rastgele yürüyüş — yani gerçek kointegrasyon YOK):

| n (bar) | corr ≥ 0.7 | ham `adfuller` p<.05 | doğru `coint` p<.05 | **tlab tam boru hattı** | düzeltilmiş boru hattı |
|---|---|---|---|---|---|
| 250 | %9.5 | **%16.8** | %8.8 | **%3.2** | %1.8 |
| 500 | %12.5 | **%18.5** | %7.0 | **%4.0** | %2.2 |
| 750 | %13.5 | **%13.8** | %5.5 | **%3.5** | %1.2 |

Nominal seviye %5 iken ham ADF **%14–18** reddediyor: **yaklaşık 3 kat aşırı-reddetme**.

#### (c) GERÇEK HATA — "iki yönü de dene, düşük p'yi al" alfa şişiriyor

`discover_pairs` her çift için hem `Y~X` hem `X~Y` deniyor ve **daha düşük p-değerlisini** raporluyor. İki testin minimumunu almak, tek testin nominal seviyesini korumaz — efektif α ≈ `1-(1-0.05)² ≈ 0.0975`. Yön-bağımlılık gözlemi doğru; çözümü "en iyisini seç" değil, **seçilen yön için düzeltme uygulamak** (ör. iki p'nin minimumuna Šidák/Bonferroni düzeltmesi) ya da simetrik bir test (Johansen) kullanmak.

#### (d) GERÇEK HATA — çoklu-test düzeltmesi yok. Bu, "çok fazla sinyal"in asıl sebebi.

`config/pairs.yaml`'daki 606 çift, `config/sectors_bist.yaml`'daki 44 sektör × 637 sembol üzerinde **8754 aynı-sektör kombinasyonu** denenerek bulunmuş. Kayıtlı `adf_p` değerleri üzerinden hesaplandı:

| Kriter | Hayatta kalan çift |
|---|---|
| Şu anki kural: `p < 0.05`, düzeltme yok | **606** |
| Benjamini–Hochberg FDR, q = 0.20, M = 8754 | 171 |
| Benjamini–Hochberg FDR, q = 0.10, M = 8754 | 82 |
| **Benjamini–Hochberg FDR, q = 0.05, M = 8754** | **36** |
| Bonferroni, α = 0.05 / 8754 | 19 |

Ve bu p-değerleri hâlâ **(b)'deki 3 kat şişkin testten** geliyor. Doğru testle yeniden koşulduğunda sayı daha da düşecek.

Çapraz kontrol: 606 / 8754 = **%6.9**. Monte Carlo'daki saf gürültü oranı **%3.2–4.0**. Yani mevcut listenin **kabaca yarısı, hiçbir gerçek kointegrasyon olmasa bile beklenen** sayıda. (Gerçek hisselerde ortak piyasa faktörü korelasyonları yükselttiği için gerçek oran muhtemelen daha kötü.)

**606 → ~20–40. Kullanıcının sezgisi doğruydu.**

#### (e) Spread'de sabit terim (intercept) yok

`rolling_beta` cov/var ile eğimi hesaplıyor (ki bu, sabitli OLS'in eğimidir) ama `log_spread` sadece `log(y) − β·log(x)` yapıyor — **α çıkarılmıyor**. Test edilen seri gerçek OLS kalıntısı değil. `adfuller`'ın varsayılan `regression='c'`'si ortalamayı soğurduğu için sonuç felakete dönüşmüyor ama tutarsız; `coint(..., trend='c')` bunu doğru yapar.

#### (f) `RelativeMomentumPair` bir arbitraj motoru değil, bir rotasyon motoru

Referans uygulamada (chapter2) olan, tlab'da **olmayan** dört kontrol:

| Kontrol | Referans | tlab |
|---|---|---|
| Çıkış (kâr al) | `|z| < 0.5` → pozisyonu kapat | **Yok** — her zaman ya Y ya X'te %100 long |
| Zarar kes | `|z| > 3.0` → zorunlu tasfiye | **Yok** |
| Zaman stopu | 30 gün sonra kapat | **Yok** (`max_bars_to_target` diğer göstergelerde var, burada yok) |
| Stop sonrası kilit | z bandın içine dönene kadar yeni giriş yok | **Yok** |
| β tahmini | in-sample eğitim penceresi, işlem out-of-sample | Aynı pencerede rolling β |

"Nakit/flat" hâli olmadığı için strateji **her zaman** piyasa beta'sına maruz. Bu, market-neutral istatistiksel arbitraj **değil**; CLAUDE.md backlog'undaki 5. madde bunu zaten tespit etmiş ama uygulanmamış.

#### (g) Sektör-içi mi, tüm evren mi? — Araştırma sonucu: **sektör-içi doğru tercih**

Kullanıcının "takip ettiğim quant tüm evreni tarıyordu" gözlemi doğru — Gatev–Goetzmann–Rouwenhorst (2006) tüm likit ABD hisselerini tarar. Ama:

- **Do & Faff (2010)**, GGR'yi 1962–2009'a genişleterek şunu buluyor: **getiriler, strateji sektör-içi çiftlerle sınırlandığında en yüksek**; daha ince sektör sınıflandırması performansı **daha da** artırıyor. Gerekçe: aynı sektördeki iki hisse birbirinin gerçek ikamesi olduğu için **yakınsama olasılığı** yüksek.
- İstatistiksel gerekçe daha da güçlü: BİST 648 sembol → tüm evren **209.628** çift; sektör-içi **8.754** çift. Çoklu-test yükü **24 kat** düşüyor. Aynı FDR seviyesinde sektör-içi tarama çok daha fazla gerçek çift bulur.

**Öneri:** sektör kısıtı **kalsın**, ama üç ekle: (1) sektör haritasının kaçırdığı **ekonomik bağları** ayrıca beyaz-listele (holding–iştirak, aynı endeks, aynı emtia); (2) FDR düzeltmesi uygula; (3) çift keşfini **out-of-sample doğrula** — keşif penceresinde bulunan çiftin sonraki pencerede hâlâ kointegre kalması şart.

### 1.5 Evren taraması web'de yok

`tlab/viz/universe_charts.py::render_alpha_scatter` ve `render_momentum_heatmap` yazılmış, `tlab universe-plot` komutu çalışıyor. `web/backend/routes/` altında karşılığı **yok** — `/scan` sayfası yalnızca tekil-sembol sinyallerini listeliyor. Artifact'teki "Alpha Dağılımı" ve "Momentum Isı Haritası" sahneleri bu iki fonksiyonun görsel hedefi.

### 1.6 Süreç boşluğu — grafiklerin görsel doğrulama döngüsü yok

`bilanco-radar` tarafında `kart-tasarim-sistemi` skill'i **zorunlu bir döngü** dayatıyor: "değişiklik → PNG üret → **PNG'yi Read ile aç ve GÖR** → sorunları listele → düzelt, en az 3 iterasyon, en az 3 veri durumu". `teknik-analiz/` altında `.claude/` klasörü **hiç yok**. Yani grafik tarafında Sonnet:

- kendi çizdiği grafiği hiç görmedi,
- karşılaştıracağı onaylı bir referans görüntüsü yoktu,
- bir tasarım gerilemesini yakalayacak bir test yoktu.

Model kapasitesi değil, **kapalı devre geri bildirim eksikliği**. Bu, Faz 3–4'ten önce kapatılmalı.

---

## 2 · YOL HARİTASI

Sıra bilinçli: **önce doğru sinyal, sonra güzel resim.** Yanlış formasyonun kusursuz çizimi iki kere iş demek.

| Faz | Konu | Süre | Bağımlılık |
|---|---|---|---|
| 0 | Tazelik + hızlı kazanımlar + tasarım altyapısı | 1 oturum | — |
| 1 | Klasik formasyon motoru v2 | 2 oturum | 0 |
| 2 | İstatistiksel arbitraj v2 | 2 oturum | 0 |
| 3 | SVG çizim motoru (çekirdek) | 2 oturum | 0 |
| 4 | 19 sahnenin portu | 3 oturum | 3, 1 |
| 5 | Kalan stratejilerin denetimi | 2 oturum | 1, 2 |
| 6 | BİST Evren Taraması sayfası | 2 oturum | 3, 4 |
| 7 | Web arayüzü + 3 tema + hız | 2 oturum | 4 |
| 8 | Doğrulama harness'ı (backtest) | 2 oturum | 1, 2, 5 |

Faz 1, 2 ve 3 **paralel** yürütülebilir (farklı dosyalara dokunuyorlar). Faz 4 hem 3'ü hem 1'i bekler.

---

### Her promptun başına yapıştırılacak ortak blok

```
ORTAK BAĞLAM — QuaxisLabs / teknik-analiz

Çalışma dizini: teknik-analiz/. Önce CLAUDE.md'yi oku (mimari + ilerleme durumu),
sonra docs/TANI_VE_YOL_HARITASI_v2.md'nin TANI bölümünü oku — bu görev oradaki
bir bulguyu kapatıyor.

MÜZAKEREYE KAPALI KURALLAR:
1. NON-REPAINTING. Bir sinyalin t barındaki değeri yalnızca t ve öncesi veriyle
   hesaplanır, sonradan değişmez. Yasak: df.shift(-n), rolling(center=True),
   find_peaks/argrelextrema sonucunu doğrudan sinyal barına yazmak, kapanmamış
   barla sinyal üretmek. Her indikatör tlab/testing/repaint.py::repaint_test'ten
   geçmeden "tamam" sayılmaz.
2. KATMAN AYRIMI: data -> features -> indicators -> scanner -> results -> viz.
   Oklar tek yönlü. viz KATMANI HESAP YAPMAZ.
3. Mevcut 560 test yeşil kalacak (pytest -q -m "not network"). Kırılan her test
   ya düzeltilir ya da NEDEN artık geçersiz olduğu yazılı gerekçeyle güncellenir;
   sessizce silinmez/skip edilmez.
4. Sihirli sayı yasak. Her eşik ya bir parametre dataclass'ında varsayılan olarak
   yaşar ya da kaynağı (kitap/makale/ölçüm) docstring'de yazılıdır.
5. Bulduğun GERÇEK hataları (bu görevin kapsamı dışında olsa bile) düzeltme —
   docs/PROGRESS_LOG.md'ye "BULUNAN HATA" başlığıyla yaz, bana bildir.
6. İş bitince CLAUDE.md'nin "İlerleme Durumu" özetini ve docs/PROGRESS_LOG.md'yi
   güncelle.
```

---

## FAZ 0 — Sinyal tazeliği, hızlı kazanımlar, tasarım altyapısı

**Amaç:** Günlük kullanımı bugün bozan tek şeyi (bayat sinyaller) düzeltmek ve sonraki fazların dayanacağı tasarım/doğrulama altyapısını kurmak.

**Neden ilk:** Tazelik filtresi bir günlük iş ama "sinyal kovalıyorum" iş akışının tamamını düzeltiyor. Tasarım altyapısı (skill + agent + golden test) Faz 3–4'ün ön koşulu; kurulmazsa Faz 4 yine "güzel görünmedi" ile biter.

**Bitti kriteri:** `/scan` sadece son N mumda oluşmuş sinyalleri listeliyor ve her satırda "kaç mum önce" görünüyor; `teknik-analiz/.claude/` altında grafik skill'i + agent'ı var; `tests/test_viz/golden/` altında en az 3 onaylı SVG/PNG referansı ve bunları karşılaştıran bir test var.

```
[ORTAK BAĞLAM bloğunu buraya yapıştır]

GÖREV — FAZ 0: Sinyal tazeliği + tasarım doğrulama altyapısı

Üç iş var, sırayla yap ve her birinden sonra pytest -q -m "not network" koş.

--- İŞ 1: SİNYAL TAZELİĞİ (en önemli) ---

Sorun: tlab/scanner/results.py::latest_signals bir sinyal zincirinin en son
satırını döndürüyor ama bar_time üzerinde HİÇBİR yaşlılık filtresi yok. Aylar
önce onaylanmış bir formasyon bugünkü taramada "AL sinyali geldi" olarak
listeleniyor (gerçek örnek: ALTNY 4H, Temmuz'da doğmuş bir çift dip Eylül
taramasında hâlâ taze gibi görünüyor). Kullanıcının istediği iş akışı net:
"bana AL sinyali gelecek, ben grafiğe bakacağım ve SON MUMDA o sinyali
göreceğim; lookback varsa son N mumda oluşanları göreceğim."

Yapılacaklar:
1. ResultsStore'a sinyalin YAŞINI hesaplayacak bir mekanizma ekle. Yaş, takvim
   günü DEĞİL BAR sayısı olmalı (4H ile 1D aynı ölçüyle karşılaştırılamaz).
   En temiz yol: runs tablosuna (ya da yeni bir bars tablosuna) her
   (market, timeframe) için o koşudaki SON KAPALI BAR'ın zamanını yazmak, sonra
   signals.bar_time ile aradaki bar sayısını takvimden (tlab/data/calendar.py)
   hesaplamak. Takvim çözümü karmaşık gelirse alternatif: scanner/engine.py
   sinyali kaydederken payload'a bars_ago yazsın (o an df'nin uzunluğunu
   biliyor) — bu daha basit ve KESİN doğru. İkisinden hangisini seçtiğini
   gerekçesiyle yaz.
2. latest_signals'a `max_bars_ago: int | None = None` parametresi ekle.
   None = eski davranış (geriye dönük uyumlu). Bir sayı verilirse yalnızca
   o kadar veya daha yeni sinyaller döner.
3. Dönen her satıra `bars_ago` alanını ekle.
4. web/backend/routes/scan.py::list_signals'a `max_bars_ago` query parametresi
   ekle, VARSAYILANI 3 yap (kullanıcının kendi ifadesi: "son 3 mumda olan
   sinyalleri göreceğim"). Yanıttaki her sinyale bars_ago'yu koy.
5. web/frontend/app/scan/page.tsx: "Tazelik" adında bir seçici ekle
   (Son 1 mum / Son 3 mum / Son 10 mum / Tümü) ve tabloya "Yaş" sütunu
   ("son mum" / "3 mum önce" gibi). Varsayılan: Son 3 mum. Tabloyu bars_ago'ya
   göre artan sırala (en taze en üstte).
6. Testler: latest_signals'ın max_bars_ago ile doğru filtrelediğini, None ile
   eski davranışı koruduğunu, bars_ago'nun doğru hesaplandığını doğrulayan
   en az 4 test.

DİKKAT: Bu bir görüntüleme filtresi, sinyal üretimi değil. Veritabanına yazılan
hiçbir şey değişmiyor, zincir bütünlüğü bozulmuyor.

--- İŞ 2: GRAFİK TASARIM SKILL'İ VE AGENT'I ---

teknik-analiz/ altında .claude/ klasörü YOK. bilanco-radar tarafında
.claude/skills/kart-tasarim-sistemi/SKILL.md var ve ZORUNLU bir görsel doğrulama
döngüsü dayatıyor ("PNG üret -> PNG'yi Read ile AÇ ve GÖR -> düzelt, en az 3
iterasyon"). Grafik tarafında bunun karşılığı hiç olmadı — bu yüzden aylardır
"grafikler istediğim gibi olmuyor" döngüsünden çıkılamıyor.

1. teknik-analiz/.claude/skills/grafik-tasarim-sistemi/SKILL.md yaz. İçeriği:
   - Tasarım referansı: docs/design/grafik_stil_vitrini.html (repoda). Bu dosya
     19 grafik türünün ÇALIŞAN SVG üretecidir; THEMES sabiti (classic/dark/
     editorial/saas/neon) ve sceneXxx() fonksiyonları OKUNARAK uygulanır,
     yeniden icat EDİLMEZ.
   - Kullanılacak 3 tema: classic (Klasik Beyaz Rapor), dark (Terminal Koyu),
     editorial (Kağıt Rapor). saas ve neon KAPSAM DIŞI.
   - Token kuralı: hardcoded renk YASAK, her renk tlab/viz/themes.py::Theme
     alanından gelir. Bu dosyadaki DARK_TERMINAL/LIGHT_ANALYSIS/KAGIT_RAPORU
     hex değerleri artifact'in THEMES'i ile ZATEN eşleşiyor — doğrula, sapma
     varsa artifact'i doğru kabul et.
   - Tipografi: sayısal her şey mono + tabular-nums; Türkçe glifler (İıĞğŞşÇçÖöÜü)
     render testinden geçmeli.
   - Etiket yerleşimi sözleşmesi: hiçbir metin başka bir metinle çakışmaz;
     mum bulutunun üstüne düşen etiket dışarı çıkarılıp önder çizgiyle bağlanır;
     rozetler hap (pill) formunda, sabit iç boşluklu.
   - ZORUNLU DOĞRULAMA DÖNGÜSÜ: değişiklik -> gerçek veriyle grafik üret ->
     çıktıyı Read ile AÇ ve GÖR -> gördüğün sorunları MADDE MADDE yaz -> düzelt.
     En az 3 iterasyon. En az 3 veri durumu: bol sinyalli sembol, tek/hiç sinyalli
     sembol, çok uzun geçmişli sembol (çakışma stresi).
2. teknik-analiz/.claude/agents/grafik-tasarimcisi.md yaz — kart-tasarimcisi.md'yi
   örnek al, alanı grafik/SVG/renderer olacak şekilde uyarla. Araçları:
   Read, Write, Edit, Bash, Glob, Grep.

--- İŞ 3: GÖRSEL GERİLEME (GOLDEN) TESTİ ---

Tasarım gerilemeleri şu an ancak kullanıcı fark edince yakalanıyor.

1. tests/test_viz/golden/ klasörü aç.
2. tests/test_viz/test_golden.py yaz: sabit (SENTETİK, deterministik — gerçek
   veri değil, ağ bağımlılığı OLMAYACAK) bir OHLCV fixture'ı üzerinde en az 3
   gösterge için çizim çıktısı üretip golden/ altındaki onaylı dosyayla
   karşılaştırsın. Şu an Plotly olduğu için karşılaştırma fig.to_dict()'in
   kararlı (normalize edilmiş) bir JSON'ı üzerinden yapılabilir; Faz 3'te SVG
   motoruna geçildiğinde karşılaştırma doğrudan SVG metni üzerinden olacak
   (testi buna hazır yaz: karşılaştırma fonksiyonunu ayrı tut).
3. pytest --update-golden bayrağı ekle (conftest.py) — onaylı çıktıları
   yeniden üretmek için. Bayrak OLMADAN test asla golden dosyayı yazmaz.

BİTTİ KRİTERİ:
- /scan varsayılan olarak son 3 mumdaki sinyalleri gösteriyor, "Yaş" sütunu var.
- teknik-analiz/.claude/ altında skill + agent var.
- pytest -q -m "not network" yeşil, en az 7 yeni test.
- CLAUDE.md ve docs/PROGRESS_LOG.md güncel.
```

---

## FAZ 0.5 — Sistemik düzeltmeler (denetim sonrası EKLENDİ)

> **2026-09-03 güncellemesi.** Tüm göstergelerin tam denetimi yapıldı — sonuçlar **`docs/STRATEJI_DENETIM_TAM.md`**'de. Denetim, tek tek gösterge hatalarından **önce** kapatılması gereken üç sistemik sorun ortaya çıkardı. Bu faz onlar için; Faz 1'den önce yapılmalı, yoksa Faz 1'de kalibre edilen her eşik yanlış bir zigzag üstünde kalibre edilmiş olur.

**Bitti kriteri:** Tüm formasyon göstergeleri ortak, önem-filtreli bir pivot girişinden besleniyor; bar cinsinden her parametre zaman dilimine göre ölçekleniyor; `supported_timeframes` sözleşmesi tarama motorunda uygulanıyor; hacim onayı bir parametre olarak var.

```
[ORTAK BAĞLAM bloğunu buraya yapıştır]

GÖREV — FAZ 0.5: Sistemik düzeltmeler

ÖNCE OKU: docs/STRATEJI_DENETIM_TAM.md bölüm A (A1/A2/A3/A4). Bu görev o dört
bulguyu kapatıyor. Hiçbiri tek bir göstergenin hatası değil -- dördü de tüm
sistemi aynı anda etkiliyor.

--- A1: PİVOT GÜRÜLTÜSÜ ---

Sistemdeki HER formasyon tek bir zigzag üstüne kurulu:
find_pivots(df, left=3, right=3) -> alternate_pivots(...). Ölçüldü: bu
varsayılan 100 barda ~14.5 pivot, ortalama bacak 6.9 bar üretiyor. 4H'te bu
BİR GÜNDEN KISA -- yani sistemin "swing" dediği şey bir günlük dalgalanma.
Bir çift dibin iki dibi 1 gün arayla oluşabiliyor.

tlab/features/swings.py::atr_zigzag ZATEN yazılmış ve test edilmiş (ATR katı
kadar ters dönüş ister -- ÖLÇEK BAĞIMSIZ, 4H'te ve 1D'de aynı ekonomik
anlamı taşır). atr_zigzag(mult=3.0) ölçümde 100 barda 4.3 pivot / 23.0 barlık
bacak veriyor -- gerçek bir yapısal swing.

Ayrıca structure/golden_zone.py'de min_swing_atr=3.0 ZATEN var ve doğru iş
yapıyor. Yani çözüm deseni projede MEVCUT, yayılmamış.

Yapılacaklar:
1. tlab/features/swings.py'ye ORTAK giriş ekle:
     significant_pivots(df, method="atr", *, left=3, right=3,
                        atr_mult=3.0, atr_period=14,
                        min_swing_atr=None) -> list[Pivot]
   method="fixed" -> find_pivots + (min_swing_atr verilmişse) önemsiz
   bacakları eleyen bir filtre; method="atr" -> atr_zigzag. İkisi de
   alternate_pivots'tan geçirilmiş, kesinleşmiş pivot döner.
   min_swing_atr filtresi golden_zone.py'de ZATEN uygulanan mantıkla AYNI
   olsun -- o kodu buraya taşı ve golden_zone da buradan kullansın (tekrar
   YOK).
2. ŞU göstergeleri bu ortak girişe bağla (hepsi şu an doğrudan find_pivots
   çağırıyor): head_shoulders, double_top_bottom, golden_zone, wedge,
   broadening, weekly_channel, price_structure. Her birinin Params'ına
   zigzag_method / atr_mult / min_swing_atr alanları ekle.
   harmonics ve swing_fib_abcd zigzag_method'u ZATEN sunuyor -- onların
   VARSAYILANINI "fixed"ten "atr"ye çevir.
3. VARSAYILAN KARARI: method="atr", atr_mult=3.0. Ama bu bir eşik değişikliği
   -- ÖLÇEREK doğrula (aşağıdaki D adımı).

--- A2: ZAMAN DİLİMİ ÖLÇEKLEMESİ ---

scanner/engine.py::_run_single_worker göstergeyi CATALOG[name].factory() ile,
yani VARSAYILAN parametrelerle kuruyor; run_eod(timeframes=("4h","1d")) aynı
nesneyi iki zaman diliminde de koşuyor. Bar cinsinden yazılmış her eşik 4H'te
takvim olarak 6 KAT KISA anlama geliyor:
  double_top_bottom.min_bars_between=5  -> 4H'te 0.8 gün (literatür: 22 gün)
  wedge.min_bars=15                     -> 4H'te 2.5 gün (literatür: 3 hafta)
  flag_pennant.flag_max_bars=20         -> 4H'te 3.3 gün (literatür: 3 hafta)
  momentum_rank.horizons=(21,63,126,252)-> 4H'te 3.5/10/21/42 gün
Son satır sadece gevşek değil AKADEMİK OLARAK GEÇERSİZ: Jegadeesh-Titman
momentumu 3-12 aylık bir olgudur ve kısa ufuklarda İŞARET TERSİNE DÖNER.

Yapılacaklar:
1. tlab/core/params.py'ye bar-cinsi alan işaretleme mekanizması ekle.
   En basit ve okunur yol: BaseParams'a bir sınıf değişkeni --
     _BAR_FIELDS: frozenset[str] = frozenset()
   ve bir metot --
     for_timeframe(self, tf: Timeframe) -> Self
   4H için ×6, 1H için ×24, W1 için ÷5 (1D taban kabul edilir). Ölçekleme
   round + max(1, ...) ile yapılsın. Her Params sınıfı KENDİ _BAR_FIELDS'ini
   bildirsin (double_top_bottom: {"min_bars_between","max_bars_between"},
   wedge: {"min_bars","max_apex_bars"}, vb.).
2. engine.py'nin üç worker'ı (single/pair/universe) göstergeyi kurarken
   params.for_timeframe(tf) uygulasın. Bu, factory()'nin döndürdüğü örneğin
   params'ını değiştirmek demek -- BaseIndicator'a bir with_params() ya da
   factory'ye tf parametresi ekle; hangisini seçtiğini gerekçelendir.
3. viz/live.py de AYNI ölçeklemeyi uygulasın (grafik ile tarama aynı sonucu
   üretmeli -- şu an ikisi de ölçeklemiyor, ama biri düzelip diğeri
   düzelmezse GRAFİKLE TARAMA ÇELİŞİR, bu daha kötü).

--- A3: supported_timeframes SÖZLEŞMESİ ---

Her göstergenin IndicatorMeta.supported_timeframes alanı DOĞRU doldurulmuş:
  momentum.alpha_rank    -> (D1,)
  momentum.momentum_rank -> (D1,)
  trend.weekly_channel   -> (W1, D1)
  diğerleri              -> (D1, H4)
Ama engine.py, eod.py, core/indicator.py ve viz/live.py'nin HİÇBİRİ bu alanı
okumuyor (grep ile doğrulandı: o dosyalarda sıfır eşleşme). Sonuç:
  - alpha_rank ve momentum_rank, kendi bildirdikleri sözleşmeyi ihlal ederek
    4H'te koşuyor (ve A2 nedeniyle anlamsız sonuç üretiyor).
  - weekly_channel W1'de HİÇ koşmuyor (run_eod yalnızca 4h+1d tarıyor) ama
    desteklemediği 4H'te koşuyor. "Haftalık kanal" haftalık veriyi HİÇ
    görmemiş.

Yapılacaklar:
1. engine.run(): bir (gösterge, tf) çifti için tf desteklenmiyorsa işi HİÇ
   AÇMA. Atlanan çiftleri logla ve run raporuna "skipped_unsupported" olarak
   yaz (sessizce atlama).
2. run_eod'un varsayılan timeframes'ine "w1" ekle. W1 verisi
   data/resample.py::resample_to_w1 ile ZATEN üretilebiliyor.
3. viz/live.py de aynı kapıyı uygulasın -- /chart'ta desteklenmeyen bir
   kombinasyon seçilirse net bir hata dönsün ("bu gösterge 4H'te
   çalışmıyor"), sessizce yanlış sonuç değil.
4. web/frontend: gösterge seçicide desteklenmeyen zaman dilimleri devre dışı
   görünsün (/api/catalog supported_timeframes'i döndürsün).

--- A4: HACİM ONAYI ---

Beş formasyon modülünün HEPSİNDE aynı desen var:
  confirm_sig.payload["volume_ok"] = bool(volume[idx] >= p.vol_k * vma)
Hesaplanıyor, payload'a yazılıyor, SİNYALİ HİÇ ENGELLEMİYOR. (broadening.py:201,
double_top_bottom.py:163, flag_pennant.py:200, head_shoulders.py:175,
wedge.py:246 -- beşi de yalnızca payload.)

Yapılacaklar:
1. Beş modüle de require_volume_confirm: bool = False parametresi ekle.
   True iken volume_ok False olan onay sinyali ÜRETİLMESİN (aday
   invalidated değil, sadece confirmed'a terfi etmesin).
2. config/scans.yaml'a "hacim_onayli" preset'i ekle.
3. Varsayılanı False bırak -- bu turda davranış DEĞİŞMESİN, seçenek açılsın.
   (Açık/kapalı kararı Faz 8'in ölçümüne bırakılıyor.)

--- D: ÖLÇÜM VE RAPOR (bu fazın kabul testi) ---

scripts/sistemik_denetim.py (YENİ):
1. BIST'ten en az 100 sembol, 4H + 1D. ESKİ ayarlarla (fixed 3/3, ölçekleme
   yok, tf kapısı yok) tüm göstergeleri tara, gösterge x tf başına sinyal
   sayısını say.
2. YENİ ayarlarla tekrarla.
3. Önce/sonra tablosu: gösterge x zaman dilimi x sinyal sayısı, ve elenme
   sebebi dağılımı (pivot filtresi / tf ölçeklemesi / tf kapısı).
4. atr_mult için 2.0 / 2.5 / 3.0 / 3.5 taraması yap: her değerde toplam
   sinyal sayısı ve ortalama formasyon süresi (bar). Varsayılanı BU ÖLÇÜME
   göre seç, benim önerdiğim 3.0'ı körü körüne kabul etme.
5. Yeni ayarlarla kalan sinyallerden RASTGELE 10 tanesi için tlab plot ile
   grafik üret, PNG'leri Read ile AÇ VE GÖR, her biri için "bu gerçekten bir
   <formasyon> mu?" sorusuna tek cümlelik yanıt yaz. BU ADIMI ATLAMA.
6. Sonucu docs/spec/SISTEMIK_DENETIM_v1.md'ye yaz.

BİTTİ KRİTERİ:
- significant_pivots() + 7 göstergenin ona bağlanması + testleri.
- BaseParams.for_timeframe() + engine/live entegrasyonu + testleri
  (4H'te bir parametrenin gerçekten 6x olduğunu doğrulayan test dahil).
- supported_timeframes kapısı + run_eod'a w1 + /api/catalog alanı + testleri.
- 5 modülde require_volume_confirm + preset.
- docs/spec/SISTEMIK_DENETIM_v1.md: önce/sonra tablosu, atr_mult taraması,
  10 grafiğin gözle incelenmiş yorumu.
- pytest -q -m "not network" yeşil.
```

---

## FAZ 1 — Klasik formasyon motoru v2

**Amaç:** "Çift dip diyor ama grafikte çift dip yok" şikayetini kökünden bitirmek. Formasyon tanımlarını literatüre oturtmak.

**Neden bu sırada:** Faz 4 bu formasyonları çizecek. Yanlış formasyonu güzel çizmek iki kere iş.

**Bitti kriteri:** Aynı evren + aynı zaman diliminde `patterns.*` sinyal sayısı belirgin şekilde azalmış, kalan her sinyal grafikte gözle "evet bu gerçekten çift dip" denebilir durumda; her yeni kural için parametre + test + kaynak referansı var.

```
[ORTAK BAĞLAM bloğunu buraya yapıştır]

GÖREV — FAZ 1: Klasik formasyon motoru v2 (tanım sıkılaştırma)

Kullanıcı şikayeti (birebir): "çift dip diye sinyal verdiği grafikte alakası
olmayan şeyler var, hiç çift dip göremiyorum". docs/TANI_VE_YOL_HARITASI_v2.md
bölüm 1.2 bunun neden olduğunu kural kural gösteriyor — önce onu oku.

Temel ilke: bu bir "eşik oynatma" görevi DEĞİL. Formasyon tanımlarına
literatürdeki EKSİK KURALLARI eklemek. Her yeni kural bir parametre olarak
yaşayacak (kapatılabilir) ve varsayılanı literatürden gelecek.

--- 1A: ORTAK ALTYAPI ---

tlab/features/pattern_context.py (YENİ) yaz. Formasyonların paylaşacağı üç
bağlam kontrolü, hepsi saf fonksiyon, non-repaint (yalnızca [0, born_idx]
aralığına bakar):

1. prior_trend(df, start_idx, lookback, direction) -> tuple[bool, float]
   Formasyonun BAŞLADIĞI bardan geriye lookback bar bakar; "düşen trend" için
   o pencerede fiyatın anlamlı biçimde düştüğünü doğrular. Ölçüt: log-fiyat
   üzerinde OLS eğiminin t-istatistiği (tlab/indicators/momentum/momentum_rank.py
   içindeki _rolling_trend_tstat aynı kapalı formu ZATEN taşıyor — onu features
   katmanına taşı ve ikisi de oradan kullansın; kod TEKRARLAMA).
   Gerekçe: Bulkowski, çift dip için "önce düşen bir trend" ve OBO/TOBO için
   ön trend şartı koyar.

2. pattern_depth_ok(depth, price, atr_at_birth, min_pct, min_atr) -> bool
   Formasyon derinliği HEM fiyatın min_pct'ından HEM atr_at_birth'ün min_atr
   katından büyük olmalı. İkisi birden çünkü: yüzde ölçütü düşük volatiliteli
   hisselerde çok gevşek, ATR ölçütü yüksek volatilitede çok gevşek.

3. breakout_volume_ok(volume, idx, ma_window, k) -> bool
   Kırılım barının hacmi, ma_window periyotluk ortalamanın k katından büyük mü.
   Bu fonksiyon ZATEN her formasyonda ayrı ayrı ve TUTARSIZ yazılmış
   (double_top_bottom vol_ma_window=20 kullanıyor, head_shoulders sağ omuz
   ortalamasını kullanıyor) — TEK yere topla.

Her üçü için test yaz (sentetik, deterministik veriyle).

--- 1B: ÇİFT TEPE / ÇİFT DİP ---

tlab/indicators/patterns/double_top_bottom.py::DoubleTopBottomParams'a ekle
(varsayılanlar ve kaynakları):

  min_bars_between: int = 22
      ESKİ DEĞER 5'Tİ. Lo-Mamaysky-Wang (Journal of Finance, 2000) DTOP/DBOT
      tanımı: iki uç "en az bir ay, yani 22 işlem günü" arayla olmalı.
      Bu tek değişiklik, kullanıcının gördüğü sahte çift diplerin çoğunu eler.
      DİKKAT: bu bar cinsinden. 4H'te 22 bar ~4 gün demek ki bu ÇOK AZ.
      Zaman dilimine göre ölçekle: parametreyi D1 için 22 kabul et ve
      indikatörün compute()'unda timeframe'e göre çevir (4H'te 1 gün = 6 bar
      -> 132 bar). Bunu bir yardımcı fonksiyonla yap ve gerekçesini yaz.

  eq_tol: float = 0.015
      ESKİ DEĞER 0.02. LMW: iki uç, ORTALAMALARININ %1.5'i içinde olmalı.
      Mevcut kod farkı ortalamaya bölüyor — bu zaten LMW ile aynı ölçüt,
      sadece sayı 0.02'den 0.015'e iniyor.

  max_bars_between: int = 0   # 0 = sınırsız
      Çift tepe/dip birkaç yıl arayla iki tepeyle "oluşmaz". D1 için makul üst
      sınır ~250 bar. Varsayılanı 0 (kapalı) bırak ama parametreyi ekle ve
      config/settings.yaml'da 250 olarak öner.

  min_rise_between_pct: float = 0.10
      YENİ. Bulkowski: iki dip arasında en az %10'luk bir yükseliş olmalı
      (çift tepede: iki tepe arasında en az %10'luk düşüş). Ölçü: boyun pivotu
      ile iki ucun ortalaması arasındaki mesafenin, ucun fiyatına oranı.
      Bu kural, "dümdüz bir taban" tipi sahte formasyonları eler.

  prior_trend_lookback: int = 20
  prior_trend_min_tstat: float = 1.5
      YENİ. Çift dip DÜŞEN bir trendden sonra gelmeli, çift tepe YÜKSELEN.
      broadening.py'de prior_trend_lookback ZATEN var — aynı deseni kullan.

  min_depth_pct: float = 0.03
  min_depth_atr: float = 2.0
      YENİ. pattern_context.pattern_depth_ok ile.

  require_volume_confirm: bool = False
      YENİ. Şu an volume_ok payload'a YAZILIYOR ama HİÇ FİLTRELENMİYOR.
      Parametreyi ekle, varsayılanı False bırak (davranış değişmesin), ama
      config/scans.yaml'a "hacim onaylı" bir preset ekle.

Ayrıca HOLOGRAM'ı düzelt: şu an polygon gerçek kapanış yolunu izliyor
(path_idxs) — bu geometrik olarak doğru ama görsel olarak amorf bir leke
üretiyor (ALTNY ekran görüntüsündeki mavi bulut tam olarak bu).
docs/design/grafik_stil_vitrini.html içindeki sceneDoubleTopBottom() fonksiyonu
doğru şekli gösteriyor: 5 köşeli, boyun seviyesine OTURAN, kendi kendini
kesmeyen bir M/W silueti — [boyun_sol, uc1, boyun, uc2, boyun_sag]. Polygon'u
buna çevir. O dosyadaki holoL/holoR dizilerini birebir örnek al.

--- 1C: OMUZ-BAŞ-OMUZ ---

tlab/features/hs_pattern.py::find_hs:

1. GERÇEK HATA — neck_slope_max yanlış normalize ediliyor.
   Mevcut: abs(neck_slope) / abs(avg_price) > neck_slope_max  (slope BAR BAŞINA)
   Bu, 40 barlık bir formasyonda boyun çizgisinin TOPLAMDA %40 eğilmesine izin
   verir. "Yaklaşık yatay boyun" kuralı fiilen hiçbir şeyi elemiyor.
   DÜZELTME: toplam eğimi formasyon süresine göre değerlendir:
     total_rise = abs(h2.price - h1.price) / avg_price
   ve bunu yeni bir neck_total_slope_max (varsayılan 0.15, yani formasyon
   boyunca boyun en fazla %15 eğilebilir) ile karşılaştır.
   Eski parametreyi SİLME, deprecated olarak bırak ve docstring'e neden
   değiştiğini yaz.

2. YENİ — yukarı eğimli boyun için doğru tetik.
   Bulkowski: boyun çizgisi HER YÖNE eğilebilir; işlem sinyali, boyun aşağı
   ya da yatay eğimliyse boyun çizgisinin kapanışla aşılmasıdır, AMA boyun
   YUKARI eğimliyse sinyal SAĞ KOLTUKALTI TEPESİNİN (h2) kapanışla aşılmasıdır.
   Şu anki kod yukarı eğimli boyunlu formasyonları TAMAMEN ELİYOR — bilgi
   kaybı. head_shoulders.py'deki _break_line fonksiyonunu buna göre değiştir:
   eğim yukarıysa sabit h2.price döndürsün, değilse neckline_value_at.
   Payload'a break_rule: "neckline" | "right_armpit" yaz.

3. YENİ parametreler (HeadShouldersParams):
   prior_trend_lookback: int = 20
   prior_trend_min_tstat: float = 1.5
       TOBO düşüşten, OBO yükselişten sonra gelmeli.
   min_depth_pct: float = 0.04
   min_depth_atr: float = 2.5
       ZOREN 4H örneğinde tespit edilen formasyonun derinliği fiyatın ~%3'ü —
       4H gürültüsünden ayırt edilemez. Eşik OBO/TOBO'da çift dipten yüksek
       tutuluyor çünkü OBO daha büyük bir yapıdır.
   require_volume_profile: bool = False
       volume_profile_ok ZATEN hesaplanıyor ama filtrelenmiyor. Ayrıca hacim
       kuralını TAMAMLA: Bulkowski'ye göre hacim SOL OMUZ ya da BAŞ'ta en
       yüksek, SAĞ OMUZ'da azalmış olmalı — şu an sadece kırılım hacmi
       sağ omuz hacmiyle karşılaştırılıyor. Üç bölgenin hacim ortalamasını
       hesapla ve desen kontrolünü ekle.

--- 1D: DOĞRULAMA (bu fazın en önemli parçası) ---

Kod bitince ÖLÇ ve RAPORLA. scripts/formasyon_denetim.py (YENİ) yaz:

1. BIST evreninden en az 100 sembol, 1D ve 4H, ESKİ parametrelerle tara,
   patterns.* sinyal sayısını kategori kategori (double_top, double_bottom,
   tobo, obo, wedge, ...) say.
2. Aynısını YENİ parametrelerle tekrarla.
3. Bir öncesi/sonrası tablosu üret: her formasyon türü için eski sayı, yeni
   sayı, elenme oranı, ELENME SEBEBİ DAĞILIMI (kaç tanesi min_bars_between'e,
   kaç tanesi ön trende, kaç tanesi derinliğe takıldı). Bunun için indikatörler
   elenen adayları bir sayaçta biriktirsin (sinyal üretmesinler, sadece sayaç).
4. Yeni parametrelerle kalan sinyallerden RASTGELE 10 tanesini seç, her biri
   için tlab plot ile grafik üret, PNG'leri Read ile AÇ ve GÖR, her biri için
   "bu gerçekten bir <formasyon> mu?" sorusuna tek cümlelik yanıt yaz.
   Bu adımı ATLAMA — bu görevin asıl kabul testi bu.
5. Sonucu docs/spec/FORMASYON_DENETIM_v2.md'ye yaz.

BİTTİ KRİTERİ:
- pattern_context.py + 3 fonksiyon + testleri.
- double_top_bottom ve head_shoulders yeni kurallarla, her kural için en az
  1 test (kuralın GERÇEKTEN elediğini gösteren negatif test dahil).
- neck_slope normalizasyon hatası düzeltilmiş + regresyon testi.
- Yukarı eğimli boyun için sağ-koltukaltı tetiği + testi.
- Hologram poligonu M/W silueti + testi.
- docs/spec/FORMASYON_DENETIM_v2.md: önce/sonra tablosu + 10 grafiğin gözle
  incelenmiş yorumu.
- pytest -q -m "not network" yeşil.
```

---

## FAZ 2 — İstatistiksel arbitraj v2

**Amaç:** 606 sahte çifti ~20–40 gerçek çifte indirmek; rotasyon motorunu gerçek bir istatistiksel arbitraj motoruna çevirmek.

**Neden bu sırada:** Faz 1'den bağımsız, paralel yürütülebilir. Kullanıcının en net "burada bir hata var" sezgisi buraya ait ve sezgi **doğru**.

**Bitti kriteri:** `config/pairs.yaml` yeniden üretilmiş ve çift sayısı iki mertebeden bire düşmüş; her çift bir OOS penceresinde yeniden doğrulanmış; pair motorunda çıkış/stop/zaman-stopu var.

```
[ORTAK BAĞLAM bloğunu buraya yapıştır]

GÖREV — FAZ 2: İstatistiksel arbitraj v2

Kullanıcı şikayeti: "arbitraj normalde çok sınırlı sinyal veren bir strateji
fakat benim taramalarımda çok fazla sinyal geliyor". Bu sezgi DOĞRU ve sebebi
ölçüldü. docs/TANI_VE_YOL_HARITASI_v2.md bölüm 1.4'ü ÖNCE OKU — orada
Monte Carlo tablosu ve BH-FDR hesabı var.

Özet bulgular:
- Ham adfuller, TAHMİN EDİLMİŞ bir OLS kalıntısına uygulanıyor. Bu, nominal
  %5 seviyede %14-18 reddetmeye yol açıyor (~3 kat aşırı-reddetme). Doğrusu
  statsmodels.tsa.stattools.coint (Engle-Granger, MacKinnon kritik değerleri).
- 8754 sektör-içi kombinasyon test edilip 606 çift "doğrulanmış" sayılmış (%6.9).
  Saf gürültünün kendi oranı %3.2-4.0. Yani listenin kabaca YARISI beklenen
  gürültü. BH-FDR q=0.05 uygulanınca 606 -> 36 kalıyor.
- İki yön denenip düşük p alınıyor: efektif alfa ~0.0975, düzeltilmemiş.
- Spread'de intercept çıkarılmıyor.
- RelativeMomentumPair'in "nakit" hâli yok; çıkış, zarar-kes, zaman stopu
  ve stop-sonrası kilit YOK.

--- 2A: TESTİ DÜZELT ---

tlab/features/stats.py:
1. YENİ fonksiyon: engle_granger_pvalue(y, x, trend="c") -> float
   statsmodels.tsa.stattools.coint kullanır. Docstring'de NEDEN ham adfuller
   yerine bunun kullanıldığını yaz (OLS kalıntısı kareler toplamını minimize
   edecek şekilde seçildiği için durağan görünmeye eğilimlidir; standart ADF
   kritik değerleri geçersizdir, MacKinnon'ın kointegrasyon kritik değerleri
   gerekir).
2. adf_pvalue'yu SİLME (başka yerlerde kullanılıyor olabilir) ama docstring'ine
   BÜYÜK bir uyarı ekle: "TAHMİN EDİLMİŞ bir regresyon kalıntısına UYGULAMA —
   o durumda engle_granger_pvalue kullan."
3. YENİ: ols_spread(y, x) -> tuple[pd.Series, float, float]
   sabit terimli OLS ile (alpha, beta) döndürüp spread = log(y) - alpha -
   beta*log(x) üretir. log_spread'in intercept'siz hâli geriye dönük uyumluluk
   için kalsın ama discovery artık bunu kullansın.
4. YENİ: benjamini_hochberg(pvalues, q) -> np.ndarray[bool]
   Standart BH-FDR prosedürü. Saf fonksiyon, tlab/features/stats.py'ye.
   Test: bilinen bir p-değeri dizisiyle elle hesaplanmış sonucu doğrula.

--- 2B: DISCOVERY v2 ---

tlab/indicators/pairs/discovery.py::discover_pairs:
1. adf_pvalue yerine engle_granger_pvalue kullan.
2. İki yön denenmesi KALSIN (yön-bağımlılık gerçek) ama artık min(p_yx, p_xy)
   alınırken Šidák düzeltmesi uygula: p_cift = 1 - (1 - min(p1,p2))^2.
   Docstring'de gerekçesini yaz.
3. YENİ parametre: fdr_q: float | None = 0.05
   Verilirse, TÜM aday çiftler tarandıktan SONRA p_cift değerlerine
   benjamini_hochberg uygulanır ve yalnızca hayatta kalanlar döner.
   PairCandidate'e alanlar ekle: p_raw, p_adjusted, n_tests, fdr_passed.
   None verilirse düzeltme yapılmaz (eski davranış, karşılaştırma için).
4. YENİ parametre: oos_split: float | None = 0.5
   Verilirse: örneklem ikiye bölünür, çift SEÇİMİ ilk yarıda yapılır,
   kointegrasyon İKİNCİ yarıda YENİDEN test edilir; ikisinde de geçen çift
   raporlanır. Bu, discovery.py'nin docstring'inde ZATEN uyarı olarak duran
   DISIPLIN-06 seçim-lookahead sorununun fiilen çözümü.
   PairCandidate'e ekle: adf_p_is, adf_p_oos.
5. YENİ parametre: economic_link_map: dict[str, set[str]] | None = None
   Sektör haritasının kaçırdığı bağları (holding-iştirak, aynı emtia, aynı
   endeks) beyaz-listeler. same_sector_only=True olsa bile bu haritada eşleşen
   çiftler taramaya DAHİL edilir. config/economic_links.yaml (YENİ, önce BOŞ
   bir şablon + 5-10 bariz örnek: KCHOL-TUPRS gibi) ile beslenir.

SEKTÖR MU TÜM EVREN Mİ — KARAR VE GEREKÇE (docstring'e yaz):
Sektör-içi kısıt KALIYOR. İki bağımsız gerekçe:
(a) Do & Faff (2010), Gatev-Goetzmann-Rouwenhorst'u 1962-2009'a genişleterek
    getirilerin sektör-içi çiftlerde EN YÜKSEK olduğunu, daha ince sektör
    sınıflandırmasının performansı DAHA DA artırdığını gösteriyor — aynı
    sektördeki iki hisse birbirinin gerçek ikamesi olduğu için yakınsama
    olasılığı yüksek.
(b) İstatistiksel: BİST 648 sembolde tüm evren 209.628 çift, sektör-içi 8.754.
    Çoklu-test yükü 24 kat düşüyor; aynı FDR seviyesinde sektör-içi tarama
    DAHA FAZLA gerçek çift bulur.
Tüm-evren taraması bir SEÇENEK olarak kalsın (same_sector_only=False) ama
o modda fdr_q zorunlu olsun ve n_tests raporlansın.

--- 2C: PAIR MOTORU v2 ---

tlab/indicators/pairs/relative_momentum.py — mevcut ROTASYONEL motoru BOZMA,
yanına gerçek bir istatistiksel arbitraj modu ekle.

RelativeMomentumParams'a ekle:
  mode: Literal["rotational", "mean_reversion"] = "rotational"
  exit_k: float = 0.5        # |z| bunun altına inince pozisyon KAPANIR (nakit)
  stop_k: float = 3.0        # |z| bunu aşarsa zorunlu tasfiye
  max_hold_bars: int = 30    # zaman stopu
  lockout_until_reentry: bool = True  # stop sonrası z bandın içine dönene
                                      # kadar yeni giriş yok

mode="mean_reversion" davranışı (referans: awesome-quant-ai chapter2):
  - z < -k  -> Y AL / X SAT (spread ucuz)
  - z > +k  -> Y SAT / X AL
  - |z| < exit_k -> POZİSYON KAPAT (nakit hâli — mevcut motorda YOK)
  - |z| > stop_k -> zorunlu tasfiye + kilit
  - giriş barından max_hold_bars sonra -> zorunlu kapat
  holding serisi artık üç değer alabilir: +1 (Y long/X short), -1 (ters),
  0 (nakit). Mevcut rotasyonel modda ikili (1.0/0.0) semantik AYNEN kalır —
  geriye dönük uyumluluk için mevcut testler değişmemeli.

tlab/backtest/pairs_engine.py: mean_reversion modu için beta-ölçekli
simultane long/short muhasebesi. CLAUDE.md backlog madde 5 bunu ZATEN
öneriyor — o notu oku ve uygula.

YENİ: tlab/indicators/pairs/coint_monitor.py
CLAUDE.md backlog madde 4: aktif bir çiftin spread'i üzerinde ROLLING
Engle-Granger p-değeri (ör. son 90 bar penceresi) izlensin; p eşiği geri
aşarsa (yapısal kırılma) z henüz dönmemiş olsa bile "cointegration_broken"
durumu üretsin ve pozisyonu düzleştirsin. Bu, aynı istatistiksel makineyi
tekrar kullanır, yeni bir yöntem gerektirmez.

--- 2D: YENİDEN KEŞİF VE RAPOR ---

scripts/pair_denetim.py (YENİ):
1. config/pairs.yaml'daki mevcut 606 çifti OKU. Her biri için engle_granger_pvalue
   ile p'yi YENİDEN hesapla. Kaç tanesi hâlâ p<0.05? Kaç tanesi BH-FDR'den geçiyor?
2. discover_pairs'i yeni ayarlarla (coint + Šidák + fdr_q=0.05 + oos_split=0.5)
   sıfırdan koş, config/pairs.yaml'ı YENİDEN ÜRET. Eski dosyayı
   config/pairs_v1_deprecated.yaml olarak sakla.
3. docs/spec/ARBITRAJ_DENETIM_v2.md yaz:
   - Eski vs yeni çift sayısı
   - Elenme sebebi dağılımı (test değişikliği / FDR / OOS)
   - Hayatta kalan çiftlerin sektör dağılımı
   - Kayıp/kazanç: mean_reversion modunda hayatta kalan çiftlerle backtest
     metrikleri (tlab/backtest/metrics.py'yi kullan) vs eski rotasyonel mod
   - "Arbitraj" vs "istatistiksel arbitraj" ayrımı için arayüz metni önerisi

--- 2E: ARAYÜZ ADLANDIRMASI ---

tlab/viz/labels_tr.py: "pair" kategorisinin Türkçe etiketini "Arbitraj"dan
"İstatistiksel Arbitraj"a çevir. Sidebar'da bu isim görünsün. Gerçek (risksiz)
arbitraj — nakit-vadeli, put-call paritesi, dönüştürülebilir tahvil — tlab'ın
tek-sembol spot veri mimarisiyle uyuşmuyor ve KAPSAM DIŞI; bunu CLAUDE.md'ye
açık bir not olarak yaz ki ileride beklenti karışmasın.

BİTTİ KRİTERİ:
- engle_granger_pvalue + ols_spread + benjamini_hochberg + testleri.
- discover_pairs: coint + Šidák + FDR + OOS + ekonomik bağ; her biri test edilmiş.
- mean_reversion modu + çıkış/stop/zaman-stopu/kilit + testleri.
- coint_monitor.py + testi.
- config/pairs.yaml yeniden üretilmiş; docs/spec/ARBITRAJ_DENETIM_v2.md yazılmış.
- pytest -q -m "not network" yeşil.
```

---

## FAZ 3 — SVG çizim motoru (çekirdek)

**Amaç:** Grafiklerin artifact'e benzememesinin **kök nedenini** ortadan kaldırmak: Plotly'yi bırakıp, artifact'in kendi tekniğiyle (saf SVG) çizen bir motor yazmak.

**Neden bu sırada:** Faz 4'ün (19 sahnenin portu) ön koşulu. Bu faz **tek bir sahne bile çizmez** — sadece motoru ve yerleşim/çakışma altyapısını kurar. Bu ayrım kritik: motor sağlam olmazsa 19 sahne 19 ayrı hack olur.

**Bitti kriteri:** Motor tek bir gösterge için (`patterns.double_top_bottom`) artifact'teki `sceneDoubleTopBottom` ile **yan yana konulduğunda ayırt edilemeyecek** bir SVG üretiyor; hiçbir etiket çakışmıyor; 3 temada da doğru; golden testi var.

```
[ORTAK BAĞLAM bloğunu buraya yapıştır]

GÖREV — FAZ 3: tlab/viz/svg/ — saf SVG çizim motoru (ÇEKİRDEK)

ÖNCE OKU: docs/design/grafik_stil_vitrini.html. Bu dosya, hedeflenen görselin
ÇALIŞAN kaynağıdır — 19 grafik türünün her biri saf SVG üreten bir JS
fonksiyonudur. Bu görevde o dosyanın ALTYAPI katmanını (satır ~176-420:
seeded, attrs, fnum, svgLine, svgRect, svgPoly, svgText, svgCircle, pill,
makeChart, drawCandles, niceTicks, priceLabels, xLabels, rightLabel,
panelLabel, outlinePill, glowFilterDefs, THEMES) Python'a çeviriyoruz.
SAHNELER (sceneXxx) BU FAZDA PORTLANMAYACAK — o Faz 4.

NEDEN PLOTLY BIRAKILIYOR (docs/TANI_VE_YOL_HARITASI_v2.md 1.1'i oku):
Plotly'de etiket çakışma çözücü, önder çizgili etiket kutusu, hap rozet ve
sahneye özel yerleşim YOK. renderer.py'nin 2884 satırının büyük kısmı bu
eksikleri elle taklit etmeye çalışıyor ve bilgi SİLEREK (declutter) çözüyor.
Ayrıca fig.to_image() her çağrıda kaleido üzerinden headless Chromium turu
demek; saf SVG üretimi ölçüldü, 300 mumluk bir grafiğin mum gövdeleri 0.46 ms.

MİMARİ KURALI DEĞİŞMİYOR: viz katmanı HESAP YAPMAZ. Girdi yine
IndicatorResult primitifleri (Level/Line/Box/Polygon/Marker/Signal/series).
Sadece çizim arka ucu değişiyor.

--- 3A: MODÜL YAPISI ---

tlab/viz/svg/
  __init__.py       -> render_svg(result, df, theme, last_n, ...) -> str
  prim.py           -> svg_line/svg_rect/svg_poly/svg_text/svg_circle/pill/
                       group/defs. Saf string üreteçleri, hiç durum tutmaz.
                       XML kaçışı (& < > " ') ZORUNLU.
  scale.py          -> Chart dataclass: makeChart karşılığı.
                       w,h,margin_l/r/t/b, i_domain, p_domain, X(i), Y(p),
                       inner_x0/x1/y0/y1. nice_ticks(lo,hi,n).
  candles.py        -> draw_candles(bars, chart, theme, width_frac).
                       Artifact'teki drawCandles ile AYNI: gövde min 0.6px,
                       fitil ayrı line, yukarı/aşağı renkleri temadan.
  axes.py           -> price_labels (yatay grid + sağ/sol fiyat etiketleri),
                       x_labels (tarih etiketleri). Tarih etiketleri hafta
                       sonu/seans dışı boşlukları GÖSTERMEZ — mevcut
                       renderer.py'de bu ZATEN çözülmüş (rangebreaks), aynı
                       mantığı bar-indeksli eksene taşı.
  layout.py         -> BU FAZIN EN ÖNEMLİ DOSYASI. Aşağıda ayrı anlatıldı.
  theme.py          -> tlab/viz/themes.py::Theme'i SVG'nin ihtiyaç duyduğu
                       ek alanlarla (candle_w, radius, glow, font_display,
                       card_bg, card_border, card_shadow) genişletir.
                       Artifact'in THEMES sabitindeki classic/dark/editorial
                       değerleriyle BİREBİR eşleşmeli — themes.py'deki mevcut
                       LIGHT_ANALYSIS/DARK_TERMINAL/KAGIT_RAPORU zaten büyük
                       ölçüde eşleşiyor, farkları TESPİT ET ve artifact'i
                       doğru kabul et.
  scenes/           -> BOŞ (Faz 4 dolduracak). Sadece __init__.py + base.py
                       (Scene protokolü: build(result, df, theme) -> SceneOut,
                       SceneOut = {title, subtitle, badge, panels|two_up}).

--- 3B: layout.py — ETİKET YERLEŞİM MOTORU ---

Bu, Plotly'de olmayan ve tüm farkı yaratan parçadır. Üç yetenek:

1. LabelBox dataclass: x, y, w, h, text, anchor_x, anchor_y (bağlanacağı
   veri noktası), priority (int, büyük = daha önemli), placement_hints
   (tercih sırası: above / below / right / left).

2. resolve_collisions(boxes, bounds) -> list[PlacedLabel]
   Açgözlü + itme (greedy + push) algoritması:
   - Kutuları priority'ye göre sırala (yüksek önce).
   - Her kutuyu tercih ettiği yere koy. Zaten yerleştirilmiş bir kutuyla
     ya da çizim sınırıyla ÇAKIŞIYORSA, sırasıyla diğer hint'leri dene,
     sonra dikey eksende adım adım (step=labelHeight+2) it.
   - Kutu, ORİJİNAL çapa noktasından belirli bir eşikten (ör. 24px) fazla
     uzaklaştıysa PlacedLabel.needs_leader = True işaretle.
   - Hiçbir yere sığmayan en düşük öncelikli kutular DROP edilir ve
     dropped listesinde raporlanır (sessizce kaybolmaz — çağıran log'lar).
   NOT: mevcut renderer.py'deki _stagger_yshifts ve _declutter_levels bu
   fonksiyonun ilkel hâlleridir. Onları BU motora göç ettir; declutter artık
   "bilgi sil" değil "yerini bul, sığmıyorsa öncelikle ele" olmalı.

3. leader_line(placed) -> str
   Çapa noktasından kutunun kenarına ince (1px, %70 opaklık) bir çizgi.
   Artifact'teki sceneClassicPatterns'ın KIRILIM/RETEST kutuları bunun
   referansı — o kodu oku.

TEST EDİLEBİLİRLİK: resolve_collisions SAF bir fonksiyondur (girdi kutu
listesi, çıktı yerleşim listesi). Onu SVG'den bağımsız test et:
- iki üst üste kutu -> ayrışıyor mu
- sınıra taşan kutu -> içeri çekiliyor mu
- 50 kutu tek noktada -> düşük öncelikliler drop ediliyor mu
- deterministik mi (aynı girdi -> aynı çıktı)

--- 3C: TEK SAHNELİK KANIT ---

Motoru tamamladıktan sonra SADECE BİR sahne yaz:
tlab/viz/svg/scenes/double_top_bottom.py

Referans: docs/design/grafik_stil_vitrini.html::sceneDoubleTopBottom (satır
~764-852). O fonksiyonu satır satır oku ve Python'a çevir. Fark: veri artık
uydurma değil, gerçek IndicatorResult'tan geliyor — pivotlar, boyun seviyesi,
hedef, kırılım/onay noktaları, "1"/"2" rozetleri hepsi primitiflerden okunacak.

Sonra ZORUNLU DOĞRULAMA DÖNGÜSÜ (grafik-tasarim-sistemi skill'i, Faz 0):
1. Gerçek BIST verisiyle, patterns.double_top_bottom sinyali OLAN bir sembolde
   SVG üret. PNG'ye çevir (cairosvg veya resvg — pyproject.toml'a ekle) ve
   PNG'yi Read ile AÇ VE GÖR.
2. docs/design/grafik_stil_vitrini.html'i de tarayıcıda/ekran görüntüsüyle
   karşılaştır (aynı sahne, aynı tema).
3. Gördüğün FARKLARI madde madde yaz. Düzelt. Tekrarla. EN AZ 3 İTERASYON.
4. Üç temada da (classic/dark/editorial) üret ve üçünü de GÖR.
5. En az 3 veri durumu: bol sinyalli sembol, tek sinyalli sembol, çok uzun
   geçmişli sembol (çakışma stresi).

--- 3D: ENTEGRASYON ---

- tlab/viz/live.py::render_live'a engine: Literal["svg","plotly"] = "svg"
  parametresi. Varsayılan svg; bir sahne henüz portlanmadıysa plotly'ye DÜŞ
  (Faz 4 boyunca ikisi yan yana yaşayacak).
- web/backend/routes/ altına chart_svg.py: GET /api/chart.svg -> image/svg+xml.
  chart_png.py KALSIN ama artık SVG'yi rasterleştirsin (kaleido devre dışı).
- tests/test_viz/golden/: SVG metinleri üzerinden karşılaştırma (Faz 0'da
  hazırlanan altyapı).

BİTTİ KRİTERİ:
- tlab/viz/svg/ modülü + layout motoru + en az 12 yeni test.
- resolve_collisions saf-fonksiyon testleri (yukarıdaki 4 senaryo).
- patterns.double_top_bottom sahnesi 3 temada üretiliyor, PNG'leri GÖRÜLMÜŞ,
  en az 3 iterasyon yapılmış, önce/sonra görüntüleri docs/design/iterasyon/
  altında.
- GET /api/chart.svg çalışıyor.
- Grafik üretim süresi ölçülmüş ve raporlanmış (eski Plotly yolu vs yeni SVG).
- pytest -q -m "not network" yeşil.
```

---

## FAZ 3.5 — Renderer kritik hataları (2026-09-05 EKLENDİ, Faz 4'ten ÖNCE)

> **Neden eklendi:** `error/` klasöründeki 10 çıktının tamamı görüntü olarak incelendi (bkz. **`docs/GORSEL_HATA_TESHISI.md`**). Üç kod hatası dosya:satır düzeyinde doğrulandı; üçü de birden fazla göstergeyi bozuyor ve Faz 4'te SVG'ye portlanan her sahne bunları miras alacak. Önce kapatılmalı.

**Bitti kriteri:** `ma_systems`'ın MA çizgileri fiyatı takip ediyor; hacim/MACD panelleri görünür pencereye göre ölçekleniyor; AL/SAT işareti onay barında, hedefte değil. Üçü de önce/sonra görüntüsüyle kanıtlanmış.

```
[ORTAK BAĞLAM bloğunu buraya yapıştır]

GÖREV — FAZ 3.5: Renderer kritik hataları

ÖNCE OKU: docs/GORSEL_HATA_TESHISI.md bölüm 1 (K1/K2/K3). Üç hata da orada
kanıtıyla ve hangi görselde nasıl göründüğüyle yazılı.

--- K1: HER Line IKI NOKTAYA INDIRGENIYOR ---

tlab/viz/renderer.py:1488 civarı:
    (t0, p0), (t1, p1) = ln.points[0], ln.points[-1]
    ...
    go.Scatter(x=[_x(t0), _x(t1)], y=[p0, p1], mode="lines", ...)

Renderer HER Line'in yalnizca ILK ve SON noktasini alip aralarina duz bir
dogru ciziyor. Trendline (2 nokta) icin dogru; ama trend.ma_systems her
hareketli ortalamanin TUM serisini tek bir Line icinde tasiyor -> EMA
8/21/55/200 birer DUZ YATAY CIZGIYE cokuyor. trend.weekly_channel'in
channel_current'i da ayni desende.

KANIT: error/INTEM_trend.ma_systems_1d.png -- turuncu/mor/mavi cizgiler
235-325 arasinda dalgalanan fiyatin ustunde kusursuz duz. Gercek bir EMA
seridi asla boyle gorunmez.

Yapilacak:
1. Cok noktali Line'lari tam polyline olarak ciz:
     xs = [_x(t) for t, _ in ln.points]; ys = [p for _, p in ln.points]
   2 noktali Line'larin davranisi DEGISMEMELI (trendline uzatma mantigi,
   _line_extensions, etiket yerlesimi hepsi ayni kalsin).
2. tlab/viz/svg/ motorunda AYNI kontrolu yap -- port sirasinda bu hata
   tasinmis olabilir. svg/scenes/weekly_channel.py'yi ozellikle kontrol et.
3. REGRESYON TESTI: 50 noktali sentetik bir sinus serisi tasiyan bir Line
   ver, cizilen trace'in 50 noktasinin da bulundugunu dogrula (fig.data
   uzerinden x/y uzunlugu). Bu test olmasaydi hata hic yakalanmazdi.

--- K2: ALT PANEL EKSENI TUM GECMISTEN OLCEKLENIYOR ---

render() son_n uygulandiginda yalnizca x-eksenini kisitliyor (docstring bunu
acikca soyluyor: "hicbir seri/primitif budanmaz"). Plotly'nin y-ekseni
otomatik olceklemesi ise trace'in TAMAMINA bakiyor. Sonuc: gecmiste 600-700k'lik
bir hacim citasi varsa, gorunur 250 barlik pencerede hacim 0-50k olsa bile
eksen 0-700k'ya aciliyor ve barlar panelin %7'sine sikisiyor.

KANIT: breakouts (hacim ekseni 0-700k, barlar tabanda duz), report ve
price_structure (hacim 0-600k, MACD -40..+20 iken veri -5..+5).
RSI PANELLERI SORUNSUZ -- cunku RSI dogasi geregi 0-100 sinirli. Teshisi
kesinlestiren gozlem bu.

Yapilacak:
1. render() son_n ile bir x-penceresi belirlediginde, HER alt panelin
   y-eksenini O PENCEREDEKI dilimden hesapla ve sabitle:
     visible = seri.loc[pencere_baslangic:pencere_sonu]
     fig.update_yaxes(range=[lo, hi], row=i, col=1)
   Ust/alt %5 pay birak. Hacim gibi tabani sifir olan panellerde alt sinir 0.
2. Ayni kurali ANA panele de uygula (su an calisiyor gorunuyor ama
   dogrula) ve SVG motoruna da tasi.
3. AYRICA -- bu hatanin ikinci yuzu: alt paneller figur yuksekliginin
   yarisini kaplayip hicbir bilgi tasimiyor. Panel yukseklik oranlarini
   gozden gecir: ana panel >= %55, her alt panel <= %15.
4. REGRESYON TESTI: seriye gorunur pencerenin 10 KATI buyuklukte bir
   aykiri deger koy, eksen araliginin ondan ETKILENMEDIGINI dogrula.

--- K3: AL ISARETI HEDEFE KONUYOR ---

tlab/indicators/patterns/*.py icindeki ortak desen:
    last_sig = pattern_signals[-1]
    if last_sig.state in ("confirmed", "completed"):
        markers.append(Marker(t=last_sig.bar_time, ..., text="AL"))

pattern_signals[-1] zincirin EN SON olayi. Tamamlanmis bir formasyonda bu
"hedefe ulasildi" olayidir -> AL isareti GIRISE degil CIKISA konuyor.

KANIT: error/INTEM_patterns.flag_pennant_1d.png -- kirilim 4 Agustos'ta
(buyuk yesil mum 202->207), ama AL etiketi 18 Agustos'ta 218'de, "BAYRAK
[HEDEFE ULASTI]" rozetinin altinda. Kullanicinin birebir sikayeti bu.

Yapilacak -- bes formasyon modulunun HEPSINDE (double_top_bottom,
head_shoulders, wedge, broadening, flag_pennant):
1. AL/SAT isareti, payload["event"] alani "_confirmed" ile BITEN sinyalin
   barina konsun (last_sig'e DEGIL).
2. Kullanicinin istedigi DORT AYRI isareti uret:
     KIRILIM  -> kirilim bari, ici bos daire + onder cizgi + "KIRILIM"
     ONAY     -> onay bari (retest tuttu), ici dolu daire + "ONAY"
     AL/SAT   -> ONAY bari, dolgulu ucgen + kalin metin
     HEDEF    -> hedefe ulasma bari, rozet "HEDEF ✓"
   Bu dort ayrim docs/design/grafik_stil_vitrini.html'in
   sceneClassicPatterns ve sceneBreakoutFvg sahnelerinde ZATEN var --
   o kodu oku, isaret dilini oradan al.
3. Formasyon SURESI DOLMUS (expired) ya da HENUZ ONAYLANMAMIS (pending)
   ise AL/SAT isareti HIC uretilmesin.
4. HEDEF Level'i de yalnizca formasyon ONAYLANDIKTAN sonra uretilsin --
   su an onaylanmamis bir formasyonun hedefi cizildigi icin eksen
   patliyor (bkz. error/AKBNK_patterns.double_top_bottom_1d.png: hedef
   37.9, mumlar 60-85, eksen 40-85'e acilip mumlari panelin ust %40'ina
   sikistiriyor).
5. Her madde icin test.

--- DOGRULAMA (ZORUNLU) ---

Her uc hata icin ONCE/SONRA gorseli uret ve Read ile AC VE GOR:
  K1 -> INTEM trend.ma_systems 1D
  K2 -> INTEM structure.price_structure 4H (hacim + MACD panelleri)
  K3 -> INTEM patterns.flag_pennant 1D
docs/design/iterasyon/faz35_<hata>_<once|sonra>.png olarak kaydet.
"Duzelttim" demeden ONCE gorseli ac ve gercekten duzeldigini GOR.

BITTI KRITERI:
- Uc hata da duzeltilmis, ucu icin de regresyon testi yazilmis.
- Once/sonra gorselleri uretilmis ve GORULMUS.
- pytest -q -m "not network" yesil.
```

---

## FAZ 4 — 19 sahnenin portu

**Amaç:** Artifact'teki 19 grafik türünün tamamını, Faz 3'ün motoruyla, gerçek veriyle üretmek.

**Neden bu sırada:** Motor (3) ve doğru formasyonlar (1) hazır olmadan buraya girmek, aylardır yaşanan döngüyü tekrar etmek olur.

**Bitti kriteri:** 19 sahnenin tamamı gerçek veriyle üretiliyor, her biri 3 temada görülmüş, hiçbirinde çakışan etiket yok, `plotly` yolu artık hiçbir sahne için kullanılmıyor.

**Bu fazı 3 oturuma böl** — her oturum bir grup, çünkü tek oturumda bağlam şişer:

| Oturum | Sahneler |
|---|---|
| 4a | `harmonic`, `report`, `swingfib`, `goldensupply`, `weekly`, `reversal_map` |
| 4b | `classic`, `double_top_bottom`(Faz 3'te bitti — gözden geçir), `wedge_triangle`, `broadening`, `flag_pennant`, `breakout_fvg`(YENİ strateji) |
| 4c | `pair`, `vol_harvest`, `alpha_rank`, `alpha_scatter`, `momentum_rank`, `momentum_heatmap`, `ewmac`, `ma_systems` |

```
[ORTAK BAĞLAM bloğunu buraya yapıştır]

GÖREV — FAZ 4<X>: Sahne portu — <grup adı>

ÖNCE OKU:
- docs/design/grafik_stil_vitrini.html — bu oturumda portlanacak sahnelerin
  sceneXxx() fonksiyonlarını SATIR SATIR oku.
- tlab/viz/svg/ (Faz 3'te yazılan motor) + scenes/double_top_bottom.py
  (referans uygulama — yeni sahneler ONUN desenini izleyecek).
- teknik-analiz/.claude/skills/grafik-tasarim-sistemi/SKILL.md

Bu oturumda portlanacak sahneler:
  <liste>

HER SAHNE İÇİN AYNI 6 ADIM:

1. Artifact'teki sceneXxx() fonksiyonunu oku. Şunları çıkar ve bir yorum
   bloğuna yaz: hangi primitifler çiziliyor (mum/çokgen/çizgi/seviye/rozet/
   etiket), hangi sırada (z-order), hangi tema alanları kullanılıyor,
   yerleşim nasıl (tek panel / twoUp / alt panel / sağ dikey panel),
   marjlar ne.
2. tlab/viz/svg/scenes/<ad>.py yaz. Uydurma veri YOK — her değer
   IndicatorResult'tan gelecek. Artifact'te uydurma olan bir şey (ör. sabit
   bir "Hedef: 20.4" metni) gerçek karşılığından okunacak; karşılığı YOKSA
   o öğe ÇİZİLMEZ ve eksik olduğu docstring'e yazılır (uydurma değer ASLA).
3. Gerçek veriyle üret. O göstergenin GERÇEKTEN sinyal ürettiği bir sembol
   seç (tlab scan ile bul, rastgele sembol deneme).
4. Çıktıyı Read ile AÇ VE GÖR. Artifact'in aynı sahnesiyle karşılaştır.
   FARKLARI MADDE MADDE YAZ.
5. Düzelt, 3. adıma dön. EN AZ 3 İTERASYON. Sonuncusunu docs/design/iterasyon/
   <sahne>_<tema>.png olarak kaydet.
6. 3 temada da (classic/dark/editorial) üret ve üçünü de GÖR.

SAHNEYE ÖZEL NOTLAR:

[4a için]
- report (Yapı Raporu): sağda DİKEY hacim profili paneli var (vp_bins/
  vp_volumes fiyat-indeksli seriler). Artifact satır ~522-551 bunu gösteriyor.
  Ayrıca alt panelde RSI. HVN (yüksek hacimli düğüm) barları farklı renkte.
- harmonic: twoUp — solda TAMAMLANMIŞ, sağda hâlâ oluşan aday. PRZ bandı
  sağa uzanan yarı-saydam kutu + kesikli sınır çizgileri + sol üstte
  "Hedef Bölge (PRZ): a-b" etiketi. Aktif adayda "AKTİF" outline pill.
  DİKKAT: mevcut renderer.py'de harmonik marker'lar en fazla 1 aday ile
  sınırlı (_MAX_HARMONIC_MARKERS=1). Yeni motorda bu sınır YERİNE layout
  motorunun öncelik sistemini kullan — daha güncel aday daha yüksek öncelik.
- reversal_map: confluence (golden zone + arz/talep + PRZ + kanal dibi
  çakışması). scanner/confluence.py::build_reversal_map ZATEN var.

[4b için]
- breakout_fvg YENİ BİR STRATEJİ — henüz kodlanmadı. Bu oturumda ÖNCE
  indikatörü yaz (tlab/indicators/patterns/breakout_fvg.py), sonra sahnesini.
  Tanım (kullanıcının paylaştığı referans görselden + literatürden):
    * KONSOLIDASYON: N bar boyunca fiyatın dar bir kutuda kalması
      (kutu yüksekliği / ATR < eşik, min_bars).
    * BREAKOUT: kapanışın kutu üst sınırını aşması.
    * BULLISH FVG (fair value gap, 3 mumlu dengesizlik): kırılım hareketi
      içinde, mum[i-1].high < mum[i+1].low olan bir üçlü. Boşluk =
      [mum[i-1].high, mum[i+1].low]. Bearish için ayna.
    * RETEST: fiyatın FVG bölgesine geri gelmesi.
    * CONFIRMATION: FVG içinde/üstünde kapanış ile dönüş -> AL.
    Parametreler: consolidation_bars, box_atr_max, min_fvg_atr,
    max_bars_to_retest, confirm_bars. Hepsi non-repaint (3 mumlu FVG
    ancak 3. mum KAPANDIĞINDA bilinir — bunu testle doğrula).
    Bulkowski/ICT karışımı olduğu için docstring'de kaynak ayrımı yap.
- classic (TOBO): hologram artifact'te ÜÇ AYRI ters üçgen (sol omuz/baş/sağ
  omuz), komşu üçgenler boyun pivotlarını paylaşır. head_shoulders.py bunu
  ZATEN böyle üretiyor — sahne sadece çizecek.
- Tüm klasik formasyonlarda AL/SAT giriş işareti: dolgulu üçgen + kalın metin,
  artifact'teki sceneClassicPatterns satır ~712-714 referans.

[4c için]
- alpha_scatter ve momentum_heatmap: tlab/viz/universe_charts.py'de Plotly
  ile ZATEN var — SVG'ye taşı. Bunlar Faz 6'nın (Evren Taraması sayfası)
  ana görselleri.
- pair: 3 satırlı düzen (normalize fiyat + tutulan dönem gölgeleri, portföy
  vs buy&hold, Z-skor + eşik çizgileri + geçiş etiketleri). Faz 2'de
  mean_reversion modu eklendiyse NAKİT dönemleri de gösterilmeli (üçüncü
  bir gölge rengi).
- ewmac / ma_systems: çok seri overlay — layout motorunun etiket önceliği
  burada kritik (her MA'nın sağ kenarda kendi etiketi olacak, üst üste
  binmeyecek).

FAZ SONU:
- tlab/viz/renderer.py (Plotly) artık hiçbir sahne için ÇAĞRILMIYOR.
  Dosyayı SİLME — tlab/viz/_legacy_plotly.py'ye taşı, live.py'deki
  engine="plotly" yolunu bırak, CLAUDE.md'ye "kaldırma adayı" notu yaz.
- Her sahne için golden testi.
- docs/design/iterasyon/ altında 19 sahne × 3 tema görüntü.

BİTTİ KRİTERİ (her oturum için):
- O gruptaki her sahne gerçek veriyle üretiliyor, 3 temada görülmüş,
  en az 3 iterasyon geçmiş.
- Hiçbir çıktıda çakışan etiket YOK (layout motorunun dropped listesi
  loglanıyor ve boş ya da gerekçeli).
- Golden testleri yeşil, pytest -q -m "not network" yeşil.
```

---

## FAZ 4d — SMC yapı katmanı (`ornek1.png` standardı, 2026-09-05 EKLENDİ)

> **Neden eklendi:** Kullanıcı `ornek1.png`/`ornek2.png`'yi birebir hedef olarak gösterdi. Oradaki öğelerin çoğu — BOS/CHoCH, temas-sayılı trend çizgisi, pivot üçgenleri, pivot-çıpalı arz/talep — **tlab'da hiç yok**. Bu bir sahne portu değil, **indikatör katmanına yeni üretim** eklemek.

**Bitti kriteri:** `ornek1.png` ile bizim çıktımız yan yana konduğunda öğe öğe eşleşiyor: pivot üçgenleri, temas-sayılı trend çizgisi, kırmızı/yeşil arz-talep bölgeleri sağ kenarda fiyat etiketli, BOS/CHoCH kesikli çizgileri.

```
[ORTAK BAĞLAM bloğunu buraya yapıştır]

GÖREV — FAZ 4d: SMC yapı katmanı

ONCE OKU:
- docs/GORSEL_HATA_TESHISI.md bolum 4 ("ornek1.png standardi") -- gorsel
  sozlesme madde madde orada.
- ornek1.png ve ornek2.png (repo kokunde) -- Read ile AC VE GOR. Bu iki
  gorsel hedefin kendisi.
- error/INTEM_structure.supply_demand_4h.png -- su anki halimiz. Farki
  kendi gozunle gor.

--- 4d-1: YAPI ISARETLERI (pivot ucgenleri + BOS/CHoCH) ---

tlab/features/swings.py::label_structure HH/HL/LH/LL'i ZATEN uretiyor.
Eksik olan iki sey:

1. GORSEL DIL: su an bu etiketler ince gri bir zigzag cizgisiyle birlestirilip
   kucuk metinlerle gosteriliyor. Kullanici bunu ACIKCA reddetti: "bizim gibi
   oradan oraya cizgi goturmuyor, tepelerine ve diplerine kucuk ucgenle ve
   yaziyla resmetmis." Yapilacak:
     - Birlestirici zigzag cizgisi KALDIRILSIN (ya da opsiyonel/varsayilan
       kapali olsun).
     - Her pivota kucuk bir UCGEN + metin: HH/LH icin altin, asagi bakan,
       pivotun USTUNDE; HL/LL icin camgobegi, yukari bakan, pivotun ALTINDA.
     - Marker.kind = "structure_label" ZATEN var; renderer/SVG sahnesi bunu
       ucgen olarak cizsin (su an duz metin).

2. BOS / CHoCH tespiti -- YENI, tlab'da hic yok.
   tlab/features/market_structure.py (YENI dosya) yaz:
     - BOS (Break of Structure): mevcut trend yonunde bir onceki yapisal
       zirvenin/dibin KAPANISLA asilmasi. Yukselen trendde son HH asilirsa
       BOS-yukari; dusen trendde son LL asilirsa BOS-asagi.
     - CHoCH (Change of Character): trend yonunun TERSINE ilk yapisal
       kirilim. Yukselen trendde (HH/HL dizisi) son HL'nin kapanisla
       asagi kirilmasi -> CHoCH-asagi.
     - Ikisi de SAF FONKSIYON, yalnizca [0, t] araligina bakar, kirilim
       bari kapandiginda uretilir (NON-REPAINT -- kirilim bari sonradan
       degismez, ama hangi pivotun "son yapisal zirve" oldugu yeni bir
       pivot dogunca degisir; bu yuzden BOS/CHoCH kaydi DOGDUGU barda
       dondurulmali, sonradan yeniden degerlendirilmemeli).
   Cikti: Level (kirilan seviyeden kesikli yatay cizgi, kirilim barinda
   biten) + Marker ("BOS↑" yesil / "CHoCH↓" kirmizi, aktif olan "/ AKTIF"
   eki alir).
   TESTLER: sentetik bir HH/HL dizisi kurup BOS'un dogru barda dogdugunu,
   CHoCH'un yon degisiminde uretildigini, ve repaint_test'ten gectigini
   dogrula.

--- 4d-2: TEMAS SAYILI TREND CIZGISI ---

tlab/features/trendlines.py::build_trendlines temas sayisini ZATEN
hesapliyor ama Line.label icine gomuyor ("(Temas:N)"). ornek1'de etiket
UC bilgi tasiyor: yon + durum + temas sayisi.

Yapilacak:
1. Trendline ciktisinda temas sayisi, kirik mi, ve yon AYRI alanlar olarak
   tasinsin (Line.label string'ine gomulmesin -- sahne bunlari kendi
   bicimlendirsin).
2. Sahne etiketi: "DUSEN TREND | TARIHSEL/KIRILMIS | TEMAS: 5" formatinda,
   cizginin ustunde, cizgiyle AYNI renkte, okunur boyutta (11-12px).
3. Cizgi stili: NOKTALI (dotted), 2px, DOYGUN renk -- dusen icin mor/magenta,
   yukselen icin yesil. Su anki ince gri kesikli cizgi ornek1'in yaninda
   gorunmuyor bile (bkz. error/INTEM_trend.breakouts_4h.png).
4. AYNI ANDA cizilecek trend cizgisi sayisini SINIRLA (en fazla 2 dusen +
   2 yukselen, temas sayisina gore secilir). Su an trendline_max_lines=4
   ama hepsi ust uste biniyor.

--- 4d-3: PIVOT-CIPALI ARZ/TALEP (algoritma degisikligi) ---

Su anki yontem (features/zones_sd.py) rally-base-drop: dar konsolidasyon +
patlama. GECERLI bir yontem ama INTEM'de TEK arz bolgesi, SIFIR talep
bolgesi uretti. Kullanicinin tarif ettigi ve ornek1/2'nin kullandigi yontem
PIVOT-CIPALI:

  1. Cipa: swing yuksek -> arz bolgesi; swing dusuk -> talep bolgesi.
  2. Sinirlar: dis kenar swing'in ekstremi; ic kenar cevredeki mumlarin
     ortalama fitil/govde boyundan turetilir (bolge gercek tepki alanini
     kapsasin, ince bir cizgi degil).
  3. Kumeleme: birbirine yakin (< 0.5 ATR) pivotlar tek bolgede birlesir.
  4. Guc = TEMAS SAYISI. Fiyatin tekrar ziyaret ettigi bolge guclenir.
  5. ATR dogrulamasi: pivottan uzaklasan hareket ATR katini asmali.
  6. Yukseklik tavani ~2.5-3.0 ATR.
  7. Tazelik: TAZE (hic test edilmemis) / TEST EDILDI / KIRILDI.

Yapilacak:
1. tlab/features/zones_sd.py'ye pivot-cipali ureteci EKLE (mevcut
   rally-base-drop'u SILME). SupplyDemandParams'a method: Literal
   ["pivot","rbd","both"] = "pivot" ekle.
2. method="both" iken iki yontem de calissin ve AYNI bolgeyi isaret
   ediyorlarsa guc skoru artsin.
3. GORSEL (kullanici bunu acikca istedi):
   - Arz KIRMIZI dolgu (opaklik ~0.12) + kirmizi kenarlik + ic kesikli
     orta cizgi. Talep YESIL, aynisi.
   - DIKKAT: tlab/viz/themes.py::_FILL_STYLE_COLOR sozlugunde "demand",
     "supply", "demand_broken", "supply_broken" ANAHTARLARI YOK -- gri
     varsayilana dusuyor. Bu, error/INTEM_structure.supply_demand_4h.png'de
     bolgelerin gri gorunmesinin sebebi. Ekle.
   - Etiket cizim alaninin DISINDA, sag kenar bosluğunda: ust satir
     "SUPPLY / ARZ" ya da "DEMAND / TEST EDILDI", alt satir fiyat araligi
     "41.80 - 42.70". ornek1'deki yerlesim birebir bu.
4. Kabul testi: INTEM 4H'te en az 2 arz + 2 talep bolgesi uretilsin ve
   uretilenler ornek1'deki gibi FIYATIN GERCEK donus yaptigi seviyelerde
   olsun. Grafigi uret, Read ile AC, ornek1 ile yan yana koy, farklari
   madde madde yaz, duzelt. EN AZ 3 ITERASYON.

--- 4d-4: TEK HAREKETLI ORTALAMA ---

ornek1/2'de TEK bir mor/lavanta MA var, fiyati takip eden, 2px. Bizim
ma_systems dort MA'lik bir serit ciziyor ve (K1 duzeltilene kadar) hepsi
duz. Faz 3.5'ten sonra serit dogru cizilecek, ama YAPI sahnesinde
(supply_demand / breakouts / report) tek bir MA yeterli -- serit ayri bir
gostergenin isi. Yapi sahnelerine tek MA (EMA-50 varsayilan) ekle.

BITTI KRITERI:
- market_structure.py + BOS/CHoCH + testleri + repaint dogrulamasi.
- Pivot ucgenleri (zigzag cizgisi olmadan) uc sahnede de calisiyor.
- Temas sayili trend cizgisi, uc bilgili etiketle.
- Pivot-cipali arz/talep, kirmizi/yesil, sag kenarda fiyat etiketli.
- ornek1.png ile kendi ciktimiz yan yana konmus, farklar yazilmis,
  en az 3 iterasyon yapilmis, son hali docs/design/iterasyon/ altinda.
- pytest -q -m "not network" yesil.
```

---

## FAZ 5 — Kalan stratejilerin denetimi

**Amaç:** Denetimde bulunan gösterge-özel hataları **düzeltmek**.

> **2026-09-05 eki.** `docs/GORSEL_HATA_TESHISI.md` bölüm 3'teki **A2** (golden zone yanlış swing'i seçiyor + Fibonacci merdiveni çizilmiyor) bu faza dahildir. **A1** (arz/talep yöntemi) Faz 4d'ye taşındı.

> **2026-09-03 güncellemesi.** Denetimin kendisi yapıldı — `docs/STRATEJI_DENETIM_TAM.md` bölüm B. Bu faz artık "denetle" değil "denetimde bulunanları düzelt": `five_zero` kök nedeni, `ewmac` sabit forecast tablosu, `momentum_rank` skor normalizasyonu (üç bileşen farklı ölçekte ham toplanıyor), `alpha_rank` likidite eşiği ölçümü, `breakouts` skor dağılımı + tür gruplama, `price_structure` optimizasyonu, evren göstergelerinin `/chart` yolunda tüm evreni hesaplamaması.

**Bitti kriteri:** Her gösterge için "kural kaynağı → kod → test" zinciri belgelenmiş; bulunan gerçek hatalar düzeltilmiş; hiçbir eşik gerekçesiz kalmamış.

```
[ORTAK BAĞLAM bloğunu buraya yapıştır]

GÖREV — FAZ 5: Kalan strateji denetimi

Faz 1 (klasik formasyonlar) ve Faz 2 (pair) tamamlandı. Geriye kalan
göstergeler aynı titizlikle denetlenecek. HER BİRİ için üç soruyu yanıtla ve
docs/spec/STRATEJI_DENETIM_v2.md'ye tablo hâlinde yaz:

  (1) Bu göstergenin her eşiği/sabiti NEREDEN geliyor? (kitap/makale/ölçüm/
      "makul varsayılan"). "Makul varsayılan" olanlar ayrı işaretlensin —
      bunlar Faz 8'de kalibre edilecek.
  (2) Literatürdeki tanımda VAR olup kodda OLMAYAN bir kural var mı?
  (3) Gerçek veride ne sıklıkta sinyal üretiyor? (sinyal/sembol/yıl)
      Anormal yüksekse (ör. günde birden fazla) SEBEBİNİ bul.

DENETLENECEK GÖSTERGELER VE BİLİNEN ŞÜPHELER:

A) harmonic.* (8 ekol)
   - CLAUDE.md'de açık: harmonic.five_zero 622 sembollük TAM evrende HİÇBİR
     aday bulamadı, iki farklı parametre setiyle de. KÖK NEDEN ARAŞTIRILMADI.
     Bu fazda araştır: geometry.generate_candidates 6 noktalı (0,X,A,B,C)
     pencereyi gerçekten üretiyor mu? five_zero'nun oran bandları
     schools/five_zero.py'de doğru mu? Bir sentetik 5-0 formasyonu kur ve
     motorun onu bulup bulmadığını TEST ET.
   - gilmore.py bilinçli olarak K1-D güncellemesinin dışında bırakılmış
     (eski 1.27/1.618 bandı). Gözden geçir: kendi kaynağına göre doğru mu?
   - PRZ toleransları (carney ±0.03, pesavento ±0.05) kaynaklı; diğerleri?

B) trend.breakouts (MultiBreakout, ~20 kırılım türü)
   - quality_score ağırlıkları (hacim .30 / yaş .20 / temas .20 / gövde .15 /
     mesafe .15) görev metninden geliyor ama NORMALIZASYON SABİTLERİ
     "makul varsayılan" olarak kodda. Gerçek dağılımı ölç: skorlar [0,1]
     aralığına dengeli mi yayılıyor yoksa bir uçta mı yığılıyor?
   - 20 kırılım türü aynı anda açıkken bir sembol tek barda 5-6 sinyal
     üretebilir. Bu, "çok fazla sinyal" hissinin ikinci kaynağı olabilir.
     Türleri gruplandırıp (trend / seviye / kanal / MA) tek bir birleşik
     sinyale indirgemeyi değerlendir.

C) trend.ewmac
   - CLAUDE.md'de AÇIK TODO: forecast_scalar hâlâ empirik/rolling hesaplanıyor;
     K3'ün kitaptan DOĞRULADIĞI sabit tablo ((2,8)->10.6 ... (64,256)->1.87)
     entegre edilmedi. Bu fazda entegre et: sabit tablo seçeneği + parametre,
     varsayılan sabit tablo. Farkı ölç ve raporla.

D) structure.* (swing_fib_abcd, price_structure, golden_zone, supply_demand)
   - price_structure diğerlerinden 10-30x YAVAŞ (O(n^2) trendline aday
     üretimi). Tam evren taramasında darboğaz. Profille ve optimize et:
     aday üretimini erken kesme, max_lines düşürme, ya da pivot çiftlerini
     mesafe/eğime göre ön-eleme. Hedef: en az 5x hızlanma, sinyal çıktısı
     DEĞİŞMEDEN (regresyon testi: eski vs yeni sinyal kümesi aynı olmalı).

E) momentum.alpha_rank / momentum.momentum_rank
   - min_liquidity_try = 5.000.000 TL — bu, BİST'in bugünkü işlem hacmine
     göre doğru mu? Evrende kaç sembolü eliyor? Ölç.
   - top_pct = 10 sabit; rank_pct <= top_pct "alfa girişi" sayılıyor.
     Bu, evrenin %10'unun HER ZAMAN sinyal üretmesi demek — yani
     600 sembolde 60 sinyal, her gün. Bu bir "sinyal" mi yoksa bir
     "sıralama" mı? Arayüzde ayrım yap: bunlar TARAMA ÇIKTISI, tekil
     AL sinyali değil. labels_tr.py'de ve /scan'de bunu görünür kıl.

F) patterns.wedge / triangle / broadening / flag_pennant
   - Faz 1'de eklenen pattern_context (ön trend, min derinlik, hacim onayı)
     bunlara da uygulanmalı. broadening'de prior_trend_lookback ZATEN var
     ama kullanılıyor mu? wedge ve flag_pennant'ta yok.
   - flag_pennant: pole_atr=2.0, flag_max_bars=20, max_retrace=0.5 —
     kaynakları?

ÇIKTI: docs/spec/STRATEJI_DENETIM_v2.md
  - Gösterge × (eşik, kaynak, durum) tablosu
  - Bulunan GERÇEK hatalar ve düzeltmeleri
  - Sinyal sıklığı tablosu (gösterge başına sinyal/sembol/yıl)
  - "Kalibrasyona muhtaç" listesi (Faz 8'in girdisi)

BİTTİ KRİTERİ:
- Her göstergenin her eşiği için kaynak kolonu DOLU (boş kalan yoksa).
- five_zero kök nedeni bulunmuş (düzeltilmiş ya da "bu formasyon BİST'te
  gerçekten oluşmuyor" diye ÖLÇÜMLE gösterilmiş).
- ewmac sabit forecast scalar tablosu entegre.
- price_structure en az 5x hızlanmış, sinyal çıktısı değişmemiş.
- pytest -q -m "not network" yeşil.
```

---

## FAZ 6 — BİST Evren Taraması sayfası

**Amaç:** Alpha dağılımı, momentum ısı haritası, sektör rotasyonu — tüm evreni bir bakışta gösteren ayrı bir bölüm.

**Bitti kriteri:** `/evren` sayfası çalışıyor; alpha saçılımı ve momentum ısı haritası gerçek BİST evreninden üretiliyor; sektör ve tüm-evren görünümleri var.

```
[ORTAK BAĞLAM bloğunu buraya yapıştır]

GÖREV — FAZ 6: BİST Evren Taraması sayfası

Durum: tlab/viz/universe_charts.py::render_alpha_scatter ve
render_momentum_heatmap ZATEN yazılmış, tlab universe-plot komutu çalışıyor.
Ama web/backend/routes/ altında karşılığı YOK — /scan yalnızca tekil sembol
sinyallerini listeliyor. Kullanıcı isteği: "artifact üzerinde alpha dağılımı
ve momentum ısı haritası gibi tüm bist evrenini tarayabildiğim görseller
mevcut, bunları da entegre etmemiz gerekiyor, bist taraması olarak ayrı bir
noktaya koyarız, orada sektörel veya tüm evrenin yaptığımız taramalarını
ekleriz."

--- 6A: BACKEND ---

web/backend/routes/universe_scan.py (YENİ):
  GET /api/universe/alpha-scatter?market=bist&tf=1d&theme=dark
      -> image/svg+xml. En son tarama koşusundan momentum.alpha_rank
         sonuçlarını okur (ResultsStore), render eder.
  GET /api/universe/momentum-heatmap?market=bist&tf=1d&theme=dark
      -> image/svg+xml.
  GET /api/universe/table?market=bist&tf=1d&sector=&sort=&limit=
      -> JSON: sembol başına alpha_rank/momentum_rank/beta/likidite/sektör.
         Sıralanabilir, sektöre göre filtrelenebilir.
  GET /api/universe/sectors?market=bist
      -> JSON: sektör başına özet (sembol sayısı, ortalama momentum,
         ortalama alfa, lider/geride kalan 3 sembol).

DİKKAT — VERİ KAYNAĞI: UniverseIndicator'lar (alpha_rank/momentum_rank)
scanner/engine.py'de TEK bir işte tüm evreni hesaplıyor ve sonuçları
ResultsStore'a yazıyor. Bu route'lar YENİDEN HESAPLAMAZ — kayıtlı sonucu
okur. Kayıtlı sonuç yoksa 404 + "önce tarama koşun" mesajı.
Eğer last_state'te saklanan alanlar bu görseller için yetmiyorsa,
engine.py'nin ne yazdığını genişlet (hesabı route'a TAŞIMA).

--- 6B: FRONTEND ---

web/frontend/app/evren/page.tsx (YENİ). Sidebar'a "BİST Taraması" girdisi.
Sayfa yapısı:
  1. Üst şerit: piyasa / zaman dilimi / tarama koşusu seçici + "Yenile".
  2. İki büyük görsel yan yana (dar ekranda alt alta):
     - Alpha Dağılımı (α-β saçılımı, ilk %10 vurgulu)
     - Momentum Isı Haritası (sektör × ufuk)
     Her ikisi de <img src="/api/universe/...svg"> olarak. PNG indir butonu.
  3. Altında: SEKTÖR ÖZETİ kartları (katlanabilir) — her sektör için ortalama
     momentum, ortalama alfa, sembol sayısı, lider 3 / geride kalan 3.
     n<5 olan sektörler "yetersiz örneklem" uyarısı taşısın (bilanco-radar'daki
     sektor-siniflandirma skill'inin AYNI kuralı).
  4. En altta: SIRALANABİLİR TAM TABLO (tüm evren). Kolonlar: sembol, sektör,
     alpha_rank %, momentum_rank %, β, yıllık α, likidite, son fiyat.
     Arama kutusu. Bir satıra tıklanınca /chart?symbol=...'a gider.
  5. Sekme: "Tüm Evren" / "Sektörel". Sektörel sekmede tablo sektöre göre
     gruplanmış ve katlanabilir.

Tasarım: Faz 3'te kurulan 3 tema token'ları (globals.css + lib/themes.ts)
kullanılacak, yeni renk TANIMLANMAYACAK.

--- 6C: TARAMA TETİKLEME ---

web/backend/routes/scan_trigger.py: universe kategorisini de tetikleyebilsin
(şu an needs_universe=True göstergeler için ayrı bir yol var mı, kontrol et).
/evren sayfasında "Evren Taramasını Yenile" butonu.

BİTTİ KRİTERİ:
- /evren sayfası çalışıyor, iki görsel gerçek BİST evreninden geliyor.
- Sektörel ve tüm-evren görünümleri, sıralanabilir tablo, arama.
- n<5 sektör uyarısı görünür.
- Backend route'ları HESAP YAPMIYOR (yalnızca ResultsStore okuyor + render).
- pytest -q -m "not network" yeşil + route'lar için en az 4 test.
```

---

## FAZ 7 — Web arayüzü, 3 tema, hız · ⚠️ YERİNİ `SITE_TASARIM_YOL_HARITASI.md` ALDI

> **2026-09-03 güncellemesi — BU FAZI ATLA.** `docs/SITE_TASARIM_YOL_HARITASI.md` bu işi daha eksiksiz kapsıyor: tasarım sistemi ve kabuk **S1+S2**'de (o belgenin `### 4.1` promptu), tarama ve grafik yüzeyi **S3+S4**'te (`### 4.2`), performans/erişilebilirlik/mobil **S8**'de (`### 4.4`). Aşağıdaki metin referans olarak duruyor; sıra için `docs/00_BASLANGIC_SIRASI.md`'ye bak.

**Amaç:** Siteyi artifact'in kabuk (shell) tasarımına taşımak; 3 temayı gerçekten uçtan uca tutarlı kılmak; algılanan hızı düzeltmek.

**Bitti kriteri:** Üç tema (Klasik Beyaz Rapor / Terminal Koyu / Kağıt Rapor) sayfanın **tamamında** tutarlı; grafik yüklenmesi anlık; `/scan` tablosu 500+ satırda takılmıyor.

```
[ORTAK BAĞLAM bloğunu buraya yapıştır]

GÖREV — FAZ 7: Web arayüzü + 3 tema + hız

ÖNCE OKU: docs/design/grafik_stil_vitrini.html'in KABUK (shell) CSS'i
(satır ~4-135: --shell-* değişkenleri, .pick-card, .tab, .stage-wrap,
.chart-note, .signal-box, .ai-report, .notes-card, .filmstrip). Bu, sitenin
hedeflenen kabuk dilidir — şu anki arayüz (Tailwind varsayılanları + birkaç
token) bunun çok gerisinde.

--- 7A: TASARIM SİSTEMİ ---

1. web/frontend/app/globals.css: token setini artifact'in shell'iyle hizala.
   Eksik olanlar: --radius ölçeği, --shadow katmanları, eyebrow/section-label
   tipografisi, mono/serif/sans font üçlüsü (tema başına farklı:
   classic -> Source Serif 4 display + Inter body + IBM Plex Mono;
   dark -> JetBrains Mono display + Inter body + JetBrains Mono;
   editorial -> Playfair Display + Source Serif 4 + IBM Plex Mono).
   Fontlar next/font ile yerel yüklensin (CDN'e bağımlılık YOK).
2. web/frontend/lib/themes.ts: 3 temanın TAM token seti. Artifact'in
   THEMES.classic / .dark / .editorial değerleriyle BİREBİR.
   saas ve neon EKLENMEYECEK (kullanıcı kararı: 3 tema).
3. Ortak bileşenler (web/frontend/components/ui/): Card, SectionLabel,
   Eyebrow, Pill, Tab, StatTile, Table. Her sayfa bunları kullansın —
   şu an her sayfa kendi Tailwind sınıflarını yazıyor.

--- 7B: SAYFA YENİDEN DÜZENİ ---

/chart sayfası artifact'in "stage" düzenine geçsin:
  - stage-wrap: kart çerçevesi + grafik + stage-caption
  - note-wrap: "Nasıl Okunur" 4 kutulu grid (NEREYE BAK / NE ÖLÇER /
    DEĞERLER NE DEMEK) — ChartGuide.tsx bunu ZATEN üretiyor, sadece
    artifact'in .chart-note grid'ine oturt
  - signal-box: sol kenarlıklı vurgulu kutu ("AL SİNYALİ NE ZAMAN OLUŞUR")
  - ai-report: ayrı kart, dashed tag
  - filmstrip: aynı grafiğin 3 temada küçük önizlemesi (opsiyonel, artifact'te
    var ve çok işe yarıyor)

/scan sayfası:
  - Faz 0'da eklenen "Yaş" sütunu ve tazelik filtresi öne çıksın
  - Sinyal satırları KART değil YOĞUN TABLO (Bloomberg/Koyfin yoğunluğu)
  - Satır üzerine gelince o sinyalin küçük grafik önizlemesi (hover preview,
    /api/chart.svg'den, boyut küçük)
  - Kategori filtreleri chip (tab) olarak, dropdown değil

--- 7C: HIZ ---

Ölç, sonra düzelt. Şu an bilinen darboğazlar:
1. Grafik: Faz 3-4'ten sonra SVG geliyor, kaleido yok. Ama ÖLÇ ve raporla.
   SVG'yi <img src> yerine INLINE gömmeyi değerlendir (tek istek daha az,
   tema değişince yeniden fetch gerekmez, CSS değişkenleriyle anında
   tema değişir).
2. /scan tablosu: 500+ satırda React render'ı yavaşlıyor mu? Ölç.
   Yavaşsa sanallaştırma (virtualization) ekle.
3. /api/chart.svg: aynı (symbol, tf, indicator, theme) için sunucu tarafı
   önbellek. Şu an chart_png.py'de Cache-Control var ama sunucu tarafı
   memoization yok; price_structure gibi O(n^2) göstergelerde bu önemli.
   Anahtar: (symbol, tf, indicator, theme, son_bar_zamani).
4. İlk yüklemede /api/catalog + /api/categories + /api/runs + /api/signals
   ardışık gidiyor. Paralelleştir.

--- 7D: GÖRSEL DOĞRULAMA ---

Bu faz TARAYICIDA doğrulanır. Playwright kullan (repoda ZATEN Chromium
kurulu değilse pyproject/package.json'a ekle):
1. scripts/ui_snapshot.py (ya da playwright test): /scan, /chart, /evren
   sayfalarını 3 temada, 2 ekran genişliğinde (1440 ve 768) ekran görüntüsü
   alır -> docs/design/ui/<sayfa>_<tema>_<genislik>.png
2. Bu PNG'leri Read ile AÇ VE GÖR. Sorunları madde madde yaz, düzelt,
   tekrarla. EN AZ 3 İTERASYON.
3. Türkçe karakter kontrolü: İ, ı, Ğ, ğ, Ş, ş, Ç, ç, Ö, ö, Ü, ü — her
   temada ve her fontta doğru render ediliyor mu (ekran görüntüsünde GÖR).

BİTTİ KRİTERİ:
- 3 tema sayfanın TAMAMINDA tutarlı (grafik + kabuk + tablo + rapor).
- docs/design/ui/ altında 3 sayfa × 3 tema × 2 genişlik görüntü, hepsi
  GÖRÜLMÜŞ ve en az 3 iterasyon geçmiş.
- Ölçülmüş hız raporu: sayfa yükleme, grafik üretimi, tablo render.
- npm run build + npm run lint temiz; pytest -q -m "not network" yeşil.
```

---

## FAZ 8 — Doğrulama harness'ı: sinyaller gerçekten çalışıyor mu?

**Amaç:** Bugüne kadar hiç sorulmamış soruyu sormak: bu stratejilerin **ileriye dönük getirisi** var mı?

**Neden en sonda:** Faz 1/2/5 kuralları düzeltmeden yapılan bir backtest, yanlış kuralları ölçer.

**Bitti kriteri:** Her gösterge için forward-return dağılımı, isabet oranı ve rastgeleye karşı üstünlük testi var; eşikler bu ölçüme göre kalibre edilmiş.

```
[ORTAK BAĞLAM bloğunu buraya yapıştır]

GÖREV — FAZ 8: Sinyal doğrulama ve kalibrasyon harness'ı

Bugüne kadar sistemin ürettiği sinyallerin İLERİYE DÖNÜK getirisi hiç
ölçülmedi (tlab/backtest/ yalnızca pair motoru ve Carver metrikleri içeriyor).
Faz 1/2/5 kuralları düzelttikten sonra artık ölçülebilir.

--- 8A: FORWARD-RETURN HARNESS ---

tlab/backtest/signal_eval.py (YENİ):
  evaluate_signals(signals, price_data, horizons=(1,5,10,21,63)) -> DataFrame
  Her sinyal için: sinyal barından sonraki h bar getirisi (long ise +,
  short ise -), aynı dönemin ENDEKS getirisi (XU100), ikisinin farkı (alfa).
  Non-repaint: getiri sinyal barının KAPANIŞINDAN itibaren; execution
  parametresi ("close" | "next_open") ile.

  bootstrap_baseline(signals, price_data, horizons, n_iter=1000) -> DataFrame
  Aynı sayıda RASTGELE (sembol, tarih) çifti seç, aynı getirileri hesapla.
  Bu, "sinyal gerçekten bilgi taşıyor mu yoksa sadece piyasa mı yükseldi"
  sorusunun cevabıdır. p-değeri: gerçek ortalama getirinin bootstrap
  dağılımındaki yüzdelik konumu.
  DİKKAT: rastgele örneklem, gerçek sinyallerin TARİH DAĞILIMINI korumalı
  (aynı aylardan örnekle) — yoksa boğa/ayı dönem karışımı sonucu bozar.

--- 8B: TAM TARAMA VE ÖLÇÜM ---

scripts/sinyal_dogrulama.py (YENİ):
1. BIST tam evreni (648 sembol), 1D + 4H, en az 3 yıllık geçmiş,
   TÜM göstergeler için tarihsel tarama koş (checkpoint'li — kesilirse
   kaldığı yerden devam etsin).
2. Her (gösterge, yön, durum) kombinasyonu için:
   - sinyal sayısı
   - h=1,5,10,21,63 için ortalama/medyan getiri ve alfa
   - isabet oranı (pozitif alfa oranı)
   - bootstrap p-değeri
   - hedef isabet oranı (kaç tanesi kendi ölçülü-hareket hedefine ulaştı)
   - ortalama maksimum ters hareket (MAE — stop yerleştirmek için)
3. docs/spec/SINYAL_DOGRULAMA_v1.md: tam tablo + yorum.
   Bootstrap p>0.10 olan göstergeler "istatistiksel destek YOK" diye
   AÇIKÇA işaretlensin. Bu sonucu yumuşatma — bir strateji çalışmıyorsa
   çalışmadığını yazmak, onu sisteme tavsiye olarak koymaktan iyidir.

--- 8C: KALİBRASYON ---

Faz 5'in "kalibrasyona muhtaç" listesindeki her eşik için:
  - Eşiği bir aralıkta tara (ör. double_top eq_tol 0.010-0.025)
  - Her değerde sinyal sayısı + ortalama alfa + bootstrap p'yi ölç
  - "Sinyal sayısı × alfa" eğrisini çıkar
  - Öneriyi gerekçesiyle yaz
DİKKAT — AŞIRI UYDURMA (overfitting) TEHLİKESİ: tlab/backtest/metrics.py
Carver'ın fitting disiplini kurallarını ZATEN taşıyor (min_sharpe_threshold,
PESSIMISM_FACTOR, speed_limit_check). Kalibrasyon önerilerini BUNLARDAN
geçir; kural sayısı / veri yılı oranı eşiği aşarsa öneriyi REDDET.
Ayrıca kalibrasyonu ilk %70 veride yap, son %30'da DOĞRULA.

--- 8D: ARAYÜZE BAĞLA ---

Her sinyalin yanında "bu göstergenin tarihsel isabeti" göstergesi:
  /scan tablosuna "Tarihsel" kolonu: h=10 için ortalama alfa ve isabet oranı
  (docs/spec/SINYAL_DOGRULAMA_v1.md'den üretilen bir JSON'dan okunur,
  canlı hesap YAPILMAZ).
  Bootstrap p>0.10 olan göstergeler tabloda soluk/uyarı işaretli.

BİTTİ KRİTERİ:
- signal_eval.py + bootstrap + testleri.
- Tam evren tarihsel taraması koşulmuş, docs/spec/SINYAL_DOGRULAMA_v1.md yazılmış.
- En az 5 eşik kalibre edilmiş, her biri OOS'ta doğrulanmış.
- /scan'de "Tarihsel" kolonu.
- pytest -q -m "not network" yeşil.
```

---

## 3 · Araç ve agent önerileri (madde 5'in yanıtı)

Soru: *"Şimdiye kadar tüm kodlamaları görselleştirmeleri Sonnet ile yaptım fakat görselleştirme kısmında tam olarak istediğime ulaşamadık. Kullanabileceğim başka ek araç veya agent var mı?"*

**Kısa yanıt: sorun modelde değil, döngüde.** Sonnet, aylardır kendi çizdiği grafiği **hiç görmedi**. Kod yazdı, sen baktın, "olmamış" dedin, o tekrar kod yazdı. Bu döngüde model ne kadar iyi olursa olsun sonuç yavaş yakınsar. Aynı repoda kart tarafında bu döngü **zorunlu** (`kart-tasarim-sistemi` skill'i "PNG üret → PNG'yi aç ve GÖR → düzelt, en az 3 iterasyon" diyor) ve kartlar grafiklerden belirgin şekilde daha iyi durumda. Fark tesadüf değil.

### Sırayla yapılacaklar (etki × maliyet sırasına göre)

**1. Tasarımı hedef olmaktan çıkarıp şartname yap — YAPILDI.**
Artifact `docs/design/grafik_stil_vitrini.html` olarak repoya alındı. 19 grafik türünün **çalışan SVG üreteci** artık Sonnet'in okuyabileceği bir dosya. Bundan sonra brief "artifact'e benzesin" değil, "`sceneDoubleTopBottom()`'ı satır satır Python'a çevir" olacak. Yorum belirsizliği sıfıra iner.

**2. Görsel geri bildirim döngüsünü zorunlu kıl (Faz 0, İş 2).**
`teknik-analiz/.claude/skills/grafik-tasarim-sistemi/SKILL.md` + `.claude/agents/grafik-tasarimcisi.md`. Skill'in içindeki en kritik cümle: *"çıktıyı Read ile AÇ ve GÖR, gördüğün sorunları madde madde yaz, düzelt, en az 3 iterasyon."* Claude, PNG'yi gerçekten görüntü olarak okur — bu bir formalite değil, kapalı devre.

**3. Golden-image gerileme testi (Faz 0, İş 3).**
Onaylanmış çıktılar `tests/test_viz/golden/` altında. Bir değişiklik grafiği bozarsa **test kırılır** — sen fark edene kadar beklemez. Tasarım kalitesi böylece "beğeni" olmaktan çıkıp CI kapısı olur.

**4. Playwright / Chrome DevTools MCP — ama sadece web arayüzü için (Faz 7).**
Tarayıcıda render edilen şeyi (site kabuğu, tablolar, tema geçişleri, Türkçe glifler, responsive kırılımlar) doğrulamak için. Grafikler artık sunucuda SVG üretileceği için grafik tarafında tarayıcıya gerek yok — sadece dosyayı açıp bakmak yeter, bu daha hızlı ve daha güvenilir.

**5. Model seçimi — faz tipine göre ayır.**
- **Tasarım/spec/mimari fazları** (Faz 3'ün layout motoru, Faz 4'ün ilk sahnesi, Faz 2'nin istatistik kısmı): daha güçlü modelde yap. Bunlar bir kere doğru kurulunca gerisi mekanikleşiyor.
- **Mekanik port fazları** (Faz 4b/4c'nin kalan sahneleri, ilk sahne deseni oturduktan sonra): Sonnet fazlasıyla yeterli ve daha hızlı/ucuz.
- Pratik kural: **"ilk örneği güçlü modelde yaz, kalan 18'ini Sonnet'e port ettir."**

**6. Anthropic'in hazır tasarım skill'leri.**
Oturumda `dataviz` (grafik/dashboard tasarım metodolojisi: form seçimi, renk formülü ve doğrulayıcısı, işaret spesifikasyonları, etkileşim kuralları) ve `artifact-design` mevcut. Faz 3'ün başında `dataviz`'i çağırmak, renk/eksen/legend kararlarını sıfırdan tartışmaktan kurtarır.

**7. Bağlam hijyeni — Faz 4'ü 3 oturuma bölmenin sebebi bu.**
19 sahne tek oturumda portlanmaz; 10. sahnede model ilk sahnenin kurallarını unutur. Skill dosyası kalıcı hafıza görevi görür, `docs/design/iterasyon/` de görsel hafıza.

### Ne YAPILMAMALI

- **Plotly'de daha fazla ısrar.** `renderer.py` 2884 satır ve büyük kısmı Plotly'yi yenme çabası. Buradan sonrası azalan verim.
- **Hazır bir grafik kütüphanesi aramak.** Araştırıldı: `lightweight-charts` finansal grafikte iyi ama özel overlay/etiket kontrolü sınırlı; ECharts/Highcharts aynı sorun; D3 zaten "kendin çiz" demek — o zaman doğrudan SVG üret, JS bağımlılığı taşıma. Aradığın şeyi (etiket çakışma çözücü + önder çizgi + hap rozet + sahneye özel yerleşim) **hiçbir kütüphane hazır vermiyor**; artifact de zaten kütüphanesiz yazılmış.
- **Grafiği tarayıcıya taşımak.** Cazip (etkileşim gelir) ama çizim mantığı ikiye bölünür ve PNG dışa aktarım/tarama önizlemesi zorlaşır. Önce sunucuda SVG'yi mükemmelleştir; etkileşim (crosshair, zoom) sonra **aynı SVG'nin üstüne** ince bir JS katmanıyla eklenebilir.

---

## 4 · Kaynakça

**Formasyon tanımları**
- Lo, A. W., Mamaysky, H., & Wang, J. (2000). *Foundations of Technical Analysis: Computational Algorithms, Statistical Inference, and Empirical Implementation.* Journal of Finance 55(4). — HS/IHS/DTOP/DBOT'un biçimsel tanımları; %1.5 tolerans, 22 işlem günü ayrım kuralı, çekirdek regresyonuyla ekstremum tespiti. https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.00265
- Bulkowski, T. — *Encyclopedia of Chart Patterns* / thepatternsite.com. Çift dip: düşen ön trend, dipler arası ≥%10 yükseliş, dipler arası fiyat farkı ≤%4-6, %16 başabaş başarısızlık oranı, %65 throwback, ölçülü hareket hedefine ulaşma %73. OBO/TOBO: omuz simetrisi (şekil/mesafe/fiyat), hacim deseni (sol omuz veya baş yüksek, sağ omuz düşük), **yukarı eğimli boyunda tetik sağ koltukaltı tepesi**, aşağı eğimli boyunlu TOBO'lar belirgin daha iyi performans. https://thepatternsite.com/hsb.html · https://www.thepatternsite.com/HSBSym.html · https://thepatternsite.com/dbsetup.html
- Fair Value Gap (3 mumlu dengesizlik) tanımı: https://trendspider.com/learning-center/fair-value-gap-trading-strategy/ · https://www.fluxcharts.com/articles/fair-value-gaps-fvg-explained

**Kointegrasyon / istatistiksel arbitraj**
- Engle-Granger kalıntı testinin standart ADF kritik değerleriyle kullanılamayacağı; MacKinnon kointegrasyon kritik değerlerinin gerekliliği: https://www.mathworks.com/help/econ/egcitest.html · https://arch.readthedocs.io/en/stable/unitroot/unitroot_cointegration_examples.html · https://real-statistics.com/time-series-analysis/time-series-miscellaneous/engle-granger-test/
- Gatev, E., Goetzmann, W. N., & Rouwenhorst, K. G. (2006). *Pairs Trading: Performance of a Relative-Value Arbitrage Rule.* Review of Financial Studies 19(3). — mesafe yöntemi, tüm likit ABD evreni, 12 aylık oluşum penceresi, en iyi 20 çift. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=141615
- Do, B., & Faff, R. (2010). — **sektör-içi kısıtın getirileri artırdığı**, daha ince sektör sınıflandırmasının performansı daha da iyileştirdiği bulgusu; 1990'lardan sonra yakınsama olasılığının düşmesi. (Bkz. Krauss 2017 içindeki değerlendirme.)
- Krauss, C. (2017). *Statistical Arbitrage Pairs Trading Strategies: Review and Outlook.* Journal of Economic Surveys 31(2), 513-545. — beş yaklaşımın (mesafe / kointegrasyon / zaman serisi / stokastik kontrol / diğer) karşılaştırması, veri gözetleme (data snooping) uyarıları. https://onlinelibrary.wiley.com/doi/abs/10.1111/joes.12153
- Benjamini, Y. & Hochberg, Y. (1995). FDR kontrolü. — çok sayıda çift taranırken zorunlu. https://www.publichealth.columbia.edu/research/population-health-methods/false-discovery-rate
- Referans uygulama (kullanıcının işaret ettiği repo): https://github.com/leoncuhk/awesome-quant-ai/blob/main/book/myquant/chapter2.md (istatistiksel arbitraj: `coint`, z eşikleri 2.0/0.5/3.0, 30 günlük zaman stopu, stop sonrası kilit, in-sample β + out-of-sample işlem) ve `chapter3.md` (GERÇEK arbitraj: nakit-vadeli, put-call paritesi, dönüştürülebilir tahvil).

**Görselleştirme**
- `docs/design/grafik_stil_vitrini.html` — bu projenin kendi tasarım şartnamesi (19 sahne, 5 tema, saf SVG).
- Kütüphane karşılaştırması: https://www.ridhwaan.xyz/blog/choosing-a-charting-library-echarts-d3-recharts-plotly-chartjs-deckgl/

**Bu belgedeki ölçümler**
- Monte Carlo (400 deneme × 3 örneklem boyu, bağımsız rastgele yürüyüşler) ve BH-FDR hesabı bu oturumda `statsmodels 0.15.0` ile koşuldu; betikler `scripts/` altına Faz 2'de kalıcılaştırılacak.
- Saf SVG üretim ölçümü: 300 mum, 50 tekrar, 0.46 ms/grafik.

---

## 5 · Yürütme notları

- **Faz 1, 2 ve 3 paralel yürütülebilir** — farklı dosyalara dokunuyorlar. Üç ayrı oturum aç.
- **Her fazın sonunda** `pytest -q -m "not network"` + `tlab lint` + CLAUDE.md güncellemesi. Bunlar atlanırsa bir sonraki oturum bağlamı kaybeder.
- **Onay kapıları:** Faz 1'in denetim raporu (10 grafiğin gözle incelenmesi), Faz 2'nin çift sayısı düşüşü, Faz 3'ün ilk sahnesi ve Faz 4'ün her grubu — bunlar sana gösterilmeden bir sonraki adıma geçilmemeli. En pahalı hata, yanlış bir tasarım kararının 19 sahneye yayılmasıdır.
- **Beklenti kalibrasyonu:** Faz 1 ve 2'den sonra sinyal sayısı **belirgin şekilde düşecek**. Bu bir kayıp değil, düzeltmenin ta kendisi — 606 çiftin ~36'ya inmesi, sistemin nihayet doğru çalıştığının göstergesi.
