# Kalan İşler — Aşama B sonrası

**Durum (2026-09-11, güncellendi):** 27 göstergenin **27'si** `tlab/
chart`'a bağlı. 1005 test yeşil (989→1005). Frontend derleniyor (`npm run
build` temiz). Gerçek BIST verisiyle 24/27 gösterge görsel olarak
doğrulandı, 3 tema spot-check edildi, `ucgenadaptoru/` kalıntısı
temizlendi. Madde 1'e ilk tur ölçüm (forward-return, 23 gösterge × 60
sembol) ve `trend.breakouts` quality_score'un getiriyle İLİŞKİSİZ
olduğunun istatistiksel kanıtı eklendi (1.6, 1.4).

**MADDE 2 (tespit edici kök nedenleri) TAMAMLANDI:** 2.1 wedge/triangle/
broadening'in aşırı-uzun-formasyon sorunu `max_bars=180` ile kapatıldı
(GARAN'ın sahte 500-barlık üçgeni artık üretilmiyor, LIDER'in gerçek
~9 aylık üçgeni doğru render ediliyor); 2.2 golden_zone swing seçimi
incelendi, kök nedeni belgelendi, üretimde tüketicisi olmadığı için
DEĞİŞTİRİLMEDİ (kullanıcı kararı önerisi bırakıldı); 2.3 `patterns.
flag_pennant`e empirik kalibre edilmiş bir `is_htf` (High and Tight
Flag) ayrımı eklendi (tam evrende 161 aday); 2.4 `broadening`
hologramının çarpık-kama görünümü zaman-hizalı yamuk köşeleriyle
düzeltildi; 2.5 `harmonic.five_zero`nun gerçek evren nadirliği
ölçüldü (60 sembolde 0, ALCAR'da elle 3).

**MADDE 3 (fikstür kırılganlığı) TAMAMLANDI:** gösterge başına aday
sayısı GERÇEK 648-sembollik tam evren taramasından (`outputs/
results.db`) ve taze bir 200-sembollük sayımdan çıkarıldı. **2 GERÇEK,
tam anlamıyla "bozuk" (dar değil) hata bulundu ve düzeltildi:**
`patterns.breakout_fvg` 4H'te SIFIR aday veriyordu (648 sembolün
648'inde de), `patterns.flag_pennant` 4H'te fiilen sıfırdı (3/648) —
ikisi de AYNI kök nedene sahip (bir ORAN parametresi `_BAR_FIELDS`
ölçeklemesinden dışarıda kalıp sabit kalırken, onunla ilişkili bar-sayısı
eşiği ×3 büyüyordu, eşik matematiksel olarak ulaşılamaz hâle geliyordu)
— `for_timeframe()` override'larıyla düzeltildi (913 ve 618 adaya
çıktı). 1007 test yeşil. Aşağıdakiler bağlama işi DEĞİL — sistemin
doğruluğu ve olgunluğu için kalanlar.

---

## 0. Sonnet için: çalışma kuralları

Bu turlarda hataların **çoğu yalnızca ekran görüntüsüne bakınca**
bulundu; kod okuyarak değil. Aynı döngüyü sürdür:

```bash
PYTHONPATH=. python3 scripts/grafik_cek.py THYAO patterns.triangle
```
Sonra **görüntüye BAK**. Sayılar makul mü, etiketler çakışıyor mu,
çizgiler fiyatla ilişkili mi.

### Tekrar tekrar yakalanan 5 tuzak

1. **Birim tuzağı (3 kez yakalandı).** `depth_pct`, `pole_pct`,
   `width_pct` — adları "yüzde" diyor ama komposer `* 100` yapıyor,
   yani sözleşme **kesir** istiyor. Grafikte "%421", "%1451", "%734"
   gördüysen bu. **Yeni bir `*_pct` alanı doldururken komposerin ne
   yaptığına BAK.**
2. **Anahtar uyuşmazlığı.** `last_state` anahtarı ile sinyal
   `payload["pattern_id"]` aynı olmayabilir (harmonikte
   `{okul}_{formasyon}_{aday}`, sinyalde ikisi ayrı alan). Eşleşmezse
   `bars_ago` sessizce `None` kalır.
3. **Alan adı ≠ anlam.** `weekly_channel`'ın `last_state["slope"]`i
   kanalın eğimi değil, orta çizginin son haftalık farkı.
   `swing_fib_abcd`'nin `last_label`i durum değil, swing etiketi.
   **Bir alanı kullanmadan önce nasıl hesaplandığına bak.**
4. **Sabit indeks.** `pat.points[3]` gibi konuma dayalı erişim iskelet
   değişince patlar — **etikete göre** ara.
5. **Ölçek çakışması.** Baz-100 normalize seriler ham mumlarla aynı
   panele konmaz.

---

## 1. ÖLÇÜM — en büyük açık (öncelik 1)

27 gösterge tarıyoruz ve **hiçbirinin ileriye dönük getirisi
ölçülmedi**. Grafiklerin güzelliğinden çok daha önemli.

- **1.1 `slope_ratio_range` düzeltmesinin etkisi ölçülmedi.**
  Yükselen/alçalan üçgen artık üretiliyor (önce SIFIRDI) → sinyal
  sayısı ARTACAK. `tlab eod --market bist` koşup önce/sonra sayımını
  karşılaştır. Beklenmedik patlama olursa
  `wedge.py::_FLAT_SIDED_SHAPES` muafiyeti gözden geçirilmeli.
- **1.2 İleriye dönük getiri doğrulaması (Aşama E).** Her gösterge ×
  her durum için: sinyalden sonraki N barda getiri dağılımı, koşulsuz
  dağılıma karşı. Yöntem: Lo-Mamaysky-Wang (2000) — koşullu vs
  koşulsuz dağılım karşılaştırması.
- **1.3 Çoklu test düzeltmesi.** `discovery.py`de Benjamini-Hochberg
  zaten var; aynı disiplin GÖSTERGE seçimine uygulanmalı. Deflated
  Sharpe (Bailey & López de Prado 2014) + permütasyon testi (Aronson).
- **1.4 `trend.breakouts` kalite skoru kalibre edilmedi.** Ağırlıklar
  (hacim 0.30 / yaş 0.20 / temas 0.20 / gövde 0.15 / mesafe 0.15)
  görev metninden geldi, ÖLÇÜLMEDİ. Artık grafik bu skora göre TEK
  kırılım seçiyor — yanlışsa yanlış kırılımı gösteriyoruz.
  **ÖLÇÜLDÜ (2026-09-11), sonuç NET:** `scripts/quality_score_
  kalibrasyon.py`, `outputs/reports/quality_score_kalibrasyon_2026-09-11.
  csv` — AYNI 60 sembol, `trend.breakouts`'un 23544 confirmed/completed
  sinyali, `sig.score` ile 20-bar yön-düzeltilmiş getiri arasında
  Spearman ρ=0.0008 (p=0.90) — **istatistiksel olarak SIFIRDAN
  AYIRT EDİLEMEZ**. Skor çeyreklik dilimlerine bölündüğünde de getiri
  monoton ARTMIYOR (en yüksek dilim değil ORTA-ÜST dilim en iyi
  ortalamayı veriyor: %1.52 vs en üst dilimin %0.83'ü). Yani "233
  kırılımdan quality_score'u en yüksek olanı seç" kuralı şu an
  RASTGELE seçmekten ölçülebilir şekilde daha iyi DEĞİL — ağırlıklar
  (hacim/yaş/temas/gövde/mesafe) gerçek veriden yeniden türetilmeli
  (ör. bileşenlerin 20-bar getiriye karşı basit bir regresyonu) ya da
  skor tamamen kaldırılıp başka bir seçim kuralı (ör. en GÜNCEL kırılım)
  denenmeli. Bu, raporun "en riskli" uyarısını DOĞRULUYOR — spekülasyon
  değil, ölçülmüş.
- **1.5 `repaint_alarm`** `pattern_id` düzeltmesinden sonra %100'den
  %0-4'e düştü ama sıfırlanmadı.
- **1.6 İLK TUR ölçüm yapıldı (2026-09-11) — 1.2'nin başlangıcı, TAM
  DEĞİL.** `scripts/olcum_forward_return.py`, `outputs/reports/ilk_
  olcum_forward_return_2026-09-11.csv`. Yöntem: context/universe
  istemeyen 23 gösterge, 60 rastgele BIST sembolü (≥300 bar, tam evrenin
  ~%9'u), 1D, `indicator(df)` TAM geçmiş üzerinde BİR KEZ (non-repaint
  sözleşmesi sayesinde walk-forward'a gerek yok) → `state in {confirmed,
  completed}` sinyaller → giriş `detected_at` kapanışı, [5,10,20] bar
  ileri getiri (short'ta işaret ters). Baz çizgi: AYNI sembollerde
  rastgele barların long/short KARIŞIMI sinyallerin kendi long/short
  oranıyla ağırlıklandırılmış hâli (`baz_adil_Nb`) — düz "uzun-only
  piyasa sürüklenmesi" baz alınsaydı BIST'in bu pencerede TL bazında çok
  güçlü nominal yükselişi TÜM göstergeleri yapay olarak "iyi" gösterirdi.

  **Bulgular (20 bar, `fark_20b` = gösterge ortalaması − adil baz):**
  büyük örneklemli (n≥300) göstergelerde küçük ama TUTARLI pozitif fark
  — `trend.breakouts` (+%0.66, n=24525), `structure.golden_zone`
  (+%0.61, n=920), `trend.ma_systems` (+%0.49, n=5100), `trend.
  weekly_channel` (+%0.61, n=3595). Orta örneklemde de pozitif: `patterns.
  double_top_bottom` (+%1.92, n=51), `patterns.head_shoulders` (+%1.55,
  n=65). **Negatif ve dikkat çekici:** `patterns.broadening` (−%1.86,
  n=102), `harmonic.carney` (−%3.66, n=68) — ikisi de n yeterince büyük,
  tesadüf ihtimali düşük. `patterns.triangle`'ın devasa +%11.86'sı
  (n=30) GÜVENİLMEZ SAYILMALI — GARAN örneğinde görsel olarak doğrulandı
  (bkz. madde 2), Ekim 2024'ten bugüne (~500 bar) süren gerçekçi olmayan
  bir "formasyon" kaynaklı, kısa vadeli kırılım kenarı değil sürdürülen
  piyasa beta'sı ölçüyor olabilir — max_bars düzeltilmeden bu sayıya
  güvenilmemeli. Küçük örneklemler (`harmonic.nenstar` n=2, `harmonic.
  navarro200` n=4, `harmonic.gilmore`/`cypher`/`wedge` n=12-15) İSTATİSTİKSEL
  OLARAK ANLAMSIZ, yalnızca ham sayı olarak kaydedildi.

  **Bu SADECE bir ilk bakış, 1.2/1.3'ün TAMAMI DEĞİL:**
  tam evren değil (648'in 60'ı), tek ~2 yıllık pencere (rejim çeşitliliği
  yok), IS/OOS ayrımı yok, işlem maliyeti yok, çoklu test düzeltmesi
  (1.3, Benjamini-Hochberg/deflated Sharpe) HENÜZ UYGULANMADI — 23
  gösterge test edilince %5 eşikte tesadüfen ~1 "anlamlı" çıkması
  beklenir. Sonraki adım: tam evren + Benjamini-Hochberg + IS/OOS split.

## 2. TESPİT EDİCİ kök nedenleri (öncelik 2)

- **2.1 `wedge.py` orantısız sınır çiftleri ÜRETİYOR — KISMEN KAPATILDI
  (2026-09-11).** İki AYRI sorun karışmıştı, ikisi de gerçek:
  (a) **süre** — formasyonun kendisi (P1-doğum mesafesi) yıllarca
  sürebiliyordu (GARAN `patterns.triangle`, Ekim 2024→bugün, ~500 bar —
  görsel olarak doğrulandı, `docs/spec/FORMASYON_DENETIM_v2.md`'nin
  span taramasıyla TUTARLI). Bu, `WedgeParams.max_bars`/`BroadeningParams.
  max_bars`'ın (1C'de eklenen ama 0=sınırsız bırakılan opsiyonel üst
  sınır) varsayılanını **180 bar (D1, ~8.5 ay)** yapılarak KAPATILDI —
  60 sembollük TAZE bir span taramasıyla doğrulandı (`scripts/max_bars_
  olcum.py`, `outputs/reports/max_bars_span_olcum_2026-09-11.csv`: 59
  confirmed/completed adayın %56'sı 180 bar altında kalıyor, üst uç
  344 bara kadar çıkıyordu). GARAN'ın 500 barlık sahte üçgeni artık HİÇ
  aday üretmiyor (tek adayıydı); LIDER'in ~9 aylık GERÇEK bir yükselen
  üçgeni (Kas 2024-Ağu 2025, net temas sayısı 9 üst/13 alt) görsel
  olarak doğrulandı, hâlâ doğru render ediliyor. 200 test yeşil, 0
  regresyon (`_BAR_FIELDS` dışında tutulduğu için timeframe ölçeklemesi
  etkilenmedi).
  (b) **orantısızlık** — `build_trendlines`'ın aday eşleştirmesi
  BENZER BÜYÜKLÜKTEKİ pivotları birleştirme kuralına (CMT) uymuyor;
  bu HENÜZ AÇIK, `max_bars` bunu dolaylı olarak azaltır (çok uzun süren
  adaylar elenince orantısız çiftlerin bir kısmı da elenir) ama kökten
  ÇÖZMEZ — `build_trendlines`'ın KENDİSİ (price_structure/breakouts/
  head_shoulders/double_top_bottom'u da etkileyen paylaşılan bir
  fonksiyon) ayrı, daha kapsamlı bir iş.
- **2.2 `golden_zone`: hangi swing güncel bölgeyi tanımlar? İNCELENDİ
  (2026-09-11), KASITLI OLARAK DEĞİŞTİRİLMEDİ — kod okuma sonucu.**
  Kök neden netleşti: `golden_zone.py::compute()` HER swing için ayrı
  Box/Level/signal üretiyor (`payload["swing_id"]` ile ayrışıyor) —
  `last_state` (`band_low`/`band_high`/`in_band`/`distance_atr`) İSE
  yalnızca döngüdeki `is_open` swing'e (kronolojik olarak EN YENİ,
  kendinden sonraki pivot henüz kesinleşmemiş) ait, çünkü döngü
  sırayla yazılıp SON swing'te üzerine yazılıyor. Adaptör (`chart_
  adapter.py::golden_zone_to_fib`) ve BAĞIMSIZ bir başka dedektör
  (`fib_retracement.py`, `best_span` ile "en geniş bacak") ise İKİSİ DE
  EN BASKIN (en büyük |fiyat açıklığı|) swing'i seçiyor — iki farklı
  yerde bağımsızca aynı karara varılmış, bu "baskın" seçiminin daha
  sağlam olduğuna dair zayıf ama gerçek bir sinyal. **Değiştirmedim
  çünkü:** `grep` ile doğrulandı — `last_state`'in band alanları `/scan`,
  `web/backend`, dashboard'un HİÇBİRİNDE tüketilmiyor (yalnızca kendi
  testinde okunuyor); yani şu an üretimde SIFIR etkisi var, "baskın"a
  çevirmek `is_open` olmayan bir swing için `distance_atr`/`in_band`'i
  YENİDEN tanımlamayı gerektiren, riski faydasından büyük bir değişiklik
  olurdu. **Öneri:** ya `last_state`'i TAMAMEN kaldır (hiçbir tüketicisi
  yok), ya da bilinçli bir ürün kararıyla "baskın"a çevir — ikisi de
  kullanıcı kararı gerektiriyor, kod tarafında engel yok.
- **2.3 "High and tight flag" ayrı tür olarak ayrılmalı — KAPATILDI
  (2026-09-11).** Kod incelemesi: `pole_flag.py::detect_pole_flag()`
  ÖLÜ KOD (hiçbir yerden çağrılmıyor, `grep` ile doğrulandı) — yalnızca
  `PoleFlag` dataclass'ı (grafik sözleşmesi tipi) canlı. GERÇEK/taranan
  direk-bayrak dedektörü `flag_pennant.py::FlagPennantIndicator`e
  additif bir `is_htf: bool` alanı eklendi (`shape`/`_LABEL_TR`
  sözlüğüne DOKUNULMADI, ayrı/ortogonal bir bayrak). **Eşik Bulkowski'nin
  ham %90'ı DEĞİL, empirik olarak kalibre edildi:** bu sistemin
  `find_impulses`i her direği SABİT `pole_bars` (varsayılan 5)
  barlık bir pencerede ölçüyor — 648 sembollük tam BIST evreninde
  3403 gerçek direğin `pole_pct` dağılımı ölçüldü (medyan %11.4, %99
  yüzdelik dilim %46.5, gözlenen maksimum %86.8) — %90'ı AŞAN SIFIR
  direk vardı, yani literatürün ham sayısı bu 5-barlık pencerede
  fiilen imkânsıza yakın. `htf_pct=0.30` (dağılımın ~%95 yüzdelik
  dilimi — "en patlayıcı direklerin en üstü") empirik varsayılan
  yapıldı; bu eşikle tam evrende **161 gerçek HTF adayı** bulundu
  (sıfır değil, aşırı kalabalık da değil). BARMA'da (%40.9 direk,
  short, KIRILIM ONAYLANDI) hem veri katmanında (`last_state["is_htf"]`)
  hem grafik başlığında ("YÜKSEK VE SIKI BAYRAK") uçtan uca GÖRSEL
  olarak doğrulandı. Yol boyunca AYRI bir gerçek hata bulunup
  düzeltildi: `is_htf` ilk haliyle `numpy.bool_` sızdırıyordu
  (`bool()` ile kaynağında önlendi — `IndicatorResult.to_json()`'un
  AYNI sınıf hatayı defansif yakaladığı önceki bir düzeltmeyle aynı
  kategori). 2 yeni kilitleyen test, 1005 test yeşil (1003→1005).
  **Kapsam dışı bırakılan:** ESKİ `tlab/viz/svg/scenes/flag_pennant.py`
  sahnesi (chart.png/dashboard yolu) `is_htf`'i HENÜZ göstermiyor —
  yalnızca YENİ `tlab/chart` yoluna (chart.json/interaktif sayfa)
  eklendi.
- **2.4 `broadening` hologramı yanıltıcı — KAPATILDI (2026-09-11).**
  Kök neden bulundu: hologram 4 köşesi iki sınır çizgisinin HAM (bağımsız
  seçilmiş, genelde FARKLI zamanlı) pivotlarını sırayla birleştiriyordu
  — üst çizginin p1'i ile alt çizginin p1'i aynı bar OLMAK ZORUNDA
  değildi, bu da ıraksayan bir formasyonu GÖRSEL olarak yakınsayan bir
  kama gibi gösterebiliyordu. Düzeltme: `boundary_adapter.py::_spanned`
  ile AYNI ilke — 4 köşe artık iki çizginin ORTAK `[start_idx,
  created_idx]` aralığındaki `Trendline.value_at()` değerlerinden
  kuruluyor (düzgün bir yamuk, sol iki köşe aynı zaman, sağ iki köşe
  aynı zaman). TEZOL/patterns.broadening'de (eski SVG motoru,
  `chart_png.py`'nin kullandığı yol) gerçek veriyle GÖRSEL olarak
  doğrulandı — düzgün genişleyen bir yamuk, artık çarpık değil. Test
  güncellendi (`test_hologram_polygon_matches_boundary_line_corners`
  eski/hatalı davranışı doğruluyordu, `test_hologram_polygon_is_time_
  aligned_trapezoid` olarak yeniden yazıldı). 1003 test yeşil, 0
  regresyon. **Not:** bu yalnızca ESKİ `tlab/viz/svg` motorunu
  (`chart.png`, dashboard/scan/EOD raporları) düzeltir — YENİ `tlab/
  chart` motoru (`chart.json`, interaktif `/chart` sayfası) zaten HİÇ
  dolgu/hologram çizmiyor (yalnızca iki çizgi), bu sorunu hiç
  yaşamıyordu.
  ham pivotları birleştirdiği için kama gibi görünebiliyor.
- **2.5 `harmonic.five_zero` gerçek evren sayısı ÖLÇÜLDÜ (2026-09-11).**
  60 rastgele BIST sembolünde (`olcum_forward_return.py`'nin AYNI
  örneklemi) **0 confirmed/completed sinyal** — ALCAR gibi BİLİNEN
  pozitif bir örnek elle test edildiğinde 3 sinyal (pending/active/
  confirmed) üretiyor, yani dedektör ÇALIŞIYOR ama son derece SEYREK.
  60/648 rastgele örneklemde sıfır çıkması, "622 sembolde sıfır"
  bulgusunun `c_beyond_a_required=True` düzeltmesinden SONRA bile
  büyük ölçüde geçerli kaldığını gösteriyor — kök neden muhtemelen
  düzeltilmedi, yalnızca (matematiksel olarak imkânsız olmaktan)
  "aşırı nadir" hâline geldi. Daha derin bir inceleme (oran
  bantlarının 8 ekol arasında neden bu kadar dar olduğu) HENÜZ
  YAPILMADI.

## 3. FİKSTÜR kırılganlığı (öncelik 3) — TAMAMLANDI (2026-09-11)

Bayrak fikstüründe n=100/105/110/120/130 denendi, **yalnızca 120**
çizilebilir aday verdi. Bu, tespit edicilerin gerçek veride ne sıklıkta
tetiklediğine dair bir uyarı. `tlab eod` sonrası gösterge başına aday
sayısı çıkarılmalı; sıfıra yakın olanlar ya çok dar ya bozuk.

**Çıkarıldı — 2 kaynaktan:** (1) `outputs/results.db`'deki GERÇEK
648-sembollik tam BIST taraması (`run_id=bist_2026-09-04`, `tlab eod`
önceden koşulmuş), (2) `scripts/aday_sayisi_sayimi.py` ile 200 rastgele
sembolde GÜNCEL koddan taze bir sayım. Tam tablo: `outputs/reports/
aday_sayisi_sayimi_2026-09-11.txt`.

**BULUNAN VE DÜZELTİLEN 2 GERÇEK HATA (tam anlamıyla "bozuk", "dar"
değil):**
- **`patterns.breakout_fvg`, 4H: 0/648 sembol — SIFIR aday tüm evrende.**
  Kök neden: `box_atr_max` (konsolidasyon kutusunun ATR'ye göre üst
  genişliği) bir ORAN, `_BAR_FIELDS` DEĞİL — `consolidation_bars`in
  D1→4H ölçeklemesi (10→30, ×3) `box_atr_max`ı (1.5) SABİT bırakıyordu.
  80 gerçek sembolde ölçüldü: 30-bar/ATR(14) oranının 4H'teki MİNİMUMU
  bile (~3.05) 1.5'in altına hiç inmiyor — eşik matematiksel olarak
  ulaşılamazdı. Düzeltme: `BreakoutFvgParams.for_timeframe()` H4 için
  `box_atr_max=3.2` (D1'in aynı ~%0.5 yüzdelik dilimi) döndürüyor.
  Sonuç: **0/648 → 913 aday / 435 sembol** (D1'in 878/440'ıyla AYNI
  mertebede).
- **`patterns.flag_pennant`, 4H: 3/648 — fiilen sıfır.** AYNI kök
  neden: `flag_min_bars` 5→15 (×3) ölçeklenirken `flag_atr` (1.5) sabit
  kalıyordu. Düzeltme: `for_timeframe()` H4 için `flag_atr=2.9`.
  Sonuç: **3 → 618 aday / 186 sembol**.
- İkisi de `scripts/breakout_fvg_box_atr_olcum.py` ile ölçüldü, 2 yeni
  kilitleyen test (`test_for_timeframe_widens_box_atr_max_on_h4`,
  `test_for_timeframe_widens_flag_atr_on_h4`), 1007 test yeşil, 0
  regresyon.

**Dar ama BOZUK OLMAYAN (gerekçesi ölçüldü, kod DEĞİŞTİRİLMEDİ):**
`harmonic.five_zero` (0-1/200-648, madde 2.5'te zaten ele alındı —
dedektör çalışıyor, aşırı seyrek). `patterns.triangle`/`patterns.wedge`
D1'de sırasıyla 7/200 ve 11/200 sembole düştü — ama bu `max_bars=180`
düzeltmesinin (madde 2.1) BEKLENEN, İSTENEN bir yan etkisi (önceden
GARAN gibi 500-barlık sahte adaylar da sayılıyordu). `patterns.
broadening`'in eskiden 590 sembolde 32194 aday (sembol başına ~55)
üretmesi de AYNI `max_bars=180` düzeltmesiyle ~1758'e (sembol başına
~13.5) indi — "çok dar" değil "çok GEVŞEK" olan bu vaka da aynı
düzeltmeyle kendiliğinden iyileşti. `structure.*`/`trend.*` grubunun
TAMAMI 648 sembolün 623'ünde doygun (623/623) — dar değil, sağlıklı.
`pair.*` 17 çiftin 17'sinde de çalışıyor (251+182 sinyal).

## 4. DOĞRULANMAMIŞ olanlar

- ~~Gerçek BIST verisiyle HİÇBİRİ doğrulanmadı~~ **DOĞRULANDI
  (2026-09-11, masaüstü ortamında).** Bu makinede `data/ohlcv/bist/`
  altında GERÇEK 648 sembollik önbellek zaten vardı (`tlab eod`
  önceden koşulmuş, veri 2026-09-04 kapanışına kadar güncel).
  Context/universe istemeyen 23 gösterge, 10 gerçek sembolde
  (THYAO/BAKAB/AKBNK/TUCLK/ISCTR/CEMTS/EMNIS/GARAN/SASA/KRPLS)
  denendi — **24/27 çöküşsüz render etti** (3'ü: `pair.*` özel akış
  ister — bu örneklemde denenmedi, `harmonic.five_zero` bilinen
  sıfır-aday sorunu). Görsel incelemede yeni bir GERÇEK hata
  BULUNMADI — GARAN `patterns.triangle`'da madde 2.1'in (wedge/
  triangle aşırı uzun sınır çifti) GERÇEK bir örneği görsel olarak
  doğrulandı (Ekim 2024 – Eylül 2026 arası, ~500 bar): bilinen sorun,
  YENİ değil.
- ~~Frontend `tsc --noEmit` / `npm run build` çalıştırılmadı~~
  **YAPILDI (2026-09-11).** `npm install` (node_modules zaten
  vardı) → `tsc --noEmit` GERÇEK bir hata verdi: `types/plotly-
  finance.d.ts`'in elle yazılmış `Config` arayüzünde `displaylogo`/
  `modeBarButtonsToRemove`/`toImageButtonOptions` eksikti (`ChartPlotly.
  tsx`'in kullandığı ama tipte olmayan alanlar) — düzeltildi, tsc/
  eslint/`next build` şimdi TEMİZ (yalnızca 2 önceden var olan/zararsız
  uyarı).
- ~~3 tema... yalnızca dark incelendi~~ **classic + editorial de
  GÖZLE incelendi** (harmonic.carney/THYAO örneği) — ikisi de temiz,
  kontrast/okunabilirlik sorunu yok. (27 göstergenin TAMAMI 3 temada
  TEK TEK incelenmedi — bu hâlâ açık, ama tasarım sisteminin 3 temada
  da çalıştığına dair spot-check pozitif.)
- **AYRICA bu turda bulunup düzeltilen, önceden bilinmeyen 2 gerçek
  hata:** `tlab/features/stats.py::engle_granger_pvalue` statsmodels
  `coint()`'in HER ZAMAN tuple döndüğünü (`.pvalue` niteliği YOK)
  fark etmemiş — discovery/coint_monitor/relative_momentum'a bağlı 19
  test bu yüzden KIRMIZI çıkıyordu (statsmodels 0.14.6 ile doğrulandı,
  düzeltildi, 1003 test şimdi yeşil). Repo kökünde unutulmuş
  `ucgenadaptoru/` klasörü (paralel bir oturumun push edemeyip zip
  teslim ettiği, zaten entegre edilmiş 3 dosyanın HAM kopyası)
  kaldırıldı.
- **YENİ — `trend.breakouts` quality_score ÖLÇÜLDÜ, kalibre
  edilmediği DOĞRULANDI** (bkz. madde 1.4: Spearman ρ=0.0008, p=0.90 —
  skorun getiriyle ilişkisi yok).

## 5. Bilinen küçük eksikler

- `zones` ve `pair` komposerlerine odak (`focus`) uygulanmadı —
  zaman aralığı tanımlı bir "formasyon" olmadığı için BİLİNÇLİ.
- `price_structure` hacim profili yan paneli çizilmiyor (`vp_*`
  serileri FİYAT-indeksli, ayrı panel ister).
- `weekly_channel` temas KONUMLARI gösterge tarafından dışa
  açılmıyor (yalnızca sayı) — çizgide temas dairesi yok.
- `alpha_rank` alfa t-istatistiği seri olarak değil, son değer olarak
  gösteriliyor (`SeriesOverlay` tek alt panel destekliyor).
