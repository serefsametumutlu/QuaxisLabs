# Tam Strateji Denetimi — 24 gösterge, kod + literatür + görsel

**Tarih:** 2026-09-03 · Kapsam: `tlab/indicators/` altındaki **tüm** göstergeler, `tlab/features/` temel katmanı, `tlab/scanner/engine.py` + `eod.py` yürütme yolu, ve her göstergenin ürettiği görsel primitiflerin `docs/design/grafik_stil_vitrini.html` ile karşılaştırması.

Bu belge `docs/TANI_VE_YOL_HARITASI_v2.md`'nin devamıdır. Orada Faz 5 "kalan stratejilerin denetimi" olarak ertelenmişti — **bu denetim şimdi yapıldı**, sonuçları aşağıda ve Faz 1/5 kapsamı buna göre genişletilmelidir.

---

## A · Üç sistemik bulgu

Bunlar tek bir göstergenin hatası değil; **tüm sistemi** aynı anda etkiliyor ve tek tek gösterge düzeltmelerinden önce kapatılmalı.

### A1 · Pivot tanımı gürültü üretiyor — ve bu, formasyonların TAMAMINI besliyor

Sistemdeki her formasyon (harmonik 8 ekol, OBO/TOBO, çift tepe/dip, takoz, üçgen, genişleyen, golden zone, AB=CD, kanal) tek bir zigzag üzerine kurulu: `find_pivots(df, left=3, right=3)` → `alternate_pivots(...)`. Bu varsayılan **istisnasız her yerde** aynı.

`left=3, right=3` demek: "kendisinden önceki 3 ve sonraki 3 bardan daha yüksek/alçak bar". Sentetik ama gerçekçi bir 4H serisinde ölçüldü (`scripts/pivot_yogunluk_olcumu.py`, n=1000, seed=7):

| Zigzag yöntemi | 100 barda pivot | Ort. bacak uzunluğu | Ort. bacak büyüklüğü |
|---|---|---|---|
| **`find_pivots(3,3)` — mevcut varsayılan** | **14.5** | **6.9 bar** | %8.6 |
| `find_pivots(5,5)` | 9.1 | 10.8 bar | %11.1 |
| `find_pivots(10,10)` | 4.8 | 19.7 bar | %14.7 |
| `atr_zigzag(mult=2.0)` | 9.2 | 10.7 bar | %11.2 |
| **`atr_zigzag(mult=3.0)`** | **4.3** | **23.0 bar** | %16.7 |

4H'te 7 barlık bir bacak **bir günden kısa**. Yani sistemin "swing" dediği şey bir günlük dalgalanma. Bir OBO'nun 5 pivotu ≈ 5 gün; bir çift dibin iki dibi ≈ 1 gün arayla. Ekran görüntülerindeki "bu neden çift dip?" hissi buradan geliyor — **kod kendi tanımına göre doğru çalışıyor, tanım yanlış.**

`tlab/features/swings.py::atr_zigzag` **zaten yazılmış ve test edilmiş** durumda (ATR katı kadar ters dönüş ister — ölçek-bağımsız, hem 4H'te hem 1D'de aynı ekonomik anlamı taşır). Ama:

- `harmonics` ve `swing_fib_abcd` `zigzag_method` parametresini **sunuyor**, varsayılanı `"fixed"`;
- `head_shoulders`, `double_top_bottom`, `golden_zone`, `wedge`, `broadening`, `weekly_channel`, `price_structure` bu seçeneği **hiç sunmuyor** — doğrudan `find_pivots(df, p.left, p.right)` çağırıyor.

**Not:** `golden_zone` bu konuda tek doğru davranan modül — `min_swing_atr: float = 3.0` ile önemsiz swing'leri eliyor. Yani çözüm deseni projede zaten var, yayılmamış.

**Öneri:** ortak bir `tlab/features/swings.py::significant_pivots(df, method, ...)` girişi; tüm formasyon göstergeleri oradan beslensin; varsayılan `atr_zigzag(mult≈2.5-3.0)` ya da `find_pivots` + `min_swing_atr` filtresi. Bu **tek değişiklik**, aşağıdaki gösterge-özel düzeltmelerin çoğundan daha fazla etki eder.

### A2 · Bar sayısı cinsinden hiçbir parametre zaman dilimine göre ölçeklenmiyor

`tlab/scanner/engine.py::_run_single_worker` göstergeyi `CATALOG[name].factory()` ile kurar — yani **varsayılan parametrelerle**, ve `run_eod(timeframes=("4h","1d"))` aynı nesneyi iki zaman diliminde de koşar. Bar cinsinden yazılmış her eşik 4H'te **kalendar olarak 6 kat kısa** anlama gelir.

| Gösterge | Parametre | 1D karşılığı | 4H karşılığı | Literatür |
|---|---|---|---|---|
| `double_top_bottom` | `min_bars_between=5` | 1 hafta | **0.8 gün** | 22 işlem günü (LMW) |
| `wedge` / `triangle` | `min_bars=15` | 3 hafta | **2.5 gün** | min. 3 hafta (Bulkowski) |
| `broadening` | `min_bars=15` | 3 hafta | **2.5 gün** | min. 3 hafta |
| `flag_pennant` | `flag_max_bars=20` | 4 hafta | **3.3 gün** | maks. 3 hafta |
| `flag_pennant` | `pole_bars=5` | 1 hafta | **0.8 gün** | "hızlı, dik direk" |
| `price_structure` | `range_min_bars=10` | 2 hafta | 1.7 gün | — |
| `momentum_rank` | `horizons=(21,63,126,252)` | 1/3/6/12 ay | **3.5/10/21/42 gün** | 12-1 (Jegadeesh–Titman) |
| `alpha_rank` | `windows=(60,120,250)` | 3/6/12 ay | **10/20/42 gün** | — |
| `ewmac` | `pairs=(2,8)…(64,256)` | Carver'ın **günlük** tablosu | ölçek bozuk | Carver, günlük veri |

Son üçü sadece "gevşek" değil, **akademik olarak geçersiz**: Jegadeesh–Titman momentumu 3–12 aylık bir olgudur ve **kısa ufuklarda işaret tersine döner** (kısa vadeli dönüş etkisi). 42 barlık bir "252" ufku momentum ölçmüyor, gürültü ölçüyor.

**Öneri:** `BaseParams`'a bir `for_timeframe(tf)` dönüştürücüsü; bar-cinsi alanlar `@bars_field(daily=22)` gibi işaretlensin ve zaman dilimine göre çarpılsın (4H→×6, W1→÷5). Alternatif ve daha basit: `config/settings.yaml`'da zaman dilimi başına parametre bloğu, `engine.py` factory'yi bununla kursun.

### A3 · `supported_timeframes` sözleşmesi hiç uygulanmıyor

Her göstergenin `IndicatorMeta.supported_timeframes` alanı **doğru doldurulmuş**:

- `momentum.alpha_rank` → `(D1,)`
- `momentum.momentum_rank` → `(D1,)`
- `trend.weekly_channel` → `(W1, D1)`
- diğerleri → `(D1, H4)`

Ama `tlab/scanner/engine.py`, `tlab/scanner/eod.py`, `tlab/core/indicator.py` ve `tlab/viz/live.py`'nin **hiçbiri bu alanı okumuyor** (`grep -n supported_timeframes` → o dosyalarda sıfır sonuç). Sonuç:

- **`momentum.alpha_rank` ve `momentum.momentum_rank` 4H'te koşuyor** — kendi bildirdikleri sözleşmeyi ihlal ederek, ve A2'deki nedenle anlamsız sonuç üreterek.
- **`trend.weekly_channel` W1'de HİÇ koşmuyor** (`run_eod` yalnızca 4H+1D tarıyor) ama desteklemediği 4H'te koşuyor. "Haftalık kanal" göstergesi haftalık veriyi hiç görmemiş durumda.

**Öneri:** tek satırlık kapı — `engine.run()` bir (gösterge, tf) çifti için `tf not in spec.factory().meta.supported_timeframes` ise işi hiç açmasın; `run_eod`'a `w1` eklensin.

### A4 (bonus) · Hacim hiçbir formasyonda filtre değil

Beş formasyon modülünün **hepsinde** aynı desen:

```python
confirm_sig.payload["volume_ok"] = bool(volume[idx] >= p.vol_k * vma)
```

Hesaplanıyor, `payload`'a yazılıyor, **sinyali hiç engellemiyor**. `vol_k` parametresi var ama hiçbir yerde `continue`/eleme üretmiyor (`broadening.py:201`, `double_top_bottom.py:163`, `flag_pennant.py:200`, `head_shoulders.py:175`, `wedge.py:246` — beşi de sadece payload). Bulkowski'nin kırılım onayı kriterlerinden biri hacim; bu bilgi üretilip çöpe atılıyor.

Ayrıca **oluşum sırasındaki hacim trendi** hiç bakılmıyor: Bulkowski takoz/üçgende hacmin oluşum boyunca **%79 oranında düştüğünü**, bayrak/flamada da düştüğünü, OBO'da sol omuz/baş yüksek → sağ omuz düşük deseni olduğunu belirtiyor.

---

## B · Gösterge gösterge denetim

Durum kodları: ✅ sağlam · ⚠️ eksik kural / kalibrasyon gerekli · ❌ gerçek hata

### Klasik formasyonlar (`patterns/`)

| Gösterge | Durum | Bulgular |
|---|---|---|
| `patterns.double_top_bottom` | ❌ | `min_bars_between=5` (LMW: 22 gün); `eq_tol=0.02` (LMW: 0.015); ön trend yok; dipler arası ≥%10 yükseliş kuralı yok; min derinlik yok; hacim filtre değil; hologram gerçek kapanış yolunu izlediği için amorf. *(Detay: TANI 1.2)* |
| `patterns.head_shoulders` | ❌ | `neck_slope_max` **bar başına** normalize (40 barda %40 eğime izin verir — kural fiilen hiçbir şey elemiyor); yukarı eğimli boyunlu formasyonlar eleniyor (Bulkowski: tetik sağ koltukaltına kayar); ön trend yok; min derinlik yok; hacim deseni (sol omuz/baş > sağ omuz) hiç kontrol edilmiyor. |
| `patterns.wedge` / `.triangle` | ⚠️ | `min_pivots=4` — Bulkowski **en az 5 temas** ister (bir çizgide 3, diğerinde 2). `min_bars=15` 4H'te 2.5 gün (min. 3 hafta olmalı). Oluşum hacim trendi (%79 düşüş) kontrol edilmiyor. Apeks zamanlaması (fiyat apekse yakın dönüş yapar, ~%75) hiç kullanılmıyor. |
| `patterns.flag_pennant` | ⚠️ | `flag_max_bars=20` 4H'te 3.3 gün; Bulkowski'nin sınırı **3 hafta** — 4H'te ~126 bar. `pole_bars=5` 4H'te <1 gün, "dik direk" tanımına uymuyor. Bayrak içi hacim düşüşü kontrol edilmiyor. `max_retrace=0.5` doğru (klasik kural). |
| `patterns.broadening` | ⚠️ | `prior_trend_lookback=20` **var** — tek doğru davranan formasyon; ama `min_bars=15` aynı ölçek sorunu. `max_bars_to_confirm=90`/`max_bars_to_target=130` sabit (apeksi olmadığı için gerekçeli, kabul). |

### Harmonik formasyonlar (`harmonics/`)

| Konu | Durum | Bulgular |
|---|---|---|
| Ortak geometri + PRZ + durum makinesi | ✅ | Mimari sağlam: aday `C` kesinleştiğinde doğuyor, D deterministik hesaplanıyor, 4 onay politikası, bacak-bazlı `invalidation`. Kaynak (Pesavento TWYS) ile hizalama K1-D'de yapılmış ve farklar belgelenmiş. |
| Pivot girdisi | ❌ | A1 — `zigzag_method="fixed"`, `left/right=3`. Harmonik oranların anlamlı olması için pivotların **gerçek swing** olması gerekir; 7 barlık bacaklarla üretilen XABCD oranları geometrik olarak doğru ama ekonomik olarak anlamsız. |
| `harmonic.five_zero` | ❌ | 622 sembollük tam evrende **hiç aday bulamadı**, iki farklı parametre setiyle de. Kök neden hiç araştırılmadı. Şüphe: `geometry.generate_candidates`'ın 6-noktalı (0,X,A,B,C) penceresi ya hiç üretilmiyor ya da `five_zero`'nun oran bandları geçersiz. **Sentetik bir 5-0 formasyonu kurup motorun bulup bulmadığı test edilmeli.** |
| `harmonic.gilmore` | ⚠️ | K1-D güncellemesinin dışında **bilinçli** bırakılmış (eski 1.27/1.618 bandı). Gerekçe makul ("ekoller birbirini import etmez") ama kendi kaynağına göre doğrulanmamış — Butterfly'ın 2.618'e kadar geçerli olduğu bulgusu Gilmore için de geçerliyse aynı false-negative sorunu orada da var. |
| Görsel | ⚠️ | **X/A/B/C/D köşe etiketleri hiç üretilmiyor.** Gösterge `Polygon:2`, `Line:2`, `Level:3`, `Marker:1` (yalnızca D kutusu) veriyor; artifact'in `harmonicPanel()`'ı her köşeye daire + harf çiziyor. Formasyonu okunur kılan asıl öğe eksik. |

### Yapı göstergeleri (`structure/`)

| Gösterge | Durum | Bulgular |
|---|---|---|
| `structure.golden_zone` | ✅ | Denetimden en temiz çıkan gösterge. `min_swing_atr=3.0` ile önemsiz swing'leri eliyor (A1'in **çözümü** burada zaten var), bant doğumu `finalized_idx`'te, extend-only `end` disiplini doğru. Band `(0.618, 0.786)` + alt band `(0.5, 0.618)` standart. |
| `structure.supply_demand` | ⚠️ | Taban+patlama tanımı (`base_max=5`, `base_atr=0.6`, `impulse_bars=3`, `impulse_atr=2.0`) makul ama **hiçbir kaynağa dayanmıyor** — "makul varsayılan". `max_zones=12` aday havuzu (belgelenmiş). Flip tek seviyeli (belgelenmiş karar). Kalibrasyon adayı. |
| `structure.swing_fib_abcd` | ⚠️ | AB=CD yapısı ve fib merdiveni doğru; `abcd_ratios=(1.0, 1.272, 1.618)` TWYS ile uyumlu. Sorun A1 (pivot gürültüsü) + `max_active_targets=3` ile aynı anda 3 hedef zinciri açılması → tek sembolde onlarca seviye. |
| `structure.price_structure` | ⚠️ | Diğerlerinden **10–30× yavaş** (O(n²) trendline aday üretimi) — tam evren taramasında darboğaz, `/api/chart.png`'de saniyeler. `trendline_max_lines=4` aday havuzu. `profile_window_bars=250` görsel varsayıma bağlı (belgelenmiş). Optimizasyon adayı. |

### Trend göstergeleri (`trend/`)

| Gösterge | Durum | Bulgular |
|---|---|---|
| `trend.breakouts` | ⚠️ | ~20 kırılım türü **aynı anda açık** → tek sembol tek barda 5-6 sinyal üretebiliyor. "Çok fazla sinyal" hissinin ikinci kaynağı. `quality_score` ağırlıkları görev metninden geliyor ama **normalizasyon sabitleri "makul varsayılan"** — skor dağılımı hiç ölçülmedi. Türleri gruplayıp tek birleşik sinyale indirgemek değerlendirilmeli. |
| `trend.weekly_channel` | ❌ | A3 — `supported_timeframes=(W1, D1)` bildiriyor ama tarama 4H+1D koşuyor: **W1'de hiç çalışmıyor, desteklemediği 4H'te çalışıyor.** `n=52` W1'de 1 yıl (doğru), D1'de 52 gün (yanlış anlam), 4H'te 9 gün (anlamsız). |
| `trend.ewmac` | ❌ | **Açık TODO (CLAUDE.md)**: `forecast_scalar` hâlâ empirik/rolling; K3'ün kitaptan doğruladığı sabit tablo ((2,8)→10.6 … (64,256)→1.87) entegre edilmedi. Ayrıca Carver'ın tablosu **günlük** veri için kalibre — 4H'te koşulması ölçeği bozuyor (A2). |
| `trend.ma_systems` | ✅ | `periods=(8,21,55,200)` standart; stack/squeeze mantığı temiz; non-repaint testleri hedefli. Tek not: `squeeze_quantile=0.2` ve `squeeze_window=100` kalibre edilmemiş. |

### Evren göstergeleri (`momentum/`)

| Gösterge | Durum | Bulgular |
|---|---|---|
| `momentum.momentum_rank` | ⚠️❌ | **Akademik temeli sağlam**: `horizons=(21,63,126,252)` + `skip=21` tam Jegadeesh–Titman 12-1 yapısı; `fip` (frog-in-the-pan / bilgi süreksizliği) doğru bir literatür bileşeni; RS eğimi + t-istatistiği doğru hesaplanmış. **İki gerçek sorun:** (1) A3 — D1-only bildirmesine rağmen 4H'te koşuyor, orada momentum işareti **tersine dönebilir** (kısa vadeli dönüş etkisi); (2) `combined_score = score + trend_score - abs(fip)` — üç bileşen **farklı ölçeklerde** (vol-ayarlı momentum ~0–3, t-istatistiği ~−5…+5, fip 0–1) ham hâlde toplanıyor, bu yüzden skoru fiilen `trend_score` domine ediyor. Z-skor/persentil normalizasyonu şart. |
| `momentum.alpha_rank` | ⚠️ | `windows=(60,120,250)` + `min_liquidity_try=5.000.000` — likidite eşiği BİST'in bugünkü hacmine göre **hiç doğrulanmadı**, evrenden kaç sembol elediği bilinmiyor. A3 (4H'te koşuyor) aynı sorun. `top_pct=10` sabit → evrenin **her zaman %10'u** "sinyal" üretiyor: 600 sembolde 60 satır, her gün. Bu bir AL sinyali değil bir **sıralama**; arayüz bu ayrımı yapmıyor. |
| Performans | ❌ | `viz/live.py::compute_live`, `needs_universe` bir gösterge için **tek sembolün grafiğini çizmek üzere tüm evreni** hesaplıyor (600 sembol × cache okuma × cross-sectional rank). `/api/chart.png` bu göstergelerde dakikalarca sürer. Sonuç `ResultsStore`'dan okunmalı. |

### Pair / istatistiksel arbitraj (`pairs/`)

Detaylı denetim `docs/TANI_VE_YOL_HARITASI_v2.md` bölüm 1.4'te. Özet: ham `adfuller` tahmin edilmiş kalıntıda (~3× aşırı-reddetme), çoklu-test düzeltmesi yok (606 → BH-FDR q=0.05 ile 36), iki-yön minimumu düzeltilmemiş, spread'de intercept yok, `RelativeMomentumPair`'de çıkış/zarar-kes/zaman-stopu/kilit yok.

| Gösterge | Durum | Ek bulgu |
|---|---|---|
| `pair.relative_momentum` | ❌ | Yukarıdakiler. Ayrıca `beta_window=60` ile aynı pencerede hem β tahmin ediliyor hem işlem yapılıyor (train/test ayrımı yok). |
| `pair.vol_harvest` | ⚠️ | Motor tasarımı iyi: `adf_pause_p=0.10` + `halflife_max=60` ile **duraklatma** mekanizması var (rejim kırılmasına karşı tek savunma sistemde bu). Ama aynı `adf_pvalue` hatasını miras alıyor — duraklatma kararı da 3× şişkin bir p-değerine dayanıyor. `check_stride=21` (kontrol sıklığı) kalibre edilmemiş. |

---

## C · Görsel denetim — gösterge çıktısı ile tasarım şartnamesi arasındaki boşluklar

Her göstergenin ürettiği primitif kümesi ile `docs/design/grafik_stil_vitrini.html`'deki karşılık gelen sahnenin çizdiği öğeler karşılaştırıldı.

### C1 · `IndicatorResult`'ta eksik olan iki kavram

**`badge`** — artifact'in **her** sahnesi sağ üstte bir durum hapı döndürüyor: `"TOP %10"`, `"BOĞA"`, `"BOĞA DİZİLİM"`, `"HASAT: +4.8%"`, `"Y AL"`. `IndicatorResult`'ta böyle bir alan yok; renderer bunu türetmek zorunda ve şu an hiç türetmiyor. **Grafiğin 3 saniyede okunan tek mesajı bu** — en kritik eksik.

**Zengin `subtitle`** — artifact: `"Z: 1.40 → 1.33 · Dönüş onaylandı"`, `"rank_pct: %6 (evrenin en iyisi)"`, `"EMA 8/21/55/200 dizilimi · bant sıkışma/genişleme"`. tlab'ın `_build_subtitle`'ı gösterge adından türetilen çok daha ince bir metin üretiyor. Hesaplanmış değerler `last_state`'te **zaten var**, başlığa taşınmıyor.

### C2 · Üretilmeyen çizim öğeleri

| Sahne | Artifact çiziyor | Gösterge üretiyor mu |
|---|---|---|
| Harmonik | X/A/B/C/D köşe daireleri + harf etiketleri | ❌ hayır (yalnızca D kutusu) |
| Harmonik | "AKTİF" outline rozeti, "→ Buraya girerse tepki/dönüş aranır" notu | ❌ hayır |
| Çift tepe/dip | Boyun seviyesine **oturan** 5 köşeli M/W hologramı | ❌ hayır — kapanış yolunu izleyen amorf çokgen |
| Klasik formasyonlar | Önder çizgili `KIRILIM` / `RETEST` kutuları | ⚠️ Marker var, önder çizgi/kutu renderer'da yok |
| Bayrak | "DİREK" hap etiketi | ⚠️ `pattern_pole` Line var, etiket yok |
| Alpha Rank | Sıralama bandı çokgenleri + `rank_pct` sağ etiketi | ❌ gösterge yalnızca Signal + series veriyor |
| MA Sistemleri | Ribbon dolgu (MA'lar arası bant), sıkışma vurgusu | ⚠️ Line var, dolgu yok |
| EWMAC | Forecast alanı (pozitif/negatif dolgu), cap çizgileri | ⚠️ series var, alan dolgusu yok |
| Dönüş Haritası | Katmanlı bölgeler + "DİPTE OLASI: X \| N kaynak" hapı | ⚠️ `render_reversal_map` **yazılmış** ama erişilemiyor (aşağı bkz.) |

### C3 · Yazılmış ama erişilemeyen görseller

- **`render_reversal_map`** (`renderer.py:2468`) tam olarak çalışan bir fonksiyon, ama `confluence` / `reversal_map` `CATALOG`'da yok ve `viz/live.py::compute_live` CATALOG'da olmayan her adı `ValueError` ile reddediyor. `structure.report` için özel bir kaçış yolu var (`STRUCTURE_REPORT_NAME`), dönüş haritası için yok. **Web'den ulaşılamıyor.**
- **`render_alpha_scatter` / `render_momentum_heatmap`** (`viz/universe_charts.py`) — `tlab universe-plot` ile çalışıyor, web'de route yok. *(TANI 1.5, Faz 6)*

### C4 · Ekran görüntülerindeki gözlemlerin kod karşılığı

| Görselde görülen | Kod nedeni |
|---|---|
| ALTNY: "ÇİFT DİP (RETEST TUTTU)" ama grafikte çift dip yok, geniş bir yuvarlak taban var | A1 (7 barlık pivotlar) + `min_bars_between=5` + ön trend yok + min derinlik yok |
| ALTNY: mavi leke formasyonu değil kapanış yolunu izliyor | `double_top_bottom.py` hologram `path_idxs` ile gerçek kapanışları çiziyor |
| ALTNY: Temmuz formasyonu Eylül grafiğinde taze gibi | `latest_signals`'ta yaşlılık filtresi yok *(TANI 1.3)* |
| ZOREN: TOBO derinliği fiyatın ~%3'ü — 4H gürültüsünden ayırt edilemez | min derinlik şartı yok |
| ZOREN: boyun çizgisi görsel olarak yatay ama kural fiilen elemiyor | `neck_slope_max` bar-başına normalize |
| Her iki görselde de hedef çizgisi grafiğin tamamına uzanıyor | `Level.end` düzeltmesi yapılmış ama declutter etiketi bastırıyor, çizgi kalıyor |

---

## D · Denetimin faz planına etkisi

`docs/TANI_VE_YOL_HARITASI_v2.md`'deki plan geçerli, ama **iki değişiklik** gerekiyor:

**1. YENİ FAZ 1-ÖNCESİ ADIM (Faz 0.5) — sistemik düzeltmeler.** A1/A2/A3 tek tek gösterge düzeltmelerinden **önce** yapılmalı, yoksa Faz 1'de kalibre edilen her eşik yanlış bir zigzag üstünde kalibre edilmiş olur. Kapsam:
- `significant_pivots()` ortak girişi + tüm formasyon göstergelerinin ona bağlanması
- `BaseParams.for_timeframe(tf)` ölçekleme mekanizması
- `engine.run()`'da `supported_timeframes` kapısı + `run_eod`'a `w1` eklenmesi
- Beş formasyonda `require_volume_confirm` parametresi (varsayılan kapalı, preset'te açık)

**2. FAZ 5 KAPSAMI DARALIYOR.** Denetim yapıldı; Faz 5 artık "denetle" değil "**denetimde bulunanları düzelt**": `five_zero` kök nedeni, `ewmac` sabit forecast tablosu, `momentum_rank` skor normalizasyonu, `alpha_rank` likidite eşiği ölçümü, `breakouts` skor dağılımı + tür gruplama, `price_structure` optimizasyonu, `universe` göstergelerinin `/chart` yolunda evren hesaplamaması.

**3. FAZ 4'e EKLENİYOR:** `IndicatorResult.badge` + zengin `subtitle` alanları (C1) ve C2'deki eksik çizim öğelerinin göstergelerde üretilmesi — bunlar viz değil **indikatör** işi (renderer hesap yapmaz ilkesi).
